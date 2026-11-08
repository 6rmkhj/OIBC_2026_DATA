"""Public-scope and snapshot tests use disposable text fixtures only."""
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

SOURCE=Path(__file__).with_name('publish_readme.py')
SPEC=importlib.util.spec_from_file_location('v3_pub_test',SOURCE)
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)
A=M.load_publisher()

class PublishTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.now=datetime.now(timezone.utc)
        self.write(M.PUBLISHER_PATH,(M.ROOT/M.PUBLISHER_PATH).read_bytes())
        for p in M.FROZEN_DEPENDENCIES:self.write(p,(M.ROOT/p).read_bytes())
        for p in M.REQUIRED_SOURCES-M.FROZEN_DEPENDENCIES.keys():self.write(p,b'# fixture source\n')
        for p in M.REQUIRED_OUTPUTS:self.write(p,b'fixture output\n')
        self.manifest={'schema_version':3,'created_utc':self.now.isoformat(),'snapshot_id':'fixture','source_snapshot_sha256':'d'*64,
            'publisher_sha256':M.PUBLISHER_SHA256,'deadline_utc':M.DEADLINE.isoformat(),'search_stop_utc':M.SEARCH_STOP.isoformat(),
            'source_sha256':{p:self.sha(p) for p in M.REQUIRED_SOURCES},'outputs_sha256':{p:self.sha(p) for p in M.REQUIRED_OUTPUTS}}
        self.save()
    def write(self,p,data):
        x=self.root/p;x.parent.mkdir(parents=True,exist_ok=True);x.write_bytes(data)
    def put(self,p,d):self.write(p,json.dumps(d).encode())
    def sha(self,p):return hashlib.sha256((self.root/p).read_bytes()).hexdigest()
    def save(self):self.put(M.MANIFEST_PATH,self.manifest)
    def capture(self):
        e=A.Evidence(self.root);s=M.capture_report(e,A,now=self.now);return e,s
    def trial(self):
        root=M.STAGE_ROOT;config={'id':'t00','family':'temporal','budget':.05}
        self.put(root+'/protocol.json',{'evaluation_folds':['primary','recent'],'required_prediction_files':['primary.parquet','recent.parquet']})
        self.put(root+'/configs.json',[config]);unit=root+'/trials/t00'
        self.put(unit+'/model.json',{'coefficients':[.01,.02]})
        for p in ['primary.parquet','recent.parquet']:self.write(unit+'/'+p,b'private saved predictions')
        receipt={'status':'PASS','id':'t00','config':config,'real_model_fits':1,'files_sha256':{p:self.sha(unit+'/'+p) for p in ['model.json','primary.parquet','recent.parquet']}}
        self.put(unit+'/receipt.json',receipt)
        result={'status':'PASS','id':'t00','config':config,'real_model_fits':1,'metrics':{'primary':{},'recent':{}},
            'receipt_sha256':self.sha(unit+'/receipt.json'),'model_sha256':self.sha(unit+'/model.json')}
        self.put(unit+'/result.json',result)
        return unit,result
    def test_exact_report_scope(self):
        e,s=self.capture();self.assertEqual(s['snapshot_id'],'fixture')
        self.assertEqual(set(e.files),set(M.REQUIRED_OUTPUTS)|set(M.REQUIRED_SOURCES)|{M.MANIFEST_PATH,M.PUBLISHER_PATH})
    def test_output_and_source_tampering(self):
        self.write('README.md',b'changed')
        with self.assertRaises(A.Refused):self.capture()
    def test_stale_future_and_missing_timezone(self):
        for stamp in [(self.now-timedelta(seconds=901)).isoformat(),(self.now+timedelta(seconds=121)).isoformat(),self.now.replace(tzinfo=None).isoformat()]:
            self.manifest['created_utc']=stamp;self.save()
            with self.assertRaises(ValueError):self.capture()
    def test_outside_outputs_and_sources(self):
        self.manifest['outputs_sha256']['private/data.csv']='a'*64;self.save()
        with self.assertRaises(ValueError):self.capture()
        del self.manifest['outputs_sha256']['private/data.csv'];self.manifest['source_sha256']['submission/new.py']='b'*64;self.save()
        with self.assertRaises(ValueError):self.capture()
    def test_private_models_predictions_runtime_not_captured(self):
        unit,result=self.trial();self.put(M.STAGE_ROOT+'/completion/selection_frozen.json',{'coefficients':[.01]})
        self.put(M.STAGE_ROOT+'/controller_state/state.json',{'private_pid':12})
        self.put(M.STAGE_ROOT+'/runtime_checks/launch_ready.json',{'private':True})
        e=A.Evidence(self.root);M.capture_stage(e)
        self.assertIn(unit+'/receipt.json',e.files);self.assertIn(unit+'/result.json',e.files)
        self.assertFalse(any('model.json' in p or '.parquet' in p or '/controller_state/' in p or '/runtime_checks/' in p or 'selection_frozen' in p for p in e.files))
        self.assertNotIn(b'coefficients',b'\n'.join(e.files.values()))
    def test_missing_or_changed_private_artifact_blocks_completed_publication(self):
        unit,result=self.trial();self.write(unit+'/primary.parquet',b'tampered')
        with self.assertRaises(ValueError):M.capture_stage(A.Evidence(self.root))
    def test_learned_model_embedded_in_result_rejected(self):
        unit,result=self.trial();result['nested']={'transport_model':{'coefficients':[.1]}};self.put(unit+'/result.json',result)
        with self.assertRaises(ValueError):M.capture_stage(A.Evidence(self.root))
    def test_completed_fold_or_fit_mismatch_rejected(self):
        unit,result=self.trial();del result['metrics']['recent'];self.put(unit+'/result.json',result)
        with self.assertRaises(ValueError):M.capture_stage(A.Evidence(self.root))
    def test_source_pin_cannot_reach_model_or_private_paths(self):
        self.trial();self.put(M.STAGE_ROOT+'/publication_pins.json',{'source_sha256':{'submission/private/model.json':'a'*64}})
        with self.assertRaises(ValueError):M.capture_stage(A.Evidence(self.root))
    def test_exact_shared_validator_pin_required(self):
        self.trial();relative='submission/validate_artifacts.py'
        self.write(relative,(M.ROOT/relative).read_bytes())
        protocol=json.loads((self.root/M.STAGE_ROOT/'protocol.json').read_text())
        protocol['source_sha256']={relative:M.SHARED_SOURCE_PINS[relative]}
        self.put(M.STAGE_ROOT+'/protocol.json',protocol)
        evidence=A.Evidence(self.root);M.capture_stage(evidence)
        self.assertEqual(evidence.files[relative],(M.ROOT/relative).read_bytes())
        # A plausible path with changed bytes and a self-consistent new pin
        # cannot use this shared-validator exception.
        self.write(relative,b'# changed validator\n')
        protocol['source_sha256'][relative]=self.sha(relative)
        self.put(M.STAGE_ROOT+'/protocol.json',protocol)
        with self.assertRaisesRegex(ValueError,'Shared validator source pin changed'):
            M.capture_stage(A.Evidence(self.root))
    def test_pending_old_snapshot_does_not_claim_requested_report(self):
        e,s=self.capture()
        class Client:
            def publish(self,evidence):return {'status':'PUSHED','commit':'x'}
            def git(self,*args,**kwargs):return SimpleNamespace(returncode=0,stdout=b'old snapshot')
        result=M.publish_snapshot(A,e,s,Client());self.assertFalse(result['requested_readme_snapshot_in_commit'])
        class Current(Client):
            def git(self,*args,**kwargs):return SimpleNamespace(returncode=0,stdout=e.files[M.MANIFEST_PATH])
        self.assertTrue(M.publish_snapshot(A,e,s,Current())['requested_readme_snapshot_in_commit'])
    def test_csv_part_gap_rejected(self):
        self.manifest['outputs_sha256'][M.OVERVIEW+'/experiments_part_002.csv']='a'*64;self.save()
        with self.assertRaises(ValueError):self.capture()

if __name__=='__main__':unittest.main()
