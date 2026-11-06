# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas"]
# ///
# How to run: imported by total_prepare.py, total_score.py and total_checks.py.
"""Capacity-weighted existing-feature summaries and label-free allocation."""
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact frozen feature/score contracts


def summarize(groups: pd.DataFrame, names: list[str]) -> pd.DataFrame:
    assert not groups.duplicated(['ts','grp']).any()
    assert np.isfinite(groups.capacity_kw).all() and groups.capacity_kw.gt(0).all()
    values = groups[names].astype('float64')
    assert not np.isinf(values.to_numpy()).any()
    numerator = values.mul(groups.capacity_kw,axis=0).groupby(groups.ts).sum(min_count=1)
    denominator = values.notna().mul(groups.capacity_kw,axis=0).groupby(groups.ts).sum()
    summary = numerator.div(denominator.where(denominator.gt(0)))
    summary['capacity_kw'] = groups.groupby('ts').capacity_kw.sum()
    return summary.reset_index()


def full_targets(groups: pd.DataFrame) -> pd.DataFrame:
    assert not groups.duplicated(['ts','grp']).any() and np.isfinite(groups.full_energy).all()
    return groups.groupby('ts',as_index=False).full_energy.sum().rename(columns={'full_energy':'full_total_energy'})


def signed_mean(predictions: np.ndarray) -> np.ndarray:
    assert np.isfinite(predictions).all()
    return np.maximum(np.mean(predictions,axis=0,dtype=np.float64),0.)


def allocate(reference: pd.DataFrame, totals: pd.DataFrame, capacities: pd.DataFrame) -> pd.DataFrame:
    assert not reference.duplicated(['ts','grp']).any() and not totals.ts.duplicated().any()
    assert not capacities.duplicated(['ts','grp']).any()
    assert set(reference)=={'ts','grp','p_reference'} and set(totals)=={'ts','p_total'}
    assert np.isfinite(reference.p_reference).all() and reference.p_reference.ge(0).all()
    assert np.isfinite(totals.p_total).all() and totals.p_total.ge(0).all()
    frame = reference.merge(capacities,on=['ts','grp'],how='left',validate='one_to_one')
    frame['capacity_kw'] = frame.capacity_kw.fillna(0.)
    frame = frame.merge(totals,on='ts',how='left',validate='many_to_one')
    cap_sum = frame.groupby('ts').capacity_kw.transform('sum')
    assert frame.p_total.isna().eq(cap_sum.eq(0)).all()
    frame['p_total'] = frame.p_total.fillna(0.)
    ref_sum = frame.groupby('ts').p_reference.transform('sum')
    assert frame.loc[frame.capacity_kw.eq(0),'p_reference'].eq(0).all()
    frame['ratio'] = np.divide(frame.p_reference,ref_sum,out=np.zeros(len(frame)),where=ref_sum.gt(0))
    fallback = ref_sum.eq(0)&cap_sum.gt(0)
    frame.loc[fallback,'ratio'] = frame.loc[fallback,'capacity_kw']/cap_sum[fallback]
    frame['capacity_fallback'] = fallback
    frame['p_new'] = frame.p_total*frame.ratio
    np.testing.assert_allclose(frame.groupby('ts').p_new.sum(),frame.groupby('ts').p_total.first(),rtol=1e-12,atol=1e-8)
    assert frame.loc[frame.capacity_kw.eq(0),'p_new'].eq(0).all()
    return frame
