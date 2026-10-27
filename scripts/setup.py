"""Inspect/install an isolated runtime only after explicit --install --allow-downloads."""
import argparse,hashlib,json,os,platform,shutil,subprocess,sys,urllib.request,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def runtime():return Path(os.environ.get('ACADEMIC_PPT_RUNTIME',str(ROOT/'.runtime'))).expanduser().resolve()
def python_at(r):return r/'venv/Scripts/python.exe'
def run(args,environment=None):
    print(json.dumps({'run':[str(x) for x in args]},ensure_ascii=False),flush=True)
    p=subprocess.run([str(x) for x in args],env=environment,timeout=1800,creationflags=subprocess.CREATE_NO_WINDOW)
    if p.returncode:raise RuntimeError('Command failed: '+str(args[0]))
def inspect(r):
    import importlib.util
    office=False
    if sys.platform=='win32':
        import winreg
        for view in [winreg.KEY_WOW64_64KEY,winreg.KEY_WOW64_32KEY]:
            try:
                with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT,'PowerPoint.Application',0,winreg.KEY_READ|view):office=True
            except OSError:pass
    node=shutil.which('node');version=subprocess.run([node,'--version'],capture_output=True,text=True).stdout.strip() if node else None
    return {'platform':platform.platform(),'pythonVersion':platform.python_version(),'runtime':str(r),'runtimePythonExists':python_at(r).is_file(),
        'node':node,'nodeVersion':version,'powerPointRegistered':office,'networkUsed':False,
        'requirements':'Tested Windows 11 x64, Python 3.12, Node 24, desktop PowerPoint 16.0. Other platforms unvalidated.',
        'powerPointMessage':'Available for actual COM export' if office else 'Desktop PowerPoint is missing; PPTX building may work, but PDF/PNG export and final acceptance are blocked. No LibreOffice compatibility claim.'}
def bootstrap_npm(r):
    # Official pinned npm distribution; verify the registry SHA-512 before safe extraction.
    target=r/'npm';cli=target/'bin/npm-cli.js'
    if cli.is_file():return cli
    with urllib.request.urlopen('https://registry.npmjs.org/npm/12.2.1',timeout=45) as s:meta=json.load(s)
    with urllib.request.urlopen(meta['dist']['tarball'],timeout=90) as s:data=s.read()
    import base64,io
    expected=meta['dist']['integrity'];got='sha512-'+base64.b64encode(hashlib.sha512(data).digest()).decode()
    if got!=expected:raise RuntimeError('npm distribution integrity mismatch.')
    target.mkdir(parents=True,exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as tar:
        for m in tar.getmembers():
            if not m.isfile():continue
            rel=Path(*Path(m.name).parts[1:]);dest=(target/rel).resolve()
            if not dest.is_relative_to(target):raise RuntimeError('Unsafe npm archive path.')
            dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(tar.extractfile(m).read())
    (r/'npm-source.json').write_text(json.dumps({'version':'12.2.1','url':meta['dist']['tarball'],'integrity':expected}),encoding='utf-8')
    return cli
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--install',action='store_true');p.add_argument('--allow-downloads',action='store_true');p.add_argument('--npm-cli',type=Path);p.add_argument('--resolve',action='store_true',help='Maintainer only: resolve requirements.in instead of the shipped hash lock')
    a=p.parse_args();r=runtime();info=inspect(r)
    if not a.install:print(json.dumps(info,ensure_ascii=False,indent=2));return 0
    if not a.allow_downloads:raise RuntimeError('Installation downloads packages/browser. Explicit --allow-downloads is required; no global install is performed.')
    if sys.platform!='win32' or sys.version_info[:2]!=(3,12) or platform.machine().lower() not in ('amd64','x86_64') or sys.maxsize<=2**32:raise RuntimeError('This release installer is validated only on Windows x64 Python 3.12.')
    if not info['nodeVersion'] or int(info['nodeVersion'].split('.')[0].lstrip('v'))!=24:raise RuntimeError('Install Node.js 24 x64 first. The installer does not change global Node/PATH.')
    r.mkdir(parents=True,exist_ok=True)
    if not python_at(r).exists():run([sys.executable,'-m','venv',r/'venv'])
    env=os.environ.copy();env.pop('PYTHONPATH',None);env['PYTHONNOUSERSITE']='1';env['PIP_DISABLE_PIP_VERSION_CHECK']='1';env['PIP_CACHE_DIR']=str(r/'pip-cache');env['npm_config_cache']=str(r/'npm-cache');env['PLAYWRIGHT_BROWSERS_PATH']=str(r/'browsers')
    # urllib already honors Windows proxy configuration. Give the browser
    # downloader the same proxy only in this child environment; never log it.
    proxies=urllib.request.getproxies()
    if not env.get('HTTPS_PROXY') and proxies.get('https'):env['HTTPS_PROXY']=proxies['https']
    req=ROOT/('requirements.in' if a.resolve else 'requirements-win-py312.lock.txt')
    if not req.exists():raise RuntimeError('Pinned requirement lock is missing; reject incomplete release.')
    args=[python_at(r),'-m','pip','install','--report',r/'pip-install-report.json']
    if not a.resolve:args+=['--require-hashes']
    run(args+['-r',req],env)
    node=r/'node';node.mkdir(exist_ok=True)
    for name in ['package.json','package-lock.json']:shutil.copyfile(ROOT/name,node/name)
    npm=a.npm_cli.resolve() if a.npm_cli else bootstrap_npm(r)
    run([info['node'],npm,'ci','--prefix',node,'--ignore-scripts','--no-audit','--no-fund'],env)
    run([info['node'],node/'node_modules/playwright/cli.js','install','--only-shell','chromium'],env)
    run([python_at(r),'-m','pip','check'],env)
    print(json.dumps({'status':'installed-local-runtime','runtime':str(r),'powerPointRegistered':info['powerPointRegistered'],'globalEnvironmentChanged':False},ensure_ascii=False))
    return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except (RuntimeError,OSError,ValueError,subprocess.SubprocessError) as e:print(json.dumps({'status':'blocked','reason':str(e)},ensure_ascii=False));raise SystemExit(2)
