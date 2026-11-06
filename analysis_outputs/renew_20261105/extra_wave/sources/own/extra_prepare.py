# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "scikit-learn", "threadpoolctl"]
# ///
# How to run: extra_run.py --prepare; zero ExtraTrees fits or predictions.
"""Raw rich100 and independently checked pre-StandardScaler MLP scalars."""
import inspect
import json
import shutil
from pathlib import Path
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact frozen frame and target/weight lineage
import sklearn
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.ensemble import _forest
from sklearn.tree import _classes,_tree
from extra_common import OUT,DATA,MLP,REFERENCE_DIR,FOLDS,REFERENCE,save,digest
from extra_math import weights

def prepare() -> None:
    from site_features import normalizer
    from final_metrics import metrics
    assert sklearn.__version__=='1.9.1'
    files = [Path(module.__file__) for module in (_forest,_classes,_tree)]
    source = '\n\n'.join(inspect.getsource(getattr(ExtraTreesRegressor,name)) for name in ('fit','predict'))
    assert 'prefer="threads"' in source and 'require="sharedmem"' in source and 'ensure_all_finite=False' in source
    assert 'sample_weight' in inspect.signature(ExtraTreesRegressor.fit).parameters
    (OUT/'evidence/installed_extra_source.txt').write_text(source,encoding='utf-8')
    save(OUT/'evidence/environment.json',{'sklearn_version':sklearn.__version__,'fit_signature':str(inspect.signature(ExtraTreesRegressor.fit)),'constructor_signature':str(inspect.signature(ExtraTreesRegressor)),'installed_sources_sha256':{str(p):digest(p) for p in files},'fit_prefer_threads':True,'predict_shared_accumulation':True,'source_accepts_nan':True,'new_dependencies_installed':False,'real_model_fits':0})
    receipts = []
    scalar_columns = ['ts','grp','normalizer','age_days','base_weight','decay','weight_normalization','sample_weight','target_normalized']
    for fold,(cutoff_text,end_text) in FOLDS.items():
        cutoff,end = (pd.Timestamp(t,tz='Asia/Seoul') for t in (cutoff_text,end_text))
        names = json.loads((DATA/fold/'features.json').read_text(encoding='utf-8'))['rich']
        assert len(names)==len(set(names))==100 and not {'ts','grp','cf','energy','y','smp','k'} & set(names)
        assert not any(n.startswith(('wa_station_','wb_station_')) for n in names)
        train = pd.read_parquet(DATA/fold/'train.parquet',columns=['ts','grp','cf',*names])
        evaluation = pd.read_parquet(DATA/fold/'evaluation.parquet',columns=['ts','grp','capacity_kw',*names])
        assert train.ts.max()<=cutoff<evaluation.ts.min() and evaluation.ts.max()<=end
        assert not train.duplicated(['ts','grp']).any() and not evaluation.duplicated(['ts','grp']).any()
        assert not np.isinf(train[names].to_numpy()).any() and not np.isinf(evaluation[names].to_numpy()).any()
        scale = normalizer(train.cosz.to_numpy(dtype=np.float64))
        age = (cutoff-train.ts).dt.total_seconds().to_numpy(dtype=np.float64)/86400.
        base,decay,weight,adjustment = weights(scale,age)
        target = train.cf.to_numpy(dtype=np.float64)/scale
        eval_scale = normalizer(evaluation.cosz.to_numpy(dtype=np.float64))
        inverse = eval_scale*evaluation.capacity_kw.to_numpy(dtype=np.float64)
        transform = pd.read_parquet(MLP/'data'/fold/'training_transform.parquet',columns=scalar_columns)
        pd.testing.assert_frame_equal(transform[['ts','grp']],train[['ts','grp']])
        for name,value in (('normalizer',scale),('age_days',age),('base_weight',base),('decay',decay),('sample_weight',weight),('target_normalized',target)):
            np.testing.assert_array_equal(transform[name],value)
        assert transform.weight_normalization.eq(adjustment).all()
        eval_transform = pd.read_parquet(MLP/'data'/fold/'evaluation_transform.parquet')
        pd.testing.assert_frame_equal(eval_transform[['ts','grp']],evaluation[['ts','grp']])
        np.testing.assert_array_equal(eval_transform.normalizer,eval_scale)
        np.testing.assert_array_equal(eval_transform.capacity_kw,evaluation.capacity_kw.to_numpy(dtype=np.float64))
        np.testing.assert_array_equal(eval_transform.inverse_kwh,inverse)
        assert np.isfinite(target).all() and np.isfinite(inverse).all() and (inverse>0).all()
        labels = pd.read_parquet(REFERENCE_DIR/fold/'predictions.parquet',columns=['ts','grp','y','smp','k','p']).rename(columns={'p':'p_reference'})
        assert abs(metrics(labels,'p_reference')['W_pct']-REFERENCE[fold])<1e-10
        coverage = pd.read_parquet(MLP/'data'/fold/'coverage.parquet')
        inputs = pd.read_parquet(MLP/'data'/fold/'application_inputs.parquet',columns=['ts','grp','wa_temp','extra_wa_snow','static_capacity'])
        reference_inputs = pd.read_parquet(REFERENCE_DIR/fold/'predictions.parquet',columns=list(inputs))
        pd.testing.assert_frame_equal(inputs,reference_inputs)
        pd.testing.assert_frame_equal(inputs[['ts','grp']],labels[['ts','grp']])
        covered = inputs[['ts','grp']].merge(coverage,on=['ts','grp'],sort=False,validate='one_to_one')
        assert covered.night.notna().all() and labels.loc[covered.night,'p_reference'].eq(0).all()
        joined = covered.merge(evaluation[['ts','grp','wa_temp','extra_wa_snow']],on=['ts','grp'],how='left',sort=False,validate='one_to_one',indicator=True)
        assert joined._merge.eq('left_only').eq(joined.night).all() and int(joined._merge.eq('both').sum())==len(evaluation)
        pd.testing.assert_frame_equal(inputs[['wa_temp','extra_wa_snow']],joined[['wa_temp','extra_wa_snow']])
        directory = OUT/'data'/fold
        directory.mkdir(parents=True)
        train.to_parquet(directory/'train.parquet',index=False)
        evaluation.to_parquet(directory/'evaluation.parquet',index=False)
        save(directory/'features.json',{'rich':names,'train_rows':len(train),'evaluation_rows':len(evaluation),'cutoff':str(cutoff),'end':str(end),'native_nan':True,'feature_pruning':False,'imputation':False,'scaling':False,'dtypes':{n:str(train[n].dtype) for n in names}})
        transform.to_parquet(directory/'training_transform.parquet',index=False)
        for name in ('evaluation_transform.parquet','coverage.parquet'):
            shutil.copyfile(MLP/'data'/fold/name,directory/name)
            assert digest(MLP/'data'/fold/name)==digest(directory/name)
        labels.to_parquet(directory/'labels.parquet',index=False)
        inputs.to_parquet(directory/'application_inputs.parquet',index=False)
        pd.testing.assert_frame_equal(pd.read_parquet(directory/'train.parquet'),train)
        pd.testing.assert_frame_equal(pd.read_parquet(directory/'evaluation.parquet'),evaluation)
        receipts.append({'fold':fold,'train_rows':len(train),'evaluation_rows':len(evaluation),'feature_count':100,'train_nan_entries':int(train[names].isna().to_numpy().sum()),'evaluation_nan_entries':int(evaluation[names].isna().to_numpy().sum()),'raw_projection_values_dtypes_NaNs_exact':True,'target_pre_StandardScaler_exact':True,'sample_weight_mlp_exact':True,'weight_mass_error':float(weight.sum()-base.sum()),'inverse_mlp_exact':True,'weather_reference_W_pct':metrics(labels,'p_reference')['W_pct'],'weather_inputs_exact':True,'night_rows':int(covered.night.sum()),'train_max':str(train.ts.max()),'evaluation_min':str(evaluation.ts.min()),'source_train_sha256':digest(DATA/fold/'train.parquet'),'source_target_weight_sha256':digest(MLP/'data'/fold/'training_transform.parquet'),'source_inverse_sha256':digest(MLP/'data'/fold/'evaluation_transform.parquet'),'real_model_fits':0})
    save(OUT/'evidence/read_receipts.json',receipts)
    manifest = {str(p.relative_to(OUT)):digest(p) for p in (OUT/'data').rglob('*') if p.is_file()}
    for name in ('environment.json','installed_extra_source.txt','read_receipts.json','selfchecks.json'):
        manifest['evidence/'+name] = digest(OUT/'evidence'/name)
    save(OUT/'prepared_manifest.json',manifest)
