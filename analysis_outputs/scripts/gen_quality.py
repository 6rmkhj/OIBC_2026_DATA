import os, numpy as np, pandas as pd, pyarrow.parquet as pq
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 50); pd.set_option("display.max_rows", 400)
B = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad"
OUT = B + "/analysis/out/"; CACHE = B + "/cache/"
DATA = "C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset"
VAL0 = pd.Timestamp("2024-06-01 01:00", tz="Asia/Seoul"); VAL1 = pd.Timestamp("2025-06-01 00:00", tz="Asia/Seoul")
def P(*a): print(*a, flush=True)

sites = pd.read_csv(DATA + "/sites.csv").set_index("site_id")
cap = sites.capacity_kw.astype("float32")
grp = sites.current_group

# ---------- raw generation checks ----------
gen = pq.read_table(DATA + "/train/generation.parquet", read_dictionary=["site_id"]).to_pandas()
P("rows", len(gen), "dups(site,ts)", gen.duplicated(["site_id", "ts"]).sum(), "NaN energy", gen.energy.isna().sum())
P("ts range", gen.ts.min(), gen.ts.max(), "min energy", gen.energy.min(), "max", gen.energy.max())
neg = gen[gen.energy < 0]
P("negatives", len(neg), "sum", neg.energy.sum(), "\n", neg.groupby("site_id", observed=True).energy.agg(["count", "min", "sum"]))
neg.to_csv(OUT + "negatives.csv", index=False)
gen["cf"] = (gen.energy / gen.site_id.astype(str).map(cap).astype(float)).astype("float32")
cf1 = gen[gen.cf > 1]
P("CF>1", len(cf1), "\n", cf1[["site_id", "ts", "energy", "cf"]].to_string())
cf1.to_csv(OUT + "cf_gt1.csv", index=False)
# value resolution per site (meter granularity)
def step(s):
    u = np.unique(np.round(s.values, 4)); d = np.diff(u); d = d[d > 0]
    return float(np.round(d.min(), 4)) if len(d) else np.nan
res = gen.groupby("site_id", observed=True).energy.apply(step); res.index = res.index.astype(str); res.name = "min_value_step_kwh"
per_site = gen.groupby("site_id", observed=True).agg(first_ts=("ts", "min"), last_ts=("ts", "max"), n_rows=("ts", "size"), n_zero=("energy", lambda s: int((s == 0).sum())), n_neg=("energy", lambda s: int((s < 0).sum())))
per_site.index = per_site.index.astype(str)
per_site["expected_rows"] = ((per_site.last_ts - per_site.first_ts) / pd.Timedelta("1h") + 1).astype(int)
per_site["coverage_within_span_pct"] = (100 * per_site.n_rows / per_site.expected_rows).round(2)
del gen, neg, cf1

# ---------- CF wide ----------
cf = pd.read_parquet(CACHE + "cf_wide.parquet")
if "ts" in cf.columns: cf = cf.set_index("ts")
cf = cf[sites.index].astype("float32")
ts = cf.index
P("cf_wide", cf.shape, ts.min(), ts.max(), "freq ok:", bool((ts[1:] - ts[:-1] == pd.Timedelta("1h")).all()))
P("rows in cf_wide notna:", int(cf.notna().values.sum()))
C = cf.values  # (T, N)
T, N = C.shape
obs = ~np.isnan(C)

# ---------- solar elevation at interval midpoint ----------
mid = ts - pd.Timedelta("30min")
doy = mid.dayofyear.values; hr = mid.hour.values + mid.minute.values / 60
g = 2 * np.pi / 365 * (doy - 1 + (hr - 12) / 24)
eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g))
decl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g) + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
lat = np.deg2rad(sites.lat.values)[None, :]; lon = sites.lon.values[None, :]
tst = hr[:, None] * 60 + eqt[:, None] + 4 * lon - 540
ha = np.deg2rad(tst / 4 - 180)
cosz = np.sin(lat) * np.sin(decl[:, None]) + np.cos(lat) * np.cos(decl[:, None]) * np.cos(ha)
elev = np.rad2deg(np.arcsin(np.clip(cosz, -1, 1))).astype("float32"); del cosz, ha, tst
day = elev > 0
P("day share of hours", float(day.mean()))

# ---------- (1) coverage ----------
month = ts.to_period("M")
cov_m = pd.DataFrame(obs, index=ts, columns=cf.columns).groupby(month).mean().T * 100  # site x month
cov_m.to_csv(OUT + "coverage_site_month_pct.csv", float_format="%.1f")
order = per_site.loc[cov_m.index].sort_values(["first_ts", "last_ts"]).index
fig, ax = plt.subplots(figsize=(14, 22))
im = ax.imshow(cov_m.loc[order].values, aspect="auto", cmap="viridis", vmin=0, vmax=100)
ax.set_yticks(range(len(order))); ax.set_yticklabels(order, fontsize=4)
ax.set_xticks(range(0, cov_m.shape[1], 3)); ax.set_xticklabels([str(m) for m in cov_m.columns[::3]], rotation=90, fontsize=7)
ax.set_title("Generation coverage % per site-month (sites sorted by first timestamp)"); plt.colorbar(im, ax=ax, fraction=0.02)
plt.tight_layout(); plt.savefig(OUT + "fig01_coverage_heatmap.png", dpi=130); plt.close()

