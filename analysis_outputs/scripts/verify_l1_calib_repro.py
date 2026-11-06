"""Adversarial verifier (reproduce-a-key-number): does L1 / SMP*k-weighted L1 training + weighted-median
calibration lower the official penalty W vs the L2 pooled baseline on the time-split validation year?
Independent re-implementation: own group map (sites.csv), own weights (smp_all), own aggregation, fresh seeds.
Restartable: per-model predictions are cached in analysis/verify_cache/pred_{obj}_{seed}.npy.
Outputs are prefixed vrepro_ (a concurrent agent uses the verify_l1_calib_ prefix)."""
import os, sys, time, gc, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

BASE = 'C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad/'
CACHE, OUT, MV, VC = BASE + 'cache/', BASE + 'analysis/out/', BASE + 'analysis/mv_cache/', BASE + 'analysis/verify_cache/'
SITES = 'C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset/sites.csv'
PFX = OUT + 'vrepro_'
os.makedirs(VC, exist_ok=True)
TZ = 'Asia/Seoul'
T0 = pd.Timestamp('2022-06-01 00:00', tz=TZ); T1 = pd.Timestamp('2024-06-01 00:00', tz=TZ)
T2 = pd.Timestamp('2025-06-01 00:00', tz=TZ); TH = pd.Timestamp('2024-12-01 00:00', tz=TZ)
TL = pd.Timestamp('2023-06-01 00:00', tz=TZ)  # last training year start (for train-residual calibration)
A6 = ['wa_cloud', 'wa_temp', 'wa_humidity', 'wa_ground_press', 'wa_wind_speed', 'wa_rain']
B9 = ['wb_cloud', 'wb_uv_idx', 'wb_temp', 'wb_rel_hum', 'wb_dew_point', 'wb_vis', 'wb_ceiling', 'wb_precip_prob', 'wb_total_liq']
BASEF = A6 + B9 + ['elev', 'azim', 'cosz', 'doy_sin', 'doy_cos', 'hour', 'capacity_kw', 'lat', 'lon']
LGB = dict(n_estimators=400, learning_rate=0.06, num_leaves=127, min_child_samples=200, subsample=0.8,
           subsample_freq=1, colsample_bytree=0.8, verbose=-1, n_jobs=10)
RUNS = [('l2', 101), ('l1', 101), ('l1w', 101), ('l2', 202), ('l1', 202), ('l1w', 202), ('l2', 303)]
def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)

# ------------------------------------------------------------------ independent metric machinery
sites = pd.read_csv(SITES)
GMAP = sites.set_index('site_id').current_group.to_dict()
smp = pd.read_parquet(CACHE + 'smp_all.parquet')
assert set(smp.k.unique()) <= {1, 3}
assert (smp.k.values == np.where(smp.ts.dt.hour.isin([11, 12, 13, 14, 15]), 3, 1)).all(), 'k column disagrees with hour rule'
WMAP = pd.Series((smp.smp * smp.k).astype('float64').values, index=smp.ts)

def fix_ts(ts):
    """numpy datetime64 from a tz-aware column is naive UTC -> make it tz-aware Asia/Seoul."""
    t = pd.DatetimeIndex(ts)
    return (t.tz_localize('UTC') if t.tz is None else t).tz_convert(TZ)

def group_frame(ts, site_ids, y, p):
    """(ts, group) sums -> frame indexed by ts with y_A,y_B,p_A,p_B,w. Own group map, own weights."""
    g = pd.Series(site_ids).map(GMAP).values
    assert not pd.isna(g).any()
    d = pd.DataFrame({'ts': fix_ts(ts), 'g': g, 'y': np.asarray(y, 'float64'), 'p': np.asarray(p, 'float64')})
    a = d.groupby(['ts', 'g'])[['y', 'p']].sum().unstack('g').fillna(0.0)
    a.columns = [f'{x}_{y}' for x, y in a.columns]
    a['w'] = WMAP.reindex(a.index).values
    assert a.w.notna().all() and len(a) == 8760, (a.w.isna().sum(), len(a))
    a['hour'] = a.index.hour
    return a

