"""Adversarial verification (math/logic): does L1 / SMP*k-weighted L1 training + weighted-median calibration lower W vs the L2 baseline?
Stages: A = recompute calibration effect from group series (cheap) | B <names> = retrain pooled LGBM fits (cached per fit) | C = summarize + bootstrap + figure."""
import sys, os, time, json, gc, glob
import numpy as np, pandas as pd
np.seterr(all='ignore'); pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
BASE = 'C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad/'
CACHE, OUT, MV = BASE + 'cache/', BASE + 'analysis/out/', BASE + 'analysis/mv_cache/'
TZ = 'Asia/Seoul'
T1 = pd.Timestamp('2024-06-01 00:00', tz=TZ); TH = pd.Timestamp('2024-12-01 00:00', tz=TZ)
A6 = ['wa_cloud', 'wa_temp', 'wa_humidity', 'wa_ground_press', 'wa_wind_speed', 'wa_rain']
B9 = ['wb_cloud', 'wb_uv_idx', 'wb_temp', 'wb_rel_hum', 'wb_dew_point', 'wb_vis', 'wb_ceiling', 'wb_precip_prob', 'wb_total_liq']
BASEF = A6 + B9 + ['elev', 'azim', 'cosz', 'doy_sin', 'doy_cos', 'hour', 'capacity_kw', 'lat', 'lon']
LGB = dict(n_estimators=400, learning_rate=0.06, num_leaves=127, min_child_samples=200, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1, n_jobs=8)
PFX = OUT + 'verify_l1_calib_'
def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)

def wmedian(x, wt):
    x = np.asarray(x, float); wt = np.asarray(wt, float); m = (wt > 0) & np.isfinite(x); x, wt = x[m], wt[m]
    o = np.argsort(x); x = x[o]; c = np.cumsum(wt[o]); return float(x[min(np.searchsorted(c, 0.5 * c[-1]), x.size - 1)])
def fit_l1(y, p, w):  # argmin_a sum w|y - a p| = (w*p)-weighted median of y/p
    m = (p > 0) & (w > 0); return wmedian(y[m] / p[m], w[m] * p[m])
def Wsum(d, p1, p2): return float((d.w * (np.abs(p1 - d.y1) + np.abs(p2 - d.y2))).sum())

def std_group(g):
    g = g.copy()
    if g.ts.dt.tz is None: g['ts'] = g.ts.dt.tz_localize('UTC').dt.tz_convert(TZ)  # .values on tz-aware ts stores naive UTC
    g['half'] = np.where(g.ts <= TH, 1, 2); g['hour'] = g.ts.dt.hour; return g

def load_mv_group(name):
    g = pd.read_parquet(MV + f'group_{name}.parquet')
    if g.index.tz is None: g.index = g.index.tz_localize('UTC').tz_convert(TZ)
    g = g.sort_index(); return std_group(pd.DataFrame({'ts': g.index, 'y1': g.y_A.values, 'y2': g.y_B.values, 'p1': g.p_A.values, 'p2': g.p_B.values, 'w': g.w.values}))

def calib_table(g):
    base = Wsum(g, g.p1, g.p2); Rw = float((g.w * (g.y1 + g.y2)).sum())
    a1 = fit_l1(g.y1.values, g.p1.values, g.w.values); a2 = fit_l1(g.y2.values, g.p2.values, g.w.values)
    Win = Wsum(g, a1 * g.p1, a2 * g.p2)
    Wcv = 0.0; Whcv = 0.0; fac = {}
    for f in (1, 2):
        fit = g[g.half != f]; te = g[g.half == f]
        b1 = fit_l1(fit.y1.values, fit.p1.values, fit.w.values); b2 = fit_l1(fit.y2.values, fit.p2.values, fit.w.values); fac[f] = (b1, b2)
        Wcv += Wsum(te, b1 * te.p1, b2 * te.p2)
        q = {}
        for gi, (yc, pc) in enumerate([('y1', 'p1'), ('y2', 'p2')], 1):
            hf = {}
            for h, d in fit.groupby('hour'):
                m = d[pc].values > 1
                hf[h] = fit_l1(d[yc].values[m], d[pc].values[m], d.w.values[m]) if m.sum() > 20 else 1.0
            q[gi] = te[pc].values * te.hour.map(hf).fillna(1.0).values
        Whcv += Wsum(te, q[1], q[2])
    h2 = g[g.half == 2]; We5 = Wsum(h2, fac[2][0] * h2.p1, fac[2][1] * h2.p2); We5b = Wsum(h2, h2.p1, h2.p2)
    return dict(W_none=base, W_pct=100 * base / Rw, a1_full=a1, a2_full=a2, W_global_insample=Win, gain_insample_pct=100 * (1 - Win / base),
                a1_fitH1=fac[2][0], a2_fitH1=fac[2][1], a1_fitH2=fac[1][0], a2_fitH2=fac[1][1],
                W_global_halfCV=Wcv, gain_global_halfCV_pct=100 * (1 - Wcv / base), W_hour_halfCV=Whcv, gain_hour_halfCV_pct=100 * (1 - Whcv / base),
                W_H2_none=We5b, W_H2_global_fitH1=We5, gain_E5style_pct=100 * (1 - We5 / We5b))