val = ((ts >= VAL0) & (ts <= VAL1)).values if hasattr((ts >= VAL0), "values") else ((ts >= VAL0) & (ts <= VAL1))
val = np.asarray(val)
val_cov = obs[val].mean(0) * 100
per_site["val_coverage_pct"] = np.round(val_cov, 2)
per_site["val_day_coverage_pct"] = np.round(np.array([obs[val][:, j][day[val][:, j]].mean() * 100 for j in range(N)]), 2)
per_site["val_night_coverage_pct"] = np.round(np.array([obs[val][:, j][~day[val][:, j]].mean() * 100 for j in range(N)]), 2)
full_year = (per_site.first_ts <= VAL0) & (per_site.last_ts >= VAL1)
P("sites spanning whole validation year (first<=VAL0 & last>=VAL1):", int(full_year.sum()))
for th in [99.9, 99, 95, 90, 80, 50]: P(f"  sites with val-year coverage >= {th}%:", int((val_cov >= th).sum()))
P("sites with first_ts after VAL0:", int((per_site.first_ts > VAL0).sum()), "; last_ts before VAL1:", int((per_site.last_ts < VAL1).sum()))
P("last_ts < VAL1 sites:\n", per_site[per_site.last_ts < VAL1][["first_ts", "last_ts", "n_rows", "val_coverage_pct"]])
P("first_ts > 2024-01-01 sites:\n", per_site[per_site.first_ts > pd.Timestamp("2024-01-01", tz="Asia/Seoul")][["first_ts", "last_ts", "n_rows", "val_coverage_pct"]])
P("first_ts distribution by year:", per_site.first_ts.dt.year.value_counts().sort_index().to_dict())
P("first_ts distribution by half-year:", per_site.first_ts.dt.to_period("Q").value_counts().sort_index().to_dict())
P("overall coverage within span: median %.2f, min %.2f, mean %.2f" % (per_site.coverage_within_span_pct.median(), per_site.coverage_within_span_pct.min(), per_site.coverage_within_span_pct.mean()))
P("val-year: median day coverage %.2f, night coverage %.2f" % (per_site.val_day_coverage_pct.median(), per_site.val_night_coverage_pct.median()))
P("sites where night coverage < day coverage - 5pp (zeros not reported at night?):", int((per_site.val_night_coverage_pct < per_site.val_day_coverage_pct - 5).sum()))
P("per-site n_zero share of rows: median %.3f" % (per_site.n_zero / per_site.n_rows).median())

# ---------- (2) gaps ----------
gaps = []
for j, sid in enumerate(cf.columns):
    o = obs[:, j]; idx = np.flatnonzero(o)
    if len(idx) == 0: continue
    a, b = idx[0], idx[-1]
    m = ~o[a:b + 1]
    if not m.any(): continue
    d = np.diff(np.r_[0, m.astype(np.int8), 0]); s = np.flatnonzero(d == 1) + a; e = np.flatnonzero(d == -1) + a
    for s0, e0 in zip(s, e):
        gaps.append((sid, ts[s0], ts[e0 - 1], e0 - s0, float(day[s0:e0, j].mean())))
gaps = pd.DataFrame(gaps, columns=["site_id", "gap_start", "gap_end", "len_h", "day_frac"])
gaps.to_csv(OUT + "gaps_all.csv", index=False)
bins = [0, 1, 3, 12, 24, 168, 720, 1e9]; labels = ["1h", "2-3h", "4-12h", "13-24h", "1-7d", "7-30d", ">30d"]
gaps["bucket"] = pd.cut(gaps.len_h, bins=bins, labels=labels)
gb = gaps.groupby("bucket", observed=False).agg(n_gaps=("len_h", "size"), hours=("len_h", "sum"), mean_day_frac=("day_frac", "mean"))
gb["hours_share_pct"] = 100 * gb.hours / gb.hours.sum()
P("gap buckets:\n", gb)
gb.to_csv(OUT + "gap_buckets.csv")
P("total gaps:", len(gaps), "total missing hours within span:", int(gaps.len_h.sum()), "; of which daytime:", int((gaps.len_h * gaps.day_frac).sum()), "(share %.3f, vs day share of hours %.3f)" % ((gaps.len_h * gaps.day_frac).sum() / gaps.len_h.sum(), day.mean()))
P("1h gaps: n=%d day_frac mean %.3f ; night-only gaps count %d ; day-only gaps count %d" % ((gaps.len_h == 1).sum(), gaps[gaps.len_h == 1].day_frac.mean(), (gaps.day_frac == 0).sum(), (gaps.day_frac == 1).sum()))
P("gap start hour distribution (gaps<=24h):", gaps[gaps.len_h <= 24].gap_start.dt.hour.value_counts().sort_index().to_dict())
long_gaps = gaps[gaps.len_h >= 168].sort_values("len_h", ascending=False)
P("gaps >= 7 days: n=%d sites=%d\n" % (len(long_gaps), long_gaps.site_id.nunique()), long_gaps.head(40).to_string())
long_gaps.to_csv(OUT + "gaps_ge7d.csv", index=False)
site_gap = gaps.groupby("site_id").agg(n_gaps=("len_h", "size"), missing_h=("len_h", "sum"), longest_gap_h=("len_h", "max"), n_gaps_ge24h=("len_h", lambda s: int((s >= 24).sum())), n_gaps_ge7d=("len_h", lambda s: int((s >= 168).sum())))
val_gaps = gaps[(gaps.gap_end >= VAL0) & (gaps.gap_start <= VAL1)]
site_gap["val_longest_gap_h"] = val_gaps.groupby("site_id").len_h.max()
site_gap["val_n_gaps"] = val_gaps.groupby("site_id").len_h.size()
per_site = per_site.join(site_gap)
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
ax[0].hist(np.log10(gaps.len_h), bins=60); ax[0].set_xlabel("log10(gap length, h)"); ax[0].set_ylabel("# gaps"); ax[0].set_title("Gap length distribution (count)")
ax[1].bar(labels, gb.hours_share_pct); ax[1].set_ylabel("% of missing hours"); ax[1].set_title("Missing hours by gap-length bucket")
plt.tight_layout(); plt.savefig(OUT + "fig02_gap_lengths.png", dpi=130); plt.close()
miss_month = pd.Series((~obs).sum(1), index=ts).groupby(month).sum()
P("missing (site,ts) per month, 2023-06..:\n", miss_month[miss_month.index >= pd.Period("2023-06")].to_string())

