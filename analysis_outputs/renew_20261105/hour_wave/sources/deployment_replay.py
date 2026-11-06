# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pandas", "lightgbm", "joblib"]
# ///
# How to run: imported by deployment_resume.py after snapshot import setup.
"""Recover predictions by replaying completed serialized models without fitting."""
from wave_common import ROOT, OUT, save_json
from final_build import CACHE, OLD, MARCH, JUNE
from site_features import normalizer
import gc
import json
import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd  # noqa: PANDAS_OK -- frozen model interface

DEST = OUT / 'deployment_check'


def replay() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Replay every completed bottom-up and group model and recover ensembles."""
    records = []
    evaluation = pd.read_parquet(DEST / 'evaluation_features.parquet')
    features = json.loads((DEST / 'features.json').read_text())
    components = evaluation[['ts','grp']].copy()
    for member in ('incumbent','rich','normalized','mlp','station'):
        seeds = []
        for seed in range(3):
            directory = DEST / ('resume/models' if member=='station' else 'models') / member / f'seed{seed}'
            names = features['incumbent'] if member=='incumbent' else features['candidate']
            if member=='station':
                names = json.loads((directory/'feature_mask.json').read_text())['selected_columns']
            if member=='mlp':
                transform = joblib.load(directory/'input_preprocessing.joblib')
                scaler = joblib.load(directory/'target_scaler.joblib')
                model = joblib.load(directory/'model.joblib')
                prediction = scaler.inverse_transform(model.predict(transform.transform(evaluation[names])).reshape(-1,1)).ravel()
                del model,transform,scaler
            else:
                model = lgb.Booster(model_file=str(directory/'model.txt'))
                prediction = model.predict(evaluation[names],num_threads=16)
                del model
                if member in ('normalized','station'):
                    prediction *= normalizer(evaluation.cosz.to_numpy())
            prediction *= evaluation.capacity_kw.to_numpy()
            raw = pd.read_parquet(directory/'daylight_raw.parquet')
            pd.testing.assert_frame_equal(raw[['ts','grp']].reset_index(drop=True),evaluation[['ts','grp']].reset_index(drop=True))
            assert np.isfinite(prediction).all() and np.isfinite(raw.p_raw).all()
            np.testing.assert_allclose(prediction,raw.p_raw,rtol=1e-10,atol=1e-6)
            records.append({'model':str(directory.relative_to(DEST)),'passed':True,'rows':len(raw),'negative_raw':int((raw.p_raw<0).sum()),'max_absolute_error':float(np.abs(prediction-raw.p_raw).max())})
            seeds.append(raw.p_raw.to_numpy())
        components[member] = np.clip(np.mean(seeds,axis=0),0,None)
    pool0 = json.loads((DEST/'models/bu_pool_0/config.json').read_text())
    site = pd.read_parquet(CACHE/'feat_train.parquet',columns=['site_id','ts','night',*pool0['features']],filters=[('ts','>',MARCH),('ts','<=',JUNE)])
    day = site.loc[~site.night].reset_index(drop=True)
    pooled = []
    individual = np.zeros(len(day))
    for directory in sorted((DEST/'models').glob('bu_*')):
        config = json.loads((directory/'config.json').read_text())
        raw = pd.read_parquet(directory/'daylight_raw.parquet')
        selected = day if directory.name.startswith('bu_pool') else day[day.site_id.eq(directory.name.removeprefix('bu_site_'))]
        pd.testing.assert_frame_equal(raw[['site_id','ts']].reset_index(drop=True),selected[['site_id','ts']].reset_index(drop=True))
        model = lgb.Booster(model_file=str(directory/'model.txt'))
        prediction = model.predict(selected[config['features']],num_threads=16)
        del model
        np.testing.assert_allclose(prediction,raw.p_raw_cf,rtol=1e-10,atol=1e-10)
        records.append({'model':str(directory.relative_to(DEST)),'passed':True,'rows':len(raw),'negative_raw':int((raw.p_raw_cf<0).sum()),'max_absolute_error':float(np.abs(prediction-raw.p_raw_cf).max())})
        if directory.name.startswith('bu_pool'):
            pooled.append(raw.p_raw_cf.to_numpy())
        else:
            individual[selected.index] = raw.p_raw_cf.to_numpy()
        gc.collect()
    mean = np.mean(pooled,axis=0)
    counts = json.loads((DEST/'site_train_counts.json').read_text())
    eligible = {r['site_id'] for r in counts if r['fitted']}
    individual[~day.site_id.isin(eligible)] = mean[~day.site_id.isin(eligible)]
    day['replayed'] = (np.clip(.9*mean+.1*individual,0,None)*day.capacity_kw.to_numpy()).astype('float32')
    saved = pd.read_parquet(DEST/'bottom_up_site.parquet')
    joined = saved.merge(day[['site_id','ts','replayed']],on=['site_id','ts'],how='left',validate='one_to_one')
    assert joined.loc[~joined.night,'replayed'].notna().all()
    np.testing.assert_array_equal(joined.p_bu,joined.replayed.fillna(0.).astype('float32'))
    assignment = json.loads((OLD.parent/'cache/assignment.json').read_text())
    saved['grp'] = saved.site_id.map(assignment)
    base = saved.groupby(['ts','grp'],as_index=False).p_bu.sum()
    save_json(DEST/'replay.json',records)
    return base,components
