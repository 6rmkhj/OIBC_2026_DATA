# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: synthetic self_check before execution; imported by sky_run.py.
"""Four fixed finite-cloud bins and one new primary-only calibration stage."""
from dataclasses import dataclass
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- existing cal_math fit_factor API
from cal_math import Factor,fit_factor

@dataclass(frozen=True,slots=True)
class CloudFactors:
    clouds: tuple[Factor,...]

def cloud_bins(frame: pd.DataFrame) -> np.ndarray:
    cloud = frame.wb_cloud.to_numpy(dtype=np.float64)
    bins = np.full(len(frame),-1,dtype=np.int64)
    finite = np.isfinite(cloud)
    bins[finite] = np.searchsorted([20.,50.,80.],cloud[finite],side='right')
    return bins

def fit(frame: pd.DataFrame) -> CloudFactors:
    assert isinstance(frame.ts.dtype,pd.DatetimeTZDtype) and frame.ts.notna().all()
    primary = frame[['ts','p_reference','y','smp','k']].copy()
    primary['ts'] = primary.ts.dt.tz_convert('Asia/Seoul')
    bins = cloud_bins(frame)
    return CloudFactors(tuple(fit_factor(primary,bins==i) for i in range(4)))

def apply(frame: pd.DataFrame, fitted: CloudFactors) -> pd.DataFrame:
    result = frame[['ts','grp','p_reference','wb_cloud','static_capacity']].copy()
    bins = cloud_bins(result)
    assert len(fitted.clouds)==4
    factors = np.array([1.,*[item.factor for item in fitted.clouds]])
    assert np.isfinite(factors).all() and ((factors>=.85)&(factors<=1.15)).all()
    assert np.isfinite(result.p_reference).all() and result.p_reference.ge(0).all()
    assert np.isfinite(result.static_capacity).all() and result.static_capacity.gt(0).all()
    assert (result.p_reference<=result.static_capacity+1e-8).all()
    result['cloud_bin'] = bins
    result['bounded_cloud_factor'] = factors[bins+1]
    result['effective_cloud_factor'] = 1+.5*(result.bounded_cloud_factor-1)
    result['before_capacity_clip'] = result.p_reference*result.effective_cloud_factor
    result['p'] = np.maximum(0,np.minimum(result.static_capacity,result.before_capacity_clip))
    result['capacity_clipped'] = result.before_capacity_clip>result.static_capacity
    assert result.loc[result.p_reference.eq(0),'p'].eq(0).all()
    return result

def self_check() -> list[str]:
    cloud = [-1.,0.,19.999,20.,49.999,50.,79.999,80.,100.,100.00000000000001,np.nan,np.inf,-np.inf]
    boundary = pd.DataFrame({'wb_cloud':cloud})
    np.testing.assert_array_equal(cloud_bins(boundary),[0,0,0,1,1,2,2,3,3,3,-1,-1,-1])
    rows = []
    for day in pd.date_range('2024-01-01',periods=25,tz='Asia/Seoul'):
        for i,value in enumerate((10.,30.,60.,90.)):
            for grp in range(6):
                rows.append({'ts':day+pd.Timedelta(hours=12),'grp':str(grp),'p_reference':100.,'y':100*[1.2,.8,1.1,.95][i],'smp':2.,'k':3.,'wb_cloud':value,'static_capacity':200.})
    frame = pd.DataFrame(rows)
    fitted = fit(frame)
    np.testing.assert_allclose([item.factor for item in fitted.clouds],[1.15,.85,1.1,.95],rtol=0,atol=1e-15)
    assert all(item.supported and item.support_rows==150 and item.support_days==25 for item in fitted.clouds)
    first = frame.loc[cloud_bins(frame)==0].copy()
    unsupported = fit_factor(first.iloc[:-1],np.ones(149,dtype=bool))
    assert not unsupported.supported and unsupported.factor==1.
    short = first.assign(ts=[pd.Timestamp('2024-01-01 12:00',tz='Asia/Seoul')+pd.Timedelta(days=i%19) for i in range(150)])
    insufficient = fit_factor(short,np.ones(150,dtype=bool))
    assert insufficient.support_days==19 and not insufficient.supported and insufficient.factor==1.
    for column in ('smp','p_reference'):
        empty = fit_factor(first.assign(**{column:0.}),np.ones(150,dtype=bool))
        assert empty.support_rows==0 and empty.support_days==0 and empty.weight_mass==0 and empty.factor==1.
    right_closed = first.assign(ts=[pd.Timestamp('2024-01-01 23:00',tz='Asia/Seoul'),pd.Timestamp('2024-01-02 00:00',tz='Asia/Seoul')]*75)
    assert fit_factor(right_closed,np.ones(150,dtype=bool)).support_days==1
    weighted = first.assign(y=80.)
    weighted.loc[weighted.index[-1],['p_reference','y']] = [10000.,12000.]
    assert 149*100*2*3==89400 and 10000*2*3==60000
    low = fit_factor(weighted,np.ones(150,dtype=bool))
    assert low.raw_median==.8 and low.factor==.85
    weighted.loc[weighted.index[-1],['p_reference','y']] = [20000.,24000.]
    assert 20000*2*3==120000 and 120000>89400
    high = fit_factor(weighted,np.ones(150,dtype=bool))
    assert high.raw_median==1.2 and high.factor==1.15
    missing = fit(frame.assign(wb_cloud=np.nan))
    assert all(not item.supported and item.factor==1. for item in missing.clouds)
    inputs = boundary.assign(ts=pd.Timestamp('2024-01-01 12:00',tz='Asia/Seoul'),grp='g',p_reference=100.,static_capacity=105.)
    result = apply(inputs,fitted)
    expected = np.array([1.15,1.15,1.15,.85,.85,1.1,1.1,.95,.95,.95,1.,1.,1.])
    np.testing.assert_allclose(result.p,np.minimum(105.,100*(1+.5*(expected-1))),rtol=0,atol=1e-13)
    assert result.capacity_clipped.iloc[0]
    assert apply(inputs.assign(p_reference=0.),fitted).p.eq(0).all()
    pd.testing.assert_frame_equal(result,apply(inputs.assign(y=np.nan,smp=-np.inf,k=np.inf,wa_temp=object(),effective_hour_factor=999.),fitted))
    staged = apply(inputs.assign(p_reference=102.5,static_capacity=200.),fitted)
    assert abs(staged.p.iloc[0]-102.5*1.075)<1e-12
    identity = CloudFactors(tuple(Factor(None,1.,0,0,0.,False) for _ in range(4)))
    np.testing.assert_array_equal(apply(inputs,identity).p,inputs.p_reference)
    return ['cloud20/50/80boundaries','finiteoutofrange100.00000000000001retained','nonfiniteidentity','fourboundedfactors','150rows25dayssupport','149rows/19daysfallback','zeroSMP/zeropredfallback','rightclosedday','explicitweightedmajorities89400vs60000and120000','newstageshrinkonce','adversariallabelsignored','capacityclip','nightzero','identity']