# ---------- (3) anomalies ----------
A = pd.DataFrame(index=cf.columns)
A["n_neg"] = (C < 0).sum(0); A["n_cf_gt1"] = (C > 1).sum(0); A["max_cf"] = np.nanmax(C, 0)
night = ~day
A["night_nonzero_h"] = ((C > 0) & night).sum(0); A["night_gt1pct_h"] = ((C > 0.01) & night).sum(0)
A["night_energy_share_pct"] = 100 * np.nansum(np.where(night, C, 0), 0) / np.nansum(np.where(C > 0, C, 0), 0)
h = ts.hour.values; late = (h >= 22) | (h <= 4)
A["h22_04_nonzero_h"] = ((C > 0) & late[:, None]).sum(0)
P("night (elev<=0) nonzero hours total:", int(A.night_nonzero_h.sum()), "; CF>1%:", int(A.night_gt1pct_h.sum()), "; sites with any:", int((A.night_nonzero_h > 0).sum()), "; sites with any CF>1%:", int((A.night_gt1pct_h > 0).sum()))
P("h22-04 nonzero hours total:", int(A.h22_04_nonzero_h.sum()), "sites:", int((A.h22_04_nonzero_h > 0).sum()))
P("top night nonzero sites:\n", A.sort_values("night_gt1pct_h", ascending=False).head(15)[["night_nonzero_h", "night_gt1pct_h", "night_energy_share_pct", "h22_04_nonzero_h"]])
nz = np.where(night, C, np.nan); A["night_max_cf"] = np.nanmax(nz, 0); del nz
# night nonzero: is it twilight (elev in -6..0)?
tw = (C > 0) & night & (elev > -6)
P("night nonzero hours with elev in (-6,0] (twilight):", int(tw.sum()), "of", int(A.night_nonzero_h.sum())); del tw
# neighbours
la, lo = np.deg2rad(sites.lat.values), np.deg2rad(sites.lon.values)
dist = 6371 * np.arccos(np.clip(np.sin(la)[:, None] * np.sin(la)[None, :] + np.cos(la)[:, None] * np.cos(la)[None, :] * np.cos(lo[:, None] - lo[None, :]), -1, 1))
np.fill_diagonal(dist, np.inf)
K = 10; nbr = np.argsort(dist, 1)[:, :K]
nbr_mean = np.full((T, N), np.nan, dtype="float32"); nbr_cnt = np.zeros((T, N), dtype="int16")
for j in range(N):
    sub = C[:, nbr[j]]
    with np.errstate(all="ignore"): nbr_mean[:, j] = np.nanmean(sub, 1)
    nbr_cnt[:, j] = (~np.isnan(sub)).sum(1)
A["nbr_median_dist_km"] = np.median(np.sort(dist, 1)[:, :K], 1)
dz = (C == 0) & (elev > 10) & (nbr_mean > 0.15) & (nbr_cnt >= 3)
A["day_zero_nbr_h"] = dz.sum(0)
A["day_zero_nbr_days"] = [len(np.unique(ts.date[dz[:, j]])) for j in range(N)]
A["val_day_zero_nbr_h"] = (dz & val[:, None]).sum(0)
A["day_zero_nbr_pct_of_dayhours"] = 100 * dz.sum(0) / np.maximum(((elev > 10) & obs).sum(0), 1)
P("daytime zeros while neighbours produce: total hours", int(dz.sum()), "; sites with any:", int((A.day_zero_nbr_h > 0).sum()), "; sites with >=24h:", int((A.day_zero_nbr_h >= 24).sum()), "; val-year hours:", int(A.val_day_zero_nbr_h.sum()))
P(A.sort_values("day_zero_nbr_h", ascending=False).head(20)[["day_zero_nbr_h", "day_zero_nbr_days", "val_day_zero_nbr_h", "day_zero_nbr_pct_of_dayhours"]])
# expected kWh lost to daytime zeros (val year) using nbr mean as proxy
A["val_day_zero_lost_kwh"] = np.nansum(np.where(dz & val[:, None], nbr_mean, 0), 0) * cap.values
up = (C < 0.3 * nbr_mean) & (C > 0) & (nbr_mean > 0.3) & (nbr_cnt >= 3) & (elev > 15)
A["day_underprod_h"] = up.sum(0); A["val_day_underprod_h"] = (up & val[:, None]).sum(0); del up, dz
P("partial under-production (<30% of nbr mean, nbr>0.3): total", int(A.day_underprod_h.sum()), "val:", int(A.val_day_underprod_h.sum()), "; sites >=100h in val:", int((A.val_day_underprod_h >= 100).sum()))
# flat-lines
same = np.zeros((T, N), bool); same[1:] = (C[1:] == C[:-1]) & (C[1:] > 0)
run = np.zeros((T, N), np.int32)
for i in range(1, T): run[i] = np.where(same[i], run[i - 1] + 1, 0)
flat4 = run >= 3
A["flat_run_ge4_h"] = flat4.sum(0)
A["flat_run_ge4_h_cf_gt5pct"] = (flat4 & (C > 0.05)).sum(0)
A["longest_flat_run_h"] = run.max(0) + 1
A["val_flat_ge4_cf_gt5pct_h"] = (flat4 & (C > 0.05) & val[:, None]).sum(0)
P("flat-line (>=4 identical nonzero values) hours total:", int(A.flat_run_ge4_h.sum()), "; with CF>5%:", int(A.flat_run_ge4_h_cf_gt5pct.sum()), "; sites with any CF>5% flat:", int((A.flat_run_ge4_h_cf_gt5pct > 0).sum()))
P(A.sort_values("flat_run_ge4_h_cf_gt5pct", ascending=False).head(15)[["flat_run_ge4_h", "flat_run_ge4_h_cf_gt5pct", "longest_flat_run_h", "val_flat_ge4_cf_gt5pct_h"]].join(res))
del same, run, flat4
# clipping / plateau
dates = ts.date; ud, dinv = np.unique(dates, return_inverse=True)
Cz = np.where(obs, C, 0)
daily = np.zeros((len(ud), N), "float32"); np.add.at(daily, dinv, Cz)
daily_cnt = np.zeros((len(ud), N), "int16"); np.add.at(daily_cnt, dinv, obs.astype("int16"))
daily[daily_cnt < 20] = 0
mask_mid = np.isin(h, [11, 12, 13, 14])
plateau_flat = np.full(N, np.nan); plateau_lvl = np.full(N, np.nan); n_plateau_days = np.zeros(N, int); p995 = np.nanquantile(C, 0.995, axis=0)
for j in range(N):
    top = np.argsort(daily[:, j])[::-1][:40]; sp = []; lv = []
    for d in top:
        rows = np.flatnonzero((dinv == d) & mask_mid); v = C[rows, j]
        if len(v) == 4 and not np.isnan(v).any() and v.mean() > 0.3:
            sp.append((v.max() - v.min()) / v.mean()); lv.append(v.mean())
    if sp:
        sp = np.array(sp); plateau_flat[j] = np.median(sp); plateau_lvl[j] = np.median(lv); n_plateau_days[j] = int((sp < 0.03).sum())
