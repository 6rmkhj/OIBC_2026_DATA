# spatial_corr: site map, capacity/feasibility, CF correlation structure, station sharing, twins, smoothing, outliers
import os, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, fcluster, leaves_list
from scipy.optimize import curve_fit

BASE = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad"
OUT = f"{BASE}/analysis/out"; os.makedirs(OUT, exist_ok=True)
SITES = "C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset/sites.csv"
rng = np.random.default_rng(0)
def P(*a): print(*a, flush=True)

sites = pd.read_csv(SITES).set_index("site_id")
ids = list(sites.index); n = len(ids)
cap = sites.capacity_kw.values.astype(np.float64)
TOTAL = cap.sum()
P("n sites", n, "total kW", round(TOTAL, 2))

# ---------- (1) map + capacity + feasibility ----------
colors = sites.current_group.map({"A": "tab:blue", "B": "tab:orange"})
fig, ax = plt.subplots(figsize=(8, 9))
ax.scatter(sites.lon, sites.lat, s=8 + cap / 4, c=colors, alpha=0.6, edgecolor="k", linewidth=0.3)
for sid in sites.index[cap > 500]:
    ax.annotate(f"{sid}\n{sites.capacity_kw[sid]:.0f}kW", (sites.lon[sid], sites.lat[sid]), fontsize=7)
ax.scatter([], [], c="tab:blue", label="group A (G1 ref)"); ax.scatter([], [], c="tab:orange", label="group B (G2 ref)")
ax.legend(); ax.set_xlabel("lon"); ax.set_ylabel("lat"); ax.set_title("253 PV sites (marker size ~ capacity)"); ax.grid(alpha=.3)
ax.set_aspect(1 / np.cos(np.deg2rad(36)))
fig.tight_layout(); fig.savefig(f"{OUT}/sc_fig1_map_sites.png", dpi=130); plt.close(fig)

bins = [0, 50, 90, 100.5, 200, 500, 1000, 2000]
labels = ["<50", "50-90", "90-100.5 (~100kW)", "100.5-200", "200-500", "500-1000", ">1000"]
cb = pd.cut(sites.capacity_kw, bins, labels=labels)
capdist = sites.groupby(cb, observed=False).agg(n_sites=("capacity_kw", "size"), kW=("capacity_kw", "sum"))
capdist["kW_share_%"] = 100 * capdist.kW / TOTAL
capdist.to_csv(f"{OUT}/sc_capacity_bins.csv"); P(capdist)
P("exact 99.96 kW:", (sites.capacity_kw == 99.96).sum(), " in [99,100.5]:", sites.capacity_kw.between(99, 100.5).sum())
top = sites.sort_values("capacity_kw", ascending=False).head(15)[["current_group", "capacity_kw", "lat", "lon"]]
top.to_csv(f"{OUT}/sc_top15_capacity.csv"); P(top)
fig, ax = plt.subplots(figsize=(8, 4)); ax.hist(sites.capacity_kw, bins=np.arange(0, 1450, 25), color="steelblue")
ax.set_yscale("log"); ax.set_xlabel("capacity kW"); ax.set_ylabel("sites (log)"); ax.set_title("Capacity distribution")
fig.tight_layout(); fig.savefig(f"{OUT}/sc_fig2_capacity_hist.png", dpi=130); plt.close(fig)

gsum = sites.groupby("current_group").capacity_kw.sum()
lo, hi = 20000.0, TOTAL - 20000.0
feas = pd.DataFrame({
    "item": ["total_kW", "G_min", "G_max", "window_width", "ref_A_kW", "ref_B_kW", "A_slack_above_min", "B_slack_above_min",
             "max_net_move_A_to_B", "max_net_move_B_to_A", "n_sites_too_big_to_move_from_A_alone", "n_sites_too_big_to_move_from_B_alone"],
    "value": [TOTAL, lo, hi, hi - lo, gsum["A"], gsum["B"], gsum["A"] - lo, gsum["B"] - lo, gsum["A"] - lo, gsum["B"] - lo,
              int(((sites.current_group == "A") & (sites.capacity_kw > gsum["A"] - lo)).sum()),
              int(((sites.current_group == "B") & (sites.capacity_kw > gsum["B"] - lo)).sum())]})
