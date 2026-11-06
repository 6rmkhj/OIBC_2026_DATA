import numpy as np, pandas as pd
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 50); pd.set_option("display.max_rows", 400)
B = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad"
OUT = B + "/analysis/out/"; CACHE = B + "/cache/"
DATA = "C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset"
VAL0 = pd.Timestamp("2024-06-01 01:00", tz="Asia/Seoul"); VAL1 = pd.Timestamp("2025-06-01 00:00", tz="Asia/Seoul")
def P(*a): print(*a, flush=True)
sites = pd.read_csv(DATA + "/sites.csv").set_index("site_id"); cap = sites.capacity_kw.astype("float32")
cf = pd.read_parquet(CACHE + "cf_wide.parquet")
if "ts" in cf.columns: cf = cf.set_index("ts")
cf = cf[sites.index].astype("float32"); ts = cf.index; C = cf.values; T, N = C.shape; obs = ~np.isnan(C)
val = np.asarray((ts >= VAL0) & (ts <= VAL1))
mid = ts - pd.Timedelta("30min"); doy = mid.dayofyear.values; hr = mid.hour.values + mid.minute.values / 60
g = 2 * np.pi / 365 * (doy - 1 + (hr - 12) / 24)
eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g))
decl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g) + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
lat = np.deg2rad(sites.lat.values)[None, :]; lon = sites.lon.values[None, :]
tst = hr[:, None] * 60 + eqt[:, None] + 4 * lon - 540; ha = np.deg2rad(tst / 4 - 180)
elev = np.rad2deg(np.arcsin(np.clip(np.sin(lat) * np.sin(decl[:, None]) + np.cos(lat) * np.cos(decl[:, None]) * np.cos(ha), -1, 1))).astype("float32"); del tst, ha

# ---- 1. true-night nonzero (elev <= -6 at interval midpoint; also deep night <= -12) ----
Q = pd.read_csv(OUT + "gq_site_quality_full.csv", index_col=0, parse_dates=["first_ts", "last_ts"])
E = C * cap.values[None, :]
n6 = (C > 0) & (elev <= -6); n12 = (C > 0) & (elev <= -12)
Q["night6_nonzero_h"] = n6.sum(0); Q["night6_kwh"] = np.nansum(np.where(n6, E, 0), 0); Q["night6_max_cf"] = np.nanmax(np.where(n6, C, np.nan), 0) if n6.any() else np.nan
Q["night12_nonzero_h"] = n12.sum(0); Q["val_night6_nonzero_h"] = (n6 & val[:, None]).sum(0)
Q["night6_kwh_share_pct"] = 100 * Q.night6_kwh / np.nansum(np.where(C > 0, E, 0), 0)
P("true night (elev<=-6) nonzero: hours %d, sites with any %d, sites with >=20h %d, total kWh %.1f (%.4f%% of all kWh); deep night (<=-12) hours %d, sites %d" % (n6.sum(), (Q.night6_nonzero_h > 0).sum(), (Q.night6_nonzero_h >= 20).sum(), Q.night6_kwh.sum(), 100 * Q.night6_kwh.sum() / np.nansum(np.where(C > 0, E, 0)), n12.sum(), (Q.night12_nonzero_h > 0).sum()))
P(Q.sort_values("night6_nonzero_h", ascending=False).head(15)[["night6_nonzero_h", "night12_nonzero_h", "val_night6_nonzero_h", "night6_kwh", "night6_max_cf", "night6_kwh_share_pct", "h22_04_nonzero_h", "capacity_kw", "current_group"]].round(4))
h = ts.hour.values; late = (h >= 22) | (h <= 4)
for sid in Q.index[Q.h22_04_nonzero_h > 0]:
    j = cf.columns.get_loc(sid); m = (C[:, j] > 0) & late
    P(f"  {sid}: 22-04h nonzero {m.sum()}h, max CF {np.nanmax(C[m, j]):.4f}, mean kWh {np.nanmean(E[m, j]):.3f}, first {ts[m].min()}, last {ts[m].max()}, by year {pd.Series(ts[m].year).value_counts().sort_index().to_dict()}")
