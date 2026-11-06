# /// script
# requires-python = ">=3.12"
# dependencies = ["catboost", "numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: environment/Scripts/python.exe submission/score_push_gpu/gpu_fit.py VARIANT FOLD SEED
"""One checkpointed GPU model fit, prediction and saved-model replay."""
from gpu_common import OUT, PARAMS, install_frozen, configure, resource, save, digest, now
import json
import sys
import time
import warnings


def main() -> None:
    install_frozen()
    from site_features import normalizer
    from profile_features import column_mask
    from threadpoolctl import threadpool_limits
    import catboost
    from catboost import CatBoostRegressor
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- frozen feature matrix contract
    import pyarrow
    configure()
    variant,fold,seed_text = sys.argv[1:]
    assert variant in ('rich_cf','station_normalized') and fold in ('primary','recent') and seed_text in ('0','1','2')
    directory = OUT/'trials'/variant/fold/f'seed{seed_text}'
    directory.mkdir(parents=True,exist_ok=True)
    with threadpool_limits(limits=16):
        save(directory/'worker_status.json',{'state':'running','identity':resource(),'utc':now()})
        features = json.loads((OUT/'data'/fold/'features.json').read_text())
        train = pd.read_parquet(OUT/'data'/fold/'train.parquet',filters=[('ts','<=',pd.Timestamp(features['cutoff']))])
        evaluation = pd.read_parquet(OUT/'data'/fold/'evaluation.parquet')
        normalized = variant=='station_normalized'
        candidates = features['station'] if normalized else features['rich']
        names = column_mask(train,candidates) if normalized else candidates
        assert names and not {'energy','cf','y','smp','k'}&set(names)
        assert train.ts.max()<=pd.Timestamp(features['cutoff'])<evaluation.ts.min()
        scale = normalizer(train.cosz.to_numpy()) if normalized else np.ones(len(train))
        inverse = normalizer(evaluation.cosz.to_numpy()) if normalized else np.ones(len(evaluation))
        params = {**PARAMS,'random_seed':int(seed_text),'train_dir':str(directory/'training_info'),'snapshot_file':str(directory/'training_snapshot.cbsnapshot')}
        save(directory/'config.json',{'variant':variant,'fold':fold,'seed':int(seed_text),'parameters':params,'features':names,'candidate_features':candidates,'train_only_mask':normalized,'training_rows':len(train),'training_max':str(train.ts.max()),'prediction_rows':len(evaluation),'normalizer':'Haurwitz floor0.05' if normalized else 'identity','sample_weight':'normalizer' if normalized else 'none','inputs_sha256':{p.name:digest(p) for p in (OUT/'data'/fold).glob('*') if p.is_file()}})
        model = CatBoostRegressor(**params)
        started = time.monotonic()
        loaded_existing = (directory/'model.cbm').exists()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            if loaded_existing:
                model.load_model(str(directory/'model.cbm'))
            else:
                model.fit(train[names],train.cf.to_numpy()/scale,sample_weight=scale if normalized else None)
                model.save_model(str(directory/'model.cbm'))
            assert model.tree_count_==2000
            prediction = model.predict(evaluation[names],thread_count=16)*inverse*evaluation.capacity_kw.to_numpy()
        assert np.isfinite(prediction).all()
        raw = evaluation[['ts','grp']].assign(p_raw=prediction)
        assert not raw.duplicated(['ts','grp']).any()
        raw.to_parquet(directory/'daylight_raw.parquet',index=False)
        replay_model = CatBoostRegressor()
        replay_model.load_model(str(directory/'model.cbm'))
        replay = replay_model.predict(evaluation[names],thread_count=16)*inverse*evaluation.capacity_kw.to_numpy()
        np.testing.assert_array_equal(prediction,replay)
        save(directory/'replay.json',{'passed':True,'rows':len(raw),'max_absolute_error':float(np.abs(prediction-replay).max()),'negative_raw':int((prediction<0).sum()),'model_sha256':digest(directory/'model.cbm'),'raw_sha256':digest(directory/'daylight_raw.parquet')})
        save(directory/'full_params.json',model.get_all_params())
        save(directory/'convergence.json',{'trees':model.tree_count_,'history':model.get_evals_result(),'warnings':[{'category':w.category.__name__,'message':str(w.message)} for w in caught]})
        save(directory/'runtime.json',{**resource(),'fit_predict_replay_seconds':time.monotonic()-started,'task_type':model.get_all_params()['task_type'],'model_thread_count':params['thread_count'],'devices':'0','gpu_ram_part':.9,'loaded_existing_model':loaded_existing,'versions':{'python':sys.version,'catboost':catboost.__version__,'numpy':np.__version__,'pandas':pd.__version__,'pyarrow':pyarrow.__version__}})
        save(directory/'worker_status.json',{'state':'complete','identity':resource(),'model_sha256':digest(directory/'model.cbm'),'raw_sha256':digest(directory/'daylight_raw.parquet'),'utc':now()})
        print('GPU FIT COMPLETE',variant,fold,seed_text,flush=True)


if __name__=='__main__':
    main()