def W(a, pA=None, pB=None):
    pA = a.p_A if pA is None else pA; pB = a.p_B if pB is None else pB
    return float((a.w * (np.abs(pA - a.y_A) + np.abs(pB - a.y_B))).sum())

def metr(a):
    Rw = float((a.w * (a.y_A + a.y_B)).sum()); w = W(a)
    return dict(W_ref=w, W_ref_pct=100 * w / Rw, Rw=Rw, bias_G1=float((a.p_A - a.y_A).mean()), bias_G2=float((a.p_B - a.y_B).mean()))

def wmedian(x, wt):
    o = np.argsort(x); x = x[o]; c = np.cumsum(wt[o]); return float(x[min(np.searchsorted(c, 0.5 * c[-1]), len(x) - 1)])

def fit_fac(fr, grp, hourly):
    """argmin_a sum w|y - a p| = (w p)-weighted median of y/p. Global (hourly=False) or per-hour (fallback 1)."""
    y, p, w, h = fr[f'y_{grp}'].values, fr[f'p_{grp}'].values, fr.w.values, fr.hour.values
    m = (p > 1) & (w > 0)
    if not hourly:
        return np.full(24, wmedian(y[m] / p[m], (w * p)[m]))
    out = np.ones(24)
    for hh in range(24):
        mm = m & (h == hh)
        if mm.sum() > 20: out[hh] = wmedian(y[mm] / p[mm], (w * p)[mm])
    return out

def apply_fac(fr, facA, facB):
    return fr.p_A.values * facA[fr.hour.values], fr.p_B.values * facB[fr.hour.values]

def calib_half(a, hourly):
    """2-fold by season half: fit on one half, apply to the other; returns total W after calibration."""
    tot = 0.0
    for fit_m in (a.index <= TH, a.index > TH):
        fit, tst = a[fit_m], a[~fit_m]
        pA, pB = apply_fac(tst, fit_fac(fit, 'A', hourly), fit_fac(fit, 'B', hourly))
        tot += W(tst, pA, pB)
    return tot

def calib_from(a_fit, a, hourly):
    pA, pB = apply_fac(a, fit_fac(a_fit, 'A', hourly), fit_fac(a_fit, 'B', hourly))
    return W(a, pA, pB)

# ------------------------------------------------------------------ 1. recompute W from the site-level caches
rows = []
log('== part 1: re-aggregate cached site predictions ==')
GF = {}
for name in ['E0_pool', 'E1_l1w', 'E0_site', 'E7_mix_site10']:
    d = pd.read_parquet(CACHE + f'val_pred_site_{name}.parquet')
    assert d.ts.min() > T1 and d.ts.max() <= T2
    a = group_frame(d.ts.values, d.site_id.values, d.y.values, d.pred.values); del d
    m = metr(a); GF[name] = a
    js = json.load(open(OUT + f'metrics_{name}.json'))
    rows.append(dict(source='cache', model=name, seed='orig', **m, W_ref_reported=js['W_ref'], rel_diff_pct=100 * (m['W_ref'] / js['W_ref'] - 1)))
    log(name, 'W_ref mine %.4e reported %.4e (%.3f%%) W%% %.3f' % (m['W_ref'], js['W_ref'], rows[-1]['rel_diff_pct'], m['W_ref_pct']))

