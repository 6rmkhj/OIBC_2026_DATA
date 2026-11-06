"""OIBC 2026 - composition (G1/G2 split) analysis.
Stages (argv[1]): prep | splits | opt | oos | sens | fig | all.  Intermediate results in comp_cache/.
Penalty W(split) = sum_t w_t (|e1_t| + |e2_t|), w = SMP*k; W_pool = sum_t w_t |e1+e2| is the lower bound.
"""
import sys, os, json, time
import numpy as np, pandas as pd

BASE = 'C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad/'
CACHE = BASE + 'cache/'; OUT = BASE + 'analysis/out/'; CC = BASE + 'analysis/comp_cache/'
DATA = 'C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset/'
os.makedirs(CC, exist_ok=True); os.makedirs(OUT, exist_ok=True)
LO, HI = 20000.0, 22655.4
VARS = ['E1_l1w', 'E7_mix_site10']
MAIN, SECOND = VARS
LOG = open(OUT + 'comp_log.txt', 'a', encoding='utf-8')


def log(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); LOG.write(s + '\n'); LOG.flush()


SITES = pd.read_csv(DATA + 'sites.csv')
IDS = SITES.site_id.tolist(); N = len(IDS); CAP = SITES.capacity_kw.values.astype(np.float64)
TOTCAP = CAP.sum(); HALF = TOTCAP / 2
REF = (SITES.current_group.values == 'A').astype(np.int8)  # A -> G1


def feasible(a, lo=LO, hi=HI):
    c1 = float(CAP @ a); return lo <= c1 <= hi


# ----------------------------------------------------------------------------- prep
def prep():
    smp = pd.read_parquet(CACHE + 'smp_all.parquet'); smp['w'] = smp.smp * smp.k
    for v in VARS:
        d = pd.read_parquet(CACHE + f'val_pred_site_{v}.parquet')
        d['e'] = (d.pred - d.y).astype('float32')
        E = d.pivot(index='ts', columns='site_id', values='e').reindex(columns=IDS)
        Y = d.pivot(index='ts', columns='site_id', values='y').reindex(columns=IDS)
        ts = E.index
        w = smp.set_index('ts').w.reindex(ts).values.astype(np.float64)
        log(v, 'rows', len(d), 'hours', len(ts), 'missing cells', int(E.isna().sum().sum()), 'w nan', int(np.isnan(w).sum()),
            'sum w*y', float((Y.fillna(0).sum(1).values * w).sum()))
        np.savez_compressed(CC + f'err_{v}.npz', E=E.fillna(0).values.astype(np.float32), ysum=Y.fillna(0).sum(1).values.astype(np.float64),
                            w=w, hour=ts.hour.values.astype(np.int8), month=ts.month.values.astype(np.int8),
                            ts=ts.tz_convert('UTC').tz_localize(None).values.astype('datetime64[ns]').astype(np.int64))
        del d, E, Y


# ----------------------------------------------------------------------------- contexts
def ctx(v, period='full'):
    z = np.load(CC + f'err_{v}.npz')
    E = z['E'].astype(np.float64); w = z['w']; hour = z['hour']; month = z['month']; ysum = z['ysum']
    half1 = np.isin(month, [6, 7, 8, 9, 10, 11])  # 2024-06..2024-11 (first 6 validation months)
    wk = pd.to_datetime(z['ts'], utc=True).tz_convert('Asia/Seoul').isocalendar().week.values.astype(int)
    pm = {'full': np.ones(len(w), bool), 'H1': half1, 'H2': ~half1, 'Weven': wk % 2 == 0, 'Wodd': wk % 2 == 1}[period]
    m = pm & (np.abs(E).sum(1) > 0) & (w > 0)
    Em = E[m]
    return dict(name=f'{v}:{period}', E=Em, ET=np.ascontiguousarray(Em.T), w=w[m], tot=Em.sum(1), hour=hour[m], month=month[m],
                wy=float((w * ysum)[pm].sum()), Wpool=float(w[m] @ np.abs(Em.sum(1))), nh=int(m.sum()), ts=z['ts'][m])


def W_of(a, C):
    g1 = C['E'] @ a; return float(C['w'] @ (np.abs(g1) + np.abs(C['tot'] - g1)))


def stats(a, C):
    g1 = C['E'] @ a; g2 = C['tot'] - g1; w = C['w']
    W = float(w @ (np.abs(g1) + np.abs(g2))); gap = W - C['Wpool']
    both = (np.abs(g1) > 0) & (np.abs(g2) > 0); dis = (g1 * g2 < 0)
    ok = np.abs(g1) + np.abs(g2) > 0
    return dict(W=W, W_pct=100 * W / C['wy'], Wpool=C['Wpool'], gap=gap, gap_pct=100 * gap / C['Wpool'], krw=0.1 * gap,
                excess_share_pct=100 * gap / W, disagree_hours=int(dis.sum()), disagree_share_hours_pct=100 * dis.sum() / max(1, both.sum()),
                disagree_share_w_pct=100 * float(w[dis].sum()) / float(w[ok].sum()), corr_e1e2=float(np.corrcoef(g1, g2)[0, 1]),
                max_hour_excess=float((w * (np.abs(g1) + np.abs(g2) - np.abs(g1 + g2))).max()))


def align(a):
    """relabel so that overlap with reference A->G1 is maximal (split is symmetric)."""
    a = a.astype(np.int8)
    return a if (a == REF).mean() >= 0.5 else (1 - a).astype(np.int8)


# ----------------------------------------------------------------------------- split constructors
def cut_split(order):
    """sort sites by `order`, cut the cumulative capacity as close to half as possible."""
    cum = np.cumsum(CAP[order]); k = int(np.argmin(np.abs(cum - HALF))) + 1
    a = np.zeros(N, np.int8); a[order[:k]] = 1; return a


def repair(a, frozen=None):
    """move smallest sites from the heavy group to the light group until feasible."""
    a = a.copy(); frozen = np.zeros(N, bool) if frozen is None else frozen
    for _ in range(N):
        c1 = CAP @ a
        if LO <= c1 <= HI: return a
        heavy = 1 if c1 > HI else 0
        idx = np.where((a == heavy) & ~frozen)[0]; excess = abs(c1 - HALF)
        cand = idx[CAP[idx] <= 2 * excess]
        j = cand[np.argmax(CAP[cand])] if len(cand) else idx[np.argmin(CAP[idx])]
        a[j] = 1 - heavy
    return a


