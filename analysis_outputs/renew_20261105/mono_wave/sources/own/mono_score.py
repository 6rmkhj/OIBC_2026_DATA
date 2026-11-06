# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
# How to run: called by released bound_run.py after all6inferences.
"""Signed seed mean, frozen three-stage calibration and one PRIMARY alpha."""
from typing import TypedDict
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- full exact-key scoring contract
from mono_common import OUT,FOLDS,REFERENCE,save
from mono_math import component

class Metric(TypedDict):
    W: float
    W_pct: float
    revenue: float
    S: float
    rows: int

class Decision(TypedDict):
    arm: str
    scores: dict[str,dict[str,Metric]]
    alpha_primary_only: float
    both_folds_improve: bool
    eligible: bool
    seeds: list[int]
    mean_relative_W: float

def compare(arm: str) -> Decision:
    from calibrate import optimal_weight
    from final_metrics import metrics
    frames = {}
    for fold in FOLDS:
        data = OUT/'data'/fold
        inputs = pd.read_parquet(data/'application_inputs.parquet')
        labels = pd.read_parquet(data/'labels.parquet')
        coverage = pd.read_parquet(data/'coverage.parquet')
        keys = inputs[['ts','grp']].merge(coverage,on=['ts','grp'],sort=False,validate='one_to_one')
        seeds = []
        for seed in (0,1,2):
            raw = pd.read_parquet(OUT/'trials'/arm/fold/f'seed{seed}'/'daylight_raw.parquet')
            full = keys.merge(raw,on=['ts','grp'],how='left',sort=False,validate='one_to_one')
            assert full.p_raw.isna().eq(full.night).all()
            assert int(full.p_raw.notna().sum())==len(raw)
            seeds.append(full.p_raw.fillna(0.).to_numpy(dtype=np.float64))
        calibrated = component(inputs,np.array(seeds,dtype=np.float64))
        frame = labels.merge(calibrated,on=['ts','grp'],sort=False,validate='one_to_one')
        pd.testing.assert_frame_equal(frame[['ts','grp']],inputs[['ts','grp']])
        assert frame.loc[keys.night,'p_new'].eq(0).all()
        frames[fold] = frame
    primary = frames['primary']
    alpha = optimal_weight(primary.assign(p_bu=primary.p_reference,p_dir=primary.p_new),0.)
    assert np.isfinite(alpha) and 0<=alpha<=1
    scores = {}
    for fold,frame in frames.items():
        frame['alpha'] = alpha
        frame['p'] = (1-alpha)*frame.p_reference+alpha*frame.p_new
        directory = OUT/'comparisons'/arm/fold
        directory.mkdir(parents=True)
        frame.to_parquet(directory/'predictions.parquet',index=False)
        scores[fold] = {name:metrics(frame,name) for name in ('p','p_reference','p_new')}
        assert abs(scores[fold]['p_reference']['W_pct']-REFERENCE[fold])<1e-10
        save(directory/'metrics.json',scores[fold])
    both = all(scores[f]['p']['W']<scores[f]['p_reference']['W'] for f in FOLDS)
    return {'arm':arm,'scores':scores,'alpha_primary_only':alpha,'both_folds_improve':both,'eligible':both and alpha>=.02,'seeds':[0,1,2],'mean_relative_W':float(np.mean([scores[f]['p']['W']/scores[f]['p_reference']['W'] for f in FOLDS]))}
