"""B/C: provenance and review gates. These checks do not infer scientific truth."""
from decimal import Decimal, InvalidOperation
import re
import unicodedata
from .common import check_source, read, require, sha, write

SECTIONS = ('background','question','methods','model','sample','results','conclusions','limitations')

def normalized(value):
    return re.sub(r'\s+', '', unicodedata.normalize('NFKC',str(value))).casefold()

def numbers(text):
    values = set()
    for token in re.findall(r'(?<![A-Za-z0-9_])[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][-+]?\d+)?',unicodedata.normalize('NFKC',str(text)).replace('\u2212','-')):
        try: values.add(str(Decimal(token.replace(',','')).normalize()))
        except InvalidOperation: pass
    return values

def indexed(items, label):
    require(isinstance(items,list) and items, 'CONTRACT', f'{label} must be a non-empty array.')
    result = {}
    for item in items:
        require(isinstance(item,dict) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*',str(item.get('id',''))), 'CONTRACT', f'{label} needs stable IDs.')
        require(item['id'] not in result,'DUPLICATE_ID',f'Duplicate {label} ID {item["id"]}.')
        result[item['id']] = item
    return result

def paper_state(job):
    state = check_source(job)
    if str(state.get('version','')).startswith('2.2.'):
        require(state.get('workflowContract')=='generalized-editorial-v1','WORKFLOW_CONTRACT','Do not remove the current run contract to bypass research/visual gates.')
    paper = read(job/'A/paper.json')
    parse_report = read(job/'A/parse-report.json')
    require(parse_report.get('paperSha256') == sha(job/'A/paper.json'), 'STALE_PARSE', 'Canonical extraction changed after parsing.')
    require(paper['sourceSha256'] == state['source']['sha256'], 'STALE_PARSE', 'Parsed source hash differs.')
    require(paper.get('allPagesExtracted') is True, 'UNREADABLE_PAGES', 'Some pages have no extracted text.')
    for page in paper['pages']:
        require(sha(job/page['image']) == page['imageSha256'], 'SOURCE_IMAGE_CHANGED','Source page image changed.')
    return state,paper

def validate_science(job, research_required=True):
    state,paper = paper_state(job)
    analysis = read(job/'B/analysis.json')
    review = read(job/'B/review.json')
    require(analysis.get('sourceSha256') == paper['sourceSha256'] and analysis.get('paperSha256') == sha(job/'A/paper.json'),
            'STALE_ANALYSIS','Analysis must reference the current source and canonical paper hash.')
    require(review.get('analysisSha256') == sha(job/'B/analysis.json'), 'STALE_SCIENTIFIC_REVIEW','Scientific review is stale or absent.')
    require(str(review.get('reviewer','')).strip(),'REVIEWER','Scientific reviewer is required (Codex or human; no implicit approval).')
    reviewed_pages = review.get('pages',[])
    require({x.get('page') for x in reviewed_pages} == set(range(1,paper['pageCount']+1)) and len(reviewed_pages)==paper['pageCount'],
            'INCOMPLETE_READING','Review must cover every PDF page, including supplements/references in the file.')
    for item in reviewed_pages:
        page = paper['pages'][item['page']-1]
        require(item.get('imageSha256') == page['imageSha256'] and item.get('status')=='reviewed' and item.get('notes'),
                'PAGE_NOT_REVIEWED',f'Page {item["page"]} needs a current image-bound review.')
    evidence = indexed(analysis.get('evidence'), 'evidence')
    require(normalized(analysis.get('paperTitle','')) and normalized(analysis['paperTitle']) in normalized(' '.join(p['text'] for p in paper['pages'])),
        'PAPER_TITLE_SOURCE','Original paper title must be transcribed from the source, not invented.')
    claims = indexed(analysis.get('claims'), 'claims')
    evidence_reviews = indexed(review.get('evidence'), 'evidence review')
    claim_reviews = indexed(review.get('claims'), 'claim review')
    assets = read(job/'A/assets.json') if (job/'A/assets.json').exists() else {}
    for key,item in evidence.items():
        page_no = item.get('page')
        require(type(page_no) is int and 1<=page_no<=paper['pageCount'], 'SOURCE_PAGE', f'{key}: invalid page.')
        require(item.get('kind') in ('text','table','formula','figure'),'EVIDENCE_KIND', f'{key}: unsupported evidence type.')
        source = paper['pages'][page_no-1]
        verified = evidence_reviews.get(key,{})
        require(verified.get('status')=='verified' and verified.get('rationale'),'UNVERIFIED_EVIDENCE',f'{key} is uncertain, rejected or unreviewed.')
        if item['kind']=='text':
            quote = item.get('quote','')
            require(len(normalized(quote)) >= 4 and normalized(quote) in normalized(source['text']),
                    'QUOTE_MISMATCH',f'{key}: quote is absent from the page extraction; review the original page.')
        else:
            asset = assets.get(item.get('assetId'),{})
            require(asset.get('page')==page_no and asset.get('sourcePageImageSha256')==source['imageSha256'],
                    'UNVERIFIED_CROP',f'{key}: crop must originate from this PDF page.')
            require(sha(job/asset['path'])==asset['sha256'] and verified.get('assetSha256')==asset['sha256'],
                    'STALE_ASSET_REVIEW',f'{key}: asset changed or has not been reviewed.')
            require(verified.get('originalVisualChecked') is True,'VISUAL_EVIDENCE_REQUIRED',f'{key}: original figure/table/formula must be checked visually.')
            if item['kind'] in ('table','formula'):
                require(verified.get('fidelity')=='verified','FIDELITY_BLOCK',f'{key}: distorted/uncertain table or formula cannot proceed.')
    for key,item in claims.items():
        require(item.get('type') in ('observation','interpretation','hypothesis'),'CLAIM_TYPE',f'{key}: distinguish observation/interpretation/hypothesis.')
        refs = item.get('evidenceIds',[])
        require(refs and all(x in evidence for x in refs),'MISSING_EVIDENCE',f'{key}: unresolved evidence references.')
        assessment = claim_reviews.get(key,{})
        require(assessment.get('status')=='supported' and assessment.get('rationale'),'UNSUPPORTED_CLAIM',f'{key}: no supported, reasoned claim review.')
        available = set()
        for quantity in item.get('quantities',[]):
            require(re.fullmatch(r'[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?',str(quantity.get('value',''))),
                    'QUANTITY_FORMAT',f'{key}: one numeric value per quantity; keep units separate.')
            require(quantity.get('evidenceId') in refs and str(quantity.get('unit','')).strip(),'QUANTITY_SOURCE',f'{key}: quantity needs an evidence ID and unit/definition.')
            available |= numbers(quantity.get('value'))
            ev = evidence[quantity['evidenceId']]
            if ev['kind']=='text':
                require(numbers(quantity['value']) <= numbers(ev.get('quote','')),'QUANTITY_MISMATCH',f'{key}: numeric value absent from cited quote.')
            else:
                require(assessment.get('quantitiesChecked') is True,'QUANTITY_VISUAL_REVIEW',f'{key}: image/table quantities require explicit original-PDF review.')
        require(numbers(item.get('text','')) <= available, 'UNINDEXED_NUMBER',f'{key}: key numerical claims need structured quantities.')
    structure = analysis.get('sections',{})
    require(all(key in structure for key in SECTIONS),'PAPER_STRUCTURE',f'Provide all sections: {SECTIONS}; use status=not-reported when absent.')
    for key,section in structure.items():
        require(isinstance(section,dict) and section.get('status') in ('reported','not-reported'),'PAPER_STRUCTURE',f'{key}: section status is required.')
        require(all(x in claims for x in section.get('claimIds',[])),'SECTION_CLAIM',f'{key}: invalid claim reference.')
        if section['status']=='reported': require(section.get('claimIds'),'SECTION_CLAIM',f'{key}: reported content needs claims.')
        else: require(section.get('reason'),'MISSING_SECTION_REASON',f'{key}: explain absent reporting; do not invent it.')
    report = {'status':'passed-contract-and-recorded-review','sourceSha256':paper['sourceSha256'],
        'analysisSha256':sha(job/'B/analysis.json'),'reviewSha256':sha(job/'B/review.json'),
        'reviewer':review['reviewer'],'pagesReviewed':paper['pageCount'],'evidenceCount':len(evidence),
        'claimCount':len(claims),'limits':'Review records are not independent proof of scientific truth. Exact source quotes, numbers and hashes were checked; semantic entailment remains the recorded reviewer assessment.'}
    from .statistics_review import statistic_definitions
    definitions=statistic_definitions(job,analysis,review)
    if definitions:report['verifiedStatisticDefinitions']=list(definitions)
    from .research import active,validate_research
    if research_required and active(state):report['researchDesign']=validate_research(analysis,review)
    write(job/'B/evidence-report.json',report)
    write(job/'B/paper-structure.json',{'paperTitle':analysis['paperTitle'],'sourceSha256':paper['sourceSha256'],
        'sections':{key:{**value,'statements':[claims[c]['text'] for c in value.get('claimIds',[])]} for key,value in structure.items()}})
    lines=['# 科学证据核验报告', '', report['limits'],'']
    for key,claim in claims.items():
        locations=', '.join(f'{e} (PDF p.{evidence[e]["page"]})' for e in claim['evidenceIds'])
        lines.extend([f'## {key}: {claim["text"]}', f'- 类型：{claim["type"]}',f'- 证据：{locations}',
            f'- 审读依据：{claim_reviews[key]["rationale"]}',''])
        for quantity in claim.get('quantities',[]):
            lines.append(f'- 核验数值：{quantity["value"]} {quantity["unit"]}；来源 {quantity["evidenceId"]}')
    lines.extend(['', '## 原始证据索引', ''])
    for key,item in evidence.items():
        lines.extend([f'### {key} — PDF p.{item["page"]} ({item["kind"]})',
            f'- 定位：{item.get("location", "PDF page as indexed")}',
            f'- 核验依据：{evidence_reviews[key]["rationale"]}'])
        if item['kind']=='text':
            lines.append('- 原文：'+item['quote'])
        else:
            asset=assets[item['assetId']]
            lines.extend([f'- 原始裁图：{item["assetId"]}；归一化区域 {asset["bbox"]}',f'- 图像 SHA-256：{asset["sha256"]}'])
        lines.append('')
    (job/'B/evidence-report.md').write_text('\n'.join(lines),encoding='utf-8')
    return analysis

def validate_plan(job, analysis=None):
    state,paper = paper_state(job)
    analysis = analysis or validate_science(job)
    plan = read(job/'C/plan.json')
    review = read(job/'C/review.json')
    settings = state['settings']
    require(plan.get('analysisSha256')==sha(job/'B/analysis.json'),'STALE_PLAN','Plan must reference current analysis.')
    require(review.get('planSha256')==sha(job/'C/plan.json') and review.get('reviewer'),'STALE_NARRATIVE_REVIEW','Plan review is absent or stale.')
    slides = plan.get('slides',[])
    indexed(slides,'slides')
    require(len(slides)==settings['slideCount'],'SLIDE_COUNT','Plan slide count differs from the run settings.')
    require(plan.get('language')==settings['language'],'LANGUAGE','Plan language differs from settings.')
    supported = indexed(review.get('slides'),'slide review')
    claims = {x['id']:x for x in analysis['claims']}
    evidence = {x['id']:x for x in analysis['evidence']}
    from .statistics_review import statistic_definitions,validate_summary
    definitions=statistic_definitions(job,analysis,read(job/'B/review.json'))
    layouts = set()
    from .research import active,resolve_layout,validate_new_plan
    if active(state):validate_new_plan(job,analysis,plan)
    for slide in slides:
        if slide.get('layout')=='auto':slide={**slide,'layout':resolve_layout(slide)}
        key=slide['id']
        legacy=('cover','statement','finding','chart','method','references')
        from .editorial import EDITORIAL_LAYOUTS, validate_visual
        require(slide.get('layout') in legacy or (plan.get('designSystem')=='modern-scientific-editorial' and slide.get('layout') in EDITORIAL_LAYOUTS), 'LAYOUT',f'{key}: use registered academic layouts.')
        layouts.add(slide['layout'])
        require(slide.get('title') and slide.get('notes') and isinstance(slide['notes'],str),'SPEAKER_NOTES',f'{key}: meaningful title and speaker notes are required.')
        require(supported.get(key,{}).get('status')=='supported' and supported[key].get('notesChecked') is True and supported[key].get('rationale'),
                'NARRATIVE_UNVERIFIED',f'{key}: check title, visible content and notes against the scientific evidence.')
        refs=slide.get('claimIds',[])
        require(refs and all(x in claims for x in refs),'SLIDE_CLAIMS',f'{key}: cite supported claims.')
        require(type(slide.get('seconds')) is int and slide['seconds']>0,'TIMING',f'{key}: positive integer seconds required.')
        body=slide.get('body',[])
        require(isinstance(body,list) and len(body)<=4 and all(isinstance(x,str) for x in body),'DENSITY',f'{key}: maximum four concise body statements.')
        visualtext=validate_visual(slide,claims) if plan.get('designSystem')=='modern-scientific-editorial' else []
        validate_summary(slide,claims,definitions)
        alltext=' '.join([slide['title'],slide['notes'],*body,*visualtext])
        allowed=set().union(*(numbers(q['value']) for cid in refs for q in claims[cid].get('quantities',[])))
        require(numbers(alltext)<=allowed,'UNSUPPORTED_SLIDE_NUMBER',f'{key}: a displayed or spoken number is not indexed in its cited claims.')
        if slide.get('assetId'):
            ev=[e for e in evidence.values() if e.get('assetId')==slide['assetId']]
            require(ev and any(e['id'] in claims[c]['evidenceIds'] for e in ev for c in refs),'ASSET_CLAIM',f'{key}: original image is not connected to its claims.')
        if slide.get('chart'):
            chart=slide['chart']
            require(chart.get('type','bar')=='bar' and not chart.get('errorBars') and chart.get('uncertainty','not-reported')=='not-reported',
                'CHART_UNSUPPORTED','Reported uncertainty/complex charts must retain a reviewed original figure; do not silently discard error bars.')
            require(chart.get('unit') and len(chart.get('labels',[]))==len(chart.get('values',[])) and 1<=len(chart.get('values',[]))<=8,'CHART_DATA',f'{key}: invalid chart data.')
            require(all(isinstance(x,(float,int)) and not isinstance(x,bool) for x in chart['values']),'CHART_DATA',f'{key}: chart values must be numeric.')
            pairs={(str(Decimal(str(q['value'])).normalize()),q['unit']) for c in refs for q in claims[c].get('quantities',[]) if numbers(q['value'])}
            require(all((str(Decimal(str(v)).normalize()),chart['unit']) in pairs for v in chart['values']), 'CHART_FIDELITY',f'{key}: chart values or units differ from indexed evidence.')
        if slide['layout']=='chart': require(slide.get('chart'),'CHART_DATA',f'{key}: chart layout needs chart data.')
        if slide['layout']=='finding': require(slide.get('assetId'),'FIGURE_REQUIRED',f'{key}: finding layout needs an original source crop.')
    total=sum(x['seconds'] for x in slides)
    maximum=settings['durationMinutes']*60
    require(0<total<=maximum,'TIMING',f'Planned {total}s exceeds allotted {maximum}s.')
    if settings['purpose']=='production':
        require(total>=maximum*0.8,'UNDER_SCRIPTED','Speaker plan uses less than 80% of allotted time.')
        require(len(layouts)>=4,'REPEATED_LAYOUT','Use at least four meaningful layout families.')
        require(slides[-1].get('role')=='conclusion','CONCLUSION_LAST','The last slide must preserve the take-home conclusions.')
        for a,b,c in zip(slides,slides[1:],slides[2:]):
            require(not resolve_layout(a)==resolve_layout(b)==resolve_layout(c),'REPEATED_LAYOUT','Avoid three identical consecutive layouts.')
    write(job/'C/narrative-report.json',{'status':'passed-contract-and-recorded-review','seconds':total,
        'allocatedSeconds':maximum,'bufferSeconds':maximum-total,'slides':len(slides),
        'planSha256':sha(job/'C/plan.json'),'reviewSha256':sha(job/'C/review.json'),
        'note':'Planned timing, not a measured speaking duration.'})
    (job/'C/speaker-notes.md').write_text('\n\n'.join(f'## {i}. {s["title"]} ({s["seconds"]}s)\n\n{s["notes"]}' for i,s in enumerate(slides,1)),encoding='utf-8')
    return {**plan,'slides':[{**s,'layout':resolve_layout(s)} for s in slides]}
