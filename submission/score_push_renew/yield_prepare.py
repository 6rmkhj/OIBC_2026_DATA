# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: yield_run.py --prepare; never estimates real site quantiles.
"""Freeze one site-yield hypothesis and prepare only original bounded projections."""
import json
from pathlib import Path
import shutil
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- existing site/group cache contracts
from yield_common import ROOT,OUT,DATA,GROUP,SITE,REFERENCE_DIR,FOLDS,ARMS,REFERENCE,PARAMS,save,digest,now


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
    for path in [*Path(__file__).parent.glob('yield_*.py'),Path(__file__).with_name('temporal_common.py')]:
        shutil.copyfile(path,OUT/'sources/own'/path.name)
        own[path.name] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    renew = OUT.parent
    shutil.copyfile(renew/'calibration_wave/coefficients.json',OUT/'selected_coefficients.json')
    shutil.copyfile(renew/'calibration_wave/static_capacity.json',OUT/'static_capacity.json')
    provenance = ROOT/'analysis_outputs/award_run/provenance.json'
    cache = provenance.parent/'cache'/json.loads(provenance.read_text())['cache_key']
    inputs = [DATA/f/n for f in FOLDS for n in ('train.parquet','evaluation.parquet','features.json')]
    inputs += [SITE/f/n for f in FOLDS for n in ('train.parquet','selection.parquet')]
    inputs += [GROUP/'data'/f/'groups.parquet' for f in FOLDS]
    inputs += [REFERENCE_DIR/f/'predictions.parquet' for f in FOLDS]
    inputs += [renew/'recency_wave/data'/f/'night_coverage.parquet' for f in FOLDS]
    inputs += [renew/'calibration_wave'/n for n in ('coefficients.json','static_capacity.json','independent_check.json')]
    inputs += [provenance,cache/'feat_train.parquet',ROOT/'handover 2/01_participant_dataset/train/generation.parquet',ROOT/'handover 2/01_participant_dataset/sites.csv',ROOT/'analysis_outputs/autoresearch_20261103/cache/assignment.json',ROOT/'analysis_outputs/autoresearch_20261103/cache/features.json',GROUP/'independent_data_check.json']
    protected = set(inputs)|set(sources)
    for folder in (ROOT/'submission/score_push_candidate',ROOT/'submission/renew_candidate_20261105',renew/'final',renew/'recency_wave',renew/'calibration_wave',renew/'group_wave',renew/'total_wave',renew/'weight_wave'):
        protected.update(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    save(OUT/'protocol.json',{'created_utc':now(),'arms':ARMS,'folds':FOLDS,'seeds':[0,1,2],'seed0_random_state':None,'site_coefficient_fits':2,'generation_model_fit_budget':6,'parameters':PARAMS,'reference_scores':REFERENCE,'hypothesis':'Train-only heterogeneous site yield normalization as active-site mix grows. No gain feature added.','clear_support':'finite cf>=0, finite cosz>.5, finite wa_cloud and wb_cloud each>=0 and<20. Support rows>=100 AND distinct right-closed(ts-1hour)calendar dates>=20.','physical_haurwitz':'UNFLOORED H(c)=1.098*max(c,0)*exp(-.059/max(c,0)), H(c<=0)=0. Scale by gain BEFORE floor. Neutralgain1 exactly matches original normalizer.','gain_fit':'Once per fold, shared all seeds. Global q90=quantile(cf/H(cosz),.9,method=linear) over ALL valid clear TRAIN rows; must finitepositive. Per-site q90 same. Unsupported or q90<=0/nonfinite=>gain1. Otherwise relative=site/global; shrink=n/(n+200); gain=clip(1+shrink*(relative-1),.5,1.5). Unknownsites1. All253 records retained. No grid.','group_gain':'SUM(active daylightsite capacity*sitegain)/SUM(active daylightsite capacity), fixed assignment. Verify train/eval capacity sums against original group capacities with rtol1e-12,atol1e-8 (<=253 float64 capacity additions).','normalizer':'max(.05,UNFLOORED H(groupcosz)*groupgain), floor ONCE after gain','target':'Existing groupCF/newnormalizer unchanged original CF values','weight':'newnormalizer * mean-normalized exp2(-age_days/180), fixed cutoff; NO monetary weights','features':'Original904station candidates and TRAIN-only constantmask; no gain/target/cost feature','inverse':'newnormalizer_eval*groupcapacity','inference':'3SIGNED seedkWh mean, clip0..STATICcapacity then frozen temperature_then_snow calibration ONCE','selection':'One PRIMARY-only alpha vs current calibrated reference, unchanged recent. BOTHstrictW improvement andalpha>=.02; one arm; else retain reference. No recalibration.','historical_exposure':'Historically exposed development, no independent holdout claim. No confirmation/test/fullrefit/export.','prefit_barrier':'Prepare only original projected data/capacity checks and synthetic fixtures. No real quantiles/coefficient fits or trees before explicit root release.','coefficient_sha256':digest(OUT/'selected_coefficients.json'),'static_capacity_sha256':digest(OUT/'static_capacity.json'),'resources':{'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_fits':1},'snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)}})


def prepare() -> None:
    from profile_features import column_mask
    from final_metrics import metrics
    sites = pd.read_csv(ROOT/'handover 2/01_participant_dataset/sites.csv',usecols=['site_id','capacity_kw'])
    assignment = json.loads((ROOT/'analysis_outputs/autoresearch_20261103/cache/assignment.json').read_text())
    assert len(sites)==253 and not sites.site_id.duplicated().any() and set(sites.site_id)==set(assignment)
    sites['grp'] = sites.site_id.map(assignment)
    (OUT/'data').mkdir(exist_ok=True)
    sites.to_parquet(OUT/'data/sites.parquet',index=False)
    receipts = []
    for fold,(cutoff_text,end_text) in FOLDS.items():
        cutoff,end = (pd.Timestamp(t,tz='Asia/Seoul') for t in (cutoff_text,end_text))
        candidates = json.loads((DATA/fold/'features.json').read_text())['station']
        assert len(candidates)==904 and not {'ts','grp','cf','y','energy','smp','k','gain','group_gain'} & set(candidates)
        train = pd.read_parquet(DATA/fold/'train.parquet',columns=['ts','grp','cf',*candidates],filters=[('ts','<=',cutoff)])
        evaluation = pd.read_parquet(DATA/fold/'evaluation.parquet',columns=['ts','grp','capacity_kw',*candidates],filters=[('ts','>',cutoff),('ts','<=',end)])
        train_cap = pd.read_parquet(GROUP/'data'/fold/'groups.parquet',columns=['ts','grp','day_capacity'],filters=[('ts','<=',cutoff)]).rename(columns={'day_capacity':'capacity_kw'})
        train_site_columns = ['ts','site_id','cf','cosz','wa_cloud','wb_cloud','capacity_kw']
        site_train = pd.read_parquet(SITE/fold/'train.parquet',columns=train_site_columns,filters=[('ts','<=',cutoff),('night','==',False)])
        site_eval = pd.read_parquet(SITE/fold/'selection.parquet',columns=['ts','site_id','capacity_kw'],filters=[('ts','>',cutoff),('ts','<=',end),('night','==',False)])
        assert train.ts.max()<=cutoff<evaluation.ts.min() and site_train.ts.max()<=cutoff<site_eval.ts.min()
        assert evaluation.ts.max()<=end and site_eval.ts.max()<=end
        errors = {}
        for name,panel,group_keys,cap in [('train',site_train,train[['ts','grp']],train_cap),('evaluation',site_eval,evaluation[['ts','grp']],evaluation[['ts','grp','capacity_kw']])]:
            assert not panel.duplicated(['ts','site_id']).any() and not group_keys.duplicated(['ts','grp']).any()
            assert np.isfinite(panel.capacity_kw).all() and panel.capacity_kw.gt(0).all()
            mapped = panel[['ts','site_id','capacity_kw']].copy()
            mapped['grp'] = mapped.site_id.astype(str).map(assignment)
            assert mapped.grp.notna().all()
            summed = mapped.groupby(['ts','grp'],as_index=False,observed=True).capacity_kw.sum()
            joined = group_keys.merge(summed,on=['ts','grp'],how='outer',validate='one_to_one',indicator=True)
            assert joined._merge.eq('both').all()
            aligned = summed.merge(cap,on=['ts','grp'],how='outer',validate='one_to_one',indicator=True,suffixes=('_sites','_original'))
            assert aligned._merge.eq('both').all()
            np.testing.assert_allclose(aligned.capacity_kw_sites,aligned.capacity_kw_original,rtol=1e-12,atol=1e-8)
            errors[name] = float(np.max(np.abs(aligned.capacity_kw_sites-aligned.capacity_kw_original)))
        labels = pd.read_parquet(REFERENCE_DIR/fold/'predictions.parquet',columns=['ts','grp','y','smp','k','p']).rename(columns={'p':'p_reference'})
        assert abs(metrics(labels,'p_reference')['W_pct']-REFERENCE[fold])<1e-10
        coverage = pd.read_parquet(OUT.parent/'recency_wave/data'/fold/'night_coverage.parquet')
        keys = labels[['ts','grp']].merge(coverage,on=['ts','grp'],how='outer',validate='one_to_one',indicator=True)
        assert keys._merge.eq('both').all()
        pd.testing.assert_frame_equal(evaluation[['ts','grp']].sort_values(['ts','grp']).reset_index(drop=True),keys.loc[~keys.night,['ts','grp']].sort_values(['ts','grp']).reset_index(drop=True))
        directory = OUT/'data'/fold
        directory.mkdir(parents=True,exist_ok=True)
        for name,frame in [('train',train),('evaluation',evaluation),('site_train',site_train),('site_evaluation',site_eval),('train_capacity',train_cap),('evaluation_capacity',evaluation[['ts','grp','capacity_kw']]),('labels',labels),('coverage',coverage)]:
            frame.to_parquet(directory/f'{name}.parquet',index=False)
        names = column_mask(train,candidates)
        save(directory/'features.json',{'cutoff':str(cutoff),'end':str(end),'candidates':candidates,'features':names,'train_rows':len(train),'evaluation_rows':len(evaluation),'mask_source':'TRAIN ONLY'})
        receipts.append({'fold':fold,'train_rows':len(train),'evaluation_rows':len(evaluation),'site_train_rows':len(site_train),'site_eval_rows':len(site_eval),'max_site_target_ts':str(site_train.ts.max()),'target_cutoff':str(cutoff),'site_train_projection':train_site_columns,'site_eval_projection':['ts','site_id','capacity_kw'],'site_eval_filters':[('ts','>',str(cutoff)),('ts','<=',str(end)),('night','==',False)],'capacity_max_errors':errors,'capacity_tolerance':{'rtol':1e-12,'atol':1e-8,'justification':'At most253 float64 additions of decimal capacities; tolerance below1e-7kW, no row rounding or dropping.'},'exact_daylight_keys':True,'real_quantile_fits':0,'no_evaluation_site_targets':True})
    save(OUT/'evidence/read_receipts.json',receipts)
    save(OUT/'prepared_manifest.json',{str(p.relative_to(OUT)):digest(p) for p in (OUT/'data').rglob('*') if p.is_file()})
