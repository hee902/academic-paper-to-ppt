"""Portable contract tests using only self-authored synthetic source material."""
import copy,json,os,shutil,subprocess,sys,unittest,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(Path(__file__).parent)]
from studio_core.common import WORKSPACE,RUNTIME,Blocked,new_run,read,write,sha
from studio_core.parsing import prepare,crop
from studio_core.contracts import validate_science,validate_plan,numbers
from studio_core.research import resolve_layout,profiles
from studio_core.quality import current_design,finalize
from studio_core.generic_layouts import interval_data
from synthetic_fixture import make_pdf,fill_known

class PortableContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.area=WORKSPACE/'.test-output'/uuid.uuid4().hex[:8];cls.area.mkdir(parents=True)
        pdf=cls.area/'synthetic.pdf';make_pdf(pdf)
        settings=read(ROOT/'config/presentation-defaults.json');settings.update(purpose='visual-prototype',slideCount=3,durationMinutes=4)
        cls.base=new_run(pdf,settings);prepare(cls.base,'docling-native')
        crop(cls.base,'SyntheticInterval',1,[.06,.44,.97,.87],4);fill_known(cls.base)
    def setUp(self):
        self.job=self.area/self._testMethodName;shutil.copytree(self.base,self.job)
    def block(self,code,fn):
        with self.assertRaises(Blocked) as e:fn()
        self.assertEqual(e.exception.code,code)
    def alter_analysis(self,fn):
        a=read(self.job/'B/analysis.json');fn(a);write(self.job/'B/analysis.json',a)
        r=read(self.job/'B/review.json');r['analysisSha256']=sha(self.job/'B/analysis.json');write(self.job/'B/review.json',r)
    def alter_plan(self,fn):
        p=read(self.job/'C/plan.json');fn(p);write(self.job/'C/plan.json',p)
        r=read(self.job/'C/review.json');r['planSha256']=sha(self.job/'C/plan.json');write(self.job/'C/review.json',r)
    def test_synthetic_full_parse_is_native_docling(self):
        p=read(self.job/'A/paper.json');self.assertIsNone(p['doclingError']);self.assertEqual(p['pageCount'],1);self.assertTrue(p['blocks'])
    def test_default_budget_and_aspect(self):
        d=read(ROOT/'config/presentation-defaults.json');self.assertEqual((d['slideCount'],d['durationMinutes'],d['aspectRatio']),(14,17,'16:9'))
    def test_actual_node_entry_cannot_borrow_ancestor_packages(self):
        r=subprocess.run(['node','-e','require(process.argv[1]);process.stdout.write(JSON.stringify(Object.keys(require.cache)));',str(ROOT/'scripts/build_deck.cjs')],capture_output=True,text=True,encoding='utf-8',check=True)
        origins=json.loads(r.stdout);self.assertGreater(len(origins),1)
        self.assertTrue(all(Path(p).is_relative_to(RUNTIME/'node/node_modules') or Path(p).is_relative_to(ROOT/'scripts') for p in origins))
    def test_run_is_in_configured_workspace(self):self.assertTrue(self.base.is_relative_to(WORKSPACE));self.assertNotEqual(self.base.parent,ROOT/'work')
    def test_valid_scientific_record(self):self.assertEqual(validate_science(self.job)['researchDesign']['primaryType'],'theoretical-methodological')
    def test_valid_narrative(self):self.assertEqual(len(validate_plan(self.job)['slides']),3)
    def test_pdf_mutation_blocks(self):
        with (self.job/'input/paper.pdf').open('ab') as f:f.write(b'change')
        self.block('SOURCE_CHANGED',lambda:validate_science(self.job))
    def test_canonical_text_mutation_blocks(self):
        p=read(self.job/'A/paper.json');p['pages'][0]['text']+=' mutation';write(self.job/'A/paper.json',p)
        self.block('STALE_PARSE',lambda:validate_science(self.job))
    def test_unreviewed_page_blocks(self):
        r=read(self.job/'B/review.json');r['pages'][0]['status']='pending';write(self.job/'B/review.json',r)
        self.block('PAGE_NOT_REVIEWED',lambda:validate_science(self.job))
    def test_false_quote_blocks_even_if_reviewed(self):
        self.alter_analysis(lambda a:a['evidence'][0].update(quote='Not a real quote in the generated document.'))
        self.block('QUOTE_MISMATCH',lambda:validate_science(self.job))
    def test_stale_science_review_blocks(self):
        a=read(self.job/'B/analysis.json');a['paperTitle']+=' change';write(self.job/'B/analysis.json',a)
        self.block('STALE_SCIENTIFIC_REVIEW',lambda:validate_science(self.job))
    def test_unknown_research_design_blocks(self):
        self.alter_analysis(lambda a:a['researchDesign'].update(primaryType='unsupported-type'))
        self.block('RESEARCH_TYPE',lambda:validate_science(self.job))
    def test_missing_design_review_blocks(self):
        r=read(self.job/'B/review.json');r['researchDesignReviewed']=False;write(self.job/'B/review.json',r)
        self.block('RESEARCH_REVIEW',lambda:validate_science(self.job))
    def test_added_scientific_number_blocks(self):
        self.alter_plan(lambda p:p['slides'][0]['body'].append('The study measured 987654 units.'))
        self.block('UNSUPPORTED_SLIDE_NUMBER',lambda:validate_plan(self.job))
    def test_stale_narrative_review_blocks(self):
        p=read(self.job/'C/plan.json');p['slides'][0]['title']+=' change';write(self.job/'C/plan.json',p)
        self.block('STALE_NARRATIVE_REVIEW',lambda:validate_plan(self.job))
    def test_missing_notes_blocks(self):
        self.alter_plan(lambda p:p['slides'][0].update(notes=''))
        self.block('SPEAKER_NOTES',lambda:validate_plan(self.job))
    def test_timing_overrun_blocks(self):
        self.alter_plan(lambda p:p['slides'][0].update(seconds=900))
        self.block('TIMING',lambda:validate_plan(self.job))
    def test_unknown_layout_task_blocks(self):
        self.alter_plan(lambda p:p['slides'][0]['visual'].update(task='unknown-task'))
        with self.assertRaises(Blocked):validate_plan(self.job)
    def test_interval_unit_cannot_become_percent(self):
        self.alter_plan(lambda p:p['slides'][-1]['visual']['statisticalInterval'].update(unit='%'))
        with self.assertRaises(Blocked):validate_plan(self.job)
    def test_interval_axis_cannot_hide_reported_endpoint(self):
        self.alter_plan(lambda p:p['slides'][-1]['visual']['statisticalInterval'].update(axis=[1.2,1.6]))
        with self.assertRaises(Blocked):validate_plan(self.job)
    def test_original_source_crop_is_bound(self):
        r=read(self.job/'B/review.json');r['evidence'][-1]['assetSha256']='0'*64;write(self.job/'B/review.json',r)
        with self.assertRaises(Blocked):validate_science(self.job)
    def test_uncertain_claim_blocks(self):
        r=read(self.job/'B/review.json');r['claims'][0]['status']='uncertain';write(self.job/'B/review.json',r)
        self.block('UNSUPPORTED_CLAIM',lambda:validate_science(self.job))
    def test_unicode_sign_retained(self):self.assertEqual(numbers('−3.50'),{'-3.5'})
    def test_ratio_interval_keeps_original_figure(self):
        self.alter_plan(lambda p:p['slides'][-1].pop('assetId'))
        with self.assertRaises(Blocked):validate_plan(self.job)
    def test_new_source_contract_is_not_optional(self):
        r=read(self.job/'run.json');r.pop('workflowContract');write(self.job/'run.json',r)
        self.block('WORKFLOW_CONTRACT',lambda:validate_science(self.job))
    def test_fresh_package_has_no_private_science_assets(self):
        self.assertFalse(list(ROOT.glob('**/paper.pdf')));self.assertFalse(list((ROOT/'third_party').glob('**/*.png')))

if __name__=='__main__':unittest.main(verbosity=2)
