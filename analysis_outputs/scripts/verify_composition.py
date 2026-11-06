"""Adversarial verifier for the composition claim.
Independent recomputation of W(split) = sum_t w_t(|e1|+|e2|) from val_pred parquet + smp cache + composition CSVs,
plus (a) model-space OOS on E0_pool/E0_site (never used by the composition agent) and
(b) time OOS with month-parity and day-parity folds using a small SA optimizer written here.
Usage: python -I verify_composition.py [A|B|all]
"""
import sys, os, time, json
import numpy as np, pandas as pd, pyarrow.parquet as pq, pyarrow as pa

BASE = 'C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad/'
CACHE = BASE + 'cache/'; OUT = BASE + 'analysis/out/'; MY = BASE + 'analysis/vc_cache/'
DATA = 'C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset/'
os.makedirs(MY, exist_ok=True)
LO, HI = 20000.0, 22655.4
LOGF = open(OUT + 'verify_composition_log.txt', 'a', encoding='utf-8')


def log(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); LOGF.write(s + '\n'); LOGF.flush()


SITES = pd.read_csv(DATA + 'sites.csv'); IDS = SITES.site_id.tolist(); N = len(IDS)
CAP = SITES.capacity_kw.values.astype(np.float64); POS = {s: i for i, s in enumerate(IDS)}
T0 = pd.Timestamp('2024-06-01 01:00', tz='Asia/Seoul'); NH = 8760
HOURS = pd.date_range(T0, periods=NH, freq='h')


