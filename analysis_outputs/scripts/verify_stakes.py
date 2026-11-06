# verify_stakes: independent recomputation of the stakes numbers in smp_weights_report.md
# Sources: smp.csv (raw, not the cache), sites.csv, cf_wide.parquet (val year only). Light on memory.
import numpy as np, pandas as pd
BASE = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad"
DS = "C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset"
OUT = BASE + "/analysis/out"; TZ = "Asia/Seoul"

# ---- 1. weights straight from smp.csv
s = pd.read_csv(f"{DS}/smp.csv"); s['ts'] = pd.to_datetime(s.ts, utc=True).dt.tz_convert(TZ)
assert len(s) == 8760 and s.ts.is_monotonic_increasing and not s.ts.duplicated().any()
assert s.ts.iloc[0] == pd.Timestamp('2025-06-01 01:00', tz=TZ) and s.ts.iloc[-1] == pd.Timestamp('2026-06-01 00:00', tz=TZ)
hour = s.ts.dt.hour; month = s.ts.dt.month
k_rule = np.where(hour.between(11, 15), 3, 1)
k_mismatch = int((s.k.values != k_rule).sum())
w = s.smp * s.k; pk = hour.between(11, 15)
print(f"k mismatches vs hour-rule: {k_mismatch}; smp min {s.smp.min()} max {s.smp.max()} zero-hours {(s.smp==0).sum()} NaN {s.smp.isna().sum()}")
print(f"mean SMP {s.smp.mean():.2f} median {s.smp.median():.2f} ; mean w {w.mean():.2f} ; mean w 11-15 {w[pk].mean():.2f} ; mean w other daylight(6-20) {w[hour.between(6,20)&~pk].mean():.2f}")
print(f"share of sum(w) in 11-15h: {w[pk].sum()/w.sum():.4f} ; share of sum(SMP) in 11-15h: {s.smp[pk].sum()/s.smp.sum():.4f}")
print(f"max w {w.max():.1f} at {s.ts[w.idxmax()]}")

# ---- 2. climatology from cf_wide (val year Jun2024-May2025), two ways
sites = pd.read_csv(f"{DS}/sites.csv", usecols=['site_id', 'capacity_kw'])
cap = sites.set_index('site_id').capacity_kw.astype('float64'); TOTAL = float(cap.sum()); print(f"total cap {TOTAL:.1f} kW, n sites {len(cap)}")
V0, V1 = pd.Timestamp('2024-06-01 01:00', tz=TZ), pd.Timestamp('2025-06-01 00:00', tz=TZ)
cf = pd.read_parquet(f"{BASE}/cache/cf_wide.parquet"); cf = cf.loc[(cf.index >= V0) & (cf.index <= V1), cap.index]
print(f"cf val rows {len(cf)} (expect 8760); NaN frac {cf.isna().mean().mean():.4f}")
mh = pd.MultiIndex.from_arrays([cf.index.month, cf.index.hour])
# way A (same as the report): hourly portfolio kWh scaled by reporting capacity, then (month,hour) mean
kwh = (cf * cap.values).sum(axis=1, min_count=1); capav = (cf.notna() * cap.values).sum(axis=1)
portA = (kwh / capav.replace(0, np.nan) * TOTAL).where(capav / TOTAL >= 0.5)
climA = portA.groupby([cf.index.month, cf.index.hour]).mean()
# way B (independent): per-site (month,hour) mean CF x capacity, summed over all 253 sites (no availability scaling)
climB = (cf.groupby([cf.index.month, cf.index.hour]).mean() * cap.values).sum(axis=1)
del cf
for name, clim in [('A_scaled', climA), ('B_persite', climB)]:
    kc = clim.reindex(pd.MultiIndex.from_arrays([month, hour])).values
    E = kc.sum(); B = float((w * kc).sum()); R = float((s.smp * kc).sum())
    print(f"\n[{name}] annual clim kWh {E/1e6:.2f} GWh (CF {E/(TOTAL*8760):.4f}) ; B = sum w*kWh = {B:.4e} KRW = {B/1e8:.2f} eok ; R = {R:.4e} = {R/1e8:.2f} eok ; B/R {B/R:.3f}")
    print(f"   exposure share 11-15h {(w*kc)[pk].sum()/B:.4f} ; kWh share 11-15h {kc[pk].sum()/E:.4f} ; kWh-weighted mean w {B/E:.2f} ; mean realized SMP {R/E:.2f}")
    print(f"   penalty @ wMAE 10% = 0.10*0.10*B = {0.01*B/1e8:.3f} eok ; @15% {0.015*B/1e8:.3f} eok ; 1pp of wMAE = {0.001*B/1e4:.0f} man-won ; 1% relative @12.5% = {0.01*0.10*0.125*B/1e4:.0f} man-won")
    print(f"   penalty as % of R @10%: {100*0.01*B/R:.2f}%")
# capacity-normalised convention check
day = hour.between(6, 20); Wd = w[day].sum()
print(f"\ndaylight(6-20) hours {int(day.sum())} ; 1pp capacity-normalised MAE over daylight = 0.10*0.01*TOTAL*sum(w_day) = {0.10*0.01*TOTAL*Wd/1e4:.0f} man-won ; 2% = {0.10*0.02*TOTAL*Wd/1e8:.3f} eok")
print(f"penalty per 1 MWh error, avg 11-15h hour: {0.10*1000*w[pk].mean():.0f} KRW ; other daylight: {0.10*1000*w[day&~pk].mean():.0f} KRW")
pd.DataFrame({'month': month, 'hour': hour, 'smp': s.smp, 'k': s.k, 'w': w}).groupby(['month','hour']).w.mean().unstack('month').to_csv(f"{OUT}/verify_stakes_w_hour_month.csv", float_format='%.2f')
print("DONE")