feas.to_csv(f"{OUT}/sc_feasibility.csv", index=False); P(feas)
ok = 0; R = 20000
for _ in range(R):
    m = rng.random(n) < 0.5; s = cap[m].sum(); ok += (lo <= s <= hi)
P(f"random Bernoulli(0.5) splits feasible: {100*ok/R:.1f}%")

# ---------- (2) correlation structure ----------
cf = pd.read_parquet(f"{BASE}/cache/cf_wide.parquet")[ids]
cf = cf.loc["2023-06-01 01:00:00+09:00":"2025-06-01 00:00:00+09:00"]
P("cf window", cf.index[0], cf.index[-1], cf.shape)
coverage = cf.notna().mean()
pm = cf.mean(axis=1)
day = pm > 0.05
cfd = cf[day]
P("daytime hours used", int(day.sum()), "of", len(cf))
idx = cfd.index
clim = cfd.groupby([idx.month, idx.hour]).transform("mean")
an = (cfd - clim).astype(np.float32)
del clim
dkey = (idx - pd.Timedelta(hours=1)).date
cnt = cfd.notna().groupby(dkey).sum()
need = pd.Series(pd.Index(dkey).value_counts()).reindex(cnt.index)
dsum = cfd.groupby(dkey).sum(min_count=1)
dsum = dsum.where(cnt.ge(0.8 * need.values[:, None]))
P("daily rows", dsum.shape, "mean non-NaN per site", round(dsum.notna().mean().mean(), 3))
dmon = pd.DatetimeIndex(pd.to_datetime(dsum.index)).month
dan = dsum - dsum.groupby(dmon).transform("mean")
C_h = cfd.corr(min_periods=500); C_a = an.corr(min_periods=500); C_d = dsum.corr(min_periods=120); C_da = dan.corr(min_periods=120)
for nm, C in [("hourly", C_h), ("anom", C_a), ("daily", C_d), ("daily_anom", C_da)]:
    C.to_csv(f"{OUT}/sc_corr_{nm}.csv")
iu = np.triu_indices(n, 1)
P("NaN pairs: hourly %d anom %d daily %d" % (np.isnan(C_h.values[iu]).sum(), np.isnan(C_a.values[iu]).sum(), np.isnan(C_d.values[iu]).sum()))
# robustness: full-panel period (all 253 sites online from 2024-08)
fp = an.loc["2024-08-01 01:00:00+09:00":]
C_fp = fp.corr(min_periods=500)
P("full-panel period rows", len(fp), "mean pairwise anom corr %.3f (2y window: %.3f)" % (np.nanmean(C_fp.values[iu]), np.nanmean(C_a.values[iu])))
first_valid = pd.read_parquet(f"{BASE}/cache/cf_wide.parquet")[ids].apply(lambda x: x.first_valid_index())
del fp
la, lo_ = np.deg2rad(sites.lat.values), np.deg2rad(sites.lon.values)
dlat = la[:, None] - la[None, :]; dlon = lo_[:, None] - lo_[None, :]
D = 6371 * 2 * np.arcsin(np.sqrt(np.sin(dlat / 2) ** 2 + np.cos(la[:, None]) * np.cos(la[None, :]) * np.sin(dlon / 2) ** 2))
Ddf = pd.DataFrame(D, index=ids, columns=ids); Ddf.to_csv(f"{OUT}/sc_distance_km.csv")
pairs = pd.DataFrame({"i": np.array(ids)[iu[0]], "j": np.array(ids)[iu[1]], "dist_km": D[iu],
                      "corr_hourly": C_h.values[iu], "corr_anom": C_a.values[iu], "corr_daily": C_d.values[iu], "corr_daily_anom": C_da.values[iu]})
