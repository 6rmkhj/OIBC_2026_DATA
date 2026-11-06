# smp_weights: SMP*k weight analysis for OIBC 2026 (test year 2025-06 ~ 2026-05)
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

BASE = "C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad"
CACHE = BASE + "/cache"; OUT = BASE + "/analysis/out"
SITES = "C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset/sites.csv"
PAL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948']
SEQ = LinearSegmentedColormap.from_list('blue', ['#fcfcfb', '#cde2fb', '#6da7ec', '#2a78d6', '#184f95', '#0d366b'])
MONTH_ORDER = [6, 7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5]
MLAB = ['Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May']
TZ = "Asia/Seoul"
plt.rcParams.update({'figure.facecolor': '#fcfcfb', 'axes.facecolor': '#fcfcfb', 'axes.edgecolor': '#c3c2b7',
                     'axes.grid': True, 'grid.color': '#e6e5e0', 'grid.linewidth': 0.6, 'axes.spines.top': False,
                     'axes.spines.right': False, 'font.size': 9, 'savefig.dpi': 130, 'axes.axisbelow': True})

def sect(t): print("\n" + "=" * 12 + " " + t + " " + "=" * 12)
def heat(mat, title, cbar, fname, fmt=None, cmap=SEQ):
    fig, ax = plt.subplots(figsize=(8.5, 6.5))
    im = ax.imshow(mat.values, aspect='auto', cmap=cmap, origin='lower')
    ax.set_xticks(range(12)); ax.set_xticklabels(MLAB); ax.set_yticks(range(0, 24, 1)); ax.set_yticklabels(mat.index)
    ax.set_xlabel('Month (test year Jun 2025 -> May 2026)'); ax.set_ylabel('Hour (ts, right-closed)'); ax.set_title(title)
    ax.grid(False); fig.colorbar(im, ax=ax, label=cbar)
    if fmt:
        v = mat.values; thr = np.nanmax(v) * 0.55
        for i in range(v.shape[0]):
            for j in range(v.shape[1]):
                if np.isfinite(v[i, j]) and v[i, j] > 0:
                    ax.text(j, i, fmt(v[i, j]), ha='center', va='center', fontsize=6, color='#f0efec' if v[i, j] > thr else '#0b0b0b')
    fig.tight_layout(); fig.savefig(f"{OUT}/smpw_{fname}"); plt.close(fig)

# ---------------------------------------------------------------- load SMP
s = pd.read_parquet(f"{CACHE}/smp_all.parquet")
s['hour'] = s.ts.dt.hour.astype('int16'); s['month'] = s.ts.dt.month.astype('int8'); s['year'] = s.ts.dt.year.astype('int16')
assert (s.k.values == np.where(s.hour.between(11, 15), 3, 1)).all(), "k != hour rule"
s['w'] = (s.smp * s.k).astype('float32')
s['pvyear'] = np.where(s.month >= 6, s.year, s.year - 1).astype('int16')   # Jun Y..May Y+1 -> Y
T0, T1 = pd.Timestamp('2025-06-01 01:00', tz=TZ), pd.Timestamp('2026-06-01 00:00', tz=TZ)
V0, V1 = pd.Timestamp('2024-06-01 01:00', tz=TZ), pd.Timestamp('2025-06-01 00:00', tz=TZ)
test = s[(s.ts >= T0) & (s.ts <= T1)].copy(); val = s[(s.ts >= V0) & (s.ts <= V1)].copy()
assert len(test) == 8760, len(test); print("val rows", len(val))
full = pd.date_range(s.ts.min(), s.ts.max(), freq='h', tz=TZ); print("smp_all rows", len(s), "expected", len(full), "dups", s.ts.duplicated().sum())

