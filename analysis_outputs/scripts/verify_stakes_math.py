# verify_stakes_math: independent recomputation of the stakes numbers from ORIGINAL smp.csv + sites.csv + cf_wide
import numpy as np, pandas as pd
BASE = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad"
DS = "C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset"
TZ = "Asia/Seoul"
out = {}
# ---- 1. original smp.csv, float64
smp = pd.read_csv(f"{DS}/smp.csv")
smp['ts'] = pd.to_datetime(smp.ts, utc=True).dt.tz_convert(TZ)
assert len(smp) == 8760 and smp.ts.is_monotonic_increasing and not smp.ts.duplicated().any()
assert smp.ts.iloc[0] == pd.Timestamp('2025-06-01 01:00', tz=TZ) and smp.ts.iloc[-1] == pd.Timestamp('2026-06-01 00:00', tz=TZ)
hour = smp.ts.dt.hour.values; month = smp.ts.dt.month.values
k_rule = np.where((hour >= 11) & (hour <= 15), 3, 1)
out['k_matches_hour_rule'] = bool((smp.k.values == k_rule).all())
out['k_values'] = sorted(smp.k.unique().tolist())
w = smp.smp.values.astype('float64') * smp.k.values
pk = (hour >= 11) & (hour <= 15)
out['smp_mean'] = smp.smp.mean(); out['smp_median'] = smp.smp.median(); out['smp_min'] = smp.smp.min(); out['smp_max'] = smp.smp.max()
out['w_mean'] = w.mean(); out['w_sum'] = w.sum(); out['w_mean_1115'] = w[pk].mean()
out['share_w_1115'] = w[pk].sum() / w.sum()
out['share_smp_1115'] = smp.smp.values[pk].sum() / smp.smp.sum()
out['n_zero_smp'] = int((smp.smp == 0).sum()); out['n_le10'] = int((smp.smp <= 10).sum())
out['zero_smp_hours'] = sorted(hour[smp.smp.values == 0].tolist())
# compare with cache
sa = pd.read_parquet(f"{BASE}/cache/smp_all.parquet"); sa = sa[(sa.ts >= smp.ts.iloc[0]) & (sa.ts <= smp.ts.iloc[-1])].sort_values('ts')
out['cache_rows_test'] = len(sa); out['cache_vs_csv_max_abs_smp_diff'] = float(np.abs(sa.smp.values.astype('float64') - smp.smp.values).max()); out['cache_k_equal'] = bool((sa.k.values == smp.k.values).all())
# ---- 2. climatology from cf_wide (val year), two conventions
sites = pd.read_csv(f"{DS}/sites.csv"); cap = sites.set_index('site_id').capacity_kw.astype('float64'); TOTAL = cap.sum()
out['n_sites'] = len(cap); out['total_cap_kw'] = TOTAL
V0, V1 = pd.Timestamp('2024-06-01 01:00', tz=TZ), pd.Timestamp('2025-06-01 00:00', tz=TZ)
cf = pd.read_parquet(f"{BASE}/cache/cf_wide.parquet"); cf = cf.loc[(cf.index >= V0) & (cf.index <= V1), cap.index].astype('float64')
out['cf_val_rows'] = len(cf)
kwh_raw = (cf * cap.values).sum(axis=1, min_count=1)               # only reporting sites
cap_av = ((~cf.isna()) * cap.values).sum(axis=1)
kwh_scaled = kwh_raw / cap_av.replace(0, np.nan) * TOTAL             # report's convention
# convention C: per-site (month,hour) mean CF then x cap, summed (each site's own climatology; missing handled per-site)
site_clim = cf.groupby([cf.index.month.values, cf.index.hour.values]).mean()   # (month,hour) x site
site_clim.index = pd.MultiIndex.from_tuples(list(site_clim.index), names=['month', 'hour'])
clim_C = (site_clim * cap.values).sum(axis=1, min_count=1)
# fill any (month,hour) cell where a site has no data by that site's share of... ponytail: just report NaN count
out['siteclim_nan_cells'] = int(site_clim.isna().sum().sum())
def clim_of(series):
    df = pd.DataFrame({'kwh': series.values}, index=series.index); df['month'] = df.index.month; df['hour'] = df.index.hour
    return df.groupby(['month', 'hour']).kwh.mean()
