"""Adversarial verifier: does L1 / SMP*k-weighted L1 + weighted-median calibration lower W vs the L2 baseline?
Stage A: recompute W_ref from cached site predictions + 2-fold weighted-median calibration (independent code).
Stage B: retrain pooled L2 / L1 / L1w with 3 seeds each (same features/params as model_validation.py) to size seed noise.
Usage: python -I ver_l1cal.py A|B
"""
import sys, os, time, gc, json
import numpy as np, pandas as pd, pyarrow.parquet as pq

BASE = 'C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad/'
CACHE, OUT, MV = BASE + 'cache/', BASE + 'analysis/out/', BASE + 'analysis/mv_cache/'
SITES = 'C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset/sites.csv'
TZ = 'Asia/Seoul'
T1 = pd.Timestamp('2024-06-01 00:00', tz=TZ); T2 = pd.Timestamp('2025-06-01 00:00', tz=TZ)
TH = pd.Timestamp('2024-12-01 00:00', tz=TZ)
P = 'ver_l1cal_'


def log(*a): print(time.strftime('%H:%M:%S'), *a, flush=True)


# ---------------------------------------------------------------- common: hourly weights, group frame, W
smp = pd.read_parquet(CACHE + 'smp_all.parquet')
smp = smp[(smp.ts > T1) & (smp.ts <= T2)].reset_index(drop=True)
assert len(smp) == 8760 and (smp.k.values == np.where(smp.ts.dt.hour.isin(range(11, 16)), 3, 1)).all()
W_T = (smp.smp * smp.k).to_numpy('float64')          # w_t, index = hour-of-year 0..8759
HOUR = smp.ts.dt.hour.to_numpy()
K = smp.k.to_numpy()
BLOCK = (((smp.ts - T1) - pd.Timedelta(seconds=1)) // pd.Timedelta(days=7)).to_numpy() % 2   # alternate 7-day blocks
HALF = np.where(smp.ts <= TH, 0, 1)
sites = pd.read_csv(SITES)
GRP = sites.set_index('site_id').current_group.map({'A': 0, 'B': 1})


def tidx(ts):  # tz-aware ts -> 0..8759
    i = ((ts - T1) // pd.Timedelta(hours=1)).to_numpy() - 1
    assert i.min() >= 0 and i.max() < 8760
    return i


def group_frame(site_id, ts, y, p):
    """(ts, group) sums -> arrays y[8760,2], p[8760,2] (missing site-hours simply absent, as in the reports)."""
    i = tidx(ts); g = GRP.reindex(site_id).to_numpy()
    assert not np.isnan(g).any()
    key = i * 2 + g.astype(int)
    Y = np.bincount(key, weights=y.astype('float64'), minlength=17520).reshape(8760, 2)
    Pp = np.bincount(key, weights=p.astype('float64'), minlength=17520).reshape(8760, 2)
    return Y, Pp


def W_of(Y, Pp, mask=None, w=W_T):
    e = np.abs(Pp - Y)
    m = np.ones(8760, bool) if mask is None else mask
    return float((w[m, None] * e[m]).sum())


def wmedian(x, wt):
    o = np.argsort(x); x, wt = x[o], wt[o]; c = np.cumsum(wt); return float(x[np.searchsorted(c, 0.5 * c[-1])])


def fit_factor(Y, Pp, mask, g, by=None, minn=20):
    """(w*p)-weighted median of y/p on rows `mask`; by=None -> scalar, by='hour' -> dict hour->factor."""
    ok = mask & (Pp[:, g] > 1)
    r = Y[ok, g] / Pp[ok, g]; wt = W_T[ok] * Pp[ok, g]
    if by is None:
        return wmedian(r, wt)
    h = HOUR[ok]; out = {}
    for hh in range(24):
        s = h == hh
        out[hh] = wmedian(r[s], wt[s]) if s.sum() > minn else 1.0
    return out


def calibrate_cv(Y, Pp, split):
    """2-fold: fit on one fold, apply on the other; returns dict of W totals (uncal, global, hourly) over both test folds."""
    fold = HALF if split == 'half' else BLOCK
    res = dict(W_base=W_of(Y, Pp), W_global=0.0, W_hour=0.0)
    facs = {}
    for f in (0, 1):
        fit_m, te_m = fold != f, fold == f
        Pg, Ph = Pp.copy(), Pp.copy()
        for g in (0, 1):
            a = fit_factor(Y, Pp, fit_m, g); facs[(f, g)] = a
            Pg[te_m, g] *= a
            ah = fit_factor(Y, Pp, fit_m, g, by='hour')
            Ph[te_m, g] *= np.vectorize(ah.get)(HOUR[te_m])
        res['W_global'] += W_of(Y, Pg, te_m); res['W_hour'] += W_of(Y, Ph, te_m)
    res['gain_global_pct'] = 100 * (1 - res['W_global'] / res['W_base'])
    res['gain_hour_pct'] = 100 * (1 - res['W_hour'] / res['W_base'])
    res.update({f'a_fitfold{f}_G{g + 1}': facs[(f, g)] for f in (0, 1) for g in (0, 1)})
    return res


def e5_style(Y, Pp):
    """model_validation E5 convention: fit on 1st half (<=TH), evaluate on 2nd half only."""
    fit_m, te_m = HALF == 0, HALF == 1
    Pg, Ph = Pp.copy(), Pp.copy()
    for g in (0, 1):
        Pg[te_m, g] *= fit_factor(Y, Pp, fit_m, g)
        ah = fit_factor(Y, Pp, fit_m, g, by='hour'); Ph[te_m, g] *= np.vectorize(ah.get)(HOUR[te_m])
    return dict(W_H2_base=W_of(Y, Pp, te_m), W_H2_global=W_of(Y, Pg, te_m), W_H2_hour=W_of(Y, Ph, te_m))


RW = None  # sum w*actual, set from the first model


def full_eval(name, Y, Pp, extra=None):
    global RW
    if RW is None:
        RW = float((W_T[:, None] * Y).sum())
    r = dict(model=name, W_ref=W_of(Y, Pp), W_ref_pct=100 * W_of(Y, Pp) / RW,
             W_k3=W_of(Y, Pp, K == 3), W_k1=W_of(Y, Pp, K == 1),
             bias_G1=float((Pp[:, 0] - Y[:, 0]).mean()), bias_G2=float((Pp[:, 1] - Y[:, 1]).mean()))
    for sp in ('half', 'wk'):
        c = calibrate_cv(Y, Pp, sp)
        r.update({f'{sp}_{k}': v for k, v in c.items()})
    r.update(e5_style(Y, Pp))
    r.update(extra or {})
    log(name, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if not k.startswith(('half_a_', 'wk_a_'))})
    return r


# ---------------------------------------------------------------- stage A: cached site predictions
def stage_a():
    rows = []
    for name in ['E0_pool', 'E1_l1w', 'E0_site', 'E7_mix_site10']:
        d = pd.read_parquet(CACHE + f'val_pred_site_{name}.parquet')
        Y, Pp = group_frame(d.site_id.to_numpy(), d.ts, d.y.to_numpy(), d.pred.to_numpy())
        # daytime-only variant (rows with pred==0 are the night rows written by model_validation): comparable to forecast_skill
        dd = d[d.pred > 0]
        Yd, Pd = group_frame(dd.site_id.to_numpy(), dd.ts, dd.y.to_numpy(), dd.pred.to_numpy())
        rows.append(full_eval(name, Y, Pp, dict(n_rows=len(d), W_ref_dayrows_only=W_of(Yd, Pd), Rw_dayrows=float((W_T[:, None] * Yd).sum()))))
        del d, dd; gc.collect()
    # E1_l1 (unweighted L1) has no site file; use the group cache from model_validation (same aggregation)
    for name in ['E1_l1', 'E1_l2w', 'E1_l1w_s2', 'E1_l1w_s3', 'E4_blend50']:
        g = pd.read_parquet(MV + f'group_{name}.parquet')
        if 'ts' in g.columns: g = g.set_index('ts')
        if g.index.tz is None: g.index = g.index.tz_localize('UTC').tz_convert(TZ)
        g = g.sort_index(); assert len(g) == 8760 and (g.index == smp.ts).all()
        Y = g[['y_A', 'y_B']].to_numpy('float64'); Pp = g[['p_A', 'p_B']].to_numpy('float64')
        assert np.allclose(g.w.to_numpy(), W_T, rtol=1e-5)
        rows.append(full_eval(name, Y, Pp, dict(source='mv_cache group')))
    df = pd.DataFrame(rows)
    df.to_csv(OUT + P + 'stageA.csv', index=False)
    log('Rw =', RW)
    return df


# ---------------------------------------------------------------- stage B: retrain with seeds
A6 = ['wa_cloud', 'wa_temp', 'wa_humidity', 'wa_ground_press', 'wa_wind_speed', 'wa_rain']
B9 = ['wb_cloud', 'wb_uv_idx', 'wb_temp', 'wb_rel_hum', 'wb_dew_point', 'wb_vis', 'wb_ceiling', 'wb_precip_prob', 'wb_total_liq']
BASEF = A6 + B9 + ['elev', 'azim', 'cosz', 'doy_sin', 'doy_cos', 'hour'] + ['capacity_kw', 'lat', 'lon']
LGB = dict(n_estimators=400, learning_rate=0.06, num_leaves=127, min_child_samples=200, subsample=0.8,
           subsample_freq=1, colsample_bytree=0.8, verbose=-1, n_jobs=8)


def stage_b():
    import lightgbm as lgb
    cols = list(dict.fromkeys(['site_id', 'ts', 'energy', 'capacity_kw', 'cf', 'w'] + BASEF))  # capacity_kw is also a feature
    df = pd.read_parquet(MV + 'day.parquet', columns=cols)
    assert len(BASEF) == 24 and df.columns.is_unique
    tr = df[df.ts <= T1]; va = df[df.ts > T1]
    log('train', len(tr), 'val', len(va))
    Xt = tr[BASEF].to_numpy('float32'); yt = tr.cf.to_numpy('float32'); wt = (tr.w / tr.w.mean()).to_numpy('float32')
    Xv = va[BASEF].to_numpy('float32'); cap = va.capacity_kw.to_numpy('float64')
    v_site = va.site_id.astype(str).to_numpy(); v_ts = va.ts; v_y = va.energy.to_numpy('float64')
    del df, tr; gc.collect()
    night = pd.read_parquet(MV + 'night.parquet', columns=['site_id', 'ts', 'energy'])
    night = night[night.ts > T1]
    Yn, _ = group_frame(night.site_id.astype(str).to_numpy(), night.ts, night.energy.to_numpy('float64'), np.zeros(len(night)))
    del night; gc.collect()
    rows = []; preds = {}
    if os.environ.get('VER_DEFAULT_SEED'):  # stage C: does LightGBM's default seed reproduce the reported E0_pool / E1_l1w?
        for obj, wflag in [('l2', False), ('l1', True)]:
            m = lgb.LGBMRegressor(objective='regression' if obj == 'l2' else 'regression_l1', **LGB)
            m.fit(Xt, yt, sample_weight=wt if wflag else None)
            p = np.clip(m.predict(Xv), 0, None) * cap
            Y, Pp = group_frame(v_site, v_ts, v_y, p); Y = Y + Yn
            rows.append(full_eval(f"{obj}{'w' if wflag else ''}_defaultseed", Y, Pp, dict(objective=obj, weighted=wflag, seed='default')))
            pd.DataFrame(rows).to_csv(OUT + P + 'stageC_defaultseed.csv', index=False)
        return
    for obj, wflag, seed in [('l2', False, 0), ('l1', False, 0), ('l1', True, 0),
                             ('l2', False, 1), ('l1', False, 1), ('l1', True, 1),
                             ('l2', False, 2), ('l1', False, 2), ('l1', True, 2)]:
        name = f"{obj}{'w' if wflag else ''}_s{seed}"
        t0 = time.time()
        m = lgb.LGBMRegressor(objective='regression' if obj == 'l2' else 'regression_l1', random_state=seed, **LGB)
        m.fit(Xt, yt, sample_weight=wt if wflag else None)
        p = np.clip(m.predict(Xv), 0, None) * cap
        Y, Pp = group_frame(v_site, v_ts, v_y, p); Y = Y + Yn
        preds[name] = Pp
        rows.append(full_eval(name, Y, Pp, dict(objective=obj, weighted=wflag, seed=seed, fit_sec=time.time() - t0)))
        pd.DataFrame(rows).to_csv(OUT + P + 'stageB.csv', index=False)
        del m; gc.collect()
    # seed-averaged ensembles per objective (3 seeds) for a like-for-like ensemble comparison
    for tag in ['l2', 'l1', 'l1w']:
        Pm = np.mean([preds[f'{tag}_s{s}'] for s in range(3)], axis=0)
        rows.append(full_eval(f'{tag}_seedavg3', Y, Pm, dict(objective=tag, seed=-1)))
    np.save(OUT + P + 'Y_val_group.npy', Y)
    pd.DataFrame(rows).to_csv(OUT + P + 'stageB.csv', index=False)


def figure():
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    a = pd.read_csv(OUT + P + 'stageA.csv'); b = pd.read_csv(OUT + P + 'stageB.csv')
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
    bb = b[b.seed >= 0]
    for i, (tag, c) in enumerate([('l2', 'tab:gray'), ('l1', 'tab:blue'), ('l1w', 'tab:green')]):
        s = bb[bb.model.str.startswith(tag + '_')]
        ax[0].scatter([i] * len(s), s.W_ref_pct, color=c, s=60, label=f'{tag} (3 seeds)')
        ax[0].scatter([i + 0.25] * len(s), s.W_ref_pct * (1 - s.half_gain_global_pct / 100),
                      color=c, marker='x', s=60, label=f'{tag} + global wmedian cal (half CV)')
    ax[0].set_xticks([0, 1, 2]); ax[0].set_xticklabels(['L2', 'L1', 'L1 w=SMP*k']); ax[0].set_ylabel('W_ref % of sum(w*actual)')
    ax[0].set_title('Retrained pooled LGBM, validation 2024-06..2025-05'); ax[0].grid(alpha=.3); ax[0].legend(fontsize=7)
    aa = a.set_index('model').loc[['E0_pool', 'E1_l1', 'E1_l1w', 'E1_l1w_s2', 'E1_l1w_s3', 'E1_l2w', 'E7_mix_site10', 'E4_blend50', 'E0_site']]
    x = np.arange(len(aa)); wd = 0.27
    ax[1].bar(x - wd, aa.W_ref_pct, wd, label='no calibration', color='tab:gray')
    ax[1].bar(x, aa.W_ref_pct * (1 - aa.half_gain_global_pct / 100), wd, label='global wmedian, half CV', color='tab:orange')
    ax[1].bar(x + wd, aa.W_ref_pct * (1 - aa.wk_gain_global_pct / 100), wd, label='global wmedian, alt-week CV', color='tab:blue')
    ax[1].set_xticks(x); ax[1].set_xticklabels(aa.index, rotation=35, ha='right', fontsize=8); ax[1].set_ylim(11.5, 17); ax[1].grid(alpha=.3, axis='y')
    ax[1].set_title('Reported models: effect of weighted-median calibration'); ax[1].legend(fontsize=7); ax[1].set_ylabel('W_ref %')
    fig.tight_layout(); fig.savefig(OUT + P + 'fig.png', dpi=120)


if __name__ == '__main__':
    st = sys.argv[1] if len(sys.argv) > 1 else 'A'
    if st == 'A': stage_a()
    elif st == 'B': stage_b()
    elif st == 'F': figure()