# ---------------------------------------------------------------- climatological CF (last training year)
sites = pd.read_csv(SITES, usecols=['site_id', 'capacity_kw', 'current_group'])
cap = sites.set_index('site_id').capacity_kw.astype('float32'); TOTAL_CAP = float(cap.sum()); print("total cap kW", TOTAL_CAP)
cf = pd.read_parquet(f"{CACHE}/cf_wide.parquet"); cf = cf.loc[(cf.index >= V0) & (cf.index <= V1)]
cf = cf[cap.index]; print("cf val-year rows", len(cf))
kwh_avail = (cf * cap.values).sum(axis=1, min_count=1).astype('float32')
cap_avail = ((~cf.isna()) * cap.values).sum(axis=1).astype('float32')
avail_frac = cap_avail / TOTAL_CAP
print("availability frac: mean %.3f min %.3f  hours<0.8: %d" % (avail_frac.mean(), avail_frac.min(), (avail_frac < 0.8).sum()))
port = (kwh_avail / cap_avail.replace(0, np.nan) * TOTAL_CAP)          # scaled to full portfolio
port = port.where(avail_frac >= 0.5)                                    # ponytail: drop hours with <50% cap reporting
del cf
pf = pd.DataFrame({'kwh': port.values.astype('float32')}, index=port.index)
pf = pf.reindex(pd.date_range(V0, V1, freq='h', tz=TZ)); pf['month'] = pf.index.month; pf['hour'] = pf.index.hour
clim = pf.groupby(['month', 'hour']).kwh.mean()
clim_mat = clim.unstack('month')[MONTH_ORDER]; clim_mat.columns = MLAB
clim_mat.to_csv(f"{OUT}/smpw_clim_portfolio_kwh_hour_month.csv")
print("val-year portfolio kWh observed(scaled) sum: %.3e ; missing hours: %d" % (pf.kwh.sum(), pf.kwh.isna().sum()))
daylight_hours = sorted(clim_mat.index[(clim_mat.max(axis=1) > 0.01 * clim_mat.values.max())].tolist())
print("daylight hours (clim kWh > 1% of peak in some month):", daylight_hours)
heat(clim_mat, 'Climatological portfolio generation (kWh per hour), Jun 2024 - May 2025, scaled to 42,655 kW',
     'kWh / hour', 'fig05_clim_kwh_heatmap.png', fmt=lambda v: f"{v/1000:.1f}k" if v >= 100 else "")

# ---------------------------------------------------------------- (1) test-year weight profile
sect("1. TEST-YEAR WEIGHTS w = SMP*k")
test['kwh_clim'] = clim.reindex(pd.MultiIndex.from_arrays([test.month, test.hour])).values.astype('float32')
test['w_kwh'] = test.w * test.kwh_clim          # penalty exposure per unit relative error (KRW)
test['rev'] = test.smp * test.kwh_clim
print("test SMP: mean %.2f median %.2f std %.2f min %.2f max %.2f ; mean w %.2f" % (test.smp.mean(), test.smp.median(), test.smp.std(), test.smp.min(), test.smp.max(), test.w.mean()))
by_hour = test.groupby('hour').agg(smp_mean=('smp', 'mean'), smp_min=('smp', 'min'), w_mean=('w', 'mean'), w_sum=('w', 'sum'), zero_smp_hours=('smp', lambda x: int((x == 0).sum())),
                                   low10_hours=('smp', lambda x: int((x <= 10).sum())), kwh_clim=('kwh_clim', 'mean'), exposure=('w_kwh', 'sum'))
by_hour['w_share'] = by_hour.w_sum / by_hour.w_sum.sum(); by_hour['exposure_share'] = by_hour.exposure / by_hour.exposure.sum()
by_hour.to_csv(f"{OUT}/smpw_test_w_by_hour.csv", float_format='%.4f'); print(by_hour.round(3).to_string())
by_month = test.groupby('month').agg(smp_mean=('smp', 'mean'), w_mean=('w', 'mean'), w_sum=('w', 'sum'), zero_smp_hours=('smp', lambda x: int((x == 0).sum())),
                                     low10_hours=('smp', lambda x: int((x <= 10).sum())), low50_hours=('smp', lambda x: int((x <= 50).sum())), exposure=('w_kwh', 'sum'), rev=('rev', 'sum'))
