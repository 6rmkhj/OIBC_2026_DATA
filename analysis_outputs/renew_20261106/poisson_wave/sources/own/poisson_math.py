# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "lightgbm"]
# ///
# How to run: poisson_run.py --prepare; synthetic checks perform zero fits.
"""Temporal Poisson weights, once-only inverse and unchanged weather component."""
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen calibration/key interfaces
from poisson_common import OUT,PARAMS

def weights(scale: np.ndarray, age: np.ndarray) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    assert np.isfinite(scale).all() and (scale>0).all() and np.isfinite(age).all() and (age>=0).all()
    decay = np.exp2(-age/180)
    multiplier = decay/decay.mean()
    weight = scale*multiplier
    assert np.isfinite(weight).all() and (weight>0).all()
    return decay,multiplier,weight

def inverse_prediction(linked_mean: np.ndarray, inverse_kwh: np.ndarray) -> np.ndarray:
    assert linked_mean.shape==inverse_kwh.shape and np.isfinite(linked_mean).all() and (linked_mean>=0).all()
    assert np.isfinite(inverse_kwh).all() and (inverse_kwh>0).all()
    result = linked_mean*inverse_kwh
    assert np.isfinite(result).all()
    return result

def component(frame: pd.DataFrame, predictions: np.ndarray) -> pd.DataFrame:
    from cal_math import Calibration,Factor,apply
    assert list(frame)==['ts','grp','wa_temp','extra_wa_snow','static_capacity']
    assert predictions.shape==(3,len(frame)) and np.isfinite(predictions).all()
    original = json.loads((OUT/'original_weather_coefficients.json').read_text(encoding='utf-8'))['factors']
    fitted = Calibration(tuple(Factor(**r) for r in original['temperature']),Factor(**original['snow']),Factor(**original['conditional_snow']))
    mean = np.mean(predictions,axis=0,dtype=np.float64)
    clipped = np.clip(mean,0,frame.static_capacity.to_numpy(dtype=np.float64))
    weather = apply(frame.assign(p_reference=clipped),fitted,'temperature_then_snow').p.to_numpy()
    return frame.assign(signed_seed_mean=mean,p_component=clipped,p_weather=weather,p_new=weather)


def self_check() -> list[str]:
    from lightgbm import LGBMRegressor
    from profile_features import column_mask
    estimator = LGBMRegressor(**PARAMS)
    assert estimator.get_params()['objective']=='poisson' and not estimator.__sklearn_is_fitted__()
    mask_frame = pd.DataFrame({'vary':[0.,1.,np.nan],'constant':[2.,2.,np.nan],'missing':[np.nan]*3})
    assert column_mask(mask_frame,list(mask_frame))==['vary']
    scale = np.array([2.,3.,4.])
    decay,multiplier,weight = weights(scale,np.array([0.,180.,360.]))
    np.testing.assert_array_equal(decay,[1.,.5,.25])
    np.testing.assert_allclose(multiplier,[12/7,6/7,3/7],rtol=1e-15)
    np.testing.assert_allclose(weight,[24/7,18/7,12/7],rtol=1e-15)
    y,mu = np.array([0.,.3,1.5]),np.array([.2,.6,2.])
    positive = y>0
    native = mu-y
    normalized = mu/scale-y/scale
    native[positive] += y[positive]*np.log(y[positive]/mu[positive])
    normalized[positive] += (y/scale)[positive]*np.log((y/scale)[positive]/(mu/scale)[positive])
    np.testing.assert_allclose(scale*normalized,native,rtol=1e-14,atol=1e-15)
    np.testing.assert_allclose(weight*normalized,multiplier*native,rtol=1e-14,atol=1e-15)
    assert native[0]==.2
    np.testing.assert_array_equal(inverse_prediction(np.array([.25,1.,3.]),np.array([4.,8.,12.])),[1.,8.,36.])
    frame = pd.DataFrame({'ts':pd.to_datetime(['2024-01-01 '+t for t in ('08:00','10:00','12:00','14:00','16:00','20:00')]).tz_localize('Asia/Seoul'),'grp':['G1']*6,'wa_temp':[-10.,0.,10.,20.,30.,np.nan],'extra_wa_snow':[0.,.001,1.,np.nan,0.,0.],'static_capacity':[100.]*6})
    predictions = np.array([[-12.,80.,150.,20.,50.,0.],[9.,90.,180.,30.,60.,0.],[9.,100.,120.,40.,70.,0.]])
    actual = component(frame,predictions)
    original = json.loads((OUT/'original_weather_coefficients.json').read_text(encoding='utf-8'))['factors']
    temperature = np.array([f['factor'] for f in original['temperature']]+[1.])
    snow = np.array([1.,original['conditional_snow']['factor'],original['conditional_snow']['factor'],1.,1.,1.])
    expected = np.maximum(0,np.minimum(100,np.clip(predictions.mean(axis=0),0,100)*(1+.5*(np.clip(temperature*snow,.85,1.15)-1))))
    np.testing.assert_array_equal(actual.p_new,expected)
    assert actual.p_component.iloc[0]==2. and actual.p_component.iloc[2]==100. and actual.p_new.iloc[-1]==0.
    return ['train_only_nonconstant_mask','half_life180_mean_one_weights','poisson_deviance_scaling_including_zero','weighted_quasi_deviance_identity','already_linked_inverse_once','signed_mean_before_clip','original_weather_only_caps','night_zero','unfitted_estimator_only']
