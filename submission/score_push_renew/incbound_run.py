# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "scikit-learn", "joblib", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/incbound_run.py --prepare; --run needs root release.
"""Inference-only prefit barrier and six serial native historical MLP workers."""
import json
import msvcrt
import os
from pathlib import Path
import subprocess
import sys
from incbound_common import ROOT,OUT,FOLDS,environment,freeze,install_frozen,require_release,configure,resource,child_identity,ensure_terminal,save,digest,now

def launch(fold: str, seed: int) -> None:
    directory = OUT/'trials'/fold/f'seed{seed}'
    directory.mkdir(parents=True,exist_ok=False)
    command = [sys.executable,str(Path(__file__).with_name('incbound_infer.py')),fold,str(seed)]
    save(directory/'launch_checkpoint.json',{'command':command,'utc':now(),'protocol_sha256':digest(OUT/'protocol.json')})
    with (directory/'inference.log').open('w',encoding='utf-8') as log:
        with subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy(),creationflags=subprocess.NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW) as process:
            identity = child_identity(process.pid)
            started = now()
            code = process.wait()
        ensure_terminal(identity)
    save(directory/'controller_receipt.json',{'exit_code':code,'identity':identity,'started_utc':started,'finished_utc':now(),'exact_worker_absent':True,'new_model_fits':0,'native_model_inferences':2 if code==0 else None})
    assert code==0,f'See {directory}/inference.log'
    status = json.loads((directory/'worker_status.json').read_text(encoding='utf-8'))
    assert status['state']=='complete' and status['new_model_fits']==0 and status['native_model_inferences']==2
    print('INCBOUND WORKER TERMINAL',fold,seed,flush=True)

def preservation() -> None:
    protocol = json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
    after = {p:digest(ROOT/p) for p in protocol['protected_sha256']}
    assert after==protocol['protected_sha256']
    save(OUT/'preservation.json',{'unchanged':True,'files':len(after),'sha256':after})

def main() -> None:
    assert sys.argv[1:] in (['--prepare'],['--run'])
    environment()
    with (OUT/'controller.lock').open('a+b') as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        if sys.argv[1:]==['--prepare']:
            freeze()
        install_frozen()
        configure()
        from threadpoolctl import threadpool_limits
        with threadpool_limits(limits=16):
            if sys.argv[1:]==['--prepare']:
                from incbound_math import self_check
                from incbound_prepare import prepare
                from incbound_lineage import prepare_lineage
                fixtures = self_check()
                save(OUT/'evidence/selfchecks.json',{'passed':True,'fixtures':fixtures,'utc':now(),'model_loads':0,'model_inferences':0,'real_model_fits':0})
                prepare()
                prepare_lineage()
                manifest = {str(p.relative_to(OUT)):digest(p) for p in (OUT/'data').rglob('*') if p.is_file()}
                for name in ('lineage.json','evidence/read_receipts.json','evidence/selfchecks.json'):
                    manifest[name] = digest(OUT/name)
                save(OUT/'prepared_manifest.json',manifest)
                preservation()
                assert not (OUT/'trials').exists() and not list(OUT.rglob('model.joblib'))
                save(OUT/'evidence/prefit_checks.json',{'passed':True,'identity':resource(),'utc':now(),'protocol_sha256':digest(OUT/'protocol.json'),'prepared_manifest_sha256':digest(OUT/'prepared_manifest.json'),'model_loads':0,'model_inferences':0,'real_model_fits':0,'candidate_scores_computed':0,'release_required':True})
                print('INCBOUND PREFIT READY',flush=True)
                return
            require_release()
            save(OUT/'controller_start.json',{'identity':resource(),'utc':now(),'native_worker_budget':6,'native_inference_budget':12,'real_model_fit_budget':0})
            for fold in FOLDS:
                for seed in (0,1,2):
                    launch(fold,seed)
            from incbound_score import compare
            record = compare()
            save(OUT/'results.json',{'records':[record],'selected':record if record['eligible'] else None,'eligible':record['eligible'],'reference_retained':not record['eligible'],'real_model_fit_count':0,'native_worker_count':6,'native_model_inferences':12,'real_calibration_fit_count':0,'new_weight_fits':0,'new_alpha_fits':0,'candidate_count':1,'confirmation_loaded':False,'test_loaded':False,'exported':False,'all_history_exposed':True})
            preservation()
            save(OUT/'controller_receipt.json',{'exit_code':0,'identity':resource(),'finished_utc':now(),'native_worker_count':6,'native_model_inferences':12,'real_model_fit_count':0,'real_calibration_fit_count':0})
            print('INCBOUND WAVE TERMINAL',flush=True)

if __name__=='__main__':
    main()
