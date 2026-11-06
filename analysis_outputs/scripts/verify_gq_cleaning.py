"""Adversarial re-computation of gen_quality anomaly counts + energy that the
'elev<=0 -> forecast 0' rule (used in model_validation.py) actually zeroes."""
import numpy as np, pandas as pd, pyarrow.parquet as pq, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
B = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad"
D = "C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset"
OUT = B + "/analysis/out/"
LOG = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.append(s)
S = {}  # summary metrics

cf = pd.read_parquet(B + "/cache/cf_wide.parquet")
ts = pd.DatetimeIndex(cf.index); cols = list(cf.columns)
sites = pd.read_csv(D + "/sites.csv").set_index("site_id").loc[cols]
cap = sites.capacity_kw.to_numpy("float32"); grp = sites.current_group.to_numpy()
C = cf.to_numpy(dtype="float32"); del cf
T, N = C.shape; obs = ~np.isnan(C); E = np.where(obs, C * cap, 0).astype("float32")
P(f"cf_wide {T}x{N}; observed rows {obs.sum()}; zero share {(C[obs]==0).mean():.4f}; total kWh {E.sum():,.0f}; tot cap {cap.sum():.1f}")
S["rows"] = int(obs.sum()); S["total_kwh"] = float(E.sum())

# ---------- 1. negatives / CF>1 ----------
neg = obs & (C < 0)
P(f"NEG: n={neg.sum()} sum={E[neg].sum():.3f} kWh sites={int((neg.sum(0)>0).sum())} groupA={int(neg[:, grp=='A'].sum())} min={E[neg].min():.4f}")
S.update(neg_n=int(neg.sum()), neg_sum_kwh=float(E[neg].sum()), neg_sites=int((neg.sum(0) > 0).sum()), neg_groupA=int(neg[:, grp == 'A'].sum()))
g1 = C > 1
P(f"CF>1: n={g1.sum()} sites={int((g1.sum(0)>0).sum())} max={C[g1].max():.4f} excess kWh if clipped to 1: {(E[g1]-cap[np.nonzero(g1)[1]]).sum():.3f}")
S.update(cfgt1_n=int(g1.sum()), cfgt1_sites=int((g1.sum(0) > 0).sum()), cfgt1_max=float(C[g1].max()), cfgt1_excess_kwh=float((E[g1] - cap[np.nonzero(g1)[1]]).sum()))
for i, j in zip(*np.nonzero(g1)): P("   ", cols[j], ts[i], round(float(C[i, j]), 4))

# ---------- 2. internal gaps (missing rows after first record) ----------
gap_rows = []
for j in range(N):
    idx = np.flatnonzero(obs[:, j]); span = idx[-1] - idx[0] + 1; miss = span - len(idx)
    if miss: gap_rows.append((cols[j], miss, str(ts[idx[0]]), str(ts[idx[-1]])))
P("internal gaps (site, missing_h, first, last):", gap_rows)
S["gap_sites"] = len(gap_rows); S["gap_hours"] = int(sum(r[1] for r in gap_rows))
last_ts_all = ts[np.array([np.flatnonzero(obs[:, j])[-1] for j in range(N)])]
S["sites_ending_early"] = int((last_ts_all < ts[-1]).sum()); P("sites whose last record < panel end:", S["sites_ending_early"])

# ---------- 3. flat-lines (same def as report: >=4 identical nonzero consecutive) ----------
same = np.zeros((T, N), bool); same[1:] = (C[1:] == C[:-1]) & (C[1:] > 0)
run = np.zeros(N, np.int32); flat_total = 0; flat_gt5 = 0; longest = 0
for i in range(T):
    run = np.where(same[i], run + 1, 0); f = run >= 3
    flat_total += int(f.sum()); flat_gt5 += int((f & (C[i] > 0.05)).sum()); longest = max(longest, int(run.max()) + 1)
P(f"FLAT: hours(run>=3)={flat_total} cf>5%={flat_gt5} longest={longest}")
S.update(flat_h=flat_total, flat_h_cf_gt5=flat_gt5, flat_longest=longest); del same

