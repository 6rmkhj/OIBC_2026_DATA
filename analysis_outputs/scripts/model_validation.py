"""OIBC 2026 model validation framework. Stages via argv: prep | e0 | pool <names...> | e4 | e5 | report
Restartable: every stage caches its outputs; completed experiments are skipped."""
import sys, os, time, json, gc
import numpy as np, pandas as pd, pyarrow as pa, pyarrow.parquet as pq, pyarrow.compute as pc

BASE = 'C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad/'
CACHE, OUT, MV = BASE + 'cache/', BASE + 'analysis/out/', BASE + 'analysis/mv_cache/'
os.makedirs(MV, exist_ok=True); os.makedirs(OUT, exist_ok=True)
TZ = 'Asia/Seoul'
T0 = pd.Timestamp('2022-06-01 00:00', tz=TZ)   # train: T0 < ts <= T1
T1 = pd.Timestamp('2024-06-01 00:00', tz=TZ)   # val:   T1 < ts <= T2
T2 = pd.Timestamp('2025-06-01 00:00', tz=TZ)
TH = pd.Timestamp('2024-12-01 00:00', tz=TZ)   # val half split for E5
A6 = ['wa_cloud', 'wa_temp', 'wa_humidity', 'wa_ground_press', 'wa_wind_speed', 'wa_rain']
B9 = ['wb_cloud', 'wb_uv_idx', 'wb_temp', 'wb_rel_hum', 'wb_dew_point', 'wb_vis', 'wb_ceiling', 'wb_precip_prob', 'wb_total_liq']
WX = A6 + B9
GEO = ['elev', 'azim', 'cosz', 'toa', 'hour', 'doy']
STATIC = ['capacity_kw', 'lat', 'lon']
PHYS = ['csa', 'csb', 'toaa', 'toab', 'uvtoa', 'cdis']
BASEF = WX + ['elev', 'azim', 'cosz', 'doy_sin', 'doy_cos', 'hour'] + STATIC
LGB_SITE = dict(n_estimators=600, learning_rate=0.06, num_leaves=127, min_child_samples=200, subsample=0.8,
                subsample_freq=1, colsample_bytree=0.8, verbose=-1, n_jobs=3)
LGB_POOL = dict(n_estimators=400, learning_rate=0.06, num_leaves=127, min_child_samples=200, subsample=0.8,
                subsample_freq=1, colsample_bytree=0.8, verbose=-1, n_jobs=10)


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


# ----------------------------------------------------------------------------- prep
def phys(df, suf=''):
    ca = (1 - df['wa_cloud' + suf] / 100).clip(0, 1); cb = (1 - df['wb_cloud' + suf] / 100).clip(0, 1)
    df['csa' + suf] = (df.cosz * ca).astype('float32'); df['csb' + suf] = (df.cosz * cb).astype('float32')
    df['toaa' + suf] = (df.toa * ca).astype('float32'); df['toab' + suf] = (df.toa * cb).astype('float32')
    df['uvtoa' + suf] = (df['wb_uv_idx' + suf] * df.toa / 1000).astype('float32')
    df['cdis' + suf] = (df['wa_cloud' + suf] - df['wb_cloud' + suf]).abs().astype('float32')


def site_ratios():
    """Rolling 30d / 365d site CF relative to fleet, lagged 2 days (strictly before 17:00 issue time)."""
    cf = pd.read_parquet(CACHE + 'cf_wide.parquet')
    day = (cf.index - pd.Timedelta(seconds=1)).floor('D')
    d = cf.groupby(day).mean()                       # daily mean CF per site (all hours)
    fleet = d.mean(axis=1)
    out = {}
    for n, mp in [(30, 15), (365, 180)]:
        rs = d.rolling(n, min_periods=mp).mean().shift(2)
        rf = fleet.rolling(n, min_periods=mp).mean().shift(2)
        r = rs.div(rf, axis=0)
        r = r.stack().rename(f'r{n}').reset_index(); r.columns = ['date', 'site_id', f'r{n}']
        out[n] = r
    r = out[30].merge(out[365], on=['date', 'site_id'], how='outer')
    r['date'] = r['date'].dt.tz_localize(None)
    return r


