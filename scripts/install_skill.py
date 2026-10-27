"""Install only manifest-listed Skill files. Never replace an existing installation."""
import argparse,hashlib,json,shutil
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--project',type=Path);g.add_argument('--user',action='store_true',help='Explicitly opt in to the user-wide Skill directory')
    p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    home=(Path.home() if a.user else a.project.expanduser()).resolve()
    dest=home/'.agents/skills/academic-paper-to-ppt'
    if not dest.resolve().is_relative_to(home):raise RuntimeError('Target resolves outside the selected project/home; check directory links.')
    if dest.exists() or dest.resolve().is_relative_to(ROOT):raise RuntimeError('Target exists or is nested in the source download; choose a separate project, never overwrite.')
    manifest=json.loads((ROOT/'package-manifest.json').read_text(encoding='utf-8'))
    for raw,h in manifest['files'].items():
        rel=PurePosixPath(raw)
        if rel.is_absolute() or '..' in rel.parts or '\\' in raw or ':' in raw:raise RuntimeError('Unsafe manifest path.')
        src=ROOT.joinpath(*rel.parts)
        if src.is_symlink() or not src.is_file() or hashlib.sha256(src.read_bytes()).hexdigest()!=h:raise RuntimeError('Package file is absent or changed: '+raw)
    print(json.dumps({'destination':str(dest),'files':len(manifest['files']),'dryRun':a.dry_run,'userWide':a.user},ensure_ascii=False))
    if a.dry_run:return
    dest.mkdir(parents=True)
    for raw in list(manifest['files'])+['package-manifest.json']:
        target=dest/raw;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/raw,target)
    print('Installed. Check/install the local runtime using scripts/setup.py; no global environment changed.')
if __name__=='__main__':
    try:main()
    except (RuntimeError,OSError,ValueError) as e:print('Installation blocked:',str(e));raise SystemExit(2)