stage = sys.argv[1]
if stage == 'A':
    rows = []
    for v in ['E0_site', 'E0_pool', 'E1_l1', 'E1_l2w', 'E1_l1w', 'E1_l1w_s2', 'E1_l1w_s3', 'E7_mix_site10', 'E4_blend50']:
        g = load_mv_group(v)
        if v in ('E0_pool', 'E1_l1w', 'E7_mix_site10', 'E4_blend50', 'E0_site'):
            c = pd.read_csv(OUT + f'pp_group_{v}.csv'); c['ts'] = pd.to_datetime(c.ts, utc=True).dt.tz_convert(TZ); c = c.sort_values('ts')
            dW = abs(Wsum(c, c.p1, c.p2) - Wsum(g, g.p1, g.p2)); log(v, 'csv-vs-parquet |dW| =', round(dW))
        r = calib_table(g); r['variant'] = v; rows.append(r); log(v, {k: (round(x, 4) if isinstance(x, float) else x) for k, x in r.items()})
    A = pd.DataFrame(rows).set_index('variant'); A.to_csv(PFX + 'A_calibration.csv')
    L2 = A.loc['E0_pool', 'W_none']
    out = []
    for v in ['E1_l1', 'E1_l1w', 'E1_l1w_s2', 'E1_l1w_s3', 'E7_mix_site10', 'E4_blend50']:
        out.append(dict(variant=v, W_L2pool_nocal=L2, W_v_nocal=A.loc[v, 'W_none'], W_v_cal_halfCV=A.loc[v, 'W_global_halfCV'], W_v_cal_hourCV=A.loc[v, 'W_hour_halfCV'],
                        W_L2pool_cal_halfCV=A.loc['E0_pool', 'W_global_halfCV'],
                        gain_v_nocal_vs_L2_pct=100 * (1 - A.loc[v, 'W_none'] / L2), gain_v_cal_vs_L2_pct=100 * (1 - A.loc[v, 'W_global_halfCV'] / L2),
                        gain_v_cal_vs_L2cal_pct=100 * (1 - A.loc[v, 'W_global_halfCV'] / A.loc['E0_pool', 'W_global_halfCV']),
                        contribution_of_calibration_pct=100 * (1 - A.loc[v, 'W_global_halfCV'] / A.loc[v, 'W_none'])))
    O = pd.DataFrame(out).set_index('variant'); O.to_csv(PFX + 'A_vs_L2.csv'); log('\n' + O.round(3).to_string())