del n6, n12

# ---- 2. exact duplicate / twin series ----
DO_DUP = False
dup = []
for i in (range(N) if DO_DUP else []):
    for j in range(i + 1, N):
        both = obs[:, i] & obs[:, j]; nb = both.sum()
        if nb < 24 * 30: continue
        ei, ej = E[both, i], E[both, j]
        eq = np.mean(np.abs(ei - ej) <= 1e-3)
        if eq > 0.9:
            dup.append((cf.columns[i], cf.columns[j], int(nb), round(float(eq), 4), float(cap.iloc[i]), float(cap.iloc[j]), str(sites.current_group.iloc[i]) + str(sites.current_group.iloc[j]), round(float(np.corrcoef(ei, ej)[0, 1]), 5)))
dup = pd.DataFrame(dup, columns=["a", "b", "overlap_h", "frac_identical_kwh", "cap_a", "cap_b", "groups", "corr"])
P("exact-duplicate energy pairs (identical kWh on >90% overlapping hours):", len(dup), "\n", dup.to_string())
dup.to_csv(OUT + "gq_duplicate_series.csv", index=False)
# CF-identical pairs (same CF but different capacity => scaled copies)
dupcf = []
for i in (range(N) if DO_DUP else []):
    for j in range(i + 1, N):
        both = obs[:, i] & obs[:, j]; nb = both.sum()
        if nb < 24 * 30: continue
        ci, cj = C[both, i], C[both, j]; d = ci > 0.05
        if d.sum() < 100: continue
        eq = np.mean(np.abs(ci[d] - cj[d]) <= 0.002)
        if eq > 0.9: dupcf.append((cf.columns[i], cf.columns[j], int(nb), round(float(eq), 4), float(cap.iloc[i]), float(cap.iloc[j]), str(sites.current_group.iloc[i]) + str(sites.current_group.iloc[j])))
dupcf = pd.DataFrame(dupcf, columns=["a", "b", "overlap_h", "frac_identical_cf", "cap_a", "cap_b", "groups"])
P("CF-identical pairs (scaled copies):", len(dupcf), "\n", dupcf.to_string())
dupcf.to_csv(OUT + "gq_duplicate_cf_series.csv", index=False)
# identical metadata
meta_dup = sites.reset_index().groupby(["lat", "lon"]).site_id.agg(list); meta_dup = meta_dup[meta_dup.str.len() > 1]
P("sites sharing identical lat/lon:", len(meta_dup), meta_dup.to_dict() if len(meta_dup) < 30 else meta_dup.head(30).to_dict())

# ---- 3. late starters & specific sites ----
late_sites = Q[Q.first_ts > VAL0].sort_values("first_ts")
P("sites starting after VAL0: n=%d, cap=%.1f kW (A %.1f / B %.1f); months of history at 2025-06-01: min %.1f median %.1f" % (len(late_sites), late_sites.capacity_kw.sum(), late_sites.capacity_kw[late_sites.current_group == "A"].sum(), late_sites.capacity_kw[late_sites.current_group == "B"].sum(), ((VAL1 - late_sites.first_ts).dt.days / 30.44).min(), ((VAL1 - late_sites.first_ts).dt.days / 30.44).median()))
hist = Q.assign(months=((VAL1 - Q.first_ts).dt.days / 30.44))
P("history length buckets (months): <6: %d sites %.0f kW; 6-12: %d sites %.0f kW; 12-24: %d sites %.0f kW; 24-36: %d %.0f kW; >36: %d %.0f kW" % tuple(x for lo, hi in [(0, 6), (6, 12), (12, 24), (24, 36), (36, 99)] for x in [((hist.months >= lo) & (hist.months < hi)).sum(), hist.capacity_kw[(hist.months >= lo) & (hist.months < hi)].sum()]))
month = ts.tz_localize(None).to_period("M")
for sid in ["PV011", "PV188", "PV218", "PV059", "PV246", "PV073", "PV208", "PV223"]:
    j = cf.columns.get_loc(sid); s = pd.Series(C[:, j], index=ts); port = pd.Series(np.nanmedian(C, 1), index=ts)
    r = (s.groupby(month).mean() / port.groupby(month).mean()).dropna()
    P(f"{sid} cap={cap[sid]:.0f} grp={sites.current_group[sid]} monthly CF ratio vs portfolio-median (last 18 months):", r.tail(18).round(2).to_dict())

