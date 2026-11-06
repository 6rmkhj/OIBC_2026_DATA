# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: yield_run.py --prepare (synthetic data ONLY).
"""Synthetic exact-value tests of the single preregistered yield formula."""
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exercise production numeric contracts
from site_features import normalizer as old_normalizer
from profile_features import column_mask
from yield_common import OUT,coefficients,save,now
from yield_math import fit_gains,clear_mask,group_gains,haurwitz,normalizer,component


def fixture(site: str, values: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({'ts':pd.date_range('2023-01-01 01:00',periods=len(values),freq='4h',tz='Asia/Seoul'),'site_id':[site]*len(values),'cf':values,'cosz':np.ones(len(values)),'wa_cloud':np.zeros(len(values)),'wb_cloud':np.zeros(len(values)),'capacity_kw':np.ones(len(values))})


def self_check() -> None:
    quantile = fit_gains(fixture('Q',np.array([0.,1.,2.,10.])),['Q'])
    np.testing.assert_allclose(quantile.global_q90,7.6/haurwitz(np.array([1.]))[0],rtol=1e-12)
    sample = pd.concat([fixture('A',np.full(150,.5)),fixture('B',np.ones(150)),fixture('Z',np.zeros(150))],ignore_index=True)
    fitted = fit_gains(sample,['A','B','Z','U'])
    by_site = {r.site_id:r for r in fitted.sites}
    np.testing.assert_allclose(by_site['A'].gain,1+(150/350)*(.5-1),rtol=1e-12)
    assert by_site['Z'].gain==by_site['U'].gain==1 and by_site['Z'].fallback_reason=='nonpositive_or_nonfinite_q90'
    assert by_site['U'].fallback_reason=='no_clear_rows' and quantile.sites[0].gain==1
    few_days = fixture('D',np.ones(150)).assign(ts=pd.date_range('2023-01-01 01:00',periods=150,freq='min',tz='Asia/Seoul'))
    assert fit_gains(few_days,['D']).sites[0].fallback_reason=='insufficient_days'
    clipped = fit_gains(pd.concat([fixture('B',np.ones(2000)),fixture('L',np.full(1000,.01)),fixture('H',np.full(100,10.))],ignore_index=True),['B','L','H'])
    assert [r.gain for r in clipped.sites]==[1.,.5,1.5]
    invalid = fixture('I',np.array([0.,-1.,np.nan,np.inf]))
    np.testing.assert_array_equal(clear_mask(invalid),[True,False,False,False])
    cloud = fixture('C',np.ones(4)).assign(wa_cloud=[-1.,20.,0.,0.],wb_cloud=[0.,0.,np.nan,0.],cosz=[1.,1.,1.,.5])
    assert not clear_mask(cloud).any()
    rejected = False
    try:
        fit_gains(fixture('Z',np.zeros(100)),['Z'])
    except AssertionError:
        rejected = True
    assert rejected
    active = pd.DataFrame({'ts':[1,1],'grp':['G1','G1'],'site_id':['A','unknown'],'capacity_kw':[1.,3.]})
    grouped = group_gains(active,fitted)
    np.testing.assert_allclose(grouped.group_gain,[(by_site['A'].gain+3)/4],rtol=1e-12)
    cosz = np.array([-.1,0.,.001,.01,.05,.1,.5,1.],dtype=np.float32)
    np.testing.assert_array_equal(normalizer(cosz,np.ones(len(cosz))),old_normalizer(cosz))
    assert normalizer(np.array([.01]),np.array([1.5]))[0]==.05
    assert old_normalizer(np.array([.01]))[0]*1.5>.05
    history = pd.DataFrame({'varying':[0.,1.],'constant':[1.,1.]})
    assert column_mask(history,['varying','constant'])==['varying']
    boundary = pd.to_datetime(['2023-06-01 00:00+09:00','2023-06-01 01:00+09:00'])
    np.testing.assert_array_equal(boundary<=pd.Timestamp('2023-06-01',tz='Asia/Seoul'),[True,False])
    frame = pd.DataFrame({'ts':pd.date_range('2024-01-01',periods=3,freq='h',tz='Asia/Seoul'),'grp':['G1']*3,'wa_temp':[15.,np.nan,0.],'extra_wa_snow':[0.,np.nan,0.],'static_capacity':[100.]*3})
    result = component(frame,np.array([[-2.,500.,-4.],[1.,200.,1.],[4.,200.,1.]]))
    expected_factor = 1+.5*(coefficients().temperature[2].factor-1)
    np.testing.assert_array_equal(result.component_before_calibration,[1.,100.,0.])
    np.testing.assert_array_equal(result.p_new,[expected_factor,100.,0.])
    result.to_parquet(OUT/'evidence/component_fixture.parquet',index=False)
    save(OUT/'evidence/selfchecks.json',{'passed':True,'utc':now(),'fixtures':['linearquantile','shrinkn/(n+200)','unsupportedrows/days','zero/nonfinite/negativeCF handling','globalnonpositive rejection','unknownsiteidentity','gainclipbothends','capacityweightedgain','neutralgainexactoldnormalizer','twilightfloorAFTERgain','cutoffboundary','train-onlymask','signedmeanbeforeclip','frozencalibrationonce'],'real_site_gain_fits':0,'real_tree_fits':0})