def prep():
    if os.path.exists(MV + 'day.parquet'):
        log('prep cached'); return
    cols = ['site_id', 'ts', 'energy', 'current_group'] + STATIC + WX + GEO
    flt = [('ts', '>', T0), ('ts', '<=', T2)]
    t = pq.read_table(CACHE + 'panel_train_r17.parquet', columns=cols, filters=flt)
    t = t.set_column(t.schema.get_field_index('site_id'), 'site_id', pc.dictionary_encode(t['site_id']))
    df = t.to_pandas(); del t
    t10 = pq.read_table(CACHE + 'panel_train_r10.parquet', columns=['ts'] + WX, filters=flt)
    assert pc.all(pc.equal(t10['ts'], pa.array(df.ts))).as_py()
    for c in WX:
        df[c + '_r10'] = t10[c].to_numpy()
    del t10; gc.collect()
    df['current_group'] = df.current_group.astype('category')
    df['hour'] = df.hour.astype('float32'); df['doy'] = df.doy.astype('float32')
    log('loaded', df.shape, 'rss', rss())
    night = df.loc[df.elev <= 0, ['site_id', 'ts', 'energy', 'current_group']].copy()
    df = df[df.elev > 0].copy(); gc.collect()
    log('day rows', len(df), 'night rows', len(night))
    df['cf'] = (df.energy / df.capacity_kw).clip(0, 1.2).astype('float32')
    df['doy_sin'] = np.sin(2 * np.pi * df.doy / 365.25).astype('float32')
    df['doy_cos'] = np.cos(2 * np.pi * df.doy / 365.25).astype('float32')
    phys(df); phys(df, '_r10')
    r = site_ratios()
    df['date'] = (df.ts - pd.Timedelta(seconds=1)).dt.floor('D').dt.tz_localize(None)
    df['site_id'] = df.site_id.astype(str)
    df = df.merge(r, on=['date', 'site_id'], how='left')
    # frozen ratios: value at the first val day, used for all val rows (mimics test where data stops at issue)
    fz = r[r.date == T1.tz_localize(None).normalize() + pd.Timedelta(days=1)].set_index('site_id')
    isval = df.ts > T1
    for n in (30, 365):
        df[f'r{n}f'] = df[f'r{n}'].astype('float32')
        df.loc[isval, f'r{n}f'] = df.loc[isval, 'site_id'].map(fz[f'r{n}']).astype('float32').values
        df[f'r{n}'] = df[f'r{n}'].astype('float32')
    df['site_id'] = df.site_id.astype('category')
    df = df.drop(columns=['date'])
    smp = pd.read_parquet(CACHE + 'smp_all.parquet'); smp['w'] = (smp.smp * smp.k).astype('float32')
    df = df.merge(smp[['ts', 'w']], on='ts', how='left')
    night = night.merge(smp[['ts', 'w']], on='ts', how='left')
    df.to_parquet(MV + 'day.parquet'); night.to_parquet(MV + 'night.parquet')
    st = df.groupby('site_id', observed=True)[['capacity_kw', 'lat', 'lon']].first()
    st['group'] = df.groupby('site_id', observed=True).current_group.first()
    st.to_csv(MV + 'static.csv')
    log('prep done', df.shape, 'rss', rss())


def rss():
    import psutil; return f'{psutil.Process().memory_info().rss / 1e9:.2f}GB'


def load_day(cols=None):
    df = pd.read_parquet(MV + 'day.parquet', columns=cols)
    return df


# ----------------------------------------------------------------------------- metrics
def group_series(df_day, pred_day, night=None, seen_only=False):
    """Aggregate to (ts, group) y/p sums. Night rows: pred 0, actual included."""
    d = pd.DataFrame({'ts': df_day.ts.values, 'g': df_day.current_group.values, 'y': df_day.energy.values,
                      'p': pred_day.astype('float64'), 'w': df_day.w.values, 's': df_day.seen.values})
    if night is not None:
        n = pd.DataFrame({'ts': night.ts.values, 'g': night.current_group.values, 'y': night.energy.values,
                          'p': 0.0, 'w': night.w.values, 's': night.seen.values})
        d = pd.concat([d, n], ignore_index=True)
    if seen_only:
        d = d[d.s]
    a = d.groupby(['ts', 'g'], observed=True).agg(y=('y', 'sum'), p=('p', 'sum'), w=('w', 'first')).unstack('g')
    a.columns = [f'{x}_{y}' for x, y in a.columns]
    a = a.fillna(0.0); a['w'] = a['w_A'].where(a['w_A'] > 0, a['w_B'])
    return a


def load_group(name):
    g = pd.read_parquet(MV + f'group_{name}.parquet')
    if g.index.tz is None:  # parquet round-trip stores the index as naive UTC
        g.index = g.index.tz_localize('UTC').tz_convert(TZ)
    return g


def metrics(a, cap):
    e1 = a.p_A - a.y_A; e2 = a.p_B - a.y_B; w = a.w
    W_ref = float((w * (e1.abs() + e2.abs())).sum()); W_pool = float((w * (e1 + e2).abs()).sum())
    Rw = float((w * (a.y_A + a.y_B)).sum())
    return dict(W_ref=W_ref, W_pool=W_pool, W_ref_pct=100 * W_ref / Rw, W_pool_pct=100 * W_pool / Rw, Rw=Rw,
                MAE_G1=float(e1.abs().mean()), MAE_G2=float(e2.abs().mean()),
                nMAE_G1=100 * float(e1.abs().mean()) / cap['A'], nMAE_G2=100 * float(e2.abs().mean()) / cap['B'],
                bias_G1=float(e1.mean()), bias_G2=float(e2.mean()), n_hours=int(len(a)))


