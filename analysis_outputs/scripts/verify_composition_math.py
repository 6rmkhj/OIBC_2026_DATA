"""Adversarial check (math/logic lens) of the composition claim.
Independent recomputation from val_pred_site_E1_l1w.parquet + smp_all.parquet + sites.csv.
1) W_pool, W(split), gap% for reference / optimized_E1 / optimized_joint / twin_errcorr  (vs report 2.354 / 0.466 / 0.505 / 1.050)
2) identity  W - W_pool = 2 * sum_t w_t * min(|e1|,|e2|) * 1[sign(e1) != sign(e2)]
3) truly out-of-sample twin heuristic: pairs from TRAIN-period errors only, evaluated on the other period
"""
import numpy as np, pandas as pd, os
BASE = 'C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad/'
CACHE = BASE + 'cache/'; OUT = BASE + 'analysis/out/'
DATA = 'C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset/'
LO, HI = 20000.0, 22655.4

sites = pd.read_csv(DATA + 'sites.csv'); IDS = sites.site_id.tolist(); N = len(IDS)
CAP = sites.capacity_kw.values.astype(np.float64); TOT = CAP.sum(); HALF = TOT / 2
print('sites', N, 'total cap', round(TOT, 1))

d = pd.read_parquet(CACHE + 'val_pred_site_E1_l1w.parquet')
d['e'] = (d.pred - d.y).astype('float32')
E = d.pivot(index='ts', columns='site_id', values='e').reindex(columns=IDS)
ts = E.index; print('hours', len(ts), 'missing cells', int(E.isna().sum().sum()))
E = E.fillna(0).values.astype(np.float64); del d
smp = pd.read_parquet(CACHE + 'smp_all.parquet').set_index('ts').reindex(ts)
w = (smp.smp * smp.k).values.astype(np.float64); assert not np.isnan(w).any()
# k sanity: k=3 for hour in 11..15
hr = ts.hour.values; assert ((smp.k.values == 3) == np.isin(hr, [11, 12, 13, 14, 15])).all(), 'k mismatch'
tot = E.sum(1)
month = ts.month.values
wk = ts.isocalendar().week.values.astype(int)
periods = {'full': np.ones(len(w), bool), 'H1': np.isin(month, [6, 7, 8, 9, 10, 11]), 'H2': ~np.isin(month, [6, 7, 8, 9, 10, 11]),
           'Weven': wk % 2 == 0, 'Wodd': wk % 2 == 1}


def load_split(fn):
    s = pd.read_csv(OUT + fn).set_index('site_id').reindex(IDS)
    return (s.group.values == 'G1').astype(np.float64)


def W_parts(a, m):
    g1 = E[m] @ a; g2 = tot[m] - g1; ww = w[m]
    W = ww @ (np.abs(g1) + np.abs(g2)); Wp = ww @ np.abs(g1 + g2)
    ident = 2 * ww @ (np.minimum(np.abs(g1), np.abs(g2)) * (g1 * g2 < 0))
    return W, Wp, ident, np.corrcoef(g1, g2)[0, 1]


rows = []
splits = {'reference': 'composition_reference.csv', 'optimized_E1': 'composition_optimized_E1.csv',
          'optimized_joint_E1E7': 'composition_optimized_joint_E1E7.csv', 'twin_errcorr': 'composition_twin_errcorr.csv',
          'twin_gencorr': 'composition_twin_gencorr.csv'}
reported = {'reference': 2.354, 'optimized_E1': 0.466, 'optimized_joint_E1E7': 0.505, 'twin_errcorr': 1.050, 'twin_gencorr': 1.147}
ref_a = None
for nm, fn in splits.items():
    a = load_split(fn)
    if nm == 'reference': ref_a = a
    c1 = CAP @ a
    W, Wp, ident, r = W_parts(a, periods['full'])
    rows.append(dict(split=nm, cap_G1=round(c1, 2), feasible=LO <= c1 <= HI, W=W, W_pool=Wp, gap=W - Wp, gap_pct=100 * (W - Wp) / Wp,
                     identity_abs_diff=abs((W - Wp) - ident), corr_e1e2=r, reported_gap_pct=reported[nm]))
