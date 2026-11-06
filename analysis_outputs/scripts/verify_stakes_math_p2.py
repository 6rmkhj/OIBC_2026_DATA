import numpy as np, pandas as pd
BASE = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad"
DS = "C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset"; TZ = "Asia/Seoul"
V0, V1 = pd.Timestamp('2024-06-01 01:00', tz=TZ), pd.Timestamp('2025-06-01 00:00', tz=TZ)
cap = pd.read_csv(f"{DS}/sites.csv").set_index('site_id').capacity_kw.astype('float64')
cf = pd.read_parquet(f"{BASE}/cache/cf_wide.parquet"); cf = cf.loc[(cf.index >= V0) & (cf.index <= V1), cap.index].astype('float64')
kwh_raw = (cf * cap.values).sum(axis=1, min_count=1)
t = pd.read_csv(f"{DS}/train/smp.csv"); t['ts'] = pd.to_datetime(t.ts, utc=True).dt.tz_convert(TZ); t = t[(t.ts >= V0) & (t.ts <= V1)].set_index('ts').smp.astype('float64')
h = t.index.hour.values; wv = t.values * np.where((h >= 11) & (h <= 15), 3, 1)
Bv_raw = (wv * kwh_raw.reindex(t.index).fillna(0).values).sum()
print(f"val-year sum w*actual (raw reporting sites) = {Bv_raw:.4e}  (model_validation quotes 1.728e10)")
B_test = 1.51131e10; r = pd.read_csv(f"{BASE}/analysis/out/results_table.csv").set_index('name')
for m in ['E4_blend50', 'E7_mix_site10', 'E1_l1w', 'E0_site']:
    if m in r.index:
        pct = r.loc[m, 'W_ref_pct'] / 100; Wv = r.loc[m, 'W_ref']
        print(f"{m}: val W_ref={Wv:.4e} ({pct:.4%}) -> val penalty 0.1W = {0.1*Wv/1e8:.3f}억 ; test-year est. penalty = 0.10*pct*B_test = {0.10*pct*B_test/1e8:.3f}억 ; 1% rel. improvement = {0.01*0.10*pct*B_test/1e4:.0f}만원 ; 1%p = {0.001*B_test/1e4:.0f}만원")
print("ratio test/val B (clim) 0.837 x scale-up 58.81/56.41 =", round(0.837 * 58.8101 / 56.4119, 4))
