"""Independent reproduction of the round/provider claim. Stages: skill | r17 | r10 | eval
skill : station-level r17 vs r10 vs 50/50 blend MAE against observed (daytime, 2023-06..2025-05)
r17   : pooled LGBM L1 SMP*k-weighted, 24 feats, round-17 inputs, seeds 0 and 2 -> val preds
r10   : same with round-10 inputs, seed 0 -> val preds
eval  : W_ref% on reference split for r17, r10, 50/50 avg, 2-seed r17 avg, weight grid, k=3 hours
"""
import sys, os, time, gc, json
import numpy as np, pandas as pd, pyarrow as pa, pyarrow.parquet as pq, pyarrow.compute as pc

BASE = 'C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad/'
CACHE, OUT = BASE + 'cache/', BASE + 'analysis/out/'
TZ = 'Asia/Seoul'
T0 = pd.Timestamp('2022-06-01 00:00', tz=TZ); T1 = pd.Timestamp('2024-06-01 00:00', tz=TZ); T2 = pd.Timestamp('2025-06-01 00:00', tz=TZ)
A6 = ['wa_cloud', 'wa_temp', 'wa_humidity', 'wa_ground_press', 'wa_wind_speed', 'wa_rain']
B9 = ['wb_cloud', 'wb_uv_idx', 'wb_temp', 'wb_rel_hum', 'wb_dew_point', 'wb_vis', 'wb_ceiling', 'wb_precip_prob', 'wb_total_liq']
WX = A6 + B9
FEATS = WX + ['elev', 'azim', 'cosz', 'doy_sin', 'doy_cos', 'hour', 'capacity_kw', 'lat', 'lon']
LGB = dict(n_estimators=400, learning_rate=0.06, num_leaves=127, min_child_samples=200, subsample=0.8, subsample_freq=1,
           colsample_bytree=0.8, objective='regression_l1', verbose=-1, n_jobs=10)
LOG = open(OUT + 'verify_round_provider_log.txt', 'a')


def log(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); LOG.write(s + '\n'); LOG.flush()


def rss():
    try:
        import psutil; return f'rss={psutil.Process().memory_info().rss/1e9:.2f}GB'
    except Exception:
        return ''


def read(path, cols, flt):
    t = pq.read_table(path, columns=cols, filters=flt)
    for c in ('site_id', 'wa_station', 'wb_station', 'current_group'):
        if c in t.column_names:
            t = t.set_column(t.schema.get_field_index(c), c, pc.dictionary_encode(t[c]))
    df = t.to_pandas(); del t; gc.collect(); return df


