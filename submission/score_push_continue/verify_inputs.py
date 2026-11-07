"""Independent, read-only validation of migrated historical experiment inputs.

Run from any directory with the project Python. Writes only a new continuation
receipt; never rewrites historical manifests or normalizes source files.
"""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pyarrow as pa

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'analysis_outputs/renew_20261106/shift_wave'
OUT = ROOT / 'analysis_outputs/renew_20261107'
KEYS = ['ts', 'grp']


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def resolve(base, name):
    path = (base / name.replace('\\', '/')).resolve()
    assert path.is_relative_to(base.resolve())
    return path


def historical_hash(base, name, expected):
    path = resolve(base, name)
    actual = digest(path)
    match = 'exact'
    if actual != expected:
        # Only declared text formats can be explained by checkout line endings.
        assert path.suffix in {'.json', '.py', '.md', '.csv', '.txt', '.log', '.ps1'}, name
        content = path.read_bytes()
        content.decode('utf-8-sig')
        windows = content.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
        assert hashlib.sha256(windows).hexdigest() == expected, name
        match = 'CRLF_to_LF_checkout'
    return {'file': str(path.relative_to(ROOT)), 'current_sha256': actual,
            'historical_sha256': expected, 'match': match}


def norm(cosz):
    positive = np.maximum(cosz, 0)
    exponent = np.divide(-.059, positive, out=np.zeros(len(positive)), where=positive > 0)
    return np.maximum(1.098 * positive * np.exp(exponent), .05)


def keys_equal(left, right):
    assert not left.duplicated(KEYS).any()
    assert not right.duplicated(KEYS).any()
    pd.testing.assert_frame_equal(left[KEYS], right[KEYS], check_exact=True)