P("pair dist km: median %.1f mean %.1f max %.1f" % (pairs.dist_km.median(), pairs.dist_km.mean(), pairs.dist_km.max()))
CC = ["corr_hourly", "corr_anom", "corr_daily", "corr_daily_anom"]
summ = pairs[CC].describe().T; summ.to_csv(f"{OUT}/sc_corr_summary.csv"); P(summ)
dbins = [0, 5, 10, 20, 30, 50, 75, 100, 150, 200, 300, 400]
pairs["dbin"] = pd.cut(pairs.dist_km, dbins)
decay = pairs.groupby("dbin", observed=False).agg(n_pairs=("dist_km", "size"), dist_mean=("dist_km", "mean"),
    corr_hourly=("corr_hourly", "mean"), corr_anom=("corr_anom", "mean"), corr_daily=("corr_daily", "mean"), corr_daily_anom=("corr_daily_anom", "mean"),
    corr_anom_median=("corr_anom", "median"), corr_anom_p10=("corr_anom", lambda x: x.quantile(.1)))
decay.to_csv(f"{OUT}/sc_dist_corr_decay.csv"); P(decay.round(3))
def expdec(d, a, L, c): return a * np.exp(-d / L) + c
fits = {}
for col in CC:
    m = pairs[col].notna()
    try:
        p, _ = curve_fit(expdec, pairs.dist_km[m], pairs[col][m], p0=[0.5, 100, 0.3], bounds=([0, 1, -1], [2, 3000, 1]), maxfev=20000)
        fits[col] = dict(a=p[0], L_km=p[1], c=p[2])
    except Exception as e: fits[col] = dict(err=str(e))
fitdf = pd.DataFrame(fits).T; fitdf.to_csv(f"{OUT}/sc_decay_fit.csv"); P("exp decay fits:\n", fitdf)
fig, ax = plt.subplots(figsize=(8, 5))
sub = pairs.sample(min(8000, len(pairs)), random_state=0)
ax.scatter(sub.dist_km, sub.corr_anom, s=3, alpha=.15, color="gray", label="pairs (anomaly, sample)")
for col, c in [("corr_hourly", "tab:blue"), ("corr_anom", "tab:red"), ("corr_daily", "tab:green"), ("corr_daily_anom", "tab:purple")]:
    ax.plot(decay.dist_mean, decay[col], "o-", color=c, label=f"{col} (bin mean)")
    if "L_km" in fits[col]:
        xx = np.linspace(0, 400, 200); ax.plot(xx, expdec(xx, fits[col]["a"], fits[col]["L_km"], fits[col]["c"]), "--", color=c, alpha=.6)
ax.set_xlabel("distance km"); ax.set_ylabel("Pearson corr"); ax.set_title("Correlation vs distance (daytime CF, 2023-06..2025-05)"); ax.legend(); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/sc_fig4_dist_corr_decay.png", dpi=130); plt.close(fig)

Ca = C_a.values.copy(); np.fill_diagonal(Ca, 1)
# fill the few NaN pairs with the distance-decay prediction, then Ward on sqrt(2(1-rho))
if "L_km" in fits["corr_anom"]:
    pred = expdec(D, fits["corr_anom"]["a"], fits["corr_anom"]["L_km"], fits["corr_anom"]["c"]); Ca = np.where(np.isnan(Ca), pred, Ca)
Ca = np.nan_to_num(Ca, nan=0.0); Ca = (Ca + Ca.T) / 2
dist_c = np.sqrt(np.clip(2 * (1 - Ca), 0, 4))
Z = linkage(dist_c[np.triu_indices(n, 1)], method="ward")
order = leaves_list(Z)
clus = pd.DataFrame(index=ids)
for k in [4, 6, 8, 12]: clus[f"cluster_k{k}"] = fcluster(Z, k, criterion="maxclust")
clus = clus.join(sites[["current_group", "capacity_kw", "lat", "lon", "wa_station", "wb_station"]])
clus.to_csv(f"{OUT}/sc_clusters.csv")
for k in [4, 6, 8]:
    g = clus.groupby(f"cluster_k{k}").agg(n=("capacity_kw", "size"), kW=("capacity_kw", "sum"), lat=("lat", "mean"), lon=("lon", "mean"),
                                         nA=("current_group", lambda x: (x == "A").sum()), nB=("current_group", lambda x: (x == "B").sum()))
    wc = []
    for c, members in clus.groupby(f"cluster_k{k}").groups.items():
        ii = [ids.index(s) for s in members]; sub = Ca[np.ix_(ii, ii)]
        wc.append(sub[np.triu_indices(len(ii), 1)].mean() if len(ii) > 1 else np.nan)
    g["within_corr_anom"] = wc
    g.to_csv(f"{OUT}/sc_cluster_summary_k{k}.csv"); P(f"clusters k={k}:\n", g.round(3))
