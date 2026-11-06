# /// script
# requires-python = ">=3.12"
# dependencies = ["catboost", "numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: existing GPU environment Python gpu_run.py --prepare|--trial VARIANT FOLD SEED|--compare VARIANT|--finish
"""Bounded single-trial controller for the frozen 24-fit mechanistic wave."""
from gpu_common import ROOT, OLD, PRIOR, OUT, PARAMS, VARIANTS, FOLDS, REFERENCE, digest, save, now, install_frozen, configure, child_identity
from typing import assert_never
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
    snapshots={}
    for folder in ('autoresearch','score_push'):
        for path in (ROOT/'submission'/folder).glob('*.py'):
            shutil.copyfile(path,OUT/'sources'/path.name)
            snapshots[path.stem]={'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    own={}
    for path in Path(__file__).parent.glob('*.py'):
        shutil.copyfile(path,OUT/'sources/own'/path.name)
        own[path.name]={'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    key=json.loads((ROOT/'analysis_outputs/award_run/provenance.json').read_text())['cache_key']
    prices=ROOT/'analysis_outputs/award_run/cache'/key/'smp.parquet'
    inputs=[p for p in (PRIOR/'data').rglob('*') if p.is_file()]
    inputs += [prices,OLD/'cache/train.parquet',OLD/'recent/cache/train.parquet',ROOT/'analysis_outputs/autoresearch_20261103/cache/selection_labels.parquet',ROOT/'analysis_outputs/autoresearch_20261103/final/outer_predictions.parquet']
    protected=set(inputs)
    protected.update(ROOT/r['original'] for r in snapshots.values())
    protected.update((ROOT/'submission/score_push_gpu').glob('*.py'))
    for folder in (OLD/'final',ROOT/'submission/score_push_candidate',ROOT/'submission/autoresearch_candidate',PRIOR/'data',PRIOR/'trials',PRIOR/'comparisons',PRIOR/'sources'):
        protected.update(p for p in folder.rglob('*') if p.is_file() and p.suffix!='.md' and '__pycache__' not in p.parts)
    protected.update(PRIOR/p for p in ('protocol.json','results.json','artifact_hashes.json','install_receipt.json'))
    save(OUT/'protocol.json',{'created_utc':now(),'variants':VARIANTS,'seeds':[0,1,2],'folds':{'primary':{'train_end':'2023-06-01 Asia/Seoul','eval_end':'2024-06-01 Asia/Seoul','keys':17568},'recent':{'train_end':'2024-06-01 Asia/Seoul','eval_end':'2025-03-01 Asia/Seoul','keys':13104}},'original_data_root':str(PRIOR/'data'),'reference_scores':REFERENCE,'common_parameters':PARAMS,'budget':{'total_fits':24,'fits_per_variant':6,'additional_fits':0},'normalization':'All variants target CF/n; n=frozen Haurwitz floor0.05; invert n*capacity. Weight n except monetary.','monetary':'n*capacity*SMP*k / training-only mean(capacity*SMP*k); exact training-key join, timestamp k11..15=3; capacity/SMP/k not added to feature matrix.','price_source':str(prices.relative_to(ROOT)),'price_provenance':'Original award feature cache SMP table; compute-hour k crosschecked independently. recent group training cache lacks SMP/k, so join original timestamp table after ts<=cutoff predicate.','missing':'904 station candidate columns; train-only constant mask; native CatBoost Min numeric NaN.','selection':'For all four variants average three finite signed seeds before clip. One optimal_weight scalar on PRIMARY only, unchanged RECENT. Eligible iff both folds strictly improve and alpha>=.02; choose minimum equal-fold mean relative W. No seed0 screen, cross-variant mixtures, additional tuning or confirmation.','snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)},'resources':{'gpu':'RTX5090 Laptop','devices':'0','gpu_ram_part':.9,'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_fits':1},'durability':'One CLI invocation per fit; own PID+creation check, exact completed-model hashes, trial-owned CatBoost snapshot every30seconds; no repeat of live or completed worker.','uncertainty':'Adaptive historically exposed development, not pristine holdout. GPU training nondeterministic; exact saved-model inference replay only. Earlier CPU and GPU adverse outcomes retained.','confirmation_loaded':False,'test_loaded':False,'no_fulltrain_or_export':True})


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




def finish() -> None:
    records=[json.loads((OUT/'comparisons'/variant/'ensemble/decision.json').read_text()) for variant in VARIANTS]
    for variant in VARIANTS:
        for fold in FOLDS:
            for seed in range(3):
                directory=OUT/'trials'/variant/fold/f'seed{seed}'
                assert json.loads((directory/'controller_receipt.json').read_text())['exit_code']==0
                status=json.loads((directory/'worker_status.json').read_text())
                assert status['state']=='complete'
                assert digest(directory/'model.cbm')==status['model_sha256']
                assert digest(directory/'daylight_raw.parquet')==status['raw_sha256']
    eligible=[r for r in records if r['eligible']]
    selected=min(eligible,key=lambda r:r['mean_relative_W']) if eligible else None
    save(OUT/'results.json',{'records':records,'selected':selected,'cpu_reference_retained':selected is None,'model_fit_count':24,'confirmation_loaded':False,'test_loaded':False})
    protocol=json.loads((OUT/'protocol.json').read_text())
    after={p:digest(ROOT/p) for p in protocol['protected_sha256']}
    assert after==protocol['protected_sha256']
    save(OUT/'preservation.json',{'unchanged':True,'files':len(after),'sha256':after})
    save(OUT/'artifact_hashes.json',{str(p.relative_to(OUT)):digest(p) for folder in ('data','trials','comparisons','sources') for p in (OUT/folder).rglob('*') if p.is_file()})
    save(OUT/'controller_receipt.json',{'exit_code':0,'finished_utc':now(),'all_24_trial_controllers_terminal':True,'selected':selected['variant'] if selected else None})
    print('REFINEMENT TERMINAL',selected['variant'] if selected else 'CPU retained',flush=True)


def main() -> None:
    freeze()
    install_frozen()
    from gpu_data import prepare
    from gpu_score import compare, self_check
    from threadpoolctl import threadpool_limits
    configure()
    protocol=json.loads((OUT/'protocol.json').read_text())
    assert all(digest(ROOT/p)==sha for p,sha in protocol['input_sha256'].items())
    with threadpool_limits(limits=16):
        match sys.argv[1:]:
            case ['--prepare']:
                assert not (OUT/'data_manifest.json').exists()
                prepare()
                self_check()
                save(OUT/'data_manifest.json',{str(p.relative_to(OUT)):digest(p) for p in (OUT/'data').rglob('*') if p.is_file()})
                save(OUT/'state.json',{'phase':'prepared','completed_fits':0,'budget':24,'utc':now()})
            case ['--trial',variant,fold,seed]:
                assert variant in VARIANTS and fold in FOLDS and seed in ('0','1','2')
                assert all(digest(OUT/p)==sha for p,sha in json.loads((OUT/'data_manifest.json').read_text()).items())
                launch(variant,fold,int(seed))
                completed=sum(json.loads(p.read_text())['state']=='complete' for p in (OUT/'trials').rglob('worker_status.json'))
                save(OUT/'state.json',{'phase':'fitting','completed_fits':completed,'budget':24,'last_trial':[variant,fold,seed],'utc':now()})
            case ['--compare',variant]:
                assert variant in VARIANTS and not (OUT/'comparisons'/variant/'ensemble/decision.json').exists()
                compare(variant,(0,1,2),'ensemble')
            case ['--finish']:
                finish()
            case unexpected:
                assert_never(unexpected)


if __name__=='__main__':
    main()