def eval_and_save(name, df_val, pred, night, cap, extra=None, save_site=False):
    a = group_series(df_val, pred, night)
    m = metrics(a, cap); m['name'] = name; m.update(extra or {})
    a2 = group_series(df_val, pred, night, seen_only=True); m2 = metrics(a2, cap)
    m.update({k + '_seen': v for k, v in m2.items() if k in ('W_ref', 'W_pool', 'W_ref_pct', 'W_pool_pct', 'nMAE_G1', 'nMAE_G2', 'bias_G1', 'bias_G2')})
    json.dump(m, open(OUT + f'metrics_{name}.json', 'w'), indent=1)
    a.to_parquet(MV + f'group_{name}.parquet'); a2.to_parquet(MV + f'group_{name}_seen.parquet')
    np.save(MV + f'pred_{name}.npy', pred.astype('float32'))
    if save_site:
        s = pd.DataFrame({'site_id': df_val.site_id.astype(str).values, 'ts': df_val.ts.array,
                          'y': df_val.energy.values, 'pred': pred.astype('float32')})
        n = pd.DataFrame({'site_id': night.site_id.astype(str).values, 'ts': night.ts.array,
                          'y': night.energy.values, 'pred': np.float32(0)})
        pd.concat([s, n]).sort_values(['site_id', 'ts']).to_parquet(CACHE + f'val_pred_site_{name}.parquet', index=False)
    log(name, {k: round(v, 3) if isinstance(v, float) else v for k, v in m.items()})
    return m


def frozen_ratios():
    """Per-site last available r30/r365 before val start (ffill) -> mv_cache/frozen.csv"""
    if os.path.exists(MV + 'frozen.csv'):
        return pd.read_csv(MV + 'frozen.csv', index_col=0)
    r = site_ratios(); r = r[r.date <= T1.tz_localize(None).normalize() + pd.Timedelta(days=1)]
    fz = r.sort_values('date').groupby('site_id')[['r30', 'r365']].last()
    fz.to_csv(MV + 'frozen.csv'); return fz


def load_val():
    df = load_day()
    tr = df[df.ts <= T1]; va = df[df.ts > T1].reset_index(drop=True)
    fz = frozen_ratios()
    for n in (30, 365):  # frozen = last available value before val start, constant over the val year
        va[f'r{n}f'] = va.site_id.astype(str).map(fz[f'r{n}']).astype('float32').values
    night = pd.read_parquet(MV + 'night.parquet'); night = night[night.ts > T1].copy()
    seen = set(tr.site_id.unique().astype(str))
    va['seen'] = va.site_id.astype(str).isin(seen).values; night['seen'] = night.site_id.astype(str).isin(seen).values
    st = pd.read_csv(MV + 'static.csv', index_col=0); cap = st.groupby('group').capacity_kw.sum().to_dict()
    return tr, va, night, cap


# ----------------------------------------------------------------------------- E0 per-site
def e0():
    import lightgbm as lgb
    from joblib import Parallel, delayed
    name = 'E0_site_raw'
    if os.path.exists(OUT + f'metrics_{name}.json'):
        log(name, 'cached'); return
    tr, va, night, cap = load_val()
    feats = BASEF
    sites = list(va.site_id.cat.categories)
    tr_idx = tr.groupby('site_id', observed=True).indices; va_idx = va.groupby('site_id', observed=True).indices

    def one(s):
        Xt = tr.iloc[tr_idx[s]]; Xv = va.iloc[va_idx[s]]
        m = lgb.LGBMRegressor(**LGB_SITE).fit(Xt[feats], Xt.cf)
        p = np.clip(m.predict(Xv[feats]), 0, None) * Xv.capacity_kw.values
        return s, va_idx[s], p.astype('float32'), m.booster_.feature_importance('gain')

    t = time.time()
    res = Parallel(n_jobs=3, verbose=0)(delayed(one)(s) for s in sites if s in tr_idx)
    log('per-site fit done', len(res), 'sites', f'{time.time() - t:.0f}s')
    pred = np.zeros(len(va), dtype='float32'); imp = []
    for s, ix, p, g in res:
        pred[ix] = p; imp.append(g)
    pd.DataFrame({'feature': feats, 'gain_mean': np.mean(imp, 0), 'gain_share_pct': 100 * np.mean(imp, 0) / np.sum(np.mean(imp, 0))}) \
        .sort_values('gain_mean', ascending=False).to_csv(OUT + 'feat_importance_E0_site.csv', index=False)
    eval_and_save(name, va, pred, night, cap, dict(fit_sec=time.time() - t, model='per-site L2 600 trees (unseen sites=0)', rnd=17))


def savesite(names):
    tr, va, night, cap = load_val(); del tr
    for n in names:
        pred = np.load(MV + f'pred_{n}.npy')
        s = pd.DataFrame({'site_id': va.site_id.astype(str).values, 'ts': va.ts.array, 'y': va.energy.values, 'pred': pred.astype('float32')})
        z = pd.DataFrame({'site_id': night.site_id.astype(str).values, 'ts': night.ts.array, 'y': night.energy.values, 'pred': np.float32(0)})
        pd.concat([s, z]).sort_values(['site_id', 'ts']).to_parquet(CACHE + f'val_pred_site_{n}.parquet', index=False); log('saved', n)


