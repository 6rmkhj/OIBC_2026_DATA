# Adversarial re-check of gen_quality anomaly claims + cost of the "night -> 0" cleaning rule.
import numpy as np, pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import pyarrow.parquet as pq
B = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad/"
OUT = B + "analysis/out/"; DS = "C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset/"
lines = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); lines.append(s)

cf = pd.read_parquet(B + "cache/cf_wide.parquet"); ts = cf.index
sites = pd.read_csv(DS + "sites.csv").set_index("site_id").loc[cf.columns]
cap = sites.capacity_kw.values.astype("float32")[None, :]
C = cf.values.astype("float32"); del cf
E = C * cap  # kWh
obs = ~np.isnan(C)
P("cf_wide", C.shape, ts.min(), ts.max(), "obs cells", int(obs.sum()))

# ---- 1. negatives / CF>1 ----
neg = obs & (C < 0); gt1 = obs & (C > 1)
P("NEG: n=%d sum_kwh=%.4f sites=%d" % (neg.sum(), np.nansum(np.where(neg, E, 0)), (neg.sum(0) > 0).sum()))
P("CF>1: n=%d sites=%d max=%.4f" % (gt1.sum(), (gt1.sum(0) > 0).sum(), np.nanmax(np.where(gt1, C, np.nan))))

# ---- 2. internal gaps (missing rows after first observed row) ----
first = obs.argmax(0); last = obs.shape[0] - 1 - obs[::-1].argmax(0)
idx = np.arange(len(ts))[:, None]
gap = (idx >= first[None, :]) & (idx <= last[None, :]) & ~obs
P("INTERNAL GAP cells: %d ; sites with gaps: %s ; sites not ending at last ts: %d"
  % (gap.sum(), list(sites.index[gap.sum(0) > 0]), int((last < len(ts) - 1).sum())))

# ---- 3. flat-lines: >=4 consecutive identical nonzero values ----
same = np.zeros_like(obs); same[1:] = obs[1:] & obs[:-1] & (C[1:] == C[:-1]) & (C[1:] != 0)
flat_h = 0; flat_h5 = 0; longest = 0; flat_vals = []
for j in range(C.shape[1]):
    s = same[:, j]; i = 0; T = len(s)
    while i < T:
        if s[i]:
            k = i
            while k < T and s[k]: k += 1
            L = k - i + 1
            if L >= 4:
                flat_h += L; longest = max(longest, L)
                if C[i, j] > 0.05: flat_h5 += L; flat_vals.append((sites.index[j], float(C[i, j]), L, float(np.nanmax(C[:, j]))))
            i = k
        else: i += 1
P("FLAT: hours in runs>=4: %d ; with CF>5%%: %d ; longest run: %d" % (flat_h, flat_h5, longest))
fv = pd.DataFrame(flat_vals, columns=["site_id", "cf", "run_len", "site_max_cf"]); fv["cf_over_sitemax"] = fv.cf / fv.site_max_cf
if len(fv): P("FLAT CF>5%% runs: n_runs=%d ; cf/site_max median=%.3f p25=%.3f p75=%.3f ; share cf/site_max>0.9: %.3f"
              % (len(fv), fv.cf_over_sitemax.median(), fv.cf_over_sitemax.quantile(.25), fv.cf_over_sitemax.quantile(.75), (fv.cf_over_sitemax > 0.9).mean()))
fv.to_csv(OUT + "vq_flat_runs.csv", index=False)

# ---- 4. solar elevation (NOAA, same as build_cache) at interval start / midpoint / end ----
def elev_at(t):
    doy = t.dayofyear.values; hr = t.hour.values + t.minute.values / 60
    g = 2 * np.pi / 365 * (doy - 1 + (hr - 12) / 24)
    eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g))
    decl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g) + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    la = np.deg2rad(sites.lat.values)[None, :]; lon = sites.lon.values[None, :]
    tst = hr[:, None] * 60 + eqt[:, None] + 4 * (lon - 135.0); ha = np.deg2rad(tst / 4 - 180)
    cz = np.sin(la) * np.sin(decl[:, None]) + np.cos(la) * np.cos(decl[:, None]) * np.cos(ha)
    return np.rad2deg(np.arcsin(np.clip(cz, -1, 1))).astype("float32"), (ha < 0)
el_mid, morning = elev_at(ts - pd.Timedelta("30min"))
el_end, _ = elev_at(ts); el_start, _ = elev_at(ts - pd.Timedelta("60min"))

tb = pq.read_table(B + "cache/panel_train_r17.parquet", columns=["site_id", "ts", "elev"], filters=[("site_id", "==", "PV001")]).to_pandas()
j = list(sites.index).index("PV001"); tbts = pd.DatetimeIndex(tb.ts); tbts = tbts.tz_localize('Asia/Seoul') if tbts.tz is None else tbts.tz_convert('Asia/Seoul'); mine = pd.Series(el_mid[:, j], index=ts).reindex(tbts); P('panel ts dtype', tb.ts.dtype, 'reindex NaN', int(mine.isna().sum()))
P("panel elev vs my midpoint elev (PV001, n=%d): max|diff|=%.3f deg" % (len(tb), np.nanmax(np.abs(mine.values - tb.elev.values)))); del tb, mine

