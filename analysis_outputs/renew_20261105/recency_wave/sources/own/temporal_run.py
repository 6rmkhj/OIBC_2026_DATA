# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/temporal_run.py [--prepare]
"""Serial 24-fit controller; completed artifacts are immutable retry checkpoints."""
from temporal_common import ROOT, OUT, FOLDS, VARIANTS, digest, save, now, install_frozen, configure, resource, child_identity
from temporal_prepare import freeze, prepare
from pathlib import Path
import json
import os
import subprocess
import sys
import msvcrt

def launch(variant: str, fold: str, seed: int) -> None:
    from gpu_run import ensure_inactive
    directory = OUT/'trials'/variant/fold/f'seed{seed}'
    directory.mkdir(parents=True,exist_ok=True)
    status_file = directory/'worker_status.json'
    if status_file.exists():
        status = json.loads(status_file.read_text())
        if status['state']=='complete':
            assert digest(directory/'model.txt')==status['model_sha256']
            assert digest(directory/'daylight_raw.parquet')==status['raw_sha256']
            assert json.loads((directory/'replay.json').read_text())['passed']
            return
    for status in (OUT/'trials').rglob('worker_status.json'):
        ensure_inactive(status.parent)
    command = [sys.executable,str(Path(__file__).with_name('temporal_fit.py')),variant,fold,str(seed)]
    save(directory/'launch_checkpoint.json',{'utc':now(),'command':command,'protocol_sha256':digest(OUT/'protocol.json')})
    with (directory/'fit.log').open('a',encoding='utf-8') as log:
        with subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy(),creationflags=subprocess.NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW) as process:
            identity = child_identity(process.pid)
            save(directory/'worker_status.json',{'state':'starting','identity':identity,'utc':now()})
            started = now()
            code = process.wait()
    # force exact identity absence check even when the worker completed its receipt.
    identity_path = directory/'terminal_identity'
    identity_path.mkdir(exist_ok=True)
    save(identity_path/'worker_status.json',{'state':'terminal_check','identity':identity})
    ensure_inactive(identity_path)
    save(directory/'controller_receipt.json',{'exit_code':code,'started_utc':started,'finished_utc':now(),'identity':identity,'exact_worker_absent':True})
    assert code==0, f'See {directory}/fit.log'
    print('TRIAL TERMINAL',variant,fold,seed,flush=True)

def main() -> None:
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'controller.lock').open('a+b') as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        freeze()
        install_frozen()
        configure()
        from threadpoolctl import threadpool_limits
        from temporal_score import compare
        with threadpool_limits(limits=16):
            if not (OUT/'evidence/prefit_checks.json').exists():
                prepare()
            protocol = json.loads((OUT/'protocol.json').read_text())
            assert all(digest(ROOT/p)==sha for p,sha in protocol['input_sha256'].items())
            if sys.argv[1:]==['--prepare']:
                print('PREFIT READY',flush=True)
                return
            assert not sys.argv[1:]
            save(OUT/'controller_start.json',{'identity':resource(),'utc':now(),'environment':{k:os.environ.get(k) for k in ('TMPDIR','TMP','TEMP','NODE_COMPILE_CACHE','BUN_RUNTIME_TRANSPILER_CACHE_PATH','PYTHONDONTWRITEBYTECODE','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}})
            for variant in VARIANTS:
                for fold in FOLDS:
                    for seed in (0,1,2):
                        launch(variant,fold,seed)
            records = [compare(v) for v in VARIANTS]
            eligible = [r for r in records if r['eligible']]
            selected = min(eligible,key=lambda r:r['mean_relative_W']) if eligible else None
            save(OUT/'results.json',{'records':records,'selected':selected,'cpu_reference_retained':selected is None,'confirmation_loaded':False,'test_loaded':False,'model_fit_count':24})
            after = {p:digest(ROOT/p) for p in protocol['protected_sha256']}
            assert after==protocol['protected_sha256']
            save(OUT/'preservation.json',{'unchanged':True,'files':len(after),'sha256':after})
            save(OUT/'controller_receipt.json',{'exit_code':0,'finished_utc':now(),'all_trial_controllers_terminal':True,'identity':resource(),'model_fit_count':24})
            save(OUT/'artifact_hashes.json',{str(p.relative_to(OUT)):digest(p) for p in OUT.rglob('*') if p.is_file() and p.name not in ('artifact_hashes.json','controller.lock','controller.log')})
            print('TEMPORAL WAVE TERMINAL',selected['variant'] if selected else 'CPU REFERENCE RETAINED',flush=True)

if __name__=='__main__':
    main()
