# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "catboost", "threadpoolctl"]
# ///
"""One embargoed GPU cloud fit, saved labels, and exact model replay."""
from cloud_common import OUT, CUTOFFS, AUX_PARAMS, install_frozen, configure, resource, save, digest, now, observed
import json
import sys
import time

def main() -> None:
    install_frozen()
    configure()
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- existing scientific helper contracts
    from catboost import CatBoostRegressor
    from threadpoolctl import threadpool_limits
    provider, cutoff_text = sys.argv[1:]
    directory = OUT/'auxiliary'/provider/cutoff_text
    directory.mkdir(parents=True,exist_ok=True)
    cutoff = pd.Timestamp(cutoff_text,tz='Asia/Seoul')
    station = f'{provider}_station'
    schema = json.loads((OUT/'data'/f'{provider}_schema.json').read_text())
    names = schema['features']
    with threadpool_limits(limits=16):
        save(directory/'worker_status.json',{'state':'running','identity':resource(),'utc':now()})
        labels, read_receipt = observed(provider,cutoff_text)
        assert labels.ts.max() <= cutoff-pd.Timedelta(days=1)
        assert labels[f'{provider}_cloud'].between(0,100).all()
        labels.to_parquet(directory/'labels.parquet',index=False)
        train = pd.read_parquet(OUT/'data'/f'{provider}_forecast.parquet',filters=[('ts','<=',cutoff-pd.Timedelta(days=1))])
        train = labels.merge(train,on=[station,'ts'],how='left',validate='one_to_one',indicator=True)
        assert train._merge.eq('both').all()
        assert not any('observed' in name for name in names)
        params = {**AUX_PARAMS,'train_dir':str(directory/'catboost'),'snapshot_file':str(directory/'training.snapshot')}
        save(directory/'config.json',{'provider':provider,'cutoff':str(cutoff),'parameters':params,'features':names,'categorical':[station],'training_rows':len(train),'training_min':str(train.ts.min()),'training_max':str(train.ts.max()),'labels_sha256':digest(directory/'labels.parquet'),'observation_read':read_receipt,'panel_sha256':schema['sha256']})
        started = time.monotonic()
        model = CatBoostRegressor(**params)
        loaded = (directory/'model.cbm').exists()
        if loaded:
            model.load_model(str(directory/'model.cbm'))
        else:
            model.fit(train[names],train[f'{provider}_cloud'],cat_features=[station])
            model.save_model(str(directory/'model.cbm'))
        del train, labels
        index = CUTOFFS.index(cutoff_text)
        end_text = CUTOFFS[index+1] if index+1<len(CUTOFFS) else '2025-03-01'
        if cutoff_text == '2023-06-01':
            end_text = '2024-06-01'
        end = pd.Timestamp(end_text,tz='Asia/Seoul')
        frame = pd.read_parquet(OUT/'data'/f'{provider}_forecast.parquet',filters=[('ts','>',cutoff),('ts','<=',end)])
        prediction = model.predict(frame[names],thread_count=16)
        assert np.isfinite(prediction).all()
        replay_model = CatBoostRegressor()
        replay_model.load_model(str(directory/'model.cbm'))
        replay = replay_model.predict(frame[names],thread_count=16)
        np.testing.assert_array_equal(prediction,replay)
        frame = frame[[station,'ts']].assign(p_raw=prediction,p_cloud=np.clip(prediction,0,100),model_cutoff=cutoff,warmup=0)
        assert (frame.ts>frame.model_cutoff).all()
        frame.to_parquet(directory/'predictions.parquet',index=False)
        save(directory/'replay.json',{'passed':True,'rows':len(frame),'max_absolute_error':0.,'model_sha256':digest(directory/'model.cbm'),'raw_sha256':digest(directory/'predictions.parquet')})
        save(directory/'runtime.json',{**resource(),'fit_predict_replay_seconds':time.monotonic()-started,'loaded_existing_model':loaded,'tree_count':model.tree_count_})
        assert model.tree_count_==1000
        save(directory/'worker_status.json',{'state':'complete','identity':resource(),'model_sha256':digest(directory/'model.cbm'),'raw_sha256':digest(directory/'predictions.parquet'),'utc':now()})
        print('AUXILIARY TERMINAL',provider,cutoff_text,flush=True)

if __name__=='__main__':
    main()
