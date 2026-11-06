"""OIBC 2026 submission pipeline.  Usage:  python make_submission.py [features|val|compose|predict|check|all]

Recipe (validated 2026-10-26, see ../analysis_outputs/reports/ANALYSIS_MEMO.md):
  * pooled LightGBM on capacity factor, objective L1 (unweighted), round-17 forecasts of providers A+B
  * 5 seeds averaged, + 10% per-site L2 models  (= bottom-up)
  * blended 50:50 with a group-level direct L1 model trained on the final composition
  * composition = twin pairs by validation-error correlation, one twin per group (interleaved), each group in [20,000, 22,655.4] kW
  * night = sun below horizon at BOTH ends of the hour (twilight hours are modelled, not zeroed)
  * missing round-17 forecast rows filled from round 10; no post-processing (no scaling, no zeroing, no caps)
Every stage caches to ./cache and is skipped when its output exists; delete the file to redo it.
"""
import sys, os, time, json
import numpy as np, pandas as pd, lightgbm as lgb
from joblib import Parallel, delayed

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(ROOT), 'handover 2', '01_participant_dataset')
CACHE = os.path.join(ROOT, 'cache'); os.makedirs(CACHE, exist_ok=True)
TZ = 'Asia/Seoul'
T1 = pd.Timestamp('2024-06-01 00:00', tz=TZ)          # validation year: T1 < ts <= T2
T2 = pd.Timestamp('2025-06-01 00:00', tz=TZ)
LO, HI = 20000.0, 22655.4                             # per-group capacity window (kW)
A6 = ['wa_cloud', 'wa_temp', 'wa_humidity', 'wa_ground_press', 'wa_wind_speed', 'wa_rain']
B9 = ['wb_cloud', 'wb_uv_idx', 'wb_temp', 'wb_rel_hum', 'wb_dew_point', 'wb_vis', 'wb_ceiling', 'wb_precip_prob', 'wb_total_liq']
WX = A6 + B9
GEO = ['elev', 'azim', 'cosz', 'toa', 'sunfrac', 'doy_sin', 'doy_cos', 'hour']
PHYS = ['csa', 'csb', 'toaa', 'toab', 'uvtoa', 'cdis']
FEATS = WX + GEO + ['capacity_kw', 'lat', 'lon']       # site-level models
GFEATS = WX + GEO + PHYS                              # group-level direct model
SEEDS = [0, 1, 2, 3, 4]
SITE_W, DIRECT_W = 0.10, 0.50                         # validated blend weights
MIN_SITE_ROWS = 1000                                  # per-site model needs this many daytime rows
POOL = dict(n_estimators=400, learning_rate=0.06, num_leaves=127, min_child_samples=200, subsample=0.8, subsample_freq=1,
            colsample_bytree=0.8, objective='regression_l1', verbose=-1, n_jobs=12)
SITE = dict(n_estimators=600, learning_rate=0.06, num_leaves=127, min_child_samples=200, subsample=0.8, subsample_freq=1,
            colsample_bytree=0.8, verbose=-1, n_jobs=2)
GROUP = dict(n_estimators=400, learning_rate=0.03, num_leaves=31, min_child_samples=50, subsample=0.8, subsample_freq=1,
             colsample_bytree=0.8, objective='regression_l1', verbose=-1, n_jobs=12)

SITES = pd.read_csv(os.path.join(DATA, 'sites.csv'))
IDS = SITES.site_id.tolist(); N = len(IDS); CAP = SITES.capacity_kw.to_numpy(np.float64)
T0 = time.time()


def log(*a):
    print(f'[{time.time() - T0:7.1f}s]', *a, flush=True)


def to_us(s):
    return pd.to_datetime(s, utc=True).dt.tz_convert(TZ).astype(f'datetime64[us, {TZ}]')