def pair_split(strata):
    """strata: list of index arrays (each already sorted). Pair consecutive members inside each stratum,
    leftovers paired by capacity; pairs placed so that the two members land in different groups,
    larger member to the currently lighter group (capacity-balanced interleave)."""
    pairs, left = [], []
    for s in strata:
        s = list(s)
        for i in range(0, len(s) - 1, 2): pairs.append((s[i], s[i + 1]))
        if len(s) % 2: left.append(s[-1])
    left = sorted(left, key=lambda i: -CAP[i])
    for i in range(0, len(left) - 1, 2): pairs.append((left[i], left[i + 1]))
    single = left[-1] if len(left) % 2 else None
    pairs.sort(key=lambda p: -(CAP[p[0]] + CAP[p[1]]))
    a = np.zeros(N, np.int8); c1 = 0.0; c2 = 0.0
    for i, j in pairs:
        big, small = (i, j) if CAP[i] >= CAP[j] else (j, i)
        if c1 <= c2: a[big] = 1; a[small] = 0; c1 += CAP[big]; c2 += CAP[small]
        else: a[big] = 0; a[small] = 1; c2 += CAP[big]; c1 += CAP[small]
    if single is not None:
        a[single] = 1 if c1 <= c2 else 0
    return repair(a)


def greedy_match(R, order=None):
    """maximum-similarity greedy matching: returns list of index arrays [i, j] (pairs) sorted by capacity."""
    iu = np.triu_indices(N, 1); sim = R[iu]; o = np.argsort(-sim)
    used = np.zeros(N, bool); pairs = []
    for k in o:
        i, j = iu[0][k], iu[1][k]
        if not used[i] and not used[j]:
            used[i] = used[j] = True; pairs.append([i, j])
        if used.sum() >= N - 1: break
    rest = np.where(~used)[0]
    strata = [np.array(p) for p in pairs] + [np.array([r]) for r in rest]
    return strata, sim[o[:len(pairs)]]


def block_split(labels):
    """assign whole clusters to the lighter group (largest cluster first) -> 'diversified' block split."""
    labs, caps = np.unique(labels, return_inverse=True)
    ccap = np.bincount(caps, weights=CAP); a = np.zeros(N, np.int8); c1 = c2 = 0.0
    for k in np.argsort(-ccap):
        if c1 <= c2: a[caps == k] = 1; c1 += ccap[k]
        else: c2 += ccap[k]
    return a


def hav(lat, lon):
    la = np.radians(lat); lo = np.radians(lon)
    d = np.sin((la[:, None] - la[None]) / 2) ** 2 + np.cos(la[:, None]) * np.cos(la[None]) * np.sin((lo[:, None] - lo[None]) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(d))


def err_corr(C):
    R = np.corrcoef(C['ET']); R[~np.isfinite(R)] = 0; np.fill_diagonal(R, 1); return R


def leaf_order(R):
    from scipy.cluster.hierarchy import linkage, optimal_leaf_ordering, leaves_list
    from scipy.spatial.distance import squareform
    D = np.sqrt(np.clip(2 * (1 - R), 0, None)); np.fill_diagonal(D, 0)
    Z = linkage(squareform(D, checks=False), 'average'); Z = optimal_leaf_ordering(Z, squareform(D, checks=False))
    return leaves_list(Z)


def build_splits(C):
    """all non-optimized splits; returns dict name -> assignment."""
    S = {}
    S['reference_AB'] = REF.copy()
    S['north_south_lat'] = cut_split(np.argsort(-SITES.lat.values))
    S['east_west_lon'] = cut_split(np.argsort(SITES.lon.values))
    cl = pd.read_csv(OUT + 'sc_clusters.csv', index_col=0).reindex(IDS)
    for k in [4, 6, 8, 12]:
        S[f'cluster_block_k{k}'] = block_split(cl[f'cluster_k{k}'].values)
    o = np.argsort(-CAP)
    a = np.zeros(N, np.int8); a[o[0::2]] = 1; S['cap_alternate'] = a
    a = np.zeros(N, np.int8); a[o[0::4]] = 1; a[o[3::4]] = 1; S['cap_snake'] = a
    S['cap_pairs_balanced'] = pair_split([o])
    R = err_corr(C)
    S['embed_leaforder_pairs'] = pair_split([leaf_order(R)])
    strata, sims = greedy_match(R); S['twin_errcorr_pairs'] = pair_split(strata)
    S['_twin_errcorr_sims'] = sims
    Rg = pd.read_csv(OUT + 'sc_corr_anom.csv', index_col=0).reindex(index=IDS, columns=IDS).values.astype(float)
    Rg[~np.isfinite(Rg)] = 0; np.fill_diagonal(Rg, 1)
    strata, sims = greedy_match(Rg); S['twin_gencorr_pairs'] = pair_split(strata); S['_twin_gencorr_sims'] = sims
    Dk = hav(SITES.lat.values, SITES.lon.values)
    strata, _ = greedy_match(-Dk); S['twin_geo_pairs'] = pair_split(strata)
    for k in [8, 12]:
        strata = [np.array(sorted(np.where(cl[f'cluster_k{k}'].values == c)[0], key=lambda i: -CAP[i])) for c in np.unique(cl[f'cluster_k{k}'].values)]
        S[f'strat_cluster{k}_x_cap'] = pair_split(strata)
    st = SITES.wa_station.values
    strata = [np.array(sorted(np.where(st == s)[0], key=lambda i: -CAP[i])) for s in np.unique(st)]
    S['strat_waStation_x_cap'] = pair_split(strata)
    st = SITES.wb_station.values
    strata = [np.array(sorted(np.where(st == s)[0], key=lambda i: -CAP[i])) for s in np.unique(st)]
    S['strat_wbStation_x_cap'] = pair_split(strata)
    return S


def random_splits(n, seed=0):
    rng = np.random.default_rng(seed); A = []
    while len(A) < n:
        B = (rng.random((4 * n, N)) < 0.5).astype(np.int8); c1 = B @ CAP
        A.extend(B[(c1 >= LO) & (c1 <= HI)])
    return np.array(A[:n], np.int8)


