#!/usr/bin/env python3
"""Independent terminal audit; never trains, resumes, reports or publishes.

Before the controller is finished and every recorded owned process group is
terminal, return CHECKPOINT_ONLY without opening late targets.  A successful
verification is separate from the scientific outcome; no qualifying recipe is
not an improvement claim.  Invoke externally after the controller has exited.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import zipfile

os.environ.update(OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', OMP_NUM_THREADS='4', NUMEXPR_NUM_THREADS='1')
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis_outputs/research_22h_20261107'
OLD = ROOT / 'analysis_outputs/research_10h_20261107'
DATA = OLD / 'data'
FINAL = ROOT / 'analysis_outputs/renew_20261105/final'
COMP = OUT / 'completion'
BEST = ROOT / 'submission/renew_candidate_20261105/submission_files.zip'
BEST_SHA = 'ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434'
helper_spec = importlib.util.spec_from_file_location('independent_generation_checks', ROOT / 'submission/score_push_10h/verify_trial.py')
helper = importlib.util.module_from_spec(helper_spec)
helper_spec.loader.exec_module(helper)
read, sha, curve, score, close_dict, keys = helper.read, helper.sha, helper.curve, helper.score, helper.close_dict, helper.keys
import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from threadpoolctl import threadpool_limits
pa.set_cpu_count(1)
pa.set_io_thread_count(1)
KEYS = ['ts', 'grp']
WEATHER = ['wa_cloud', 'wa_temp', 'wa_humidity', 'wa_rain', 'wa_wind_speed', 'wb_cloud', 'wb_uv_idx',
           'wb_precip_prob', 'wb_total_liq', 'wb_rel_hum', 'extra_wa_snow', 'cosz', 'grp_code']
CALENDAR = ['doy_sin', 'doy_cos', 'hour']
FAMILIES = {'core': WEATHER + ['raw_fraction'], 'season': WEATHER + ['raw_fraction'] + CALENDAR,
            'age': WEATHER + ['raw_fraction'] + CALENDAR + ['forecast_age_days', 'model_history_days']}


def kst(value):
    stamp = pd.Timestamp(value)
    return stamp.tz_localize('Asia/Seoul') if stamp.tzinfo is None else stamp.tz_convert('Asia/Seoul')


def file_checks(folder, receipt):
    for name, expected in receipt['files_sha256'].items():
        target = (folder / name).resolve()
        assert target.is_relative_to(ROOT) and sha(target) == expected, str(folder / name)


def joined(left, right, columns):
    keys(left)
    keys(right)
    result = left.merge(right[KEYS + columns], on=KEYS, how='left', sort=False, validate='one_to_one', indicator=True)
    pd.testing.assert_frame_equal(result[KEYS], left[KEYS].reset_index(drop=True), check_exact=True)
    assert result._merge.eq('both').all()
    return result.drop(columns='_merge')


def terminal_gate(directory):
    path = directory / 'state.json'
    if not path.exists():
        return False, {'reason': 'Controller state does not exist', 'controller_state_dir': str(directory)}
    state = read(path)
    if state.get('phase') != 'finished':
        return False, {'reason': 'Controller has not finished', 'phase': state.get('phase'), 'current_job': state.get('current_job')}
    assert state['controller_sha256'] == sha(ROOT / 'submission/score_push_22h/controller.py'), 'Terminal controller source hash changed'
    allowed_statuses = {'completed', 'failed', 'interrupted', 'time_limit', 'stopped', 'deferred_budget', 'skipped_dependency', 'pending'}
    for job, entry in state['jobs'].items():
        assert entry['status'] in allowed_statuses, f'Finished controller has unresolved job status: {job}/{entry["status"]}'
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    live = {}
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            parts = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
        if parts[0] not in {'Z', 'X'}:
            live[int(proc.name)] = dict(pid=int(proc.name), pgid=int(parts[2]), start_ticks=int(parts[19]), boot_id=boot)
    identities = [state['controller_identity']]
    identities += [entry['wrapper_identity'] for entry in state['jobs'].values() if entry.get('wrapper_identity')]
    for started_path in sorted((directory / 'jobs').glob('*/started.json')):
        started = read(started_path)
        assert started['manifest_sha256'] == state['manifest_sha256']
        entry = state['jobs'][started_path.parent.name]
        assert started['nonce'] == entry['nonce']
        identities += [started[name] for name in ('identity', 'worker_identity') if started.get(name)]
    groups = {item['pgid'] for item in identities if item['boot_id'] == boot}
    owned_alive = [item['pid'] for item in identities if item['pid'] in live and
                   all(item[key] == live[item['pid']][key] for key in ('pid', 'pgid', 'start_ticks', 'boot_id'))]
    group_alive = [pid for pid, item in live.items() if item['pgid'] in groups]
    evidence = dict(controller_phase='finished', controller_state_dir=str(directory),
                    recorded_identities=len(identities), recorded_groups=len({(item['boot_id'], item['pgid']) for item in identities}),
                    live_recorded_identity_pids=sorted(set(owned_alive)), live_recorded_group_pids=sorted(group_alive),
                    controller_manifest_sha256=state['manifest_sha256'])
    if owned_alive or group_alive:
        return False, {'reason': 'Recorded controller or owned group is still alive; no terminal audit started', **evidence}
    manifest_path = OUT / 'controller_manifest.json'
    assert manifest_path.exists() and sha(manifest_path) == state['manifest_sha256']
    for name, expected in read(manifest_path).get('input_sha256', {}).items():
        target = Path(name)
        target = target if target.is_absolute() else ROOT / target
        assert target.resolve().is_relative_to(ROOT) and sha(target) == expected, f'Terminal controller input pin changed: {name}'
    return True, evidence


def alpha_optimal(frame, alpha):
    difference = frame.p.to_numpy() - frame.p_reference.to_numpy()
    money = frame.smp.to_numpy() * frame.k.to_numpy()
    active = (difference != 0) & (money > 0)
    ratios = (frame.y.to_numpy()[active] - frame.p_reference.to_numpy()[active]) / difference[active]
    masses = money[active] * np.abs(difference[active])
    assert 0 <= alpha <= 1
    if not len(ratios):
        assert alpha == 0
    else:
        if alpha > 0:
            assert masses[ratios < alpha].sum() <= masses.sum() / 2 * (1 + 1e-12)
        if alpha < 1:
            assert masses[ratios > alpha].sum() <= masses.sum() / 2 * (1 + 1e-12)


def blend_verified(frames, record):
    alpha = record['alpha']
    alpha_optimal(frames['primary'], alpha)
    improved = []
    for fold, frame in frames.items():
        prediction = frame.p_reference + alpha * (frame.p - frame.p_reference)
        scores = dict(reference=score(frame, frame.p_reference), component=score(frame, frame.p), blend=score(frame, prediction))
        for role, expected in scores.items():
            close_dict(record['scores'][fold][role], expected)
        improved.append(scores['blend']['W'] < scores['reference']['W'])
    assert record['eligible'] == (alpha >= .02 and all(improved))
    assert record['primary_only_alpha'] and record['recent_unchanged_transfer']


def engineered(frame):
    result = pd.DataFrame(index=frame.index)
    for name in WEATHER + CALENDAR:
        result[name] = frame.grp.map({'G1': 0., 'G2': 1.}) if name == 'grp_code' and name not in frame else frame[name].to_numpy(dtype=float)
    result = result.replace([np.inf, -np.inf], np.nan)
    capacity = frame.capacity_kw.to_numpy(dtype=float)
    assert np.isfinite(capacity).all() and (capacity > 0).all()
    result['raw_fraction'] = frame.p.to_numpy(dtype=float) / capacity
    age = (frame.ts - frame.model_origin).dt.total_seconds().to_numpy() / 86400
    assert (age > 0).all()
    result['forecast_age_days'] = np.minimum(age, 366.)
    result['model_history_days'] = frame.train_history_days.to_numpy(dtype=float)
    assert np.isfinite(result[['raw_fraction', 'forecast_age_days', 'model_history_days']]).all().all()
    return result


def scale(frame, config):
    solar = frame.capacity_kw.to_numpy(dtype=float) * curve(frame)
    assert np.isfinite(solar).all() and (solar > 0).all()
    return solar if config['mode'] == 'additive' else np.maximum(frame.p.to_numpy(dtype=float), .05 * solar)


class Audit:
    def __init__(self):
        self.protocol = read(OUT / 'protocol.json')
        self.old_protocol = read(OLD / 'protocol.json')
        self.data_manifest = read(DATA / 'manifest.json')
        baseline_proof = read(OLD / 'independent_baseline_check.json')
        assert baseline_proof['status'] == 'PASS' and sha(Path(helper.__file__)) == baseline_proof['verifier_sha256']
        for name in ('bases', 'configs', 'jobs'):
            assert sha(OUT / f'{name}.json') == self.protocol[f'{name}_sha256']
        assert sha(OLD / 'protocol.json') == self.protocol['old_protocol_sha256']
        assert sha(DATA / 'manifest.json') == self.protocol['data_manifest_sha256'] == self.old_protocol['data_manifest_sha256']
        for name, expected in {**self.protocol['source_sha256'], **self.old_protocol['source_sha256'],
                               **self.data_manifest['source_sha256'], **self.old_protocol['deployment_input_sha256']}.items():
            assert sha(ROOT / name) == expected, name
        for name, expected in self.data_manifest['data_sha256'].items():
            assert sha(DATA / name) == expected, name
        assert sha(BEST) == BEST_SHA
        self.bases = {item['id']: item for item in read(OUT / 'bases.json')}
        self.configs = {item['id']: item for item in read(OUT / 'configs.json')}
        self.tables = {}
        self.pools = {}
        self.replayed = 0
        self.oof_origins = 0
        self.training_checks = 0
        self.late_allowed = False

    def base(self, identifier):
        item = self.bases[identifier]
        for name, expected in item['old_files_sha256'].items():
            assert sha(ROOT / name) == expected, name
        assert sha(OLD / 'trials' / item['source_id'] / 'result.json') == item['source_result_sha256']
        assert read(OLD / 'trials' / item['source_id'] / 'result.json')['config'] == item['config']
        return item

    def table(self, cutoff):
        if cutoff in self.tables:
            return self.tables[cutoff]
        if kst(cutoff) <= kst('2025-03-01'):
            features = pd.read_parquet(DATA / 'search_features.parquet')
            labels = pd.read_parquet(DATA / 'search_labels.parquet')
            features = features.loc[features.ts.le(kst(cutoff))].reset_index(drop=True)
            labels = labels.loc[labels.ts.le(kst(cutoff))].reset_index(drop=True)
        else:
            assert self.late_allowed, 'Late target access requires an eligible frozen recipe and terminal controller'
            filters = [('ts', '<=', kst(cutoff))]
            features = pq.read_table(ROOT / 'analysis_outputs/renew_20261107/runtime_inputs/test_train.parquet', filters=filters).to_pandas()
            site = pq.read_table(ROOT / 'submission/cache/feat_train.parquet', columns=['ts', 'site_id', 'energy', 'night'], filters=filters).to_pandas()
            site['grp'] = site.site_id.map(read(ROOT / 'analysis_outputs/autoresearch_20261103/cache/assignment.json'))
            assert site.grp.notna().all()
            labels = site.groupby(KEYS, as_index=False).agg(y=('energy', 'sum'), night=('night', 'all'))
            del site
            prices = pq.read_table(ROOT / 'submission/cache/smp.parquet', columns=['ts', 'smp', 'k'], filters=filters).to_pandas()
            labels = labels.merge(prices, on='ts', validate='many_to_one')
            labels = labels.merge(features[KEYS + ['capacity_kw']], on=KEYS, how='left', validate='one_to_one')
            labels['static_capacity'] = labels.grp.map(read(ROOT / 'analysis_outputs/renew_20261105/final/static_capacity.json'))
            features = joined(features, labels, ['y', 'smp', 'k'])
        assert features.ts.max() <= kst(cutoff) and labels.ts.max() <= kst(cutoff)
        assert labels.capacity_kw.isna().equals(labels.night)
        self.tables[cutoff] = features, labels
        return features, labels

    def pool(self, base, cutoff, search=False):
        cache_key = base['id'], cutoff, search
        if cache_key in self.pools:
            return self.pools[cache_key]
        features, labels = self.table('2025-03-01' if search else cutoff)
        origins = self.protocol['inner_origins'] if search else [str(ts.date()) for ts in pd.date_range('2021-06-01', kst(cutoff).tz_localize(None), freq='QS-MAR') if kst(ts) < kst(cutoff)]
        rows = []
        base_folder = OUT / 'bases' / base['id']
        base_result = read(base_folder / 'result.json')
        for index, origin in enumerate(origins):
            end = str(min(kst(origin) + pd.Timedelta(days=366), kst(cutoff)).date())
            folder = base_folder / 'origins' / origin
            if not (folder / 'receipt.json').exists() or read(folder / 'receipt.json').get('end') != end:
                assert not search
                folder = COMP / 'oof' / cutoff / base['id'] / origin
            receipt = read(folder / 'receipt.json')
            file_checks(folder, receipt)
            assert receipt['origin'] == origin and receipt['end'] == end and receipt['config'] == base['config']
            if search:
                assert receipt == base_result['origins'][index]
            model_path = ROOT / receipt['model_source'] if receipt.get('model_reused') else folder / 'model.txt'
            assert model_path.resolve().is_relative_to(ROOT)
            if receipt.get('model_reused'):
                assert sha(model_path) == receipt['model_source_sha256']
            transform = read(model_path.parent / 'transform.json')
            assert transform['origin'] == origin and kst(transform['training_end']) <= kst(origin)
            history = (kst(origin) - kst(transform['training_start'])).total_seconds() / 86400
            assert receipt['train_history_days'] == history
            prediction = pd.read_parquet(folder / 'predictions.parquet')
            expected = labels.loc[labels.ts.gt(kst(origin)) & labels.ts.le(kst(end))].reset_index(drop=True)
            common = [name for name in expected if name in prediction]
            pd.testing.assert_frame_equal(prediction[common], expected[common], check_exact=True)
            keys(prediction)
            assert prediction.ts.gt(kst(origin)).all() and prediction.ts.le(kst(end)).all()
            assert prediction.loc[prediction.night, 'p'].eq(0).all()
            daylight = prediction.loc[~prediction.night & prediction.ts.le(kst(cutoff))].copy()
            daylight = joined(daylight, features, [name for name in WEATHER + CALENDAR if name not in daylight])
            daylight['model_origin'] = kst(origin)
            daylight['train_history_days'] = history
            rows.append(daylight)
            self.oof_origins += 1
        pool = pd.concat(rows, ignore_index=True)
        assert not pool.duplicated(KEYS + ['model_origin']).any()
        assert pool.model_origin.lt(pool.ts).all() and pool.ts.le(kst(cutoff)).all()
        assert (pool.ts - pool.model_origin).dt.total_seconds().le(366 * 86400).all()
        assert not pool.night.any()
        if search:
            assert sha(base_folder / 'pool.parquet') == base_result['pool_sha256']
            pd.testing.assert_frame_equal(pool, pd.read_parquet(base_folder / 'pool.parquet'), check_exact=True)
            assert len(pool) == base_result['pool_rows'] and len(pool[KEYS].drop_duplicates()) == base_result['unique_targets']
        self.pools[cache_key] = pool
        return pool

    def application(self, base, fold):
        folder = OLD / 'trials' / base['source_id'] / fold
        full = pd.read_parquet(folder / 'predictions.parquet')
        evaluation = pd.read_parquet(DATA / fold / 'evaluation.parquet')
        daylight = full.loc[~full.night].copy()
        daylight = joined(daylight, evaluation, [name for name in WEATHER + CALENDAR if name not in daylight])
        origin = self.protocol['folds'][fold]['origin']
        daylight['model_origin'] = kst(origin)
        daylight['train_history_days'] = (kst(origin) - kst(read(folder / 'transform.json')['training_start'])).total_seconds() / 86400
        return daylight, full

    def calibration(self, folder, config, seed, fold, pool, daylight, full, cutoff):
        receipt = read(folder / 'receipt.json')
        file_checks(folder, receipt)
        assert receipt['status'] == 'PASS' and receipt['config'] == config and receipt['seed'] == seed and receipt['fold'] == fold
        assert receipt['native_saved_model_replay'] and receipt['real_model_fits'] == int(config['method'] == 'tree')
        train = pool.loc[pool.ts.le(kst(cutoff))].reset_index(drop=True)
        assert train.model_origin.lt(train.ts).all() and train.ts.le(kst(cutoff)).all()
        units = scale(train, config)
        target = (train.y.to_numpy(dtype=float) - train.p.to_numpy(dtype=float)) / units
        duplicate = train.groupby(KEYS, dropna=False).ts.transform('size').to_numpy(dtype=float)
        weight = train.smp.to_numpy(dtype=float) * train.k.to_numpy(dtype=float) * units / duplicate
        if config['half_life'] is not None:
            age = (kst(cutoff) - train.ts).dt.total_seconds().to_numpy() / 86400
            weight *= np.exp2(-age / config['half_life'])
        weight /= weight.mean()
        assert np.isfinite(target).all() and np.isfinite(weight).all() and (weight >= 0).all()
        features = FAMILIES[config['features']]
        transform = read(folder / 'transform.json')
        expected = dict(features=features, training_rows=len(train), unique_targets=len(train[KEYS].drop_duplicates()), cutoff=cutoff,
                        training_target_start=str(train.ts.min()), training_target_end=str(train.ts.max()),
                        generating_origin_start=str(train.model_origin.min()), generating_origin_end=str(train.model_origin.max()),
                        every_origin_precedes_target=True, training_only=True)
        for name, value in expected.items():
            assert transform[name] == value, (str(folder), name)
        for name, value in dict(weight_min=weight.min(), weight_max=weight.max(), weight_mean=weight.mean(), target_min=target.min(), target_max=target.max()).items():
            np.testing.assert_allclose(transform[name], value, rtol=1e-12, atol=1e-12)
        prediction_X = engineered(daylight)[features]
        if config['method'] == 'median':
            model = read(folder / 'model.json')
            value = model['value']
            assert model['method'] == 'weighted_median'
            assert weight[target < value].sum() <= weight.sum() / 2 * (1 + 1e-12)
            assert weight[target > value].sum() <= weight.sum() / 2 * (1 + 1e-12)
            delta = np.full(len(daylight), value)
        else:
            with threadpool_limits(limits=1, user_api='blas'):
                model = lgb.Booster(model_file=str(folder / 'model.txt'))
                assert model.feature_name() == features
                for name, value in dict(objective='regression_l1', seed=seed, num_iterations=config['n_estimators'],
                    num_leaves=config['num_leaves'], min_data_in_leaf=config['min_child_samples'], learning_rate=config['learning_rate'],
                    lambda_l2=config['reg_lambda'], feature_fraction=.9, bagging_fraction=.8, bagging_freq=1,
                    num_threads=4, deterministic=True, force_col_wise=True).items():
                    assert model.params[name] == value, (str(folder), name)
                delta = model.predict(prediction_X, num_threads=4)
            self.replayed += 1
        corrected = np.clip(daylight.p.to_numpy(dtype=float) + config['shrink'] * np.clip(delta, -config['bound'], config['bound']) * scale(daylight, config), 0, daylight.static_capacity.to_numpy(dtype=float))
        change = daylight[KEYS].copy()
        change['corrected'] = corrected
        prediction = full.rename(columns={'p': 'p_base'}).merge(change, on=KEYS, how='left', sort=False, validate='one_to_one')
        assert prediction.corrected.isna().equals(prediction.night)
        prediction['p'] = prediction.corrected.fillna(0)
        prediction.drop(columns='corrected', inplace=True)
        stored = pd.read_parquet(folder / 'predictions.parquet')
        pd.testing.assert_frame_equal(stored, prediction, check_exact=True)
        if 'y' in prediction:
            close_dict(receipt['score'], score(prediction, prediction.p))
            close_dict(receipt['raw_score'], score(prediction, prediction.p_base))
        else:
            assert receipt['score'] is None and receipt['raw_score'] is None
        self.training_checks += 1
        return prediction

    def deployed_base(self, base, split, cutoff):
        train, _ = self.table(cutoff)
        part = 'test' if split == 'test' else 'march_may'
        evaluation = pd.read_parquet(FINAL / 'data' / part / 'evaluation.parquet')
        coverage = pd.read_parquet(FINAL / 'data' / part / 'coverage.parquet')
        full = pd.read_parquet(FINAL / 'predictions' / split / 'predictions.parquet', columns=KEYS + ['p', 'static_capacity']).rename(columns={'p': 'p_reference'})
        full = joined(full, coverage, ['night'])
        folder = COMP / split / base['id'] / 'generation'
        receipt = read(folder / 'receipt.json')
        file_checks(folder, receipt)
        assert receipt['config'] == base['config'] and receipt['seed'] == 0 and receipt['fold'] == split
        transform = read(folder / 'transform.json')
        candidates = read(DATA / 'features.json')[base['config']['features']]
        columns = [name for name in candidates if train[name].nunique(dropna=True) > 1]
        assert columns == transform['features'] and transform['origin'] == cutoff
        assert transform['training_rows'] == len(train) and kst(transform['training_end']) <= kst(cutoff) < evaluation.ts.min()
        with threadpool_limits(limits=1, user_api='blas'):
            model = lgb.Booster(model_file=str(folder / 'model.txt'))
            assert model.feature_name() == columns
            config = base['config']
            for name, value in dict(objective=config['objective'], seed=0, num_iterations=config['n_estimators'],
                learning_rate=config['learning_rate'], num_leaves=config['num_leaves'], min_data_in_leaf=config['min_child_samples'],
                lambda_l2=config['reg_lambda'], feature_fraction=config['colsample_bytree'], bagging_fraction=config['subsample'],
                bagging_freq=1, num_threads=4, deterministic=True, force_col_wise=True).items():
                assert model.params[name] == value, (str(folder), name)
            raw = model.predict(evaluation[columns], num_threads=4)
        self.replayed += 1
        daylight_prediction = evaluation[KEYS].copy()
        daylight_prediction['p'] = raw * curve(evaluation) * evaluation.capacity_kw.to_numpy()
        generated = full.merge(daylight_prediction, on=KEYS, how='left', validate='one_to_one', indicator=True)
        assert generated._merge.eq('left_only').equals(generated.night)
        generated['p'] = np.clip(generated.p.fillna(0).to_numpy(), 0, generated.static_capacity.to_numpy())
        generated.loc[generated.night, 'p'] = 0.
        generated.drop(columns='_merge', inplace=True)
        pd.testing.assert_frame_equal(generated, pd.read_parquet(folder / 'predictions.parquet'), check_exact=True)
        daylight = generated.loc[~generated.night].copy()
        daylight = joined(daylight, evaluation, [name for name in ['capacity_kw'] + WEATHER + CALENDAR if name not in daylight])
        daylight['model_origin'] = kst(cutoff)
        daylight['train_history_days'] = (kst(cutoff) - train.ts.min()).total_seconds() / 86400
        return daylight, generated


def combined(frames):
    expected = frames[0].copy()
    for frame in frames:
        pd.testing.assert_frame_equal(keys(frame), keys(expected), check_exact=True)
        for name in ('y', 'smp', 'k', 'p_reference', 'night', 'static_capacity'):
            if name in expected:
                np.testing.assert_array_equal(frame[name], expected[name])
    expected['p'] = np.mean([frame.p.to_numpy() for frame in frames], axis=0)
    return expected


def main(controller_directory):
    report = dict(utc=datetime.now(timezone.utc).isoformat(), actual_model_fits=0, native_model_replays=0,
                  improvement_verified=False, official_improvement_verified=False, official_score_available=False,
                  all_history_previously_exposed=True, uploaded=False, verifier_sha256=sha(Path(__file__)),
                  helper_sha256=sha(Path(helper.__file__)))
    ready, gate = terminal_gate(controller_directory)
    report['terminal_gate'] = gate
    if not ready or not (COMP / 'result.json').exists():
        budget = read(COMP / 'budget_stop.json') if (COMP / 'budget_stop.json').exists() else None
        return {**report, 'status': 'CHECKPOINT_ONLY', 'verification_status': 'CHECKPOINT_ONLY',
                'outcome': budget.get('status', 'INCOMPLETE') if budget else 'INCOMPLETE',
                'reason': gate.get('reason', 'No terminal completion result'), 'late_targets_loaded': False}
    audit = Audit()
    report.update(protocol_sha256=sha(OUT / 'protocol.json'), protected_best_sha256=sha(BEST), official_best_preserved=True)
    result = read(COMP / 'result.json')
    shortlist = read(COMP / 'shortlist.json')
    selected = shortlist['selected']
    assert shortlist['before_late_targets']
    report.update(outcome=result['status'], completion_result_sha256=sha(COMP / 'result.json'))
    if result['status'] == 'NO_QUALIFYING_RECIPE':
        assert not selected and result['exported'] is False and result['march_may_targets_loaded'] is False
        return {**report, 'status': 'PASS', 'verification_status': 'PASS', 'late_targets_loaded': False,
                'reason': 'Empty frozen shortlist verified; no improved model or candidate was produced'}
    assert result['status'] in {'SEED_STABILITY_GATE_FAILED', 'EXPORTED_UNSCORED_CANDIDATE'}
    selection = read(COMP / 'selection_frozen.json')
    assert selection['selected'] == selected and 1 <= len(selected) <= 3
    assert len({item['base_id'] for item in selected}) == len(selected)
    assert selection['before_late_audit_target_reads'] and selection['no_reselection_after_audit']
    assert selection['generation_seed'] == 0 and selection['residual_seeds'] == [0, 1, 2] and selection['equal_weights']
    baseline = read(OLD / 'trials/c000/result.json')
    for item in selected:
        assert item['config'] == audit.configs[item['id']] and item['base_id'] == item['config']['base_id']
        trial_path = OUT / 'trials' / item['id']
        assert sha(trial_path / 'result.json') == item['result_sha256']
        trial = read(trial_path / 'result.json')
        assert trial['protocol_sha256'] == sha(OUT / 'protocol.json') and trial['eligible']
        raw_ratios, base_ratios, frames = {}, {}, {}
        for fold in audit.protocol['folds']:
            receipt = read(trial_path / fold / 'receipt.json')
            assert receipt == trial['folds'][fold]
            file_checks(trial_path / fold, receipt)
            frame = pd.read_parquet(trial_path / fold / 'predictions.parquet')
            labels = pd.read_parquet(DATA / fold / 'labels.parquet')
            pd.testing.assert_frame_equal(frame[list(labels)], labels, check_exact=True)
            computed = score(frame, frame.p)
            raw = score(frame, frame.p_base)
            close_dict(receipt['score'], computed)
            close_dict(receipt['raw_score'], raw)
            raw_ratios[fold] = computed['W'] / raw['W']
            base_ratios[fold] = computed['W'] / baseline['folds'][fold]['score']['W']
            if fold in {'primary', 'recent'}:
                frames[fold] = frame
        assert np.mean(list(raw_ratios.values())) < 1 and max(raw_ratios.values()) <= 1.02
        assert sum(value < 1 for value in raw_ratios.values()) >= 3 and np.mean(list(base_ratios.values())) < 1
        blend_verified(frames, trial['blend'])
    validation = {}
    for fold in ('primary', 'recent'):
        frames = []
        for item in selected:
            base = audit.base(item['base_id'])
            pool = audit.pool(base, '2024-06-01', search=True)
            daylight, full = audit.application(base, fold)
            for seed in (0, 1, 2):
                folder = OUT / 'trials' / item['id'] / fold if seed == 0 else COMP / 'validation' / item['id'] / f'seed{seed}' / fold
                frames.append(audit.calibration(folder, item['config'], seed, fold, pool, daylight, full, audit.protocol['folds'][fold]['origin']))
        validation[fold] = combined(frames)
        path = COMP / f'{fold}_ensemble.parquet'
        assert sha(path) == selection['ensemble_sha256'][fold]
        pd.testing.assert_frame_equal(validation[fold], pd.read_parquet(path), check_exact=True)
    blend_verified(validation, selection)
    report.update(native_model_replays=audit.replayed, verified_oof_origin_artifacts=audit.oof_origins,
                  duplicate_safe_training_weight_checks=audit.training_checks, selection_sha256=sha(COMP / 'selection_frozen.json'))
    if result['status'] == 'SEED_STABILITY_GATE_FAILED':
        assert not selection['eligible'] and result['exported'] is False and result['march_may_targets_loaded'] is False
        return {**report, 'status': 'PASS', 'verification_status': 'PASS', 'late_targets_loaded': False,
                'reason': 'Seed-stability rejection verified; no improved model or candidate was produced'}
    assert selection['eligible'] and result['exported'] and result['uploaded'] is False
    audit.late_allowed = True
    outputs = {}
    frozen_time = datetime.fromisoformat(selection['utc'])
    for split, cutoff in [('latest_cutoff_march_may', '2025-03-01'), ('test', '2025-06-01')]:
        frames = []
        for item in selected:
            base = audit.base(item['base_id'])
            pool = audit.pool(base, cutoff)
            daylight, full = audit.deployed_base(base, split, cutoff)
            for seed in (0, 1, 2):
                folder = COMP / split / item['id'] / f'seed{seed}'
                assert datetime.fromisoformat(read(folder / 'started.json')['utc']) >= frozen_time
                frames.append(audit.calibration(folder, item['config'], seed, split, pool, daylight, full, cutoff))
        output = combined(frames)
        output['p_component'] = output.p
        output['p'] = output.p_reference + selection['alpha'] * (output.p_component - output.p_reference)
        path = COMP / split / 'predictions.parquet'
        frozen = read(path.parent / 'frozen.json')
        assert sha(path) == frozen['predictions_sha256'] and frozen['selection_sha256'] == sha(COMP / 'selection_frozen.json')
        assert datetime.fromisoformat(frozen['utc']) >= frozen_time
        pd.testing.assert_frame_equal(output, pd.read_parquet(path), check_exact=True)
        assert np.isfinite(output.p).all() and output.p.ge(0).all() and (output.p <= output.static_capacity + 1e-9).all()
        assert output.loc[output.night, 'p'].eq(0).all()
        outputs[split] = output
    late_audit = read(COMP / 'audit.json')
    label_path = FINAL / 'predictions/latest_cutoff_march_may/scored_predictions.parquet'
    assert sha(label_path) == audit.old_protocol['late_audit_labels_hash_only_sha256'] == late_audit['label_source_sha256']
    assert not late_audit['used_for_selection'] and late_audit['selection_sha256'] == sha(COMP / 'selection_frozen.json')
    assert late_audit['predictions_sha256'] == sha(COMP / 'latest_cutoff_march_may/predictions.parquet')
    assert datetime.fromisoformat(read(COMP / 'latest_cutoff_march_may/frozen.json')['utc']) <= datetime.fromisoformat(late_audit['utc'])
    labels = pd.read_parquet(label_path, columns=KEYS + ['y', 'smp', 'k'])
    scored = joined(outputs['latest_cutoff_march_may'], labels, ['y', 'smp', 'k'])
    pd.testing.assert_frame_equal(scored, pd.read_parquet(COMP / 'latest_cutoff_march_may/scored_predictions.parquet'), check_exact=True)
    close_dict(late_audit['reference'], score(scored, scored.p_reference))
    close_dict(late_audit['candidate'], score(scored, scored.p))
    candidate = ROOT / 'submission/research_22h_candidate_20261107'
    assert Path(result['candidate']) == candidate and sha(candidate / 'manifest.json') == result['manifest_sha256']
    manifest = read(candidate / 'manifest.json')
    file_checks(candidate, manifest)
    assert manifest['selection'] == selection and manifest['audit'] == late_audit
    assert manifest['original_best_sha256'] == BEST_SHA and result['audit'] == late_audit
    assert not manifest['uploaded'] and manifest['official_score_available'] is False
    with zipfile.ZipFile(BEST) as protected, zipfile.ZipFile(candidate / 'submission_files.zip') as archive:
        assert sorted(archive.namelist()) == ['composition.csv', 'forecast.csv']
        assert archive.read('composition.csv') == protected.read('composition.csv') == (candidate / 'composition.csv').read_bytes()
        assert archive.read('forecast.csv') == (candidate / 'forecast.csv').read_bytes()
        forecast = pd.read_csv(io.BytesIO(archive.read('forecast.csv')))
        original = pd.read_csv(io.BytesIO(protected.read('forecast.csv')))
    assert list(forecast) == ['group', 'ts', 'forecast_kwh'] and len(forecast) == 17520
    for frame in (forecast, original):
        frame['ts'] = pd.to_datetime(frame.ts).dt.tz_convert('Asia/Seoul')
        frame.rename(columns={'group': 'grp'}, inplace=True)
        frame.sort_values(['grp', 'ts'], inplace=True, ignore_index=True)
    test = outputs['test'].sort_values(['grp', 'ts']).reset_index(drop=True)
    pd.testing.assert_frame_equal(keys(test), keys(forecast), check_exact=True)
    pd.testing.assert_frame_equal(keys(test), keys(original), check_exact=True)
    np.testing.assert_array_equal(forecast.forecast_kwh, np.round(test.p, 3))
    np.testing.assert_array_equal(original.forecast_kwh, np.round(test.p_reference, 3))
    assert sha(BEST) == BEST_SHA
    report.update(status='PASS', verification_status='PASS', improvement_verified=True,
        improvement_scope='Frozen primary and transferred recent development gates only; all history was exposed',
        late_targets_loaded=True, native_model_replays=audit.replayed, verified_oof_origin_artifacts=audit.oof_origins,
        duplicate_safe_training_weight_checks=audit.training_checks, candidate=str(candidate),
        candidate_sha256=sha(candidate / 'submission_files.zip'), alpha=selection['alpha'], descriptive_late_audit=late_audit)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controller-state-dir', type=Path, default=OUT / 'controller_state')
    args = parser.parse_args()
    try:
        result = main(args.controller_state_dir)
        if result['verification_status'] == 'PASS':
            destination = OUT / 'independent_completion_check.json'
            if destination.exists():
                previous = read(destination)
                assert {k: v for k, v in previous.items() if k != 'utc'} == {k: v for k, v in result.items() if k != 'utc'}
            else:
                destination.write_text(json.dumps(result, indent=2, allow_nan=False))
        print(json.dumps(result, indent=2, allow_nan=False))
    except Exception as error:
        print(json.dumps(dict(status='FAIL', verification_status='FAIL', improvement_verified=False,
                              actual_model_fits=0, reason=f'{type(error).__name__}: {error}'), indent=2))
        raise SystemExit(1)