# ------------------------------------------------------------------ 2. independent retrain with fresh seeds
log('== part 2: load day/night ==')
cols = ['site_id', 'ts', 'energy', 'current_group', 'cf'] + BASEF
df = pd.read_parquet(MV + 'day.parquet', columns=cols)
df['site_id'] = df.site_id.astype(str)
assert (df.site_id.map(GMAP).values == df.current_group.astype(str).values).all(), 'group map mismatch'
assert (df.ts > T0).all() and (df.ts <= T2).all()
cf_chk = (df.energy / df.capacity_kw).clip(0, 1.2).astype('float32')
assert np.allclose(cf_chk.values, df.cf.values, atol=1e-5), 'cf column mismatch'
del cf_chk
isv = (df.ts > T1).values
tr, va = df[~isv].copy(), df[isv].copy(); del df; gc.collect()
night = pd.read_parquet(MV + 'night.parquet', columns=['site_id', 'ts', 'energy'])
night = night[night.ts > T1].copy(); night['site_id'] = night.site_id.astype(str)
log('train rows', len(tr), 'val day rows', len(va), 'val night rows', len(night))
wtr = tr.ts.map(WMAP).astype('float64').values; wtr = (wtr / wtr.mean()).astype('float32')
assert np.isfinite(wtr).all()
last = (tr.ts > TL).values  # last training year, for in-sample residual calibration

def val_frame(p_day):
    ts = np.concatenate([va.ts.values, night.ts.values]); sid = np.concatenate([va.site_id.values, night.site_id.values])
    y = np.concatenate([va.energy.values, night.energy.values]); p = np.concatenate([p_day, np.zeros(len(night))])
    return group_frame(ts, sid, y, p)

pv = np.load(MV + 'pred_E1_l1w.npy')
assert len(pv) == len(va)
a_chk = val_frame(pv.astype('float64')); log('alignment check pred_E1_l1w.npy -> W_ref %.4e (reported 2.1534e9)' % W(a_chk))
ALIGNED = abs(W(a_chk) / 2153371817.17 - 1) < 1e-3
if ALIGNED:
    for name in ['E0_pool', 'E1_l1', 'E1_l2w', 'E1_l1w', 'E1_l1w_s2', 'E1_l1w_s3']:
        a = val_frame(np.load(MV + f'pred_{name}.npy').astype('float64')); m = metr(a); GF[name] = a
        js = json.load(open(OUT + f'metrics_{name}.json'))
        rows.append(dict(source='orig_npy', model=name, seed='orig', **m, W_ref_reported=js['W_ref'], rel_diff_pct=100 * (m['W_ref'] / js['W_ref'] - 1)))
        log(name, 'W_ref mine %.4e reported %.4e W%% %.3f' % (m['W_ref'], js['W_ref'], m['W_ref_pct']))

import lightgbm as lgb
Xt, Xv = tr[BASEF], va[BASEF]
TRF = {}
fit_sec = {}
for obj, seed in RUNS:
    f = VC + f'pred_{obj}_{seed}.npy'; fi = VC + f'predtr_{obj}_{seed}.npy'
    if not os.path.exists(f):
        t = time.time()
        m = lgb.LGBMRegressor(objective='regression' if obj == 'l2' else 'regression_l1', random_state=seed, **LGB)
        m.fit(Xt, tr.cf.values, sample_weight=wtr if obj == 'l1w' else None)
        p = (np.clip(m.predict(Xv), 0, None) * va.capacity_kw.values).astype('float32')
        ptr = (np.clip(m.predict(Xt[last]), 0, None) * tr.capacity_kw.values[last]).astype('float32')
        np.save(f, p); np.save(fi, ptr); del m; gc.collect()
        fit_sec[(obj, seed)] = time.time() - t
        log(f'trained {obj} seed {seed} in {fit_sec[(obj, seed)]:.0f}s')
    p = np.load(f); ptr = np.load(fi)
    a = val_frame(p.astype('float64')); m = metr(a); GF[f'V_{obj}_{seed}'] = a
    trl = tr[last]
    d = pd.DataFrame({'ts': fix_ts(trl.ts.values), 'g': trl.site_id.map(GMAP).values, 'y': trl.energy.values.astype('float64'), 'p': ptr.astype('float64')})
    af = d.groupby(['ts', 'g'])[['y', 'p']].sum().unstack('g').fillna(0.0); af.columns = [f'{x}_{y}' for x, y in af.columns]
    af['w'] = WMAP.reindex(af.index).values; af['hour'] = af.index.hour; TRF[f'V_{obj}_{seed}'] = af
    rows.append(dict(source='verify', model=f'V_{obj}', seed=seed, **m, W_ref_reported=np.nan, rel_diff_pct=np.nan))
    log(f'V_{obj} seed {seed}: W_ref %.4e  W%% %.3f  bias %.1f/%.1f' % (m['W_ref'], m['W_ref_pct'], m['bias_G1'], m['bias_G2']))