by_month = by_month.loc[MONTH_ORDER]; by_month['w_share'] = by_month.w_sum / by_month.w_sum.sum(); by_month['exposure_share'] = by_month.exposure / by_month.exposure.sum()
by_month.index = list(MLAB)
by_month.to_csv(f"{OUT}/smpw_test_w_by_month.csv", float_format='%.4f'); print(by_month.round(3).to_string())
w_mat = test.pivot_table(index='hour', columns='month', values='w', aggfunc='mean')[MONTH_ORDER]; w_mat.columns = MLAB
w_mat.to_csv(f"{OUT}/smpw_test_w_hour_month.csv", float_format='%.2f')
smp_mat = test.pivot_table(index='hour', columns='month', values='smp', aggfunc='mean')[MONTH_ORDER]; smp_mat.columns = MLAB
smp_mat.to_csv(f"{OUT}/smpw_test_smp_hour_month.csv", float_format='%.2f')
pk = test.hour.between(11, 15); day = test.hour.isin(daylight_hours)
sh = dict(share_w_1115_of_all=test.w[pk].sum() / test.w.sum(), share_w_1115_of_daylight=test.w[pk].sum() / test.w[day].sum(),
          share_smp_1115_of_all=test.smp[pk].sum() / test.smp.sum(), share_smp_1115_of_daylight=test.smp[pk].sum() / test.smp[day].sum(),
          share_exposure_1115=test.w_kwh[pk].sum() / test.w_kwh.sum(), share_kwh_1115=test.kwh_clim[pk].sum() / test.kwh_clim.sum(),
          share_exposure_daylight_hours=test.w_kwh[day].sum() / test.w_kwh.sum(),
          smp_mean_1115=test.smp[pk].mean(), smp_mean_other_daylight=test.smp[day & ~pk].mean(), smp_mean_night=test.smp[~day].mean(),
          w_mean_1115=test.w[pk].mean(), w_mean_other_daylight=test.w[day & ~pk].mean())
for k_, v_ in sh.items(): print(f"{k_}: {v_:.4f}")
pd.Series(sh).to_csv(f"{OUT}/smpw_test_shares.csv", header=['value'])
z = test[test.smp == 0][['ts', 'hour', 'k', 'kwh_clim']].copy(); z['date'] = z.ts.dt.date; z['dow'] = z.ts.dt.day_name()
z.to_csv(f"{OUT}/smpw_zero_smp_hours_test.csv", index=False)
low = test[test.smp <= 10][['ts', 'smp', 'hour', 'k', 'kwh_clim']].copy(); low['date'] = low.ts.dt.date; low['dow'] = low.ts.dt.day_name()
low.to_csv(f"{OUT}/smpw_low_smp_hours_test.csv", index=False)
print(f"zero-SMP hours in test: {len(z)} ({len(z)/87.6:.2f}% of hours); in 11-15h: {int(z.k.eq(3).sum())}; distinct days: {z.date.nunique()}")
print("zero hours by hour:", z.hour.value_counts().sort_index().to_dict()); print("zero hours by month:", z.ts.dt.month.value_counts().sort_index().to_dict())
print("zero hours by weekday:", z.dow.value_counts().to_dict())
print("zero-SMP list (date,hour):", [(str(d), int(h)) for d, h in zip(z.date, z.hour)])
print(f"SMP<=10 hours: {len(low)}; SMP<=50: {int((test.smp<=50).sum())}; SMP<=80: {int((test.smp<=80).sum())}; share of clim kWh falling in zero-SMP hours: {z.kwh_clim.sum()/test.kwh_clim.sum():.4%}; in SMP<=10 hours: {low.kwh_clim.sum()/test.kwh_clim.sum():.4%}")
print("low (<=10) hours by month:", low.ts.dt.month.value_counts().sort_index().to_dict(), " by hour:", low.hour.value_counts().sort_index().to_dict())
print("low (<=10) list (date,hour,smp):", [(str(d), int(h), float(v)) for d, h, v in zip(low.date, low.hour, low.smp)])
zh = s[s.smp == 0].groupby('pvyear').size(); print("zero-SMP hours by PV-year (all history):", zh.to_dict())
lh = s[s.smp <= 10].groupby('pvyear').size(); print("SMP<=10 hours by PV-year:", lh.to_dict())
l50 = s[s.smp <= 50].groupby('pvyear').size(); print("SMP<=50 hours by PV-year:", l50.to_dict())
fig, ax = plt.subplots(figsize=(9, 4))
ax.bar(by_hour.index, by_hour.w_mean, color=[PAL[1] if 11 <= h <= 15 else PAL[0] for h in by_hour.index], width=0.8, edgecolor='#fcfcfb')
ax.plot(by_hour.index, by_hour.smp_mean, color='#0b0b0b', lw=2, marker='o', ms=4, label='mean SMP (KRW/kWh)')
ax.set_xticks(range(24)); ax.set_xlabel('Hour (ts, right-closed)'); ax.set_ylabel('KRW/kWh'); ax.set_title('Test year: mean weight w = SMP x k by hour (orange = k=3, 11-15h)')
ax.legend(loc='upper left', frameon=False); fig.tight_layout(); fig.savefig(f"{OUT}/smpw_fig01_test_w_by_hour.png"); plt.close(fig)
fig, ax = plt.subplots(figsize=(9, 4))
ax.bar(range(12), by_month.w_mean, color=PAL[0], width=0.8, edgecolor='#fcfcfb', label='mean w = SMP x k')
ax.plot(range(12), by_month.smp_mean, color='#0b0b0b', lw=2, marker='o', ms=4, label='mean SMP')
ax.set_xticks(range(12)); ax.set_xticklabels(MLAB); ax.set_ylabel('KRW/kWh'); ax.set_title('Test year: mean weight and SMP by month'); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(f"{OUT}/smpw_fig02_test_w_by_month.png"); plt.close(fig)
heat(w_mat, 'Test year: mean weight w = SMP x k (KRW/kWh) by hour x month', 'KRW/kWh', 'fig03_test_w_heatmap.png', fmt=lambda v: f"{v:.0f}")
fig, axes = plt.subplots(1, 2, figsize=(11, 4), gridspec_kw={'width_ratios': [3, 1]})
ax = axes[0]; ax.scatter(low.ts.dt.tz_localize(None), low.hour, s=28, color=PAL[3], label='0 < SMP <= 10', zorder=2)
ax.scatter(z.ts.dt.tz_localize(None), z.hour, s=28, color=PAL[7], label='SMP = 0', zorder=3)
ax.axhspan(10.5, 15.5, color=PAL[1], alpha=0.12, lw=0, label='k=3 band (11-15h)'); ax.set_ylim(-0.5, 23.5); ax.set_yticks(range(0, 24, 2))
ax.set_xlim(pd.Timestamp('2025-06-01'), pd.Timestamp('2026-06-01'))
ax.set_title('Test year: zero / near-zero SMP hours'); ax.set_ylabel('Hour'); ax.legend(frameon=False, loc='upper right'); fig.autofmt_xdate()
ax = axes[1]; zc = z.ts.dt.month.value_counts().reindex(MONTH_ORDER, fill_value=0); lc = low.ts.dt.month.value_counts().reindex(MONTH_ORDER, fill_value=0)
ax.bar(range(12), lc.values, color=PAL[3], label='SMP<=10'); ax.bar(range(12), zc.values, color=PAL[7], label='SMP=0'); ax.set_xticks(range(12)); ax.set_xticklabels(MLAB, rotation=90)
ax.set_title('Count by month'); ax.legend(frameon=False); fig.tight_layout(); fig.savefig(f"{OUT}/smpw_fig04_zero_smp_hours.png"); plt.close(fig)