A["mid_spread_median"] = plateau_flat; A["mid_level_topdays"] = plateau_lvl; A["n_plateau_days_of_top40"] = n_plateau_days; A["p995_cf"] = p995
A["clip_flag"] = (A.n_plateau_days_of_top40 >= 15)
P("plateau/clipping candidates (>=15 of top-40 days with 11-14h spread<3%):", int(A.clip_flag.sum()), "; >=5 days:", int((A.n_plateau_days_of_top40 >= 5).sum()))
P("mid_spread_median distribution:", A.mid_spread_median.describe().round(3).to_dict())
P(A.sort_values("n_plateau_days_of_top40", ascending=False).head(25)[["n_plateau_days_of_top40", "mid_spread_median", "mid_level_topdays", "p995_cf", "max_cf"]].join(cap))
# suspicious capacity
Cv = np.where(val[:, None] & day, C, np.nan)
with np.errstate(all="ignore"):
    A["val_p99_cf"] = np.nanquantile(Cv, 0.99, axis=0); A["val_max_cf"] = np.nanmax(Cv, 0)
del Cv
med99 = np.nanmedian(A.val_p99_cf); A["p99_vs_peer_median"] = A.val_p99_cf / med99
P("val-year daytime p99 CF: median %.3f, p10 %.3f, p90 %.3f, min %.3f, max %.3f" % (med99, np.nanquantile(A.val_p99_cf, 0.1), np.nanquantile(A.val_p99_cf, 0.9), np.nanmin(A.val_p99_cf), np.nanmax(A.val_p99_cf)))
P("sites with p99 < 0.6 x peer median:\n", A[A.p99_vs_peer_median < 0.6][["val_p99_cf", "val_max_cf", "max_cf", "p99_vs_peer_median"]].join(cap))
P("sites with p99 > 1.2 x peer median (capacity understated?):\n", A[A.p99_vs_peer_median > 1.2][["val_p99_cf", "val_max_cf", "max_cf", "n_cf_gt1"]].join(cap))
P("all-time max CF distribution:", A.max_cf.describe().round(3).to_dict(), "; sites with max_cf<0.5:", int((A.max_cf < 0.5).sum()))

# ---------- (4) annual CF, peak, trend ----------
yrs = {"Y21_22": ("2021-06-01 01:00", "2022-06-01 00:00"), "Y22_23": ("2022-06-01 01:00", "2023-06-01 00:00"), "Y23_24": ("2023-06-01 01:00", "2024-06-01 00:00"), "Y24_25": ("2024-06-01 01:00", "2025-06-01 00:00")}
ann = pd.DataFrame(index=cf.columns)
for k, (a, b) in yrs.items():
    m = np.asarray((ts >= pd.Timestamp(a, tz="Asia/Seoul")) & (ts <= pd.Timestamp(b, tz="Asia/Seoul")))
    covk = obs[m].mean(0)
    with np.errstate(all="ignore"): mean_cf = np.nanmean(C[m], 0); pk = np.nanmax(C[m], 0)
    ann["cf_" + k] = np.where(covk >= 0.8, mean_cf, np.nan); ann["cov_" + k] = covk; ann["peak_" + k] = pk
ann["yoy_24_vs_23_pct"] = 100 * (ann.cf_Y24_25 / ann.cf_Y23_24 - 1)
port_yoy = np.nanmedian(ann.yoy_24_vs_23_pct)
ann["yoy_rel_to_median_pp"] = ann.yoy_24_vs_23_pct - port_yoy
mcf = pd.DataFrame(C, index=ts).groupby(month).mean(); mcov = pd.DataFrame(obs, index=ts).groupby(month).mean()
mcf = mcf.where(mcov >= 0.8); mcf.columns = cf.columns
port_m = mcf.median(1)
rel = mcf.div(port_m, axis=0)
slope = {}
for sid in cf.columns:
    r = rel[sid].dropna(); r = r[r.index >= pd.Period("2022-06")]
    if len(r) >= 18:
        x = np.arange(len(r)); b1 = np.polyfit(x, r.values / np.nanmean(r.values), 1)[0]; slope[sid] = 100 * 12 * b1
