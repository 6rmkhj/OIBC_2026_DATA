# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "scikit-learn", "joblib", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/extra_run.py --prepare; --run ONLY after root release.
"""Prefit barrier and six serial fixed ExtraTrees workers."""
import json
import msvcrt
import os
from pathlib import Path
import subprocess
import sys
from extra_common import ROOT,OUT,FOLDS,environment,freeze,install_frozen,require_release,configure,resource,child_identity,ensure_terminal,save,digest,now

def launch(fold: str, seed: int) -> None:
    directory = OUT/'trials'/fold/f'seed{seed}'
    directory.mkdir(parents=True,exist_ok=False)
    command = [sys.executable,str(Path(__file__).with_name('extra_fit.py')),fold,str(seed)]
    save(directory/'launch_checkpoint.json',{'command':command,'utc':now(),'protocol_sha256':digest(OUT/'protocol.json')})
    with (directory/'fit.log').open('w',encoding='utf-8') as log:
        with subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy(),creationflags=subprocess.NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW) as process:
            identity = child_identity(process.pid)
            started = now()
            code = process.wait()
    ensure_terminal(identity)
    save(directory/'controller_receipt.json',{'exit_code':code,'identity':identity,'started_utc':started,'finished_utc':now(),'exact_worker_absent':True})
    assert code==0,f'See {directory}/fit.log'
    status = json.loads((directory/'worker_status.json').read_text(encoding='utf-8'))
    assert status['state']=='complete' and status['model_sha256']==digest(directory/'model.joblib')
    print('EXTRA TRIAL TERMINAL',fold,seed,flush=True)

def main() -> None:
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
                from extra_math import self_check
                from extra_prepare import prepare
                fixtures = self_check()
                save(OUT/'evidence/selfchecks.json',{'passed':True,'utc':now(),'fixtures':fixtures,'real_model_fits':0})
                prepare()
                protocol = json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
                after = {p:digest(ROOT/p) for p in protocol['protected_sha256']}
                assert after==protocol['protected_sha256']
                save(OUT/'preservation.json',{'unchanged':True,'files':len(after),'sha256':after})
                assert not (OUT/'trials').exists() and not list(OUT.rglob('model.joblib'))
                save(OUT/'evidence/prefit_checks.json',{'passed':True,'identity':resource(),'utc':now(),'protocol_sha256':digest(OUT/'protocol.json'),'prepared_manifest_sha256':digest(OUT/'prepared_manifest.json'),'real_model_fits':0,'real_calibration_fits':0})
                print('EXTRA PREFIT READY',flush=True)
                return
            assert sys.argv[1:]==['--run']
            require_release()
            save(OUT/'controller_start.json',{'identity':resource(),'utc':now(),'model_fit_budget':6})
            for fold in FOLDS:
                for seed in (0,1,2):
                    launch(fold,seed)
            from extra_score import compare
            record = compare()
            save(OUT/'results.json',{'records':[record],'selected':record if record['eligible'] else None,'eligible':record['eligible'],'reference_retained':not record['eligible'],'real_model_fit_count':6,'real_calibration_fit_count':0,'candidate_count':1,'confirmation_loaded':False,'test_loaded':False,'exported':False,'all_history_exposed':True})
            protocol = json.loads((OUT/'protocol.json').read_text(encoding='utf-8'))
            after = {p:digest(ROOT/p) for p in protocol['protected_sha256']}
            assert after==protocol['protected_sha256']
            save(OUT/'preservation.json',{'unchanged':True,'files':len(after),'sha256':after})
            save(OUT/'controller_receipt.json',{'exit_code':0,'identity':resource(),'finished_utc':now(),'real_model_fit_count':6,'real_calibration_fit_count':0})
            print('EXTRA WAVE TERMINAL',flush=True)
if __name__=='__main__':
    main()
