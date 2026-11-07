"""Independent saved-model, ensemble, metric and provenance checks on new runs."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os

os.environ.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow as pa
from scipy.special import expit
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'analysis_outputs/renew_20261107'
SOURCE = ROOT / 'analysis_outputs/renew_20261106/shift_wave'
KEYS = ['ts', 'grp']


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def metric(frame, prediction):
    y = frame.y.to_numpy()
    money = frame.smp.to_numpy() * frame.k.to_numpy()
    penalty = float(np.dot(money, np.abs(prediction - y)))
    revenue = float(np.dot(frame.smp, y))
    return dict(W=penalty, W_pct=100 * penalty / np.dot(money, y),
                revenue=revenue, S=revenue - .1 * penalty, rows=len(frame))


def weather(inputs, signed):
    factors = read(SOURCE / 'original_weather_coefficients.json')['factors']
    temp = inputs.wa_temp.to_numpy(dtype=float)
    bins = np.digitize(temp, [0, 10, 20, 30], right=False)
    bins[~np.isfinite(temp)] = 5
    t = np.array([r['factor'] for r in factors['temperature']] + [1.])[bins]
    s = np.where(np.isfinite(inputs.extra_wa_snow) & (inputs.extra_wa_snow >= .001),
                 factors['conditional_snow']['factor'], 1.)
    adjustment = .5 + .5 * np.clip(t * s, .85, 1.15)
    cap = inputs.static_capacity.to_numpy()
    clipped = np.maximum(0, np.minimum(signed, cap))
    return clipped, np.maximum(0, np.minimum(clipped * adjustment, cap))


def verify_domain(out, fold):
    data = SOURCE / 'data' / fold
    source = np.load(data / 'domain_train_matrix.npy')
    future = np.load(data / 'domain_evaluation_matrix.npy')
    partition = pd.read_parquet(data / 'domain_fold.parquet')
    logits = np.empty(len(source))
    gradients = []
    for split in range(3):
        trial = out / fold / f'domain_split{split}'
        bundle = joblib.load(trial / 'classifier.joblib')
        model = bundle['classifier']
        assert bundle['preprocessing'] == read(data / 'preprocessing.json')
        assert model.classes_.tolist() == [0, 1]
        held = partition.domain_fold.to_numpy() == split
        raw = pd.read_parquet(trial / 'oof.parquet')
        np.testing.assert_array_equal(raw.row_index, np.flatnonzero(held))
        pd.testing.assert_frame_equal(raw[KEYS].reset_index(drop=True), partition.loc[held, KEYS].reset_index(drop=True))
        logits[held] = (source[held] @ model.coef_.ravel()) + model.intercept_[0]
        np.testing.assert_allclose(raw.logit, logits[held], rtol=1e-13, atol=1e-13)
        np.testing.assert_allclose(model.decision_function(source[held]), raw.logit, rtol=1e-13, atol=1e-13)
        x = np.concatenate([source[~held], future])
        target = np.r_[np.zeros((~held).sum()), np.ones(len(future))]
        balanced = np.where(target == 0, len(target) / (2 * (~held).sum()), len(target) / (2 * len(future)))
        residual = balanced * (expit(x @ model.coef_.ravel() + model.intercept_[0]) - target)
        grad = np.r_[x.T @ residual + model.coef_.ravel() / .01, residual.sum()] / len(target)
        assert np.max(np.abs(grad)) < 1e-5, np.max(np.abs(grad))
        gradients.append(float(np.max(np.abs(grad))))
    base = pd.read_parquet(data / 'training_transform.parquet')
    saved = pd.read_parquet(out / fold / 'domain_weights.parquet')
    pd.testing.assert_frame_equal(saved[KEYS], base[KEYS])
    np.testing.assert_allclose(saved.logit, logits, rtol=1e-13, atol=1e-13)
    modifier = np.sqrt(np.clip(np.exp(logits), .25, 4.))
    expected = base.sample_weight.to_numpy() * modifier
    expected *= base.sample_weight.sum() / expected.sum()
    np.testing.assert_allclose(saved.sample_weight, expected, rtol=1e-13, atol=1e-13)
    np.testing.assert_allclose(saved.base_weight, base.sample_weight, rtol=0, atol=0)
    return {'domain_gradients_max_abs': gradients, 'weight_mass': float(expected.sum()),
            'modifier_min': float(modifier.min()), 'modifier_max': float(modifier.max())}


def verify_pca(out):
    records = []
    for fold in ('primary', 'recent'):
        data = out / 'data' / fold
        original = SOURCE / 'data' / fold
        train = pd.read_parquet(original / 'train.parquet')
        future = pd.read_parquet(original / 'evaluation.parquet')
        specification = read(data / 'pca_features.json')
        all_names = read(original / 'feature_mask.json')['candidate_columns']
        spatial = [c for c in all_names if c.startswith(('wa_station_', 'wb_station_'))]
        selected = [c for c in spatial if train[c].nunique(dropna=True) > 1]
        assert selected == specification['selected_columns']
        assert len(specification['components']) == 16
        raw = np.array(train[selected], dtype=float, order='C')
        median = np.nanmedian(raw, axis=0)
        filled = np.where(np.isnan(raw), median, raw)
        mean, scale = filled.mean(axis=0), filled.std(axis=0, ddof=0)
        standardized = (filled - mean) / scale
        center = standardized.mean(axis=0)
        with np.load(data / 'pca_arrays.npz') as archive:
            fitted = {k: archive[k] for k in archive.files}
        for key, value in [('medians', median), ('mean', mean), ('scale', scale), ('center', center)]:
            np.testing.assert_allclose(fitted[key], value, rtol=1e-12, atol=1e-12)
        vectors = fitted['components']
        covariance = (standardized - center).T @ (standardized - center) / (len(train) - 1)
        np.testing.assert_allclose(vectors @ vectors.T, np.eye(16), rtol=1e-12, atol=1e-12)
        eigenvalues = np.linalg.eigvalsh(covariance)[-16:][::-1]
        np.testing.assert_allclose(fitted['eigenvalues'], eigenvalues, rtol=1e-10, atol=1e-10)
        np.testing.assert_allclose(covariance @ vectors.T, vectors.T * eigenvalues, rtol=1e-9, atol=1e-10)
        np.testing.assert_allclose(fitted['variance_ratio'], eigenvalues / np.trace(covariance), rtol=1e-10, atol=1e-12)
        rich = [c for c in all_names if c not in spatial]
        assert len(rich) == 100
        mask = read(data / 'feature_mask.json')['selected_columns']
        assert mask == [c for c in rich if train[c].nunique(dropna=True) > 1] + specification['components']
        for kind, frame in [('train', train), ('evaluation', future)]:
            saved = pd.read_parquet(data / f'{kind}.parquet')
            pd.testing.assert_frame_equal(saved[KEYS + rich], frame[KEYS + rich])
            raw = np.array(frame[selected], dtype=float, order='C')
            projection = ((np.where(np.isnan(raw), median, raw) - mean) / scale - center) @ vectors.T
            np.testing.assert_allclose(saved[specification['components']], projection, rtol=1e-11, atol=1e-11)
            if kind == 'evaluation':
                assert not {'cf', 'y', 'smp', 'k', 'energy'} & set(saved)
        records.append({'fold': fold, 'source_dimensions': len(selected), 'components': 16,
                        'features': len(mask), 'variance_explained': float(fitted['variance_ratio'].sum()),
                        'train_only_eigensystem_and_projection': 'PASS'})
    report = {'status': 'PASS', 'records': records, 'protocol_sha256': sha(out / 'protocol.json'),
              'prepared_manifest_sha256': sha(out / 'prepared_manifest.json'), 'generation_fits': 0}
    destination = out / 'independent_pca_check.json'
    if not destination.exists():
        destination.write_text(json.dumps(report, indent=2), encoding='utf-8')
    else:
        assert read(destination) == report
    return report


def optimality(frame, alpha):
    base, candidate, y = [frame[c].to_numpy() for c in ('p_reference', 'p_new', 'y')]
    delta = candidate - base
    monetary = frame.smp.to_numpy() * frame.k.to_numpy()
    active = (delta != 0) & (monetary > 0)
    crossings = (y[active] - base[active]) / delta[active]
    masses = monetary[active] * np.abs(delta[active])
    order = np.argsort(crossings)
    optimum = 0. if len(order) == 0 else float(np.clip(crossings[order[np.searchsorted(np.cumsum(masses[order]), .5 * masses.sum())]], 0, 1))
    assert abs(alpha - optimum) < 1e-12
    optimum_loss = np.dot(monetary, np.abs(base + alpha * delta - y))
    for test in np.r_[np.linspace(0, 1, 101), max(alpha - 1e-5, 0), min(alpha + 1e-5, 1)]:
        assert np.dot(monetary, np.abs(base + test * delta - y)) >= optimum_loss - 1e-6
    return optimum


def descriptive_diagnostics(frame):
    money = frame.smp.to_numpy() * frame.k.to_numpy()
    daily = pd.DataFrame({'day': (frame.ts - pd.Timedelta(hours=1)).dt.floor('D'),
                          'delta': money * (np.abs(frame.p - frame.y) - np.abs(frame.p_reference - frame.y)),
                          'denominator': money * frame.y}).groupby('day').sum()
    rng = np.random.default_rng(20261107)
    ix = rng.integers(0, len(daily), size=(2000, len(daily)))
    delta = 100 * daily.delta.to_numpy()[ix].sum(axis=1) / daily.denominator.to_numpy()[ix].sum(axis=1)
    monthly = []
    for month, rows in frame.groupby((frame.ts - pd.Timedelta(hours=1)).dt.strftime('%Y-%m')):
        before, after = metric(rows, rows.p_reference), metric(rows, rows.p)
        monthly.append({'month': month, 'reference_W_pct': before['W_pct'], 'candidate_W_pct': after['W_pct'],
                        'delta_W_pct': after['W_pct'] - before['W_pct']})
    return {'daily_block_bootstrap_delta_W_pct_95CI': np.quantile(delta, [.025, .975]).tolist(),
            'bootstrap_replicates': 2000, 'bootstrap_seed': 20261107, 'months': monthly,
            'interpretation': 'Descriptive only; adaptive selection and prior historical exposure invalidate pristine holdout claims.'}


def verify(name):
    out = BASE / name
    result = read(out / 'results.json')
    protocol = read(out / 'protocol.json')
    assert (out / 'completed.json').exists()
    assert not (out / 'independent_check.json').exists(), 'Preserve verifier evidence'
    for file, expected in read(out / 'terminal_manifest.json').items():
        assert sha(out / file) == expected, file
    receipt = read(BASE / 'independent_input_check.json')
    for file, expected in receipt['current_protected_sha256'].items():
        assert sha(ROOT / file.replace('\\', '/')) == expected, file
    intervals = read(out / 'fit_intervals.json')
    assert len(intervals) == result.get('real_model_fit_count', result['real_generation_fit_count'])
    assert all(a['finished_utc'] <= b['started_utc'] for a, b in zip(intervals, intervals[1:]))
    records, diagnostics = [], {}
    for fold in ('primary', 'recent'):
        domain = verify_domain(out, fold) if name == 'shift_linux' else {}
        data = SOURCE / 'data' / fold
        app = pd.read_parquet(data / 'application_inputs.parquet')
        coverage = pd.read_parquet(data / 'coverage.parquet')
        labels = pd.read_parquet(data / 'labels.parquet')
        inv = pd.read_parquet(data / 'evaluation_transform.parquet')
        model_data = out / 'data' / fold if name == 'pca_station' else data
        mask = read(model_data / 'feature_mask.json')['selected_columns']
        future = pd.read_parquet(model_data / 'evaluation.parquet', columns=mask)
        members = []
        for seed in range(3):
            trial = out / fold / f'generation_seed{seed}'
            saved = pd.read_parquet(trial / 'daylight_raw.parquet')
            pd.testing.assert_frame_equal(saved[KEYS], inv[KEYS])
            model = lgb.Booster(model_file=str(trial / 'model.txt'))
            assert model.feature_name() == list(future)
            assert model.current_iteration() == protocol['generation_parameters']['n_estimators']
            replay = model.predict(future, num_threads=1, validate_features=True) * inv.inverse_kwh.to_numpy()
            np.testing.assert_array_equal(saved.p_raw, replay)
            full = labels[KEYS].merge(saved, how='left', on=KEYS, sort=False, validate='one_to_one')
            pd.testing.assert_frame_equal(full[KEYS], labels[KEYS])
            assert full.p_raw.isna().equals(coverage.night)
            members.append(full.p_raw.fillna(0).to_numpy())
        mean = np.asarray(members).mean(axis=0)
        clipped, corrected = weather(app, mean)
        frame = pd.read_parquet(out / fold / 'predictions.parquet')
        pd.testing.assert_frame_equal(frame[list(labels)], labels)
        np.testing.assert_array_equal(frame.signed_seed_mean, mean)
        np.testing.assert_array_equal(frame.p_component, clipped)
        np.testing.assert_allclose(frame.p_new, corrected, rtol=1e-14, atol=1e-10)
        alpha = result['alpha_primary_only']
        assert frame.alpha.eq(alpha).all()
        np.testing.assert_allclose(frame.p, (1 - alpha) * frame.p_reference + alpha * corrected, rtol=1e-14, atol=1e-10)
        assert frame.loc[coverage.night, 'p'].eq(0).all()
        assert frame.p.ge(0).all() and (frame.p <= app.static_capacity + 1e-8).all()
        if fold == 'primary':
            optimality(frame, alpha)
        for column in ('p', 'p_reference', 'p_new'):
            computed = metric(frame, frame[column].to_numpy())
            for key, value in computed.items():
                np.testing.assert_allclose(result['scores'][fold][column][key], value, rtol=1e-13, atol=1e-7)
        diagnostics[fold] = descriptive_diagnostics(frame)
        records.append({'fold': fold, 'rows': len(frame), 'models_replayed': 3, **domain})
    both = all(result['scores'][fold]['p']['W'] < result['scores'][fold]['p_reference']['W'] for fold in ('primary', 'recent'))
    assert result['both_folds_improve'] == both
    assert result['eligible'] == (both and result['alpha_primary_only'] >= .02)
    report = {'status': 'PASS', 'utc': datetime.now(timezone.utc).isoformat(), 'records': records,
              'eligible': result['eligible'], 'alpha_primary_only': result['alpha_primary_only'],
              'terminal_manifest_sha256': sha(out / 'terminal_manifest.json'),
              'verifier_sha256': sha(Path(__file__)), 'all_history_exposed': True, 'diagnostics': diagnostics}
    (out / 'independent_check.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'diagnostics'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('name')
    parser.add_argument('--inputs-only', action='store_true')
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    with threadpool_limits(limits=1):
        args = parser.parse_args()
        if args.inputs_only:
            assert args.name == 'pca_station'
            print(json.dumps(verify_pca(BASE / args.name), indent=2))
        else:
            if args.name == 'pca_station':
                verify_pca(BASE / args.name)
            verify(args.name)