# ---------------------------------------------------------------- (2) effective penalty exposure
sect("2. EFFECTIVE PENALTY EXPOSURE  (w x climatological kWh)")
exp_mat = test.pivot_table(index='hour', columns='month', values='w_kwh', aggfunc='sum')[MONTH_ORDER]; exp_mat.columns = MLAB
exp_share = exp_mat / exp_mat.values.sum(); exp_share.to_csv(f"{OUT}/smpw_exposure_share_hour_month.csv", float_format='%.5f')
(exp_mat / 1e6).to_csv(f"{OUT}/smpw_exposure_MKRW_hour_month.csv", float_format='%.3f')
B = float(test.w_kwh.sum()); R = float(test.rev.sum())
print(f"penalty base B = sum_t w_t*kWh_clim_t = {B:.4e} KRW ; revenue proxy R = sum_t SMP_t*kWh_clim_t = {R:.4e} KRW ; B/R = {B/R:.3f}")
print(f"kWh-weighted mean w (KRW per kWh of error, if error prop. to generation) = {B/test.kwh_clim.sum():.2f} ; kWh-weighted mean SMP = {R/test.kwh_clim.sum():.2f}")
top = exp_share.stack().sort_values(ascending=False).head(15); print("top-15 (hour, month) cells by exposure share %:"); print((top * 100).round(2).to_string())
print("exposure share by hour %:"); print((by_hour.exposure_share * 100).round(2).to_string())
print("exposure share by month %:"); print((by_month.exposure_share * 100).round(2).to_string())
cum = by_hour.exposure_share.sort_values(ascending=False).cumsum(); print("hours needed to cover 50/80/95% of exposure:", int((cum < 0.5).sum() + 1), int((cum < 0.8).sum() + 1), int((cum < 0.95).sum() + 1))
heat(exp_share * 100, 'Penalty exposure share (%): sum of w x climatological kWh, hour x month', '% of total exposure', 'fig06_exposure_heatmap.png', fmt=lambda v: f"{v:.1f}")

