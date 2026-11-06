# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "scikit-learn", "joblib", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/bound_run.py
"""One frozen bounds recipe and six serial native inferences, no training."""
import json
import msvcrt
import os
from pathlib import Path
import subprocess
import sys
from bound_common import ROOT,OUT,MLP,FOLDS,environment,freeze,install_frozen,check_prepared,configure,resource,child_identity,ensure_terminal,save,digest,now

def launch(fold: str, seed: int) -> None:
    directory = OUT/'trials'/fold/f'seed{seed}'
    directory.mkdir(parents=True,exist_ok=False)
    command = [sys.executable,str(Path(__file__).with_name('bound_infer.py')),fold,str(seed)]
    save(directory/'launch_checkpoint.json',{'command':command,'utc':now(),'protocol_sha256':digest(OUT/'protocol.json')})
    with (directory/'inference.log').open('w',encoding='utf-8') as log:
        with subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy(),creationflags=subprocess.NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW) as process:
            identity = child_identity(process.pid)
            started = now()
            code = process.wait()
    ensure_terminal(identity)
    save(directory/'controller_receipt.json',{'exit_code':code,'identity':identity,'started_utc':started,'finished_utc':now(),'exact_worker_absent':True,'new_model_fits':0})
    assert code==0,f'See {directory}/inference.log'
    status = json.loads((directory/'worker_status.json').read_text(encoding='utf-8'))
    assert status['state']=='complete' and status['source_model_sha256']==digest(MLP/'trials'/fold/f'seed{seed}'/'model.joblib')
    print('BOUND INFERENCE TERMINAL',fold,seed,flush=True)

def main() -> None:
    environment()
    with (OUT/'controller.lock').open('a+b') as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        freeze()
        install_frozen()
        configure()
        from threadpoolctl import threadpool_limits
        from bound_prepare import self_check,prepare
        with threadpool_limits(limits=16):
            save(OUT/'controller_start.json',{'identity':resource(),'utc':now(),'new_model_fits':0,'inference_budget':6})
            fixtures = self_check()
            save(OUT/'evidence/selfchecks.json',{'passed':True,'utc':now(),'fixtures':fixtures,'new_model_fits':0})
            prepare()
            check_prepared()
            for fold in FOLDS:
                for seed in (0,1,2):
                    launch(fold,seed)
            from bound_score import compare
            record = compare()
            save(OUT/'results.json',{'records':[record],'selected':record if record['eligible'] else None,'eligible':record['eligible'],'reference_retained':not record['eligible'],'real_model_fit_count':0,'real_inference_count':6,'bounds_transform_count':2,'real_calibration_fit_count':0,'candidate_count':1,'confirmation_loaded':False,'test_loaded':False,'exported':False,'all_history_exposed':True})
            protocol = json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
            after = {path:digest(ROOT/path) for path in protocol['protected_sha256']}
            assert after==protocol['protected_sha256']
            save(OUT/'preservation.json',{'unchanged':True,'files':len(after),'sha256':after})
            save(OUT/'controller_receipt.json',{'exit_code':0,'identity':resource(),'finished_utc':now(),'real_model_fit_count':0,'real_inference_count':6,'bounds_transform_count':2})
            print('BOUNDS WAVE TERMINAL',flush=True)
if __name__=='__main__':
    main()