def ens(args):
    """ens NAME m1 m2 ... [-- w1 w2 ...]: weighted average of cached val predictions."""
    name = args[0]; rest = args[1:]
    members = rest[:rest.index('--')] if '--' in rest else rest
    w = np.array([float(x) for x in rest[rest.index('--') + 1:]]) if '--' in rest else np.ones(len(members)) / len(members)
    tr, va, night, cap = load_val(); del tr
    P = np.stack([np.load(MV + f'pred_{m}.npy') for m in members]); p = (P * w[:, None]).sum(0)
    eval_and_save(name, va, p.astype('float32'), night, cap, dict(model='ens:' + '+'.join(f'{wi:.2f}*{m}' for wi, m in zip(w, members)), rnd=0, n_feats=len(members)))


def e0fb():
    """E0_site = per-site model where the site has training history, else pooled E0_pool prediction."""
    tr, va, night, cap = load_val(); del tr
    raw = np.load(MV + 'pred_E0_site_raw.npy'); pool = np.load(MV + 'pred_E0_pool.npy')
    pred = np.where(va.seen.values, raw, pool).astype('float32')
    eval_and_save('E0_site', va, pred, night, cap, dict(model='per-site L2 600 trees + pooled fallback for 48 unseen sites', rnd=17), save_site=True)


# ----------------------------------------------------------------------------- pooled experiments
def pooled_exps():
    best1 = best_of(['E0_pool', 'E1_l1', 'E1_l1w', 'E1_l2w'])  # objective choice
    ob = {'E0_pool': ('l2', False), 'E1_l1': ('l1', False), 'E1_l1w': ('l1', True), 'E1_l2w': ('l2', True)}.get(best1, ('l2', False))
    E = {
        'E0_pool': dict(feats=BASEF, obj='l2', rnd=17, wt=False),
        'E1_l1': dict(feats=BASEF, obj='l1', rnd=17, wt=False),
        'E1_l1w': dict(feats=BASEF, obj='l1', rnd=17, wt=True),
        'E1_l2w': dict(feats=BASEF, obj='l2', rnd=17, wt=True),
        'E2_r10': dict(feats=BASEF, obj=ob[0], rnd=10, wt=ob[1]),
        'E2_both': dict(feats=BASEF + [c + '_r10' for c in WX], obj=ob[0], rnd=17, wt=ob[1]),
        'E3_phys': dict(feats=BASEF + ['toa'] + PHYS, obj=ob[0], rnd=17, wt=ob[1]),
        'E3_phys_both': dict(feats=BASEF + ['toa'] + PHYS + [c + '_r10' for c in WX] + [c + '_r10' for c in PHYS], obj=ob[0], rnd=17, wt=ob[1]),
        'E3_site': dict(feats=BASEF + ['toa'] + PHYS + ['site'], obj=ob[0], rnd=17, wt=ob[1], cat=['site']),
        'E3_site_nolatlon': dict(feats=[f for f in BASEF if f not in ('lat', 'lon')] + ['toa'] + PHYS + ['site'], obj=ob[0], rnd=17, wt=ob[1], cat=['site']),
        'E3_r30': dict(feats=BASEF + ['toa'] + PHYS + ['r30', 'r365'], obj=ob[0], rnd=17, wt=ob[1]),
        'E3_r30f': dict(feats=BASEF + ['toa'] + PHYS + ['r30f', 'r365f'], obj=ob[0], rnd=17, wt=ob[1]),
        'E3_r365f': dict(feats=BASEF + ['toa'] + PHYS + ['r365f'], obj=ob[0], rnd=17, wt=ob[1]),
        'E3_site_r365f': dict(feats=BASEF + ['toa'] + PHYS + ['site', 'r365f'], obj=ob[0], rnd=17, wt=ob[1], cat=['site']),
        'E3_site_both': dict(feats=BASEF + ['toa'] + PHYS + ['site'] + [c + '_r10' for c in WX] + [c + '_r10' for c in PHYS], obj=ob[0], rnd=17, wt=ob[1], cat=['site']),
        'E3_site_nophys': dict(feats=BASEF + ['site'], obj=ob[0], rnd=17, wt=ob[1], cat=['site']),
        'E3_r365f_nophys': dict(feats=BASEF + ['r365f'], obj=ob[0], rnd=17, wt=ob[1]),
        'E1_l1w_s2': dict(feats=BASEF, obj='l1', rnd=17, wt=True, seed=2),
        'E1_l1w_s3': dict(feats=BASEF, obj='l1', rnd=17, wt=True, seed=3),
        'E6_trees800': dict(feats=BASEF, obj=ob[0], rnd=17, wt=ob[1], params=dict(n_estimators=800)),
        'E6_lr03_t800': dict(feats=BASEF, obj=ob[0], rnd=17, wt=ob[1], params=dict(n_estimators=800, learning_rate=0.03)),
        'E6_leaves255': dict(feats=BASEF, obj=ob[0], rnd=17, wt=ob[1], params=dict(num_leaves=255, min_child_samples=100)),
        'E6_leaves63': dict(feats=BASEF, obj=ob[0], rnd=17, wt=ob[1], params=dict(num_leaves=63, min_child_samples=400)),
    }
    return E


