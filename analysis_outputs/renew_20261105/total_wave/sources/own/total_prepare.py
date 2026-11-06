# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "threadpoolctl"]
# ///
# How to run: python submission/score_push_renew/total_run.py --prepare.
"""Immutable preregistration and bounded full-portfolio preparation."""
import json
from pathlib import Path
import shutil
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- preserve existing numeric feature contract
from total_common import ROOT,OUT,DATA,GROUP,REFERENCE_DIR,FOLDS,ARMS,REFERENCE,PARAMS,save,digest,now,decay_multiplier
from total_math import summarize,full_targets,allocate


def freeze() -> None:
    if (OUT/'protocol.json').exists():
        return
    (OUT/'sources/own').mkdir(parents=True)
    (OUT/'evidence').mkdir(exist_ok=True)
    snapshots = {}
    for folder in ('autoresearch','score_push','score_push_gpu'):
        for path in (ROOT/'submission'/folder).glob('*.py'):
            shutil.copyfile(path,OUT/'sources'/path.name)
            snapshots[path.stem] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    own = {}
    for path in [*Path(__file__).parent.glob('total_*.py'),Path(__file__).with_name('temporal_common.py')]:
        shutil.copyfile(path,OUT/'sources/own'/path.name)
        own[path.name] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    provenance = ROOT/'analysis_outputs/award_run/provenance.json'
    inputs = [provenance,ROOT/'handover 2/01_participant_dataset/train/generation.parquet',ROOT/'analysis_outputs/autoresearch_20261103/cache/assignment.json',ROOT/'analysis_outputs/autoresearch_20261103/cache/features.json',GROUP/'independent_data_check.json',GROUP/'protocol.json',GROUP/'prepared_manifest.json']
    inputs += [DATA/f/name for f in FOLDS for name in ('train.parquet','evaluation.parquet','features.json')]
    inputs += [GROUP/'data'/f/name for f in FOLDS for name in ('groups.parquet','complete_training_groups.parquet')]
    inputs += [REFERENCE_DIR/f/'predictions.parquet' for f in FOLDS]
    protected = set(inputs)|{ROOT/r['original'] for r in snapshots.values()}
    for folder in ('submission/score_push_candidate','submission/autoresearch_candidate','analysis_outputs/score_push_20261104/final','analysis_outputs/renew_20261105/group_wave'):
        protected.update(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    save(OUT/'protocol.json',{'created_utc':now(),'arms':ARMS,'folds':FOLDS,'seeds':[0,1,2],'seed0_random_state':None,'model_fit_budget':12,'parameters':PARAMS,'reference_scores':REFERENCE,'feature_summary':'One row per timestamp. Each numeric feature except grp_code is sum(cap*x for finite x)/sum(cap for finite x); allmissing remains NaN; infinities rejected. Weighted SUMMARY of existing group features, not exact raw-station reaggregation. Same semantics for station contribution/share columns. Rich99/station903 before TRAIN-only columnmask.','capacity_source':'GPU train matrix lacks capacity. Join ONLY ts/grp/day_capacity from verified group_wave groups.parquet by exact two-way keys and preserve input order; rename to capacity_kw. Evaluation uses existing GPU matrix capacity_kw.','target':'Sum complete_training_groups full_energy original raw float64 across ALL groups per timestamp incl night-only contributions. Join only daylight training timestamps <= fixed cutoff. Fulltotal_cf=energy/sum daylight capacity; target=cf/Haurwitz normalizer; no old clipped GPU cf read.','weights':'normalizer * (2**(-age_days/180)/mean(training decay)); no SMP weights.','inference':'Each seed raw_score=True * evaluation normalizer * totaldaylight capacity; mean signed kWh across3seeds THEN totalclip>=0.','allocation':'Reference p share if reference total>0; otherwise daylight group capacity share if daylight capacity>0; otherwise total/new exactly0. Complete reference group keys unchanged, allnight groups0. No labels in allocation.','selection':'ONE alpha PRIMARY only, unchanged recent; both W strictly improve and alpha>=.02; select minimum equal-fold relative W across2arms otherwise retain decay180.','historical_exposure':'Historically exposed development; no independent holdout claim. No composition change, confirmation/test, full refit, export or upload.','resources':{'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_fits':1},'snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)}})


def prepare() -> None:
    from profile_features import column_mask
    from site_features import normalizer
    from final_metrics import metrics
    receipts = []
    for fold,(cutoff_text,end_text) in FOLDS.items():
        cutoff,end = (pd.Timestamp(t,tz='Asia/Seoul') for t in (cutoff_text,end_text))
        spec = json.loads((DATA/fold/'features.json').read_text())
        candidates = {arm:[n for n in spec[key] if n!='grp_code'] for arm,key in ARMS.items()}
        assert [len(candidates[a]) for a in ARMS]==[99,903]
        names = list(dict.fromkeys(n for names in candidates.values() for n in names))
        assert not {'cf','y','energy','smp','k','grp','grp_code','ts','capacity_kw'} & set(names)
        train = pd.read_parquet(DATA/fold/'train.parquet',columns=['ts','grp',*names],filters=[('ts','<=',cutoff)])
        evaluation = pd.read_parquet(DATA/fold/'evaluation.parquet',columns=['ts','grp','capacity_kw',*names],filters=[('ts','>',cutoff),('ts','<=',end)])
        capacity = pd.read_parquet(GROUP/'data'/fold/'groups.parquet',columns=['ts','grp','day_capacity'],filters=[('ts','<=',cutoff)]).rename(columns={'day_capacity':'capacity_kw'})
        keys = train[['ts','grp']].merge(capacity[['ts','grp']],on=['ts','grp'],how='outer',validate='one_to_one',indicator=True)
        assert keys._merge.eq('both').all()
        original_keys = train[['ts','grp']].copy()
        train = train.merge(capacity,on=['ts','grp'],how='left',sort=False,validate='one_to_one')
        pd.testing.assert_frame_equal(train[['ts','grp']],original_keys)
        assert train.ts.max()<=cutoff<evaluation.ts.min() and evaluation.ts.max()<=end
        full = pd.read_parquet(GROUP/'data'/fold/'complete_training_groups.parquet',columns=['ts','grp','full_energy'],filters=[('ts','<=',cutoff)])
        assert full.ts.max()<=cutoff
        total_train,total_eval = summarize(train,names),summarize(evaluation,names)
        targets = full_targets(full)
        target_rows = total_train[['ts','capacity_kw']].merge(targets,on='ts',how='left',validate='one_to_one')
        assert target_rows.full_total_energy.notna().all()
        target_rows['cf'] = target_rows.full_total_energy/target_rows.capacity_kw
        target_rows['normalizer'] = normalizer(total_train.cosz.to_numpy())
        target_rows['age_days'] = (cutoff-target_rows.ts).dt.total_seconds()/86400
        target_rows['decay'] = decay_multiplier(target_rows.age_days.to_numpy(),180)
        target_rows['sample_weight'] = target_rows.normalizer*target_rows.decay
        target_rows['target'] = target_rows.cf/target_rows.normalizer
        assert np.isfinite(target_rows.iloc[:,1:].to_numpy()).all() and target_rows.sample_weight.gt(0).all()
        assert abs(target_rows.decay.mean()-1)<1e-12
        features = {a:column_mask(total_train,n) for a,n in candidates.items()}
        labels = pd.read_parquet(REFERENCE_DIR/fold/'predictions.parquet',columns=['ts','grp','y','smp','k','p']).rename(columns={'p':'p_reference'})
        assert abs(metrics(labels,'p_reference')['W_pct']-REFERENCE[fold])<1e-10
        placeholder = total_eval[['ts']].assign(p_total=1.)
        allocation = allocate(labels[['ts','grp','p_reference']],placeholder,evaluation[['ts','grp','capacity_kw']])
        directory = OUT/'data'/fold
        directory.mkdir(parents=True,exist_ok=True)
        for name,frame in [('group_train_inputs',train),('group_evaluation_inputs',evaluation),('full_training_groups',full),('train',total_train),('evaluation',total_eval),('targets_weights',target_rows),('labels',labels),('allocation_template',allocation)]:
            frame.to_parquet(directory/f'{name}.parquet',index=False)
        save(directory/'features.json',{'candidates':candidates,'features':features,'candidate_counts':{a:len(n) for a,n in candidates.items()},'retained_counts':{a:len(n) for a,n in features.items()},'categorical_features':[],'mask_source':'TRAIN ONLY','cutoff':str(cutoff),'end':str(end)})
        receipts.append({'fold':fold,'training_group_rows':len(train),'training_total_rows':len(total_train),'full_training_group_rows':len(full),'allnight_training_timestamps_excluded':len(targets)-len(total_train),'evaluation_group_rows':len(evaluation),'evaluation_total_rows':len(total_eval),'max_target_ts':str(full.ts.max()),'target_projection':['ts','grp','full_energy'],'target_filter':['ts','<=',str(cutoff)],'train_projection':['ts','grp',*names],'eval_projection':['ts','grp','capacity_kw',*names],'capacity_key_equivalence':True,'train_order_preserved':True,'no_future_targets':True,'allnight_evaluation_groups':int(allocation.capacity_kw.eq(0).sum()),'retained_features':{a:len(n) for a,n in features.items()}})
        print('TOTAL PREPARED',fold,len(total_train),len(total_eval),flush=True)
    save(OUT/'evidence/read_receipts.json',receipts)
    save(OUT/'prepared_manifest.json',{str(p.relative_to(OUT)):digest(p) for p in (OUT/'data').rglob('*') if p.is_file()})
