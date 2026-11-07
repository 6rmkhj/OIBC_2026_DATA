"""Read-only final audit. Replays saved models; never trains or resumes a campaign.

Without a terminal completion receipt this reports CHECKPOINT_ONLY honestly.
With an exported candidate it checks frozen selection, validation/deployment
replays, late-audit source targets, exact ZIP content and the protected best ZIP.
"""
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import zipfile

import verify_trial as independent
import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from threadpoolctl import threadpool_limits

ROOT, OUT, DATA, KEYS = independent.ROOT, independent.OUT, independent.DATA, independent.KEYS
read, sha, curve, score, close_dict, keys = (independent.read, independent.sha, independent.curve,
                                          independent.score, independent.close_dict, independent.keys)
FINAL = ROOT / 'analysis_outputs/renew_20261105/final'
COMP = OUT / 'completion'
BEST = ROOT / 'submission/renew_candidate_20261105/submission_files.zip'
BEST_SHA = 'ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434'


def files(directory, receipt):
    for name, expected in receipt['files_sha256'].items():
        assert sha(directory / name) == expected, str(directory / name)


def replay(directory, config, seed, fold, evaluation, full, expected_features):
    receipt = read(directory / 'receipt.json')
    assert receipt['status'] == 'PASS' and receipt['config'] == config
    assert receipt['seed'] == seed and receipt['fold'] == fold
    assert receipt['native_saved_model_replay'] and receipt['real_model_fits'] == 1
    files(directory, receipt)
    transformed = read(directory / 'transform.json')
    assert transformed['features'] == expected_features
    with threadpool_limits(limits=1, user_api='blas'):
        model = lgb.Booster(model_file=str(directory / 'model.txt'))
        assert model.feature_name() == expected_features
        for name, expected in dict(objective=config['objective'], num_iterations=config['n_estimators'],
                learning_rate=config['learning_rate'], num_leaves=config['num_leaves'],
                min_data_in_leaf=config['min_child_samples'], lambda_l2=config['reg_lambda'],
                feature_fraction=config['colsample_bytree'], bagging_fraction=config['subsample'],
                bagging_freq=1, num_threads=4, seed=seed, deterministic=True, force_col_wise=True,
                device_type='cpu').items():
            assert model.params[name] == expected, (fold, name, model.params[name], expected)
        assert model.num_trees() == config['n_estimators']
        raw = model.predict(evaluation[expected_features], num_threads=4)
    prediction = evaluation[KEYS].copy()
    prediction['raw_replay'] = raw * curve(evaluation) * evaluation.capacity_kw.to_numpy()
    joined = full.merge(prediction, on=KEYS, how='left', validate='one_to_one', indicator=True)
    assert joined._merge.eq('left_only').equals(joined.night)
    prediction = np.clip(joined.raw_replay.fillna(0).to_numpy(), 0., joined.static_capacity.to_numpy())
    prediction[joined.night] = 0.
    stored = pd.read_parquet(directory / 'predictions.parquet')
    pd.testing.assert_frame_equal(keys(stored), keys(full), check_exact=True)
    pd.testing.assert_frame_equal(stored[list(full)], full, check_exact=True)
    np.testing.assert_array_equal(stored.p, prediction)
    if 'y' in full:
        close_dict(receipt['score'], score(full, prediction))
    else:
        assert receipt['score'] is None
    return stored


def verify_alpha(frame, alpha):
    difference = frame.p.to_numpy() - frame.p_reference.to_numpy()
    money = frame.smp.to_numpy() * frame.k.to_numpy()
    active = (difference != 0) & (money > 0)
    ratios = (frame.y.to_numpy()[active] - frame.p_reference.to_numpy()[active]) / difference[active]
    masses = money[active] * np.abs(difference[active])
    assert 0 <= alpha <= 1
    if not len(ratios):
        assert alpha == 0
        return
    if alpha > 0:
        assert masses[ratios < alpha].sum() <= masses.sum() / 2 * (1 + 1e-12)
    if alpha < 1:
        assert masses[ratios > alpha].sum() <= masses.sum() / 2 * (1 + 1e-12)


