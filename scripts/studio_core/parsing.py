"""A: full-page source snapshots, canonical blocks and optional local MinerU OCR."""
from pathlib import Path
import json
import re
import sys
import pypdfium2 as pdfium
from .common import ROOT, RUNTIME, Blocked, check_source, command, read, require, sha, write

def prepare(job, parser='auto'):
    state = check_source(job)
    output = job/'A'
    output.mkdir(exist_ok=True)
    pdf = job/'input/paper.pdf'
    try:
        document = pdfium.PdfDocument(str(pdf))
        pages = []
        for number in range(len(document)):
            page = document[number]
            textpage = page.get_textpage()
            text = textpage.get_text_range()
            image = output/'pages'/f'page-{number+1:04}.png'
            image.parent.mkdir(exist_ok=True)
            page.render(scale=1.6).to_pil().save(image)
            pages.append({'page':number+1,'text':text,'textSource':'pdf-text-layer',
                'width':page.get_width(),'height':page.get_height(),
                'image':str(image.relative_to(job)).replace('\\','/'),'imageSha256':sha(image)})
            textpage.close(); page.close()
        document.close()
    except Exception as exc:
        raise Blocked('PDF_UNREADABLE', f'PDF cannot be read/rendered: {exc}') from exc
    require(pages, 'NO_PAGES', 'PDF contains no pages.')
    # Preserve and actually invoke the existing Docling adapter.
    docling_error = None
    try:
        command([sys.executable,ROOT/'scripts/parse_pdf.py',pdf,'--output',output/'docling'],output/'docling.log',timeout=300)
    except Blocked as exc:
        docling_error = exc.message
    missing = [p['page'] for p in pages if len(re.sub(r'\s','',p['text'])) < 20]
    blocks = []
    if (output/'docling/paper.json').is_file():
        raw = read(output/'docling/paper.json')
        for index, item in enumerate(raw.get('texts', []),1):
            for prov in item.get('prov', []):
                blocks.append({'id':f'D{index}-p{prov["page_no"]}','page':prov['page_no'],
                    'text':item.get('text',''),'label':item.get('label'),'bbox':prov.get('bbox'),
                    'source':'docling-native','readingOrderVerified':False})
    mineru = None
    if parser == 'mineru-basic' or (parser == 'auto' and missing):
        mineru = _mineru(job, len(pages))
        content = mineru['content']
        # One page per request preserves page provenance; no regex guess of page boundaries.
        for page in pages:
            if page['page'] in content:
                page['text'] = content[page['page']]['content']['content']
                page['textSource'] = 'mineru-basic-ocr-unverified'
                page['locator'] = content[page['page']]['content'].get('content_ranges',[])
                blocks.append({'id':f'M-p{page["page"]}','page':page['page'],'text':page['text'],
                    'source':'mineru-basic','readingOrderVerified':False})
    empty = [p['page'] for p in pages if len(re.sub(r'\s','',p['text'])) < 20]
    paper = {'schemaVersion':'2.0','sourceSha256':state['source']['sha256'],
        'pageCount':len(pages),'pages':pages,'blocks':blocks,
        'parser':parser,'allPagesExtracted':not empty,
        'limitations':['Native reading order/tables/formulas are unverified.',
            'MinerU basic has a recorded born-digital table-column fidelity failure.',
            'Every source page and every table/formula/figure must be visually reviewed.'],
        'doclingError':docling_error,'emptyPages':empty}
    write(output/'paper.json', paper)
    (output/'paper.md').write_text('\n\n'.join(f'<!-- PDF page {p["page"]} -->\n\n{p["text"]}' for p in pages),encoding='utf-8')
    write(output/'parse-report.json',{'pages':len(pages),'emptyPages':empty,'paperSha256':sha(output/'paper.json'),
        'status':'blocked' if empty else 'awaiting-scientific-review','doclingError':docling_error,
        'parserSources':sorted({p['textSource'] for p in pages})})
    require(not empty, 'UNREADABLE_PAGES', f'No trustworthy text on PDF pages {empty}; local OCR or manual transcription review is required.')
    require(not (docling_error and not mineru), 'DOCLING_FAILED', docling_error or '')
    return paper

