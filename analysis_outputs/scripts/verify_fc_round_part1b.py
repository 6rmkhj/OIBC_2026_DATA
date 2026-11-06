# verify_fc_round_part1b.py -- monthly time series of r10/r17 agreement (identical fraction, mean |r17-r10|) per provider,
# train (2023-06..2025-05) + test (2025-06..2026-05), to locate the shift seen in part 1.
import time, gc
import numpy as np, pandas as pd
import pyarrow as pa, pyarrow.parquet as pq, pyarrow.compute as pc
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
T0 = time.time()
def log(*a): print(f"[{time.time()-T0:6.1f}s]", *a, flush=True)
ROOT = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad"
CACHE = ROOT + "/cache"; OUT = ROOT + "/analysis/out"; TZ = "Asia/Seoul"
def tsc(s): return pa.scalar(pd.Timestamp(s, tz=TZ).value // 1000, type=pa.timestamp("us", tz=TZ))
FILT_TR = (pc.field("ts") >= tsc("2023-06-01 01:00")) & (pc.field("elev") > 0)
FILT_TE = pc.field("elev") > 0
V = {"wa_station": ["wa_cloud", "wa_humidity"], "wb_station": ["wb_cloud", "wb_uv_idx"]}

def read(path, cols, filt):
    t = pq.read_table(path, columns=cols, filters=filt, read_dictionary=[c for c in cols if c.endswith("station")])
    df = t.to_pandas(); del t
    for c in df.columns:
        if df[c].dtype == np.float64: df[c] = df[c].astype(np.float32)
    return df

rows = []
for st, vs in V.items():
    for split, f17p, f10p, filt in (("train", "panel_train_r17", "panel_train_r10", FILT_TR), ("test", "panel_test_r17", "panel_test_r10", FILT_TE)):
        f17 = read(CACHE + f"/{f17p}.parquet", ["ts", st] + vs, filt).drop_duplicates([st, "ts"])
        f10 = read(CACHE + f"/{f10p}.parquet", ["ts", st] + vs, filt).drop_duplicates([st, "ts"])
        f17[st] = f17[st].astype(str); f10[st] = f10[st].astype(str)
        d = f17.merge(f10, on=[st, "ts"], suffixes=("_17", "_10")); del f17, f10
        d["month"] = d.ts.dt.tz_convert(TZ).dt.strftime("%Y-%m")
        for v in vs:
            x = d[[v + "_17", v + "_10", "month"]].dropna()
            g = x.groupby("month").apply(lambda s: pd.Series(dict(n=len(s), frac_identical=float((s[v + "_17"] == s[v + "_10"]).mean()),
                                                                mad=float((s[v + "_17"] - s[v + "_10"]).abs().mean()), corr=float(s[v + "_17"].corr(s[v + "_10"])))), include_groups=False).reset_index()
            g.insert(0, "var", v); g.insert(0, "split", split); rows.append(g)
        del d; gc.collect()
        log(st, split, "done")
R = pd.concat(rows, ignore_index=True)
R.to_csv(OUT + "/vfr_round_agreement_by_month.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
for v in ["wa_cloud", "wa_humidity", "wb_cloud", "wb_uv_idx"]:
    s = R[R["var"] == v]
    print(f"\n=== {v}: monthly r10/r17 agreement ===")
    print(s[["split", "month", "n", "frac_identical", "mad", "corr"]].round(4).to_string(index=False))
fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
for v, c in (("wa_cloud", "tab:blue"), ("wb_cloud", "tab:red"), ("wb_uv_idx", "tab:orange"), ("wa_humidity", "tab:green")):
    s = R[R["var"] == v]
    axes[0].plot(s.month, s.frac_identical, marker="o", ms=3, color=c, label=v)
    axes[1].plot(s.month, s.mad / s.mad.iloc[:12].mean(), marker="o", ms=3, color=c, label=v)
axes[0].set_ylabel("fraction r17 == r10"); axes[1].set_ylabel("mean|r17-r10| / first-12-month mean")
for ax in axes:
    ax.axvline(s.month.tolist().index("2025-06") if "2025-06" in s.month.tolist() else 24, color="k", ls="--", lw=1); ax.grid(alpha=.3); ax.legend(fontsize=8)
axes[1].tick_params(axis="x", rotation=90)
fig.suptitle("Round-10 vs round-17 forecast agreement by month (station-level, daytime); dashed = test year start")
fig.tight_layout(); fig.savefig(OUT + "/vfr_fig_round_agreement_by_month.png", dpi=110)
log("done")