def W_many(A, C, chunk=400):
    out = np.empty(len(A))
    for s in range(0, len(A), chunk):
        G1 = C['E'] @ A[s:s + chunk].T.astype(np.float64)
        out[s:s + chunk] = C['w'] @ (np.abs(G1) + np.abs(C['tot'][:, None] - G1))
    return out


# ----------------------------------------------------------------------------- optimizer
def sa(C, a0, iters=150000, seed=0, lo=LO, hi=HI, T0=None, Tend_ratio=2000.0, verbose=True, pairs=None):
    """pairs: optional array (P,2) -> moves restricted to swapping the two members of a pair (orientation search)."""
    rng = np.random.default_rng(seed); ET = C['ET']; w = C['w']; tot = C['tot']
    a = a0.astype(np.int8).copy(); g1 = ET.T @ a; cap1 = float(CAP @ a)
    cur = float(w @ (np.abs(g1) + np.abs(tot - g1))); best = cur; besta = a.copy()
    # temperature from random feasible proposals
    if T0 is None:
        ds = []
        for _ in range(400):
            i, j = pairs[rng.integers(len(pairs))] if pairs is not None else rng.integers(N, size=2)
            if a[i] == a[j]: continue
            si, sj = (i, j) if a[i] == 1 else (j, i)
            g = g1 - ET[si] + ET[sj]; ds.append(abs(float(w @ (np.abs(g) + np.abs(tot - g))) - cur))
        T0 = float(np.median(ds)) if ds else 1e5
    Tend = T0 / Tend_ratio; lr = np.log(Tend / T0); acc = 0; t0 = time.time()
    for it in range(iters):
        T = T0 * np.exp(lr * it / iters)
        if pairs is not None:
            i, j = pairs[rng.integers(len(pairs))]
            if a[i] == a[j]: continue
            if a[i] == 0: i, j = j, i
            nc = cap1 - CAP[i] + CAP[j]
            if not (lo <= nc <= hi): continue
            g = g1 - ET[i] + ET[j]; flip = (i, j)
        elif rng.random() < 0.4:
            j = int(rng.integers(N)); s = -1.0 if a[j] else 1.0; nc = cap1 + s * CAP[j]
            if not (lo <= nc <= hi): continue
            g = g1 + s * ET[j]; flip = (j,)
        else:
            i, j = rng.integers(N, size=2)
            if a[i] == a[j]: continue
            if a[i] == 0: i, j = j, i  # i in G1 -> out, j in G2 -> in
            nc = cap1 - CAP[i] + CAP[j]
            if not (lo <= nc <= hi): continue
            g = g1 - ET[i] + ET[j]; flip = (i, j)
        new = float(w @ (np.abs(g) + np.abs(tot - g))); d = new - cur
        if d < 0 or rng.random() < np.exp(-d / T):
            for f in flip: a[f] = 1 - a[f]
            g1 = g; cur = new; cap1 = nc; acc += 1
            if cur < best: best = cur; besta = a.copy()
    if verbose: log(f'   SA seed={seed} iters={iters} T0={T0:.3g} acc={acc / iters:.2%} start={float(w @ (np.abs(ET.T @ a0) + np.abs(tot - ET.T @ a0))):.6g} best={best:.6g} ({time.time() - t0:.0f}s)')
    return besta, best


def polish(C, a, lo=LO, hi=HI, max_sweeps=80, frozen=None, verbose=True):
    """steepest descent over all single flips and all pair swaps."""
    E = C['E']; w = C['w']; tot = C['tot']; a = a.astype(np.int8).copy(); t0 = time.time()
    frozen = np.zeros(N, bool) if frozen is None else frozen
    cur = W_of(a, C); start = cur
    for sw in range(max_sweeps):
        g1 = E @ a; cap1 = float(CAP @ a)
        S = np.where(a == 1, -1.0, 1.0)
        cand = g1[:, None] + S[None, :] * E
        Wf = w @ (np.abs(cand) + np.abs(tot[:, None] - cand))
        ncap = cap1 + S * CAP; Wf[(ncap < lo) | (ncap > hi) | frozen] = np.inf
        bestW = Wf.min(); move = (int(np.argmin(Wf)),)
        G1i = np.where((a == 1) & ~frozen)[0]; G2i = np.where((a == 0) & ~frozen)[0]
        E2 = E[:, G2i]
        for i in G1i:
            cand = (g1 - E[:, i])[:, None] + E2
            Ws = w @ (np.abs(cand) + np.abs(tot[:, None] - cand))
            ncap = cap1 - CAP[i] + CAP[G2i]; Ws[(ncap < lo) | (ncap > hi)] = np.inf
            k = int(np.argmin(Ws))
            if Ws[k] < bestW: bestW = Ws[k]; move = (int(i), int(G2i[k]))
        if bestW < cur - 1e-6:
            for f in move: a[f] = 1 - a[f]
            cur = bestW
        else: break
    if verbose: log(f'   polish: {start:.6g} -> {cur:.6g} in {sw} sweeps ({time.time() - t0:.0f}s)')
    return a, cur


def optimize(C, starts, iters=150000, seeds=None, lo=LO, hi=HI, tag=''):
    res = []; best = (None, np.inf, None)
    for k, (nm, a0) in enumerate(starts.items()):
        if not (lo <= CAP @ a0 <= hi): a0 = repair(a0)
        w0 = W_of(a0, C)
        a1, w1 = sa(C, a0, iters=iters, seed=(seeds[k] if seeds else k), lo=lo, hi=hi)
        a2, w2 = polish(C, a1, lo=lo, hi=hi)
        res.append(dict(start=nm, W_start=w0, W_sa=w1, W_final=w2, cap_G1=float(CAP @ a2), a=a2))
        log(f'  [{tag}] start={nm}: {w0:.6g} -> SA {w1:.6g} -> polish {w2:.6g}  capG1={CAP @ a2:.1f}')
        if w2 < best[1]: best = (nm, w2, a2)
    return best, res


def agree(a, b):
    m = (a == b).mean(); return max(m, 1 - m)


def agree_cap(a, b):
    m = (CAP * (a == b)).sum() / TOTCAP; return max(m, 1 - m)