ann["rel_perf_trend_pct_per_yr"] = pd.Series(slope)
ann["rel_perf_last12m"] = rel[rel.index >= pd.Period("2024-06")].mean().values
ann["rel_perf_prev12m"] = rel[(rel.index >= pd.Period("2023-06")) & (rel.index <= pd.Period("2024-05"))].mean().values
ann["group"] = grp; ann["capacity_kw"] = cap
P("annual CF (sites w/ >=80% cov) summary:\n", ann[[c for c in ann.columns if c.startswith("cf_")]].describe().round(4))
P("peak CF per year summary:\n", ann[[c for c in ann.columns if c.startswith("peak_")]].describe().round(3))
P("portfolio median YoY (24/25 vs 23/24): %.2f%% ; n sites with both years: %d" % (port_yoy, ann.yoy_24_vs_23_pct.notna().sum()))
P("YoY distribution:", ann.yoy_24_vs_23_pct.describe().round(2).to_dict())
P("YoY < -10pp relative to median:\n", ann[ann.yoy_rel_to_median_pp < -10][["cf_Y23_24", "cf_Y24_25", "yoy_24_vs_23_pct", "yoy_rel_to_median_pp", "rel_perf_trend_pct_per_yr", "group", "capacity_kw"]].round(4))
P("YoY > +10pp relative to median:\n", ann[ann.yoy_rel_to_median_pp > 10][["cf_Y23_24", "cf_Y24_25", "yoy_24_vs_23_pct", "yoy_rel_to_median_pp", "rel_perf_trend_pct_per_yr", "group", "capacity_kw"]].round(4))
P("rel-perf trend < -5%/yr:\n", ann[ann.rel_perf_trend_pct_per_yr < -5][["rel_perf_trend_pct_per_yr", "rel_perf_last12m", "rel_perf_prev12m", "cf_Y24_25", "group", "capacity_kw"]].round(4))
P("trend summary: ", ann.rel_perf_trend_pct_per_yr.describe().round(3).to_dict(), "; cap-weighted mean trend %.3f" % np.average(ann.rel_perf_trend_pct_per_yr.dropna(), weights=ann.capacity_kw[ann.rel_perf_trend_pct_per_yr.notna()]))
P("portfolio cap-weighted annual CF by June-May year:", {k: round(float(np.average(ann["cf_" + k].dropna(), weights=ann.capacity_kw[ann["cf_" + k].notna()])), 4) for k in yrs})
P("CF vs capacity: corr(cf_Y24_25, log cap) = %.3f ; mean CF cap<50kW %.4f, 50-100 %.4f, 100-500 %.4f, >500 %.4f" % (ann[["cf_Y24_25"]].assign(l=np.log(ann.capacity_kw)).corr().iloc[0, 1], ann.cf_Y24_25[ann.capacity_kw < 50].mean(), ann.cf_Y24_25[(ann.capacity_kw >= 50) & (ann.capacity_kw < 100)].mean(), ann.cf_Y24_25[(ann.capacity_kw >= 100) & (ann.capacity_kw < 500)].mean(), ann.cf_Y24_25[ann.capacity_kw >= 500].mean()))
def wavg(x, w): m = x.notna(); return float(np.average(x[m], weights=w[m])) if m.any() else np.nan
gstat = ann.groupby("group").apply(lambda d: pd.Series({"n": len(d), "cap_kw": d.capacity_kw.sum(), "cf_Y24_25_mean": d.cf_Y24_25.mean(), "cf_Y24_25_capw": wavg(d.cf_Y24_25, d.capacity_kw), "cf_Y23_24_capw": wavg(d.cf_Y23_24, d.capacity_kw), "cf_Y22_23_capw": wavg(d.cf_Y22_23, d.capacity_kw), "peak_Y24_25_median": d.peak_Y24_25.median(), "cov_Y24_25_mean": d.cov_Y24_25.mean(), "trend_median": d.rel_perf_trend_pct_per_yr.median(), "n_sites_full_val_year": int(full_year.reindex(d.index).sum()), "lat_mean": sites.lat.reindex(d.index).mean(), "lon_mean": sites.lon.reindex(d.index).mean()}))
P("group A vs B:\n", gstat.round(4).T); gstat.to_csv(OUT + "group_AB_compare.csv")
Aj = A.join(grp); P("flags by group:\n", Aj.groupby("current_group")[["n_neg", "n_cf_gt1", "night_gt1pct_h", "day_zero_nbr_h", "val_day_zero_nbr_h", "flat_run_ge4_h_cf_gt5pct", "clip_flag"]].sum())
fig, ax = plt.subplots(1, 3, figsize=(15, 4.5))
for gname, c in [("A", "tab:blue"), ("B", "tab:orange")]:
    d = ann[ann.group == gname]; ax[0].hist(d.cf_Y24_25.dropna(), bins=25, alpha=.6, label=f"{gname} (n={d.cf_Y24_25.notna().sum()})", color=c)
    ax[1].scatter(d.cf_Y23_24, d.cf_Y24_25, s=12, alpha=.7, label=gname, color=c)
ax[0].set_xlabel("annual CF 2024-06..2025-05"); ax[0].legend(); ax[0].set_title("Annual CF by reference group")
lim = [0.08, 0.22]; ax[1].plot(lim, lim, "k--", lw=.8); ax[1].set_xlabel("CF 2023/24"); ax[1].set_ylabel("CF 2024/25"); ax[1].set_title("Year-over-year annual CF"); ax[1].legend()
ax[2].hist(ann.rel_perf_trend_pct_per_yr.dropna(), bins=40); ax[2].set_xlabel("relative performance trend (%/yr, vs portfolio median)"); ax[2].set_title("Degradation / drift (2022-06 ..)")
plt.tight_layout(); plt.savefig(OUT + "fig03_annual_cf_trend.png", dpi=130); plt.close()
ann.round(5).to_csv(OUT + "site_annual_cf.csv")

