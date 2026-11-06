# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: imported by weight_prepare.py and weight_score.py.
"""Mass-preserving training weights and exactly-once frozen calibration."""
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen inference calibration contract
from weight_common import coefficients


def normalized_weights(base: np.ndarray, modifier: np.ndarray) -> np.ndarray:
    assert base.shape==modifier.shape and np.isfinite(base).all() and np.isfinite(modifier).all()
    assert (base>0).all() and (modifier>=0).all()
    total = float(np.sum(base*modifier,dtype=np.float64))
    assert np.isfinite(total) and total>0
    result = base*modifier*(np.sum(base,dtype=np.float64)/total)
    assert np.isfinite(result).all() and (result>=0).all()
    np.testing.assert_allclose(result.sum(),base.sum(),rtol=1e-12)
    np.testing.assert_array_equal(result[modifier==0],0.)
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
