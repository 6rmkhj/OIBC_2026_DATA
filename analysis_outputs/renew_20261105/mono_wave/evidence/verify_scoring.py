# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: imported by verify_terminal.py; no fitting.
"""Independent signed ensemble, old calibration stages and primary blend algebra."""
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact existing timestamp and metric arithmetic

def component(inputs: pd.DataFrame, seeds: np.ndarray, originals: dict) -> dict[str,np.ndarray]:
    capacity = inputs.static_capacity.to_numpy()
    mean = np.mean(seeds,axis=0,dtype=np.float64)
    clipped = np.clip(mean,0,capacity)
    temp = inputs.wa_temp.to_numpy()
    finite = np.isfinite(temp)
    bins = np.full(len(temp),-1,dtype=np.int64)
    bins[finite] = np.select([temp[finite]<0,temp[finite]<10,temp[finite]<20,temp[finite]<30],[0,1,2,3],default=4)
    weather = originals['weather']
    temperature_factor = np.array([1.,*[f['factor'] for f in weather['temperature']]])[bins+1]
    snow = np.isfinite(inputs.extra_wa_snow)&inputs.extra_wa_snow.ge(.001)
    weather_factor = np.clip(temperature_factor*np.where(snow,weather['conditional_snow']['factor'],1.),.85,1.15)
    p_weather = np.clip(clipped*(1+.5*(weather_factor-1)),0,capacity)
    hour = inputs.ts.dt.tz_convert('Asia/Seoul').dt.hour.to_numpy()
    hour_bins = np.select([hour<10,hour<12,hour<14,hour<16],[0,1,2,3],default=4)
    hour_factor = np.array([f['factor'] for f in originals['hour']['hours']])[hour_bins]
    p_hour = np.clip(p_weather*(1+.5*(hour_factor-1)),0,capacity)
    cloud = inputs.wb_cloud.to_numpy()
    finite = np.isfinite(cloud)
    cloud_bins = np.full(len(cloud),-1,dtype=np.int64)
    cloud_bins[finite] = np.select([cloud[finite]<20,cloud[finite]<50,cloud[finite]<80],[0,1,2],default=3)
    cloud_factor = np.array([1.,*[f['factor'] for f in originals['cloud']['clouds']]])[cloud_bins+1]
    p_new = np.clip(p_hour*(1+.5*(cloud_factor-1)),0,capacity)
    return {'signed_seed_mean':mean,'p_component':clipped,'p_weather':p_weather,'p_hour':p_hour,'p_new':p_new}

def primary_alpha(frame: pd.DataFrame) -> float:
    delta = frame.p_new.to_numpy()-frame.p_reference.to_numpy()
    cost = (frame.smp*frame.k).to_numpy()
    active = (delta!=0)&(cost>0)
    if not active.any():
        return 0.
    crossing = (frame.y.to_numpy()[active]-frame.p_reference.to_numpy()[active])/delta[active]
    mass = cost[active]*np.abs(delta[active])
    order = np.argsort(crossing)
    position = int(np.searchsorted(np.cumsum(mass[order]),mass.sum()/2))
    return float(np.clip(crossing[order[position]],0,1))

def metrics(frame: pd.DataFrame, name: str):
    cost = frame.smp*frame.k
    w = float((cost*(frame[name]-frame.y).abs()).sum())
    revenue = float((frame.smp*frame.y).sum())
    return {'W':w,'W_pct':100*w/float((cost*frame.y).sum()),'revenue':revenue,'S':revenue-.1*w,'rows':len(frame)}
