"""Content-driven Modern Scientific Editorial layout compiler.

Scientific literals are supplied and reviewed in C/plan.json; statistical summaries
resolve structured B quantities. This module never invents a model or a dataset.
"""
import base64, html, json, math, re, shutil, sys
from pathlib import Path
from PIL import Image
from .generic_layouts import LAYOUTS as GENERIC_LAYOUTS,validate_generic,interval_data
from .common import ROOT, read, write, require, sha, command

EDITORIAL_LAYOUTS=('background','question','sample','measurement','models','comparison','figure','interval','valuation','limitations','conclusion',
 'method-summary','distribution','triangulation','china-valuation','global-valuation','limitations-audit','policy','conclusions-three',*GENERIC_LAYOUTS)
ALL_LAYOUTS=('cover','method','finding','references',*EDITORIAL_LAYOUTS)

def interval_values(slide,claims):
    block=slide.get('visual',{}).get('intervalSummary')
    if not block:return None
    require(block.get('claimId') in slide['claimIds'],'INTERVAL_SOURCE','Interval needs a cited claim.')
    claim=claims[block['claimId']];roles=block.get('quantityRoles',{})
    require(set(roles)=={'point','se','level','lower','upper'},'INTERVAL_SOURCE','Map every reported interval quantity explicitly.')
    quantities=claim.get('quantities',[])
    require(all(type(i) is int and 0<=i<len(quantities) for i in roles.values()),'INTERVAL_SOURCE','Bad interval quantity index.')
    require(len(set(roles.values()))==5,'INTERVAL_SOURCE','Do not relabel one quantity as multiple interval parameters.')
    require(all(quantities[i].get('role')==role for role,i in roles.items()),'INTERVAL_ROLE','Structured quantity roles must match the interval mapping.')
    values={k:float(quantities[i]['value']) for k,i in roles.items()}
    require(values['lower']<=values['point']<=values['upper'] and values['se']>=0 and 0<values['level']<100,'INTERVAL_VALUES','Invalid reported interval.')
    axis=block.get('axis',[min(0,math.floor(values['lower'])),max(0,math.ceil(values['upper']))])
    require(len(axis)==2 and all(isinstance(v,(int,float)) for v in axis) and axis[0]<=min(0,values['lower']) and axis[1]>=max(0,values['upper']) and axis[1]>axis[0],
        'INTERVAL_AXIS','Summary axis must include zero and every reported endpoint.')
    require(slide.get('assetId'),'INTERVAL_ORIGINAL','The interval summary supplements, and does not replace, a verified original figure.')
    return {**values,'axis':axis,'claimId':block['claimId'],'unit':block.get('unit','%')}

def validate_visual(slide,claims):
    visual=slide.get('visual',{})
    require(slide['layout'] in ALL_LAYOUTS,'LAYOUT','Unsupported editorial layout.')
    text=visual.get('text',{})
    require(isinstance(text,dict) and all(isinstance(k,str) and isinstance(v,str) for k,v in text.items()),'VISUAL_TEXT','Editorial text must be a reviewed string registry.')
    interval_values(slide,claims)
    from .editorial_final import reported_range_values
    reported_range_values(slide,claims)
    validate_generic(slide,claims)
    return list(text.values())

def source_caption(slide,analysis,pages):
    label=slide.get('visual',{}).get('text',{}).get('sourceLabel',analysis.get('paperTitle','论文'))
    locators=source_locators(slide,analysis)
    return f'来源：{label} · '+(' · '.join(locators) if locators else f'PDF p.{pages}')

