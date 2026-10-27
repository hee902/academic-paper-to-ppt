"""Bootstrap the package-local runtime; scientific/visual review stays in Codex."""
import os,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
runtime=Path(os.environ.get('ACADEMIC_PPT_RUNTIME',str(root/'.runtime'))).expanduser().resolve()
python=runtime/'venv/Scripts/python.exe'
if not python.is_file():
    print('Local runtime missing. Run Python 3.12 scripts/setup.py --check, then --install --allow-downloads after reviewing INSTALLATION.md.')
    raise SystemExit(2)
if Path(sys.prefix).resolve()!=(runtime/'venv').resolve():
    env=os.environ.copy();env.pop('PYTHONPATH',None);env['PYTHONNOUSERSITE']='1'
    raise SystemExit(subprocess.call([str(python),'-X','utf8',str(Path(__file__).resolve()),*sys.argv[1:]],env=env))
from studio_core.pipeline import main

if __name__ == '__main__':
    raise SystemExit(main())
