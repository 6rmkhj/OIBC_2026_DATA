# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: imported by bound_score.py.
"""Unchanged signed mean and original three-stage calibration; no old OUT import."""
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- existing frozen scalar-stage API
from bound_common import OUT

def signed_clip(predictions: np.ndarray, capacity: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    assert predictions.shape==(3,len(capacity)) and np.isfinite(predictions).all()
    mean = np.mean(predictions,axis=0,dtype=np.float64)
    return mean,np.clip(mean,0,capacity)

def component(frame: pd.DataFrame, predictions: np.ndarray) -> pd.DataFrame:
    from cal_math import Calibration,Factor,apply as weather_apply
    from hour_math import HourFactors,apply as hour_apply
    from sky_math import CloudFactors,apply as cloud_apply
    assert list(frame)==['ts','grp','wa_temp','extra_wa_snow','wb_cloud','static_capacity']
    original = {stage:json.loads((OUT/f'original_{stage}_coefficients.json').read_text(encoding='utf-8'))['factors'] for stage in ('weather','hour','cloud')}
    weather = original['weather']
    fitted_weather = Calibration(tuple(Factor(**r) for r in weather['temperature']),Factor(**weather['snow']),Factor(**weather['conditional_snow']))
    fitted_hour = HourFactors(tuple(Factor(**r) for r in original['hour']['hours']))
    fitted_cloud = CloudFactors(tuple(Factor(**r) for r in original['cloud']['clouds']))
    result = frame.copy()
    mean,clipped = signed_clip(predictions,frame.static_capacity.to_numpy(dtype=np.float64))
    result['signed_seed_mean'] = mean
    result['p_component'] = clipped
    result['p_weather'] = weather_apply(frame.assign(p_reference=clipped),fitted_weather,'temperature_then_snow').p.to_numpy()
    result['p_hour'] = hour_apply(frame.assign(p_reference=result.p_weather),fitted_hour).p.to_numpy()
    result['p_new'] = cloud_apply(frame.assign(p_reference=result.p_hour),fitted_cloud).p.to_numpy()
    return result