# ---- 4. rebuild risk table with stricter night flag ----
reasons = [];
for sid, r in Q.iterrows():
    rs = []
    if r.first_ts > VAL0: rs.append(f"started {r.first_ts.date()} ({(VAL1 - r.first_ts).days / 30.44:.1f} mo history)")
    if r.val_missing_day_share_pct > 5: rs.append(f"val-year missing daytime {r.val_missing_day_share_pct:.1f}%")
    if r.n_cf_gt1 > 0: rs.append(f"CF>1 x{int(r.n_cf_gt1)}")
    if r.n_neg > 0: rs.append(f"neg x{int(r.n_neg)}")
    if r.night6_max_cf >= 0.05: rs.append(f"true-night CF up to {r.night6_max_cf:.2f} ({int(r.night6_nonzero_h)}h)")
    if r.val_day_zero_nbr_h >= 24: rs.append(f"val daytime zeros vs nbrs {int(r.val_day_zero_nbr_h)}h")
    if r.day_zero_nbr_h >= 200: rs.append(f"all-time daytime zeros vs nbrs {int(r.day_zero_nbr_h)}h/{int(r.day_zero_nbr_days)}d")
    if r.val_flat_ge4_cf_gt5pct_h >= 24: rs.append(f"val flat-lines {int(r.val_flat_ge4_cf_gt5pct_h)}h")
    if pd.notna(r.yoy_rel_to_median_pp) and abs(r.yoy_rel_to_median_pp) > 10: rs.append(f"YoY {r.yoy_rel_to_median_pp:+.1f}pp vs median")
    if pd.notna(r.rel_perf_trend_pct_per_yr) and r.rel_perf_trend_pct_per_yr < -5: rs.append(f"trend {r.rel_perf_trend_pct_per_yr:+.1f}%/yr")
    if pd.notna(r.rel_perf_last12m) and r.rel_perf_last12m < 0.85: rs.append(f"last-12m rel.perf {r.rel_perf_last12m:.2f}")
    if r.val_day_underprod_h >= 100: rs.append(f"val under-prod(<30% nbrs) {int(r.val_day_underprod_h)}h")
    if r.val_p99_cf < 0.72: rs.append(f"val p99 CF {r.val_p99_cf:.2f} (low peak)")
    reasons.append("; ".join(rs))
