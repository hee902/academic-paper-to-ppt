// Editable native PPTX builder for the unified Skill and its compatibility test.
const fs = require('fs');
const path = require('path');
const runtime = path.resolve(process.env.ACADEMIC_PPT_RUNTIME || path.join(__dirname,'..','.runtime'));
const pptxgen = require(path.join(runtime,'node','node_modules','pptxgenjs'));

async function build(specPath, output) {
  const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
  if (['2.0','2.1-editorial'].includes(spec.schemaVersion)) return require('./studio_native.cjs').build(specPath, output);
  if (!Array.isArray(spec.slides) || spec.slides.length === 0) throw new Error('slides are required');
  const expected = spec.slideCount || 14;
  if (spec.slides.length !== expected) throw new Error(`Expected ${expected} slides, got ${spec.slides.length}`);
  const totalSeconds = spec.slides.reduce((sum,s)=>sum+(s.seconds||0),0);
  if (totalSeconds > (spec.durationMinutes||17)*60) throw new Error('Speaker timing exceeds allotted duration');
  const pptx = new pptxgen();
  pptx.layout = 'LAYOUT_WIDE';
  pptx.lang = 'zh-CN';
  pptx.author = spec.author || 'Academic Presentation Studio';
  pptx.subject = spec.title;
  pptx.title = spec.title;
  pptx.company = 'Academic Presentation Studio V2.0';
  const font = spec.font || 'Microsoft YaHei';
  pptx.theme = {headFontFace:font,bodyFontFace:font,lang:'zh-CN'};
  spec.slides.forEach((item,i)=>{
    if(!item.title || !item.notes) throw new Error(`Slide ${i+1} needs title and speaker notes`);
    const slide = pptx.addSlide();
    slide.background = {color:'FFFFFF'};
    slide.addText(item.title, {x:0.65,y:0.5,w:12.0,h:0.85,fontFace:font,fontSize:i===0?32:28,bold:true,color:'17365D',margin:0,breakLine:false});
    const bullets = item.bullets || [];
    if(bullets.length>4) throw new Error(`Too many bullets on slide ${i+1}`);
    const bodyWidth = item.chart || item.figure ? 4.1 : 11.8;
    const bodyX = item.chart || item.figure ? 8.45 : 0.7;
    bullets.forEach((t,j)=>slide.addText(t,{x:bodyX,y:1.65+j*0.78,w:bodyWidth,h:0.65,fontFace:font,fontSize:22,color:'263238',margin:0,breakLine:false}));
    if(item.chart) {
      const c=item.chart;
      if(!c.source || !c.unit) throw new Error('Chart source and unit are required');
      slide.addChart(pptx.ChartType.bar,[{name:c.unit,labels:c.labels,values:c.values}],{x:0.7,y:1.6,w:7.1,h:4.5,catAxisLabelFontFace:font,catAxisLabelFontSize:16,valAxisLabelFontFace:font,valAxisLabelFontSize:14,showLegend:false,showValue:true,showTitle:false,chartColors:['2E75B6'],showCatName:false,valAxisMinVal:0,showBorder:false});
    }
    if(item.figure) {
      const imagePath=path.resolve(path.dirname(specPath),item.figure);
      slide.addImage({path:imagePath,x:0.7,y:1.55,w:7.2,h:4.9,sizing:{type:'contain',w:7.2,h:4.9}});
    }
    const sources = item.sources || [];
    if(item.chart && !sources.includes(item.chart.source)) sources.push(item.chart.source);
    slide.addText(sources.join('；'), {x:0.7,y:6.55,w:11.7,h:0.38,fontFace:font,fontSize:11,color:'566573',margin:0});
    slide.addText(`${String(i+1).padStart(2,'0')} / ${expected}`,{x:11.8,y:7.05,w:0.9,h:0.2,fontFace:font,fontSize:10,color:'566573',margin:0,align:'right'});
    slide.addNotes(`${item.notes}\n建议讲述时间：${item.seconds||0} 秒\n来源：${sources.join('；')}`);
  });
  fs.mkdirSync(path.dirname(path.resolve(output)),{recursive:true});
  await pptx.writeFile({fileName:output});
  console.log(JSON.stringify({output,slides:expected,seconds:totalSeconds,editable:true}));
}
if(require.main===module) build(process.argv[2],process.argv[3]).catch(e=>{console.error(e.message);process.exit(1)});
module.exports={build};