# ----------------------------------------------------------------------------- features
def solar(t, lat, lon):
    """NOAA approximation at instant t (tz-aware DatetimeIndex). Returns elevation, azimuth (deg), cos zenith."""
    doy = t.day_of_year.to_numpy(); hour = t.hour.to_numpy() + t.minute.to_numpy() / 60.0
    g = 2 * np.pi / 365.0 * (doy - 1 + (hour - 12) / 24.0)
    eqt = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g) - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g))
    decl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g) + 0.000907 * np.sin(2 * g)
            - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    ha = np.radians((hour * 60 + eqt + 4 * (lon - 135.0)) / 4.0 - 180.0); la = np.radians(lat)
    cosz = np.clip(np.sin(la) * np.sin(decl) + np.cos(la) * np.cos(decl) * np.cos(ha), -1, 1)
    elev = 90.0 - np.degrees(np.arccos(cosz))
    az = np.degrees(np.arctan2(-np.sin(ha), np.tan(decl) * np.cos(la) - np.sin(la) * np.cos(ha))) % 360
    return elev.astype('float32'), az.astype('float32'), cosz.astype('float32')


def add_geometry(d):
    ts = pd.DatetimeIndex(d.ts); lat = d.lat.to_numpy(); lon = d.lon.to_numpy()
    lit = np.zeros(len(d), np.float32)
    for m in (60, 50, 40, 30, 20, 10, 0):                      # ts is right-closed: hour spans ts-60min .. ts
        e, az, cz = solar(ts - pd.Timedelta(minutes=m), lat, lon)
        lit += e > 0
        if m == 60: e_start = e
        if m == 30: d['elev'], d['azim'], d['cosz'] = e, az, cz
        if m == 0: e_end = e
    d['sunfrac'] = lit / 7
    d['night'] = (e_start <= 0) & (e_end <= 0)
    doy = ts.day_of_year.to_numpy()
    d['toa'] = (1361 * (1 + 0.033 * np.cos(2 * np.pi * doy / 365.0)) * np.clip(d.cosz, 0, None)).astype('float32')
    d['doy_sin'] = np.sin(2 * np.pi * doy / 365.25).astype('float32'); d['doy_cos'] = np.cos(2 * np.pi * doy / 365.25).astype('float32')
    d['hour'] = ts.hour.to_numpy().astype('float32')
    ca = (1 - d.wa_cloud / 100).clip(0, 1); cb = (1 - d.wb_cloud / 100).clip(0, 1)
    d['csa'] = d.cosz * ca; d['csb'] = d.cosz * cb; d['toaa'] = d.toa * ca; d['toab'] = d.toa * cb
    d['uvtoa'] = d.wb_uv_idx * d.toa / 1000; d['cdis'] = (d.wa_cloud - d.wb_cloud).abs()
    for c in WX + PHYS:
        d[c] = d[c].astype('float32')
    return d


def load_fc(split, rnd):
    fa = pd.read_parquet(os.path.join(DATA, split, 'forecast_wa.parquet'), columns=['wa_station', 'round', 'ts'] + A6)
    fb = pd.read_parquet(os.path.join(DATA, split, 'forecast_wb.parquet'), columns=['wb_station', 'round', 'ts'] + B9)
    fa = fa[fa['round'] == rnd].drop(columns='round'); fb = fb[fb['round'] == rnd].drop(columns='round')
    fa['ts'] = to_us(fa.ts); fb['ts'] = to_us(fb.ts)
    return fa.drop_duplicates(['wa_station', 'ts']), fb.drop_duplicates(['wb_station', 'ts'])


def panel(base, split):
    d = base.merge(SITES[['site_id', 'capacity_kw', 'lat', 'lon', 'wa_station', 'wb_station']], on='site_id', how='left')
    for rnd in (17, 10):                                        # round 17 first; round 10 only fills holes
        fa, fb = load_fc(split, rnd)
        if rnd == 17:
            d = d.merge(fa, on=['wa_station', 'ts'], how='left').merge(fb, on=['wb_station', 'ts'], how='left')
            continue
        for key, f, cols in (('wa_station', fa, A6), ('wb_station', fb, B9)):
            miss = d[cols].isna().any(axis=1).to_numpy()
            if miss.any():
                fill = d.loc[miss, [key, 'ts']].merge(f, on=[key, 'ts'], how='left')
                d.loc[miss, cols] = np.where(d.loc[miss, cols].isna(), fill[cols].to_numpy(), d.loc[miss, cols])
                log(f'{split}: filled {int(miss.sum())} round-17 holes in {key} from round 10 (still missing: {int(d.loc[miss, cols].isna().any(axis=1).sum())})')
    return add_geometry(d)


