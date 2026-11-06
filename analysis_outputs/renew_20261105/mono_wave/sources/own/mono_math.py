# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: imported by mono_score.py.
"""Unchanged signed mean and original three-stage calibration; no old OUT import."""
import json
import re
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- existing frozen scalar-stage API
from mono_common import OUT

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


def constraints(names: list[str]) -> list[int]:
    negative = re.compile(r'(wa_station_WA[0-9]{3}_wa_cloud|wb_station_WB[0-9]{3}_wb_cloud)')
    positive = re.compile(r'(wa_station_WA[0-9]{3}_toaa|wb_station_WB[0-9]{3}_toab)')
    return [-1 if name in ('wa_cloud','wb_cloud') or negative.fullmatch(name) else 1 if name in ('toaa','toab') or positive.fullmatch(name) else 0 for name in names]

def weights(scale: np.ndarray, age_days: np.ndarray) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    assert np.isfinite(scale).all() and (scale>0).all() and np.isfinite(age_days).all() and (age_days>=0).all()
    decay = np.exp2(-age_days/180)
    multiplier = decay/decay.mean()
    weight = scale*multiplier
    assert np.isfinite(weight).all() and (weight>0).all()
    return decay,multiplier,weight

def self_check() -> list[str]:
    from profile_features import column_mask
    accepted = ['wa_cloud','wb_cloud','wa_station_WA001_wa_cloud','wb_station_WB073_wb_cloud','toaa','toab','wa_station_WA061_toaa','wb_station_WB002_toab']
    rejected = ['r10_wa_cloud','rev_wb_cloud','wa_cloud_ramp','wb_cloud_lead','wa_cloud_daylight_mean','wb_cloud_daylight_std','csa','csb','wa_station_WA001_csa','wb_station_WB073_csb','toaa_lead','toab_ramp','extra_wa_cloud','wa_station_WB001_wa_cloud','wa_station_WA001_wb_cloud','wa_station_WA001_toab','wa_station_WA01_wa_cloud','wa_station_WA0001_wa_cloud','prefix_wa_station_WA001_wa_cloud','wa_station_WA001_wa_cloud_suffix']
    assert constraints(accepted)==[-1]*4+[1]*4
    assert constraints(rejected)==[0]*len(rejected)
    train = pd.DataFrame({'wa_cloud':[1.,2.,np.nan],'toaa':[2.,3.,4.],'csa':[-.01,.2,.3],'constant':[0.]*3,'missing':[np.nan]*3})
    future = pd.DataFrame({'wa_cloud':[np.nan,1e6],'toaa':[2.,3.],'csa':[-.3,.1],'constant':[100.,200.],'missing':[1.,2.]})
    names = column_mask(train,list(train))
    assert names==['wa_cloud','toaa','csa'] and constraints(names)==[-1,1,0]
    assert future[names].wa_cloud.isna().iloc[0] and train[names].wa_cloud.isna().iloc[2]
    scale = np.array([.05,.5,1.])
    decay,multiplier,weight = weights(scale,np.array([0.,180.,360.]))
    np.testing.assert_array_equal(decay,[1.,.5,.25])
    np.testing.assert_array_equal(multiplier,decay/decay.mean())
    np.testing.assert_array_equal(weight,scale*multiplier)
    np.testing.assert_allclose(multiplier.mean(),1.,rtol=1e-15)
    mean,clipped = signed_clip(np.array([[-12.,-9.],[9.,1.],[9.,2.]]),np.array([100.,100.]))
    np.testing.assert_array_equal(mean,[2.,-2.])
    np.testing.assert_array_equal(clipped,[2.,0.])
    assert np.maximum(np.array([-12.,9.,9.]),0).mean()!=clipped[0]
    frame = pd.DataFrame({'ts':pd.to_datetime(['2024-01-01 '+t for t in ('08:00','10:00','12:00','14:00','16:00','20:00')]).tz_localize('Asia/Seoul'),'grp':['G1']*6,'wa_temp':[-10.,0.,10.,20.,30.,np.nan],'extra_wa_snow':[0.,.001,1.,np.nan,0.,0.],'wb_cloud':[0.,20.,50.,80.,np.nan,0.],'static_capacity':[100.]*6})
    predictions = np.array([[-12.,80.,150.,20.,50.,0.],[9.,90.,180.,30.,60.,0.],[9.,100.,120.,40.,70.,0.]])
    actual = component(frame,predictions)
    originals = {stage:json.loads((OUT/f'original_{stage}_coefficients.json').read_text(encoding='utf-8'))['factors'] for stage in ('weather','hour','cloud')}
    t = np.array([f['factor'] for f in originals['weather']['temperature']]+[1.])
    snow = np.array([1.,originals['weather']['conditional_snow']['factor'],originals['weather']['conditional_snow']['factor'],1.,1.,1.])
    weather = np.clip(np.clip(predictions.mean(axis=0),0,100)*(1+.5*(np.clip(t*snow,.85,1.15)-1)),0,100)
    h = np.array([f['factor'] for f in originals['hour']['hours']])[[0,1,2,3,4,4]]
    hour = np.clip(weather*(1+.5*(h-1)),0,100)
    c = np.array([f['factor'] for f in originals['cloud']['clouds']]+[1.])[[0,1,2,3,4,0]]
    final = np.clip(hour*(1+.5*(c-1)),0,100)
    for name,expected in (('p_weather',weather),('p_hour',hour),('p_new',final)):
        np.testing.assert_array_equal(actual[name],expected)
    assert actual.p_new.iloc[-1]==0.
    return ['exact_constraint_names_and_decoy_rejection','csa_csb_all0_including_negative_twilight','TRAINonly_mask_future_values_unused','native_NaNs_preserved','raw_and_mean1_decay180_exact','sample_weight_normalizer_times_multiplier','signed_mean_before_clip','original_weather_hour_cloud_order_and_caps_exact','zero_night_preserved']