def source_locators(slide,analysis):
    """Resolve concise figure/section locators only from cited B evidence."""
    claims={c['id']:c for c in analysis.get('claims',[])};evidence={e['id']:e for e in analysis.get('evidence',[])}
    cited={eid for cid in slide.get('claimIds',[]) for eid in claims[cid]['evidenceIds']}
    selected=slide.get('visual',{}).get('sourceEvidenceIds')
    if selected is not None:
        require(isinstance(selected,list) and selected and len(selected)==len(set(selected)) and all(e in cited for e in selected),
            'SOURCE_LOCATOR','Visible source locators must reference unique evidence actually cited by this slide.')
    else:selected=sorted(cited)
    figures=[];sections=[];other=[]
    for eid in selected:
        e=evidence[eid];location=e.get('location','')
        for match in re.finditer(r'(?:Fig\.?\s*|Figure\s*)(S?\d+(?:[a-z]|\([a-z]\))?(?:\s*[,–-]\s*(?:S?\d+)?[a-z])*)(?![A-Za-z0-9])',location+' '+e.get('assetId',''),re.I):
            locator='Fig. '+re.sub(r'\s*([,–-])\s*',r'\1',match[1])
            if locator not in figures:figures.append(locator)
        for match in re.finditer(r'§\s*(\d+(?:\.\d+)*)',location):
            if '§'+match[1] not in sections:sections.append('§'+match[1])
        for match in re.finditer(r'Table\s*(S?\d+|[IVX]+)(?![A-Za-z0-9])',location,re.I):
            if 'Table '+match[1] not in other:other.append('Table '+match[1])
        if not re.search(r'§\s*\d',location):
            match=re.search(r'\b(Methods|Results|Discussion|Introduction|Abstract)\b',location,re.I)
            if match and match[1].title() not in sections:sections.append(match[1].title())
    return figures+other+sections

