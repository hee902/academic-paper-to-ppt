"""Portable environment inspection; no install, API request or document upload."""
import importlib.metadata,os,platform,shutil
from .common import ROOT,RUNTIME,WORKSPACE,VERSION,read,require
def doctor():
    from pathlib import Path
    from importlib.util import spec_from_file_location,module_from_spec
    spec=spec_from_file_location('portable_setup',ROOT/'scripts/setup.py');m=module_from_spec(spec);spec.loader.exec_module(m)
    info=m.inspect(RUNTIME)
    info.update(engineVersion=VERSION,packageVersion='0.1.0',skillRoot=str(ROOT),workspace=str(WORKSPACE),
        packages={n:importlib.metadata.version(n) for n in ['docling-slim','pypdfium2','python-pptx','pypdf','pywin32']},
        primaryPptxEngine='PptxGenJS 4.0.1',semanticEngine='Codex in the invoking session; no standalone model API',
        routing=read(ROOT/'config/component-routing.json'),knownLimitations=read(ROOT/'references/known-limitations.json'))
    return info
