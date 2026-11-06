# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: imported by verify_terminal.py; arithmetic only, never calls fit.
"""Independent weighted-median records and three-stage array equations."""
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact existing right-closed day contract

def temperature_bins(frame: pd.DataFrame) -> np.ndarray:
    value = frame.wa_temp.to_numpy()
    finite = np.isfinite(value)
    bins = np.full(len(value),-1,dtype=np.int64)
    bins[finite] = np.select([value[finite]<0,value[finite]<10,value[finite]<20,value[finite]<30],[0,1,2,3],default=4)
    return bins

def hours(frame: pd.DataFrame) -> np.ndarray:
    value = frame.ts.dt.tz_convert('Asia/Seoul').dt.hour.to_numpy()
    return np.select([value<10,value<12,value<14,value<16],[0,1,2,3],default=4)

def clouds(frame: pd.DataFrame) -> np.ndarray:
    value = frame.wb_cloud.to_numpy()
    finite = np.isfinite(value)
    bins = np.full(len(value),-1,dtype=np.int64)
    bins[finite] = np.select([value[finite]<20,value[finite]<50,value[finite]<80],[0,1,2],default=3)
    return bins

def weather_p(frame: pd.DataFrame, factors: dict) -> np.ndarray:
    temperature = np.array([1.,*[r['factor'] for r in factors['temperature']]])[temperature_bins(frame)+1]
    snow = np.isfinite(frame.extra_wa_snow)&frame.extra_wa_snow.ge(.001)
    product = temperature*np.where(snow,factors['conditional_snow']['factor'],1.)
    bounded = np.clip(product,.85,1.15)
    return np.clip(frame.p_reference.to_numpy()*(1+.5*(bounded-1)),0,frame.static_capacity.to_numpy())

def stages(frame: pd.DataFrame, factors: dict) -> dict[str,np.ndarray]:
    weather = weather_p(frame,factors['weather'])
    hour_factor = np.array([r['factor'] for r in factors['hour']['hours']])[hours(frame)]
    hour = np.clip(weather*(1+.5*(hour_factor-1)),0,frame.static_capacity.to_numpy())
    cloud_factor = np.array([1.,*[r['factor'] for r in factors['cloud']['clouds']]])[clouds(frame)+1]
    cloud = np.clip(hour*(1+.5*(cloud_factor-1)),0,frame.static_capacity.to_numpy())
    return {'p_weather':weather,'p_hour':hour,'p_cloud':cloud,'p':cloud}

def verify_factor(frame: pd.DataFrame, prediction: np.ndarray, mask: np.ndarray, record: dict) -> None:
    monetary = (frame.smp*frame.k).to_numpy()
    active = mask&(prediction>0)&(monetary>0)
    count = int(active.sum())
    days = int((frame.loc[active,'ts'].dt.tz_convert('Asia/Seoul')-pd.Timedelta(hours=1)).dt.normalize().nunique())
    weight = monetary[active]*prediction[active]
    mass = float(weight.sum(dtype=np.float64))
    assert count==record['support_rows'] and days==record['support_days'] and mass==record['weight_mass']
    support = count>=150 and days>=20 and mass>0
    assert record['supported']==support
    if support:
        ratios = frame.y.to_numpy()[active]/prediction[active]
        order = np.argsort(ratios,kind='stable')
        index = int(np.searchsorted(np.cumsum(weight[order],dtype=np.float64),mass/2,side='left'))
        median = float(ratios[order[index]])
        assert median==record['raw_median'] and float(np.clip(median,.85,1.15))==record['factor']
    else:
        assert record['raw_median'] is None and record['factor']==1.

def verify_factors(frame: pd.DataFrame, factors: dict) -> int:
    raw = frame.p_reference.to_numpy()
    temperature = temperature_bins(frame)
    snow = (np.isfinite(frame.extra_wa_snow)&frame.extra_wa_snow.ge(.001)).to_numpy()
    weather = factors['weather']
    assert len(weather['temperature'])==5
    for i,record in enumerate(weather['temperature']):
        verify_factor(frame,raw,temperature==i,record)
    verify_factor(frame,raw,snow,weather['snow'])
    full_temperature = np.array([1.,*[r['factor'] for r in weather['temperature']]])[temperature+1]
    verify_factor(frame,raw*full_temperature,snow,weather['conditional_snow'])
    first = weather_p(frame,weather)
    hour_bin = hours(frame)
    assert len(factors['hour']['hours'])==5
    for i,record in enumerate(factors['hour']['hours']):
        verify_factor(frame,first,hour_bin==i,record)
    second_factor = np.array([r['factor'] for r in factors['hour']['hours']])[hour_bin]
    second = np.clip(first*(1+.5*(second_factor-1)),0,frame.static_capacity.to_numpy())
    cloud_bin = clouds(frame)
    assert len(factors['cloud']['clouds'])==4
    for i,record in enumerate(factors['cloud']['clouds']):
        verify_factor(frame,second,cloud_bin==i,record)
    return 16
