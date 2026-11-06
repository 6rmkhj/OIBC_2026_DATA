# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
# How to run: after all12 released fits by yield_run.py.
"""Calibrate each signed ensemble once, then blend only on PRIMARY."""
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- fixed calibration and score contracts
from yield_common import OUT,FOLDS,REFERENCE,save
from yield_math import component


def compare(arm: str):
    from calibrate import optimal_weight
    from final_metrics import metrics
    frames = {}
    capacity = json.loads((OUT/'static_capacity.json').read_text())
    for fold in FOLDS:
        labels = pd.read_parquet(OUT/'data'/fold/'labels.parquet')
        coverage = pd.read_parquet(OUT/'data'/fold/'coverage.parquet')
        features = pd.read_parquet(OUT/'data'/fold/'evaluation.parquet',columns=['ts','grp','wa_temp','extra_wa_snow'])
        keys = labels[['ts','grp']].merge(coverage,on=['ts','grp'],validate='one_to_one')
        predictions = []
        for seed in range(3):
            raw = pd.read_parquet(OUT/'trials'/arm/fold/f'seed{seed}'/'daylight_raw.parquet')
            pd.testing.assert_frame_equal(raw[['ts','grp']],features[['ts','grp']])
            complete = keys.merge(raw,on=['ts','grp'],how='left',validate='one_to_one')
            assert complete.p_raw.isna().eq(complete.night).all()
            predictions.append(complete.p_raw.fillna(0.).to_numpy())
        inputs = keys[['ts','grp']].merge(features,on=['ts','grp'],how='left',validate='one_to_one')
        inputs['static_capacity'] = inputs.grp.map(capacity)
        calibrated = component(inputs,np.array(predictions)).drop(columns='p_reference')
        frame = labels.merge(calibrated,on=['ts','grp'],validate='one_to_one')
        pd.testing.assert_frame_equal(frame[['ts','grp']],keys[['ts','grp']])
        assert frame.loc[keys.night,'p_new'].eq(0).all()
        frames[fold] = frame
    alpha = optimal_weight(frames['primary'].assign(p_bu=frames['primary'].p_reference,p_dir=frames['primary'].p_new),0.)
    assert np.isfinite(alpha) and 0<=alpha<=1
    scores = {}
    for fold,frame in frames.items():
        frame['alpha'] = alpha
        frame['p'] = (1-alpha)*frame.p_reference+alpha*frame.p_new
        directory = OUT/'comparisons'/arm/'ensemble'/fold
        directory.mkdir(parents=True,exist_ok=True)
        frame.to_parquet(directory/'predictions.parquet',index=False)
        scores[fold] = {n:metrics(frame,n) for n in ('p','p_reference','p_new')}
        assert abs(scores[fold]['p_reference']['W_pct']-REFERENCE[fold])<1e-10
        save(directory/'metrics.json',scores[fold])
    both = all(scores[f]['p']['W_pct']<REFERENCE[f] for f in FOLDS)
    record = {'arm':arm,'seeds':[0,1,2],'alpha_primary_only':alpha,'scores':scores,'both_folds_improve':both,'eligible':both and alpha>=.02,'mean_relative_W':sum(scores[f]['p']['W_pct']/REFERENCE[f] for f in FOLDS)/2}
    save(OUT/'comparisons'/arm/'decision.json',record)
    return record
