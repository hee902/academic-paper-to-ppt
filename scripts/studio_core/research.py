"""Source-bound research classification and content-driven, domain-neutral routing.

Classification and entailment are supplied by the invoking Codex session. The
validator checks coverage/provenance, never infers research design from keywords.
"""
from .common import ROOT,read,require,write,sha

CONTRACT='generalized-editorial-v1'
TASK_LAYOUTS={'process':'research-flow','study-overview':'study-overview',
    'evidence-matrix':'evidence-matrix','argument':'argument','statistical-interval':'statistical-interval',
    'original-figure':'figure','simple-comparison':'interval','cover':'cover','conclusion':'conclusion',
    'scenario-contrast':'scenario-matrix','distribution-analysis':'distribution-analysis',
    'figure-commentary':'figure-commentary'}
GENERIC_LAYOUTS=tuple(TASK_LAYOUTS.values())

def profiles():return read(ROOT/'config/research-profiles.json')['profiles']

def active(state):return state.get('workflowContract')==CONTRACT

def validate_research(analysis,review):
    config=profiles();d=analysis.get('researchDesign',{})
    primary=d.get('primaryType');secondary=d.get('secondaryTypes',[])
    require(primary in config and isinstance(secondary,list) and len(set(secondary))==len(secondary)
        and all(x in config and x!=primary for x in secondary),'RESEARCH_TYPE','Select source-supported primary/secondary research types; do not copy a case outline.')
    evidence={e['id'] for e in analysis['evidence']}
    refs=d.get('evidenceIds')
    require(d.get('rationale') and isinstance(refs,list) and refs and len(refs)==len(set(refs)) and set(refs)<=evidence,
        'RESEARCH_SOURCE','Explain classification using current-paper evidence.')
    require(d.get('inferenceScope') in ('descriptive','associational','causal-identification-claimed','predictive','qualitative','evidence-synthesis','theoretical'),
        'INFERENCE_SCOPE','Declare the actual scope of inference; method names do not establish causation.')
    checks=d.get('checks',{})
    for key in {k for t in [primary,*secondary] for k in config[t]['checks']}:
        item=checks.get(key,{})
        require(item.get('status') in ('reported','not-reported','not-applicable') and item.get('reason'),
            'RESEARCH_CHECK','Review applicable study-design issue: '+key)
        if item.get('status')=='reported':
            require(isinstance(item.get('evidenceIds'),list) and item['evidenceIds'] and set(item['evidenceIds'])<=evidence,'RESEARCH_SOURCE','Design check needs current evidence: '+key)
    require(review.get('researchDesignReviewed') is True,'RESEARCH_REVIEW','Classification and inference scope need substantive source-bound review.')
    return d

def resolve_layout(slide):
    if slide.get('layout')!='auto':return slide.get('layout')
    task=slide.get('visual',{}).get('task')
    require(task in TASK_LAYOUTS,'LAYOUT_TASK','Auto layout requires an explicit scientific communication task.')
    return TASK_LAYOUTS[task]

def validate_new_plan(job,analysis,plan):
    require(plan.get('designSystem')=='modern-scientific-editorial','DESIGN_SYSTEM','New runs use the accepted design system.')
    require(plan.get('researchDesignSha256')==sha(job/'B/analysis.json'),'RESEARCH_PLAN','Reconsider narrative after current-paper classification.')
    narrative=plan.get('narrative',{})
    require(narrative.get('rationale') and narrative.get('audience') and narrative.get('centralQuestion'),
        'NARRATIVE_STRATEGY','Explain audience, central question and content-dependent sequence, not a fixed chapter list.')
    route=[]
    for s in plan['slides']:
        layout=resolve_layout(s)
        require(layout in GENERIC_LAYOUTS,'CASE_LAYOUT','New papers use domain-neutral layouts; historical case recipes are compatibility-only.')
        require(s.get('layoutRationale'),'LAYOUT_RATIONALE','Explain how the layout serves the scientific content.')
        route.append({'slideId':s['id'],'task':s.get('visual',{}).get('task'),'layout':layout,'rationale':s['layoutRationale']})
    write(job/'C/layout-routing.json',{'contract':CONTRACT,'analysisSha256':sha(job/'B/analysis.json'),
        'primaryType':analysis['researchDesign']['primaryType'],'narrative':narrative,'routes':route,
        'limits':'Routing is deterministic after reviewed semantic choices; seven profiles do not imply seven real-paper acceptances.'})
    return route
