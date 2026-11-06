# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/cloud_generation.py ARM FOLD SEED
"""One bounded normalized LightGBM fit with an exact saved-model replay."""
from cloud_common import OUT, DATA, ARMS, FOLDS, PARAMS, install_frozen, configure, resource, save, digest, now, decay_multiplier
import json
import sys
import time

def main() -> None:
    install_frozen()
    configure()
    from site_features import normalizer
    from profile_features import column_mask
    from threadpoolctl import threadpool_limits
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- frozen scientific helper contracts
    import lightgbm as lgb
    import pyarrow
    variant, fold, seed_text = sys.argv[1:]
    assert variant in ARMS and fold in FOLDS and seed_text in ('0','1','2')
    directory = OUT/'trials'/variant/fold/f'seed{seed_text}'
    directory.mkdir(parents=True, exist_ok=True)
    with threadpool_limits(limits=16):
        save(directory/'worker_status.json', {'state':'running','identity':resource(),'utc':now()})
        specification = json.loads((DATA/fold/'features.json').read_text())
        cutoff = pd.Timestamp(specification['cutoff'])
        candidates = specification['station']
        train = pd.read_parquet(DATA/fold/'train.parquet', columns=['ts','grp','cf',*candidates], filters=[('ts','<=',cutoff)])
        evaluation = pd.read_parquet(DATA/fold/'evaluation.parquet', columns=['ts','grp','capacity_kw',*candidates])
        assert not {'energy','cf','y','smp','k'} & set(evaluation)
        assert train.ts.max() <= cutoff < evaluation.ts.min()
        assert len(evaluation) == specification['daylight_keys']
        assert not train.duplicated(['ts','grp']).any() and not evaluation.duplicated(['ts','grp']).any()
        extra_train = pd.read_parquet(OUT/'data'/fold/'train_features.parquet')
        extra_eval = pd.read_parquet(OUT/'data'/fold/'evaluation_features.parquet')
        pd.testing.assert_frame_equal(train[['ts','grp']], extra_train[['ts','grp']])
        pd.testing.assert_frame_equal(evaluation[['ts','grp']], extra_eval[['ts','grp']])
        added = [c for c in extra_train if c not in ('ts','grp') and (variant=='profiles' or c.endswith(('_mean','_warmup')))]
        train = train.merge(extra_train[['ts','grp',*added]],on=['ts','grp'],validate='one_to_one')
        evaluation = evaluation.merge(extra_eval[['ts','grp',*added]],on=['ts','grp'],validate='one_to_one')
        candidates = [*candidates,*added]
        names = column_mask(train, candidates)
        scale = normalizer(train.cosz.to_numpy())
        age = (cutoff-train.ts).dt.total_seconds().to_numpy()/86400
        decay = decay_multiplier(age, 180)
        weights = train[['ts','grp']].assign(normalizer=scale, age_days=age, recency_multiplier=decay, sample_weight=scale*decay)
        assert np.isfinite(weights.iloc[:,2:].to_numpy()).all() and np.isfinite(train.cf).all()
        weights_path = OUT/'data'/variant/fold/'training_weights.parquet'
        weights_path.parent.mkdir(parents=True, exist_ok=True)
        if weights_path.exists():
            pd.testing.assert_frame_equal(weights, pd.read_parquet(weights_path))
        else:
            weights.to_parquet(weights_path, index=False)
        params = {**PARAMS, 'random_state':None if seed_text=='0' else int(seed_text)}
        save(directory/'config.json', {'variant':variant,'fold':fold,'seed':int(seed_text),'parameters':params,'features':names,'candidate_features':candidates,'training_rows':len(train),'training_min':str(train.ts.min()),'training_max':str(train.ts.max()),'prediction_rows':len(evaluation),'cutoff':str(cutoff),'half_life_days':180,'weights_path':str(weights_path.relative_to(OUT)),'weights_sha256':digest(weights_path),'evaluation_columns':list(evaluation),'target':'cf / normalizer','inverse':'normalizer * capacity_kw'})
        started = time.monotonic()
        loaded = (directory/'model.txt').exists()
        if loaded:
            model = lgb.Booster(model_file=str(directory/'model.txt'))
        else:
            estimator = lgb.LGBMRegressor(**params)
            estimator.fit(train[names], train.cf.to_numpy()/scale, sample_weight=weights.sample_weight.to_numpy())
            model = estimator.booster_
            model.save_model(str(directory/'model.txt'))
        assert model.current_iteration() == 400
        inverse = normalizer(evaluation.cosz.to_numpy())*evaluation.capacity_kw.to_numpy()
        prediction = model.predict(evaluation[names], num_threads=16)*inverse
        assert np.isfinite(prediction).all()
        raw = evaluation[['ts','grp']].assign(p_raw=prediction)
        raw.to_parquet(directory/'daylight_raw.parquet', index=False)
        replay = lgb.Booster(model_file=str(directory/'model.txt')).predict(evaluation[names], num_threads=16)*inverse
        np.testing.assert_array_equal(prediction, replay)
        save(directory/'replay.json', {'passed':True,'rows':len(raw),'max_absolute_error':float(np.max(np.abs(prediction-replay))),'negative_raw':int((prediction<0).sum()),'model_sha256':digest(directory/'model.txt'),'raw_sha256':digest(directory/'daylight_raw.parquet')})
        save(directory/'runtime.json', {**resource(),'model_thread_count':16,'fit_predict_replay_seconds':time.monotonic()-started,'loaded_existing_model':loaded,'versions':{'python':sys.version,'lightgbm':lgb.__version__,'numpy':np.__version__,'pandas':pd.__version__,'pyarrow':pyarrow.__version__}})
        save(directory/'worker_status.json', {'state':'complete','identity':resource(),'model_sha256':digest(directory/'model.txt'),'raw_sha256':digest(directory/'daylight_raw.parquet'),'utc':now()})
        print('TEMPORAL FIT COMPLETE', variant, fold, seed_text, flush=True)

if __name__ == '__main__':
    main()

