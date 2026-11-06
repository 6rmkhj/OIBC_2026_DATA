# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: called by weight_run.py --prepare.
"""Expected-value checks for weight mass, zeros and one calibration application."""
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact frozen calibration fixtures
from weight_common import OUT,coefficients,decay_multiplier,save,now
from weight_math import normalized_weights,component
from profile_features import column_mask


def self_check() -> None:
    history = pd.DataFrame({'varying':[0.,1.],'constant':[1.,1.]})
    future = history.assign(constant=[1.,2.])
    assert list(future[column_mask(history,['varying','constant'])])==['varying']
    base = np.array([1.,2.,3.])
    modifier = np.array([1.,3.,0.])
    weights = normalized_weights(base,modifier)
    np.testing.assert_allclose(weights,[6/7,36/7,0.],rtol=1e-12)
    np.testing.assert_allclose(normalized_weights(base,modifier*100),weights,rtol=1e-12)
    np.testing.assert_allclose(weights.sum(),base.sum(),rtol=1e-12)
    assert weights[2]==0
    rejected = []
    for invalid in [np.zeros(3),np.array([1.,-1.,0.]),np.array([1.,np.nan,0.])]:
        try:
            normalized_weights(base,invalid)
        except AssertionError:
            rejected.append(True)
    assert rejected==[True]*3
    np.testing.assert_allclose(decay_multiplier(np.array([0.,180.]),180),[4/3,2/3])
    times = pd.to_datetime(['2023-06-01 00:00+09:00','2023-06-01 01:00+09:00'])
    np.testing.assert_array_equal(times<=pd.Timestamp('2023-06-01',tz='Asia/Seoul'),[True,False])
    frame = pd.DataFrame({'ts':pd.date_range('2024-01-01',periods=3,freq='h',tz='Asia/Seoul'),'grp':['G1']*3,'wa_temp':[15.,np.nan,0.],'extra_wa_snow':[0.,np.nan,0.],'static_capacity':[100.]*3})
    prediction = np.array([[-2.,500.,-4.],[1.,200.,1.],[4.,200.,1.]])
    result = component(frame,prediction)
    np.testing.assert_array_equal(result.component_before_calibration,[1.,100.,0.])
    expected_factor = 1+.5*(coefficients().temperature[2].factor-1)
    np.testing.assert_array_equal(result.p_new,[expected_factor,100.,0.])
    assert result.p_new.iloc[0]!=expected_factor**2
    result.to_parquet(OUT/'evidence/component_fixture.parquet',index=False)
    save(OUT/'evidence/selfchecks.json',{'passed':True,'utc':now(),'fixtures':['train-only constant mask','mass preserving formula','modifier-scale invariance','zero modifier row retained','allzero/negative/nonfinite rejection','half-life mean normalization','cutoff exactboundary','mean signed before staticcapclip','frozen calibration exactly once','missingconditions identity','night zero'],'real_model_fits':0})
