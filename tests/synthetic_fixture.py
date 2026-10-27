"""New independent synthetic source. NEVER a review generator for real papers."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from studio_core.common import ROOT,read,write,sha,require
from studio_core.research import profiles
TITLE='SYNTHETIC METHODS BENCHMARK - SOFTWARE TEST ONLY'

def make_pdf(path):
    from reportlab.pdfgen import canvas
    c=canvas.Canvas(str(path),pagesize=(720,600))
    c.setFont('Helvetica-Bold',17);c.drawString(30,563,TITLE)
    lines=['This is a technical fixture, not empirical research.',
        'Design: methodological demonstration of source-bound reporting.',
        'Procedure: inspect source, map evidence, render and inspect.',
        'Demonstration estimate: 1.40 ratio. Reported lower: 1.10 ratio.',
        'Reported upper: 1.80 ratio. Confidence level: 95%.',
        'The interval is deliberately supplied, not estimated from observations.',
        'No causal inference, population generalization or scientific finding is supported.',
        'Figure A. Known synthetic ratio interval for rendering tests.']
    c.setFont('Helvetica',13)
    for i,t in enumerate(lines):c.drawString(30,525-i*24,t)
    c.setFont('Helvetica-Bold',18);c.drawString(70,288,'Synthetic interval / ratio (not a research result)')
    x=lambda z:100+(z-1)*500
    c.setStrokeColorRGB(.17,.42,.35);c.setLineWidth(4);c.line(x(1.1),215,x(1.8),215)
    for v in (1.1,1.8):c.line(x(v),205,x(v),225)
    c.setFillColorRGB(.09,.24,.22);c.circle(x(1.4),215,6,fill=1,stroke=0)
    c.setStrokeColorRGB(.3,.3,.3);c.setLineWidth(1);c.line(100,170,600,170)
    c.setFont('Helvetica',18)
    for v in (1,1.2,1.4,1.6,1.8,2):c.drawCentredString(x(v),140,f'{v:g}')
    c.drawString(90,96,'Point: 1.40    95% confidence interval: 1.10-1.80 ratio')
    c.setFont('Helvetica',12);c.drawString(30,40,'Fixture values must never enter a real-paper presentation.')
    c.save()

def fill_known(job,variant=1):
    paper=read(job/'A/paper.json');require(TITLE in paper['pages'][0]['text'],'TEST_ONLY','This generator only accepts its known synthetic PDF.')
    quotes=[('E0','This is a technical fixture, not empirical research.'),
        ('EM','Design: methodological demonstration of source-bound reporting.'),
        ('EP','Procedure: inspect source, map evidence, render and inspect.'),
        ('EQ','Demonstration estimate: 1.40 ratio. Reported lower: 1.10 ratio.'),
        ('EU','Reported upper: 1.80 ratio. Confidence level: 95%.'),
        ('EB','No causal inference, population generalization or scientific finding is supported.')]
    evidence=[{'id':k,'page':1,'kind':'text','quote':q,'location':'Methods / technical fixture'} for k,q in quotes]
    evidence.append({'id':'EF','page':1,'kind':'figure','assetId':'SyntheticInterval','location':'Figure A / technical fixture'})
    claims=[{'id':'C0','type':'observation','text':'本材料仅用于软件测试，不包含科研结论。','evidenceIds':['E0'],'quantities':[]},
        {'id':'CM','type':'observation','text':'测试检验来源、证据映射和渲染审阅的衔接。','evidenceIds':['EM','EP','EB'],'quantities':[]},
        {'id':'CQ','type':'observation','text':'测试区间的点为1.40，端点为1.10与1.80，水平为95%。','evidenceIds':['EQ','EU','EF'],'quantities':[
            {'value':v,'unit':'%' if r=='level' else 'ratio','role':r,'evidenceId':'EU' if r in ('upper','level') else 'EQ'} for r,v in [('point',1.4),('lower',1.1),('upper',1.8),('level',95)]]}]
    sections={k:{'status':'reported','claimIds':['CM' if k=='methods' else 'CQ' if k=='results' else 'C0']} for k in ['background','question','methods','model','sample','results','conclusions','limitations']}
    for k in ['question','model','sample']:sections[k]={'status':'not-reported','reason':'Technical fixture has no empirical study, sample or estimated model.','claimIds':[]}
    design={'primaryType':'theoretical-methodological','secondaryTypes':[],'inferenceScope':'theoretical','evidenceIds':['EM'],
        'rationale':'The source explicitly identifies a methodological demonstration; classification exercises the contract, not scientific appraisal.',
        'checks':{k:{'status':'not-applicable','reason':'This software fixture is not a methodological research claim.'} for k in profiles()['theoretical-methodological']['checks']}}
    a={'paperTitle':TITLE,'sourceSha256':paper['sourceSha256'],'paperSha256':sha(job/'A/paper.json'),'evidence':evidence,'claims':claims,'sections':sections,'researchDesign':design}
    write(job/'B/analysis.json',a);asset=read(job/'A/assets.json')['SyntheticInterval']
    review={'reviewer':'Known synthetic fixture author; technical test only','analysisSha256':sha(job/'B/analysis.json'),'researchDesignReviewed':True,
        'pages':[{'page':1,'imageSha256':paper['pages'][0]['imageSha256'],'status':'reviewed','notes':'Known generated source; full page checked as a technical fixture.'}],
        'claims':[{'id':c['id'],'status':'supported','rationale':'Matches only the deliberately synthetic source; not a research result.'} for c in claims],
        'evidence':[{'id':e['id'],'status':'verified','rationale':'Known fixture literal/source checked.'} for e in evidence]}
    review['evidence'][-1].update(originalVisualChecked=True,assetSha256=asset['sha256']);write(job/'B/review.json',review)
    flow={'lead':'来源与审核记录共同约束输出','stageA':'原始文件','detailA':'完整保存并核对来源', 'stageB':'证据映射','detailB':'文字和图件绑定来源',
        'stageC':'实际渲染','detailC':'检查输出与原始内容','edgeAB':'提取','edgeBC':'生成','boundary':'软件测试材料，不包含真实科研结论'}
    matrix={'row1Label':'文字证据','row1Text':'保留原文与定位，审核后才进入页面','row2Label':'原始图件','row2Text':'保留图件字节与单位，不猜测重绘',
        'row3Label':'实际输出','row3Text':'同源HTML预览与PowerPoint结果成对审阅','boundary':'测试规则的可执行性，不评价真实研究质量'}
    interval={'estimateLabel':'已给定的测试点','intervalLabel':'CI','axisTitle':'ratio · logarithmic axis','interpretation':'已给定端点，不计算或推断新结果','boundary':'合成测试，不能用于科研汇报'}
    overview={'context':'技术材料用于检查数据传递','materialLabel':'材料来源','material':'明确标记的软件合成PDF','analysisLabel':'检查对象','analysis':'文字、原图、单位及审核记录','boundary':'不属于实际研究，也不支持经验推断'}
    argument={'lead':'技术通过不等于科学结论通过','premiseLabel':'测试前提','premise':'所有数值均由测试作者事先给定','reasoningLabel':'验证边界','reasoning':'只检验文件、证据和渲染的数据传递','implication':'真实论文仍需全文审读与领域判断'}
    def slide(id,task,title,text,refs=['CM'],asset=None):
        s={'id':id,'role':'result','layout':'auto','layoutRationale':'Choose geometry for the named communication task in this technical fixture.',
            'title':title,'body':[],'seconds':55,'claimIds':refs,'notes':'这是一份明确标记的软件测试材料。这里只检查来源、记录和输出之间的对应关系，不包含真实研究发现。',
            'visual':{'task':task,'text':{'sourceLabel':'技术测试',**text},'sourceEvidenceIds':['EF' if asset else 'EP' if refs==['CM'] else 'E0']}}
        if asset:s['assetId']=asset
        return s
    if variant==1:
        slides=[slide('flow','process','来源约束贯穿技术流程',flow),slide('matrix','evidence-matrix','不同证据保留不同审核依据',matrix),
            slide('ratio','statistical-interval','区间摘要沿用原始单位与端点',interval,['CQ'],'SyntheticInterval')]
        slides[-1]['visual']['statisticalInterval']={'claimId':'CQ','quantityRoles':{'point':0,'lower':1,'upper':2,'level':3},'unit':'ratio','axis':[1,2],
            'scale':'log','kind':'confidence','axisRationale':'Explicitly disclosed ratio log axis retains all supplied endpoints. No inferred null or new data.'}
    else:slides=[slide('overview','study-overview','材料与分析任务分别说明',overview),slide('argument','argument','审核结论保留测试边界',argument),
        slide('original','original-figure','原件保留完整坐标与单位',{'figureGuide':'Figure A · 软件合成图，仅作渲染测试'},['CQ'],'SyntheticInterval')]
    p={'title':'技术回归样张，非学术成果','language':'zh-CN','analysisSha256':sha(job/'B/analysis.json'),'researchDesignSha256':sha(job/'B/analysis.json'),
        'designSystem':'modern-scientific-editorial','narrative':{'audience':'工程验收','centralQuestion':'通用规则能否正确传递并审核新来源内容？',
            'rationale':'Select communication tasks, not the prior paper chapter sequence; this is a three-page technical probe.'},'slides':slides}
    write(job/'C/plan.json',p);write(job/'C/review.json',{'reviewer':'Known synthetic fixture author, not a scientific reviewer','planSha256':sha(job/'C/plan.json'),
        'slides':[{'id':s['id'],'status':'supported','notesChecked':True,'rationale':'Technical fixture content only, source/units and limitations retained.'} for s in slides]})