# ----------------------------------------------------------------------------- stages
def stage_splits():
    C = ctx(MAIN); C2 = ctx(SECOND)
    log(f'ctx {C["name"]}: day-hours {C["nh"]}, sum w*y {C["wy"]:.4g}, W_pool {C["Wpool"]:.6g} ({100 * C["Wpool"] / C["wy"]:.3f}%)')
    log(f'ctx {C2["name"]}: day-hours {C2["nh"]}, sum w*y {C2["wy"]:.4g}, W_pool {C2["Wpool"]:.6g} ({100 * C2["Wpool"] / C2["wy"]:.3f}%)')
    S = build_splits(C)
    sims = {k: S.pop(k) for k in list(S) if k.startswith('_')}
    log('twin errcorr sims: median %.3f min %.3f; twin gencorr sims: median %.3f min %.3f' % (np.median(sims['_twin_errcorr_sims']), sims['_twin_errcorr_sims'].min(),
                                                                                              np.median(sims['_twin_gencorr_sims']), sims['_twin_gencorr_sims'].min()))
    np.savez(CC + 'splits.npz', **{k: v for k, v in S.items()})
    t0 = time.time(); A = random_splits(2000); Wr = W_many(A, C); Wr2 = W_many(A, C2)
    log(f'random 2000 draws: W mean {Wr.mean():.6g} sd {Wr.std():.4g} min {Wr.min():.6g} max {Wr.max():.6g} ({time.time() - t0:.0f}s)')
    pd.DataFrame(dict(W_E1=Wr, gap_E1=Wr - C['Wpool'], W_E7=Wr2, gap_E7=Wr2 - C2['Wpool'], cap_G1=A @ CAP, cap_imbalance=np.abs(2 * (A @ CAP) - TOTCAP),
                      n_G1=A.sum(1))).to_csv(OUT + 'comp_random_draws.csv', index=False)
    np.save(CC + 'random_A.npy', A)
    rows = []
    for nm, a in S.items():
        st = stats(a, C); st2 = stats(a, C2)
        rows.append(dict(split=nm, feasible=feasible(a), cap_G1=CAP @ a, cap_G2=TOTCAP - CAP @ a, n_G1=int(a.sum()),
                         **{f'{k}_E1': v for k, v in st.items()}, **{f'{k}_E7': v for k, v in st2.items()},
                         rand_pctile_E1=100 * (Wr < st['W']).mean(), agree_ref=agree(a, REF)))
    T = pd.DataFrame(rows); T.to_csv(OUT + 'comp_splits_table.csv', index=False)
    log(T[['split', 'feasible', 'cap_G1', 'W_E1', 'gap_pct_E1', 'krw_E1', 'disagree_share_w_pct_E1', 'corr_e1e2_E1', 'gap_pct_E7', 'rand_pctile_E1']].to_string())


def stage_opt():
    C = ctx(MAIN); S = dict(np.load(CC + 'splits.npz'))
    A = np.load(CC + 'random_A.npy')
    starts = {'reference_AB': S['reference_AB'], 'embed_leaforder_pairs': S['embed_leaforder_pairs'], 'twin_errcorr_pairs': S['twin_errcorr_pairs'],
              'strat_cluster8_x_cap': S['strat_cluster8_x_cap'], 'random_1': A[0], 'random_2': A[1], 'random_3': A[2]}
    best, res = optimize(C, starts, iters=600000, tag='E1 full')
    log(f'BEST from start {best[0]}: W={best[1]:.6g}')
    a_opt = align(best[2]); np.save(CC + 'opt_E1_full.npy', a_opt)
    for r in res: r['agree_best'] = agree(r['a'], a_opt); r['agree_best_cap'] = agree_cap(r['a'], a_opt)
    np.savez(CC + 'opt_restarts.npz', **{f"{r['start']}": r['a'] for r in res})
    pd.DataFrame([{k: v for k, v in r.items() if k != 'a'} for r in res]).to_csv(OUT + 'comp_opt_restarts.csv', index=False)
    st = stats(a_opt, C); log('opt stats E1:', json.dumps(st))
    json.dump(st, open(CC + 'opt_E1_stats.json', 'w'))