night_mid = el_mid <= 0; night_both = (el_start <= 0) & (el_end <= 0); true_night = el_mid <= -6
tot_E = np.nansum(np.where(obs, E, 0)); nz = obs & (C > 0)
P("NIGHT(mid<=0) nonzero hours: %d ; twilight (-6,0]: %d ; true night <=-6: %d"
  % ((nz & night_mid).sum(), (nz & night_mid & ~true_night).sum(), (nz & true_night).sum()))
tn_E = np.nansum(np.where(true_night & obs, E, 0)); tw_E = np.nansum(np.where(night_mid & ~true_night & obs, E, 0))
P("true-night energy: %.1f kWh = %.5f%% of total %.0f kWh" % (tn_E, 100 * tn_E / tot_E, tot_E))
P("twilight (-6<mid<=0) energy: %.1f kWh = %.4f%% of total" % (tw_E, 100 * tw_E / tot_E))
P("energy at mid<=0 while sun up at interval start or end: %.1f kWh" % np.nansum(np.where(night_mid & ~night_both & obs, E, 0)))

# ---- 5. convention test: energy by midpoint-elevation band, morning vs evening ----
bands = [-90, -12, -6, -3, 0, 3, 6, 10, 90]
def band_table(el, morn):
    rows = []
    for lo, hi in zip(bands[:-1], bands[1:]):
        m = obs & (el > lo) & (el <= hi)
        for nm, mm in (("morning", m & morn), ("evening", m & ~morn)):
            rows.append(dict(band=f"({lo},{hi}]", half=nm, hours=int(mm.sum()), nonzero_hours=int((mm & nz).sum()),
                             energy_kwh=float(np.nansum(np.where(mm, E, 0)))))
    return pd.DataFrame(rows)
bt = band_table(el_mid, morning); bt.to_csv(OUT + "vq_energy_by_elev_band.csv", index=False)
P("ENERGY BY MIDPOINT-ELEV BAND (ts = interval END, README):\n" + bt.to_string(index=False))
el_alt, morning_alt = elev_at(ts + pd.Timedelta("30min"))
bt2 = band_table(el_alt, morning_alt); bt2.to_csv(OUT + "vq_energy_by_elev_band_LEFTCLOSED.csv", index=False)
P("ENERGY BY ELEV BAND if ts were interval START (midpoint ts+30):\n" + bt2.to_string(index=False)); del el_alt, morning_alt

# ---- 6. cost of the 'night -> forecast 0' rule in VAL year, in W units ----
smp = pd.read_parquet(B + "cache/smp_all.parquet"); w = (smp.smp * smp.k).astype("float64"); w.index = smp.ts
wv = w.reindex(ts).values; assert not np.isnan(wv).any()
VAL0 = pd.Timestamp("2024-06-01 01:00", tz="Asia/Seoul"); VAL1 = pd.Timestamp("2025-06-01 00:00", tz="Asia/Seoul")
val = np.asarray((ts >= VAL0) & (ts <= VAL1))
val_E = np.nansum(np.where(obs & val[:, None], E, 0))
def Wcost(mask):
    e = np.nansum(np.where(mask & obs & val[:, None], E, 0), 1)
    return float((wv * e).sum()), float(e.sum())
for nm, m in (("mid<=0 (panel/model rule)", night_mid), ("mid<=-6", true_night), ("start&end<=0 (sun never up)", night_both), ("mid<=-3", el_mid <= -3)):
    Wc, Ec = Wcost(m); P("VAL W-cost of forcing 0 where %-28s: W=%.3e kWh=%.0f (=%.2f%% of best single-model W 2.115e9; %.3f%% of VAL kWh %.0f)" % (nm, Wc, Ec, 100 * Wc / 2.115e9, 100 * Ec / val_E, val_E))
e_mid = np.nansum(np.where(night_mid & obs & val[:, None], E, 0), 1) * wv
tsv = pd.Series(ts, index=ts)[val]
P("mid<=0 W-cost by month (VAL, 1e6):\n" + (pd.Series(e_mid, index=ts)[val].groupby(tsv.dt.month).sum() / 1e6).round(2).to_string())
hs = pd.Series(e_mid, index=ts)[val].groupby(tsv.dt.hour).sum()
P("mid<=0 W-cost by hour (VAL, 1e6):\n" + (hs[hs > 0] / 1e6).round(2).to_string())

# ---- 7. VAL missing rows ----
miss_val = (~obs) & val[:, None]
P("VAL missing cells: %d ; daytime(mid>0): %d" % (miss_val.sum(), (miss_val & ~night_mid).sum()))

fig, ax = plt.subplots(1, 2, figsize=(12, 4))
order = [f"({lo},{hi}]" for lo, hi in zip(bands[:-1], bands[1:])]
for i, (df, t) in enumerate(((bt, "ts = interval END (README)"), (bt2, "ts = interval START (alt.)"))):
    piv = df.pivot(index="band", columns="half", values="energy_kwh").reindex(order).clip(lower=1)
    piv.plot.bar(ax=ax[i], logy=True); ax[i].set_title("kWh by midpoint elev band: " + t, fontsize=10); ax[i].set_ylabel("kWh (log)")
plt.tight_layout(); plt.savefig(OUT + "vq_fig_elev_band_symmetry.png", dpi=110)
open(OUT + "vq_verify_genq_math_log.txt", "w", encoding="utf-8").write("\n".join(lines))
