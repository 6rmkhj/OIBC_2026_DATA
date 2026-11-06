# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
# How to run: imported by gpu_run.py after bounded GPU fits.
"""Primary-only scalar complement calibration and paired development evidence."""
from gpu_common import OUT, FOLDS, REFERENCE, save
from calibrate import optimal_weight
from final_metrics import metrics
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact historical weighted loss


def compare(variant: str, seeds: tuple[int,...], stage: str):
    frames = {}
    for fold in FOLDS:
        labels = pd.read_parquet(OUT/'data'/fold/'labels.parquet')
        keys = pd.read_parquet(OUT/'data'/fold/'evaluation.parquet',columns=['ts','grp'])
        predictions = []
        for seed in seeds:
            raw = pd.read_parquet(OUT/'trials'/variant/fold/f'seed{seed}'/'daylight_raw.parquet')
            pd.testing.assert_frame_equal(raw[['ts','grp']],keys)
            assert np.isfinite(raw.p_raw).all()
            predictions.append(raw.p_raw.to_numpy())
        pure = keys.assign(p_new=ensemble_prediction(predictions))
        frame = labels.merge(pure,on=['ts','grp'],how='left',validate='one_to_one')
        assert len(frame)==(17568 if fold=='primary' else 13104)
        frame['p_new'] = frame.p_new.fillna(0.)
        assert np.isfinite(frame.p_new).all() and frame.p_new.ge(0).all()
        frames[fold]=frame
    primary = frames['primary'].assign(p_bu=frames['primary'].p_reference,p_dir=frames['primary'].p_new)
    alpha = optimal_weight(primary,0.)
    scores = {}
    for fold,frame in frames.items():
        directory = OUT/'comparisons'/variant/stage/fold
        directory.mkdir(parents=True,exist_ok=True)
        frame['p'] = (1-alpha)*frame.p_reference+alpha*frame.p_new
        frame['alpha'] = alpha
        frame.to_parquet(directory/'predictions.parquet',index=False)
        scores[fold] = {name:metrics(frame,name) for name in ('p','p_new','p_reference','p_incumbent')}
        save(directory/'metrics.json',scores[fold])
        months = {name:rows for name,rows in frame.groupby((frame.ts-pd.Timedelta(hours=1)).dt.strftime('%Y-%m'))}
        monthly = [{'slice':name,'arm':arm,**metrics(rows,arm)} for name,rows in {**months,'peak_11_15':frame[frame.k.eq(3)]}.items() for arm in ('p','p_new','p_reference','p_incumbent')]
        pd.DataFrame(monthly).to_csv(directory/'diagnostics.csv',index=False)
    both = all(scores[fold]['p']['W_pct']<REFERENCE[fold] for fold in FOLDS)
    result = {'variant':variant,'stage':stage,'seeds':list(seeds),'alpha_primary_only':alpha,'scores':scores,'both_folds_improve':both,'eligible':both and alpha>=.02,'mean_relative_W':sum(scores[f]['p']['W_pct']/REFERENCE[f] for f in FOLDS)/2,'calibration_model_fits':0}
    save(OUT/'comparisons'/variant/stage/'decision.json',result)
    print('PAIRED GPU',variant,stage,alpha,{fold:scores[fold]['p']['W_pct'] for fold in FOLDS},flush=True)
    return result



def ensemble_prediction(predictions: list[np.ndarray]) -> np.ndarray:
    assert predictions and all(np.isfinite(p).all() for p in predictions)
    return np.clip(np.mean(predictions,axis=0),0,None)


def self_check() -> None:
    np.testing.assert_array_equal(ensemble_prediction([np.array([-2.,-4.]),np.array([1.,1.]),np.array([4.,2.])]),np.array([1.,0.]))
    n=np.array([.05,.5,1.])
    cap=np.array([100.,200.,300.])
    smp=np.array([50.,90.,120.])
    k=np.array([1.,3.,1.])
    cf=np.array([.1,.3,.4])
    z=np.array([.5,.3,.6])
    cost=cap*smp*k
    weights=n*cost/cost.mean()
    np.testing.assert_allclose(weights*np.abs(z-cf/n)*cost.mean(),smp*k*np.abs(n*z*cap-cf*cap),rtol=1e-12)
    save(OUT/'evidence/arithmetic_self_check.json',{'mean_before_clip':True,'monetary_loss_equivalence':True,'passed':True})

