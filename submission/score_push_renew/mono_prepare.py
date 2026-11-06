# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: mono_run.py --prepare; this module performs zero model fits.
"""Native station inputs, TRAIN-only masks, fixed weights and constraint vectors."""
import json
import shutil
from pathlib import Path
import lightgbm as lgb
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen station/key/scoring contracts
from mono_common import RENEW,OUT,DATA,MLP,FOLDS,REFERENCE,save,digest
from mono_math import constraints,weights

def prepare() -> None:
    from profile_features import column_mask
    from site_features import normalizer
    from final_metrics import metrics
    native = Path(lgb.__file__).parent/'bin/lib_lightgbm.dll'
    compatibility = json.loads((RENEW/'monotone_compatibility.json').read_text(encoding='utf-8'))
    assert lgb.__version__==compatibility['lightgbm']=='4.7.0'
    assert digest(native)==compatibility['native_sha256']
    save(OUT/'evidence/environment.json',{'lightgbm_version':lgb.__version__,'native_library':str(native),'native_sha256':digest(native),'numpy_version':np.__version__,'new_dependencies_installed':False,'real_model_fits':0})
    receipts = []
    for fold,(cutoff_text,end_text) in FOLDS.items():
        cutoff,end = (pd.Timestamp(t,tz='Asia/Seoul') for t in (cutoff_text,end_text))
        candidates = json.loads((DATA/fold/'features.json').read_text(encoding='utf-8'))['station']
        assert len(candidates)==904 and len(set(candidates))==904
        assert not {'ts','grp','cf','y','energy','smp','k'} & set(candidates)
        train = pd.read_parquet(DATA/fold/'train.parquet')
        evaluation = pd.read_parquet(DATA/fold/'evaluation.parquet')
        assert list(train)==['ts','grp','cf',*candidates]
        assert list(evaluation)==['ts','grp','capacity_kw',*candidates]
        assert train.ts.max()<=cutoff<evaluation.ts.min() and evaluation.ts.max()<=end
        assert not train.duplicated(['ts','grp']).any() and not evaluation.duplicated(['ts','grp']).any()
        names = column_mask(train,candidates)
        vector = constraints(names)
        expected = (460,62) if fold=='primary' else (790,117)
        assert len(names)==expected[0] and vector.count(-1)==vector.count(1)==expected[1]
        assert not np.isinf(train[names].to_numpy()).any() and not np.isinf(evaluation[names].to_numpy()).any()
        scale = normalizer(train.cosz.to_numpy())
        age = (cutoff-train.ts).dt.total_seconds().to_numpy()/86400
        decay,multiplier,weight = weights(scale,age)
        target = train.cf.to_numpy()/scale
        eval_scale = normalizer(evaluation.cosz.to_numpy())
        inverse = eval_scale*evaluation.capacity_kw.to_numpy()
        for value in (scale,age,decay,multiplier,weight,target,eval_scale,inverse):
            assert np.isfinite(value).all()
        assert (inverse>0).all()
        previous = pd.read_parquet(RENEW/'recency_wave/data/decay180'/fold/'training_weights.parquet')
        pd.testing.assert_frame_equal(train[['ts','grp']],previous[['ts','grp']])
        for name,value in (('normalizer',scale),('age_days',age),('recency_multiplier',multiplier),('sample_weight',weight)):
            np.testing.assert_array_equal(previous[name],value)
        labels = pd.read_parquet(MLP/'data'/fold/'labels.parquet')
        coverage = pd.read_parquet(MLP/'data'/fold/'coverage.parquet')
        inputs = pd.read_parquet(MLP/'data'/fold/'application_inputs.parquet')
        assert abs(metrics(labels,'p_reference')['W_pct']-REFERENCE[fold])<1e-10
        pd.testing.assert_frame_equal(labels[['ts','grp']],inputs[['ts','grp']])
        full = labels[['ts','grp']].merge(coverage,on=['ts','grp'],sort=False,validate='one_to_one')
        assert full.night.notna().all()
        keys = full.merge(evaluation[['ts','grp']],on=['ts','grp'],how='left',sort=False,validate='one_to_one',indicator=True)
        assert keys._merge.eq('left_only').eq(keys.night).all()
        assert int(keys._merge.eq('both').sum())==len(evaluation)
        assert labels.loc[full.night,'p_reference'].eq(0).all()
        directory = OUT/'data'/fold
        directory.mkdir(parents=True)
        for name in ('train.parquet','evaluation.parquet'):
            shutil.copyfile(DATA/fold/name,directory/name)
            assert digest(DATA/fold/name)==digest(directory/name)
        for name in ('labels.parquet','coverage.parquet','application_inputs.parquet'):
            shutil.copyfile(MLP/'data'/fold/name,directory/name)
            assert digest(MLP/'data'/fold/name)==digest(directory/name)
        save(directory/'feature_mask.json',{'candidate_columns':candidates,'selected_columns':names,'dropped_columns':[n for n in candidates if n not in names],'fitted_on':'training only','native_nan':True,'selected_dtypes':{n:str(train[n].dtype) for n in names},'cutoff':str(cutoff),'end':str(end),'train_rows':len(train),'evaluation_rows':len(evaluation)})
        pd.DataFrame({'feature_index':range(len(names)),'feature':names,'fair_control':[0]*len(names),'fair_monotone':vector}).to_parquet(directory/'constraints.parquet',index=False)
        train[['ts','grp']].assign(normalizer=scale,age_days=age,decay=decay,recency_multiplier=multiplier,sample_weight=weight,target_normalized=target).to_parquet(directory/'training_transform.parquet',index=False)
        evaluation[['ts','grp']].assign(normalizer=eval_scale,capacity_kw=evaluation.capacity_kw.to_numpy(),inverse_kwh=inverse).to_parquet(directory/'evaluation_transform.parquet',index=False)
        receipts.append({'fold':fold,'train_rows':len(train),'evaluation_rows':len(evaluation),'full_rows':len(labels),'selected_features':len(names),'candidate_features':904,'negative_constraints':vector.count(-1),'positive_constraints':vector.count(1),'zero_constraints':vector.count(0),'native_train_nan_entries':int(train[names].isna().to_numpy().sum()),'native_evaluation_nan_entries':int(evaluation[names].isna().to_numpy().sum()),'raw_inputs_byte_identical':True,'scoring_inputs_byte_identical':True,'recency180_training_weights_exact':True,'mean_recency_multiplier':float(multiplier.mean()),'sample_weight_sum':float(weight.sum()),'exact_daylight_keys':True,'night_rows':int(full.night.sum()),'cutoff':str(cutoff),'train_max_ts':str(train.ts.max()),'evaluation_min_ts':str(evaluation.ts.min()),'real_model_fits':0})
    save(OUT/'evidence/read_receipts.json',receipts)
    manifest = {str(p.relative_to(OUT)):digest(p) for p in (OUT/'data').rglob('*') if p.is_file()}
    for name in ('environment.json','read_receipts.json','selfchecks.json'):
        manifest['evidence/'+name] = digest(OUT/'evidence'/name)
    save(OUT/'prepared_manifest.json',manifest)
