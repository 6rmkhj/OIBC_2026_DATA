#!/usr/bin/env python3
"""Independent terminal audit; never trains, resumes, reports or publishes.

Before the controller is finished and every recorded owned process group is
terminal, return CHECKPOINT_ONLY without opening late targets.  A successful
verification is separate from the scientific outcome; no qualifying recipe is
not an improvement claim.  Invoke externally after the controller has exited.
The 23 KST gates, seed/base weights, and all original artifacts remain frozen.
"""
from __future__ import annotations
import argparse
import hashlib
from datetime import datetime, timezone
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import zipfile

os.environ.update(OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', OMP_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis_outputs/research_23kst_20261108'
OLD = ROOT / 'analysis_outputs/research_10h_20261107'
LEGACY = ROOT / 'analysis_outputs/research_22h_20261107'
DATA = OLD / 'data'
FINAL = ROOT / 'analysis_outputs/renew_20261105/final'
COMP = OUT / 'completion'
BEST = ROOT / 'submission/renew_candidate_20261105/submission_files.zip'
BEST_SHA = 'ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434'
helper_spec = importlib.util.spec_from_file_location('independent_generation_checks', ROOT / 'submission/score_push_10h/verify_trial.py')
helper = importlib.util.module_from_spec(helper_spec)
helper_spec.loader.exec_module(helper)
os.environ.update(OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', OMP_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1')
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
BASE_IDS = ('b00', 'b02', 'b09', 'b22')


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
    assert state['controller_sha256'] == sha(ROOT / 'submission/score_push_23kst/controller.py'), 'Terminal controller source hash changed'
    allowed_statuses = {'completed', 'failed', 'interrupted', 'time_limit', 'stopped', 'deferred_budget', 'skipped_dependency', 'pending'}
    for job, entry in state['jobs'].items():
        assert entry['status'] in allowed_statuses, f'Finished controller has unresolved job status: {job}/{entry["status"]}'
    boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    live = {}
    unreadable_processes = 0
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():
            continue
        try:
            parts = (proc / 'stat').read_text().rsplit(')', 1)[1].split()
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError:
            unreadable_processes += 1
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
    if unreadable_processes:
        return False, {'reason': 'Process scan incomplete; cannot prove owned groups are terminal',
                       'unreadable_process_stat_files': unreadable_processes, **evidence}
    if owned_alive or group_alive:
        return False, {'reason': 'Recorded controller or owned group is still alive; no terminal audit started', **evidence}
    manifest_path = OUT / 'controller_manifest.json'
    assert manifest_path.exists() and sha(manifest_path) == state['manifest_sha256']
    manifest = read(manifest_path)
    assert state['deadline_utc'] == manifest['deadline_utc'], 'Controller deadline differs from its frozen manifest'
    requested_jobs = manifest.get('jobs', []) + manifest.get('completion_jobs', [])
    expected_ids = {item['id'] for item in requested_jobs}
    assert len(expected_ids) == len(requested_jobs), 'Repeated job ids in frozen manifest'
    extra_ids = set(state['jobs']) - expected_ids
    finalizer = manifest.get('finalizer')
    assert expected_ids.issubset(state['jobs'])
    assert not extra_ids or (finalizer and extra_ids == {finalizer['id']}), 'Unexpected controller job'
    receipt_checks = 0
    for identifier, entry in state['jobs'].items():
        if entry.get('receipt_sha256'):
            path = directory / 'jobs' / identifier / 'receipt.json'
            assert sha(path) == entry['receipt_sha256'], f'Controller receipt changed: {identifier}'
            receipt = read(path)
            for name, expected in [('nonce', entry['nonce']), ('manifest_sha256', state['manifest_sha256']),
                                   ('status', entry['status']), ('exit_code', entry.get('exit_code'))]:
                assert receipt[name] == expected, (identifier, name)
            receipt_checks += 1
    evidence['controller_receipts_verified'] = receipt_checks
    evidence['completion_job_statuses'] = {item['id']: state['jobs'][item['id']]['status']
                                         for item in manifest.get('completion_jobs', [])}
    for name, expected in manifest.get('input_sha256', {}).items():
        target = Path(name)
        target = target if target.is_absolute() else ROOT / target
        assert target.resolve().is_relative_to(ROOT) and sha(target) == expected, f'Terminal controller input pin changed: {name}'
    if any(entry['status'] == 'pending' for entry in state['jobs'].values()):
        return False, {'reason': 'Terminal controller retains pending jobs; incomplete checkpoint', **evidence}
    if any(status != 'completed' for status in evidence['completion_job_statuses'].values()):
        return False, {'reason': 'Completion job did not finish successfully; incomplete checkpoint', **evidence}
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


def novel_engineered(frame, config, rich):
    assert config['features'] in {'weather_spread', 'rich_spread'}
    names = WEATHER + CALENDAR if config['features'] == 'weather_spread' else list(rich)
    assert not set(names) & {'y', 'cf', 'smp', 'k', 'energy', 'p_reference'}
    result = frame[names].copy().replace([np.inf, -np.inf], np.nan)
    units = frame.capacity_kw.to_numpy(dtype=float) * curve(frame)
    assert np.isfinite(units).all() and (units > 0).all()
    cross = frame[[f'cross_{base}' for base in BASE_IDS]].to_numpy(dtype=float)
    assert np.isfinite(cross).all()
    raw = frame.p.to_numpy(dtype=float)
    result['raw_solar_fraction'] = raw / units
    result['cross_mean'] = np.mean(cross, axis=1) / units
    result['cross_spread'] = np.std(cross, axis=1) / units
    result['cross_range'] = np.ptp(cross, axis=1) / units
    for index, base in enumerate(BASE_IDS):
        result[f'cross_delta_{base}'] = (cross[:, index] - raw) / units
    ages = (frame.ts - frame.model_origin).dt.total_seconds().to_numpy(dtype=float) / 86400
    assert np.isfinite(ages).all() and (ages > 0).all() and (ages <= 366).all()
    result['forecast_age_days'] = ages
    result['model_history_days'] = frame.train_history_days.to_numpy(dtype=float)
    assert np.isfinite(result['model_history_days']).all() and result.model_history_days.ge(0).all()
    return result


def novel_training(pool, config, cutoff, horizon_days, rich):
    assert config['weighting'] in {'money', 'horizon', 'horizon_groupseason'}
    train = pool.loc[pool.ts.le(kst(cutoff))].reset_index(drop=True)
    assert train.model_origin.lt(train.ts).all() and train.ts.le(kst(cutoff)).all()
    assert not train.night.any()
    ages = (train.ts - train.model_origin).dt.total_seconds().to_numpy(dtype=float) / 86400
    assert (ages > 0).all() and (ages <= 366).all()
    if config['weighting'] != 'money':
        train = train.loc[ages <= horizon_days].reset_index(drop=True)
    assert len(train)
    units = train.capacity_kw.to_numpy(dtype=float) * curve(train)
    assert np.isfinite(units).all() and (units > 0).all()
    target = (train.y.to_numpy(dtype=float) - train.p.to_numpy(dtype=float)) / units
    multiplicity = train.groupby(KEYS, dropna=False).ts.transform('size').to_numpy(dtype=float)
    weight = train.smp.to_numpy(dtype=float) * train.k.to_numpy(dtype=float) * units / multiplicity
    assert np.isfinite(target).all() and np.isfinite(weight).all() and (weight >= 0).all()
    if config['weighting'] == 'horizon_groupseason':
        seasons = (train.ts.dt.month.to_numpy() % 12) // 3
        cells = pd.Series(train.grp.to_numpy().astype(str) + '_' + seasons.astype(str))
        mass = pd.Series(weight).groupby(cells).transform('sum').to_numpy(dtype=float)
        assert (mass > 0).all()
        weight = weight / mass
    assert weight.sum() > 0
    weight = weight / weight.mean()
    matrix = novel_engineered(train, config, rich)
    active = [name for name in matrix if matrix[name].nunique(dropna=False) > 1]
    assert active
    return train, matrix[active], target, weight


class LegacyAudit:
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
                delta = model.predict(prediction_X, num_threads=1)
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
            raw = model.predict(evaluation[columns], num_threads=1)
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
    assert frames, 'Cannot average an empty model set'
    expected = frames[0].copy()
    for frame in frames:
        pd.testing.assert_frame_equal(keys(frame), keys(expected), check_exact=True)
        for name in ('y', 'smp', 'k', 'p_reference', 'night', 'static_capacity'):
            if name in expected:
                np.testing.assert_array_equal(frame[name], expected[name])
    expected['p'] = np.mean([frame.p.to_numpy() for frame in frames], axis=0)
    if 'p_base' in expected:
        assert all('p_base' in frame for frame in frames)
        expected['p_base'] = np.mean([frame.p_base.to_numpy() for frame in frames], axis=0)
    return expected


def optimal_alpha(frame):
    """Independent weighted-L1 optimum, using primary labels only."""
    delta = frame.p.to_numpy(dtype=float) - frame.p_reference.to_numpy(dtype=float)
    money = frame.smp.to_numpy(dtype=float) * frame.k.to_numpy(dtype=float)
    active = (delta != 0) & (money > 0)
    if not active.any():
        return 0.0
    ratios = (frame.y.to_numpy(dtype=float)[active] - frame.p_reference.to_numpy(dtype=float)[active]) / delta[active]
    masses = money[active] * np.abs(delta[active])
    order = np.argsort(ratios, kind='stable')
    position = np.searchsorted(np.cumsum(masses[order]), masses.sum() / 2, side='left')
    return float(np.clip(ratios[order[min(position, len(order) - 1)]], 0, 1))


def evaluate_development(seed_frames, annual_names, quarter_names, alpha=None):
    """Reconstruct the predeclared 23 KST gates; annual and quarterly scores stay separate.

    Each seed frame may already be the equal-base ensemble. Both corrected p
    and its matching uncorrected p_base must use the same component weights.
    """
    assert set(seed_frames) == {0, 1, 2}
    assert len(annual_names) == 5 and len(quarter_names) == 11
    assert not set(annual_names) & set(quarter_names)
    names = list(annual_names) + list(quarter_names)
    assert all(set(frames) == set(names) for frames in seed_frames.values())
    frames = {name: combined([seed_frames[seed][name] for seed in (0, 1, 2)]) for name in names}
    annual_ratios, quarter_ratios = {}, {}
    metrics = {}
    for name, frame in frames.items():
        assert np.isfinite(frame[['p', 'p_base', 'y', 'smp', 'k']].to_numpy(dtype=float)).all()
        assert (frame.smp.to_numpy() * frame.k.to_numpy() >= 0).all()
        assert frame.loc[frame.night, ['p', 'p_base']].eq(0).all().all()
        raw, corrected = score(frame, frame.p_base), score(frame, frame.p)
        assert raw['W'] > 0
        metrics[name] = {'raw': raw, 'corrected': corrected}
        (annual_ratios if name in annual_names else quarter_ratios)[name] = corrected['W'] / raw['W']
    # The quarterly slices form one chronological sequence without duplicated targets.
    quarter_keys = pd.concat([frames[name][KEYS] for name in quarter_names], ignore_index=True)
    keys(quarter_keys)
    group_ratios = {}
    for group in ('G1', 'G2'):
        numerator = denominator = 0.0
        for name in quarter_names:
            part = frames[name].loc[frames[name].grp.eq(group)]
            numerator += score(part, part.p)['W']
            denominator += score(part, part.p_base)['W']
        assert denominator > 0
        group_ratios[group] = numerator / denominator
    seed_ratios = {}
    for seed, records in seed_frames.items():
        numerator = sum(score(records[name], records[name].p)['W'] for name in quarter_names)
        denominator = sum(score(records[name], records[name].p_base)['W'] for name in quarter_names)
        assert denominator > 0
        seed_ratios[str(seed)] = numerator / denominator
    if alpha is None:
        alpha = optimal_alpha(frames['primary'])
    alpha_optimal(frames['primary'], alpha)
    np.testing.assert_allclose(alpha, optimal_alpha(frames['primary']), rtol=0, atol=1e-14)
    blend, blend_ratios, blend_group_ratios = {}, {}, {}
    for name in ('primary', 'recent'):
        frame = frames[name]
        predicted = frame.p_reference + alpha * (frame.p - frame.p_reference)
        reference = score(frame, frame.p_reference)
        changed = score(frame, predicted)
        assert reference['W'] > 0
        blend[name] = {'reference': reference, 'component': score(frame, frame.p), 'blend': changed}
        blend_ratios[name] = changed['W'] / reference['W']
        blend_group_ratios[name] = {}
        for group in ('G1', 'G2'):
            mask = frame.grp.eq(group)
            part = frame.loc[mask]
            denominator = score(part, part.p_reference)['W']
            assert denominator > 0
            blend_group_ratios[name][group] = score(part, predicted.loc[mask])['W'] / denominator
    annual = list(annual_ratios.values())
    quarter = list(quarter_ratios.values())
    checks = {
        'quarter_mean_at_most_0995': float(np.mean(quarter)) <= .995,
        'quarter_improved_at_least_7': sum(value < 1 for value in quarter) >= 7,
        'quarter_worst_at_most_102': max(quarter) <= 1.02,
        'quarter_each_group_at_most_1': max(group_ratios.values()) <= 1,
        'each_seed_quarter_aggregate_below_1': max(seed_ratios.values()) < 1,
        'annual_mean_below_1': float(np.mean(annual)) < 1,
        'annual_improved_at_least_3': sum(value < 1 for value in annual) >= 3,
        'annual_worst_at_most_102': max(annual) <= 1.02,
        'primary_alpha_at_least_002': alpha >= .02,
        'both_blends_at_most_09999': max(blend_ratios.values()) <= .9999,
        'each_blend_group_at_most_1001': max(value for groups in blend_group_ratios.values() for value in groups.values()) <= 1.001,
    }
    return {'eligible': bool(all(checks.values())), 'gate_checks': {name: bool(value) for name, value in checks.items()},
            'alpha': float(alpha), 'annual_ratios': annual_ratios, 'quarter_ratios': quarter_ratios,
            'quarter_group_ratios': group_ratios, 'seed_quarter_aggregate_ratios': seed_ratios,
            'blend_ratios': blend_ratios, 'blend_group_ratios': blend_group_ratios, 'blend_scores': blend,
            'rank': [max(group_ratios.values()), float(np.mean(quarter)), float(np.mean(annual)), float(np.mean(list(blend_ratios.values())))],
            'metrics': metrics}, frames


class Audit(LegacyAudit):
    """Independent reconstruction of the novel three-seed experiment artifacts."""
    def __init__(self):
        self.protocol = read(OUT / 'protocol.json')
        self.old_protocol = read(OLD / 'protocol.json')
        prior = read(LEGACY / 'protocol.json')
        self.data_manifest = read(DATA / 'manifest.json')
        baseline_proof = read(OLD / 'independent_baseline_check.json')
        assert baseline_proof['status'] == 'PASS' and sha(Path(helper.__file__)) == baseline_proof['verifier_sha256']
        assert self.protocol['status'] == 'FROZEN'
        assert kst(self.protocol['deadline_utc']) == kst('2026-11-08T14:00:00Z')
        assert kst(self.protocol['search_stop_utc']) == kst('2026-11-08T12:00:00Z')
        assert self.protocol['search_seeds'] == [0, 1, 2] and self.protocol['generation_seed'] == 0
        assert self.protocol['fixed_base_ids'] == list(BASE_IDS)
        assert self.protocol['all_history_previously_exposed'] and not self.protocol['independent_holdout']
        assert not self.protocol['late_targets_for_selection']
        for name in ('bases', 'configs', 'jobs'):
            assert sha(OUT / f'{name}.json') == self.protocol[f'{name}_sha256']
        assert sha(LEGACY / 'protocol.json') == self.protocol['old_protocol_sha256']
        assert sha(DATA / 'manifest.json') == self.protocol['old_data_manifest_sha256'] == self.old_protocol['data_manifest_sha256']
        for source in (self.protocol, prior, self.old_protocol, self.data_manifest):
            for name, expected in source.get('source_sha256', {}).items():
                assert sha(ROOT / name) == expected, name
        for name, expected in self.old_protocol['deployment_input_sha256'].items():
            assert sha(ROOT / name) == expected, name
        for name, expected in self.data_manifest['data_sha256'].items():
            assert sha(DATA / name) == expected, name
        assert sha(ROOT / self.protocol['input_audit_path']) == self.protocol['input_audit_sha256']
        assert sha(BEST) == BEST_SHA == self.protocol['original_best_sha256']
        self.bases = {item['id']: item for item in read(OUT / 'bases.json')}
        self.configs = {item['id']: item for item in read(OUT / 'configs.json')}
        assert set(self.bases) == set(BASE_IDS) and len(self.configs) == 288
        assert all(item['id'].startswith('r') for item in self.configs.values())
        self.annual = list(self.protocol['annual_folds'])
        self.quarter = list(self.protocol['quarter_folds'])
        assert len(self.annual) == 5 and len(self.quarter) == 11
        expected_quarters = {'q' + stamp.strftime('%Y%m'): dict(origin=str(stamp.date()),
            end=str((stamp + pd.DateOffset(months=3)).date()), kind='quarter', horizon_days=92)
            for stamp in pd.date_range('2022-06-01', '2024-12-01', freq='QS-MAR')}
        assert self.protocol['quarter_folds'] == expected_quarters
        assert self.protocol['annual_folds'] == {name: dict(item, kind='annual', horizon_days=366)
                                                for name, item in self.old_protocol['folds'].items()}
        self.rich = read(DATA / 'features.json')['rich']
        self.tables, self.pools, self.generation_cache = {}, {}, {}
        self.replayed = self.oof_origins = self.training_checks = 0
        self.late_allowed = False
        self.shared = None
        self.checked_results = {}

    def generation_frame(self, base_id, origin, folder, train, evaluation, full, replay=False):
        cache_key = str(folder), replay
        if cache_key in self.generation_cache:
            return self.generation_cache[cache_key]
        base = self.base(base_id)
        record = read(folder / 'receipt.json')
        file_checks(folder, record)
        assert record['status'] == 'PASS' and record['config'] == base['config'] and record['seed'] == 0
        assert record['native_saved_model_replay']
        model_path = ROOT / record['model_source'] if record.get('model_source') else folder / 'model.txt'
        assert model_path.resolve().is_relative_to(ROOT)
        if record.get('model_source'):
            assert sha(model_path) == record['model_source_sha256'] and record['real_model_fits'] == 0
        else:
            assert record['real_model_fits'] == 1 and 'model.txt' in record['files_sha256']
        assert {'transform.json', 'predictions.parquet'}.issubset(record['files_sha256'])
        transform = read(folder / 'transform.json')
        assert transform['origin'] == origin and kst(transform['training_end']) <= kst(origin)
        assert transform['training_rows'] == len(train) and kst(transform['training_start']) == train.ts.min()
        candidates = read(DATA / 'features.json')[base['config']['features']]
        columns = [name for name in candidates if train[name].nunique(dropna=True) > 1]
        assert transform['features'] == columns
        prediction = pd.read_parquet(folder / 'predictions.parquet')
        keys(prediction)
        pd.testing.assert_frame_equal(prediction[list(full)], full.reset_index(drop=True), check_exact=True)
        assert prediction.ts.gt(kst(origin)).all() and prediction.loc[prediction.night, 'p'].eq(0).all()
        assert np.isfinite(prediction.p).all() and prediction.p.ge(0).all()
        assert (prediction.p <= prediction.static_capacity + 1e-9).all()
        if replay:
            model = lgb.Booster(model_file=str(model_path))
            assert model.feature_name() == columns
            config = base['config']
            parameters = dict(objective=config['objective'], seed=0, num_iterations=config['n_estimators'],
                learning_rate=config['learning_rate'], num_leaves=config['num_leaves'], min_data_in_leaf=config['min_child_samples'],
                lambda_l2=config['reg_lambda'], feature_fraction=config['colsample_bytree'], bagging_fraction=config['subsample'],
                bagging_freq=1, num_threads=4, deterministic=True, force_col_wise=True)
            assert all(model.params[name] == value for name, value in parameters.items())
            with threadpool_limits(limits=1):
                raw = model.predict(evaluation[columns], num_threads=1)
            day = evaluation[KEYS].copy()
            day['p'] = raw * curve(evaluation) * evaluation.capacity_kw.to_numpy()
            expected = full.merge(day, on=KEYS, how='left', sort=False, validate='one_to_one', indicator=True)
            assert expected._merge.eq('left_only').equals(expected.night)
            expected['p'] = np.clip(expected.p.fillna(0).to_numpy(), 0, expected.static_capacity.to_numpy())
            expected.loc[expected.night, 'p'] = 0.0
            expected.drop(columns='_merge', inplace=True)
            pd.testing.assert_frame_equal(prediction, expected, check_exact=True)
            self.replayed += 1
        self.oof_origins += 1
        self.generation_cache[cache_key] = prediction
        return prediction

    def origin_common(self, origins, cutoff, locations, replay=False):
        features, labels = self.table(cutoff)
        pieces, pins = [], {}
        for origin in origins:
            end = min(kst(origin) + pd.Timedelta(days=366), kst(cutoff))
            train = features.loc[features.ts.le(kst(origin))].reset_index(drop=True)
            evaluation = features.loc[features.ts.gt(kst(origin)) & features.ts.le(end)].reset_index(drop=True)
            full = labels.loc[labels.ts.gt(kst(origin)) & labels.ts.le(end)].reset_index(drop=True)
            common = None
            for base in BASE_IDS:
                folder = locations(base, origin)
                record = read(folder / 'receipt.json')
                assert record['origin'] == origin and kst(record['end']) == end
                predicted = self.generation_frame(base, origin, folder, train, evaluation, full, replay)
                history = (kst(origin) - train.ts.min()).total_seconds() / 86400
                assert record['train_history_days'] == history
                if common is None:
                    common = predicted.drop(columns='p').copy()
                    common['model_origin'] = kst(origin)
                    common['train_history_days'] = history
                else:
                    pd.testing.assert_frame_equal(keys(common), keys(predicted), check_exact=True)
                common[f'cross_{base}'] = predicted.p.to_numpy()
                for name in ('receipt.json', 'predictions.parquet'):
                    pins[str((folder / name).relative_to(ROOT))] = sha(folder / name)
            pieces.append(common)
        result = pd.concat(pieces, ignore_index=True)
        assert not result.duplicated(['model_origin', *KEYS]).any()
        assert result.model_origin.lt(result.ts).all() and result.ts.le(kst(cutoff)).all()
        return result, pins

    def search_data(self, replay=False):
        manifest = read(OUT / 'shared/search_data_manifest.json')
        file_checks(OUT / 'shared', manifest)
        for name, expected in manifest['origin_source_sha256'].items():
            assert sha(ROOT / name) == expected
        features, _ = self.table('2025-03-01')
        columns = list(dict.fromkeys([*KEYS, 'capacity_kw', *self.rich, *WEATHER, *CALENDAR]))
        pd.testing.assert_frame_equal(features[columns], pd.read_parquet(OUT / 'shared/features.parquet'), check_exact=True)
        common, pins = self.origin_common(self.protocol['inner_origins'], '2025-03-01',
                                         lambda base, origin: OUT / 'bases' / base / 'origins' / origin, replay)
        assert pins == manifest['origin_source_sha256']
        pool = common.loc[~common.night & common.ts.le(kst('2024-12-01'))].reset_index(drop=True)
        pd.testing.assert_frame_equal(pool, pd.read_parquet(OUT / 'shared/pool.parquet'), check_exact=True)
        assert len(pool) == manifest['pool_rows'] and len(pool[KEYS].drop_duplicates()) == manifest['unique_pool_targets']
        applications = {}
        for fold, item in self.protocol['folds'].items():
            part = common.loc[common.model_origin.eq(kst(item['origin'])) & common.ts.gt(kst(item['origin'])) & common.ts.le(kst(item['end']))].reset_index(drop=True)
            if fold in self.annual:
                labels = pd.read_parquet(DATA / fold / 'labels.parquet')
                pd.testing.assert_frame_equal(keys(part), keys(labels), check_exact=True)
                for name in ('y', 'smp', 'k', 'night'):
                    np.testing.assert_array_equal(part[name], labels[name])
                if 'p_reference' in labels:
                    part['p_reference'] = labels.p_reference.to_numpy()
            pd.testing.assert_frame_equal(part, pd.read_parquet(OUT / 'shared' / (fold + '.parquet')), check_exact=True)
            applications[fold] = self.with_features(part, features[columns], daylight_only=True)
        keys(pd.concat([applications[name][KEYS] for name in self.quarter], ignore_index=True))
        assert manifest['feature_columns'] == self.rich and manifest['quarter_keys_disjoint']
        self.shared = manifest, self.with_features(pool, features[columns]), applications
        return self.shared

    @staticmethod
    def with_features(frame, features, daylight_only=False):
        keys(features)
        columns = [name for name in features if name not in frame and name not in KEYS]
        selected = frame.loc[~frame.night].reset_index(drop=True) if daylight_only else frame
        result = selected.merge(features[KEYS + columns], on=KEYS, how='left', sort=False, validate='many_to_one', indicator=True)
        pd.testing.assert_frame_equal(result[KEYS], selected[KEYS].reset_index(drop=True), check_exact=True)
        assert result._merge.eq('both').all()
        result.drop(columns='_merge', inplace=True)
        if daylight_only:
            return frame.merge(result[KEYS + columns], on=KEYS, how='left', sort=False, validate='one_to_one')
        return result

    @staticmethod
    def for_base(frame, identifier):
        result = frame.copy()
        result['p'] = result[f'cross_{identifier}'].to_numpy()
        return result

    def correction(self, folder, config, seed, fold, pool, application, cutoff, horizon, provenance):
        record = read(folder / 'receipt.json')
        file_checks(folder, record)
        assert record['config'] == config and record['seed'] == seed and record['fold'] == fold and record['status'] == 'PASS'
        assert record['native_saved_model_replay']
        train, matrix, target, weights = novel_training(pool, config, cutoff, horizon, self.rich)
        transform = read(folder / 'transform.json')
        digest = hashlib.sha256(pd.util.hash_pandas_object(train[['model_origin', *KEYS]], index=False).to_numpy().tobytes()).hexdigest()
        expected = dict(features=list(matrix), cutoff=cutoff, horizon_days=horizon, training_rows=len(train),
            unique_targets=len(train[KEYS].drop_duplicates()), training_target_start=str(train.ts.min()), training_target_end=str(train.ts.max()),
            generating_origin_start=str(train.model_origin.min()), generating_origin_end=str(train.model_origin.max()),
            chronology_keys_sha256=digest, every_origin_precedes_target=True, train_only_feature_mask=True,
            group_mix=config['group_mix'], anchor_penalty=config['anchor_penalty'], provenance=provenance)
        for name, value in expected.items():
            assert transform[name] == value, (str(folder), name)
        for name, value in dict(weight_min=weights.min(), weight_max=weights.max(), weight_mean=weights.mean(), target_min=target.min(), target_max=target.max()).items():
            np.testing.assert_allclose(transform[name], value, rtol=1e-12, atol=1e-12)
        groups = (['pooled'] if config['group_mix'] < 1 else []) + (['G1', 'G2'] if config['group_mix'] > 0 else [])
        files = [name + '.txt' for name in groups]
        assert transform['model_files'] == record['model_files'] == files and record['real_model_fits'] == len(files)
        assert set(record['files_sha256']) == {*files, 'predictions.parquet', 'transform.json'}
        day = application.loc[~application.night].reset_index(drop=True)
        matrix_pred = novel_engineered(day, config, self.rich)[list(matrix)]
        outputs = {}
        params = dict(objective='regression_l1', seed=seed, num_iterations=config['n_estimators'],
            learning_rate=config['learning_rate'], num_leaves=config['num_leaves'], min_data_in_leaf=config['min_child_samples'],
            lambda_l2=config['reg_lambda'], feature_fraction=.9, bagging_fraction=.8, bagging_freq=1,
            num_threads=4, deterministic=True, force_col_wise=True)
        receipt_params = {name: config[name] for name in ('num_leaves', 'n_estimators', 'learning_rate', 'min_child_samples', 'reg_lambda')}
        receipt_params.update(objective='regression_l1', colsample_bytree=.9, subsample=.8, subsample_freq=1,
            n_jobs=4, verbose=-1, random_state=seed, deterministic=True, force_col_wise=True)
        assert record['model_params'] == receipt_params
        for name in groups:
            model = lgb.Booster(model_file=str(folder / (name + '.txt')))
            assert model.feature_name() == list(matrix)
            assert all(model.params[key] == value for key, value in params.items())
            with threadpool_limits(limits=1):
                outputs[name] = model.predict(matrix_pred, num_threads=1)
            self.replayed += 1
        mix = config['group_mix']
        delta = (1 - mix) * outputs.get('pooled', np.zeros(len(day))) + mix * np.where(day.grp.eq('G1'), outputs.get('G1', 0.), outputs.get('G2', 0.))
        units = day.capacity_kw.to_numpy() * curve(day)
        changed = np.clip(day.p.to_numpy() + config['shrink'] * np.clip(delta, -config['bound'], config['bound']) * units, 0, day.static_capacity.to_numpy())
        expected_frame = application.rename(columns={'p': 'p_base'}).copy()
        expected_frame['p'] = 0.0
        expected_frame.loc[~expected_frame.night, 'p'] = changed
        keep = [*KEYS, 'y', 'smp', 'k', 'night', 'capacity_kw', 'static_capacity', 'p_reference', 'p_base', 'p']
        expected_frame = expected_frame[[name for name in keep if name in expected_frame]]
        stored = pd.read_parquet(folder / 'predictions.parquet')
        pd.testing.assert_frame_equal(stored, expected_frame, check_exact=True)
        if 'y' in stored:
            close_dict(record['score'], score(stored, stored.p))
            close_dict(record['raw_score'], score(stored, stored.p_base))
        else:
            assert record['score'] is None and record['raw_score'] is None
        self.training_checks += 1
        return stored

    def trial_frames(self, identifier, replay=False):
        config = self.configs[identifier]
        folder = OUT / 'trials' / identifier
        result = read(folder / 'result.json')
        assert result['status'] == 'PASS' and result['config'] == config and result['base_id'] == config['base_id']
        assert result['seeds'] == [0, 1, 2] and result['completed_seed_folds'] == 48
        assert result['protocol_sha256'] == sha(OUT / 'protocol.json')
        assert self.shared is not None
        manifest, common_pool, applications = self.shared
        pool = self.for_base(common_pool, config['base_id']) if replay else None
        frames, fits = {}, 0
        for seed in (0, 1, 2):
            frames[seed] = {}
            for fold, item in self.protocol['folds'].items():
                location = folder / f'seed{seed}' / fold
                receipt = read(location / 'receipt.json')
                file_checks(location, receipt)
                assert receipt['status'] == 'PASS' and receipt['config'] == config and receipt['seed'] == seed and receipt['fold'] == fold
                fits += receipt['real_model_fits']
                if replay:
                    frame = self.correction(location, config, seed, fold, pool, self.for_base(applications[fold], config['base_id']), item['origin'], item['horizon_days'],
                        dict(shared_manifest_sha256=sha(OUT / 'shared/search_data_manifest.json'), matched_cross_base_ids=list(BASE_IDS)))
                else:
                    frame = pd.read_parquet(location / 'predictions.parquet')
                    labels = applications[fold]
                    common = [name for name in labels if name in frame and name not in {'p', 'p_base'}]
                    pd.testing.assert_frame_equal(frame[common], labels[common], check_exact=True)
                    np.testing.assert_array_equal(frame.p_base, labels[f'cross_{config["base_id"]}'])
                    close_dict(receipt['score'], score(frame, frame.p))
                    close_dict(receipt['raw_score'], score(frame, frame.p_base))
                frames[seed][fold] = frame
        assert result['real_model_fits'] == fits
        computed, _ = evaluate_development(frames, self.annual, self.quarter, result['blend']['alpha'])
        check_evaluation(result, computed)
        self.checked_results[identifier] = dict(sha256=sha(folder / 'result.json'), computed=computed)
        return frames

    def deployment_table(self, cutoff):
        assert self.late_allowed
        filters = [('ts', '<=', kst(cutoff))]
        features = pq.read_table(ROOT / 'analysis_outputs/renew_20261107/runtime_inputs/test_train.parquet', filters=filters).to_pandas()
        site = pq.read_table(ROOT / 'submission/cache/feat_train.parquet', columns=['ts', 'site_id', 'energy', 'night'], filters=filters).to_pandas()
        site['grp'] = site.site_id.map(read(ROOT / 'analysis_outputs/autoresearch_20261103/cache/assignment.json'))
        assert site.grp.notna().all()
        labels = site.groupby(KEYS, as_index=False).agg(y=('energy', 'sum'), night=('night', 'all'))
        prices = pq.read_table(ROOT / 'submission/cache/smp.parquet', columns=['ts', 'smp', 'k'], filters=filters).to_pandas()
        labels = labels.merge(prices, on='ts', validate='many_to_one')
        labels = labels.merge(features[KEYS + ['capacity_kw']], on=KEYS, how='left', validate='one_to_one')
        labels['static_capacity'] = labels.grp.map(read(ROOT / 'analysis_outputs/renew_20261105/final/static_capacity.json'))
        features = joined(features, labels, ['y', 'smp', 'k'])
        assert labels.capacity_kw.isna().equals(labels.night)
        assert labels.ts.le(kst(cutoff)).all() and features.ts.le(kst(cutoff)).all()
        self.tables[cutoff] = features, labels
        return features, labels

    def completion_inputs(self, split, cutoff):
        features, _ = self.deployment_table(cutoff)
        origins = [str(ts.date()) for ts in pd.date_range('2021-06-01', kst(cutoff).tz_localize(None), freq='QS-MAR') if kst(ts) < kst(cutoff)]
        def location(base, origin):
            old = OUT / 'bases' / base / 'origins' / origin
            end = min(kst(origin) + pd.Timedelta(days=366), kst(cutoff))
            if (old / 'receipt.json').exists() and kst(read(old / 'receipt.json')['end']) == end:
                return old
            return COMP / 'oof' / cutoff / base / origin
        common, pool_pins = self.origin_common(origins, cutoff, location, replay=True)
        columns = list(dict.fromkeys([*KEYS, 'capacity_kw', *self.rich, *WEATHER, *CALENDAR]))
        pool = self.with_features(common.loc[~common.night].reset_index(drop=True), features[columns])
        part = 'test' if split == 'test' else 'march_may'
        evaluation = pd.read_parquet(FINAL / 'data' / part / 'evaluation.parquet')
        coverage = pd.read_parquet(FINAL / 'data' / part / 'coverage.parquet')
        full = pd.read_parquet(FINAL / 'predictions' / split / 'predictions.parquet', columns=KEYS + ['p', 'static_capacity']).rename(columns={'p': 'p_reference'})
        full = joined(full, coverage, ['night'])
        application, application_pins = None, {}
        for base in BASE_IDS:
            folder = COMP / split / 'generation' / base
            generated = self.generation_frame(base, cutoff, folder, features, evaluation, full, replay=True)
            if application is None:
                application = generated.drop(columns='p').copy()
                application['model_origin'] = kst(cutoff)
                application['train_history_days'] = (kst(cutoff) - features.ts.min()).total_seconds() / 86400
            else:
                pd.testing.assert_frame_equal(keys(application), keys(generated), check_exact=True)
            application[f'cross_{base}'] = generated.p.to_numpy()
            application_pins[str((folder / 'receipt.json').relative_to(ROOT))] = sha(folder / 'receipt.json')
        application = self.with_features(application, evaluation[columns], daylight_only=True)
        return pool, application, dict(oof_source_sha256=pool_pins, application_source_sha256=application_pins,
            selection_sha256=sha(COMP / 'selection_frozen.json'), matched_cross_base_ids=list(BASE_IDS))


def check_evaluation(actual, computed):
    assert actual['eligible'] == computed['eligible'] and isinstance(actual['eligible'], bool)
    assert actual['all_history_previously_exposed'] and actual['independent_holdout'] is False
    assert actual['annual_and_quarter_metrics_not_pooled']
    np.testing.assert_allclose(actual['blend']['alpha'], computed['alpha'], rtol=0, atol=1e-14)
    for kind in ('annual', 'quarter'):
        stored = actual[kind + '_summary']
        ratios = computed[kind + '_ratios']
        close_dict(stored['ratios'], ratios)
        for name, value in dict(mean_ratio=np.mean(list(ratios.values())), worst_ratio=max(ratios.values()), improved_folds=sum(value < 1 for value in ratios.values())).items():
            np.testing.assert_allclose(stored[name], value, rtol=1e-12, atol=1e-12)
    close_dict(actual['quarter_summary']['group_aggregate_ratios'], computed['quarter_group_ratios'])
    close_dict(actual['seed_quarter_aggregate_ratios'], computed['seed_quarter_aggregate_ratios'])
    close_dict(actual['blend']['ratios'], computed['blend_ratios'])
    np.testing.assert_allclose(actual['blend']['mean_ratio'], np.mean(list(computed['blend_ratios'].values())), rtol=1e-12, atol=1e-12)
    gate_names = dict(quarter_mean='quarter_mean_at_most_0995', quarter_improved='quarter_improved_at_least_7',
        quarter_worst='quarter_worst_at_most_102', quarter_groups='quarter_each_group_at_most_1',
        each_seed_quarter='each_seed_quarter_aggregate_below_1', annual_mean='annual_mean_below_1',
        annual_improved='annual_improved_at_least_3', annual_worst='annual_worst_at_most_102',
        alpha='primary_alpha_at_least_002', reference_periods='both_blends_at_most_09999', reference_groups='each_blend_group_at_most_1001')
    assert actual['gates'] == {name: computed['gate_checks'][source] for name, source in gate_names.items()}
    assert actual['blend']['primary_only_alpha'] and actual['blend']['recent_unchanged_transfer']
    for fold in ('primary', 'recent'):
        close_dict(actual['blend']['group_ratios'][fold], computed['blend_group_ratios'][fold])
        for role in ('reference', 'blend'):
            close_dict(actual['blend']['scores'][fold][role], computed['blend_scores'][fold][role])
    for fold, metrics in computed['metrics'].items():
        close_dict(actual['folds'][fold]['score'], metrics['corrected'])
        close_dict(actual['folds'][fold]['raw_score'], metrics['raw'])


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
    assert shortlist['before_late_targets'] and shortlist['recovered_diagnostics_excluded']
    recovered_audit = read(ROOT / audit.protocol['input_audit_path'])
    assert len(recovered_audit['rows']) == 12
    recovered_count = 0
    for anchor in recovered_audit['rows']:
        old_folder = LEGACY / 'trials' / anchor['id']
        assert not (old_folder / 'result.json').exists()
        assert sha(old_folder / 'result.json.tmp') == anchor['temporary_summary_sha256']
        for fold, expected in anchor['fold_receipt_sha256'].items():
            assert sha(old_folder / fold / 'receipt.json') == expected
        restored = OUT / 'recovered' / anchor['id'] / 'result.json'
        if restored.exists():
            record = read(restored)
            assert record['source_audit_row'] == anchor and record['alpha'] == anchor['alpha']
            assert record['source_audit_sha256'] == audit.protocol['input_audit_sha256']
            assert record['real_model_fits'] == 0 and record['diagnostics_only'] and not record['eligible']
            recovered_count += 1
    paths = sorted((OUT / 'trials').glob('r*/result.json'))
    if paths:
        audit.search_data(replay=False)
    for path in paths:
        assert path.parent.name in audit.configs
        audit.trial_frames(path.parent.name, replay=False)
    complete_ids = set(audit.checked_results)
    counts = {base: sum(audit.configs[name]['base_id'] == base for name in complete_ids) for base in BASE_IDS}
    sufficient = len(complete_ids) >= 12 and min(counts.values()) >= 3
    assert shortlist['completed_recipes'] == len(complete_ids) and shortlist['completed_per_base'] == counts
    assert shortlist['minimum_coverage_passed'] == sufficient
    ordered = sorted(complete_ids, key=lambda name: (*audit.checked_results[name]['computed']['rank'], name))
    expected_selected, seen = [], set()
    if sufficient:
        for name in ordered:
            config = audit.configs[name]
            if audit.checked_results[name]['computed']['eligible'] and config['base_id'] not in seen:
                expected_selected.append(dict(id=name, base_id=config['base_id'], config=config,
                                              result_sha256=audit.checked_results[name]['sha256']))
                seen.add(config['base_id'])
                if len(expected_selected) == 3:
                    break
    selected = shortlist['selected']
    assert selected == expected_selected, 'Frozen shortlist differs from independently reconstructed ranking'
    uncommitted_complete = []
    for identifier in audit.configs:
        if identifier not in complete_ids and all((OUT / 'trials' / identifier / f'seed{seed}' / fold / 'receipt.json').exists()
                for seed in (0, 1, 2) for fold in audit.protocol['folds']):
            uncommitted_complete.append(identifier)
    report.update(outcome=result['status'], completion_result_sha256=sha(COMP / 'result.json'),
        completed_recipes_verified=len(complete_ids), completed_per_base=counts,
        eligible_committed_recipes=sum(audit.checked_results[name]['computed']['eligible'] for name in complete_ids),
        complete_but_uncommitted_recipe_ids=uncommitted_complete,
        recovered_diagnostic_records_verified=recovered_count, recovered_diagnostics_selected=False)
    if result['status'] in {'NO_QUALIFYING_RECIPE', 'INSUFFICIENT_COMPLETED_COVERAGE'}:
        assert not selected and result['exported'] is False and result['march_may_targets_loaded'] is False
        assert (result['status'] == 'NO_QUALIFYING_RECIPE') == sufficient
        return {**report, 'status': 'PASS', 'verification_status': 'PASS', 'late_targets_loaded': False,
                'reason': 'Committed-result ranking and coverage verified; no exported candidate. Uncommitted/diagnostic records are not proof of absence of possible improvements.'}
    assert result['status'] in {'ENSEMBLE_GATE_FAILED', 'EXPORTED_UNSCORED_CANDIDATE'}
    selection = read(COMP / 'selection_frozen.json')
    assert selection['selected'] == selected and 1 <= len(selected) <= 3
    assert len({item['base_id'] for item in selected}) == len(selected)
    assert selection['seed_weights'] == {str(seed): 1/3 for seed in (0, 1, 2)}
    assert selection['base_weights'] == {item['base_id']: 1/len(selected) for item in selected}
    assert selection['protocol_sha256'] == sha(OUT / 'protocol.json')
    assert selection['before_late_targets'] and selection['primary_only_alpha'] and selection['recent_used_for_development_selection']
    assert datetime.fromisoformat(selection['utc']) >= datetime.fromisoformat(shortlist['utc'])
    audit.search_data(replay=True)
    parts = {item['id']: audit.trial_frames(item['id'], replay=True) for item in selected}
    seed_frames = {seed: {fold: combined([parts[item['id']][seed][fold] for item in selected])
                         for fold in audit.protocol['folds']} for seed in (0, 1, 2)}
    evidence, validation = evaluate_development(seed_frames, audit.annual, audit.quarter, selection['alpha'])
    check_evaluation(selection['evidence'], evidence)
    assert selection['eligible'] == evidence['eligible'] and selection['alpha'] == evidence['alpha']
    report.update(native_model_replays=audit.replayed, verified_oof_origin_artifact_checks=audit.oof_origins,
        duplicate_safe_training_weight_checks=audit.training_checks, selection_sha256=sha(COMP / 'selection_frozen.json'))
    if result['status'] == 'ENSEMBLE_GATE_FAILED':
        assert not selection['eligible'] and result['exported'] is False and result['march_may_targets_loaded'] is False
        return {**report, 'status': 'PASS', 'verification_status': 'PASS', 'late_targets_loaded': False,
                'reason': 'Fixed equal-base/equal-seed ensemble rejection verified; no candidate exported'}
    assert selection['eligible'] and result['exported'] and result['uploaded'] is False
    audit.late_allowed = True
    outputs = {}
    frozen_time = datetime.fromisoformat(selection['utc'])
    for split, cutoff in [('latest_cutoff_march_may', '2025-03-01'), ('test', '2025-06-01')]:
        pool, application, provenance = audit.completion_inputs(split, cutoff)
        frames = []
        for item in selected:
            for seed in (0, 1, 2):
                folder = COMP / split / item['id'] / f'seed{seed}'
                assert datetime.fromisoformat(read(folder / 'started.json')['utc']) >= frozen_time
                frames.append(audit.correction(folder, item['config'], seed, split,
                    audit.for_base(pool, item['base_id']), audit.for_base(application, item['base_id']), cutoff, 366, provenance))
        output = combined(frames)
        output['p_component'] = output.p
        output['p'] = output.p_reference + selection['alpha'] * (output.p_component - output.p_reference)
        path = COMP / split / 'predictions.parquet'
        frozen = read(path.parent / 'frozen.json')
        assert sha(path) == frozen['predictions_sha256'] and frozen['selection_sha256'] == sha(COMP / 'selection_frozen.json')
        assert frozen['before_late_scoring'] and datetime.fromisoformat(frozen['utc']) >= frozen_time
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
    candidate = ROOT / 'submission/research_23kst_candidate_20261108'
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
        improvement_scope='Frozen quarterly, annual, per-group, per-seed and primary/recent development gates only; all history was exposed',
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
