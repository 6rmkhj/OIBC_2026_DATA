# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: imported by cal_run.py and cal_checks.py.
"""Primary-only bounded weighted-median fits and strictly label-free application."""
from dataclasses import dataclass
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen scoring contract

@dataclass(frozen=True,slots=True)
class Factor:
    raw_median: float | None
    factor: float
    support_rows: int
    support_days: int
    weight_mass: float
    supported: bool

@dataclass(frozen=True,slots=True)
class Calibration:
    temperature: tuple[Factor,...]
    snow: Factor
    conditional_snow: Factor


def conditions(frame: pd.DataFrame) -> tuple[np.ndarray,np.ndarray]:
    temp = frame.wa_temp.to_numpy(dtype=np.float64)
    snow = frame.extra_wa_snow.to_numpy(dtype=np.float64)
    bins = np.full(len(frame),-1,dtype=np.int64)
    valid = np.isfinite(temp)
    bins[valid] = np.searchsorted([0.,10.,20.,30.],temp[valid],side='right')
    return bins,np.isfinite(snow)&(snow>=.001)


def fit_factor(frame: pd.DataFrame, mask: np.ndarray) -> Factor:
    p,y = frame.p_reference.to_numpy(),frame.y.to_numpy()
    monetary = (frame.smp*frame.k).to_numpy()
    assert np.isfinite(p).all() and (p>=0).all() and np.isfinite(y).all()
    assert np.isfinite(monetary).all() and (monetary>=0).all()
    active = mask&(p>0)&(monetary>0)
    rows = int(active.sum())
    days = int((frame.loc[active,'ts']-pd.Timedelta(hours=1)).dt.normalize().nunique())
    weights = monetary[active]*p[active]
    mass = float(weights.sum(dtype=np.float64))
    assert np.isfinite(mass)
    if rows<150 or days<20 or mass<=0:
        return Factor(None,1.,rows,days,mass,False)
    ratios = y[active]/p[active]
    assert np.isfinite(ratios).all()
    order = np.argsort(ratios,kind='stable')
    index = np.searchsorted(np.cumsum(weights[order],dtype=np.float64),mass/2,side='left')
    median = float(ratios[order[index]])
    return Factor(median,float(np.clip(median,.85,1.15)),rows,days,mass,True)


def fit(frame: pd.DataFrame) -> Calibration:
    bins,snow = conditions(frame)
    temperature = tuple(fit_factor(frame,bins==i) for i in range(5))
    temperature_factor = np.array([1.,*[f.factor for f in temperature]])[bins+1]
    adjusted = frame.assign(p_reference=frame.p_reference*temperature_factor)
    return Calibration(temperature,fit_factor(frame,snow),fit_factor(adjusted,snow))


def apply(frame: pd.DataFrame, fitted: Calibration, arm: str) -> pd.DataFrame:
    result = frame[['ts','grp','p_reference','wa_temp','extra_wa_snow','static_capacity']].copy()
    assert np.isfinite(result.p_reference).all() and result.p_reference.ge(0).all()
    assert np.isfinite(result.static_capacity).all() and result.static_capacity.gt(0).all()
    assert (result.p_reference<=result.static_capacity+1e-8).all()
    bins,snow = conditions(result)
    temperature = np.array([1.,*[f.factor for f in fitted.temperature]])[bins+1]
    recipes = {'snow_only':np.where(snow,fitted.snow.factor,1.),'temperature_only':temperature,'temperature_then_snow':temperature*np.where(snow,fitted.conditional_snow.factor,1.)}
    result['temperature_bin'] = bins
    result['snow_condition'] = snow
    result['raw_factor'] = recipes[arm]
    result['bounded_factor'] = np.clip(result.raw_factor,.85,1.15)
    result['effective_factor'] = 1+.5*(result.bounded_factor-1)
    result['before_capacity_clip'] = result.p_reference*result.effective_factor
    result['p'] = np.maximum(0,np.minimum(result.static_capacity,result.before_capacity_clip))
    result['capacity_clipped'] = result.before_capacity_clip>result.static_capacity
    assert result.loc[result.p_reference.eq(0),'p'].eq(0).all()
    return result