def main():
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    OUT.mkdir(parents=True, exist_ok=True)
    destination = OUT / 'independent_input_check.json'
    assert not destination.exists(), 'Preserve previous verification receipt'
    protocol = read(SOURCE / 'protocol.json')
    checked = []
    for base, manifest in [(SOURCE, read(SOURCE / 'prepared_manifest.json')),
                           (ROOT, protocol['input_sha256'])]:
        checked.extend(historical_hash(base, name, sha) for name, sha in manifest.items())
    # Preserve the CURRENT migrated workspace. Historical hash identity for all
    # old files is deliberately not claimed (some files are LFS pointers).
    current = {name: digest(resolve(ROOT, name)) for name in protocol['protected_sha256']}
    best = ROOT / 'submission/renew_candidate_20261105/submission_files.zip'
    assert digest(best) == 'ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434'
    columns = protocol['domain_columns']
    records = []
    for fold, (start, end) in protocol['folds'].items():
        data = SOURCE / 'data' / fold
        train = pd.read_parquet(data / 'train.parquet')
        future = pd.read_parquet(data / 'evaluation.parquet')
        raw = ROOT / 'analysis_outputs/score_push_gpu_20261104/data' / fold
        pd.testing.assert_frame_equal(train, pd.read_parquet(raw / 'train.parquet'), check_exact=True)
        pd.testing.assert_frame_equal(future, pd.read_parquet(raw / 'evaluation.parquet'), check_exact=True)
        cutoff, limit = [pd.Timestamp(t, tz='Asia/Seoul') for t in (start, end)]
        assert train.ts.max() <= cutoff < future.ts.min() <= future.ts.max() <= limit
        assert not {'cf', 'energy', 'y', 'smp', 'k'} & set(future)
        mask = read(data / 'feature_mask.json')
        assert len(mask['candidate_columns']) == 904
        selected = [c for c in mask['candidate_columns'] if train[c].nunique(dropna=True) > 1]
        assert selected == mask['selected_columns']
        assert not {'cf', 'energy', 'y', 'smp', 'k', *KEYS} & set(selected)
        training = pd.read_parquet(data / 'training_transform.parquet')
        inverse = pd.read_parquet(data / 'evaluation_transform.parquet')
        keys_equal(train, training)
        keys_equal(future, inverse)
        scale = norm(train.cosz.to_numpy())
        age = (cutoff - train.ts).dt.total_seconds().to_numpy() / 86400
        decay = np.exp2(-age / 180)
        normalized_decay = decay / decay.mean()
        for name, expected in {'normalizer': scale, 'age_days': age, 'decay': decay,
                               'recency_multiplier': normalized_decay,
                               'sample_weight': scale * normalized_decay,
                               'target_normalized': train.cf.to_numpy() / scale}.items():
            np.testing.assert_allclose(training[name], expected, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(inverse.inverse_kwh, norm(future.cosz.to_numpy()) * future.capacity_kw,
                                   rtol=1e-12, atol=1e-12)
        domain = {}
        for kind, frame in [('train', train), ('evaluation', future)]:
            projection = pd.read_parquet(data / f'domain_{kind}_inputs.parquet')
            pd.testing.assert_frame_equal(projection, frame[columns], check_exact=True)
            domain[kind] = np.asfortranarray(projection.to_numpy(dtype=np.float64))
        med = np.nanmedian(domain['train'], axis=0)
        imputed = np.where(np.isnan(domain['train']), med, domain['train'])
        mean, std = imputed.mean(axis=0), imputed.std(axis=0, ddof=0)
        std[std == 0] = 1
        preprocessing = read(data / 'preprocessing.json')
        for name, expected in [('median', med), ('mean', mean), ('scale', std)]:
            np.testing.assert_allclose(preprocessing[name], expected, rtol=1e-14, atol=1e-12)
        for kind, frame in domain.items():
            expected = np.clip((np.where(np.isnan(frame), med, frame) - mean) / std, -8, 8)
            np.testing.assert_allclose(np.load(data / f'domain_{kind}_matrix.npy'), expected,
                                       rtol=1e-14, atol=1e-12)
        partition = pd.read_parquet(data / 'domain_fold.parquet')
        keys_equal(train, partition)
        ordinal = train.ts.dt.tz_convert('Asia/Seoul').dt.date.map(lambda d: d.toordinal()).to_numpy()
        np.testing.assert_array_equal(partition.date_ordinal, ordinal)
        np.testing.assert_array_equal(partition.domain_fold, ordinal % 3)
        app = pd.read_parquet(data / 'application_inputs.parquet')
        labels = pd.read_parquet(data / 'labels.parquet')
        coverage = pd.read_parquet(data / 'coverage.parquet')
        keys_equal(app, labels)
        keys_equal(app, coverage)
        joined = coverage.merge(future[KEYS], on=KEYS, how='outer', indicator=True, validate='one_to_one')
        assert joined._merge.eq('left_only').equals(joined.night)
        assert labels.loc[coverage.night, 'p_reference'].eq(0).all()
        reference = pd.read_parquet(ROOT / 'analysis_outputs/renew_20261105/calibration_wave/comparisons/temperature_then_snow' / fold / 'predictions.parquet')
        pd.testing.assert_frame_equal(labels, reference[[*KEYS, 'y', 'smp', 'k', 'p']].rename(columns={'p': 'p_reference'}), check_exact=True)
        pd.testing.assert_frame_equal(app, reference[list(app)], check_exact=True)
        monetary = labels.smp.to_numpy() * labels.k.to_numpy()
        pct = 100 * np.sum(monetary * np.abs(labels.p_reference - labels.y)) / np.sum(monetary * labels.y)
        assert abs(pct - protocol['reference_scores'][fold]) < 1e-10
        records.append({'fold': fold, 'train_rows': len(train), 'daylight_rows': len(future),
                        'evaluation_rows': len(labels), 'features': len(selected), 'reference_W_pct': pct})
    result = {'status': 'PASS', 'utc': datetime.now(timezone.utc).isoformat(), 'records': records,
              'required_historical_artifacts': checked, 'current_protected_sha256': current,
              'best_zip_sha256': digest(best), 'real_model_fits': 0,
              'scope': 'Raw station data, train-only masks/targets/weights/domain transforms, exact keys, night coverage, historical baseline. All periods previously exposed.'}
    destination.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ['required_historical_artifacts', 'current_protected_sha256']}, indent=2))


if __name__ == '__main__':
    main()
