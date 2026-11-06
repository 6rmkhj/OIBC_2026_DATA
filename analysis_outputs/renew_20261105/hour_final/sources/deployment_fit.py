# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "pyarrow", "lightgbm", "scikit-learn", "joblib"]
# ///
# How to run: through deployment_run.py, with frozen imports.
"""Sequential bottom-up and group fitting at the single declared cutoff."""
from wave_common import ROOT, OUT, configure, receipt, save_json, digest
from final_build import OLD, CACHE, MARCH, JUNE, enrich
from final_infer import compose
from train import BASE_FEATURES, forecast_context
from refine_models import normalized_fit
from learner_models import fit as neural_fit
from profile_models import fit as station_fit
from site_features import normalizer
import gc
import json
import time
import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- exact frozen numerical interfaces

DEST = OUT / "deployment_check"
FEATURES = ['wa_cloud','wa_temp','wa_humidity','wa_ground_press','wa_wind_speed','wa_rain','wb_cloud','wb_uv_idx','wb_temp','wb_rel_hum','wb_dew_point','wb_vis','wb_ceiling','wb_precip_prob','wb_total_liq','elev','azim','cosz','toa','sunfrac','doy_sin','doy_cos','hour','capacity_kw','lat','lon']
PARAMS = dict(n_estimators=400, learning_rate=.06, num_leaves=127, min_child_samples=200, subsample=.8, subsample_freq=1, colsample_bytree=.8, objective='regression_l1', verbose=-1, n_jobs=2)
REPLAY = []


def tree_fit(train: pd.DataFrame, evaluation: pd.DataFrame, directory):
    """Fit and immediately replay a tree using its saved config."""
    config = json.loads((directory / 'config.json').read_text())
    names = config['features']
    assert not {'energy','cf','y'} & set(names)
    model = lgb.LGBMRegressor(**config['parameters'])
    started = time.monotonic()
    model.fit(train[names], train.cf)
    prediction = model.predict(evaluation[names])
    assert np.isfinite(prediction).all()
    model.booster_.save_model(str(directory / 'model.txt'))
    replay = lgb.Booster(model_file=str(directory / 'model.txt')).predict(evaluation[names], num_threads=2)
    np.testing.assert_array_equal(prediction, replay)
    REPLAY.append({'model':str(directory.relative_to(DEST)), 'max_absolute_error':0., 'negative_raw':int((prediction<0).sum()),'rows':len(prediction)})
    receipt(directory / 'runtime.json', [time.monotonic()-started])
    return prediction


