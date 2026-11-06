# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: poisson_run.py --prepare; zero model fits or native predictions.
"""Independently reconstruct station masks, temporal scalars and weather inputs."""
import json
import shutil
from pathlib import Path
import lightgbm as lgb
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact frozen station/scalar contracts
from poisson_common import ROOT,RENEW,OUT,DATA,MONO,VERIFIED,REFERENCE_DIR,FOLDS,REFERENCE,save,digest
from poisson_math import weights

def prepare() -> None:
    from profile_features import column_mask
    from site_features import normalizer
    from final_metrics import metrics
    native = Path(lgb.__file__).parent/'bin/lib_lightgbm.dll'
    compatibility = json.loads((RENEW/'monotone_compatibility.json').read_text(encoding='utf-8'))
    assert lgb.__version__==compatibility['lightgbm']=='4.7.0' and digest(native)==compatibility['native_sha256']
    installed = [Path(lgb.__file__).parent/name for name in ('basic.py','sklearn.py','engine.py')]
    save(OUT/'evidence/environment.json',{'lightgbm_version':lgb.__version__,'native_library':str(native),'native_sha256':digest(native),'installed_sources_sha256':{str(p):digest(p) for p in installed},'numpy_version':np.__version__,'source_reference_sha256':digest(OUT/'evidence/poisson_source_reference.json'),'source_reference_scope':'Moving-main upstream docs; installed4.7.0 DLL pinned separately','new_dependencies_installed':False,'real_model_fits':0})
    receipts = []
    for fold,(cutoff_text,end_text) in FOLDS.items():
        cutoff,end = (pd.Timestamp(t,tz='Asia/Seoul') for t in (cutoff_text,end_text))
        candidates = json.loads((DATA/fold/'features.json').read_text(encoding='utf-8'))['station']
        assert len(candidates)==len(set(candidates))==904 and not {'ts','grp','cf','energy','y','smp','k'} & set(candidates)
        train = pd.read_parquet(DATA/fold/'train.parquet')
        evaluation = pd.read_parquet(DATA/fold/'evaluation.parquet')
        assert list(train)==['ts','grp','cf',*candidates] and list(evaluation)==['ts','grp','capacity_kw',*candidates]
        assert train.ts.max()<=cutoff<evaluation.ts.min() and evaluation.ts.max()<=end
        assert not train.duplicated(['ts','grp']).any() and not evaluation.duplicated(['ts','grp']).any()
        names = column_mask(train,candidates)
        mask = json.loads((MONO/'data'/fold/'feature_mask.json').read_text(encoding='utf-8'))
        assert mask['candidate_columns']==candidates and mask['selected_columns']==names
        assert len(names)==(460 if fold=='primary' else 790)
        assert not np.isinf(train[names].to_numpy()).any() and not np.isinf(evaluation[names].to_numpy()).any()
        scale = normalizer(train.cosz.to_numpy())
        age = (cutoff-train.ts).dt.total_seconds().to_numpy()/86400
        decay,multiplier,weight = weights(scale,age)
        target = train.cf.to_numpy()/scale
        eval_scale = normalizer(evaluation.cosz.to_numpy())
        inverse = eval_scale*evaluation.capacity_kw.to_numpy()
        assert np.isfinite(target).all() and (target>=0).all() and target.sum()>0
        assert np.isfinite(inverse).all() and (inverse>0).all()
        transform = pd.read_parquet(MONO/'data'/fold/'training_transform.parquet')
        expected = train[['ts','grp']].assign(normalizer=scale,age_days=age,decay=decay,recency_multiplier=multiplier,sample_weight=weight,target_normalized=target)
        pd.testing.assert_frame_equal(transform,expected,check_exact=True)
        eval_transform = pd.read_parquet(MONO/'data'/fold/'evaluation_transform.parquet')
        expected_eval = evaluation[['ts','grp']].assign(normalizer=eval_scale,capacity_kw=evaluation.capacity_kw.to_numpy(),inverse_kwh=inverse)
        pd.testing.assert_frame_equal(eval_transform,expected_eval,check_exact=True)
        labels = pd.read_parquet(REFERENCE_DIR/fold/'predictions.parquet',columns=['ts','grp','y','smp','k','p']).rename(columns={'p':'p_reference'})
        assert abs(metrics(labels,'p_reference')['W_pct']-REFERENCE[fold])<1e-10
        coverage = pd.read_parquet(VERIFIED/'data'/fold/'coverage.parquet')
        inputs = pd.read_parquet(VERIFIED/'data'/fold/'application_inputs.parquet')
        assert list(inputs)==['ts','grp','wa_temp','extra_wa_snow','static_capacity']
        reference_inputs = pd.read_parquet(REFERENCE_DIR/fold/'predictions.parquet',columns=list(inputs))
        pd.testing.assert_frame_equal(inputs,reference_inputs,check_exact=True)
        pd.testing.assert_frame_equal(inputs[['ts','grp']],labels[['ts','grp']],check_exact=True)
        covered = inputs[['ts','grp']].merge(coverage,on=['ts','grp'],sort=False,validate='one_to_one')
        assert covered.night.notna().all() and labels.loc[covered.night,'p_reference'].eq(0).all()
        joined = covered.merge(evaluation[['ts','grp','wa_temp','extra_wa_snow']],on=['ts','grp'],how='left',sort=False,validate='one_to_one',indicator=True)
        assert joined._merge.eq('left_only').eq(joined.night).all() and int(joined._merge.eq('both').sum())==len(evaluation)
        pd.testing.assert_frame_equal(inputs[['wa_temp','extra_wa_snow']],joined[['wa_temp','extra_wa_snow']],check_exact=True)
        directory = OUT/'data'/fold
        directory.mkdir(parents=True)
        originals = [DATA/fold/name for name in ('train.parquet','evaluation.parquet')]
        originals += [MONO/'data'/fold/name for name in ('feature_mask.json','training_transform.parquet','evaluation_transform.parquet')]
        originals += [VERIFIED/'data'/fold/name for name in ('coverage.parquet','application_inputs.parquet')]
        for path in originals:
            shutil.copyfile(path,directory/path.name)
            assert digest(path)==digest(directory/path.name)
        labels.to_parquet(directory/'labels.parquet',index=False)
        receipts.append({'fold':fold,'train_rows':len(train),'evaluation_rows':len(evaluation),'candidate_features':904,'selected_features':len(names),'raw_inputs_byte_identical':True,'train_only_mask_exact':True,'mono_target_weight_inverse_exact':True,'target_min':float(target.min()),'target_max':float(target.max()),'target_sum':float(target.sum()),'sample_weight_sum':float(weight.sum()),'mean_recency_multiplier':float(multiplier.mean()),'weather_reference_W_pct':metrics(labels,'p_reference')['W_pct'],'weather_inputs_exact':True,'night_rows':int(covered.night.sum()),'train_max':str(train.ts.max()),'evaluation_min':str(evaluation.ts.min()),'native_train_nan_entries':int(train[names].isna().to_numpy().sum()),'native_evaluation_nan_entries':int(evaluation[names].isna().to_numpy().sum()),'source_sha256':{str(p.relative_to(ROOT)):digest(p) for p in originals},'real_model_fits':0})
    save(OUT/'evidence/read_receipts.json',receipts)
    manifest = {str(p.relative_to(OUT)):digest(p) for p in (OUT/'data').rglob('*') if p.is_file()}
    for name in ('environment.json','poisson_source_reference.json','read_receipts.json','selfchecks.json'):
        manifest['evidence/'+name] = digest(OUT/'evidence'/name)
    save(OUT/'prepared_manifest.json',manifest)
