"""Domain-neutral recipes: scientific strings and quantities come from reviewed B/C."""
import math
from .common import require
LAYOUTS=('research-flow','study-overview','evidence-matrix','argument','statistical-interval','scenario-matrix','distribution-analysis','figure-commentary')

def interval_data(slide,claims):
    b=slide.get('visual',{}).get('statisticalInterval')
    if not b:return None
    require(b.get('claimId') in slide['claimIds'],'INTERVAL_SOURCE','Cite the reported interval claim.')
    qs=claims[b['claimId']].get('quantities',[]);roles=b.get('quantityRoles',{})
    require(set(roles) in ({'point','lower','upper','level'},{'point','lower','upper','level','se'}),'INTERVAL_ROLE','Map point, reported endpoints, level and optional SE.')
    require(all(type(i)is int and 0<=i<len(qs) for i in roles.values()) and len(set(roles.values()))==len(roles),'INTERVAL_SOURCE','Invalid interval quantity mapping.')
    require(all(qs[i].get('role')==r for r,i in roles.items()),'INTERVAL_ROLE','Quantity semantic roles differ.')
    unit=b.get('unit')
    require(unit and all(qs[i]['unit']==unit for r,i in roles.items() if r!='level') and qs[roles['level']]['unit']=='%','INTERVAL_UNIT','Point, endpoints and SE need the same source unit; level is a separate percentage.')
    v={r:float(qs[i]['value']) for r,i in roles.items()}
    require(all(math.isfinite(x) for x in v.values()) and v['lower']<=v['point']<=v['upper'] and 0<v['level']<100 and v.get('se',0)>=0,'INTERVAL_VALUES','Invalid source interval.')
    require(b.get('kind') in ('confidence','credible','prediction') and b.get('axisRationale'),'INTERVAL_KIND','Declare reported interval nature and explain the axis; a reported range is not a CI.')
    axis=b.get('axis',[]);scale=b.get('scale','linear')
    require(len(axis)==2 and all(type(x) in (int,float) and math.isfinite(x) for x in axis) and axis[0]<axis[1] and axis[0]<=v['lower']<=v['upper']<=axis[1],'INTERVAL_AXIS','Explicit axis must include every endpoint.')
    require(scale in ('linear','log') and (scale!='log' or axis[0]>0),'INTERVAL_AXIS','Invalid logarithmic/linear axis.')
    require(slide.get('assetId'),'INTERVAL_ORIGINAL','Summary supplements a reviewed original figure.')
    return {**v,'unit':unit,'axis':axis,'scale':scale,'kind':b['kind'],'axisRationale':b['axisRationale']}

def validate_generic(s,claims):
    f=s.get('visual',{}).get('text',{});kind=s['layout']
    needed={'research-flow':['lead','stageA','detailA','stageB','detailB','stageC','detailC','edgeAB','edgeBC','boundary'],
        'study-overview':['context','materialLabel','material','analysisLabel','analysis','boundary'],
        'argument':['lead','premiseLabel','premise','reasoningLabel','reasoning','implication'],
        'evidence-matrix':['row1Label','row1Text','row2Label','row2Text','boundary'],
        'statistical-interval':['estimateLabel','intervalLabel','axisTitle','interpretation','boundary'],
        'scenario-matrix':['inputTitle','inputBody','modelTitle','modelBody','col0','col1','row0','row1',
            'cell00Title','cell00Body','cell01Title','cell01Body','cell10Title','cell10Body','cell11Title','cell11Body','contrastA','contrastB','output','boundary'],
        'distribution-analysis':['summaryLabel','label0','value0','label1','value1','label2','value2','figureGuide','boundary'],
        'figure-commentary':['headingA','commentA','headingB','commentB','figureGuide','boundary']}.get(kind,[])
    require(all(isinstance(f.get(k),str) and f[k].strip() for k in needed),'VISUAL_CONTENT','Provide reviewed content for '+kind+': '+', '.join(needed))
    if kind=='research-flow':require(('stageD' in f)==('detailD' in f)==('edgeCD' in f),'FLOW_RELATION','Fourth stage needs detail and a scientific edge label.')
    if kind=='evidence-matrix':
        for n in (3,4):require((f'row{n}Label' in f)==(f'row{n}Text' in f),'VISUAL_CONTENT','Evidence row needs heading and substance.')
    if kind=='statistical-interval':require(interval_data(s,claims),'INTERVAL_SOURCE','Missing statisticalInterval.')
    if kind=='distribution-analysis':require(s.get('assetId'),'FIGURE_REQUIRED','Distribution analysis retains a reviewed original distribution image.')
    if kind=='figure-commentary':require(s.get('assetId'),'FIGURE_REQUIRED','Commentary supplements a source-bound original; it is not a substitute graph.')
    if kind=='scenario-matrix':
        relations=s.get('visual',{}).get('relations',[])
        require(len(relations)==2 and {(r.get('from'),r.get('to')) for r in relations}=={('cell00','cell01'),('cell00','cell10')}
            and all(r.get('sourceClaimId') in s['claimIds'] for r in relations),'SCENARIO_RELATIONS','Explicitly cite both single-driver contrasts against the baseline; a grid is not proof of causality.')
        projection=s.get('visual',{}).get('sharedProjection')
        if projection is not None:
            require(isinstance(f.get('projectionLabel'),str) and f['projectionLabel'].strip(),'VISUAL_CONTENT','Label the scientific meaning of shared model projection.')
            require(projection.get('from')=='fitted-species-model' and set(projection.get('to',[]))=={'cell00','cell01','cell10','cell11'}
                and len(projection['to'])==4 and projection.get('sourceClaimId') in s['claimIds'],
                'SHARED_PROJECTION','A fixed species model must explicitly project to all four environmental cells.')

