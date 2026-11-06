# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: smooth_run.py executes fixtures before the fixed comparison.
"""Label-free exact-neighbor smoothing of normalized weather predictions."""
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact frozen key/dtype interfaces
from site_features import normalizer
from smooth_common import APPLICATION

def apply(frame: pd.DataFrame) -> pd.DataFrame:
    assert list(frame)==APPLICATION and not frame.duplicated(['ts','grp']).any()
    assert np.isfinite(frame.p_reference).all() and np.isfinite(frame.static_capacity).all() and frame.static_capacity.gt(0).all()
    assert frame.night.notna().all() and frame.loc[frame.night,'p_reference'].eq(0).all()
    ordered = frame.reset_index(drop=True).sort_values(['grp','ts'])
    inverse = np.zeros(len(ordered),dtype=np.float64)
    day = ~ordered.night.to_numpy(dtype=bool)
    inverse[day] = normalizer(ordered.loc[day,'cosz'].to_numpy())*ordered.loc[day,'capacity_kw'].to_numpy()
    q = pd.Series(np.divide(ordered.p_reference.to_numpy(),inverse,out=np.zeros(len(ordered)),where=np.isfinite(inverse)&(inverse>0)),index=ordered.index)
    valid = ~ordered.night & np.isfinite(ordered.cosz) & ordered.cosz.ge(.15) & np.isfinite(ordered.capacity_kw) & ordered.capacity_kw.gt(0)
    dates = ordered.ts.dt.tz_convert('Asia/Seoul').dt.normalize()
    supported = valid & valid.shift(1,fill_value=False) & valid.shift(-1,fill_value=False)
    supported &= ordered.grp.eq(ordered.grp.shift(1)) & ordered.grp.eq(ordered.grp.shift(-1))
    supported &= dates.eq(dates.shift(1)) & dates.eq(dates.shift(-1))
    supported &= ordered.ts.sub(ordered.ts.shift(1)).eq(pd.Timedelta(hours=1)) & ordered.ts.shift(-1).sub(ordered.ts).eq(pd.Timedelta(hours=1))
    smoothed = q.copy()
    smoothed.loc[supported] = (.25*q.shift(1)+.5*q+.25*q.shift(-1)).loc[supported]
    result = ordered.assign(supported=supported,q_before=q,q_smoothed=smoothed,inverse_kwh=inverse,p_new=ordered.p_reference.to_numpy(copy=True))
    result.loc[supported,'p_new'] = np.clip(smoothed.loc[supported].to_numpy()*inverse[supported.to_numpy()],0,ordered.loc[supported,'static_capacity'].to_numpy())
    result = result.sort_index().reset_index(drop=True)
    assert np.isfinite(result.p_new).all()
    unsupported = ~result.supported.to_numpy()
    assert np.array_equal(result.p_new.to_numpy()[unsupported].view(np.uint64),frame.p_reference.to_numpy()[unsupported].view(np.uint64))
    return result

def self_check() -> list[str]:
    from site_features import normalizer as oracle_normalizer
    times = pd.date_range('2024-01-01 08:00',periods=5,freq='h',tz='Asia/Seoul')
    cosz = np.array([.2,.4,.8,.5,.3])
    capacity = np.array([10.,20.,15.,40.,30.])
    inverse = oracle_normalizer(cosz)*capacity
    base = pd.DataFrame({'ts':times,'grp':['A']*5,'p_reference':2*inverse,'cosz':cosz,'capacity_kw':capacity,'static_capacity':[1000.]*5,'night':[False]*5})
    constant = apply(base)
    np.testing.assert_allclose(constant.p_new,base.p_reference,rtol=1e-14,atol=1e-14)
    np.testing.assert_allclose(constant.q_smoothed,2.,rtol=1e-14)
    impulse = base.assign(p_reference=np.array([0.,0.,1.,0.,0.])*inverse)
    actual = apply(impulse)
    np.testing.assert_array_equal(actual.q_smoothed,[0.,.25,.5,.25,0.])
    assert actual.supported.tolist()==[False,True,True,True,False]
    groups = apply(impulse.assign(grp=['A','A','B','B','B']))
    assert groups.supported.tolist()==[False,False,False,True,False] and groups.p_new.iloc[1]==0.
    boundary = base.iloc[:3].copy()
    boundary['ts'] = pd.date_range('2024-01-01 23:00',periods=3,freq='h',tz='Asia/Seoul')
    assert not apply(boundary).supported.any()
    gap = impulse.copy()
    gap['ts'] = pd.to_datetime(['2024-01-01 '+t for t in ('08:00','09:00','11:00','12:00','13:00')]).tz_localize('Asia/Seoul')
    assert apply(gap).supported.tolist()==[False,False,False,True,False]
    assert not apply(base.assign(cosz=[.15,.15,.149999,.15,.15])).supported.any()
    assert apply(base.assign(cosz=.15)).supported.tolist()==[False,True,True,True,False]
    night = base.copy()
    night.loc[2,['p_reference','cosz','capacity_kw','night']] = [0.,np.nan,np.nan,True]
    at_night = apply(night)
    assert not at_night.supported.any() and at_night.p_new.iloc[2]==at_night.inverse_kwh.iloc[2]==at_night.q_before.iloc[2]==0.
    capped = apply(impulse.assign(static_capacity=1.))
    assert capped.p_new.iloc[2]==1.
    labelled = impulse.assign(y=np.arange(5),smp=-100.,k=999.)
    pd.testing.assert_frame_equal(apply(labelled[APPLICATION]),actual,check_exact=True)
    rejected = False
    try:
        apply(pd.concat([base,base.iloc[[0]]],ignore_index=True))
    except AssertionError:
        rejected = True
    assert rejected
    return ['constant_normalized_cf_changing_geometry_capacity','exact_impulse_kernel','groups_no_bleed','same_KST_day_only','missing_hour_no_interpolation','cosz_threshold_inclusive','night_zero','unsupported_bitwise_identity','static_capacity_clip','labels_excluded','duplicate_key_rejected']
