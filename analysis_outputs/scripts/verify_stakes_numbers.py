"""Independent recomputation of the 'stakes' numbers in smp_weights_report.md.
Reads raw smp.csv (not the cache), sites.csv and cf_wide.parquet only."""
import numpy as np, pandas as pd

D = "C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset"
CACHE = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad/cache"
OUT = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad/analysis/out"
TZ = "Asia/Seoul"

# ---- 1. raw smp.csv ---------------------------------------------------------
s = pd.read_csv(f"{D}/smp.csv")
s["ts"] = pd.to_datetime(s.ts, utc=True).dt.tz_convert(TZ)
assert len(s) == 8760 and s.ts.is_monotonic_increasing and not s.ts.duplicated().any()
assert s.ts.iloc[0] == pd.Timestamp("2025-06-01 01:00", tz=TZ) and s.ts.iloc[-1] == pd.Timestamp("2026-06-01 00:00", tz=TZ)
hr = s.ts.dt.hour
k_rule = np.where(hr.between(11, 15), 3, 1)
print("k matches hour rule:", (s.k.values == k_rule).all(), "| k values:", sorted(s.k.unique()))
s["w"] = s.smp * s.k
pk = hr.between(11, 15)
print(f"SMP mean {s.smp.mean():.2f} median {s.smp.median():.2f} std {s.smp.std():.2f} min {s.smp.min():.2f} max {s.smp.max():.2f}")
print(f"w mean {s.w.mean():.2f} | w mean 11-15 {s.w[pk].mean():.2f} | zero-SMP hours {(s.smp==0).sum()} (all k=3: {(s.k[s.smp==0]==3).all()}) | <=10: {(s.smp<=10).sum()}")
print(f"share of sum(w) in 11-15h: {s.w[pk].sum()/s.w.sum():.4%}  (share of sum(SMP) in 11-15h: {s.smp[pk].sum()/s.smp.sum():.4%})")
print(f"max w {s.w.max():.1f} at {s.loc[s.w.idxmax(),'ts']}")
print(f"penalty per 1 MWh error, avg 11-15h hour: {0.10*1000*s.w[pk].mean():.0f} KRW")

# ---- 2. climatological portfolio kWh from cf_wide (PV2024 = 2024-06-01 01:00 .. 2025-06-01 00:00)
sites = pd.read_csv(f"{D}/sites.csv", usecols=["site_id", "capacity_kw"]).set_index("site_id")
cap = sites.capacity_kw.astype("float64"); TOT = cap.sum(); print(f"total capacity {TOT:.1f} kW, n sites {len(cap)}")
V0, V1 = pd.Timestamp("2024-06-01 01:00", tz=TZ), pd.Timestamp("2025-06-01 00:00", tz=TZ)
cf = pd.read_parquet(f"{CACHE}/cf_wide.parquet")
cf = cf.loc[(cf.index >= V0) & (cf.index <= V1), cap.index].astype("float32")
print("val-year cf rows:", len(cf), "| NaN frac:", float(cf.isna().mean().mean()).__round__(4), "| CF>1 cells:", int((cf > 1).sum().sum()), "| CF<0 cells:", int((cf < 0).sum().sum()))
kwh = cf * cap.values.astype("float32")

# (a) report's method: scale observed kWh by TOT / available capacity
cap_av = ((~cf.isna()) * cap.values).sum(axis=1)
port_a = kwh.sum(axis=1, min_count=1) / cap_av.replace(0, np.nan) * TOT
port_a = port_a.where(cap_av / TOT >= 0.5)
# (b) alternative: fill each site's missing CF with that site's own (month,hour) mean CF, then sum (no linear scale-up)
mh = pd.MultiIndex.from_arrays([cf.index.month, cf.index.hour])
site_mh_mean = cf.groupby([cf.index.month, cf.index.hour]).transform("mean")
cf_fill = cf.fillna(site_mh_mean)
port_b = (cf_fill * cap.values.astype("float32")).sum(axis=1)
# (c) lower bound: no fill at all (missing sites contribute 0)
port_c = kwh.sum(axis=1, min_count=1)

def clim_on_test(port):
    p = pd.DataFrame({"kwh": port.values}, index=port.index)
    p["m"] = p.index.month; p["h"] = p.index.hour
    cl = p.groupby(["m", "h"]).kwh.mean()
    return cl.reindex(pd.MultiIndex.from_arrays([s.ts.dt.month, s.ts.dt.hour])).values