NOT_DEPLOYABLE = {'E3_r30', 'E0_site_raw'}  # rolling ratio cannot be updated in the test year


def best_of(names):
    done = {n: json.load(open(OUT + f'metrics_{n}.json'))['W_ref'] for n in names if os.path.exists(OUT + f'metrics_{n}.json') and n not in NOT_DEPLOYABLE}
    return min(done, key=done.get) if done else None


def run_pool(names):
    import lightgbm as lgb
    E = pooled_exps()
    names = [n for n in names if not os.path.exists(OUT + f'metrics_{n}.json')]
    if not names:
        log('all cached'); return
    tr, va, night, cap = load_val()
    tr = tr.copy(); va = va.copy()
    tr['site'] = tr.site_id.cat.codes.astype('int16'); va['site'] = va.site_id.cat.codes.astype('int16')
    wtr = (tr.w / tr.w.mean()).astype('float32').values
    for n in names:
        if n == 'E2_avg':
            continue
        c = E[n]; feats = list(c['feats'])
        if c['rnd'] == 10:  # swap weather & phys cols to round-10 versions
            feats = [f + '_r10' if (f in WX or f in PHYS) else f for f in feats]
        Xt = tr[feats]; Xv = va[feats]
        if c.get('cat'):
            Xt = Xt.astype({'site': 'category'}); Xv = Xv.astype({'site': 'category'})
        params = dict(LGB_POOL, objective='regression' if c['obj'] == 'l2' else 'regression_l1', random_state=c.get('seed', 0), **c.get('params', {}))
        t = time.time()
        m = lgb.LGBMRegressor(**params).fit(Xt, tr.cf, sample_weight=wtr if c['wt'] else None,
                                             categorical_feature=c.get('cat', 'auto'))
        p = np.clip(m.predict(Xv), 0, None) * va.capacity_kw.values
        imp = m.booster_.feature_importance('gain')
        pd.DataFrame({'feature': feats, 'gain': imp, 'gain_share_pct': 100 * imp / imp.sum()}).sort_values('gain', ascending=False) \
            .to_csv(OUT + f'feat_importance_{n}.csv', index=False)
        eval_and_save(n, va, p.astype('float32'), night, cap, dict(fit_sec=time.time() - t, model=f"pooled {c['obj']}{' w' if c['wt'] else ''} 400 trees", rnd=c['rnd'], n_feats=len(feats)))
        del m, Xt, Xv; gc.collect()
    if 'E2_avg' in names:
        b = best_of(['E0_pool', 'E1_l1', 'E1_l1w', 'E1_l2w'])
        p = 0.5 * (np.load(MV + f'pred_{b}.npy') + np.load(MV + 'pred_E2_r10.npy'))
        eval_and_save('E2_avg', va, p, night, cap, dict(model=f'avg({b}, E2_r10)', rnd=0))


# ----------------------------------------------------------------------------- E4 direct aggregate
def e4():
    import lightgbm as lgb
    if os.path.exists(OUT + 'metrics_E4_direct.json'):
        log('E4 cached'); return
    tr, va, night, cap = load_val()
    feats = WX + ['toa'] + PHYS + ['elev', 'azim', 'cosz', 'doy_sin', 'doy_cos', 'hour']
    def agg(df):
        d = df[['ts', 'current_group', 'energy', 'capacity_kw', 'w']].copy()
        for f in feats:
            d[f] = df[f].values * df.capacity_kw.values
        g = d.groupby(['ts', 'current_group'], observed=True).sum()
        for f in feats:
            g[f] = g[f] / g.capacity_kw
        g['cf'] = g.energy / g.capacity_kw; g['w'] = d.groupby(['ts', 'current_group'], observed=True).w.first()
        return g.reset_index()
    gt, gv = agg(tr), agg(va)
    gv['p'] = 0.0
    ob = best_of(['E0_pool', 'E1_l1', 'E1_l1w', 'E1_l2w']); obj = 'regression_l1' if ob and 'l1' in ob else 'regression'
    wt = ob is not None and ob.endswith('w')
    for grp in ['A', 'B']:
        a = gt[gt.current_group == grp]; b = gv.current_group == grp
        m = lgb.LGBMRegressor(n_estimators=400, learning_rate=0.03, num_leaves=31, min_child_samples=50, subsample=0.8,
                              subsample_freq=1, colsample_bytree=0.8, objective=obj, verbose=-1, n_jobs=10)
        m.fit(a[feats], a.cf, sample_weight=(a.w / a.w.mean()) if wt else None)
        gv.loc[b, 'p'] = np.clip(m.predict(gv.loc[b, feats]), 0, None) * gv.loc[b, 'capacity_kw'].values
    # build group series in same format (night actuals from night frame)
    nz = night.groupby(['ts', 'current_group'], observed=True).agg(y=('energy', 'sum'), w=('w', 'first')).reset_index(); nz['p'] = 0.0
    d = pd.concat([gv[['ts', 'current_group', 'energy', 'p', 'w']].rename(columns={'energy': 'y'}), nz[['ts', 'current_group', 'y', 'p', 'w']]])
    a = d.groupby(['ts', 'current_group'], observed=True).agg(y=('y', 'sum'), p=('p', 'sum'), w=('w', 'first')).unstack('current_group')
    a.columns = [f'{x}_{y}' for x, y in a.columns]; a = a.fillna(0.0); a['w'] = a['w_A'].where(a['w_A'] > 0, a['w_B'])
    m = metrics(a, cap); m['name'] = 'E4_direct'; m['model'] = f'direct group-level {obj}{" w" if wt else ""}'
    json.dump(m, open(OUT + 'metrics_E4_direct.json', 'w'), indent=1); a.to_parquet(MV + 'group_E4_direct.parquet')
    log('E4_direct', {k: round(v, 3) if isinstance(v, float) else v for k, v in m.items()})
    # E4 blend: 0.5 direct + 0.5 bottom-up best
    bb = best_of([n for n in pooled_exps() if n != 'E2_avg'] + ['E2_avg', 'E0_site', 'E7_seed3', 'E7_mix', 'E7_mix_site10', 'E7_mix_site25'])
    g = load_group(bb)
    for wgt in (0.3, 0.5, 0.7):
        c = g.copy(); c['p_A'] = (1 - wgt) * g.p_A + wgt * a.p_A.reindex(g.index).fillna(0); c['p_B'] = (1 - wgt) * g.p_B + wgt * a.p_B.reindex(g.index).fillna(0)
        m = metrics(c, cap); m['name'] = f'E4_blend{int(wgt*100)}'; m['model'] = f'{1-wgt:.1f}*{bb} + {wgt:.1f}*E4_direct'
        json.dump(m, open(OUT + f"metrics_{m['name']}.json", 'w'), indent=1); c.to_parquet(MV + f"group_{m['name']}.parquet")
        log(m['name'], round(m['W_ref']), round(m['W_ref_pct'], 3))