del Xt, Xv; gc.collect()

res = pd.DataFrame(rows); res.to_csv(PFX + 'models.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
log('\n' + res.round(4).to_string())
vs = res[res.source == 'verify'].groupby('model').W_ref_pct.agg(['mean', 'std', 'min', 'max', 'count'])
log('\nverify runs by objective (W_ref%):\n' + vs.round(4).to_string())
# pooled seed statistics: original + verify runs per objective family
fam = {'L2': ['E0_pool', 'V_l2'], 'L1': ['E1_l1', 'V_l1'], 'L1w': ['E1_l1w', 'E1_l1w_s2', 'E1_l1w_s3', 'V_l1w']}
r2 = res.drop_duplicates(['model', 'seed'])
fs = pd.DataFrame({k: r2[r2.model.isin(v)].W_ref_pct.agg(['mean', 'std', 'min', 'max', 'count']) for k, v in fam.items()}).T
fs.to_csv(PFX + 'family_stats.csv'); log('\nall seeds (orig + verify) by objective family (W_ref%):\n' + fs.round(4).to_string())

# ------------------------------------------------------------------ 3. weighted-median calibration
log('== part 3: calibration ==')
crow = []
for name, a in GF.items():
    base = W(a)
    r = dict(model=name, W_base=base, W_global_halfCV=calib_half(a, False), W_hourly_halfCV=calib_half(a, True))
    if name in TRF:
        r['W_global_trainfit'] = calib_from(TRF[name], a, False); r['W_hourly_trainfit'] = calib_from(TRF[name], a, True)
        r['fac_train_G1'] = fit_fac(TRF[name], 'A', False)[0]; r['fac_train_G2'] = fit_fac(TRF[name], 'B', False)[0]
    h1 = a[a.index <= TH]; h2 = a[a.index > TH]
    r['fac_H1_G1'] = fit_fac(h1, 'A', False)[0]; r['fac_H1_G2'] = fit_fac(h1, 'B', False)[0]
    r['fac_H2_G1'] = fit_fac(h2, 'A', False)[0]; r['fac_H2_G2'] = fit_fac(h2, 'B', False)[0]
    r['W_global_insample'] = calib_from(a, a, False); r['W_hourly_insample'] = calib_from(a, a, True)
    for k in list(r):
        if k.startswith('W_') and k != 'W_base': r[k.replace('W_', 'impr_pct_')] = 100 * (1 - r[k] / base)
    crow.append(r)
cal = pd.DataFrame(crow); cal.to_csv(PFX + 'calibration.csv', index=False)
log('\n' + cal.round(4).to_string())

# ------------------------------------------------------------------ 4. decisive comparison: L1(+calib) vs L2 baseline
log('== part 4: decisive comparison ==')
l2_mine = res[(res.source == 'verify') & (res.model == 'V_l2')].W_ref
dec = []
for name in [n for n in GF if n.startswith('V_l1')] + ['E1_l1w', 'E1_l1w_s2', 'E1_l1w_s3', 'E1_l1']:
    if name not in GF: continue
    c = cal[cal.model == name].iloc[0]
    for variant, wv in [('no calib', c.W_base), ('global wmedian halfCV', c.W_global_halfCV), ('hourly wmedian halfCV', c.W_hourly_halfCV),
                        ('global wmedian trainfit', c.get('W_global_trainfit', np.nan)), ('hourly wmedian trainfit', c.get('W_hourly_trainfit', np.nan))]:
        if np.isnan(wv): continue
        dec.append(dict(model=name, variant=variant, W=wv, vs_L2_mean_pct=100 * (wv / l2_mine.mean() - 1), vs_L2_best_seed_pct=100 * (wv / l2_mine.min() - 1),
                        vs_E0_pool_pct=100 * (wv / W(GF['E0_pool']) - 1)))
dec = pd.DataFrame(dec); dec.to_csv(PFX + 'decisive.csv', index=False)
log('\nL2 verify seeds W_ref: ' + ', '.join('%.4e' % v for v in l2_mine) + '  mean %.4e' % l2_mine.mean())
log('\n' + dec.round(3).to_string())
log('worst case L1-family (+any calib) vs E0_pool: %.3f%%; vs L2 verify mean: %.3f%%' % (dec.vs_E0_pool_pct.max(), dec.vs_L2_mean_pct.max()))

# ------------------------------------------------------------------ 5. figure
fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
ordr = ['E0_pool', 'E1_l1', 'E1_l1w', 'E1_l1w_s2', 'E1_l1w_s3', 'E1_l2w']
o = res[res.model.isin(ordr)].drop_duplicates('model').set_index('model').reindex(ordr)
ax[0].bar(range(len(o)), o.W_ref_pct, color=['tab:blue' if ('l2' in m or m == 'E0_pool') else 'tab:orange' for m in o.index])
ax[0].set_xticks(range(len(o))); ax[0].set_xticklabels(o.index, rotation=30, ha='right'); ax[0].set_ylim(12.0, 13.0)
ax[0].set_ylabel('W_ref % (val year, ref groups)'); ax[0].set_title('Original runs (re-aggregated)')
v = res[res.source == 'verify']
for i, mdl in enumerate(['V_l2', 'V_l1', 'V_l1w']):
    s = v[v.model == mdl]
    ax[1].scatter([i] * len(s), s.W_ref_pct, s=60, color='tab:blue' if mdl == 'V_l2' else 'tab:orange')
    ax[1].hlines(s.W_ref_pct.mean(), i - 0.3, i + 0.3, color='k')
ax[1].set_xticks(range(3)); ax[1].set_xticklabels(['L2 (seeds 101/202/303)', 'L1 (101/202)', 'L1 w=SMP*k (101/202)']); ax[1].set_ylim(12.0, 13.0)
ax[1].set_title('Independent retrain, fresh seeds (bar = mean)'); ax[1].set_ylabel('W_ref %')
plt.tight_layout(); plt.savefig(PFX + 'fig_seeds.png', dpi=130); plt.close()

fig, ax = plt.subplots(figsize=(10, 4.5))
cc = cal[cal.model.str.startswith('V_')].set_index('model')
xs = np.arange(len(cc)); wd = 0.2
for j, (col, lab) in enumerate([('impr_pct_global_halfCV', 'global, half-CV'), ('impr_pct_hourly_halfCV', 'hourly, half-CV'),
                                ('impr_pct_global_trainfit', 'global, fit on train-year residuals'), ('impr_pct_hourly_trainfit', 'hourly, fit on train-year residuals')]):
    ax.bar(xs + (j - 1.5) * wd, cc[col], wd, label=lab)
ax.axhline(0, color='k', lw=0.8); ax.set_xticks(xs); ax.set_xticklabels(cc.index, rotation=30, ha='right')
ax.set_ylabel('W improvement from weighted-median calibration (%)'); ax.legend(fontsize=8); ax.set_title('Calibration effect by objective / seed (fresh retrains)')
plt.tight_layout(); plt.savefig(PFX + 'fig_calibration.png', dpi=130); plt.close()
log('DONE')