# ---------------------------------------------------------------- (3) compare to prior years
sect("3. SMP LEVEL & SHAPE vs PRIOR YEARS (PV-year = Jun..May)")
def yr_stats(g):
    pk = g.hour.between(11, 15); dl = g.hour.isin(daylight_hours); ev = g.hour.between(18, 21); mid = g.hour.between(12, 14)
    return pd.Series(dict(hours=len(g), smp_mean=g.smp.mean(), smp_median=g.smp.median(), smp_std=g.smp.std(), smp_p10=g.smp.quantile(.1), smp_p90=g.smp.quantile(.9),
                          w_mean=g.w.mean(), smp_1115=g.smp[pk].mean(), smp_daylight=g.smp[dl].mean(), smp_night=g.smp[~dl].mean(), smp_1821=g.smp[ev].mean(),
                          midday_ratio_1115_all=g.smp[pk].mean() / g.smp.mean(), midday_ratio_1214_evening=g.smp[mid].mean() / g.smp[ev].mean(),
                          duck_depth_pct=100 * (1 - g.smp[mid].mean() / g.smp[ev].mean()),
                          share_w_1115=g.w[pk].sum() / g.w.sum(), zero_hours=int((g.smp == 0).sum()), le10_hours=int((g.smp <= 10).sum()), le50_hours=int((g.smp <= 50).sum()),
                          cv_hourly_profile=(g.groupby('hour').smp.mean().std() / g.smp.mean())))
ys = s[s.pvyear.between(2021, 2025)].groupby('pvyear').apply(yr_stats, include_groups=False); ys.index = [f"PV{y} (Jun{y}-May{y+1})" for y in ys.index]
ys.to_csv(f"{OUT}/smpw_year_compare_pvyear.csv", float_format='%.4f'); print(ys.round(3).T.to_string())
cy = s[s.year.between(2021, 2026)].groupby('year').apply(yr_stats, include_groups=False); cy.to_csv(f"{OUT}/smpw_year_compare_calendar.csv", float_format='%.4f')
print("calendar-year view:"); print(cy[['hours', 'smp_mean', 'smp_median', 'midday_ratio_1115_all', 'duck_depth_pct', 'zero_hours', 'le10_hours']].round(3).to_string())
mon_y = s[s.pvyear.between(2021, 2025)].pivot_table(index='month', columns='pvyear', values='smp', aggfunc='mean').loc[MONTH_ORDER]; mon_y.index = MLAB
mon_y.columns = [f"PV{c}" for c in mon_y.columns]; mon_y.to_csv(f"{OUT}/smpw_smp_month_by_pvyear.csv", float_format='%.2f'); print("monthly mean SMP by PV-year:"); print(mon_y.round(1).to_string())
print("test / prior ratio by month:"); print((mon_y[['PV2021', 'PV2022', 'PV2023', 'PV2024']].rdiv(mon_y['PV2025'], axis=0)).round(3).to_string())
hp = s[s.pvyear.between(2021, 2025)].pivot_table(index='hour', columns='pvyear', values='smp', aggfunc='mean'); hp.columns = [f"PV{c}" for c in hp.columns]
hp.to_csv(f"{OUT}/smpw_smp_hourly_profile_by_pvyear.csv", float_format='%.2f'); hpn = hp / hp.mean(); hpn.to_csv(f"{OUT}/smpw_smp_hourly_profile_norm_by_pvyear.csv", float_format='%.4f')
print("normalized hourly profile (mean=1):"); print(hpn.round(3).to_string())
dd = s[s.pvyear.between(2021, 2025)].copy(); dd['band'] = np.where(dd.hour.between(12, 14), 'mid', np.where(dd.hour.between(18, 21), 'eve', 'x'))
dm = dd[dd.band != 'x'].pivot_table(index=['pvyear', 'month'], columns='band', values='smp', aggfunc='mean'); dm['duck_depth_pct'] = 100 * (1 - dm.mid / dm.eve)
duck_my = dm.duck_depth_pct.unstack('pvyear').loc[MONTH_ORDER]; duck_my.index = MLAB; duck_my.columns = [f"PV{c}" for c in duck_my.columns]
duck_my.to_csv(f"{OUT}/smpw_duck_depth_month_by_pvyear.csv", float_format='%.2f'); print("duck depth % (1 - SMP12-14 / SMP18-21) by month x PV-year:"); print(duck_my.round(1).to_string())
del dd, dm
pk_my = s[s.pvyear.between(2021, 2025)].assign(pk=lambda d: d.hour.between(11, 15)).groupby(['pvyear', 'month']).apply(lambda g: g.w[g.pk].sum() / g.w.sum(), include_groups=False).unstack('pvyear').loc[MONTH_ORDER]
pk_my.index = MLAB; pk_my.columns = [f"PV{c}" for c in pk_my.columns]; pk_my.to_csv(f"{OUT}/smpw_share_w_1115_month_by_pvyear.csv", float_format='%.4f'); print("share of w in 11-15h by month x PV-year:"); print(pk_my.round(3).to_string())
yrs = list(hp.columns)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
for i, c in enumerate(yrs):
    lw = 2.6 if c == 'PV2025' else 1.6
    axes[0].plot(hp.index, hp[c], color=PAL[i], lw=lw, label=c + (' (test)' if c == 'PV2025' else '')); axes[1].plot(hpn.index, hpn[c], color=PAL[i], lw=lw, label=c)