# ------------------------------------------------------------------ skill
def stage_skill():
    TS = pd.Timestamp('2023-06-01 01:00', tz=TZ)
    flt = [('ts', '>=', TS), ('elev', '>', 0)]
    obs = read(CACHE + 'panel_train_obs.parquet', ['ts', 'wa_station', 'wb_station', 'obs_wa_cloud', 'obs_wa_humidity', 'obs_wb_cloud', 'obs_wb_uv_idx'], flt)
    log('obs rows', len(obs), rss())
    oa = obs.drop_duplicates(['wa_station', 'ts'])[['wa_station', 'ts', 'obs_wa_cloud', 'obs_wa_humidity']].copy()
    ob = obs.drop_duplicates(['wb_station', 'ts'])[['wb_station', 'ts', 'obs_wb_cloud', 'obs_wb_uv_idx']].copy()
    del obs; gc.collect()
    fc = {}
    for r in (17, 10):
        f = read(CACHE + f'panel_train_r{r}.parquet', ['ts', 'wa_station', 'wb_station', 'wa_cloud', 'wa_humidity', 'wb_cloud', 'wb_uv_idx'], flt)
        fa = f.drop_duplicates(['wa_station', 'ts'])[['wa_station', 'ts', 'wa_cloud', 'wa_humidity']].rename(columns={'wa_cloud': f'r{r}_wa_cloud', 'wa_humidity': f'r{r}_wa_humidity'})
        fb = f.drop_duplicates(['wb_station', 'ts'])[['wb_station', 'ts', 'wb_cloud', 'wb_uv_idx']].rename(columns={'wb_cloud': f'r{r}_wb_cloud', 'wb_uv_idx': f'r{r}_wb_uv_idx'})
        del f; gc.collect()
        fa['wa_station'] = fa.wa_station.astype(str); fb['wb_station'] = fb.wb_station.astype(str)
        fc[r] = (fa, fb)
    oa['wa_station'] = oa.wa_station.astype(str); ob['wb_station'] = ob.wb_station.astype(str)
    A = oa.merge(fc[17][0], on=['wa_station', 'ts'], how='inner').merge(fc[10][0], on=['wa_station', 'ts'], how='inner')
    B = ob.merge(fc[17][1], on=['wb_station', 'ts'], how='inner').merge(fc[10][1], on=['wb_station', 'ts'], how='inner')
    log('station-hours A', len(A), 'B', len(B))
    rows = []
    for prov, df, vars_ in (('A', A, ['wa_cloud', 'wa_humidity']), ('B', B, ['wb_cloud', 'wb_uv_idx'])):
        for v in vars_:
            x = df[[f'obs_{v}', f'r17_{v}', f'r10_{v}']].dropna()
            o, f17, f10 = x[f'obs_{v}'].astype('float64'), x[f'r17_{v}'].astype('float64'), x[f'r10_{v}'].astype('float64')
            e17, e10, eb = f17 - o, f10 - o, (f17 + f10) / 2 - o
            grid = {float(wt): float(((1 - wt) * f17 + wt * f10 - o).abs().mean()) for wt in np.round(np.arange(0, 1.01, 0.1), 2)}
            best_w = min(grid, key=grid.get)
            rows.append(dict(provider=prov, var=v, n=len(x), mae_r17=float(e17.abs().mean()), mae_r10=float(e10.abs().mean()), mae_blend50=float(eb.abs().mean()),
                             best_blend_w_r10=best_w, mae_best_blend=grid[best_w], corr_r17=float(np.corrcoef(f17, o)[0, 1]), corr_r10=float(np.corrcoef(f10, o)[0, 1]),
                             bias_r17=float(e17.mean()), bias_r10=float(e10.mean()), corr_err_r17_r10=float(np.corrcoef(e17, e10)[0, 1]),
                             frac_identical=float((f17 == f10).mean()), frac_r17_better_nontie=float((e17.abs() < e10.abs()).sum() / max(1, (e17.abs() != e10.abs()).sum()))))
            log(prov, v, {k: (round(val, 4) if isinstance(val, float) else val) for k, val in rows[-1].items()})
    pd.DataFrame(rows).to_csv(OUT + 'verify_skill_rounds.csv', index=False)
    A['hour'] = A.ts.dt.hour
    h = A.groupby('hour').apply(lambda d: pd.Series({'mae_r17': (d.r17_wa_cloud - d.obs_wa_cloud).abs().mean(), 'mae_r10': (d.r10_wa_cloud - d.obs_wa_cloud).abs().mean(), 'n': len(d)}), include_groups=False)
    h.to_csv(OUT + 'verify_skill_A_cloud_by_hour.csv'); log('A cloud MAE by hour r17/r10:\n' + h.round(2).to_string())


# ------------------------------------------------------------------ model fits
def load_panel(r):
    cols = ['site_id', 'ts', 'energy', 'current_group', 'capacity_kw', 'lat', 'lon'] + WX + ['elev', 'azim', 'cosz', 'hour', 'doy']
    df = read(CACHE + f'panel_train_r{r}.parquet', cols, [('ts', '>', T0), ('ts', '<=', T2), ('elev', '>', 0)])
    df['cf'] = (df.energy / df.capacity_kw).clip(0, 1.2).astype('float32')
    df['doy_sin'] = np.sin(2 * np.pi * df.doy / 365.25).astype('float32'); df['doy_cos'] = np.cos(2 * np.pi * df.doy / 365.25).astype('float32')
    df['hour'] = df.hour.astype('float32')
    smp = pd.read_parquet(CACHE + 'smp_all.parquet'); smp['w'] = (smp.smp * smp.k).astype('float32')
    df = df.merge(smp[['ts', 'w']], on='ts', how='left')
    assert df.w.notna().all()
    return df


def stage_fit(r, seeds):
    import lightgbm as lgb
    df = load_panel(r)
    tr = df[df.ts <= T1]; va = df[df.ts > T1]
    log(f'r{r}: train rows', len(tr), 'val rows', len(va), 'val sites', va.site_id.nunique(), rss())
    wtr = (tr.w / tr.w.mean()).astype('float32').values
    out = pd.DataFrame({'site_id': va.site_id.astype(str).values, 'ts': va.ts.values, 'y': va.energy.values, 'g': va.current_group.astype(str).values, 'w': va.w.values})
    for s in seeds:
        t = time.time()
        m = lgb.LGBMRegressor(**LGB, random_state=s).fit(tr[FEATS], tr.cf, sample_weight=wtr)
        out[f'p_s{s}'] = (np.clip(m.predict(va[FEATS]), 0, None) * va.capacity_kw.values).astype('float32')
        log(f'r{r} seed {s} fit {time.time()-t:.0f}s', rss())
        imp = pd.Series(m.booster_.feature_importance('gain'), index=FEATS).sort_values(ascending=False)
        log(f'r{r} seed {s} top gain %:', (100 * imp / imp.sum()).round(1).head(8).to_dict())
    out.to_parquet(OUT + f'verify_valpred_r{r}.parquet', index=False)
    del df, tr, va; gc.collect()


