# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "scikit-learn", "joblib", "threadpoolctl"]
# ///
# How to run: released incbound_run.py launches incbound_infer.py FOLD SEED serially.
"""One unchanged historical MLP: exact old replay then one bounded inference."""
import json
import sys
import time
from incbound_common import ROOT,OUT,MODELS,FOLDS,environment,install_frozen,require_release,configure,resource,save,digest,now

def main() -> None:
    environment()
    install_frozen()
    configure()
    require_release()
    import joblib
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- original raw prediction/key parity
    from threadpoolctl import threadpool_limits,threadpool_info
    fold,seed_text = sys.argv[1:]
    assert fold in FOLDS and seed_text in ('0','1','2')
    source = MODELS/fold/'mlp_cf'/f'seed{seed_text}'
    directory = OUT/'trials'/fold/f'seed{seed_text}'
    assert directory.is_dir() and not (directory/'original_raw.parquet').exists() and not (directory/'bounded_raw.parquet').exists()
    model = joblib.load(source/'model.joblib')
    scaler = joblib.load(source/'target_scaler.joblib')
    with threadpool_limits(limits=16),threadpool_limits(limits=1,user_api='blas'):
        pools = threadpool_info()
        assert all(p['num_threads']==1 if p['user_api']=='blas' else 1<=p['num_threads']<=16 for p in pools)
        save(directory/'worker_status.json',{'state':'running','identity':resource(),'historical_inference_blas_threads':1,'utc':now()})
        data = OUT/'data'/fold
        original = np.load(data/'x_evaluation_original.npy',allow_pickle=False)
        bounded = np.load(data/'x_evaluation_bounded.npy',allow_pickle=False)
        inverse = pd.read_parquet(data/'evaluation_transform.parquet')
        stored = pd.read_parquet(source/'daylight_raw.parquet',columns=['ts','grp','p_raw'])
        pd.testing.assert_frame_equal(stored[['ts','grp']],inverse[['ts','grp']])
        save(directory/'config.json',{'fold':fold,'seed':int(seed_text),'source_model':str((source/'model.joblib').relative_to(ROOT)),'source_model_sha256':digest(source/'model.joblib'),'source_preprocessor_sha256':digest(source/'input_preprocessing.joblib'),'source_target_scaler_sha256':digest(source/'target_scaler.joblib'),'source_config_sha256':digest(source/'config.json'),'original_matrix_sha256':digest(data/'x_evaluation_original.npy'),'bounded_matrix_sha256':digest(data/'x_evaluation_bounded.npy'),'capacity_inverse_sha256':digest(data/'evaluation_transform.parquet'),'prepared_manifest_sha256':digest(OUT/'prepared_manifest.json'),'historical_inference_blas_threads':1,'cpu_max_threads':16,'new_model_fits':0,'native_model_inferences':2})
        started = time.monotonic()
        old_prediction = scaler.inverse_transform(model.predict(original).reshape(-1,1)).ravel()*inverse.capacity_kw.to_numpy()
        assert np.array_equal(old_prediction.view(np.uint64),stored.p_raw.to_numpy().view(np.uint64)),'Historical raw parity failure; do not continue bounded inference'
        inverse[['ts','grp']].assign(p_raw=old_prediction).to_parquet(directory/'original_raw.parquet',index=False)
        prediction = scaler.inverse_transform(model.predict(bounded).reshape(-1,1)).ravel()*inverse.capacity_kw.to_numpy()
        assert np.isfinite(prediction).all()
        unchanged = np.all(original==bounded,axis=1)
        assert np.array_equal(prediction[unchanged].view(np.uint64),old_prediction[unchanged].view(np.uint64))
        inverse[['ts','grp']].assign(p_raw=prediction).to_parquet(directory/'bounded_raw.parquet',index=False)
        save(directory/'replay.json',{'original_full_exact':True,'original_max_absolute_error':0.,'original_rows':len(stored),'bounded_rows':len(prediction),'unchanged_input_rows_bitwise_prediction_exact':True,'source_model_sha256':digest(source/'model.joblib'),'source_original_raw_sha256':digest(source/'daylight_raw.parquet'),'original_raw_sha256':digest(directory/'original_raw.parquet'),'bounded_raw_sha256':digest(directory/'bounded_raw.parquet'),'inverse_scaler_once_then_capacity':True,'native_model_inferences':2,'new_model_fits':0})
        save(directory/'runtime.json',{**resource(),'seconds':time.monotonic()-started,'historical_inference_blas_threads':1,'native_model_inferences':2,'new_model_fits':0})
        save(directory/'worker_status.json',{'state':'complete','identity':resource(),'utc':now(),'source_model_sha256':digest(source/'model.joblib'),'original_raw_sha256':digest(directory/'original_raw.parquet'),'bounded_raw_sha256':digest(directory/'bounded_raw.parquet'),'native_model_inferences':2,'new_model_fits':0})
        print('INCBOUND INFERENCE COMPLETE',fold,seed_text,flush=True)

if __name__=='__main__':
    main()
