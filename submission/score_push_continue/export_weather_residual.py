"""Export only the independently verified, fixed eligible cloud correction.

No training, coefficient selection, or leaderboard submission occurs here.
The March--May figures are read only after every deployment prediction is sealed.
"""
from pathlib import Path
import io
import json
import shutil
import subprocess
import sys
import zipfile

import joblib
import numpy as np
import pandas as pd

from weather_residual import OUT as WAVE, INPUT_COLUMNS, FEATURES, PARAMS, apply_residual
from shift_linux import ROOT, KEYS, sha, read, save, now, metric, assert_keys

FINAL = ROOT / 'analysis_outputs/renew_20261105/final'
OUT = ROOT / 'analysis_outputs/renew_20261107/weather_residual_final'
CANDIDATE = ROOT / 'submission/renew_weather_residual_candidate_20261107'
BEST = ROOT / 'submission/renew_candidate_20261105/submission_files.zip'
SPLITS = ('old_cutoff_march_may', 'latest_cutoff_march_may', 'test')


def main():
    result = read(WAVE / 'results.json')
    assert result['eligible'] and result['both_folds_improve']
    verified = read(WAVE / 'independent_check.json')
    assert verified['status'] == 'PASS'
    assert sha(BEST) == 'ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434'
    assert not OUT.exists() and not CANDIDATE.exists(), 'Preserve existing export'
    coefficient = WAVE / 'fits/primary/config.json'
    model_path = WAVE / 'fits/primary/model.joblib'
    model = joblib.load(model_path)
    fitted = read(coefficient)
    assert fitted['features'] == FEATURES and fitted['parameters'] == PARAMS and fitted['shrink'] == .5
    assert model.feature_names_in_.tolist() == FEATURES and model.n_iter_ == 100 and not model.do_early_stopping_
    for name, expected in read(WAVE / 'terminal_manifest.json').items():
        assert sha(WAVE / name) == expected, name
    protected = {}
    for folder in ('renew_candidate_20261105', 'renew_hour_candidate_20261105', 'renew_sky_candidate_20261105'):
        protected.update({str(p.relative_to(ROOT)): sha(p) for p in (ROOT / 'submission' / folder).rglob('*') if p.is_file()})
    OUT.mkdir()
    shutil.copyfile(coefficient, OUT / 'config.json')
    shutil.copyfile(model_path, OUT / 'model.joblib')
    shutil.copyfile(__file__, OUT / 'export_weather_residual.py')
    inputs = {}
    for split in SPLITS:
        feature_split = 'test' if split == 'test' else 'march_may'
        for path in (FINAL / 'predictions' / split / 'predictions.parquet',
                     FINAL / 'data' / feature_split / 'evaluation.parquet',
                     FINAL / 'data' / feature_split / 'coverage.parquet'):
            inputs[str(path.relative_to(ROOT))] = sha(path)
    save(OUT / 'protocol.json', dict(created_utc=now(), coefficient_sha256=sha(coefficient), model_sha256=sha(model_path),
         development_results_sha256=sha(WAVE / 'results.json'), independent_check_sha256=sha(WAVE / 'independent_check.json'),
         source_sha256={str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__), Path(__file__).with_name('weather_residual.py'), Path(__file__).with_name('shift_linux.py')]},
         recipe='Original official-best unrounded weather-only prediction * (1 + .5 * clipped fixed six-weather-feature HGB residual delta); static-cap clip; night zero',
         inputs_sha256=inputs, protected_sha256=protected, new_fits=0, diagnostics_do_not_select=True,
         all_history_exposed=True, official_score_available=False, uploaded=False))
    frozen = {}
    predictions = {}
    for split in SPLITS:
        feature_split = 'test' if split == 'test' else 'march_may'
        reference = pd.read_parquet(FINAL / 'predictions' / split / 'predictions.parquet',
                                    columns=[*KEYS, 'p', 'static_capacity']).rename(columns={'p': 'p_reference'})
        cloud = pd.read_parquet(FINAL / 'data' / feature_split / 'evaluation.parquet', columns=[*KEYS, *FEATURES])
        coverage = pd.read_parquet(FINAL / 'data' / feature_split / 'coverage.parquet')
        assert len(reference) == (17520 if split == 'test' else 4416)
        joined = reference.merge(coverage, on=KEYS, how='left', sort=False, validate='one_to_one')
        joined = joined.merge(cloud, on=KEYS, how='left', sort=False, validate='one_to_one', indicator=True)
        assert_keys(joined, reference)
        assert joined.night.notna().all() and joined._merge.eq('left_only').equals(joined.night)
        assert joined.loc[joined.night, 'p_reference'].eq(0).all()
        app = joined[INPUT_COLUMNS]
        predicted = apply_residual(app, model)
        # Independent saved-model replay followed by explicit bounded arithmetic.
        replay_model = joblib.load(OUT / 'model.joblib')
        raw_delta = replay_model.predict(app[FEATURES])
        np.testing.assert_array_equal(predicted.raw_delta, raw_delta)
        delta = np.clip(raw_delta, -.15, .15)
        replay = np.clip(app.p_reference.to_numpy() * (1 + .5 * delta), 0, app.static_capacity.to_numpy())
        replay[app.night.to_numpy()] = 0
        np.testing.assert_allclose(predicted.p, replay, rtol=1e-14, atol=1e-10)
        folder = OUT / split
        folder.mkdir()
        app.to_parquet(folder / 'inputs.parquet', index=False)
        predicted.to_parquet(folder / 'predictions.parquet', index=False)
        frozen[split] = sha(folder / 'predictions.parquet')
        predictions[split] = predicted
    save(OUT / 'predictions_fixed.json', dict(utc=now(), before_diagnostic_label_reads=True,
         coefficient_sha256=sha(coefficient), model_sha256=sha(model_path), prediction_sha256=frozen))
    # Establish that the source is exactly the previous submitted forecast after rounding.
    with zipfile.ZipFile(BEST) as archive:
        assert sorted(archive.namelist()) == ['composition.csv', 'forecast.csv']
        composition_bytes = archive.read('composition.csv')
        original = pd.read_csv(io.BytesIO(archive.read('forecast.csv')))
    original['ts'] = pd.to_datetime(original.ts).dt.tz_convert('Asia/Seoul')
    original = original.rename(columns={'group': 'grp'}).sort_values(['grp', 'ts']).reset_index(drop=True)
    test = predictions['test'].sort_values(['grp', 'ts']).reset_index(drop=True)
    assert_keys(test, original)
    np.testing.assert_array_equal(np.round(test.p_reference, 3), original.forecast_kwh)
    diagnostics = {}
    for split in SPLITS[:-1]:
        labels = pd.read_parquet(FINAL / 'predictions' / split / 'scored_predictions.parquet', columns=[*KEYS, 'y', 'smp', 'k'])
        assert_keys(predictions[split], labels)
        frame = predictions[split].merge(labels, on=KEYS, sort=False, validate='one_to_one')
        frame.to_parquet(OUT / split / 'scored_predictions.parquet', index=False)
        diagnostics[split] = {column: metric(frame, column) for column in ('p_reference', 'p')}
    save(OUT / 'diagnostics.json', dict(scores=diagnostics, descriptive_only=True, used_for_reselection=False,
         label_read_after_prediction_freeze=True, all_history_exposed=True))
    CANDIDATE.mkdir()
    (CANDIDATE / 'composition.csv').write_bytes(composition_bytes)
    export = pd.DataFrame({'group': test.grp, 'ts': test.ts.astype(str), 'forecast_kwh': np.round(test.p, 3)})
    export.to_csv(CANDIDATE / 'forecast.csv', index=False, lineterminator='\r\n')
    with zipfile.ZipFile(CANDIDATE / 'submission_files.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in ('composition.csv', 'forecast.csv'):
            archive.write(CANDIDATE / name, arcname=name)
    check = subprocess.run([sys.executable, str(ROOT / 'submission/validate_artifacts.py'), str(CANDIDATE), '--self-check'],
                           capture_output=True, text=True)
    (OUT / 'validation.log').write_text(check.stdout + check.stderr, encoding='utf-8')
    assert check.returncode == 0, check.stdout + check.stderr
    validation = json.loads(check.stdout)
    assert validation['rows_above_own_capacity'] == 0
    with zipfile.ZipFile(CANDIDATE / 'submission_files.zip') as archive:
        assert sorted(archive.namelist()) == ['composition.csv', 'forecast.csv']
        assert archive.read('composition.csv') == composition_bytes
        assert archive.read('forecast.csv') == (CANDIDATE / 'forecast.csv').read_bytes()
    for name, expected in inputs.items():
        assert sha(ROOT / name) == expected
    for name, expected in protected.items():
        assert sha(ROOT / name) == expected
    hashes = {name: sha(CANDIDATE / name) for name in ('composition.csv', 'forecast.csv', 'submission_files.zip')}
    manifest = dict(protocol_sha256=sha(OUT / 'protocol.json'), coefficient_sha256=sha(coefficient), model_sha256=sha(model_path),
         recipe=read(OUT / 'protocol.json')['recipe'], features=FEATURES, parameters=PARAMS, delta_bounds=[-.15,.15], shrink=.5,
         development_scores=result['scores'], supplemental_forward_diagnostic=result['diagnostic_scores'],
         deployment_diagnostics=diagnostics, source_best_zip_sha256=sha(BEST), files_sha256=hashes,
         validation=validation, all_history_exposed=True, primary_fit_partly_in_sample=True,
         official_best_user_reported=6454220836, official_score_available=False, uploaded=False)
    save(CANDIDATE / 'manifest.json', manifest)
    (CANDIDATE / 'README.md').write_text(
         '# 기상 잔여 오차 보정 후보\n\n'
         '기존 최고 공식 점수 제출의 예측에 6개 기상 변수의 잔여 오차 보정만 추가했습니다. '
         '기본 기간에서 고정한 얕은 트리 100개로 보정량을 예측하고 ±15%로 제한한 뒤 절반만 적용했습니다. '
         '결측 기상값은 모델의 결측 분기를 사용하며, 야간 0과 설비용량 상한을 유지합니다.\n\n'
         '`submission_files.zip`에는 기존과 바이트까지 같은 `composition.csv`와 '
         '17,520행의 `forecast.csv`가 있습니다.\n\n'
         '모든 과거 평가 기간은 이미 연구에 사용됐으며 독립 테스트가 아닙니다. '
         '기본 기간 보정 효과는 일부 표본 내 결과입니다. 2025년 3~5월 진단은 '
         '예측을 고정한 뒤 계산했으며 계수를 다시 선택하지 않았습니다. '
         '이 후보의 공식 점수는 아직 없고 업로드하지 않았습니다.\n\n'
         '수치, 모델 설정, 입력·출력 해시는 manifest.json에 있습니다. '
         '최고 공식 점수 6,454,220,836은 이전 사용자 보고값이며 원본 ZIP을 보존했습니다.\n', encoding='utf-8')
    save(OUT / 'export_check.json', dict(status='PASS', validator_exit_code=check.returncode, sites=253,
         forecast_rows=17520, independent_application_replay=True, previous_submitted_forecast_reconstructed=True,
         original_composition_bytes_preserved=True, protected_candidate_files_unchanged=True,
         diagnostics_not_used_for_reselection=True, files_sha256=hashes, uploaded=False))
    print(json.dumps({'status': 'PASS', 'candidate': str(CANDIDATE), 'validation': validation,
                      'development_scores': result['scores'], 'deployment_diagnostics': diagnostics}, indent=2))


if __name__ == '__main__':
    main()
