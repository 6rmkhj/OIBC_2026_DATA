# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: synthetic checks before release; coefficient fits only after release.
"""Fixed train-only site quantiles, capacity-weighted gains and physical scaling."""
from dataclasses import dataclass
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen site/group contracts
from yield_common import coefficients

@dataclass(frozen=True,slots=True)
class SiteGain:
    site_id: str
    observed_rows: int
    clear_rows: int
    clear_days: int
    raw_q90: float | None
    raw_relative: float | None
    shrink: float
    gain: float
    fallback_reason: str

@dataclass(frozen=True,slots=True)
class YieldFit:
    global_q90: float
    clear_rows: int
    sites: tuple[SiteGain,...]


def haurwitz(cosz: np.ndarray) -> np.ndarray:
    positive = np.maximum(cosz,0.)
    exponent = np.divide(-.059,positive,out=np.zeros_like(positive,dtype=float),where=positive>0)
    return 1.098*positive*np.exp(exponent)


def normalizer(cosz: np.ndarray, gain: np.ndarray) -> np.ndarray:
    assert np.isfinite(gain).all() and (gain>0).all()
    return np.maximum(.05,haurwitz(cosz)*gain)


def clear_mask(frame: pd.DataFrame) -> np.ndarray:
    values = frame[['cf','cosz','wa_cloud','wb_cloud']].to_numpy()
    return np.isfinite(values).all(axis=1)&frame.cf.ge(0).to_numpy()&frame.cosz.gt(.5).to_numpy()&frame.wa_cloud.between(0,20,inclusive='left').to_numpy()&frame.wb_cloud.between(0,20,inclusive='left').to_numpy()


def fit_gains(frame: pd.DataFrame, site_ids: list[str]) -> YieldFit:
    assert set(frame.site_id.astype(str))<=set(site_ids)
    clear = frame.loc[clear_mask(frame)].copy()
    assert len(clear)>0
    clear['ratio'] = clear.cf.to_numpy()/haurwitz(clear.cosz.to_numpy())
    global_q90 = float(np.quantile(clear.ratio.to_numpy(),.9,method='linear'))
    assert np.isfinite(global_q90) and global_q90>0
    records = []
    for site in site_ids:
        rows = clear.loc[clear.site_id.eq(site)]
        count = len(rows)
        days = int((rows.ts-pd.Timedelta(hours=1)).dt.normalize().nunique())
        q90 = float(np.quantile(rows.ratio.to_numpy(),.9,method='linear')) if count else None
        q90 = q90 if q90 is not None and np.isfinite(q90) else None
        relative = q90/global_q90 if q90 is not None else None
        shrink = count/(count+200)
        supported = count>=100 and days>=20 and q90 is not None and np.isfinite(q90) and q90>0
        if supported:
            assert relative is not None
            gain = float(np.clip(1+shrink*(relative-1),.5,1.5))
        else:
            gain = 1.
        reason = 'supported' if supported else ('no_clear_rows' if count==0 else 'insufficient_rows' if count<100 else 'insufficient_days' if days<20 else 'nonpositive_or_nonfinite_q90')
        records.append(SiteGain(site,int(frame.site_id.eq(site).sum()),count,days,q90,relative,shrink,gain,reason))
    return YieldFit(global_q90,len(clear),tuple(records))


def group_gains(sites: pd.DataFrame, fitted: YieldFit) -> pd.DataFrame:
    assert not sites.duplicated(['ts','site_id']).any()
    assert np.isfinite(sites.capacity_kw).all() and sites.capacity_kw.gt(0).all()
    frame = sites[['ts','grp','capacity_kw']].copy()
    gain = sites.site_id.astype(str).map({r.site_id:r.gain for r in fitted.sites}).fillna(1.)
    frame['yield_capacity'] = frame.capacity_kw*gain
    result = frame.groupby(['ts','grp'],as_index=False,observed=True)[['capacity_kw','yield_capacity']].sum()
    result['group_gain'] = result.yield_capacity/result.capacity_kw
    assert np.isfinite(result.group_gain).all() and result.group_gain.between(.5-1e-12,1.5+1e-12).all()
    return result


def component(frame: pd.DataFrame, predictions: np.ndarray) -> pd.DataFrame:
    from cal_math import apply
    assert set(frame)=={'ts','grp','wa_temp','extra_wa_snow','static_capacity'}
    assert predictions.shape==(3,len(frame)) and np.isfinite(predictions).all()
    mean = np.mean(predictions,axis=0,dtype=np.float64)
    clipped = np.maximum(0,np.minimum(frame.static_capacity.to_numpy(),mean))
    result = apply(frame.assign(p_reference=clipped),coefficients(),'temperature_then_snow')
    result['signed_seed_mean'] = mean
    result['component_before_calibration'] = clipped
    return result.rename(columns={'p':'p_new'})