fig, axs = plt.subplots(1, 2, figsize=(15, 8))
for ax, k in zip(axs, [6, 8]):
    sc = ax.scatter(clus.lon, clus.lat, c=clus[f"cluster_k{k}"], cmap="tab10", s=10 + clus.capacity_kw / 4, edgecolor="k", linewidth=.3, alpha=.8)
    ax.set_aspect(1 / np.cos(np.deg2rad(36))); ax.set_title(f"Ward clusters k={k} (on sqrt(2(1-corr)) of CF anomaly)")
    ax.set_xlabel("lon"); ax.set_ylabel("lat"); plt.colorbar(sc, ax=ax, label="cluster", fraction=.04); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{OUT}/sc_fig5_cluster_map.png", dpi=130); plt.close(fig)
fig, axs = plt.subplots(1, 2, figsize=(14, 6.5))
for ax, (nm, C) in zip(axs, [("hourly daytime CF", C_h), ("CF anomaly (climatology removed)", C_a)]):
    im = ax.imshow(C.values[np.ix_(order, order)], vmin=0, vmax=1, cmap="viridis"); ax.set_title(f"corr: {nm}\n(sites ordered by cluster dendrogram)")
    plt.colorbar(im, ax=ax, fraction=.046)
fig.tight_layout(); fig.savefig(f"{OUT}/sc_fig3_corr_heatmap.png", dpi=130); plt.close(fig)

# ---------- (3) station sharing ----------
st = {}
for prov in ["wa", "wb"]:
    vc = sites[f"{prov}_station"].value_counts()
    vc.to_csv(f"{OUT}/sc_station_counts_{prov}.csv")
    st[prov] = dict(n_stations_used=len(vc), max_sites_per_station=int(vc.max()), mean_sites_per_station=vc.mean(),
                    n_stations_with_1_site=int((vc == 1).sum()), n_stations_with_ge5=int((vc >= 5).sum()), n_stations_with_ge10=int((vc >= 10).sum()),
                    dist_km_mean=sites[f"{prov}_dist"].mean() / 1000, dist_km_median=sites[f"{prov}_dist"].median() / 1000, dist_km_max=sites[f"{prov}_dist"].max() / 1000,
                    top5=";".join(f"{k}:{v}" for k, v in vc.head(5).items()))
stdf = pd.DataFrame(st).T; stdf.to_csv(f"{OUT}/sc_station_stats.csv"); P(stdf)
wa = sites.wa_station.values; wb = sites.wb_station.values
pairs["same_wa"] = wa[iu[0]] == wa[iu[1]]; pairs["same_wb"] = wb[iu[0]] == wb[iu[1]]
pairs["same_both"] = pairs.same_wa & pairs.same_wb
pairs["same_group"] = sites.current_group.values[iu[0]] == sites.current_group.values[iu[1]]
pairs.to_csv(f"{OUT}/sc_pairs.csv", index=False)
near = pairs[pairs.dist_km <= 30].copy(); near["dbin2"] = pd.cut(near.dist_km, [0, 5, 10, 15, 20, 30])
rows = []
for col in ["same_wa", "same_wb"]:
    g = near.groupby(["dbin2", col], observed=False).agg(n=("corr_anom", "size"), corr_anom=("corr_anom", "mean"), corr_daily=("corr_daily", "mean"), dist=("dist_km", "mean")).reset_index()
    g["which"] = col; rows.append(g)
share = pd.concat(rows); share.to_csv(f"{OUT}/sc_station_sharing_test.csv", index=False); P(share.round(3))
P("same_wa pairs:", int(pairs.same_wa.sum()), "mean dist %.1f km, corr_anom %.3f" % (pairs[pairs.same_wa].dist_km.mean(), pairs[pairs.same_wa].corr_anom.mean()))
P("same_wb pairs:", int(pairs.same_wb.sum()), "mean dist %.1f km, corr_anom %.3f" % (pairs[pairs.same_wb].dist_km.mean(), pairs[pairs.same_wb].corr_anom.mean()))
P("same_both pairs:", int(pairs.same_both.sum()), "corr_anom %.3f" % pairs[pairs.same_both].corr_anom.mean())
fig, axs = plt.subplots(1, 2, figsize=(12, 4.5))
for ax, prov in zip(axs, ["wa", "wb"]):
    vc = sites[f"{prov}_station"].value_counts()
    ax.bar(range(len(vc)), vc.values, color="steelblue"); ax.set_title(f"sites per {prov} station ({len(vc)} stations used)"); ax.set_xlabel("station rank"); ax.set_ylabel("# sites")
