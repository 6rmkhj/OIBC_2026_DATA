# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/mono_run.py --prepare; --run needs root release.
"""Prefit barrier followed only on release by twelve serial native workers."""
import json
import msvcrt
import os
from pathlib import Path
import subprocess
import sys
from mono_common import ROOT,OUT,FOLDS,ARMS,environment,freeze,install_frozen,require_release,configure,resource,child_identity,ensure_terminal,save,digest,now

def launch(arm: str, fold: str, seed: int) -> None:
    directory = OUT/'trials'/arm/fold/f'seed{seed}'
    directory.mkdir(parents=True,exist_ok=False)
    command = [sys.executable,str(Path(__file__).with_name('mono_fit.py')),arm,fold,str(seed)]
    save(directory/'launch_checkpoint.json',{'command':command,'utc':now(),'protocol_sha256':digest(OUT/'protocol.json')})
    with (directory/'fit.log').open('w',encoding='utf-8') as log:
        with subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy(),creationflags=subprocess.NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW) as process:
            identity = child_identity(process.pid)
            started = now()
            code = process.wait()
        ensure_terminal(identity)
    save(directory/'controller_receipt.json',{'exit_code':code,'identity':identity,'started_utc':started,'finished_utc':now(),'exact_worker_absent':True,'new_model_fits':1 if code==0 else None})
    assert code==0,f'See {directory}/fit.log'
    status = json.loads((directory/'worker_status.json').read_text(encoding='utf-8'))
    assert status['state']=='complete' and status['model_sha256']==digest(directory/'model.txt') and status['new_model_fits']==1
    print('MONO TRIAL TERMINAL',arm,fold,seed,flush=True)

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
                from mono_math import self_check
                from mono_prepare import prepare
                fixtures = self_check()
                save(OUT/'evidence/selfchecks.json',{'passed':True,'utc':now(),'fixtures':fixtures,'real_model_fits':0})
                prepare()
                preservation()
                assert not list(OUT.rglob('model.txt')) and not (OUT/'trials').exists()
                save(OUT/'evidence/prefit_checks.json',{'passed':True,'identity':resource(),'utc':now(),'protocol_sha256':digest(OUT/'protocol.json'),'prepared_manifest_sha256':digest(OUT/'prepared_manifest.json'),'real_model_fits':0,'real_calibration_fits':0,'release_required':True})
                print('MONO PREFIT READY',flush=True)
                return
            require_release()
            save(OUT/'controller_start.json',{'identity':resource(),'utc':now(),'model_fit_budget':12})
            for arm in ARMS:
                for fold in FOLDS:
                    for seed in (0,1,2):
                        launch(arm,fold,seed)
            from mono_score import compare
            records = [compare(arm) for arm in ARMS]
            eligible = [r for r in records if r['eligible']]
            selected = min(eligible,key=lambda r:r['mean_relative_W']) if eligible else None
            control,monotone = records
            matched = {fold:{kind:{'control_W':control['scores'][fold][kind]['W'],'monotone_W':monotone['scores'][fold][kind]['W'],'monotone_minus_control_W':monotone['scores'][fold][kind]['W']-control['scores'][fold][kind]['W'],'control_W_pct':control['scores'][fold][kind]['W_pct'],'monotone_W_pct':monotone['scores'][fold][kind]['W_pct']} for kind in ('p_new','p')} for fold in FOLDS}
            save(OUT/'results.json',{'records':records,'selected':selected,'eligible':bool(eligible),'reference_retained':selected is None,'matched_fair_comparison':matched,'real_model_fit_count':12,'real_calibration_fit_count':0,'candidate_count':2,'confirmation_loaded':False,'test_loaded':False,'exported':False,'all_history_exposed':True})
            preservation()
            save(OUT/'controller_receipt.json',{'exit_code':0,'identity':resource(),'finished_utc':now(),'real_model_fit_count':12,'real_calibration_fit_count':0})
            print('MONO WAVE TERMINAL',flush=True)

if __name__=='__main__':
    main()
