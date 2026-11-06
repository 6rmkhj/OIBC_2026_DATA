# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: released renew_final_run.py launches SPLIT SEED serially.
"""One of exactly six fixed-cutoff normalized temporal180 fits."""
import json
import sys
import time
from renew_final_common import OUT,CUTOFFS,PARAMS,environment,install_frozen,configure,resource,save,digest,now


def main() -> None:
    environment()
    install_frozen()
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- unchanged normalized temporal model contract
    import lightgbm as lgb
    from site_features import normalizer
    from threadpoolctl import threadpool_limits
    configure()
    split,seed_text = sys.argv[1:]
    assert split in CUTOFFS and seed_text in ('0','1','2')
    release = json.loads((OUT/'release.json').read_text())
    assert release['approved'] and release['protocol_sha256']==digest(OUT/'protocol.json') and release['prepared_manifest_sha256']==digest(OUT/'prepared_manifest.json')
    directory = OUT/'models'/split/f'seed{seed_text}'
    directory.mkdir(parents=True,exist_ok=True)
    with threadpool_limits(limits=16):
        save(directory/'worker_status.json',{'state':'running','identity':resource(),'utc':now()})
        for p,sha in json.loads((OUT/'prepared_manifest.json').read_text()).items():
            assert digest(OUT/p)==sha,p
        spec = json.loads((OUT/'data'/split/'features.json').read_text())
        names = spec['features']
        train = pd.read_parquet(OUT/'data'/split/'train.parquet')
        weights = pd.read_parquet(OUT/'data'/split/'weights.parquet')
        evaluation = pd.read_parquet(OUT/'data'/('march_may' if split=='latest' else 'test')/'evaluation.parquet')
        pd.testing.assert_frame_equal(train[['ts','grp']],weights[['ts','grp']])
        assert train.ts.max()<=pd.Timestamp(spec['cutoff'])<evaluation.ts.min()
        params = {**PARAMS,'random_state':None if seed_text=='0' else int(seed_text)}
        save(directory/'config.json',{'split':split,'seed':int(seed_text),'parameters':params,'features':names,'candidates':spec['candidates'],'cutoff':spec['cutoff'],'train_rows':len(train),'evaluation_rows':len(evaluation),'prepared_manifest_sha256':digest(OUT/'prepared_manifest.json')})
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
        prediction = model.predict(evaluation[names],raw_score=True,num_threads=16)*inverse
        assert np.isfinite(prediction).all()
        raw = evaluation[['ts','grp']].assign(p_raw=prediction)
        raw.to_parquet(directory/'daylight_raw.parquet',index=False)
        replay = lgb.Booster(model_file=str(directory/'model.txt')).predict(evaluation[names],raw_score=True,num_threads=16)*inverse
        np.testing.assert_array_equal(prediction,replay)
        save(directory/'replay.json',{'passed':True,'rows':len(raw),'actual_iteration':model.current_iteration(),'max_absolute_error':0.,'model_sha256':digest(directory/'model.txt'),'raw_sha256':digest(directory/'daylight_raw.parquet')})
        save(directory/'runtime.json',{**resource(),'seconds':time.monotonic()-started,'loaded_existing_model':loaded})
        save(directory/'worker_status.json',{'state':'complete','identity':resource(),'model_sha256':digest(directory/'model.txt'),'raw_sha256':digest(directory/'daylight_raw.parquet'),'utc':now()})
        print('RENEW FINAL FIT COMPLETE',split,seed_text,flush=True)

if __name__=='__main__':
    main()
