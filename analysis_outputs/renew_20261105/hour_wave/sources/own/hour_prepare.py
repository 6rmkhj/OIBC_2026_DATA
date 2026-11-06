# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
# How to run: hour_run.py --prepare.
"""Freeze one hour-stage recipe and prepare complete, label-free apply inputs."""
import json
import shutil
from pathlib import Path
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- retain exact original scoring row order
from hour_common import ROOT,OUT,REFERENCE_DIR,FOLDS,REFERENCE,BINS,save,digest,now

def freeze() -> None:
    if (OUT/'protocol.json').exists():
        return
    (OUT/'sources/own').mkdir(parents=True)
    (OUT/'evidence').mkdir(exist_ok=True)
    snapshots = {}
    paths = [p for folder in ('autoresearch','score_push','score_push_gpu') for p in (ROOT/'submission'/folder).glob('*.py')]
    paths.append(Path(__file__).with_name('cal_math.py'))
    for path in paths:
        shutil.copyfile(path,OUT/'sources'/path.name)
        snapshots[path.stem] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    own = {}
    for path in Path(__file__).parent.glob('hour_*.py'):
        shutil.copyfile(path,OUT/'sources/own'/path.name)
        own[path.name] = {'original':str(path.relative_to(ROOT)),'sha256':digest(path)}
    inputs = [ROOT/'handover 2/01_participant_dataset/sites.csv',ROOT/'analysis_outputs/autoresearch_20261103/cache/assignment.json']
    inputs += [ROOT/'analysis_outputs/renew_20261105/calibration_wave'/p for p in ('coefficients.json','static_capacity.json','results.json')]
    inputs += [ROOT/'analysis_outputs/renew_20261105/final/selected_coefficients.json']
    inputs += [REFERENCE_DIR/fold/'predictions.parquet' for fold in FOLDS]
    inputs += [ROOT/'analysis_outputs/renew_20261105/recency_wave/data'/fold/'night_coverage.parquet' for fold in FOLDS]
    protected = set(inputs)|{ROOT/r['original'] for r in snapshots.values()}
    protected.update(p for p in (ROOT/'submission').rglob('*.py') if '__pycache__' not in p.parts and not p.name.startswith('hour_'))
    for folder in ('submission/score_push_candidate','submission/autoresearch_candidate','submission/renew_candidate_20261105','analysis_outputs/score_push_20261104/final','analysis_outputs/renew_20261105'):
        protected.update(p for p in (ROOT/folder).rglob('*') if p.is_file() and OUT not in p.parents and '__pycache__' not in p.parts and 'tmp' not in p.parts and p.name!='controller.lock')
    save(OUT/'protocol.json',{'created_utc':now(),'candidate':'hour_bias','candidate_count':1,'folds':FOLDS,'reference_scores':REFERENCE,'reference':'CURRENT already temperature_then_snow calibrated p; no temperature/snow refit or repeated shrink','timezone':'Asia/Seoul; reject naive, malformed or missing timestamps','hour_bins':BINS,'fit':'Exactly5 cal_math.fit_factor calls, PRIMARY ONLY. Per bin y/current_calibrated_p weighted by SMP*k*current_calibrated_p; p>0 and SMP*k>0; >=150 rows AND>=20 distinct KST (ts-1hour) dates; otherwise identity. Bound median[.85,1.15].','apply':'effective_hour=1+.5*(bounded_hour-1); p=clip(current_calibrated_p*effective_hour,0,static composition capacity). Shrink ONLY new hour stage ONCE. Apply reads ts,grp,p_reference,static_capacity; no labels or monetary columns.','selection':'One candidate, strict lower W both folds else retain current reference. No alpha optimization, coefficient/threshold/bin/shrink grid, or recent adaptation.','historical_exposure':'All periods historically exposed; primary improvement partly in-sample by construction. Not an independent holdout.','resources':{'cpu_threads':16,'blas_threads':16,'pyarrow_threads':4,'priority_class':32,'parallel_jobs':1,'tree_fits':0,'real_scalar_fit_budget_after_release':5},'no_confirmation_test_fullrefit_export_upload':True,'reported_official_reference_score':6454220836,'reported_score_provenance':'User reported, not locally inferred','snapshots':snapshots,'own_sources':own,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in inputs},'protected_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sorted(protected)}})

def prepare() -> None:
    from final_metrics import metrics
    from hour_math import hour_bins
    sites = pd.read_csv(ROOT/'handover 2/01_participant_dataset/sites.csv',usecols=['site_id','capacity_kw'])
    assignment = json.loads((ROOT/'analysis_outputs/autoresearch_20261103/cache/assignment.json').read_text(encoding='utf-8'))
    assert len(sites)==253 and not sites.site_id.duplicated().any() and set(sites.site_id)==set(assignment)
    sites['grp'] = sites.site_id.map(assignment)
    capacity = sites.groupby('grp',as_index=False).capacity_kw.sum().rename(columns={'capacity_kw':'static_capacity'})
    frozen_capacity = json.loads((ROOT/'analysis_outputs/renew_20261105/calibration_wave/static_capacity.json').read_text(encoding='utf-8'))
    assert dict(zip(capacity.grp,capacity.static_capacity))==frozen_capacity
    save(OUT/'static_capacity.json',frozen_capacity)
    receipts = []
    for fold,(start_text,end_text) in FOLDS.items():
        start,end = (pd.Timestamp(t,tz='Asia/Seoul') for t in (start_text,end_text))
        reference = pd.read_parquet(REFERENCE_DIR/fold/'predictions.parquet',columns=['ts','grp','y','smp','k','p']).rename(columns={'p':'p_reference'})
        assert not reference.duplicated(['ts','grp']).any()
        assert start<reference.ts.min() and reference.ts.max()<=end
        assert np.isfinite(reference[['y','smp','k','p_reference']]).all().all()
        assert reference.smp.ge(0).all() and reference.k.ge(0).all() and reference.p_reference.ge(0).all()
        coverage = pd.read_parquet(ROOT/'analysis_outputs/renew_20261105/recency_wave/data'/fold/'night_coverage.parquet')
        frame = reference.merge(coverage,on=['ts','grp'],how='left',sort=False,validate='one_to_one').merge(capacity,on='grp',how='left',sort=False,validate='many_to_one')
        pd.testing.assert_frame_equal(frame[['ts','grp']],reference[['ts','grp']])
        assert frame.night.notna().all() and frame.static_capacity.notna().all()
        assert frame.loc[frame.night,'p_reference'].eq(0).all()
        assert (frame.p_reference<=frame.static_capacity+1e-8).all()
        assert abs(metrics(frame,'p_reference')['W_pct']-REFERENCE[fold])<1e-10
        bins = hour_bins(frame)
        directory = OUT/'data'/fold
        directory.mkdir(parents=True,exist_ok=True)
        frame.to_parquet(directory/'rows.parquet',index=False)
        apply_columns = ['ts','grp','p_reference','static_capacity']
        frame[apply_columns].to_parquet(directory/'apply_inputs.parquet',index=False)
        receipts.append({'fold':fold,'full_rows':len(frame),'night_rows':int(frame.night.sum()),'positive_reference_rows':int(frame.p_reference.gt(0).sum()),'hour_bin_counts':{str(i):int((bins==i).sum()) for i in range(5)},'period':{'start_exclusive':str(start),'end_inclusive':str(end)},'rows_columns':list(frame),'apply_columns':apply_columns,'exact_reference_keys_and_values':True,'night_prediction_zero':True,'reference_W_pct':metrics(frame,'p_reference')['W_pct'],'real_scalar_fits':0})
    save(OUT/'evidence/read_receipts.json',receipts)
    save(OUT/'prepared_manifest.json',{str(p.relative_to(OUT)):digest(p) for p in (OUT/'data').rglob('*') if p.is_file()})
