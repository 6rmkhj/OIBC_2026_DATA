# verify_fc_round_part2.py -- small independent LightGBM check: r17 vs r10 vs feature-averaged vs both-rounds,
# evaluated as group penalty W/rev (reference groups A->G1, B->G2) on 2024-06..2025-05 daytime rows. 2 seeds each.
import time, gc
import numpy as np, pandas as pd
import pyarrow as pa, pyarrow.parquet as pq, pyarrow.compute as pc
import lightgbm as lgb
T0 = time.time()
def log(*a): print(f"[{time.time()-T0:6.1f}s]", *a, flush=True)
ROOT = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad"
CACHE = ROOT + "/cache"; OUT = ROOT + "/analysis/out"; TZ = "Asia/Seoul"
def tsc(s): return pa.scalar(pd.Timestamp(s, tz=TZ).value // 1000, type=pa.timestamp("us", tz=TZ))
T_START = "2023-06-01 01:00"; T_VAL = pd.Timestamp("2024-06-01 01:00", tz=TZ)
FILT = (pc.field("ts") >= tsc(T_START)) & (pc.field("elev") > 0)
A6 = ["wa_cloud", "wa_temp", "wa_humidity", "wa_ground_press", "wa_wind_speed", "wa_rain"]
B9 = ["wb_cloud", "wb_uv_idx", "wb_temp", "wb_rel_hum", "wb_dew_point", "wb_vis", "wb_ceiling", "wb_precip_prob", "wb_total_liq"]
WX = A6 + B9
BASE = ["elev", "cosz", "toa", "hour", "month", "lat", "lon", "capacity_kw"]

def read(path, cols, filt):
    t = pq.read_table(path, columns=cols, filters=filt, read_dictionary=["site_id", "current_group"] if "current_group" in cols else ["site_id"])
    df = t.to_pandas(); del t
    for c in df.columns:
        if df[c].dtype == np.float64: df[c] = df[c].astype(np.float32)
    return df

d = read(CACHE + "/panel_train_r17.parquet", ["site_id", "ts", "energy", "current_group"] + BASE + WX, FILT).drop_duplicates(["site_id", "ts"])
d["site_id"] = d["site_id"].astype(str)
r10 = read(CACHE + "/panel_train_r10.parquet", ["site_id", "ts"] + WX, FILT).drop_duplicates(["site_id", "ts"])
r10["site_id"] = r10["site_id"].astype(str); r10.columns = ["site_id", "ts"] + [c + "_r10" for c in WX]
d = d.merge(r10, on=["site_id", "ts"], how="left"); del r10; gc.collect()
for c in WX:
    d[c + "_avg"] = ((d[c] + d[c + "_r10"]) / 2).astype(np.float32)
    d[c + "_w75"] = (0.75 * d[c] + 0.25 * d[c + "_r10"]).astype(np.float32)
d["cf"] = np.clip(d.energy / d.capacity_kw, 0, 1.2).astype(np.float32)
smp = pd.read_parquet(CACHE + "/smp_all.parquet"); smp["w"] = (smp.smp * smp.k).astype(np.float32)
d = d.merge(smp[["ts", "w"]], on="ts", how="left"); del smp
log("panel", d.shape, "nan r10 frac", float(d["wa_cloud_r10"].isna().mean()))
tr = d[d.ts < T_VAL]; va = d[d.ts >= T_VAL].reset_index(drop=True)
log("train rows", len(tr), "val rows", len(va))
tr = tr.sample(n=min(300_000, len(tr)), random_state=0)
log("train sample", len(tr))

SETS = {"M17 (r17 only)": BASE + WX, "M10 (r10 only)": BASE + [c + "_r10" for c in WX],
        "Mavg (feature-level (r17+r10)/2)": BASE + [c + "_avg" for c in WX], "Mw75 (feature-level 0.75*r17+0.25*r10)": BASE + [c + "_w75" for c in WX],
        "Mboth (r17+r10 features)": BASE + WX + [c + "_r10" for c in WX]}
PAR = dict(n_estimators=200, learning_rate=0.06, num_leaves=63, min_child_samples=200, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, n_jobs=8, verbose=-1)

def evaluate(p, tag):
    pk = p * va.capacity_kw.values; yk = va.energy.values
    g = pd.DataFrame({"grp": va.current_group.astype(str).values, "ts": va.ts.values, "hr": va.hour.values, "p": pk, "y": yk, "w": va.w.values}).groupby(["grp", "ts"], sort=False).agg(p=("p", "sum"), y=("y", "sum"), w=("w", "first"), hr=("hr", "first")).reset_index()
    W = float((g.w * (g.p - g.y).abs()).sum()); rev = float((g.w * g.y).sum())
    gk = g[g.hr.between(11, 15)]
    Wk = float((gk.w * (gk.p - gk.y).abs()).sum())
    return dict(model=tag, mae_cf=float(np.abs(p - va.cf.values).mean()), mae_kwh=float(np.abs(pk - yk).mean()), W_group=W, W_over_rev_pct=100 * W / rev, W_k3_share_pct=100 * Wk / W, bias_kwh=float((pk - yk).mean()))

res = []; preds = {}
for seed in (0, 1):
    for tag, feats in SETS.items():
        t = time.time()
        m = lgb.LGBMRegressor(random_state=seed, **PAR).fit(tr[feats], tr.cf)
        p = np.clip(m.predict(va[feats]), 0, None).astype(np.float32)
        preds[(tag, seed)] = p
        r = evaluate(p, tag); r["seed"] = seed; r["fit_sec"] = time.time() - t; res.append(r); log(r)
        del m; gc.collect()
    p = 0.5 * (preds[("M17 (r17 only)", seed)] + preds[("M10 (r10 only)", seed)])
    r = evaluate(p, "Mpavg (prediction-level avg of M17,M10)"); r["seed"] = seed; res.append(r); log(r)
    if seed == 1:
        p = 0.5 * (preds[("M17 (r17 only)", 0)] + preds[("M17 (r17 only)", 1)])
        r = evaluate(p, "M17 2-seed avg (equal-cost ensemble baseline)"); r["seed"] = -1; res.append(r); log(r)
R = pd.DataFrame(res); R.to_csv(OUT + "/vfr_model_recompute.csv", index=False)
S = R.groupby("model", sort=False).agg(W_over_rev_pct_mean=("W_over_rev_pct", "mean"), W_over_rev_pct_min=("W_over_rev_pct", "min"), W_over_rev_pct_max=("W_over_rev_pct", "max"), mae_cf=("mae_cf", "mean"), mae_kwh=("mae_kwh", "mean"), bias_kwh=("bias_kwh", "mean"), n=("seed", "size")).reset_index()
S.to_csv(OUT + "/vfr_model_recompute_summary.csv", index=False)
pd.set_option("display.width", 250)
print("\n=== per-fit ===\n", R.round(4).to_string(index=False))
print("\n=== summary (mean over seeds) ===\n", S.round(4).to_string(index=False))
log("done")
