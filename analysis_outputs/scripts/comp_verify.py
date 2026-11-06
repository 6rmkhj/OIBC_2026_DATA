"""Independent re-computation of the composition claim's key numbers.
W(split) = sum_t w_t(|e1|+|e2|), W_pool = sum_t w_t|e1+e2|, gap% = (W-W_pool)/W_pool.
Light on memory: error matrices built with numpy from the prediction caches (8760 x 253 float64 ~ 18 MB each)."""
import numpy as np, pandas as pd, pyarrow.parquet as pq, pyarrow.compute as pc, time, sys
from scipy.stats import spearmanr
BASE = 'C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad/'
CACHE, OUT = BASE + 'cache/', BASE + 'analysis/out/'
DATA = 'C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset/'
LO, HI = 20000.0, 22655.4
rng = np.random.default_rng(12345)
sites = pd.read_csv(DATA + 'sites.csv'); IDS = sites.site_id.tolist(); N = len(IDS)
CAP = sites.capacity_kw.values.astype(np.float64); TOT = CAP.sum(); HALF = TOT / 2
sid2i = {s: i for i, s in enumerate(IDS)}
print('sites', N, 'total cap', TOT)

smp = pd.read_parquet(CACHE + 'smp_all.parquet'); smp['w'] = smp.smp * smp.k
w_by_ts = smp.set_index('ts').w


def load_err(v):
    t = pq.read_table(CACHE + f'val_pred_site_{v}.parquet', columns=['site_id', 'ts', 'y', 'pred'])
    sid = pc.dictionary_encode(t['site_id']).combine_chunks()
    dic = sid.dictionary.to_pylist(); codes = sid.indices.to_numpy()
    col = np.array([sid2i[s] for s in dic])[codes]
    ts = pd.DatetimeIndex(t['ts'].to_pandas())
    tsu = ts.unique().sort_values(); row = tsu.get_indexer(ts)
    y = t['y'].to_numpy(zero_copy_only=False).astype(np.float64); p = t['pred'].to_numpy(zero_copy_only=False).astype(np.float64)
    E = np.zeros((len(tsu), N)); E[row, col] = p - y
    Y = np.zeros((len(tsu), N)); Y[row, col] = y
    w = w_by_ts.reindex(tsu).values.astype(np.float64)
    assert not np.isnan(w).any()
    print(f'{v}: rows {len(t)} hours {len(tsu)} first {tsu[0]} last {tsu[-1]} missing cells {len(tsu) * N - len(t)}')
    return dict(E=E, w=w, ts=tsu, ysum=Y.sum(1))


def ctx(z, mask=None):
    m = (np.abs(z['E']).sum(1) > 0) & (z['w'] > 0)
    if mask is not None: m &= mask
    E = z['E'][m]; w = z['w'][m]; tot = E.sum(1)
    return dict(E=E, w=w, tot=tot, Wpool=float(w @ np.abs(tot)), wy=float((z['w'] * z['ysum'])[m if mask is None else mask].sum()), nh=int(m.sum()))


def W_of(a, C):
    g1 = C['E'] @ a; return float(C['w'] @ (np.abs(g1) + np.abs(C['tot'] - g1)))


def st(a, C):
    g1 = C['E'] @ a; g2 = C['tot'] - g1; W = float(C['w'] @ (np.abs(g1) + np.abs(g2)))
    dis = g1 * g2 < 0; both = (g1 != 0) & (g2 != 0)
    return dict(W=W, gap=W - C['Wpool'], gap_pct=100 * (W - C['Wpool']) / C['Wpool'], corr=float(np.corrcoef(g1, g2)[0, 1]),
                disagree_share_hours_pct=100 * dis.sum() / both.sum(), capG1=float(CAP @ a), feasible=bool(LO <= CAP @ a <= HI))


def W_many(A, C, chunk=250):
    out = np.empty(A.shape[1])
    for s in range(0, A.shape[1], chunk):
        G1 = C['E'] @ A[:, s:s + chunk]; out[s:s + chunk] = C['w'] @ (np.abs(G1) + np.abs(C['tot'][:, None] - G1))
    return out


