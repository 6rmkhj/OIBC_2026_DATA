# forecast_skill.py  -- OIBC 2026: weather-forecast skill, explanatory power, perfect-forecast bound,
# observed anomalies, missing test rows, provider/round recommendation.
import os, gc, time, warnings, sys
import numpy as np, pandas as pd
import pyarrow as pa, pyarrow.parquet as pq, pyarrow.compute as pc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import lightgbm as lgb
warnings.filterwarnings("ignore")
T0 = time.time()
def log(*a):
    print(f"[{time.time()-T0:6.1f}s]", *a, flush=True)

ROOT = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad"
CACHE = ROOT + "/cache"
OUT = ROOT + "/analysis/out"
RAW = "C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset"
os.makedirs(OUT, exist_ok=True)
TZ = "Asia/Seoul"
T_START = pd.Timestamp("2023-06-01 01:00", tz=TZ)   # last 2 years
T_VAL = pd.Timestamp("2024-06-01 01:00", tz=TZ)     # validation start
def ts_scalar(t):
    return pa.scalar(t.value // 1000, type=pa.timestamp("us", tz=TZ))
FILT = (pc.field("ts") >= ts_scalar(T_START)) & (pc.field("elev") > 0)
DICT = ["site_id", "wa_station", "wb_station", "current_group"]

def read(path, cols, filt=FILT):
    t = pq.read_table(path, columns=cols, filters=filt, read_dictionary=[c for c in DICT if c in cols])
    df = t.to_pandas()
    del t
    for c in df.columns:
        if df[c].dtype == np.float64:
            df[c] = df[c].astype(np.float32)
    return df

CKPT = OUT + "/_fs_merged.parquet"
A_V = ["cloud", "temp", "humidity", "rain"]
B_V = ["cloud", "temp", "rel_hum", "uv_idx", "vis", "ceiling"]
if os.path.exists(CKPT):
    log("loading checkpoint")
    df = pd.read_parquet(CKPT)
else:
    obs_cols = ["site_id", "ts", "energy", "capacity_kw", "wa_station", "wb_station", "current_group",
                "elev", "cosz", "toa", "hour", "month"] + [f"obs_wa_{v}" for v in A_V] + [f"obs_wb_{v}" for v in B_V]
    df = read(CACHE + "/panel_train_obs.parquet", obs_cols)
    log("obs panel", df.shape)
    df = df.drop_duplicates(["site_id", "ts"]).reset_index(drop=True)
    log("obs dedup", df.shape)
    fc_cols = ["site_id", "ts"] + [f"wa_{v}" for v in A_V] + [f"wb_{v}" for v in B_V] + ["wb_precip_prob", "wb_total_liq"]
    for r in (17, 10):
        f = read(CACHE + f"/panel_train_r{r}.parquet", fc_cols)
        f = f.drop_duplicates(["site_id", "ts"])
        f.columns = ["site_id", "ts"] + [f"r{r}_{c}" for c in f.columns[2:]]
        # align categorical dtypes for merge
        f["site_id"] = f["site_id"].astype(str).astype(df["site_id"].dtype)
        df = df.merge(f, on=["site_id", "ts"], how="left")
        log(f"merged r{r}", df.shape, "nan frac cloud:", float(f[f"r{r}_wa_cloud"].isna().mean()), float(f[f"r{r}_wb_cloud"].isna().mean()))
        del f; gc.collect()
    df.to_parquet(CKPT)
log("merged frame", df.shape, f"{df.memory_usage(deep=True).sum()/1e6:.0f} MB")

# ---------------- (4) observed anomalies (station-level, daytime, last 2y) ----------------
anom = []
stA = df.drop_duplicates(["wa_station", "ts"])
stB = df.drop_duplicates(["wb_station", "ts"])
def cnt(name, s, n):
    anom.append(dict(check=name, count=int(s.sum()), total=int(n), pct=round(100 * float(s.sum()) / n, 4)))
cnt("obs_wa_humidity>100", stA["obs_wa_humidity"] > 100, stA["obs_wa_humidity"].notna().sum())
cnt("obs_wa_humidity<=0", stA["obs_wa_humidity"] <= 0, stA["obs_wa_humidity"].notna().sum())
cnt("obs_wa_cloud>100", stA["obs_wa_cloud"] > 100, stA["obs_wa_cloud"].notna().sum())
cnt("obs_wa_temp outside[-30,45]", ~stA["obs_wa_temp"].between(-30, 45) & stA["obs_wa_temp"].notna(), stA["obs_wa_temp"].notna().sum())
cnt("obs_wa_rain>100", stA["obs_wa_rain"] > 100, stA["obs_wa_rain"].notna().sum())
cnt("obs_wa missing (cloud NaN)", stA["obs_wa_cloud"].isna(), len(stA))
cnt("obs_wb_cloud>100", stB["obs_wb_cloud"] > 100, stB["obs_wb_cloud"].notna().sum())
cnt("obs_wb_uv_idx>15", stB["obs_wb_uv_idx"] > 15, stB["obs_wb_uv_idx"].notna().sum())
cnt("obs_wb_vis>50", stB["obs_wb_vis"] > 50, stB["obs_wb_vis"].notna().sum())
cnt("obs_wb_ceiling>15240", stB["obs_wb_ceiling"] > 15240, stB["obs_wb_ceiling"].notna().sum())
cnt("obs_wb_rel_hum<=0", stB["obs_wb_rel_hum"] <= 0, stB["obs_wb_rel_hum"].notna().sum())
cnt("obs_wb_temp outside[-30,45]", ~stB["obs_wb_temp"].between(-30, 45) & stB["obs_wb_temp"].notna(), stB["obs_wb_temp"].notna().sum())
cnt("obs_wb missing (cloud NaN)", stB["obs_wb_cloud"].isna(), len(stB))
cnt("forecast r17 wa missing", stA["r17_wa_cloud"].isna(), len(stA))
cnt("forecast r10 wa missing", stA["r10_wa_cloud"].isna(), len(stA))
cnt("forecast r17 wb missing", stB["r17_wb_cloud"].isna(), len(stB))
cnt("forecast r10 wb missing", stB["r10_wb_cloud"].isna(), len(stB))
cnt("forecast wa_humidity>100 (r17)", stA["r17_wa_humidity"] > 100, stA["r17_wa_humidity"].notna().sum())
# full-period anomaly counts for wind/pressure (columns not in main frame): read only what is needed, no filter
full = pq.read_table(CACHE + "/panel_train_obs.parquet",
                     columns=["ts", "wa_station", "wb_station", "obs_wa_wind_speed", "obs_wb_wind_speed", "obs_wb_pressure", "obs_wb_cloud", "obs_wb_uv_idx", "obs_wb_vis"],
                     read_dictionary=["wa_station", "wb_station"]).to_pandas()
fa = full.drop_duplicates(["wa_station", "ts"]); fb = full.drop_duplicates(["wb_station", "ts"])
cnt("FULL obs_wa_wind_speed==9999", fa["obs_wa_wind_speed"] == 9999, fa["obs_wa_wind_speed"].notna().sum())
cnt("FULL obs_wa_wind_speed>50", fa["obs_wa_wind_speed"] > 50, fa["obs_wa_wind_speed"].notna().sum())
cnt("FULL obs_wb_wind_speed>200", fb["obs_wb_wind_speed"] > 200, fb["obs_wb_wind_speed"].notna().sum())
cnt("FULL obs_wb_pressure<900", fb["obs_wb_pressure"] < 900, fb["obs_wb_pressure"].notna().sum())
cnt("FULL obs_wb_pressure==0", fb["obs_wb_pressure"] == 0, fb["obs_wb_pressure"].notna().sum())
cnt("FULL obs_wb_cloud>100", fb["obs_wb_cloud"] > 100, fb["obs_wb_cloud"].notna().sum())
cnt("FULL obs_wb_uv_idx>15", fb["obs_wb_uv_idx"] > 15, fb["obs_wb_uv_idx"].notna().sum())
cnt("FULL obs_wb_vis>50", fb["obs_wb_vis"] > 50, fb["obs_wb_vis"].notna().sum())
# what do the wb_cloud>100 values look like?
bad = fb.loc[fb["obs_wb_cloud"] > 100, "obs_wb_cloud"]
log("wb_cloud>100 value distribution:", bad.describe().to_dict() if len(bad) else "none")
log("wb_cloud>100 by station (top5):", fb.loc[fb["obs_wb_cloud"] > 100, "wb_station"].value_counts().head(5).to_dict())
badu = fb.loc[fb["obs_wb_uv_idx"] > 15, "obs_wb_uv_idx"]
log("wb_uv>15 values:", badu.describe().to_dict() if len(badu) else "none")
anom_df = pd.DataFrame(anom); anom_df.to_csv(OUT + "/obs_anomalies.csv", index=False)
print(anom_df.to_string())
del full, fa, fb; gc.collect()

# ---------------- clean observed ----------------
df.loc[df["obs_wb_cloud"] > 100, "obs_wb_cloud"] = np.nan
df.loc[df["obs_wb_uv_idx"] > 15, "obs_wb_uv_idx"] = np.nan
df.loc[df["obs_wb_vis"] > 50, "obs_wb_vis"] = np.nan
df["obs_wa_humidity"] = df["obs_wa_humidity"].clip(upper=100)
for r in (17, 10):
    df[f"r{r}_wa_humidity"] = df[f"r{r}_wa_humidity"].clip(upper=100)
df["cf"] = (df["energy"] / df["capacity_kw"]).clip(lower=0).astype(np.float32)
df = df[df["cf"] <= 1.5].reset_index(drop=True)
df["kt"] = np.where(df["toa"] > 50, df["cf"] / (df["toa"] / 1000.0), np.nan).astype(np.float32)
df.loc[df["kt"] > 3, "kt"] = np.nan
smp = pd.read_parquet(CACHE + "/smp_all.parquet")
smp["w"] = (smp["smp"] * smp["k"]).astype(np.float32)
df = df.merge(smp[["ts", "w"]], on="ts", how="left")
log("after clean", df.shape, "w NaN:", int(df["w"].isna().sum()))

# ---------------- (1) forecast skill, station-level ----------------
def grouped_skill(d, fc, ob, by):
    x = d[[by, fc, ob]].dropna()
    x = x.rename(columns={fc: "x", ob: "y"})
    x["e"] = x["x"] - x["y"]; x["ae"] = x["e"].abs()
    x["xy"] = x["x"] * x["y"]; x["x2"] = x["x"] ** 2; x["y2"] = x["y"] ** 2
    g = x.groupby(by, observed=True).agg(n=("e", "size"), mae=("ae", "mean"), bias=("e", "mean"), rmse=("e", lambda s: float(np.sqrt(np.mean(s ** 2)))),
                                        mx=("x", "mean"), my=("y", "mean"), mxy=("xy", "mean"), mx2=("x2", "mean"), my2=("y2", "mean"), sd_obs=("y", "std"))
    cov = g["mxy"] - g["mx"] * g["my"]
    g["corr"] = cov / np.sqrt((g["mx2"] - g["mx"] ** 2) * (g["my2"] - g["my"] ** 2))
    return g[["n", "mae", "rmse", "bias", "corr", "sd_obs"]].reset_index()

stA = df.drop_duplicates(["wa_station", "ts"]).copy()
stB = df.drop_duplicates(["wb_station", "ts"]).copy()
stA["all"] = 1; stB["all"] = 1
log("station-level rows A/B:", len(stA), len(stB))
VARS = [("A", v, stA) for v in ["cloud", "temp", "humidity", "rain"]] + [("B", v, stB) for v in ["cloud", "temp", "rel_hum", "uv_idx", "vis", "ceiling"]]
rows_h, rows_m, rows_all = [], [], []
for prov, v, d in VARS:
    p = "wa" if prov == "A" else "wb"
    ob = f"obs_{p}_{v}"
    for r in (17, 10):
        fc = f"r{r}_{p}_{v}"
        for by, store in (("hour", rows_h), ("month", rows_m), ("all", rows_all)):
            g = grouped_skill(d, fc, ob, by)
            g.insert(0, "round", r); g.insert(0, "var", v); g.insert(0, "provider", prov)
            store.append(g)
    # paired comparison r17 vs r10 and blend
    x = d[[f"r17_{p}_{v}", f"r10_{p}_{v}", ob]].dropna()
    e17 = x[f"r17_{p}_{v}"] - x[ob]; e10 = x[f"r10_{p}_{v}"] - x[ob]
    eb = (x[f"r17_{p}_{v}"] + x[f"r10_{p}_{v}"]) / 2 - x[ob]
    rows_all.append(pd.DataFrame([dict(provider=prov, var=v, round="paired", all=1, n=len(x),
                                       mae=float(e17.abs().mean()), rmse=float(np.sqrt((e17 ** 2).mean())), bias=float(e17.mean()),
                                       corr=float(np.corrcoef(e17, e10)[0, 1]), sd_obs=float(x[ob].std()),
                                       mae_r10=float(e10.abs().mean()), mae_blend=float(eb.abs().mean()),
                                       frac_r17_better=float((e17.abs() < e10.abs()).mean()), frac_tie=float((e17.abs() == e10.abs()).mean()),
                                       frac_identical_fc=float((x[f"r17_{p}_{v}"] == x[f"r10_{p}_{v}"]).mean()))]))
sk_h = pd.concat(rows_h); sk_m = pd.concat(rows_m); sk_all = pd.concat(rows_all)
for r in (17, 10):
    sk_h.loc[sk_h["round"] == r, "lead_h"] = sk_h.loc[sk_h["round"] == r, "hour"].replace(0, 24) + (7 if r == 17 else 14)
sk_h.to_csv(OUT + "/skill_by_hour.csv", index=False); sk_m.to_csv(OUT + "/skill_by_month.csv", index=False); sk_all.to_csv(OUT + "/skill_overall.csv", index=False)
print("=== overall skill ===\n", sk_all.drop(columns=["all"]).to_string(index=False))
# cross-provider: A cloud vs B cloud forecasts (site-level, both available) and obs agreement
xx = df[["r17_wa_cloud", "r17_wb_cloud", "obs_wa_cloud", "obs_wb_cloud"]].dropna()
cross = dict(n=len(xx), corr_fcA_fcB=float(xx["r17_wa_cloud"].corr(xx["r17_wb_cloud"])), corr_obsA_obsB=float(xx["obs_wa_cloud"].corr(xx["obs_wb_cloud"])),
             corr_fcA_obsB=float(xx["r17_wa_cloud"].corr(xx["obs_wb_cloud"])), corr_fcB_obsA=float(xx["r17_wb_cloud"].corr(xx["obs_wa_cloud"])),
             mean_fcA=float(xx["r17_wa_cloud"].mean()), mean_fcB=float(xx["r17_wb_cloud"].mean()), mean_obsA=float(xx["obs_wa_cloud"].mean()), mean_obsB=float(xx["obs_wb_cloud"].mean()))
print("cross-provider cloud:", cross)
pd.DataFrame([cross]).to_csv(OUT + "/cloud_cross_provider.csv", index=False)
del xx

# figures for (1)
def plot_skill(tab, by, fname, metric="mae"):
    fig, axes = plt.subplots(2, 5, figsize=(20, 7))
    for ax, (prov, v, _) in zip(axes.flat, VARS):
        for r, c in ((10, "tab:orange"), (17, "tab:blue")):
            s = tab[(tab.provider == prov) & (tab["var"] == v) & (tab["round"] == r)]
            ax.plot(s[by], s[metric], marker="o", ms=3, color=c, label=f"round {r}")
        ax.set_title(f"{prov}: {v}"); ax.set_xlabel(by); ax.set_ylabel(metric.upper()); ax.grid(alpha=.3)
    axes[0, 0].legend(); fig.suptitle(f"Forecast {metric.upper()} vs observed, by {by} (station-level, daytime, 2023-06..2025-05)")
    fig.tight_layout(); fig.savefig(OUT + "/" + fname, dpi=110); plt.close(fig)
plot_skill(sk_h, "hour", "fig_skill_mae_by_hour.png")
plot_skill(sk_m, "month", "fig_skill_mae_by_month.png")
plot_skill(sk_h, "hour", "fig_skill_corr_by_hour.png", "corr")
plot_skill(sk_h, "hour", "fig_skill_bias_by_hour.png", "bias")
del stA, stB; gc.collect()

# ---------------- (2) explanatory power for CF ----------------
samp = df.sample(min(500_000, len(df)), random_state=0)
sp_cols = {"cf": "cf", "kt": "kt"}
feat_list = ["r17_wa_cloud", "r17_wa_temp", "r17_wa_humidity", "r17_wa_rain", "r17_wb_cloud", "r17_wb_temp", "r17_wb_rel_hum", "r17_wb_uv_idx", "r17_wb_vis", "r17_wb_ceiling", "r17_wb_precip_prob", "r17_wb_total_liq",
             "r10_wa_cloud", "r10_wb_cloud", "r10_wb_uv_idx", "obs_wa_cloud", "obs_wa_temp", "obs_wa_humidity", "obs_wb_cloud", "obs_wb_temp", "obs_wb_rel_hum", "obs_wb_uv_idx", "obs_wb_vis", "obs_wb_ceiling", "toa", "elev", "cosz"]
sp = samp[feat_list + ["cf", "kt"]].corr(method="spearman")
sp_tab = pd.DataFrame({"feature": feat_list, "spearman_cf": sp.loc[feat_list, "cf"].values, "spearman_kt": sp.loc[feat_list, "kt"].values})
sp_tab.to_csv(OUT + "/spearman_cf.csv", index=False)
print("=== Spearman with CF / kt (500k daytime sample) ===\n", sp_tab.round(3).to_string(index=False))
fig, ax = plt.subplots(figsize=(9, 8))
o = sp_tab.sort_values("spearman_kt")
ax.barh(o["feature"], o["spearman_kt"], color=["tab:green" if f.startswith("obs") else ("tab:blue" if "wa_" in f else "tab:red") for f in o["feature"]])
ax.set_xlabel("Spearman corr with clear-sky index kt (green=observed, blue=A fc, red=B fc)"); ax.grid(alpha=.3, axis="x"); fig.tight_layout(); fig.savefig(OUT + "/fig_spearman_kt.png", dpi=110); plt.close(fig)
del samp, sp; gc.collect()

# ---------------- models ----------------
df["site_code"] = df["site_id"].cat.codes.astype(np.int16)
tr = df[df["ts"] < T_VAL]; va = df[df["ts"] >= T_VAL]
log("train rows", len(tr), "val rows", len(va), "val sites", va["site_id"].nunique())
trs = tr.sample(min(500_000, len(tr)), random_state=1)
BASE = ["site_code", "elev", "cosz", "toa", "hour", "month"]
A17 = [f"r17_wa_{v}" for v in A_V]; B17 = [f"r17_wb_{v}" for v in B_V] + ["r17_wb_precip_prob", "r17_wb_total_liq"]
A10 = [f"r10_wa_{v}" for v in A_V]; B10 = [f"r10_wb_{v}" for v in B_V] + ["r10_wb_precip_prob", "r10_wb_total_liq"]
OA = [f"obs_wa_{v}" for v in A_V]; OB = [f"obs_wb_{v}" for v in B_V]
B17c = [f"r17_wb_{v}" for v in B_V]; B10c = [f"r10_wb_{v}" for v in B_V]  # same variables as observed B
PARAMS = dict(n_estimators=150, learning_rate=0.1, num_leaves=63, min_child_samples=200, subsample=0.8, subsample_freq=1, colsample_bytree=0.9, n_jobs=8, verbose=-1)
va_w = va["w"].fillna(0).to_numpy(); va_act = va["energy"].to_numpy(); va_cap = va["capacity_kw"].to_numpy()
rev_w = float((va_w * va_act).sum())
def evaluate(pred_cf, tag):
    p = np.clip(pred_cf, 0, None)
    y = va["cf"].to_numpy()
    r2 = 1 - float(((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum())
    pk = p * va_cap
    g = pd.DataFrame({"ts": va["ts"].values, "grp": va["current_group"].values, "d": pk - va_act, "w": va_w}).groupby(["ts", "grp"], observed=True).agg(d=("d", "sum"), w=("w", "first"))
    W = float((g["w"] * g["d"].abs()).sum())
    return dict(model=tag, r2_cf=r2, mae_cf=float(np.abs(y - p).mean()), mae_kwh=float(np.abs(pk - va_act).mean()),
                wmae_kwh=float((va_w * np.abs(pk - va_act)).sum() / va_w.sum()), W_group=W, W_over_revenue=W / rev_w, bias_kwh=float((pk - va_act).mean()))
def fit(feats):
    X = trs[feats].to_numpy(np.float32); y = trs["cf"].to_numpy(np.float32)
    m = lgb.LGBMRegressor(**PARAMS); m.fit(X, y, categorical_feature=[0]); return m
def pred(m, feats, d=None):
    d = va if d is None else d
    return m.predict(d[feats].to_numpy(np.float32))
res = []; preds = {}
sets = {"S0 base(geometry+site)": BASE,
        "Sa r17 A": BASE + A17, "Sb r17 B": BASE + B17, "Sc r17 A+B": BASE + A17 + B17,
        "Sa r10 A": BASE + A10, "Sb r10 B": BASE + B10, "Sc r10 A+B": BASE + A10 + B10,
        "Sd r10+r17 A+B": BASE + A17 + B17 + A10 + B10,
        "Sa-cloud r17 A cloud": BASE + ["r17_wa_cloud"], "Sb-cloud r17 B cloud": BASE + ["r17_wb_cloud"], "Sab-cloud r17 A+B cloud": BASE + ["r17_wa_cloud", "r17_wb_cloud"],
        "Sb-noCloud r17 B minus cloud": BASE + [c for c in B17 if c != "r17_wb_cloud"], "Sa-noCloud r17 A minus cloud": BASE + [c for c in A17 if c != "r17_wa_cloud"]}
for tag, feats in sets.items():
    m = fit(feats); p = pred(m, feats); preds[tag] = p; res.append(evaluate(p, tag)); log(tag, {k: round(v, 4) for k, v in res[-1].items() if k != "model"})
    if tag == "Sc r17 A+B":
        imp = pd.DataFrame({"feature": feats, "gain": m.booster_.feature_importance("gain")}).sort_values("gain", ascending=False)
        imp["gain_pct"] = 100 * imp["gain"] / imp["gain"].sum(); imp.to_csv(OUT + "/lgb_importance_Sc_r17.csv", index=False); print(imp.round(2).to_string(index=False))
# ---------------- (3) perfect-forecast bound ----------------
osets = {"OA obs A": (BASE + OA, BASE + A17, BASE + A10), "OB obs B": (BASE + OB, BASE + B17c, BASE + B10c), "OC obs A+B": (BASE + OA + OB, BASE + A17 + B17c, BASE + A10 + B10c)}
for tag, (fo, f17, f10) in osets.items():
    m = fit(fo)
    p = pred(m, fo); preds[tag + " -> obs"] = p; res.append(evaluate(p, tag + " -> obs (perfect weather)")); log(res[-1])
    p = pred(m, f17); preds[tag + " -> r17"] = p; res.append(evaluate(p, tag + " -> r17 fc (obs-trained model fed forecast)")); log(res[-1])
    p = pred(m, f10); res.append(evaluate(p, tag + " -> r10 fc")); log(res[-1])
    # realistic model with the SAME variable set (fc-trained, fc-fed)
    m2 = fit(f17); p = pred(m2, f17); preds[tag + " fc17"] = p; res.append(evaluate(p, tag.replace("obs", "fc17") + " (fc-trained, fc-fed, same vars)")); log(res[-1])
res_df = pd.DataFrame(res); res_df.to_csv(OUT + "/model_results.csv", index=False)
print("=== model results (validation 2024-06..2025-05, daytime) ===\n", res_df.round(4).to_string(index=False))
# error decomposition by hour and month: perfect vs realistic (A+B)
dec = va[["hour", "month", "cf", "capacity_kw", "w"]].copy()
dec["e_perfect"] = np.abs(np.clip(preds["OC obs A+B -> obs"], 0, None) - dec["cf"]) * dec["capacity_kw"]
dec["e_cross"] = np.abs(np.clip(preds["OC obs A+B -> r17"], 0, None) - dec["cf"]) * dec["capacity_kw"]
dec["e_fc"] = np.abs(np.clip(preds["OC obs A+B fc17"], 0, None) - dec["cf"]) * dec["capacity_kw"]
dec["e_base"] = np.abs(np.clip(preds["S0 base(geometry+site)"], 0, None) - dec["cf"]) * dec["capacity_kw"]
dh = dec.groupby("hour")[["e_base", "e_fc", "e_cross", "e_perfect"]].mean(); dm = dec.groupby("month")[["e_base", "e_fc", "e_cross", "e_perfect"]].mean()
dh.to_csv(OUT + "/decomp_by_hour.csv"); dm.to_csv(OUT + "/decomp_by_month.csv")
print("=== site-level MAE kWh by hour ===\n", dh.round(2).to_string()); print("=== by month ===\n", dm.round(2).to_string())
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for ax, t, nm in ((axes[0], dh, "hour"), (axes[1], dm, "month")):
    for c, lab in (("e_base", "no weather (geometry+site)"), ("e_fc", "forecast weather r17 (realistic)"), ("e_cross", "obs-trained model fed r17 forecast"), ("e_perfect", "observed weather (perfect forecast)")):
        ax.plot(t.index, t[c], marker="o", ms=3, label=lab)
    ax.set_xlabel(nm); ax.set_ylabel("site-level MAE (kWh)"); ax.grid(alpha=.3)
axes[0].legend(fontsize=8); fig.suptitle("Error decomposition: perfect-forecast bound vs realistic (val year, daytime)"); fig.tight_layout(); fig.savefig(OUT + "/fig_decomp_perfect_vs_forecast.png", dpi=110); plt.close(fig)
fig, ax = plt.subplots(figsize=(11, 6))
o = res_df.sort_values("W_over_revenue", ascending=False)
ax.barh(o["model"], o["W_over_revenue"] * 100, color=["tab:green" if "obs (perfect" in m else ("tab:gray" if "S0" in m else "tab:blue") for m in o["model"]])
ax.set_xlabel("group-level weighted penalty W / weighted revenue (%)  [lower is better]"); ax.grid(alpha=.3, axis="x"); fig.tight_layout(); fig.savefig(OUT + "/fig_model_W.png", dpi=110); plt.close(fig)
del dec, preds, tr, va, trs; gc.collect()

# ---------------- (5) missing test forecast A rows ----------------
k = pq.read_table(RAW + "/test/forecast_wa.parquet", columns=["wa_station", "round", "ts"]).to_pandas()
grid = pd.date_range("2025-06-01 01:00", "2026-06-01 00:00", freq="h", tz=TZ)
full_idx = pd.MultiIndex.from_product([sorted(k["wa_station"].unique()), [10, 17], grid], names=["wa_station", "round", "ts"])
have = pd.MultiIndex.from_frame(k[["wa_station", "round", "ts"]])
miss = full_idx.difference(have).to_frame(index=False)
log("test A: rows", len(k), "expected", len(full_idx), "missing", len(miss), "dup keys", int(have.duplicated().sum()))
miss["date"] = miss["ts"].dt.date; miss["hour"] = miss["ts"].dt.hour
other = have.to_frame(index=False); other["round"] = other["round"].map({10: 17, 17: 10})
oth_idx = pd.MultiIndex.from_frame(other[["wa_station", "round", "ts"]])
miss["other_round_available"] = pd.MultiIndex.from_frame(miss[["wa_station", "round", "ts"]]).isin(oth_idx)
sites = pd.read_csv(RAW + "/sites.csv")
nsites = sites.groupby("wa_station").size(); capst = sites.groupby("wa_station")["capacity_kw"].sum()
miss["n_sites"] = miss["wa_station"].map(nsites).fillna(0).astype(int); miss["capacity_kw"] = miss["wa_station"].map(capst).fillna(0)
miss["daytime(6-19)"] = miss["hour"].between(6, 19)
miss.to_csv(OUT + "/test_wa_missing_rows.csv", index=False)
summ = miss.groupby(["wa_station", "round", "date"], observed=True).agg(n_hours=("ts", "size"), hours=("hour", lambda s: f"{s.min()}-{s.max()}"), other_round_ok=("other_round_available", "mean"), n_sites=("n_sites", "first"), capacity_kw=("capacity_kw", "first")).reset_index()
summ.to_csv(OUT + "/test_wa_missing_summary.csv", index=False)
print("=== test forecast_wa missing rows summary ===\n", summ.to_string(index=False))
print("by round:", miss["round"].value_counts().to_dict(), "| other round available:", int(miss["other_round_available"].sum()), "/", len(miss), "| daytime rows:", int(miss["daytime(6-19)"].sum()))
# B test completeness
kb = pq.read_table(RAW + "/test/forecast_wb.parquet", columns=["wb_station", "round", "ts"]).to_pandas()
log("test B: rows", len(kb), "expected", kb["wb_station"].nunique() * 2 * len(grid), "dup keys", int(kb.duplicated().sum()))
# neighbour A station for each affected station (station location ~ mean of its sites' coordinates)
stloc = sites.groupby("wa_station")[["lat", "lon"]].mean()
nb = []
for s in miss["wa_station"].unique():
    if s not in stloc.index: nb.append(dict(wa_station=s, nearest=None, dist_km=None)); continue
    d = np.sqrt(((stloc["lat"] - stloc.loc[s, "lat"]) * 111) ** 2 + ((stloc["lon"] - stloc.loc[s, "lon"]) * 88.5) ** 2).drop(s)
    nb.append(dict(wa_station=s, nearest=d.idxmin(), dist_km=round(float(d.min()), 1), wb_stations_of_sites=",".join(sorted(sites.loc[sites.wa_station == s, "wb_station"].unique()))))
nb = pd.DataFrame(nb); nb.to_csv(OUT + "/test_wa_missing_neighbours.csv", index=False); print(nb.to_string(index=False))
# confirm panel_test_r17/r10 NaN rows correspond
for r in (17, 10):
    t = pq.read_table(CACHE + f"/panel_test_r{r}.parquet", columns=["site_id", "ts", "wa_cloud", "wb_cloud"], read_dictionary=["site_id"]).to_pandas()
    log(f"panel_test_r{r}: wa_cloud NaN rows", int(t["wa_cloud"].isna().sum()), "sites affected", t.loc[t["wa_cloud"].isna(), "site_id"].nunique(), "| wb_cloud NaN", int(t["wb_cloud"].isna().sum()))
    del t
fig, ax = plt.subplots(figsize=(12, 4))
for r, c in ((10, "tab:orange"), (17, "tab:blue")):
    s = miss[miss["round"] == r]; ax.scatter(s["ts"], s["wa_station"], s=8, color=c, label=f"round {r}")
ax.legend(); ax.set_title("test/forecast_wa missing (station, round, ts) rows"); ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(OUT + "/fig_test_wa_missing.png", dpi=110); plt.close(fig)
log("DONE")
