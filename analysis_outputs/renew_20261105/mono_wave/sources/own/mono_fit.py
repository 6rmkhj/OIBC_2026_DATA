# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: released mono_run.py launches mono_fit.py ARM FOLD SEED serially.
"""One released fixed fair-loss model and exact complete saved-model replay."""
import json
import sys
import time
import warnings
from pathlib import Path
from mono_common import OUT,FOLDS,ARMS,PARAMS,environment,install_frozen,require_release,configure,resource,save,digest,now

def main() -> None:
    environment()
    install_frozen()
    configure()
    require_release()
    import lightgbm as lgb
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- frozen native station matrices and keys
    from threadpoolctl import threadpool_limits,threadpool_info
    expected = json.loads((OUT/'evidence/environment.json').read_text(encoding='utf-8'))
    assert lgb.__version__==expected['lightgbm_version']
    assert digest(Path(lgb.__file__).parent/'bin/lib_lightgbm.dll')==expected['native_sha256']
    arm,fold,seed_text = sys.argv[1:]
    assert arm in ARMS and fold in FOLDS and seed_text in ('0','1','2')
    directory = OUT/'trials'/arm/fold/f'seed{seed_text}'
    assert directory.is_dir() and not (directory/'model.txt').exists(),'No repeated fit'
    with threadpool_limits(limits=16):
        assert all(p['num_threads']==16 for p in threadpool_info())
        save(directory/'worker_status.json',{'state':'running','identity':resource(),'utc':now()})
        data = OUT/'data'/fold
        mask = json.loads((data/'feature_mask.json').read_text(encoding='utf-8'))
        names = mask['selected_columns']
        vectors = pd.read_parquet(data/'constraints.parquet')
        assert vectors.feature.tolist()==names
        vector = vectors[arm].tolist()
        train = pd.read_parquet(data/'train.parquet',columns=names)
        future = pd.read_parquet(data/'evaluation.parquet',columns=names)
        transform = pd.read_parquet(data/'training_transform.parquet')
        inverse = pd.read_parquet(data/'evaluation_transform.parquet')
        params = {**PARAMS,'random_state':None if seed_text=='0' else int(seed_text),'monotone_constraints':vector}
        save(directory/'config.json',{'arm':arm,'fold':fold,'seed':int(seed_text),'parameters':params,'features':names,'candidate_features':mask['candidate_columns'],'training_rows':len(train),'prediction_rows':len(future),'cutoff':mask['cutoff'],'prepared_manifest_sha256':digest(OUT/'prepared_manifest.json'),'input_sha256':{name:digest(data/name) for name in ('train.parquet','evaluation.parquet','feature_mask.json','constraints.parquet','training_transform.parquet','evaluation_transform.parquet')},'target':'cf / normalizer; no target scaler','sample_weight':'normalizer * mean1_decay180','inverse':'normalizer * capacity_kw','native_nan':True})
        started = time.monotonic()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            estimator = lgb.LGBMRegressor(**params)
            estimator.fit(train,transform.target_normalized.to_numpy(),sample_weight=transform.sample_weight.to_numpy())
        warning_records = [{'category':w.category.__name__,'message':str(w.message)} for w in caught]
        for warning in caught:
            warnings.showwarning(warning.message,warning.category,warning.filename,warning.lineno)
        model = estimator.booster_
        assert model.current_iteration()==400 and model.feature_name()==names
        model.save_model(str(directory/'model.txt'))
        prediction = model.predict(future,num_threads=16,validate_features=True)*inverse.inverse_kwh.to_numpy()
        assert np.isfinite(prediction).all()
        raw = inverse[['ts','grp']].assign(p_raw=prediction)
        raw.to_parquet(directory/'daylight_raw.parquet',index=False)
        saved = lgb.Booster(model_file=str(directory/'model.txt'))
        assert saved.feature_name()==names and saved.current_iteration()==400
        replay = saved.predict(future,num_threads=16,validate_features=True)*inverse.inverse_kwh.to_numpy()
        np.testing.assert_array_equal(prediction,replay)
        save(directory/'convergence.json',{'warnings':warning_records,'iterations':model.current_iteration(),'all_seeds_retained':True})
        save(directory/'replay.json',{'passed':True,'rows':len(raw),'max_absolute_error':0.,'negative_raw':int((prediction<0).sum()),'inverse_once':True,'model_sha256':digest(directory/'model.txt'),'raw_sha256':digest(directory/'daylight_raw.parquet')})
        assert all(p['num_threads']==16 for p in threadpool_info())
        save(directory/'runtime.json',{**resource(),'seconds':time.monotonic()-started,'loaded_existing_model':False,'new_model_fits':1,'warnings':warning_records})
        save(directory/'worker_status.json',{'state':'complete','identity':resource(),'utc':now(),'model_sha256':digest(directory/'model.txt'),'raw_sha256':digest(directory/'daylight_raw.parquet'),'new_model_fits':1})
        print('MONO FIT COMPLETE',arm,fold,seed_text,flush=True)

if __name__=='__main__':
    main()
