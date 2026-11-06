# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/total_run.py --prepare; then --run after release.json.
"""Immutable 12-fit serial controller, with explicit prefit release barrier."""
import json
import os
from pathlib import Path
import subprocess
import sys
import msvcrt
from total_common import OUT, ROOT, ARMS, FOLDS, environment, install_frozen, check_inputs, configure, resource, child_identity, ensure_terminal, save, digest, now


def launch(arm: str, fold: str, seed: int) -> None:
    directory = OUT/'trials'/arm/fold/f'seed{seed}'
    directory.mkdir(parents=True,exist_ok=True)
    status_path = directory/'worker_status.json'
    if status_path.exists():
        status = json.loads(status_path.read_text())
        ensure_terminal(status['identity'])
        if status['state']=='complete':
            assert digest(directory/'model.txt')==status['model_sha256']
            assert digest(directory/'total_raw.parquet')==status['raw_sha256']
            assert json.loads((directory/'replay.json').read_text())['passed']
            assert json.loads((directory/'controller_receipt.json').read_text())['exit_code']==0
            return
    for status in (OUT/'trials').rglob('worker_status.json'):
        ensure_terminal(json.loads(status.read_text())['identity'])
    command = [sys.executable,str(Path(__file__).with_name('total_fit.py')),arm,fold,str(seed)]
    save(directory/'launch_checkpoint.json',{'utc':now(),'command':command,'protocol_sha256':digest(OUT/'protocol.json')})
    with (directory/'fit.log').open('a',encoding='utf-8') as log:
        with subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy(),creationflags=subprocess.NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW) as process:
            identity = child_identity(process.pid)
            save(directory/'worker_status.json',{'state':'starting','identity':identity,'utc':now()})
            started = now()
            code = process.wait()
    ensure_terminal(identity)
    save(directory/'controller_receipt.json',{'exit_code':code,'started_utc':started,'finished_utc':now(),'identity':identity,'exact_worker_absent':True})
    assert code==0,f'See {directory}/fit.log'
    print('TRIAL TERMINAL',arm,fold,seed,flush=True)


def main() -> None:
    environment()
    from total_prepare import freeze, prepare
    with (OUT/'controller.lock').open('a+b') as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        freeze()
        install_frozen()
        configure()
        from threadpoolctl import threadpool_limits
        from total_checks import self_check
        from total_score import compare
        with threadpool_limits(limits=16):
            check_inputs()
            if sys.argv[1:]==['--prepare']:
                self_check()
                prepare()
                save(OUT/'evidence/prefit_checks.json',{'passed':True,'utc':now(),'protocol_sha256':digest(OUT/'protocol.json'),'prepared_manifest_sha256':digest(OUT/'prepared_manifest.json'),'identity':resource(),'real_model_fits':0})
                print('PREFIT READY',flush=True)
                return
            assert sys.argv[1:]==['--run']
            release = json.loads((OUT/'release.json').read_text())
            assert release['approved'] and release['protocol_sha256']==digest(OUT/'protocol.json') and release['prepared_manifest_sha256']==digest(OUT/'prepared_manifest.json')
            save(OUT/'controller_start.json',{'identity':resource(),'utc':now(),'environment':{k:os.environ.get(k) for k in ('TMPDIR','TMP','TEMP','NODE_COMPILE_CACHE','BUN_RUNTIME_TRANSPILER_CACHE_PATH','PYTHONDONTWRITEBYTECODE','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}})
            for arm in ARMS:
                for fold in FOLDS:
                    for seed in (0,1,2):
                        launch(arm,fold,seed)
            records = [compare(arm) for arm in ARMS]
            eligible = [r for r in records if r['eligible']]
            selected = min(eligible,key=lambda r:r['mean_relative_W']) if eligible else None
            save(OUT/'results.json',{'records':records,'selected':selected,'reference_retained':selected is None,'confirmation_loaded':False,'test_loaded':False,'real_model_fit_count':12})
            protocol = json.loads((OUT/'protocol.json').read_text())
            after = {p:digest(ROOT/p) for p in protocol['protected_sha256']}
            assert after==protocol['protected_sha256']
            save(OUT/'preservation.json',{'unchanged':True,'files':len(after),'sha256':after})
            save(OUT/'controller_receipt.json',{'exit_code':0,'finished_utc':now(),'all_trial_controllers_terminal':True,'identity':resource(),'real_model_fit_count':12})
            save(OUT/'artifact_hashes.json',{str(p.relative_to(OUT)):digest(p) for p in OUT.rglob('*') if p.is_file() and p.name not in ('artifact_hashes.json','controller.lock','controller.log') and 'tmp' not in p.relative_to(OUT).parts})
            print('TOTAL WAVE TERMINAL',selected['arm'] if selected else 'REFERENCE RETAINED',flush=True)

if __name__=='__main__':
    main()
