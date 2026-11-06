# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: weight_run.py --prepare.
"""Freeze the distinct normalized-station-decay weighting test and exact joins."""
import json
from pathlib import Path
import shutil
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- original temporal feature/label contract
from weight_common import ROOT,OUT,DATA,GROUP,REFERENCE_DIR,FOLDS,ARMS,REFERENCE,PARAMS,save,digest,now,decay_multiplier
from weight_math import normalized_weights


def freeze() -> None:
    if (OUT/'protocol.json').exists():
        return
    (OUT/'sources/own').mkdir(parents=True)
    (OUT/'evidence').mkdir(exist_ok=True)
    snapshots = {}
    sources = [p for folder in ('autoresearch','score_push','score_push_gpu') for p in (ROOT/'submission'/folder).glob('*.py')]
    sources.append(Path(__file__).with_name('cal_math.py'))
    for path in sources:
        shutil.copyfile(path,OUT/'sources'/path.name)
        snapshots[path.stem] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    own = {}
    for path in [*Path(__file__).parent.glob('weight_*.py'),Path(__file__).with_name('temporal_common.py')]:
        shutil.copyfile(path,OUT/'sources/own'/path.name)
        own[path.name] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    renew = OUT.parent
    shutil.copyfile(renew/'calibration_wave/coefficients.json',OUT/'selected_coefficients.json')
    shutil.copyfile(renew/'calibration_wave/static_capacity.json',OUT/'static_capacity.json')
    inputs = [DATA/f/n for f in FOLDS for n in ('train.parquet','evaluation.parquet','features.json')]
    inputs += [GROUP/'data'/f/'groups.parquet' for f in FOLDS]
    inputs += [REFERENCE_DIR/f/'predictions.parquet' for f in FOLDS]
    inputs += [renew/'recency_wave/data'/f/'night_coverage.parquet' for f in FOLDS]
    inputs += [renew/'calibration_wave'/n for n in ('coefficients.json','static_capacity.json','independent_check.json')]
    inputs += [GROUP/'independent_data_check.json',ROOT/'analysis_outputs/autoresearch_20261103/results.tsv',ROOT/'analysis_outputs/autoresearch_20261103/cache/features.json']
    protected = set(inputs)|set(sources)
    for folder in (ROOT/'submission/score_push_candidate',ROOT/'submission/renew_candidate_20261105',renew/'final',renew/'recency_wave',renew/'calibration_wave',renew/'group_wave',renew/'total_wave'):
        protected.update(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    save(OUT/'protocol.json',{'created_utc':now(),'arms':ARMS,'folds':FOLDS,'seeds':[0,1,2],'seed0_random_state':None,'model_fit_budget':12,'parameters':PARAMS,'reference_scores':REFERENCE,'features':'Existing station904 candidates, TRAIN-only constant mask. Never monetary weights/targets as features. No evaluation cost reads in fitting.','join':'GPU train exact two-way ts/grp keys and original row order joined ONLY to verified groups ts/grp/day_capacity/smp/k. No target drop, zero monetary rows retained.','target':'Existing cf/normalizer unchanged','base_weight':'normalizer * exp2(-age_days/180)/mean(TRAIN decay), fixed fold cutoff','modifiers':{'peak_k':'k','scored':'day_capacity*smp*k'},'new_weight':'base_weight*modifier*sum(base_weight)/sum(base_weight*modifier), same total training weight, train-only normalization','inference':'All3 signed seed kWh averaged, clip to0..STATIC composition capacity, apply frozen temperature_then_snow coefficients and fixed shrink.5 ONCE. No coefficient refit.','selection':'One alpha fitted PRIMARY only vs complete current calibrated reference; unchanged recent; strictW improvement BOTH and alpha>=.02; minimum mean relativeW across2arms else retain reference. No grid or extra thresholds.','prior_weighting':'Earlier raw-CF scored/capacity baseline rows in autoresearch results.tsv were discarded. This is distinctly normalized target + station features + temporal180, not the first weighting test.','historical_exposure':'All development historically exposed; no independent holdout claim. No confirmation/test/fullrefit/export.','coefficient_sha256':digest(OUT/'selected_coefficients.json'),'static_capacity_sha256':digest(OUT/'static_capacity.json'),'resources':{'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_fits':1},'snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)}})


def prepare() -> None:
    from site_features import normalizer
    from profile_features import column_mask
    from final_metrics import metrics
    receipts = []
    for fold,(cutoff_text,end_text) in FOLDS.items():
        cutoff,end = (pd.Timestamp(t,tz='Asia/Seoul') for t in (cutoff_text,end_text))
        spec = json.loads((DATA/fold/'features.json').read_text())
        candidates = spec['station']
        assert len(candidates)==904 and not {'ts','grp','cf','y','energy','smp','k','day_capacity'} & set(candidates)
        train = pd.read_parquet(DATA/fold/'train.parquet',columns=['ts','grp','cf',*candidates],filters=[('ts','<=',cutoff)])
        evaluation = pd.read_parquet(DATA/fold/'evaluation.parquet',columns=['ts','grp','capacity_kw',*candidates],filters=[('ts','>',cutoff),('ts','<=',end)])
        monetary = pd.read_parquet(GROUP/'data'/fold/'groups.parquet',columns=['ts','grp','day_capacity','smp','k'],filters=[('ts','<=',cutoff)])
        keys = train[['ts','grp']].merge(monetary,on=['ts','grp'],how='outer',validate='one_to_one',indicator=True)
        assert keys._merge.eq('both').all()
        context = train[['ts','grp']].assign(row_id=np.arange(len(train))).merge(monetary,on=['ts','grp'],how='left',sort=False,validate='one_to_one')
        pd.testing.assert_frame_equal(context[['ts','grp']],train[['ts','grp']])
        np.testing.assert_array_equal(context.row_id,np.arange(len(train)))
        assert train.ts.max()<=cutoff<evaluation.ts.min() and evaluation.ts.max()<=end
        assert not train.duplicated(['ts','grp']).any() and not evaluation.duplicated(['ts','grp']).any()
        assert np.isfinite(context[['day_capacity','smp','k']].to_numpy()).all() and context.day_capacity.gt(0).all() and context.smp.ge(0).all()
        np.testing.assert_array_equal(context.k,np.where(context.ts.dt.hour.between(11,15),3.,1.))
        context['normalizer'] = normalizer(train.cosz.to_numpy())
        context['age_days'] = (cutoff-train.ts).dt.total_seconds()/86400
        context['decay'] = decay_multiplier(context.age_days.to_numpy(),180)
        context['base_weight'] = context.normalizer*context.decay
        directory = OUT/'data'/fold
        directory.mkdir(parents=True,exist_ok=True)
        train.to_parquet(directory/'train.parquet',index=False)
        evaluation.to_parquet(directory/'evaluation.parquet',index=False)
        context.to_parquet(directory/'train_context.parquet',index=False)
        names = column_mask(train,candidates)
        save(directory/'features.json',{'cutoff':str(cutoff),'end':str(end),'candidates':candidates,'features':names,'train_rows':len(train),'evaluation_rows':len(evaluation),'mask_source':'TRAIN ONLY'})
        modifiers = {'peak_k':context.k.to_numpy(),'scored':(context.day_capacity*context.smp*context.k).to_numpy()}
        for arm,modifier in modifiers.items():
            weights = context[['row_id','ts','grp','base_weight']].copy()
            weights['modifier'] = modifier
            weights['normalization'] = context.base_weight.sum()/np.sum(context.base_weight.to_numpy()*modifier,dtype=np.float64)
            weights['sample_weight'] = normalized_weights(context.base_weight.to_numpy(),modifier)
            target_dir = OUT/'data'/arm/fold
            target_dir.mkdir(parents=True,exist_ok=True)
            weights.to_parquet(target_dir/'weights.parquet',index=False)
        assert int((modifiers['scored']==0).sum())=={'primary':0,'recent':6}[fold]
        labels = pd.read_parquet(REFERENCE_DIR/fold/'predictions.parquet',columns=['ts','grp','y','smp','k','p']).rename(columns={'p':'p_reference'})
        assert abs(metrics(labels,'p_reference')['W_pct']-REFERENCE[fold])<1e-10
        coverage = pd.read_parquet(OUT.parent/'recency_wave/data'/fold/'night_coverage.parquet')
        check = labels[['ts','grp']].merge(coverage,on=['ts','grp'],how='outer',validate='one_to_one',indicator=True)
        assert check._merge.eq('both').all()
        pd.testing.assert_frame_equal(evaluation[['ts','grp']],check.loc[~check.night,['ts','grp']].reset_index(drop=True))
        labels.to_parquet(directory/'labels.parquet',index=False)
        coverage.to_parquet(directory/'coverage.parquet',index=False)
        receipts.append({'fold':fold,'cutoff':str(cutoff),'max_target_ts':str(train.ts.max()),'train_rows':len(train),'zero_monetary_rows':int((modifiers['scored']==0).sum()),'source_group_projection':['ts','grp','day_capacity','smp','k'],'exact_two_way_keys':True,'row_order_preserved':True,'same_total_weight':True,'evaluation_columns':list(evaluation),'no_evaluation_cost_read':True,'feature_count':len(names)})
    save(OUT/'evidence/read_receipts.json',receipts)
    save(OUT/'prepared_manifest.json',{str(p.relative_to(OUT)):digest(p) for p in (OUT/'data').rglob('*') if p.is_file()})
