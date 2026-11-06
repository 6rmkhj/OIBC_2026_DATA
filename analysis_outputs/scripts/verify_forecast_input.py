# verify_forecast_input.py -- adversarial re-computation of the provider/round claim (OIBC 2026)
# (1) round-blend curve + day-block bootstrap from cached group series (no retraining)
# (2) station-level forecast-vs-observed skill r17 vs r10 by YEAR (stability over time)
# (3) test-period r10/r17 behaviour vs train (identical fraction, mean |r17-r10|)
import os, gc, numpy as np, pandas as pd, pyarrow.parquet as pq
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ROOT = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad"
CACHE, MV, OUT = ROOT + "/cache", ROOT + "/analysis/mv_cache", ROOT + "/analysis/out"
TZ = "Asia/Seoul"
def log(*a): print(*a, flush=True)

def load_group(name):
    g = pd.read_parquet(f"{MV}/group_{name}.parquet")
    if g.index.tz is None: g.index = g.index.tz_localize("UTC").tz_convert(TZ)
    return g
def W(g, pA, pB, mask=None):
    e = (pA - g.y_A).abs() + (pB - g.y_B).abs(); w = g.w; r = g.w * (g.y_A + g.y_B)
    if mask is not None: e, w, r = e[mask], w[mask], r[mask]
    Wr = float((w * e).sum()); return Wr, 100 * Wr / float(r.sum())

# ---------------- (1) round blend curve ----------------
G = {n: load_group(n) for n in ["E1_l1w", "E2_r10", "E1_l1w_s2", "E1_l1w_s3", "E2_both", "E7_seed3"]}
idx = G["E1_l1w"].index
for n, g in G.items(): assert g.index.equals(idx), n
g17, g10 = G["E1_l1w"], G["E2_r10"]
log("check W_ref E1_l1w / E2_r10 / E2_both / E7_seed3 :", [round(W(G[n], G[n].p_A, G[n].p_B)[0]) for n in ["E1_l1w", "E2_r10", "E2_both", "E7_seed3"]])
hour = idx.hour; k3 = pd.Series((hour >= 11) & (hour <= 15), index=idx)
rows = []
for lam in np.round(np.arange(0, 1.0001, 0.05), 2):
    pA = lam * g17.p_A + (1 - lam) * g10.p_A; pB = lam * g17.p_B + (1 - lam) * g10.p_B
    Wr, Wp = W(g17, pA, pB); Wk3, _ = W(g17, pA, pB, k3)
    rows.append(dict(lam_r17=lam, W_ref=Wr, W_ref_pct=Wp, W_ref_k3=Wk3))
bl = pd.DataFrame(rows); bl["delta_pct_vs_r17only"] = 100 * (bl.W_ref / bl.W_ref.iloc[-1] - 1)
# seed-blend baselines (same-input models)
s1, s2, s3 = G["E1_l1w"], G["E1_l1w_s2"], G["E1_l1w_s3"]
base = []
for nm, (a, b) in {"s1+s2": (s1, s2), "s1+s3": (s1, s3), "s2+s3": (s2, s3)}.items():
    Wr, Wp = W(s1, 0.5 * (a.p_A + b.p_A), 0.5 * (a.p_B + b.p_B)); base.append(dict(blend=nm, W_ref=Wr, W_ref_pct=Wp))
for nm in ["E1_l1w", "E1_l1w_s2", "E1_l1w_s3", "E2_r10", "E2_both", "E7_seed3"]:
    Wr, Wp = W(G[nm], G[nm].p_A, G[nm].p_B); base.append(dict(blend=nm, W_ref=Wr, W_ref_pct=Wp))
# r10 added on top of the 3-seed r17 average
for lam in [1.0, 0.9, 0.8, 0.75, 0.5]:
    e7 = G["E7_seed3"]; Wr, Wp = W(e7, lam * e7.p_A + (1 - lam) * g10.p_A, lam * e7.p_B + (1 - lam) * g10.p_B)
    base.append(dict(blend=f"{lam:.2f}*E7_seed3+{1-lam:.2f}*E2_r10", W_ref=Wr, W_ref_pct=Wp))
base = pd.DataFrame(base)
bl.to_csv(OUT + "/vfi_round_blend_curve.csv", index=False); base.to_csv(OUT + "/vfi_blend_baselines.csv", index=False)
log("\n== round blend curve (lam = weight on r17 model E1_l1w, rest on E2_r10) ==\n", bl.round(3).to_string(index=False))
log("\n== baselines ==\n", base.round(3).to_string(index=False))
# day-block bootstrap of W(lam) - W(1) for lam in {0, 0.5, best}
best_lam = float(bl.loc[bl.W_ref.idxmin(), "lam_r17"])
day = (idx - pd.Timedelta(seconds=1)).floor("D")
def daily_W(pA, pB):
    e = (pA - g17.y_A).abs() + (pB - g17.y_B).abs(); return (g17.w * e).groupby(day).sum().to_numpy()