elif stage == 'B':
    import lightgbm as lgb, psutil
    names = [n for n in sys.argv[2:] if not os.path.exists(PFX + f'grp_{n}.parquet')]
    if not names: log('all cached'); sys.exit()
    cols = list(dict.fromkeys(['ts', 'current_group', 'energy', 'capacity_kw', 'w', 'cf'] + BASEF))
    df = pd.read_parquet(MV + 'day.parquet', columns=cols)
    for c in BASEF + ['w', 'cf', 'energy', 'capacity_kw']: df[c] = df[c].astype('float32')
    df['current_group'] = df.current_group.astype('category')
    tr = df[df.ts <= T1]; va = df[df.ts > T1].reset_index(drop=True); del df; gc.collect()
    night = pd.read_parquet(MV + 'night.parquet', columns=['ts', 'energy', 'current_group', 'w']); night = night[night.ts > T1]
    log('train', tr.shape, 'val', va.shape, 'night', night.shape, 'rss %.2fGB' % (psutil.Process().memory_info().rss / 1e9))
    assert tr.cf.between(0, 1.2).all() and tr[BASEF].shape[1] == 24
    wtr = (tr.w / tr.w.mean()).astype('float32').values
    Xt = tr[BASEF]; Xv = va[BASEF]
    for n in names:
        obj, seed = n.split('_s'); seed = int(seed)
        params = dict(LGB, objective='regression' if obj == 'l2' else 'regression_l1', random_state=seed)
        t = time.time()
        m = lgb.LGBMRegressor(**params).fit(Xt, tr.cf, sample_weight=wtr if obj.endswith('w') else None)
        p = np.clip(m.predict(Xv), 0, None) * va.capacity_kw.values
        d = pd.DataFrame({'ts': va.ts.values, 'g': va.current_group.values, 'y': va.energy.values.astype('float64'), 'p': p.astype('float64'), 'w': va.w.values.astype('float64')})
        nn = pd.DataFrame({'ts': night.ts.values, 'g': night.current_group.values, 'y': night.energy.values.astype('float64'), 'p': 0.0, 'w': night.w.values.astype('float64')})
        a = pd.concat([d, nn], ignore_index=True).groupby(['ts', 'g'], observed=True).agg(y=('y', 'sum'), p=('p', 'sum'), w=('w', 'first')).unstack('g')
        a.columns = [f'{x}_{y}' for x, y in a.columns]; a = a.fillna(0.0); a['w'] = a['w_A'].where(a['w_A'] > 0, a['w_B'])
        g = pd.DataFrame({'ts': a.index, 'y1': a.y_A.values, 'y2': a.y_B.values, 'p1': a.p_A.values, 'p2': a.p_B.values, 'w': a.w.values}).sort_values('ts')
        g.to_parquet(PFX + f'grp_{n}.parquet', index=False)
        W = Wsum(g, g.p1, g.p2); Rw = float((g.w * (g.y1 + g.y2)).sum())
        log(n, 'W_ref=%.4e  W_ref%%=%.3f  n_hours=%d  fit %.0fs  bias G1/G2 %.1f/%.1f' % (W, 100 * W / Rw, len(g), time.time() - t, (g.p1 - g.y1).mean(), (g.p2 - g.y2).mean()))
        del m, p, d, a, g; gc.collect()

