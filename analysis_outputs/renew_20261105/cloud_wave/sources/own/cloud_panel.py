# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow"]
# ///
"""Forecast-only complete station-hour panels and chronological self-checks."""
from cloud_common import OUT, RAW, CUTOFFS, PROVIDERS, save, digest, block_indices
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen profile interface
import pyarrow.parquet as pq

def features(keys: pd.DataFrame, forecasts: pd.DataFrame, provider: str) -> pd.DataFrame:
    station = f'{provider}_station'
    columns = [c for c in forecasts if c not in (station,'ts','round')]
    assert all(c.startswith(provider+'_') for c in columns)
    assert not any('observed' in c for c in columns)
    assert not forecasts.duplicated([station,'ts','round']).any()
    frames = []
    for issue in (17,10):
        subset = forecasts.loc[forecasts['round'].eq(issue),[station,'ts',*columns]].assign(present=1)
        frames.append(keys.merge(subset,on=[station,'ts'],how='left',validate='one_to_one'))
    latest, earlier = frames
    result = keys.copy()
    for name in columns:
        result['base_'+name] = latest[name].where(latest.present.eq(1),earlier[name])
        result['r10_'+name] = earlier[name]
        result['rev_'+name] = latest[name]-earlier[name]
    result['missing17'] = latest.present.isna().astype('int8')
    result['missing10'] = earlier.present.isna().astype('int8')
    for name,values,period in [('hour',keys.ts.dt.hour,24),('doy',keys.ts.dt.dayofyear,365.25)]:
        result[name+'_sin'] = np.sin(2*np.pi*values/period)
        result[name+'_cos'] = np.cos(2*np.pi*values/period)
    return result

def prepare_panels() -> None:
    sites = pd.read_csv(RAW/'sites.csv')
    times = pd.date_range('2021-01-01 01:00','2025-03-01',freq='h',tz='Asia/Seoul')
    for provider in PROVIDERS:
        path = OUT/'data'/f'{provider}_forecast.parquet'
        if path.exists():
            continue
        station = f'{provider}_station'
        schema = pq.read_schema(RAW/'train'/f'forecast_{provider}.parquet')
        stations = sorted(sites[station].unique())
        estimate = len(times)*len(stations)*(3*(len(schema)-3)+10)*8
        save(OUT/'evidence'/f'{provider}_size_estimate.json',{'rows':len(times)*len(stations),'numeric_estimated_bytes':estimate,'working_multiplier':4,'estimated_working_bytes':4*estimate,'provider_serial':True})
        keys = pd.MultiIndex.from_product([stations,times],names=[station,'ts']).to_frame(index=False)
        forecasts = pd.read_parquet(RAW/'train'/f'forecast_{provider}.parquet',filters=[('ts','<=',times.max()),('round','in',[10,17])])
        frame = features(keys,forecasts,provider)
        frame.to_parquet(path,index=False)
        save(OUT/'data'/f'{provider}_schema.json',{'columns':list(frame),'features':[c for c in frame if c!='ts'],'rows':len(frame),'min_ts':str(frame.ts.min()),'max_ts':str(frame.ts.max()),'sha256':digest(path),'no_observation_columns':True})

def self_check() -> None:
    from profile_features import self_check as profile_check
    from cloud_aggregate import cloud_mean
    from cloud_common import signed_mean
    profile_check()
    times = pd.DatetimeIndex(pd.to_datetime(['2021-05-31','2021-06-01','2021-06-01 01:00','2021-12-01','2021-12-01 01:00'],format='mixed')).tz_localize('Asia/Seoul')
    np.testing.assert_array_equal(block_indices(times),[-1,-1,0,0,1])
    assert not np.array_equal(np.searchsorted(pd.DatetimeIndex(CUTOFFS,tz='Asia/Seoul').asi8,times.asi8,side='right')-1,block_indices(times))
    keys = pd.DataFrame({'wa_station':['a','b','c'],'ts':pd.Timestamp('2023-06-01 01:00',tz='Asia/Seoul')})
    forecast = pd.DataFrame({'wa_station':['a','a','b'],'ts':keys.ts.iloc[0],'round':[17,10,10],'wa_cloud':[np.nan,20.,30.]})
    actual = features(keys,forecast,'wa')
    assert np.isnan(actual.base_wa_cloud.iloc[0]) and actual.base_wa_cloud.iloc[1]==30
    assert np.isnan(actual.base_wa_cloud.iloc[2]) and actual.missing17.tolist()==[0,1,1]
    np.testing.assert_array_equal(signed_mean([[-2.],[1.],[4.]]),[1.])
    assert np.maximum([[-2.],[1.],[4.]],0).mean()!=1
    boundaries = pd.DatetimeIndex(pd.to_datetime(['2023-06-01 00:00','2023-06-01 01:00','2024-01-15 00:00'])).tz_localize('Asia/Seoul')
    np.testing.assert_array_equal(block_indices(boundaries),[3,4,5])
    from cloud_common import expected_cutoffs
    primary = pd.Timestamp('2023-06-01',tz='Asia/Seoul')
    recent = pd.Timestamp('2024-06-01',tz='Asia/Seoul')
    assert expected_cutoffs(boundaries[-1:],primary,True).iloc[0]==primary
    assert expected_cutoffs(boundaries[-1:],recent,False).iloc[0]==pd.Timestamp('2023-12-01',tz='Asia/Seoul')
    assert expected_cutoffs(boundaries[-1:],primary,True).iloc[0]!=expected_cutoffs(boundaries[-1:],recent,False).iloc[0]
    from cloud_common import valid_cloud
    np.testing.assert_array_equal(valid_cloud(pd.Series([-1.,0.,100.,101.,np.nan,np.inf])),[False,True,True,False,False,False])
    fixture = pd.DataFrame({'ts':[1,1,2,2],'grp':['g']*4,'capacity_kw':[1.,3.,1.,3.],'p_cloud':[100.,np.nan,np.nan,np.nan]})
    means = cloud_mean(fixture)
    assert means.iloc[0]==100 and np.isnan(means.iloc[1])
    assert fixture.iloc[0].p_cloud*fixture.iloc[0].capacity_kw/fixture.loc[fixture.ts.eq(1),'capacity_kw'].sum()==25
    save(OUT/'evidence/prefit_checks.json',{'passed':True,'scenarios':['strict-forward boundary mutant rejected','whole-row fallback preserves present NaN','missing rows preserved','profile capacity-weight mutant rejected','future-label perturbation invariant profile','signed mean before clip mutant rejected']})

