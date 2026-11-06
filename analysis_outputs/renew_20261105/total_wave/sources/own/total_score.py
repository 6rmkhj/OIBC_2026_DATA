# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
# How to run: called after all12 fits by total_run.py.
"""Signed-total ensemble, frozen-share allocation and primary-only selection."""
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen calibration/metric contract
from total_common import OUT,FOLDS,REFERENCE,save
from total_math import signed_mean,allocate


def compare(arm: str):
    from calibrate import optimal_weight
    from final_metrics import metrics
    frames = {}
    for fold in FOLDS:
        keys = pd.read_parquet(OUT/'data'/fold/'evaluation.parquet',columns=['ts','capacity_kw'])
        predictions = []
        for seed in (0,1,2):
            raw = pd.read_parquet(OUT/'trials'/arm/fold/f'seed{seed}'/'total_raw.parquet')
            pd.testing.assert_frame_equal(raw[['ts','capacity_kw']],keys)
            assert np.isfinite(raw.p_raw).all()
            predictions.append(raw.p_raw.to_numpy())
        totals = keys.assign(signed_seed_mean=np.mean(predictions,axis=0,dtype=np.float64),p_total=signed_mean(np.array(predictions)))
        labels = pd.read_parquet(OUT/'data'/fold/'labels.parquet')
        capacities = pd.read_parquet(OUT/'data'/fold/'group_evaluation_inputs.parquet',columns=['ts','grp','capacity_kw'])
        allocation = allocate(labels[['ts','grp','p_reference']],totals[['ts','p_total']],capacities)
        frame = labels.merge(allocation.drop(columns='p_reference'),on=['ts','grp'],how='outer',validate='one_to_one',indicator=True)
        assert frame._merge.eq('both').all()
        frames[fold] = frame.drop(columns='_merge')
        directory = OUT/'comparisons'/arm/'ensemble'/fold
        directory.mkdir(parents=True,exist_ok=True)
        totals.to_parquet(directory/'signed_total_ensemble.parquet',index=False)
        allocation.to_parquet(directory/'allocation.parquet',index=False)
    alpha = optimal_weight(frames['primary'].assign(p_bu=frames['primary'].p_reference,p_dir=frames['primary'].p_new),0.)
    assert np.isfinite(alpha) and 0<=alpha<=1
    scores = {}
    for fold,frame in frames.items():
        frame['alpha'] = alpha
        frame['p'] = (1-alpha)*frame.p_reference+alpha*frame.p_new
        directory = OUT/'comparisons'/arm/'ensemble'/fold
        frame.to_parquet(directory/'predictions.parquet',index=False)
        scores[fold] = {name:metrics(frame,name) for name in ('p','p_reference','p_new')}
        assert abs(scores[fold]['p_reference']['W_pct']-REFERENCE[fold])<1e-10
        save(directory/'metrics.json',scores[fold])
    both = all(scores[f]['p']['W_pct']<REFERENCE[f] for f in FOLDS)
    result = {'arm':arm,'seeds':[0,1,2],'alpha_primary_only':alpha,'scores':scores,'both_folds_improve':both,'eligible':both and alpha>=.02,'mean_relative_W':sum(scores[f]['p']['W_pct']/REFERENCE[f] for f in FOLDS)/2}
    save(OUT/'comparisons'/arm/'decision.json',result)
    return result