def read_comp(fn):
    d = pd.read_csv(OUT + fn).set_index('site_id').reindex(IDS); assert d.group.notna().all()
    return (d.group.values == 'G1').astype(np.float64)


def cut_split(order):
    cum = np.cumsum(CAP[order]); k = int(np.argmin(np.abs(cum - HALF))) + 1
    a = np.zeros(N); a[order[:k]] = 1; return a


def random_split():
    while True:
        a = (rng.random(N) < 0.5).astype(np.float64)
        if LO <= CAP @ a <= HI: return a


def local_search(a, C, max_flip_sweeps=600, swap_rounds=2):
    """steepest-descent single flips until none improves; then up to `swap_rounds` rounds of best pair swap (+ flips again)."""
    a = a.copy(); E, w, tot = C['E'], C['w'], C['tot']
    def flips(a):
        for _ in range(max_flip_sweeps):
            g1 = E @ a; cur = float(w @ (np.abs(g1) + np.abs(tot - g1)))
            sgn = 1 - 2 * a  # +1 if moving into G1
            cand = g1[:, None] + sgn[None, :] * E
            Wf = w @ (np.abs(cand) + np.abs(tot[:, None] - cand))
            capf = CAP @ a + sgn * CAP; Wf[(capf < LO) | (capf > HI)] = np.inf
            j = int(np.argmin(Wf))
            if Wf[j] - cur >= -1e-6: return a
            a[j] = 1 - a[j]
        return a
    a = flips(a)
    for _ in range(swap_rounds):
        g1 = E @ a; cur = float(w @ (np.abs(g1) + np.abs(tot - g1)))
        i1 = np.where(a == 1)[0]; i0 = np.where(a == 0)[0]
        P = np.array(np.meshgrid(i1, i0, indexing='ij')).reshape(2, -1)
        capn = CAP @ a - CAP[P[0]] + CAP[P[1]]; P = P[:, (capn >= LO) & (capn <= HI)]
        best, move = -1e-6, None
        for s in range(0, P.shape[1], 400):
            pi, pj = P[0, s:s + 400], P[1, s:s + 400]
            c = g1[:, None] - E[:, pi] + E[:, pj]
            Ws = w @ (np.abs(c) + np.abs(tot[:, None] - c)); k = int(np.argmin(Ws))
            if Ws[k] - cur < best: best = Ws[k] - cur; move = (pi[k], pj[k])
        if move is None: break
        a[move[0]] = 0; a[move[1]] = 1; a = flips(a)
    return a


def greedy_twins(R):
    iu = np.triu_indices(N, 1); o = np.argsort(-R[iu]); used = np.zeros(N, bool); pairs = []
    for k in o:
        i, j = iu[0][k], iu[1][k]
        if not used[i] and not used[j]: used[i] = used[j] = True; pairs.append((i, j))
        if used.sum() >= N - 1: break
    rest = np.where(~used)[0]
    pairs.sort(key=lambda p: -(CAP[p[0]] + CAP[p[1]]))
    a = np.zeros(N); c1 = c2 = 0.0
    for i, j in pairs:
        big, small = (i, j) if CAP[i] >= CAP[j] else (j, i)
        if c1 <= c2: a[big] = 1; c1 += CAP[big]; c2 += CAP[small]
        else: a[small] = 1; c2 += CAP[big]; c1 += CAP[small]
    for r in rest:
        a[r] = 1 if c1 <= c2 else 0; c1 += CAP[r] * a[r]; c2 += CAP[r] * (1 - a[r])
    assert LO <= CAP @ a <= HI, CAP @ a
    return a


STAGE = sys.argv[1] if len(sys.argv) > 1 else 'all'
t0 = time.time()
Z1 = load_err('E1_l1w'); C1 = ctx(Z1)
print(f'E1 full: hours {C1["nh"]} W_pool {C1["Wpool"]:.6g} = {100 * C1["Wpool"] / C1["wy"]:.3f}% of sum w*y {C1["wy"]:.5g}')

# --- 1. compositions
comps = {'reference(sites.csv A->G1)': (sites.current_group.values == 'A').astype(np.float64),
         'north_south_lat(my cut)': cut_split(np.argsort(-sites.lat.values)),
         'east_west_lon(my cut)': cut_split(np.argsort(sites.lon.values))}