def compile_editorial(job,analysis,plan,theme,settings):
    from .design import render_html
    require(all(s['layout'] in ALL_LAYOUTS for s in plan['slides']),'LAYOUT','Choose an editorial recipe, not an arbitrary canvas.')
    p={'paper':'F5F3EC','white':'FFFFFF','ink':'173E37','muted':'52675F','green':'2C6B59','gold':'E6CA84','dark':'102F2A','light':'B9CEC4','rule':'CBD5CE'}
    p.update(theme.get('editorialColors',{}))
    font=settings['font'] if settings['language']=='zh-CN' else settings['englishFont']
    evidence={e['id']:e for e in analysis['evidence']};claims={c['id']:c for c in analysis['claims']}
    assets=read(job/'A/assets.json');slides=[]
    for index,s in enumerate(plan['slides'],1):
        validate_visual(s,claims);f=s.get('visual',{}).get('text',{});objects=[];kind=s['layout']
        bg=p['dark'] if kind in ('method','question','method-summary','conclusions-three','scenario-matrix') else p['paper'] if kind in ('cover','background','limitations','limitations-audit','conclusion') else p['white']
        dark=bg==p['dark'];ink=p['white'] if dark else p['ink'];muted=p['light'] if dark else p['muted']
        def T(key,text,x,y,w,h,size=22,role='body',**opt):
            require(isinstance(text,str),'VISUAL_TEXT','Text not supplied for '+key)
            size=theme.get('editorialTypeScale',{}).get(str(size),size)
            if opt.get('fontFace')=='Arial':opt['fontFace']=theme.get('editorialFonts',{}).get('en','Arial')
            if opt.get('fontFace')=='Georgia':opt['fontFace']=theme.get('editorialFonts',{}).get('serif','Georgia')
            objects.append({'id':key,'type':'text','text':text,'x':x,'y':y,'w':w,'h':h,'fontSize':size,
                'minFontSize':12 if role=='caption' else 16 if role=='axis' else min(size,18 if role=='secondary' else 20),
                'role':role,'color':ink,'fontFace':font,'valign':'mid',**opt})
        def L(key,x,y,x2,y2,color=None,width=1,arrow=False):
            # Only axis-aligned lines; no decorative edge masquerades as a model.
            require(x2>=x and y2>=y,'GEOMETRY','Use ordered line endpoints.')
            objects.append({'id':key,'type':'line','x':x,'y':y,'w':x2-x,'h':y2-y,'color':color or muted,'lineWidth':width,'arrow':arrow})
        def R(key,x,y,w,h,color):objects.append({'id':key,'type':'rect','x':x,'y':y,'w':w,'h':h,'color':color})
        def D(key,x,y,r,color):objects.append({'id':key,'type':'ellipse','x':x-r,'y':y-r,'w':2*r,'h':2*r,'color':color})
        def image(asset_id,frame):
            a=assets[asset_id];path=job/a['path'];w,h=Image.open(path).size;x,y,fw,fh=frame;factor=min(fw/w,fh/h)
            objects.append({'id':'original-figure','type':'image','x':x+(fw-w*factor)/2,'y':y+(fh-h*factor)/2,'w':w*factor,'h':h*factor,
                'path':str(path.resolve()),'assetId':asset_id,'sha256':a['sha256']})
            if s.get('visual',{}).get('figureLegibility'):
                objects[-1]['legibility']=s['visual']['figureLegibility']
        def fact(key,x,y,w,h,size=22,**opts):T(key,f[key],x,y,w,h,size,**opts)
        refs=sorted({e for cid in s['claimIds'] for e in claims[cid]['evidenceIds']})
        citations=' | '.join(f'{eid}: PDF p.{evidence[eid]["page"]} ({evidence[eid].get("location", "")})' for eid in refs)
        pages=','.join(map(str,sorted({evidence[e]['page'] for e in refs})))
        T('eyebrow',f.get('eyebrow',kind.upper()),.68,.43,11.9,.25,13,'caption',fontFace='Arial',color=muted,charSpacing=1.3)
        if kind!='cover':T('title',s['title'],.66,.86 if kind=='finding' else .96,12.0,.80 if kind in ('background','question','conclusion') else .64,
                             30 if kind=='finding' else 32,'title',bold=True)
        if kind=='cover':
            fact('journal',.68,.95,8,.35,16,fontFace='Arial',color=muted)
            fact('titleLead',.64,1.99,7.7,.85,45,role='cover',bold=True)
            fact('titleMain',.61,2.84,8,1.25,64,role='cover',bold=True)
            fact('english',.70,4.27,7.5,.85,25,fontFace='Georgia',italic=True)
            if f.get('scope'):fact('scope',.70,5.27,8.1,.35,20,color=p['green'])
            R('question-field',9.24,1.95,40/3-9.24,3.9,p['ink'])
            T('question-label','RESEARCH QUESTION',9.66,2.32,3.17,.27,13,'caption',fontFace='Arial',color=p['light'],charSpacing=1.2)
            fact('researchQuestion',9.65,3.04,3.22,1.76,26,color=p['white'],bold=True)
            fact('authors',.70,5.76,8,.68,18,fontFace='Arial')
            fact('affiliations',.70,6.57,11.8,.3,14,role='caption',color=muted)
            doi=evidence.get(s['visual'].get('doiEvidence','DOI'),{}).get('quote','').split('doi.org/')[-1]
            T('sources','doi:'+doi if doi else f'来源：论文 PDF p.{pages}',.68,7.10,11.58,.24,12,'caption',color=muted)
        elif kind=='background':
            fact('lead',.76,2.02,8.85,1.18,36,bold=True)
            for i,(key,label) in enumerate([('nature','保护地'),('health','心理健康'),('value','健康服务价值')]):
                x=.78+i*4.05
                T('concept-'+key,label,x,4.25,3.6,.48,27,bold=True)
                fact(key,x,4.98,3.50,.95,22)
                if i<2:L('concept-edge-'+key,x+3.15,4.49,x+3.88,4.49,p['green'],1.7,True)
            fact('boundary',.78,6.30,11.7,.42,19,role='secondary',color=muted)
        elif kind=='question':
            fact('question',.78,2.08,10.85,1.25,39,bold=True)
            L('split',.78,3.73,12.5,3.73,'4C6C60',.8)
            fact('previous',.80,4.20,4.9,1.16,24,color=p['light'])
            T('bridge','→',6.02,4.37,.7,.6,32,fontFace='Arial',color=p['gold'])
            fact('new',7.1,4.20,5.0,1.16,24)
            fact('contribution',.80,6.10,11.4,.45,23,color=p['gold'])
        elif kind=='sample':
            T('pilot-label',f['pilotLabel'],.76,1.95,3.0,.45,24,bold=True)
            fact('pilotN',.76,2.58,3.0,.79,42,fontFace='Arial',bold=True)
            fact('pilotMeaning',.76,3.66,3.1,1.28,21,color=muted)
            L('sampling-split',4.28,2.0,4.28,6.30,p['rule'],1)
            fact('formalLabel',4.83,1.95,7.5,.43,24,bold=True)
            for i,prefix in enumerate(['park','city']):
                x=4.83+i*4.0;fact(prefix,x,2.77,3.3,.40,23)
                fact(prefix+'N',x,3.38,3.3,.90,46,fontFace='Arial',bold=True)
                fact(prefix+'Role',x,4.72,3.3,.92,21,color=muted)
            fact('warning',4.83,6.17,7.5,.42,19,role='secondary',color=muted)
        elif kind=='measurement':
            R('outcome-field',.70,1.96,4.40,4.80,p['paper'])
            T('outcome-label','结果变量',1.00,2.24,3.8,.4,21,color=muted)
            fact('outcome',1.00,2.92,3.8,.74,43,fontFace='Arial',bold=True)
            fact('transform',1.00,3.98,3.75,.55,25)
            fact('interpretation',1.00,5.16,3.75,.90,20,color=muted)
            for i,(label,key) in enumerate([('自然接触','exposure'),('锻炼','exercise'),('人口与社会经济','controls')]):
                y=2.12+i*1.43;T('label-'+key,label,5.62,y,6.65,.37,22,bold=True)
                fact(key,5.62,y+.54,6.65,.60,21,color=muted)
                if i<2:L('row-'+key,5.62,y+1.15,12.52,y+1.15,p['rule'],.7)
        elif kind=='method':
            # Unequal functional regions: prior pilot is separate from survey data;
            # measurement feeds two explicit model stages, then comparison/valuation.
            R('pilot-band',.70,1.85,3.10,1.03,'24473E')
            fact('pilotLabel',.94,2.02,1.47,.30,17,role='secondary',color=p['light'])
            fact('pilotN',2.38,2.00,1.25,.38,23,fontFace='Arial',bold=True)
            fact('pilotMeaning',.94,2.45,2.65,.25,14,role='caption',color=p['light'])
            fact('formalLabel',4.32,1.85,7.8,.29,17,role='secondary',color=p['light'])
            fact('park',4.32,2.27,3.6,.42,24,bold=True)
            fact('city',8.72,2.27,3.6,.42,24,bold=True)
            L('pilot-to-selection',3.84,2.35,4.16,2.35,p['light'],1.2,True)
            L('sample-to-measure-vertical',6.62,2.96,6.62,3.17,p['light'],1.2)
            L('sample-to-measure-horizontal',2.20,3.17,10.50,3.17,p['light'],1.2)
            L('city-to-measure-vertical',10.50,2.96,10.50,3.17,p['light'],1.2)
            L('sample-to-measure-arrow',2.20,3.17,2.20,3.40,p['light'],1.2,True)
            fact('measurement',.74,3.45,3.30,.58,26,bold=True)
            fact('covariates',.74,4.18,3.32,1.06,20,color=p['light'])
            L('measured-to-fit',3.64,3.80,4.30,3.80,p['light'],1.5,True)
            fact('regression',4.45,3.45,2.28,.53,25,bold=True)
            fact('scopes',4.45,4.21,2.30,.99,20,color=p['light'])
            L('fit-to-average',6.72,3.80,7.30,3.80,p['light'],1.5,True)
            fact('averaging',7.44,3.45,2.43,.53,25,bold=True,color=p['gold'])
            fact('averageMeaning',7.44,4.21,2.36,.99,20,color=p['light'])
            L('average-to-delta',9.66,3.80,10.19,3.80,p['light'],1.5,True)
            fact('delta',10.32,3.45,2.30,.53,25,bold=True,color=p['gold'])
            fact('deltaMeaning',10.32,4.21,2.30,.99,20,color=p['light'])
            L('delta-to-valuation',11.45,5.25,11.45,5.85,p['light'],1.2,True)
            L('valuation-separator',.74,5.67,12.56,5.67,'4C6C60',.7)
            T('valuation-label','福利估值 / 外部参数换算',.74,5.97,4.35,.40,22,bold=True)
            fact('valuation',5.26,5.97,7.30,.62,22)
            fact('warning',.74,6.70,11.9,.27,14,role='caption',color=p['light'])
        elif kind=='models':
            fact('scopes',.78,1.96,11.7,.51,25,bold=True)
            L('model-rule',.78,2.69,12.5,2.69,p['rule'],.8)
            for i,(key,label) in enumerate([('fit','回归估计'),('average','AIC模型平均')]):
                x=.80+i*6.45;T(key+'-heading',label,x,3.12,5.2,.52,30,bold=True)
                fact(key,x,4.02,5.18,1.04,24)
            T('model-arrow','→',6.10,3.20,.55,.55,31,fontFace='Arial',color=p['green'])
            fact('boundary',.80,5.80,11.6,.77,21,color=muted)
        elif kind=='comparison':
            fact('premise',.78,1.98,11.70,.60,25)
            for i,key in enumerate(['observed','counterfactual']):
                x=.80+i*6.20
                T(key+'-label',f[key+'Label'],x,3.00,5.20,.50,23,bold=True)
                fact(key,x,3.77,5.15,1.00,28)
            T('minus','−',6.25,3.85,.55,.55,35,fontFace='Arial',color=p['green'])
            L('comparison-rule',.8,5.20,12.50,5.20,p['rule'],1)
            fact('aggregate',.8,5.56,11.7,.58,28,bold=True)
            fact('warning',.8,6.40,11.7,.32,19,role='secondary',color=muted)
        elif kind=='figure':
            require(s.get('assetId'),'FIGURE_REQUIRED','Full original-figure recipe needs a source-bound image.')
            if s.get('visual',{}).get('reportedStatistic'):
                fact('summaryValue',.76,1.73,4.52,.43,29,bold=True,fontFace='Arial',color=p['green'])
                fact('summaryDefinition',5.40,1.75,7.12,.41,18,role='secondary',color=muted)
                image(s['assetId'],[.65,2.13,12.03,4.38])
            elif f.get('readingCue'):
                fact('readingCue',.76,1.73,11.86,.35,20,color=p['green'])
                image(s['assetId'],[.65,2.10,12.03,4.41])
            else:image(s['assetId'],[.72,1.90,11.90,4.70])
            large=s.get('visual',{}).get('largeReadingGuide',False)
            fact('figureGuide',.75,6.68 if large else 6.77,11.80,.40 if large else .30,18 if large else 14,role='caption',color=muted)
        elif kind=='finding':
            image(s['assetId'],[.57,1.48,7.65,5.16])
            fact('figureGuide',.70,6.79,7.77,.28,14,role='caption',color=muted)
            L('analysis-divider',8.64,1.73,8.64,6.89,p['rule'],.8)
            v=interval_values(s,claims);require(v,'INTERVAL_SOURCE','Finding recipe requires an explicit reported interval summary.')
            fact('meanLabel',8.95,1.82,3.78,.49,18,role='secondary',color=muted)
            T('point-estimate',f'{v["point"]:g}{v["unit"]}',8.91,2.28,3.88,1.20,67,bold=True,fontFace='Arial')
            T('standard-error',f'SE {v["se"]:g}{v["unit"]}',8.98,3.54,3.6,.38,22,fontFace='Arial',color=muted)
            T('confidence-text',f'{v["level"]:g}% CI {v["lower"]:g}%–{v["upper"]:g}%',8.98,4.07,3.77,.35,18.5,fontFace='Arial')
            xx=lambda x:8.95+(x-v['axis'][0])/(v['axis'][1]-v['axis'][0])*3.6
            L('ci-interval',xx(v['lower']),4.73,xx(v['upper']),4.73,p['green'],3)
            for name,val in [('lower',v['lower']),('upper',v['upper'])]:L('ci-cap-'+name,xx(val),4.64,xx(val),4.82,p['green'],2)
            D('ci-point',xx(v['point']),4.73,.065,p['ink']);L('ci-axis',xx(v['axis'][0]),5.05,xx(v['axis'][1]),5.05,p['muted'],.8)
            for i in range(math.ceil(v['axis'][0]),math.floor(v['axis'][1])+1):
                L('ci-tick-'+str(i),xx(i),5.05,xx(i),5.115,p['muted'],.8)
                T('ci-axis-value-'+str(i),str(i),xx(i)-.15,5.14,.30,.27,16,'axis',fontFace='Arial',align='center',color=muted)
            fact('axisTitle',8.98,5.51,3.7,.31,14,role='caption',color=muted)
            legend=f.get('legendPoint','点：加权均值' if '加权' in f.get('meanLabel','') else '点：点估计')
            D('legend-point',9.03,6.02,.035,p['ink']);T('legend-point-text',legend,9.16,5.88,1.49,.28,14,'caption',color=muted)
            L('legend-line',10.87,6.02,11.22,6.02,p['green'],2)
            T('legend-line-text',f'线：{v["level"]:g}% CI',11.32,5.88,1.38,.28,14,'caption',color=muted)
            fact('warning',8.98,6.34,3.75,.58,19,role='secondary',color=muted)
        elif kind=='interval':
            # Simple comparative bars: values are checked against B by validate_plan.
            fact('context',.79,1.98,11.75,.50,24)
            maximum=max(s['chart']['values']);axis_max=max(1.0,math.ceil(maximum))
            objects.append({**s['chart'],'id':'population-comparison','type':'chart','chartType':'bar','x':.90,'y':2.90,'w':11.45,'h':2.95,
                'color':p['green'],'barDir':'bar','axisMax':axis_max,'axisStep':axis_max/5,'numFmt':'0.00"%"' if s['chart']['unit']=='%' else '0.00'})
            fact('interpretation',.80,6.02,11.7,.50,23,bold=True)
            fact('warning',.80,6.66,11.7,.27,14,role='caption',color=muted)
        elif kind=='valuation':
            fact('equation',.78,2.00,11.8,.82,33,bold=True)
            # Empirical estimate and external multipliers have different evidential roles.
            for i,(label,key) in enumerate([('现场估计','empirical'),('外部输入','external')]):
                x=.82+i*6.18;T('valuation-'+key,label,x,3.38,5.35,.44,23,bold=True)
                fact(key,x,4.09,5.26,1.02,25,color=p['green'] if i==0 else muted)
            L('valuation-rule',.82,5.58,12.50,5.58,p['rule'],.8)
            fact('boundary',.82,5.94,11.65,.74,23)
        elif kind=='limitations':
            # An evidence ladder rather than three repeated warning cards.
            labels=['样本与测量','模型与解释','外推与参数']
            for i in range(3):
                y=1.98+i*1.46;T('limit-label-'+str(i),labels[i],.80,y,3.3,.44,24,bold=True)
                fact('limit'+str(i),4.30,y,8.12,.87,22)
                if i<2:L('limit-separator-'+str(i),.80,y+1.18,12.5,y+1.18,p['rule'],.7)
            fact('future',.8,6.47,11.7,.38,20,role='secondary',color=muted)
        elif kind=='references':
            for i in range(2):
                y=2.00+i*1.68;T('reference-index-'+str(i),str(i+1).zfill(2),.78,y,.72,.46,23,fontFace='Arial',color=p['green'])
                fact('reference'+str(i),1.75,y,10.70,1.22,21)
                if i==0:L('ref-rule',1.75,y+1.42,12.5,y+1.42,p['rule'],.7)
            fact('availability',.80,5.63,11.7,.56,22)
            fact('disclosure',.80,6.36,11.7,.42,18,role='secondary',color=muted)
        elif kind=='conclusion':
            fact('takehome',.80,2.10,11.65,1.24,35,bold=True)
            for i in range(2):
                L('takeaway-rule-'+str(i),.83,3.66+i*1.30,12.5,3.66+i*1.30,p['rule'],.8)
                fact('takeaway'+str(i),.83,3.99+i*1.30,11.5,.68,24)
            fact('lastline',.83,6.50,11.5,.38,21,color=p['green'])
        elif kind in GENERIC_LAYOUTS:
            from .generic_layouts import compose
            compose(s,claims,p,muted,T,L,R,D,image,fact,objects)
        else:
            from .editorial_final import compose_final
            compose_final(s,claims,p,muted,T,L,R,D,image,fact,objects)
        if kind!='cover':
            T('sources',source_caption(s,analysis,pages),.68,7.10 if kind!='distribution-analysis' else 7.18,11.58,.24,12,'caption',color=muted)
            objects[-1]['sourceLocators']=source_locators(s,analysis)
        T('page',str(index).zfill(2),12.35,7.08,.30,.25,12,'caption',fontFace='Arial',align='right',color=muted)
        slides.append({'id':s['id'],'layout':kind,'title':s['title'],'background':bg,'seconds':s['seconds'],'notes':s['notes'],
            'citations':citations,'objects':objects,'intervalSummary':interval_values(s,claims),
            'statisticalInterval':interval_data(s,claims)})
    theme={**theme,'previewWidth':1920,'previewHeight':1080}
    spec={'schemaVersion':'2.1-editorial','language':settings['language'],'font':font,'title':plan['title'],'engine':'pptxgenjs',
        'designMethodology':'baoyu-design','designSystem':'modern-scientific-editorial','theme':theme,'slides':slides,
        'planSha256':sha(job/'C/plan.json'),'analysisSha256':sha(job/'B/analysis.json'),
        'scientificReviewSha256':sha(job/'B/review.json'),'narrativeReviewSha256':sha(job/'C/review.json')}
    from .editorial_quality import policy,preflight
    spec['editorialQualityPolicy']=policy();spec['deliveryTiming']=plan.get('deliveryTiming',{})
    from .research import active
    if active(read(job/'run.json')):spec['workflowContract']='generalized-editorial-v1'
    quality=preflight(spec,settings)
    write(job/'D/editorial-quality.json',quality)
    require(quality['status']!='blocked','EDITORIAL_QUALITY','Editorial preflight: '+str(quality['findings']))
    write(job/'D/deck-spec.json',spec)
    palette=command([sys.executable,ROOT/'third_party/scientific-visualization/scripts/palette_audit.py',
        '--palette','okabe_ito_on_white','--background','FFFFFF','--role','graphical'],job/'D/scientific-palette.log')
    write(job/'D/scientific-visualization-audit.json',{'referencePaletteAudit':json.loads(palette),
        'actualPalette':p,'originalFigurePalette':'Preserved unchanged; not recoloured to theme.',
        'limits':'Reference palette CLI is advisory, not a certification of the actual slides.'})
    for attempt in range(settings['maxLayoutRepairAttempts']+1):
        render_editorial_html(job,spec)
        command(['node',ROOT/'scripts/studio_browser.cjs',job],job/f'D/browser-{attempt}.log')
        report=read(job/'D/browser-report.json')
        if not report['issues']:
            report.update(repairAttempts=attempt,specSha256=sha(job/'D/deck-spec.json'))
            write(job/'D/design-report.json',report);return spec
        require(attempt<settings['maxLayoutRepairAttempts'],'LAYOUT_BLOCKED','Editorial content overflow: revise the supported plan/recipe.')
        changes=[]
        for issue in report['issues']:
            if issue['code']!='text-overflow':continue
            o=next(o for s in slides if s['id']==issue['slideId'] for o in s['objects'] if o['id']==issue['objectId'])
            if o['fontSize']-1>=o['minFontSize']:
                changes.append({'slide':issue['slideId'],'id':o['id'],'from':o['fontSize'],'to':o['fontSize']-1});o['fontSize']-=1
        write(job/f'D/repairs-{attempt+1}.json',changes)
        require(changes,'LAYOUT_BLOCKED','No safe type adjustment; revise layout without changing science.')
        write(job/'D/deck-spec.json',spec)