def stage_oos():
    S = dict(np.load(CC + 'splits.npz')); A = np.load(CC + 'random_A.npy'); a_opt = np.load(CC + 'opt_E1_full.npy')
    starts = {'reference_AB': S['reference_AB'], 'embed_leaforder_pairs': S['embed_leaforder_pairs'], 'random_1': A[0]}
    Cs = {f'{v}:{p}': ctx(v, p) for v in VARS for p in ['full', 'H1', 'H2', 'Weven', 'Wodd']}
    opt = {'opt_E1_full': a_opt}
    short = lambda key: key.replace('E1_l1w', 'E1').replace('E7_mix_site10', 'E7').replace(':', '_')
    for key, it in [('E1_l1w:H1', 300000), ('E1_l1w:H2', 300000), ('E7_mix_site10:full', 300000), ('E1_l1w:Weven', 300000), ('E1_l1w:Wodd', 300000)]:
        best, _ = optimize(Cs[key], starts, iters=it, tag=key); opt['opt_' + short(key)] = align(best[2])
    # pair-orientation optimizer: twin pairs fixed (greedy matching on the training-period error correlation), only which twin goes to G1 is optimized
    for key in ['E1_l1w:full', 'E1_l1w:H1', 'E1_l1w:H2', 'E1_l1w:Weven', 'E1_l1w:Wodd']:
        Ck = Cs[key]; strata, _ = greedy_match(err_corr(Ck)); pairs = np.array([s for s in strata if len(s) == 2])
        a0 = pair_split(strata); w0 = W_of(a0, Ck)
        a1, w1 = sa(Ck, a0, iters=200000, seed=7, pairs=pairs, verbose=False)
        log(f'  [pairs {key}] twin-pairs heuristic {w0:.6g} -> orientation SA {w1:.6g}  capG1={CAP @ a1:.1f}')
        opt['pairopt_' + short(key)] = align(a1)
    # joint objective: stacked E1 + E7 full-year
    C1, C7 = Cs['E1_l1w:full'], Cs['E7_mix_site10:full']
    CJ = dict(name='joint', E=np.vstack([C1['E'], C7['E']]), w=np.concatenate([C1['w'], C7['w']]), tot=np.concatenate([C1['tot'], C7['tot']]))
    CJ['ET'] = np.ascontiguousarray(CJ['E'].T); CJ['Wpool'] = C1['Wpool'] + C7['Wpool']; CJ['wy'] = C1['wy'] + C7['wy']
    best, _ = optimize(CJ, {'opt_E1_full': a_opt, 'embed_leaforder_pairs': S['embed_leaforder_pairs'], 'random_1': A[0]}, iters=300000, tag='joint E1+E7')
    opt['opt_joint_E1E7'] = align(best[2])
    np.savez(CC + 'opt_all.npz', **opt)
    # evaluation table
    rows = []
    evalsets = list(Cs.keys())
    for nm, a in list(opt.items()) + [(k, S[k]) for k in ['reference_AB', 'embed_leaforder_pairs', 'twin_errcorr_pairs', 'twin_gencorr_pairs', 'strat_cluster8_x_cap', 'cap_pairs_balanced']]:
        r = dict(split=nm, cap_G1=CAP @ a)
        for k in evalsets:
            st = stats(a, Cs[k]); r[f'gap_{k}'] = st['gap']; r[f'gap_pct_{k}'] = st['gap_pct']; r[f'W_{k}'] = st['W']
        rows.append(r)
    r = dict(split='random_mean')
    for k in evalsets:
        Wr = W_many(A[:500], Cs[k]); r[f'W_{k}'] = Wr.mean(); r[f'gap_{k}'] = Wr.mean() - Cs[k]['Wpool']; r[f'gap_pct_{k}'] = 100 * (Wr.mean() - Cs[k]['Wpool']) / Cs[k]['Wpool']
    rows.append(r)
    T = pd.DataFrame(rows); T.to_csv(OUT + 'comp_oos_table.csv', index=False)
    log(T[['split'] + [f'gap_pct_{k}' for k in evalsets]].to_string())
    # survival of the optimized gain: gain = gap(ref) - gap(split); oracle = split optimized on that eval set
    surv = []
    g = lambda nm, k: float(T.loc[T.split == nm, f'gap_{k}'].iloc[0])
    for train, ev, oracle in [('opt_E1_H1', 'E1_l1w:H2', 'opt_E1_H2'), ('opt_E1_H2', 'E1_l1w:H1', 'opt_E1_H1'),
                              ('opt_E1_full', 'E7_mix_site10:full', 'opt_E7_full'), ('opt_E7_full', 'E1_l1w:full', 'opt_E1_full'),
                              ('opt_E1_H1', 'E7_mix_site10:H2', None), ('opt_E1_H2', 'E7_mix_site10:H1', None),
                              ('opt_E1_Weven', 'E1_l1w:Wodd', 'opt_E1_Wodd'), ('opt_E1_Wodd', 'E1_l1w:Weven', 'opt_E1_Weven'),
                              ('opt_E1_Weven', 'E7_mix_site10:Wodd', None), ('opt_E1_Wodd', 'E7_mix_site10:Weven', None),
                              ('pairopt_E1_H1', 'E1_l1w:H2', 'opt_E1_H2'), ('pairopt_E1_H2', 'E1_l1w:H1', 'opt_E1_H1'),
                              ('pairopt_E1_Weven', 'E1_l1w:Wodd', 'opt_E1_Wodd'), ('pairopt_E1_Wodd', 'E1_l1w:Weven', 'opt_E1_Weven'),
                              ('pairopt_E1_full', 'E7_mix_site10:full', 'opt_E7_full'),
                              ('opt_joint_E1E7', 'E1_l1w:full', 'opt_E1_full'), ('opt_joint_E1E7', 'E7_mix_site10:full', 'opt_E7_full')]:
        gain_ref = g('reference_AB', ev) - g(train, ev); gain_rand = g('random_mean', ev) - g(train, ev)
        d = dict(optimized_on=train, evaluated_on=ev, gap_ref=g('reference_AB', ev), gap_random=g('random_mean', ev), gap_split=g(train, ev),
                 gain_vs_ref=gain_ref, gain_vs_random=gain_rand, krw_gain_vs_ref=0.1 * gain_ref)
        if oracle:
            d['gap_oracle'] = g(oracle, ev); d['gain_oracle_vs_ref'] = g('reference_AB', ev) - g(oracle, ev)
            d['survival_pct_vs_ref'] = 100 * gain_ref / d['gain_oracle_vs_ref'] if d['gain_oracle_vs_ref'] else np.nan
            d['survival_pct_vs_random'] = 100 * gain_rand / (g('random_mean', ev) - g(oracle, ev))
        surv.append(d)
    SV = pd.DataFrame(surv); SV.to_csv(OUT + 'comp_oos_survival.csv', index=False); log(SV.to_string())
    # agreement between optimized solutions
    names = list(opt.keys()); M = pd.DataFrame([[agree(opt[i], opt[j]) for j in names] for i in names], index=names, columns=names)
    M.to_csv(OUT + 'comp_opt_agreement.csv'); log('agreement between optimized splits (site share):\n' + M.round(3).to_string())


