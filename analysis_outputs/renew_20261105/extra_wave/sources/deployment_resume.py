# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "threadpoolctl"]
# ///
# How to run: python submission/score_push/deployment_resume.py
"""Resume only unfinished station fits after documented original PID absence."""
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from deployment_run import ROOT, OUT, DEST, FrozenImports, digest

RESUME = DEST / 'resume'


def worker() -> None:
    """One sequential GPU capability test, then exactly three CPU station fits."""
    amendment = json.loads((DEST/'resource_amendment.json').read_text())
    for name, expected in amendment['resumed_sources_sha256'].items():
        assert digest(Path(__file__).with_name(name)) == expected
        assert digest(RESUME/'sources'/name) == expected
    sys.meta_path.insert(0,FrozenImports())
    from wave_common import save_json
    from final_build import OLD, MARCH, enrich
    from profile_features import column_mask
    from site_features import normalizer
    from verify import MemoryCounters
    from threadpoolctl import threadpool_limits, threadpool_info
    import lightgbm as lgb
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- exact frozen recipe interface
    import pyarrow as pa
    kernel = ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.SetPriorityClass.argtypes = [wintypes.HANDLE,wintypes.DWORD]
    kernel.GetPriorityClass.argtypes = [wintypes.HANDLE]
    ctypes.windll.psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE,ctypes.POINTER(MemoryCounters),wintypes.DWORD]
    handle = kernel.GetCurrentProcess()
    assert kernel.SetPriorityClass(handle,32)
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[name]='16'
    pa.set_cpu_count(4)
    pa.set_io_thread_count(4)
    started = time.monotonic()
    with threadpool_limits(limits=16):
        from deployment_gpu import nvidia_device
        gpu_devices = nvidia_device()
        rng = np.random.default_rng(20261104)
        tiny = rng.normal(size=(128,4))
        try:
            gpu = lgb.LGBMRegressor(device_type='gpu',n_estimators=2,num_leaves=3,min_child_samples=2,n_jobs=16,random_state=20261104,**gpu_devices['selected_parameters'])
            gpu.fit(tiny,tiny[:,0]+tiny[:,1])
            assert np.isfinite(gpu.predict(tiny)).all()
            gpu.booster_.save_model(str(RESUME/'gpu_capability_model.txt'))
            capability = {'supported':True,'device_type':'gpu','rows':128,'trees':2,'scientific_training':False,'parameters':gpu.get_params(),'device_inventory':gpu_devices}
            del gpu
        except lgb.basic.LightGBMError as error:
            capability = {'supported':False,'error':str(error),'scientific_training':False,'device_inventory':gpu_devices}
        save_json(RESUME/'gpu_capability.json',capability)
        print('GPU CAPABILITY',json.dumps(capability),flush=True)
        train = pd.read_parquet(OLD/'full_train.parquet',filters=[('ts','<=',MARCH)])
        train, names, profiles = enrich(train,pd.read_parquet(OUT/'final/cache/train_weather.parquet'),pd.read_parquet(OUT/'final/cache/train_stations.parquet'))
        evaluation = pd.read_parquet(DEST/'evaluation_features.parquet')
        selected = column_mask(train,profiles)
        prior_mask = json.loads((DEST/'models/station/seed0/feature_mask.json').read_text())
        assert selected == prior_mask['selected_columns'] and train.ts.max() <= MARCH
        config = json.loads((OUT/'final/models/station/seed0/config.json').read_text())
        scale = normalizer(train.cosz.to_numpy())
        for seed in range(3):
            directory = RESUME/'models/station'/f'seed{seed}'
            directory.mkdir(parents=True)
            params = {**config['parameters'],'random_state':None if seed==0 else seed,'n_jobs':16}
            model = lgb.LGBMRegressor(**params)
            fit_started = time.monotonic()
            model.fit(train[selected],train.cf.to_numpy()/scale,sample_weight=scale)
            prediction = model.predict(evaluation[selected])*normalizer(evaluation.cosz.to_numpy())*evaluation.capacity_kw.to_numpy()
            assert np.isfinite(prediction).all()
            model.booster_.save_model(str(directory/'model.txt'))
            replay = lgb.Booster(model_file=str(directory/'model.txt')).predict(evaluation[selected],num_threads=16)*normalizer(evaluation.cosz.to_numpy())*evaluation.capacity_kw.to_numpy()
            np.testing.assert_allclose(prediction,replay,rtol=1e-10,atol=1e-6)
            evaluation[['ts','grp']].assign(p_raw=prediction).to_parquet(directory/'daylight_raw.parquet',index=False)
            save_json(directory/'feature_mask.json',prior_mask)
            save_json(directory/'config.json',{'parameters':params,'features':selected,'train_rows':len(train),'train_max':str(train.ts.max()),'original_config':str(OUT/'final/models/station/seed0/config.json')})
            counters = MemoryCounters()
            counters.cb = ctypes.sizeof(counters)
            assert ctypes.windll.psapi.GetProcessMemoryInfo(handle,ctypes.byref(counters),counters.cb)
            priority = kernel.GetPriorityClass(handle)
            assert priority==32 and model.booster_.params['num_threads']==16
            save_json(directory/'runtime.json',{'pid':os.getpid(),'priority_class':priority,'parallel_fits':1,'model_n_jobs':16,'fit_seconds':[time.monotonic()-fit_started],'peak_working_set_bytes':counters.peak_working_set,'working_set_bytes':counters.working_set,'threadpools':threadpool_info(),'pyarrow_cpu':pa.cpu_count(),'pyarrow_io':pa.io_thread_count(),'environment':{k:os.environ[k] for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')},'replay_max_absolute_error':float(np.abs(prediction-replay).max())})
            del model
            print('RESUMED STATION',seed,flush=True)
        del train
        from deployment_replay import replay as replay_models
        from final_infer import compose
        from deployment_report import report
        base,components = replay_models()
        components.to_parquet(DEST/'components.parquet',index=False)
        prediction = compose(base,components.drop(columns='incumbent'))
        prediction = prediction.merge(components[['ts','grp','incumbent']],on=['ts','grp'],how='left',validate='one_to_one')
        prediction['incumbent'] = prediction.incumbent.fillna(0.)
        prediction['p_previous'] = .7149301735712863*prediction.incumbent+(1-.7149301735712863)*prediction.p_bu
        assert len(prediction)==4416
        prediction.to_parquet(DEST/'frozen_predictions.parquet',index=False)
        save_json(DEST/'prediction_freeze.json',{'sha256':digest(DEST/'frozen_predictions.parquet'),'evaluation_labels_opened':False,'utc':datetime.now(timezone.utc).isoformat()})
        report(prediction)
        protocol = json.loads((DEST/'protocol.json').read_text())
        after = {p:digest(ROOT/p) for p in protocol['protected_sha256']}
        assert after==protocol['protected_sha256']
        amendment = json.loads((DEST/'resource_amendment.json').read_text())
        retained = {p:digest(DEST/p) for p in amendment['completed_before_sha256']}
        assert retained==amendment['completed_before_sha256']
        save_json(DEST/'preservation.json',{'unchanged':True,'files':len(after),'sha256':after,'completed_models_unchanged':True,'completed_files':len(retained)})
        save_json(RESUME/'runtime.json',{'pid':os.getpid(),'priority_class':kernel.GetPriorityClass(handle),'model_n_jobs':16,'blas_threads':16,'parallel_fits':1,'seconds':time.monotonic()-started,'station_fits':3,'gpu_synthetic_capability_fits':1})
        save_json(DEST/'hashes.json',{str(p.relative_to(DEST)):digest(p) for p in DEST.rglob('*') if p.is_file() and p.name not in {'hashes.json','run.log'}})
        print('RESUME COMPLETE',flush=True)


def main() -> None:
    if sys.argv[1:]==['--worker']:
        worker()
        return
    absent = json.loads((DEST/'evidence/process_probe.json').read_text())
    assert absent['GetLastError']==87 and absent['OpenProcess_handle'] is None
    RESUME.mkdir(exist_ok=False)
    (RESUME/'sources').mkdir()
    for source in (Path(__file__),Path(__file__).with_name('deployment_replay.py'),Path(__file__).with_name('deployment_gpu.py')):
        shutil.copyfile(source,RESUME/'sources'/source.name)
    completed = [p for p in (DEST/'models').rglob('*') if p.is_file()]
    amendment = {'utc':datetime.now(timezone.utc).isoformat(),'user_instruction':'모델에 더 많은 리소스를 할당; 컴퓨터 확인하고 가용 최대 리소스 사용','reason':'Original PID31788 absent by OpenProcess ERROR_INVALID_PARAMETER; tool handle lost and original controller exit unavailable. Preserve finished work; resume only three unfinished station models.','original_status':'interrupted, exit code unknown; no success claim','hardware':{'logical_cpus':16,'ram_gib':63.32,'gpu':'RTX5090 Laptop 24463MiB'},'effective':{'n_jobs':16,'blas_threads':16,'priority_class':32,'pyarrow_threads':4,'parallel_fits':1},'scientific_change':False,'protocol_sha256':digest(DEST/'protocol.json'),'completed_before_sha256':{str(p.relative_to(DEST)):digest(p) for p in completed},'resumed_sources_sha256':{p.name:digest(p) for p in (RESUME/'sources').glob('*.py')},'model_paths':{f'station_seed{s}':f'resume/models/station/seed{s}' for s in range(3)}}
    (DEST/'resource_amendment.json').write_text(json.dumps(amendment,indent=2),encoding='utf-8')
    with (RESUME/'run.log').open('w',encoding='utf-8') as stream:
        result = subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker'],stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.NORMAL_PRIORITY_CLASS|subprocess.CREATE_NO_WINDOW,check=False)
    (RESUME/'controller_receipt.json').write_text(json.dumps({'exit_code':result.returncode,'original_controller_exit_code':None,'original_status':'interrupted','amendment_sha256':digest(DEST/'resource_amendment.json')}),encoding='utf-8')
    assert result.returncode==0,'See resume/run.log'


if __name__=='__main__':
    main()
