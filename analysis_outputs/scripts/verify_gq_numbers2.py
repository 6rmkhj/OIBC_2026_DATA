import numpy as np, pandas as pd
B = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad/"
OUT = B + "analysis/out/vq_"
sites = pd.read_csv("C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset/sites.csv").set_index("site_id")
cf = pd.read_parquet(B + "cache/cf_wide.parquet"); sites = sites.loc[cf.columns]
cap = sites.capacity_kw.to_numpy("float64"); lat = np.deg2rad(sites.lat.to_numpy()); lon = sites.lon.to_numpy()
ts = cf.index; C = cf.to_numpy(); T, N = C.shape; E = (C.astype("float64") * cap[None, :])
hod = ts.hour.to_numpy()
t = ts - pd.Timedelta(minutes=30); doy = t.dayofyear.to_numpy(); hr = t.hour.to_numpy() + t.minute.to_numpy() / 60
g = 2 * np.pi / 365 * (doy - 1 + (hr - 12) / 24)
eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g))
dec = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g) + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
rows = []; flat_hod = np.zeros(24, int); flat_cf = []
for j in range(N):
    x = E[:, j]; c = C[:, j]; pos = x[(x > 0) & ~np.isnan(x)]
    ha = np.deg2rad((hr * 60 + eqt + 4 * lon[j] - 540) / 4 - 180)
    el = np.rad2deg(np.arcsin(np.clip(np.sin(lat[j]) * np.sin(dec) + np.cos(lat[j]) * np.cos(dec) * np.cos(ha), -1, 1)))
    tw = (el <= 0) & (c > 0)
    # flat runs (all members, >=4 identical nonzero, CF>5%)
    same = np.r_[False, (x[1:] == x[:-1]) & (x[1:] > 0)]
    run = np.zeros(T, int); r = 0
    for i in range(T): r = r + 1 if same[i] else 1; run[i] = r
    inrun = np.zeros(T, bool); i = T - 1
    while i >= 0:
        if run[i] >= 4: inrun[i - run[i] + 1:i + 1] = True; i -= run[i]
        else: i -= 1
    fl = inrun & (c > 0.05); flat_hod += np.bincount(hod[fl], minlength=24); flat_cf.append(c[fl])
    rows.append(dict(site=cf.columns[j], cap=cap[j], n_pos=len(pos), n_unique_pos=len(np.unique(np.round(pos, 4))),
        frac_int=float(np.mean(np.abs(pos - np.round(pos)) < 1e-3)), frac_half=float(np.mean(np.abs(pos * 2 - np.round(pos * 2)) < 2e-3)),
        frac_tenth=float(np.mean(np.abs(pos * 10 - np.round(pos * 10)) < 1e-2)),
        flat_h_cf_gt5=int(fl.sum()), flat_med_cf=float(np.median(c[fl])) if fl.any() else np.nan,
        tw_h=int(tw.sum()), tw_kwh=float(x[tw].sum()), tw_share_pct=float(100 * x[tw].sum() / pos.sum()), tw_max_cf=float(c[tw].max()) if tw.any() else 0,
        tw_h_cf_gt5=int((tw & (c > 0.05)).sum()), tw_h_cf_gt2=int((tw & (c > 0.02)).sum())))
R = pd.DataFrame(rows).set_index("site"); R.to_csv(OUT + "quantization_twilight_by_site.csv")
print("portfolio frac of positive values that are integer kWh: median %.3f, mean %.3f; sites with frac_int>0.9: %d; frac_tenth>0.9: %d" % (R.frac_int.median(), R.frac_int.mean(), (R.frac_int > 0.9).sum(), (R.frac_tenth > 0.9).sum()))
print("n_unique_pos: median", int(R.n_unique_pos.median()), "min", int(R.n_unique_pos.min()))
print("flat-line sites (CF>5%) quantization:\n", R[R.flat_h_cf_gt5 > 0].sort_values("flat_h_cf_gt5", ascending=False)[["cap", "n_pos", "n_unique_pos", "frac_int", "frac_half", "frac_tenth", "flat_h_cf_gt5", "flat_med_cf"]].head(12).to_string())
print("flat hours by hour-of-day:", {h: int(v) for h, v in enumerate(flat_hod) if v})
fc = np.concatenate(flat_cf); print("flat-hour CF quantiles p50/p75/p90/max:", np.round(np.quantile(fc, [.5, .75, .9, 1]), 3), "; share of flat hours with CF>0.3:", round(float((fc > 0.3).mean()), 3))
print("twilight (elev_mid<=0) hours with CF>0.05: %d (sites %d); CF>0.02: %d" % (R.tw_h_cf_gt5.sum(), (R.tw_h_cf_gt5 > 0).sum(), R.tw_h_cf_gt2.sum()))
print("top sites by twilight share of own kWh:\n", R.sort_values("tw_share_pct", ascending=False)[["cap", "tw_h", "tw_kwh", "tw_share_pct", "tw_max_cf", "tw_h_cf_gt5"]].head(10).to_string())
print("twilight share quantiles p10/p50/p90:", np.round(R.tw_share_pct.quantile([.1, .5, .9]).to_numpy(), 3))
