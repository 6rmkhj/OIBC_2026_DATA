# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: released weight_run.py launches ARM FOLD SEED serially.
"""One unchanged temporal model with the declared mass-preserving row weights."""
import json
import sys
import time
from weight_common import OUT,ARMS,FOLDS,PARAMS,environment,install_frozen,configure,resource,save,digest,now


def main() -> None:
    environment()
    install_frozen()
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- exact temporal estimator contract
    import lightgbm as lgb
    from site_features import normalizer
    from threadpoolctl import threadpool_limits
    configure()
    arm,fold,seed_text = sys.argv[1:]
    assert arm in ARMS and fold in FOLDS and seed_text in ('0','1','2')
    release = json.loads((OUT/'release.json').read_text())
    assert release['approved'] and release['protocol_sha256']==digest(OUT/'protocol.json') and release['prepared_manifest_sha256']==digest(OUT/'prepared_manifest.json')
    directory = OUT/'trials'/arm/fold/f'seed{seed_text}'
    directory.mkdir(parents=True,exist_ok=True)
    with threadpool_limits(limits=16):
        save(directory/'worker_status.json',{'state':'running','identity':resource(),'utc':now()})
        for p,sha in json.loads((OUT/'prepared_manifest.json').read_text()).items():
            assert digest(OUT/p)==sha,p
        spec = json.loads((OUT/'data'/fold/'features.json').read_text())
        names = spec['features']
        train = pd.read_parquet(OUT/'data'/fold/'train.parquet')
        evaluation = pd.read_parquet(OUT/'data'/fold/'evaluation.parquet')
        weights_path = OUT/'data'/arm/fold/'weights.parquet'
        weights = pd.read_parquet(weights_path)
        pd.testing.assert_frame_equal(train[['ts','grp']],weights[['ts','grp']])
        np.testing.assert_array_equal(weights.row_id,np.arange(len(train)))
        assert train.ts.max()<=pd.Timestamp(spec['cutoff'])<evaluation.ts.min()
        assert not {'y','cf','energy','smp','k','day_capacity'} & set(evaluation)
        params = {**PARAMS,'random_state':None if seed_text=='0' else int(seed_text)}
        save(directory/'config.json',{'arm':arm,'fold':fold,'seed':int(seed_text),'parameters':params,'features':names,'candidates':spec['candidates'],'train_rows':len(train),'evaluation_rows':len(evaluation),'zero_weight_rows':int(weights.sample_weight.eq(0).sum()),'weights_sha256':digest(weights_path),'prepared_manifest_sha256':digest(OUT/'prepared_manifest.json')})
        start = time.monotonic()
        loaded = (directory/'model.txt').exists()
        if loaded:
            model = lgb.Booster(model_file=str(directory/'model.txt'))
        else:
            estimator = lgb.LGBMRegressor(**params)
            estimator.fit(train[names],train.cf.to_numpy()/normalizer(train.cosz.to_numpy()),sample_weight=weights.sample_weight.to_numpy())
            model = estimator.booster_
            model.save_model(str(directory/'model.txt'))
        assert model.current_iteration()==400
        inverse = normalizer(evaluation.cosz.to_numpy())*evaluation.capacity_kw.to_numpy()
        prediction = model.predict(evaluation[names],raw_score=True,num_threads=16)*inverse
        assert np.isfinite(prediction).all()
        raw = evaluation[['ts','grp']].assign(p_raw=prediction)
        raw.to_parquet(directory/'daylight_raw.parquet',index=False)
        replay = lgb.Booster(model_file=str(directory/'model.txt')).predict(evaluation[names],raw_score=True,num_threads=16)*inverse
        np.testing.assert_array_equal(prediction,replay)
        save(directory/'replay.json',{'passed':True,'rows':len(raw),'actual_iteration':400,'max_absolute_error':0.,'negative_raw':int((prediction<0).sum()),'model_sha256':digest(directory/'model.txt'),'raw_sha256':digest(directory/'daylight_raw.parquet')})
        save(directory/'runtime.json',{**resource(),'seconds':time.monotonic()-start,'loaded_existing_model':loaded})
        save(directory/'worker_status.json',{'state':'complete','identity':resource(),'model_sha256':digest(directory/'model.txt'),'raw_sha256':digest(directory/'daylight_raw.parquet'),'utc':now()})
        print('WEIGHT FIT COMPLETE',arm,fold,seed_text,flush=True)

if __name__=='__main__':
    main()