for fn in ['composition_reference.csv', 'composition_twin_errcorr.csv', 'composition_twin_gencorr.csv', 'composition_optimized_E1.csv',
           'composition_optimized_joint_E1E7.csv', 'composition_optimized_E7_full.csv', 'composition_strat_cluster8_cap.csv', 'composition_cap_pairs_balanced.csv']:
    comps[fn] = read_comp(fn)
A = np.stack([random_split() for _ in range(2000)], 1)
ref = comps['reference(sites.csv A->G1)']; twin = comps['composition_twin_errcorr.csv']

if STAGE in ('splits', 'all'):
    Z7 = load_err('E7_mix_site10'); C7 = ctx(Z7)
    print(f'E7 full: hours {C7["nh"]} W_pool {C7["Wpool"]:.6g} = {100 * C7["Wpool"] / C7["wy"]:.3f}%')
    print('csv reference == sites.csv reference:', bool((comps['composition_reference.csv'] == ref).all()))
    rows = []
    for nm, a in comps.items():
        s1, s7 = st(a, C1), st(a, C7)
        rows.append(dict(split=nm, capG1=s1['capG1'], feasible=s1['feasible'], W_E1=s1['W'], gap_pct_E1=s1['gap_pct'], krw_0p1gap_E1=0.1 * s1['gap'],
                         corr_E1=s1['corr'], disagree_pct_E1=s1['disagree_share_hours_pct'], gap_pct_E7=s7['gap_pct']))
    T = pd.DataFrame(rows); print(T.to_string()); T.to_csv(OUT + 'compv_splits.csv', index=False)
    # --- 2. random splits percentile
    Wr = W_many(A, C1); gr = 100 * (Wr - C1['Wpool']) / C1['Wpool']
    ref_gap = T.loc[T.split.str.startswith('reference'), 'gap_pct_E1'].iloc[0]
    twin_gap = T.loc[T.split == 'composition_twin_errcorr.csv', 'gap_pct_E1'].iloc[0]
    print(f'random 2000: gap% mean {gr.mean():.3f} sd {gr.std():.3f} min {gr.min():.3f} max {gr.max():.3f}; reference percentile {100 * (gr < ref_gap).mean():.1f}; '
          f'share of random splits beating twin_errcorr: {100 * (gr < twin_gap).mean():.2f}%')
    imb = np.abs(2 * (CAP @ A) - TOT)
    print('random: spearman(|cap imbalance|, gap) =', spearmanr(imb, gr))
    del Z7, C7

def stage_oos():
    """--- 3. my own OOS: optimize on H1 (Jun-Nov) -> evaluate on H2 (Dec-May), and odd/even ISO weeks"""
    mon = Z1['ts'].month.values; wk = Z1['ts'].isocalendar().week.values.astype(int)
    periods = {'H1': np.isin(mon, [6, 7, 8, 9, 10, 11]), 'H2': ~np.isin(mon, [6, 7, 8, 9, 10, 11]), 'Weven': wk % 2 == 0, 'Wodd': wk % 2 == 1}
    CP = {k: ctx(Z1, m) for k, m in periods.items()}
    oos = []
    for tr, te in [('H1', 'H2'), ('H2', 'H1'), ('Weven', 'Wodd'), ('Wodd', 'Weven')]:
        Ct, Ce = CP[tr], CP[te]
        R = np.corrcoef(Ct['E'].T); R[~np.isfinite(R)] = 0; np.fill_diagonal(R, 1); twin_tr = greedy_twins(R)
        t1 = time.time(); a_ref = local_search(ref, Ct); a_tw = local_search(twin_tr, Ct); a_rd = local_search(random_split(), Ct)
        print(f'  [{tr}] local searches done {time.time() - t1:.0f}s', flush=True)
        oracle = min(local_search(ref, Ce), local_search(twin_tr, Ce), key=lambda a: W_of(a, Ce))
        rr = {}
        for nm, a in [('reference', ref), ('twin_fullyear_csv', twin), ('twin_built_on_train', twin_tr), ('opt_from_ref', a_ref), ('opt_from_twin', a_tw),
                      ('opt_from_random', a_rd), ('oracle(opt on test)', oracle)]:
            rr[nm] = dict(train_gap_pct=st(a, Ct)['gap_pct'], test_gap_pct=st(a, Ce)['gap_pct'], test_gap=st(a, Ce)['gap'])
        Ar = np.stack([random_split() for _ in range(300)], 1); rand_te = (W_many(Ar, Ce) - Ce['Wpool']).mean()
        g_ref = rr['reference']['test_gap']; g_or = rr['oracle(opt on test)']['test_gap']
        for nm, d in rr.items():
            oos.append(dict(train=tr, test=te, split=nm, **d, test_random_mean_gap_pct=100 * rand_te / Ce['Wpool'],
                            survival_vs_ref_pct=100 * (g_ref - d['test_gap']) / (g_ref - g_or)))
        print(f'[{tr}->{te}] done in {time.time() - t1:.0f}s', flush=True)
    O = pd.DataFrame(oos); print(O.to_string()); O.to_csv(OUT + 'compv_oos.csv', index=False)