# ----------------------------------------------------------------------------- E5 calibration
def wmedian(x, w):
    o = np.argsort(x); x, w = x[o], w[o]; c = np.cumsum(w); return x[np.searchsorted(c, 0.5 * c[-1])]


def e5():
    E = pooled_exps(); cands = [n for n in E] + ['E2_avg', 'E0_site', 'E4_blend30', 'E4_blend50']
    rows = []
    for bb in [best_of(cands), 'E0_site']:
        g = load_group(bb); g['hour'] = g.index.hour
        h1, h2 = g[g.index <= TH], g[g.index > TH]
        st = pd.read_csv(MV + 'static.csv', index_col=0); cap = st.groupby('group').capacity_kw.sum().to_dict()
        base = metrics(h2, cap); fac = {}
        for grp in ['A', 'B']:
            for h, d in h1.groupby('hour'):
                msk = d[f'p_{grp}'] > 1
                fac[(grp, h)] = wmedian((d[f'y_{grp}'] / d[f'p_{grp}'])[msk].values, (d.w * d[f'p_{grp}'])[msk].values) if msk.sum() > 20 else 1.0
            msk = h1[f'p_{grp}'] > 1
            fac[(grp, -1)] = wmedian((h1[f'y_{grp}'] / h1[f'p_{grp}'])[msk].values, (h1.w * h1[f'p_{grp}'])[msk].values)
        c = h2.copy()
        for grp in ['A', 'B']:
            c[f'p_{grp}'] = h2[f'p_{grp}'] * h2.hour.map(lambda h: fac[(grp, h)]).values
        mh = metrics(c, cap)
        c2 = h2.copy()
        for grp in ['A', 'B']:
            c2[f'p_{grp}'] = h2[f'p_{grp}'] * fac[(grp, -1)]
        mg = metrics(c2, cap)
        # also in-sample (first half) for reference
        c3 = h1.copy()
        for grp in ['A', 'B']:
            c3[f'p_{grp}'] = h1[f'p_{grp}'] * h1.hour.map(lambda h: fac[(grp, h)]).values
        rows += [dict(base=bb, variant='none (2nd half)', **base), dict(base=bb, variant='global factor (2nd half)', **mg),
                 dict(base=bb, variant='hourly factor (2nd half)', **mh), dict(base=bb, variant='none (1st half)', **metrics(h1, cap)),
                 dict(base=bb, variant='hourly factor (1st half, in-sample)', **metrics(c3, cap))]
        pd.Series({f'{k[0]}_h{k[1]}': v for k, v in fac.items()}).to_csv(OUT + f'E5_factors_{bb}.csv')
        log(bb, 'E5 base', round(base['W_ref']), 'hourly', round(mh['W_ref']), 'global', round(mg['W_ref']), 'factors A', {h: round(fac[('A', h)], 3) for h in range(6, 20)})
    pd.DataFrame(rows).to_csv(OUT + 'E5_calibration.csv', index=False)