axes[0].set_title('Mean SMP by hour (KRW/kWh)'); axes[1].set_title('Hourly profile normalized by yearly mean'); axes[1].axhline(1, color='#c3c2b7', lw=1)
for ax in axes: ax.set_xticks(range(0, 24, 2)); ax.set_xlabel('Hour'); ax.axvspan(10.5, 15.5, color=PAL[1], alpha=0.08, lw=0)
axes[0].legend(frameon=False); fig.tight_layout(); fig.savefig(f"{OUT}/smpw_fig07_smp_hourly_by_pvyear.png"); plt.close(fig)
fig, ax = plt.subplots(figsize=(9, 4.2))
for i, c in enumerate(mon_y.columns): ax.plot(range(12), mon_y[c], color=PAL[i], lw=2.6 if c == 'PV2025' else 1.6, marker='o', ms=3, label=c + (' (test)' if c == 'PV2025' else ''))
ax.set_xticks(range(12)); ax.set_xticklabels(MLAB); ax.set_ylabel('KRW/kWh'); ax.set_title('Monthly mean SMP, same months across PV-years (Jun->May)'); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(f"{OUT}/smpw_fig08_smp_monthly_by_pvyear.png"); plt.close(fig)
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
ax = axes[0]; ax.bar(range(5), ys.duck_depth_pct.values, color=[PAL[0]] * 4 + [PAL[1]]); ax.set_xticks(range(5)); ax.set_xticklabels([c[:6] for c in ys.index]); ax.set_title('Duck depth: 1 - SMP(12-14h)/SMP(18-21h), %')
ax = axes[1]; ax.bar(range(5), 100 * ys.share_w_1115.values, color=[PAL[0]] * 4 + [PAL[1]]); ax.set_xticks(range(5)); ax.set_xticklabels([c[:6] for c in ys.index]); ax.set_title('Share of yearly weight w in 11-15h, %')
ax = axes[2]
for i, c in enumerate(duck_my.columns): ax.plot(range(12), duck_my[c], color=PAL[i], lw=2.6 if c == 'PV2025' else 1.6, marker='o', ms=3, label=c)
ax.set_xticks(range(12)); ax.set_xticklabels(MLAB); ax.axhline(0, color='#c3c2b7', lw=1); ax.set_title('Duck depth by month, %'); ax.legend(frameon=False, fontsize=7)
fig.tight_layout(); fig.savefig(f"{OUT}/smpw_fig09_duck_trend.png"); plt.close(fig)

