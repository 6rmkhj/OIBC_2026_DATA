# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: imported by incbound_prepare.py and released incbound_score.py.
"""TRAIN extrema, historical signed ensemble and unchanged calibration arithmetic."""
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact historical pandas groupmean and condition APIs
from incbound_common import OUT

def training_range(train: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    assert train.dtype==np.dtype('float64') and train.ndim==2 and np.isfinite(train).all()
    lower,upper = np.min(train,axis=0),np.max(train,axis=0)
    assert np.array_equal(np.clip(train,lower,upper).view(np.uint64),train.view(np.uint64))
    return lower,upper

def ensemble(keys: pd.DataFrame, raws: list[pd.DataFrame]) -> np.ndarray:
    assert len(raws)==3
    raw = pd.concat(raws).groupby(['ts','grp'],as_index=False).p_raw.mean()
    full = keys.merge(raw,on=['ts','grp'],how='left',sort=False,validate='one_to_one')
    assert np.isfinite(raw.p_raw).all()
    return np.clip(full.p_raw.fillna(0.).to_numpy(),0.,None)

def substitute(raw: np.ndarray, delta: np.ndarray, weight: float) -> np.ndarray:
    assert np.isfinite(raw).all() and np.isfinite(delta).all() and 0<weight<1
    result = raw.copy()
    active = delta!=0.
    result[active] = raw[active]+weight*delta[active]
    assert np.array_equal(result[~active].view(np.uint64),raw[~active].view(np.uint64))
    return result

def stages(frame: pd.DataFrame, raw: np.ndarray) -> pd.DataFrame:
    from cal_math import conditions
    from hour_math import hour_bins
    from sky_math import cloud_bins
    assert list(frame)==['ts','grp','wa_temp','extra_wa_snow','wb_cloud','static_capacity']
    assert np.isfinite(raw).all()
    original = {stage:json.loads((OUT/f'original_{stage}_coefficients.json').read_text(encoding='utf-8'))['factors'] for stage in ('weather','hour','cloud')}
    bins,snow = conditions(frame)
    temperature = np.array([1.,*[f['factor'] for f in original['weather']['temperature']]])[bins+1]
    product = temperature*np.where(snow,original['weather']['conditional_snow']['factor'],1.)
    weather_factor = 1+.5*(np.clip(product,.85,1.15)-1)
    cap = frame.static_capacity.to_numpy()
    weather = np.maximum(0,np.minimum(cap,raw*weather_factor))
    hours = np.array([f['factor'] for f in original['hour']['hours']])[hour_bins(frame)]
    hour = np.maximum(0,np.minimum(cap,weather*(1+.5*(hours-1))))
    clouds = np.array([1.,*[f['factor'] for f in original['cloud']['clouds']]])[cloud_bins(frame)+1]
    prediction = np.maximum(0,np.minimum(cap,hour*(1+.5*(clouds-1))))
    return frame.assign(p_raw_candidate=raw,p_weather=weather,p_hour=hour,p=prediction)

def self_check() -> list[str]:
    train = np.array([[-2.,4.,0.],[3.,5.,0.],[1.,8.,0.]])
    lower,upper = training_range(train)
    np.testing.assert_array_equal(lower,[-2.,4.,0.])
    np.testing.assert_array_equal(upper,[3.,8.,0.])
    future = np.array([[-9.,6.,7.],[2.,12.,-1.]])
    np.testing.assert_array_equal(np.clip(future,lower,upper),[[-2.,6.,0.],[2.,8.,0.]])
    keys = pd.DataFrame({'ts':pd.date_range('2024-01-01',periods=3,tz='Asia/Seoul'),'grp':['G1']*3})
    raws = [keys.iloc[:2].assign(p_raw=values) for values in ([-12.,-9.],[9.,1.],[9.,2.])]
    np.testing.assert_array_equal(ensemble(keys,raws),[2.,0.,0.])
    raw = np.array([0.,-0.,1.,120.])
    delta = np.array([0.,0.,-1.,2.])
    result = substitute(raw,delta,.25)
    np.testing.assert_array_equal(result,[0.,-0.,.75,120.5])
    assert result[-1]>100.
    assert np.array_equal(result[:2].view(np.uint64),raw[:2].view(np.uint64))
    return ['TRAINonly_exact_minmax','TRAINclip_bitwise_identity','all_columns_bounded_without_selection','historical_pandas_signed_mean_before_max0','zero_delta_preserves_raw_bits_including_signedzero','no_early_capacity_clip']
