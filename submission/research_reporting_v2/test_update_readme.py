"""Read-only metadata fixture tests; temporary directories only; zero model fits."""
import ast
import csv
import importlib.util
import io
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT / 'submission/research_reporting_v2/update_readme.py'
SPEC = importlib.util.spec_from_file_location('reporter_fixture', PATH)
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
OLD = M.load_old(ROOT)


def put(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


class SmallSnapshot:
    def __init__(self, root):
        self.root, self.created = root, '2026-11-07T18:00:00+00:00'
        self.rows, self.campaigns = [], []

    def read(self, relative, required=False):
        path = self.root / relative
        return json.loads(path.read_text()) if path.exists() else None


class ReportingChecks(unittest.TestCase):
    def test_syntax_and_pinned_dependency_load(self):
        ast.parse(PATH.read_text())
        self.assertEqual(M.sha(PATH.read_bytes()), 'f392d7e8806ed8b200797c9e7036cc8cc7947f2ec9755ba97460a0a08cb07f2a')
        self.assertEqual(len(M.PINS), 2)

    def test_full_planned_schema(self):
        prefix = 'analysis_outputs/' + M.STAGE
        ids = ['n0132','n0135','n0142','n0169','n0171','n0173','n0174','n0186','n0188','n0191','n0582','n1450']
        base_ids = ['b00','b02','b09','b22']
        configs = []
        for index, (features, weighting, mix, reg, base) in enumerate(itertools.product(
                ['weather_spread','rich_spread'], ['money','horizon','horizon_groupseason'],
                [0,.5,1], ['small','medium','large','anchored'], base_ids)):
            configs.append(dict(id=f'r{index:04d}', base_id=base, features=features, weighting=weighting,
                group_mix=mix, regularization=reg, mode='additive', shrink=.5, bound=.2, n_estimators=300,
                learning_rate=.025, num_leaves=15, min_child_samples=1000, reg_lambda=10,
                anchor_penalty=.25 if reg == 'anchored' else 0))
        names = ['early2022','primary','winter','spring','recent'] + [f'q{i:02d}' for i in range(11)]
        folds = {name: {'origin':'2023-01-01','end':'2023-04-01'} for name in names}
        jobs = [{'id':'validate_'+i, 'argv':['engine','validate','--id',i]} for i in ids]
        fixture = {
            prefix+'/protocol.json': {'folds':folds,'search_seeds':[0,1,2],'recovered_ids':ids},
            prefix+'/configs.json': configs,
            prefix+'/bases.json': [{'id':b,'source_id':sid,'config':{}} for b,sid in zip(base_ids,['c206','c174','c093','c185'])],
            prefix+'/jobs.json': jobs,
            prefix+'/controller_manifest.json': {'deadline_utc':M.DEADLINE,'jobs':jobs},
        }
        raw, load, ownership = OLD.Snapshot.raw, M.load_old, M.check_ownership
        def fake_raw(snapshot, relative):
            relative = str(relative)
            if relative.startswith(prefix+'/'):
                value = fixture.get(relative)
                if value is None:
                    return None
                data = json.dumps(value, sort_keys=True).encode()
                snapshot.cache[relative], snapshot.inputs[relative] = data, M.sha(data)
                return data
            return raw(snapshot, relative)
        try:
            OLD.Snapshot.raw = fake_raw
            M.load_old = lambda root: OLD
            # Ownership is separately tested against temporary files below.
            M.check_ownership = lambda root, outputs: None
            outputs, manifest, _ = M.build(ROOT)
        finally:
            OLD.Snapshot.raw, M.load_old, M.check_ownership = raw, load, ownership
        self.assertEqual(manifest['historical_campaigns'], 36)
        self.assertEqual(manifest['experiment_rows'], 2896)
        parts = {p:data for p,data in outputs.items() if p.endswith('.csv')}
        self.assertGreaterEqual(len(parts), 2)
        self.assertTrue(all(len(data) <= M.LIMIT for data in outputs.values()))
        records = []
        for path, data in parts.items():
            records.extend(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
            self.assertIn(f']({Path(path).name})', outputs[M.OVERVIEW+'/README.md'].decode())
        new = [r for r in records if r['campaign'] == M.STAGE]
        self.assertEqual(len(new), 317)
        for kind, count in [('new_calibration',288),('recovered_result',12),('seed_validation',12),('reused_oof_inputs',4),('assembled_search_inputs',1)]:
            self.assertEqual(sum(r['kind'] == kind for r in new), count)
        self.assertTrue(all(manifest['outputs_sha256'][p] == M.sha(data) for p,data in outputs.items()))
        self.assertTrue(all(digest == M.sha((ROOT/p).read_bytes()) for p,digest in manifest['source_sha256'].items()))
        readme = outputs['README.md'].decode()
        for phrase in ['11개 분기 평가 구간은 서로 겹치지 않지만', '연간 5개 구간은 서로 및 분기 구간과 겹칩니다',
                       '옛 기록은 계속 실패 상태로 보존', '새 단계의 복원·추가 시드 진단이 이미 완료됐다는 뜻은 아닙니다',
                       '총 24개는 모두 0을 포함']:
            self.assertIn(phrase, readme)

    def test_unicode_csv_record_boundaries(self):
        rows = [{'id':str(i),'text':'기상, "검증"\n값'} for i in range(30)]
        parts = M.csv_outputs(rows, ['id','text'], limit=130)
        actual = []
        for data in parts.values():
            self.assertLessEqual(len(data), 130)
            actual.extend(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))
        self.assertEqual(actual, rows)

    def test_partial_base_new_fit_counts(self):
        with tempfile.TemporaryDirectory(prefix='oibc-v2-base-') as directory:
            root, prefix = Path(directory), 'analysis_outputs/'+M.STAGE
            put(root,prefix+'/bases.json',[{'id':'b00','source_id':'c206'}])
            for origin, fits in [('2024-09-01',1),('2023-01-01',0),('2024-12-01.interrupted.1',1)]:
                put(root,prefix+f'/bases/b00/origins/{origin}/receipt.json',{'status':'PASS','real_model_fits':fits})
            stage = M.new_stage(SmallSnapshot(root), OLD)
            self.assertEqual(stage['recorded_model_fits'], 1)
            self.assertEqual(stage['bases'][0]['status'], 'partial')

    def test_completed_receipts_and_diagnostic_isolation(self):
        with tempfile.TemporaryDirectory(prefix='oibc-v2-results-') as directory:
            root, prefix = Path(directory), 'analysis_outputs/'+M.STAGE
            folds = ['primary','recent']+[f'q{i:02d}' for i in range(14)]
            put(root,prefix+'/protocol.json',{'folds':dict.fromkeys(folds,{}),'search_seeds':[0,1,2],'recovered_ids':['n0132']})
            put(root,prefix+'/configs.json',[{'id':'r0000','base_id':'b00'}])
            for seed in range(3):
                for fold in folds:
                    put(root,prefix+f'/trials/r0000/seed{seed}/{fold}/receipt.json',{'status':'PASS','real_model_fits':3,'elapsed_seconds':1})
            for location in ['seed0/primary.interrupted.123', 'seed0.interrupted.123/primary',
                             'seed99/primary', 'seed0/unknown_fold', 'seed0/.hidden']:
                put(root,prefix+f'/trials/r0000/{location}/receipt.json',{'status':'PASS','real_model_fits':100,'elapsed_seconds':1})
            put(root,prefix+'/trials/r0000/result.json',{'status':'PASS','eligible':True,'folds':{}})
            put(root,prefix+'/recovered/n0132/result.json',{'status':'RECOVERED_DIAGNOSTIC','eligible':True,'real_model_fits':0})
            put(root,prefix+'/validation/n0132/result.json',{'status':'PASS','eligible':True,'real_model_fits':4,'frozen_alpha':.07})
            snap = SmallSnapshot(root)
            stage = M.new_stage(snap, OLD)
            rows = {(r['kind'],r['id']):r for r in snap.rows}
            self.assertEqual(rows['new_calibration','r0000']['completed_folds'],16)
            self.assertEqual(rows['new_calibration','r0000']['recorded_model_fits'],144)
            self.assertEqual(stage['eligible'],1)
            self.assertIsNone(rows['recovered_result','n0132']['eligible'])
            self.assertIsNone(rows['seed_validation','n0132']['eligible'])
            self.assertEqual(rows['seed_validation','n0132']['blend_alpha'],.07)

    def test_manual_edits_blocked_first_and_later(self):
        with tempfile.TemporaryDirectory(prefix='oibc-v2-ownership-') as directory:
            root = Path(directory)
            outputs = {'README.md':b'owned',M.OVERVIEW+'/README.md':b'detail',M.OVERVIEW+'/experiments.csv':b'csv'}
            (root/'README.md').write_bytes(b'owned')
            put(root,'analysis_outputs/experiment_overview/snapshot_manifest.json',{'outputs_sha256':{'README.md':M.sha(b'owned')}})
            M.check_ownership(root,outputs)
            (root/'README.md').write_bytes(b'manual')
            with self.assertRaises(ValueError): M.check_ownership(root,outputs)
            for path,data in outputs.items():
                target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
            put(root,M.OVERVIEW+'/snapshot_manifest.json',{'outputs_sha256':{p:M.sha(v) for p,v in outputs.items()}})
            M.check_ownership(root,outputs)
            (root/M.OVERVIEW/'experiments.csv').write_bytes(b'manual')
            with self.assertRaises(ValueError): M.check_ownership(root,outputs)

    def test_stale_pid_and_failed_receipts(self):
        identity={'pid':99999999,'pgid':0,'start_ticks':0,'boot_id':'no'}
        self.assertEqual(M.job_status({'status':'running','wrapper_identity':identity},None,[],OLD)[0],'unknown')
        self.assertEqual(M.job_status({'status':'failed'}, {'status':'PASS'},[{}],OLD)[0],'failed')

    def test_completion_outcome_uses_actual_job_identity_and_keeps_result_kind(self):
        with tempfile.TemporaryDirectory(prefix='oibc-v2-completion-') as directory:
            root, prefix = Path(directory), 'analysis_outputs/' + M.STAGE
            for outcome in sorted(M.FINALIZATION_OUTCOMES):
                for state, live, expected in [('running', True, 'finalizing'), ('running', False, 'completed'),
                                              ('completed', False, 'completed'), ('failed', False, 'failed')]:
                    with self.subTest(outcome=outcome, state=state, live=live):
                        put(root, prefix+'/controller_state/state.json', {'jobs': {
                            'complete': {'status': 'failed'},
                            'completion': {'status': state, 'wrapper_identity': {'live': live},
                                           'launched_utc': '2026-11-07T17:00:00+00:00'}}})
                        put(root, prefix+'/completion/result.json', {'status': outcome})
                        snapshot = SmallSnapshot(root)
                        with patch.object(OLD, 'identity_alive', side_effect=lambda value: value.get('live', False)):
                            stage = M.new_stage(snapshot, OLD)
                        row = next(r for r in snapshot.rows if r['kind'] == 'finalization')
                        self.assertEqual(row['status'], expected)
                        self.assertEqual(row['controller_status'], state)
                        self.assertEqual(row['process_identity_matches'], live)
                        self.assertEqual(row['result_status'], outcome)
                        self.assertEqual(row['job_elapsed_seconds'], 3600)
                        self.assertNotIn('eligible', row)
                        self.assertEqual(stage['eligible'], 0)

    def test_completion_budget_checkpoint_and_active_job_are_not_candidate_success(self):
        with tempfile.TemporaryDirectory(prefix='oibc-v2-completion-budget-') as directory:
            root, prefix = Path(directory), 'analysis_outputs/' + M.STAGE
            put(root, prefix+'/controller_state/state.json', {'jobs': {
                'completion': {'status': 'running', 'wrapper_identity': {'live': True}}}})
            snapshot = SmallSnapshot(root)
            with patch.object(OLD, 'identity_alive', return_value=True):
                M.new_stage(snapshot, OLD)
            self.assertEqual(next(r for r in snapshot.rows if r['kind']=='finalization')['status'], 'running')
            for outcome, expected in [('TIME_BUDGET_EXHAUSTED', 'time_limit'), ('STORAGE_BUDGET_EXHAUSTED', 'partial')]:
                with self.subTest(outcome=outcome):
                    put(root, prefix+'/completion/budget_stop.json',
                        {'status': outcome, 'checkpoint_preserved': True, 'exported': False})
                    put(root, prefix+'/controller_state/state.json', {'jobs': {'completion': {'status': 'completed'}}})
                    snapshot = SmallSnapshot(root)
                    stage = M.new_stage(snapshot, OLD)
                    row = next(r for r in snapshot.rows if r['kind']=='finalization')
                    self.assertEqual(row['status'], expected)
                    self.assertEqual(row['result_status'], outcome)
                    self.assertIn('체크포인트만 보존; 후보 검증 성공이 아님', row['note'])
                    self.assertEqual(stage['completion']['status'], outcome)
                    self.assertNotIn('eligible', row)


if __name__ == '__main__':
    unittest.main(verbosity=2)
