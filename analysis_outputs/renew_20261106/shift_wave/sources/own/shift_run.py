# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "joblib", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/shift_run.py --prepare; --run only after root release.
"""Prefit barrier, six serial domain fits, six generation fits and one alpha."""
import json
import msvcrt
import os
from pathlib import Path
import subprocess
import sys
from shift_common import ROOT,OUT,FOLDS,environment,freeze,install_frozen,require_release,configure,resource,child_identity,ensure_terminal,save,digest,now

def launch(fold: str, index: int, is_domain: bool) -> None:
    directory = OUT/'domain_trials'/fold/f'split{index}' if is_domain else OUT/'trials'/fold/f'seed{index}'
    module = 'shift_domain.py' if is_domain else 'shift_fit.py'
    directory.mkdir(parents=True,exist_ok=False)
    command = [sys.executable,str(Path(__file__).with_name(module)),fold,str(index)]
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
    model,key = ('classifier.joblib','classifier_sha256') if is_domain else ('model.txt','model_sha256')
    assert status['state']=='complete' and status[key]==digest(directory/model)
    print('SHIFT TRIAL TERMINAL',module,fold,index,flush=True)

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
                import numpy as np
                import shift_math
                from shift_prepare import prepare
                fixtures = shift_math.self_check()
                original = shift_math.density_weights
                def squared_modifier(logit: np.ndarray,base: np.ndarray) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
                    ratio,modifier,_ = original(logit,base)
                    modifier = modifier**2
                    return ratio,modifier,base*modifier*base.sum()/(base*modifier).sum()
                rejected = False
                shift_math.density_weights = squared_modifier
                try:
                    shift_math.self_check()
                except AssertionError:
                    rejected = True
                finally:
                    shift_math.density_weights = original
                assert rejected and shift_math.self_check()==fixtures
                save(OUT/'evidence/selfchecks.json',{'passed':True,'utc':now(),'fixtures':fixtures,'mutation_rejected':'incorrect_squared_modifier','baseline_restored':True,'production_files_modified':False,'real_model_fits':0,'real_domain_fits':0,'real_generation_fits':0})
                prepare()
                protocol = json.loads((OUT/'protocol.json').read_text())
                after = {p:digest(ROOT/p) for p in protocol['protected_sha256']}
                assert after==protocol['protected_sha256']
                save(OUT/'preservation.json',{'unchanged':True,'files':len(after),'sha256':after})
                assert not (OUT/'domain_trials').exists() and not (OUT/'trials').exists() and not list(OUT.rglob('*.joblib')) and not list(OUT.rglob('model.txt'))
                save(OUT/'evidence/prefit_checks.json',{'passed':True,'identity':resource(),'utc':now(),'protocol_sha256':digest(OUT/'protocol.json'),'prepared_manifest_sha256':digest(OUT/'prepared_manifest.json'),'real_model_fit_count':0,'real_domain_fit_count':0,'real_generation_fit_count':0,'real_alpha_fit_count':0})
                print('SHIFT PREFIT READY',flush=True)
                return
            assert sys.argv[1:]==['--run']
            require_release()
            save(OUT/'controller_start.json',{'identity':resource(),'utc':now(),'model_fit_budget':12,'domain_fit_budget':6,'generation_fit_budget':6,'alpha_fit_budget':1})
            for fold in FOLDS:
                for split in (0,1,2):
                    launch(fold,split,True)
            from shift_domain import combine_weights
            combine_weights()
            for fold in FOLDS:
                for seed in (0,1,2):
                    launch(fold,seed,False)
            from shift_score import compare
            record = compare()
            counts = {'real_model_fit_count':12,'real_domain_fit_count':6,'real_generation_fit_count':6,'real_calibration_fit_count':0,'real_alpha_fit_count':1}
            save(OUT/'results.json',{'records':[record],'selected':record if record['eligible'] else None,'eligible':record['eligible'],'reference_retained':not record['eligible'],**counts,'candidate_count':1,'confirmation_loaded':False,'test_loaded':False,'exported':False,'all_history_exposed':True,'transductive_future_weather':True})
            protocol = json.loads((OUT/'protocol.json').read_text())
            after = {p:digest(ROOT/p) for p in protocol['protected_sha256']}
            assert after==protocol['protected_sha256']
            save(OUT/'preservation.json',{'unchanged':True,'files':len(after),'sha256':after})
            save(OUT/'controller_receipt.json',{'exit_code':0,'identity':resource(),'finished_utc':now(),**counts})
            print('SHIFT WAVE TERMINAL',flush=True)

if __name__=='__main__':
    main()