def compose(s,claims,p,muted,T,L,R,D,image,fact,objects):
    f=s['visual']['text'];kind=s['layout']
    if kind=='scenario-matrix':
        fact('inputTitle',.78,2.07,2.65,.97,29,bold=True)
        fact('inputBody',.78,3.26,2.67,1.16,20,color=muted)
        fact('modelTitle',.78,4.88,2.95,.48,22,bold=True,color=p['gold'])
        fact('modelBody',.78,5.58,2.95,.79,18,role='secondary',color=muted)
        if s.get('visual',{}).get('sharedProjection'):
            # The arrow points from the fitted-model area to the entire scenario field.
            # It denotes model reuse, not a causal path or independent re-fitting.
            L('shared-model-projection',3.48,4.28,4.84,4.28,p['gold'],1.8,True)
            T('shared-model-fixed',f['projectionLabel'],3.40,3.81,1.49,.30,14,'caption',color=p['gold'],align='center')
        fact('col0',5.08,2.01,3.30,.34,20,bold=True,align='center')
        fact('col1',8.83,2.01,3.55,.34,20,bold=True,align='center')
        fact('row0',3.65,3.02,1.22,.75,19,role='secondary',color=muted,align='center')
        fact('row1',3.65,4.76,1.22,.75,19,role='secondary',color=muted,align='center')
        R('scenario-field',4.98,2.58,7.51,3.41,'24473E')
        L('driver-column-divider',8.70,2.58,8.70,5.99,'4C6C60',1)
        L('driver-row-divider',4.98,4.29,12.49,4.29,'4C6C60',1)
        for row,y in [(0,2.89),(1,4.61)]:
            for col,x in [(0,5.25),(1,8.98)]:
                cell=f'cell{row}{col}'
                fact(cell+'Title',x,y,3.18,.46,24,bold=True,color=p['gold'] if cell=='cell10' else p['white'])
                fact(cell+'Body',x,y+.69,3.18,.39,19,role='secondary',color=muted)
        fact('contrastA',5.02,6.18,3.56,.31,16,role='axis',color=muted)
        fact('contrastB',8.90,6.18,3.56,.31,16,role='axis',color=p['gold'])
        fact('output',.78,6.66,11.8,.31,17,role='secondary')
        # The uncertainty boundary is in Notes and in a readable contextual label.
        fact('boundary',.78,1.78,11.75,.25,14,role='caption',color=muted)
    elif kind=='distribution-analysis':
        fact('summaryLabel',.78,1.99,2.13,.84,19,role='secondary',color=muted)
        for i,x in enumerate([3.17,6.39,9.62]):
            fact('label'+str(i),x,1.97,2.65,.34,20,align='center',color=muted)
            fact('value'+str(i),x,2.37,2.65,.61,34,bold=True,fontFace='Arial',align='center',color=p['green'] if i==2 else p['ink'])
        image(s['assetId'],[.72,3.10,11.90,3.18])
        large=s.get('visual',{}).get('largeReadingGuide',False)
        fact('figureGuide',.78,6.48,11.70,.37 if large else .31,18 if large else 14,role='caption',color=muted)
        fact('boundary',.78,6.88 if large else 6.84,11.70,.28 if large else .30,16 if large else 14,role='caption',color=muted)
    elif kind=='figure-commentary':
        image(s['assetId'],[.70,1.93,7.30,4.62])
        fact('headingA',8.39,2.16,4.13,.68,25,bold=True)
        fact('commentA',8.39,3.00,4.10,1.00,20,color=muted)
        fact('headingB',8.39,4.37,4.13,.68,25,bold=True)
        fact('commentB',8.39,5.21,4.10,1.00,20,color=muted)
        large=s.get('visual',{}).get('largeReadingGuide',False)
        fact('figureGuide',.78,6.61 if large else 6.65,7.22,.38 if large else .28,18 if large else 14,role='caption',color=muted)
        fact('boundary',8.39,6.64 if large else 6.65,4.10,.33 if large else .28,16 if large else 14,role='caption',color=muted)
    elif kind=='research-flow':
        fact('lead',.78,1.92,11.72,.65,27,bold=True)
        keys=['A','B','C']+(['D'] if 'stageD' in f else []);pos=[(.80,3.10),(7.10,3.10),(7.10,5.17),(.80,5.17)]
        for i,key in enumerate(keys):
            x,y=pos[i];fact('stage'+key,x,y,5.3,.45,26,bold=True);fact('detail'+key,x,y+.60,5.3,.66,21,color=muted)
        L('flow-AB',6.1,3.34,6.84,3.34,p['green'],1.5,True);fact('edgeAB',5.88,2.86,1.12,.30,14,role='caption',align='center',color=muted)
        L('flow-BC',9.72,4.45,9.72,4.91,p['green'],1.5,True);fact('edgeBC',10.0,4.52,2.42,.28,14,role='caption',color=muted)
        if 'D' in keys:
            T('flow-CD-direction','←',6.12,5.16,.7,.48,28,fontFace='Arial');fact('edgeCD',5.88,5.91,1.12,.28,14,role='caption',align='center',color=muted)
        fact('boundary',.80,6.68,11.7,.28,14,role='caption',color=muted)
    elif kind=='study-overview':
        fact('context',.80,2.04,11.55,.86,32,bold=True)
        fact('materialLabel',.80,3.38,3.45,.43,23,bold=True);fact('material',4.63,3.32,7.70,.93,25)
        L('study-rule',.8,4.70,12.5,4.70,p['rule'],.8)
        fact('analysisLabel',.8,5.14,3.45,.43,23,bold=True);fact('analysis',4.63,5.08,7.7,.93,25)
        fact('boundary',.8,6.56,11.65,.34,18,role='secondary',color=muted)
    elif kind=='evidence-matrix':
        rows=[n for n in range(1,5) if f'row{n}Label' in f];step=4.56/len(rows)
        for j,n in enumerate(rows):
            y=2.02+j*step;fact(f'row{n}Label',.80,y,3.10,.63,24,bold=True);fact(f'row{n}Text',4.18,y,8.12,min(step-.24,1.20),22)
            if j<len(rows)-1:L('evidence-rule-'+str(n),.8,y+step-.15,12.5,y+step-.15,p['rule'],.7)
        fact('boundary',.8,6.66,11.7,.30,16,role='axis',color=muted)
    elif kind=='argument':
        fact('lead',.80,2.04,11.4,1.22,36,bold=True)
        fact('premiseLabel',.80,3.59,3.05,.43,22,bold=True);fact('premise',4.10,3.55,8.12,.83,24)
        fact('reasoningLabel',.80,4.88,3.05,.43,22,bold=True);fact('reasoning',4.10,4.84,8.12,.83,24)
        fact('implication',.80,6.22,11.5,.64,23,color=p['green'])
    elif kind=='statistical-interval':
        image(s['assetId'],[.72,1.95,6.3,4.55]);v=interval_data(s,claims)
        fact('estimateLabel',7.58,1.99,4.91,.57,23,bold=True);T('estimate',f'{v["point"]:g} {v["unit"]}',7.55,2.81,4.94,.85,44,fontFace='Arial',bold=True)
        T('interval-label',f'{v["level"]:g}% '+f['intervalLabel']+f' {v["lower"]:g}–{v["upper"]:g} {v["unit"]}',7.58,3.85,4.9,.64,21,fontFace='Arial')
        transform=math.log if v['scale']=='log' else lambda x:x
        lo,hi=map(transform,v['axis']);xx=lambda x:7.64+(transform(x)-lo)/(hi-lo)*4.62
        L('reported-interval',xx(v['lower']),4.90,xx(v['upper']),4.90,p['green'],3)
        for name in ('lower','upper'):L('cap-'+name,xx(v[name]),4.81,xx(v[name]),4.99,p['green'],2)
        D('reported-point',xx(v['point']),4.90,.065,p['ink']);L('interval-axis',7.64,5.29,12.26,5.29,p['muted'],.8)
        for name,val in zip(('min','max'),v['axis']):T('tick-'+name,f'{val:g}',xx(val)-.32,5.42,.64,.30,16,'axis',fontFace='Arial',align='center')
        fact('axisTitle',7.60,5.94,4.9,.35,16,role='axis',color=muted)
        fact('interpretation',.80,6.54,6.35,.36,18,role='secondary');fact('boundary',7.60,6.54,4.9,.36,16,role='axis',color=muted)
