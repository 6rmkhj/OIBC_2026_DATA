# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: called by cal_run.py --prepare before real calibration release.
"""Synthetic expected-value checks of weighting, support and application boundaries."""
from dataclasses import replace
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact metric-related fixtures
from cal_common import OUT,save,now
from cal_math import Calibration,conditions,fit_factor,fit,apply


def self_check() -> None:
    frame = pd.DataFrame({'ts':pd.date_range('2023-01-01 01:00',periods=150,freq='4h',tz='Asia/Seoul'),'grp':['G1']*150,'p_reference':np.ones(150),'y':np.r_[np.full(149,.9),1.1],'smp':np.r_[np.full(149,.01),100.],'k':np.ones(150),'wa_temp':np.full(150,15.),'extra_wa_snow':np.ones(150),'static_capacity':np.full(150,200.)})
    factor = fit_factor(frame,np.ones(150,dtype=bool))
    assert factor.supported and factor.raw_median==1.1 and np.median(frame.y)==.9
    scaled = fit_factor(frame.assign(smp=frame.smp*7),np.ones(150,dtype=bool))
    assert scaled.factor==factor.factor and scaled.raw_median==factor.raw_median
    extra = pd.concat([frame,frame.iloc[:2].assign(p_reference=[0.,1.],smp=[1.,0.],y=999.)],ignore_index=True)
    assert fit_factor(extra,np.ones(152,dtype=bool))==factor
    for unsupported in [frame.iloc[:149],frame.assign(ts=frame.ts.iloc[0]),frame.assign(smp=0.)]:
        result = fit_factor(unsupported,np.ones(len(unsupported),dtype=bool))
        assert not result.supported and result.factor==1.
    boundaries = pd.DataFrame({'wa_temp':[-1.,0.,9.999,10.,19.99,20.,29.99,30.,np.nan],'extra_wa_snow':[0.,.000999,.001,np.nan,0.,0.,0.,0.,np.nan]})
    bins,snow = conditions(boundaries)
    np.testing.assert_array_equal(bins,[0,1,1,2,2,3,3,4,-1])
    np.testing.assert_array_equal(snow,[False,False,True,False,False,False,False,False,False])
    sequential = frame.assign(p_reference=100.,y=110.,smp=1.)
    coefficients = fit(sequential)
    assert coefficients.temperature[2].factor==1.1
    np.testing.assert_allclose(coefficients.conditional_snow.factor,1.,rtol=1e-12)
    applied = apply(sequential,coefficients,'temperature_then_snow')
    np.testing.assert_allclose(applied.p,105.,rtol=1e-12)
    missing = sequential.iloc[:2].assign(wa_temp=np.nan,extra_wa_snow=np.nan,p_reference=[0.,100.])
    np.testing.assert_array_equal(apply(missing,coefficients,'temperature_then_snow').p,[0.,100.])
    high = replace(factor,factor=1.15)
    upper = Calibration((high,)*5,high,high)
    capped = apply(sequential.assign(static_capacity=106.),upper,'temperature_then_snow')
    np.testing.assert_allclose(capped.raw_factor,1.3225)
    np.testing.assert_allclose(capped.effective_factor,1.075)
    np.testing.assert_array_equal(capped.p,106.)
    assert capped.capacity_clipped.all()
    pd.testing.assert_frame_equal(apply(sequential.drop(columns=['y','smp','k']),coefficients,'temperature_then_snow'),apply(sequential.assign(y=np.nan,smp=-999.,k=-99.),coefficients,'temperature_then_snow'))
    rejected = False
    try:
        apply(sequential.assign(p_reference=-1.),coefficients,'snow_only')
    except AssertionError:
        rejected = True
    assert rejected
    right_closed = frame.copy()
    right_closed['ts'] = pd.to_datetime(['2023-01-01 23:00+09:00','2023-01-02 00:00+09:00']*75).tz_convert('Asia/Seoul')
    assert fit_factor(right_closed,np.ones(150,dtype=bool)).support_days==1
    applied.to_parquet(OUT/'evidence/sequential_fixture.parquet',index=False)
    save(OUT/'evidence/selfchecks.json',{'passed':True,'utc':now(),'fixtures':['weighted median differs from unweighted','positive mass scaling invariant','zero P and SMP ignored','insufficient rows identity','insufficient days identity','allzero weights identity','right-closed calendar support days','exact temperature boundaries','snow threshold and NaN','sequential adjusted primary denominator','combined bound then shrink once','static capacity cap','allnight zero','signed reference rejection','adversarial labels leave application identical'],'actual_calibration_fits':0})
