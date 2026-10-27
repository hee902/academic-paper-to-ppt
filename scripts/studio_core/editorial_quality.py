"""Reusable editorial screens based on this project's actual export failures.

No scientific numbers are changed. Glyph-row checks use the actual PowerPoint
PDF; they detect implicit wraps that are absent from DataLabel.Text.
"""
import math,re,statistics
from .common import ROOT,read,write,require,sha

def policy():return read(ROOT/'config/editorial-quality-policy.json')

def preflight(spec,settings):
    p=spec.get('editorialQualityPolicy',policy());findings=[];figures=[];timing=[]
    def issue(code,slide,obj,message,severity='review'):
        findings.append({'code':code,'slideId':slide,'objectId':obj,'severity':severity,'message':message})
    for s in spec['slides']:
        for o in s['objects']:
            if o['type']=='text':
                if re.search(r'\d[ \t]*[\r\n\v]+[ \t]*[%％]',o['text']):
                    issue('PERCENT_EXPLICIT_BREAK',s['id'],o['id'],'Number and percent sign contain an explicit line break.','error')
                if o['id']=='sources':
                    if len(o['text'])>p['sourceCaptionMaxCharacters'] or len(o.get('sourceLocators',[]))>p['sourceCaptionMaxLocators']:
                        issue('SOURCE_VERBOSE',s['id'],o['id'],'Use only author/year and the key figure/table/section; keep the full evidence chain in notes.','error')
            if o['type']=='image':
                area=o['w']*o['h']/(spec.get('theme',{}).get('slideWidthInches',40/3)*spec.get('theme',{}).get('slideHeightInches',7.5));short=min(o['w'],o['h'])
                info={'slideId':s['id'],'assetId':o['assetId'],'areaFraction':round(area,4),'shortSideInches':round(short,3)}
                if area<p['figureMinAreaFraction'] or short<p['figureMinShortSideInches']:
                    issue('FIGURE_SMALL',s['id'],o['id'],'Scientific figure is below area/short-side screen; enlarge or justify a readable alternative.')
                measurement=o.get('legibility')
                if measurement:
                    require(measurement.get('assetSha256')==o['sha256'],'FIGURE_MEASUREMENT_SOURCE','Legibility measurement must bind the unchanged original asset.')
                    fs=measurement['referenceTextSizePt'];width=measurement['referenceFigureWidthPt']
                    require(all(type(x)in(int,float) and math.isfinite(x) and x>0 for x in [fs,width]),'FIGURE_MEASUREMENT','Invalid source text/figure measurement.')
                    equivalent=fs*(o['w']*72/width)
                    minimum=p['calculationDiagramReferenceTextMinPt'] if measurement.get('role')=='calculation-summary' else 12
                    info.update(referenceTextEquivalentPt=round(equivalent,2),minimumPt=minimum,measurement=measurement)
                    if equivalent<minimum:issue('FIGURE_TEXT_SMALL',s['id'],o['id'],f'Source reference text displays at {equivalent:.2f}pt, below {minimum}pt screen.','error')
                else:info['textSizeStatus']='unmeasured-raster-requires-actual-visual-review'
                figures.append(info)
        han=len(re.findall(r'[\u4e00-\u9fff]',s['notes']));words=len(re.findall(r'[A-Za-z]+',s['notes']))
        pace=han/s['seconds'];wpm=words*60/s['seconds']
        timing.append({'slideId':s['id'],'seconds':s['seconds'],'hanCharacters':han,'hanPerSecond':round(pace,2),'englishWordsPerMinute':round(wpm,1)})
        if (han and pace>p['hanCharactersPerSecondReviewThreshold']) or (not han and wpm>p['englishWordsPerMinuteReviewThreshold']):
            issue('SPEECH_PACE',s['id'],'notes','Dense script for allotted time; revise time or substance and rehearse.')
        if s['seconds']>p['maximumSlideSecondsBeforeReview']:issue('SLIDE_DURATION',s['id'],'notes','Long dwell time requires content-specific review.')
    spoken=sum(s['seconds'] for s in spec['slides']);reading=spec.get('deliveryTiming',{}).get('readingAndTransitionSeconds',0)
    require(type(reading)is int and reading>=0,'TIMING','Reading/transition allowance must be nonnegative seconds.')
    per_slide=spec.get('deliveryTiming',{}).get('perSlideBuffers')
    if per_slide is not None:
        valid=isinstance(per_slide,dict) and set(per_slide)=={s['id'] for s in spec['slides']} and all(type(v)is int and v>=0 for v in per_slide.values())
        if not valid or sum(per_slide.values())!=reading:
            issue('TRANSITION_ALLOCATION','deck','notes','Per-page reading/pause buffers must cover every page and sum to the declared buffer.','error')
    if settings['purpose']=='production':
        minimum,maximum=settings['productionMinuteRange']
        if not minimum*60<=spoken+reading<=maximum*60 or spoken+reading>settings['durationMinutes']*60:
            issue('DELIVERY_TIMING','deck','notes','Spoken plus reading/transition plan exceeds the slot or is outside 15–20 minutes.','error')
        if spec['slides'][-1]['seconds']<p['conclusionRecommendedMinSeconds']:
            issue('CONCLUSION_RUSHED',spec['slides'][-1]['id'],'notes','Review time for final conclusions and discussion; do not pad with repeated introductions.')
    from .general_quality import screen_preflight
    screen_preflight(spec,findings)
    return {'status':'blocked' if any(x['severity']=='error' for x in findings) else 'screened-requires-visual-review',
        'policy':p,'findings':findings,'figures':figures,'timing':timing,'spokenSeconds':spoken,
        'readingAndTransitionSeconds':reading,'plannedTotalSeconds':spoken+reading,
        'limits':'Area and font estimates are screens. Raster labels, visual hierarchy and real speech still need review.'}

