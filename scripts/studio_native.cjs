// The only production PPTX authoring engine: native PptxGenJS.
const fs=require('fs'),path=require('path');
const runtime=path.resolve(process.env.ACADEMIC_PPT_RUNTIME||path.join(__dirname,'..','.runtime'));
const modules=path.join(runtime,'node','node_modules');
const pptxgen=require(path.join(modules,'pptxgenjs'));
async function build(specPath,output){
  const spec=JSON.parse(fs.readFileSync(specPath,'utf8'));
  const pptx=new pptxgen();pptx.layout='LAYOUT_WIDE';pptx.lang=spec.language;
  pptx.title=spec.title;pptx.author='Academic Presentation Studio';
  pptx.theme={headFontFace:spec.font,bodyFontFace:spec.font,lang:spec.language};
  let chartNumber=0;const noWrapCharts=[];
  for(const item of spec.slides){
    const slide=pptx.addSlide();slide.background={color:item.background||'FFFFFF'};
    for(const obj of item.objects){
      const box={x:obj.x,y:obj.y,w:obj.w,h:obj.h};
      if(obj.type==='text')slide.addText(obj.text,{...box,fontFace:obj.fontFace||spec.font,fontSize:obj.fontSize,
        color:obj.color,bold:obj.bold??['title','cover'].includes(obj.role),italic:!!obj.italic,align:obj.align||'left',
        margin:0,breakLine:false,paraSpaceAfterPt:0,objectName:obj.id,isTextBox:true,
        valign:obj.valign||'top',charSpacing:obj.charSpacing||0,lineSpacingMultiple:1.15});
      else if(obj.type==='image')slide.addImage({path:obj.path,...box,objectName:obj.id,sizing:{type:'contain',w:obj.w,h:obj.h}});
      else if(obj.type==='chart'){
       chartNumber++;
       if(obj.noWrapDataLabels||obj.unit==='%'||(obj.numFmt||'').includes('%'))noWrapCharts.push(chartNumber);
       slide.addChart(pptx.ChartType.bar,[{name:obj.unit,labels:obj.labels,values:obj.values}],{
        ...box,chartColors:[obj.color||'0072B2'],showLegend:false,showValue:true,showTitle:false,objectName:obj.id,
        barDir:obj.barDir||'col',
        catAxisLabelFontFace:spec.font,catAxisLabelFontSize:obj.compact?16:obj.barDir==='bar'?20:18,valAxisLabelFontFace:spec.font,valAxisLabelFontSize:obj.barDir==='bar'?16:14,
        valAxisMinVal:Math.min(0,...obj.values),valAxisMaxVal:obj.axisMax,valAxisMajorUnit:obj.axisStep,
        valAxisLabelFormatCode:obj.numFmt||'General',
        showValAxisTitle:!obj.compact,valAxisTitle:obj.unit,valAxisTitleFontSize:14,
        valGridLine:{color:'CBD5CE',width:0.5},
        showBorder:false,showCatName:false,showCatAxisTitle:false,
        dataLabelPosition:'outEnd',dataLabelFontFace:obj.compact?'Arial':undefined,dataLabelColor:'173E37',dataLabelFontSize:obj.compact?18:obj.barDir==='bar'?22:18,dataLabelFormatCode:obj.numFmt||'General'});
      }
      else if(['rect','ellipse','line'].includes(obj.type))slide.addShape(pptx.ShapeType[obj.type],{...box,objectName:obj.id,
        fill:obj.type==='line'?undefined:{color:obj.color},line:{color:obj.color,width:obj.lineWidth||0,
        transparency:obj.type==='line'?0:100,endArrowType:obj.arrow?'triangle':'none'}});
      else throw new Error(`Unsupported native object ${obj.type}`);
    }
    slide.addNotes(`${item.notes}\n\n[Sources] ${item.citations}\n[Planned seconds] ${item.seconds}`);
  }
  fs.mkdirSync(path.dirname(path.resolve(output)),{recursive:true});
  await pptx.writeFile({fileName:output});
  if(noWrapCharts.length){
    // PptxGenJS 4.0.1 has no data-label wrapping option. Normalize only the
    // chart label text-body property, preserving all series/workbook values.
    const JSZip=require(path.join(modules,'jszip')),zip=await JSZip.loadAsync(fs.readFileSync(output));
    for(const number of noWrapCharts){
      const name=`ppt/charts/chart${number}.xml`,entry=zip.file(name);
      if(!entry)throw new Error(`Missing generated native chart ${number}`);
      const original=await entry.async('string');let count=0;
      const updated=original.replace(/<c:dLbls>[\s\S]*?<\/c:dLbls>/g,block=>block.replace(/<a:bodyPr\s*\/>/g,()=>{
        count++;return '<a:bodyPr wrap="none" vertOverflow="overflow" horzOverflow="overflow"/>';
      }));
      if(!count)throw new Error(`No native label text-body normalized for chart ${number}`);
      zip.file(name,updated);
    }
    fs.writeFileSync(output,await zip.generateAsync({type:'nodebuffer',compression:'DEFLATE'}));
  }
  console.log(JSON.stringify({engine:'PptxGenJS',slides:spec.slides.length,output}));
}
if(require.main===module)build(process.argv[2],process.argv[3]).catch(e=>{console.error(e);process.exit(1)});
module.exports={build};
