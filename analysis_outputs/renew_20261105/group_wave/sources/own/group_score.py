# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
# How to run: called by group_run.py after all 18 model receipts.
"""Signed site ensemble, complete-group clipping, primary-only blend selection."""
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen calibration and scoring contract
from group_common import OUT, FOLDS, REFERENCE, save


def compare(arm: str):
    from calibrate import optimal_weight
    from final_metrics import metrics
    frames = {}
    for fold in FOLDS:
        evaluation = pd.read_parquet(OUT/'data'/fold/'evaluation.parquet',columns=['ts','site_id','grp','capacity_kw','night'])
        predictions = []
        for seed in (0,1,2):
            raw = pd.read_parquet(OUT/'trials'/arm/fold/f'seed{seed}'/'site_raw.parquet')
            pd.testing.assert_frame_equal(raw[list(evaluation)],evaluation)
            assert np.isfinite(raw.cf_raw).all() and raw.loc[raw.night,'cf_raw'].eq(0).all()
            predictions.append(raw.cf_raw.to_numpy())
        ensemble = evaluation.assign(cf_raw=np.mean(predictions,axis=0,dtype=np.float64))
        ensemble['energy_raw'] = ensemble.cf_raw*ensemble.capacity_kw
        summed = ensemble.groupby(['ts','grp'],as_index=False,observed=True).energy_raw.sum()
        summed['p_new'] = summed.energy_raw.clip(lower=0)
        labels = pd.read_parquet(OUT/'data'/fold/'labels.parquet')
        frame = labels.merge(summed,on=['ts','grp'],how='outer',validate='one_to_one',indicator=True)
        assert frame._merge.eq('both').all()
        frame = frame.drop(columns='_merge')
        coverage = pd.read_parquet(OUT/'data'/fold/'coverage.parquet')
        aligned = frame.merge(coverage,on=['ts','grp'],validate='one_to_one')
        assert aligned.loc[aligned.night,'p_new'].eq(0).all()
        directory = OUT/'comparisons'/arm/'ensemble'/fold
        directory.mkdir(parents=True,exist_ok=True)
        ensemble.to_parquet(directory/'signed_site_ensemble.parquet',index=False)
        save(directory/'aggregation.json',{'negative_cf':int((ensemble.cf_raw<0).sum()),'negative_group_raw':int((summed.energy_raw<0).sum()),'allnight_groups':int(coverage.night.sum()),'complete_groups':len(frame),'allnight_zero':True,'order':'mean signed CF, multiply capacity, sum group, clip group'})
        frames[fold] = frame
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
