"""D: compile a reviewed narrative into a shared HTML/native-PPTX layout contract."""
import base64
import html
import shutil
import json
import sys
from .common import ROOT, command, read, require, sha, write
from .contracts import validate_plan, validate_science

def compile_design(job):
    analysis = validate_science(job)
    plan = validate_plan(job,analysis)
    settings = read(job/'run.json')['settings']
    theme = read(ROOT/'config/academic-theme.json')
    if plan.get('designSystem')=='modern-scientific-editorial':
        from .editorial import compile_editorial
        return compile_editorial(job,analysis,plan,theme,settings)
    font = settings['font'] if settings['language']=='zh-CN' else settings['englishFont']
    evidence = {e['id']:e for e in analysis['evidence']}
    claims = {c['id']:c for c in analysis['claims']}
    assets = read(job/'A/assets.json') if (job/'A/assets.json').exists() else {}
    slides=[]
    for index,slide in enumerate(plan['slides'],1):
        objects=[]
        def text(key, value, box, role='body'):
            objects.append({'id':key,'type':'text','text':value,'x':box[0],'y':box[1],'w':box[2],'h':box[3],
                'fontSize':theme['fontSizes'][role],'minFontSize':theme['minimumFontSizes'][role],
                'role':role,'color':theme['colors']['primary' if role in ('cover','title') else 'muted' if role=='caption' else 'text']})
        layout=slide['layout']
        text('title',slide['title'],[.7,1.45,11.9,1.9] if layout=='cover' else [.65,.5,12.0,1.08], 'cover' if layout=='cover' else 'title')
        body=slide.get('body',[])
        if layout=='cover':
            text('body','\n'.join(body),[.75,3.7,11.5,1.8])
        elif layout in ('chart','finding'):
            if layout=='chart':
                objects.append({**slide['chart'],'id':'evidence-chart','type':'chart','chartType':'bar','x':.7,'y':1.85,'w':8.0,'h':4.5})
            else:
                asset=assets[slide['assetId']]
                objects.append({'id':'original-figure','type':'image','x':.65,'y':1.7,'w':8.1,'h':4.9,
                    'path':str((job/asset['path']).resolve()),'assetId':slide['assetId'],'sha256':asset['sha256']})
            text('body','\n\n'.join(body),[9.05,2.05,3.5,3.95])
        elif layout=='statement':
            text('body','\n\n'.join(body),[.85,2.25,11.4,3.5])
        else:
            for number,value in enumerate(body):
                text(f'body-{number}',value,[.85,1.95+number*1.02,11.55,.86])
        refs=sorted({e for c in slide['claimIds'] for e in claims[c]['evidenceIds']})
        citations=' | '.join(f'{e}: PDF p.{evidence[e]["page"]}' for e in refs)
        text('sources',citations,[.65,6.72,11.6,.33],'caption')
        text('page',f'{index} / {len(plan["slides"])}',[11.6,7.05,1.05,.3],'caption')
        slides.append({'id':slide['id'],'layout':layout,'title':slide['title'],'seconds':slide['seconds'],
            'notes':slide['notes'],'citations':citations,'objects':objects})
    spec={'schemaVersion':'2.0','language':settings['language'],'font':font,'title':plan['title'],
        'engine':'pptxgenjs','designMethodology':'baoyu-design','theme':theme,'slides':slides,
        'planSha256':sha(job/'C/plan.json'),'analysisSha256':sha(job/'B/analysis.json'),
        'scientificReviewSha256':sha(job/'B/review.json'),'narrativeReviewSha256':sha(job/'C/review.json')}
    write(job/'D/deck-spec.json',spec)
    palette = command([sys.executable,ROOT/'third_party/scientific-visualization/scripts/palette_audit.py',
        '--palette','okabe_ito_on_white','--background','FFFFFF','--role','graphical'],job/'D/scientific-palette.log')
    write(job/'D/scientific-visualization-audit.json',{'paletteAudit':json.loads(palette),
        'charts':[{'slideId':s['id'],'unit':o['unit'],'values':o['values'],'uncertainty':'not-reported',
            'editable':True} for s in spec['slides'] for o in s['objects'] if o['type']=='chart'],
        'note':'Palette checks are advisory, not a scientific/accessibility certification. Reported uncertainty or unsupported chart types must use reviewed original figures.'})
    for attempt in range(settings['maxLayoutRepairAttempts']+1):
        render_html(job,spec)
        command(['node',ROOT/'scripts/studio_browser.cjs',job],job/f'D/browser-{attempt}.log')
        report=read(job/'D/browser-report.json')
        if not report['issues']:
            report['repairAttempts']=attempt
            report['specSha256']=sha(job/'D/deck-spec.json')
            write(job/'D/design-report.json',report)
            return spec
        require(attempt < settings['maxLayoutRepairAttempts'],'LAYOUT_BLOCKED','Text/geometry still overflows after bounded repair; edit the plan, not the scientific facts.')
        repaired=[]
        for issue in report['issues']:
            if issue['code']!='text-overflow': continue
            obj=next(o for s in spec['slides'] if s['id']==issue['slideId'] for o in s['objects'] if o['id']==issue['objectId'])
            new_size=max(obj['minFontSize'],obj['fontSize']-2)
            if new_size<obj['fontSize']:
                repaired.append({'slide':issue['slideId'],'object':obj['id'],'from':obj['fontSize'],'to':new_size})
                obj['fontSize']=new_size
        write(job/f'D/repairs-{attempt+1}.json',repaired)
        require(repaired,'LAYOUT_BLOCKED','No safe typography repair remains; revise the supported content/layout.')
        write(job/'D/deck-spec.json',spec)

