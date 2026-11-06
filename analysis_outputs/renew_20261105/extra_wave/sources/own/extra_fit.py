# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "scikit-learn", "joblib", "threadpoolctl"]
# ///
# How to run: released extra_run.py launches extra_fit.py FOLD SEED serially.
"""One fixed ExtraTrees fit with parallel trees and deterministic saved inference."""
import json
import sys
import time
import warnings
from pathlib import Path
from extra_common import OUT,FOLDS,PARAMS,environment,install_frozen,require_release,configure,resource,save,digest,now

def main() -> None:
    environment()
    install_frozen()
    configure()
    require_release()
    import joblib
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- native raw featureframes and frozen scalar contracts
    import sklearn
    from sklearn.ensemble import ExtraTreesRegressor
    from threadpoolctl import threadpool_limits,threadpool_info
    expected = json.loads((OUT/'evidence/environment.json').read_text(encoding='utf-8'))
    assert sklearn.__version__==expected['sklearn_version']=='1.9.1'
    for name,sha in expected['installed_sources_sha256'].items():
        assert digest(Path(name))==sha
    fold,seed_text = sys.argv[1:]
    assert fold in FOLDS and seed_text in ('0','1','2')
    directory = OUT/'trials'/fold/f'seed{seed_text}'
    assert directory.is_dir() and not (directory/'model.joblib').exists(),'No repeated fit'
    with threadpool_limits(limits=16):
        assert all(p['num_threads']==16 for p in threadpool_info())
        save(directory/'worker_status.json',{'state':'running','identity':resource(),'utc':now()})
        data = OUT/'data'/fold
        spec = json.loads((data/'features.json').read_text(encoding='utf-8'))
        names = spec['rich']
        train = pd.read_parquet(data/'train.parquet',columns=names)
        future = pd.read_parquet(data/'evaluation.parquet',columns=names)
        transform = pd.read_parquet(data/'training_transform.parquet')
        inverse = pd.read_parquet(data/'evaluation_transform.parquet')
        fit_params = {**PARAMS,'random_state':int(seed_text)}
        inference_params = {**fit_params,'n_jobs':1}
        save(directory/'config.json',{'fold':fold,'seed':int(seed_text),'fit_parameters':fit_params,'inference_parameters':inference_params,'features':names,'training_rows':len(train),'prediction_rows':len(future),'cutoff':spec['cutoff'],'native_nan':True,'prepared_manifest_sha256':digest(OUT/'prepared_manifest.json'),'input_sha256':{name:digest(data/name) for name in ('train.parquet','evaluation.parquet','features.json','training_transform.parquet','evaluation_transform.parquet')},'target':'target_normalized pre-StandardScaler','weight':'sample_weight exact MLP n^2 mean-preserving decay180','inverse':'inverse_kwh exact MLP normalizer*capacity','fit_backend_preference':'threads','serial_top_level_models':True})
        model = ExtraTreesRegressor(**fit_params)
        assert model.get_params()==fit_params
        started = time.monotonic()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            model.fit(train,transform.target_normalized.to_numpy(),sample_weight=transform.sample_weight.to_numpy())
        fit_seconds = time.monotonic()-started
        warning_records = [{'category':w.category.__name__,'message':str(w.message)} for w in caught]
        for warning in caught:
            warnings.showwarning(warning.message,warning.category,warning.filename,warning.lineno)
        assert len(model.estimators_)==600 and model.feature_names_in_.tolist()==names
        assert model.get_params()==fit_params
        model.set_params(n_jobs=1)
        assert model.get_params()==inference_params
        assert {k for k in fit_params if fit_params[k]!=inference_params[k]}=={'n_jobs'}
        joblib.dump(model,directory/'model.joblib')
        prediction = model.predict(future)*inverse.inverse_kwh.to_numpy()
        assert np.isfinite(prediction).all()
        inverse[['ts','grp']].assign(p_raw=prediction).to_parquet(directory/'daylight_raw.parquet',index=False)
        saved = joblib.load(directory/'model.joblib')
        assert saved.get_params()==inference_params and len(saved.estimators_)==600
        replay = saved.predict(future)*inverse.inverse_kwh.to_numpy()
        assert np.array_equal(prediction.view(np.uint64),replay.view(np.uint64))
        save(directory/'convergence.json',{'trees':600,'warnings':warning_records,'fit_seconds':fit_seconds,'tree_node_counts':[tree.tree_.node_count for tree in model.estimators_],'all_seeds_retained':True})
        save(directory/'replay.json',{'passed':True,'rows':len(prediction),'max_absolute_error':0.,'bitwise_exact':True,'negative_raw':int((prediction<0).sum()),'serial_tree_accumulation':True,'saved_n_jobs':saved.n_jobs,'inverse_once':True,'model_sha256':digest(directory/'model.joblib'),'raw_sha256':digest(directory/'daylight_raw.parquet')})
        assert all(p['num_threads']==16 for p in threadpool_info())
        save(directory/'runtime.json',{**resource(),'seconds':time.monotonic()-started,'fit_seconds':fit_seconds,'fit_internal_tree_jobs':16,'inference_tree_jobs':1,'new_model_fits':1,'warnings':warning_records})
        save(directory/'worker_status.json',{'state':'complete','identity':resource(),'utc':now(),'model_sha256':digest(directory/'model.joblib'),'raw_sha256':digest(directory/'daylight_raw.parquet'),'new_model_fits':1})
        print('EXTRA FIT COMPLETE',fold,seed_text,flush=True)

if __name__=='__main__':
    main()
