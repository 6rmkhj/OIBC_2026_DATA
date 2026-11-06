# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
# How to run: called by gpu_run.py after protocol freeze.
"""Predicate-bounded development data and the complete frozen CPU reference."""
from gpu_common import ROOT, OLD, OUT, FOLDS, REFERENCE, save
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- preserve frozen feature numerics
from train import forecast_context
from final_metrics import metrics


def prepare() -> None:
    profiles = pd.read_parquet(OLD/'profile_wave/cache/stations.parquet',filters=[('ts','<=',pd.Timestamp('2025-03-01',tz='Asia/Seoul'))])
    for fold in FOLDS:
        directory = OUT/'data'/fold
        directory.mkdir(parents=True)
        cache = OLD/('cache' if fold=='primary' else 'recent/cache')
        cutoff = pd.Timestamp('2023-06-01' if fold=='primary' else '2024-06-01',tz='Asia/Seoul')
        end = pd.Timestamp('2024-06-01' if fold=='primary' else '2025-03-01',tz='Asia/Seoul')
        train = pd.read_parquet(cache/'train.parquet',filters=[('ts','<=',cutoff)])
        evaluation = pd.read_parquet(cache/'selection.parquet',filters=[('ts','>',cutoff),('ts','<=',end)])
        assert not {'energy','cf','y'}&set(evaluation)
        train = forecast_context(train,'ramps_daily_lead')
        evaluation = forecast_context(evaluation,'ramps_daily_lead')
        names = json.loads((OLD/'trials/combined_physics/features.json').read_text())
        names += [n for n in evaluation if n.endswith(('_ramp','_lead','_daylight_mean','_daylight_std'))]
        names.append('grp_code')
        frames = []
        for frame in (train,evaluation):
            frame = frame.assign(grp_code=frame.grp.map({'G1':0,'G2':1})).merge(profiles,on=['ts','grp'],how='left',validate='one_to_one',indicator=True)
            assert frame._merge.eq('both').all()
            frames.append(frame.drop(columns='_merge'))
        train,evaluation = frames
        profile_names = names+list(profiles.columns[2:])
        assert len(names)==100 and len(profile_names)==904
        assert train.ts.max()<=cutoff<evaluation.ts.min() and evaluation.ts.max()<=end
        assert not {'energy','cf','y','smp','k'}&set(profile_names)
        assert not np.isinf(train[profile_names].to_numpy()).any() and not np.isinf(evaluation[profile_names].to_numpy()).any()
        reference = pd.read_parquet(OLD/f'closing_wave/{fold}/selected/predictions.parquet',columns=['ts','grp','y','smp','k','p'],filters=[('ts','>',cutoff),('ts','<=',end)]).rename(columns={'p':'p_reference'})
        if fold=='primary':
            oracle = pd.read_parquet(ROOT/'analysis_outputs/autoresearch_20261103/cache/selection_labels.parquet',filters=[('ts','>',cutoff),('ts','<=',end)])
            direct = pd.read_parquet(OLD/'trials/baseline_exact/predictions.parquet')
            oracle = oracle.merge(direct,on=['ts','grp'],how='left',validate='one_to_one')
            oracle['p_incumbent'] = (1-.7149301735712863)*oracle.p_bu+.7149301735712863*oracle.p_dir.fillna(0.)
        else:
            oracle = pd.read_parquet(ROOT/'analysis_outputs/autoresearch_20261103/final/outer_predictions.parquet',columns=['ts','grp','y','smp','k','site_count','p_candidate'],filters=[('ts','>',cutoff),('ts','<=',end)]).rename(columns={'p_candidate':'p_incumbent'})
        labels = reference.merge(oracle,on=['ts','grp'],how='outer',validate='one_to_one',suffixes=('','_oracle'),indicator=True)
        assert labels._merge.eq('both').all() and len(labels)==(17568 if fold=='primary' else 13104)
        for name in ('y','smp','k'):
            np.testing.assert_array_equal(labels[name],labels[name+'_oracle'])
        columns = ['ts','grp','y','smp','k','p_reference','p_incumbent']+(['site_count'] if 'site_count' in labels else [])
        labels = labels[columns]
        np.testing.assert_array_equal(labels.k,np.where(labels.ts.dt.hour.between(11,15),3,1))
        assert abs(metrics(labels,'p_reference')['W_pct']-REFERENCE[fold])<1e-10
        assert set(map(tuple,evaluation[['ts','grp']].to_numpy()))<=set(map(tuple,labels[['ts','grp']].to_numpy()))
        train[['ts','grp','cf',*profile_names]].to_parquet(directory/'train.parquet',index=False)
        evaluation[['ts','grp','capacity_kw',*profile_names]].to_parquet(directory/'evaluation.parquet',index=False)
        labels.to_parquet(directory/'labels.parquet',index=False)
        save(directory/'features.json',{'rich':names,'station':profile_names,'train_rows':len(train),'daylight_keys':len(evaluation),'full_keys':len(labels),'train_min':str(train.ts.min()),'train_max':str(train.ts.max()),'cutoff':str(cutoff),'evaluation_min':str(evaluation.ts.min()),'evaluation_max':str(evaluation.ts.max()),'train_label_filter':[['ts','<=',str(cutoff)]],'missing_semantics':'Native CatBoost Min numeric NaN; no imputation fitted on evaluation; station mask train-only','reference':metrics(labels,'p_reference'),'old_incumbent':metrics(labels,'p_incumbent')})