def render_html(job,spec):
    theme=spec['theme']; ratio=theme['previewWidth']/theme['slideWidthInches']
    sections=[]
    for slide in spec['slides']:
        elements=[]
        for obj in slide['objects']:
            style=f'position:absolute;left:{obj["x"]*ratio}px;top:{obj["y"]*ratio}px;width:{obj["w"]*ratio}px;height:{obj["h"]*ratio}px;box-sizing:border-box;'
            if obj['type']=='text':
                style+=f'font-size:{obj["fontSize"]*ratio/72}px;line-height:1.22;color:#{obj["color"]};font-weight:{600 if obj["role"] in ("title","cover") else 400};white-space:pre-wrap;overflow:visible;'
                value=html.escape(obj['text'])
            elif obj['type']=='image':
                data=base64.b64encode(open(obj['path'],'rb').read()).decode()
                value=f'<img src="data:image/png;base64,{data}" style="width:100%;height:100%;object-fit:contain">'
            else:
                value=chart_preview(obj)
            elements.append(f'<div data-object="{obj["id"]}" data-kind="{obj["type"]}" style="{style}">{value}</div>')
        sections.append(f'<section data-label="{html.escape(slide["title"],quote=True)}" data-slide-id="{slide["id"]}"><div class="slide-canvas">{"".join(elements)}</div></section>')
    folder=job/'D';folder.mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'third_party/baoyu-design/starter-components/deck-stage.js',folder/'deck-stage.js')
    notes=json_dumps([s['notes'] for s in spec['slides']]).replace('</','<\\/')
    source=f'<!doctype html><html lang="{spec["language"]}"><meta charset="utf-8"><title>{html.escape(spec["title"])}</title><style>body{{margin:0;font-family:"{spec["font"]}",sans-serif;background:#E7EDF2}}.slide-canvas{{height:100%;width:100%;position:relative;background:white}}p{{margin:0}}</style><script src="deck-stage.js"></script><deck-stage width="1600" height="900">{"".join(sections)}</deck-stage><script type="application/json" id="speaker-notes">{notes}</script></html>'
    (folder/'deck.html').write_text(source,encoding='utf-8')

def json_dumps(value):
    import json
    return json.dumps(value,ensure_ascii=False)

def chart_preview(obj):
    """Data-faithful signed bars; preview only, final output is a native chart."""
    values=obj['values'];low=min(0,min(values));high=max(0,max(values));span=high-low or 1
    top,height=45,300
    y=lambda value:top+(high-value)/span*height
    baseline=y(0);step=760/len(values);bars=[]
    for i,(label,value) in enumerate(zip(obj['labels'],values)):
        x=60+step*(i+.5);end=y(value)
        bars.append(f'<rect data-value="{value}" x="{x-step*.27}" y="{min(baseline,end)}" width="{step*.54}" height="{abs(end-baseline)}" fill="#0072B2"/>')
        bars.append(f'<text x="{x}" y="{end-10 if value>=0 else end+24}" text-anchor="middle">{html.escape(str(value))}</text>')
        bars.append(f'<text x="{x}" y="395" text-anchor="middle">{html.escape(label)}</text>')
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 450" width="100%" height="100%" data-baseline="{baseline}" style="font-size:23px;font-family:inherit"><line x1="50" y1="{baseline}" x2="830" y2="{baseline}" stroke="#526575"/>{"".join(bars)}<text x="450" y="438" text-anchor="middle">{html.escape(obj["unit"])}</text></svg>'