R = pd.DataFrame(rows); pd.set_option('display.width', 250)
print('\n== 1) recomputed gaps (full validation year, E1_l1w) ==')
print(R.to_string(index=False))
assert (R.identity_abs_diff < 1e-3 * R.gap).all(), 'identity failed'
# reference check vs sites.csv current_group
assert (ref_a == (sites.current_group.values == 'A')).all(), 'composition_reference.csv != current_group A->G1'
R.to_csv(OUT + 'vcm_recomputed_gaps.csv', index=False)

# ---------------------------------------------------------------- 3) truly OOS twin heuristic
def greedy_pairs(R):
    iu = np.triu_indices(N, 1); o = np.argsort(-R[iu]); used = np.zeros(N, bool); pairs = []
    for k in o:
        i, j = iu[0][k], iu[1][k]
        if not used[i] and not used[j]:
            used[i] = used[j] = True; pairs.append((i, j))
        if used.sum() >= N - 1: break
    return pairs, np.where(~used)[0]


def interleave(pairs, rest):
    """each pair -> different groups, larger member to the lighter group; leftover to lighter; then repair feasibility."""
    a = np.zeros(N); c = [0.0, 0.0]
    for i, j in sorted(pairs, key=lambda p: -(CAP[p[0]] + CAP[p[1]])):
        big, small = (i, j) if CAP[i] >= CAP[j] else (j, i)
        light = 1 if c[1] <= c[0] else 0
        a[big] = light; a[small] = 1 - light; c[light] += CAP[big]; c[1 - light] += CAP[small]
    for r in rest:
        light = 1 if c[1] <= c[0] else 0; a[r] = light; c[light] += CAP[r]
    for _ in range(N):
        c1 = CAP @ a
        if LO <= c1 <= HI: break
        heavy = 1 if c1 > HI else 0; idx = np.where(a == heavy)[0]; a[idx[np.argmin(CAP[idx])]] = 1 - heavy
    return a


def err_corr(m):
    X = E[m]; X = X[:, :]; keep = X.std(0) > 0
    R = np.zeros((N, N)); Rk = np.corrcoef(X[:, keep].T); R[np.ix_(keep, keep)] = Rk; np.fill_diagonal(R, 1); return R


rng = np.random.default_rng(0)
def random_mean_gap(m, n=300):
    out = []
    while len(out) < n:
        B = (rng.random((4 * n, N)) < 0.5).astype(np.float64); c1 = B @ CAP; B = B[(c1 >= LO) & (c1 <= HI)]
        for b in B:
            W, Wp, _, _ = W_parts(b, m); out.append(100 * (W - Wp) / Wp)
            if len(out) >= n: break
    return float(np.mean(out))

oos = []
for tr, te in [('H1', 'H2'), ('H2', 'H1'), ('Weven', 'Wodd'), ('Wodd', 'Weven')]:
    pairs, rest = greedy_pairs(err_corr(periods[tr]))
    a = interleave(pairs, rest)
    W_in, Wp_in, _, _ = W_parts(a, periods[tr]); W_te, Wp_te, _, r_te = W_parts(a, periods[te])
    W_ref, Wp_ref, _, _ = W_parts(ref_a, periods[te])
    W_tw, _, _, _ = W_parts(load_split('composition_twin_errcorr.csv'), periods[te])
    W_opt, _, _, _ = W_parts(load_split('composition_optimized_E1.csv'), periods[te])
    oos.append(dict(train=tr, test=te, cap_G1=round(CAP @ a, 1), gap_pct_in_sample=100 * (W_in - Wp_in) / Wp_in,
                    gap_pct_OOS_twin_trainonly=100 * (W_te - Wp_te) / Wp_te, corr_OOS=r_te,
                    gap_pct_ref_on_test=100 * (W_ref - Wp_ref) / Wp_ref,
                    gap_pct_fullyear_twin_on_test=100 * (W_tw - Wp_te) / Wp_te,
                    gap_pct_fullyear_opt_on_test=100 * (W_opt - Wp_te) / Wp_te,
                    gap_pct_random_mean_on_test=random_mean_gap(periods[te])))
O = pd.DataFrame(oos)
print('\n== 3) truly out-of-sample twin heuristic (pairs from TRAIN-period errors only) ==')
print(O.round(3).to_string(index=False))
O.to_csv(OUT + 'vcm_oos_twin_trainonly.csv', index=False)

# split-invariance of the pooled bound: W_pool must not depend on the split (bottom-up forecasts)
Wp_vals = [W_parts(load_split(fn), periods['full'])[1] for fn in splits.values()]
print('\nW_pool across splits (must be identical):', [round(x) for x in Wp_vals])
