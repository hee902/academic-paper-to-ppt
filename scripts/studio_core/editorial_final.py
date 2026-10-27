"""Additional content layouts within the established editorial design system.

Reported economic ranges are explicitly different from statistical confidence
intervals. Values resolve reviewed B quantities; no range is inferred from ±.
"""
import math
from .common import require

def reported_range_values(slide,claims):
 block=slide.get('visual',{}).get('reportedRange')
 if not block:return None
 cid=block.get('claimId');require(cid in slide['claimIds'],'REPORTED_RANGE_SOURCE','Economic range must cite its source claim.')
 claim=claims[cid];roles=block.get('quantityRoles',{});quantities=claim.get('quantities',[])
 require(set(roles)=={'point','reportedHalfWidth','lower','upper'} and len(set(roles.values()))==4,
  'REPORTED_RANGE_ROLE','Map each independent reported quantity.')
 require(all(type(i)is int and 0<=i<len(quantities) and quantities[i].get('role')==role for role,i in roles.items()),
  'REPORTED_RANGE_ROLE','Range quantity roles do not match the structured source.')
 require(block.get('kind')==claim.get('uncertaintyKind')=='reported-sensitivity-component-range' and
  block.get('confidenceLevel') is None and claim.get('confidenceLevel') is None,
  'REPORTED_RANGE_NATURE','Do not label the reported economic range as a confidence interval.')
 require(block.get('unit') and all(quantities[i]['unit']==block['unit'] for i in roles.values()),'REPORTED_RANGE_UNIT','Economic range units differ.')
 values={role:float(quantities[i]['value']) for role,i in roles.items()}
 require(values['lower']<=values['point']<=values['upper'] and values['reportedHalfWidth']>=0,
  'REPORTED_RANGE_VALUES','Invalid reported range; do not silently repair inconsistent sources.')
 axis=block.get('axis');require(isinstance(axis,list) and len(axis)==2 and all(type(x)in(int,float) and math.isfinite(x) for x in axis)
  and axis[0]<=min(0,values['lower']) and axis[1]>=values['upper'] and axis[1]>axis[0],
  'REPORTED_RANGE_AXIS','Reported range axis must include zero and both original endpoints.')
 require(slide.get('assetId'),'REPORTED_RANGE_ORIGINAL','Keep the author calculation diagram alongside the range summary.')
 return {**values,'axis':axis,'unit':block['unit']}