def load_err(v):
    f = MY + f'err_{v}.npz'
    if os.path.exists(f):
        z = np.load(f); return z['E'], z['ysum']
    t = pq.read_table(CACHE + f'val_pred_site_{v}.parquet', columns=['site_id', 'ts', 'y', 'pred'], read_dictionary=['site_id'])
    sid = t['site_id'].combine_chunks(); dic = sid.dictionary.to_pylist(); codes = sid.indices.to_numpy()
    site_idx = np.array([POS[s] for s in dic])[codes]
    ts_us = t['ts'].cast(pa.int64()).to_numpy()  # epoch microseconds (UTC)
    h = (ts_us - T0.value // 1000) / 3.6e9
    assert np.allclose(h, np.round(h)) and h.min() >= 0 and h.max() < NH, 'hour index not integral'
    h = np.round(h).astype(np.int64)
    y = t['y'].to_numpy().astype(np.float64); p = t['pred'].to_numpy().astype(np.float64)
    assert len(np.unique(h * N + site_idx)) == len(h), 'duplicate (site, ts) rows'
    E = np.zeros((NH, N)); Y = np.zeros((NH, N)); E[h, site_idx] = p - y; Y[h, site_idx] = y
    log(f'{v}: rows {len(h):,}, observed cells {len(h):,} of {NH * N:,} (missing {NH * N - len(h):,}), sum y {Y.sum():.4e}')
    E32 = E.astype(np.float32); ysum = Y.sum(1)
    np.savez_compressed(f, E=E32, ysum=ysum); del t, E, Y
    return E32, ysum


smp = pd.read_parquet(CACHE + 'smp_all.parquet'); smp['w'] = smp.smp * smp.k
W_ALL = smp.set_index('ts').w.reindex(HOURS).values.astype(np.float64)
assert not np.isnan(W_ALL).any()
MONTH = HOURS.month.values; DOY = HOURS.dayofyear.values


def ctx(v, mask=None):
    E32, ysum = load_err(v); E = E32.astype(np.float64)
    m = (np.abs(E).sum(1) > 0) & (W_ALL > 0)
    if mask is not None: m &= mask
    Em = E[m]; w = W_ALL[m]; tot = Em.sum(1)
    return dict(name=v, E=Em, ET=np.ascontiguousarray(Em.T), w=w, tot=tot, Wpool=float(w @ np.abs(tot)),
                wy=float((W_ALL * ysum)[mask if mask is not None else slice(None)].sum()), nh=int(m.sum()))


def W_of(a, C):
    g1 = C['E'] @ a; return float(C['w'] @ (np.abs(g1) + np.abs(C['tot'] - g1)))


def stats(a, C):
    g1 = C['E'] @ a; g2 = C['tot'] - g1; w = C['w']; W = float(w @ (np.abs(g1) + np.abs(g2)))
    both = (g1 != 0) & (g2 != 0); dis = g1 * g2 < 0
    return dict(W=W, Wpool=C['Wpool'], W_pct_of_wy=100 * W / C['wy'], gap=W - C['Wpool'], gap_pct=100 * (W - C['Wpool']) / C['Wpool'],
                krw_0p1gap=0.1 * (W - C['Wpool']), corr_e1e2=float(np.corrcoef(g1, g2)[0, 1]),
                disagree_share_hours_pct=100 * dis.sum() / max(1, both.sum()), cap_G1=float(CAP @ a), n_G1=int(a.sum()),
                feasible=bool(LO <= CAP @ a <= HI))


def load_comp(name):
    d = pd.read_csv(OUT + f'composition_{name}.csv').set_index('site_id').group.reindex(IDS)
    assert d.notna().all(); return (d.values == 'G1').astype(np.float64)


def random_splits(n, seed):
    rng = np.random.default_rng(seed); A = []
    while len(A) < n:
        B = (rng.random((4 * n, N)) < 0.5).astype(np.float64); c1 = B @ CAP
        A.extend(B[(c1 >= LO) & (c1 <= HI)])
    return np.array(A[:n])


def W_many(A, C, chunk=250):
    out = np.empty(len(A)); cor = np.empty(len(A))
    for s in range(0, len(A), chunk):
        G1 = C['E'] @ A[s:s + chunk].T; G2 = C['tot'][:, None] - G1
        out[s:s + chunk] = C['w'] @ (np.abs(G1) + np.abs(G2))
        g1c = G1 - G1.mean(0); g2c = G2 - G2.mean(0)
        cor[s:s + chunk] = (g1c * g2c).sum(0) / np.sqrt((g1c ** 2).sum(0) * (g2c ** 2).sum(0))
    return out, cor


def sa(C, a0, iters=300000, seed=0):
    """plain SA: 40% single move / 60% swap, geometric cooling T0=median|dW| of random proposals, Tend=T0/2000."""
    rng = np.random.default_rng(seed); ET = C['ET']; w = C['w']; tot = C['tot']
    a = a0.copy(); g1 = ET.T @ a; cap1 = float(CAP @ a); cur = float(w @ (np.abs(g1) + np.abs(tot - g1))); best = cur; besta = a.copy()
    ds = []
    for _ in range(400):
        i, j = rng.integers(N, size=2)
        if a[i] == a[j]: continue
        si, sj = (i, j) if a[i] == 1 else (j, i); g = g1 - ET[si] + ET[sj]
        ds.append(abs(float(w @ (np.abs(g) + np.abs(tot - g))) - cur))
    T0 = float(np.median(ds)); lr = np.log(1 / 2000.0)
    for it in range(iters):
        T = T0 * np.exp(lr * it / iters)
        if rng.random() < 0.4:
            j = int(rng.integers(N)); s = -1.0 if a[j] else 1.0; nc = cap1 + s * CAP[j]
            if not (LO <= nc <= HI): continue
            g = g1 + s * ET[j]; flip = (j,)
        else:
            i, j = rng.integers(N, size=2)
            if a[i] == a[j]: continue
            if a[i] == 0: i, j = j, i
            nc = cap1 - CAP[i] + CAP[j]
            if not (LO <= nc <= HI): continue
            g = g1 - ET[i] + ET[j]; flip = (i, j)
        new = float(w @ (np.abs(g) + np.abs(tot - g))); d = new - cur
        if d < 0 or rng.random() < np.exp(-d / T):
            for f in flip: a[f] = 1 - a[f]
            g1 = g; cur = new; cap1 = nc
            if cur < best: best = cur; besta = a.copy()
    return besta, best


COMPS = ['reference', 'twin_errcorr', 'twin_gencorr', 'strat_cluster8_cap', 'cap_pairs_balanced', 'embed_leaforder',
         'optimized_E1', 'optimized_joint_E1E7', 'optimized_E7_full', 'optimized_E1_tightcap']


def part_A():
    log('=== PART A: independent recomputation ===')
    # cross-check my error matrix against the composition agent's cache
    E32, ysum = load_err('E1_l1w')
    z = np.load(BASE + 'analysis/comp_cache/err_E1_l1w.npz')
    log('cross-check vs comp_cache err_E1_l1w: max|dE| =', float(np.abs(E32 - z['E']).max()), ' max|dw| =', float(np.abs(W_ALL - z['w']).max()),
        ' max|dysum| =', float(np.abs(ysum - z['ysum']).max()))
    rows = []
    # extra constructed splits: north/south by latitude median cut, and 'anti-twin' (twins kept together) as hedging test
    lat_order = np.argsort(-SITES.lat.values); cum = np.cumsum(CAP[lat_order]); k = int(np.argmin(np.abs(cum - CAP.sum() / 2))) + 1
    ns = np.zeros(N); ns[lat_order[:k]] = 1
    extra = {'north_south_lat(mine)': ns}
    for v in ['E1_l1w', 'E7_mix_site10', 'E0_pool', 'E0_site']:
        C = ctx(v); log(f'{v}: day-hours {C["nh"]}, sum w*y {C["wy"]:.4e}, W_pool {C["Wpool"]:.5e} ({100 * C["Wpool"] / C["wy"]:.3f}%)')
        for name in COMPS:
            s = stats(load_comp(name), C); s.update(variant=v, split=name); rows.append(s)
        for name, a in extra.items():
            s = stats(a, C); s.update(variant=v, split=name); rows.append(s)
        # random baseline + hedging test: relation between corr(e1,e2) and gap across random splits
        A = random_splits(500, seed=123); Wr, cr = W_many(A, C)
        gp = 100 * (Wr - C['Wpool']) / C['Wpool']
        from scipy.stats import spearmanr
        rho = spearmanr(cr, gp).correlation
        rows.append(dict(variant=v, split='random500_mean', W=float(Wr.mean()), Wpool=C['Wpool'], gap=float((Wr - C['Wpool']).mean()), gap_pct=float(gp.mean()),
                         corr_e1e2=float(cr.mean()), krw_0p1gap=0.1 * float((Wr - C['Wpool']).mean())))
        log(f'{v}: random500 gap% mean {gp.mean():.3f} sd {gp.std():.3f} min {gp.min():.3f} max {gp.max():.3f}; Spearman(corr(e1,e2), gap%) = {rho:.3f}')
        for name in ['reference', 'twin_errcorr', 'optimized_E1', 'optimized_joint_E1E7']:
            g = [r for r in rows if r['variant'] == v and r['split'] == name][0]['gap_pct']
            log(f'   {name:>22s}: gap% {g:.3f}  random percentile {100 * (gp < g).mean():.1f}')
        del C, A
    df = pd.DataFrame(rows); df.to_csv(OUT + 'verify_composition_partA.csv', index=False)
    piv = df.pivot(index='split', columns='variant', values='gap_pct').reindex(COMPS + list(extra) + ['random500_mean'])
    log('\ngap% by split x model variant:\n' + piv.round(3).to_string())
    log('\nE1_l1w details:\n' + df[df.variant == 'E1_l1w'][['split', 'W', 'Wpool', 'W_pct_of_wy', 'gap', 'gap_pct', 'krw_0p1gap', 'corr_e1e2', 'disagree_share_hours_pct', 'cap_G1', 'n_G1', 'feasible']].round(4).to_string(index=False))


def part_B():
    log('=== PART B: time out-of-sample with my own SA (E1_l1w) ===')
    folds = {'month_even': np.isin(MONTH, [6, 8, 10, 12, 2, 4]), 'month_odd': np.isin(MONTH, [7, 9, 11, 1, 3, 5]),
             'day_even': DOY % 2 == 0, 'day_odd': DOY % 2 == 1}
    pairs = [('month_even', 'month_odd'), ('month_odd', 'month_even'), ('day_even', 'day_odd'), ('day_odd', 'day_even')]
    twin = load_comp('twin_errcorr'); ref = load_comp('reference'); optfull = load_comp('optimized_E1'); joint = load_comp('optimized_joint_E1E7')
    C = {k: ctx('E1_l1w', m) for k, m in folds.items()}
    for k in C: log(f'fold {k}: day-hours {C[k]["nh"]}, W_pool {C[k]["Wpool"]:.4e}')
    opt = {}
    for k in folds:
        t = time.time(); a, best = sa(C[k], twin.copy(), iters=300000, seed=1); a2, best2 = sa(C[k], ref.copy(), iters=300000, seed=2)
        if best2 < best: a, best = a2, best2
        opt[k] = a; log(f'SA on {k}: W {best:.5e} gap% {100 * (best - C[k]["Wpool"]) / C[k]["Wpool"]:.3f} (two starts: {best:.5e}/{best2:.5e}) {time.time() - t:.0f}s')
    rows = []
    for tr, te in pairs:
        Ct = C[te]; A = random_splits(300, seed=7); Wr, _ = W_many(A, Ct); gr = float(Wr.mean())
        g = {n: W_of(a, Ct) for n, a in [('opt_fold', opt[tr]), ('oracle', opt[te]), ('twin_errcorr', twin), ('reference', ref), ('opt_E1_full(report, in-sample)', optfull), ('opt_joint(report, in-sample)', joint)]}
        g['random300_mean'] = gr
        surv = (g['reference'] - g['opt_fold']) / (g['reference'] - g['oracle'])
        surv_twin = (g['twin_errcorr'] - g['opt_fold']) / (g['twin_errcorr'] - g['oracle'])
        r = dict(train=tr, test=te, **{f'gap_pct_{n}': 100 * (v - Ct['Wpool']) / Ct['Wpool'] for n, v in g.items()},
                 survival_vs_ref_pct=100 * surv, opt_minus_twin_gap_pct=100 * (g['opt_fold'] - g['twin_errcorr']) / Ct['Wpool'],
                 krw_opt_vs_twin=0.1 * (g['twin_errcorr'] - g['opt_fold']), krw_opt_vs_ref=0.1 * (g['reference'] - g['opt_fold']),
                 agree_opt_fold_vs_oracle=float(max((opt[tr] == opt[te]).mean(), 1 - (opt[tr] == opt[te]).mean())))
        rows.append(r); log(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()}))
    pd.DataFrame(rows).to_csv(OUT + 'verify_composition_partB_oos.csv', index=False)
    # full-year numbers for the two fold-optimized splits, and agreement with report's optimum
    Cf = ctx('E1_l1w')
    for k, a in opt.items():
        s = stats(a, Cf); log(f'fold-opt {k} on full year: gap% {s["gap_pct"]:.3f} corr {s["corr_e1e2"]:.3f} cap_G1 {s["cap_G1"]:.0f}; agreement with report optimized_E1: {max((a == optfull).mean(), 1 - (a == optfull).mean()):.2f}')


