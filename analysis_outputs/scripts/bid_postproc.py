# bid_postproc: post-processing experiments on validation-year group forecasts, official weighted penalty W.
import os, json, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
np.seterr(all='ignore'); pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
BASE = 'C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad/'
CACHE = BASE + 'cache/'; OUT = BASE + 'analysis/out/'; MV = BASE + 'analysis/mv_cache/'
SITES = 'C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset/sites.csv'
TZ = 'Asia/Seoul'
V0 = pd.Timestamp('2024-06-01 01:00', tz=TZ); V1 = pd.Timestamp('2025-06-01 00:00', tz=TZ); VM = pd.Timestamp('2024-12-01 00:00', tz=TZ)
T0 = pd.Timestamp('2025-06-01 01:00', tz=TZ); T1 = pd.Timestamp('2026-06-01 00:00', tz=TZ)
VARIANTS = ['E0_site', 'E0_pool', 'E1_l1w', 'E7_mix_site10']
BINS = [0, .02, .05, .1, .2, .3, .4, .5, .6, .7, 2.0]
BINLAB = ['0-2%', '2-5%', '5-10%', '10-20%', '20-30%', '30-40%', '40-50%', '50-60%', '60-70%', '70%+']
def log(*a): print(*a, flush=True)

# ---------------------------------------------------------------- data
sites = pd.read_csv(SITES)
gmap = sites.set_index('site_id').current_group.map({'A': 1, 'B': 2}); cmap = sites.set_index('site_id').capacity_kw
CAP = {1: float(sites.capacity_kw[sites.current_group == 'A'].sum()), 2: float(sites.capacity_kw[sites.current_group == 'B'].sum())}
smp = pd.read_parquet(CACHE + 'smp_all.parquet')
smp_val = smp[(smp.ts >= V0) & (smp.ts <= V1)].set_index('ts').sort_index(); assert len(smp_val) == 8760
smp_test = smp[(smp.ts >= T0) & (smp.ts <= T1)].set_index('ts').sort_index(); assert len(smp_test) == 8760

def build(name):
    d = pd.read_parquet(CACHE + f'val_pred_site_{name}.parquet')
    d['g'] = d.site_id.map(gmap).astype('int8'); d['cap'] = d.site_id.map(cmap).astype('float32')
    a = d.groupby(['ts', 'g'])[['y', 'pred', 'cap']].sum().unstack('g')
    a.columns = [{'y': 'y', 'pred': 'p', 'cap': 'c'}[c[0]] + str(c[1]) for c in a.columns]
    del d
    return a.reindex(smp_val.index).fillna(0.0).astype('float64')

