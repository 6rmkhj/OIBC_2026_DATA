"""Build compact float32 feature caches so analysis agents don't each re-join 5M-row tables."""
import pandas as pd, numpy as np, os, time, gc
D = r"C:/Users/User/Downloads/OIBC_2026_DATA/handover 2/01_participant_dataset"
C = r"C:/Users/User/AppData/Local/Temp/claude/C--Users-User-Downloads-OIBC-2026-DATA/dfcedbe5-607d-48a7-8c29-05284fe8d563/scratchpad/cache"
os.makedirs(C, exist_ok=True)
t0=time.time(); log=lambda m: print(f"[{time.time()-t0:6.1f}s] {m}", flush=True)

WA = ["wa_cloud","wa_temp","wa_humidity","wa_ground_press","wa_wind_speed","wa_wind_dir","wa_rain","wa_snow"]
WB = ["wb_temp","wb_feel_temp","wb_wet_bulb_temp","wb_dew_point","wb_wind_speed","wb_wind_dir","wb_wind_gust_spd",
      "wb_rel_hum","wb_vis","wb_ceiling","wb_uv_idx","wb_precip_prob","wb_rain_prob","wb_snow_prob","wb_ice_prob",
      "wb_total_liq","wb_rain","wb_snow","wb_ice","wb_cloud"]

def solar(ts, lat, lon):
    doy = ts.dayofyear.to_numpy(); hour = ts.hour.to_numpy() + ts.minute.to_numpy()/60.0
    g = 2*np.pi/365.0*(doy-1+(hour-12)/24.0)
    eqtime = 229.18*(0.000075+0.001868*np.cos(g)-0.032077*np.sin(g)-0.014615*np.cos(2*g)-0.040849*np.sin(2*g))
    decl = (0.006918-0.399912*np.cos(g)+0.070257*np.sin(g)-0.006758*np.cos(2*g)+0.000907*np.sin(2*g)-0.002697*np.cos(3*g)+0.00148*np.sin(3*g))
    tst = (hour-0.5)*60+eqtime+4*(lon-135.0); ha = np.radians(tst/4.0-180.0); la=np.radians(lat)
    cosz = np.clip(np.sin(la)*np.sin(decl)+np.cos(la)*np.cos(decl)*np.cos(ha),-1,1)
    elev = 90.0-np.degrees(np.arccos(cosz))
    az = np.degrees(np.arctan2(-np.sin(ha), np.tan(decl)*np.cos(la)-np.sin(la)*np.cos(ha)))%360
    # extraterrestrial irradiance on horizontal (W/m2) as clear-sky proxy
    E0 = 1361*(1+0.033*np.cos(2*np.pi*doy/365.0))
    toa = np.clip(E0*cosz, 0, None)
    return elev.astype("float32"), az.astype("float32"), cosz.astype("float32"), toa.astype("float32")

sites = pd.read_csv(f"{D}/sites.csv")
smp_te = pd.read_csv(f"{D}/smp.csv"); smp_te["ts"]=pd.to_datetime(smp_te.ts, utc=True).dt.tz_convert("Asia/Seoul")
smp_tr = pd.read_csv(f"{D}/train/smp.csv"); smp_tr["ts"]=pd.to_datetime(smp_tr.ts, utc=True).dt.tz_convert("Asia/Seoul")
smp_tr["k"] = np.where(smp_tr.ts.dt.hour.between(11,15),3,1)
smp_all = pd.concat([smp_tr, smp_te]).sort_values("ts").reset_index(drop=True)
smp_all.to_parquet(f"{C}/smp_all.parquet", index=False)
log(f"smp_all {len(smp_all)}")

gen = pd.read_parquet(f"{D}/train/generation.parquet")
gen["ts"] = pd.to_datetime(gen.ts).dt.tz_convert("Asia/Seoul").astype("datetime64[us, Asia/Seoul]")
gen["energy"] = gen.energy.astype("float32")
log(f"gen {gen.shape}")

