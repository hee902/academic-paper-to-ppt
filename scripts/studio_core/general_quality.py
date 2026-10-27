"""Additional inspectable screens, never an aesthetic/scientific scoring system."""
import re,unicodedata
from collections import Counter
from pypdf import PdfReader
from .common import require,sha
from .research import CONTRACT

REVIEW_CHECKS={'percentage-layout','figure-legibility','concise-sources','delivery-timing',
    'statistical-units','density-and-rhythm','font-fidelity','html-pptx-consistency'}
PAGE_CHECKS={'layout','legibility','scientific-figures','sources','notes','font-fidelity','html-pptx-consistency'}

def screen_preflight(spec,findings):
    if spec.get('workflowContract')!=CONTRACT:return
    p=spec['editorialQualityPolicy'];fingerprints=[];families=[]
    for s in spec['slides']:
        sid=s['id'];objs=[o for o in s['objects'] if o.get('id') not in ('title','eyebrow','page','sources') and o['type'] in ('text','image','chart')]
        def issue(code,msg):findings.append({'code':code,'slideId':sid,'objectId':'content','severity':'review','message':msg})
        text=''.join(o['text'] for o in objs if o['type']=='text')
        if len(text)>p['slideTextCharacterReviewThreshold']:issue('TEXT_DENSITY','Content text exceeds character screen; review hierarchy, duplication and actual readability.')
        width=spec['theme']['slideWidthInches'];height=spec['theme']['slideHeightInches']
        cells={(x,y) for x in range(40) for y in range(24) if any(o['x']<=width*(x+.5)/40<=o['x']+o['w'] and o['y']<=height*(y+.5)/24<=o['y']+o['h'] for o in objs)}
        fraction=len(cells)/960;low,high=p['contentOccupancyReviewRange']
        if s['layout']!='cover' and not low<=fraction<=high:issue('CONTENT_OCCUPANCY',f'Content bounding areas occupy {fraction:.1%}; inspect excessive density or unmotivated empty space. This is not an ink/beauty score.')
        fingerprints.append(tuple(sorted((o['type'],*(round(o[k],1) for k in ('x','y','w','h'))) for o in objs)))
        families.append(s['layout'])
    for i in range(2,len(fingerprints)):
        if fingerprints[i] and fingerprints[i]==fingerprints[i-1]==fingerprints[i-2]:
            findings.append({'code':'MECHANICAL_GEOMETRY','slideId':spec['slides'][i]['id'],'objectId':'content','severity':'review','message':'Three consecutive pages have identical content geometry even if layout names differ; justify or vary according to the evidence.'})
    if len(families)>=8:
        kind,count=Counter(families).most_common(1)[0]
        if count/len(families)>p['dominantLayoutReviewFraction']:findings.append({'code':'DOMINANT_LAYOUT','slideId':'deck','objectId':'content','severity':'review','message':f'{kind} occupies {count}/{len(families)} pages; inspect scientific rhythm and avoid cosmetic variation.'})

def normal_font(s):return re.sub('[^a-z0-9]','',str(s).split('+')[-1].lower())

def actual_text_box(page,text,frame):
    """Nearest matching glyph sequence in the actual PDF, with whitespace removed.

    COM BoundWidth includes font side bearings on some right-aligned text. Never
    call that clipping without checking the exported glyphs themselves.
    """
    tp=page.get_textpage();flat='';indices=[]
    try:
        for i in range(tp.count_chars()):
            c=''.join(unicodedata.normalize('NFKC',tp.get_text_range(i,1)).split())
            flat+=c;indices.extend([i]*len(c))
        target=''.join(unicodedata.normalize('NFKC',text).split());start=0;candidates=[]
        if not target:return None
        while True:
            at=flat.find(target,start)
            if at<0:break
            boxes=[tp.get_charbox(i) for i in set(indices[at:at+len(target)])]
            if boxes:
                box=[min(b[0] for b in boxes),page.get_height()-max(b[3] for b in boxes),max(b[2] for b in boxes),page.get_height()-min(b[1] for b in boxes)]
                x,y,w,h=frame;candidates.append((((box[0]+box[2])/2-x-w/2)**2+((box[1]+box[3])/2-y-h/2)**2,box))
            start=at+1
        return min(candidates,key=lambda b:b[0])[1] if candidates else None
    finally:tp.close()