def _mineru(job, count):
    # Local configuration/models already installed. Never download or add --remote.
    import os
    executable=Path(os.environ.get('ACADEMIC_PPT_MINERU',''))
    require(os.environ.get('ACADEMIC_PPT_ENABLE_MINERU')=='1' and executable.is_file(), 'OCR_NOT_CONFIGURED', 'Scanned/unreadable PDF: local OCR is not configured. See INSTALLATION.md; no remote upload or automatic model download.')
    prefix = [executable]
    overrides={'MINERU_HOME':str(RUNTIME/'cache/mineru'),'HF_HOME':str(RUNTIME/'cache/huggingface-mineru'),
        'MODELSCOPE_CACHE':str(RUNTIME/'cache/modelscope')}
    def invoke(args,log,timeout=180):return command(prefix+args,log,timeout=timeout,overrides=overrides)
    status = json.loads(invoke(['server','status','--json'],job/'A/mineru-status.log'))
    owned = not status.get('running')
    if owned:
        invoke(['server','start'],job/'A/mineru-start.log')
    result = {}
    try:
        invoke(['telemetry','disable'],job/'A/mineru-telemetry.log')
        for page in range(1,count+1):
            raw = invoke(['parse',job/'input/paper.pdf','--tier','basic','--pages',str(page),
                '--wait','180','--json'],job/f'A/mineru-page-{page:04}.log',timeout=240)
            parsed = json.loads(raw)
            write(job/f'A/mineru/page-{page:04}.json',parsed)
            require(parsed.get('parse',{}).get('status') == 'done' and parsed.get('content') is not None,
                    'MINERU_FAILED', f'Local basic parsing did not finish on page {page}.')
            require(not parsed['content'].get('truncated') and parsed['content'].get('next_request') is None,
                    'MINERU_TRUNCATED', f'Page {page} needs continuation; no partial-page reading is accepted.')
            result[page] = parsed
    finally:
        if owned:
            # Only stop the instance started for this invocation.
            invoke(['server','stop'],job/'A/mineru-stop.log')
    return {'content':result}

def crop(job, asset_id, page_no, bbox, scale=None):
    from PIL import Image
    check_source(job)
    require(re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,63}',asset_id), 'ASSET_ID', 'Use a stable alphanumeric asset ID.')
    paper = read(job/'A/paper.json')
    require(1 <= page_no <= paper['pageCount'], 'SOURCE_PAGE', 'Crop page does not exist.')
    require(len(bbox)==4 and 0 <= bbox[0] < bbox[2] <= 1 and 0 <= bbox[1] < bbox[3] <= 1,
            'SOURCE_BBOX','bbox must be normalized left, top, right, bottom in [0,1].')
    page = paper['pages'][page_no-1]
    require(scale is None or (type(scale) in (int,float) and 1.6<=scale<=6),'CROP_SCALE','Optional PDF source render scale must be 1.6–6; never upscale a raster to invent detail.')
    if scale is not None:
        document=pdfium.PdfDocument(str(job/'input/paper.pdf'));source_page=document[page_no-1]
        image=source_page.render(scale=scale).to_pil()
    else:image=Image.open(job/page['image'])
    try:
        w,h = image.size
        result = image.crop((round(bbox[0]*w),round(bbox[1]*h),round(bbox[2]*w),round(bbox[3]*h)))
        target = job/f'A/assets/{asset_id}.png'
        target.parent.mkdir(exist_ok=True)
        result.save(target)
    finally:
        image.close()
        if scale is not None:source_page.close();document.close()
    manifest = read(job/'A/assets.json') if (job/'A/assets.json').exists() else {}
    manifest[asset_id] = {'page':page_no,'bbox':bbox,'path':str(target.relative_to(job)).replace('\\','/'),
        'sha256':sha(target),'sourcePageImageSha256':page['imageSha256']}
    if scale is not None:manifest[asset_id].update(renderScale=scale,pixelSize=list(result.size),method='Direct original-PDF render and crop; no raster upscaling, recolouring or scientific reconstruction')
    write(job/'A/assets.json',manifest)
    return manifest[asset_id]