d1 = daily_W(g17.p_A, g17.p_B)
rng = np.random.default_rng(0); nb = 2000; nd = len(d1)
boot = []
for lam in sorted(set([0.0, 0.5, best_lam, 0.8])):
    dl = daily_W(lam * g17.p_A + (1 - lam) * g10.p_A, lam * g17.p_B + (1 - lam) * g10.p_B)
    diff = dl - d1  # <0 means blend better than r17 only
    sims = np.array([diff[rng.integers(0, nd, nd)].sum() for _ in range(nb)])
    boot.append(dict(lam_r17=lam, delta_W=float(diff.sum()), delta_pct=100 * float(diff.sum()) / d1.sum(),
                     ci_lo_pct=100 * float(np.percentile(sims, 2.5)) / d1.sum(), ci_hi_pct=100 * float(np.percentile(sims, 97.5)) / d1.sum(),
                     p_blend_better=float((sims < 0).mean()), n_days_blend_better=int((diff < 0).sum()), n_days=nd))
# seed-blend bootstrap for comparison (s1+s2 average vs s1)
dl = daily_W(0.5 * (s1.p_A + s2.p_A), 0.5 * (s1.p_B + s2.p_B)); diff = dl - d1
sims = np.array([diff[rng.integers(0, nd, nd)].sum() for _ in range(nb)])
boot.append(dict(lam_r17="seed avg s1+s2 vs s1", delta_W=float(diff.sum()), delta_pct=100 * float(diff.sum()) / d1.sum(),
                 ci_lo_pct=100 * float(np.percentile(sims, 2.5)) / d1.sum(), ci_hi_pct=100 * float(np.percentile(sims, 97.5)) / d1.sum(),
                 p_blend_better=float((sims < 0).mean()), n_days_blend_better=int((diff < 0).sum()), n_days=nd))
boot = pd.DataFrame(boot); boot.to_csv(OUT + "/vfi_blend_bootstrap.csv", index=False)
log("\n== day-block bootstrap: W(blend) - W(r17 only), negative = blend better ==\n", boot.round(4).to_string(index=False))
# monthly best lambda
mon = idx.month; mrows = []
for m in range(1, 13):
    mk = pd.Series(mon == m, index=idx); ws = {lam: W(g17, lam * g17.p_A + (1 - lam) * g10.p_A, lam * g17.p_B + (1 - lam) * g10.p_B, mk)[0] for lam in [0.0, 0.5, 0.8, 1.0]}
    mrows.append(dict(month=m, W_r10=ws[0.0], W_blend50=ws[0.5], W_blend80=ws[0.8], W_r17=ws[1.0], gain_blend50_pct=100 * (ws[0.5] / ws[1.0] - 1), gain_blend80_pct=100 * (ws[0.8] / ws[1.0] - 1), r10_vs_r17_pct=100 * (ws[0.0] / ws[1.0] - 1)))
mrows = pd.DataFrame(mrows); mrows.to_csv(OUT + "/vfi_blend_by_month.csv", index=False)
log("\n== by month ==\n", mrows.round(2).to_string(index=False))
del G, g17, g10, s1, s2, s3; gc.collect()

# ---------------- (2) station-level skill by year ----------------
def read(path, cols, flt=[("elev", ">", 0)]):
    t = pq.read_table(path, columns=cols, filters=flt); df = t.to_pandas(); del t
    for c in df.columns:
        if df[c].dtype == np.float64: df[c] = df[c].astype(np.float32)
    return df
def station_merge(st, obs_cols, fc_cols):
    o = read(CACHE + "/panel_train_obs.parquet", [st, "ts"] + obs_cols).drop_duplicates([st, "ts"]); o[st] = o[st].astype(str)
    log("obs station rows", st, len(o))
    for r in (17, 10):
        f = read(CACHE + f"/panel_train_r{r}.parquet", [st, "ts"] + fc_cols).drop_duplicates([st, "ts"]); f[st] = f[st].astype(str)
        f = f.rename(columns={c: f"r{r}_{c}" for c in fc_cols}); o = o.merge(f, on=[st, "ts"], how="inner"); del f; gc.collect()
    return o
def skill_rows(m, prov, var, ob, f17, f10):
    out = []
    m = m[["ts", ob, f17, f10]].dropna()
    per = m.ts.dt.year.astype(str).rename("period")
    val = ((m.ts > pd.Timestamp("2024-06-01 00:00", tz=TZ)) & (m.ts <= pd.Timestamp("2025-06-01 00:00", tz=TZ)))
    last2 = m.ts > pd.Timestamp("2023-06-01 00:00", tz=TZ)
    groups = [(p, per == p) for p in sorted(per.unique())] + [("val_2024-06..2025-05", val), ("last2y_2023-06..2025-05", last2), ("ALL", pd.Series(True, index=m.index))]
    for name, mk in groups:
        x = m[mk]; e17 = x[f17] - x[ob]; e10 = x[f10] - x[ob]; eb = 0.5 * (x[f17] + x[f10]) - x[ob]
        out.append(dict(provider=prov, var=var, period=name, n=len(x), mae_r17=float(e17.abs().mean()), mae_r10=float(e10.abs().mean()), mae_blend=float(eb.abs().mean()),
                        bias_r17=float(e17.mean()), bias_r10=float(e10.mean()), corr_r17=float(np.corrcoef(x[f17], x[ob])[0, 1]), corr_r10=float(np.corrcoef(x[f10], x[ob])[0, 1]),
                        frac_identical=float((x[f17] == x[f10]).mean()), mean_abs_r17_minus_r10=float((x[f17] - x[f10]).abs().mean()),
                        r17_gain_pct=100 * (1 - float(e17.abs().mean()) / float(e10.abs().mean()))))
    return out
