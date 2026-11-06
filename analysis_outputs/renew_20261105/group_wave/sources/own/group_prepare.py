# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/group_run.py --prepare
"""Freeze the protocol and reconstruct bounded, complete raw generation groups."""
from pathlib import Path
import json
import shutil
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen site/metric contracts
from group_common import ROOT, OUT, SITE, REFERENCE_DIR, FOLDS, ARMS, PARAMS, REFERENCE, save, digest, now


def freeze() -> None:
    if (OUT/'protocol.json').exists():
        return
    (OUT/'sources/own').mkdir(parents=True)
    (OUT/'evidence').mkdir()
    snapshots = {}
    for folder in ('autoresearch','score_push','score_push_gpu'):
        for path in (ROOT/'submission'/folder).glob('*.py'):
            shutil.copyfile(path,OUT/'sources'/path.name)
            snapshots[path.stem] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    own = {}
    for path in Path(__file__).parent.glob('group_*.py'):
        shutil.copyfile(path,OUT/'sources/own'/path.name)
        own[path.name] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    for name in ('temporal_common.py',):
        path = Path(__file__).with_name(name)
        shutil.copyfile(path,OUT/'sources/own'/name)
        own[name] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    provenance = ROOT/'analysis_outputs/award_run/provenance.json'
    original = provenance.parent/'cache'/json.loads(provenance.read_text())['cache_key']/'feat_train.parquet'
    assignment = ROOT/'analysis_outputs/autoresearch_20261103/cache/assignment.json'
    raw = ROOT/'handover 2/01_participant_dataset/train/generation.parquet'
    smp = ROOT/'handover 2/01_participant_dataset/train/smp.csv'
    metadata = ROOT/'handover 2/01_participant_dataset/sites.csv'
    inputs = [provenance,original,assignment,raw,smp,metadata,assignment.with_name("features.json")]
    inputs += [SITE/f/name for f in FOLDS for name in ('train.parquet','selection.parquet')]
    inputs += [REFERENCE_DIR/f/'predictions.parquet' for f in FOLDS]
    protected = set(inputs)|{ROOT/r['original'] for r in snapshots.values()}
    for folder in ('submission/score_push_candidate','submission/autoresearch_candidate','analysis_outputs/score_push_20261104/final'):
        protected.update(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    save(OUT/'protocol.json',{'created_utc':now(),'folds':FOLDS,'arms':ARMS,'seeds':[0,1,2],'model_fit_budget':18,'boosting_rounds':1000,'parameters':PARAMS,'reference_scores':REFERENCE,'original':str(original.relative_to(ROOT)),'raw':str(raw.relative_to(ROOT)),'smp':str(smp.relative_to(ROOT)),'metadata':str(metadata.relative_to(ROOT)),'assignment':str(assignment.relative_to(ROOT)),'target':'Full original raw float64 generation sum incl night / actual daylight capacity. Verify raw float32 projection equals cached energy; never derive target from clipped cf. Cache cf retained only as site regularizer target.','math':'q=cap/Cg; R=sum(q*f)-tg; wg=Cg*SMP*k; ai=wg*q; divide wg and ai by common mean(ai) over all daylight train rows. Group loss=sum(wg*(sqrt(R^2+delta^2)-delta))+lambda/2*sum(ai*(f-cf)^2). Gradient=ai*(R/sqrt(R^2+delta^2)+lambda*(f-cf)); global diagonal majorizer ai*(1/delta+lambda), NOT exact Hessian. Site control substitutes individual residual. Zero SMP retains zero gradient/majorizer.','dataset':'Original site FEATURES with fixed metadata-only categories; no weights or init_score; zero initial predictions. Full group dataset each iteration, no row sampling; no direct groupID, epoch, price, target features. Float64 reductions.','inference':'Predict raw_score=True on daylight site rows; night zero. Average signed CF across all 3 seeds, multiply capacity, sum full timestamp/group, only then clip group >=0.','selection':'One alpha fitted PRIMARY only; unchanged recent. Both W improve and alpha>=.02; minimum equal-fold relative W including site_control; otherwise retain decay180 reference.','historical_exposure':'All development historically exposed; no independent holdout claim. No confirmation/test labels, full-history refit or export.','diagnostics':'Training weighted group L1 and declared smooth objective at zero/every100/final, never adaptive. Genuine iteration<1000 halts for root review.','resources':{'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_fits':1},'snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)}})


def prepare() -> None:
    from site_features import FEATURES, CATEGORIES
    from final_metrics import metrics
    protocol = json.loads((OUT/'protocol.json').read_text())
    assignment = json.loads((ROOT/protocol['assignment']).read_text())
    sites = pd.read_csv(ROOT/protocol['metadata'],usecols=[*CATEGORIES,'capacity_kw'])
    prices = pd.read_csv(ROOT/protocol['smp'])
    prices['ts'] = pd.to_datetime(prices.ts).dt.tz_convert('Asia/Seoul')
    assert not prices.ts.duplicated().any()
    assert not {'ts','energy','cf','y','smp','k','grp','group_id','night'} & set(FEATURES)
    receipts = []
    for fold,(cutoff_text,end_text,expected_rows) in FOLDS.items():
        cutoff,end = (pd.Timestamp(t,tz='Asia/Seoul') for t in (cutoff_text,end_text))
        train = pd.read_parquet(SITE/fold/'train.parquet')
        evaluation = pd.read_parquet(SITE/fold/'selection.parquet')
        assert len(train)==expected_rows and train.ts.max()<=cutoff<evaluation.ts.min() and evaluation.ts.max()<=end
        assert not train.night.any() and not train.duplicated(['ts','site_id']).any()
        assert not evaluation.duplicated(['ts','site_id']).any() and not {'cf','y','energy'} & set(evaluation)
        categories = {}
        for column in CATEGORIES:
            expected = sorted(sites[column].dropna().unique())
            assert list(train[column].cat.categories)==list(evaluation[column].cat.categories)==expected
            categories[column] = expected
        for frame in (train,evaluation):
            assert frame[list(CATEGORIES)].notna().all().all()
            frame['grp'] = frame.site_id.astype(str).map(assignment)
            assert frame.grp.notna().all()
            capacities = frame.site_id.astype(str).map(sites.set_index('site_id').capacity_kw)
            np.testing.assert_array_equal(frame.capacity_kw,capacities)
        raw = pd.read_parquet(ROOT/protocol['raw'],columns=['ts','site_id','energy'],filters=[('ts','<=',cutoff)])
        observed = pd.read_parquet(ROOT/protocol['original'],columns=['ts','site_id','energy','night','capacity_kw'],filters=[('ts','<=',cutoff)])
        assert raw.ts.max()<=cutoff and observed.ts.max()<=cutoff and not raw.duplicated(['ts','site_id']).any()
        raw['ts'] = raw.ts.astype(observed.ts.dtype)
        raw = raw.sort_values(['ts','site_id']).reset_index(drop=True)
        observed = observed.sort_values(['ts','site_id']).reset_index(drop=True)
        pd.testing.assert_frame_equal(raw[['ts','site_id']],observed[['ts','site_id']])
        assert np.isfinite(raw.energy).all()
        np.testing.assert_array_equal(raw.energy.to_numpy().astype(np.float32),observed.energy)
        raw['night'] = observed.night.to_numpy()
        raw['grp'] = raw.site_id.map(assignment)
        assert raw.grp.notna().all()
        daylight = observed.loc[~observed.night,['ts','site_id','capacity_kw']].copy()
        cached = train[['ts','site_id','capacity_kw']].copy()
        cached['site_id'] = cached.site_id.astype(str)
        pd.testing.assert_frame_equal(cached.sort_values(['ts','site_id']).reset_index(drop=True),daylight.reset_index(drop=True))
        full = raw.groupby(['ts','grp'],as_index=False).agg(full_energy=('energy','sum'),observed_sites=('site_id','size'))
        night = raw.loc[raw.night].groupby(['ts','grp'],as_index=False).agg(night_energy=('energy','sum'))
        full = full.merge(night,on=['ts','grp'],how='left',validate='one_to_one').fillna({'night_energy':0.})
        capacity = train.groupby(['ts','grp'],as_index=False,observed=True).agg(day_capacity=('capacity_kw','sum'),day_sites=('site_id','size'))
        full = full.merge(capacity,on=['ts','grp'],how='left',validate='one_to_one').merge(prices.loc[prices.ts<=cutoff],on='ts',how='left',validate='many_to_one')
        full['k'] = np.where(full.ts.dt.hour.between(11,15),3.,1.)
        assert np.isfinite(full.smp).all() and (full.smp>=0).all()
        groups = full.loc[full.day_capacity.notna()].sort_values(['ts','grp']).reset_index(drop=True).copy()
        groups['group_id'] = np.arange(len(groups))
        groups['target'] = groups.full_energy/groups.day_capacity
        groups['group_weight_raw'] = groups.day_capacity*groups.smp*groups.k
        train['row_id'] = np.arange(len(train))
        aligned = train[['row_id','ts','site_id','grp','capacity_kw','cf']].merge(groups[['ts','grp','group_id','day_capacity','smp','k']],on=['ts','grp'],how='left',validate='many_to_one',sort=False)
        assert aligned.row_id.eq(np.arange(len(train))).all() and aligned.group_id.notna().all()
        aligned['share'] = aligned.capacity_kw/aligned.day_capacity
        aligned['weight_raw'] = aligned.capacity_kw*aligned.smp*aligned.k
        normalization = float(aligned.weight_raw.mean())
        assert np.isfinite(normalization) and normalization>0
        aligned['weight'] = aligned.weight_raw/normalization
        groups['group_weight'] = groups.group_weight_raw/normalization
        np.testing.assert_allclose(aligned.groupby('group_id').share.sum(),1.,rtol=1e-12)
        np.testing.assert_allclose(aligned.groupby('group_id').capacity_kw.sum(),groups.day_capacity,rtol=1e-12)
        assert train.cf.between(0,1.2).all() and np.isfinite(train.cf).all()
        labels = pd.read_parquet(REFERENCE_DIR/fold/'predictions.parquet',columns=['ts','grp','y','smp','k','p']).rename(columns={'p':'p_reference'})
        assert abs(metrics(labels,'p_reference')['W_pct']-REFERENCE[fold])<1e-10
        coverage = evaluation.groupby(['ts','grp'],as_index=False,observed=True).agg(night=('night','all'),sites=('site_id','size'))
        coverage = labels[['ts','grp']].merge(coverage,on=['ts','grp'],how='outer',validate='one_to_one',indicator=True)
        assert coverage._merge.eq('both').all()
        directory = OUT/'data'/fold
        directory.mkdir(parents=True,exist_ok=True)
        train.to_parquet(directory/'train.parquet',index=False)
        evaluation.to_parquet(directory/'evaluation.parquet',index=False)
        aligned.to_parquet(directory/'rows.parquet',index=False)
        groups.to_parquet(directory/'groups.parquet',index=False)
        full.to_parquet(directory/'complete_training_groups.parquet',index=False)
        labels.to_parquet(directory/'labels.parquet',index=False)
        coverage.drop(columns='_merge').to_parquet(directory/'coverage.parquet',index=False)
        save(directory/'features.json',{'features':FEATURES,'categories':categories,'normalization':normalization,'row_order':'original cached train order; row_id=0..N-1','train_rows':len(train),'groups':len(groups),'evaluation_rows':len(evaluation),'evaluation_day_rows':int((~evaluation.night).sum())})
        receipts.append({'fold':fold,'cutoff':str(cutoff),'raw_columns':['ts','site_id','energy'],'raw_filter':['ts','<=',str(cutoff)],'cache_columns':['ts','site_id','energy','night','capacity_kw'],'raw_rows':len(raw),'max_ts':str(raw.ts.max()),'keys_exact':True,'raw_float32_projection_exact':True,'target_source':'original raw float64','night_energy_sum':float(raw.loc[raw.night,'energy'].sum()),'training_allnight_groups':int(full.day_capacity.isna().sum()),'day_groups_with_night_energy':int((groups.night_energy!=0).sum()),'normalization':normalization,'zero_price_rows':int(aligned.weight.eq(0).sum()),'categories_metadata_only':True,'no_future_target_read':True})
        print('PREPARED',fold,len(train),len(groups),flush=True)
    save(OUT/'evidence/read_receipts.json',receipts)
    save(OUT/'prepared_manifest.json',{str(p.relative_to(OUT)):digest(p) for p in (OUT/'data').rglob('*') if p.is_file()})