fig.tight_layout(); fig.savefig(f"{OUT}/sc_fig6_station_sharing.png", dpi=130); plt.close(fig)

# ---------- (4) twins ----------
Cm = C_a.values.copy(); np.fill_diagonal(Cm, -np.inf); Cm = np.where(np.isnan(Cm), -np.inf, Cm)
Ch = C_h.values.copy(); np.fill_diagonal(Ch, -np.inf); Ch = np.where(np.isnan(Ch), -np.inf, Ch)
Dn = D.copy(); np.fill_diagonal(Dn, np.inf)
tw = pd.DataFrame(index=ids)
tw["twin_anom"] = np.array(ids)[Cm.argmax(1)]; tw["twin_anom_corr"] = Cm.max(1); tw["twin_anom_dist_km"] = D[np.arange(n), Cm.argmax(1)]
tw["twin_hourly"] = np.array(ids)[Ch.argmax(1)]; tw["twin_hourly_corr"] = Ch.max(1); tw["twin_hourly_dist_km"] = D[np.arange(n), Ch.argmax(1)]
tw["nearest_site"] = np.array(ids)[Dn.argmin(1)]; tw["nearest_dist_km"] = Dn.min(1); tw["nearest_corr_anom"] = Cm[np.arange(n), Dn.argmin(1)]
rank = (-Cm).argsort(1).argsort(1); tw["nearest_rank_by_corr"] = rank[np.arange(n), Dn.argmin(1)] + 1
tw["twin_same_group"] = sites.current_group.values == sites.current_group.reindex(tw.twin_anom).values
tw["twin_same_wa"] = wa == sites.wa_station.reindex(tw.twin_anom).values
tw["twin_same_wb"] = wb == sites.wb_station.reindex(tw.twin_anom).values
tw["mutual_twin"] = tw.twin_anom.map(tw.twin_anom) == tw.index
tw["mean_corr_anom_others"] = np.nanmean(np.where(np.isfinite(Cm), Cm, np.nan), 1)
tw = tw.join(sites[["current_group", "capacity_kw", "wa_station", "wb_station"]])
tw.to_csv(f"{OUT}/sc_twins.csv")
P("twin (anom): median dist %.1f km, mean %.1f, <=10km %.0f%%, <=20km %.0f%%, median corr %.3f" % (tw.twin_anom_dist_km.median(), tw.twin_anom_dist_km.mean(),
  100 * (tw.twin_anom_dist_km <= 10).mean(), 100 * (tw.twin_anom_dist_km <= 20).mean(), tw.twin_anom_corr.median()))
P("twin in same ref group: %.1f%%  same_wa %.1f%%  same_wb %.1f%%  mutual %.1f%%  nearest==twin %.1f%%  nearest median rank %d" % (100 * tw.twin_same_group.mean(),
  100 * tw.twin_same_wa.mean(), 100 * tw.twin_same_wb.mean(), 100 * tw.mutual_twin.mean(), 100 * (tw.nearest_site == tw.twin_anom).mean(), tw.nearest_rank_by_corr.median()))
P("twin_hourly == twin_anom: %.1f%%" % (100 * (tw.twin_hourly == tw.twin_anom).mean()))
fig, axs = plt.subplots(1, 2, figsize=(14, 6.5))
ax = axs[0]; ax.scatter(sites.lon, sites.lat, s=12, c=colors, alpha=.7)
for s in ids:
    t = tw.twin_anom[s]; ax.plot([sites.lon[s], sites.lon[t]], [sites.lat[s], sites.lat[t]], "-", color="red" if tw.twin_same_group[s] else "green", lw=.7, alpha=.6)
