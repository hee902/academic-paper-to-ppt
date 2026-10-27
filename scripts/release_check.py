"""Fail-closed allowlist/privacy scan for the publishable Skill tree."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXT={'.py','.md','.json','.yaml','.yml','.cjs','.js','.txt','.in'}
FORBIDDEN_DIRS={'.runtime','.venv','.venv-mineru','node_modules','__pycache__','.cache','work','output','audit','.git'}
def scan(root):
    failures=[];files=[]
    for p in sorted(Path(root).rglob('*')):
        rel=p.relative_to(root)
        if p.is_symlink():failures.append({'file':rel.as_posix(),'reason':'symlink'});continue
        if not p.is_file():continue
        if FORBIDDEN_DIRS.intersection(rel.parts):failures.append({'file':rel.as_posix(),'reason':'runtime/cache/history directory'});continue
        if p.suffix.lower() not in EXT and p.name not in ['LICENSE','.gitignore']:failures.append({'file':rel.as_posix(),'reason':'non-source asset not approved'});continue
        try:t=p.read_text(encoding='utf-8-sig')
        except UnicodeError:failures.append({'file':rel.as_posix(),'reason':'binary'});continue
        patterns={'private-windows-path':r'[A-Za-z]:[\\/](?:Users[\\/][^<>\s/\\]+|Academic[-_]PPT)',
                  'private-old-run':r'work[\\/]2026\d{4}-\d{6}-[0-9a-f]{8}',
                  'github-token':r'gh[pousr]_[A-Za-z0-9_]{25,}',
                  'api-key-value':r'sk-[A-Za-z0-9_-]{25,}',
                  'private-key':r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
                  'url-credential':r'https?://[^\s/:]+:[^\s/@]+@'}
        for label,pattern in patterns.items():
            if re.search(pattern,t):failures.append({'file':rel.as_posix(),'reason':label})
        files.append(rel.as_posix())
    for vendor in ['baoyu-design','scientific-critical-thinking','scientific-slides','scientific-visualization']:
        if not (Path(root)/'third_party'/vendor/'LICENSE').is_file():failures.append({'file':vendor,'reason':'missing license'})
    return {'status':'passed' if not failures else 'blocked','filesScanned':len(files),'failures':failures,
        'scope':'Every source/metadata file checked; no private papers, generated media, runtime/cache directories or credential-like values allowed. Pattern scans are not a mathematical proof of no secrets.'}
if __name__=='__main__':
    r=scan(ROOT);print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(r['status']!='passed')