def features():
    if os.path.exists(os.path.join(CACHE, 'feat_test.parquet')):
        log('features cached'); return
    smp_tr = pd.read_csv(os.path.join(DATA, 'train', 'smp.csv')); smp_tr['ts'] = to_us(smp_tr.ts)
    smp_tr['k'] = np.where(smp_tr.ts.dt.hour.between(11, 15), 3, 1)
    smp_te = pd.read_csv(os.path.join(DATA, 'smp.csv')); smp_te['ts'] = to_us(smp_te.ts)
    smp = pd.concat([smp_tr, smp_te], ignore_index=True); smp['w'] = (smp.smp * smp.k).astype('float32')
    smp[['ts', 'smp', 'k', 'w']].to_parquet(os.path.join(CACHE, 'smp.parquet'), index=False)

    gen = pd.read_parquet(os.path.join(DATA, 'train', 'generation.parquet')); gen['ts'] = to_us(gen.ts)
    gen['energy'] = gen.energy.astype('float32')
    d = panel(gen, 'train').merge(smp[['ts', 'w']], on='ts', how='left')
    d['cf'] = (d.energy / d.capacity_kw).clip(0, 1.2).astype('float32')
    d.to_parquet(os.path.join(CACHE, 'feat_train.parquet'), index=False)
    log('feat_train', d.shape, 'night rows', int(d.night.sum()), 'twilight energy kept (kWh)',
        round(float(d.loc[~d.night & (d.elev <= 0), 'energy'].sum())))
    del d, gen

    grid = pd.MultiIndex.from_product([IDS, smp_te.ts], names=['site_id', 'ts']).to_frame(index=False)
    d = panel(grid, 'test')
    assert len(d) == N * len(smp_te) and d[WX].isna().mean().max() < 0.001, d[WX].isna().sum()
    d.to_parquet(os.path.join(CACHE, 'feat_test.parquet'), index=False)
    log('feat_test', d.shape, 'remaining NaN cells', int(d[WX].isna().sum().sum()))


# ----------------------------------------------------------------------------- models
def fit_pooled(tr, seed):
    return lgb.LGBMRegressor(**POOL, random_state=seed).fit(tr[FEATS], tr.cf)


def fit_site(tr):
    """Per-site L2 models (the validated 10% bottom-up member). Sites with little history fall back to pooled."""
    idx = tr.groupby('site_id').indices

    def one(s):
        d = tr.iloc[idx[s]]
        return s, lgb.LGBMRegressor(**SITE).fit(d[FEATS], d.cf)
    sites = [s for s in idx if len(idx[s]) >= MIN_SITE_ROWS]
    return dict(Parallel(n_jobs=6)(delayed(one)(s) for s in sites))


def predict_bottom_up(pools, site_models, X):
    """kWh per row: 0.9 * mean of pooled seeds + 0.1 * per-site model (pooled mean where no site model)."""
    pool = np.mean([m.predict(X[FEATS]) for m in pools], axis=0)
    site = pool.copy(); idx = X.groupby('site_id').indices
    for s, m in site_models.items():
        if s in idx:
            site[idx[s]] = m.predict(X.iloc[idx[s]][FEATS])
    cf = (1 - SITE_W) * pool + SITE_W * site
    return np.clip(cf, 0, None) * X.capacity_kw.to_numpy()


def group_frame(d, assign):
    """Capacity-weighted (ts, group) rows for the direct model. cf = sum energy / sum capacity of reporting sites."""
    g = d[['ts', 'capacity_kw']].copy(); g['grp'] = d.site_id.map(assign).to_numpy()
    for f in GFEATS:
        g[f] = d[f].to_numpy() * d.capacity_kw.to_numpy()
    if 'energy' in d:
        g['energy'] = d.energy.to_numpy()
    a = g.groupby(['ts', 'grp'], sort=True).sum()
    for f in GFEATS:
        a[f] = a[f] / a.capacity_kw
    if 'energy' in a:
        a['cf'] = (a.energy / a.capacity_kw).clip(0, 1.2)
    return a.reset_index()


def fit_direct(tr, assign):
    gt = group_frame(tr, assign)
    return {grp: lgb.LGBMRegressor(**GROUP).fit(a[GFEATS], a.cf) for grp, a in gt.groupby('grp')}