ax.set_aspect(1 / np.cos(np.deg2rad(36))); ax.set_title("site -> twin (max anomaly corr). red: same ref group, green: split"); ax.grid(alpha=.3)
ax = axs[1]; ax.hist(tw.twin_anom_dist_km, bins=40, color="steelblue"); ax.set_xlabel("distance to twin km"); ax.set_ylabel("# sites"); ax.set_title("Twin distance")
fig.tight_layout(); fig.savefig(f"{OUT}/sc_fig7_twins.png", dpi=130); plt.close(fig)

# ---------- (5) smoothing ----------
A = an.values.astype(np.float32)
H = cfd.values.astype(np.float32)
site_sd_an = np.nanstd(A, 0); site_sd_h = np.nanstd(H, 0)
w = cap / TOTAL
def wmean(M, wv):
    m = ~np.isnan(M); ww = m * wv[None, :]; return np.nansum(np.nan_to_num(M) * ww, 1) / np.maximum(ww.sum(1), 1e-9)
port_an = wmean(A, w); port_h = wmean(H, w); port_an_eq = np.nanmean(A, 1)
sm = {"mean_site_std_anom": site_sd_an.mean(), "portfolio_capw_std_anom": port_an.std(), "portfolio_eqw_std_anom": port_an_eq.std(),
      "ratio_capw_anom": port_an.std() / site_sd_an.mean(), "mean_site_std_hourlyCF": site_sd_h.mean(), "portfolio_capw_std_hourlyCF": port_h.std(),
      "ratio_capw_hourly": port_h.std() / site_sd_h.mean(), "mean_pairwise_corr_anom": np.nanmean(C_a.values[iu]), "mean_pairwise_corr_hourly": np.nanmean(C_h.values[iu]),
      "mean_pairwise_corr_daily": np.nanmean(C_d.values[iu])}
sm["n_eff_anom(1/rho)"] = 1 / sm["mean_pairwise_corr_anom"]
gA = (sites.current_group == "A").values; gB = ~gA
GA = wmean(A, np.where(gA, cap, 0) / cap[gA].sum()); GB = wmean(A, np.where(gB, cap, 0) / cap[gB].sum())
sm["refG1_std_anom"] = GA.std(); sm["refG2_std_anom"] = GB.std(); sm["corr_refG1_refG2_anom"] = np.corrcoef(GA, GB)[0, 1]
smdf = pd.Series(sm); smdf.to_csv(f"{OUT}/sc_smoothing_summary.csv"); P(smdf.round(4))
Dd = dsum.values.astype(np.float32); dsd = np.nanstd(Dd, 0); pd_ = wmean(Dd, w)
P("daily: mean site std %.3f, portfolio std %.3f, ratio %.3f" % (dsd.mean(), pd_.std(), pd_.std() / dsd.mean()))
sizes = [1, 2, 3, 5, 8, 12, 20, 30, 50, 80, 127, 180, 253]; NDRAW = 60
rows = []
for N in sizes:
    r_rand, r_clu, r_daily = [], [], []
    for _ in range(NDRAW):
        sel = rng.choice(n, N, replace=False)
        with np.errstate(all="ignore"):
            import warnings; warnings.simplefilter("ignore")
            r_rand.append(np.nanstd(np.nanmean(A[:, sel], 1)) / site_sd_an[sel].mean())
            r_daily.append(np.nanstd(np.nanmean(Dd[:, sel], 1)) / dsd[sel].mean())
            seed = rng.integers(n); selc = np.argsort(D[seed])[:N]
            r_clu.append(np.nanstd(np.nanmean(A[:, selc], 1)) / site_sd_an[selc].mean())
    rho = sm["mean_pairwise_corr_anom"]
    rows.append(dict(n=N, ratio_random_anom=np.mean(r_rand), ratio_clustered_anom=np.mean(r_clu), ratio_random_daily=np.mean(r_daily), theory_sqrt=np.sqrt(1 / N + (1 - 1 / N) * rho)))