# ---------- (5) portfolio profile ----------
capv = cap.values[None, :]
port_cf = np.nansum(Cz * capv, 1) / np.maximum((obs * capv).sum(1), 1)
pcf = pd.Series(port_cf, index=ts)
tsv = ts[val]
prof = pcf[val].groupby([tsv.month, tsv.hour]).mean().unstack()
prof.to_csv(OUT + "portfolio_cf_month_hour_val.csv", float_format="%.4f")
E = np.nansum(Cz * capv, 1)
smp = pd.read_parquet(CACHE + "smp_all.parquet"); smp = smp.set_index("ts").reindex(ts)
w = (smp.smp * smp.k).values.astype(float); smpv = smp.smp.values.astype(float)
Ev = pd.Series(E, index=ts)[val]; kmask = np.isin(tsv.hour, [11, 12, 13, 14, 15])
P("VAL year: share of kWh in ts-hour 11..15: %.2f%% ; SMP-weighted share %.2f%% ; w(=SMP*k)-weighted share %.2f%%" % (100 * Ev[kmask].sum() / Ev.sum(), 100 * (Ev * smpv[val])[kmask].sum() / (Ev * smpv[val]).sum(), 100 * (Ev * w[val])[kmask].sum() / (Ev * w[val]).sum()))
P("VAL year: share of kWh by ts-hour (%):\n", (100 * Ev.groupby(tsv.hour).sum() / Ev.sum()).round(2).to_string())
P("VAL year: share of w-weighted kWh by ts-hour (%):\n", (100 * (Ev * w[val]).groupby(tsv.hour).sum() / (Ev * w[val]).sum()).round(2).to_string())
share_m = (100 * Ev[kmask].groupby(tsv[kmask].month).sum() / Ev.groupby(tsv.month).sum()).round(2)
P("share of kWh in 11..15 by month (val year):", share_m.to_dict())
P("portfolio capacity-weighted CF val year: %.4f; by month:" % pcf[val].mean(), pcf[val].groupby(tsv.month).mean().round(4).to_dict())
P("portfolio hourly mean CF (val year):", pcf[val].groupby(tsv.hour).mean().round(4).to_dict())
P("max portfolio CF (val):", float(pcf[val].max()), "at", pcf[val].idxmax(), "; p99 %.3f" % pcf[val].quantile(.99))
P("mean SMP by hour (val):", smp.smp[val].groupby(tsv.hour).mean().round(1).to_dict())
P("mean SMP (val) %.2f ; hours with SMP==0: %d ; mean SMP in 11..15: %.2f" % (smp.smp[val].mean(), int((smp.smp[val] == 0).sum()), smp.smp[val][kmask].mean()))
fig, ax = plt.subplots(1, 2, figsize=(14, 4.5))
im = ax[0].imshow(prof.values, aspect="auto", cmap="inferno", origin="lower"); ax[0].set_yticks(range(12)); ax[0].set_yticklabels(prof.index); ax[0].set_xticks(range(0, 24, 2)); ax[0].set_xticklabels(prof.columns[::2]); ax[0].set_xlabel("ts hour (right-closed)"); ax[0].set_ylabel("month"); ax[0].set_title("Portfolio cap-weighted CF, 2024-06..2025-05"); plt.colorbar(im, ax=ax[0])
for mth in [1, 4, 7, 10]: ax[1].plot(prof.columns, prof.loc[mth], label=f"month {mth}")
ax[1].axvspan(10.5, 15.5, color="red", alpha=.1, label="k=3 (ts 11..15)"); ax[1].legend(); ax[1].set_xlabel("ts hour"); ax[1].set_ylabel("CF"); ax[1].set_title("Diurnal profile by season")
plt.tight_layout(); plt.savefig(OUT + "fig04_portfolio_profile.png", dpi=130); plt.close()

