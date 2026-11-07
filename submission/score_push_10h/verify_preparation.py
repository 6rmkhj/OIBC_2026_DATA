"""Independent source/key/chronology/target checks for the 10-hour campaign.

This verifier does not import production preparation/engine code or fit models.
It reconstructs the official floating-point aggregation contract from projected
site observations, while never loading observed targets after the search cutoff.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os

os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis_outputs/research_10h_20261107'
DATA = OUT / 'data'
KEYS = ['ts', 'grp']
END = pd.Timestamp('2025-03-01', tz='Asia/Seoul')
FOLDS = {
    'early2022': ('2022-06-01', '2023-06-01'),
    'primary': ('2023-06-01', '2024-06-01'),
    'winter': ('2023-12-01', '2024-12-01'),
    'spring': ('2024-03-01', '2025-03-01'),
    'recent': ('2024-06-01', '2025-03-01'),
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def assert_keys(frame):
    assert frame[KEYS].notna().all().all()
    assert not frame.duplicated(KEYS).any()


def sorted_keys(frame):
    assert_keys(frame)
    return frame[KEYS].sort_values(KEYS).reset_index(drop=True)


def compare(left, right):
    assert_keys(left)
    assert_keys(right)
    pd.testing.assert_frame_equal(left.sort_values(KEYS).reset_index(drop=True),
                                  right.sort_values(KEYS).reset_index(drop=True), check_exact=True)


def normalizer(values):
    positive = np.maximum(values, 0.)
    exponent = np.divide(-.059, positive, out=np.zeros(len(positive)), where=positive > 0)
    return np.maximum(1.098 * positive * np.exp(exponent), .05)


def main():
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    manifest = read(DATA / 'manifest.json')
    assert manifest['status'] == 'PASS'
    assert manifest['folds'] == {k: {'origin': a, 'end': b} for k, (a, b) in FOLDS.items()}
    assert manifest['search_end_kst'] == str(END)
    for name, expected in manifest['source_sha256'].items():
        path = (ROOT / name).resolve()
        assert path.is_relative_to(ROOT)
        assert digest(path) == expected, name
    for name, expected in manifest['data_sha256'].items():
        path = (DATA / name).resolve()
        assert path.is_relative_to(DATA)
        assert digest(path) == expected, name
    best = ROOT / 'submission/renew_candidate_20261105/submission_files.zip'
    assert digest(best) == 'ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434'
    original_spec = read(ROOT / 'analysis_outputs/score_push_gpu_20261104/data/primary/features.json')
    rich, station = original_spec['rich'], original_spec['station']
    spec = read(DATA / 'features.json')
    assert spec['rich'] == rich and spec['station'] == station
    assert len(rich) == 100 and len(station) == 904
    assert not {'cf', 'y', 'energy', 'smp', 'k', 'ts', 'grp', 'capacity_kw'} & set(station)
    filters = [('ts', '<=', END)]
    full_path = ROOT / 'analysis_outputs/renew_20261107/runtime_inputs/test_train.parquet'
    feature_columns = [*KEYS, 'capacity_kw', *station]
    original = pq.read_table(full_path, columns=[*feature_columns, 'cf'], filters=filters).to_pandas()
    assert original.ts.max() <= END and len(original) == 37743
    source = pq.read_table(ROOT / 'submission/cache/feat_train.parquet',
                           columns=['ts', 'site_id', 'energy', 'night'], filters=filters).to_pandas()
    assert source.ts.max() <= END and not source.duplicated(['ts', 'site_id']).any()
    assert np.isfinite(source.energy).all() and source.night.notna().all()
    assignment = read(ROOT / 'analysis_outputs/autoresearch_20261103/cache/assignment.json')
    assert len(assignment) == 253
    source['grp'] = source.site_id.map(assignment)
    assert source.grp.notna().all()
    # Explicitly preserve the established float32 group-sum contract. In
    # particular, an all-night flag does not replace an observed target with 0.
    truth = source.groupby(KEYS, as_index=False, sort=True).agg(y=('energy', 'sum'), night=('night', 'all'))
    del source
    prices = pq.read_table(ROOT / 'submission/cache/smp.parquet', columns=['ts', 'smp', 'k'], filters=filters).to_pandas()
    assert not prices.ts.duplicated().any()
    truth = truth.merge(prices, on='ts', how='left', validate='many_to_one', sort=False)
    assert np.isfinite(truth[['y', 'smp', 'k']].to_numpy()).all()
    # A few observed aggregate targets are slightly negative; keep those exact
    # observations as the scorer does rather than imposing a physical clip.
    assert truth.smp.ge(0).all() and truth.k.gt(0).all()
    labels = pd.read_parquet(DATA / 'search_labels.parquet')
    compare(labels[[*KEYS, 'y', 'night', 'smp', 'k']], truth)
    assert len(labels) == 69098 and labels.ts.max() <= END
    pd.testing.assert_frame_equal(sorted_keys(labels.loc[~labels.night]), sorted_keys(original))
    assert labels.capacity_kw.isna().equals(labels.night)
    assert labels.daylight.equals(~labels.night)
    caps = read(ROOT / 'analysis_outputs/renew_20261105/final/static_capacity.json')
    np.testing.assert_array_equal(labels.static_capacity, labels.grp.map(caps))
    features = pd.read_parquet(DATA / 'search_features.parquet')
    compare(features[[*feature_columns, 'cf']], original)
    source_y = original[KEYS].merge(truth[[*KEYS, 'y', 'smp', 'k']], on=KEYS, how='left', validate='one_to_one', sort=False)
    pd.testing.assert_frame_equal(features[[*KEYS, 'y', 'smp', 'k']], source_y, check_exact=True)
    records = []
    for fold, (begin, finish) in FOLDS.items():
        origin = pd.Timestamp(begin, tz='Asia/Seoul')
        limit = pd.Timestamp(finish, tz='Asia/Seoul')
        directory = DATA / fold
        train = pd.read_parquet(directory / 'train.parquet')
        future = pd.read_parquet(directory / 'evaluation.parquet')
        scored = pd.read_parquet(directory / 'labels.parquet')
        compare(train, features.loc[features.ts <= origin])
        compare(future, original.loc[(original.ts > origin) & (original.ts <= limit), feature_columns])
        expected_labels = labels.loc[(labels.ts > origin) & (labels.ts <= limit)]
        compare(scored[list(labels)], expected_labels)
        assert train.ts.max() <= origin < future.ts.min() <= future.ts.max() <= limit <= END
        assert not {'cf', 'y', 'smp', 'k', 'energy'} & set(future)
        mask = read(directory / 'features.json')
        assert mask['train_only_feature_selection'] and mask['origin'] == str(origin) and mask['end'] == str(limit)
        for family, names in [('rich', rich), ('station', station)]:
            chosen = []
            for name in names:
                values = train[name].to_numpy()
                assert not np.isinf(values).any()
                if len(np.unique(values[np.isfinite(values)])) > 1:
                    chosen.append(name)
            assert mask['selected'][family] == mask['selected_' + family] == chosen
        pd.testing.assert_frame_equal(sorted_keys(scored.loc[~scored.night]), sorted_keys(future))
        if fold in {'primary', 'recent'}:
            reference = pq.read_table(ROOT / 'analysis_outputs/renew_20261106/shift_wave/data' / fold / 'labels.parquet',
                                       columns=[*KEYS, 'y', 'smp', 'k', 'p_reference'],
                                       filters=[('ts', '>', origin), ('ts', '<=', limit)]).to_pandas()
            compare(scored[list(reference)], reference)
            assert scored.loc[scored.night, 'p_reference'].eq(0).all()
        # Real-row algebra validates the normalization/weights proposed by the
        # engine, independently of the fitted model or future targets.
        inverse = train.capacity_kw.to_numpy() * normalizer(train.cosz.to_numpy())
        assert np.isfinite(inverse).all() and (inverse > 0).all()
        target = train.y.to_numpy() / inverse
        money = train.smp.to_numpy() * train.k.to_numpy()
        trial_prediction = np.linspace(-.05, 1.05, len(train))
        for power in (1, 2):
            lhs = money * inverse ** power * np.abs(trial_prediction - target) ** power
            rhs = money * np.abs(trial_prediction * inverse - train.y.to_numpy()) ** power
            np.testing.assert_allclose(lhs, rhs, rtol=2e-10, atol=1e-5)
        age = (origin - train.ts).dt.total_seconds().to_numpy() / 86400
        assert (age >= 0).all()
        delta = np.abs(train.y.to_numpy() - train.cf.to_numpy() * train.capacity_kw.to_numpy())
        records.append({'fold': fold, 'train_rows': len(train), 'daylight_rows': len(future), 'score_rows': len(scored),
                        'night_rows': int(scored.night.sum()), 'night_nonzero_y_rows': int((scored.night & scored.y.ne(0)).sum()),
                        'max_allsite_vs_legacy_training_energy_difference': float(delta.max()),
                        'rich_features': len(mask['selected_rich']), 'station_features': len(mask['selected_station'])})
    # Receipts are evidence, not a replacement for the source projections above.
    for entry in read(DATA / 'read_receipts.json'):
        constraints = [x for x in entry['filters'] if x[0] == 'ts' and x[1] == '<=']
        assert constraints and pd.Timestamp(constraints[-1][2]) <= END
    report = {'status': 'PASS', 'utc': datetime.now(timezone.utc).isoformat(), 'records': records,
              'search_end_kst': str(END), 'scoring_rows': len(labels), 'daylight_rows': len(features),
              'nonzero_all_night_targets_preserved': int((labels.night & labels.y.ne(0)).sum()),
              'negative_observed_targets_preserved': int(labels.y.lt(0).sum()),
              'source_aggregation_reconstructed': True, 'train_only_masks_verified': True,
              'L1_and_L2_normalization_identities_verified': True, 'actual_model_fits': 0,
              'march_may_2025_targets_loaded': False, 'manifest_sha256': digest(DATA / 'manifest.json'),
              'verifier_sha256': digest(Path(__file__)), 'best_zip_sha256': digest(best)}
    path = OUT / 'independent_preparation.json'
    if path.exists():
        old = read(path)
        assert {k: v for k, v in report.items() if k != 'utc'} == {k: v for k, v in old.items() if k != 'utc'}
    else:
        path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
