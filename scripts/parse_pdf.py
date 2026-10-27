"""Local model-free Docling SDK adapter. Native PDF text is not OCR/layout recovery."""
from pathlib import Path
import argparse
import json
import os
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import NativePdfPipelineOptions
from docling.document_converter import DocumentConverter, NativePdfFormatOption

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    source=Path(args.input).resolve(strict=True)
    if source.suffix.lower()!='.pdf': parser.error('A local PDF is required')
    output=Path(args.output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    os.environ['HF_HUB_OFFLINE']='1'
    options=NativePdfPipelineOptions()
    converter=DocumentConverter(allowed_formats=[InputFormat.PDF],format_options={InputFormat.PDF:NativePdfFormatOption(pipeline_options=options)})
    result=converter.convert(source)
    document=result.document
    markdown=document.export_to_markdown()
    extracted_text='\n'.join(item.text for item in document.texts if getattr(item,'text',None))
    (output/'paper.md').write_text(markdown,encoding='utf-8')
    (output/'paper.json').write_text(json.dumps(document.export_to_dict(),ensure_ascii=False,indent=2),encoding='utf-8')
    summary={'status':str(result.status),'pipeline':'docling-native-sdk','pages':len(document.pages),'characters':len(markdown),'text_characters':len(extracted_text.strip()),'limitations':['No OCR','No recovered reading order/headings/tables','Check every scientific figure/formula against original PDF'],'source':str(source)}
    (output/'parse-result.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))
    if not extracted_text.strip() or 'success' not in str(result.status).lower(): raise SystemExit(2)

if __name__=='__main__': main()