def part_C():
    """figure: corr(e1,e2) vs gap% over random splits, named splits marked (hedging test), E1_l1w and E0_site."""
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, v in zip(axes, ['E1_l1w', 'E0_site']):
        C = ctx(v); A = random_splits(500, seed=123); Wr, cr = W_many(A, C); gp = 100 * (Wr - C['Wpool']) / C['Wpool']
        ax.scatter(cr, gp, s=6, alpha=0.4, label='500 random feasible splits')
        for name, mk in [('reference', 'x'), ('twin_errcorr', 's'), ('optimized_E1', '^'), ('optimized_joint_E1E7', 'v')]:
            s = stats(load_comp(name), C); ax.scatter([s['corr_e1e2']], [s['gap_pct']], s=70, marker=mk, label=f"{name} ({s['gap_pct']:.2f}%)")
        ax.set_xlabel('corr(e_G1, e_G2)'); ax.set_ylabel('gap% = (W - W_pool)/W_pool'); ax.set_title(f'{v}: higher error correlation -> lower penalty')
        ax.legend(fontsize=7); ax.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig(OUT + 'verify_composition_fig1_corr_vs_gap.png', dpi=120); log('saved fig')


if __name__ == '__main__':
    stage = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if stage in ('A', 'all'): part_A()
    if stage in ('B', 'all'): part_B()
    if stage in ('C', 'all'): part_C()
