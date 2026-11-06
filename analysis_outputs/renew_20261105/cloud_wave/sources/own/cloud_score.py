# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
# How to run: called by temporal_run.py after all 24 fits.
"""Paired complete-key evidence and primary-only scalar selection."""
from cloud_common import OUT, DATA, TEMPORAL, FOLDS, REFERENCE, save, signed_mean

def compare(variant: str):
    import numpy as np
    import pandas as pd  # noqa: PANDAS_OK -- frozen metric/calibration contracts
    from calibrate import optimal_weight
    from final_metrics import metrics
    frames = {}
    for fold in FOLDS:
        labels = pd.read_parquet(DATA/fold/'labels.parquet').drop(columns='p_reference')
        temporal = pd.read_parquet(TEMPORAL/'comparisons/decay180/ensemble'/fold/'predictions.parquet')
        pd.testing.assert_frame_equal(labels[['ts','grp','y','smp','k','p_incumbent']],temporal[['ts','grp','y','smp','k','p_incumbent']])
        labels['p_reference'] = temporal.p
        labels['p_noaux'] = temporal.p_new
        keys = pd.read_parquet(DATA/fold/'evaluation.parquet',columns=['ts','grp'])
        predictions = []
        for seed in (0,1,2):
            raw = pd.read_parquet(OUT/'trials'/variant/fold/f'seed{seed}'/'daylight_raw.parquet')
            pd.testing.assert_frame_equal(raw[['ts','grp']],keys)
            assert np.isfinite(raw.p_raw).all()
            predictions.append(raw.p_raw.to_numpy())
        pure = keys.assign(p_new=signed_mean(predictions))
        frame = labels.merge(pure,on=['ts','grp'],how='left',validate='one_to_one')
        coverage = pd.read_parquet(TEMPORAL/'data'/fold/'night_coverage.parquet')
        frame = frame.merge(coverage,on=['ts','grp'],how='left',validate='one_to_one')
        assert frame.night.notna().all() and frame.p_new.isna().eq(frame.night).all()
        frame['p_new'] = frame.p_new.fillna(0.)
        frames[fold] = frame.drop(columns='night')
    alpha = optimal_weight(frames['primary'].assign(p_bu=frames['primary'].p_reference,p_dir=frames['primary'].p_new),0.)
    scores = {}
    for fold,frame in frames.items():
        directory = OUT/'comparisons'/variant/'ensemble'/fold
        directory.mkdir(parents=True,exist_ok=True)
        frame['alpha'] = alpha
        frame['p'] = (1-alpha)*frame.p_reference+alpha*frame.p_new
        frame.to_parquet(directory/'predictions.parquet',index=False)
        scores[fold] = {name:metrics(frame,name) for name in ('p','p_reference','p_new','p_incumbent','p_noaux')}
        save(directory/'metrics.json',scores[fold])
    both = all(scores[f]['p']['W_pct']<REFERENCE[f] for f in FOLDS)
    result = {'variant':variant,'stage':'ensemble','seeds':[0,1,2],'alpha_primary_only':alpha,'scores':scores,'both_folds_improve':both,'eligible':both and alpha>=.02,'mean_relative_W':sum(scores[f]['p']['W_pct']/REFERENCE[f] for f in FOLDS)/2}
    save(OUT/'comparisons'/variant/'ensemble/decision.json',result)
    return result