def predict_direct(models, X, assign):
    gx = group_frame(X, assign); gx['p'] = 0.0
    for grp, m in models.items():
        b = gx.grp == grp
        gx.loc[b, 'p'] = np.clip(m.predict(gx.loc[b, GFEATS]), 0, None) * gx.loc[b, 'capacity_kw'].to_numpy()
    return gx[['ts', 'grp', 'p']]


def blend(site_pred, direct, assign):
    """site_pred: (site_id, ts, p) kWh with night already 0 -> (ts, grp, forecast_kwh) 50:50 with the direct model."""
    bu = site_pred.assign(grp=site_pred.site_id.map(assign)).groupby(['ts', 'grp'], as_index=False).p.sum()
    m = bu.merge(direct, on=['ts', 'grp'], how='left', suffixes=('_bu', '_dir'))
    m['p_dir'] = m.p_dir.fillna(0.0)                 # hours with no daylight row anywhere -> direct model has no row -> 0
    m['forecast_kwh'] = (1 - DIRECT_W) * m.p_bu + DIRECT_W * m.p_dir
    return m


def score(site_pred, assign, label):
    """Official penalty on validation rows. site_pred: site_id, ts, y, p (all hours; night p=0). Returns W% of sum(w*y)."""
    smp = pd.read_parquet(os.path.join(CACHE, 'smp.parquet'))
    d = site_pred.assign(grp=site_pred.site_id.map(assign)).groupby(['ts', 'grp']).agg(y=('y', 'sum'), p=('p', 'sum')).unstack('grp').fillna(0)
    d.columns = [f'{a}_{b}' for a, b in d.columns]
    d['w'] = smp.set_index('ts').w.reindex(d.index).to_numpy()
    e1 = d.p_G1 - d.y_G1; e2 = d.p_G2 - d.y_G2
    Rw = float((d.w * (d.y_G1 + d.y_G2)).sum())
    r = dict(W_pct=100 * float((d.w * (e1.abs() + e2.abs())).sum()) / Rw, W_pool_pct=100 * float((d.w * (e1 + e2).abs()).sum()) / Rw,
             bias_G1=float(e1.mean()), bias_G2=float(e2.mean()), hours=int(len(d)))
    log(label, {k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()})
    return r


def ref_assign():
    return dict(zip(IDS, np.where(SITES.current_group == 'A', 'G1', 'G2')))


# ----------------------------------------------------------------------------- stage: validation
def val():
    out = os.path.join(CACHE, 'val_pred_site.parquet')
    if os.path.exists(out):
        log('val cached'); return
    d = pd.read_parquet(os.path.join(CACHE, 'feat_train.parquet'))
    tr = d[(d.ts <= T1) & ~d.night]; va = d[(d.ts > T1) & (d.ts <= T2)]
    log('val: train rows', len(tr), 'val rows', len(va))
    pools = [fit_pooled(tr, s) for s in SEEDS]; log('pooled seeds done')
    sm = fit_site(tr); log('site models', len(sm))
    vd = va[~va.night]
    p = np.zeros(len(va)); p[~va.night.to_numpy()] = predict_bottom_up(pools, sm, vd)
    sp = pd.DataFrame({'site_id': va.site_id.to_numpy(), 'ts': va.ts.to_numpy(), 'y': va.energy.to_numpy(), 'p': p.astype('float32')})
    sp.to_parquet(out, index=False)
    r = score(sp, ref_assign(), 'VAL bottom-up, reference split')
    json.dump(r, open(os.path.join(CACHE, 'val_bottom_up.json'), 'w'), indent=1)


# ----------------------------------------------------------------------------- stage: composition
def repair(a):
    """move sites from the heavy group to the light one until both groups are inside [LO, HI]."""
    a = a.copy(); half = CAP.sum() / 2
    for _ in range(N):
        c1 = CAP @ a
        if LO <= c1 <= HI: return a
        heavy = 1 if c1 > HI else 0
        idx = np.where(a == heavy)[0]; cand = idx[CAP[idx] <= 2 * abs(c1 - half)]
        j = cand[np.argmax(CAP[cand])] if len(cand) else idx[np.argmin(CAP[idx])]
        a[j] = 1 - heavy
    raise RuntimeError('no feasible repair')


