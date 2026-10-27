"""Stdlib-only release/installer safeguards; never installs or downloads dependencies."""
import hashlib,importlib.util,json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name):
 spec=importlib.util.spec_from_file_location('release_test_'+name,ROOT/'scripts'/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
class ReleaseSafeguards(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.setup=load('setup');cls.installer=load('install_skill');cls.scan=load('release_check')
  area=Path(os.environ.get('ACADEMIC_PPT_WORKSPACE',str(Path.cwd())))/'.test-output';area.mkdir(parents=True,exist_ok=True)
  cls.tmp=tempfile.TemporaryDirectory(prefix='release-check-',dir=area);cls.area=Path(cls.tmp.name)
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def installer_call(self,args):
  return subprocess.run([sys.executable,str(ROOT/'scripts/install_skill.py'),*args],capture_output=True,text=True,encoding='utf-8')
 def skeleton(self,name):
  root=self.area/name;root.mkdir()
  for v in ['baoyu-design','scientific-critical-thinking','scientific-slides','scientific-visualization']:
   p=root/'third_party'/v/'LICENSE';p.parent.mkdir(parents=True);p.write_text('synthetic test notice')
  return root
 def test_manifest_matches_every_source_file(self):
  m=json.loads((ROOT/'package-manifest.json').read_text(encoding='utf-8'))
  actual={raw:hashlib.sha256((ROOT/raw).read_bytes()).hexdigest() for raw in m['files']}
  self.assertEqual(m['files'],actual)
 def test_public_tree_scan_passes(self):
  clean=self.area/'manifest-source-view';clean.mkdir()
  m=json.loads((ROOT/'package-manifest.json').read_text(encoding='utf-8'))
  for raw in [*m['files'],'package-manifest.json']:
   target=clean/raw;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/raw,target)
  self.assertEqual(self.scan.scan(clean)['status'],'passed')
 def test_dry_install_is_nonmutating(self):
  target=self.area/'Unicode 项目';r=self.installer_call(['--project',str(target),'--dry-run'])
  self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertFalse(target.exists())
 def test_existing_skill_is_never_overwritten(self):
  target=self.area/'existing';sentinel=target/'.agents/skills/academic-paper-to-ppt/keep.txt';sentinel.parent.mkdir(parents=True);sentinel.write_text('keep')
  r=self.installer_call(['--project',str(target)]);self.assertEqual(r.returncode,2);self.assertEqual(sentinel.read_text(),'keep')
 def test_recursive_install_is_blocked(self):
  r=self.installer_call(['--project',str(ROOT/'nested-test'),'--dry-run']);self.assertEqual(r.returncode,2)
 def test_no_approval_means_no_download_or_directory(self):
  target=self.area/'not-created'
  with patch.dict(os.environ,{'ACADEMIC_PPT_RUNTIME':str(target)}),patch.object(sys,'argv',['setup.py','--install']):
   with self.assertRaisesRegex(RuntimeError,'allow-downloads'):self.setup.main()
  self.assertFalse(target.exists())
 def test_missing_office_has_explicit_blocking_message(self):
  if sys.platform!='win32':self.skipTest('Windows registry diagnostic')
  with patch('winreg.OpenKey',side_effect=FileNotFoundError):r=self.setup.inspect(self.area)
  self.assertFalse(r['powerPointRegistered']);self.assertIn('blocked',r['powerPointMessage']);self.assertFalse(r['networkUsed'])
 def test_unvalidated_architecture_is_blocked(self):
  with patch.object(sys,'argv',['setup.py','--install','--allow-downloads']),patch.object(self.setup.platform,'machine',return_value='ARM64'):
   with self.assertRaisesRegex(RuntimeError,'Windows x64'):self.setup.main()
 def test_pdf_is_not_publishable_source(self):
  root=self.skeleton('pdf');(root/'paper.pdf').write_bytes(b'synthetic, not a PDF');self.assertEqual(self.scan.scan(root)['status'],'blocked')
 def test_runtime_directory_is_rejected(self):
  root=self.skeleton('runtime');p=root/'node_modules/private.js';p.parent.mkdir();p.write_text('test');self.assertEqual(self.scan.scan(root)['status'],'blocked')
 def test_token_like_values_are_rejected(self):
  root=self.skeleton('secret');(root/'test.txt').write_text('gh'+'p_'+'A'*36);self.assertEqual(self.scan.scan(root)['status'],'blocked')
 def test_missing_third_party_notice_is_rejected(self):
  root=self.area/'missing-notices';root.mkdir();self.assertEqual(self.scan.scan(root)['status'],'blocked')
if __name__=='__main__':unittest.main(verbosity=2)
