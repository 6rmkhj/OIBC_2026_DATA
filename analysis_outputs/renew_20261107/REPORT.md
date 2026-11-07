# OIBC 모델 개선 실행 기록 — 2026-11-07

최종 갱신: 2026-11-07T01:58:12.600918+09:00

이번 실험은 최고 공식 점수로 보고된 **6,454,220,836**의 기존 weather-only 후보를 비교 기준으로 삼았습니다. 공식 리더보드에 업로드하지 않았으므로 **공식 점수 개선은 확인되지 않았습니다**. 기존 최고 ZIP과 다른 이전 후보를 보존했습니다.

## 결과

W%는 가격·시간대 가중 절대오차이며 낮을수록 좋습니다. 기본 기간은 2023-06-01 이후~2024-06-01, 최근 기간은 2024-06-01 이후~2025-03-01입니다. 후기 진단은 최신 학습 기준의 2025-03-01 이후~2025-06-01입니다. 모두 한국시간이며 오른쪽 끝을 포함합니다.

| 후보 | 기본 기간 W% | 최근 기간 W% | 후기 진단 W% | 개발 조건 |
|---|---:|---:|---:|---|
| 기존 최고 공식 제출 | 11.959229 | 11.000953 | 9.390467 | 보존 |
| 분포 변화 가중치 | 11.946060 | 11.048252 | 평가 안 함 | 기각 |
| 관측소 PCA 16성분 | 11.958167 | 11.004912 | 평가 안 함 | 기각 |
| DART 800트리 | 11.956103 | 11.036163 | 평가 안 함 | 기각 |
| 연속 구름량 보정 | 11.838568 | 10.946708 | 9.418260 | 통과 |
| 구름량·태양 고도 보정 | 11.847839 | 10.945554 | 9.417728 | 통과 |
| 기상 잔여 오차 보정 | 11.694870 | 10.927911 | 9.441703 | 통과 |

기본 기간에서 고정한 설정을 최근 기간에 그대로 적용했습니다. 보정 후보의 기본 기간 결과는 일부 표본 내 효과입니다. 모든 과거 기간은 이미 연구에 사용되었으며 독립적인 미공개 테스트가 아닙니다. 후기 진단은 각 후보의 예측을 저장하고 해시로 고정한 뒤 계산했으며 계수 재선택에 사용하지 않았습니다. 개발 조건 통과와 공식 점수 개선은 다릅니다.

기존 sky 후보의 개발 W%는 11.792837/10.955416입니다. 새 보정이 모든 이전 후보를 지배한다고 주장하지 않습니다. 후기 진단이 악화한 후보는 기존 최고 제출을 대체할 근거가 충분하지 않습니다.

## 제출 후보

- [cloud_curve ZIP](../../submission/renew_cloud_curve_candidate_20261107/submission_files.zip), SHA256 `b8c63dc60346e9fc2710eb917bfb0520782d4b98421eec325607156f96d16eb1`
- [cloud_solar_surface ZIP](../../submission/renew_cloud_solar_candidate_20261107/submission_files.zip), SHA256 `e05ac9609aa39c6f09f0efb4d4579af01c43eb5c6384f694abe496442d604b60`
- [weather_residual ZIP](../../submission/renew_weather_residual_candidate_20261107/submission_files.zip), SHA256 `b2474fe6c9c355b16ebc2a808605cd67ae26b57a52c8a1908f6c211ef71d382d`

각 ZIP은 `composition.csv`, `forecast.csv`만 담습니다. 조합은 원래 최고 ZIP의 바이트를 그대로 사용했으며 253개 발전소, 두 그룹 각각 8,760시간, 총 17,520행을 검사했습니다. 예측은 소수 셋째 자리, 야간 0, 음수·비유한 값 없음, 그룹 설비용량 상한을 만족합니다. 후보별 `manifest.json`에 계수와 결과·파일 해시가 있습니다.

## 실행과 검증

- 발전량 모델 18회, 도메인 분류기 6회, PCA 2회, 보정 학습 6회, 혼합 비율 선택 3회. 학습은 직렬로 실행했습니다.
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