def stage_sens():
    C = ctx(MAIN); C2 = ctx(SECOND); a_opt = np.load(CC + 'opt_E1_full.npy'); S = dict(np.load(CC + 'splits.npz'))
    W0 = W_of(a_opt, C); Wref = W_of(REF, C); rows = []
    top = np.argsort(-CAP)[:10]
    for j in top:
        for base_nm, base in [('optimized', a_opt), ('reference', REF)]:
            a = base.copy(); a[j] = 1 - a[j]; fz = np.zeros(N, bool); fz[j] = True
            Wb = W_of(base, C); d = dict(site_id=IDS[j], capacity_kw=CAP[j], base=base_nm, group_in_base='G1' if base[j] else 'G2', flip_feasible=feasible(a))
            d['dW_flip_alone'] = W_of(a, C) - Wb; d['dW_flip_alone_pct_of_W'] = 100 * d['dW_flip_alone'] / Wb
            if base_nm == 'optimized':
                a2 = repair(a, frozen=fz) if not feasible(a) else a
                a3, W3 = polish(C, a2, frozen=fz, verbose=False); d['W_after_repair'] = W_of(a2, C) - Wb
                d['dW_flip_then_reoptimize'] = W3 - Wb; d['dW_flip_then_reopt_pct'] = 100 * (W3 - Wb) / Wb; d['n_sites_changed_after_reopt'] = int((a3 != base).sum())
            rows.append(d); log(d)
    pd.DataFrame(rows).to_csv(OUT + 'comp_sens_large_sites.csv', index=False)
    # per-site marginal contribution in the optimized split (flip alone, all sites)
    g1 = C['E'] @ a_opt; S_ = np.where(a_opt == 1, -1.0, 1.0); cand = g1[:, None] + S_[None, :] * C['E']
    Wf = C['w'] @ (np.abs(cand) + np.abs(C['tot'][:, None] - cand)) - W0
    pd.DataFrame(dict(site_id=IDS, capacity_kw=CAP, group=np.where(a_opt == 1, 'G1', 'G2'), dW_if_flipped=Wf, dW_pct=100 * Wf / W0)).sort_values('dW_if_flipped', ascending=False).to_csv(OUT + 'comp_sens_flip_each_site.csv', index=False)
    log('flip-each-site: median dW %.4g, max %.4g (%s), min %.4g' % (np.median(Wf), Wf.max(), IDS[int(np.argmax(Wf))], Wf.min()))
    # capacity balance: random draws binned
    R = pd.read_csv(OUT + 'comp_random_draws.csv')
    R['imb_bin'] = pd.cut(R.cap_imbalance, [0, 500, 1000, 1500, 2000, 2700])
    B = R.groupby('imb_bin', observed=True).agg(n=('gap_E1', 'size'), gap_E1_mean=('gap_E1', 'mean'), gap_E1_sd=('gap_E1', 'std'), gap_E7_mean=('gap_E7', 'mean')).reset_index()
    B['imb_bin'] = B.imb_bin.astype(str); B.to_csv(OUT + 'comp_sens_cap_balance_random.csv', index=False); log(B.to_string())
    from scipy.stats import spearmanr
    rs = spearmanr(R.cap_imbalance, R.gap_E1); log(f'spearman(cap imbalance, gap_E1) = {rs.statistic:.3f} p={rs.pvalue:.2g}')
    # constrained / relaxed optima
    cons = []
    for nm, lo, hi in [('tight_|dc|<=200', HALF - 100, HALF + 100), ('feasible_[20000,22655]', LO, HI), ('relaxed_[17000,25655]', 17000.0, TOTCAP - 17000.0), ('relaxed_[12000,30655]', 12000.0, TOTCAP - 12000.0)]:
        a0 = a_opt.copy()
        if not (lo <= CAP @ a0 <= hi):  # move smallest sites to satisfy the tight band
            while not (lo <= CAP @ a0 <= hi):
                c1 = CAP @ a0; heavy = 1 if c1 > hi else 0; idx = np.where(a0 == heavy)[0]; a0[idx[np.argmin(CAP[idx])]] = 1 - heavy
        a1, w1 = sa(C, a0, iters=100000, seed=11, lo=lo, hi=hi, verbose=False); a2, w2 = polish(C, a1, lo=lo, hi=hi, verbose=False)
        st = stats(a2, C); cons.append(dict(constraint=nm, cap_G1=CAP @ a2, cap_G2=TOTCAP - CAP @ a2, W=w2, gap=st['gap'], gap_pct=st['gap_pct'], gap_pct_E7=stats(a2, C2)['gap_pct'], n_G1=int(a2.sum())))
        log(cons[-1])
        if nm.startswith('tight'): np.save(CC + 'opt_tight.npy', a2)
    pd.DataFrame(cons).to_csv(OUT + 'comp_sens_capacity_constraint.csv', index=False)
    # by hour / by month decomposition for ref, opt, best heuristic
    rows = []
    for nm, a in [('reference_AB', REF), ('optimized', a_opt), ('twin_errcorr_pairs', S['twin_errcorr_pairs']), ('embed_leaforder_pairs', S['embed_leaforder_pairs']), ('strat_cluster8_x_cap', S['strat_cluster8_x_cap'])]:
        g1 = C['E'] @ a; g2 = C['tot'] - g1; ex = C['w'] * (np.abs(g1) + np.abs(g2) - np.abs(g1 + g2)); dis = (g1 * g2 < 0)
        for key, arr in [('hour', C['hour']), ('month', C['month'])]:
            for v in np.unique(arr):
                m = arr == v; both = m & (np.abs(g1) > 0) & (np.abs(g2) > 0)
                rows.append(dict(split=nm, by=key, value=int(v), excess=ex[m].sum(), W=float(C['w'][m] @ (np.abs(g1[m]) + np.abs(g2[m]))), Wpool=float(C['w'][m] @ np.abs(C['tot'][m])),
                                 disagree_share_pct=100 * dis[both].mean() if both.sum() else np.nan, corr=np.corrcoef(g1[m], g2[m])[0, 1] if m.sum() > 2 else np.nan,
                                 corr_abs=np.corrcoef(np.abs(g1[m]), np.abs(g2[m]))[0, 1] if m.sum() > 2 else np.nan))
    pd.DataFrame(rows).to_csv(OUT + 'comp_by_hour_month.csv', index=False)
    # compositions
    opt_all = dict(np.load(CC + 'opt_all.npz')) if os.path.exists(CC + 'opt_all.npz') else {}
    comps = {'reference': REF, 'optimized_E1': a_opt, 'twin_errcorr': S['twin_errcorr_pairs'], 'twin_gencorr': S['twin_gencorr_pairs'], 'embed_leaforder': S['embed_leaforder_pairs'],
             'strat_cluster8_cap': S['strat_cluster8_x_cap'], 'cap_pairs_balanced': S['cap_pairs_balanced']}
    for k in ['opt_joint_E1E7', 'opt_E7_full']:
        if k in opt_all: comps[k.replace('opt_', 'optimized_')] = opt_all[k]
    if os.path.exists(CC + 'opt_tight.npy'): comps['optimized_E1_tightcap'] = np.load(CC + 'opt_tight.npy')
    summ = []
    for nm, a in comps.items():
        a = align(a); df = pd.DataFrame(dict(site_id=IDS, group=np.where(a == 1, 'G1', 'G2'))); df.to_csv(OUT + f'composition_{nm}.csv', index=False)
        c1 = CAP @ a; st = stats(a, C); st2 = stats(a, C2)
        summ.append(dict(name=nm, file=f'composition_{nm}.csv', cap_G1=round(c1, 2), cap_G2=round(TOTCAP - c1, 2), n_G1=int(a.sum()), n_G2=int(N - a.sum()), feasible=feasible(a),
                         gap_pct_E1=st['gap_pct'], krw_gap_E1=st['krw'], gap_pct_E7=st2['gap_pct'], agree_with_optimized=agree(a, a_opt)))
        log(f'composition_{nm}.csv  G1 {c1:.2f} kW ({int(a.sum())} sites) / G2 {TOTCAP - c1:.2f} kW ({N - int(a.sum())} sites)  feasible={feasible(a)}  gap% E1={st["gap_pct"]:.3f} E7={st2["gap_pct"]:.3f}')
    pd.DataFrame(summ).to_csv(OUT + 'comp_compositions_summary.csv', index=False)
    wide = pd.DataFrame({'site_id': IDS, 'capacity_kw': CAP, **{nm: np.where(align(a) == 1, 'G1', 'G2') for nm, a in comps.items()}})
    wide.to_csv(OUT + 'comp_assignments_wide.csv', index=False)