# ----------------------------------------------------------------------------- report tables & figures
def report():
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    ms = []
    for f in sorted(os.listdir(OUT)):
        if f.startswith('metrics_') and f.endswith('.json'):
            m = json.load(open(OUT + f)); m['name'] = f[8:-5]; ms.append(m)
    R = pd.DataFrame(ms); order = ['E0_site_raw', 'E0_site', 'E0_pool', 'E1_l1', 'E1_l1w', 'E1_l2w', 'E2_r10', 'E2_avg', 'E2_both', 'E3_phys', 'E3_phys_both', 'E3_site',
                                   'E3_site_nolatlon', 'E3_r30', 'E3_r30f', 'E3_r365f', 'E3_site_r365f', 'E3_site_both', 'E3_site_nophys', 'E3_r365f_nophys', 'E1_l1w_s2', 'E1_l1w_s3', 'E6_trees800', 'E6_lr03_t800', 'E6_leaves255', 'E6_leaves63', 'E7_seed3', 'E7_mix', 'E7_mix_site10', 'E7_mix_site25', 'E4_direct', 'E4_blend30', 'E4_blend50', 'E4_blend70']
    R['o'] = R.name.map({n: i for i, n in enumerate(order)}).fillna(99); R = R.sort_values('o').drop(columns='o')
    e0 = R.loc[R.name == 'E0_site', 'W_ref'].iloc[0]
    R['gain_vs_E0_pct'] = 100 * (1 - R.W_ref / e0)
    if 'W_ref_seen' in R: R['gain_seen_vs_E0_pct'] = 100 * (1 - R.W_ref_seen / R.loc[R.name == 'E0_site', 'W_ref_seen'].iloc[0])
    cols = ['name', 'model', 'rnd', 'n_feats', 'W_ref', 'W_ref_pct', 'W_pool', 'W_pool_pct', 'MAE_G1', 'MAE_G2', 'nMAE_G1', 'nMAE_G2', 'bias_G1', 'bias_G2', 'gain_vs_E0_pct', 'W_ref_seen', 'W_ref_pct_seen', 'W_pool_pct_seen', 'nMAE_G1_seen', 'nMAE_G2_seen', 'gain_seen_vs_E0_pct', 'fit_sec']
    R = R[[c for c in cols if c in R.columns]]
    R.to_csv(OUT + 'results_table.csv', index=False)
    print(R.round(3).to_string())
    # fig1 results
    fig, ax = plt.subplots(figsize=(10, 5)); ax.barh(R.name, R.W_ref_pct, color=['tab:red' if n == 'E0_site' else 'tab:blue' for n in R.name])
    ax.set_xlabel('W_ref / sum(w*actual)  [%]  (lower is better)'); ax.set_title('Validation 2024-06..2025-05: weighted abs error, reference split'); ax.invert_yaxis()
    for i, v in enumerate(R.W_ref_pct): ax.text(v, i, f' {v:.2f}', va='center', fontsize=8)
    fig.tight_layout(); fig.savefig(OUT + 'fig_results_W_ref.png', dpi=130); plt.close(fig)
    best = R.loc[~R.name.isin(['E0_site'] + list(NOT_DEPLOYABLE)) & ~R.name.str.startswith('E4_blend')].sort_values('W_ref').name.iloc[0]
    g0 = load_group('E0_site'); gb = load_group(best)
    def contrib(g):
        return g.w * ((g.p_A - g.y_A).abs() + (g.p_B - g.y_B).abs())
    # fig2 hourly profile
    fig, ax = plt.subplots(1, 2, figsize=(12, 4))
    h0 = contrib(g0).groupby(g0.index.hour).sum() / 1e6; hb = contrib(gb).groupby(gb.index.hour).sum() / 1e6
    ax[0].plot(h0.index, h0.values, 'o-', label='E0_site'); ax[0].plot(hb.index, hb.values, 's-', label=best); ax[0].set_xlabel('hour (KST, right-closed)'); ax[0].set_ylabel('W contribution [M KRW-kWh]'); ax[0].legend(); ax[0].set_title('W by hour of day')
    m0 = contrib(g0).groupby(g0.index.to_period('M')).sum() / 1e6; mb = contrib(gb).groupby(gb.index.to_period('M')).sum() / 1e6
    ax[1].plot(m0.index.astype(str), m0.values, 'o-', label='E0_site'); ax[1].plot(mb.index.astype(str), mb.values, 's-', label=best); ax[1].tick_params(axis='x', rotation=60); ax[1].legend(); ax[1].set_title('W by month')
    fig.tight_layout(); fig.savefig(OUT + 'fig_W_by_hour_month.png', dpi=130); plt.close(fig)
    pd.DataFrame({'E0_site': h0, best: hb}).to_csv(OUT + 'W_by_hour.csv'); pd.DataFrame({'E0_site': m0, best: mb}).to_csv(OUT + 'W_by_month.csv')
    # fig3 importance
    fib = best if os.path.exists(OUT + f'feat_importance_{best}.csv') else 'E1_l1w'
    fi = pd.read_csv(OUT + f'feat_importance_{fib}.csv').head(20)
    fig, ax = plt.subplots(figsize=(8, 6)); ax.barh(fi.feature, fi.gain_share_pct); ax.invert_yaxis(); ax.set_xlabel('gain share [%]'); ax.set_title(f'Feature importance ({fib})')
    fig.tight_layout(); fig.savefig(OUT + 'fig_feat_importance.png', dpi=130); plt.close(fig)
    # fig4 sample week + scatter
    wk = gb.loc['2024-08-05':'2024-08-12']
    fig, ax = plt.subplots(2, 1, figsize=(12, 7))
    ax[0].plot(wk.index, wk.y_A + wk.y_B, 'k-', label='actual total'); ax[0].plot(wk.index, wk.p_A + wk.p_B, 'r--', label=f'pred {best}')
    w0 = g0.loc['2024-08-05':'2024-08-12']; ax[0].plot(w0.index, w0.p_A + w0.p_B, 'b:', label='pred E0_site'); ax[0].legend(); ax[0].set_ylabel('kWh/h'); ax[0].set_title('Sample week Aug 2024 (total of G1+G2)')
    ax[1].scatter(gb.y_A + gb.y_B, gb.p_A + gb.p_B, s=2, alpha=0.3); mx = (gb.y_A + gb.y_B).max(); ax[1].plot([0, mx], [0, mx], 'k-'); ax[1].set_xlabel('actual total kWh'); ax[1].set_ylabel('pred'); ax[1].set_title('Hourly total: pred vs actual')
    fig.tight_layout(); fig.savefig(OUT + 'fig_week_scatter.png', dpi=130); plt.close(fig)
    # fig5 E5 factors
    e5f = [x for x in os.listdir(OUT) if x.startswith('E5_factors_') and 'E0_site' not in x]
    if e5f:
        f = pd.read_csv(OUT + e5f[0], index_col=0).iloc[:, 0]; best5 = e5f[0][11:-4]
        fig, ax = plt.subplots(figsize=(8, 4))
        for grp in ['A', 'B']:
            s = f[[i for i in f.index if i.startswith(grp + '_h') and not i.endswith('h-1')]]; ax.plot([int(i.split('h')[1]) for i in s.index], s.values, 'o-', label=f'G{1 if grp == "A" else 2}')
        ax.axhline(1, color='k', lw=0.5); ax.set_xlabel('hour'); ax.set_ylabel('multiplicative factor'); ax.legend(); ax.set_title(f'E5 hourly calibration factors fitted on 2024-06..11 ({best5})')
        fig.tight_layout(); fig.savefig(OUT + 'fig_E5_factors.png', dpi=130); plt.close(fig)
    # per-site error table for best
    if os.path.exists(CACHE + f'val_pred_site_{best}.parquet'):
        s = pd.read_parquet(CACHE + f'val_pred_site_{best}.parquet')
        if s.ts.dt.tz is None: s['ts'] = s.ts.dt.tz_localize('UTC').dt.tz_convert(TZ)
        s = s.merge(pd.read_parquet(CACHE + 'smp_all.parquet')[['ts', 'smp', 'k']], on='ts')
        s['w'] = s.smp * s.k; s['ae'] = (s.pred - s.y).abs()
        st = pd.read_csv(MV + 'static.csv', index_col=0)
        ps = s.groupby('site_id').apply(lambda d: pd.Series({'W_site': (d.w * d.ae).sum(), 'Rw_site': (d.w * d.y).sum(), 'MAE': d.ae.mean(), 'bias': (d.pred - d.y).mean(), 'n': len(d)}), include_groups=False)
        ps = ps.join(st); ps['W_pct'] = 100 * ps.W_site / ps.Rw_site; ps['nMAE_cap_pct'] = 100 * ps.MAE / ps.capacity_kw
        hist = pd.read_csv(OUT + 'mv_site_history.csv', index_col=0); ps['first_obs'] = hist['first'].str[:10]; ps['seen_in_train'] = pd.to_datetime(hist['first'].str[:10]) <= '2024-06-01'
        print('W share unseen sites %:', round(100 * ps.loc[~ps.seen_in_train, 'W_site'].sum() / ps.W_site.sum(), 2), ' W_pct seen/unseen:', round(100 * ps.loc[ps.seen_in_train, 'W_site'].sum() / ps.loc[ps.seen_in_train, 'Rw_site'].sum(), 2), round(100 * ps.loc[~ps.seen_in_train, 'W_site'].sum() / ps.loc[~ps.seen_in_train, 'Rw_site'].sum(), 2))
        ps.sort_values('W_pct', ascending=False).to_csv(OUT + f'per_site_val_error_{best}.csv')
        print(ps.sort_values('W_pct', ascending=False).head(15).round(2).to_string())
    print('BEST', best)


if __name__ == '__main__':
    st = sys.argv[1]
    if st == 'prep': prep()
    elif st == 'e0': e0()
    elif st == 'e0fb': e0fb()
    elif st == 'savesite': savesite(sys.argv[2:])
    elif st == 'ens': ens(sys.argv[2:])
    elif st == 'pool': run_pool(sys.argv[2:])
    elif st == 'e4': e4()
    elif st == 'e5': e5()
    elif st == 'report': report()
