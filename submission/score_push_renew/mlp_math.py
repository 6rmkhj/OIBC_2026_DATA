# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "scikit-learn", "joblib"]
# ///
# How to run: imported by mlp_prepare.py, mlp_fit.py, mlp_score.py.
"""Exact normalized MSE weights, signed ensemble and fixed original stages."""
import json
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen numerical/scalar-stage contracts
from mlp_common import OUT
from site_features import normalizer

def weights(scale: np.ndarray, age_days: np.ndarray) -> tuple[np.ndarray,np.ndarray,np.ndarray,float]:
    scale = np.asarray(scale,dtype=np.float64)
    age_days = np.asarray(age_days,dtype=np.float64)
    assert np.isfinite(scale).all() and (scale>0).all() and np.isfinite(age_days).all() and (age_days>=0).all()
    base = scale**2
    decay = np.exp2(-age_days/180.)
    adjustment = float(base.sum(dtype=np.float64)/(base*decay).sum(dtype=np.float64))
    weight = base*decay*base.sum(dtype=np.float64)/(base*decay).sum(dtype=np.float64)
    assert np.isfinite(weight).all() and (weight>0).all()
    np.testing.assert_allclose(weight.sum(dtype=np.float64),base.sum(dtype=np.float64),rtol=2e-15,atol=1e-12)
    return base,decay,weight,adjustment

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

def self_check() -> list[str]:
    from learner_models import preprocessing
    from profile_features import column_mask
    from sklearn.preprocessing import StandardScaler
    import joblib
    train = pd.DataFrame({'varying':pd.Series([1,2,3],dtype='float32'),'constant':[0.,0.,0.],'missing':[np.nan]*3})
    future = pd.DataFrame({'varying':[np.nan,1e12],'constant':[999.,2.],'missing':[123.,456.]})
    selected = column_mask(train,list(train))
    assert selected==['varying']
    transform,x,z = preprocessing(train[selected].astype(np.float64),future[selected].astype(np.float64))
    assert x.dtype==z.dtype==np.dtype('float64')
    np.testing.assert_allclose(x[:,0],[-np.sqrt(1.5),0,np.sqrt(1.5)])
    assert z[0,0]==0.
    before = joblib.hash(transform)
    transform.transform(future[selected].astype(np.float64)*1e10)
    assert joblib.hash(transform)==before
    empty_transform,empty_x,empty_z = preprocessing(train[['varying','missing']].astype(np.float64),future[['varying','missing']].astype(np.float64))
    assert np.isfinite(empty_x).all() and np.isfinite(empty_z).all() and empty_z.shape==(2,2)
    assert empty_transform[0].statistics_[1]==0.
    scale = normalizer(np.array([0.,.5,1.],dtype=np.float64))
    age = np.array([0.,180.,360.])
    base,decay,weight,adjustment = weights(scale,age)
    np.testing.assert_array_equal(decay,[1.,.5,.25])
    np.testing.assert_array_equal(weight,base*decay*base.sum()/(base*decay).sum())
    target = np.array([.03,.4,.7])
    normalized = target/scale
    predicted = np.array([.5,.6,1.])
    scaler = StandardScaler().fit(normalized.reshape(-1,1))
    scaled_target = scaler.transform(normalized.reshape(-1,1)).ravel()
    scaled_prediction = scaler.transform(predicted.reshape(-1,1)).ravel()
    np.testing.assert_allclose(weight*(scaled_target-scaled_prediction)**2*scaler.scale_[0]**2/adjustment,decay*(target-scale*predicted)**2,rtol=1e-12,atol=1e-15)
    np.testing.assert_allclose(scaler.inverse_transform(scaled_prediction.reshape(-1,1)).ravel(),predicted,rtol=1e-15)
    mean,clipped = signed_clip(np.array([[-12.,-9.],[9.,1.],[9.,2.]]),np.array([100.,100.]))
    np.testing.assert_array_equal(mean,[2.,-2.])
    np.testing.assert_array_equal(clipped,[2.,0.])
    assert np.mean(np.maximum(0,np.array([-12.,9.,9.])))!=clipped[0]
    return ['TRAINonlyconstantmask','float64beforepreprocess','TRAINonlymedianandscale','futuremissing/extremeunchangedtransform','allmissingcolumnretainedbyhelper','targetscalerinverseonce','baseweightmasspreserved','half_life180','normalizedstandardizedweightedMSEequivalence','signedmeanbeforeclip']