def twin_split(E):
    """E: hours x sites error matrix. Greedy max-correlation matching, twins put in different groups, capacity balanced."""
    R = np.corrcoef(E.T); R[~np.isfinite(R)] = 0; np.fill_diagonal(R, -np.inf)
    iu = np.triu_indices(N, 1); order = np.argsort(-R[iu]); used = np.zeros(N, bool); pairs = []
    for k in order:
        i, j = iu[0][k], iu[1][k]
        if not used[i] and not used[j]:
            used[i] = used[j] = True; pairs.append((i, j))
    rest = sorted(np.where(~used)[0], key=lambda i: -CAP[i])
    pairs += [(rest[i], rest[i + 1]) for i in range(0, len(rest) - 1, 2)]
    pairs.sort(key=lambda p: -(CAP[p[0]] + CAP[p[1]]))
    a = np.zeros(N, np.int8); c = [0.0, 0.0]
    for i, j in pairs:
        big, small = (i, j) if CAP[i] >= CAP[j] else (j, i)
        light = int(np.argmin(c)); a[big] = light; a[small] = 1 - light
        c[light] += CAP[big]; c[1 - light] += CAP[small]
    if len(rest) % 2:
        a[rest[-1]] = int(np.argmin(c))
    return repair(a), pairs


def compose():
    out = os.path.join(ROOT, 'composition.csv')
    if os.path.exists(out):
        log('composition cached'); return
    sp = pd.read_parquet(os.path.join(CACHE, 'val_pred_site.parquet'))
    smp = pd.read_parquet(os.path.join(CACHE, 'smp.parquet')).set_index('ts').w
    E = sp.assign(e=sp.p - sp.y).pivot(index='ts', columns='site_id', values='e').reindex(columns=IDS).fillna(0.0)
    E = E[(E.abs().sum(axis=1) > 0) & (smp.reindex(E.index).fillna(0) > 0)]
    a, pairs = twin_split(E.to_numpy(np.float64))
    assign = {s: ('G1' if a[i] == 1 else 'G2') for i, s in enumerate(IDS)}
    cap = {g: float(CAP[[i for i, s in enumerate(IDS) if assign[s] == g]].sum()) for g in ('G1', 'G2')}
    assert all(LO <= v <= HI for v in cap.values()), cap
    pd.DataFrame({'site_id': IDS, 'group': [assign[s] for s in IDS]}).to_csv(out, index=False)
    log('composition saved', cap, 'pairs', len(pairs))
    for s in ('PV004', 'PV011', 'PV188', 'PV189', 'PV215', 'PV143', 'PV240', 'PV059', 'PV246'):
        log('  ', s, assign[s])
    ref = ref_assign()
    r_ref = score(sp, ref, 'VAL bottom-up, reference split'); r_twin = score(sp, assign, 'VAL bottom-up, twin split')
    # the exact submission recipe on the validation year: direct model trained on the twin composition, blended 50:50
    d = pd.read_parquet(os.path.join(CACHE, 'feat_train.parquet'))
    tr = d[(d.ts <= T1) & ~d.night]; va = d[(d.ts > T1) & (d.ts <= T2) & ~d.night]
    direct = predict_direct(fit_direct(tr, assign), va, assign)
    m = blend(sp[['site_id', 'ts', 'p']], direct, assign)
    full = sp.assign(grp=sp.site_id.map(assign)).groupby(['ts', 'grp'], as_index=False).y.sum().merge(m, on=['ts', 'grp'])
    sm = smp.reindex(full.ts).to_numpy(); e = full.forecast_kwh - full.y
    Wf = 100 * float((sm * e.abs()).sum()) / float((sm * full.y).sum())
    Wd = 100 * float((sm * (full.p_dir - full.y).abs()).sum()) / float((sm * full.y).sum())
    log(f'VAL final recipe (bottom-up 50% + direct 50%, twin split): W% = {Wf:.3f}   (direct alone {Wd:.3f})')
    json.dump(dict(reference=r_ref, twin=r_twin, direct_pct=Wd, final_blend_pct=Wf, cap=cap),
              open(os.path.join(CACHE, 'val_summary.json'), 'w'), indent=1)


