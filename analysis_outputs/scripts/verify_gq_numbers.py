# Independent re-check of gen_quality anomaly counts + impact of the proposed cleaning rules.
import numpy as np, pandas as pd
B = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad/"
OUT = B + "analysis/out/vq_"
sites = pd.read_csv("C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset/sites.csv").set_index("site_id")
cf = pd.read_parquet(B + "cache/cf_wide.parquet")
sites = sites.loc[cf.columns]
cap = sites.capacity_kw.to_numpy("float64"); lat = np.deg2rad(sites.lat.to_numpy()); lon = sites.lon.to_numpy()
ts = cf.index; C = cf.to_numpy(); T, N = C.shape; obs = ~np.isnan(C)
E = C * cap[None, :].astype("float32")               # kWh, float32
tot = float(np.nansum(E, dtype="float64"))
print("cf_wide", C.shape, "obs rows", int(obs.sum()), "total kWh", round(tot, 1))

smp = pd.read_parquet(B + "cache/smp_all.parquet").set_index("ts").reindex(ts)
w = (smp.smp * smp.k).to_numpy("float64"); print("w aligned NaN:", int(np.isnan(w).sum()))

def elev(off_min):  # solar elevation at ts - off_min (NOAA approx), per site loop to save RAM
    t = ts - pd.Timedelta(minutes=off_min)
    doy = t.dayofyear.to_numpy(); hr = t.hour.to_numpy() + t.minute.to_numpy() / 60
    g = 2 * np.pi / 365 * (doy - 1 + (hr - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g))
    dec = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g) + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    out = np.empty((T, N), "float32")
    for j in range(N):
        ha = np.deg2rad((hr * 60 + eqt + 4 * lon[j] - 540) / 4 - 180)
        cz = np.sin(lat[j]) * np.sin(dec) + np.cos(lat[j]) * np.cos(dec) * np.cos(ha)
        out[:, j] = np.rad2deg(np.arcsin(np.clip(cz, -1, 1)))
    return out
e_mid = elev(30); e_end = elev(0); e_sta = elev(60)

rows = []
def night_stats(name, mask):
    nz = mask & (C > 0)
    k = float(np.nansum(np.where(nz, E, 0), dtype="float64"))
    kw = float(np.nansum(np.where(nz, E * w[:, None], 0), dtype="float64"))
    rows.append(dict(rule=name, nonzero_hours=int(nz.sum()), sites=int(nz.any(0).sum()), kwh=round(k, 1),
                     pct_of_total_kwh=round(100 * k / tot, 4), pct_of_total_w_kwh=round(100 * kw / float(np.nansum(E * w[:, None], dtype="float64")), 4),
                     max_cf=float(np.nanmax(np.where(nz, C, np.nan))) if nz.any() else 0.0))
night_stats("elev_mid<=0 (report 'night')", e_mid <= 0)
night_stats("elev_mid<=-6 (true night)", e_mid <= -6)
night_stats("twilight -6<elev_mid<=0", (e_mid > -6) & (e_mid <= 0))
night_stats("elev_end<=0 (end of interval)", e_end <= 0)
night_stats("elev_start<=0 (start of interval)", e_sta <= 0)
night_stats("sun below horizon whole hour (start&end<=0)", (e_sta <= 0) & (e_end <= 0))
night_stats("sun below horizon whole hour & mid<=-6", (e_sta <= 0) & (e_end <= 0) & (e_mid <= -6))
night_stats("hour 22-04", np.isin(ts.hour, [22, 23, 0, 1, 2, 3, 4])[:, None] & np.ones((1, N), bool))
R = pd.DataFrame(rows); R.to_csv(OUT + "night_rule_impact.csv", index=False); print(R.to_string())

