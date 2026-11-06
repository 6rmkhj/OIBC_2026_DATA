# verify_fc_round_part1.py -- independent recomputation of r17-vs-r10 forecast skill (station-level, vs observed),
# optimal blend weight, k=3-hour subset, and test-year transfer of the r10/r17 relationship.
import time, gc
import numpy as np, pandas as pd
import pyarrow as pa, pyarrow.parquet as pq, pyarrow.compute as pc
T0 = time.time()
def log(*a): print(f"[{time.time()-T0:6.1f}s]", *a, flush=True)
ROOT = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad"
CACHE = ROOT + "/cache"; OUT = ROOT + "/analysis/out"
TZ = "Asia/Seoul"
def tsc(s): return pa.scalar(pd.Timestamp(s, tz=TZ).value // 1000, type=pa.timestamp("us", tz=TZ))
T_START = "2023-06-01 01:00"; T_VAL = "2024-06-01 01:00"
FILT = (pc.field("ts") >= tsc(T_START)) & (pc.field("elev") > 0)
VARS = {"A": [("wa_cloud", "obs_wa_cloud"), ("wa_humidity", "obs_wa_humidity")],
        "B": [("wb_cloud", "obs_wb_cloud"), ("wb_uv_idx", "obs_wb_uv_idx")]}
STA = {"A": "wa_station", "B": "wb_station"}

def read(path, cols, filt):
    t = pq.read_table(path, columns=cols, filters=filt, read_dictionary=[c for c in cols if c.endswith("station")])
    df = t.to_pandas(); del t
    for c in df.columns:
        if df[c].dtype == np.float64: df[c] = df[c].astype(np.float32)
    return df

def station_frame(prov, test=False):
    """one row per (station, ts): r17 vars, r10 vars, (obs vars if train)"""
    st = STA[prov]; fcv = [v for v, _ in VARS[prov]]
    if test:
        f17 = read(CACHE + "/panel_test_r17.parquet", ["ts", st, "hour", "elev"] + fcv, pc.field("elev") > 0)
        f10 = read(CACHE + "/panel_test_r10.parquet", ["ts", st] + fcv, pc.field("elev") > 0)
    else:
        f17 = read(CACHE + "/panel_train_r17.parquet", ["ts", st, "hour", "elev"] + fcv, FILT)
        f10 = read(CACHE + "/panel_train_r10.parquet", ["ts", st] + fcv, FILT)
    f17 = f17.drop_duplicates([st, "ts"]); f10 = f10.drop_duplicates([st, "ts"])
    f17.columns = ["ts", st, "hour", "elev"] + ["r17_" + v for v in fcv]
    f10.columns = ["ts", st] + ["r10_" + v for v in fcv]
    for f in (f17, f10): f[st] = f[st].astype(str)
    d = f17.merge(f10, on=[st, "ts"], how="inner"); del f17, f10
    if not test:
        ov = [o for _, o in VARS[prov]]
        ob = read(CACHE + "/panel_train_obs.parquet", ["ts", st] + ov, FILT).drop_duplicates([st, "ts"])
        ob[st] = ob[st].astype(str)
        d = d.merge(ob, on=[st, "ts"], how="inner"); del ob
    gc.collect()
    return d

def skill(x, f17, f10, ob):
    e17 = x[f17] - x[ob]; e10 = x[f10] - x[ob]
    ws = np.round(np.arange(0.50, 1.0001, 0.05), 2)
    mae_w = {w: float((w * x[f17] + (1 - w) * x[f10] - x[ob]).abs().mean()) for w in ws}
    rmse_w = {w: float(np.sqrt(((w * x[f17] + (1 - w) * x[f10] - x[ob]) ** 2).mean())) for w in ws}
    bw_mae = min(mae_w, key=mae_w.get); bw_rmse = min(rmse_w, key=rmse_w.get)
    return dict(n=len(x), mae17=float(e17.abs().mean()), mae10=float(e10.abs().mean()), mae_blend50=mae_w[0.5],
                rmse17=rmse_w[1.0], rmse10=float(np.sqrt((e10 ** 2).mean())), rmse_blend50=rmse_w[0.5],
                bias17=float(e17.mean()), bias10=float(e10.mean()),
                corr17_obs=float(x[f17].corr(x[ob])), corr10_obs=float(x[f10].corr(x[ob])),
                corr_err=float(np.corrcoef(e17, e10)[0, 1]), corr_fc=float(x[f17].corr(x[f10])),
                frac_identical=float((x[f17] == x[f10]).mean()),
                frac_r17_better=float((e17.abs() < e10.abs()).mean()), frac_tie=float((e17.abs() == e10.abs()).mean()),
                best_w_mae=bw_mae, mae_at_best_w=mae_w[bw_mae], mae_gain_pct=100 * (1 - mae_w[bw_mae] / mae_w[1.0]),
                best_w_rmse=bw_rmse, rmse_at_best_w=rmse_w[bw_rmse], rmse_gain_pct=100 * (1 - rmse_w[bw_rmse] / rmse_w[1.0]))

rows = []
for prov in ("A", "B"):
    d = station_frame(prov); st = STA[prov]
    log(prov, "train station frame", d.shape, "stations", d[st].nunique(), "ts range", d.ts.min(), d.ts.max())
    k3 = d.hour.between(11, 15)
    val = d.ts >= pd.Timestamp(T_VAL, tz=TZ)
    new_regime = d.ts >= pd.Timestamp("2025-01-01 01:00", tz=TZ)   # B rounds diverge from 2025-01 (part1b)
    old_regime = val & ~new_regime                                    # 2024-06 .. 2024-12
    for v, o in VARS[prov]:
        f17, f10 = "r17_" + v, "r10_" + v
        for sub, mask in (("all_daytime", np.ones(len(d), bool)), ("hour11-15", k3.values), ("val_year", val.values), ("val_year_hour11-15", (k3 & val).values),
                          ("regime_old_2024-06..12", old_regime.values), ("regime_new_2025-01..05", new_regime.values), ("regime_new_hour11-15", (new_regime & k3).values)):
            x = d.loc[mask, [f17, f10, o]].dropna()
            r = dict(provider=prov, var=v, subset=sub); r.update(skill(x, f17, f10, o)); rows.append(r)
    # test-year transfer of the r10/r17 relationship
    t = station_frame(prov, test=True)
    log(prov, "test station frame", t.shape, "stations", t[st].nunique())
    for v, _ in VARS[prov]:
        f17, f10 = "r17_" + v, "r10_" + v
        for name, fr in (("val_year(train)", d.loc[val]), ("test_year", t)):
            x = fr[[f17, f10]].dropna()
            rows.append(dict(provider=prov, var=v, subset="transfer:" + name, n=len(x), frac_identical=float((x[f17] == x[f10]).mean()),
                             corr_fc=float(x[f17].corr(x[f10])), mean17=float(x[f17].mean()), mean10=float(x[f10].mean()),
                             sd17=float(x[f17].std()), sd10=float(x[f10].std()), mad_17_10=float((x[f17] - x[f10]).abs().mean())))
    del d, t; gc.collect()

R = pd.DataFrame(rows)
R.to_csv(OUT + "/vfr_skill_recompute.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print("\n=== SKILL (station-level, forecast vs observed) ===")
print(R[~R.subset.str.startswith("transfer")][["provider", "var", "subset", "n", "mae17", "mae10", "mae_blend50", "rmse17", "rmse10", "rmse_blend50", "corr17_obs", "corr10_obs", "corr_err", "frac_identical", "frac_r17_better", "frac_tie", "best_w_mae", "mae_gain_pct", "best_w_rmse", "rmse_gain_pct"]].round(4).to_string(index=False))
print("\n=== TRANSFER: r10 vs r17 relationship, validation year vs test year ===")
print(R[R.subset.str.startswith("transfer")][["provider", "var", "subset", "n", "frac_identical", "corr_fc", "mean17", "mean10", "sd17", "sd10", "mad_17_10"]].round(4).to_string(index=False))
log("done")
