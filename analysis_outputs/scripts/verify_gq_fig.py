import pandas as pd, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
O = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad/analysis/out/"
R = pd.read_csv(O + "vq_night_rule_impact.csv")
hod = {6: 8608, 7: 9684, 8: 18039, 18: 25554, 19: 15212, 20: 16506, 21: 29}
fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
ax[0].barh(R.rule, R.kwh / 1000, color=["tab:red" if "mid<=0 (report" in r else "tab:gray" for r in R.rule]); ax[0].set_xlabel("kWh zeroed by rule (MWh)"); ax[0].set_title("Legit generation removed by each 'night' definition")
ax[1].bar(list(hod), [v / 1000 for v in hod.values()]); ax[1].set_xlabel("hour of day (ts, right-closed)"); ax[1].set_ylabel("MWh"); ax[1].set_title("Twilight (-6<elev_mid<=0) generation by hour")
plt.tight_layout(); plt.savefig(O + "vq_fig01_night_rule_impact.png", dpi=120); print("saved")
