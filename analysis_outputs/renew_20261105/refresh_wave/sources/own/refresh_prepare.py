# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
# How to run: called by refresh_run.py before any real scalar fitting.
"""Exact three-cohort projections, chronological splits and original replay."""
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact historical source and chronological contracts
from refresh_common import RENEW,OUT,FOLDS,COLUMNS,source_paths,save,digest,now

def prepare() -> None:
    capacity = json.loads((RENEW/'final/static_capacity.json').read_text(encoding='utf-8'))
    cohorts = {}
    references = {}
    receipts = []
    periods = {'primary':('2023-06-01','2024-06-01'),'recent':('2024-06-01','2025-03-01'),'latest':('2025-03-01','2025-06-01')}
    for name in ('primary','recent','latest'):
        paths = source_paths(name)
        prediction_name = 'p_reference' if name=='latest' else 'p'
        raw = pd.read_parquet(paths['raw'],columns=['ts','grp',prediction_name]).rename(columns={prediction_name:'p_reference'})
        labels = pd.read_parquet(paths['labels'],columns=['ts','grp','y','smp','k'])
        assert isinstance(raw.ts.dtype,pd.DatetimeTZDtype) and raw.ts.notna().all()
        assert str(raw.ts.dt.tz) in ('Asia/Seoul','UTC+09:00','pytz.FixedOffset(540)')
        start,end = (pd.Timestamp(t,tz='Asia/Seoul') for t in periods[name])
        assert start<raw.ts.min() and raw.ts.max()<=end
        assert not raw.duplicated(['ts','grp']).any() and not labels.duplicated(['ts','grp']).any()
        pd.testing.assert_frame_equal(raw[['ts','grp']],labels[['ts','grp']])
        rows = raw.merge(labels,on=['ts','grp'],how='left',sort=False,validate='one_to_one')
        features = pd.read_parquet(paths['weather'],columns=['ts','grp','wa_temp','extra_wa_snow','wb_cloud'])
        coverage = pd.read_parquet(paths['coverage'])
        assert not features.duplicated(['ts','grp']).any()
        rows = rows.merge(features,on=['ts','grp'],how='left',sort=False,validate='one_to_one',indicator=True)
        rows = rows.merge(coverage,on=['ts','grp'],how='left',sort=False,validate='one_to_one')
        assert rows.night.notna().all() and rows._merge.eq('left_only').eq(rows.night).all()
        assert int(rows._merge.eq('both').sum())==len(features)
        assert rows.loc[rows.night,'p_reference'].eq(0).all()
        rows = rows.drop(columns='_merge')
        rows['static_capacity'] = rows.grp.map(capacity)
        pd.testing.assert_frame_equal(rows[['ts','grp','p_reference']],raw)
        assert np.isfinite(rows[['p_reference','y','smp','k','static_capacity']]).all().all()
        assert rows.p_reference.ge(0).all() and rows.smp.ge(0).all() and rows.k.ge(0).all()
        assert (rows.p_reference<=rows.static_capacity+1e-8).all()
        frozen = rows[['ts','grp']].copy()
        for stage in ('p_weather','p_hour','p_cloud'):
            original = pd.read_parquet(paths[stage],columns=['ts','grp','p'])
            pd.testing.assert_frame_equal(original[['ts','grp']],frozen[['ts','grp']])
            frozen[stage] = original.p.to_numpy()
        directory = OUT/'data/sources'/name
        directory.mkdir(parents=True)
        rows.to_parquet(directory/'rows.parquet',index=False)
        features.to_parquet(directory/'feature_projection.parquet',index=False)
        frozen.to_parquet(directory/'frozen_references.parquet',index=False)
        cohorts[name],references[name] = rows,frozen
        receipts.append({'source':name,'rows':len(rows),'night_rows':int(rows.night.sum()),'weather_rows':len(features),'projected_columns':list(features),'raw_prediction_column':prediction_name,'unmatched_exact_allnight':True,'reference_zero_allnight':True,'raw_ts_min':str(raw.ts.min()),'raw_ts_max':str(raw.ts.max())})
    history = pd.concat([cohorts['primary'],cohorts['recent']],ignore_index=True)
    assert not history.duplicated(['ts','grp']).any()
    split_receipts = []
    for fold,(cutoff_text,end_text) in FOLDS.items():
        cutoff,end = (pd.Timestamp(t,tz='Asia/Seoul') for t in (cutoff_text,end_text))
        train = history.loc[history.ts<=cutoff].reset_index(drop=True)
        source = 'recent' if fold=='late_recent' else 'latest'
        evaluation = cohorts[source].loc[(cohorts[source].ts>cutoff)&(cohorts[source].ts<=end)].reset_index(drop=True)
        refs = references[source].loc[(references[source].ts>cutoff)&(references[source].ts<=end)].reset_index(drop=True)
        assert len(evaluation)==(4320 if fold=='late_recent' else 4416)
        assert train.ts.max()<=cutoff<evaluation.ts.min() and evaluation.ts.max()<=end
        assert not train[['ts','grp']].merge(evaluation[['ts','grp']],on=['ts','grp']).shape[0]
        pd.testing.assert_frame_equal(evaluation[['ts','grp']],refs[['ts','grp']])
        directory = OUT/'data'/fold
        directory.mkdir()
        train.to_parquet(directory/'train.parquet',index=False)
        evaluation[COLUMNS].to_parquet(directory/'evaluation.parquet',index=False)
        evaluation[['ts','grp','y','smp','k']].to_parquet(directory/'labels.parquet',index=False)
        refs.to_parquet(directory/'references.parquet',index=False)
        split_receipts.append({'fold':fold,'cutoff_inclusive':str(cutoff),'end_inclusive':str(end),'train_rows':len(train),'evaluation_rows':len(evaluation),'train_max_ts':str(train.ts.max()),'evaluation_min_ts':str(evaluation.ts.min()),'evaluation_columns':COLUMNS,'no_key_overlap':True})
    save(OUT/'evidence/read_receipts.json',{'sources':receipts,'folds':split_receipts})
    save(OUT/'prepared_manifest.json',{str(p.relative_to(OUT)):digest(p) for p in (OUT/'data').rglob('*') if p.is_file()})

def original_replay() -> None:
    from refresh_math import decode,apply_pipeline
    originals = {stage:json.loads((OUT/f'original_{stage}_coefficients.json').read_text(encoding='utf-8'))['factors'] for stage in ('weather','hour','cloud')}
    fitted = decode(originals)
    records = []
    for name in ('primary','recent','latest'):
        rows = pd.read_parquet(OUT/'data/sources'/name/'rows.parquet')
        reference = pd.read_parquet(OUT/'data/sources'/name/'frozen_references.parquet')
        prediction = apply_pipeline(rows[COLUMNS],fitted)
        pd.testing.assert_frame_equal(prediction[['ts','grp']],reference[['ts','grp']])
        for stage in ('p_weather','p_hour','p_cloud'):
            np.testing.assert_array_equal(prediction[stage],reference[stage])
        directory = OUT/'old_replay'/name
        directory.mkdir(parents=True)
        prediction.to_parquet(directory/'predictions.parquet',index=False)
        record = {'source':name,'rows':len(rows),'all_three_stages_exact':True,'max_absolute_error':0.,'prediction_sha256':digest(directory/'predictions.parquet')}
        save(directory/'replay.json',record)
        records.append(record)
    save(OUT/'old_replay/receipt.json',{'passed':True,'utc':now(),'before_first_newfit':True,'real_scalar_fit_count':0,'records':records})
