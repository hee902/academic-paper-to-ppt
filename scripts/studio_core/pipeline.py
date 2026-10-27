import argparse
import json
from pathlib import Path
from .common import ROOT, VERSION, Blocked, check_source, command, job_path, new_run, read, record, require, sha, write
from .parsing import crop, prepare
from .contracts import SECTIONS, validate_plan, validate_science
from .design import compile_design
from .quality import build, finalize, qa

STAGES={'prepare':('A',prepare),'check-evidence':('B',validate_science),'check-plan':('C',validate_plan),
    'design':('D',compile_design),'build':('E',build),'qa':('F',qa),'finalize':('F',finalize)}

def scaffolds(job):
    paper=read(job/'A/paper.json')
    write(job/'B/analysis.template.json',{'sourceSha256':paper['sourceSha256'],'paperSha256':sha(job/'A/paper.json'),
        'researchDesign':{'primaryType':'','secondaryTypes':[],'inferenceScope':'','rationale':'','evidenceIds':[],'checks':{}},
        'paperTitle':'','sections':{k:{'status':'not-reported','reason':'Pending full-paper review','claimIds':[]} for k in SECTIONS},
        'evidence':[],'claims':[]})
    (job/'agent-task.md').write_text('# Continue this run with $academic-paper-to-ppt\n\n'+
        'Read all A/paper.md and all original A/pages images. Write B/analysis.json with source-located evidence and claims; never infer missing statistics. '+
        'Read bundled third_party/scientific-critical-thinking/guide.md, references/contracts.md and references/research-routing.md. '+
        'Classify the actual design from evidence; select narrative and layout:auto tasks for this paper, not an earlier case outline. '+
        'Then record the actual B/review.json, write C/plan.json and C/review.json using bundled third_party/scientific-slides/guide.md. '+
        'Run scripts/studio.py resume on this directory. Review every actual PowerPoint render, write F/visual-review.json, then finalize. '+
        'Templates do not grant approval. No standalone LLM API is configured: Codex supplies semantic work in this chat.\n',encoding='utf-8')

def review_template(job,kind):
    if kind=='science':
        paper=read(job/'A/paper.json');analysis=read(job/'B/analysis.json')
        value={'reviewer':'','analysisSha256':sha(job/'B/analysis.json'),
            'pages':[{'page':p['page'],'imageSha256':p['imageSha256'],'status':'pending','notes':''} for p in paper['pages']],
            'evidence':[{'id':e['id'],'status':'pending','rationale':''} for e in analysis['evidence']],
            'claims':[{'id':c['id'],'status':'pending','rationale':''} for c in analysis['claims']], 'researchDesignReviewed':False}
        target=job/'B/review.template.json'
    else:
        plan=read(job/'C/plan.json')
        value={'reviewer':'','planSha256':sha(job/'C/plan.json'),'slides':[{'id':s['id'],'status':'pending','notesChecked':False,'rationale':''} for s in plan['slides']]}
        target=job/'C/review.template.json'
    write(target,value)
    return target

def execute(job,action,args=None):
    stage,function=STAGES[action]
    try:
        result=function(job,parser=args.parser) if action=='prepare' else function(job)
        status='complete' if action=='finalize' else 'awaiting-visual-review' if action=='qa' else 'passed'
        record(job,stage,status,{'action':action})
        if action=='prepare':scaffolds(job)
        return result
    except Blocked as exc:
        record(job,stage,'blocked',{'action':action,'code':exc.code,'message':exc.message})
        raise

def resume(job):
    check_source(job)
    for paths,stage in [(['B/analysis.json','B/review.json'],'B'),(['C/plan.json','C/review.json'],'C')]:
        missing=[p for p in paths if not (job/p).is_file()]
        if missing:
            record(job,stage,'awaiting-codex',{'missing':missing})
            return {'status':'awaiting-codex','run':str(job),'missing':missing,'task':str(job/'agent-task.md')},3
    execute(job,'check-evidence');execute(job,'check-plan')
    execute(job,'design');execute(job,'build');execute(job,'qa')
    return {'status':'awaiting-visual-review','run':str(job),'template':str(job/'F/visual-review.template.json')},3