sk = []
mA = station_merge("wa_station", ["obs_wa_cloud", "obs_wa_humidity"], ["wa_cloud", "wa_humidity"])
sk += skill_rows(mA, "A", "cloud", "obs_wa_cloud", "r17_wa_cloud", "r10_wa_cloud")
sk += skill_rows(mA, "A", "humidity", "obs_wa_humidity", "r17_wa_humidity", "r10_wa_humidity")
del mA; gc.collect()
mB = station_merge("wb_station", ["obs_wb_cloud", "obs_wb_uv_idx"], ["wb_cloud", "wb_uv_idx"])
mB = mB[(mB.obs_wb_cloud <= 100) & (mB.obs_wb_uv_idx <= 15)]
sk += skill_rows(mB, "B", "cloud", "obs_wb_cloud", "r17_wb_cloud", "r10_wb_cloud")
sk += skill_rows(mB, "B", "uv_idx", "obs_wb_uv_idx", "r17_wb_uv_idx", "r10_wb_uv_idx")
del mB; gc.collect()
sk = pd.DataFrame(sk); sk.to_csv(OUT + "/vfi_skill_by_year.csv", index=False)
log("\n== station-level daytime skill r17 vs r10 by period ==\n", sk.round(3).to_string(index=False))

# ---------------- (3) test-period round behaviour vs train ----------------
def round_diff(split, flt_extra=None):
    cols = ["wa_station", "wb_station", "ts", "wa_cloud", "wa_humidity", "wb_cloud", "wb_uv_idx"]
    flt = [("elev", ">", 0)] + (flt_extra or [])
    a = read(CACHE + f"/panel_{split}_r17.parquet", cols, flt); b = read(CACHE + f"/panel_{split}_r10.parquet", cols, flt)
    assert (a.ts.values == b.ts.values).all() and (a.wa_station.astype(str).values == b.wa_station.astype(str).values).all()
    out = []
    for st, v in [("wa_station", "wa_cloud"), ("wa_station", "wa_humidity"), ("wb_station", "wb_cloud"), ("wb_station", "wb_uv_idx")]:
        key = a[st].astype(str) + "|" + a.ts.astype(str); keep = ~key.duplicated()
        x17 = a.loc[keep, v]; x10 = b.loc[keep, v]; both = x17.notna() & x10.notna()
        out.append(dict(split=split, var=v, n_station_hours=int(keep.sum()), nan_r17=float(x17.isna().mean()), nan_r10=float(x10.isna().mean()),
                        frac_identical=float((x17[both] == x10[both]).mean()), mean_abs_diff=float((x17[both] - x10[both]).abs().mean()),
                        mean_r17=float(x17.mean()), mean_r10=float(x10.mean()), sd_r17=float(x17.std()), sd_r10=float(x10.std())))
    del a, b; gc.collect(); return out
T1 = pd.Timestamp("2024-06-01 00:00", tz=TZ)
rd = round_diff("train", [("ts", ">", T1)]) + round_diff("test")
rd = pd.DataFrame(rd); rd.to_csv(OUT + "/vfi_test_vs_train_round_behaviour.csv", index=False)
log("\n== r17 vs r10 behaviour: train last 12m vs test (daytime station-hours) ==\n", rd.round(4).to_string(index=False))

# ---------------- figure ----------------
fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
ax[0].plot(bl.lam_r17, bl.W_ref_pct, marker="o"); ax[0].axhline(base.loc[base.blend == "E7_seed3", "W_ref_pct"].iloc[0], ls="--", c="gray", label="3-seed r17 avg (E7_seed3)")
ax[0].set_xlabel("weight on r17 model (1 = r17 only, 0 = r10 only)"); ax[0].set_ylabel("W_ref % (validation year)"); ax[0].set_title("Round blend curve"); ax[0].grid(alpha=.3); ax[0].legend()
s = sk[(sk.period.str.len() == 4)]
for (p, v), d in s.groupby(["provider", "var"]): ax[1].plot(d.period, d.r17_gain_pct, marker="o", label=f"{p} {v}")
ax[1].axhline(0, c="k", lw=.8); ax[1].set_ylabel("MAE gain of r17 over r10 (%)"); ax[1].set_title("r17 vs r10 skill gain by year (station-level, daytime)"); ax[1].grid(alpha=.3); ax[1].legend()
fig.tight_layout(); fig.savefig(OUT + "/vfi_fig_round_blend_and_yearly_gain.png", dpi=110)
log("DONE")