def stage_clim():
    """--- 4. model-free error source: climatology forecast (mean CF by month x hour from train period) on validation year"""
    cf = pd.read_parquet(CACHE + 'cf_wide.parquet'); cf = cf.reindex(columns=IDS)
    ts = cf.index; trm = ts < pd.Timestamp('2024-06-01 01:00', tz='Asia/Seoul')
    va = (ts >= pd.Timestamp('2024-06-01 01:00', tz='Asia/Seoul')) & (ts <= pd.Timestamp('2025-06-01 00:00', tz='Asia/Seoul'))
    clim = cf[trm].groupby([ts[trm].month, ts[trm].hour]).mean()
    key = pd.MultiIndex.from_arrays([ts[va].month, ts[va].hour])
    pred = clim.reindex(key).values; obs = cf[va].values.astype(np.float64)
    Ec = np.where(np.isnan(obs) | np.isnan(pred), 0.0, (pred - obs)) * CAP[None, :]
    Zc = dict(E=Ec, w=w_by_ts.reindex(ts[va]).values.astype(np.float64), ts=ts[va], ysum=np.nansum(np.nan_to_num(obs) * CAP[None, :], 1))
    Cc = ctx(Zc); print(f'climatology errors: hours {Cc["nh"]} W_pool {Cc["Wpool"]:.6g} ({100 * Cc["Wpool"] / Cc["wy"]:.2f}% of sum w*y)')
    rows = []
    for nm, a in comps.items():
        s = st(a, Cc); rows.append(dict(split=nm, gap_pct_clim=s['gap_pct'], corr_clim=s['corr']))
    Wrc = W_many(A, Cc); grc = 100 * (Wrc - Cc['Wpool']) / Cc['Wpool']
    rows.append(dict(split='random_mean(2000)', gap_pct_clim=grc.mean(), corr_clim=np.nan))
    Tc = pd.DataFrame(rows); print(Tc.to_string()); Tc.to_csv(OUT + 'compv_climatology.csv', index=False)
    print(f'climatology: reference percentile among random {100 * (grc < Tc.gap_pct_clim.iloc[0]).mean():.1f}; '
          f'random beating twin_errcorr {100 * (grc < Tc.loc[Tc.split == "composition_twin_errcorr.csv", "gap_pct_clim"].iloc[0]).mean():.2f}%; '
          f'random beating optimized_E1 {100 * (grc < Tc.loc[Tc.split == "composition_optimized_E1.csv", "gap_pct_clim"].iloc[0]).mean():.2f}%')
    # the same climatology-error check, but with a split optimized ON the climatology errors (how far can W_pool be approached with model-free errors)
    a_c = local_search(twin, Cc); s = st(a_c, Cc); print(f'climatology: optimized-on-clim split gap {s["gap_pct"]:.3f}% ; that split on E1 errors: {st(a_c, C1)["gap_pct"]:.3f}%')


if STAGE in ('oos', 'all'): stage_oos()
if STAGE in ('clim', 'all'): stage_clim()
print('total', time.time() - t0, 's')
