# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "catboost", "lightgbm", "threadpoolctl"]
# ///
"""Serial cloud-wave controller with immutable prefit and terminal receipts."""
from cloud_common import ROOT, OUT, FOLDS, CUTOFFS, PROVIDERS, ARMS, save, digest, now, install_frozen, configure, resource, child_identity, ensure_terminal
from cloud_prepare import freeze
from pathlib import Path
import json
import os
import subprocess
import sys
import time
import msvcrt


def launch(stage: str, arguments: list[str], directory: Path) -> None:
    directory.mkdir(parents=True,exist_ok=True)
    model_name = 'model.cbm' if stage=='aux' else 'model.txt'
    raw_name = 'predictions.parquet' if stage=='aux' else 'daylight_raw.parquet'
    status_file = directory/'worker_status.json'
    if status_file.exists():
        status = json.loads(status_file.read_text())
        ensure_terminal(status['identity'])
        if status['state']=='complete':
            assert digest(directory/model_name)==status['model_sha256']
            assert digest(directory/raw_name)==status['raw_sha256']
            assert json.loads((directory/'replay.json').read_text())['passed']
            assert json.loads((directory/'controller_receipt.json').read_text())['exit_code']==0
            return
    for root in (OUT/'auxiliary',OUT/'trials'):
        for path in root.rglob('worker_status.json'):
            ensure_terminal(json.loads(path.read_text())['identity'])
    filename = 'cloud_aux.py' if stage=='aux' else 'cloud_generation.py'
    command = [sys.executable,str(Path(__file__).with_name(filename)),*arguments]
    started = now()
    save(directory/'launch_checkpoint.json',{'utc':started,'command':command,'protocol_sha256':digest(OUT/'protocol.json')})
    with (directory/'fit.log').open('a',encoding='utf-8') as log, (directory/'gpu_samples.csv').open('a',encoding='utf-8') as samples:
        with subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy(),creationflags=subprocess.NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW) as process:
            identity = child_identity(process.pid)
            save(directory/'worker_status.json',{'state':'starting','identity':identity,'utc':now()})
            while process.poll() is None:
                if stage=='aux':
                    sample = subprocess.run(['nvidia-smi','--query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total,power.draw','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW,check=True)
                    samples.write(sample.stdout)
                    samples.flush()
                time.sleep(1)
            code = process.wait()
        ensure_terminal(identity)
    save(directory/'controller_receipt.json',{'exit_code':code,'started_utc':started,'finished_utc':now(),'identity':identity,'exact_worker_absent':True})
    assert code==0,f'See {directory}/fit.log'
    print('FIT TERMINAL',stage,*arguments,flush=True)


def main() -> None:
    OUT.mkdir(parents=True,exist_ok=True)
    temporary = OUT/'tmp'
    temporary.mkdir(exist_ok=True)
    for name in ('TMPDIR','TMP','TEMP','NODE_COMPILE_CACHE','BUN_RUNTIME_TRANSPILER_CACHE_PATH'):
        os.environ[name]=str(temporary)
    os.environ['PYTHONDONTWRITEBYTECODE']='1'
    with (OUT/'controller.lock').open('a+b') as lock:
        lock.seek(0)
        msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        freeze()
        install_frozen()
        configure()
        from threadpoolctl import threadpool_limits
        from cloud_panel import prepare_panels, self_check
        from cloud_aggregate import aggregate
        from cloud_score import compare
        with threadpool_limits(limits=16):
            protocol = json.loads((OUT/'protocol.json').read_text())
            assert all(digest(ROOT/p)==sha for p,sha in protocol['input_sha256'].items())
            if not (OUT/'evidence/prefit_checks.json').exists():
                self_check()
            prepare_panels()
            if sys.argv[1:]==['--prepare']:
                print('CLOUD PREFIT READY',flush=True)
                return
            assert not sys.argv[1:]
            save(OUT/'controller_start.json',{'identity':resource(),'utc':now(),'owned_temp':str(temporary),'environment':{k:os.environ.get(k) for k in ('TMPDIR','TMP','TEMP','PYTHONDONTWRITEBYTECODE','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}})
            for provider in PROVIDERS:
                for cutoff in CUTOFFS:
                    launch('aux',[provider,cutoff],OUT/'auxiliary'/provider/cutoff)
            aggregate()
            for arm in ARMS:
                for fold in FOLDS:
                    for seed in (0,1,2):
                        launch('generation',[arm,fold,str(seed)],OUT/'trials'/arm/fold/f'seed{seed}')
            records = [compare(arm) for arm in ARMS]
            eligible = [record for record in records if record['eligible']]
            selected = min(eligible,key=lambda r:r['mean_relative_W']) if eligible else None
            save(OUT/'results.json',{'records':records,'selected':selected,'temporal_reference_retained':selected is None,'confirmation_loaded':False,'test_loaded':False,'auxiliary_fit_count':14,'generation_fit_count':12,'upstream_seeds':[0],'robust_adoption':False})
            after = {p:digest(ROOT/p) for p in protocol['protected_sha256']}
            assert after==protocol['protected_sha256']
            save(OUT/'preservation.json',{'unchanged':True,'files':len(after),'sha256':after})
            save(OUT/'controller_receipt.json',{'exit_code':0,'finished_utc':now(),'identity':resource(),'all_trial_controllers_terminal':True,'auxiliary_fit_count':14,'generation_fit_count':12})
            save(OUT/'artifact_hashes.json',{str(p.relative_to(OUT)):digest(p) for p in OUT.rglob('*') if p.is_file() and 'tmp' not in p.parts and p.name not in ('artifact_hashes.json','controller.lock','controller.log')})
            print('CLOUD WAVE TERMINAL',selected['variant'] if selected else 'TEMPORAL REFERENCE RETAINED',flush=True)


if __name__=='__main__':
    main()
