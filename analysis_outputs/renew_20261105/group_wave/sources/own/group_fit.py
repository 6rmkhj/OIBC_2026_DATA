# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: group_run.py launches this once per ARM FOLD SEED.
"""One serial native custom-objective fit and exact raw-score replay."""
import json
import sys
import time
from group_common import OUT, ARMS, FOLDS, PARAMS, environment, install_frozen, configure, resource, save, digest, now

def main() -> None:
    environment()
    install_frozen()
    configure()
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- frozen site feature contracts
    import lightgbm as lgb
    import pyarrow
    from threadpoolctl import threadpool_limits
    from group_objective import GroupLoss
    arm,fold,seed_text = sys.argv[1:]
    assert arm in ARMS and fold in FOLDS and seed_text in ('0','1','2')
    directory = OUT/'trials'/arm/fold/f'seed{seed_text}'
    directory.mkdir(parents=True,exist_ok=True)
    prepared = json.loads((OUT/'prepared_manifest.json').read_text())
    for name,sha in prepared.items():
        assert digest(OUT/name)==sha,name
    with threadpool_limits(limits=16):
        save(directory/'worker_status.json',{'state':'running','identity':resource(),'utc':now()})
        data_path = OUT/'data'/fold
        train = pd.read_parquet(data_path/'train.parquet')
        evaluation = pd.read_parquet(data_path/'evaluation.parquet')
        rows = pd.read_parquet(data_path/'rows.parquet')
        groups = pd.read_parquet(data_path/'groups.parquet')
        names = json.loads((data_path/'features.json').read_text())['features']
        pd.testing.assert_frame_equal(train[['ts','site_id','grp','capacity_kw','cf','row_id']],rows[['ts','site_id','grp','capacity_kw','cf','row_id']])
        np.testing.assert_array_equal(rows.row_id,np.arange(len(train)))
        np.testing.assert_array_equal(groups.group_id,np.arange(len(groups)))
        delta,regularizer,grouped = ARMS[arm]
        loss = GroupLoss(rows.group_id.to_numpy(dtype=np.int64),rows.share.to_numpy(dtype=np.float64),groups.target.to_numpy(dtype=np.float64),train.cf.to_numpy(dtype=np.float64),rows.weight.to_numpy(dtype=np.float64),groups.group_weight.to_numpy(dtype=np.float64),delta,regularizer,grouped)
        dataset = lgb.Dataset(train[names],label=loss.cf,free_raw_data=False)
        diagnostics = []
        calls = 0
        def diagnostic(prediction,iteration):
            residual = loss.residual(prediction)
            diagnostics.append({'iteration':iteration,'group_weighted_L1':float(np.dot(loss.group_weight,np.abs(residual))),'declared_smooth_objective':loss.value(prediction)})
        def objective(prediction,data):
            nonlocal calls
            assert data is dataset
            if calls==0:
                np.testing.assert_array_equal(prediction,0.)
            if calls%100==0:
                diagnostic(prediction,calls)
            calls += 1
            return loss(prediction,data)
        params = {**PARAMS,'seed':int(seed_text),'feature_fraction_seed':int(seed_text),'objective':objective}
        save(directory/'config.json',{'arm':arm,'fold':fold,'seed':int(seed_text),'parameters':{**PARAMS,'seed':int(seed_text),'feature_fraction_seed':int(seed_text),'objective':'native callable complete group' if grouped else 'native callable site control'},'boosting_rounds':1000,'features':names,'train_rows':len(train),'train_groups':len(groups),'dataset_weight':None,'dataset_init_score':None,'majorizer':'global diagonal, not exact Hessian','prepared_manifest_sha256':digest(OUT/'prepared_manifest.json')})
        start = time.monotonic()
        loaded = (directory/'model.txt').exists()
        if loaded:
            model = lgb.Booster(model_file=str(directory/'model.txt'))
            diagnostics = json.loads((directory/'diagnostics.json').read_text())
        else:
            model = lgb.train(params,dataset,num_boost_round=1000)
            model.save_model(str(directory/'model.txt'))
            diagnostic(model.predict(train[names],raw_score=True,num_threads=16),model.current_iteration())
            save(directory/'diagnostics.json',diagnostics)
        save(directory/'iteration.json',{'actual_iteration':model.current_iteration(),'requested_iteration':1000,'objective_calls':calls,'loaded_existing_model':loaded})
        assert model.current_iteration()==1000,'Genuine early terminal condition: root review required before adoption'
        day = ~evaluation.night
        prediction = np.zeros(len(evaluation),dtype=np.float64)
        prediction[day] = model.predict(evaluation.loc[day,names],raw_score=True,num_threads=16)
        assert np.isfinite(prediction).all()
        raw = evaluation[['ts','site_id','grp','capacity_kw','night']].assign(cf_raw=prediction)
        raw['energy_raw'] = raw.cf_raw*raw.capacity_kw
        raw.to_parquet(directory/'site_raw.parquet',index=False)
        grouped_raw = raw.groupby(['ts','grp'],as_index=False,observed=True).energy_raw.sum().rename(columns={'energy_raw':'p_raw'})
        grouped_raw.to_parquet(directory/'group_raw.parquet',index=False)
        replay = lgb.Booster(model_file=str(directory/'model.txt')).predict(evaluation.loc[day,names],raw_score=True,num_threads=16)
        np.testing.assert_array_equal(prediction[day],replay)
        np.save(directory/'replay_raw.npy',replay)
        save(directory/'replay.json',{'passed':True,'rows':int(day.sum()),'max_absolute_error':float(np.max(np.abs(prediction[day]-replay))),'negative_cf_rows':int((prediction<0).sum()),'negative_group_rows':int((grouped_raw.p_raw<0).sum()),'night_exact_zero':bool((prediction[~day]==0).all()),'model_sha256':digest(directory/'model.txt'),'raw_sha256':digest(directory/'site_raw.parquet')})
        save(directory/'runtime.json',{**resource(),'seconds':time.monotonic()-start,'loaded_existing_model':loaded,'versions':{'python':sys.version,'lightgbm':lgb.__version__,'numpy':np.__version__,'pandas':pd.__version__,'pyarrow':pyarrow.__version__}})
        save(directory/'worker_status.json',{'state':'complete','identity':resource(),'model_sha256':digest(directory/'model.txt'),'raw_sha256':digest(directory/'site_raw.parquet'),'utc':now()})
        print('GROUP FIT COMPLETE',arm,fold,seed_text,flush=True)

if __name__=='__main__':
    main()
