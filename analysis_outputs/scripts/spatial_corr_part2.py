# spatial_corr part 2: illustrate how split composition changes cross-group error cancellation (CF-anomaly proxy)
import numpy as np, pandas as pd
from scipy.cluster.hierarchy import linkage, leaves_list
BASE = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad"
OUT = f"{BASE}/analysis/out"
sites = pd.read_csv("C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset/sites.csv").set_index("site_id")
ids = list(sites.index); n = len(ids); cap = sites.capacity_kw.values.astype(float); TOTAL = cap.sum(); lo, hi = 20000.0, TOTAL - 20000.0
cf = pd.read_parquet(f"{BASE}/cache/cf_wide.parquet")[ids].loc["2024-08-01 01:00:00+09:00":"2025-06-01 00:00:00+09:00"]
cf = cf[cf.mean(axis=1) > 0.05]
an = (cf - cf.groupby([cf.index.month, cf.index.hour]).transform("mean")).astype(np.float32)
A = np.nan_to_num(an.values); print("rows", len(an), "missing frac %.4f" % np.isnan(an.values).mean())  # full-panel period: all 253 sites online
C = pd.read_csv(f"{OUT}/sc_corr_anom.csv", index_col=0).loc[ids, ids].values; np.fill_diagonal(C, 1); C = np.nan_to_num(C, nan=0.5)
Z = linkage(np.sqrt(np.clip(2 * (1 - (C + C.T) / 2), 0, 4))[np.triu_indices(n, 1)], method="ward"); order = leaves_list(Z)

def fix(mask):
    """move smallest sites across until group-1 capacity is inside [lo, hi]"""
    mask = mask.copy()
    for _ in range(300):
        s = cap[mask].sum()
        if lo <= s <= hi: return mask
        cand = np.where(~mask if s < lo else mask)[0]; k = cand[np.argmin(cap[cand])]; mask[k] = ~mask[k]
    return None
def evaluate(name, mask):
    E1 = A[:, mask] @ cap[mask]; E2 = A[:, ~mask] @ cap[~mask]
    return dict(split=name, G1_kW=cap[mask].sum(), G2_kW=cap[~mask].sum(), n1=int(mask.sum()), corr_G1_G2=np.corrcoef(E1, E2)[0, 1],
                same_sign_frac=np.mean(np.sign(E1) == np.sign(E2)), inflation=np.mean(np.abs(E1) + np.abs(E2)) / np.mean(np.abs(E1 + E2)),
                mean_abs_sum_kWcf=np.mean(np.abs(E1) + np.abs(E2)))
rows = []
ref = (sites.current_group == "A").values; rows.append(evaluate("reference A/B", ref))
sw = ref.copy(); sw[ids.index("PV215")] = False; sw[ids.index("PV240")] = True; rows.append(evaluate("reference + swap PV215<->PV240", sw))
alt = np.zeros(n, bool); alt[order[::2]] = True; alt = fix(alt); rows.append(evaluate("dendrogram-alternating (interleaved)", alt))
# twin-interleaved: greedy over twins table, each site opposite to its twin where possible, then fix
tw = pd.read_csv(f"{OUT}/sc_twins.csv", index_col=0)
assign = {}
for s in tw.sort_values("twin_anom_corr", ascending=False).index:
    t = tw.twin_anom[s]
    if s in assign: continue
    if t in assign: assign[s] = not assign[t]
    else: assign[s] = True; assign[t] = False
ti = fix(np.array([assign[s] for s in ids])); rows.append(evaluate("twin-opposite greedy", ti))
lat_order = np.argsort(-sites.lat.values); north = np.zeros(n, bool); north[lat_order[:np.searchsorted(np.cumsum(cap[lat_order]), lo) + 1]] = True
north = fix(north); rows.append(evaluate("regional: north vs south (by lat)", north))
lon_order = np.argsort(sites.lon.values); west = np.zeros(n, bool); west[lon_order[:np.searchsorted(np.cumsum(cap[lon_order]), lo) + 1]] = True
west = fix(west); rows.append(evaluate("regional: west vs east (by lon)", west))
for _ in range(3):
    r = fix(np.random.default_rng(_).random(n) < 0.5); rows.append(evaluate(f"random #{_}", r))
res = pd.DataFrame(rows); res.to_csv(f"{OUT}/sc_split_illustration.csv", index=False)
pd.set_option("display.width", 250); print(res.round(4))
