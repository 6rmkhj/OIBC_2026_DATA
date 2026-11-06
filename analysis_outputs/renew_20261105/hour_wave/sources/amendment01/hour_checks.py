# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: called by hour_run.py --prepare; synthetic data only.
"""Production-function fixtures for fixed bins, support, stage order and isolation."""
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exercise frozen scalar fit/apply API
from cal_math import Factor,fit_factor
from hour_common import OUT,save,now
from hour_math import HourFactors,hour_bins,kst_timestamps,fit,apply

def self_check() -> None:
    hours = [9,10,11,12,13,14,15,16,23,0]
    boundary = pd.DataFrame({'ts':pd.to_datetime([f'2024-01-02 {h:02}:00' for h in hours]).tz_localize('Asia/Seoul')})
    expected = [0,1,1,2,2,3,3,4,4,0]
    np.testing.assert_array_equal(hour_bins(boundary),expected)
    for timezone in ('UTC','Etc/GMT-9'):
        equivalent = boundary.assign(ts=boundary.ts.dt.tz_convert(timezone))
        np.testing.assert_array_equal(hour_bins(equivalent),expected)
    fixed = boundary.assign(ts=pd.to_datetime([f'2024-01-02T{h:02}:00:00+09:00' for h in hours]))
    np.testing.assert_array_equal(hour_bins(fixed),expected)
    for invalid in (boundary.assign(ts=boundary.ts.dt.tz_localize(None)),boundary.assign(ts='malformed'),boundary.assign(ts=pd.NaT)):
        rejected = False
        try:
            kst_timestamps(invalid)
        except AssertionError:
            rejected = True
        assert rejected
    missing = boundary.copy()
    missing.loc[0,'ts'] = pd.NaT
    rejected = False
    try:
        hour_bins(missing)
    except AssertionError:
        rejected = True
    assert rejected
    rows = []
    for day in pd.date_range('2024-01-01',periods=25,tz='Asia/Seoul'):
        for index,hour in enumerate((9,11,13,15,17)):
            for group in range(6):
                rows.append({'ts':day+pd.Timedelta(hours=hour),'grp':str(group),'p_reference':100.,'y':100*[1.2,.8,1.1,.95,1.][index],'smp':2.,'k':3.,'static_capacity':200.})
    frame = pd.DataFrame(rows)
    fitted = fit(frame)
    np.testing.assert_allclose([f.factor for f in fitted.hours],[1.15,.85,1.1,.95,1.],rtol=0,atol=1e-15)
    assert all(f.supported and f.support_rows==150 and f.support_days==25 for f in fitted.hours)
    bin0 = frame.loc[hour_bins(frame)==0].copy()
    below_rows = fit_factor(bin0.iloc[:-1],np.ones(149,dtype=bool))
    assert not below_rows.supported and below_rows.factor==1.
    short_days = bin0.assign(ts=[pd.Timestamp('2024-01-01 09:00',tz='Asia/Seoul')+pd.Timedelta(days=i%19) for i in range(150)])
    insufficient = fit_factor(short_days,np.ones(150,dtype=bool))
    assert insufficient.support_days==19 and not insufficient.supported and insufficient.factor==1.
    for column in ('smp','p_reference'):
        empty = fit_factor(bin0.assign(**{column:0.}),np.ones(150,dtype=bool))
        assert empty.support_rows==0 and empty.support_days==0 and empty.weight_mass==0 and empty.factor==1.
    clock = bin0.assign(ts=[pd.Timestamp('2024-01-01 23:00',tz='Asia/Seoul'),pd.Timestamp('2024-01-02 00:00',tz='Asia/Seoul')]*75)
    assert fit_factor(clock,np.ones(150,dtype=bool)).support_days==1
    weighted = bin0.assign(y=80.)
    weighted.loc[weighted.index[-1],['p_reference','y']] = [20000.,24000.]
    assert fit_factor(weighted,np.ones(150,dtype=bool)).raw_median==1.2
    inputs = boundary.assign(grp='a',p_reference=100.,static_capacity=105.)
    calculated = apply(inputs,fitted)
    expected_factors = np.array([1.15,.85,1.1,.95,1.])[expected]
    np.testing.assert_allclose(calculated.p,np.minimum(105.,100*(1+.5*(expected_factors-1))),rtol=0,atol=1e-13)
    assert calculated.capacity_clipped.iloc[0]
    assert apply(inputs.assign(p_reference=0.),fitted).p.eq(0).all()
    identity = HourFactors(tuple(Factor(None,1.,0,0,0.,False) for _ in range(5)))
    np.testing.assert_array_equal(apply(inputs,identity).p,inputs.p_reference)
    poisoned = inputs.assign(y=np.nan,smp=-np.inf,k=np.inf,wa_temp=object(),extra_wa_snow=object(),raw_factor=999.)
    pd.testing.assert_frame_equal(apply(poisoned,fitted),calculated)
    sequential = apply(inputs.assign(p_reference=100*1.025,static_capacity=200.),fitted)
    assert abs(sequential.p.iloc[0]-(100*1.025*1.075))<1e-12
    save(OUT/'evidence/selfchecks.json',{'passed':True,'utc':now(),'fixtures':['KST bins9/10/11/12/13/14/15/16/23/0','UTC/fixed+09/namedKST equivalent','rejectnaive/malformed/NaT','fiveboundedweightedmedianfactors','150rows25dayssupported','149rowsfallback','19daysfallback','zeroSMP/zeropredfallback','rightclosed23and00sameday','monetarytimespredictionweightedmedian','newstagefixedshrinkonceoncurrentp','staticcapacityclip','nightzero','identityunchanged','adversariallabel/money/weather/oldfactorignored'],'real_scalar_fits':0,'tree_fits':0})