# ---------------------------------------------------------------- (4) validation-year vs test-year weights
sect("4. VALIDATION-YEAR (PV2024) vs TEST-YEAR (PV2025) WEIGHTS")
val['kwh_clim'] = clim.reindex(pd.MultiIndex.from_arrays([val.month, val.hour])).values.astype('float32'); val['w_kwh'] = val.w * val.kwh_clim
vm = val.pivot_table(index='hour', columns='month', values='w', aggfunc='mean')[MONTH_ORDER]; vm.columns = MLAB
tm = w_mat
r_mh = np.corrcoef(vm.values.ravel(), tm.values.ravel())[0, 1]
vh = val.groupby('hour').w.mean(); th = test.groupby('hour').w.mean(); vmo = val.groupby('month').w.mean().loc[MONTH_ORDER]; tmo = test.groupby('month').w.mean().loc[MONTH_ORDER]
print(f"mean w: val {val.w.mean():.2f} test {test.w.mean():.2f} ratio {test.w.mean()/val.w.mean():.3f} ; mean SMP val {val.smp.mean():.2f} test {test.smp.mean():.2f}")
print(f"corr of (month,hour) mean-w matrices val vs test: {r_mh:.3f} ; corr hour profiles: {np.corrcoef(vh, th)[0,1]:.3f} ; corr month profiles: {np.corrcoef(vmo, tmo)[0,1]:.3f}")
print(f"share w 11-15: val {val.w[val.hour.between(11,15)].sum()/val.w.sum():.4f} test {sh['share_w_1115_of_all']:.4f}")
print(f"zero hours: val {int((val.smp==0).sum())} test {len(z)} ; <=10: val {int((val.smp<=10).sum())} test {len(low)} ; <=50: val {int((val.smp<=50).sum())} test {int((test.smp<=50).sum())}")
Bv = float(val.w_kwh.sum()); print(f"penalty base with same clim kWh: val-year w {Bv:.4e}  test-year w {B:.4e}  ratio test/val {B/Bv:.3f}")
ev = val.groupby('hour').w_kwh.sum() / Bv; et = by_hour.exposure_share
print("exposure share by hour, val vs test (pp diff):"); print(pd.DataFrame({'val': ev * 100, 'test': et * 100, 'diff_pp': (et - ev) * 100}).round(2).loc[daylight_hours].to_string())
evm = val.groupby('month').w_kwh.sum().loc[MONTH_ORDER] / Bv; etm = by_month.exposure_share.values
print("exposure share by month, val vs test:"); print(pd.DataFrame({'val': evm.values * 100, 'test': etm * 100, 'diff_pp': (etm - evm.values) * 100}, index=MLAB).round(2).to_string())
def r2(pred): pred = np.asarray(pred, dtype='float64'); return 1 - ((test.w.values - pred) ** 2).sum() / ((test.w.values - test.w.mean()) ** 2).sum()
k_only = test.k.values * test.w.mean() / test.k.mean()
mi = pd.MultiIndex.from_arrays([test.month.values, test.hour.values])
tm_long = tm.rename(columns={MLAB[i]: MONTH_ORDER[i] for i in range(12)}).stack(); tm_long.index = tm_long.index.swaplevel(); vm_long = vm.rename(columns={MLAB[i]: MONTH_ORDER[i] for i in range(12)}).stack(); vm_long.index = vm_long.index.swaplevel()
mh_test = tm_long.reindex(mi).values; mh_val = vm_long.reindex(mi).values
r2s = dict(k_only=r2(k_only), hour_means_test=r2(test.hour.map(th).values), month_hour_means_test=r2(mh_test),
           hour_means_val_rescaled=r2(test.hour.map(vh).values * test.w.mean() / val.w.mean()), month_hour_means_val_rescaled=r2(mh_val * test.w.mean() / val.w.mean()),
           month_hour_means_val_raw=r2(mh_val), day_specific_test=1.0)
print("R^2 of test-year hourly w explained by weighting scheme:"); [print(f"  {a}: {b:.3f}") for a, b in r2s.items()]
pd.Series(r2s).to_csv(f"{OUT}/smpw_w_scheme_r2.csv", header=['r2'])
pd.DataFrame({'w_hour_val': vh, 'w_hour_test': th, 'exp_share_val': ev, 'exp_share_test': et}).to_csv(f"{OUT}/smpw_val_vs_test_by_hour.csv", float_format='%.4f')
pd.DataFrame({'w_month_val': vmo.values, 'w_month_test': tmo.values, 'exp_share_val': evm.values, 'exp_share_test': etm}, index=MLAB).to_csv(f"{OUT}/smpw_val_vs_test_by_month.csv", float_format='%.4f')
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
axes[0].plot(vh.index, vh, color=PAL[0], lw=2, marker='o', ms=3, label='validation year PV2024'); axes[0].plot(th.index, th, color=PAL[1], lw=2, marker='o', ms=3, label='test year PV2025')
axes[0].set_title('Mean w = SMP x k by hour'); axes[0].set_xticks(range(0, 24, 2)); axes[0].legend(frameon=False)
axes[1].plot(range(12), vmo.values, color=PAL[0], lw=2, marker='o', ms=3, label='validation'); axes[1].plot(range(12), tmo.values, color=PAL[1], lw=2, marker='o', ms=3, label='test')
axes[1].set_xticks(range(12)); axes[1].set_xticklabels(MLAB); axes[1].set_title('Mean w by month'); axes[1].legend(frameon=False)
x = np.arange(len(daylight_hours)); axes[2].bar(x - 0.2, 100 * ev.loc[daylight_hours], 0.4, color=PAL[0], label='validation w'); axes[2].bar(x + 0.2, 100 * et.loc[daylight_hours], 0.4, color=PAL[1], label='test w')
axes[2].set_xticks(x); axes[2].set_xticklabels(daylight_hours); axes[2].set_title('Exposure share by hour (%), same clim kWh'); axes[2].legend(frameon=False)
fig.tight_layout(); fig.savefig(f"{OUT}/smpw_fig10_val_vs_test_w.png"); plt.close(fig)