smc = pd.DataFrame(rows); smc.to_csv(f"{OUT}/sc_smoothing_curve.csv", index=False); P(smc.round(3))
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(smc.n, smc.ratio_random_anom, "o-", label="random sites, hourly anomaly")
ax.plot(smc.n, smc.ratio_clustered_anom, "s-", label="spatially clustered (nearest neighbours)")
ax.plot(smc.n, smc.ratio_random_daily, "^-", label="random sites, daily sum")
ax.plot(smc.n, smc.theory_sqrt, "--", color="gray", label=f"sqrt(1/n+(1-1/n)rho), rho={sm['mean_pairwise_corr_anom']:.2f}")
ax.set_xscale("log"); ax.set_xlabel("# sites in group (equal weight)"); ax.set_ylabel("std(group mean) / mean site std"); ax.set_title("Smoothing of CF variability with group size")
ax.legend(); ax.grid(alpha=.3, which="both"); fig.tight_layout(); fig.savefig(f"{OUT}/sc_fig8_smoothing_curve.png", dpi=130); plt.close(fig)

# ---------- (6) outliers ----------
stats = pd.DataFrame(index=ids)
stats["coverage_2y"] = coverage.values
stats["mean_daytime_cf"] = np.nanmean(H, 0); stats["max_cf"] = np.nanmax(cf.values, 0); stats["p99_cf"] = np.nanpercentile(cf.values, 99, axis=0)
stats["mean_corr_anom"] = tw.mean_corr_anom_others
Chh = C_h.values.copy(); np.fill_diagonal(Chh, np.nan); stats["mean_corr_hourly"] = np.nanmean(Chh, 1)
cwp = []
for i in range(n):
    m = np.isfinite(A[:, i]); cwp.append(np.corrcoef(A[m, i], port_an[m])[0, 1] if m.sum() > 1000 else np.nan)