rows = []
for name, port in [("A_scaled_like_report", port_a), ("B_site_monthhour_fill", port_b), ("C_no_fill_lower_bound", port_c)]:
    kc = clim_on_test(port)
    B = float(np.nansum(s.w.values * kc)); R = float(np.nansum(s.smp.values * kc)); E = float(np.nansum(kc))
    exp_1115 = float(np.nansum((s.w.values * kc)[pk.values])) / B
    kwh_1115 = float(np.nansum(kc[pk.values])) / E
    rows.append(dict(method=name, annual_GWh=E / 1e6, CF=E / (TOT * 8760), B_eokwon=B / 1e8, R_eokwon=R / 1e8, B_over_R=B / R,
                     exposure_share_1115=exp_1115, kwh_share_1115=kwh_1115, penalty_wMAE10pct_eokwon=0.10 * 0.10 * B / 1e8,
                     penalty_wMAE15pct_eokwon=0.10 * 0.15 * B / 1e8, value_1pp_wMAE_manwon=0.10 * 0.01 * B / 1e4,
                     value_1pct_rel_at12p5_manwon=0.01 * 0.10 * 0.125 * B / 1e4, kwh_weighted_mean_w=B / E, kwh_weighted_mean_smp=R / E))
res = pd.DataFrame(rows).set_index("method")
pd.set_option("display.width", 250); pd.set_option("display.float_format", lambda v: f"{v:,.4f}")
print(res.T.to_string())
res.to_csv(f"{OUT}/verify_stakes_numbers.csv")

# ---- 3. sensitivity: weather-year variability and the clim-vs-actual covariance bias ---------------
cf_all = pd.read_parquet(f"{CACHE}/cf_wide.parquet")[cap.index]
print("\n--- availability by PV-year (fraction of site-hours present) ---")
avail = {}
for y in [2021, 2022, 2023, 2024]:
    c = cf_all.loc[(cf_all.index >= pd.Timestamp(f"{y}-06-01 01:00", tz=TZ)) & (cf_all.index <= pd.Timestamp(f"{y+1}-06-01 00:00", tz=TZ))]
    avail[y] = c.notna().mean()
    print(f"PV{y}: rows {len(c)}, site-hour availability {float(c.notna().mean().mean()):.3f}, sites with >=90% coverage: {int((avail[y] >= 0.9).sum())}")
# same-site CF ratio PV2023 vs PV2024 for sites covered >=90% in both (weather-year variability of the portfolio)
good = avail[2023].index[(avail[2023] >= 0.9) & (avail[2024] >= 0.9)]
c23 = cf_all.loc[(cf_all.index >= pd.Timestamp("2023-06-01 01:00", tz=TZ)) & (cf_all.index <= pd.Timestamp("2024-06-01 00:00", tz=TZ)), good]
c24 = cf_all.loc[(cf_all.index >= pd.Timestamp("2024-06-01 01:00", tz=TZ)) & (cf_all.index <= pd.Timestamp("2025-06-01 00:00", tz=TZ)), good]
cf23 = float((c23.mean() * cap[good]).sum() / cap[good].sum()); cf24 = float((c24.mean() * cap[good]).sum() / cap[good].sum())
print(f"same {len(good)} sites ({cap[good].sum():.0f} kW): mean CF PV2023 {cf23:.4f} vs PV2024 {cf24:.4f}, ratio {cf23/cf24:.3f}")
# covariance check inside PV2024: sum(w*actual) vs sum(w*clim(m,h)) with val-year SMP (k from hour)
tr = pd.read_csv(f"{D}/train/smp.csv"); tr["ts"] = pd.to_datetime(tr.ts, utc=True).dt.tz_convert(TZ)
tr = tr[(tr.ts >= V0) & (tr.ts <= V1)].set_index("ts").reindex(port_a.index)
wv = tr.smp.values * np.where(tr.index.hour.isin(range(11, 16)), 3, 1)
pa = pd.DataFrame({"kwh": port_a.values}, index=port_a.index); pa["m"] = pa.index.month; pa["h"] = pa.index.hour
clim_v = pa.groupby(["m", "h"]).kwh.transform("mean").values
ok = np.isfinite(port_a.values) & np.isfinite(wv)
Ba = float(np.sum(wv[ok] * port_a.values[ok])); Bc = float(np.sum(wv[ok] * clim_v[ok]))
Ra = float(np.sum(tr.smp.values[ok] * port_a.values[ok])); Rc = float(np.sum(tr.smp.values[ok] * clim_v[ok]))
print(f"PV2024 (val-year SMP): sum w*actual {Ba/1e8:.2f} eok vs sum w*clim {Bc/1e8:.2f} eok -> ratio {Ba/Bc:.4f}; revenue actual/clim ratio {Ra/Rc:.4f} ({ok.sum()} hours)")
print("DONE")