def percent_glyph_rows(pdf_path,tolerance_factor=.7):
    import pypdfium2 as pdfium
    pdf=pdfium.PdfDocument(str(pdf_path));tokens=[]
    regex=re.compile(r'(?<![\d.])[-+]?\d+(?:\.\d+)?\s*[%％]')
    for page_index in range(len(pdf)):
        page=pdf[page_index];tp=page.get_textpage();text='';indices=[]
        for i in range(tp.count_chars()):
            value=tp.get_text_range(i,1);text+=value;indices.extend([i]*len(value))
        for m in regex.finditer(text):
            boxes=[]
            for pos in range(m.start(),m.end()):
                if text[pos].isdigit() or text[pos] in '%％':
                    box=tp.get_charbox(indices[pos]);boxes.append(list(box))
            if not boxes:continue
            centres=[(b[1]+b[3])/2 for b in boxes];height=statistics.median(b[3]-b[1] for b in boxes)
            spread=max(centres)-min(centres);tolerance=max(4,height*tolerance_factor)
            tokens.append({'slide':page_index+1,'text':re.sub(r'\s','',m.group()),'glyphBoxesPt':boxes,
                'rowSpreadPt':round(spread,3),'tolerancePt':round(tolerance,3),'singleRow':spread<=tolerance})
        tp.close();page.close()
    pdf.close();return tokens

def postflight(job,spec,export,pdf_path):
    tokens=percent_glyph_rows(pdf_path,spec['editorialQualityPolicy']['percentTokenRowToleranceFactor']);findings=[]
    for t in tokens:
        if not t['singleRow']:findings.append({'code':'PERCENT_RENDER_WRAP','slide':t['slide'],'severity':'error','message':t['text']+' spans multiple rendered glyph rows.'})
    for i,s in enumerate(spec['slides'],1):
        for o in s['objects']:
            if o['type']=='chart' and o['unit']=='%':
                measured=[c for c in export.get('chartMetrics',[]) if c['slide']==i and c['id']==o['id']]
                expected=[f'{v:.2f}%' for v in o['values']] if o.get('numFmt')=='0.00"%"' else []
                actual=[lab['text'] for c in measured for series in c['series'] for lab in series['labels']]
                if expected and actual!=expected:findings.append({'code':'PERCENT_LABEL_TEXT','slide':i,'severity':'error','message':f'Actual chart labels {actual} differ from source-formatted labels {expected}.'})
                for value in expected:
                    inside=lambda t:all(o['x']*72-2<=b[0] and b[2]<=(o['x']+o['w'])*72+2 and
                        540-(o['y']+o['h'])*72-2<=b[1] and b[3]<=540-o['y']*72+2 for b in t['glyphBoxesPt'])
                    if not any(t['slide']==i and t['text']==value and t['singleRow'] and inside(t) for t in tokens):
                        findings.append({'code':'PERCENT_LABEL_UNMEASURED','slide':i,'severity':'error','message':value+' was not verified as one rendered PDF glyph row.'})
    for page in export['textMetrics']:
        for o in page['text']:
            if o['id']=='sources':
                chars=o.get('renderedLines',{}).get('characters',[]);tops=[c['top'] for c in chars if c['top'] is not None]
                if tops and max(tops)-min(tops)>o['fontSize']*.7:
                    findings.append({'code':'SOURCE_RENDER_WRAP','slide':page['slide'],'severity':'error','message':'Source caption occupies multiple actual PowerPoint rows.'})
    from .general_quality import screen_postflight
    extra,general=screen_postflight(job,spec,export,pdf_path);findings+=extra
    result={'status':'blocked' if any(f['severity']=='error' for f in findings) else 'passed-automatic-screen-awaiting-visual-review',
        'pptxSha256':sha(job/'E/presentation.pptx'),'pdfSha256':sha(pdf_path),'specSha256':sha(job/'D/deck-spec.json'),
        'percentTokens':tokens,'findings':findings,'preflight':read(job/'D/editorial-quality.json'),'generalizedScreens':general,
        'method':'Actual PowerPoint DataLabel.Text plus exported PDF character geometry. COM chart TextFrame2 is optional and may be unavailable.',
        'limits':'Does not certify raster figure internals, visual beauty, scientific correctness or actual speaking duration.'}
    write(job/'F/editorial-quality.json',result);return result
