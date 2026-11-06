# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm"]
# ///
# How to run: prefit recent replay, then released final inference.
"""Signed saved-model inference and unchanged frozen calibration."""
from pathlib import Path
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen final feature/calibration contracts
import lightgbm as lgb
from renew_final_common import OUT,ROOT,RENEW,ALPHA,save,digest,coefficients


def temporal(frame: pd.DataFrame, paths: list[Path]) -> pd.DataFrame:
    from site_features import normalizer
    inverse = normalizer(frame.cosz.to_numpy())*frame.capacity_kw.to_numpy()
    predictions = []
    assert len(paths)==3
    for path in paths:
        config = json.loads((path/'config.json').read_text())
        model = lgb.Booster(model_file=str(path/'model.txt'))
        assert model.current_iteration()==400
        prediction = model.predict(frame[config['features']],raw_score=True,num_threads=16)*inverse
        assert np.isfinite(prediction).all()
        predictions.append(prediction)
    result = frame[['ts','grp']].copy()
    for seed,prediction in enumerate(predictions):
        result[f'seed{seed}_raw'] = prediction
    result['signed_seed_mean'] = np.mean(predictions,axis=0,dtype=np.float64)
    result['p_temporal'] = result.signed_seed_mean.clip(lower=0)
    return result


def compose(frame: pd.DataFrame, base: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    from cal_math import apply
    joined = base.merge(raw,on=['ts','grp'],how='left',validate='one_to_one')
    joined['p_temporal'] = joined.p_temporal.fillna(0.)
    joined['p_reference'] = (1-ALPHA)*joined.p_cpu+ALPHA*joined.p_temporal
    joined = joined.merge(frame[['ts','grp','wa_temp','extra_wa_snow']],on=['ts','grp'],how='left',validate='one_to_one')
    capacity = json.loads((OUT/'static_capacity.json').read_text())
    joined['static_capacity'] = joined.grp.map(capacity)
    calibrated = apply(joined,coefficients(),'temperature_then_snow')
    return joined.merge(calibrated[['ts','grp','temperature_bin','snow_condition','raw_factor','bounded_factor','effective_factor','before_capacity_clip','p','capacity_clipped']],on=['ts','grp'],validate='one_to_one')


def recent_replay() -> None:
    frame = pd.read_parquet(OUT/'data/recent/evaluation.parquet')
    expected_features = pd.read_parquet(ROOT/'analysis_outputs/score_push_gpu_20261104/data/recent/evaluation.parquet')
    pd.testing.assert_frame_equal(frame[expected_features.columns],expected_features)
    paths = [RENEW/'recency_wave/trials/decay180/recent'/f'seed{s}' for s in range(3)]
    raw = temporal(frame,paths)
    base = pd.read_parquet(OUT/'data/recent/cpu_base.parquet')
    prediction = compose(frame,base,raw)
    expected = pd.read_parquet(RENEW/'calibration_wave/comparisons/temperature_then_snow/recent/predictions.parquet',columns=['ts','grp','p'])
    paired = prediction[['ts','grp','p']].merge(expected,on=['ts','grp'],suffixes=('_replay','_selected'),how='outer',validate='one_to_one',indicator=True)
    assert paired._merge.eq('both').all() and len(paired)==13104
    error = float(np.max(np.abs(paired.p_replay-paired.p_selected)))
    exact = bool(np.array_equal(paired.p_replay,paired.p_selected))
    raw.to_parquet(OUT/'evidence/recent_temporal_raw.parquet',index=False)
    paired.drop(columns='_merge').to_parquet(OUT/'evidence/recent_replay.parquet',index=False)
    save(OUT/'evidence/recent_replay.json',{'passed':exact,'exact':exact,'rows':len(paired),'max_absolute_error':error,'features_exact':True,'coefficient_sha256':digest(OUT/'selected_coefficients.json'),'alpha':ALPHA})
    assert exact,f'Recent replay differs by {error}; root review required before release'
