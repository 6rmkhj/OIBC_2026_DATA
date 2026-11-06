# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "scikit-learn", "joblib", "threadpoolctl"]
# ///
# How to run: mlp_run.py --run launches mlp_fit.py FOLD SEED only after release.
"""One fixed weighted MLP fit using shared frozen float64 matrices."""
import json
import sys
import time
import warnings
from mlp_common import OUT,FOLDS,PARAMS,environment,install_frozen,require_release,configure,resource,save,digest,now

def main() -> None:
    environment()
    install_frozen()
    configure()
    require_release()
    import joblib
    import sklearn
    assert sklearn.__version__==json.loads((OUT/'evidence/environment.json').read_text(encoding='utf-8'))['sklearn_version']
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- persisted daylight prediction keys
    from sklearn.neural_network import MLPRegressor
    from threadpoolctl import threadpool_limits
    fold,seed_text = sys.argv[1:]
    assert fold in FOLDS and seed_text in ('0','1','2')
    directory = OUT/'trials'/fold/f'seed{seed_text}'
    directory.mkdir(parents=True,exist_ok=True)
    assert not (directory/'model.joblib').exists(),'No repeated fit'
    with threadpool_limits(limits=16):
        save(directory/'worker_status.json',{'state':'running','identity':resource(),'utc':now()})
        data = OUT/'data'/fold
        x = np.load(data/'x_train.npy',allow_pickle=False)
        future = np.load(data/'x_evaluation.npy',allow_pickle=False)
        y = np.load(data/'y_train.npy',allow_pickle=False)
        weight = np.load(data/'sample_weight.npy',allow_pickle=False)
        for value in (x,future,y,weight):
            assert value.dtype==np.dtype('float64') and np.isfinite(value).all()
        assert (weight>0).all()
        inverse = pd.read_parquet(data/'evaluation_transform.parquet')
        scaler = joblib.load(data/'target_scaler.joblib')
        params = {**PARAMS,'random_state':int(seed_text)}
        save(directory/'config.json',{'fold':fold,'seed':int(seed_text),'parameters':params,'prepared_manifest_sha256':digest(OUT/'prepared_manifest.json'),'matrix_sha256':{name:digest(data/name) for name in ('x_train.npy','x_evaluation.npy','y_train.npy','sample_weight.npy','input_preprocessing.joblib','target_scaler.joblib')},'train_rows':len(x),'evaluation_rows':len(future),'feature_count':x.shape[1],'dtype':'float64','sample_weight_used':True})
        started = time.monotonic()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            model = MLPRegressor(**params)
            model.fit(x,y,sample_weight=weight)
        warning_records = [{'category':w.category.__name__,'message':str(w.message)} for w in caught]
        for warning in caught:
            warnings.showwarning(warning.message,warning.category,warning.filename,warning.lineno)
        assert 1<=model.n_iter_<=400
        assert all(coef.dtype==np.dtype('float64') for coef in model.coefs_)
        joblib.dump(model,directory/'model.joblib')
        scaled = model.predict(future)
        prediction = scaler.inverse_transform(scaled.reshape(-1,1)).ravel()*inverse.inverse_kwh.to_numpy()
        assert prediction.dtype==np.dtype('float64') and np.isfinite(prediction).all()
        raw = inverse[['ts','grp']].assign(p_raw=prediction)
        raw.to_parquet(directory/'daylight_raw.parquet',index=False)
        replay_scaled = joblib.load(directory/'model.joblib').predict(future)
        replay = scaler.inverse_transform(replay_scaled.reshape(-1,1)).ravel()*inverse.inverse_kwh.to_numpy()
        np.testing.assert_array_equal(prediction,replay)
        save(directory/'convergence.json',{'warnings':warning_records,'iterations':model.n_iter_,'loss_curve':model.loss_curve_,'last_loss':model.loss_,'all_seeds_retained':True})
        save(directory/'replay.json',{'passed':True,'rows':len(raw),'max_absolute_error':0.,'negative_raw':int((prediction<0).sum()),'inverse_target_scaler_once':True,'model_sha256':digest(directory/'model.joblib'),'raw_sha256':digest(directory/'daylight_raw.parquet')})
        save(directory/'runtime.json',{**resource(),'seconds':time.monotonic()-started,'loaded_existing_model':False})
        save(directory/'worker_status.json',{'state':'complete','identity':resource(),'utc':now(),'model_sha256':digest(directory/'model.joblib'),'raw_sha256':digest(directory/'daylight_raw.parquet')})
        print('MLP FIT COMPLETE',fold,seed_text,flush=True)
if __name__=='__main__':
    main()