Q["risk_reasons"] = reasons
sc = ((Q.first_ts > VAL0) * 3 + (Q.val_missing_day_share_pct > 20) * 3 + (Q.val_day_zero_nbr_h >= 24) * 2 + (Q.day_zero_nbr_h >= 200) * 1 + (Q.yoy_rel_to_median_pp.abs() > 10).fillna(False) * 2 + (Q.rel_perf_trend_pct_per_yr < -5).fillna(False) * 2 + (Q.rel_perf_last12m < 0.85).fillna(False) * 2 + (Q.val_flat_ge4_cf_gt5pct_h >= 24) * 1 + (Q.night6_max_cf >= 0.05) * 1 + (Q.n_cf_gt1 > 0) * 1 + (Q.n_neg > 0) * 1 + (Q.val_day_underprod_h >= 100) * 2 + (Q.val_p99_cf < 0.72) * 1)
Q["risk_score"] = sc.astype(int); Q["n_flags"] = [len(x.split("; ")) if x else 0 for x in reasons]
Q.to_csv(OUT + "gq_site_quality_full.csv")
risky = Q[Q.risk_score >= 2].sort_values(["risk_score", "capacity_kw"], ascending=False)
risky[["current_group", "capacity_kw", "first_ts", "val_coverage_pct", "val_missing_day_share_pct", "cf_Y24_25", "rel_perf_last12m", "val_p99_cf", "risk_score", "risk_reasons"]].to_csv(OUT + "gq_risky_sites.csv")
P("risk score distribution:", Q.risk_score.value_counts().sort_index().to_dict())
P("RISKY (score>=2): n=%d cap=%.0f kW (A %.0f / B %.0f); excluding late-start-only: %d" % (len(risky), risky.capacity_kw.sum(), risky.capacity_kw[risky.current_group == "A"].sum(), risky.capacity_kw[risky.current_group == "B"].sum(), (risky.n_flags > 1).sum()))
P(risky[["current_group", "capacity_kw", "cf_Y24_25", "rel_perf_last12m", "risk_score", "risk_reasons"]].to_string())
P("CLEAN (score 0): n=%d cap=%.0f kW (A %d/%.0f, B %d/%.0f); score<=1: n=%d cap=%.0f" % ((Q.risk_score == 0).sum(), Q.capacity_kw[Q.risk_score == 0].sum(), ((Q.risk_score == 0) & (Q.current_group == "A")).sum(), Q.capacity_kw[(Q.risk_score == 0) & (Q.current_group == "A")].sum(), ((Q.risk_score == 0) & (Q.current_group == "B")).sum(), Q.capacity_kw[(Q.risk_score == 0) & (Q.current_group == "B")].sum(), (Q.risk_score <= 1).sum(), Q.capacity_kw[Q.risk_score <= 1].sum()))
P("flag counts: late-start %d, night6_cf>=0.05 %d, val_dayzero>=24 %d, alltime_dayzero>=200 %d, |yoy|>10 %d, trend<-5 %d, relperf<0.85 %d, flat>=24 %d, cf>1 %d, neg %d, underprod>=100 %d, p99<0.72 %d" % ((Q.first_ts > VAL0).sum(), (Q.night6_max_cf >= 0.05).sum(), (Q.val_day_zero_nbr_h >= 24).sum(), (Q.day_zero_nbr_h >= 200).sum(), (Q.yoy_rel_to_median_pp.abs() > 10).sum(), (Q.rel_perf_trend_pct_per_yr < -5).sum(), (Q.rel_perf_last12m < 0.85).sum(), (Q.val_flat_ge4_cf_gt5pct_h >= 24).sum(), (Q.n_cf_gt1 > 0).sum(), (Q.n_neg > 0).sum(), (Q.val_day_underprod_h >= 100).sum(), (Q.val_p99_cf < 0.72).sum()))
P("rel_perf_last12m distribution:", Q.rel_perf_last12m.describe(percentiles=[.05, .1, .25, .5, .75, .9]).round(3).to_dict())
P("lowest rel_perf_last12m:\n", Q.sort_values("rel_perf_last12m").head(12)[["current_group", "capacity_kw", "cf_Y24_25", "rel_perf_last12m", "rel_perf_trend_pct_per_yr", "val_p99_cf", "val_day_zero_nbr_h", "val_day_underprod_h"]].round(3))
# val-year per-site CF==0 during strong sun regardless of neighbours (full outage proxy)
z = (C == 0) & (elev > 20) & val[:, None]
Q["val_zero_elev20_h"] = z.sum(0)
P("val-year zero-at-elev>20 hours: total %d, sites with >=24h: %d" % (z.sum(), (Q.val_zero_elev20_h >= 24).sum()), Q.val_zero_elev20_h.sort_values(ascending=False).head(12).to_dict())
P("DONE2")