def decorate(a):
    a = a.copy()
    a['smp'] = smp_val.smp.values; a['k'] = smp_val.k.values; a['w'] = a.smp * a.k
    a['hour'] = a.index.hour; a['month'] = a.index.month
    a['half'] = np.where(a.index <= VM, 1, 2)
    a['wk'] = ((a.index - V0).days // 7) % 2
    for g in (1, 2):
        c = a[f'c{g}'].where(a[f'c{g}'] > 0, 1.0)
        a[f'cf{g}'] = a[f'p{g}'] / c
        a[f'acf{g}'] = a[f'y{g}'] / c
        a[f'cfbin{g}'] = np.where(a[f'p{g}'] > 0, np.digitize(a[f'cf{g}'], BINS[1:-1]), -1)
    return a

D = {}
for v in VARIANTS:
    D[v] = decorate(build(v)); log('built', v, D[v].shape)
g4 = pd.read_parquet(MV + 'group_E4_blend50.parquet')
if g4.index.tz is None: g4.index = g4.index.tz_localize('UTC').tz_convert(TZ)
g4 = g4.reindex(smp_val.index)
b = D['E7_mix_site10'].copy()
log('E4_blend50 y consistency: max|y_A-y1|=%.3f max|y_B-y2|=%.3f' % (np.abs(g4.y_A.values - b.y1.values).max(), np.abs(g4.y_B.values - b.y2.values).max()))
b['p1'] = g4.p_A.values; b['p2'] = g4.p_B.values
D['E4_blend50'] = decorate(b[['y1', 'y2', 'p1', 'p2', 'c1', 'c2']])
ALLV = VARIANTS + ['E4_blend50']
for v in ALLV: D[v][['y1', 'y2', 'p1', 'p2', 'c1', 'c2', 'smp', 'k', 'w']].to_csv(OUT + f'pp_group_{v}.csv', float_format='%.3f')
x = D['E7_mix_site10']
log('hours with no observed site in G1: %d, G2: %d; cap_obs G1 median %.0f (ref %.1f), G2 median %.0f (ref %.1f)' % ((x.c1 == 0).sum(), (x.c2 == 0).sum(), x.c1.median(), CAP[1], x.c2.median(), CAP[2]))

# ---------------------------------------------------------------- helpers
def W_of(df, p1, p2):
    return float((df.w * np.abs(p1 - df.y1)).sum()), float((df.w * np.abs(p2 - df.y2)).sum())

def wmedian(x, wt):
    x = np.asarray(x, float); wt = np.asarray(wt, float); m = (wt > 0) & np.isfinite(x); x = x[m]; wt = wt[m]
    if x.size == 0: return np.nan
    o = np.argsort(x); x = x[o]; c = np.cumsum(wt[o])
    return float(x[min(np.searchsorted(c, 0.5 * c[-1]), x.size - 1)])

def wquant(x, wt, qs):
    x = np.asarray(x, float); wt = np.asarray(wt, float); m = (wt > 0) & np.isfinite(x); x = x[m]; wt = wt[m]
    if x.size == 0: return [np.nan] * len(qs)
    o = np.argsort(x); x = x[o]; c = np.cumsum(wt[o]); c = c / c[-1]
    return [float(x[min(np.searchsorted(c, q), x.size - 1)]) for q in qs]

def fit_factor(y, p, w, how='l1', minn=20):
    m = (p > 0) & (w > 0)
    if m.sum() < minn: return np.nan
    y = y[m]; p = p[m]; w = w[m]
    if how == 'l1': return wmedian(y / p, w * p)          # argmin_a sum w|y-ap| = weighted median of y/p with weights w*p
    if how == 'mean': return float((w * y).sum() / (w * p).sum())   # weighted mean of ratio (weights w*p)
    if how == 'l2w': return float((w * p * y).sum() / (w * p * p).sum())
    if how == 'l2': return float((p * y).sum() / (p * p).sum())
    if how == 'l1u': return wmedian(y / p, p)             # unweighted-in-SMP L1
    raise ValueError(how)

def gk(keys, g): return [k.format(g=g) for k in keys]

def fit_cells(fit, keys, g, how='l1', minn=20):
    y = fit[f'y{g}'].values; p = fit[f'p{g}'].values; w = fit.w.values
    if not keys: return fit_factor(y, p, w, how, minn)
    out = {}
    for key, idx in fit.groupby(gk(keys, g)).indices.items():
        out[key] = fit_factor(y[idx], p[idx], w[idx], how, minn)
    return pd.Series(out, dtype=float)

def factor_array(test, fac, keys, g):
    if not keys: return np.full(len(test), fac, float)
    kk = gk(keys, g)
    idx = pd.MultiIndex.from_frame(test[kk]) if len(kk) > 1 else test[kk[0]].values
    return fac.reindex(idx).values.astype(float)

def exp_factor(df, split, keys, how='l1', shrink=1.0, fb_keys=None, minn=20, where=None):
    """fit multiplicative factors per cell on the other fold, apply to this fold (optionally only where(test,g) is True). returns per-fold + total W."""
    rows = []
    for fold in sorted(df[split].unique()):
        fit = df[df[split] != fold]; test = df[df[split] == fold]
        q = {}
        for g in (1, 2):
            a = factor_array(test, fit_cells(fit, keys, g, how, minn), keys, g)
            if fb_keys is not None: a = np.where(np.isnan(a), factor_array(test, fit_cells(fit, fb_keys, g, how, minn), fb_keys, g), a)
            a = np.where(np.isnan(a), 1.0, a); a = 1 + shrink * (a - 1)
            if where is not None: a = np.where(where(test, g), a, 1.0)
            q[g] = test[f'p{g}'].values * a
        b1, b2 = W_of(test, test.p1, test.p2); a1, a2 = W_of(test, q[1], q[2])
        rows.append(dict(fold=fold, W1_base=b1, W2_base=b2, W1=a1, W2=a2))
    return rows

RES = []
def rec(variant, split, exp, rows):
    for r in rows: RES.append(dict(variant=variant, split=split, exp=exp, **r))
    t = pd.DataFrame(rows)[['W1_base', 'W2_base', 'W1', 'W2']].sum()
    RES.append(dict(variant=variant, split=split, exp=exp, fold='all', **t.to_dict()))
    return 100 * (1 - (t.W1 + t.W2) / (t.W1_base + t.W2_base)), 100 * (1 - t.W1 / t.W1_base), 100 * (1 - t.W2 / t.W2_base)

# ---------------------------------------------------------------- 0. baseline table
base = []
for v in ALLV:
    x = D[v]; w1, w2 = W_of(x, x.p1, x.p2); Rw = float((x.w * (x.y1 + x.y2)).sum()); pool = float((x.w * np.abs(x.p1 + x.p2 - x.y1 - x.y2)).sum())
    h = {hh: W_of(x[x.half == hh], x[x.half == hh].p1, x[x.half == hh].p2) for hh in (1, 2)}
    base.append(dict(variant=v, W_G1=w1, W_G2=w2, W_ref=w1 + w2, W_ref_pct=100 * (w1 + w2) / Rw, W_pool=pool, W_pool_pct=100 * pool / Rw, Rw=Rw,
                     W_H1=sum(h[1]), W_H2=sum(h[2]), bias_G1=float((x.p1 - x.y1).mean()), bias_G2=float((x.p2 - x.y2).mean())))
base = pd.DataFrame(base); base.to_csv(OUT + 'pp_baseline.csv', index=False)
log('\n== baseline W (validation year, reference groups) ==\n', base.round(3).to_string())

# ---------------------------------------------------------------- 1. global factors
fac_rows = []
for v in ALLV:
    x = D[v]
    for hh in (1, 2):
        f = x[x.half == hh]
        for g in (1, 2):
            fac_rows.append(dict(variant=v, fit_half=hh, group=g, **{how: fit_cells(f, [], g, how) for how in ['l1', 'l1u', 'mean', 'l2w', 'l2']}))
    for how in ['l1', 'l1u', 'mean', 'l2w', 'l2']:
        rec(v, 'half', f'global_{how}', exp_factor(x, 'half', [], how))
        rec(v, 'wk', f'global_{how}', exp_factor(x, 'wk', [], how))
fac = pd.DataFrame(fac_rows); fac.to_csv(OUT + 'pp_global_factors.csv', index=False)
log('\n== global factors by fit half ==\n', fac.round(4).to_string())

# ---------------------------------------------------------------- 2. hour / month x hour factors
hf_rows = []
for v in ALLV:
    x = D[v]
    for hh in (1, 2):
        for g in (1, 2):
            s = fit_cells(x[x.half == hh], ['hour'], g, 'l1')
            for h, a in s.items(): hf_rows.append(dict(variant=v, fit_half=hh, group=g, hour=h, a_l1=a))
    rec(v, 'half', 'hour_l1', exp_factor(x, 'half', ['hour']))
    rec(v, 'half', 'hour_l1_shrink50', exp_factor(x, 'half', ['hour'], shrink=0.5))
    rec(v, 'half', 'hour_l2w', exp_factor(x, 'half', ['hour'], 'l2w'))
    rec(v, 'half', 'hour_mean', exp_factor(x, 'half', ['hour'], 'mean'))
    rec(v, 'half', 'month_x_hour_l1(fb hour)', exp_factor(x, 'half', ['month', 'hour'], fb_keys=['hour']))   # no month overlap -> == hour
    rec(v, 'wk', 'hour_l1', exp_factor(x, 'wk', ['hour']))
    rec(v, 'wk', 'hour_l1_shrink50', exp_factor(x, 'wk', ['hour'], shrink=0.5))
    rec(v, 'wk', 'month_l1', exp_factor(x, 'wk', ['month']))
    # wk split leaves ~15 rows per month x hour cell, so minn must be < 15 for the cell factor to be used at all
    rec(v, 'wk', 'month_x_hour_l1_minn20(=hour fb)', exp_factor(x, 'wk', ['month', 'hour'], fb_keys=['hour']))
    rec(v, 'wk', 'month_x_hour_l1_minn12(fb hour)', exp_factor(x, 'wk', ['month', 'hour'], fb_keys=['hour'], minn=12))
    rec(v, 'wk', 'month_x_hour_l1_minn8(fb hour)', exp_factor(x, 'wk', ['month', 'hour'], fb_keys=['hour'], minn=8))
    rec(v, 'wk', 'month_x_hour_l1_minn8_shrink50', exp_factor(x, 'wk', ['month', 'hour'], shrink=0.5, fb_keys=['hour'], minn=8))
    rec(v, 'wk', 'month_x_hour_l1_minn8_shrink25', exp_factor(x, 'wk', ['month', 'hour'], shrink=0.25, fb_keys=['hour'], minn=8))
    rec(v, 'wk', 'month_l1_shrink50', exp_factor(x, 'wk', ['month'], shrink=0.5))
hf = pd.DataFrame(hf_rows); hf.to_csv(OUT + 'pp_hour_factors.csv', index=False)
log('\n== hourly L1 factors (E7_mix_site10 / E4_blend50) ==')
for v in ['E7_mix_site10', 'E4_blend50']:
    t = hf[hf.variant == v].pivot_table(index='hour', columns=['group', 'fit_half'], values='a_l1'); log(v, '\n', t.round(3).to_string())

# ---------------------------------------------------------------- 3. conditional shrink to zero for low predicted CF
sh_rows = []
for v in ALLV:
    x = D[v]
    for th in [0.0, 0.005, 0.01, 0.02, 0.03, 0.05, 0.08]:
        for hh in (1, 2, 0):
            t = x if hh == 0 else x[x.half == hh]
            q = {g: np.where(t[f'p{g}'] < th * t[f'c{g}'], 0.0, t[f'p{g}']) for g in (1, 2)}
            b1, b2 = W_of(t, t.p1, t.p2); a1, a2 = W_of(t, q[1], q[2])
            n_aff = int(((t.p1 > 0) & (t.p1 < th * t.c1)).sum() + ((t.p2 > 0) & (t.p2 < th * t.c2)).sum())
            sh_rows.append(dict(variant=v, theta=th, half=hh, n_group_hours_zeroed=n_aff, W_base=b1 + b2, W=a1 + a2, gain_pct=100 * (1 - (a1 + a2) / (b1 + b2)),
                                gain_G1_pct=100 * (1 - a1 / b1), gain_G2_pct=100 * (1 - a2 / b2)))
sh = pd.DataFrame(sh_rows); sh.to_csv(OUT + 'pp_shrink_zero.csv', index=False)
log('\n== conditional zeroing (pred < theta*cap_obs), full year (half=0) ==\n', sh[sh.half == 0].round(3).to_string())
# conditional median in the lowest bins (what does the data say the right factor is?)
lowb = []
for v in ALLV:
    x = D[v]
    for g in (1, 2):
        for bin_ in (0, 1, 2):
            m = x[f'cfbin{g}'] == bin_; y = x.loc[m, f'y{g}'].values; p = x.loc[m, f'p{g}'].values; w = x.loc[m, 'w'].values
            lowb.append(dict(variant=v, group=g, cfbin=BINLAB[bin_], n=int(m.sum()), med_ratio=wmedian(y / p, w * p), mean_ratio=float((w * y).sum() / (w * p).sum()),
                             share_zero_actual=float((y <= 0).mean()), W_share_pct=100 * float((w * np.abs(p - y)).sum()) / float((x.w * np.abs(x[f'p{g}'] - x[f'y{g}'])).sum())))
lowb = pd.DataFrame(lowb); lowb.to_csv(OUT + 'pp_lowbin_ratio.csv', index=False)
log('\n== low predicted-CF bins: conditional ratio ==\n', lowb.round(3).to_string())

# ---------------------------------------------------------------- 4. zero-SMP hours and k=1 vs k=3
def smp_summary(s, label):
    s = s.copy(); s['w'] = s.smp * s.k; s['hour'] = s.index.hour; s['month'] = s.index.month
    day = s[(s.hour >= 6) & (s.hour <= 20)]
    return dict(period=label, n_zero_smp=int((s.smp == 0).sum()), n_zero_smp_daytime6_20=int((day.smp == 0).sum()), n_smp_le10=int((s.smp <= 10).sum()),
                n_smp_le10_daytime=int((day.smp <= 10).sum()), n_smp_le50_daytime=int((day.smp <= 50).sum()),
                mean_smp=float(s.smp.mean()), mean_smp_k3=float(s.smp[s.k == 3].mean()), mean_smp_k1_day=float(day.smp[day.k == 1].mean()),
                share_w_k3_daytime_pct=100 * float(day.w[day.k == 3].sum() / day.w.sum()),
                zero_smp_by_month=json.dumps({int(m): int(c) for m, c in s[s.smp == 0].groupby('month').size().items()}),
                zero_smp_by_hour=json.dumps({int(h): int(c) for h, c in s[s.smp == 0].groupby('hour').size().items()}))
zs = pd.DataFrame([smp_summary(smp_val, 'val 2024-06..2025-05'), smp_summary(smp_test, 'test 2025-06..2026-05')])
zs.to_csv(OUT + 'pp_zero_smp.csv', index=False)
log('\n== zero / low SMP hours ==\n', zs.T.to_string())
# W contribution by k and in zero/low-SMP hours (baseline E7)
kc = []
for v in ALLV:
    x = D[v]; e = x.w * (np.abs(x.p1 - x.y1) + np.abs(x.p2 - x.y2)); ue = np.abs(x.p1 - x.y1) + np.abs(x.p2 - x.y2)
    kc.append(dict(variant=v, W_share_k3_pct=100 * float(e[x.k == 3].sum() / e.sum()), unweighted_abs_err_share_k3_pct=100 * float(ue[x.k == 3].sum() / ue.sum()),
                   unweighted_abs_err_share_smp0_pct=100 * float(ue[x.smp == 0].sum() / ue.sum()), unweighted_abs_err_share_smp_le50_pct=100 * float(ue[x.smp <= 50].sum() / ue.sum()),
                   hours_k3_share_pct=100 * 5 / 24))
kc = pd.DataFrame(kc); kc.to_csv(OUT + 'pp_k_share.csv', index=False); log('\n== W share by k ==\n', kc.round(2).to_string())
kf = []
for v in ALLV:
    x = D[v]
    for hh in (1, 2):
        f = x[x.half == hh]
        for g in (1, 2):
            s = fit_cells(f, ['k'], g, 'l1'); su = fit_cells(f, ['k'], g, 'l1u')
            kf.append(dict(variant=v, fit_half=hh, group=g, a_k1=s.get(1, np.nan), a_k3=s.get(3, np.nan), a_all=fit_cells(f, [], g, 'l1'), a_k1_unwSMP=su.get(1, np.nan), a_k3_unwSMP=su.get(3, np.nan),
                           a_k1_hours9_10_16_17=fit_factor(f[f.hour.isin([9, 10, 16, 17])][f'y{g}'].values, f[f.hour.isin([9, 10, 16, 17])][f'p{g}'].values, f[f.hour.isin([9, 10, 16, 17])].w.values)))
    rec(v, 'half', 'k_l1', exp_factor(x, 'half', ['k']))
    rec(v, 'wk', 'k_l1', exp_factor(x, 'wk', ['k']))
    rec(v, 'half', 'k_x_hour_l1(fb hour)', exp_factor(x, 'half', ['k', 'hour'], fb_keys=['hour']))
kf = pd.DataFrame(kf); kf.to_csv(OUT + 'pp_k_factors.csv', index=False); log('\n== factors by k ==\n', kf.round(4).to_string())

# ---------------------------------------------------------------- 5. quantile view by predicted-CF bin
qb = []
for v in ALLV:
    x = D[v]
    for g in (1, 2):
        Wg = float((x.w * np.abs(x[f'p{g}'] - x[f'y{g}'])).sum())
        for bin_ in range(10):
            m = x[f'cfbin{g}'] == bin_
            if m.sum() == 0: continue
            y = x.loc[m, f'y{g}'].values; p = x.loc[m, f'p{g}'].values; w = x.loc[m, 'w'].values; r = y / p; wt = w * p
            q10, q25, q50, q75, q90 = wquant(r, wt, [.1, .25, .5, .75, .9])
            qb.append(dict(variant=v, group=g, cfbin=BINLAB[bin_], n=int(m.sum()), mean_ratio=float((w * y).sum() / (w * p).sum()), med_ratio=q50, q10=q10, q25=q25, q75=q75, q90=q90,
                           W_share_pct=100 * float((w * np.abs(p - y)).sum()) / Wg, bias_kwh=float((p - y).mean()),
                           W_in_median=float((w * np.abs(q50 * p - y)).sum()), W_in_mean=float((w * np.abs(((w * y).sum() / (w * p).sum()) * p - y)).sum()), W_in_none=float((w * np.abs(p - y)).sum())))
qb = pd.DataFrame(qb); qb.to_csv(OUT + 'pp_ratio_bins.csv', index=False)
log('\n== ratio distribution by predicted-CF bin (E7_mix_site10) ==\n', qb[qb.variant == 'E7_mix_site10'].round(3).to_string())
ins = qb.groupby('variant')[['W_in_none', 'W_in_mean', 'W_in_median']].sum()
ins['gain_mean_pct'] = 100 * (1 - ins.W_in_mean / ins.W_in_none); ins['gain_median_pct'] = 100 * (1 - ins.W_in_median / ins.W_in_none)
ins.to_csv(OUT + 'pp_ratio_bins_insample.csv'); log('\n== in-sample (full year) per-bin correction: mean vs median ==\n', ins.round(3).to_string())
for v in ALLV:
    x = D[v]
    for sp in ('half', 'wk'):
        rec(v, sp, 'cfbin_median', exp_factor(x, sp, ['cfbin{g}']))
        rec(v, sp, 'cfbin_mean', exp_factor(x, sp, ['cfbin{g}'], 'mean'))
        rec(v, sp, 'cfbin_l2w', exp_factor(x, sp, ['cfbin{g}'], 'l2w'))
        rec(v, sp, 'cfbin_median_shrink50', exp_factor(x, sp, ['cfbin{g}'], shrink=0.5))
        rec(v, sp, 'cfbin_median_lowbins_only(CF<10%)', exp_factor(x, sp, ['cfbin{g}'], where=lambda t, g: t[f'cfbin{g}'].values < 3))
        rec(v, sp, 'cfbin_median_lowbins_only(CF<5%)', exp_factor(x, sp, ['cfbin{g}'], where=lambda t, g: t[f'cfbin{g}'].values < 2))
        rec(v, sp, 'cfbin_x_k_median(fb cfbin)', exp_factor(x, sp, ['cfbin{g}', 'k'], fb_keys=['cfbin{g}']))
    rec(v, 'wk', 'cfbin_x_month_median(fb cfbin)', exp_factor(x, 'wk', ['cfbin{g}', 'month'], fb_keys=['cfbin{g}']))

# ---------------------------------------------------------------- 6. blends
bl = []
pairs = [('E1_l1w', 'E7_mix_site10'), ('E0_pool', 'E1_l1w'), ('E0_site', 'E7_mix_site10'), ('E7_mix_site10', 'E4_blend50'), ('E0_pool', 'E7_mix_site10'), ('E0_site', 'E1_l1w')]
for a, bname in pairs:
    xa, xb = D[a], D[bname]
    def Wmix(m, lam): return sum(W_of(xa[m], lam * xa.p1[m] + (1 - lam) * xb.p1[m], lam * xa.p2[m] + (1 - lam) * xb.p2[m]))
    allm = np.ones(len(xa), bool)
    grid = np.round(np.arange(0, 1.01, 0.1), 2); Wg = [Wmix(allm, l) for l in grid]
    lam_star = float(grid[int(np.argmin(Wg))])
    cv = 0.0; cvb = 0.0; lams = []
    for fold in (1, 2):
        mf = (xa.half != fold).values; mt = (xa.half == fold).values
        l = float(grid[int(np.argmin([Wmix(mf, l) for l in grid]))]); lams.append(l); cv += Wmix(mt, l); cvb += Wmix(mt, 0.5)
    bl.append(dict(A=a, B=bname, W_A=Wmix(allm, 1), W_B=Wmix(allm, 0), W_avg=Wmix(allm, 0.5), gain_avg_vs_best_pct=100 * (1 - Wmix(allm, 0.5) / min(Wmix(allm, 1), Wmix(allm, 0))),
                   lam_star_insample=lam_star, W_lam_star=min(Wg), lam_fold1=lams[0], lam_fold2=lams[1], W_cv_lam=cv, W_cv_avg=cvb, gain_cvlam_vs_avg_pct=100 * (1 - cv / cvb)))
bl = pd.DataFrame(bl); bl.to_csv(OUT + 'pp_blend.csv', index=False); log('\n== blends ==\n', bl.round(3).to_string())

# ---------------------------------------------------------------- 7. fat tails and caps
tail = []; tail_month = []; lorenz = {}
for v in ALLV:
    x = D[v]; c = (x.w * (np.abs(x.p1 - x.y1) + np.abs(x.p2 - x.y2))).values; o = np.argsort(-c); cs = np.cumsum(c[o]) / c.sum(); lorenz[v] = cs
    n = len(c); top = {q: float(cs[int(q * n) - 1]) for q in (0.01, 0.05, 0.10, 0.20)}
    idx5 = x.index[o[:int(0.05 * n)]]; t5 = x.loc[idx5]; e5 = (t5.p1 + t5.p2 - t5.y1 - t5.y2)
    tail.append(dict(variant=v, W=float(c.sum()), top1_pct=100 * top[0.01], top5_pct=100 * top[0.05], top10_pct=100 * top[0.10], top20_pct=100 * top[0.20],
                     n_hours_for_50pct_W=int(np.searchsorted(cs, 0.5) + 1), top5_over_forecast_share_pct=100 * float((e5 > 0).mean()), top5_k3_share_pct=100 * float((t5.k == 3).mean()),
                     top5_mean_smp=float(t5.smp.mean()), all_day_mean_smp=float(x.smp[(x.hour >= 9) & (x.hour <= 17)].mean()),
                     top5_mean_pred_cf_total=float(((t5.p1 + t5.p2) / (t5.c1 + t5.c2)).mean()), top5_mean_actual_cf_total=float(((t5.y1 + t5.y2) / (t5.c1 + t5.c2)).mean()),
                     top5_W_over_share_pct=100 * float(c[o[:int(0.05 * n)]][(e5 > 0).values].sum() / c[o[:int(0.05 * n)]].sum())))
    for m, grp in t5.groupby('month'):
        e = grp.p1 + grp.p2 - grp.y1 - grp.y2
        tail_month.append(dict(variant=v, month=m, n_top5_hours=len(grp), n_over=int((e > 0).sum()), n_under=int((e < 0).sum()), W_share_of_total_pct=100 * float((grp.w * (np.abs(grp.p1 - grp.y1) + np.abs(grp.p2 - grp.y2))).sum() / c.sum())))
tail = pd.DataFrame(tail); tail.to_csv(OUT + 'pp_tail_share.csv', index=False); log('\n== tails ==\n', tail.round(2).to_string())
tail_month = pd.DataFrame(tail_month); tail_month.to_csv(OUT + 'pp_tail_top5_by_month.csv', index=False)
log('\n== top-5% hours by month (E7_mix_site10) ==\n', tail_month[tail_month.variant == 'E7_mix_site10'].round(2).to_string())
# actual CF extremes (how high does the group ever go?)
ext = []
for g in (1, 2):
    x = D['E7_mix_site10']; a = x[f'acf{g}'][x[f'c{g}'] > 0]; p = x[f'cf{g}'][x[f'c{g}'] > 0]
    ext.append(dict(group=g, actual_cf_max=float(a.max()), actual_cf_q999=float(a.quantile(.999)), actual_cf_q99=float(a.quantile(.99)), n_hours_actual_cf_gt_0_85=int((a > .85).sum()), n_hours_actual_cf_gt_0_80=int((a > .80).sum()), n_hours_actual_cf_gt_0_75=int((a > .75).sum()),
                    pred_cf_max_E7=float(p.max()), n_hours_pred_cf_gt_0_85_E7=int((p > .85).sum()), n_hours_pred_cf_gt_0_80_E7=int((p > .80).sum()), n_hours_pred_cf_gt_0_75_E7=int((p > .75).sum()),
                    pred_cf_max_E0site=float(D['E0_site'][f'cf{g}'].max()), n_hours_pred_cf_gt_0_85_E0site=int((D['E0_site'][f'cf{g}'] > .85).sum())))
ext = pd.DataFrame(ext); ext.to_csv(OUT + 'pp_cf_extremes.csv', index=False); log('\n== CF extremes ==\n', ext.round(3).to_string())
cap_rows = []
for v in ALLV:
    x = D[v]
    for cc in [0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95]:
        for hh in (1, 2, 0):
            t = x if hh == 0 else x[x.half == hh]
            q = {g: np.minimum(t[f'p{g}'].values, cc * t[f'c{g}'].values) for g in (1, 2)}
            b1, b2 = W_of(t, t.p1, t.p2); a1, a2 = W_of(t, q[1], q[2])
            cap_rows.append(dict(variant=v, cap=cc, half=hh, n_group_hours_capped=int((t.p1 > cc * t.c1).sum() + (t.p2 > cc * t.c2).sum()), W_base=b1 + b2, W=a1 + a2, gain_pct=100 * (1 - (a1 + a2) / (b1 + b2))))
cap = pd.DataFrame(cap_rows); cap.to_csv(OUT + 'pp_cap.csv', index=False)
log('\n== fixed cap on group forecast (full year) ==\n', cap[cap.half == 0].round(3).to_string())
# empirical cap: per hour-of-day quantile of ACTUAL group CF from the other fold (wk split)
qc_rows = []
for v in ALLV:
    x = D[v]
    for qq in [0.98, 0.99, 0.995, 1.0]:
        tot_b = tot_a = 0.0; naff = 0
        for fold in (0, 1):
            fit = x[x.wk != fold]; test = x[x.wk == fold]
            q = {}
            for g in (1, 2):
                ch = fit[fit[f'c{g}'] > 0].groupby('hour')[f'acf{g}'].quantile(qq)
                lim = ch.reindex(test.hour.values).fillna(0).values * test[f'c{g}'].values
                q[g] = np.minimum(test[f'p{g}'].values, lim); naff += int((test[f'p{g}'].values > lim).sum())
            tot_b += sum(W_of(test, test.p1, test.p2)); tot_a += sum(W_of(test, q[1], q[2]))
        qc_rows.append(dict(variant=v, actual_cf_quantile_by_hour=qq, n_group_hours_capped=naff, W_base=tot_b, W=tot_a, gain_pct=100 * (1 - tot_a / tot_b)))
qc = pd.DataFrame(qc_rows); qc.to_csv(OUT + 'pp_cap_quantile_hour.csv', index=False); log('\n== empirical hour-of-day quantile cap (wk split) ==\n', qc.round(3).to_string())

# ---------------------------------------------------------------- results table
R = pd.DataFrame(RES); R['W_base'] = R.W1_base + R.W2_base; R['W'] = R.W1 + R.W2
R['gain_pct'] = 100 * (1 - R.W / R.W_base); R['gain_G1_pct'] = 100 * (1 - R.W1 / R.W1_base); R['gain_G2_pct'] = 100 * (1 - R.W2 / R.W2_base)
R.to_csv(OUT + 'pp_experiments.csv', index=False)
S = R[R.fold == 'all'].pivot_table(index=['split', 'exp'], columns='variant', values='gain_pct')[ALLV]
S.to_csv(OUT + 'pp_experiments_summary.csv'); log('\n== out-of-fold gain % vs no post-processing (sum of both test folds) ==\n', S.round(2).to_string())
Sg = R[R.fold == 'all'].pivot_table(index=['split', 'exp'], columns='variant', values=['gain_G1_pct', 'gain_G2_pct'])
Sg.to_csv(OUT + 'pp_experiments_summary_bygroup.csv'); log('\n== per group gains (E7_mix_site10, E4_blend50, E0_site) ==\n', Sg.xs('E7_mix_site10', axis=1, level=1).round(2).to_string(), '\n', Sg.xs('E4_blend50', axis=1, level=1).round(2).to_string(), '\n', Sg.xs('E0_site', axis=1, level=1).round(2).to_string())
Rf = R[(R.fold != 'all') & R.exp.isin(['global_l1', 'global_l2w', 'hour_l1', 'cfbin_median', 'k_l1'])].copy()
log('\n== per-fold detail (half split) for key experiments ==\n', Rf[Rf.split == 'half'][['variant', 'exp', 'fold', 'W_base', 'W', 'gain_pct', 'gain_G1_pct', 'gain_G2_pct']].round(2).to_string())

# ---------------------------------------------------------------- figures
fig, ax = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
for gi, g in enumerate((1, 2)):
    for v, col in zip(['E0_site', 'E7_mix_site10', 'E4_blend50'], ['tab:gray', 'tab:blue', 'tab:red']):
        for hh, ls in ((1, '-'), (2, '--')):
            t = hf[(hf.variant == v) & (hf.group == g) & (hf.fit_half == hh)].set_index('hour').a_l1
            ax[gi].plot(t.index, t.values, ls, color=col, marker='o', ms=3, label=f'{v} fit H{hh}')
    ax[gi].axhline(1, color='k', lw=.8); ax[gi].set_title(f'G{g}: hourly L1 factor (weighted median of y/pred)'); ax[gi].set_xlabel('hour (KST, right-closed)'); ax[gi].set_xlim(5, 20); ax[gi].grid(alpha=.3)
ax[0].set_ylabel('factor a'); ax[0].legend(fontsize=7); plt.tight_layout(); plt.savefig(OUT + 'fig_pp_hour_factors.png', dpi=130); plt.close()

fig, ax = plt.subplots(2, 2, figsize=(12, 8))
for gi, g in enumerate((1, 2)):
    for v, col in zip(['E7_mix_site10', 'E4_blend50'], ['tab:blue', 'tab:red']):
        t = qb[(qb.variant == v) & (qb.group == g)]; xs = np.arange(len(t))
        ax[0, gi].plot(xs, t.med_ratio, '-o', color=col, label=f'{v} weighted median'); ax[0, gi].plot(xs, t.mean_ratio, '--s', color=col, alpha=.7, label=f'{v} weighted mean')
        ax[0, gi].fill_between(xs, t.q25, t.q75, color=col, alpha=.12)
        ax[1, gi].bar(xs + (0.2 if v == 'E4_blend50' else -0.2), t.W_share_pct, width=.4, color=col, label=v)
    ax[0, gi].axhline(1, color='k', lw=.8); ax[0, gi].set_xticks(range(10)); ax[0, gi].set_xticklabels(BINLAB, rotation=45); ax[0, gi].set_title(f'G{g}: y/pred ratio by predicted-CF bin (band = weighted IQR)'); ax[0, gi].grid(alpha=.3); ax[0, gi].legend(fontsize=7)
    ax[1, gi].set_xticks(range(10)); ax[1, gi].set_xticklabels(BINLAB, rotation=45); ax[1, gi].set_title(f'G{g}: share of W by predicted-CF bin (%)'); ax[1, gi].grid(alpha=.3); ax[1, gi].legend(fontsize=7)
plt.tight_layout(); plt.savefig(OUT + 'fig_pp_ratio_bins.png', dpi=130); plt.close()

fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
for v in ALLV: ax[0].plot(np.arange(1, 8761) / 87.6, lorenz[v], label=v)
ax[0].axvline(5, color='k', lw=.8, ls=':'); ax[0].set_xlabel('% of hours (sorted by contribution, desc)'); ax[0].set_ylabel('cumulative share of W'); ax[0].set_xlim(0, 30); ax[0].grid(alpha=.3); ax[0].legend(fontsize=8); ax[0].set_title('Concentration of W in worst hours')
tm = tail_month[tail_month.variant == 'E7_mix_site10'].set_index('month').reindex(range(1, 13)).fillna(0)
ax[1].bar(tm.index, tm.n_over, color='tab:red', label='over-forecast (e>0)'); ax[1].bar(tm.index, tm.n_under, bottom=tm.n_over, color='tab:blue', label='under-forecast'); ax[1].set_xticks(range(1, 13)); ax[1].set_title('E7_mix_site10: top-5% worst hours by month'); ax[1].legend(); ax[1].grid(alpha=.3)
plt.tight_layout(); plt.savefig(OUT + 'fig_pp_tail.png', dpi=130); plt.close()

fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
for v in ALLV:
    t = sh[(sh.variant == v) & (sh.half == 0)]; ax[0].plot(t.theta * 100, t.gain_pct, '-o', label=v)
    t = cap[(cap.variant == v) & (cap.half == 0)]; ax[1].plot(t.cap, t.gain_pct, '-o', label=v)
ax[0].axhline(0, color='k', lw=.8); ax[0].set_xlabel('theta: zero forecast when pred < theta % of observed capacity'); ax[0].set_ylabel('W gain % (full year)'); ax[0].set_title('Conditional zeroing'); ax[0].grid(alpha=.3); ax[0].legend(fontsize=7)
ax[1].axhline(0, color='k', lw=.8); ax[1].set_xlabel('cap c: forecast <= c x observed capacity'); ax[1].set_title('Fixed cap'); ax[1].grid(alpha=.3); ax[1].legend(fontsize=7)
plt.tight_layout(); plt.savefig(OUT + 'fig_pp_cap_shrink.png', dpi=130); plt.close()
log('\nDONE. figures: fig_pp_hour_factors.png fig_pp_ratio_bins.png fig_pp_tail.png fig_pp_cap_shrink.png')