def render_editorial_html(job,spec):
    ratio=1920/spec['theme']['slideWidthInches'];sizes=sorted({o['fontSize'] for s in spec['slides'] for o in s['objects'] if o['type']=='text'})
    token=lambda n:'--type-'+str(n).replace('.','p')
    css=':root{'+''.join(f'{token(n)}:{n*ratio/72}px;' for n in sizes)+'--pad-x:97.92px;--pad-top:61.92px;--pad-bottom:57.6px;--gap-item:28px;}'
    css+='body{margin:0;background:#243D32}*{box-sizing:border-box}.slide-canvas{width:100%;height:100%;position:relative}.object{position:absolute}.text{white-space:pre-wrap;display:flex;align-items:center;line-height:1.12}.arrow:after{content:"";position:absolute;right:-2px;top:-6px;border-top:6px solid transparent;border-bottom:6px solid transparent;border-left:10px solid currentColor}'
    sections=[]
    for s in spec['slides']:
        elements=[]
        for o in s['objects']:
            style=f'left:{o["x"]*ratio}px;top:{o["y"]*ratio}px;width:{o["w"]*ratio}px;height:{o["h"]*ratio}px;'
            if o['type']=='text':
                style+=f'font-family:"{o["fontFace"]}";font-size:var({token(o["fontSize"])});color:#{o["color"]};font-weight:{700 if o.get("bold") else 400};font-style:{"italic" if o.get("italic") else "normal"};letter-spacing:{o.get("charSpacing",0)*ratio/72}px;justify-content:{"flex-end" if o.get("align")=="right" else "center" if o.get("align")=="center" else "flex-start"};'
                value=html.escape(o['text']);kind='text'
            elif o['type']=='image':
                mime='image/jpeg' if Path(o['path']).suffix.lower() in ('.jpg','.jpeg') else 'image/png'
                value=f'<img alt="Original figure" src="data:{mime};base64,{base64.b64encode(Path(o["path"]).read_bytes()).decode()}" style="width:100%;height:100%;object-fit:contain">';kind='image'
            elif o['type']=='chart':
                # Same explicit source numbers as the native comparative bar chart.
                vals=o['values'];mx=o.get('axisMax',max(vals));mn=min(0,min(vals));bars=[]
                for i,(lab,val) in enumerate(zip(o['labels'],vals)):
                    row=100/max(1,len(vals));left=30+(min(0,val)-mn)/(mx-mn)*52;width=abs(val)/(mx-mn)*52
                    label=f'{val:.2f}'+('%' if o['unit']=='%' else ' '+o['unit'])
                    bars.append(f'<div style="position:absolute;left:0;top:{i*row}%;width:26%;font:36px Microsoft YaHei">{html.escape(lab)}</div><div style="position:absolute;left:{left}%;top:{i*row+4}%;height:{row*.45}%;width:{width}%;background:#{o["color"]}"></div><div style="position:absolute;left:{left+width+1}%;top:{i*row+3}%;font:38px Arial;color:#173E37">{html.escape(label)}</div>')
                value=''.join(bars);kind='chart'
            elif o['type']=='line':
                style=f'left:{o["x"]*ratio}px;top:{o["y"]*ratio}px;width:{math.hypot(o["w"],o["h"])*ratio}px;height:0;border-top:{o["lineWidth"]*ratio/72}px solid #{o["color"]};color:#{o["color"]};transform-origin:0 0;transform:rotate({math.degrees(math.atan2(o["h"],o["w"]))}deg);'
                value='';kind='line'
            else:style+=f'background:#{o["color"]};'+('border-radius:50%;' if o['type']=='ellipse' else '');value='';kind=o['type']
            elements.append(f'<div class="object {"text" if kind=="text" else "arrow" if o.get("arrow") else ""}" data-object="{o["id"]}" data-kind="{kind}" style="{html.escape(style,quote=True)}">{value}</div>')
        sections.append(f'<section data-label="{html.escape(s["title"],quote=True)}" data-slide-id="{s["id"]}"><div class="slide-canvas" style="background:#{s["background"]}">{"".join(elements)}</div></section>')
    folder=job/'D';folder.mkdir(exist_ok=True);shutil.copyfile(ROOT/'third_party/baoyu-design/starter-components/deck-stage.js',folder/'deck-stage.js')
    source=f'<!doctype html><html lang="{spec["language"]}"><meta charset="utf-8"><title>{html.escape(spec["title"])}</title><style>{css}</style><script src="deck-stage.js"></script><deck-stage width="1920" height="1080">{"".join(sections)}</deck-stage></html>'
    (folder/'deck.html').write_text(source,encoding='utf-8')
