"""Reporting fixtures only; never writes production outputs or trains."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SOURCE = Path(__file__).with_name('update_readme.py')
SPEC = importlib.util.spec_from_file_location('v3_report_test', SOURCE)
M = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)
V2 = M.load_v2(); OLD = V2.load_old(M.ROOT)

def put(root, relative, value):
    path = root / relative; path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))

class Snapshot:
    def __init__(self, root):
        self.root=root; self.created='2026-11-08T07:30:00+00:00'; self.rows=[]; self.campaigns=[]
        self.best_ok=True;self.warnings=[]
    def read(self, path, required=False):
        file=self.root/path; return json.loads(file.read_text()) if file.exists() else None
    def link(self, path, label, prefix=''):
        return f'[{label}]({prefix}{path})' if path else ''

class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.prefix='analysis_outputs/'+M.STAGE
        self.configs=[{'id':'t00','family':'temporal','budget':.05,'context':'all'},
                      {'id':'t01','family':'temporal','budget':.1,'context':'all'},
                      {'id':'t02','family':'temporal','budget':.05,'context':'cloud'},
                      {'id':'s00','family':'spatial','budget':.05,'context':'all'}]
        put(self.root,self.prefix+'/configs.json',self.configs)
    def result(self, identifier, primary=90, recent=99, status='completed'):
        config=next(x for x in self.configs if x['id']==identifier); unit=self.prefix+'/trials/'+identifier
        receipt={'status':'PASS','id':identifier,'config':config,'real_model_fits':1}
        put(self.root,unit+'/receipt.json',receipt)
        put(self.root,unit+'/result.json',{'status':'PASS','id':identifier,'config':config,'eligible':True,'metrics':{
            'primary':{'reference':{'W':100,'W_pct':10},'candidate':{'W':primary,'W_pct':9}},
            'recent':{'reference':{'W':100,'W_pct':10},'candidate':{'W':recent,'W_pct':9.9}}}})
        state=self.root/self.prefix/'controller_state/state.json'
        d=json.loads(state.read_text()) if state.exists() else {'jobs':{}}
        d['jobs'][identifier]={'status':status};put(self.root,self.prefix+'/controller_state/state.json',d)
    def test_prespecified_nearest_comparison_not_score(self):
        self.result('t00',50,99);self.result('t01',10,30);self.result('t02',80,95)
        stage=M.novel_stage(Snapshot(self.root),OLD,V2);rows={r['id']:r for r in stage['rows']}
        self.assertEqual(rows['t02']['comparison_id'],'t00')
        self.assertEqual(rows['t02']['changed_setting_count'],1)
        self.assertAlmostEqual(rows['t02']['primary_W_change_pct_vs_comparison'],60)
        self.assertAlmostEqual(rows['t02']['recent_W_change_pct_vs_reference'],-5)
        self.assertEqual(rows['s00']['comparison_id'],'')
        self.assertIsNone(rows['t00']['blend_alpha'])
    def test_score_comparison_only_completed(self):
        self.result('t00',status='failed');self.result('t01')
        rows={r['id']:r for r in M.novel_stage(Snapshot(self.root),OLD,V2)['rows']}
        self.assertEqual(rows['t00']['status'],'failed')
        self.assertNotIn('primary_W_change_pct_vs_comparison',rows['t01'])
    def test_receipt_required_for_completed(self):
        self.result('t00');(self.root/self.prefix/'trials/t00/receipt.json').unlink()
        row=M.novel_stage(Snapshot(self.root),OLD,V2)['rows'][0]
        self.assertEqual(row['status'],'partial');self.assertEqual(row['recorded_model_fits'],0)
        self.assertNotIn('primary_W',row)
    def test_receipt_config_mismatch_stays_partial(self):
        self.result('t00');p=self.root/self.prefix/'trials/t00/receipt.json'
        d=json.loads(p.read_text());d['config']={'id':'t00','budget':999};p.write_text(json.dumps(d))
        row=M.novel_stage(Snapshot(self.root),OLD,V2)['rows'][0]
        self.assertEqual(row['status'],'partial');self.assertNotIn('primary_W',row)
    def test_stale_pid_is_not_running(self):
        put(self.root,self.prefix+'/controller_state/state.json',{'phase':'search','jobs':{'t00':{'status':'running','wrapper_identity':{'pid':99999999,'pgid':0,'start_ticks':0,'boot_id':'no'}}}})
        self.assertEqual(M.novel_stage(Snapshot(self.root),OLD,V2)['rows'][0]['status'],'unknown')
    def test_reject_unsafe_or_forward_comparison_id(self):
        self.configs[0]['comparison_id']='t01';put(self.root,self.prefix+'/configs.json',self.configs)
        with self.assertRaises(ValueError):M.novel_stage(Snapshot(self.root),OLD,V2)
        self.configs[0]={'id':'../outside'};put(self.root,self.prefix+'/configs.json',self.configs)
        with self.assertRaises(ValueError):M.novel_stage(Snapshot(self.root),OLD,V2)
    def test_initial_and_later_manual_edit_protection(self):
        outputs={'README.md':b'root',M.OVERVIEW+'/README.md':b'detail',M.OVERVIEW+'/experiments.csv':b'csv'}
        (self.root/'README.md').write_bytes(b'root')
        put(self.root,M.PREVIOUS_OVERVIEW+'/snapshot_manifest.json',{'outputs_sha256':{'README.md':M.sha(b'root')}})
        M.check_ownership(self.root,outputs)
        (self.root/'README.md').write_bytes(b'manual')
        with self.assertRaises(ValueError):M.check_ownership(self.root,outputs)
        for p,b in outputs.items():
            x=self.root/p;x.parent.mkdir(parents=True,exist_ok=True);x.write_bytes(b)
        put(self.root,M.OVERVIEW+'/snapshot_manifest.json',{'outputs_sha256':{p:M.sha(b) for p,b in outputs.items()}})
        M.check_ownership(self.root,outputs)
        (self.root/M.OVERVIEW/'experiments.csv').write_bytes(b'manual')
        with self.assertRaises(ValueError):M.check_ownership(self.root,outputs)
    def test_no_learned_coefficients_in_report_fields(self):
        self.assertNotIn('coefficients_json',M.EXTRA_FIELDS)
        self.assertIn('primary_fit_status',M.EXTRA_FIELDS)
        self.assertIn('recent_evaluation_status',M.EXTRA_FIELDS)
    def test_exported_but_late_worse_not_recommended_is_prominent(self):
        # A development winner can produce a valid exported file yet worsen
        # on the later audit. The report must not collapse those outcomes.
        self.result('t00',primary=90,recent=98)
        completion={'status':'EXPORTED_UNSCORED_CANDIDATE','selected_id':'t00','exported':True,
                    'candidate':str(M.ROOT/'submission/research_novel_candidate_20261108'),
                    'recommendation':'NOT_RECOMMENDED','late_W_ratio':1.0123,'late_targets_loaded':True}
        audit={'metrics':{'ratio':1.0123},'weekly_bootstrap':{'CI95':[-.4,2.8],
               'relative_W_change_pct':1.23,'zero_in_CI':True},'used_for_selection':False}
        put(self.root,self.prefix+'/completion/result.json',completion)
        put(self.root,self.prefix+'/completion/audit.json',audit)
        put(self.root,self.prefix+'/independent_completion_check.json',{'verification_status':'PASS'})
        snapshot=Snapshot(self.root);stage=M.novel_stage(snapshot,OLD,V2)
        text=M.render(snapshot,OLD,V2,{},stage)['README.md'].decode()
        self.assertIn('EXPORTED_UNSCORED_CANDIDATE',text)
        self.assertIn('독립 검증: `PASS`',text)
        self.assertIn('선정 ID: `t00`',text)
        self.assertIn('**NOT_RECOMMENDED (추천하지 않음)**',text)
        self.assertIn('**1.012300**',text);self.assertIn('**1.2300% (악화)**',text)
        self.assertIn('**[-0.4000%, 2.8000%]** · 0 포함',text)
        self.assertIn('submission/research_novel_candidate_20261108/submission_files.zip',text)
        self.assertIn('ZIP 생성·검증 성공을 개선 성공으로 해석하지',text)
        self.assertIn('context=cloud_trend3',text);self.assertIn('transfer_fraction=0.10',text)
        self.assertIn('−10 미만 / −10~10 / 10 초과',text)
        self.assertIn(M.STAGE+'/CAMPAIGN.md',text)
    def test_no_qualifier_can_still_have_point_improvement(self):
        self.result('t00',primary=90,recent=99)
        put(self.root,self.prefix+'/completion/result.json',{'status':'NO_QUALIFYING_RECIPE','exported':False})
        snapshot=Snapshot(self.root);stage=M.novel_stage(snapshot,OLD,V2)
        text=M.render(snapshot,OLD,V2,{},stage)['README.md'].decode()
        self.assertIn('일부 기간의 점추정 개선까지 없었다는 뜻은 아닙니다',text)
        self.assertNotIn('기록된 후보 ZIP 경로:',text)
    def test_actual_fit_duration_uses_receipt_timestamps_not_controller_walltime(self):
        self.result('t00');p=self.root/self.prefix/'trials/t00/receipt.json'
        receipt=json.loads(p.read_text());receipt['training']={
            'fit_started_utc':'2026-11-08T07:00:01.250Z','fit_finished_utc':'2026-11-08T07:00:08.750Z'}
        p.write_text(json.dumps(receipt))
        state=self.root/self.prefix/'controller_state/state.json'
        recorded=json.loads(state.read_text());recorded['jobs']['t00'].update({
            'launched_utc':'2026-11-08T06:00:00Z','finished_utc':'2026-11-08T08:00:00Z'})
        state.write_text(json.dumps(recorded))
        row=M.novel_stage(Snapshot(self.root),OLD,V2)['rows'][0]
        self.assertEqual(row['actual_fit_seconds'],7.5)
        self.assertEqual(row['recorded_model_fits'],1)
        receipt['training']['fit_finished_utc']='2026-11-08T06:00:00Z'
        self.assertIsNone(M.actual_fit_seconds(receipt))

if __name__=='__main__':unittest.main()
