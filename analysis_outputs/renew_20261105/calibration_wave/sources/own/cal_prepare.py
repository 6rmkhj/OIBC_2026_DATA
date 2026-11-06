# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "threadpoolctl"]
# ///
# How to run: cal_run.py --prepare.
"""Preregister fixed calibration recipes and exact-key feature projections."""
import json
from pathlib import Path
import shutil
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- preserve frozen reference labels
from cal_common import ROOT,OUT,DATA,REFERENCE_DIR,FOLDS,ARMS,REFERENCE,save,digest,now


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
    for path in [*Path(__file__).parent.glob('cal_*.py'),Path(__file__).with_name('temporal_common.py')]:
        shutil.copyfile(path,OUT/'sources/own'/path.name)
        own[path.name] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    inputs = [ROOT/'handover 2/01_participant_dataset/sites.csv',ROOT/'analysis_outputs/autoresearch_20261103/cache/assignment.json']
    inputs += [DATA/f/'evaluation.parquet' for f in FOLDS]
    inputs += [REFERENCE_DIR/f/'predictions.parquet' for f in FOLDS]
    inputs += [ROOT/'analysis_outputs/renew_20261105/recency_wave/data'/f/'night_coverage.parquet' for f in FOLDS]
    protected = set(inputs)|{ROOT/r['original'] for r in snapshots.values()}
    for folder in ('submission/score_push_candidate','submission/autoresearch_candidate','analysis_outputs/score_push_20261104/final','analysis_outputs/renew_20261105/group_wave','analysis_outputs/renew_20261105/total_wave'):
        protected.update(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    save(OUT/'protocol.json',{'created_utc':now(),'arms':ARMS,'folds':FOLDS,'reference_scores':REFERENCE,'feature_projection':['ts','grp','wa_temp','extra_wa_snow'],'temperature_bins':['[-inf,0)','[0,10)','[10,20)','[20,30)','[30,inf)'],'snow_threshold':.001,'fit':'PRIMARY only weighted median y/p, weight=SMP*k*p. Only condition true,p>0,SMP*k>0. >=150 support rows AND>=20 distinct right-closed calendar days (ts-1hour). Otherwise identity, including zero mass. Raw median clipped[.85,1.15]. Missing conditions identity.','recipes':{'snow_only':'One snow factor fitted on original PRIMARY reference.','temperature_only':'Five temperature factors fitted on original PRIMARY reference.','temperature_then_snow':'Reuse exact same five temperature factors, apply FULL bounded factors to PRIMARY reference, fit additional snow factor on adjusted PRIMARY p using adjusted p in ratio AND weights.'},'apply':'Raw factor is snow, temperature, or temperature*conditional snow. Clip raw product [.85,1.15], THEN shrink ONCE effective=1+.5*(bounded-1). Prediction=max(0,min(static composition capacity,reference*effective)). Apply reads no y/SMP/k. Exact same factors transfer to RECENT.','selection':'Strict W improvement BOTH folds; minimum equal-fold relativeW among3arms, else retain reference. NO alpha optimization or alpha>=.02 gate; fixed shrink.5.','historical_exposure':'Primary fitted improvement is partly in-sample calibration by construction. All periods historically exposed; no independent holdout claim. No threshold/bin/shrink search or recent adaptation.','resources':{'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_jobs':1,'tree_model_fits':0},'snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)}})


def prepare() -> None:
    from final_metrics import metrics
    sites = pd.read_csv(ROOT/'handover 2/01_participant_dataset/sites.csv',usecols=['site_id','capacity_kw'])
    assignment = json.loads((ROOT/'analysis_outputs/autoresearch_20261103/cache/assignment.json').read_text())
    assert not sites.site_id.duplicated().any() and set(sites.site_id)==set(assignment)
    sites['grp'] = sites.site_id.map(assignment)
    assert sites.grp.notna().all() and np.isfinite(sites.capacity_kw).all() and sites.capacity_kw.gt(0).all()
    capacity = sites.groupby('grp',as_index=False).capacity_kw.sum().rename(columns={'capacity_kw':'static_capacity'})
    save(OUT/'static_capacity.json',dict(zip(capacity.grp,capacity.static_capacity)))
    receipts = []
    for fold,(start_text,end_text) in FOLDS.items():
        start,end = (pd.Timestamp(t,tz='Asia/Seoul') for t in (start_text,end_text))
        reference = pd.read_parquet(REFERENCE_DIR/fold/'predictions.parquet',columns=['ts','grp','y','smp','k','p'],filters=[('ts','>',start),('ts','<=',end)]).rename(columns={'p':'p_reference'})
        features = pd.read_parquet(DATA/fold/'evaluation.parquet',columns=['ts','grp','wa_temp','extra_wa_snow'],filters=[('ts','>',start),('ts','<=',end)])
        assert not reference.duplicated(['ts','grp']).any() and not features.duplicated(['ts','grp']).any()
        assert start<reference.ts.min() and reference.ts.max()<=end
        assert np.isfinite(reference[['y','smp','k','p_reference']].to_numpy()).all()
        assert reference.smp.ge(0).all() and reference.p_reference.ge(0).all()
        coverage = pd.read_parquet(ROOT/'analysis_outputs/renew_20261105/recency_wave/data'/fold/'night_coverage.parquet')
        frame = reference.merge(features,on=['ts','grp'],how='outer',validate='one_to_one',indicator=True)
        assert not frame._merge.eq('right_only').any()
        frame = frame.merge(coverage,on=['ts','grp'],how='left',validate='one_to_one')
        assert frame.night.notna().all() and frame._merge.eq('left_only').eq(frame.night).all()
        assert frame.loc[frame.night,'p_reference'].eq(0).all()
        frame = frame.drop(columns='_merge').merge(capacity,on='grp',how='left',validate='many_to_one')
        assert frame.static_capacity.notna().all() and (frame.p_reference<=frame.static_capacity+1e-8).all()
        assert abs(metrics(frame,'p_reference')['W_pct']-REFERENCE[fold])<1e-10
        directory = OUT/'data'/fold
        directory.mkdir(parents=True,exist_ok=True)
        frame.to_parquet(directory/'rows.parquet',index=False)
        features.to_parquet(directory/'feature_projection.parquet',index=False)
        frame[['ts','grp','p_reference','wa_temp','extra_wa_snow','static_capacity']].to_parquet(directory/'apply_inputs.parquet',index=False)
        receipts.append({'fold':fold,'period':{'start_exclusive':str(start),'end_inclusive':str(end)},'full_rows':len(frame),'daylight_rows':len(features),'allnight_unmatched_rows':int(frame.night.sum()),'projected_feature_columns':list(features),'unmatched_exact_allnight':True,'reference_zero_allnight':True,'reference_within_static_capacity':True,'apply_columns':['ts','grp','p_reference','wa_temp','extra_wa_snow','static_capacity'],'no_confirmation_or_test':True})
    save(OUT/'evidence/read_receipts.json',receipts)
    save(OUT/'prepared_manifest.json',{str(p.relative_to(OUT)):digest(p) for p in (OUT/'data').rglob('*') if p.is_file()})