def main(argv=None):
    parser=argparse.ArgumentParser(description='Academic Presentation Studio A-F workflow; semantic stages run in Codex, not an unconfigured paid API.')
    sub=parser.add_subparsers(dest='action',required=True)
    run=sub.add_parser('run');run.add_argument('pdf');run.add_argument('--slides',type=int);run.add_argument('--minutes',type=int)
    run.add_argument('--language',choices=['zh-CN','en-US']);run.add_argument('--purpose',choices=['production','integration-test','visual-prototype'],default='production')
    run.add_argument('--parser',choices=['auto','docling-native','mineru-basic'],default=None)
    branch=sub.add_parser('branch',help='New run reusing a hash-verified reviewed extraction; does not reparse or modify the parent')
    branch.add_argument('parent');branch.add_argument('--purpose',choices=['production','visual-prototype'],default='production')
    branch.add_argument('--slides',type=int);branch.add_argument('--minutes',type=int)
    for action in STAGES:
        p=sub.add_parser(action);p.add_argument('run')
        if action=='prepare':p.add_argument('--parser',choices=['auto','docling-native','mineru-basic'],default='auto')
    for action in ('resume','status','review-template','probe-baoyu'):
        p=sub.add_parser(action);p.add_argument('run')
        if action=='review-template':p.add_argument('--kind',choices=['science','narrative'],required=True)
    p=sub.add_parser('crop');p.add_argument('run');p.add_argument('--id',required=True);p.add_argument('--page',type=int,required=True);p.add_argument('--bbox',type=float,nargs=4,required=True);p.add_argument('--scale',type=float)
    sub.add_parser('doctor')
    args=parser.parse_args(argv)
    job=None
    try:
        if args.action=='doctor':
            from .portable import doctor
            output=doctor()
        elif args.action=='branch':
            import shutil
            parent=job_path(args.parent);check_source(parent)
            settings=read(ROOT/'config/presentation-defaults.json');settings['purpose']=args.purpose
            for k,v in [('slideCount',args.slides),('durationMinutes',args.minutes)]:
                if v is not None:settings[k]=v
            if args.purpose=='production':
                require(settings['productionSlideRange'][0]<=settings['slideCount']<=settings['productionSlideRange'][1], 'SLIDE_RANGE','Production target is 12–16 slides.')
                require(settings['productionMinuteRange'][0]<=settings['durationMinutes']<=settings['productionMinuteRange'][1], 'DURATION_RANGE','Production target is 15–20 minutes.')
            else:require(1<=settings['slideCount']<=3 and 1<=settings['durationMinutes']<=20,'TEST_SCOPE','Prototype needs at most three slides.')
            job=new_run(parent/'input/paper.pdf',settings)
            for folder in ['A','B']:shutil.copytree(parent/folder,job/folder)
            validate_science(job,research_required=False)
            write(job/'lineage.json',{'parentRun':str(parent),'reusedFiles':{f:sha(job/f) for f in ['input/paper.pdf','A/paper.json','B/analysis.json','B/review.json']},
                'noReparse':True,'scope':'A/B source-bound review reused; C and visual review must be supplied for this new run.'})
            record(job,'A','reused-reviewed-snapshot',{'parent':str(parent)});record(job,'B','passed',{'reusedReview':True})
            output={'status':'awaiting-codex','run':str(job),'next':'Review/add B.researchDesign for the new contract, then write/review a current-paper C plan; no reparse. Rebind B review after any change.'}
            print(json.dumps(output,ensure_ascii=False));return 3
        elif args.action=='run':
            settings=read(ROOT/'config/presentation-defaults.json');settings['purpose']=args.purpose
            for k,v in [('slideCount',args.slides),('durationMinutes',args.minutes),('language',args.language),('parser',args.parser)]:
                if v is not None:settings[k]=v
            if args.purpose=='production':
                require(settings['productionSlideRange'][0]<=settings['slideCount']<=settings['productionSlideRange'][1], 'SLIDE_RANGE','Production target is 12–16 slides.')
                require(settings['productionMinuteRange'][0]<=settings['durationMinutes']<=settings['productionMinuteRange'][1], 'DURATION_RANGE','Production target is 15–20 minutes.')
            else:
                require(1<=settings['slideCount']<=3,'TEST_SCOPE','Integration tests and visual prototypes are limited to three slides.')
                require(1<=settings['durationMinutes']<=20,'DURATION_RANGE','A test/prototype needs a positive duration of at most 20 minutes.')
            job=new_run(args.pdf,settings);args.parser=settings['parser'];execute(job,'prepare',args)
            output,code=resume(job)
            print(json.dumps(output,ensure_ascii=False));return code
        else:
            job=job_path(args.run)
            require(read(job/'run.json')['status']!='complete' or args.action=='status','IMMUTABLE_RUN','Finalized runs are immutable; create a new run.')
            if args.action=='resume':
                output,code=resume(job);print(json.dumps(output,ensure_ascii=False));return code
            if args.action=='status':
                check_source(job);output=read(job/'run.json')
                if output['status']=='complete':
                    manifest=read(job/'deliverables/manifest.json')
                    require(all((job/'deliverables'/p).is_file() and sha(job/'deliverables'/p)==digest for p,digest in manifest['files'].items()),
                        'DELIVERY_CHANGED','A finalized deliverable changed; do not treat it as the verified snapshot.')
            elif args.action=='probe-baoyu':
                command(['node',ROOT/'scripts/studio_browser.cjs',job,'--probe-baoyu'],job/'D/baoyu-probe.log')
                output=read(job/'D/baoyu-probe.json')
            elif args.action=='review-template':output={'template':str(review_template(job,args.kind))}
            elif args.action=='crop':output=crop(job,args.id,args.page,args.bbox,args.scale)
            else:
                execute(job,args.action,args)
                output={'status':'complete' if args.action=='finalize' else 'awaiting-visual-review' if args.action=='qa' else 'passed','action':args.action,'run':str(job)}
        print(json.dumps(output,ensure_ascii=False));return 0
    except Blocked as exc:
        output={'status':'blocked','code':exc.code,'message':exc.message,'run':str(job) if job else None}
        print(json.dumps(output,ensure_ascii=False));return 2
    except (ValueError,KeyError,TypeError,IndexError,OSError) as exc:
        if job:record(job,'contract','blocked',{'code':'MALFORMED_ARTIFACT','message':str(exc)})
        print(json.dumps({'status':'blocked','code':'MALFORMED_ARTIFACT','message':str(exc),'run':str(job) if job else None},ensure_ascii=False));return 2