def bottom_up() -> pd.DataFrame:
    """Reuse original site features but retrain pooled and eligible sites serially."""
    train = pd.read_parquet(CACHE / 'feat_train.parquet', columns=['site_id','ts','cf',*FEATURES], filters=[('ts','<=',MARCH),('night','==',False)])
    assert train.cf.notna().all() and train.ts.max() <= MARCH
    evaluation = pd.read_parquet(CACHE / 'feat_train.parquet', columns=['site_id','ts','night',*FEATURES], filters=[('ts','>',MARCH),('ts','<=',JUNE)])
    day = evaluation.loc[~evaluation.night].reset_index(drop=True)
    pooled_seeds = []
    for seed in range(5):
        directory = DEST / 'models' / f'bu_pool_{seed}'
        directory.mkdir(parents=True)
        save_json(directory / 'config.json', {'parameters':{**PARAMS,'random_state':seed},'features':FEATURES,'rows':len(train),'train_max':str(train.ts.max())})
        pred = tree_fit(train, day, directory)
        day[['site_id','ts']].assign(p_raw_cf=pred).to_parquet(directory / 'daylight_raw.parquet',index=False)
        pooled_seeds.append(pred)
        print('BU POOL',seed,flush=True)
    pooled = np.mean(pooled_seeds,axis=0)
    del pooled_seeds
    individual = pooled.copy()
    train_indices = train.groupby('site_id').indices
    eval_indices = day.groupby('site_id').indices
    counts = []
    for site, ix in train_indices.items():
        rows = train.iloc[ix]
        counts.append({'site_id':site,'rows':len(rows),'train_max':str(rows.ts.max()),'fitted':len(rows)>=1000})
        if len(rows) < 1000:
            continue
        directory = DEST / 'models' / f'bu_site_{site}'
        directory.mkdir()
        save_json(directory / 'config.json',{'parameters':{**PARAMS,'n_estimators':600,'objective':'regression_l2'},'features':FEATURES,'rows':len(rows),'train_max':str(rows.ts.max())})
        indices = eval_indices.get(site, np.array([], dtype=int))
        pred = tree_fit(rows, day.iloc[indices], directory)
        individual[indices] = pred
        day.iloc[indices][['site_id','ts']].assign(p_raw_cf=pred).to_parquet(directory / 'daylight_raw.parquet',index=False)
        print('BU SITE',site,len(rows),flush=True)
    save_json(DEST / 'site_train_counts.json',counts)
    day['p_bu'] = np.clip(.9*pooled+.1*individual,0,None)*day.capacity_kw.to_numpy()
    result = evaluation[['site_id','ts','night']].merge(day[['site_id','ts','p_bu']],on=['site_id','ts'],how='left',validate='one_to_one')
    assert result.loc[~result.night,'p_bu'].notna().all()
    result['p_bu'] = result.p_bu.fillna(0.).astype('float32')
    result.to_parquet(DEST / 'bottom_up_site.parquet',index=False)
    assignment = json.loads((OLD.parent / 'cache/assignment.json').read_text())
    result['grp'] = result.site_id.map(assignment)
    assert result.grp.notna().all()
    return result.groupby(['ts','grp'],as_index=False).p_bu.sum()


def group_fits() -> pd.DataFrame:
    """Train identical incumbent/candidate features on predicate-bounded labels."""
    train = pd.read_parquet(OLD / 'full_train.parquet',filters=[('ts','<=',MARCH)])
    evaluation = pd.read_parquet(OLD / 'outer_features.parquet',filters=[('ts','>',MARCH),('ts','<=',JUNE)])
    assert not {'energy','cf','y'} & set(evaluation)
    weather = pd.read_parquet(OUT / 'final/cache/train_weather.parquet')
    stations = pd.read_parquet(OUT / 'final/cache/train_stations.parquet')
    train, names, profiles = enrich(train,weather,stations)
    evaluation, names2, profiles2 = enrich(evaluation,weather,stations)
    assert names == names2 and profiles == profiles2 and train.ts.max() <= MARCH
    incumbent_names = list(BASE_FEATURES) + [n for n in evaluation if n.endswith(('_ramp','_lead','_daylight_mean','_daylight_std'))] + ['grp_code']
    save_json(DEST / 'features.json',{'incumbent':incumbent_names,'candidate':names,'station_candidates':profiles,'train_rows':len(train),'train_max':str(train.ts.max()),'evaluation_rows':len(evaluation)})
    evaluation.to_parquet(DEST / 'evaluation_features.parquet',index=False)
    result = evaluation[['ts','grp']].copy()
    for member in ('incumbent','rich','normalized','mlp','station'):
        predictions = []
        for seed in range(3):
            directory = DEST / 'models' / member / f'seed{seed}'
            match member:
                case 'normalized':
                    raw = normalized_fit(seed,63,400,train,evaluation,names,directory)
                case 'mlp':
                    raw = neural_fit('mlp_cf',seed,train,evaluation,names,directory)
                case 'station':
                    raw = station_fit('lgb',seed,train,evaluation,profiles,directory)
                case 'incumbent' | 'rich':
                    selected = incumbent_names if member == 'incumbent' else names
                    directory.mkdir(parents=True)
                    params = dict(n_estimators=400,learning_rate=.03,num_leaves=31,min_child_samples=50,subsample=.8,subsample_freq=1,colsample_bytree=.8,objective='regression_l1',verbose=-1,n_jobs=2,random_state=None if seed==0 else seed)
                    save_json(directory / 'config.json',{'parameters':params,'features':selected,'train_rows':len(train),'train_max':str(train.ts.max())})
                    pred = tree_fit(train,evaluation,directory)*evaluation.capacity_kw.to_numpy()
                    raw = evaluation[['ts','grp']].assign(p_raw=pred)
                    raw.to_parquet(directory / 'daylight_raw.parquet',index=False)
                case unreachable:
                    from typing import assert_never
                    assert_never(unreachable)
            assert np.isfinite(raw.p_raw).all()
            predictions.append(raw.p_raw.to_numpy())
            selected = incumbent_names if member == 'incumbent' else names
            if member == 'station':
                selected = json.loads((directory / 'feature_mask.json').read_text())['selected_columns']
            if member == 'mlp':
                transform = joblib.load(directory / 'input_preprocessing.joblib')
                target = joblib.load(directory / 'target_scaler.joblib')
                model = joblib.load(directory / 'model.joblib')
                replay = target.inverse_transform(model.predict(transform.transform(evaluation[names])).reshape(-1,1)).ravel()
                del model, transform, target
            else:
                model = lgb.Booster(model_file=str(directory / 'model.txt'))
                replay = model.predict(evaluation[selected],num_threads=2)
                del model
                if member in ('normalized','station'):
                    replay *= normalizer(evaluation.cosz.to_numpy())
            replay *= evaluation.capacity_kw.to_numpy()
            np.testing.assert_allclose(raw.p_raw,replay,rtol=1e-12,atol=1e-8)
            REPLAY.append({'model':str(directory.relative_to(DEST)),'max_absolute_error':float(np.abs(raw.p_raw-replay).max()),'negative_raw':int((raw.p_raw<0).sum()),'rows':len(raw)})
            print('GROUP',member,seed,flush=True)
            gc.collect()
        result[member] = np.clip(np.mean(predictions,axis=0),0,None)
    return result