def main():
    assert sha(BEST) == BEST_SHA
    protocol = read(OUT / 'protocol.json')
    baseline = read(OUT / 'independent_baseline_check.json')
    assert baseline['status'] == 'PASS' and baseline['protocol_sha256'] == sha(OUT / 'protocol.json')
    manifest = read(DATA / 'manifest.json')
    assert sha(DATA / 'manifest.json') == protocol['data_manifest_sha256']
    assert sha(OUT / 'configs.json') == protocol['configs_sha256']
    for name, expected in {**manifest['source_sha256'], **protocol['source_sha256'],
                           **protocol['deployment_input_sha256']}.items():
        assert sha(ROOT / name) == expected, name
    report = dict(utc=datetime.now(timezone.utc).isoformat(), actual_model_fits=0,
                  official_best_preserved=True, official_best_sha256=BEST_SHA,
                  verifier_sha256=sha(Path(__file__)), helper_sha256=sha(Path(independent.__file__)),
                  protocol_sha256=sha(OUT / 'protocol.json'), saved_models_replayed=0)
    if not (COMP / 'result.json').exists():
        report.update(status='CHECKPOINT_ONLY', exported_candidate_verified=False,
                      reason='No terminal completion result; no completion or fit was started by this verifier',
                      budget_stop=read(COMP / 'budget_stop.json') if (COMP / 'budget_stop.json').exists() else None)
        return report
    result = read(COMP / 'result.json')
    shortlist = read(COMP / 'shortlist.json')
    report['completion_result_sha256'] = sha(COMP / 'result.json')
    if result['status'] == 'NO_QUALIFYING_RECIPE':
        assert not shortlist['candidates'] and result['exported'] is False
        assert result['march_may_targets_loaded'] is False
        report.update(status='PASS_NO_QUALIFYING_RECIPE', exported_candidate_verified=False)
        return report
    assert result['status'] in {'SEED_STABILITY_GATE_FAILED', 'EXPORTED_UNSCORED_CANDIDATE'}
    chosen = shortlist['candidates']
    selection = read(COMP / 'selection_frozen.json')
    assert selection['before_late_audit_target_reads'] and selection['no_reselection_after_latest_audit']
    assert selection['shortlist_sha256'] == sha(COMP / 'shortlist.json')
    assert selection['ids'] == [item['id'] for item in chosen]
    assert selection['configs'] == [item['config'] for item in chosen]
    assert selection['seeds'] == [0, 1, 2] and selection['equal_weights']
    assert 1 <= len(chosen) <= 3
    diversity = {tuple(item['config'][key] for key in ('features', 'objective', 'target', 'half_life')) for item in chosen}
    assert len(diversity) == len(chosen)
    base_result = read(OUT / 'trials/c000/result.json')
    for item in chosen:
        selected_result = read(OUT / 'trials' / item['id'] / 'result.json')
        ratios = []
        for fold in independent.FOLDS:
            folder = OUT / 'trials' / item['id'] / fold
            receipt = read(folder / 'receipt.json')
            files(folder, receipt)
            frame = pd.read_parquet(folder / 'predictions.parquet')
            labels = pd.read_parquet(DATA / fold / 'labels.parquet')
            pd.testing.assert_frame_equal(frame[list(labels)], labels, check_exact=True)
            computed = score(frame, frame.p)
            close_dict(selected_result['folds'][fold]['score'], computed)
            ratios.append(computed['W'] / base_result['folds'][fold]['score']['W'])
        assert np.mean(ratios) < 1 and max(ratios) <= 1.02 and sum(value < 1 for value in ratios) >= 3
        assert item['eligible'] and selected_result['blend']['eligible']
    validation = {}
    for fold in ('primary', 'recent'):
        evaluation = pd.read_parquet(DATA / fold / 'evaluation.parquet')
        labels = pd.read_parquet(DATA / fold / 'labels.parquet')
        feature_spec = read(DATA / fold / 'features.json')
        frames = []
        for item in chosen:
            for seed in (0, 1, 2):
                folder = OUT / 'trials' / item['id'] / fold if seed == 0 else COMP / 'validation' / item['id'] / f'seed{seed}' / fold
                frames.append(replay(folder, item['config'], seed, fold, evaluation, labels,
                                     feature_spec['selected'][item['config']['features']]))
                report['saved_models_replayed'] += 1
        expected = np.mean([frame.p.to_numpy() for frame in frames], axis=0)
        ensemble_path = COMP / f'{fold}_ensemble.parquet'
        assert sha(ensemble_path) == selection[f'{fold}_ensemble_sha256']
        ensemble = pd.read_parquet(ensemble_path)
        pd.testing.assert_frame_equal(ensemble[list(labels)], labels, check_exact=True)
        np.testing.assert_array_equal(ensemble.p, expected)
        validation[fold] = ensemble
    alpha = selection['alpha']
    verify_alpha(validation['primary'], alpha)
    improved = []
    for fold, frame in validation.items():
        blended = frame.p_reference + alpha * (frame.p - frame.p_reference)
        computed = dict(reference=score(frame, frame.p_reference), component=score(frame, frame.p), blend=score(frame, blended))
        for role, value in computed.items():
            close_dict(selection['scores'][fold][role], value)
        improved.append(computed['blend']['W'] < computed['reference']['W'])
    assert selection['eligible'] == (alpha >= .02 and all(improved))
    if result['status'] == 'SEED_STABILITY_GATE_FAILED':
        assert not selection['eligible'] and not result['exported'] and not result['march_may_targets_loaded']
        report.update(status='PASS_SEED_STABILITY_GATE_FAILED', exported_candidate_verified=False)
        return report
    assert selection['eligible'] and result['exported'] and result['uploaded'] is False
    frozen_at = datetime.fromisoformat(selection['utc'])
    deployment_outputs = {}
    full_features = ROOT / 'analysis_outputs/renew_20261107/runtime_inputs/test_train.parquet'
    for split, feature_split, origin in [('latest_cutoff_march_may', 'march_may', '2025-03-01'), ('test', 'test', '2025-06-01')]:
        evaluation = pd.read_parquet(FINAL / 'data' / feature_split / 'evaluation.parquet')
        coverage = pd.read_parquet(FINAL / 'data' / feature_split / 'coverage.parquet')
        full = pd.read_parquet(FINAL / 'predictions' / split / 'predictions.parquet',
                               columns=[*KEYS, 'p', 'static_capacity']).rename(columns={'p': 'p_reference'})
        full = full.merge(coverage, on=KEYS, how='left', validate='one_to_one')
        assert full.night.notna().all()
        spec = read(DATA / 'features.json')
        frames = []
        for item in chosen:
            config = item['config']
            training_features = pq.read_table(full_features, columns=['ts', *spec[config['features']]],
                filters=[('ts', '<=', pd.Timestamp(origin, tz='Asia/Seoul'))]).to_pandas()
            expected_features = [name for name in spec[config['features']] if training_features[name].nunique(dropna=True) > 1]
            assert training_features.ts.max() <= pd.Timestamp(origin, tz='Asia/Seoul') < evaluation.ts.min()
            for seed in (0, 1, 2):
                folder = COMP / split / item['id'] / f'seed{seed}'
                assert datetime.fromisoformat(read(folder / 'started.json')['utc']) >= frozen_at
                frames.append(replay(folder, config, seed, split, evaluation, full, expected_features))
                report['saved_models_replayed'] += 1
        output_path = COMP / split / 'predictions.parquet'
        frozen = read(output_path.parent / 'frozen.json')
        assert frozen['prediction_sha256'] == sha(output_path)
        assert frozen['selection_sha256'] == sha(COMP / 'selection_frozen.json')
        output = pd.read_parquet(output_path)
        pd.testing.assert_frame_equal(output[list(full)], full, check_exact=True)
        component = np.mean([frame.p.to_numpy() for frame in frames], axis=0)
        np.testing.assert_array_equal(output.p_component, component)
        np.testing.assert_array_equal(output.p, full.p_reference + alpha * (component - full.p_reference))
        assert np.isfinite(output.p).all() and output.p.ge(0).all()
        assert (output.p <= output.static_capacity + 1e-9).all() and output.loc[output.night, 'p'].eq(0).all()
        deployment_outputs[split] = output
    audit = read(COMP / 'audit.json')
    labels_path = FINAL / 'predictions/latest_cutoff_march_may/scored_predictions.parquet'
    assert sha(labels_path) == protocol['late_audit_labels_hash_only_sha256'] == audit['labels_source_sha256']
    assert audit['selection_sha256'] == sha(COMP / 'selection_frozen.json') and audit['used_for_selection'] is False
    assert frozen_at <= datetime.fromisoformat(read(COMP / 'latest_cutoff_march_may/frozen.json')['utc']) <= datetime.fromisoformat(audit['utc'])
    labels = pd.read_parquet(labels_path, columns=[*KEYS, 'y', 'smp', 'k'])
    scored = deployment_outputs['latest_cutoff_march_may'].merge(labels, on=KEYS, how='left', validate='one_to_one')
    pd.testing.assert_frame_equal(scored, pd.read_parquet(COMP / 'latest_cutoff_march_may/scored_predictions.parquet'), check_exact=True)
    close_dict(audit['reference'], score(scored, scored.p_reference))
    close_dict(audit['candidate'], score(scored, scored.p))
    candidate = Path(result['candidate'])
    assert candidate == ROOT / 'submission/research_10h_candidate_20261107'
    assert sha(candidate / 'manifest.json') == result['manifest_sha256']
    export = read(candidate / 'manifest.json')
    assert export['selection'] == selection and export['audit'] == audit
    assert export['uploaded'] is False and export['official_score_available'] is False
    files(candidate, export)
    with zipfile.ZipFile(BEST) as protected, zipfile.ZipFile(candidate / 'submission_files.zip') as archive:
        assert set(archive.namelist()) == {'composition.csv', 'forecast.csv'}
        assert len(archive.namelist()) == 2
        assert archive.read('composition.csv') == protected.read('composition.csv') == (candidate / 'composition.csv').read_bytes()
        assert archive.read('forecast.csv') == (candidate / 'forecast.csv').read_bytes()
        forecast = pd.read_csv(io.BytesIO(archive.read('forecast.csv')))
        reference_csv = pd.read_csv(io.BytesIO(protected.read('forecast.csv')))
    assert list(forecast) == ['group', 'ts', 'forecast_kwh'] and len(forecast) == 17520
    for frame in (forecast, reference_csv):
        frame['ts'] = pd.to_datetime(frame.ts).dt.tz_convert('Asia/Seoul')
        frame.rename(columns={'group': 'grp'}, inplace=True)
        frame.sort_values(['grp', 'ts'], inplace=True, ignore_index=True)
    test = deployment_outputs['test'].sort_values(['grp', 'ts']).reset_index(drop=True)
    pd.testing.assert_frame_equal(keys(test), keys(forecast), check_exact=True)
    pd.testing.assert_frame_equal(keys(test), keys(reference_csv), check_exact=True)
    np.testing.assert_array_equal(forecast.forecast_kwh, np.round(test.p, 3))
    np.testing.assert_array_equal(reference_csv.forecast_kwh, np.round(test.p_reference, 3))
    assert sha(BEST) == BEST_SHA
    report.update(status='PASS_EXPORTED_UNSCORED_CANDIDATE', exported_candidate_verified=True,
        candidate=str(candidate), candidate_sha256=sha(candidate / 'submission_files.zip'),
        selection_sha256=sha(COMP / 'selection_frozen.json'), alpha=alpha, audit=audit,
        all_history_previously_exposed=True, official_score_available=False, uploaded=False)
    return report


if __name__ == '__main__':
    result = main()
    # Checkpoint results remain console-only; terminal audit evidence is immutable.
    if result['status'].startswith('PASS_'):
        destination = OUT / 'independent_completion_check.json'
        if destination.exists():
            previous = read(destination)
            assert {k: v for k, v in previous.items() if k != 'utc'} == {k: v for k, v in result.items() if k != 'utc'}
        else:
            destination.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