def compose_final(s,claims,p,muted,T,L,R,D,image,fact,objects):
 kind=s['layout'];f=s['visual']['text']
 if kind=='method-summary':
  for key,x,w in [('measure',.80,3.0),('model',4.62,3.9),('predict',9.24,3.28)]:
   fact(key,x,2.05,w,.55,26,bold=True,color=p['gold'] if key=='predict' else p['white'])
   fact(key+'Detail',x,2.96,w,1.25,22,color=p['light'])
  L('measure-model',3.75,2.34,4.38,2.34,p['light'],1.5,True)
  L('model-predict',8.44,2.34,8.99,2.34,p['light'],1.5,True)
  L('method-baseline',.8,4.45,12.52,4.45,'4C6C60',.8)
  fact('difference',.80,4.80,11.70,.77,35,bold=True)
  fact('weight',.82,5.88,11.60,.52,26,color=p['gold'])
  fact('warning',.82,6.67,11.60,.28,14,role='caption',color=p['light'])
 elif kind=='distribution':
  image(s['assetId'],[2.12,1.79,9.70,4.73])
  fact('leftLabel',.80,2.35,1.32,1.55,20,color=muted)
  fact('guide',.80,6.56,11.85,.29,14,role='caption',color=muted)
  # Interpretation stays in the speaker notes, leaving the original plot dominant.
 elif kind=='triangulation':
  image(s['assetId'],[.59,1.90,7.65,4.82])
  fact('pathA',8.85,1.94,3.70,.40,22,bold=True)
  fact('formulaA',8.85,2.47,3.72,.50,22,fontFace='Arial')
  fact('pathB',8.85,3.25,3.70,.40,22,bold=True)
  fact('formulaB',8.85,3.78,3.72,.58,20)
  objects.append({**s['chart'],'id':'population-comparison','type':'chart','chartType':'bar','x':8.56,'y':4.64,'w':4.24,'h':1.58,
   'color':p['green'],'barDir':'bar','axisMax':1.2,'axisStep':.6,'numFmt':'0.00"%"','compact':True,'noWrapDataLabels':True})
  fact('figureGuide',.70,6.70,7.75,.24,12,role='caption',color=muted)
  fact('warning',8.85,6.43,3.71,.55,14,role='caption',color=muted)
 elif kind=='china-valuation':
  fact('empiricalLabel',.80,1.90,2.65,.35,18,role='secondary',color=p['green'])
  T('external-heading','外部输入（作者引用）',3.64,1.90,8.65,.35,18,'secondary',color=muted)
  slots=[('delta','deltaLabel',.80,2.05),('qaly','qalyLabel',3.62,2.80),('share','shareLabel',7.38,1.85),('population','populationLabel',10.23,2.0)]
  for key,label,x,w in slots:
   fact(key,x,2.45,w,.76,39,fontFace='Arial',bold=True)
   fact(label,x,3.40,w,.68,19,color=muted)
  for i,x in enumerate([2.91,6.63,9.47]):T('multiply-'+str(i),'×',x,2.59,.45,.48,28,fontFace='Arial',color=p['green'])
  fact('operatorLabel',.82,4.28,11.65,.48,22)
  L('valuation-rule',.82,4.97,12.52,4.97,p['rule'],.8)
  fact('value',.82,5.20,3.0,1.06,64,bold=True,fontFace='Arial')
  fact('valueUnit',3.82,5.61,3.20,.45,24)
  fact('valueMeaning',7.35,5.32,5.10,.95,22)
  fact('boundary',.82,6.66,11.65,.28,14,role='caption',color=muted)
 elif kind=='global-valuation':
  v=reported_range_values(s,claims);require(v,'REPORTED_RANGE_SOURCE','Global layout needs a source-bound range.')
  T('global-point',f'{v["point"]:g}',.80,1.95,2.50,1.15,67,bold=True,fontFace='Arial')
  T('global-plus-minus',f'±{v["reportedHalfWidth"]:.1f}',.85,3.17,3.30,.70,38,bold=True,fontFace='Arial',color=p['green'])
  fact('unit',.85,4.06,3.60,.45,24)
  fact('headlineMeaning',.85,4.68,3.60,.32,18,role='secondary',color=muted)
  image(s['assetId'],[4.75,1.75,7.85,3.41])
  fact('figureGuide',4.75,5.18,7.85,.22,12,role='caption',color=muted)
  T('reported-range-heading','正文报告范围 / 万亿美元每年',.85,5.43,11.60,.30,20)
  x=lambda a:1.12+(a-v['axis'][0])/(v['axis'][1]-v['axis'][0])*10.95
  L('global-range',x(v['lower']),6.17,x(v['upper']),6.17,p['green'],3)
  for label in ['lower','upper']:
   L('range-cap-'+label,x(v[label]),6.08,x(v[label]),6.26,p['green'],2)
   T('range-value-'+label,f'{v[label]:g}',x(v[label])-.37,5.76,.74,.25,18,'axis',fontFace='Arial',align='center')
  D('global-range-point',x(v['point']),6.17,.065,p['ink'])
  L('global-range-axis',x(v['axis'][0]),6.40,x(v['axis'][1]),6.40,muted,.8)
  for i in range(int(v['axis'][0]),int(v['axis'][1])+1,2):
   L('global-tick-'+str(i),x(i),6.40,x(i),6.465,muted,.7)
   T('global-axis-'+str(i),str(i),x(i)-.2,6.49,.40,.25,16,'axis',fontFace='Arial',align='center',color=muted)
  fact('legend',.85,6.85,11.70,.22,14,role='caption',color=muted)
  # Range nature is retained in the concise legend, the notes and full evidence.
 elif kind=='limitations-audit':
  for i,key in enumerate(['sample','model','external']):fact(key,.82,1.93+i*.73,11.65,.55,23)
  L('audit-rule',.82,4.19,12.52,4.19,p['rule'],.8)
  fact('auditTitle',.82,4.42,11.65,.43,24,bold=True)
  fact('pointLabel',.86,5.06,2.4,.32,18,role='secondary',color=muted)
  fact('rangeLabel',5.20,5.06,5.8,.32,18,role='secondary',color=muted)
  fact('point',.86,5.44,3.00,.76,42,bold=True,fontFace='Arial')
  T('not-inside','∉',4.08,5.48,.75,.69,35,fontFace='Arial',color=p['green'])
  fact('range',5.20,5.44,5.10,.76,42,bold=True,fontFace='Arial')
  fact('auditUnit',10.20,5.78,2.20,.39,18,role='secondary',color=muted)
  fact('warning',.86,6.51,11.60,.36,19,role='secondary',color=muted)
 elif kind=='policy':
  fact('leftLabel',.82,2.11,3.45,.60,26,bold=True)
  fact('centre',5.15,2.03,3.08,.75,35,bold=True,color=p['green'])
  fact('rightLabel',9.08,2.11,3.45,.60,26,bold=True)
  T('value-to-goal','→',4.34,2.18,.60,.55,32,fontFace='Arial',color=p['green'])
  T('safeguard-to-goal','←',8.32,2.18,.60,.55,32,fontFace='Arial',color=p['green'])
  fact('leftDetail',.83,3.30,4.10,1.13,24,color=muted)
  fact('rightDetail',9.10,3.30,3.45,1.13,24,color=muted)
  fact('research',.83,5.08,11.65,.65,28,bold=True)
  fact('researchDetail',.83,6.05,11.65,.48,22)
  fact('warning',.83,6.76,11.65,.25,12,role='caption',color=muted)
 elif kind=='conclusions-three':
  for i in range(3):
   y=2.04+i*1.37;fact('stat'+str(i),.83,y,3.92,.86,42,fontFace='Arial',bold=True,color=p['gold'])
   fact('meaning'+str(i),5.00,y+.03,7.42,.86,23)
  fact('discussion',.83,6.60,11.65,.35,20,color=p['light'])
 else:raise ValueError(kind)