# ---------- 4. solar elevation at interval end / midpoint / start (independent NOAA impl, tz=+9) ----------
def elev_deg(ref):
    doy = ref.dayofyear.to_numpy(); fh = ref.hour.to_numpy() + ref.minute.to_numpy() / 60.0
    g = 2 * np.pi / 365 * (doy - 1 + (fh - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g))
    dec = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g) + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    la = np.deg2rad(sites.lat.to_numpy())[None, :]
    ha = np.deg2rad(((fh * 60 + eqt)[:, None] + 4 * sites.lon.to_numpy()[None, :] - 540) / 4 - 180)
    cz = np.sin(la) * np.sin(dec[:, None]) + np.cos(la) * np.cos(dec[:, None]) * np.cos(ha); del ha
    return np.rad2deg(np.arcsin(np.clip(cz, -1, 1))).astype("float32")
e_mid = elev_deg(ts - pd.Timedelta("30min")); e_end = elev_deg(ts); e_start = elev_deg(ts - pd.Timedelta("60min"))

# agree with the panel cache's elev (what model_validation.py masks on)?
chk = [sites.lon.idxmin(), sites.lon.idxmax(), sites.lat.idxmax(), "PV001"]
for sid in chk:
    t = pq.read_table(B + "/cache/panel_train_r17.parquet", columns=["ts", "elev"], filters=[("site_id", "=", sid)]).to_pandas()
    mine = pd.Series(e_mid[:, cols.index(sid)], index=ts).reindex(pd.DatetimeIndex(t.ts)).to_numpy(); pe = t.elev.to_numpy()
    P(f"panel elev vs mine ({sid}): max|diff|={np.nanmax(np.abs(mine - pe)):.3f} deg, sign disagreements (<=0)={int(((mine<=0)!=(pe<=0)).sum())}/{len(t)}")

# ---------- 5. energy zeroed by the rule ----------
w = pd.read_parquet(B + "/cache/smp_all.parquet").set_index("ts").reindex(ts)
W = (w.smp * w.k).fillna(0).to_numpy("float32")[:, None]; P("smp rows missing on cf index:", int(w.smp.isna().sum()))
val = ((ts >= pd.Timestamp("2024-06-01 01:00", tz="Asia/Seoul")) & (ts <= pd.Timestamp("2025-06-01 00:00", tz="Asia/Seoul")))[:, None]
pos = obs & (C > 0)
rules = {
    "mid<=0 (panel rule)": e_mid <= 0, "mid<=-6 (true night)": e_mid <= -6, "-6<mid<=0 (twilight)": (e_mid > -6) & (e_mid <= 0),
    "mid<=0 & sun up at start or end (partly lit)": (e_mid <= 0) & ((e_start > 0) | (e_end > 0)),
    "start<=0 & end<=0 (fully dark hour)": (e_start <= 0) & (e_end <= 0), "end<=0": e_end <= 0, "start<=0": e_start <= 0,
    "mid<=0 sunrise side (end>0)": (e_mid <= 0) & (e_end > 0), "mid<=0 sunset side (start>0)": (e_mid <= 0) & (e_start > 0),
}
tot_e, tot_we = E.sum(), (E * W).sum(); tot_e_val, tot_we_val = (E * val).sum(), (E * W * val).sum()
P(f"TOTAL kWh {tot_e:,.0f}; w-kWh {tot_we:.4e}; VAL kWh {tot_e_val:,.0f}; VAL w-kWh {tot_we_val:.4e}")
rows = []
for name, m in rules.items():
    mm = m & pos; e = E[mm].sum(); we = (E * W)[mm].sum(); ev = (E * val)[mm].sum(); wev = (E * W * val)[mm].sum()
    r = dict(rule=name, nonzero_h=int(mm.sum()), sites=int((mm.sum(0) > 0).sum()), kwh=round(float(e), 1), pct_kwh=round(100 * e / tot_e, 4),
             w_pct=round(100 * we / tot_we, 4), val_kwh=round(float(ev), 1), val_pct_kwh=round(100 * ev / tot_e_val, 4), val_w_pct=round(100 * wev / tot_we_val, 4),
             max_cf=round(float(C[mm].max()), 4) if mm.any() else 0, p99_cf=round(float(np.quantile(C[mm], 0.99)), 4) if mm.any() else 0)
    rows.append(r); P(r)
