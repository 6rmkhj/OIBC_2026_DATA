# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "scikit-learn"]
# ///
# How to run: extra_run.py --prepare fixtures; released extra_score.py weather-only component.
"""Normalized MSE scalars, signed ensemble and the original weather-only stage."""
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen calibration/key interfaces
from extra_common import OUT,PARAMS

def weights(scale: np.ndarray, age: np.ndarray) -> tuple[np.ndarray,np.ndarray,np.ndarray,float]:
    assert np.isfinite(scale).all() and (scale>0).all() and np.isfinite(age).all() and (age>=0).all()
    base = scale**2
    decay = np.exp2(-age/180.)
    adjustment = float(base.sum(dtype=np.float64)/(base*decay).sum(dtype=np.float64))
    weight = base*decay*base.sum(dtype=np.float64)/(base*decay).sum(dtype=np.float64)
    assert np.isfinite(weight).all() and (weight>0).all()
    np.testing.assert_allclose(weight.sum(dtype=np.float64),base.sum(dtype=np.float64),rtol=2e-15,atol=1e-12)
    return base,decay,weight,adjustment

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
    from site_features import normalizer
    from sklearn.ensemble import ExtraTreesRegressor
    from sklearn.utils import get_tags
    model = ExtraTreesRegressor(**PARAMS,random_state=0)
    assert get_tags(model).input_tags.allow_nan
    fit_params = model.get_params()
    assert fit_params=={**PARAMS,'random_state':0}
    model.set_params(n_jobs=1)
    infer_params = model.get_params()
    assert {k for k in fit_params if fit_params[k]!=infer_params[k]}=={'n_jobs'}
    assert fit_params['n_jobs']==16 and infer_params['n_jobs']==1
    assert not hasattr(model,'estimators_')
    scale = normalizer(np.array([0.,.5,1.],dtype=np.float64))
    base,decay,weight,adjustment = weights(scale,np.array([0.,180.,360.]))
    np.testing.assert_array_equal(decay,[1.,.5,.25])
    np.testing.assert_array_equal(weight,base*decay*base.sum()/(base*decay).sum())
    truth = np.array([.03,.4,.7])
    predicted = np.array([.5,.6,1.])
    np.testing.assert_allclose(weight*(truth/scale-predicted)**2/adjustment,decay*(truth-scale*predicted)**2,rtol=1e-12,atol=1e-15)
    frame = pd.DataFrame({'ts':pd.to_datetime(['2024-01-01 '+t for t in ('08:00','10:00','12:00','14:00','16:00','20:00')]).tz_localize('Asia/Seoul'),'grp':['G1']*6,'wa_temp':[-10.,0.,10.,20.,30.,np.nan],'extra_wa_snow':[0.,.001,1.,np.nan,0.,0.],'static_capacity':[100.]*6})
    predictions = np.array([[-12.,80.,150.,20.,50.,0.],[9.,90.,180.,30.,60.,0.],[9.,100.,120.,40.,70.,0.]])
    actual = component(frame,predictions)
    original = json.loads((OUT/'original_weather_coefficients.json').read_text(encoding='utf-8'))['factors']
    temperature = np.array([f['factor'] for f in original['temperature']]+[1.])
    snow = np.array([1.,original['conditional_snow']['factor'],original['conditional_snow']['factor'],1.,1.,1.])
    expected = np.maximum(0,np.minimum(100,np.clip(predictions.mean(axis=0),0,100)*(1+.5*(np.clip(temperature*snow,.85,1.15)-1))))
    np.testing.assert_array_equal(actual.p_weather,expected)
    np.testing.assert_array_equal(actual.p_new,expected)
    assert actual.p_component.iloc[0]==2. and actual.p_component.iloc[2]==100. and actual.p_new.iloc[-1]==0.
    assert np.maximum(predictions[:,0],0).mean()!=actual.p_component.iloc[0]
    return ['native_nan_estimator_tag','fit16_to_inference1_only_parameter_change_without_fit','raw_decay_half_life180','weight_preserves_base_mass','normalized_weighted_MSE_equivalence','signed_mean_before_clip','weather_only_original_factors_and_caps','night_zero_preserved']
