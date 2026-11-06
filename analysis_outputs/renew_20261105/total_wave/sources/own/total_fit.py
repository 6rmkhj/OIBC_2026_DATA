# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: total_run.py launches this for ARM FOLD SEED.
"""Fixed-budget total-portfolio LightGBM and saved raw-score replay."""
import json
import sys
import time
from total_common import OUT,ARMS,FOLDS,PARAMS,environment,install_frozen,configure,resource,save,digest,now


def main() -> None:
    environment()
    install_frozen()
    configure()
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- frozen model feature contract
    import lightgbm as lgb
    import pyarrow
    from threadpoolctl import threadpool_limits
    from site_features import normalizer
    arm,fold,seed_text = sys.argv[1:]
    assert arm in ARMS and fold in FOLDS and seed_text in ('0','1','2')
    directory = OUT/'trials'/arm/fold/f'seed{seed_text}'
    directory.mkdir(parents=True,exist_ok=True)
    for name,sha in json.loads((OUT/'prepared_manifest.json').read_text()).items():
        assert digest(OUT/name)==sha,name
    with threadpool_limits(limits=16):
        save(directory/'worker_status.json',{'state':'running','identity':resource(),'utc':now()})
        data_path = OUT/'data'/fold
        specification = json.loads((data_path/'features.json').read_text())
        names = specification['features'][arm]
        train = pd.read_parquet(data_path/'train.parquet',columns=['ts',*names])
        evaluation = pd.read_parquet(data_path/'evaluation.parquet')
        weights = pd.read_parquet(data_path/'targets_weights.parquet')
        pd.testing.assert_series_equal(train.ts,weights.ts)
        assert train.ts.max()<=pd.Timestamp(specification['cutoff'])<evaluation.ts.min()
        assert not {'cf','energy','y','smp','k','grp','grp_code','ts'} & set(names)
        params = {**PARAMS,'random_state':None if seed_text=='0' else int(seed_text)}
        save(directory/'config.json',{'arm':arm,'fold':fold,'seed':int(seed_text),'parameters':params,'features':names,'candidates':specification['candidates'][arm],'train_rows':len(train),'evaluation_rows':len(evaluation),'target':'fulltotal_cf / normalizer','weight':'normalizer * normalized_decay180','inverse':'normalizer * totaldaylight capacity','prepared_manifest_sha256':digest(OUT/'prepared_manifest.json')})
        started = time.monotonic()
        loaded = (directory/'model.txt').exists()
        if loaded:
            model = lgb.Booster(model_file=str(directory/'model.txt'))
        else:
            estimator = lgb.LGBMRegressor(**params)
            estimator.fit(train[names],weights.target.to_numpy(),sample_weight=weights.sample_weight.to_numpy())
            model = estimator.booster_
            model.save_model(str(directory/'model.txt'))
        assert model.current_iteration()==400
        inverse = normalizer(evaluation.cosz.to_numpy())*evaluation.capacity_kw.to_numpy()
        normalized = model.predict(evaluation[names],raw_score=True,num_threads=16)
        prediction = normalized*inverse
        assert np.isfinite(prediction).all()
        raw = evaluation[['ts','capacity_kw']].assign(inverse=inverse,normalized_raw=normalized,p_raw=prediction)
        raw.to_parquet(directory/'total_raw.parquet',index=False)
        replay = lgb.Booster(model_file=str(directory/'model.txt')).predict(evaluation[names],raw_score=True,num_threads=16)
        np.testing.assert_array_equal(normalized,replay)
        np.testing.assert_array_equal(prediction,replay*inverse)
        np.save(directory/'replay_raw.npy',replay)
        save(directory/'replay.json',{'passed':True,'rows':len(raw),'max_absolute_error':0.,'negative_total_raw':int((prediction<0).sum()),'actual_iteration':model.current_iteration(),'model_sha256':digest(directory/'model.txt'),'raw_sha256':digest(directory/'total_raw.parquet')})
        save(directory/'runtime.json',{**resource(),'seconds':time.monotonic()-started,'loaded_existing_model':loaded,'versions':{'python':sys.version,'lightgbm':lgb.__version__,'numpy':np.__version__,'pandas':pd.__version__,'pyarrow':pyarrow.__version__}})
        save(directory/'worker_status.json',{'state':'complete','identity':resource(),'model_sha256':digest(directory/'model.txt'),'raw_sha256':digest(directory/'total_raw.parquet'),'utc':now()})
        print('TOTAL FIT COMPLETE',arm,fold,seed_text,flush=True)

if __name__=='__main__':
    main()