clim_A = clim_of(kwh_scaled); clim_B = clim_of(kwh_raw)
idx = pd.MultiIndex.from_arrays([month, hour])
res = {}
for name, cl in [('scaled_to_full_cap(report)', clim_A), ('raw_reporting_sites_only', clim_B), ('per_site_clim_x_cap', clim_C)]:
    kc = cl.reindex(idx).values.astype('float64')
    B = (w * kc).sum(); R = (smp.smp.values * kc).sum()
    res[name] = dict(annual_GWh=kc.sum() / 1e6, CF=kc.sum() / (TOTAL * 8760), B_KRW=B, R_KRW=R, B_over_R=B / R,
                     share_exposure_1115=(w * kc)[pk].sum() / B, share_kwh_1115=kc[pk].sum() / kc.sum(),
                     penalty_10pct=0.10 * 0.10 * B, penalty_15pct=0.10 * 0.15 * B, value_1pp=0.001 * B,
                     value_1pct_rel_at_12p5=0.01 * 0.10 * 0.125 * B, kwh_weighted_w=B / kc.sum(), kwh_weighted_smp=R / kc.sum())
res = pd.DataFrame(res).T
# ---- 3. daylight convention: Wd and value of 1pp capacity-normalised MAE
day = (hour >= 6) & (hour <= 20)
Wd = w[day].sum(); out['n_daylight_hours'] = int(day.sum()); out['Wd'] = Wd
out['value_1pp_capnorm_daylight'] = 0.10 * 0.01 * TOTAL * Wd
out['penalty_capnorm_2pct'] = 0.10 * 0.02 * TOTAL * Wd
# ---- 4. covariance check on the VAL year: actual hourly kWh x actual val w   vs  clim kWh x val w
tsmp = pd.read_csv(f"{DS}/train/smp.csv"); tsmp['ts'] = pd.to_datetime(tsmp.ts, utc=True).dt.tz_convert(TZ)
tsmp = tsmp[(tsmp.ts >= V0) & (tsmp.ts <= V1)].set_index('ts').smp.astype('float64')
assert len(tsmp) == 8760
hv = tsmp.index.hour.values; mv = tsmp.index.month.values
wv = tsmp.values * np.where((hv >= 11) & (hv <= 15), 3, 1)
act = kwh_scaled.reindex(tsmp.index)
out['val_actual_missing_hours'] = int(act.isna().sum())
act = act.fillna(0.0).values
kc_val = clim_A.reindex(pd.MultiIndex.from_arrays([mv, hv])).values
Bv_act = (wv * act).sum(); Bv_clim = (wv * kc_val).sum()
out['val_B_actual_hourly'] = Bv_act; out['val_B_clim'] = Bv_clim; out['val_B_actual_over_clim'] = Bv_act / Bv_clim
out['val_share_exposure_1115_actual'] = (wv * act)[(hv >= 11) & (hv <= 15)].sum() / Bv_act
out['val_share_exposure_1115_clim'] = (wv * kc_val)[(hv >= 11) & (hv <= 15)].sum() / Bv_clim
out['val_R_actual'] = (tsmp.values * act).sum(); out['val_R_clim'] = (tsmp.values * kc_val).sum()
out['val_smp_mean'] = tsmp.mean(); out['val_w_mean'] = wv.mean(); out['val_share_w_1115'] = wv[(hv >= 11) & (hv <= 15)].sum() / wv.sum()
# ---- 5. year-over-year generation growth check: does val-year clim understate test-year output? (sites with <1y history)
first_obs = pd.read_parquet(f"{BASE}/cache/cf_wide.parquet").notna().idxmax()
late = first_obs[first_obs > V0]
out['sites_first_obs_after_val_start'] = int(len(late)); out['cap_kw_first_obs_after_val_start'] = float(cap[late.index].sum())
out['mean_avail_frac_val'] = float((cap_av / TOTAL).mean()); out['min_avail_frac_val'] = float((cap_av / TOTAL).min())
pd.set_option('display.width', 200); pd.set_option('display.float_format', lambda v: f"{v:,.6g}")
for kk, vv in out.items(): print(f"{kk}: {vv}")
print(res.T.to_string())
res.to_csv(f"{BASE}/analysis/out/verify_stakes_math_conventions.csv")
pd.Series({k: v for k, v in out.items() if not isinstance(v, list)}).to_csv(f"{BASE}/analysis/out/verify_stakes_math_scalars.csv", header=['value'])
