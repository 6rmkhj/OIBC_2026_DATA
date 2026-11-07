"""Independently replay a completed campaign trial; never fit or load late targets."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os

os.environ.update(OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', OMP_NUM_THREADS='4')
import lightgbm as lgb
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis_outputs/research_10h_20261107'
DATA = OUT / 'data'
KEYS = ['ts', 'grp']
FOLDS = {
    'early2022': ('2022-06-01', '2023-06-01'),
    'primary': ('2023-06-01', '2024-06-01'),
    'winter': ('2023-12-01', '2024-12-01'),
    'spring': ('2024-03-01', '2025-03-01'),
    'recent': ('2024-06-01', '2025-03-01'),
}
BASELINE = dict(id='c000', features='station', objective='regression_l1', target='original_cf',
                weighting='legacy', half_life=180, n_estimators=400, learning_rate=.03,
                num_leaves=63, min_child_samples=50, reg_lambda=0., colsample_bytree=.8, subsample=.8)


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def keys(frame):
    assert not frame.duplicated(KEYS).any() and frame[KEYS].notna().all().all()
    return frame[KEYS]


def curve(frame):
    cosine = np.maximum(frame.cosz.to_numpy(dtype=float), 0.)
    exponent = np.divide(-.059, cosine, out=np.zeros(len(cosine)), where=cosine > 0)
    return np.maximum(1.098 * cosine * np.exp(exponent), .05)


def score(frame, prediction):
    y = frame.y.to_numpy(dtype=float)
    price = frame.smp.to_numpy(dtype=float)
    weight = price * frame.k.to_numpy(dtype=float)
    penalty = np.dot(weight, np.abs(np.asarray(prediction, dtype=float) - y))
    revenue = np.dot(price, y)
    return dict(W=float(penalty), W_pct=float(100 * penalty / np.dot(weight, y)),
                revenue=float(revenue), S=float(revenue - .1 * penalty), rows=len(frame))


def close_dict(actual, expected):
    assert actual.keys() == expected.keys()
    for name in expected:
        np.testing.assert_allclose(actual[name], expected[name], rtol=1e-12, atol=1e-5)


def main(identifier):
    protocol = read(OUT / 'protocol.json')
    manifest = read(DATA / 'manifest.json')
    preparation = read(OUT / 'independent_preparation.json')
    assert preparation['status'] == 'PASS' and preparation['manifest_sha256'] == sha(DATA / 'manifest.json')
    assert sha(DATA / 'manifest.json') == protocol['data_manifest_sha256']
    assert sha(OUT / 'configs.json') == protocol['configs_sha256']
    late_labels = ROOT / 'analysis_outputs/renew_20261105/final/predictions/latest_cutoff_march_may/scored_predictions.parquet'
    assert sha(late_labels) == protocol['late_audit_labels_hash_only_sha256']
    for name, expected in {**manifest['source_sha256'], **protocol['source_sha256'],
                           **protocol['deployment_input_sha256']}.items():
        assert sha(ROOT / name) == expected, name
    for name, expected in manifest['data_sha256'].items():
        assert sha(DATA / name) == expected, name
    configs = read(OUT / 'configs.json')
    assert len(configs) == 256 and configs[0] == BASELINE
    assert len({json.dumps({key: value for key, value in item.items() if key != 'id'}, sort_keys=True)
                for item in configs}) == 256
    config = next(item for item in configs if item['id'] == identifier)
    trial = OUT / 'trials' / identifier
    result = read(trial / 'result.json')
    assert result['id'] == identifier and result['config'] == config and result['status'] == 'PASS'
    assert result['real_model_fits'] == 5 and result['march_may_targets_loaded'] is False
    assert result['protocol_sha256'] == sha(OUT / 'protocol.json')
    records, frames = [], {}
    for fold, (origin, finish) in FOLDS.items():
        directory = trial / fold
        receipt = read(directory / 'receipt.json')
        assert result['folds'][fold] == receipt
        assert receipt['status'] == 'PASS' and receipt['config'] == config
        assert receipt['seed'] == 0 and receipt['fold'] == fold and receipt['real_model_fits'] == 1
        assert receipt['native_saved_model_replay'] and receipt['train_only_feature_mask']
        for name, expected in receipt['files_sha256'].items():
            assert sha(directory / name) == expected, str(directory / name)
        train = pd.read_parquet(DATA / fold / 'train.parquet')
        evaluation = pd.read_parquet(DATA / fold / 'evaluation.parquet')
        labels = pd.read_parquet(DATA / fold / 'labels.parquet')
        output = pd.read_parquet(directory / 'predictions.parquet')
        pd.testing.assert_frame_equal(keys(output), keys(labels), check_exact=True)
        pd.testing.assert_frame_equal(output[list(labels)], labels, check_exact=True)
        assert train.ts.max() <= pd.Timestamp(origin, tz='Asia/Seoul') < evaluation.ts.min()
        assert evaluation.ts.max() <= pd.Timestamp(finish, tz='Asia/Seoul')
        assert not {'y', 'cf', 'energy', 'smp', 'k'} & set(evaluation)
        feature_spec = read(DATA / fold / 'features.json')
        features = [name for name in feature_spec[config['features']] if train[name].nunique(dropna=True) > 1]
        assert features == feature_spec['selected'][config['features']]
        transform = read(directory / 'transform.json')
        assert transform['features'] == features and transform['origin'] == origin
        assert transform['training_rows'] == len(train) and transform['evaluation_rows'] == len(evaluation)
        assert transform['training_start'] == str(train.ts.min()) and transform['training_end'] == str(train.ts.max())
        norm = curve(train)
        inverse = norm * train.capacity_kw.to_numpy(dtype=float)
        age = (pd.Timestamp(origin, tz='Asia/Seoul') - train.ts).dt.total_seconds().to_numpy() / 86400
        decay = np.ones(len(train)) if config['half_life'] is None else np.exp2(-age / config['half_life'])
        target = train.cf.to_numpy() / norm if config['target'] == 'original_cf' else train.y.to_numpy() / inverse
        if config['weighting'] == 'legacy':
            weight = norm * decay / decay.mean()
        else:
            power = 2 if config['objective'] == 'regression_l2' else 1
            weight = train.smp.to_numpy() * train.k.to_numpy() * inverse ** power * decay
            weight /= weight.mean()
        for name, expected in dict(weight_min=weight.min(), weight_max=weight.max(), weight_mean=weight.mean(),
                                   target_min=target.min(), target_max=target.max()).items():
            np.testing.assert_allclose(transform[name], expected, rtol=1e-12, atol=1e-12)
        with threadpool_limits(limits=1, user_api='blas'):
            model = lgb.Booster(model_file=str(directory / 'model.txt'))
            assert model.feature_name() == features
            assert model.num_trees() == config['n_estimators']
            for name, expected in dict(objective=config['objective'], num_iterations=config['n_estimators'],
                    learning_rate=config['learning_rate'], num_leaves=config['num_leaves'],
                    min_data_in_leaf=config['min_child_samples'], lambda_l2=config['reg_lambda'],
                    feature_fraction=config['colsample_bytree'], bagging_fraction=config['subsample'],
                    bagging_freq=1, num_threads=4, seed=0, deterministic=True, force_col_wise=True,
                    device_type='cpu').items():
                assert model.params[name] == expected, (fold, name, model.params[name], expected)
            raw = model.predict(evaluation[features], num_threads=4)
        expected = evaluation[KEYS].copy()
        expected['replay'] = raw * curve(evaluation) * evaluation.capacity_kw.to_numpy()
        joined = labels.merge(expected, on=KEYS, how='left', validate='one_to_one', indicator=True)
        assert joined._merge.eq('left_only').equals(joined.night)
        replay = np.clip(joined.replay.fillna(0).to_numpy(), 0., joined.static_capacity.to_numpy())
        replay[joined.night] = 0.
        np.testing.assert_array_equal(output.p, replay)
        assert output.loc[output.night, 'p'].eq(0).all() and np.isfinite(output.p).all()
        independently_scored = score(labels, replay)
        close_dict(receipt['score'], independently_scored)
        records.append(dict(fold=fold, training_rows=len(train), score_rows=len(output), features=len(features),
            score=independently_scored, native_prediction_replay_exact=True,
            night_nonzero_y_rows=int((labels.night & labels.y.ne(0)).sum()),
            model_sha256=sha(directory / 'model.txt'), receipt_sha256=sha(directory / 'receipt.json')))
        if fold in {'primary', 'recent'}:
            frames[fold] = output
    alpha = float(result['blend']['alpha'])
    frame = frames['primary']
    delta = frame.p.to_numpy() - frame.p_reference.to_numpy()
    monetary = frame.smp.to_numpy() * frame.k.to_numpy()
    supported = (delta != 0) & (monetary > 0)
    ratios = (frame.y.to_numpy()[supported] - frame.p_reference.to_numpy()[supported]) / delta[supported]
    masses = monetary[supported] * np.abs(delta[supported])
    if len(ratios):
        # Check weighted-median subgradient conditions instead of reusing the
        # implementation's sorting/cumulative selection algorithm.
        half = masses.sum() / 2
        if alpha > 0:
            assert masses[ratios < alpha].sum() <= half * (1 + 1e-12)
        if alpha < 1:
            assert masses[ratios > alpha].sum() <= half * (1 + 1e-12)
    else:
        assert alpha == 0
    assert 0 <= alpha <= 1
    scores = {}
    for fold, frame in frames.items():
        blended = frame.p_reference + alpha * (frame.p - frame.p_reference)
        scores[fold] = dict(reference=score(frame, frame.p_reference), component=score(frame, frame.p), blend=score(frame, blended))
        for role in scores[fold]:
            close_dict(result['blend']['scores'][fold][role], scores[fold][role])
    eligible = alpha >= .02 and all(item['blend']['W'] < item['reference']['W'] for item in scores.values())
    assert result['blend']['eligible'] == eligible
    assert result['blend']['primary_only_alpha'] and result['blend']['recent_unchanged_transfer']
    receipt = dict(status='PASS', utc=datetime.now(timezone.utc).isoformat(), id=identifier, records=records,
        alpha=alpha, blend_eligible=eligible, score_formula='sum(SMP*k*abs(p-y)); S=sum(SMP*y)-0.1*W',
        native_prediction_replay_exact=True, all_nights_and_exact_observed_targets_preserved=True,
        primary_weighted_median_optimality_verified=True, actual_model_fits=0, saved_models_replayed=5,
        march_may_2025_targets_loaded=False, protocol_sha256=sha(OUT / 'protocol.json'),
        result_sha256=sha(trial / 'result.json'), verifier_sha256=sha(Path(__file__)),
        official_best_sha256=sha(ROOT / 'submission/renew_candidate_20261105/submission_files.zip'))
    path = OUT / ('independent_baseline_check.json' if identifier == 'c000' else f'independent_{identifier}_check.json')
    if path.exists():
        old = read(path)
        assert {k: v for k, v in receipt.items() if k != 'utc'} == {k: v for k, v in old.items() if k != 'utc'}
    else:
        path.write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', default='c000')
    main(parser.parse_args().id)