def run() -> None:
    configure()
    started = time.monotonic()
    protocol = json.loads((DEST / 'protocol.json').read_text())
    actual_inputs = {p:digest(ROOT/p) for p in protocol['input_sha256']}
    assert actual_inputs == protocol['input_sha256']
    save_json(DEST / 'input_hashes.json',actual_inputs)
    base = bottom_up()
    components = group_fits()
    components.to_parquet(DEST / 'components.parquet',index=False)
    prediction = compose(base,components.drop(columns='incumbent'))
    prediction = prediction.merge(components[['ts','grp','incumbent']],on=['ts','grp'],how='left',validate='one_to_one')
    prediction['incumbent'] = prediction.incumbent.fillna(0.)
    prediction['p_previous'] = .7149301735712863*prediction.incumbent+(1-.7149301735712863)*prediction.p_bu
    assert len(prediction)==4416 and np.isfinite(prediction[['p_previous','p_candidate']]).all().all()
    prediction.to_parquet(DEST / 'frozen_predictions.parquet',index=False)
    save_json(DEST / 'prediction_freeze.json',{'sha256':digest(DEST / 'frozen_predictions.parquet'),'evaluation_labels_opened':False})
    save_json(DEST / 'replay.json',REPLAY)
    from deployment_report import report
    report(prediction)
    after = {p:digest(ROOT/p) for p in protocol['protected_sha256']}
    assert after == protocol['protected_sha256']
    save_json(DEST / 'preservation.json',{'unchanged':True,'files':len(after),'sha256':after})
    receipt(DEST / 'runtime.json',[time.monotonic()-started])
    save_json(DEST / 'hashes.json',{str(p.relative_to(DEST)):digest(p) for p in DEST.rglob('*') if p.is_file() and p.name not in {'hashes.json','run.log'}})
    print('DEPLOYMENT COMPLETE',flush=True)
