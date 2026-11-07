"""Build a compact, honest comparison from completed experiment receipts."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import csv
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'analysis_outputs/renew_20261107'
EXPERIMENTS = {
    'shift_linux': '분포 변화 가중치',
    'pca_station': '관측소 PCA 16성분',
    'dart_station': 'DART 800트리',
    'cloud_curve': '연속 구름량 보정',
    'cloud_solar_surface': '구름량·태양 고도 보정',
    'weather_residual': '기상 잔여 오차 보정',
}
EXPORTS = {'cloud_curve': ('cloud_curve_final', 'renew_cloud_curve_candidate_20261107'),
           'cloud_solar_surface': ('cloud_solar_surface_final', 'renew_cloud_solar_candidate_20261107'),
           'weather_residual': ('weather_residual_final', 'renew_weather_residual_candidate_20261107')}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    best = ROOT / 'submission/renew_candidate_20261105/submission_files.zip'
    assert sha(best) == 'ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434'
    rows, candidates, counts = [], [], {'generation': 0, 'domain': 0, 'pca': 0, 'calibration': 0, 'alpha': 0}
    for name, label in EXPERIMENTS.items():
        path = OUT / name / 'results.json'
        if not path.exists():
            rows.append(dict(name=name, label=label, status='pending'))
            continue
        result = read(path)
        check = path.parent / 'independent_check.json'
        row = dict(name=name, label=label, status='verified' if check.exists() and read(check)['status'] == 'PASS' else 'unverified',
                   eligible=result['eligible'], primary_W_pct=result['scores']['primary']['p']['W_pct'],
                   recent_W_pct=result['scores']['recent']['p']['W_pct'],
                   primary_delta=result['scores']['primary']['p']['W_pct'] - result['scores']['primary']['p_reference']['W_pct'],
                   recent_delta=result['scores']['recent']['p']['W_pct'] - result['scores']['recent']['p_reference']['W_pct'],
                   results_sha256=sha(path), alpha=result.get('alpha_primary_only'))
        for kind in counts:
            counts[kind] += result.get(f'real_{kind}_fit_count', 0)
        if name in EXPORTS:
            final_name, candidate_name = EXPORTS[name]
            final, candidate = OUT / final_name, ROOT / 'submission' / candidate_name
            if (final / 'diagnostics.json').exists():
                diagnostic = read(final / 'diagnostics.json')['scores']['latest_cutoff_march_may']
                row['march_may_W_pct'] = diagnostic['p']['W_pct']
                row['march_may_delta'] = diagnostic['p']['W_pct'] - diagnostic['p_reference']['W_pct']
            if (candidate / 'submission_files.zip').exists():
                export_check = final / 'independent_export_check.json'
                candidates.append(dict(name=name, directory=str(candidate.relative_to(ROOT)),
                    zip_sha256=sha(candidate / 'submission_files.zip'),
                    independently_verified=export_check.exists() and read(export_check)['status'] == 'PASS'))
        rows.append(row)
    stamp = datetime.now(ZoneInfo('Asia/Seoul')).isoformat()
    result = dict(updated_kst=stamp, official_best_user_reported=6454220836, official_best_zip_sha256=sha(best),
        official_submission_made=False, official_score_improvement_established=False,
        all_history_previously_exposed=True, reference_retained=True,
        comparison_reference='Official-best weather-only baseline, not a claim to dominate every previous development candidate',
        fit_counts=counts, experiments=rows, exported_candidates=candidates)
    (OUT / 'summary.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    fields = ['name', 'label', 'status', 'eligible', 'primary_W_pct', 'recent_W_pct', 'march_may_W_pct',
              'primary_delta', 'recent_delta', 'march_may_delta', 'alpha', 'results_sha256']
    with (OUT / 'results.csv').open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    table = ['| 후보 | 기본 기간 W% | 최근 기간 W% | 후기 진단 W% | 개발 조건 |',
             '|---|---:|---:|---:|---|', '| 기존 최고 공식 제출 | 11.959229 | 11.000953 | 9.390467 | 보존 |']
    for row in rows:
        if row['status'] == 'pending':
            continue
        late = f"{row['march_may_W_pct']:.6f}" if 'march_may_W_pct' in row else '평가 안 함'
        decision = '통과' if row['eligible'] else '기각'
        table.append(f"| {row['label']} | {row['primary_W_pct']:.6f} | {row['recent_W_pct']:.6f} | {late} | {decision} |")
    sky = read(ROOT / 'analysis_outputs/renew_20261105/sky_wave/results.json')['selected']['scores']
    links = '\n'.join(f"- [{entry['name']} ZIP](../../{entry['directory']}/submission_files.zip), SHA256 `{entry['zip_sha256']}`" for entry in candidates)
    doc = f'''# OIBC 모델 개선 실행 기록 — 2026-11-07

최종 갱신: {stamp}

이번 실험은 최고 공식 점수로 보고된 **6,454,220,836**의 기존 weather-only 후보를 비교 기준으로 삼았습니다. 공식 리더보드에 업로드하지 않았으므로 **공식 점수 개선은 확인되지 않았습니다**. 기존 최고 ZIP과 다른 이전 후보를 보존했습니다.

## 결과

W%는 가격·시간대 가중 절대오차이며 낮을수록 좋습니다. 기본 기간은 2023-06-01 이후~2024-06-01, 최근 기간은 2024-06-01 이후~2025-03-01입니다. 후기 진단은 최신 학습 기준의 2025-03-01 이후~2025-06-01입니다. 모두 한국시간이며 오른쪽 끝을 포함합니다.

{chr(10).join(table)}

기본 기간에서 고정한 설정을 최근 기간에 그대로 적용했습니다. 보정 후보의 기본 기간 결과는 일부 표본 내 효과입니다. 모든 과거 기간은 이미 연구에 사용되었으며 독립적인 미공개 테스트가 아닙니다. 후기 진단은 각 후보의 예측을 저장하고 해시로 고정한 뒤 계산했으며 계수 재선택에 사용하지 않았습니다. 개발 조건 통과와 공식 점수 개선은 다릅니다.

기존 sky 후보의 개발 W%는 {sky['primary']['p']['W_pct']:.6f}/{sky['recent']['p']['W_pct']:.6f}입니다. 새 보정이 모든 이전 후보를 지배한다고 주장하지 않습니다. 후기 진단이 악화한 후보는 기존 최고 제출을 대체할 근거가 충분하지 않습니다.

## 제출 후보

{links or '아직 생성된 후보가 없습니다.'}

각 ZIP은 `composition.csv`, `forecast.csv`만 담습니다. 조합은 원래 최고 ZIP의 바이트를 그대로 사용했으며 253개 발전소, 두 그룹 각각 8,760시간, 총 17,520행을 검사했습니다. 예측은 소수 셋째 자리, 야간 0, 음수·비유한 값 없음, 그룹 설비용량 상한을 만족합니다. 후보별 `manifest.json`에 계수와 결과·파일 해시가 있습니다.

## 실행과 검증

- 발전량 모델 {counts['generation']}회, 도메인 분류기 {counts['domain']}회, PCA {counts['pca']}회, 보정 학습 {counts['calibration']}회, 혼합 비율 선택 {counts['alpha']}회. 학습은 직렬로 실행했습니다.
- Linux CPU 4개·메모리 16GiB 환경에서 CPU4/BLAS1을 사용했습니다. 선형계획 보정은 HiGHS 1스레드입니다.
- 원래 station 데이터와 시간 경계, 학습 구간만 사용한 피처 마스크·정규화·가중치, 전체 행 키, 야간 범위를 독립 검증했습니다.
- Windows→Linux 이동으로 생긴 텍스트 줄바꿈 변경은 명시적으로 구분했습니다. 이번에 필요한 수치 데이터는 원래 해시와 일치했습니다. 누락된 최종 학습 LFS 객체는 별도 사본으로 복구했고 기존 포인터 파일을 바꾸지 않았습니다.
- 트리 모델은 저장본 전체 재생을 검사했습니다. PCA는 학습 공분산의 고유값·고유벡터와 투영을 독립 계산했습니다. 선형계획은 저장된 원문제·쌍대해·정지 조건·쌍대 간극과 예측을 독립 확인했습니다.
- 제출 파일은 생산 코드와 별도 구현으로 재계산해 반올림 결과, ZIP 내용, KST 시간, 용량, 원래 조합 바이트와 기존 파일 보존을 확인했습니다.

입력 검증: `independent_input_check.json`. 개별 실험: `<후보>/protocol.json`, `results.json`, `independent_check.json`. 제출 검증: `<후보>_final/independent_export_check.json`. 자세한 표: `results.csv`; 기계 판독용 요약: `summary.json`.

## 실행 명령

Python은 `/workspace/.venvs/oibc-2026/bin/python`입니다. 코드 위치는 `submission/score_push_continue/`입니다. 이미 완료된 결과를 보호하므로 동일 출력 경로에 재학습을 반복하지 않습니다. 재현하려면 원본 입력을 유지하고 새 실행의 출력이 아직 없는 별도 작업 사본을 사용하세요.

```bash
python submission/score_push_continue/verify_inputs.py
python submission/score_push_continue/shift_linux.py --prepare
python submission/score_push_continue/shift_linux.py --run
python submission/score_push_continue/pca_station.py --prepare
python submission/score_push_continue/pca_station.py --run
python submission/score_push_continue/dart_station.py --prepare
python submission/score_push_continue/dart_station.py --run
python submission/score_push_continue/cloud_curve.py --prepare
python submission/score_push_continue/cloud_curve.py --run
python submission/score_push_continue/cloud_solar_surface.py --prepare
python submission/score_push_continue/cloud_solar_surface.py --run
python submission/score_push_continue/weather_residual.py --prepare
python submission/score_push_continue/weather_residual.py --run
python submission/score_push_continue/verify_completed.py shift_linux
python submission/score_push_continue/verify_completed.py pca_station
python submission/score_push_continue/verify_completed.py dart_station
python submission/score_push_continue/verify_cloud_curve.py
python submission/score_push_continue/verify_cloud_solar_surface.py
python submission/score_push_continue/verify_weather_residual.py
python submission/score_push_continue/summarize.py
```

각 실험의 독립 검증을 통과한 뒤에만 `export_*.py`를 실행합니다. 결과가 기각된 모델은 제출 후보로 내보내지 않았습니다. 이번 실행은 계정 잔여 토큰이나 전체 사용량을 조회하지 못했으므로 토큰 전량 소진을 확인했다는 의미가 아닙니다.
'''
    (OUT / 'REPORT.md').write_text(doc, encoding='utf-8')
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
