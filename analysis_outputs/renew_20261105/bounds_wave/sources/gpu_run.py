# /// script
# requires-python = ">=3.12"
# dependencies = ["catboost", "numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: analysis_outputs/score_push_gpu_20261104/environment/Scripts/python.exe submission/score_push_gpu/gpu_run.py
"""Freeze and execute exactly one bounded two-variant GPU development family."""
from gpu_common import ROOT, OLD, OUT, PARAMS, FOLDS, REFERENCE, digest, save, now, install_frozen, configure, child_identity
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time


def freeze() -> None:
    if (OUT/'protocol.json').exists():
        return
    (OUT/'sources/own').mkdir(parents=True)
    (OUT/'evidence').mkdir()
    snapshots = {}
    for folder in ('autoresearch','score_push'):
        for path in (ROOT/'submission'/folder).glob('*.py'):
            shutil.copyfile(path,OUT/'sources'/path.name)
            snapshots[path.stem]={'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    own = {}
    for path in Path(__file__).parent.glob('*.py'):
        shutil.copyfile(path,OUT/'sources/own'/path.name)
        own[path.name]={'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    inputs = [OLD/p for p in ('cache/train.parquet','cache/selection.parquet','recent/cache/train.parquet','recent/cache/selection.parquet','profile_wave/cache/stations.parquet','trials/combined_physics/features.json','trials/baseline_exact/predictions.parquet')]
    inputs += [OLD/f'closing_wave/{f}/selected/predictions.parquet' for f in FOLDS]
    inputs += [ROOT/'analysis_outputs/autoresearch_20261103'/p for p in ('cache/selection_labels.parquet','cache/features.json','final/outer_predictions.parquet')]
    protected = set(inputs)
    protected.update(ROOT/r['original'] for r in snapshots.values())
    for folder in (OLD/'final',ROOT/'submission/score_push_candidate',ROOT/'submission/autoresearch_candidate'):
        protected.update(p for p in folder.rglob('*') if p.is_file() and p.suffix!='.md' and '__pycache__' not in p.parts)
    save(OUT/'protocol.json',{'created_utc':now(),'variants':['rich_cf','station_normalized'],'initial_seeds':[0],'folds':{'primary':{'train_end':'2023-06-01 Asia/Seoul','eval_end':'2024-06-01 Asia/Seoul','keys':17568},'recent':{'train_end':'2024-06-01 Asia/Seoul','eval_end':'2025-03-01 Asia/Seoul','keys':13104}},'reference_scores':REFERENCE,'parameters':PARAMS,'normalization':'station only: frozen Haurwitz floor.05, y=cf/normalizer, sample_weight=normalizer, inverse multiply normalizer then capacity','missing':'native numeric NaN Min; station train-only constant mask, rich all100 columns','selection':'Per variant primary-only optimal_weight vs complete frozen CPU reference; transfer unchanged recent. Both-fold strict gain and alpha>=.02 qualifies. One best mean-relative-W qualifier gets seeds1,2 both folds. Recalibrate three-seed average primary only; adopt only if both folds improve. Otherwise retain CPU.','budget':{'initial_fits':4,'conditional_extra_fits':4,'max_total_fits':8},'snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)},'resources':{'gpu':'RTX5090 Laptop','devices':'0','gpu_ram_part':.9,'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_fits':1},'durability_amendment':'Root authorized allow_writing_files=True only under each trial, save_snapshot=True/30sec, explicit trial-owned train_dir/snapshot_file. Scientific parameters unchanged. Completed model+replay checkpoints skipped on restart.','uncertainty':'Exploratory/adaptive historical development, not pristine holdout. CatBoost GPU training nondeterministic; saved-model replay tested. Original CPU confirmation and cutoff-diagnostic adverse results retained.','confirmation_loaded':False,'test_loaded':False,'no_fulltrain_or_export':True})


def ensure_inactive(directory: Path) -> None:
    status_file = directory/'worker_status.json'
    if not status_file.exists():
        return
    status = json.loads(status_file.read_text())
    if status['state']=='complete':
        return
    kernel = ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    kernel.GetProcessTimes.argtypes=[wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)]
    handle=kernel.OpenProcess(0x1000,False,status['identity']['pid'])
    if not handle:
        assert ctypes.get_last_error()==87,'Cannot prove prior worker is absent'
        return
    times=[wintypes.FILETIME() for _ in range(4)]
    assert kernel.GetProcessTimes(handle,*[ctypes.byref(t) for t in times])
    creation=(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime
    kernel.CloseHandle(handle)
    assert creation!=status['identity']['creation_filetime'],'Previous exact worker still active; do not duplicate'


def launch(variant: str, fold: str, seed: int) -> None:
    directory=OUT/'trials'/variant/fold/f'seed{seed}'
    directory.mkdir(parents=True,exist_ok=True)
    if (directory/'replay.json').exists() and (directory/'worker_status.json').exists():
        status=json.loads((directory/'worker_status.json').read_text())
        if status['state']=='complete':
            assert digest(directory/'model.cbm')==status['model_sha256'] and digest(directory/'daylight_raw.parquet')==status['raw_sha256']
            return
    for status in (OUT/'trials').rglob('worker_status.json'):
        ensure_inactive(status.parent)
    save(directory/'launch_checkpoint.json',{'utc':now(),'state':'launching','variant':variant,'fold':fold,'seed':seed,'protocol_sha256':digest(OUT/'protocol.json'),'command':[sys.executable,str(Path(__file__).with_name('gpu_fit.py')),variant,fold,str(seed)]})
    with (directory/'fit.log').open('a',encoding='utf-8') as log, (directory/'gpu_samples.csv').open('a',encoding='utf-8') as samples:
        with subprocess.Popen([sys.executable,str(Path(__file__).with_name('gpu_fit.py')),variant,fold,str(seed)],stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW) as process:
            save(directory/'worker_status.json',{'state':'starting','identity':child_identity(process.pid),'utc':now()})
            save(directory/'controller_pid.json',{'worker_pid':process.pid,'started_utc':now()})
            while process.poll() is None:
                observed=subprocess.run(['nvidia-smi','--query-gpu=timestamp,name,utilization.gpu,memory.used,memory.total,power.draw','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW,check=False)
                assert observed.returncode==0,observed.stderr
                samples.write(observed.stdout)
                samples.flush()
                time.sleep(1)
            code=process.wait()
    save(directory/'controller_receipt.json',{'exit_code':code,'finished_utc':now(),'worker_pid':process.pid})
    assert code==0,f'See {directory}/fit.log'


def main() -> None:
    freeze()
    install_frozen()
    from gpu_data import prepare
    from gpu_score import compare
    from threadpoolctl import threadpool_limits
    configure()
    protocol=json.loads((OUT/'protocol.json').read_text())
    assert all(digest(ROOT/p)==sha for p,sha in protocol['input_sha256'].items())
    with threadpool_limits(limits=16):
        if not (OUT/'data_manifest.json').exists():
            prepare()
            save(OUT/'data_manifest.json',{str(p.relative_to(OUT)):digest(p) for p in (OUT/'data').rglob('*') if p.is_file()})
        assert all(digest(OUT/p)==sha for p,sha in json.loads((OUT/'data_manifest.json').read_text()).items())
        records=[]
        for variant in ('rich_cf','station_normalized'):
            for fold in FOLDS:
                launch(variant,fold,0)
            records.append(compare(variant,(0,),'screen'))
            save(OUT/'progress.json',records)
        eligible=[r for r in records if r['eligible']]
        selected=None
        followup=None
        if eligible:
            chosen=min(eligible,key=lambda r:r['mean_relative_W'])
            followup=chosen['variant']
            for fold in FOLDS:
                for seed in (1,2):
                    launch(followup,fold,seed)
            result=compare(followup,(0,1,2),'ensemble')
            records.append(result)
            if result['both_folds_improve']:
                selected=result
        save(OUT/'results.json',{'records':records,'followup_variant':followup,'selected':selected,'cpu_reference_retained':selected is None,'confirmation_loaded':False,'test_loaded':False,'model_fit_count':4+(4 if followup else 0)})
        after={p:digest(ROOT/p) for p in protocol['protected_sha256']}
        assert after==protocol['protected_sha256']
        save(OUT/'preservation.json',{'unchanged':True,'files':len(after),'sha256':after})
        save(OUT/'artifact_hashes.json',{str(p.relative_to(OUT)):digest(p) for folder in ('data','trials','comparisons','sources') for p in (OUT/folder).rglob('*') if p.is_file()})
        save(OUT/'controller_receipt.json',{'exit_code':0,'finished_utc':now(),'all_trial_controllers_terminal':True,'selected':selected['variant'] if selected else None})
        print('GPU FAMILY TERMINAL',json.dumps({'selected':selected,'followup':followup}),flush=True)


if __name__=='__main__':
    main()