# twilight kWh by hour-of-day / season (where does the forced-zero loss sit?)
tw = (e_mid > -6) & (e_mid <= 0) & (C > 0)
twE = np.where(tw, E, 0).sum(1, dtype="float64")
byh = pd.Series(twE).groupby(ts.hour.to_numpy()).sum().round(0); print("twilight kWh by hour:\n", byh[byh > 0].to_string())
bym = pd.Series(twE).groupby(ts.month.to_numpy()).sum().round(0); print("twilight kWh by month:\n", bym.to_string())
# typical CF of generating twilight hours
twcf = C[tw]; print("twilight CF quantiles p50/p90/p99/max:", np.round(np.nanquantile(twcf, [.5, .9, .99, 1]), 4))
# VAL year share
val = (ts >= pd.Timestamp("2024-06-01 01:00", tz="Asia/Seoul")) & (ts <= pd.Timestamp("2025-06-01 00:00", tz="Asia/Seoul"))
Ev = E[val]; wv = w[val]; twv = tw[val]
val_tot = float(np.nansum(Ev, dtype="float64")); val_wtot = float(np.nansum(Ev * wv[:, None], dtype="float64"))
val_tw = float(np.nansum(np.where(twv, Ev, 0), dtype="float64")); val_tww = float(np.nansum(np.where(twv, Ev * wv[:, None], 0), dtype="float64"))
print(f"VAL: twilight kWh {val_tw:,.0f} = {100*val_tw/val_tot:.3f}% of kWh; w-weighted {100*val_tww/val_wtot:.3f}% of Σw·actual ({val_tww:.3e} of {val_wtot:.3e})")
del e_end, e_sta

# negatives / CF>1
neg = C < 0; gt1 = C > 1
print("negatives: n", int(neg.sum()), "sum kWh", round(float(np.nansum(np.where(neg, E, 0))), 3), "sites", int(neg.any(0).sum()), "min kWh", round(float(np.nanmin(np.where(neg, E, np.nan))), 3))
print("CF>1: n", int(gt1.sum()), "sites", int(gt1.any(0).sum()), "max CF", round(float(np.nanmax(C)), 4), "kWh removed by clip to 1:", round(float(np.nansum(np.where(gt1, (C - 1) * cap[None, :], 0))), 2))
gi = np.argwhere(gt1); print(pd.DataFrame({"site": cf.columns[gi[:, 1]], "ts": ts[gi[:, 0]], "cf": C[gt1]}).to_string())

# internal gaps (missing rows between first and last observation)
first = obs.argmax(0); last = T - 1 - obs[::-1].argmax(0)
inner_nan = np.array([(~obs[first[j]:last[j] + 1, j]).sum() for j in range(N)])
print("internal missing hours total:", int(inner_nan.sum()), "sites with any:", int((inner_nan > 0).sum()), {cf.columns[j]: int(inner_nan[j]) for j in np.flatnonzero(inner_nan)})
j = int(np.flatnonzero(inner_nan)[0]) if inner_nan.any() else None
if j is not None:
    idx = np.flatnonzero(~obs[first[j]:last[j] + 1, j]) + first[j]; print("gap ts:", ts[idx].min(), "->", ts[idx].max())

# flat-lines: >=4 identical consecutive nonzero values; meter resolution
fl = []; 
for j in range(N):
    x = E[:, j]; same = np.zeros(T, bool); same[1:] = (x[1:] == x[:-1]) & (x[1:] > 0)
    # run lengths of identical values
    run = np.zeros(T, int); r = 0
    for i in range(T):
        r = r + 1 if same[i] else 1; run[i] = r
    # mark members of runs with final length>=4
    inrun = np.zeros(T, bool); i = T - 1
    while i >= 0:
        if run[i] >= 4 and (i == T - 1 or run[i + 1] == 1): inrun[i - run[i] + 1:i + 1] = True; i -= run[i]
        else: i -= 1
    pos = x[x > 0]; u = np.unique(pos[~np.isnan(pos)]); step = float(np.diff(u).min()) if len(u) > 1 else np.nan
    fl.append(dict(site=cf.columns[j], flat_h=int(inrun.sum()), flat_h_cf_gt5=int((inrun & (C[:, j] > 0.05)).sum()), longest=int(run.max()) if inrun.any() else 0, min_step_kwh=step, n_unique_pos=len(u)))
F = pd.DataFrame(fl).set_index("site"); F.to_csv(OUT + "flatline_by_site.csv")
print("flat-line hours total:", int(F.flat_h.sum()), "CF>5%:", int(F.flat_h_cf_gt5.sum()), "sites CF>5%:", int((F.flat_h_cf_gt5 > 0).sum()), "longest:", int(F.longest.max()))
print("median min step kWh:", F.min_step_kwh.median())
print(F.sort_values("flat_h_cf_gt5", ascending=False).head(8).to_string())
# example: longest CF>5% flat run of top site
s = F.flat_h_cf_gt5.idxmax(); j = cf.columns.get_loc(s); x = E[:, j]
same = np.r_[False, (x[1:] == x[:-1]) & (x[1:] > 0) & (C[1:, j] > 0.05)]
i = int(np.argmax(np.convolve(same.astype(int), np.ones(4, int), "valid") == 4)); print(f"example {s} run starting {ts[i]}:", x[i:i + 6].round(3), "capacity", cap[j])
