from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib
import json
import os
import subprocess
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[2]
VERSION = '2.2.0-generalized.1'
PACKAGE_VERSION = '0.1.0'
RUNTIME = Path(os.environ.get('ACADEMIC_PPT_RUNTIME', str(ROOT/'.runtime'))).expanduser().resolve()
WORKSPACE = Path(os.environ.get('ACADEMIC_PPT_WORKSPACE', str(Path.cwd()))).expanduser().resolve()

class Blocked(Exception):
    def __init__(self, code, message):
        self.code, self.message = code, message
        super().__init__(message)

def read(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError) as exc:
        raise Blocked('INVALID_ARTIFACT', f'{path}: {exc}') from exc

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        temporary = stream.name
    os.replace(temporary, path)

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def require(condition, code, message):
    if not condition:
        raise Blocked(code, message)

def env():
    result = os.environ.copy()
    result.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8', MPLBACKEND='Agg',
                  HF_HOME=str(RUNTIME/'cache/huggingface'), HF_HUB_OFFLINE='1',
                  MPLCONFIGDIR=str(RUNTIME/'cache/matplotlib'),
                  PLAYWRIGHT_BROWSERS_PATH=str(RUNTIME/'browsers'),
                  NODE_PATH=str(RUNTIME/'node/node_modules'), PYTHONNOUSERSITE='1', ACADEMIC_PPT_RUNTIME=str(RUNTIME))
    result.pop('PYTHONPATH',None)
    return result

def command(args, log, timeout=180, overrides=None):
    try:
        child_env=env();child_env.update(overrides or {})
        result = subprocess.run([str(x) for x in args], cwd=ROOT, env=child_env,
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    except subprocess.TimeoutExpired as exc:
        Path(log).parent.mkdir(parents=True, exist_ok=True)
        Path(log).write_text('Command timed out; export is not accepted.\n', encoding='utf-8')
        raise Blocked('COMMAND_TIMEOUT', f'Timeout: {args[0]}; see {log}') from exc
    except OSError as exc:
        raise Blocked('COMMAND_UNAVAILABLE', str(exc)) from exc
    Path(log).parent.mkdir(parents=True, exist_ok=True)
    Path(log).write_text(result.stdout+'\n'+result.stderr, encoding='utf-8')
    require(result.returncode == 0, 'COMMAND_FAILED', f'Exit {result.returncode}: {args[0]}; see {log}')
    return result.stdout

def job_path(value):
    job = Path(value).resolve()
    require((job/'run.json').is_file(), 'NO_RUN', f'Not a Studio run: {job}')
    return job

def check_source(job):
    state = read(job/'run.json')
    require(sha(job/'input/paper.pdf') == state['source']['sha256'], 'SOURCE_CHANGED', 'Input PDF snapshot changed; create a new run.')
    return state

def record(job, stage, status, detail=None):
    state = read(job/'run.json')
    entry = {'status': status, 'detail': detail, 'time': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()}
    state.setdefault('stages', {})[stage] = entry
    state['status'] = status
    state.setdefault('events', []).append({'stage': stage, **entry})
    write(job/'run.json', state)

def new_run(pdf, settings):
    import shutil
    source = Path(pdf).resolve()
    require(source.is_file() and source.suffix.lower() == '.pdf', 'INPUT_PDF', 'Provide an existing local PDF.')
    require(source.stat().st_size > 0, 'EMPTY_PDF', 'The input PDF is empty.')
    folder = WORKSPACE/settings['outputRoot']
    require(folder.resolve().is_relative_to(WORKSPACE), 'OUTPUT_ROOT', 'outputRoot must stay in the configured workspace.')
    run_id = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:8]
    job = folder/run_id
    (job/'input').mkdir(parents=True)
    shutil.copyfile(source, job/'input/paper.pdf')
    write(job/'run.json', {'version':VERSION, 'workflowContract':'generalized-editorial-v1', 'id':run_id, 'settings':settings,
        'source':{'originalPath':str(source),'sha256':sha(job/'input/paper.pdf')},
        'status':'created','stages':{},'events':[]})
    return job