stats["corr_with_portfolio_anom"] = cwp
summer = cf[cf.index.month.isin([5, 6, 7, 8])]
prof = summer.groupby(summer.index.hour).mean()
prof_n = prof / prof.max()
hrs = prof.index.values.astype(float)
stats["peak_hour_summer"] = prof.idxmax().values
stats["centroid_hour_summer"] = (prof.values * hrs[:, None]).sum(0) / prof.values.sum(0)
med_c = stats.centroid_hour_summer.median(); stats["centroid_shift_h"] = stats.centroid_hour_summer - med_c
night = cf[cf.index.hour.isin([23, 0, 1, 2, 3])]
stats["night_nonzero_frac"] = (night > 0.01).mean().values
zero_days = (dsum == 0) & (pd.Series(pd_, index=dsum.index) > 0.5).values[:, None]
stats["zero_days_while_portfolio_ok"] = zero_days.sum().values; stats["n_days"] = dsum.notna().sum().values
stats["zero_day_frac"] = stats.zero_days_while_portfolio_ok / stats.n_days
stats = stats.join(sites[["current_group", "capacity_kw", "lat", "lon"]])
q1, q3 = stats.mean_corr_anom.quantile([.25, .75]); thr = q1 - 1.5 * (q3 - q1)
stats["first_valid"] = first_valid.dt.strftime("%Y-%m-%d").values
# distance-adjusted: how much lower is a site's mean corr than the decay curve predicts from its distances to everyone?
Dn0 = D.copy(); np.fill_diagonal(Dn0, np.nan)
stats["expected_corr_from_dist"] = np.nanmean(expdec(Dn0, fits["corr_anom"]["a"], fits["corr_anom"]["L_km"], fits["corr_anom"]["c"]), 1)
stats["corr_resid_vs_dist"] = stats.mean_corr_anom - stats.expected_corr_from_dist
Cnn = np.where(np.isfinite(Cm), Cm, np.nan)
nn3 = np.argsort(Dn, 1)[:, :3]
stats["corr_3nearest"] = np.array([np.nanmean(Cnn[i, nn3[i]]) for i in range(n)]); stats["dist_3nearest_km"] = np.array([Dn[i, nn3[i]].mean() for i in range(n)])
rq1, rq3 = stats.corr_resid_vs_dist.quantile([.25, .75]); rthr = rq1 - 1.5 * (rq3 - rq1)
stats["flag_low_corr_resid"] = stats.corr_resid_vs_dist < rthr
P("resid threshold %.3f; lowest residual sites:\n" % rthr, stats.sort_values("corr_resid_vs_dist")[["mean_corr_anom", "expected_corr_from_dist", "corr_resid_vs_dist", "corr_3nearest", "dist_3nearest_km", "coverage_2y", "centroid_shift_h", "capacity_kw", "current_group"]].head(12).round(3))
stats["flag_low_corr"] = stats.mean_corr_anom < thr
stats["flag_low_portfolio_corr"] = stats.corr_with_portfolio_anom < stats.corr_with_portfolio_anom.quantile(.05)
stats["flag_shift"] = stats.centroid_shift_h.abs() >= 0.5
stats["flag_coverage"] = stats.coverage_2y < 0.3
stats["flag_zero_days"] = stats.zero_day_frac > 0.05
stats["flag_cf_gt1"] = stats.max_cf > 1.0
stats["n_flags"] = stats[[c for c in stats.columns if c.startswith("flag_")]].sum(axis=1)
P("coverage_2y bins:", pd.cut(stats.coverage_2y, [0, .3, .5, .7, .9, 1.01]).value_counts().sort_index().to_dict())
P("mean_corr_anom by group:", stats.groupby("current_group").mean_corr_anom.mean().round(3).to_dict(), " corr_with_portfolio by group:", stats.groupby("current_group").corr_with_portfolio_anom.mean().round(3).to_dict())
P("mean_corr_anom vs coverage corr: %.3f" % stats[["mean_corr_anom", "coverage_2y"]].corr().iloc[0, 1])
stats.sort_values("mean_corr_anom").to_csv(f"{OUT}/sc_site_stats.csv")
out = stats[stats.n_flags > 0].sort_values(["n_flags", "mean_corr_anom"], ascending=[False, True])
out.to_csv(f"{OUT}/sc_outliers.csv")
P("low-corr threshold (Q1-1.5IQR) = %.3f; median mean_corr_anom = %.3f" % (thr, stats.mean_corr_anom.median()))
P("flags:", stats[[c for c in stats.columns if c.startswith("flag_")]].sum().to_dict())
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
P(out[["mean_corr_anom", "corr_with_portfolio_anom", "coverage_2y", "first_valid", "centroid_shift_h", "peak_hour_summer", "max_cf", "zero_day_frac", "capacity_kw", "current_group", "n_flags"]].round(3).head(30))
P("lowest 10 mean_corr_anom:\n", stats.sort_values("mean_corr_anom")[["mean_corr_anom", "corr_with_portfolio_anom", "coverage_2y", "first_valid", "centroid_shift_h", "capacity_kw", "current_group", "lat", "lon"]].head(10).round(3))
P("peak_hour_summer counts:", stats.peak_hour_summer.value_counts().to_dict())
P("median centroid hour summer %.2f, median peak hour %d" % (med_c, stats.peak_hour_summer.median()))
fig, axs = plt.subplots(1, 2, figsize=(14, 5))
ax = axs[0]; ax.scatter(stats.coverage_2y, stats.mean_corr_anom, s=10 + stats.capacity_kw / 10, c=stats.centroid_shift_h, cmap="coolwarm", vmin=-1, vmax=1, edgecolor="k", lw=.3)
for s in out.index[:15]: ax.annotate(s, (stats.coverage_2y[s], stats.mean_corr_anom[s]), fontsize=7)
ax.axhline(thr, ls="--", color="r"); ax.set_xlabel("data coverage (last 2y)"); ax.set_ylabel("mean anomaly corr with other sites"); ax.set_title("Outlier screen (colour = summer centroid-hour shift)")
ax = axs[1]
for s in ids: ax.plot(prof_n.index, prof_n[s], color="gray", alpha=.15, lw=.6)
for s in stats[stats.flag_shift].index: ax.plot(prof_n.index, prof_n[s], lw=1.4, label=f"{s} ({stats.centroid_shift_h[s]:+.1f}h)")
ax.set_xlabel("hour (KST, right-closed)"); ax.set_ylabel("normalised summer profile"); ax.set_title("Diurnal profiles; highlighted = centroid shift >= 0.5h"); ax.legend(fontsize=6, ncol=2)
fig.tight_layout(); fig.savefig(f"{OUT}/sc_fig9_outliers.png", dpi=130); plt.close(fig)
P("DONE")
