# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: imported by hour_run.py and hour_checks.py.
"""One bounded primary-only hour stage, applied to already calibrated p."""
from dataclasses import dataclass
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen scalar calibration API
from cal_math import Factor,fit_factor

@dataclass(frozen=True,slots=True)
class HourFactors:
    hours: tuple[Factor,...]

def kst_timestamps(frame: pd.DataFrame) -> pd.Series:
    assert isinstance(frame.ts.dtype,pd.DatetimeTZDtype),'Timezone-aware timestamps required'
    assert frame.ts.notna().all(),'Missing timestamps rejected'
    return frame.ts.dt.tz_convert('Asia/Seoul')

def hour_bins(frame: pd.DataFrame) -> np.ndarray:
    return np.searchsorted([10,12,14,16],kst_timestamps(frame).dt.hour.to_numpy(),side='right')

def fit(frame: pd.DataFrame) -> HourFactors:
    bins = hour_bins(frame)
    primary = frame[['ts','p_reference','y','smp','k']].copy()
    primary['ts'] = kst_timestamps(frame)
    return HourFactors(tuple(fit_factor(primary,bins==i) for i in range(5)))

def apply(frame: pd.DataFrame, fitted: HourFactors) -> pd.DataFrame:
    result = frame[['ts','grp','p_reference','static_capacity']].copy()
    bins = hour_bins(result)
    assert len(fitted.hours)==5
    factors = np.array([f.factor for f in fitted.hours])
    assert np.isfinite(factors).all() and ((factors>=.85)&(factors<=1.15)).all()
    assert np.isfinite(result.p_reference).all() and result.p_reference.ge(0).all()
    assert np.isfinite(result.static_capacity).all() and result.static_capacity.gt(0).all()
    assert (result.p_reference<=result.static_capacity+1e-8).all()
    result['hour_bin'] = bins
    result['bounded_hour_factor'] = factors[bins]
    result['effective_hour_factor'] = 1+.5*(result.bounded_hour_factor-1)
    result['before_capacity_clip'] = result.p_reference*result.effective_hour_factor
    result['p'] = np.maximum(0,np.minimum(result.static_capacity,result.before_capacity_clip))
    result['capacity_clipped'] = result.before_capacity_clip>result.static_capacity
    assert result.loc[result.p_reference.eq(0),'p'].eq(0).all()
    return result