def stage_fig():
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    COL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']; GRAY = '#9a9a93'
    plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.alpha': 0.25})
    C = ctx(MAIN); T = pd.read_csv(OUT + 'comp_splits_table.csv'); R = pd.read_csv(OUT + 'comp_random_draws.csv'); a_opt = np.load(CC + 'opt_E1_full.npy')
    st_opt = json.load(open(CC + 'opt_E1_stats.json')); S = dict(np.load(CC + 'splits.npz'))
    # fig1: gap% per split
    T2 = T.sort_values('gap_pct_E1'); fig, ax = plt.subplots(figsize=(9, 6.5))
    names = list(T2.split) + ['optimized (SA)']; vals = list(T2.gap_pct_E1) + [st_opt['gap_pct']]
    cols = [COL[1] if n == 'reference_AB' else (COL[2] if n.startswith('optimized') else COL[0]) for n in names]
    ax.barh(names, vals, color=cols, height=0.7); ax.axvline(100 * (R.gap_E1.mean()) / C['Wpool'], color=GRAY, ls='--', lw=1.5, label='random mean')
    ax.axvspan(100 * R.gap_E1.quantile(.05) / C['Wpool'], 100 * R.gap_E1.quantile(.95) / C['Wpool'], color=GRAY, alpha=.15, label='random 5-95%')
    for i, v in enumerate(vals): ax.text(v + 0.03, i, f'{v:.2f}%', va='center', fontsize=8)
    ax.set_xlabel('gap to pooled lower bound  (W - W_pool) / W_pool  [%]  (E1_l1w, validation year)'); ax.set_title('Penalty excess over W_pool by composition (lower = better)'); ax.legend(loc='lower right')
    fig.tight_layout(); fig.savefig(OUT + 'comp_fig1_gap_by_split.png', dpi=130); plt.close(fig)
    # fig2: random distribution
    fig, ax = plt.subplots(figsize=(8, 4.2)); gp = 100 * R.gap_E1 / C['Wpool']
    ax.hist(gp, bins=50, color=COL[0], alpha=.8, edgecolor='white'); ax.set_xlabel('gap to W_pool [%]  (2000 random feasible splits)'); ax.set_ylabel('count')
    marks = [('reference_AB', COL[1]), ('twin_errcorr_pairs', COL[2]), ('embed_leaforder_pairs', COL[3]), ('strat_cluster8_x_cap', COL[4]), ('north_south_lat', COL[5])]
    for i, (nm, c) in enumerate(marks):
        v = float(T.loc[T.split == nm, 'gap_pct_E1'].iloc[0]); ax.axvline(v, color=c, lw=2); ax.text(v, ax.get_ylim()[1] * (0.95 - 0.08 * i), nm, color=c, fontsize=8, ha='left')
    ax.axvline(st_opt['gap_pct'], color='black', lw=2); ax.text(st_opt['gap_pct'], ax.get_ylim()[1] * 0.5, ' optimized', fontsize=8)
    ax.set_title('Where does each composition fall in the random-split distribution?'); fig.tight_layout(); fig.savefig(OUT + 'comp_fig2_random_hist.png', dpi=130); plt.close(fig)
    # fig3: by hour: disagreement share + excess
    H = pd.read_csv(OUT + 'comp_by_hour_month.csv'); fig, ax = plt.subplots(1, 3, figsize=(14, 4))
    for i, nm in enumerate(['reference_AB', 'optimized', 'twin_errcorr_pairs', 'strat_cluster8_x_cap']):
        h = H[(H.split == nm) & (H.by == 'hour')].sort_values('value')
        ax[0].plot(h.value, h.disagree_share_pct, 'o-', color=COL[i], label=nm, ms=4, lw=2); ax[1].plot(h.value, h.excess / 1e6, 'o-', color=COL[i], ms=4, lw=2, label=nm); ax[2].plot(h.value, h['corr'], 'o-', color=COL[i], ms=4, lw=2, label=nm)
    ax[0].set_title('Share of hours where sign(e1) != sign(e2) [%]'); ax[1].set_title('Excess penalty  w*(|e1|+|e2|-|e1+e2|)  [M KRW]'); ax[2].set_title('corr(e1, e2) within hour-of-day')
    for a_ in ax: a_.set_xlabel('hour (KST, right-closed)'); a_.axvspan(10.5, 15.5, color=GRAY, alpha=.12)
    ax[0].legend(fontsize=8); fig.tight_layout(); fig.savefig(OUT + 'comp_fig3_by_hour.png', dpi=130); plt.close(fig)
    # fig4: scatter e1 vs e2
    fig, ax = plt.subplots(1, 2, figsize=(10, 4.8), sharex=True, sharey=True)
    for i, (nm, a) in enumerate([('reference_AB', REF), ('optimized', a_opt)]):
        g1 = C['E'] @ a; g2 = C['tot'] - g1; m = C['w'] > 0
        ax[i].scatter(g1, g2, s=3, alpha=.25, color=COL[0]); lim = np.percentile(np.abs(np.r_[g1, g2]), 99.5)
        ax[i].set_xlim(-lim, lim); ax[i].set_ylim(-lim, lim); ax[i].axhline(0, color=GRAY, lw=1); ax[i].axvline(0, color=GRAY, lw=1)
        dis = 100 * ((g1 * g2) < 0).mean(); ax[i].set_title(f'{nm}: corr={np.corrcoef(g1, g2)[0, 1]:.3f}, sign-disagree={dis:.1f}% of day hours'); ax[i].set_xlabel('e_G1 [kWh]')
    ax[0].set_ylabel('e_G2 [kWh]'); fig.tight_layout(); fig.savefig(OUT + 'comp_fig4_scatter_e1_e2.png', dpi=130); plt.close(fig)
    # fig5: map
    fig, ax = plt.subplots(1, 2, figsize=(11, 5.5))
    for i, (nm, a) in enumerate([('reference_AB', REF), ('optimized', a_opt)]):
        for g, c, lab in [(1, COL[0], 'G1'), (0, COL[1], 'G2')]:
            m = a == g; ax[i].scatter(SITES.lon[m], SITES.lat[m], s=8 + CAP[m] / 8, color=c, alpha=.6, edgecolor='white', lw=.5, label=f'{lab} ({CAP[m].sum():.0f} kW, {m.sum()} sites)')
        ax[i].set_title(nm); ax[i].set_xlabel('lon'); ax[i].legend(fontsize=8, loc='lower left'); ax[i].set_aspect(1.2)
    ax[0].set_ylabel('lat'); fig.tight_layout(); fig.savefig(OUT + 'comp_fig5_map.png', dpi=130); plt.close(fig)
    # fig6: by month
    fig, ax = plt.subplots(figsize=(8, 4)); order = [6, 7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5]
    for i, nm in enumerate(['reference_AB', 'optimized', 'twin_errcorr_pairs', 'strat_cluster8_x_cap']):
        h = H[(H.split == nm) & (H.by == 'month')].set_index('value').reindex(order); ax.plot(range(12), h.excess / 1e6, 'o-', color=COL[i], label=nm, lw=2, ms=4)
    ax.set_xticks(range(12)); ax.set_xticklabels([f'{m:02d}' for m in order]); ax.set_xlabel('month (2024-06 .. 2025-05)'); ax.set_ylabel('excess penalty W - W_pool [M KRW]'); ax.legend(fontsize=8); ax.set_title('Excess penalty by month')
    fig.tight_layout(); fig.savefig(OUT + 'comp_fig6_by_month.png', dpi=130); plt.close(fig)
    # fig7: OOS
    if os.path.exists(OUT + 'comp_oos_table.csv'):
        O = pd.read_csv(OUT + 'comp_oos_table.csv').set_index('split'); fig, ax = plt.subplots(figsize=(10, 4.5))
        sets = ['E1_l1w:H1', 'E1_l1w:H2', 'E1_l1w:Weven', 'E1_l1w:Wodd', 'E7_mix_site10:full']
        splits = ['reference_AB', 'random_mean', 'twin_errcorr_pairs', 'opt_E1_H1', 'opt_E1_H2', 'opt_E1_Weven', 'opt_E1_Wodd', 'opt_E1_full']
        cols = [COL[1], GRAY, COL[2], COL[0], COL[3], COL[4], COL[5], 'black']
        x = np.arange(len(sets)); wd = 0.1
        for i, s in enumerate(splits):
            ax.bar(x + (i - 3.5) * wd, [O.loc[s, f'gap_pct_{k}'] for k in sets], wd, color=cols[i], label=s)
        ax.set_xticks(x); ax.set_xticklabels(sets); ax.set_ylabel('gap to W_pool [%]'); ax.set_title('Out-of-sample check: splits optimized on one half / one model, evaluated on the other'); ax.legend(fontsize=7, ncol=4)
        fig.tight_layout(); fig.savefig(OUT + 'comp_fig7_oos.png', dpi=130); plt.close(fig)
    # fig8: capacity imbalance vs gap
    fig, ax = plt.subplots(figsize=(7, 4)); ax.scatter(R.cap_imbalance, 100 * R.gap_E1 / C['Wpool'], s=4, alpha=.3, color=COL[0])
    B = R.groupby(pd.cut(R.cap_imbalance, 10), observed=True).agg(x=('cap_imbalance', 'mean'), y=('gap_E1', 'mean')); ax.plot(B.x, 100 * B.y / C['Wpool'], 'o-', color=COL[1], lw=2, label='bin mean')
    ax.set_xlabel('|cap_G1 - cap_G2| [kW]'); ax.set_ylabel('gap to W_pool [%]'); ax.set_title('Random splits: capacity imbalance vs penalty excess'); ax.legend(); fig.tight_layout(); fig.savefig(OUT + 'comp_fig8_cap_balance.png', dpi=130); plt.close(fig)
    # fig9: restart convergence
    if os.path.exists(OUT + 'comp_opt_restarts.csv'):
        Rr = pd.read_csv(OUT + 'comp_opt_restarts.csv'); fig, ax = plt.subplots(figsize=(8, 4)); x = np.arange(len(Rr))
        for i, c in enumerate(['W_start', 'W_sa', 'W_final']): ax.bar(x + (i - 1) * 0.27, 100 * (Rr[c] - C['Wpool']) / C['Wpool'], 0.27, color=COL[i], label=c)
        ax.set_xticks(x); ax.set_xticklabels(Rr.start, rotation=20); ax.set_ylabel('gap to W_pool [%]'); ax.set_title('Optimizer restarts: start -> SA -> polish'); ax.legend(); fig.tight_layout(); fig.savefig(OUT + 'comp_fig9_restarts.png', dpi=130); plt.close(fig)
    log('figures written')


if __name__ == '__main__':
    st = sys.argv[1] if len(sys.argv) > 1 else 'all'
    t0 = time.time(); log(f'=== stage {st} start {time.strftime("%H:%M:%S")}')
    for s in (['prep', 'splits', 'opt', 'oos', 'sens', 'fig'] if st == 'all' else [st]):
        globals()['stage_' + s]() if s != 'prep' else prep(); log(f'--- {s} done {time.time() - t0:.0f}s')
