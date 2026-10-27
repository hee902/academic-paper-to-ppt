"""PowerPoint COM equivalent of the existing PS helper; no execution-policy change."""
from pathlib import Path
import argparse
import gc
import json
import psutil
import win32com.client

def rendered_lines(text_range):
    """Read glyph rows from PowerPoint, including implicit chart-label wraps.

    Counting newline characters is insufficient: Office can wrap a percent sign
    without inserting a newline in DataLabel.Text. Keep measurement failures
    explicit rather than treating them as a one-line success.
    """
    text=text_range.Text
    chars=[]
    try:
        for i,c in enumerate(text,1):
            if c in '\r\n\v':
                chars.append({'char':c,'top':None});continue
            part=text_range.Characters(i,1)
            chars.append({'char':c,'top':round(float(part.BoundTop),2)})
        return {'characters':chars,'measurement':'PowerPoint character BoundTop; token-specific row comparison'}
    except Exception as exc:
        return {'characters':[],'measurementError':str(exc)}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('input');parser.add_argument('--output',required=True)
    parser.add_argument('--width',type=int,default=1600);parser.add_argument('--height',type=int,default=900)
    args=parser.parse_args()
    source=Path(args.input).resolve(strict=True)
    target=Path(args.output).resolve()
    if target.exists() and any(target.iterdir()):raise RuntimeError('PowerPoint export requires a fresh empty directory')
    target.mkdir(parents=True,exist_ok=True)
    had_app=any((p.info.get('name') or '').lower()=='powerpnt.exe' for p in psutil.process_iter(['name']))
    app=deck=None
    try:
        app=win32com.client.DispatchEx('PowerPoint.Application')
        deck=app.Presentations.Open(str(source),True,False,False)
        deck.SaveAs(str(target/'deck.pdf'),32)
        images=target/'slides';images.mkdir(exist_ok=True)
        metrics=[];chart_metrics=[]
        for index in range(1,deck.Slides.Count+1):
            slide=deck.Slides.Item(index)
            slide.Export(str(images/f'slide-{index:02}.png'),'PNG',args.width,args.height)
            texts=[]
            for n in range(1,slide.Shapes.Count+1):
                shape=slide.Shapes.Item(n)
                if shape.HasTextFrame and shape.TextFrame.HasText:
                    r=shape.TextFrame.TextRange
                    value={'id':shape.Name,'text':r.Text,'font':r.Font.Name,'fontSize':r.Font.Size,
                        'frame':[shape.Left,shape.Top,shape.Width,shape.Height],
                        'textBounds':[r.BoundLeft,r.BoundTop,r.BoundWidth,r.BoundHeight]}
                    if not str(value['font']).strip():
                        try:
                            value['fontRuns']=[{'text':r.Runs(k,1).Text,'font':r.Runs(k,1).Font.Name,'fontSize':r.Runs(k,1).Font.Size}
                                for k in range(1,r.Runs().Count+1)]
                        except Exception as exc:value['fontRunMeasurementError']=str(exc)
                    if '%' in r.Text or '％' in r.Text or shape.Name=='sources':value['renderedLines']=rendered_lines(r)
                    texts.append(value)
                if shape.HasChart:
                    chart=shape.Chart;series_metrics=[]
                    for sn in range(1,chart.SeriesCollection().Count+1):
                        series=chart.SeriesCollection(sn);labels=[]
                        if series.HasDataLabels:
                            for dn in range(1,series.DataLabels().Count+1):
                                label=series.DataLabels(dn);item={'index':dn,'text':label.Text}
                                try:
                                    frame=label.Format.TextFrame2;r=frame.TextRange
                                    item.update(wordWrap=frame.WordWrap,renderedLines=rendered_lines(r),
                                        bounds=[r.BoundLeft,r.BoundTop,r.BoundWidth,r.BoundHeight],fontSize=r.Font.Size)
                                except Exception as exc:item['measurementError']=str(exc)
                                labels.append(item)
                        series_metrics.append({'series':sn,'values':list(series.Values),'labels':labels})
                    chart_metrics.append({'slide':index,'id':shape.Name,'series':series_metrics})
            metrics.append({'slide':index,'text':texts})
        result={'engine':'Microsoft PowerPoint COM via Python','slides':deck.Slides.Count,'version':app.Version,
            'pdf':str(target/'deck.pdf'),'images':str(images),'pngResolution':[args.width,args.height],
            'textMetrics':metrics,'chartMetrics':chart_metrics}
        (target/'export-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps({k:v for k,v in result.items() if k not in ('textMetrics','chartMetrics')}))
    finally:
        if deck is not None:deck.Close()
        if app is not None and not had_app:app.Quit()
        deck=app=None;gc.collect()

if __name__=='__main__':main()