# ---------------------------------------------------------------- (5) stakes in KRW
sect("5. STAKES (KRW)")
print(f"annual climatological portfolio energy: {test.kwh_clim.sum():.4e} kWh = {test.kwh_clim.sum()/1e6:.2f} GWh ; capacity factor {test.kwh_clim.sum()/(TOTAL_CAP*8760):.4f}")
print(f"revenue term (test SMP x clim kWh): {R:.4e} KRW = {R/1e8:.2f} eok-won ; mean realized SMP per kWh {R/test.kwh_clim.sum():.2f}")
rows = []
for r in [0.05, 0.08, 0.10, 0.125, 0.15, 0.20]:
    P = 0.10 * r * B; rows.append(dict(convention='weighted MAE as % of weighted actual kWh', level=f"{r:.1%}", penalty_KRW=P, penalty_eokwon=P / 1e8, penalty_pct_of_revenue=100 * P / R, score_S=R - P))
Wd = float(test.w[day].sum()); n_day = int(day.sum())
for n in [0.02, 0.03, 0.05, 0.08]:
    P = 0.10 * n * TOTAL_CAP * Wd; rows.append(dict(convention=f'|e1|+|e2| = nMAE x 42,655 kW every daylight hour ({n_day} h)', level=f"{n:.0%} of capacity", penalty_KRW=P, penalty_eokwon=P / 1e8, penalty_pct_of_revenue=100 * P / R, score_S=R - P))
st = pd.DataFrame(rows); st.to_csv(f"{OUT}/smpw_stakes.csv", index=False, float_format='%.1f'); print(st.to_string())
print(f"value of 1 percentage-point of weighted MAE (of weighted actual): {0.001*B:.4e} KRW = {0.001*B/1e4:.0f} man-won /yr")
print(f"value of 1% RELATIVE penalty reduction at 12.5% wMAE: {0.01*0.10*0.125*B:.4e} KRW = {0.01*0.10*0.125*B/1e4:.0f} man-won /yr")
print(f"value of 1 pp of capacity-normalised MAE (daylight hours): {0.10*0.01*TOTAL_CAP*Wd:.4e} KRW = {0.10*0.01*TOTAL_CAP*Wd/1e4:.0f} man-won /yr")
print(f"penalty per 1 MWh of error in an average 11-15h hour: {0.10*1000*test.w[pk].mean():.0f} KRW ; in an average other daylight hour: {0.10*1000*test.w[day & ~pk].mean():.0f} KRW ; max single hour w: {test.w.max():.1f} on {test.loc[test.w.idxmax(),'ts']}")
fig, ax = plt.subplots(figsize=(8, 4)); rr = np.linspace(0, 0.25, 26); ax.plot(100 * rr, 0.10 * rr * B / 1e8, color=PAL[1], lw=2.2)
for r in [0.05, 0.10, 0.15, 0.20]: ax.scatter([100 * r], [0.10 * r * B / 1e8], color=PAL[1], s=30, zorder=3); ax.annotate(f"{0.10*r*B/1e8:.2f}", (100 * r, 0.10 * r * B / 1e8), textcoords='offset points', xytext=(4, -12), fontsize=8)
ax.set_xlabel('weighted MAE, % of weighted actual energy'); ax.set_ylabel('yearly penalty, 100M KRW (eok-won)'); ax.set_title(f'Yearly penalty vs weighted MAE  (revenue term ~ {R/1e8:.1f} eok-won)')
fig.tight_layout(); fig.savefig(f"{OUT}/smpw_fig11_stakes.png"); plt.close(fig)
print("\nDONE")