def add_common(d):
    ts = pd.DatetimeIndex(d.ts)
    d["elev"], d["azim"], d["cosz"], d["toa"] = solar(ts, d.lat.to_numpy(), d.lon.to_numpy())
    d["hour"] = ts.hour.to_numpy().astype("int8"); d["doy"] = ts.dayofyear.to_numpy().astype("int16")
    d["month"] = ts.month.to_numpy().astype("int8")
    for c in d.columns:
        if d[c].dtype == "float64": d[c] = d[c].astype("float32")
    return d

meta_cols = ["site_id","capacity_kw","lat","lon","wa_station","wb_station","current_group"]
for split, base_fn in [("train", None), ("test", None)]:
    for r in (10, 17):
        fa = pd.read_parquet(f"{D}/{split}/forecast_wa.parquet", columns=["wa_station","round","ts"]+WA)
        fa = fa[fa["round"]==r].drop(columns="round"); fa["ts"]=pd.to_datetime(fa.ts).dt.tz_convert("Asia/Seoul").astype("datetime64[us, Asia/Seoul]")
        fb = pd.read_parquet(f"{D}/{split}/forecast_wb.parquet", columns=["wb_station","round","ts"]+WB)
        fb = fb[fb["round"]==r].drop(columns="round"); fb["ts"]=pd.to_datetime(fb.ts).dt.tz_convert("Asia/Seoul").astype("datetime64[us, Asia/Seoul]")
        if split=="train":
            base = gen
        else:
            idx = pd.DatetimeIndex(smp_te.ts).astype("datetime64[us, Asia/Seoul]")
            base = pd.MultiIndex.from_product([sites.site_id, idx], names=["site_id","ts"]).to_frame(index=False)
        d = base.merge(sites[meta_cols], on="site_id", how="left")
        d = d.merge(fa, on=["wa_station","ts"], how="left").merge(fb, on=["wb_station","ts"], how="left")
        d = add_common(d)
        d["round"] = np.int8(r)
        d.to_parquet(f"{C}/panel_{split}_r{r}.parquet", index=False, compression="zstd")
        log(f"panel_{split}_r{r} {d.shape} missA={d.wa_cloud.isna().mean():.4f} missB={d.wb_cloud.isna().mean():.4f}")
        del fa, fb, d; gc.collect()

# observed weather joined to (site, ts) on generation rows (for forecast-skill analysis), one file
oa = pd.read_parquet(f"{D}/train/observed_wa.parquet", columns=["wa_station","ts"]+WA)
oa["ts"]=pd.to_datetime(oa.ts).dt.tz_convert("Asia/Seoul").astype("datetime64[us, Asia/Seoul]")
oa = oa.rename(columns={c: "obs_"+c for c in WA})
OBS_B = ["wb_temp","wb_rel_hum","wb_dew_point","wb_wind_speed","wb_uv_idx","wb_vis","wb_cloud","wb_ceiling","wb_pressure","wb_precip_1h"]
ob = pd.read_parquet(f"{D}/train/observed_wb.parquet", columns=["wb_station","ts"]+OBS_B)
ob["ts"]=pd.to_datetime(ob.ts).dt.tz_convert("Asia/Seoul").astype("datetime64[us, Asia/Seoul]")
ob = ob.rename(columns={c: "obs_"+c for c in OBS_B})
d = gen.merge(sites[meta_cols], on="site_id", how="left").merge(oa, on=["wa_station","ts"], how="left").merge(ob, on=["wb_station","ts"], how="left")
d = add_common(d)
d.to_parquet(f"{C}/panel_train_obs.parquet", index=False, compression="zstd")
log(f"panel_train_obs {d.shape} missA={d.obs_wa_cloud.isna().mean():.4f} missB={d.obs_wb_cloud.isna().mean():.4f}")
# wide CF matrix (ts x site) for correlation / composition work
cf = gen.merge(sites[["site_id","capacity_kw"]], on="site_id")
cf["cf"] = (cf.energy/cf.capacity_kw).astype("float32")
wide = cf.pivot(index="ts", columns="site_id", values="cf").sort_index()
wide.to_parquet(f"{C}/cf_wide.parquet")
log(f"cf_wide {wide.shape}")
print("DONE")
