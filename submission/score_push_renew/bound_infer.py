# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "scikit-learn", "joblib", "threadpoolctl"]
# ///
# How to run: bound_run.py launches bound_infer.py FOLD SEED serially.
"""Native inference-only worker reusing one immutable MLP model."""
import json
import sys
import time
import warnings
from bound_common import ROOT,OUT,MLP,FOLDS,environment,install_frozen,check_prepared,configure,resource,save,digest,now

def main() -> None:
    environment()
    install_frozen()
    configure()
    check_prepared()
    import joblib
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- exact immutable inverse/key contract
    import sklearn
    from sklearn.neural_network import MLPRegressor
    from threadpoolctl import threadpool_limits,threadpool_info
    assert sklearn.__version__==json.loads((MLP/'evidence/environment.json').read_text(encoding='utf-8'))['sklearn_version']
    fold,seed_text = sys.argv[1:]
    assert fold in FOLDS and seed_text in ('0','1','2')
    directory = OUT/'trials'/fold/f'seed{seed_text}'
    directory.mkdir(parents=True,exist_ok=True)
    source_model = MLP/'trials'/fold/f'seed{seed_text}'/'model.joblib'
    matrix_path = OUT/'data'/fold/'x_evaluation_bounded.npy'
    matrix = np.load(matrix_path,allow_pickle=False)
    scaler = joblib.load(MLP/'data'/fold/'target_scaler.joblib')
    inverse = pd.read_parquet(MLP/'data'/fold/'evaluation_transform.parquet')
    model = joblib.load(source_model)
    assert isinstance(model,MLPRegressor)
    assert matrix.dtype==np.dtype('float64') and np.isfinite(matrix).all()
    with threadpool_limits(limits=16):
        assert all(pool['num_threads']==16 for pool in threadpool_info())
        save(directory/'worker_status.json',{'state':'running','identity':resource(),'utc':now()})
        source_hash = digest(source_model)
        save(directory/'config.json',{'fold':fold,'seed':int(seed_text),'source_model':str(source_model.relative_to(ROOT)),'source_model_sha256':source_hash,'bounded_matrix_sha256':digest(matrix_path),'target_scaler_sha256':digest(MLP/'data'/fold/'target_scaler.joblib'),'inverse_sha256':digest(MLP/'data'/fold/'evaluation_transform.parquet'),'prepared_manifest_sha256':digest(OUT/'prepared_manifest.json'),'new_model_fits':0,'native_inferences':1})
        started = time.monotonic()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            scaled = model.predict(matrix)
            prediction = scaler.inverse_transform(scaled.reshape(-1,1)).ravel()*inverse.inverse_kwh.to_numpy()
        assert np.isfinite(prediction).all()
        raw = inverse[['ts','grp']].assign(p_raw=prediction)
        raw.to_parquet(directory/'daylight_raw.parquet',index=False)
        replay_scaled = joblib.load(source_model).predict(matrix)
        replay = scaler.inverse_transform(replay_scaled.reshape(-1,1)).ravel()*inverse.inverse_kwh.to_numpy()
        np.testing.assert_array_equal(replay,prediction)
        assert digest(source_model)==source_hash
        save(directory/'replay.json',{'passed':True,'rows':len(raw),'max_absolute_error':0.,'source_model_sha256':source_hash,'raw_sha256':digest(directory/'daylight_raw.parquet'),'negative_raw':int((prediction<0).sum()),'inverse_target_scaler_once':True})
        warning_records = [{'category':w.category.__name__,'message':str(w.message)} for w in caught]
        for warning in caught:
            warnings.showwarning(warning.message,warning.category,warning.filename,warning.lineno)
        save(directory/'runtime.json',{**resource(),'seconds':time.monotonic()-started,'warnings':warning_records,'new_model_fits':0,'original_model_iterations':model.n_iter_})
        save(directory/'worker_status.json',{'state':'complete','identity':resource(),'utc':now(),'source_model_sha256':source_hash,'raw_sha256':digest(directory/'daylight_raw.parquet'),'new_model_fits':0})
        print('BOUND INFERENCE COMPLETE',fold,seed_text,flush=True)
if __name__=='__main__':
    main()