# ---------- missing-as-zero impact (val year) ----------
miss = (~obs) & val[:, None]
miss_day = miss & day
exp_cf = np.where(np.isnan(port_cf), 0, port_cf)[:, None]
site_miss = pd.DataFrame(index=cf.columns)
site_miss["val_missing_h"] = miss.sum(0); site_miss["val_missing_day_h"] = miss_day.sum(0)
site_miss["val_missing_day_share_pct"] = 100 * miss_day.sum(0) / (val[:, None] & day).sum(0)
site_miss["exp_missing_kwh"] = (miss * exp_cf * capv).sum(0)
site_miss["exp_annual_kwh"] = (val[:, None] * exp_cf * capv).sum(0)
site_miss["exp_missing_kwh_share_pct"] = 100 * site_miss.exp_missing_kwh / site_miss.exp_annual_kwh
site_miss["w_missing"] = (miss * exp_cf * capv * w[:, None]).sum(0)
site_miss["w_annual"] = (val[:, None] * exp_cf * capv * w[:, None]).sum(0)
site_miss["w_missing_share_pct"] = 100 * site_miss.w_missing / site_miss.w_annual
site_miss["capacity_kw"] = cap; site_miss["group"] = grp
P("VAL year missing: total (site,ts) %d ; daytime %d ; sites with 0 missing: %d ; sites with missing-day-share>1%%: %d ; >5%%: %d ; >20%%: %d" % (miss.sum(), miss_day.sum(), (site_miss.val_missing_h == 0).sum(), (site_miss.val_missing_day_share_pct > 1).sum(), (site_miss.val_missing_day_share_pct > 5).sum(), (site_miss.val_missing_day_share_pct > 20).sum()))
tot_exp = site_miss.exp_missing_kwh.sum(); tot_act = Ev.sum()
P("expected kWh in missing slots (val): %.0f = %.2f%% of reported portfolio kWh %.0f" % (tot_exp, 100 * tot_exp / tot_act, tot_act))
P("w-weighted: missing %.4e vs reported %.4e => %.2f%%; penalty if forecast perfect & missing scored as 0 = 0.1*w_missing = %.4e KRW vs revenue Σsmp*actual = %.4e KRW (%.3f%%)" % (site_miss.w_missing.sum(), (Ev * w[val]).sum(), 100 * site_miss.w_missing.sum() / (Ev * w[val]).sum(), 0.1 * site_miss.w_missing.sum(), (Ev * smpv[val]).sum(), 100 * 0.1 * site_miss.w_missing.sum() / (Ev * smpv[val]).sum()))
P("by group (val): expected missing kWh share %:", site_miss.groupby("group").apply(lambda d: 100 * d.exp_missing_kwh.sum() / d.exp_annual_kwh.sum()).round(3).to_dict())
P("missing-day-share distribution (%):", site_miss.val_missing_day_share_pct.describe(percentiles=[.5, .75, .9, .95]).round(3).to_dict())
P("top 25 sites by w-missing:\n", site_miss.sort_values("w_missing", ascending=False).head(25).round(3))
P("concentration: top-10 sites hold %.1f%% of w_missing; top-20 %.1f%%; top-5 %.1f%%" % (100 * site_miss.w_missing.nlargest(10).sum() / site_miss.w_missing.sum(), 100 * site_miss.w_missing.nlargest(20).sum() / site_miss.w_missing.sum(), 100 * site_miss.w_missing.nlargest(5).sum() / site_miss.w_missing.sum()))
P("excluding sites with missing-day-share>20%%: remaining w_missing share = %.3f%% of reported w-kWh" % (100 * site_miss.w_missing[site_miss.val_missing_day_share_pct <= 20].sum() / (Ev * w[val]).sum()))
site_miss.round(4).to_csv(OUT + "site_missing_val_year.csv")
mm = pd.Series((miss * exp_cf * capv).sum(1), index=ts)[val].groupby(tsv.month).sum()
P("expected missing kWh by month (val):", mm.round(0).to_dict())
# daily count of sites missing in val year (how bursty?)
dm = pd.Series(miss.sum(1), index=ts)[val].groupby(tsv.date).sum()
P("val: days with >= 24*5 missing site-hours (>=5 site-days):", int((dm >= 120).sum()), "; max site-hours missing in one day:", int(dm.max()), "on", dm.idxmax())
top = site_miss.sort_values("w_missing_share_pct", ascending=False).head(30)
fig, ax = plt.subplots(figsize=(12, 4.5)); ax.bar(range(len(top)), top.w_missing_share_pct, color=["tab:blue" if g == "A" else "tab:orange" for g in top.group]); ax.set_xticks(range(len(top))); ax.set_xticklabels(top.index, rotation=90, fontsize=7); ax.set_ylabel("% of annual w-weighted expected kWh missing"); ax.set_title("Val-year missing-daytime weight share, top 30 sites (blue=A, orange=B)")
plt.tight_layout(); plt.savefig(OUT + "fig05_missing_val_year.png", dpi=130); plt.close()

# ---------- example figures: clipping ----------
ex = list(A.sort_values("n_plateau_days_of_top40", ascending=False).head(4).index)
fig, axs = plt.subplots(2, 2, figsize=(12, 7)); axs = axs.ravel()
for k, sid in enumerate(ex):
    j = cf.columns.get_loc(sid); top = np.argsort(daily[:, j])[::-1][:12]
    for d in top:
        rows = np.flatnonzero(dinv == d); axs[k].plot(h[rows], C[rows, j], alpha=.6, lw=.8)
    axs[k].set_title(f"{sid} cap={cap[sid]:.0f}kW top-12 days (plateau {A.loc[sid,'n_plateau_days_of_top40']}/40, p99.5={A.loc[sid,'p995_cf']:.2f})", fontsize=9); axs[k].set_xlabel("ts hour"); axs[k].set_ylabel("CF")
plt.tight_layout(); plt.savefig(OUT + "fig06_clipping_examples.png", dpi=130); plt.close()
# distribution figure of anomalies
fig, ax = plt.subplots(1, 3, figsize=(15, 4))
ax[0].scatter(cap, A.val_p99_cf, s=10); ax[0].set_xscale("log"); ax[0].set_xlabel("capacity kW"); ax[0].set_ylabel("val-year daytime p99 CF"); ax[0].set_title("Peak CF vs capacity (low = capacity overstated?)")
ax[1].hist(A.night_gt1pct_h.clip(upper=200), bins=40); ax[1].set_xlabel("night hours with CF>1% (clipped at 200)"); ax[1].set_title("Night-time nonzero")
ax[2].hist(A.day_zero_nbr_h.clip(upper=500), bins=40); ax[2].set_xlabel("daytime zero hours while neighbours >0.15 CF (clipped 500)"); ax[2].set_title("Outage proxy")
plt.tight_layout(); plt.savefig(OUT + "fig07_anomaly_distributions.png", dpi=130); plt.close()