def screen_postflight(job,spec,export,pdf_path):
    if spec.get('workflowContract')!=CONTRACT:return [],{}
    import pypdfium2 as pdfium
    p=spec['editorialQualityPolicy'];findings=[];font_report=[];investigations=[];glyph_pdf=pdfium.PdfDocument(str(pdf_path))
    def issue(code,i,msg,severity='review'):
        findings.append({'code':code,'slideId':spec['slides'][i-1]['id'],'slide':i,'severity':severity,'message':msg})
    reader=PdfReader(pdf_path)
    for i,(s,page) in enumerate(zip(spec['slides'],reader.pages),1):
        fonts=page['/Resources'].get('/Font',{});fonts=fonts.get_object() if hasattr(fonts,'get_object') else fonts
        pdf_fonts=sorted({str(f.get_object().get('/BaseFont','')).lstrip('/') for f in fonts.values()})
        expected={o['fontFace'] for o in s['objects'] if o['type']=='text' and o['text']}
        permitted={normal_font(a) for f in expected for a in p['fontAliases'].get(f,[f])}
        # Original image internals are pixels and absent from PDF text resources.
        unexpected=[f for f in pdf_fonts if normal_font(f) not in permitted]
        if unexpected:issue('FONT_RESOURCE_REVIEW',i,'Unmapped PDF font resources: '+', '.join(unexpected)+'. Check actual Chinese/Latin glyphs and record any legitimate fallback.')
        native=next((m for m in export.get('textMetrics',[]) if m['slide']==i),{})
        byid={o['id']:o for o in s['objects']}
        for o in native.get('text',[]):
            target=byid.get(o['id'],{})
            if target.get('fontFace'):
                measured={r.get('font','') for r in o.get('fontRuns',[]) if str(r.get('text','')).strip()}
                if not measured and str(o.get('font','')).strip():measured={o['font']}
                if not measured or '' in measured:issue('FONT_UNMEASURED',i,'No reliable visible-run font measurement: '+o['id'])
                elif any(normal_font(f)!=normal_font(target['fontFace']) for f in measured):
                    issue('FONT_SUBSTITUTION',i,f'{o["id"]}: requested {target["fontFace"]}, PowerPoint visible runs report {sorted(measured)}.')
            if len(o.get('frame',[]))==4 and len(o.get('textBounds',[]))==4:
                x,y,w,h=o['frame'];a,b,c,d=o['textBounds'];tol=p['renderTextOverflowTolerancePt']
                if a<x-tol or b<y-tol or a+c>x+w+tol or b+d>y+h+tol:
                    gp=glyph_pdf[i-1]
                    try:box=actual_text_box(gp,o['text'],o['frame'])
                    finally:gp.close()
                    investigations.append({'slideId':s['id'],'objectId':o['id'],'comBounds':o['textBounds'],'frame':o['frame'],'actualPdfGlyphBox':box})
                    if box:
                        if box[0]<x-tol or box[1]<y-tol or box[2]>x+w+tol or box[3]>y+h+tol:
                            issue('TEXT_RENDER_OVERFLOW',i,'Exported PDF glyphs exceed text frame: '+o['id'],'error')
                    else:issue('TEXT_BOUNDS_UNMEASURED',i,'COM indicates overhang but the PDF text sequence could not be measured: '+o['id'])
            if o['id']=='sources' and not o.get('renderedLines',{}).get('characters'):issue('SOURCE_ROWS_UNMEASURED',i,'Source row geometry unavailable; inspect actual PNG/PDF explicitly.')
        preview=job/'D/preview'/f'slide-{i:02}.png'
        require(preview.is_file(),'HTML_PREVIEW_MISSING','Keep the paired HTML preview for actual PPTX comparison.')
        font_report.append({'slideId':s['id'],'requested':sorted(expected),'pdfResources':pdf_fonts,'htmlPreview':str(preview.relative_to(job)).replace('\\','/'),'htmlPreviewSha256':sha(preview)})
    glyph_pdf.close()
    return findings,{'fontsAndPreviewPairs':font_report,'textBoundInvestigations':investigations,'limits':'Font aliases and glyph/frame geometry screen substitution/overflow; they do not prove every glyph or HTML/PPTX visual equivalence. Inspect both images.'}
