// Local HTML design verification. No outside requests and no user browser profile.
const fs=require('fs'),path=require('path'),http=require('http');
const {spawn}=require('child_process');
const root=path.resolve(__dirname,'..'),job=path.resolve(process.argv[2]);
// Browser cache is explicitly configured by the portable launcher.
// Use the already-tested browser/client pair from Baoyu's pinned lockfile.
// The root Playwright version expects a different browser revision.
const runtime=path.resolve(process.env.ACADEMIC_PPT_RUNTIME||path.join(root,'.runtime'));
const {chromium}=require(path.join(runtime,'node/node_modules/playwright'));
async function main(){
  const spec=JSON.parse(fs.readFileSync(path.join(job,'D/deck-spec.json'),'utf8'));
  const server=http.createServer((req,res)=>{
    const file=path.resolve(job,'.'+decodeURIComponent(req.url.split('?')[0]));
    if(!file.startsWith(job+path.sep)){res.writeHead(403);res.end();return}
    fs.readFile(file,(err,data)=>{if(err){res.writeHead(404);res.end();return}res.setHeader('Content-Type',file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.js')?'text/javascript':'application/octet-stream');res.end(data)});
  });
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  const origin=`http://127.0.0.1:${server.address().port}`;let browser;
  const report={engine:'Chromium DOM preflight',issues:[],slides:[],externalRequests:[],limits:'HTML preflight does not replace inspection of PowerPoint-rendered images.'};
  try{
    browser=await chromium.launch({headless:true});
    const context=await browser.newContext({viewport:{width:spec.theme.previewWidth,height:spec.theme.previewHeight}});
    await context.route('**/*',route=>{const u=route.request().url();if(u.startsWith(origin)||u.startsWith('data:'))return route.continue();report.externalRequests.push(u);return route.abort()});
    const page=await context.newPage();
    page.on('pageerror',e=>report.issues.push({code:'browser-error',message:e.message}));
    await page.goto(origin+'/D/deck.html',{waitUntil:'networkidle'});
    await page.evaluate(()=>document.fonts.ready);
    await page.evaluate(()=>document.querySelector('deck-stage').shadowRoot.querySelectorAll('.overlay,.rail,.tap-zone').forEach(n=>n.style.display='none'));
    fs.mkdirSync(path.join(job,'D/preview'),{recursive:true});
    for(let i=0;i<spec.slides.length;i++){
      await page.evaluate(n=>document.querySelector('deck-stage').goTo(n),i);
      await page.waitForTimeout(100);
      const item=await page.evaluate(id=>{
        const slide=document.querySelector(`[data-slide-id="${id}"]`);
        return {id,objects:[...slide.querySelectorAll('[data-object]')].map(el=>({id:el.dataset.object,kind:el.dataset.kind,
          computedColor:getComputedStyle(el).color,computedFontSize:parseFloat(getComputedStyle(el).fontSize),
          overflow:el.dataset.kind==='text'&&(el.scrollWidth>el.clientWidth+2||el.scrollHeight>el.clientHeight+2),
          text:el.textContent,scrollWidth:el.scrollWidth,width:el.clientWidth,scrollHeight:el.scrollHeight,height:el.clientHeight}))};
      },spec.slides[i].id);
      for(const o of item.objects)if(o.overflow)report.issues.push({code:'text-overflow',slideId:item.id,objectId:o.id,...o});
      if(spec.workflowContract==='generalized-editorial-v1')for(const o of item.objects.filter(o=>o.kind==='text')){
        const target=spec.slides[i].objects.find(t=>t.id===o.id),ratio=1920/spec.theme.slideWidthInches;
        const rgb=target.color.match(/../g).map(c=>parseInt(c,16)),expectedColor=`rgb(${rgb.join(', ')})`;
        if(o.computedColor!==expectedColor||Math.abs(o.computedFontSize-target.fontSize*ratio/72)>.1)
          report.issues.push({code:'text-style-mismatch',slideId:item.id,objectId:o.id,expectedColor,...o});
      }
      report.slides.push(item);
      await page.locator('deck-stage > section').nth(i).screenshot({path:path.join(job,'D/preview',`slide-${String(i+1).padStart(2,'0')}.png`)});
    }
    if(process.argv.includes('--probe-baoyu'))throw new Error('Optional Baoyu exporter is not bundled; production PptxGenJS remains available.');
  }finally{if(browser)await browser.close();await new Promise(resolve=>server.close(resolve))}
  fs.writeFileSync(path.join(job,'D/browser-report.json'),JSON.stringify(report,null,2));
}
main().catch(e=>{console.error(e);process.exitCode=1});