# ----------------------------------------------------------------------------- stage: full training + test prediction
def predict():
    out = os.path.join(ROOT, 'forecast.csv')
    if os.path.exists(out):
        log('forecast cached'); return
    assign = pd.read_csv(os.path.join(ROOT, 'composition.csv')).set_index('site_id').group.to_dict()
    d = pd.read_parquet(os.path.join(CACHE, 'feat_train.parquet')); tr = d[~d.night]; del d
    X = pd.read_parquet(os.path.join(CACHE, 'feat_test.parquet'))
    log('full train rows', len(tr), 'test rows', len(X))
    pools = [fit_pooled(tr, s) for s in SEEDS]; log('pooled seeds done')
    sm = fit_site(tr); log('site models', len(sm))
    direct_models = fit_direct(tr, assign); log('direct models done')
    del tr
    day = ~X.night.to_numpy()
    p = np.zeros(len(X)); p[day] = predict_bottom_up(pools, sm, X[day])
    sp = pd.DataFrame({'site_id': X.site_id.to_numpy(), 'ts': X.ts.to_numpy(), 'p': p.astype('float32')})
    sp.to_parquet(os.path.join(CACHE, 'test_pred_site.parquet'), index=False)
    direct = predict_direct(direct_models, X[day], assign)
    m = blend(sp, direct, assign)
    night_hours = set(X.loc[~day, 'ts']) - set(X.loc[day, 'ts'])     # hours where no site sees the sun -> 0
    m.loc[m.ts.isin(night_hours), 'forecast_kwh'] = 0.0
    m['forecast_kwh'] = m.forecast_kwh.clip(lower=0).round(3)
    m = m.sort_values(['grp', 'ts'])
    f = pd.DataFrame({'group': m.grp, 'ts': m.ts.dt.strftime('%Y-%m-%d %H:%M:%S') + '+09:00', 'forecast_kwh': m.forecast_kwh})
    f.to_csv(out, index=False)
    log('forecast saved', len(f), 'rows; annual GWh', round(f.forecast_kwh.sum() / 1e6, 2),
        'bottom-up vs direct annual ratio', round(float(m.p_bu.sum() / m.p_dir.sum()), 4))


# ----------------------------------------------------------------------------- stage: format checks
def check():
    c = pd.read_csv(os.path.join(ROOT, 'composition.csv')); f = pd.read_csv(os.path.join(ROOT, 'forecast.csv'))
    smp = pd.read_csv(os.path.join(DATA, 'smp.csv'))
    assert list(c.columns) == ['site_id', 'group'] and len(c) == N and sorted(c.site_id) == sorted(IDS), 'composition rows'
    assert set(c.group) == {'G1', 'G2'}, 'composition groups'
    cap = c.merge(SITES, on='site_id').groupby('group').capacity_kw.sum()
    assert cap.between(LO, HI).all(), cap
    assert list(f.columns) == ['group', 'ts', 'forecast_kwh'] and len(f) == 2 * len(smp), 'forecast rows'
    for g in ('G1', 'G2'):
        assert list(f.loc[f.group == g, 'ts']) == list(smp.ts), f'{g} timestamps differ from smp.csv'
    assert f.forecast_kwh.notna().all() and (f.forecast_kwh >= 0).all() and np.isfinite(f.forecast_kwh).all(), 'forecast values'
    assert (f.forecast_kwh <= f.group.map(cap)).all(), 'forecast above its group capacity'
    hr = pd.to_datetime(f.ts).dt.hour
    print('composition OK: capacities', cap.round(1).to_dict())
    print('forecast OK: rows', len(f), '| annual GWh', round(f.forecast_kwh.sum() / 1e6, 2), '| share in ts 11-15h',
          round(100 * f.loc[hr.between(11, 15), 'forecast_kwh'].sum() / f.forecast_kwh.sum(), 1), '%',
          '| zero hours', int((f.forecast_kwh == 0).sum()), '| max kWh', round(f.forecast_kwh.max(), 1))
    print(f.groupby([f.group, hr]).forecast_kwh.mean().unstack(0).round(0).T.to_string())


if __name__ == '__main__':
    stage = sys.argv[1] if len(sys.argv) > 1 else 'all'
    steps = dict(features=features, val=val, compose=compose, predict=predict, check=check)
    for name in (list(steps) if stage == 'all' else [stage]):
        log('==', name); steps[name]()
