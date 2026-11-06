# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "scikit-learn", "joblib"]
# ///
# How to run: mlp_run.py --prepare; no MLP fit is called here.
"""TRAIN-only float64 station preprocessing, targets and exact time weights."""
import inspect
import json
import joblib
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- preserve exact original station/key contracts
import sklearn
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from mlp_common import RENEW,OUT,DATA,REFERENCE_DIR,FOLDS,REFERENCE,save,digest,now

def prepare() -> None:
    from learner_models import preprocessing
    from profile_features import column_mask
    from site_features import normalizer
    from final_metrics import metrics
    from mlp_math import weights
    assert 'sample_weight' in inspect.signature(MLPRegressor.fit).parameters
    save(OUT/'evidence/environment.json',{'sklearn_version':sklearn.__version__,'MLP_fit_signature':str(inspect.signature(MLPRegressor.fit)),'sample_weight_supported':True,'numpy_version':np.__version__,'joblib_version':joblib.__version__,'new_dependencies_installed':False})
    capacity = json.loads((RENEW/'final/static_capacity.json').read_text(encoding='utf-8'))
    save(OUT/'static_capacity.json',capacity)
    receipts = []
    for fold,(cutoff_text,end_text) in FOLDS.items():
        cutoff,end = (pd.Timestamp(t,tz='Asia/Seoul') for t in (cutoff_text,end_text))
        candidates = json.loads((DATA/fold/'features.json').read_text(encoding='utf-8'))['station']
        assert len(candidates)==904 and not {'ts','grp','cf','y','energy','smp','k'} & set(candidates)
        train = pd.read_parquet(DATA/fold/'train.parquet',columns=['ts','grp','cf',*candidates])
        evaluation = pd.read_parquet(DATA/fold/'evaluation.parquet',columns=['ts','grp','capacity_kw',*candidates])
        assert train.ts.max()<=cutoff<evaluation.ts.min() and evaluation.ts.max()<=end
        assert not train.duplicated(['ts','grp']).any() and not evaluation.duplicated(['ts','grp']).any()
        selected = column_mask(train,candidates)
        assert selected
        selected_train = train[selected].astype(np.float64)
        selected_eval = evaluation[selected].astype(np.float64)
        transform,x_train,x_evaluation = preprocessing(selected_train,selected_eval)
        scale = normalizer(train.cosz.to_numpy(dtype=np.float64))
        age = (cutoff-train.ts).dt.total_seconds().to_numpy(dtype=np.float64)/86400.
        base,decay,weight,adjustment = weights(scale,age)
        target = train.cf.to_numpy(dtype=np.float64)/scale
        target_scaler = StandardScaler()
        y_train = target_scaler.fit_transform(target.reshape(-1,1)).ravel()
        eval_scale = normalizer(evaluation.cosz.to_numpy(dtype=np.float64))
        inverse = eval_scale*evaluation.capacity_kw.to_numpy(dtype=np.float64)
        for value in (x_train,x_evaluation,y_train,weight,scale,eval_scale,target,inverse):
            assert value.dtype==np.dtype('float64') and np.isfinite(value).all()
        assert (inverse>0).all()
        labels = pd.read_parquet(REFERENCE_DIR/fold/'predictions.parquet',columns=['ts','grp','y','smp','k','p']).rename(columns={'p':'p_reference'})
        coverage = pd.read_parquet(RENEW/'recency_wave/data'/fold/'night_coverage.parquet')
        full = labels[['ts','grp']].merge(coverage,on=['ts','grp'],how='left',sort=False,validate='one_to_one')
        assert full.night.notna().all()
        fields = ['ts','grp','wa_temp','extra_wa_snow','wb_cloud']
        joined = full.merge(evaluation[fields],on=['ts','grp'],how='left',sort=False,validate='one_to_one',indicator=True)
        assert joined._merge.eq('left_only').eq(joined.night).all()
        assert int(joined._merge.eq('both').sum())==len(evaluation)
        assert labels.loc[full.night,'p_reference'].eq(0).all()
        inputs = joined[fields].copy()
        inputs['static_capacity'] = inputs.grp.map(capacity)
        assert inputs.static_capacity.notna().all()
        assert abs(metrics(labels,'p_reference')['W_pct']-REFERENCE[fold])<1e-10
        directory = OUT/'data'/fold
        directory.mkdir(parents=True)
        train.to_parquet(directory/'train.parquet',index=False)
        evaluation.to_parquet(directory/'evaluation.parquet',index=False)
        labels.to_parquet(directory/'labels.parquet',index=False)
        coverage.to_parquet(directory/'coverage.parquet',index=False)
        inputs.to_parquet(directory/'application_inputs.parquet',index=False)
        save(directory/'feature_mask.json',{'candidate_columns':candidates,'selected_columns':selected,'dropped_columns':[n for n in candidates if n not in selected],'fitted_on':'training only','selected_cast_dtype':'float64','cutoff':str(cutoff),'end':str(end),'train_rows':len(train),'evaluation_rows':len(evaluation)})
        joblib.dump(transform,directory/'input_preprocessing.joblib')
        joblib.dump(target_scaler,directory/'target_scaler.joblib')
        for name,value in [('x_train',x_train),('x_evaluation',x_evaluation),('y_train',y_train),('sample_weight',weight)]:
            np.save(directory/f'{name}.npy',value,allow_pickle=False)
        train_transform = train[['ts','grp']].assign(normalizer=scale,age_days=age,base_weight=base,decay=decay,weight_normalization=adjustment,sample_weight=weight,target_normalized=target,target_scaled=y_train)
        eval_transform = evaluation[['ts','grp']].assign(normalizer=eval_scale,capacity_kw=evaluation.capacity_kw.to_numpy(dtype=np.float64),inverse_kwh=inverse)
        train_transform.to_parquet(directory/'training_transform.parquet',index=False)
        eval_transform.to_parquet(directory/'evaluation_transform.parquet',index=False)
        np.testing.assert_array_equal(joblib.load(directory/'input_preprocessing.joblib').transform(selected_train),x_train)
        np.testing.assert_array_equal(joblib.load(directory/'input_preprocessing.joblib').transform(selected_eval),x_evaluation)
        np.testing.assert_array_equal(joblib.load(directory/'target_scaler.joblib').transform(target.reshape(-1,1)).ravel(),y_train)
        before = joblib.hash(transform)
        adversarial = selected_eval.copy()
        adversarial.iloc[:min(3,len(adversarial)),:] = np.nan
        transform.transform(adversarial)
        assert joblib.hash(transform)==before
        receipts.append({'fold':fold,'train_rows':len(train),'evaluation_rows':len(evaluation),'full_rows':len(labels),'selected_features':len(selected),'candidate_features':904,'feature_dtype':str(x_train.dtype),'target_dtype':str(y_train.dtype),'weight_dtype':str(weight.dtype),'base_weight_sum':float(base.sum()),'sample_weight_sum':float(weight.sum()),'weight_mass_error':float(weight.sum()-base.sum()),'train_only_transform_replay_exact':True,'target_transform_replay_exact':True,'eval_transform_did_not_mutate_preprocessor':True,'exact_daylight_keys':True,'night_rows':int(full.night.sum()),'cutoff':str(cutoff),'train_max_ts':str(train.ts.max()),'evaluation_min_ts':str(evaluation.ts.min()),'real_model_fits':0})
    save(OUT/'evidence/read_receipts.json',receipts)
    manifest = {str(p.relative_to(OUT)):digest(p) for p in (OUT/'data').rglob('*') if p.is_file()}
    manifest['evidence/environment.json'] = digest(OUT/'evidence/environment.json')
    save(OUT/'prepared_manifest.json',manifest)