elif stage == 'C':
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fits = sorted([os.path.basename(f)[len('verify_l1_calib_grp_'):-8] for f in glob.glob(PFX + 'grp_*.parquet')])
    G = {n: std_group(pd.read_parquet(PFX + f'grp_{n}.parquet')) for n in fits}
    rows = []
    for n, g in G.items():
        r = calib_table(g); r.update(fit=n, objective=n.split('_s')[0], seed=int(n.split('_s')[1]), bias_G1=float((g.p1 - g.y1).mean()), bias_G2=float((g.p2 - g.y2).mean())); rows.append(r)
    R = pd.DataFrame(rows).set_index('fit'); R.to_csv(PFX + 'C_fits.csv')
    log('\n' + R[['objective', 'seed', 'W_none', 'W_pct', 'gain_insample_pct', 'gain_global_halfCV_pct', 'gain_hour_halfCV_pct', 'gain_E5style_pct', 'bias_G1', 'bias_G2']].round(3).to_string())
    S = R.groupby('objective').agg(n=('W_none', 'size'), W_mean=('W_none', 'mean'), W_sd=('W_none', 'std'), W_min=('W_none', 'min'), W_max=('W_none', 'max'), Wpct_mean=('W_pct', 'mean'), Wpct_sd=('W_pct', 'std'),
                                   Wcal_mean=('W_global_halfCV', 'mean'), cal_gain_mean=('gain_global_halfCV_pct', 'mean'), hourcal_gain_mean=('gain_hour_halfCV_pct', 'mean'))
    S['gain_vs_l2_mean_pct'] = 100 * (1 - S.W_mean / S.loc['l2', 'W_mean']); S['gain_cal_vs_l2_mean_pct'] = 100 * (1 - S.Wcal_mean / S.loc['l2', 'W_mean'])
    S.to_csv(PFX + 'C_summary.csv'); log('\n' + S.round(4).to_string())
    ts = G[fits[0]].ts; day = (ts - pd.Timedelta(seconds=1)).dt.tz_convert(TZ).dt.floor('D').values
    def ens(obj):
        ns = [n for n in fits if n.split('_s')[0] == obj]; g = G[ns[0]].copy(); g['p1'] = np.mean([G[n].p1.values for n in ns], 0); g['p2'] = np.mean([G[n].p2.values for n in ns], 0); return g, len(ns)
    def dayW(g): c = (g.w * (np.abs(g.p1 - g.y1) + np.abs(g.p2 - g.y2))).values; return pd.Series(c).groupby(day).sum().values
    rng = np.random.default_rng(0); boot = []
    gl2, nl2 = ens('l2'); dl2 = dayW(gl2)
    for obj in [o for o in S.index if o != 'l2']:
        go, no = ens(obj); do = dayW(go); diff = do - dl2; nd = len(diff)
        bs = np.array([diff[rng.integers(0, nd, nd)].sum() for _ in range(4000)])
        pw = [100 * (1 - R.loc[a, 'W_none'] / R.loc[b, 'W_none']) for a in fits if a.startswith(obj + '_s') for b in fits if b.startswith('l2_s')]
        boot.append(dict(objective=obj, n_seeds=no, n_seeds_l2=nl2, W_ens=dl2.sum() + diff.sum(), W_ens_l2=dl2.sum(), gain_pct=100 * (-diff.sum() / dl2.sum()),
                         boot_ci95_gain_lo=100 * (-np.percentile(bs, 97.5) / dl2.sum()), boot_ci95_gain_hi=100 * (-np.percentile(bs, 2.5) / dl2.sum()),
                         p_boot_diff_ge0=float((bs >= 0).mean()), days_better=int((diff < 0).sum()), days_worse=int((diff > 0).sum()),
                         pairwise_gain_min=min(pw), pairwise_gain_max=max(pw), pairwise_all_positive=bool(min(pw) > 0)))
        log(obj, boot[-1])
    Bt = pd.DataFrame(boot).set_index('objective'); Bt.to_csv(PFX + 'C_bootstrap.csv')
    gl1w = ens('l1w')[0] if 'l1w' in S.index else None
    order = ['l2', 'l1', 'l1w']; col = {'l2': 'C3', 'l1': 'C0', 'l1w': 'C2'}
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    for n in fits:
        o = n.split('_s')[0]; Rw = R.loc[n, 'W_none'] / R.loc[n, 'W_pct']
        ax[0].scatter(order.index(o), R.loc[n, 'W_pct'], color=col[o], s=40)
        ax[0].scatter(order.index(o) + 0.15, R.loc[n, 'W_global_halfCV'] / Rw, marker='x', color='k', s=40)
    ax[0].set_xticks([0, 1, 2]); ax[0].set_xticklabels(['L2', 'L1', 'L1 w=SMP*k']); ax[0].set_ylabel('W_ref / sum(w*actual) [%]')
    ax[0].set_title('Validation 2024-06..2025-05, pooled LGBM, per seed\n(dot = raw, x = + global weighted-median calibration, half-CV)'); ax[0].grid(alpha=.3)
    if gl1w is not None:
        h = gl2.hour.values
        c2 = (gl2.w * (np.abs(gl2.p1 - gl2.y1) + np.abs(gl2.p2 - gl2.y2))).groupby(h).sum() / 1e6
        c1 = (gl1w.w * (np.abs(gl1w.p1 - gl1w.y1) + np.abs(gl1w.p2 - gl1w.y2))).groupby(h).sum() / 1e6
        ax[1].bar(c2.index - 0.2, c2.values, 0.4, label=f'L2 seed-avg ({nl2})', color='C3'); ax[1].bar(c1.index + 0.2, c1.values, 0.4, label='L1w seed-avg', color='C2')
        ax[1].set_xlabel('hour (KST, right-closed)'); ax[1].set_ylabel('W [1e6]'); ax[1].legend(); ax[1].set_title('W by hour: L2 vs weighted-L1 (seed-averaged)'); ax[1].grid(alpha=.3)
    plt.tight_layout(); plt.savefig(PFX + 'fig.png', dpi=110); log('saved fig')