# ------------------------------------------------------------------ eval
def group_W(day, pcol, night):
    d = pd.DataFrame({'ts': day.ts.values, 'g': day.g.values, 'y': day.y.values, 'p': day[pcol].astype('float64').values, 'w': day.w.values})
    n = pd.DataFrame({'ts': night.ts.values, 'g': night.g.values, 'y': night.y.values, 'p': 0.0, 'w': night.w.values})
    d = pd.concat([d, n], ignore_index=True)
    a = d.groupby(['ts', 'g']).agg(y=('y', 'sum'), p=('p', 'sum'), w=('w', 'first')).unstack('g').fillna(0.0)
    w = a[('w', 'A')].where(a[('w', 'A')] > 0, a[('w', 'B')])
    eA = a[('p', 'A')] - a[('y', 'A')]; eB = a[('p', 'B')] - a[('y', 'B')]
    Rw = float((w * (a[('y', 'A')] + a[('y', 'B')])).sum())
    W = float((w * (eA.abs() + eB.abs())).sum())
    idx = a.index if a.index.tz is not None else a.index.tz_localize('UTC').tz_convert(TZ)  # .values stripped tz -> naive UTC
    hr = idx.hour
    k3 = (hr >= 11) & (hr <= 15)
    W3 = float((w[k3] * (eA.abs() + eB.abs())[k3]).sum())
    return dict(W_ref=W, Rw=Rw, W_ref_pct=100 * W / Rw, W_k3=W3, W_k3_share=100 * W3 / W, n_hours=int(len(a)),
                bias_A=float(eA.mean()), bias_B=float(eB.mean()))


def stage_eval():
    p17 = pd.read_parquet(OUT + 'verify_valpred_r17.parquet'); p10 = pd.read_parquet(OUT + 'verify_valpred_r10.parquet')
    assert len(p17) == len(p10) and (p17.site_id.values == p10.site_id.values).all() and (p17.ts.values == p10.ts.values).all(), 'val row alignment differs'
    day = p17.copy(); day['p10_s0'] = p10.p_s0.values; del p10
    night = read(CACHE + 'panel_train_r17.parquet', ['site_id', 'ts', 'energy', 'current_group'], [('ts', '>', T1), ('ts', '<=', T2), ('elev', '<=', 0)])
    smp = pd.read_parquet(CACHE + 'smp_all.parquet'); smp['w'] = (smp.smp * smp.k).astype('float32')
    night = night.merge(smp[['ts', 'w']], on='ts', how='left').rename(columns={'energy': 'y', 'current_group': 'g'}); night['g'] = night.g.astype(str)
    log('day val rows', len(day), 'night val rows', len(night), 'night energy sum', float(night.y.sum()))
    day['avg_r17_2seed'] = (day.p_s0 + day.p_s2) / 2
    day['avg_r17_r10'] = (day.p_s0 + day.p10_s0) / 2
    res = {}
    for name, col in [('r17_s0', 'p_s0'), ('r17_s2', 'p_s2'), ('r10_s0', 'p10_s0'), ('avg_r17_2seed', 'avg_r17_2seed'), ('avg50_r17_r10', 'avg_r17_r10')]:
        res[name] = group_W(day, col, night); log(name, {k: round(v, 4) if isinstance(v, float) else v for k, v in res[name].items()})
    grid = {}
    for wt in np.round(np.arange(0, 0.51, 0.1), 2):
        day['_tmp'] = (1 - wt) * day.avg_r17_2seed + wt * day.p10_s0
        grid[float(wt)] = group_W(day, '_tmp', night)['W_ref_pct']
    log('W_ref% vs weight on r10 (base = 2-seed r17 avg):', {k: round(v, 3) for k, v in grid.items()})
    for c in ['p_s0', 'p10_s0', 'avg_r17_r10', 'avg_r17_2seed']:
        log('site-level w-MAE kWh', c, round(float((day.w * (day[c] - day.y).abs()).sum() / day.w.sum()), 3))
    rows = [dict(model=k, **v) for k, v in res.items()] + [dict(model=f'blend_w_r10={k}', W_ref_pct=v) for k, v in grid.items()]
    pd.DataFrame(rows).to_csv(OUT + 'verify_round_W.csv', index=False)
    json.dump({'res': res, 'grid': {str(k): v for k, v in grid.items()}}, open(OUT + 'verify_round_W.json', 'w'), indent=1)


if __name__ == '__main__':
    st = sys.argv[1]
    log(f'=== stage {st} start', time.strftime('%H:%M:%S'))
    if st == 'skill': stage_skill()
    elif st == 'r17': stage_fit(17, [0, 2])
    elif st == 'r10': stage_fit(10, [0])
    elif st == 'eval': stage_eval()
    log(f'=== stage {st} done', time.strftime('%H:%M:%S'))
