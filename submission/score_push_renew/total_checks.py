# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: called by total_run.py --prepare.
"""Independent expected-value fixtures for total summaries and allocation."""
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exercise frozen numeric contracts
from total_common import OUT,save,now,decay_multiplier
from total_math import summarize,full_targets,signed_mean,allocate


def self_check() -> None:
    from profile_features import column_mask
    frame = pd.DataFrame({'ts':[1,1,2,2],'grp':['G1','G2','G1','G2'],'capacity_kw':[1.,3.,2.,6.],'x':[2.,6.,4.,8.],'partial':[5.,np.nan,np.nan,7.],'missing':[np.nan]*4,'constant':[1.]*4})
    result = summarize(frame,['x','partial','missing','constant'])
    np.testing.assert_array_equal(result.capacity_kw,[4.,8.])
    np.testing.assert_array_equal(result.x,[5.,7.])
    np.testing.assert_array_equal(result.partial,[5.,7.])
    assert result.missing.isna().all()
    assert column_mask(result,['x','partial','missing','constant'])==['x','partial']
    unseen_eval = result.assign(constant=[1.,2.],missing=[3.,4.])
    assert list(unseen_eval[column_mask(result,['x','partial','missing','constant'])])==['x','partial']
    full = pd.DataFrame({'ts':[1,1,2],'grp':['G1','G2','G1'],'full_energy':[10.,7.,2.]})
    assert full_targets(full).full_total_energy.tolist()==[17.,2.]
    np.testing.assert_array_equal(signed_mean(np.array([[-2.,-4.],[1.,1.],[4.,1.]])),[1.,0.])
    np.testing.assert_allclose(decay_multiplier(np.array([0.,180.]),180),[4/3,2/3],rtol=1e-12)
    reference = pd.DataFrame({'ts':np.repeat([1,2,3,4],2),'grp':['G1','G2']*4,'p_reference':[2.,6.,0.,0.,0.,0.,5.,0.]})
    capacities = pd.DataFrame({'ts':[1,1,2,2,4],'grp':['G1','G2','G1','G2','G1'],'capacity_kw':[9.,1.,1.,3.,2.]})
    totals = pd.DataFrame({'ts':[1,2,4],'p_total':[40.,20.,12.]})
    allocation = allocate(reference,totals,capacities)
    np.testing.assert_array_equal(allocation.p_new,[10.,30.,5.,15.,0.,0.,12.,0.])
    np.testing.assert_array_equal(allocation.ratio,[.25,.75,.25,.75,0.,0.,1.,0.])
    rejected = []
    for bad in [pd.concat([frame,frame.iloc[:1]]),frame.assign(x=[np.inf,6.,4.,8.])]:
        try:
            summarize(bad,['x'])
        except AssertionError:
            rejected.append(True)
    assert rejected==[True,True]
    result.to_parquet(OUT/'evidence/summary_fixture.parquet',index=False)
    allocation.to_parquet(OUT/'evidence/allocation_fixture.parquet',index=False)
    save(OUT/'evidence/selfchecks.json',{'passed':True,'utc':now(),'fixtures':['unequal capacity mean','partialmissing denominator','allmissing NaN','train-only constant/allmissing mask','night-only group target retained','signed mean before clip','half-life normalization','reference share','zero-reference capacity fallback','allnight zero','onegroupnight zero','total conserved','duplicate rejection','infinity rejection'],'synthetic_model_fits':0})