# ---------- (6) risk table ----------
R = per_site.join(A.drop(columns=["n_neg"])).join(ann[["cf_Y24_25", "cf_Y23_24", "yoy_rel_to_median_pp", "rel_perf_trend_pct_per_yr", "rel_perf_last12m"]]).join(site_miss[["val_missing_day_share_pct", "w_missing_share_pct"]]).join(sites[["current_group", "capacity_kw"]]).join(res)
reasons = []
for sid, r in R.iterrows():
    rs = []
    if r.last_ts < VAL1 - pd.Timedelta("7D"): rs.append(f"stopped reporting {r.last_ts.date()}")
    if r.first_ts > VAL0: rs.append(f"started {r.first_ts.date()} (<1y history)")
    if r.val_missing_day_share_pct > 5: rs.append(f"val missing daytime {r.val_missing_day_share_pct:.1f}%")
    if pd.notna(r.n_gaps_ge7d) and r.n_gaps_ge7d >= 1 and r.first_ts <= VAL0: rs.append(f"{int(r.n_gaps_ge7d)} gaps>=7d (longest {int(r.longest_gap_h)}h)")
    if r.n_cf_gt1 > 0: rs.append(f"CF>1 x{int(r.n_cf_gt1)}")
    if r.n_neg > 0: rs.append(f"neg x{int(r.n_neg)}")
    if r.night_gt1pct_h > 20: rs.append(f"night CF>1% x{int(r.night_gt1pct_h)}")
    if r.val_day_zero_nbr_h >= 24: rs.append(f"val daytime zeros vs nbrs {int(r.val_day_zero_nbr_h)}h")
    if r.val_flat_ge4_cf_gt5pct_h >= 24: rs.append(f"val flat-lines {int(r.val_flat_ge4_cf_gt5pct_h)}h")
    if r.clip_flag: rs.append(f"clipping plateau (level {r.mid_level_topdays:.2f})")
    if pd.notna(r.p99_vs_peer_median) and r.p99_vs_peer_median < 0.6: rs.append(f"p99 CF {r.val_p99_cf:.2f} = {r.p99_vs_peer_median:.2f}x peers (capacity?)")
    if pd.notna(r.yoy_rel_to_median_pp) and r.yoy_rel_to_median_pp < -10: rs.append(f"YoY {r.yoy_rel_to_median_pp:+.1f}pp vs median")
    if pd.notna(r.rel_perf_trend_pct_per_yr) and r.rel_perf_trend_pct_per_yr < -5: rs.append(f"trend {r.rel_perf_trend_pct_per_yr:+.1f}%/yr")
    if r.val_day_underprod_h >= 100: rs.append(f"val under-prod(<30% nbrs) {int(r.val_day_underprod_h)}h")
    reasons.append("; ".join(rs))
R["risk_reasons"] = reasons; R["n_flags"] = [len(x.split("; ")) if x else 0 for x in reasons]
sev = ((R.last_ts < VAL1 - pd.Timedelta("7D")) * 5 + (R.first_ts > VAL0) * 3 + (R.val_missing_day_share_pct > 5) * 3 + (R.val_missing_day_share_pct > 20) * 3 + (R.val_day_zero_nbr_h >= 24) * 2 + (R.yoy_rel_to_median_pp < -10).fillna(False) * 2 + (R.rel_perf_trend_pct_per_yr < -5).fillna(False) * 2 + (R.p99_vs_peer_median < 0.6).fillna(False) * 2 + (R.val_flat_ge4_cf_gt5pct_h >= 24) * 1 + (R.night_gt1pct_h > 20) * 1 + (R.n_cf_gt1 > 0) * 1 + (R.clip_flag) * 1 + (R.val_day_underprod_h >= 100) * 2)
R["risk_score"] = sev.astype(int)
R.round(4).to_csv(OUT + "site_quality_full.csv")
risky = R[R.risk_score >= 3].sort_values("risk_score", ascending=False)
risky[["current_group", "capacity_kw", "first_ts", "last_ts", "val_coverage_pct", "val_missing_day_share_pct", "w_missing_share_pct", "cf_Y24_25", "risk_score", "risk_reasons"]].to_csv(OUT + "risky_sites.csv")
P("RISKY sites (score>=3): n=%d, capacity %.0f kW (A %.0f, B %.0f)" % (len(risky), risky.capacity_kw.sum(), risky[risky.current_group == "A"].capacity_kw.sum(), risky[risky.current_group == "B"].capacity_kw.sum()))
P(risky[["current_group", "capacity_kw", "val_coverage_pct", "cf_Y24_25", "risk_score", "risk_reasons"]].to_string())
P("flag counts:", {c: int((R[c] > 0).sum()) for c in ["n_neg", "n_cf_gt1"]}, "night>20:", int((R.night_gt1pct_h > 20).sum()), "clip:", int(R.clip_flag.sum()), "lowcap:", int((R.p99_vs_peer_median < 0.6).sum()), "val_dayzero>=24:", int((R.val_day_zero_nbr_h >= 24).sum()), "val_flat>=24:", int((R.val_flat_ge4_cf_gt5pct_h >= 24).sum()), "yoy<-10:", int((R.yoy_rel_to_median_pp < -10).sum()), "trend<-5:", int((R.rel_perf_trend_pct_per_yr < -5).sum()), "underprod>=100:", int((R.val_day_underprod_h >= 100).sum()))
P("risk score distribution:", R.risk_score.value_counts().sort_index().to_dict())
P("clean sites (score 0): n=%d cap=%.0f kW; score<=1: n=%d cap=%.0f; score<=2: n=%d cap=%.0f" % ((R.risk_score == 0).sum(), R.capacity_kw[R.risk_score == 0].sum(), (R.risk_score <= 1).sum(), R.capacity_kw[R.risk_score <= 1].sum(), (R.risk_score <= 2).sum(), R.capacity_kw[R.risk_score <= 2].sum()))
P("clean by group: ", R[R.risk_score <= 1].groupby("current_group").capacity_kw.agg(["count", "sum"]).to_dict())
P("meter resolution (min step kWh) distribution:", res.describe().round(3).to_dict(), "; sites with step>=1 kWh:", int((res >= 1).sum()), "; step>=0.1:", int((res >= 0.1).sum()))
P("DONE")