R = pd.DataFrame(rows); R.to_csv(OUT + "vgq_rule_energy.csv", index=False)
# how many of the zeroed hours actually have CF>=1% (clearly real generation)?
m = (e_mid <= 0) & pos; P("mid<=0 nonzero hours with CF>=0.01:", int((m & (C >= 0.01)).sum()), " CF>=0.05:", int((m & (C >= 0.05)).sum()), " kWh in CF>=0.01:", round(float(E[m & (C >= 0.01)].sum()), 1))
S["mid0_h_cf_ge1pct"] = int((m & (C >= 0.01)).sum()); S["mid0_h_cf_ge5pct"] = int((m & (C >= 0.05)).sum())

# energy by 1-deg bins of midpoint elevation
bins = np.arange(-12, 13); dig = np.digitize(e_mid, bins)
be = np.array([E[(dig == k) & pos].sum() for k in range(1, len(bins))]); bh = np.array([((dig == k) & pos).sum() for k in range(1, len(bins))])
BE = pd.DataFrame({"elev_mid_bin_lo": bins[:-1], "elev_mid_bin_hi": bins[1:], "nonzero_h": bh, "kwh": be.round(1), "pct_total_kwh": (100 * be / tot_e).round(4)})
BE.to_csv(OUT + "vgq_elev_band_energy.csv", index=False); P(BE.to_string())
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
ax[0].bar(bins[:-1] + .5, be / 1e3, color=np.where(bins[:-1] < 0, "tab:red", "tab:blue")); ax[0].set_xlabel("midpoint solar elevation bin (deg)"); ax[0].set_ylabel("MWh (all sites, 2021-2025)"); ax[0].set_title("Energy by elevation band (red = zeroed by elev<=0 rule)"); ax[0].set_yscale("log")
ax[1].bar(bins[:-1] + .5, bh / 1e3, color=np.where(bins[:-1] < 0, "tab:red", "tab:blue")); ax[1].set_xlabel("midpoint solar elevation bin (deg)"); ax[1].set_ylabel("nonzero site-hours (k)"); ax[1].set_title("Nonzero hours by band")
plt.tight_layout(); plt.savefig(OUT + "vgq_fig_elev_band_energy.png", dpi=110); plt.close()

# per-site zeroed energy (twilight) in VAL year
mv = (e_mid <= 0) & pos & val
ps = pd.DataFrame({"site_id": cols, "group": grp, "capacity_kw": cap, "val_zeroed_kwh": np.where(mv, E, 0).sum(0).round(1), "val_zeroed_h": mv.sum(0),
                   "val_total_kwh": np.where(val & obs, E, 0).sum(0).round(0)})
ps["val_zeroed_pct"] = (100 * ps.val_zeroed_kwh / ps.val_total_kwh.clip(lower=1)).round(3)
ps.sort_values("val_zeroed_kwh", ascending=False).to_csv(OUT + "vgq_site_zeroed_val.csv", index=False)
P("per-site VAL zeroed kWh: median pct", ps.val_zeroed_pct.median(), "max", ps.val_zeroed_pct.max(), "\n", ps.sort_values("val_zeroed_kwh", ascending=False).head(8).to_string())
P("by group VAL zeroed kWh:", ps.groupby("group").val_zeroed_kwh.sum().round(0).to_dict(), " group VAL total:", ps.groupby("group").val_total_kwh.sum().round(0).to_dict())

pd.Series(S).to_csv(OUT + "vgq_summary.csv", header=["value"])
open(OUT + "vgq_log.txt", "w", encoding="utf-8").write("\n".join(LOG))
