# 전체 실험·시도 상태표

확인 시각: **2026-11-07 19:03:51 KST**.

[프로젝트 요약](../../README.md) · [필터링 가능한 전체 CSV](experiments.csv)

현재 단계의 ID는 고정된 전체 설정 큐를 포함합니다. `pending`은 아직 실행되지 않았다는 뜻이며 실패가 아닙니다. 과거 표의 `keep`/`discard`는 당시 탐색 결정이지 공식 점수 상승이나 실패를 뜻하지 않습니다. 같은 ID의 재시도는 별도 과거 로그 행으로 남깁니다.

현재 5개 기간 검증에서 결과 저장이 실패한 실험은 완료 영수증 수와 별도로 `failed`로 표시합니다. 모델의 과학적 적격 여부를 최종 결과 없이 추정하지 않습니다.

## 설정과 결과 비교 읽는 법

설정 키의 한국어 설명·평가 날짜·대표 전후 비교는 [프로젝트 README](../../README.md#무엇을-바꾸며-실험하는가)에 있습니다. 아래 현재 실험 표는 **앞선 ID 중 설정 차이가 가장 적은 실험**을 비교 대상으로 고릅니다(동률이면 ID순, 점수는 선택에 사용하지 않음). 연장 단계는 동일한 기초 모델 안에서만 비교합니다. 비교 대상은 실험 설계의 공식 대조군을 뜻하지 않습니다.

`primary/recent` 칸: **혼합 전 W_pct (비교 ID 대비 W 상대 변화)**. 낮을수록 좋으며 음수는 개선, 양수는 악화입니다. 두 결과가 모두 정상 완료된 경우만 상대 변화를 계산합니다. 여러 설정이 바뀐 행은 각각의 효과를 분리할 수 없습니다. 대기·실패 행도 설정 차이는 표시하지만 혼합 전 전후 점수를 성공으로 추정하지 않습니다.

CSV에는 각 실험의 전체 `config_json`, `base_id→source_generation_id`, `comparison_id`, `changed_settings`, primary/recent 원래 W와 W_pct, 비교 대상·보정 전 기초 모델 대비 W 변화, `blend_alpha`, 최고 제출 대비 혼합 W 변화를 따로 제공합니다. 실패 후보의 감사로 복원한 혼합 수치는 기존 `audit_gate_pass`와 근거를 함께 확인하세요. 과거 캠페인은 평가 방식이 달라 자동으로 공통 기준을 붙이지 않고 기존 변경 설명·지표 단위·근거를 보존합니다.

## 기초 데이터·예보·구성·점수 검증

기존 make_submission 실행 경로와 입력 품질·예보·발전소 구성·후처리 분석을 정리했습니다. 아래 행은 학습 횟수가 아닌 검토 문서이며, 기존 val_summary는 평가 기간의 자료로 발전소 구성을 선택한 개발 점수입니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| ANALYSIS_MEMO | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/ANALYSIS_MEMO.md) |
| bid_postproc_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/bid_postproc_report.md) |
| comp_verify_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/comp_verify_report.md) |
| composition_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/composition_report.md) |
| forecast_skill_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/forecast_skill_report.md) |
| gen_quality_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/gen_quality_report.md) |
| model_validation_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/model_validation_report.md) |
| smp_weights_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/smp_weights_report.md) |
| spatial_corr_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/spatial_corr_report.md) |
| ver_l1cal_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/ver_l1cal_report.md) |
| verify_composition_math_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_composition_math_report.md) |
| verify_composition_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_composition_report.md) |
| verify_fc_round_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_fc_round_report.md) |
| verify_forecast_input_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_forecast_input_report.md) |
| verify_genq_math_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_genq_math_report.md) |
| verify_gq_cleaning_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_gq_cleaning_report.md) |
| verify_gq_numbers_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_gq_numbers_report.md) |
| verify_l1_calib_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_l1_calib_report.md) |
| verify_l1_calib_repro_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_l1_calib_repro_report.md) |
| verify_round_provider_report | historical_record | 분석 문서 있음 | — | — |  | — | 기초 분석 또는 검증 문서이며, 모델 실험 횟수로 합산하지 않습니다. [기록](../../analysis_outputs/reports/verify_round_provider_report.md) |

## 초기 수상 도전 파이프라인

이전 연도에서 2개 구성과 5개 혼합비, 총 10개 조합을 비교해 inner_twins/direct0.5를 선택했으며, 후기 연간 W_pct는 11.552586으로 기준 11.881605보다 낮았습니다. 표의 10행은 모델 10개가 아닌 조합 평가 수이고, 후보 경로는 submission/award_candidate입니다; 생성 당시 공식 점수는 없었으며 이후 보고된 최초 점수를 어느 파일에 연결할지는 여기서 단정하지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| reference | historical_record | 과거 기록 | — | — | W_pct | 13.7844 | 원본 표/로그 행 1 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 0.0.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |
| reference | historical_record | 과거 기록 | — | — | W_pct | 13.4807 | 원본 표/로그 행 2 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 0.25.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |
| reference | historical_record | 과거 기록 | — | — | W_pct | 13.4126 | 원본 표/로그 행 3 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 0.5.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |
| reference | historical_record | 과거 기록 | — | — | W_pct | 13.5511 | 원본 표/로그 행 4 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 0.75.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |
| reference | historical_record | 과거 기록 | — | — | W_pct | 13.8526 | 원본 표/로그 행 5 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 1.0.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |
| inner_twins | historical_record | 과거 기록 | — | — | W_pct | 13.6476 | 원본 표/로그 행 6 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 0.0.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |
| inner_twins | historical_record | 과거 기록 | — | — | W_pct | 13.3181 | 원본 표/로그 행 7 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 0.25.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |
| inner_twins | historical_record | 과거 기록 | — | — | W_pct | 13.2102 | 원본 표/로그 행 8 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 0.5.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |
| inner_twins | historical_record | 과거 기록 | — | — | W_pct | 13.3134 | 원본 표/로그 행 9 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 0.75.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |
| inner_twins | historical_record | 과거 기록 | — | — | W_pct | 13.5837 | 원본 표/로그 행 10 (재시도·다른 조건을 합치지 않음). 그룹 직접 모델 혼합 비중 1.0.  [기록](../../analysis_outputs/award_run/inner_selection.csv) |

## Autoresearch 다섯 차례 탐색

results.tsv의 51개 시도 행은 성공 기록 50개와 baseline 사전 검사 실패 1회이며, 같은 baseline ID의 실패와 성공을 합치지 않습니다. 성공 기록은 실제 모델 적합 40회와 무학습 재평가 10회이므로 별도 모델 50개를 뜻하지 않습니다. 최종 선택은 w5_lgb_calibrated이고, 기본 개발 W_pct는 12.695950, 후기 연간은 11.048843(award 기준 11.552586)입니다. 후보 생성 당시에는 미제출 상태였지만 이후 사용자가 6,447,820,797점을 보고했습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| baseline | historical_record | 실행 실패 | — | — | W_pct | — | 원본 표/로그 행 1 (재시도·다른 조건을 합치지 않음). Reproduce unchanged direct 50 percent baseline [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| baseline | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 13.2102 | 원본 표/로그 행 2 (재시도·다른 조건을 합치지 않음). Reproduce unchanged direct 50 percent baseline [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| scored | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.4109 | 원본 표/로그 행 3 (재시도·다른 조건을 합치지 않음). Capacity times SMP times k aligns CF loss with scored kWh [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| capacity | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.3233 | 원본 표/로그 행 4 (재시도·다른 조건을 합치지 않음). Capacity weighting aligns CF loss with group kWh [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| trees800 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.2636 | 원본 표/로그 행 5 (재시도·다른 조건을 합치지 않음). More boosting reduces underfit [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| leaves63 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.4495 | 원본 표/로그 행 6 (재시도·다른 조건을 합치지 않음). More trees and leaves capture weather interactions [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| lr02 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.2295 | 원본 표/로그 행 7 (재시도·다른 조건을 합치지 않음). Slower 800-tree boosting improves generalization [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| l2 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.5860 | 원본 표/로그 행 8 (재시도·다른 조건을 합치지 않음). L2 alternative may offer ensemble diversity [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| recent365 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.3025 | 원본 표/로그 행 9 (재시도·다른 조건을 합치지 않음). One-year half-life adapts to recent fleet and weather [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| recent730 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.2315 | 원본 표/로그 행 10 (재시도·다른 조건을 합치지 않음). Two-year half-life balances adaptation and history [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_baseline | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.2544 | 원본 표/로그 행 11 (재시도·다른 조건을 합치지 않음). Second-wave one-factor w2_baseline [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_baseline_default | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.2102 | 원본 표/로그 행 12 (재시도·다른 조건을 합치지 않음). Reproduce original default seed after seed-zero explicit-vs-default check [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_child100 | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 13.2021 | 원본 표/로그 행 13 (재시도·다른 조건을 합치지 않음). Second-wave one-factor w2_child100 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_child200 | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 13.1849 | 원본 표/로그 행 14 (재시도·다른 조건을 합치지 않음). Second-wave one-factor w2_child200 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_leaves15 | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 13.1052 | 원본 표/로그 행 15 (재시도·다른 조건을 합치지 않음). Second-wave one-factor w2_leaves15 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_lr02 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.2039 | 원본 표/로그 행 16 (재시도·다른 조건을 합치지 않음). Second-wave one-factor w2_lr02 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_n200 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.2133 | 원본 표/로그 행 17 (재시도·다른 조건을 합치지 않음). Second-wave one-factor w2_n200 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_n300 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.1957 | 원본 표/로그 행 18 (재시도·다른 조건을 합치지 않음). Second-wave one-factor w2_n300 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_ramps | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 13.0593 | 원본 표/로그 행 19 (재시도·다른 조건을 합치지 않음). Second-wave one-factor w2_ramps [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_seeds012 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.1993 | 원본 표/로그 행 20 (재시도·다른 조건을 합치지 않음). Second-wave one-factor w2_seeds012 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_leaf15_child100 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.1210 | 원본 표/로그 행 21 (재시도·다른 조건을 합치지 않음). Combine measured promising smaller leaves with w2_leaf15_child100 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_leaf15_seeds | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.1047 | 원본 표/로그 행 22 (재시도·다른 조건을 합치지 않음). Combine measured promising smaller leaves with w2_leaf15_seeds [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_leaf15_ramps | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 13.0075 | 원본 표/로그 행 23 (재시도·다른 조건을 합치지 않음). Combine measured promising smaller leaves with w2_leaf15_ramps [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_blend4 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.0579 | 원본 표/로그 행 24 (재시도·다른 조건을 합치지 않음). Blend-only rescore best measured direct model at 0.4 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w2_blend6 | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 12.9937 | 원본 표/로그 행 25 (재시도·다른 조건을 합치지 않음). Blend-only rescore best measured direct model at 0.6 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_baseline | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.9937 | 원본 표/로그 행 26 (재시도·다른 조건을 합치지 않음). Third-wave one-factor w3_baseline [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_daily | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 12.8804 | 원본 표/로그 행 27 (재시도·다른 조건을 합치지 않음). Third-wave one-factor w3_daily [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_lead | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.9474 | 원본 표/로그 행 28 (재시도·다른 조건을 합치지 않음). Third-wave one-factor w3_lead [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_leaves7 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.1593 | 원본 표/로그 행 29 (재시도·다른 조건을 합치지 않음). Third-wave one-factor w3_leaves7 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_n600 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.9903 | 원본 표/로그 행 30 (재시도·다른 조건을 합치지 않음). Third-wave one-factor w3_n600 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_seeds | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.9884 | 원본 표/로그 행 31 (재시도·다른 조건을 합치지 않음). Third-wave one-factor w3_seeds [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_daily_lead | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 12.8490 | 원본 표/로그 행 32 (재시도·다른 조건을 합치지 않음). Both daylight summaries and next-hour issued forecasts improved parent; test complementary context [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_context_seeds | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 12.7950 | 원본 표/로그 행 33 (재시도·다른 조건을 합치지 않음). Seed ensemble marginally improved parent; test variance reduction with best measured context [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_blend5 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.8312 | 원본 표/로그 행 34 (재시도·다른 조건을 합치지 않음). Blend-only rescore of best measured context model [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w3_blend7 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.7996 | 원본 표/로그 행 35 (재시도·다른 조건을 합치지 않음). Blend-only rescore of best measured context model [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w4_baseline | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.7950 | 원본 표/로그 행 36 (재시도·다른 조건을 합치지 않음). Fourth-wave one-factor w4_baseline [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w4_spatial | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.8051 | 원본 표/로그 행 37 (재시도·다른 조건을 합치지 않음). Fourth-wave one-factor w4_spatial [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w4_pooled15 | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 12.7468 | 원본 표/로그 행 38 (재시도·다른 조건을 합치지 않음). Fourth-wave one-factor w4_pooled15 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w4_pooled31 | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 12.7219 | 원본 표/로그 행 39 (재시도·다른 조건을 합치지 않음). Fourth-wave one-factor w4_pooled31 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w4_pooled_spatial | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.7637 | 원본 표/로그 행 40 (재시도·다른 조건을 합치지 않음). Pooled groups improved; test whether spatial heterogeneity adds complementary group information [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w4_pooled_n600 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.7383 | 원본 표/로그 행 41 (재시도·다른 조건을 합치지 않음). One capacity check: pooled data may support more trees; n600 was marginally useful earlier [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w4_blend5 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.7841 | 원본 표/로그 행 42 (재시도·다른 조건을 합치지 않음). Blend-only refinement after measured pooled-group gain [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w4_blend7 | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 12.6964 | 원본 표/로그 행 43 (재시도·다른 조건을 합치지 않음). Blend-only refinement after measured pooled-group gain [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w5_baseline | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.6964 | 원본 표/로그 행 44 (재시도·다른 조건을 합치지 않음). Final distinct-learner family w5_baseline [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w5_hist31 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.8837 | 원본 표/로그 행 45 (재시도·다른 조건을 합치지 않음). Final distinct-learner family w5_hist31 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w5_hist15 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.7963 | 원본 표/로그 행 46 (재시도·다른 조건을 합치지 않음). Final distinct-learner family w5_hist15 [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w5_original_calibrated | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 13.2100 | 원본 표/로그 행 47 (재시도·다른 조건을 합치지 않음). Analytical weighted-median single blend coefficient fitted only on inner selection; no model fit [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w5_lgb_calibrated | historical_record | 당시 탐색에서 유지 | — | — | W_pct | 12.6960 | 원본 표/로그 행 48 (재시도·다른 조건을 합치지 않음). Analytical weighted-median single blend coefficient fitted only on inner selection; no model fit [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w5_hist15_calibrated | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.7870 | 원본 표/로그 행 49 (재시도·다른 조건을 합치지 않음). Analytical weighted-median single blend coefficient fitted only on inner selection; no model fit [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w5_hist15_n600 | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.8214 | 원본 표/로그 행 50 (재시도·다른 조건을 합치지 않음). Single bounded neighbor: 15 leaves improved HGB markedly versus31; test whether more rounds recover remaining underfit [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |
| w5_hist15_n600_calibrated | historical_record | 당시 탐색에서 제외 | — | — | W_pct | 12.8124 | 원본 표/로그 행 51 (재시도·다른 조건을 합치지 않음). Analytical weighted-median single blend coefficient fitted only on inner selection; no model fit [기록](../../analysis_outputs/autoresearch_20261103/results.tsv) |

## 예보 변수 확장·물리 특성 탐색

17시 예보 확장, 10시 예보와의 변화량, 물리 특성 및 시간에 따른 변화 양상을 비교해 combined_physics를 선택했습니다. 표에는 요약 파일에 기록된 비교 행만 담았으며, 각 단계의 기준 예측이 다르므로 다른 실험군과 수치만으로 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| combined_physics | historical_record | 고정 혼합 계수 비교 | — | — | primary W_pct | 12.6250 | 혼합 계수를 고정한 입력 특성 비교 결과이며, 최종 모델 선택과는 구분합니다. [기록](../../analysis_outputs/score_push_20261104/ranking.json) |
| combined | historical_record | 고정 혼합 계수 비교 | — | — | primary W_pct | 12.6374 | 혼합 계수를 고정한 입력 특성 비교 결과이며, 최종 모델 선택과는 구분합니다. [기록](../../analysis_outputs/score_push_20261104/ranking.json) |
| expanded17 | historical_record | 고정 혼합 계수 비교 | — | — | primary W_pct | 12.6482 | 혼합 계수를 고정한 입력 특성 비교 결과이며, 최종 모델 선택과는 구분합니다. [기록](../../analysis_outputs/score_push_20261104/ranking.json) |
| combined_trajectory | historical_record | 고정 혼합 계수 비교 | — | — | primary W_pct | 12.6664 | 혼합 계수를 고정한 입력 특성 비교 결과이며, 최종 모델 선택과는 구분합니다. [기록](../../analysis_outputs/score_push_20261104/ranking.json) |
| bothround_core | historical_record | 고정 혼합 계수 비교 | — | — | primary W_pct | 12.6939 | 혼합 계수를 고정한 입력 특성 비교 결과이며, 최종 모델 선택과는 구분합니다. [기록](../../analysis_outputs/score_push_20261104/ranking.json) |
| baseline_exact | historical_record | 고정 혼합 계수 비교 | — | — | primary W_pct | 12.6960 | 혼합 계수를 고정한 입력 특성 비교 결과이며, 최종 모델 선택과는 구분합니다. [기록](../../analysis_outputs/score_push_20261104/ranking.json) |
| capacity63_600 | historical_record | 고정 혼합 계수 비교 | — | — | primary W_pct | 12.7053 | 혼합 계수를 고정한 입력 특성 비교 결과이며, 최종 모델 선택과는 구분합니다. [기록](../../analysis_outputs/score_push_20261104/ranking.json) |

## 정규화 LightGBM·신경망·커널 모델 비교

물리 정규화를 적용한 LightGBM, 설비용량 대비 발전 비율(CF) 또는 정규화된 값을 예측하는 신경망, L1 커널 모델이 기존 예측을 보완하는지 비교했습니다. 표는 이 단계에 기록된 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| mlp_cf | historical_record | 두 개발 기간 개선 | — | — | primary W_pct (lower better; internal) | 12.3219 | 단계=ensemble(시드 평균); 혼합 기준=richer_reference; 기준 예측열=p_reference; 기본 개발 W_pct=12.321941; 최근 개발 W_pct=11.317672; 기본 개발 기간에서 정한 혼합비(alpha)=0.243688 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |
| lgb_normalized | historical_record | 두 개발 기간 개선 | — | — | primary W_pct (lower better; internal) | 12.3573 | 단계=screen(1차 비교); 혼합 기준=richer_reference; 기준 예측열=p_reference; 기본 개발 W_pct=12.357347; 최근 개발 W_pct=11.378860; 기본 개발 기간에서 정한 혼합비(alpha)=0.524180 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |
| mlp_cf | historical_record | 두 개발 기간 개선 | — | — | primary W_pct (lower better; internal) | 12.3810 | 단계=screen(1차 비교); 혼합 기준=richer_reference; 기준 예측열=p_reference; 기본 개발 W_pct=12.380962; 최근 개발 W_pct=11.478764; 기본 개발 기간에서 정한 혼합비(alpha)=0.205419 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |
| mlp_normalized | historical_record | 두 개발 기간 개선 | — | — | primary W_pct (lower better; internal) | 12.4832 | 단계=screen(1차 비교); 혼합 기준=richer_reference; 기준 예측열=p_reference; 기본 개발 W_pct=12.483239; 최근 개발 W_pct=11.428834; 기본 개발 기간에서 정한 혼합비(alpha)=0.176650 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |
| kernel_l1 | historical_record | 두 개발 기간 개선 | — | — | primary W_pct (lower better; internal) | 12.5428 | 단계=screen(1차 비교); 혼합 기준=richer_reference; 기준 예측열=p_reference; 기본 개발 W_pct=12.542757; 최근 개발 W_pct=11.484403; 기본 개발 기간에서 정한 혼합비(alpha)=0.122572 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |
| lgb_normalized | historical_record | 두 기간 동시 개선 아님 | — | — | primary W_pct (lower better; internal) | 12.5254 | 단계=screen(1차 비교); 혼합 기준=old_bottom_up; 기준 예측열=p_bu_old; 기본 개발 W_pct=12.525412; 최근 개발 W_pct=11.562568; 기본 개발 기간에서 정한 혼합비(alpha)=0.811187 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |
| mlp_cf | historical_record | 두 기간 동시 개선 아님 | — | — | primary W_pct (lower better; internal) | 12.9245 | 단계=ensemble(시드 평균); 혼합 기준=old_bottom_up; 기준 예측열=p_bu_old; 기본 개발 W_pct=12.924519; 최근 개발 W_pct=11.935300; 기본 개발 기간에서 정한 혼합비(alpha)=0.395510 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |
| mlp_cf | historical_record | 두 기간 동시 개선 아님 | — | — | primary W_pct (lower better; internal) | 13.0256 | 단계=screen(1차 비교); 혼합 기준=old_bottom_up; 기준 예측열=p_bu_old; 기본 개발 W_pct=13.025560; 최근 개발 W_pct=12.274438; 기본 개발 기간에서 정한 혼합비(alpha)=0.321470 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |
| mlp_normalized | historical_record | 두 기간 동시 개선 아님 | — | — | primary W_pct (lower better; internal) | 13.1983 | 단계=screen(1차 비교); 혼합 기준=old_bottom_up; 기준 예측열=p_bu_old; 기본 개발 W_pct=13.198281; 최근 개발 W_pct=12.215356; 기본 개발 기간에서 정한 혼합비(alpha)=0.300956 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |
| kernel_l1 | historical_record | 두 기간 동시 개선 아님 | — | — | primary W_pct (lower better; internal) | 13.2403 | 단계=screen(1차 비교); 혼합 기준=old_bottom_up; 기준 예측열=p_bu_old; 기본 개발 W_pct=13.240267; 최근 개발 W_pct=12.361865; 기본 개발 기간에서 정한 혼합비(alpha)=0.282885 [기록](../../analysis_outputs/score_push_20261104/learner_wave/results.json) |

## 기상 관측소·공간 격자별 입력 비교

공간 격자와 기상 관측소별 예보를 LightGBM·MLP에 입력해 비교하고, 관측소 LightGBM인 stations_lgb를 선택했습니다. 표에는 해당 단계의 비교 행만 담았으며, 기준 예측이 다른 실험군과 수치만으로 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| cells_lgb | historical_record | 두 개발 기간 개선 | — | — | primary W_pct (lower better; internal) | 12.1143 | 단계=screen(1차 비교); 기본 개발 W_pct=12.114264; 최근 개발 W_pct=11.178757; 기본 개발 기간에서 정한 혼합비(alpha)=0.274999 [기록](../../analysis_outputs/score_push_20261104/profile_wave/results.json) |
| cells_mlp | historical_record | 두 개발 기간 개선 | — | — | primary W_pct (lower better; internal) | 12.1221 | 단계=screen(1차 비교); 기본 개발 W_pct=12.122070; 최근 개발 W_pct=11.183734; 기본 개발 기간에서 정한 혼합비(alpha)=0.071150 [기록](../../analysis_outputs/score_push_20261104/profile_wave/results.json) |
| stations_lgb | historical_record | 두 개발 기간 개선 | — | — | primary W_pct (lower better; internal) | 12.0581 | 단계=screen(1차 비교); 기본 개발 W_pct=12.058063; 최근 개발 W_pct=11.090472; 기본 개발 기간에서 정한 혼합비(alpha)=0.256838 [기록](../../analysis_outputs/score_push_20261104/profile_wave/results.json) |
| stations_mlp | historical_record | 두 기간 동시 개선 아님 | — | — | primary W_pct (lower better; internal) | 12.1081 | 단계=screen(1차 비교); 기본 개발 W_pct=12.108093; 최근 개발 W_pct=11.210210; 기본 개발 기간에서 정한 혼합비(alpha)=0.047556 [기록](../../analysis_outputs/score_push_20261104/profile_wave/results.json) |
| stations_lgb | historical_record | 두 개발 기간 개선 | — | — | primary W_pct (lower better; internal) | 12.0416 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.041604; 최근 개발 W_pct=11.064367; 기본 개발 기간에서 정한 혼합비(alpha)=0.280847 [기록](../../analysis_outputs/score_push_20261104/profile_wave/results.json) |

## 모델 복잡도·시드·혼합 정제

모델 복잡도, 추가 시드, 여러 예측의 혼합을 비교한 최종 선택은 leaves63_trees400_ensemble입니다. 최초 results.json의 5개 모델 혼합 선택보다 clarified_results.json·chosen_recipe.json과 final/freeze.json을 우선하며, 탐색 중 선택 규칙을 명확히 한 이력을 보존합니다. 표는 이 단계의 비교 기록으로, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| three_default_mlp3 | historical_record | 비교 기록 | — | — | primary W_pct (lower better; internal) | 12.1593 | 기본 개발 W_pct=12.159323; 최근 개발 W_pct=11.222655 [기록](../../analysis_outputs/score_push_20261104/refinement_wave/clarified_results.json) |
| five_default_mlp3 | historical_record | 비교 기록 | — | — | primary W_pct (lower better; internal) | 12.1574 | 기본 개발 W_pct=12.157431; 최근 개발 W_pct=11.215643 [기록](../../analysis_outputs/score_push_20261104/refinement_wave/clarified_results.json) |
| three_default_mlp5 | historical_record | 비교 기록 | — | — | primary W_pct (lower better; internal) | 12.1961 | 기본 개발 W_pct=12.196127; 최근 개발 W_pct=11.255751 [기록](../../analysis_outputs/score_push_20261104/refinement_wave/clarified_results.json) |
| leaves15_trees400_screen | historical_record | 비교 기록 | — | — | primary W_pct (lower better; internal) | 12.1354 | 기본 개발 W_pct=12.135388; 최근 개발 W_pct=11.216609 [기록](../../analysis_outputs/score_push_20261104/refinement_wave/clarified_results.json) |
| leaves63_trees400_screen | historical_record | 비교 기록 | — | — | primary W_pct (lower better; internal) | 12.1354 | 기본 개발 W_pct=12.135414; 최근 개발 W_pct=11.211930 [기록](../../analysis_outputs/score_push_20261104/refinement_wave/clarified_results.json) |
| leaves31_trees800_screen | historical_record | 비교 기록 | — | — | primary W_pct (lower better; internal) | 12.1830 | 기본 개발 W_pct=12.183023; 최근 개발 W_pct=11.264612 [기록](../../analysis_outputs/score_push_20261104/refinement_wave/clarified_results.json) |
| leaves63_trees400_ensemble | historical_record | 비교 기록 | — | — | primary W_pct (lower better; internal) | 12.1620 | 기본 개발 W_pct=12.161988; 최근 개발 W_pct=11.187338 [기록](../../analysis_outputs/score_push_20261104/refinement_wave/clarified_results.json) |

## 발전소별 모델과 물리 정규화 비교

발전소별 입력과 물리 정규화 목표값을 비교했지만, 선택된 재혼합의 기본 개발 W_pct가 12.698487로 기존 기준 12.695950보다 나빠 최종 CPU 후보에 채택하지 않았습니다. 표의 행은 이 단계에서 기록한 모델·기준 예측 조합이며, 다른 실험군의 수치와 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| normalized_l1+rich | historical_record | 고정 혼합 계수 비교 | — | — | paired mean relative loss | 1.0012 | 두 개발 기간의 평균 상대 오차는 1.001241684입니다. 이 행은 발전소별 모델과 그룹 직접 예측의 조합 비교입니다. [기록](../../analysis_outputs/score_push_20261104/site_wave/results.json) |
| identity_l1+rich | historical_record | 고정 혼합 계수 비교 | — | — | paired mean relative loss | 1.0021 | 두 개발 기간의 평균 상대 오차는 1.002109152입니다. 이 행은 발전소별 모델과 그룹 직접 예측의 조합 비교입니다. [기록](../../analysis_outputs/score_push_20261104/site_wave/results.json) |
| identity_l2+rich | historical_record | 고정 혼합 계수 비교 | — | — | paired mean relative loss | 1.0052 | 두 개발 기간의 평균 상대 오차는 1.005249807입니다. 이 행은 발전소별 모델과 그룹 직접 예측의 조합 비교입니다. [기록](../../analysis_outputs/score_push_20261104/site_wave/results.json) |
| normalized_l1+incumbent | historical_record | 고정 혼합 계수 비교 | — | — | paired mean relative loss | 1.0092 | 두 개발 기간의 평균 상대 오차는 1.009242127입니다. 이 행은 발전소별 모델과 그룹 직접 예측의 조합 비교입니다. [기록](../../analysis_outputs/score_push_20261104/site_wave/results.json) |
| identity_l1+incumbent | historical_record | 고정 혼합 계수 비교 | — | — | paired mean relative loss | 1.0094 | 두 개발 기간의 평균 상대 오차는 1.009359116입니다. 이 행은 발전소별 모델과 그룹 직접 예측의 조합 비교입니다. [기록](../../analysis_outputs/score_push_20261104/site_wave/results.json) |
| identity_l2+incumbent | historical_record | 고정 혼합 계수 비교 | — | — | paired mean relative loss | 1.0134 | 두 개발 기간의 평균 상대 오차는 1.013417659입니다. 이 행은 발전소별 모델과 그룹 직접 예측의 조합 비교입니다. [기록](../../analysis_outputs/score_push_20261104/site_wave/results.json) |

## 기존 공간 격자 모델 추가 혼합

추가 모델 학습 0회로 기존 공간 격자 모델을 관측소 앙상블에 혼합했지만, 최근 개발 기간이 악화돼 거부했습니다. 표는 해당 단계에 기록된 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| cell_addition_no_fit | historical_record | 최근 기간 악화로 제외 | — | — |  | — | 기존 공간 격자 모델을 새 학습 없이 추가 혼합했지만 채택하지 않고 station_complete를 유지했습니다. [기록](../../analysis_outputs/score_push_20261104/closing_wave/results.json) |

## 최근 데이터 가중치와 학습 창 비교

180·365·730일 반감기 가중치와 최근 365일 학습 창을 비교하며 모델 24개를 적합했고, decay180을 선택했습니다. 표는 해당 단계의 기준 예측과 비교한 기록이므로, 다른 실험군의 수치와 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| decay180 | historical_record | 개발 기준 통과 | — | — | primary W_pct (lower better; internal) | 12.0332 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.033226; 최근 개발 W_pct=11.059225; 기본 개발 기간에서 정한 혼합비(alpha)=0.077949 [기록](../../analysis_outputs/renew_20261105/recency_wave/results.json) |
| decay365 | historical_record | 개발 기준 통과 | — | — | primary W_pct (lower better; internal) | 12.0409 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.040889; 최근 개발 W_pct=11.056701; 기본 개발 기간에서 정한 혼합비(alpha)=0.026961 [기록](../../analysis_outputs/renew_20261105/recency_wave/results.json) |
| decay730 | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0416 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.041586; 최근 개발 W_pct=11.063084; 기본 개발 기간에서 정한 혼합비(alpha)=0.005786 [기록](../../analysis_outputs/renew_20261105/recency_wave/results.json) |
| window365 | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.9924 | 단계=ensemble(시드 평균); 기본 개발 W_pct=11.992404; 최근 개발 W_pct=11.134984; 기본 개발 기간에서 정한 혼합비(alpha)=0.106463 [기록](../../analysis_outputs/renew_20261105/recency_wave/results.json) |

## 구름 예측을 보조 특성으로 추가

구름 예측과 예보 분포의 평균·공간 정보를 보조 입력으로 추가하며, 보조 모델 14개와 발전량 모델 12개를 적합했습니다. 표에는 기록된 비교 결과만 담았으며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| means | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0304 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.030441; 최근 개발 W_pct=11.066725; 기본 개발 기간에서 정한 혼합비(alpha)=0.043785 [기록](../../analysis_outputs/renew_20261105/cloud_wave/results.json) |
| profiles | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0309 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.030940; 최근 개발 W_pct=11.069780; 기본 개발 기간에서 정한 혼합비(alpha)=0.039184 [기록](../../analysis_outputs/renew_20261105/cloud_wave/results.json) |

## 그룹 오차를 반영한 모델 비교

그룹 단위 오차를 반영한 신경망과 발전소 단위 대조 모델을 비교하며 모델 18개를 적합했습니다. 표는 해당 단계에 기록된 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| group_l01 | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0332 | 기본 개발 W_pct=12.033226; 최근 개발 W_pct=11.059225; 기본 개발 기간에서 정한 혼합비(alpha)=0.000000 [기록](../../analysis_outputs/renew_20261105/group_wave/results.json) |
| group_l1 | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0332 | 기본 개발 W_pct=12.033226; 최근 개발 W_pct=11.059225; 기본 개발 기간에서 정한 혼합비(alpha)=0.000000 [기록](../../analysis_outputs/renew_20261105/group_wave/results.json) |
| site_control | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0332 | 기본 개발 W_pct=12.033226; 최근 개발 W_pct=11.059225; 기본 개발 기간에서 정한 혼합비(alpha)=0.000000 [기록](../../analysis_outputs/renew_20261105/group_wave/results.json) |

## 전체 발전량 예측 후 그룹 배분

전체 발전량을 먼저 예측한 뒤 고정된 그룹에 배분하는 방법으로 모델 12개를 적합했습니다. 표에는 해당 단계의 비교 결과만 담았으며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| total_rich | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0242 | 기본 개발 W_pct=12.024160; 최근 개발 W_pct=11.075880; 기본 개발 기간에서 정한 혼합비(alpha)=0.106190 [기록](../../analysis_outputs/renew_20261105/total_wave/results.json) |
| total_station | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0181 | 기본 개발 W_pct=12.018104; 최근 개발 W_pct=11.110085; 기본 개발 기간에서 정한 혼합비(alpha)=0.073052 [기록](../../analysis_outputs/renew_20261105/total_wave/results.json) |

## 온도·눈 조건별 편향 보정

기본 개발 기간에서 온도·눈 조건별 보정 계수를 구하고 보정 범위를 제한하는 후보 3개를 비교했으며, 새 트리 학습은 0회이고 선택은 temperature_then_snow입니다. 표는 해당 단계의 기준 예측과 비교한 결과이므로, 다른 실험군의 수치와 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| snow_only | historical_record | 개발 기준 통과 | — | — | primary W_pct (lower better; internal) | 12.0102 | 기본 개발 W_pct=12.010182; 최근 개발 W_pct=11.038762 [기록](../../analysis_outputs/renew_20261105/calibration_wave/results.json) |
| temperature_only | historical_record | 개발 기준 통과 | — | — | primary W_pct (lower better; internal) | 11.9689 | 기본 개발 W_pct=11.968930; 최근 개발 W_pct=11.010944 [기록](../../analysis_outputs/renew_20261105/calibration_wave/results.json) |
| temperature_then_snow | historical_record | 개발 기준 통과 | — | — | primary W_pct (lower better; internal) | 11.9592 | 기본 개발 W_pct=11.959229; 최근 개발 W_pct=11.000953 [기록](../../analysis_outputs/renew_20261105/calibration_wave/results.json) |

## 피크·금액 기준 손실 가중치 비교

피크 시간 가중치 k와 금액 기준 손실 가중치를 비교하며 모델 12개를 적합했습니다. 표는 이 단계에 기록된 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| peak_k | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.9560 | 기본 개발 W_pct=11.956016; 최근 개발 W_pct=11.022002; 기본 개발 기간에서 정한 혼합비(alpha)=0.041249 [기록](../../analysis_outputs/renew_20261105/weight_wave/results.json) |
| scored | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.9459 | 기본 개발 W_pct=11.945918; 최근 개발 W_pct=11.059273; 기본 개발 기간에서 정한 혼합비(alpha)=0.060576 [기록](../../analysis_outputs/renew_20261105/weight_wave/results.json) |

## 발전소별 수율 차이 정규화

학습 자료만으로 발전소별 수율 차이를 정규화하며 발전량 모델 6개와 발전소 수율 계수 2세트를 적합했습니다. 표에는 해당 단계의 비교 결과만 담았으며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| site_yield | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.9466 | 기본 개발 W_pct=11.946590; 최근 개발 W_pct=11.038143; 기본 개발 기간에서 정한 혼합비(alpha)=0.100551 [기록](../../analysis_outputs/renew_20261105/yield_wave/results.json) |

## 시간대별 편향 보정

시간대별 보정 범위를 제한한 후보 1개에 대해 스칼라 계수 5개를 적합하고 hour_bias를 선택했으며, 새 트리 학습은 0회입니다. 표는 해당 단계의 기준 예측과 비교한 결과이므로, 다른 실험군의 수치와 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| hour_bias | historical_record | 개발 기준 통과 | — | — | primary W_pct (lower better; internal) | 11.9126 | 기본 개발 W_pct=11.912571; 최근 개발 W_pct=10.998535 [기록](../../analysis_outputs/renew_20261105/hour_wave/results.json) |

## 구름량 구간별 편향 보정

시간대 보정을 마친 예측에 구름량 구간별 보정을 추가한 후보 1개를 비교해 cloud_bias를 선택했으며, 스칼라 계수 적합은 4회이고 새 트리 학습은 0회입니다. 표는 해당 단계의 기준 예측과 비교한 결과이므로, 다른 실험군의 수치와 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| cloud_bias | historical_record | 개발 기준 통과 | — | — | primary W_pct (lower better; internal) | 11.7928 | 기본 개발 W_pct=11.792837; 최근 개발 W_pct=10.955416 [기록](../../analysis_outputs/renew_20261105/sky_wave/results.json) |

## 시간 순서를 지킨 보정 계수 갱신

시간 순서를 지키며 기상·시간대·구름 보정 계수를 갱신한 후보 1개를 비교했고, 스칼라 계수 적합은 32회이며 새 트리 학습은 0회입니다. 표는 해당 단계의 기준 예측과 비교한 결과이므로, 다른 실험군의 수치와 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| chronological_refresh | historical_record | 개발 기준 미통과 | — | — |  | — | 후기 최근 기간(late_recent)의 W_pct는 9.485826으로 고정 기상 보정 기준 9.408122보다 높고, 최신 기간(latest)도 9.420960으로 기준 9.390467보다 높았습니다. 스칼라 계수 32개를 적합하고 트리 학습은 0회 수행했으며, 갱신된 보정은 채택하지 않았습니다. [기록](../../analysis_outputs/renew_20261105/refresh_wave/results.json) |

## 관측소 신경망에 물리·시간 정규화 적용

물리 정규화와 시간 가중치를 적용한 관측소 MLP 후보 1개를 모델 6개로 검증했으며, 추가 보정 계수 적합은 0회입니다. 표는 해당 단계의 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| station_mlp_normalized_decay180 | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.7772 | 기본 개발 W_pct=11.777166; 최근 개발 W_pct=10.982662; 기본 개발 기간에서 정한 혼합비(alpha)=0.021664 [기록](../../analysis_outputs/renew_20261105/mlp_wave/results.json) |

## 관측소 신경망 입력을 학습 범위로 제한

기존 관측소 MLP의 입력을 학습 범위로 제한한 후보 1개를 검증했으며, 모델 추론 6회와 범위 제한 변환 2회를 수행하고 새 모델 학습 및 보정 계수 적합은 각각 0회였습니다. 표는 해당 단계의 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| station_mlp_train_range | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.7687 | 기본 개발 W_pct=11.768679; 최근 개발 W_pct=11.062367; 기본 개발 기간에서 정한 혼합비(alpha)=0.052955 [기록](../../analysis_outputs/renew_20261105/bounds_wave/results.json) |

## 단조 제약 부스팅과 동일 손실 대조 모델

동일한 fair 손실을 사용하는 대조 모델과 단조 제약 관측소 부스팅 후보 2개를 모델 12개로 비교했으며, 추가 보정 계수 적합은 0회입니다. 표는 해당 단계의 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| fair_control | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.7885 | 기본 개발 W_pct=11.788477; 최근 개발 W_pct=10.979584; 기본 개발 기간에서 정한 혼합비(alpha)=0.067177 [기록](../../analysis_outputs/renew_20261105/mono_wave/results.json) |
| fair_monotone | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.7848 | 기본 개발 W_pct=11.784847; 최근 개발 W_pct=10.988034; 기본 개발 기간에서 정한 혼합비(alpha)=0.093063 [기록](../../analysis_outputs/renew_20261105/mono_wave/results.json) |

## 기존 신경망 입력 범위 제한

기존 rich MLP의 혼합 가중치를 고정하고 입력을 학습 범위로 제한한 후보 1개를 비교했으며, 새 모델 학습·보정 계수 적합·혼합비(alpha) 적합은 모두 0회였습니다. 표는 해당 단계의 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| incumbent_rich_mlp_train_range | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.7917 | 기본 개발 W_pct=11.791707; 최근 개발 W_pct=10.955423 [기록](../../analysis_outputs/renew_20261105/incbound_wave/results.json) |

## ExtraTrees 모델의 보완 효과 검증

확장 기상 입력과 물리 정규화를 사용하는 ExtraTrees 앙상블 후보 1개를 모델 6개로 검증했으며, 추가 보정 계수 적합은 0회입니다. 표는 해당 단계의 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| extratrees_normalized_rich_decay180 | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.9581 | 기본 개발 W_pct=11.958096; 최근 개발 W_pct=11.006260; 기본 개발 기간에서 정한 혼합비(alpha)=0.025608 [기록](../../analysis_outputs/renew_20261105/extra_wave/results.json) |

## Poisson 로그 연결 부스팅

Poisson 손실과 로그 연결을 사용하는 관측소 부스팅 후보 1개를 모델 6개로 검증했으며, 추가 보정 계수 적합은 0회입니다. 표는 해당 단계의 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| poisson_normalized_station_decay180 | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.9592 | 기본 개발 W_pct=11.959229; 최근 개발 W_pct=11.000953; 기본 개발 기간에서 정한 혼합비(alpha)=0.000000 [기록](../../analysis_outputs/renew_20261106/poisson_wave/results.json) |

## 태양 고도를 보정한 3시간 예측 평활화

맑은 하늘의 태양 고도로 정규화한 예측을 3시간 단위로 평활화하는 후보 1개를 비교했으며, 새 모델 학습과 보정 계수 적합은 각각 0회이고 혼합비(alpha)만 1회 적합했습니다. 표는 해당 단계의 비교 결과이며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| normalized_temporal_smoothing | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.9509 | 기본 개발 W_pct=11.950907; 최근 개발 W_pct=11.010421; 기본 개발 기간에서 정한 혼합비(alpha)=0.380199 [기록](../../analysis_outputs/renew_20261106/smooth_wave/results.json) |

## CatBoost GPU 초기 비교

CatBoost GPU 후보를 1차 비교하고 여러 시드에서의 안정성을 확인하며 모델 8개를 적합했습니다. 표에는 실제 기록된 단계별 비교만 담았으며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| rich_cf | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0375 | 단계=screen(1차 비교); 기본 개발 W_pct=12.037505; 최근 개발 W_pct=11.069621; 기본 개발 기간에서 정한 혼합비(alpha)=0.062314 [기록](../../analysis_outputs/score_push_gpu_20261104/results.json) |
| station_normalized | historical_record | 개발 기준 통과 | — | — | primary W_pct (lower better; internal) | 12.0119 | 단계=screen(1차 비교); 기본 개발 W_pct=12.011915; 최근 개발 W_pct=11.055529; 기본 개발 기간에서 정한 혼합비(alpha)=0.160744 [기록](../../analysis_outputs/score_push_gpu_20261104/results.json) |
| station_normalized | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0104 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.010373; 최근 개발 W_pct=11.067682; 기본 개발 기간에서 정한 혼합비(alpha)=0.187019 [기록](../../analysis_outputs/score_push_gpu_20261104/results.json) |

## CatBoost GPU 네 가지 정제

얕은 모델·깊은 모델·긴 학습·금액 가중치라는 네 가지 고정 CatBoost GPU 가설을 모델 24개로 비교했습니다. 표에는 실제 기록된 비교 행만 담았으며, 기준 예측이 다른 실험군과 직접 순위를 매기지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| shallow | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 11.9909 | 단계=ensemble(시드 평균); 기본 개발 W_pct=11.990907; 최근 개발 W_pct=11.117183; 기본 개발 기간에서 정한 혼합비(alpha)=0.226076 [기록](../../analysis_outputs/score_push_gpu_refine_20261105/results.json) |
| deep | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0024 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.002405; 최근 개발 W_pct=11.090419; 기본 개발 기간에서 정한 혼합비(alpha)=0.234670 [기록](../../analysis_outputs/score_push_gpu_refine_20261105/results.json) |
| longer | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0181 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.018120; 최근 개발 W_pct=11.069844; 기본 개발 기간에서 정한 혼합비(alpha)=0.153113 [기록](../../analysis_outputs/score_push_gpu_refine_20261105/results.json) |
| monetary | historical_record | 개발 기준 미통과 | — | — | primary W_pct (lower better; internal) | 12.0152 | 단계=ensemble(시드 평균); 기본 개발 W_pct=12.015155; 최근 개발 W_pct=11.163519; 기본 개발 기간에서 정한 혼합비(alpha)=0.116792 [기록](../../analysis_outputs/score_push_gpu_refine_20261105/results.json) |

## CPU 최종 후보·학습 종료일 진단

최종 재학습은 그룹 모델 12개이며, 학습 종료일 진단은 모델 272개로 기존 269개를 보존하고 미완료 3개만 재개했습니다. 이 수를 새로운 가설 수와 구분하고, autoresearch와 동일한 발전소 구성을 사용한 새 제출 파일 쌍은 별도 폴더에 보존했으며 공식 점수 기록은 없습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| cpu_final | historical_record | 후보 생성·검증, 기간별 성능 혼재 | — | — |  | — | 기본 개발 W_pct 12.041604, 최근 개발 11.064367로 개선됐고 후기 연간은 10.716156입니다. 다만 이전 학습 종료일 기준 3~5월은 9.848507로, 기준 9.576119보다 악화됐습니다. [기록](../../analysis_outputs/score_push_20261104/final/outer_metrics.json) |
| latest_cutoff_diagnostic | historical_record | 검증상 이점 없음 | — | — |  | — | 양쪽 모델을 2025-03-01까지 재학습해 같은 3~5월을 평가했을 때 새 모델은 9.446583, 기존 모델은 9.437775였습니다. 사후 진단이며 결과에 따라 다시 선택하지 않았습니다. [기록](../../analysis_outputs/score_push_20261104/deployment_check/independent_check.json) |

## 시간가중·기상·시간대·구름 보정 제출 후보

최고 공식 점수는 사용자 보고이며, 기상 보정만 적용한 renew가 현재 보존 기준입니다. hour·sky 후보의 더 좋은 개발 점수만으로 공식 성능 우위를 뜻하지는 않으며, 기상·시간대·구름 보정의 기본 개발 기간 자료는 계수 학습에도 일부 사용됐습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| renew_weather | historical_record | 사용자 보고 최고점 | — | — | user-reported official score | 6454220836.0000 | 180일 시간 가중치와 온도·눈 보정을 적용한 후보입니다. 기본 개발 W_pct는 11.959229, 최근 개발은 11.000953이며, 사용자가 6,454,220,836점을 보고했습니다. 후보: submission/renew_candidate_20261105. [기록](../../analysis_outputs/renew_20261105/official_feedback.json) |
| renew_hour | historical_record | 사용자 보고 점수 하락 | — | — | user-reported official score | 6453783187.0000 | 내부 기본 개발 W_pct는 11.912571, 최근 개발은 10.998535입니다. 사용자 보고 점수는 6,453,783,187로 기상 보정 기준보다 437,649 낮았습니다. 후보: submission/renew_hour_candidate_20261105. [기록](../../analysis_outputs/renew_20261105/official_feedback_hour_20261105.json) |
| renew_sky | historical_record | 후보 생성·검증, 당시 공식 점수 미확인 | — | — |  | — | 내부 기본 개발 W_pct는 11.792837, 최근 개발은 10.955416이며 공식 점수는 확인되지 않았습니다. 후보: submission/renew_sky_candidate_20261105. [기록](../../submission/renew_sky_candidate_20261105/manifest.json) |

## 분포 변화 가중치 사전 준비

이 폴더는 사전 준비 단계이며, 실행 결과는 11월 7일 Linux 후속 실험에 있습니다. 준비와 실행을 별도 모델 학습으로 중복 집계하지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| shift_preparation | historical_record | 준비 후 Linux에서 이어 실행 | — | — |  | — | 이 준비 폴더에서 학습 완료 횟수를 0회라고 단정하지 않고, 후속 shift_linux 결과로 실제 완료된 학습을 확인합니다. [기록](../../analysis_outputs/renew_20261106/shift_wave/protocol.json) |

## Linux 후속 여섯 가설

6개 가설 중 shift·PCA·DART는 최근 개발 기간이 악화돼 거부됐고, cloud_curve·cloud_solar_surface·weather_residual는 개발 기준을 통과해 후보 3개를 내보냈습니다. 다만 이미 공개된 최신 학습 종료일 기준 3~5월 오차는 각각 9.418260·9.417728·9.441703으로 기준 9.390467보다 높았습니다. 적합 수는 발전량 모델 18개, 분포 구분 모델 6개, PCA 2개, 보정 모델 6개, 혼합비(alpha) 3개로 구분하며, 새 후보는 모두 공식 미채점 상태이고 기존 공식 기준을 보존합니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| shift_linux | historical_record | 검증 기록 있음 | — | — | primary_W_pct | 11.9461 | 원본 표/로그 행 1 (재시도·다른 조건을 합치지 않음). 분포 변화 가중치 [기록](../../analysis_outputs/renew_20261107/results.csv) |
| pca_station | historical_record | 검증 기록 있음 | — | — | primary_W_pct | 11.9582 | 원본 표/로그 행 2 (재시도·다른 조건을 합치지 않음). 관측소 PCA 16성분 [기록](../../analysis_outputs/renew_20261107/results.csv) |
| dart_station | historical_record | 검증 기록 있음 | — | — | primary_W_pct | 11.9561 | 원본 표/로그 행 3 (재시도·다른 조건을 합치지 않음). DART 800트리 [기록](../../analysis_outputs/renew_20261107/results.csv) |
| cloud_curve | historical_record | 검증 기록 있음 | — | — | primary_W_pct | 11.8386 | 원본 표/로그 행 4 (재시도·다른 조건을 합치지 않음). 연속 구름량 보정 [기록](../../analysis_outputs/renew_20261107/results.csv) |
| cloud_solar_surface | historical_record | 검증 기록 있음 | — | — | primary_W_pct | 11.8478 | 원본 표/로그 행 5 (재시도·다른 조건을 합치지 않음). 구름량·태양 고도 보정 [기록](../../analysis_outputs/renew_20261107/results.csv) |
| weather_residual | historical_record | 검증 기록 있음 | — | — | primary_W_pct | 11.6949 | 원본 표/로그 행 6 (재시도·다른 조건을 합치지 않음). 기상 잔여 오차 보정 [기록](../../analysis_outputs/renew_20261107/results.csv) |

## 초기 모델·입력·앙상블 비교 E0~E7

원본 results_table.csv의 34개 비교 행을 순서대로 보존했습니다. 학습은 2022-06-01 01:00~2024-06-01 00:00 KST, 평가는 2024-06-01 01:00~2025-06-01 00:00 KST이며 당시의 고정 참조 발전소 구성을 사용하므로 이후 후보와 직접 순위를 매기지 않습니다. E5 보정은 별도 표에 있고, E3_r30은 실측 갱신을 요구하는 배포 불가 진단입니다. 후속 검증에서 확인된 기본 난수 설정과 선택 편향의 한계도 함께 보존합니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| E0_site_raw | historical_record | 미학습 발전소 진단 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 29.3478 | 원본 표/로그 행 1 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: per-site L2 600 trees. 고정 참조 구성의 연간 W_ref_pct=29.347803; E0_site 대비 오차 감소율=-80.194311%. 학습 이력이 없는 48개 발전소를 0으로 예측한 초기 진단이며, 신규 발전소 대체 예측을 적용한 E0_site와 구분합니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E0_site | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 16.2868 | 원본 표/로그 행 2 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: per-site L2 600 trees + pooled fallback for 48 unseen sites. 고정 참조 구성의 연간 W_ref_pct=16.286753; E0_site 대비 오차 감소율=0.000000%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E0_pool | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6610 | 원본 표/로그 행 3 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l2 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.660987; E0_site 대비 오차 감소율=22.262059%. 원래 실행은 명시적 seed=0이 아닌 LightGBM 기본 난수 설정입니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E1_l1 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.5214 | 원본 표/로그 행 4 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.521386; E0_site 대비 오차 감소율=23.119201%. 원래 실행은 명시적 seed=0이 아닌 LightGBM 기본 난수 설정입니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E1_l1w | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.4599 | 원본 표/로그 행 5 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.459947; E0_site 대비 오차 감소율=23.496434%. 원래 실행은 명시적 seed=0이 아닌 LightGBM 기본 난수 설정입니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E1_l2w | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.8324 | 원본 표/로그 행 6 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l2 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.832373; E0_site 대비 오차 감소율=21.209757%. 원래 실행은 명시적 seed=0이 아닌 LightGBM 기본 난수 설정입니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E2_r10 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 13.1061 | 원본 표/로그 행 7 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=13.106078; E0_site 대비 오차 감소율=19.529217%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E2_avg | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.5551 | 원본 표/로그 행 8 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: avg(E1_l1w, E2_r10). 고정 참조 구성의 연간 W_ref_pct=12.555137; E0_site 대비 오차 감소율=22.911971%. 저장된 모델 예측의 평균·혼합을 포함하며 별도 모델 한 개를 새로 학습했다는 뜻은 아닙니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E2_both | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.5123 | 원본 표/로그 행 9 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.512309; E0_site 대비 오차 감소율=23.174934%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_phys | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.7238 | 원본 표/로그 행 10 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.723761; E0_site 대비 오차 감소율=21.876629%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_phys_both | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6830 | 원본 표/로그 행 11 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.683040; E0_site 대비 오차 감소율=22.126656%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_site | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6804 | 원본 표/로그 행 12 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.680361; E0_site 대비 오차 감소율=22.143104%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_site_nolatlon | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6637 | 원본 표/로그 행 13 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.663746; E0_site 대비 오차 감소율=22.245119%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_r30 | historical_record | 실시간 관측 사용 진단·제출 불가 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.3635 | 원본 표/로그 행 14 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.363522; E0_site 대비 오차 감소율=24.088477%. 검증 기간의 실측을 갱신하는 이동 비율이 필요해, 연간 일괄 제출에 배포할 수 없는 진단입니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_r30f | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6311 | 원본 표/로그 행 15 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.631136; E0_site 대비 오차 감소율=22.445342%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_r365f | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6096 | 원본 표/로그 행 16 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.609570; E0_site 대비 오차 감소율=22.577754%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_site_r365f | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6247 | 원본 표/로그 행 17 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.624719; E0_site 대비 오차 감소율=22.484742%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_site_both | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.7059 | 원본 표/로그 행 18 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.705903; E0_site 대비 오차 감소율=21.986275%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_site_nophys | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6534 | 원본 표/로그 행 19 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.653412; E0_site 대비 오차 감소율=22.308570%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E3_r365f_nophys | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6011 | 원본 표/로그 행 20 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.601062; E0_site 대비 오차 감소율=22.629995%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E1_l1w_s2 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.4369 | 원본 표/로그 행 21 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.436864; E0_site 대비 오차 감소율=23.638160%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E1_l1w_s3 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.5533 | 원본 표/로그 행 22 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.553283; E0_site 대비 오차 감소율=22.923358%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E6_trees800 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.6675 | 원본 표/로그 행 23 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.667464; E0_site 대비 오차 감소율=22.222287%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E6_lr03_t800 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.4497 | 원본 표/로그 행 24 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.449727; E0_site 대비 오차 감소율=23.559182%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E6_leaves255 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.4576 | 원본 표/로그 행 25 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.457566; E0_site 대비 오차 감소율=23.511052%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E6_leaves63 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.5927 | 원본 표/로그 행 26 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: pooled l1 w 400 trees. 고정 참조 구성의 연간 W_ref_pct=12.592658; E0_site 대비 오차 감소율=22.681598%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E7_seed3 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.4286 | 원본 표/로그 행 27 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: ens:0.33*E1_l1w+0.33*E1_l1w_s2+0.33*E1_l1w_s3. 고정 참조 구성의 연간 W_ref_pct=12.428556; E0_site 대비 오차 감소율=23.689177%. 저장된 모델 예측의 평균·혼합을 포함하며 별도 모델 한 개를 새로 학습했다는 뜻은 아닙니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E7_mix | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.4069 | 원본 표/로그 행 28 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: ens:0.14*E1_l1w+0.14*E1_l1w_s2+0.14*E1_l1w_s3+0.14*E2_both+0.14*E3_site_nophys+0.14*E3_r365f_nophys+0.14*E3_phys. 고정 참조 구성의 연간 W_ref_pct=12.406942; E0_site 대비 오차 감소율=23.821884%. 저장된 모델 예측의 평균·혼합을 포함하며 별도 모델 한 개를 새로 학습했다는 뜻은 아닙니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E7_mix_site10 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.2956 | 원본 표/로그 행 29 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: ens:0.90*E7_mix+0.10*E0_site. 고정 참조 구성의 연간 W_ref_pct=12.295638; E0_site 대비 오차 감소율=24.505285%. 저장된 모델 예측의 평균·혼합을 포함하며 별도 모델 한 개를 새로 학습했다는 뜻은 아닙니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E7_mix_site25 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.4349 | 원본 표/로그 행 30 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: ens:0.75*E7_mix+0.25*E0_site. 고정 참조 구성의 연간 W_ref_pct=12.434867; E0_site 대비 오차 감소율=23.650426%. 저장된 모델 예측의 평균·혼합을 포함하며 별도 모델 한 개를 새로 학습했다는 뜻은 아닙니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E4_direct | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.5027 | 원본 표/로그 행 31 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: direct group-level regression_l1 w. 고정 참조 구성의 연간 W_ref_pct=12.502673; E0_site 대비 오차 감소율=23.234101%. [기록](../../analysis_outputs/tables/results_table.csv) |
| E4_blend30 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.0524 | 원본 표/로그 행 32 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: 0.7*E7_mix_site10 + 0.3*E4_direct. 고정 참조 구성의 연간 W_ref_pct=12.052447; E0_site 대비 오차 감소율=25.998465%. 저장된 모델 예측의 평균·혼합을 포함하며 별도 모델 한 개를 새로 학습했다는 뜻은 아닙니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E4_blend50 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.0307 | 원본 표/로그 행 33 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: 0.5*E7_mix_site10 + 0.5*E4_direct. 고정 참조 구성의 연간 W_ref_pct=12.030696; E0_site 대비 오차 감소율=26.132015%. 저장된 모델 예측의 평균·혼합을 포함하며 별도 모델 한 개를 새로 학습했다는 뜻은 아닙니다. [기록](../../analysis_outputs/tables/results_table.csv) |
| E4_blend70 | historical_record | 과거 개발 모델 비교 | — | — | 고정 참조 구성 W_ref_pct (%, 낮을수록 좋음) | 12.1375 | 원본 표/로그 행 34 (재시도·다른 조건을 합치지 않음). 원본 모델 설명: 0.3*E7_mix_site10 + 0.7*E4_direct. 고정 참조 구성의 연간 W_ref_pct=12.137475; E0_site 대비 오차 감소율=25.476401%. 저장된 모델 예측의 평균·혼합을 포함하며 별도 모델 한 개를 새로 학습했다는 뜻은 아닙니다. [기록](../../analysis_outputs/tables/results_table.csv) |

## 초기 E5 사후 보정 비교

E4_blend50과 E0_site에 대한 10개 비교 행을 원본 순서대로 보존했습니다. 검증 전반인 2024-06~11월에서 계수를 적합하고 후반인 2024-12~2025-05월에서 평가했으며, 전반의 표본 내 진단도 별도 행으로 표시합니다. 전역·시간대 보정은 E4_blend50의 후반 오차를 악화시켰지만 E0_site에서는 개선됐고, 이 10행을 독립 모델 10개로 세지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| E4_blend50 / none (2nd half) | historical_record | 이후 기간으로 보정 이전 평가 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 10.2886 | 원본 표/로그 행 1 (재시도·다른 조건을 합치지 않음). 후반 평가의 보정 없는 기준입니다. W_ref_pct=10.288569, 평가 시각 수=4,368이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |
| E4_blend50 / global factor (2nd half) | historical_record | 이후 기간으로 보정 이전 평가 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 10.5289 | 원본 표/로그 행 2 (재시도·다른 조건을 합치지 않음). 전반에 적합한 전역 계수를 후반에 적용입니다. W_ref_pct=10.528879, 평가 시각 수=4,368이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |
| E4_blend50 / hourly factor (2nd half) | historical_record | 이후 기간으로 보정 이전 평가 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 10.5402 | 원본 표/로그 행 3 (재시도·다른 조건을 합치지 않음). 전반에 적합한 시간대별 계수를 후반에 적용입니다. W_ref_pct=10.540152, 평가 시각 수=4,368이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |
| E4_blend50 / none (1st half) | historical_record | 보정 학습 기간 기준값 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 13.8378 | 원본 표/로그 행 4 (재시도·다른 조건을 합치지 않음). 계수 적합에 사용한 전반의 보정 없는 기준입니다. W_ref_pct=13.837824, 평가 시각 수=4,392이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |
| E4_blend50 / hourly factor (1st half, in-sample) | historical_record | 계수 학습 기간 내 진단 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 13.6506 | 원본 표/로그 행 5 (재시도·다른 조건을 합치지 않음). 계수 적합과 같은 전반 자료에서 계산한 표본 내 결과입니다. W_ref_pct=13.650630, 평가 시각 수=4,392이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |
| E0_site / none (2nd half) | historical_record | 이후 기간으로 보정 이전 평가 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 14.2920 | 원본 표/로그 행 6 (재시도·다른 조건을 합치지 않음). 후반 평가의 보정 없는 기준입니다. W_ref_pct=14.292008, 평가 시각 수=4,368이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |
| E0_site / global factor (2nd half) | historical_record | 이후 기간으로 보정 이전 평가 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 13.3170 | 원본 표/로그 행 7 (재시도·다른 조건을 합치지 않음). 전반에 적합한 전역 계수를 후반에 적용입니다. W_ref_pct=13.317005, 평가 시각 수=4,368이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |
| E0_site / hourly factor (2nd half) | historical_record | 이후 기간으로 보정 이전 평가 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 12.4012 | 원본 표/로그 행 8 (재시도·다른 조건을 합치지 않음). 전반에 적합한 시간대별 계수를 후반에 적용입니다. W_ref_pct=12.401249, 평가 시각 수=4,368이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |
| E0_site / none (1st half) | historical_record | 보정 학습 기간 기준값 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 18.3559 | 원본 표/로그 행 9 (재시도·다른 조건을 합치지 않음). 계수 적합에 사용한 전반의 보정 없는 기준입니다. W_ref_pct=18.355924, 평가 시각 수=4,392이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |
| E0_site / hourly factor (1st half, in-sample) | historical_record | 계수 학습 기간 내 진단 | — | — | 해당 반기 W_ref_pct (%, 낮을수록 좋음) | 14.6289 | 원본 표/로그 행 10 (재시도·다른 조건을 합치지 않음). 계수 적합과 같은 전반 자료에서 계산한 표본 내 결과입니다. W_ref_pct=14.628876, 평가 시각 수=4,392이며 전반과 후반 수치를 같은 기간처럼 비교하지 않습니다. [기록](../../analysis_outputs/tables/E5_calibration.csv) |

## 초기 발전소 구성 후보 10개

원본 구성 요약표의 10개 후보를 모두 기록하며, 이후 award_run의 2개 구성×5개 혼합비 비교와는 다른 실험군입니다. 값은 2024-06~2025-05월의 E1·E7 발전소별 예측을 합산했을 때 pooled 하한을 얼마나 초과하는지 나타내며, 전체 W_pct나 공식 점수가 아닙니다. 같은 검증 연도의 오차로 최적화한 구성도 포함돼 독립 검증으로 볼 수 없고, 그룹 직접 모델을 섞은 E4의 구성 개선 효과는 여기서 측정하지 않았습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| reference | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 2.3544 | 원본 표/로그 행 1 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=2.354429%, E7 기준=2.323334%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_reference.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |
| optimized_E1 | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 0.4662 | 원본 표/로그 행 2 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=0.466174%, E7 기준=0.650415%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_optimized_E1.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |
| twin_errcorr | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 1.0503 | 원본 표/로그 행 3 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=1.050339%, E7 기준=1.047958%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_twin_errcorr.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |
| twin_gencorr | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 1.1467 | 원본 표/로그 행 4 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=1.146748%, E7 기준=1.121325%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_twin_gencorr.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |
| embed_leaforder | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 1.5878 | 원본 표/로그 행 5 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=1.587842%, E7 기준=1.584817%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_embed_leaforder.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |
| strat_cluster8_cap | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 1.5046 | 원본 표/로그 행 6 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=1.504611%, E7 기준=1.354257%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_strat_cluster8_cap.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |
| cap_pairs_balanced | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 1.8094 | 원본 표/로그 행 7 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=1.809392%, E7 기준=1.782725%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_cap_pairs_balanced.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |
| optimized_joint_E1E7 | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 0.5047 | 원본 표/로그 행 8 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=0.504688%, E7 기준=0.546782%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_optimized_joint_E1E7.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |
| optimized_E7_full | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 0.6569 | 원본 표/로그 행 9 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=0.656942%, E7 기준=0.486551%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_optimized_E7_full.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |
| optimized_E1_tightcap | historical_record | 과거 발전소 구성 비교 | — | — | E1 pooled 하한 대비 초과오차 gap_pct_E1 (%) | 0.4951 | 원본 표/로그 행 10 (재시도·다른 조건을 합치지 않음). E1 기준 pooled 하한 대비 초과오차=0.495074%, E7 기준=0.666134%; 용량 제약 충족 여부=True. 원본 구성 파일명: composition_optimized_E1_tightcap.csv. [기록](../../analysis_outputs/tables/comp_compositions_summary.csv) |

## 초기 예보 제공사·입력 제거·완벽 예보 진단

model_results.csv의 25개 명명된 비교를 모두 보존했습니다. 150개 트리의 소형 LightGBM은 2023-06~2024-05월 주간 자료 중 50만 행을 학습에 사용하고 2024-06~2025-05월 주간 자료를 평가했으므로, 학습 창이 다른 E0~E7 표와 직접 순위를 매기지 않습니다. W_over_revenue는 Σ(SMP×k×절대오차)/Σ(SMP×k×실적)의 비율이며 백분율이나 공식 점수가 아니고, 실측 기상 입력 및 같은 모델의 반복 추론 진단을 포함하므로 25행을 새 모델 학습 25회로 세지 않습니다.

| ID | 종류 | 상태 | 완료 기간 / 예정 | 확인된 모델 학습 | 지표 | 값 | 비고·근거 |
|---|---|---|---:|---:|---|---:|---|
| S0 base(geometry+site) | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.3077 | 원본 표/로그 행 1 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.307723232, 발전 비율(CF) R²=0.512499. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sa r17 A | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1293 | 원본 표/로그 행 2 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.129265514, 발전 비율(CF) R²=0.796065. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sb r17 B | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1413 | 원본 표/로그 행 3 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.141276383, 발전 비율(CF) R²=0.787936. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sc r17 A+B | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1224 | 원본 표/로그 행 4 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.122408867, 발전 비율(CF) R²=0.809621. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sa r10 A | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1347 | 원본 표/로그 행 5 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.134718150, 발전 비율(CF) R²=0.791326. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sb r10 B | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1474 | 원본 표/로그 행 6 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.147440442, 발전 비율(CF) R²=0.779895. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sc r10 A+B | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1299 | 원본 표/로그 행 7 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.129878374, 발전 비율(CF) R²=0.802725. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sd r10+r17 A+B | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1250 | 원본 표/로그 행 8 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.124985574, 발전 비율(CF) R²=0.808098. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sa-cloud r17 A cloud | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1881 | 원본 표/로그 행 9 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.188126099, 발전 비율(CF) R²=0.703710. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sb-cloud r17 B cloud | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.2216 | 원본 표/로그 행 10 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.221558720, 발전 비율(CF) R²=0.670851. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sab-cloud r17 A+B cloud | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1774 | 원본 표/로그 행 11 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.177420713, 발전 비율(CF) R²=0.728151. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sb-noCloud r17 B minus cloud | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1434 | 원본 표/로그 행 12 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.143355518, 발전 비율(CF) R²=0.784910. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| Sa-noCloud r17 A minus cloud | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1523 | 원본 표/로그 행 13 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.152321903, 발전 비율(CF) R²=0.766906. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OA obs A -> obs (perfect weather) | historical_record | 완벽한 날씨 가정 진단·제출 불가 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1032 | 원본 표/로그 행 14 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.103165935, 발전 비율(CF) R²=0.827505. 실측 기상을 평가 입력으로 사용하는 완벽 예보 진단이며 실제 제출 가능한 후보가 아닙니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OA obs A -> r17 fc (obs-trained model fed forecast) | historical_record | 관측 학습·예보 입력 차이 진단 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1307 | 원본 표/로그 행 15 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.130727791, 발전 비율(CF) R²=0.789331. 실측 기상으로 학습한 모델에 예보를 넣은 분포 차이 진단입니다. 같은 학습 모델의 여러 입력 비교가 포함됩니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OA obs A -> r10 fc | historical_record | 관측 학습·예보 입력 차이 진단 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1362 | 원본 표/로그 행 16 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.136209411, 발전 비율(CF) R²=0.783927. 실측 기상으로 학습한 모델에 예보를 넣은 분포 차이 진단입니다. 같은 학습 모델의 여러 입력 비교가 포함됩니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OA fc17 A (fc-trained, fc-fed, same vars) | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1293 | 원본 표/로그 행 17 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.129265514, 발전 비율(CF) R²=0.796065. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OB obs B -> obs (perfect weather) | historical_record | 완벽한 날씨 가정 진단·제출 불가 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.0943 | 원본 표/로그 행 18 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.094269333, 발전 비율(CF) R²=0.844936. 실측 기상을 평가 입력으로 사용하는 완벽 예보 진단이며 실제 제출 가능한 후보가 아닙니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OB obs B -> r17 fc (obs-trained model fed forecast) | historical_record | 관측 학습·예보 입력 차이 진단 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1771 | 원본 표/로그 행 19 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.177117221, 발전 비율(CF) R²=0.727710. 실측 기상으로 학습한 모델에 예보를 넣은 분포 차이 진단입니다. 같은 학습 모델의 여러 입력 비교가 포함됩니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OB obs B -> r10 fc | historical_record | 관측 학습·예보 입력 차이 진단 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1832 | 원본 표/로그 행 20 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.183246558, 발전 비율(CF) R²=0.716787. 실측 기상으로 학습한 모델에 예보를 넣은 분포 차이 진단입니다. 같은 학습 모델의 여러 입력 비교가 포함됩니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OB fc17 B (fc-trained, fc-fed, same vars) | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1430 | 원본 표/로그 행 21 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.143037449, 발전 비율(CF) R²=0.785447. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OC obs A+B -> obs (perfect weather) | historical_record | 완벽한 날씨 가정 진단·제출 불가 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.0847 | 원본 표/로그 행 22 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.084678284, 발전 비율(CF) R²=0.861470. 실측 기상을 평가 입력으로 사용하는 완벽 예보 진단이며 실제 제출 가능한 후보가 아닙니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OC obs A+B -> r17 fc (obs-trained model fed forecast) | historical_record | 관측 학습·예보 입력 차이 진단 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1515 | 원본 표/로그 행 23 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.151455415, 발전 비율(CF) R²=0.777385. 실측 기상으로 학습한 모델에 예보를 넣은 분포 차이 진단입니다. 같은 학습 모델의 여러 입력 비교가 포함됩니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OC obs A+B -> r10 fc | historical_record | 관측 학습·예보 입력 차이 진단 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1572 | 원본 표/로그 행 24 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.157163020, 발전 비율(CF) R²=0.769749. 실측 기상으로 학습한 모델에 예보를 넣은 분포 차이 진단입니다. 같은 학습 모델의 여러 입력 비교가 포함됩니다. [기록](../../analysis_outputs/tables/model_results.csv) |
| OC fc17 A+B (fc-trained, fc-fed, same vars) | historical_record | 과거 예보 입력 비교 | — | — | 가중 오차 비율 W_over_revenue (백분율 아님) | 0.1261 | 원본 표/로그 행 25 (재시도·다른 조건을 합치지 않음). 가중 오차 비율 W_over_revenue=0.126055866, 발전 비율(CF) R²=0.807531. 예보 제공사·발표 시각·입력 변수 구성을 바꾼 비교입니다. [기록](../../analysis_outputs/tables/model_results.csv) |

## 기존 10시간 단계

| ID / 상태 | 기초 / 비교 ID | 바뀐 설정 | primary W_pct (W 변화) | recent W_pct (W 변화) | alpha / 최고 제출 대비 혼합 W 변화 primary, recent | 완료 기간 / 학습 횟수 | 비고·근거 |
|---|---|---|---:|---:|---|---|---|
| c000 / 완료 | c000 | 변경 없음(비교 기준 자체) (기준 자체) | 13.1606 (0.0000%) | 12.8018 (0.0000%) | 0.007840 / -0.0008%, 0.0218% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c000/result.json) |
| c001 / 완료 | c000 | target: original_cf→exact_energy; weighting: legacy→monetary (여러 설정 동시 변경) | 14.4948 (10.1379%) | 14.5970 (14.0226%) | 0.051463 / -0.0731%, 0.5234% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c001/result.json) |
| c002 / 완료 | c001 | features: station→rich (단일 설정 차이) | 13.1918 (-8.9894%) | 11.8937 (-18.5193%) | 0.028925 / -0.0100%, 0.0001% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c002/result.json) |
| c003 / 완료 | c000 | features: station→rich (단일 설정 차이) | 12.7386 (-3.2060%) | 11.5981 (-9.4028%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c003/result.json) |
| c004 / 완료 | c002 | colsample_bytree: 0.8→0.65; half_life: 180→없음; learning_rate: 0.03→0.025; min_child_samples: 50→100; n_estimators: 400→1400 (여러 설정 동시 변경) | 12.7371 (-3.4466%) | 11.9893 (0.8042%) | 0.109772 / -0.1132%, 0.5195% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c004/result.json) |
| c005 / 완료 | c001 | colsample_bytree: 0.8→1.0; half_life: 180→365; learning_rate: 0.03→0.015; n_estimators: 400→1000; num_leaves: 63→127; reg_lambda: 0.0→20.0 (여러 설정 동시 변경) | 14.2400 (-1.7574%) | 13.9756 (-4.2565%) | 0.051759 / -0.0642%, 0.4352% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c005/result.json) |
| c006 / 완료 | c002 | colsample_bytree: 0.8→1.0; half_life: 180→90; learning_rate: 0.03→0.055; min_child_samples: 50→200; n_estimators: 400→2000; num_leaves: 63→15; reg_lambda: 0.0→8.0 (여러 설정 동시 변경) | 13.6787 (3.6909%) | 12.5383 (5.4193%) | 0.019264 / -0.0086%, -0.0037% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c006/result.json) |
| c007 / 완료 | c005 | colsample_bytree: 1.0→0.65; learning_rate: 0.015→0.07; min_child_samples: 50→300; n_estimators: 1000→400; objective: regression_l1→regression_l2 (여러 설정 동시 변경) | 13.8602 (-2.6673%) | 14.3406 (2.6112%) | 0.010088 / -0.0024%, 0.0781% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c007/result.json) |
| c008 / 완료 | c002 | colsample_bytree: 0.8→1.0; learning_rate: 0.03→0.04; min_child_samples: 50→200; num_leaves: 63→127; reg_lambda: 0.0→20.0 (여러 설정 동시 변경) | 13.2202 (0.2153%) | 12.1603 (2.2419%) | 0.066218 / -0.0721%, 0.2044% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c008/result.json) |
| c009 / 완료 | c007 | half_life: 365→없음; num_leaves: 127→15; objective: regression_l2→regression_l1; reg_lambda: 20.0→0.0 (여러 설정 동시 변경) | 13.0981 (-5.4983%) | 12.6914 (-11.4997%) | 0.096191 / -0.1535%, 0.4693% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c009/result.json) |
| c010 / 완료 | c005 | colsample_bytree: 1.0→0.8; features: station→rich; num_leaves: 127→31; reg_lambda: 20.0→2.0 (여러 설정 동시 변경) | 12.8987 (-9.4197%) | 12.0231 (-13.9708%) | 0.084305 / -0.0729%, 0.2499% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c010/result.json) |
| c011 / 완료 | c001 | colsample_bytree: 0.8→0.65; learning_rate: 0.03→0.025; n_estimators: 400→700; num_leaves: 63→31; reg_lambda: 0.0→2.0 (여러 설정 동시 변경) | 14.8116 (2.1857%) | 14.0410 (-3.8085%) | 0.053686 / -0.0950%, 0.4666% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c011/result.json) |
| c012 / 완료 | c008 | colsample_bytree: 1.0→0.65; learning_rate: 0.04→0.07; min_child_samples: 200→100; n_estimators: 400→700 (여러 설정 동시 변경) | 13.1511 (-0.5224%) | 11.9831 (-1.4579%) | 0.035287 / -0.0175%, 0.0182% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c012/result.json) |
| c013 / 완료 | c005 | half_life: 365→180; learning_rate: 0.015→0.025; min_child_samples: 50→100; n_estimators: 1000→2000; reg_lambda: 20.0→8.0 (여러 설정 동시 변경) | 14.7607 (3.6565%) | 14.4213 (3.1887%) | 0.051435 / -0.0775%, 0.4150% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c013/result.json) |
| c014 / 완료 | c003 | half_life: 180→90; learning_rate: 0.03→0.015; min_child_samples: 50→100; n_estimators: 400→1000; num_leaves: 63→31 (여러 설정 동시 변경) | 13.0694 (2.5966%) | 12.0661 (4.0354%) | 0.012466 / -0.0008%, 0.0260% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c014/result.json) |
| c015 / 완료 | c011 | half_life: 180→없음; learning_rate: 0.025→0.07; min_child_samples: 50→200; objective: regression_l1→regression_l2 (여러 설정 동시 변경) | 13.8106 (-6.7581%) | 13.1183 (-6.5714%) | 0.012167 / -0.0035%, 0.0545% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c015/result.json) |
| c016 / 완료 | c013 | colsample_bytree: 1.0→0.65; learning_rate: 0.025→0.055; reg_lambda: 8.0→2.0 (여러 설정 동시 변경) | 15.0885 (2.2208%) | 14.7004 (1.9354%) | 0.049324 / -0.1093%, 0.4966% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c016/result.json) |
| c017 / 완료 | c006 | learning_rate: 0.055→0.04; min_child_samples: 200→50; reg_lambda: 8.0→20.0 (여러 설정 동시 변경) | 13.5461 (-0.9694%) | 12.4879 (-0.4014%) | 0.031245 / -0.0172%, 0.0134% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c017/result.json) |
| c018 / 완료 | c001 | colsample_bytree: 0.8→0.65; half_life: 180→90; learning_rate: 0.03→0.04; reg_lambda: 0.0→20.0 (여러 설정 동시 변경) | 15.6719 (8.1210%) | 15.2821 (4.6940%) | 0.034611 / -0.0542%, 0.2257% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c018/result.json) |
| c019 / 완료 | c002 | half_life: 180→90; learning_rate: 0.03→0.04; min_child_samples: 50→100; n_estimators: 400→1000; reg_lambda: 0.0→8.0 (여러 설정 동시 변경) | 13.5879 (3.0032%) | 12.0343 (1.1821%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c019/result.json) |
| c020 / 완료 | c005 | colsample_bytree: 1.0→0.8; half_life: 365→90; min_child_samples: 50→200; n_estimators: 1000→1400; num_leaves: 127→31 (여러 설정 동시 변경) | 15.4412 (8.4348%) | 15.6629 (12.0728%) | 0.039026 / -0.0667%, 0.4113% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c020/result.json) |
| c021 / 완료 | c006 | colsample_bytree: 1.0→0.65; half_life: 90→365; n_estimators: 2000→400 (여러 설정 동시 변경) | 12.8506 (-6.0537%) | 12.1310 (-3.2481%) | 0.144174 / -0.2559%, 0.5003% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c021/result.json) |
| c022 / 완료 | c005 | colsample_bytree: 1.0→0.65; learning_rate: 0.015→0.055; n_estimators: 1000→700; reg_lambda: 20.0→8.0 (여러 설정 동시 변경) | 14.3227 (0.5806%) | 13.9469 (-0.2053%) | 0.059638 / -0.0969%, 0.5255% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c022/result.json) |
| c023 / 완료 | c006 | half_life: 90→365; min_child_samples: 200→100; n_estimators: 2000→700; objective: regression_l1→regression_l2; reg_lambda: 8.0→2.0 (여러 설정 동시 변경) | 13.1858 (-3.6028%) | 12.6928 (1.2329%) | 0.066847 / -0.0508%, 0.3281% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c023/result.json) |
| c024 / 완료 | c009 | colsample_bytree: 0.65→1.0; learning_rate: 0.07→0.025; n_estimators: 400→1400 (여러 설정 동시 변경) | 12.9602 (-1.0529%) | 12.8399 (1.1701%) | 0.074783 / -0.0781%, 0.4359% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c024/result.json) |
| c025 / 완료 | c012 | min_child_samples: 100→50; n_estimators: 700→1400; num_leaves: 127→15 (여러 설정 동시 변경) | 13.1517 (0.0045%) | 12.3937 (3.4265%) | 0.080200 / -0.0923%, 0.2256% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c025/result.json) |
| c026 / 완료 | c013 | colsample_bytree: 1.0→0.8; half_life: 180→365; num_leaves: 127→31; reg_lambda: 8.0→20.0 (여러 설정 동시 변경) | 13.9314 (-5.6186%) | 13.7423 (-4.7081%) | 0.069651 / -0.1079%, 0.5825% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c026/result.json) |
| c027 / 완료 | c024 | colsample_bytree: 1.0→0.8; features: station→rich; n_estimators: 1400→1000; reg_lambda: 0.0→20.0 (여러 설정 동시 변경) | 12.7684 (-1.4800%) | 12.1929 (-5.0392%) | 0.132571 / -0.1908%, 0.5980% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c027/result.json) |
| c028 / 완료 | c024 | colsample_bytree: 1.0→0.8; learning_rate: 0.025→0.055; reg_lambda: 0.0→2.0 (여러 설정 동시 변경) | 13.0752 (0.8871%) | 12.7629 (-0.5999%) | 0.131997 / -0.2618%, 0.6702% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c028/result.json) |
| c029 / 완료 | c004 | half_life: 없음→365; min_child_samples: 100→200; n_estimators: 1400→2000; num_leaves: 63→31 (여러 설정 동시 변경) | 12.7758 (0.3039%) | 12.2123 (1.8597%) | 0.136825 / -0.1836%, 0.6833% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c029/result.json) |
| c030 / 완료 | c000 | learning_rate: 0.03→0.025; min_child_samples: 50→200; n_estimators: 400→2000 (여러 설정 동시 변경) | 13.1621 (0.0118%) | 12.7992 (-0.0203%) | 0.073268 / -0.0761%, 0.3121% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c030/result.json) |
| c031 / 완료 | c003 | colsample_bytree: 0.8→1.0; half_life: 180→90; learning_rate: 0.03→0.055; min_child_samples: 50→200; objective: regression_l1→regression_l2 (여러 설정 동시 변경) | 13.5439 (6.3213%) | 12.5321 (8.0536%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c031/result.json) |
| c032 / 완료 | c017 | half_life: 90→없음; n_estimators: 2000→1000; reg_lambda: 20.0→8.0 (여러 설정 동시 변경) | 12.7858 (-5.6126%) | 12.2914 (-1.5740%) | 0.121863 / -0.1390%, 0.6271% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c032/result.json) |
| c033 / 완료 | c005 | learning_rate: 0.015→0.07; n_estimators: 1000→700; num_leaves: 127→15 (여러 설정 동시 변경) | 13.8095 (-3.0235%) | 14.0011 (0.1825%) | 0.097302 / -0.1943%, 0.8919% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c033/result.json) |
| c034 / 완료 | c010 | min_child_samples: 50→100; n_estimators: 1000→2000; reg_lambda: 2.0→8.0 (여러 설정 동시 변경) | 12.8394 (-0.4594%) | 11.9351 (-0.7319%) | 0.100208 / -0.1079%, 0.2416% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c034/result.json) |
| c035 / 완료 | c006 | features: rich→station; learning_rate: 0.055→0.07; num_leaves: 15→127 (여러 설정 동시 변경) | 15.1091 (10.4574%) | 15.3442 (22.3794%) | 0.026573 / -0.0312%, 0.2498% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c035/result.json) |
| c036 / 완료 | c019 | half_life: 90→없음; min_child_samples: 100→200; n_estimators: 1000→2000; reg_lambda: 8.0→2.0 (여러 설정 동시 변경) | 12.7515 (-6.1560%) | 12.0808 (0.3864%) | 0.139050 / -0.1619%, 0.6541% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c036/result.json) |
| c037 / 완료 | c018 | n_estimators: 400→1400; reg_lambda: 20.0→0.0 (여러 설정 동시 변경) | 15.8015 (0.8272%) | 15.6853 (2.6383%) | 0.056476 / -0.1365%, 0.6071% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c037/result.json) |
| c038 / 완료 | c005 | features: station→rich; learning_rate: 0.015→0.055; n_estimators: 1000→2000 (여러 설정 동시 변경) | 13.4003 (-5.8967%) | 11.9232 (-14.6856%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c038/result.json) |
| c039 / 완료 | c005 | colsample_bytree: 1.0→0.8; half_life: 365→없음; min_child_samples: 50→300; objective: regression_l1→regression_l2; reg_lambda: 20.0→8.0 (여러 설정 동시 변경) | 13.1729 (-7.4940%) | 13.1010 (-6.2584%) | 0.057691 / -0.0519%, 0.3233% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c039/result.json) |
| c040 / 완료 | c006 | half_life: 90→180; n_estimators: 2000→700 (여러 설정 동시 변경) | 13.3756 (-2.2153%) | 12.3091 (-1.8280%) | 0.051177 / -0.0314%, 0.1142% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c040/result.json) |
| c041 / 완료 | c018 | min_child_samples: 50→200; num_leaves: 63→127; reg_lambda: 20.0→2.0 (여러 설정 동시 변경) | 15.7347 (0.4010%) | 15.6112 (2.1536%) | 0.030104 / -0.0386%, 0.2338% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c041/result.json) |
| c042 / 완료 | c019 | learning_rate: 0.04→0.025; n_estimators: 1000→1400; num_leaves: 63→15 (여러 설정 동시 변경) | 13.4880 (-0.7353%) | 12.4689 (3.6117%) | 0.019078 / -0.0067%, 0.0331% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c042/result.json) |
| c043 / 완료 | c009 | learning_rate: 0.07→0.055; min_child_samples: 300→50; num_leaves: 15→31 (여러 설정 동시 변경) | 13.3940 (2.2589%) | 13.0320 (2.6833%) | 0.073792 / -0.0873%, 0.4349% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c043/result.json) |
| c044 / 완료 | c032 | learning_rate: 0.04→0.015; n_estimators: 1000→400 (여러 설정 동시 변경) | 12.8269 (0.3214%) | 12.1208 (-1.3873%) | 0.170747 / -0.3356%, 0.7480% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c044/result.json) |
| c045 / 완료 | c041 | half_life: 90→365; n_estimators: 400→1000; num_leaves: 127→63 (여러 설정 동시 변경) | 13.6732 (-13.1019%) | 14.2058 (-9.0030%) | 0.077867 / -0.1289%, 0.8138% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c045/result.json) |
| c046 / 완료 | c044 | learning_rate: 0.015→0.055; num_leaves: 15→127; target: exact_energy→original_cf; weighting: monetary→legacy (여러 설정 동시 변경) | 13.0814 (1.9842%) | 11.6046 (-4.2592%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c046/result.json) |
| c047 / 완료 | c005 | half_life: 365→90; min_child_samples: 50→100; num_leaves: 127→15; objective: regression_l1→regression_l2 (여러 설정 동시 변경) | 14.5280 (2.0221%) | 14.9999 (7.3290%) | 0.007456 / -0.0011%, 0.0619% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c047/result.json) |
| c048 / 완료 | c020 | colsample_bytree: 0.8→0.65; learning_rate: 0.015→0.055; num_leaves: 31→15 (여러 설정 동시 변경) | 15.5118 (0.4573%) | 15.8991 (1.5079%) | 0.036099 / -0.0605%, 0.4943% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c048/result.json) |
| c049 / 완료 | c022 | features: station→rich; num_leaves: 127→31 (여러 설정 동시 변경) | 13.0736 (-8.7210%) | 12.1106 (-13.1665%) | 0.067719 / -0.0467%, 0.2413% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c049/result.json) |
| c050 / 완료 | c001 | colsample_bytree: 0.8→1.0; learning_rate: 0.03→0.07; min_child_samples: 50→300; n_estimators: 400→2000 (여러 설정 동시 변경) | 14.2610 (-1.6127%) | 14.6569 (0.4110%) | 0.048728 / -0.0639%, 0.5031% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c050/result.json) |
| c051 / 완료 | c040 | colsample_bytree: 1.0→0.8; min_child_samples: 200→100 (여러 설정 동시 변경) | 13.2148 (-1.2026%) | 12.1812 (-1.0386%) | 0.066211 / -0.0644%, 0.1191% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c051/result.json) |
| c052 / 완료 | c041 | colsample_bytree: 0.65→0.8; min_child_samples: 200→100; n_estimators: 400→700 (여러 설정 동시 변경) | 15.2350 (-3.1760%) | 15.7062 (0.6084%) | 0.063643 / -0.1567%, 0.6491% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c052/result.json) |
| c053 / 완료 | c035 | features: station→rich; half_life: 90→없음; n_estimators: 2000→700 (여러 설정 동시 변경) | 12.9756 (-14.1204%) | 12.0181 (-21.6765%) | 0.086811 / -0.0898%, 0.2617% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c053/result.json) |
| c054 / 완료 | c037 | colsample_bytree: 0.65→1.0; n_estimators: 1400→1000 (여러 설정 동시 변경) | 15.7115 (-0.5695%) | 15.3787 (-1.9549%) | 0.045354 / -0.1001%, 0.4005% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c054/result.json) |
| c055 / 완료 | c051 | learning_rate: 0.055→0.07; objective: regression_l1→regression_l2; reg_lambda: 8.0→0.0 (여러 설정 동시 변경) | 13.3092 (0.7144%) | 12.7830 (4.9407%) | 0.014875 / -0.0028%, 0.0651% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c055/result.json) |
| c056 / 완료 | c035 | colsample_bytree: 1.0→0.65; learning_rate: 0.07→0.025 (여러 설정 동시 변경) | 15.6054 (3.2846%) | 15.4581 (0.7422%) | 0.036417 / -0.0642%, 0.2670% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c056/result.json) |
| c057 / 완료 | c008 | half_life: 180→90; min_child_samples: 200→100; reg_lambda: 20.0→2.0 (여러 설정 동시 변경) | 13.4774 (1.9454%) | 12.0908 (-0.5717%) | 0.018651 / -0.0052%, 0.0122% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c057/result.json) |
| c058 / 완료 | c016 | n_estimators: 2000→400; num_leaves: 127→63; reg_lambda: 2.0→8.0 (여러 설정 동시 변경) | 14.8312 (-1.7052%) | 14.4382 (-1.7834%) | 0.056126 / -0.1021%, 0.5160% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c058/result.json) |
| c059 / 완료 | c002 | learning_rate: 0.03→0.04; num_leaves: 63→15; reg_lambda: 0.0→8.0 (여러 설정 동시 변경) | 13.1661 (-0.1949%) | 12.2855 (3.2939%) | 0.064923 / -0.0660%, 0.1622% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c059/result.json) |
| c060 / 완료 | c016 | colsample_bytree: 0.65→0.8; learning_rate: 0.055→0.07; num_leaves: 127→31 (여러 설정 동시 변경) | 14.3287 (-5.0361%) | 15.1150 (2.8204%) | 0.093909 / -0.2293%, 1.2829% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c060/result.json) |
| c061 / 완료 | c004 | half_life: 없음→365; learning_rate: 0.025→0.07; min_child_samples: 100→300 (여러 설정 동시 변경) | 13.1103 (2.9298%) | 12.2919 (2.5234%) | 0.038249 / -0.0181%, 0.1130% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c061/result.json) |
| c062 / 완료 | c018 | min_child_samples: 50→300; n_estimators: 400→2000; num_leaves: 63→31; target: exact_energy→original_cf; weighting: monetary→legacy (여러 설정 동시 변경) | 14.5573 (-7.1120%) | 14.8039 (-3.1295%) | 0.057461 / -0.0994%, 0.5283% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c062/result.json) |
| c063 / 완료 | c031 | half_life: 90→없음; learning_rate: 0.055→0.025; min_child_samples: 200→300; n_estimators: 400→2000; reg_lambda: 0.0→8.0 (여러 설정 동시 변경) | 13.5859 (0.3104%) | 12.2280 (-2.4271%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c063/result.json) |
| c064 / 완료 | c004 | colsample_bytree: 0.65→1.0; half_life: 없음→90; min_child_samples: 100→200; reg_lambda: 0.0→20.0 (여러 설정 동시 변경) | 13.2743 (4.2178%) | 12.0725 (0.6934%) | 0.025276 / -0.0108%, 0.0134% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c064/result.json) |
| c065 / 완료 | c037 | n_estimators: 1400→1000 (단일 설정 차이) | 15.7952 (-0.0398%) | 15.6618 (-0.1500%) | 0.056634 / -0.1360%, 0.6078% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c065/result.json) |
| c066 / 완료 | c038 | half_life: 365→없음; reg_lambda: 20.0→8.0 (여러 설정 동시 변경) | 12.9870 (-3.0847%) | 12.0129 (0.7521%) | 0.043966 / -0.0202%, 0.1354% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c066/result.json) |
| c067 / 완료 | c020 | learning_rate: 0.015→0.04; n_estimators: 1400→2000 (여러 설정 동시 변경) | 15.3829 (-0.3771%) | 16.2830 (3.9590%) | 0.043324 / -0.0831%, 0.5062% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c067/result.json) |
| c068 / 완료 | c025 | colsample_bytree: 0.65→0.8; half_life: 180→365; num_leaves: 15→63 (여러 설정 동시 변경) | 13.2406 (0.6760%) | 12.1064 (-2.3176%) | 0.021428 / -0.0043%, 0.0521% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c068/result.json) |
| c069 / 완료 | c001 | learning_rate: 0.03→0.04; min_child_samples: 50→200; n_estimators: 400→1000; num_leaves: 63→15 (여러 설정 동시 변경) | 14.5541 (0.4093%) | 14.2390 (-2.4524%) | 0.053929 / -0.1043%, 0.5105% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c069/result.json) |
| c070 / 완료 | c069 | features: station→rich; num_leaves: 15→127 (여러 설정 동시 변경) | 13.2134 (-9.2117%) | 12.0949 (-15.0581%) | 0.014526 / -0.0021%, 0.0263% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c070/result.json) |
| c071 / 완료 | c007 | colsample_bytree: 0.65→1.0; half_life: 365→90; learning_rate: 0.07→0.055; num_leaves: 127→31; reg_lambda: 20.0→2.0 (여러 설정 동시 변경) | 14.9911 (8.1595%) | 15.7089 (9.5418%) | 0.014388 / -0.0058%, 0.1424% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c071/result.json) |
| c072 / 완료 | c006 | min_child_samples: 200→300; n_estimators: 2000→1000; num_leaves: 15→63; reg_lambda: 8.0→2.0 (여러 설정 동시 변경) | 13.3238 (-2.5942%) | 12.3207 (-1.7347%) | 0.041956 / -0.0241%, 0.0710% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c072/result.json) |
| c073 / 완료 | c020 | colsample_bytree: 0.8→0.65; half_life: 90→없음; n_estimators: 1400→400 (여러 설정 동시 변경) | 13.0320 (-15.6019%) | 12.8146 (-18.1852%) | 0.111624 / -0.1813%, 0.7943% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c073/result.json) |
| c074 / 완료 | c036 | colsample_bytree: 0.8→0.65; learning_rate: 0.04→0.07; n_estimators: 2000→400 (여러 설정 동시 변경) | 12.7908 (0.3086%) | 12.1653 (0.6999%) | 0.135144 / -0.2015%, 0.6562% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c074/result.json) |
| c075 / 완료 | c005 | half_life: 365→180; num_leaves: 127→31; reg_lambda: 20.0→2.0 (여러 설정 동시 변경) | 14.7031 (3.2517%) | 14.0521 (0.5472%) | 0.059656 / -0.1150%, 0.4907% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c075/result.json) |
| c076 / 완료 | c009 | features: station→rich; learning_rate: 0.07→0.055; reg_lambda: 0.0→20.0 (여러 설정 동시 변경) | 12.7357 (-2.7670%) | 12.1348 (-4.3863%) | 0.159563 / -0.2542%, 0.7091% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c076/result.json) |
| c077 / 완료 | c020 | colsample_bytree: 0.8→1.0; num_leaves: 31→63; reg_lambda: 20.0→8.0 (여러 설정 동시 변경) | 14.9648 (-3.0852%) | 15.5047 (-1.0096%) | 0.046807 / -0.0848%, 0.4735% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c077/result.json) |
| c078 / 완료 | c014 | colsample_bytree: 0.8→1.0; half_life: 90→180; learning_rate: 0.015→0.07; min_child_samples: 100→300; reg_lambda: 0.0→8.0 (여러 설정 동시 변경) | 12.6959 (-2.8577%) | 11.9503 (-0.9599%) | 0.134350 / -0.1835%, 0.3722% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c078/result.json) |
| c079 / 완료 | c028 | half_life: 없음→365; learning_rate: 0.055→0.04; min_child_samples: 300→50; objective: regression_l1→regression_l2 (여러 설정 동시 변경) | 13.6148 (4.1273%) | 14.2577 (11.7121%) | 0.044941 / -0.0428%, 0.3982% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c079/result.json) |
| c080 / 완료 | c019 | features: rich→station; half_life: 90→180; reg_lambda: 8.0→20.0 (여러 설정 동시 변경) | 14.2141 (4.6079%) | 14.5220 (20.6719%) | 0.055489 / -0.0692%, 0.5600% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c080/result.json) |
| c081 / 완료 | c064 | half_life: 90→없음; reg_lambda: 20.0→8.0 (여러 설정 동시 변경) | 12.8495 (-3.2000%) | 12.0054 (-0.5555%) | 0.111701 / -0.1234%, 0.4129% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c081/result.json) |
| c082 / 완료 | c050 | learning_rate: 0.07→0.025; n_estimators: 2000→1000; reg_lambda: 0.0→2.0 (여러 설정 동시 변경) | 14.1286 (-0.9285%) | 14.2404 (-2.8422%) | 0.073203 / -0.1562%, 0.7592% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c082/result.json) |
| c083 / 완료 | c011 | features: station→rich; min_child_samples: 50→200; n_estimators: 700→1000 (여러 설정 동시 변경) | 13.0650 (-11.7917%) | 12.1660 (-13.3539%) | 0.069771 / -0.0479%, 0.2111% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c083/result.json) |
| c084 / 완료 | c021 | features: rich→station; min_child_samples: 200→100 (여러 설정 동시 변경) | 13.7839 (7.2626%) | 14.1905 (16.9776%) | 0.089860 / -0.1496%, 1.0037% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c084/result.json) |
| c085 / 완료 | c068 | half_life: 365→없음; learning_rate: 0.07→0.055; n_estimators: 1400→700 (여러 설정 동시 변경) | 12.8124 (-3.2338%) | 11.9648 (-1.1699%) | 0.093625 / -0.1024%, 0.2816% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c085/result.json) |
| c086 / 완료 | c073 | colsample_bytree: 0.65→1.0; learning_rate: 0.015→0.025 (여러 설정 동시 변경) | 12.9399 (-0.7071%) | 12.8106 (-0.0308%) | 0.074216 / -0.0927%, 0.4454% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c086/result.json) |
| c087 / 완료 | c055 | min_child_samples: 100→300; num_leaves: 15→63; reg_lambda: 0.0→8.0 (여러 설정 동시 변경) | 13.4433 (1.0073%) | 12.7462 (-0.2879%) | 0.031064 / -0.0181%, 0.1458% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c087/result.json) |
| c088 / 완료 | c033 | colsample_bytree: 1.0→0.65; learning_rate: 0.07→0.04; min_child_samples: 50→200 (여러 설정 동시 변경) | 13.7469 (-0.4529%) | 14.0642 (0.4508%) | 0.069761 / -0.1187%, 0.7022% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c088/result.json) |
| c089 / 완료 | c027 | learning_rate: 0.025→0.07; n_estimators: 1000→1400; num_leaves: 15→31; reg_lambda: 20.0→8.0 (여러 설정 동시 변경) | 12.8549 (0.6771%) | 12.1111 (-0.6713%) | 0.152494 / -0.2642%, 0.6076% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c089/result.json) |
| c090 / 완료 | c088 | colsample_bytree: 0.65→1.0; num_leaves: 15→127; reg_lambda: 20.0→0.0 (여러 설정 동시 변경) | 13.7206 (-0.1917%) | 13.5330 (-3.7770%) | 0.101363 / -0.2309%, 0.9196% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c090/result.json) |
| c091 / 완료 | c008 | colsample_bytree: 1.0→0.65; min_child_samples: 200→100; num_leaves: 127→63 (여러 설정 동시 변경) | 13.1871 (-0.2500%) | 11.8607 (-2.4640%) | 0.057867 / -0.0380%, 0.0416% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c091/result.json) |
| c092 / 완료 | c013 | half_life: 180→365; n_estimators: 2000→700 (여러 설정 동시 변경) | 13.8757 (-5.9957%) | 13.6638 (-5.2524%) | 0.072638 / -0.1320%, 0.5310% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c092/result.json) |
| c093 / 완료 | c057 | colsample_bytree: 1.0→0.65; half_life: 90→없음; n_estimators: 400→1000 (여러 설정 동시 변경) | 12.8923 (-4.3410%) | 11.8974 (-1.5996%) | 0.098907 / -0.0755%, 0.3573% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c093/result.json) |
| c094 / 완료 | c000 | half_life: 180→90; learning_rate: 0.03→0.025; n_estimators: 400→1400; num_leaves: 63→15; reg_lambda: 0.0→20.0 (여러 설정 동시 변경) | 14.5522 (10.5745%) | 14.5147 (13.3802%) | 0.054122 / -0.0873%, 0.4449% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c094/result.json) |
| c095 / 완료 | c046 | colsample_bytree: 1.0→0.65; learning_rate: 0.055→0.07; objective: regression_l1→regression_l2; reg_lambda: 8.0→0.0 (여러 설정 동시 변경) | 13.6162 (4.0883%) | 11.8426 (2.0506%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c095/result.json) |
| c096 / 완료 | c038 | n_estimators: 2000→1400; num_leaves: 127→31; reg_lambda: 20.0→0.0 (여러 설정 동시 변경) | 12.8489 (-4.1151%) | 12.1119 (1.5821%) | 0.134374 / -0.1998%, 0.4013% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c096/result.json) |
| c097 / 완료 | c045 | learning_rate: 0.04→0.07; n_estimators: 1000→2000; num_leaves: 63→15 (여러 설정 동시 변경) | 13.9698 (2.1693%) | 14.1516 (-0.3809%) | 0.083892 / -0.1933%, 0.7640% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c097/result.json) |
| c098 / 완료 | c002 | learning_rate: 0.03→0.015; n_estimators: 400→700; num_leaves: 63→15 (여러 설정 동시 변경) | 13.1736 (-0.1379%) | 12.2746 (3.2030%) | 0.070925 / -0.0759%, 0.2382% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c098/result.json) |
| c099 / 완료 | c041 | colsample_bytree: 0.65→0.8; learning_rate: 0.04→0.07 (여러 설정 동시 변경) | 15.5117 (-1.4175%) | 15.3405 (-1.7344%) | 0.029456 / -0.0340%, 0.1966% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c099/result.json) |
| c100 / 완료 | c073 | features: station→rich; learning_rate: 0.015→0.055 (여러 설정 동시 변경) | 12.8368 (-1.4980%) | 12.1283 (-5.3555%) | 0.099293 / -0.1039%, 0.4355% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c100/result.json) |
| c101 / 완료 | c005 | n_estimators: 1000→2000; num_leaves: 127→15; reg_lambda: 20.0→0.0 (여러 설정 동시 변경) | 13.7153 (-3.6848%) | 13.6413 (-2.3923%) | 0.080391 / -0.1264%, 0.6646% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c101/result.json) |
| c102 / 완료 | c047 | features: station→rich; objective: regression_l2→regression_l1 (여러 설정 동시 변경) | 13.4874 (-7.1628%) | 12.6026 (-15.9823%) | 0.027824 / -0.0167%, 0.0673% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c102/result.json) |
| c103 / 완료 | c050 | learning_rate: 0.07→0.025; n_estimators: 2000→700; objective: regression_l1→regression_l2 (여러 설정 동시 변경) | 14.0901 (-1.1986%) | 14.3505 (-2.0907%) | 0.028185 / -0.0257%, 0.2326% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c103/result.json) |
| c104 / 완료 | c008 | colsample_bytree: 1.0→0.65; min_child_samples: 200→300; n_estimators: 400→1400 (여러 설정 동시 변경) | 13.0335 (-1.4123%) | 12.1411 (-0.1580%) | 0.089616 / -0.0952%, 0.2285% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c104/result.json) |
| c105 / 완료 | c028 | colsample_bytree: 0.8→0.65; half_life: 없음→90; learning_rate: 0.055→0.015 (여러 설정 동시 변경) | 15.1890 (16.1669%) | 15.2169 (19.2275%) | 0.056465 / -0.1224%, 0.6323% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c105/result.json) |
| c106 / 완료 | c057 | min_child_samples: 100→300; num_leaves: 127→31; reg_lambda: 2.0→0.0 (여러 설정 동시 변경) | 13.6896 (1.5745%) | 12.3107 (1.8187%) | 0.027752 / -0.0111%, 0.0154% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c106/result.json) |
| c107 / 완료 | c077 | min_child_samples: 200→50; reg_lambda: 8.0→20.0 (여러 설정 동시 변경) | 15.3824 (2.7905%) | 15.3062 (-1.2803%) | 0.059683 / -0.1269%, 0.6041% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c107/result.json) |
| c108 / 완료 | c006 | learning_rate: 0.055→0.07; n_estimators: 2000→1000 (여러 설정 동시 변경) | 13.7152 (0.2671%) | 12.4926 (-0.3637%) | 0.027144 / -0.0140%, 0.0177% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c108/result.json) |
| c109 / 완료 | c086 | half_life: 없음→90; min_child_samples: 200→300 (여러 설정 동시 변경) | 14.8626 (14.8588%) | 15.1744 (18.4516%) | 0.075329 / -0.1854%, 0.8232% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c109/result.json) |
| c110 / 완료 | c078 | half_life: 180→90; min_child_samples: 300→200 (여러 설정 동시 변경) | 13.2478 (4.3466%) | 12.0162 (0.5515%) | 0.040020 / -0.0209%, 0.0126% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c110/result.json) |
| c111 / 완료 | c058 | learning_rate: 0.055→0.07; num_leaves: 63→15; objective: regression_l1→regression_l2 (여러 설정 동시 변경) | 14.1725 (-4.4417%) | 14.8504 (2.8546%) | 0.009021 / -0.0023%, 0.0869% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c111/result.json) |
| c112 / 완료 | c043 | min_child_samples: 50→300; reg_lambda: 0.0→2.0 (여러 설정 동시 변경) | 13.2542 (-1.0441%) | 12.8442 (-1.4412%) | 0.036448 / -0.0266%, 0.1913% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c112/result.json) |
| c113 / 완료 | c019 | colsample_bytree: 0.8→0.65; num_leaves: 63→31 (여러 설정 동시 변경) | 13.5591 (-0.2124%) | 12.2851 (2.0839%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c113/result.json) |
| c114 / 완료 | c092 | n_estimators: 700→1000; num_leaves: 127→31 (여러 설정 동시 변경) | 13.6700 (-1.4826%) | 13.5872 (-0.5605%) | 0.067236 / -0.0853%, 0.5369% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c114/result.json) |
| c115 / 완료 | c098 | num_leaves: 15→63; reg_lambda: 0.0→2.0 (여러 설정 동시 변경) | 13.1408 (-0.2492%) | 11.8869 (-3.1587%) | 0.036139 / -0.0114%, 0.0455% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c115/result.json) |
| c116 / 완료 | c041 | half_life: 90→180; learning_rate: 0.04→0.015; num_leaves: 127→63 (여러 설정 동시 변경) | 14.5723 (-7.3877%) | 14.1914 (-9.0952%) | 0.054191 / -0.1008%, 0.4864% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c116/result.json) |
| c117 / 완료 | c096 | half_life: 365→없음; learning_rate: 0.055→0.025 (여러 설정 동시 변경) | 12.6146 (-1.8235%) | 12.0052 (-0.8808%) | 0.201246 / -0.3627%, 0.9154% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c117/result.json) |
| c118 / 완료 | c005 | num_leaves: 127→63; reg_lambda: 20.0→0.0 (여러 설정 동시 변경) | 13.9669 (-1.9181%) | 13.7724 (-1.4543%) | 0.055508 / -0.0677%, 0.3939% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c118/result.json) |
| c119 / 완료 | c010 | learning_rate: 0.015→0.07; min_child_samples: 50→200; num_leaves: 31→15; objective: regression_l1→regression_l2 (여러 설정 동시 변경) | 13.3055 (3.1543%) | 12.7972 (6.4384%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c119/result.json) |
| c120 / 완료 | c004 | features: rich→station; half_life: 없음→365; learning_rate: 0.025→0.015 (여러 설정 동시 변경) | 14.0189 (10.0633%) | 13.9126 (16.0413%) | 0.050873 / -0.0522%, 0.4605% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c120/result.json) |
| c121 / 완료 | c019 | num_leaves: 63→31; reg_lambda: 8.0→0.0 (여러 설정 동시 변경) | 13.5440 (-0.3234%) | 12.2649 (1.9160%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c121/result.json) |
| c122 / 완료 | c011 | learning_rate: 0.025→0.055; min_child_samples: 50→200; num_leaves: 31→15 (여러 설정 동시 변경) | 14.5782 (-1.5755%) | 14.8785 (5.9647%) | 0.051220 / -0.0833%, 0.5742% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c122/result.json) |
| c123 / 완료 | c057 | learning_rate: 0.04→0.025; min_child_samples: 100→200; num_leaves: 127→31 (여러 설정 동시 변경) | 13.4513 (-0.1937%) | 12.4576 (3.0339%) | 0.045644 / -0.0332%, 0.0708% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c123/result.json) |
| c124 / 완료 | c086 | learning_rate: 0.025→0.055; n_estimators: 400→2000; num_leaves: 31→63 (여러 설정 동시 변경) | 13.3623 (3.2642%) | 12.8993 (0.6924%) | 0.044705 / -0.0293%, 0.2735% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c124/result.json) |
| c125 / 완료 | c075 | features: station→rich; min_child_samples: 50→100 (여러 설정 동시 변경) | 13.2064 (-10.1794%) | 12.0468 (-14.2708%) | 0.058300 / -0.0403%, 0.0940% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c125/result.json) |
| c126 / 완료 | c060 | learning_rate: 0.07→0.055; target: exact_energy→original_cf; weighting: monetary→legacy (여러 설정 동시 변경) | 13.1316 (-8.3543%) | 12.8535 (-14.9616%) | 0.029564 / -0.0157%, 0.0725% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c126/result.json) |
| c127 / 완료 | c031 | half_life: 90→365; min_child_samples: 200→50; n_estimators: 400→2000; num_leaves: 63→127 (여러 설정 동시 변경) | 13.3887 (-1.1460%) | 11.9768 (-4.4317%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c127/result.json) |
| c128 / 완료 | c011 | features: station→rich; half_life: 180→365; num_leaves: 31→15 (여러 설정 동시 변경) | 12.9391 (-12.6420%) | 12.1998 (-13.1131%) | 0.095326 / -0.0977%, 0.3970% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c128/result.json) |
| c129 / 완료 | c028 | min_child_samples: 300→200; reg_lambda: 2.0→20.0 (여러 설정 동시 변경) | 12.9750 (-0.7665%) | 13.2682 (3.9590%) | 0.099580 / -0.1691%, 0.7258% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c129/result.json) |
| c130 / 완료 | c128 | n_estimators: 700→400; reg_lambda: 2.0→20.0 (여러 설정 동시 변경) | 12.9334 (-0.0440%) | 12.2919 (0.7551%) | 0.132935 / -0.2099%, 0.6258% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c130/result.json) |
| c131 / 완료 | c037 | learning_rate: 0.04→0.055; min_child_samples: 50→100; num_leaves: 63→31 (여러 설정 동시 변경) | 15.4515 (-2.2148%) | 16.1930 (3.2364%) | 0.033968 / -0.0529%, 0.3538% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c131/result.json) |
| c132 / 완료 | c006 | colsample_bytree: 1.0→0.8; num_leaves: 15→31 (여러 설정 동시 변경) | 13.4459 (-1.7016%) | 12.2535 (-2.2713%) | 0.053957 / -0.0501%, 0.0314% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c132/result.json) |
| c133 / 완료 | c084 | half_life: 365→없음; learning_rate: 0.055→0.015; n_estimators: 400→1400 (여러 설정 동시 변경) | 13.0715 (-5.1682%) | 13.0461 (-8.0651%) | 0.096591 / -0.1283%, 0.6596% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c133/result.json) |
| c134 / 완료 | c038 | min_child_samples: 50→300; n_estimators: 2000→1000; reg_lambda: 20.0→0.0 (여러 설정 동시 변경) | 13.0872 (-2.3369%) | 12.1865 (2.2077%) | 0.094651 / -0.1115%, 0.3110% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c134/result.json) |
| c135 / 완료 | c028 | learning_rate: 0.055→0.04; n_estimators: 1400→400; num_leaves: 15→63; objective: regression_l1→regression_l2 (여러 설정 동시 변경) | 13.2801 (1.5671%) | 13.3587 (4.6684%) | 0.033192 / -0.0192%, 0.2145% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c135/result.json) |
| c136 / 완료 | c056 | features: station→rich; min_child_samples: 200→300 (여러 설정 동시 변경) | 13.1223 (-15.9116%) | 11.9654 (-22.5946%) | 0.066269 / -0.0550%, 0.0528% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c136/result.json) |
| c137 / 완료 | c077 | n_estimators: 1400→400; reg_lambda: 8.0→20.0 (여러 설정 동시 변경) | 15.1287 (1.0953%) | 14.9529 (-3.5593%) | 0.051484 / -0.1141%, 0.4359% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c137/result.json) |
| c138 / 완료 | c004 | learning_rate: 0.025→0.055; n_estimators: 1400→1000; reg_lambda: 0.0→20.0 (여러 설정 동시 변경) | 12.8491 (0.8797%) | 12.1235 (1.1194%) | 0.099487 / -0.1066%, 0.5100% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c138/result.json) |
| c139 / 완료 | c004 | features: rich→station; learning_rate: 0.025→0.055; n_estimators: 1400→700 (여러 설정 동시 변경) | 13.7432 (7.8990%) | 13.2563 (10.5677%) | 0.023698 / -0.0147%, 0.1342% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c139/result.json) |
| c140 / 완료 | c042 | half_life: 90→180; min_child_samples: 100→200; num_leaves: 15→127 (여러 설정 동시 변경) | 13.1214 (-2.7180%) | 12.0231 (-3.5759%) | 0.031575 / -0.0121%, 0.0716% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c140/result.json) |
| c141 / 완료 | c011 | min_child_samples: 50→300; n_estimators: 700→1400 (여러 설정 동시 변경) | 14.3379 (-3.1978%) | 14.5484 (3.6132%) | 0.058304 / -0.0963%, 0.5613% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c141/result.json) |
| c142 / 완료 | c125 | n_estimators: 1000→2000; target: exact_energy→original_cf; weighting: monetary→legacy (여러 설정 동시 변경) | 12.6584 (-4.1492%) | 11.8043 (-2.0124%) | 0.055059 / -0.0195%, 0.1581% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c142/result.json) |
| c143 / 완료 | c103 | colsample_bytree: 1.0→0.8; n_estimators: 700→400 (여러 설정 동시 변경) | 14.1646 (0.5289%) | 14.3629 (0.0864%) | 0.006343 / -0.0010%, 0.0553% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c143/result.json) |
| c144 / 완료 | c041 | learning_rate: 0.04→0.055; n_estimators: 400→700 (여러 설정 동시 변경) | 15.5446 (-1.2080%) | 15.9852 (2.3953%) | 0.041692 / -0.0774%, 0.3589% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c144/result.json) |
| c145 / 완료 | c004 | half_life: 없음→180; n_estimators: 1400→2000; reg_lambda: 0.0→2.0 (여러 설정 동시 변경) | 12.9937 (2.0149%) | 12.0570 (0.5642%) | 0.068580 / -0.0517%, 0.2082% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c145/result.json) |
| c146 / 완료 | c024 | half_life: 없음→180; learning_rate: 0.025→0.055 (여러 설정 동시 변경) | 14.1550 (9.2190%) | 14.5323 (13.1803%) | 0.073300 / -0.1601%, 0.8259% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c146/result.json) |
| c147 / 완료 | c020 | features: station→rich; half_life: 90→180; num_leaves: 31→15 (여러 설정 동시 변경) | 13.1061 (-15.1225%) | 12.3085 (-21.4161%) | 0.079201 / -0.1070%, 0.3105% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c147/result.json) |
| c148 / 완료 | c039 | colsample_bytree: 0.8→0.65; min_child_samples: 300→200; objective: regression_l2→regression_l1 (여러 설정 동시 변경) | 13.0795 (-0.7089%) | 12.9020 (-1.5188%) | 0.077082 / -0.1075%, 0.5410% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c148/result.json) |
| c149 / 완료 | c020 | features: station→rich; learning_rate: 0.015→0.025; min_child_samples: 200→50 (여러 설정 동시 변경) | 13.4795 (-12.7042%) | 12.3271 (-21.2971%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c149/result.json) |
| c150 / 완료 | c035 | half_life: 90→180; n_estimators: 2000→400 (여러 설정 동시 변경) | 15.1805 (0.4724%) | 13.7481 (-10.4023%) | 0.018727 / -0.0138%, 0.1127% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c150/result.json) |
| c151 / 완료 | c100 | n_estimators: 400→1000; objective: regression_l1→regression_l2; reg_lambda: 20.0→0.0 (여러 설정 동시 변경) | 13.0695 (1.8125%) | 12.3083 (1.4841%) | 0.089518 / -0.0979%, 0.4439% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c151/result.json) |
| c152 / 완료 | c120 | learning_rate: 0.015→0.04; reg_lambda: 0.0→8.0 (여러 설정 동시 변경) | 14.0415 (0.1613%) | 14.2134 (2.1625%) | 0.041474 / -0.0399%, 0.3964% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c152/result.json) |
| c153 / 완료 | c072 | learning_rate: 0.055→0.07; n_estimators: 1000→700 (여러 설정 동시 변경) | 13.5633 (1.7977%) | 12.4867 (1.3470%) | 0.052487 / -0.0441%, 0.1031% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c153/result.json) |
| c154 / 완료 | c079 | n_estimators: 1400→700; objective: regression_l2→regression_l1 (여러 설정 동시 변경) | 13.6927 (0.5718%) | 13.7815 (-3.3397%) | 0.107465 / -0.2111%, 1.0152% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c154/result.json) |
| c155 / 완료 | c128 | half_life: 365→없음; learning_rate: 0.025→0.07 (여러 설정 동시 변경) | 12.7733 (-1.2812%) | 12.3198 (0.9835%) | 0.181010 / -0.2765%, 1.1769% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c155/result.json) |
| c156 / 완료 | c020 | learning_rate: 0.015→0.025; n_estimators: 1400→1000; reg_lambda: 20.0→2.0 (여러 설정 동시 변경) | 15.3221 (-0.7712%) | 15.6135 (-0.3156%) | 0.047704 / -0.1000%, 0.5171% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c156/result.json) |
| c157 / 완료 | c066 | learning_rate: 0.055→0.025; min_child_samples: 50→300; num_leaves: 127→31 (여러 설정 동시 변경) | 12.7998 (-1.4417%) | 12.1531 (1.1674%) | 0.130905 / -0.1679%, 0.5884% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c157/result.json) |
| c158 / 완료 | c022 | num_leaves: 127→31; reg_lambda: 8.0→0.0; target: exact_energy→original_cf; weighting: monetary→legacy (여러 설정 동시 변경) | 13.2182 (-7.7117%) | 12.2059 (-12.4834%) | 0.003791 / -0.0000%, 0.0074% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c158/result.json) |
| c159 / 완료 | c031 | min_child_samples: 200→100; n_estimators: 400→1400; num_leaves: 63→127 (여러 설정 동시 변경) | 13.4061 (-1.0175%) | 12.2318 (-2.3963%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c159/result.json) |
| c160 / 완료 | c089 | n_estimators: 1400→1000; reg_lambda: 8.0→0.0 (여러 설정 동시 변경) | 12.7360 (-0.9243%) | 12.2636 (1.2594%) | 0.196137 / -0.4555%, 1.0554% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c160/result.json) |
| c161 / 완료 | c020 | half_life: 90→없음; n_estimators: 1400→1000; reg_lambda: 20.0→0.0 (여러 설정 동시 변경) | 13.1001 (-15.1611%) | 12.9962 (-17.0252%) | 0.075957 / -0.0873%, 0.5169% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c161/result.json) |
| c162 / 완료 | c147 | min_child_samples: 200→300; reg_lambda: 20.0→8.0 (여러 설정 동시 변경) | 13.1494 (0.3304%) | 12.3089 (0.0031%) | 0.068803 / -0.0756%, 0.2347% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c162/result.json) |
| c163 / 완료 | c005 | colsample_bytree: 1.0→0.65; min_child_samples: 50→100; num_leaves: 127→31 (여러 설정 동시 변경) | 13.7718 (-3.2878%) | 13.6248 (-2.5104%) | 0.083733 / -0.1437%, 0.7028% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c163/result.json) |
| c164 / 완료 | c053 | colsample_bytree: 1.0→0.8; learning_rate: 0.07→0.025; num_leaves: 127→31 (여러 설정 동시 변경) | 12.8691 (-0.8210%) | 12.0234 (0.0441%) | 0.087412 / -0.0876%, 0.2811% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c164/result.json) |
| c165 / 완료 | c026 | half_life: 365→90; n_estimators: 2000→400; num_leaves: 31→127 (여러 설정 동시 변경) | 15.0331 (7.9081%) | 15.5857 (13.4140%) | 0.053539 / -0.1046%, 0.4478% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c165/result.json) |
| c166 / 완료 | c066 | n_estimators: 2000→1000; reg_lambda: 8.0→0.0 (여러 설정 동시 변경) | 12.9687 (-0.1410%) | 11.8228 (-1.5824%) | 0.031129 / -0.0121%, 0.0428% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c166/result.json) |
| c167 / 완료 | c001 | half_life: 180→90; learning_rate: 0.03→0.07; num_leaves: 63→31; objective: regression_l1→regression_l2 (여러 설정 동시 변경) | 14.4979 (0.0219%) | 15.4190 (5.6316%) | 0.033066 / -0.0367%, 0.3595% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c167/result.json) |
| c168 / 완료 | c019 | min_child_samples: 100→200; n_estimators: 1000→1400; reg_lambda: 8.0→0.0 (여러 설정 동시 변경) | 13.1504 (-3.2204%) | 12.1097 (0.6266%) | 0.082375 / -0.0900%, 0.0821% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c168/result.json) |
| c169 / 완료 | c137 | min_child_samples: 200→100; num_leaves: 63→127 (여러 설정 동시 변경) | 15.1875 (0.3886%) | 14.6817 (-1.8139%) | 0.049612 / -0.0941%, 0.3286% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c169/result.json) |
| c170 / 완료 | c044 | half_life: 없음→365; learning_rate: 0.015→0.025; num_leaves: 15→63 (여러 설정 동시 변경) | 13.0860 (2.0201%) | 11.9513 (-1.3991%) | 0.053168 / -0.0293%, 0.1289% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c170/result.json) |
| c171 / 완료 | c101 | num_leaves: 15→63 (단일 설정 차이) | 14.0824 (2.6766%) | 13.8380 (1.4418%) | 0.048748 / -0.0529%, 0.3421% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c171/result.json) |
| c172 / 완료 | c166 | learning_rate: 0.055→0.07; reg_lambda: 0.0→20.0 (여러 설정 동시 변경) | 12.9705 (0.0142%) | 12.0761 (2.1426%) | 0.072437 / -0.0683%, 0.2559% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c172/result.json) |
| c173 / 완료 | c005 | half_life: 365→없음 (단일 설정 차이) | 13.4835 (-5.3124%) | 12.8015 (-8.4016%) | 0.072113 / -0.0943%, 0.3483% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c173/result.json) |
| c174 / 완료 | c093 | n_estimators: 1000→400; num_leaves: 127→15; target: exact_energy→original_cf; weighting: monetary→legacy (여러 설정 동시 변경) | 12.5450 (-2.6940%) | 11.7210 (-1.4831%) | 0.101568 / -0.0644%, 0.3072% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c174/result.json) |
| c175 / 완료 | c047 | colsample_bytree: 1.0→0.65; min_child_samples: 100→50; n_estimators: 1000→2000 (여러 설정 동시 변경) | 14.3680 (-1.1008%) | 15.1457 (0.9718%) | 0.024522 / -0.0143%, 0.2427% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c175/result.json) |
| c176 / 완료 | c105 | half_life: 90→365; min_child_samples: 300→50 (여러 설정 동시 변경) | 13.9189 (-8.3624%) | 13.6258 (-10.4559%) | 0.077200 / -0.1368%, 0.6459% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c176/result.json) |
| c177 / 완료 | c012 | colsample_bytree: 0.65→0.8; learning_rate: 0.07→0.055; n_estimators: 700→1400 (여러 설정 동시 변경) | 13.3999 (1.8921%) | 12.2120 (1.9103%) | 0.011353 / -0.0014%, 0.0366% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c177/result.json) |
| c178 / 완료 | c156 | n_estimators: 1000→700 (단일 설정 차이) | 15.2948 (-0.1778%) | 15.6132 (-0.0014%) | 0.050863 / -0.1053%, 0.5601% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c178/result.json) |
| c179 / 완료 | c072 | learning_rate: 0.055→0.025; num_leaves: 63→15 (여러 설정 동시 변경) | 13.5238 (1.5011%) | 12.4860 (1.3411%) | 0.033757 / -0.0214%, 0.0440% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c179/result.json) |
| c180 / 완료 | c129 | min_child_samples: 200→50; num_leaves: 15→31 (여러 설정 동시 변경) | 13.3418 (2.8271%) | 12.8887 (-2.8605%) | 0.075224 / -0.1178%, 0.3356% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c180/result.json) |
| c181 / 완료 | c034 | learning_rate: 0.015→0.07; num_leaves: 31→15 (여러 설정 동시 변경) | 12.9216 (0.6403%) | 12.4447 (4.2692%) | 0.114349 / -0.1247%, 0.5774% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c181/result.json) |
| c182 / 완료 | c052 | n_estimators: 700→2000; reg_lambda: 2.0→0.0 (여러 설정 동시 변경) | 15.9564 (4.7356%) | 15.8781 (1.0940%) | 0.038704 / -0.0817%, 0.3652% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c182/result.json) |
| c183 / 완료 | c115 | n_estimators: 700→400; num_leaves: 63→127; objective: regression_l1→regression_l2 (여러 설정 동시 변경) | 13.2465 (0.8048%) | 12.1627 (2.3196%) | 0.038791 / -0.0263%, 0.0979% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c183/result.json) |
| c184 / 완료 | c115 | features: rich→station; reg_lambda: 2.0→20.0 (여러 설정 동시 변경) | 14.6185 (11.2454%) | 14.4372 (21.4541%) | 0.059942 / -0.1151%, 0.5932% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c184/result.json) |
| c185 / 완료 | c021 | half_life: 365→없음; learning_rate: 0.055→0.015; n_estimators: 400→700 (여러 설정 동시 변경) | 12.6735 (-1.3784%) | 12.0630 (-0.5605%) | 0.171411 / -0.3405%, 0.6880% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c185/result.json) |
| c186 / 완료 | c173 | min_child_samples: 50→300 (단일 설정 차이) | 12.9605 (-3.8789%) | 12.8148 (0.1042%) | 0.139965 / -0.2310%, 0.9694% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c186/result.json) |
| c187 / 완료 | c040 | colsample_bytree: 1.0→0.65; learning_rate: 0.055→0.04; min_child_samples: 200→300 (여러 설정 동시 변경) | 13.2171 (-1.1849%) | 12.2959 (-0.1066%) | 0.065021 / -0.0625%, 0.1444% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c187/result.json) |
| c188 / 완료 | c035 | n_estimators: 2000→1400; reg_lambda: 8.0→2.0 (여러 설정 동시 변경) | 15.9683 (5.6867%) | 15.5725 (1.4876%) | 0.020451 / -0.0205%, 0.1669% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c188/result.json) |
| c189 / 완료 | c025 | learning_rate: 0.07→0.015; min_child_samples: 50→300 (여러 설정 동시 변경) | 13.0567 (-0.7226%) | 12.3272 (-0.5364%) | 0.080814 / -0.0979%, 0.2833% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c189/result.json) |
| c190 / 완료 | c030 | learning_rate: 0.025→0.055; n_estimators: 2000→700; reg_lambda: 0.0→20.0 (여러 설정 동시 변경) | 13.2799 (0.8948%) | 12.8992 (0.7814%) | 0.047267 / -0.0467%, 0.1318% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c190/result.json) |
| c191 / 완료 | c003 | learning_rate: 0.03→0.015; n_estimators: 400→1400; num_leaves: 63→31; objective: regression_l1→regression_l2 (여러 설정 동시 변경) | 12.9021 (1.2833%) | 11.8771 (2.4059%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c191/result.json) |
| c192 / 완료 | c053 | colsample_bytree: 1.0→0.8; half_life: 없음→365; n_estimators: 700→1000 (여러 설정 동시 변경) | 13.1027 (0.9796%) | 12.2613 (2.0229%) | 0.090466 / -0.1193%, 0.4230% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c192/result.json) |
| c193 / 완료 | c050 | half_life: 180→365; num_leaves: 63→31; reg_lambda: 0.0→2.0 (여러 설정 동시 변경) | 13.5615 (-4.9050%) | 14.0115 (-4.4034%) | 0.081860 / -0.1214%, 0.8580% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c193/result.json) |
| c194 / 완료 | c179 | min_child_samples: 300→50; reg_lambda: 2.0→0.0 (여러 설정 동시 변경) | 13.5353 (0.0850%) | 12.6502 (1.3153%) | 0.023711 / -0.0112%, 0.0657% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c194/result.json) |
| c195 / 완료 | c020 | half_life: 90→365; num_leaves: 31→127 (여러 설정 동시 변경) | 13.6863 (-11.3647%) | 13.7863 (-11.9811%) | 0.077757 / -0.1363%, 0.7418% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c195/result.json) |
| c196 / 완료 | c009 | features: station→rich; half_life: 없음→90; n_estimators: 400→2000 (여러 설정 동시 변경) | 13.5472 (3.4288%) | 12.6969 (0.0428%) | 0.055260 / -0.0717%, 0.0917% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c196/result.json) |
| c197 / 완료 | c084 | learning_rate: 0.055→0.025; reg_lambda: 8.0→20.0 (여러 설정 동시 변경) | 13.8407 (0.4123%) | 13.7383 (-3.1869%) | 0.087484 / -0.1543%, 0.8582% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c197/result.json) |
| c198 / 완료 | c042 | half_life: 90→365; n_estimators: 1400→700; reg_lambda: 8.0→0.0 (여러 설정 동시 변경) | 12.9639 (-3.8860%) | 12.2297 (-1.9189%) | 0.086247 / -0.0845%, 0.3487% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c198/result.json) |
| c199 / 완료 | c135 | learning_rate: 0.04→0.07; num_leaves: 63→127 (여러 설정 동시 변경) | 13.4626 (1.3747%) | 13.3543 (-0.0334%) | 0.008338 / -0.0009%, 0.0416% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c199/result.json) |
| c200 / 완료 | c113 | half_life: 90→없음; min_child_samples: 100→300 (여러 설정 동시 변경) | 12.6788 (-6.4918%) | 11.9820 (-2.4673%) | 0.165494 / -0.2295%, 0.5611% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c200/result.json) |
| c201 / 완료 | c154 | min_child_samples: 50→100 (단일 설정 차이) | 13.6147 (-0.5692%) | 13.6948 (-0.6293%) | 0.030694 / -0.0163%, 0.2315% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c201/result.json) |
| c202 / 완료 | c008 | n_estimators: 400→2000; num_leaves: 127→31; reg_lambda: 20.0→2.0 (여러 설정 동시 변경) | 13.1945 (-0.1944%) | 12.1555 (-0.0401%) | 0.062977 / -0.0494%, 0.1471% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c202/result.json) |
| c203 / 완료 | c043 | learning_rate: 0.055→0.015; n_estimators: 400→1000 (여러 설정 동시 변경) | 13.3104 (-0.6242%) | 12.9709 (-0.4687%) | 0.072774 / -0.0788%, 0.4692% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c203/result.json) |
| c204 / 완료 | c012 | num_leaves: 127→31 (단일 설정 차이) | 13.2709 (0.9110%) | 12.2553 (2.2716%) | 0.031157 / -0.0112%, 0.0442% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c204/result.json) |
| c205 / 완료 | c020 | num_leaves: 31→127; reg_lambda: 20.0→2.0 (여러 설정 동시 변경) | 15.1406 (-1.9466%) | 15.4575 (-1.3112%) | 0.054041 / -0.1072%, 0.5684% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c205/result.json) |
| c206 / 완료 | c117 | n_estimators: 1400→700; target: exact_energy→original_cf; weighting: monetary→legacy (여러 설정 동시 변경) | 12.6211 (0.0513%) | 11.6277 (-3.1440%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c206/result.json) |
| c207 / 완료 | c103 | min_child_samples: 300→100 (단일 설정 차이) | 14.2341 (1.0225%) | 14.3486 (-0.0137%) | 0.003138 / -0.0002%, 0.0207% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c207/result.json) |
| c208 / 완료 | c033 | half_life: 365→90; num_leaves: 15→127 (여러 설정 동시 변경) | 15.4035 (11.5432%) | 15.5977 (11.4030%) | 0.047308 / -0.0994%, 0.4201% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c208/result.json) |
| c209 / 완료 | c196 | learning_rate: 0.07→0.025; n_estimators: 2000→1400 (여러 설정 동시 변경) | 13.3695 (-1.3124%) | 12.5866 (-0.8686%) | 0.062870 / -0.0820%, 0.1160% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c209/result.json) |
| c210 / 완료 | c013 | learning_rate: 0.025→0.04; n_estimators: 2000→700; num_leaves: 127→15 (여러 설정 동시 변경) | 14.2214 (-3.6534%) | 14.2566 (-1.1421%) | 0.062884 / -0.1047%, 0.5855% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c210/result.json) |
| c211 / 완료 | c008 | num_leaves: 127→15; reg_lambda: 20.0→2.0 (여러 설정 동시 변경) | 13.2327 (0.0944%) | 12.1628 (0.0202%) | 0.073595 / -0.0876%, 0.1385% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c211/result.json) |
| c212 / 완료 | c001 | learning_rate: 0.03→0.055; min_child_samples: 50→300; n_estimators: 400→700 (여러 설정 동시 변경) | 14.4599 (-0.2405%) | 15.2538 (4.4997%) | 0.066832 / -0.1307%, 0.9149% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c212/result.json) |
| c213 / 완료 | c027 | min_child_samples: 300→100; num_leaves: 15→63 (여러 설정 동시 변경) | 12.8563 (0.6881%) | 11.9840 (-1.7134%) | 0.020764 / -0.0035%, 0.0811% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c213/result.json) |
| c214 / 완료 | c022 | colsample_bytree: 0.65→1.0; min_child_samples: 50→200; n_estimators: 700→1400 (여러 설정 동시 변경) | 13.9119 (-2.8683%) | 14.3214 (2.6850%) | 0.051360 / -0.0588%, 0.4655% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c214/result.json) |
| c215 / 완료 | c029 | colsample_bytree: 0.65→0.8; num_leaves: 31→127; objective: regression_l1→regression_l2 (여러 설정 동시 변경) | 13.0863 (2.4305%) | 12.2461 (0.2770%) | 0.068346 / -0.0548%, 0.2812% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c215/result.json) |
| c216 / 완료 | c188 | colsample_bytree: 1.0→0.65; reg_lambda: 2.0→0.0 (여러 설정 동시 변경) | 17.0663 (6.8764%) | 15.4236 (-0.9562%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c216/result.json) |
| c217 / 완료 | c006 | min_child_samples: 200→300; reg_lambda: 8.0→2.0 (여러 설정 동시 변경) | 13.4666 (-1.5500%) | 12.4461 (-0.7354%) | 0.063033 / -0.0823%, 0.0964% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c217/result.json) |
| c218 / 완료 | c022 | learning_rate: 0.055→0.015; n_estimators: 700→2000; num_leaves: 127→31 (여러 설정 동시 변경) | 13.8592 (-3.2361%) | 13.8826 (-0.4613%) | 0.097987 / -0.1666%, 0.9452% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c218/result.json) |
| c219 / 완료 | c090 | features: station→rich; min_child_samples: 200→300 (여러 설정 동시 변경) | 13.0098 (-5.1806%) | 12.3065 (-9.0629%) | 0.139184 / -0.2398%, 0.6524% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c219/result.json) |
| c220 / 완료 | c216 | half_life: 90→180; reg_lambda: 0.0→20.0 (여러 설정 동시 변경) | 15.3200 (-10.2328%) | 14.7729 (-4.2190%) | 0.013031 / -0.0064%, 0.1117% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c220/result.json) |
| c221 / 완료 | c010 | n_estimators: 1000→400; reg_lambda: 2.0→0.0 (여러 설정 동시 변경) | 12.9456 (0.3639%) | 12.0189 (-0.0347%) | 0.105547 / -0.1146%, 0.3031% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c221/result.json) |
| c222 / 완료 | c000 | learning_rate: 0.03→0.07; n_estimators: 400→700; num_leaves: 63→15; reg_lambda: 0.0→8.0 (여러 설정 동시 변경) | 13.3220 (1.2270%) | 12.8662 (0.5030%) | 0.025724 / -0.0135%, 0.0985% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c222/result.json) |
| c223 / 완료 | c127 | n_estimators: 2000→1000; num_leaves: 127→15; reg_lambda: 0.0→20.0 (여러 설정 동시 변경) | 13.1062 (-2.1099%) | 12.0345 (0.4820%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c223/result.json) |
| c224 / 완료 | c085 | colsample_bytree: 0.8→1.0; min_child_samples: 50→300 (여러 설정 동시 변경) | 12.9965 (1.4363%) | 12.0112 (0.3877%) | 0.089898 / -0.0796%, 0.2478% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c224/result.json) |
| c225 / 완료 | c069 | min_child_samples: 200→50; n_estimators: 1000→700 (여러 설정 동시 변경) | 14.2261 (-2.2536%) | 14.2173 (-0.1524%) | 0.088420 / -0.1700%, 0.8590% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c225/result.json) |
| c226 / 완료 | c059 | n_estimators: 400→1000; num_leaves: 15→127 (여러 설정 동시 변경) | 13.2466 (0.6120%) | 11.8913 (-3.2080%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c226/result.json) |
| c227 / 완료 | c041 | learning_rate: 0.04→0.025; num_leaves: 127→15 (여러 설정 동시 변경) | 15.4185 (-2.0099%) | 15.4738 (-0.8803%) | 0.042752 / -0.0842%, 0.5071% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c227/result.json) |
| c228 / 완료 | c089 | half_life: 없음→180; min_child_samples: 300→50 (여러 설정 동시 변경) | 13.4593 (4.7017%) | 12.2274 (0.9603%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c228/result.json) |
| c229 / 완료 | c028 | half_life: 없음→365; n_estimators: 1400→1000; num_leaves: 15→63 (여러 설정 동시 변경) | 13.6521 (4.4121%) | 14.1393 (10.7845%) | 0.108786 / -0.2427%, 1.2931% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c229/result.json) |
| c230 / 완료 | c115 | learning_rate: 0.015→0.04; min_child_samples: 50→300; num_leaves: 63→31 (여러 설정 동시 변경) | 13.2260 (0.6486%) | 12.0496 (1.3681%) | 0.009961 / -0.0013%, 0.0081% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c230/result.json) |
| c231 / 완료 | c047 | min_child_samples: 100→300; num_leaves: 15→63 (여러 설정 동시 변경) | 14.8462 (2.1907%) | 14.9009 (-0.6598%) | 0.020876 / -0.0132%, 0.1608% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c231/result.json) |
| c232 / 완료 | c121 | half_life: 90→180; reg_lambda: 0.0→2.0 (여러 설정 동시 변경) | 13.2228 (-2.3712%) | 11.8991 (-2.9818%) | 0.006599 / -0.0006%, 0.0042% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c232/result.json) |
| c233 / 완료 | c013 | colsample_bytree: 1.0→0.8; half_life: 180→없음; min_child_samples: 100→50 (여러 설정 동시 변경) | 13.8455 (-6.2003%) | 13.1407 (-8.8795%) | 0.021917 / -0.0102%, 0.1157% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c233/result.json) |
| c234 / 완료 | c021 | reg_lambda: 8.0→20.0 (단일 설정 차이) | 12.9269 (0.5939%) | 12.1953 (0.5302%) | 0.133416 / -0.2299%, 0.4950% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c234/result.json) |
| c235 / 완료 | c178 | half_life: 90→없음; num_leaves: 31→15 (여러 설정 동시 변경) | 13.0062 (-14.9637%) | 12.9310 (-17.1793%) | 0.078702 / -0.1132%, 0.4957% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c235/result.json) |
| c236 / 완료 | c153 | half_life: 90→180; num_leaves: 63→15 (여러 설정 동시 변경) | 13.2444 (-2.3518%) | 12.4777 (-0.0720%) | 0.089673 / -0.1299%, 0.2289% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c236/result.json) |
| c237 / 완료 | c101 | colsample_bytree: 1.0→0.8; half_life: 365→90 (여러 설정 동시 변경) | 15.6329 (13.9817%) | 15.7692 (15.5991%) | 0.042056 / -0.0844%, 0.5259% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c237/result.json) |
| c238 / 완료 | c014 | learning_rate: 0.015→0.04; n_estimators: 1000→2000; num_leaves: 31→15; reg_lambda: 0.0→20.0 (여러 설정 동시 변경) | 13.2240 (1.1827%) | 12.1175 (0.4262%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c238/result.json) |
| c239 / 완료 | c143 | n_estimators: 400→1000; reg_lambda: 0.0→20.0 (여러 설정 동시 변경) | 14.1813 (0.1179%) | 14.2502 (-0.7849%) | 0.009601 / -0.0024%, 0.0662% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c239/result.json) |
| c240 / 완료 | c086 | min_child_samples: 200→100; n_estimators: 400→700; num_leaves: 31→63 (여러 설정 동시 변경) | 13.0658 (0.9728%) | 12.9442 (1.0427%) | 0.118544 / -0.1637%, 0.8721% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c240/result.json) |
| c241 / 완료 | c036 | min_child_samples: 200→50; num_leaves: 63→127; reg_lambda: 2.0→0.0 (여러 설정 동시 변경) | 12.8145 (0.4943%) | 11.8116 (-2.2284%) | 0.055528 / -0.0279%, 0.1381% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c241/result.json) |
| c242 / 완료 | c105 | n_estimators: 1400→2000 (단일 설정 차이) | 15.2479 (0.3876%) | 15.2830 (0.4344%) | 0.055003 / -0.1174%, 0.6190% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c242/result.json) |
| c243 / 완료 | c219 | colsample_bytree: 1.0→0.65; reg_lambda: 0.0→2.0 (여러 설정 동시 변경) | 12.8108 (-1.5295%) | 12.1407 (-1.3475%) | 0.123397 / -0.1548%, 0.5056% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c243/result.json) |
| c244 / 완료 | c133 | n_estimators: 1400→2000; num_leaves: 15→63 (여러 설정 동시 변경) | 13.2788 (1.5854%) | 13.1052 (0.4536%) | 0.079388 / -0.1229%, 0.5719% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c244/result.json) |
| c245 / 완료 | c074 | half_life: 없음→90; n_estimators: 400→700 (여러 설정 동시 변경) | 13.5292 (5.7728%) | 12.1294 (-0.2950%) | 0.009177 / -0.0010%, 0.0021% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c245/result.json) |
| c246 / 완료 | c036 | features: rich→station; learning_rate: 0.04→0.025 (여러 설정 동시 변경) | 13.1933 (3.4651%) | 13.0285 (7.8446%) | 0.086995 / -0.1246%, 0.6793% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c246/result.json) |
| c247 / 완료 | c196 | learning_rate: 0.07→0.055; n_estimators: 2000→700; objective: regression_l1→regression_l2 (여러 설정 동시 변경) | 13.5863 (0.2882%) | 12.9375 (1.8951%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c247/result.json) |
| c248 / 완료 | c139 | colsample_bytree: 0.65→1.0; learning_rate: 0.055→0.04 (여러 설정 동시 변경) | 13.1838 (-4.0706%) | 13.0057 (-1.8902%) | 0.071980 / -0.0760%, 0.4192% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c248/result.json) |
| c249 / 완료 | c010 | colsample_bytree: 0.8→0.65; half_life: 365→90; learning_rate: 0.015→0.055 (여러 설정 동시 변경) | 13.5697 (5.2026%) | 12.4944 (3.9196%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c249/result.json) |
| c250 / 완료 | c148 | half_life: 없음→180; min_child_samples: 200→100 (여러 설정 동시 변경) | 14.6060 (11.6706%) | 14.4812 (12.2400%) | 0.043129 / -0.0533%, 0.3920% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c250/result.json) |
| c251 / 완료 | c027 | learning_rate: 0.025→0.07; min_child_samples: 300→200; n_estimators: 1000→2000 (여러 설정 동시 변경) | 12.7307 (-0.2953%) | 12.2380 (0.3700%) | 0.149064 / -0.2438%, 0.7235% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c251/result.json) |
| c252 / 완료 | c109 | learning_rate: 0.025→0.04; n_estimators: 400→1400 (여러 설정 동시 변경) | 14.6327 (-1.5471%) | 15.8264 (4.2970%) | 0.056499 / -0.0957%, 0.7000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c252/result.json) |
| c253 / 완료 | c091 | min_child_samples: 100→50; num_leaves: 63→31 (여러 설정 동시 변경) | 13.3516 (1.2475%) | 12.0177 (1.3233%) | 0.006536 / -0.0001%, 0.0044% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c253/result.json) |
| c254 / 완료 | c062 | colsample_bytree: 0.65→0.8; learning_rate: 0.04→0.025; n_estimators: 2000→400 (여러 설정 동시 변경) | 14.6016 (0.3043%) | 14.5607 (-1.6426%) | 0.046939 / -0.0668%, 0.3867% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c254/result.json) |
| c255 / 완료 | c031 | colsample_bytree: 1.0→0.8; half_life: 90→180; num_leaves: 63→31; reg_lambda: 0.0→20.0 (여러 설정 동시 변경) | 13.1163 (-3.1568%) | 12.0265 (-4.0345%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_10h_20261107/trials/c255/result.json) |

## 12시간 연장 단계

| ID / 상태 | 기초 / 비교 ID | 바뀐 설정 | primary W_pct (W 변화) | recent W_pct (W 변화) | alpha / 최고 제출 대비 혼합 W 변화 primary, recent | 완료 기간 / 학습 횟수 | 비고·근거 |
|---|---|---|---:|---:|---|---|---|
| n0000 / 완료 | b00→c206 / n0000 | 변경 없음(비교 기준 자체) (기준 자체) | 12.7225 (0.0000%) | 11.6269 (0.0000%) | 0.012241 / -0.0015%, 0.0245% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0000/result.json) |
| n0001 / 완료 | b00→c206 / n0000 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | 12.6843 (-0.2997%) | 11.6278 (0.0071%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0001/result.json) |
| n0002 / 완료 | b00→c206 / n0000 | half_life: 없음→365 (단일 설정 차이) | 12.6942 (-0.2218%) | 11.6419 (0.1288%) | 0.009839 / -0.0008%, 0.0222% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0002/result.json) |
| n0003 / 완료 | b00→c206 / n0001 | half_life: 없음→365 (단일 설정 차이) | 12.6677 (-0.1309%) | 11.6327 (0.0422%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0003/result.json) |
| n0004 / 완료 | b00→c206 / n0002 | bound: 0.2→0.3; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→1000; n_estimators: 0→160; num_leaves: 0→7; reg_lambda: 0.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.6669 (-0.2156%) | 11.4840 (-1.3561%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0004/result.json) |
| n0005 / 완료 | b00→c206 / n0004 | features: core→season; half_life: 365→없음; min_child_samples: 1000→500; mode: additive→multiplicative; num_leaves: 7→15; reg_lambda: 2.0→10.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.6100 (7.4457%) | 11.7427 (2.2529%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0005/result.json) |
| n0006 / 완료 | b00→c206 / n0004 | features: core→age; half_life: 365→180; learning_rate: 0.025→0.05; n_estimators: 160→300; num_leaves: 7→3; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 12.6417 (-0.1984%) | 11.4728 (-0.0976%) | 0.011100 / -0.0003%, 0.0148% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0006/result.json) |
| n0007 / 완료 | b00→c206 / n0004 | bound: 0.3→0.15; learning_rate: 0.025→0.05; mode: additive→multiplicative; n_estimators: 160→80; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.1894 (4.1254%) | 11.4889 (0.0428%) | 0.024354 / -0.0073%, 0.0050% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0007/result.json) |
| n0008 / 완료 | b00→c206 / n0006 | bound: 0.3→0.2; features: age→season; min_child_samples: 1000→200; num_leaves: 3→7; shrink: 0.25→1.0 (여러 설정 동시 변경) | 14.0337 (11.0107%) | 11.5724 (0.8678%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0008/result.json) |
| n0009 / 완료 | b00→c206 / n0006 | bound: 0.3→0.15; mode: additive→multiplicative; n_estimators: 300→160; num_leaves: 3→7; shrink: 0.25→0.5 (여러 설정 동시 변경) | 12.8878 (1.9465%) | 11.4558 (-0.1487%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0009/result.json) |
| n0010 / 완료 | b00→c206 / n0004 | bound: 0.3→0.1; half_life: 365→180; min_child_samples: 1000→500; n_estimators: 160→80; num_leaves: 7→15 (여러 설정 동시 변경) | 12.6690 (0.0167%) | 11.5023 (0.1593%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0010/result.json) |
| n0011 / 완료 | b00→c206 / n0008 | bound: 0.2→0.15; learning_rate: 0.05→0.025; mode: additive→multiplicative; num_leaves: 7→3; reg_lambda: 30.0→2.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.7344 (-9.2586%) | 11.4448 (-1.1028%) | 0.010032 / -0.0003%, 0.0129% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0011/result.json) |
| n0012 / 완료 | b00→c206 / n0004 | bound: 0.3→0.2; features: core→age; reg_lambda: 2.0→10.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.4632 (6.2870%) | 11.4842 (0.0018%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0012/result.json) |
| n0013 / 완료 | b00→c206 / n0005 | bound: 0.3→0.15; features: season→core; num_leaves: 15→3; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.7084 (-6.6249%) | 11.5162 (-1.9295%) | 0.016360 / -0.0020%, 0.0262% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0013/result.json) |
| n0014 / 완료 | b00→c206 / n0008 | half_life: 180→없음; learning_rate: 0.05→0.025; min_child_samples: 200→500; n_estimators: 300→80; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.6646 (-9.7558%) | 11.5531 (-0.1665%) | 0.009547 / -0.0002%, 0.0167% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0014/result.json) |
| n0015 / 완료 | b00→c206 / n0011 | features: season→age; half_life: 180→365; n_estimators: 300→160; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.6515 (-0.6505%) | 11.5368 (0.8046%) | 0.005388 / -0.0001%, 0.0096% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0015/result.json) |
| n0016 / 완료 | b00→c206 / n0011 | bound: 0.15→0.1; features: season→core; mode: multiplicative→additive; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 12.7294 (-0.0386%) | 11.3936 (-0.4468%) | 0.010655 / -0.0003%, 0.0050% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0016/result.json) |
| n0017 / 완료 | b00→c206 / n0006 | features: age→season; half_life: 180→365; mode: additive→multiplicative; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | 12.6399 (-0.0147%) | 11.5010 (0.2452%) | 0.011342 / -0.0009%, 0.0181% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0017/result.json) |
| n0018 / 완료 | b00→c206 / n0012 | bound: 0.2→0.1; learning_rate: 0.025→0.05; min_child_samples: 1000→200; n_estimators: 160→80; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.8229 (-4.7562%) | 11.4369 (-0.4119%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0018/result.json) |
| n0019 / 완료 | b00→c206 / n0004 | bound: 0.3→0.5; half_life: 365→180; mode: additive→multiplicative; num_leaves: 7→15; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 12.6947 (0.2199%) | 11.4562 (-0.2424%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0019/result.json) |
| n0020 / 완료 | b00→c206 / n0012 | features: age→season; learning_rate: 0.025→0.05; min_child_samples: 1000→500; num_leaves: 7→3; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.7876 (-5.0187%) | 11.4431 (-0.3583%) | 0.012589 / -0.0006%, 0.0137% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0020/result.json) |
| n0021 / 완료 | b00→c206 / n0018 | bound: 0.1→0.5; mode: additive→multiplicative; n_estimators: 80→300; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.7509 (7.2373%) | 11.8057 (3.2242%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0021/result.json) |
| n0022 / 완료 | b00→c206 / n0004 | bound: 0.3→0.1; n_estimators: 160→300; num_leaves: 7→15; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 12.6815 (0.1156%) | 11.4472 (-0.3206%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0022/result.json) |
| n0023 / 완료 | b00→c206 / n0007 | features: core→season; min_child_samples: 1000→500; n_estimators: 80→160; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.8379 (-2.6648%) | 11.4690 (-0.1732%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0023/result.json) |
| n0024 / 완료 | b00→c206 / n0008 | features: season→age; learning_rate: 0.05→0.025; reg_lambda: 30.0→10.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.6879 (-9.5893%) | 11.4729 (-0.8599%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0024/result.json) |
| n0025 / 완료 | b00→c206 / n0013 | learning_rate: 0.025→0.05; n_estimators: 160→80; num_leaves: 3→7 (여러 설정 동시 변경) | 12.7243 (0.1256%) | 11.4925 (-0.2057%) | 0.031604 / -0.0063%, 0.0473% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0025/result.json) |
| n0026 / 완료 | b00→c206 / n0008 | bound: 0.2→0.3; half_life: 180→없음; n_estimators: 300→80; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.8112 (-8.7111%) | 11.5076 (-0.5597%) | 0.019506 / -0.0029%, 0.0295% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0026/result.json) |
| n0027 / 완료 | b00→c206 / n0021 | bound: 0.5→0.15; half_life: 365→없음; learning_rate: 0.05→0.025; n_estimators: 300→80 (여러 설정 동시 변경) | 13.0410 (-5.1626%) | 11.5462 (-2.1983%) | 0.020699 / -0.0039%, 0.0390% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0027/result.json) |
| n0028 / 완료 | b00→c206 / n0020 | features: season→core; min_child_samples: 500→200; reg_lambda: 10.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.0816 (2.2992%) | 11.3657 (-0.6764%) | 0.022132 / -0.0065%, -0.0126% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0028/result.json) |
| n0029 / 완료 | b00→c206 / n0011 | n_estimators: 300→160; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.6597 (-0.5861%) | 11.5282 (0.7294%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0029/result.json) |
| n0030 / 완료 | b00→c206 / n0013 | bound: 0.15→0.2; features: core→age; mode: multiplicative→additive; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | 12.7255 (0.1348%) | 11.4986 (-0.1529%) | 0.017201 / -0.0022%, 0.0253% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0030/result.json) |
| n0031 / 완료 | b00→c206 / n0007 | bound: 0.15→0.5; n_estimators: 80→160 (여러 설정 동시 변경) | 13.4117 (1.6854%) | 11.5541 (0.5673%) | 0.010833 / -0.0011%, -0.0088% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0031/result.json) |
| n0032 / 완료 | b00→c206 / n0006 | features: age→season; learning_rate: 0.05→0.025; min_child_samples: 1000→200; num_leaves: 3→15 (여러 설정 동시 변경) | 12.7626 (0.9560%) | 11.5007 (0.2432%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0032/result.json) |
| n0033 / 완료 | b00→c206 / n0007 | features: core→age; half_life: 365→180; min_child_samples: 1000→200; num_leaves: 7→3 (여러 설정 동시 변경) | 12.9580 (-1.7546%) | 11.4491 (-0.3468%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0033/result.json) |
| n0034 / 완료 | b00→c206 / n0028 | min_child_samples: 200→500; num_leaves: 3→15; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.2965 (1.6434%) | 11.4679 (0.8994%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0034/result.json) |
| n0035 / 완료 | b00→c206 / n0029 | bound: 0.15→0.3; min_child_samples: 200→1000 (여러 설정 동시 변경) | 12.6624 (0.0212%) | 11.5309 (0.0227%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0035/result.json) |
| n0036 / 완료 | b00→c206 / n0034 | features: core→age; n_estimators: 160→80; num_leaves: 15→3 (여러 설정 동시 변경) | 12.8328 (-3.4878%) | 11.4361 (-0.2777%) | 0.023379 / -0.0048%, 0.0240% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0036/result.json) |
| n0037 / 완료 | b00→c206 / n0025 | num_leaves: 7→3; reg_lambda: 10.0→2.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | 12.8147 (0.7105%) | 11.5100 (0.1522%) | 0.014332 / -0.0018%, 0.0223% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0037/result.json) |
| n0038 / 완료 | b00→c206 / n0026 | n_estimators: 80→160; num_leaves: 7→15; reg_lambda: 30.0→2.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.4348 (4.8674%) | 11.6615 (1.3371%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0038/result.json) |
| n0039 / 완료 | b00→c206 / n0009 | bound: 0.15→0.3; min_child_samples: 1000→500; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 12.8751 (-0.0988%) | 11.4428 (-0.1135%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0039/result.json) |
| n0040 / 완료 | b00→c206 / n0020 | features: season→core; half_life: 365→180; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 12.7481 (-0.3083%) | 11.3786 (-0.5634%) | 0.001036 / -0.0000%, 0.0003% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0040/result.json) |
| n0041 / 완료 | b00→c206 / n0005 | bound: 0.3→0.15; half_life: 없음→180; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 13.6161 (0.0446%) | 11.6371 (-0.8999%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0041/result.json) |
| n0042 / 완료 | b00→c206 / n0018 | bound: 0.1→0.2; n_estimators: 80→300; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | 13.0049 (1.4190%) | 11.4542 (0.1513%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0042/result.json) |
| n0043 / 완료 | b00→c206 / n0037 | bound: 0.15→0.3; half_life: 없음→365; shrink: 0.75→0.25 (여러 설정 동시 변경) | 12.6501 (-1.2844%) | 11.5480 (0.3303%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0043/result.json) |
| n0044 / 완료 | b00→c206 / n0008 | bound: 0.2→0.1; min_child_samples: 200→500; n_estimators: 300→160; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.6919 (-9.5614%) | 11.4581 (-0.9875%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0044/result.json) |
| n0045 / 완료 | b00→c206 / n0021 | learning_rate: 0.05→0.025; min_child_samples: 200→500; n_estimators: 300→80; num_leaves: 7→3 (여러 설정 동시 변경) | 12.8617 (-6.4669%) | 11.4604 (-2.9242%) | 0.005365 / -0.0001%, 0.0073% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0045/result.json) |
| n0046 / 완료 | b00→c206 / n0022 | min_child_samples: 1000→200; reg_lambda: 10.0→30.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.6175 (7.3811%) | 11.5622 (1.0041%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0046/result.json) |
| n0047 / 완료 | b00→c206 / n0026 | min_child_samples: 200→1000; mode: additive→multiplicative; num_leaves: 7→15 (여러 설정 동시 변경) | 12.8859 (0.5832%) | 11.5381 (0.2647%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0047/result.json) |
| n0048 / 완료 | b00→c206 / n0006 | bound: 0.3→0.1; half_life: 180→없음; n_estimators: 300→160; reg_lambda: 30.0→10.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | 12.9446 (2.3958%) | 11.4662 (-0.0576%) | 0.026809 / -0.0059%, 0.0310% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0048/result.json) |
| n0049 / 완료 | b00→c206 / n0007 | num_leaves: 7→3; reg_lambda: 2.0→30.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | 12.7858 (-3.0604%) | 11.4716 (-0.1509%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0049/result.json) |
| n0050 / 완료 | b00→c206 / n0008 | half_life: 180→365; n_estimators: 300→80; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.6764 (-9.6716%) | 11.5024 (-0.6044%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0050/result.json) |
| n0051 / 완료 | b00→c206 / n0021 | bound: 0.5→0.3; num_leaves: 7→3; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | 13.1572 (-4.3176%) | 11.5657 (-2.0329%) | 0.011732 / -0.0011%, 0.0006% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0051/result.json) |
| n0052 / 완료 | b00→c206 / n0022 | bound: 0.1→0.2; min_child_samples: 1000→500 (여러 설정 동시 변경) | 12.6763 (-0.0415%) | 11.4706 (0.2044%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0052/result.json) |
| n0053 / 완료 | b00→c206 / n0035 | half_life: 180→없음; num_leaves: 3→7; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 12.6528 (-0.0757%) | 11.5419 (0.0953%) | 0.009640 / -0.0005%, 0.0176% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0053/result.json) |
| n0054 / 완료 | b00→c206 / n0006 | min_child_samples: 1000→200; n_estimators: 300→80; num_leaves: 3→7; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 12.6690 (0.2154%) | 11.4959 (0.2013%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0054/result.json) |
| n0055 / 완료 | b00→c206 / n0038 | features: season→core; mode: additive→multiplicative (여러 설정 동시 변경) | 13.1212 (-2.3341%) | 11.5926 (-0.5905%) | 0.018493 / -0.0046%, 0.0194% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0055/result.json) |
| n0056 / 완료 | b00→c206 / n0020 | min_child_samples: 500→1000; n_estimators: 160→300; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | 12.8288 (0.3222%) | 11.4511 (0.0702%) | 0.009414 / -0.0004%, 0.0100% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0056/result.json) |
| n0057 / 완료 | b00→c206 / n0039 | reg_lambda: 2.0→2.5; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.2337 (2.7851%) | 11.5003 (0.5028%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0057/result.json) |
| n0058 / 완료 | b00→c206 / n0010 | n_estimators: 80→160; num_leaves: 15→7; shrink: 0.25→0.75 (여러 설정 동시 변경) | 12.9673 (2.3550%) | 11.3255 (-1.5375%) | 0.000834 / -0.0000%, -0.0006% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0058/result.json) |
| n0059 / 완료 | b00→c206 / n0035 | reg_lambda: 2.0→10.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | 12.8642 (1.5940%) | 11.4446 (-0.7484%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0059/result.json) |
| n0060 / 완료 | b00→c206 / n0036 | min_child_samples: 500→200; n_estimators: 80→300; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 13.0241 (1.4907%) | 11.4633 (0.2383%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0060/result.json) |
| n0061 / 완료 | b00→c206 / n0017 | features: season→core; learning_rate: 0.05→0.025; shrink: 0.25→1.0 (여러 설정 동시 변경) | 12.9491 (2.4466%) | 11.4310 (-0.6083%) | 0.015147 / -0.0026%, 0.0039% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0061/result.json) |
| n0062 / 완료 | b00→c206 / n0022 | features: core→season; num_leaves: 15→7; shrink: 0.25→0.5 (여러 설정 동시 변경) | 12.9094 (1.7967%) | 11.4463 (-0.0079%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0062/result.json) |
| n0063 / 완료 | b00→c206 / n0009 | reg_lambda: 30.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.5565 (5.1888%) | 11.6577 (1.7632%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0063/result.json) |
| n0064 / 완료 | b01→c003 / n0064 | 변경 없음(비교 기준 자체) (기준 자체) | 12.8426 (0.0000%) | 11.6215 (0.0000%) | 0.008161 / -0.0003%, 0.0113% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0064/result.json) |
| n0065 / 완료 | b01→c003 / n0064 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | 12.8139 (-0.2239%) | 11.6224 (0.0070%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0065/result.json) |
| n0066 / 완료 | b01→c003 / n0064 | half_life: 없음→365 (단일 설정 차이) | 12.8020 (-0.3166%) | 11.6600 (0.3310%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0066/result.json) |
| n0067 / 완료 | b01→c003 / n0065 | half_life: 없음→365 (단일 설정 차이) | 12.7891 (-0.1935%) | 11.6508 (0.2449%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0067/result.json) |
| n0068 / 완료 | b01→c003 / n0064 | bound: 0.2→0.3; half_life: 없음→180; learning_rate: 0.0→0.05; method: median→tree; min_child_samples: 0→500; n_estimators: 0→300; num_leaves: 0→7; reg_lambda: 0.0→30.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.8681 (0.1987%) | 11.5509 (-0.6079%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0068/result.json) |
| n0069 / 완료 | b01→c003 / n0065 | bound: 0.3→0.5; features: core→season; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→200; n_estimators: 0→80; num_leaves: 0→15; reg_lambda: 0.0→10.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.1997 (3.0111%) | 11.7602 (1.1859%) | 0.005284 / -0.0000%, 0.0062% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0069/result.json) |
| n0070 / 완료 | b01→c003 / n0068 | features: core→age; half_life: 180→365; min_child_samples: 500→1000; n_estimators: 300→160; num_leaves: 7→3; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.2750 (3.1621%) | 11.7285 (1.5372%) | 0.027662 / -0.0097%, -0.0065% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0070/result.json) |
| n0071 / 완료 | b01→c003 / n0068 | half_life: 180→365; mode: additive→multiplicative; n_estimators: 300→160; num_leaves: 7→15; reg_lambda: 30.0→2.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.4919 (4.8478%) | 11.7825 (2.0051%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0071/result.json) |
| n0072 / 완료 | b01→c003 / n0068 | bound: 0.3→0.1; features: core→season; half_life: 180→없음; n_estimators: 300→80; num_leaves: 7→3; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | 12.8149 (-0.4136%) | 11.5811 (0.2615%) | 0.011632 / -0.0008%, 0.0100% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0072/result.json) |
| n0073 / 완료 | b01→c003 / n0070 | bound: 0.3→0.5; min_child_samples: 1000→500; mode: additive→multiplicative; n_estimators: 160→80; num_leaves: 3→7 (여러 설정 동시 변경) | 13.3682 (0.7021%) | 11.9206 (1.6384%) | 0.005612 / -0.0002%, 0.0036% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0073/result.json) |
| n0074 / 완료 | b01→c003 / n0068 | half_life: 180→없음; n_estimators: 300→160; reg_lambda: 30.0→2.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.8692 (7.7798%) | 11.8400 (2.5033%) | 0.016588 / -0.0052%, -0.0012% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0074/result.json) |
| n0075 / 완료 | b01→c003 / n0071 | bound: 0.3→0.15; features: core→season; learning_rate: 0.05→0.025; min_child_samples: 500→1000; shrink: 0.75→1.0 (여러 설정 동시 변경) | 13.9463 (3.3675%) | 11.9374 (1.3145%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0075/result.json) |
| n0076 / 완료 | b01→c003 / n0068 | bound: 0.3→0.1; features: core→age; half_life: 180→없음; min_child_samples: 500→200; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.7883 (7.1508%) | 11.9312 (3.2928%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0076/result.json) |
| n0077 / 완료 | b01→c003 / n0073 | features: age→core; num_leaves: 7→3 (여러 설정 동시 변경) | 13.0915 (-2.0705%) | 11.7052 (-1.8070%) | 0.022500 / -0.0048%, 0.0218% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0077/result.json) |
| n0078 / 완료 | b01→c003 / n0071 | bound: 0.3→0.2; features: core→season; half_life: 365→180; mode: multiplicative→additive; num_leaves: 15→3 (여러 설정 동시 변경) | 13.0465 (-3.3015%) | 11.6044 (-1.5114%) | 0.030470 / -0.0088%, -0.0226% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0078/result.json) |
| n0079 / 완료 | b01→c003 / n0068 | features: core→age; learning_rate: 0.05→0.025; mode: additive→multiplicative; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 12.8484 (-0.1532%) | 11.5901 (0.3394%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0079/result.json) |
| n0080 / 완료 | b01→c003 / n0074 | learning_rate: 0.05→0.025; min_child_samples: 500→1000; n_estimators: 160→300; num_leaves: 7→15; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 14.1152 (1.7735%) | 11.9969 (1.3250%) | 0.010783 / -0.0020%, 0.0043% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0080/result.json) |
| n0081 / 완료 | b01→c003 / n0069 | bound: 0.5→0.15; min_child_samples: 200→1000; num_leaves: 15→7; shrink: 0.75→1.0 (여러 설정 동시 변경) | 13.3310 (0.9946%) | 11.8020 (0.3554%) | 0.030458 / -0.0108%, 0.0480% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0081/result.json) |
| n0082 / 완료 | b01→c003 / n0074 | bound: 0.3→0.2; features: core→age; n_estimators: 160→80 (여러 설정 동시 변경) | 13.6179 (-1.8119%) | 11.7718 (-0.5766%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0082/result.json) |
| n0083 / 완료 | b01→c003 / n0079 | features: age→core; min_child_samples: 500→200; num_leaves: 7→3; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.0141 (1.2893%) | 11.6331 (0.3708%) | 0.010398 / -0.0005%, -0.0016% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0083/result.json) |
| n0084 / 완료 | b01→c003 / n0068 | bound: 0.3→0.2; features: core→season; learning_rate: 0.05→0.025; min_child_samples: 500→1000; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | 12.8799 (0.0914%) | 11.5838 (0.2853%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0084/result.json) |
| n0085 / 완료 | b01→c003 / n0079 | half_life: 180→365; min_child_samples: 500→1000; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 12.8278 (-0.1607%) | 11.6105 (0.1764%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0085/result.json) |
| n0086 / 완료 | b01→c003 / n0070 | bound: 0.3→0.2; features: age→core; half_life: 365→없음; learning_rate: 0.05→0.025; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.8114 (-3.4923%) | 11.5740 (-1.3173%) | 0.010563 / -0.0004%, 0.0081% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0086/result.json) |
| n0087 / 완료 | b01→c003 / n0075 | bound: 0.15→0.5; learning_rate: 0.025→0.05; num_leaves: 15→7; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.8667 (-7.7411%) | 11.6076 (-2.7629%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0087/result.json) |
| n0088 / 완료 | b01→c003 / n0085 | bound: 0.3→0.1; min_child_samples: 1000→500; mode: multiplicative→additive; n_estimators: 300→160 (여러 설정 동시 변경) | 12.8383 (0.0820%) | 11.5948 (-0.1358%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0088/result.json) |
| n0089 / 완료 | b01→c003 / n0083 | bound: 0.3→0.5; num_leaves: 3→15 (여러 설정 동시 변경) | 13.4620 (3.4416%) | 11.7409 (0.9268%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0089/result.json) |
| n0090 / 완료 | b01→c003 / n0070 | features: age→season; learning_rate: 0.05→0.025; n_estimators: 160→300 (여러 설정 동시 변경) | 13.3425 (0.5082%) | 11.6867 (-0.3561%) | 0.026336 / -0.0106%, -0.0093% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0090/result.json) |
| n0091 / 완료 | b01→c003 / n0073 | learning_rate: 0.05→0.025; min_child_samples: 500→1000; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.8870 (-3.5997%) | 11.6584 (-2.1996%) | 0.011468 / -0.0005%, 0.0129% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0091/result.json) |
| n0092 / 완료 | b01→c003 / n0078 | features: season→core; learning_rate: 0.05→0.025; num_leaves: 3→15; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 13.4227 (2.8834%) | 11.6885 (0.7245%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0092/result.json) |
| n0093 / 완료 | b01→c003 / n0081 | half_life: 없음→365; learning_rate: 0.025→0.05; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.8294 (-3.7621%) | 11.6026 (-1.6895%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0093/result.json) |
| n0094 / 완료 | b01→c003 / n0076 | bound: 0.1→0.2; learning_rate: 0.05→0.025; min_child_samples: 200→1000; shrink: 1.0→0.5 (여러 설정 동시 변경) | 13.0537 (-5.3279%) | 11.6406 (-2.4356%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0094/result.json) |
| n0095 / 완료 | b01→c003 / n0068 | min_child_samples: 500→1000; mode: additive→multiplicative; num_leaves: 7→15; shrink: 0.25→0.5 (여러 설정 동시 변경) | 13.2242 (2.7672%) | 11.7016 (1.3044%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0095/result.json) |
| n0096 / 완료 | b01→c003 / n0075 | bound: 0.15→0.1; min_child_samples: 1000→200; mode: multiplicative→additive; n_estimators: 160→80; num_leaves: 15→7 (여러 설정 동시 변경) | 13.3560 (-4.2324%) | 11.6989 (-1.9977%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0096/result.json) |
| n0097 / 완료 | b01→c003 / n0073 | bound: 0.5→0.15; reg_lambda: 30.0→30.5; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.8207 (-4.0955%) | 11.6185 (-2.5342%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0097/result.json) |
| n0098 / 완료 | b01→c003 / n0082 | features: age→core; min_child_samples: 500→1000; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.3827 (-1.7277%) | 11.6448 (-1.0791%) | 0.014300 / -0.0022%, 0.0013% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0098/result.json) |
| n0099 / 완료 | b01→c003 / n0093 | reg_lambda: 10.0→2.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.4600 (4.9146%) | 11.8144 (1.8254%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0099/result.json) |
| n0100 / 완료 | b01→c003 / n0070 | min_child_samples: 1000→200; n_estimators: 160→80; shrink: 1.0→0.75 (여러 설정 동시 변경) | 12.9702 (-2.2965%) | 11.6076 (-1.0306%) | 0.017502 / -0.0021%, 0.0064% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0100/result.json) |
| n0101 / 완료 | b01→c003 / n0087 | bound: 0.5→0.3; features: season→core; n_estimators: 160→80 (여러 설정 동시 변경) | 12.8200 (-0.3627%) | 11.5848 (-0.1957%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0101/result.json) |
| n0102 / 완료 | b01→c003 / n0096 | min_child_samples: 200→500; n_estimators: 80→300; num_leaves: 7→15 (여러 설정 동시 변경) | 14.1737 (6.1225%) | 12.0496 (2.9976%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0102/result.json) |
| n0103 / 완료 | b01→c003 / n0079 | half_life: 180→365; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 12.8294 (-0.1481%) | 11.6062 (0.1389%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0103/result.json) |
| n0104 / 완료 | b01→c003 / n0088 | bound: 0.1→0.3; features: age→core (여러 설정 동시 변경) | 12.8420 (0.0289%) | 11.5715 (-0.2005%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0104/result.json) |
| n0105 / 완료 | b01→c003 / n0069 | min_child_samples: 200→500; n_estimators: 80→300 (여러 설정 동시 변경) | 13.5398 (2.5765%) | 11.9133 (1.3023%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0105/result.json) |
| n0106 / 완료 | b01→c003 / n0088 | half_life: 365→180; min_child_samples: 500→200; reg_lambda: 30.0→2.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.2534 (3.2333%) | 11.6583 (0.5479%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0106/result.json) |
| n0107 / 완료 | b01→c003 / n0077 | learning_rate: 0.05→0.025; n_estimators: 80→300; num_leaves: 3→15 (여러 설정 동시 변경) | 13.9083 (6.2397%) | 11.9737 (2.2941%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0107/result.json) |
| n0108 / 완료 | b01→c003 / n0070 | features: age→season; half_life: 365→180; min_child_samples: 1000→200; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.9013 (-2.8150%) | 11.5645 (-1.3979%) | 0.007789 / -0.0002%, -0.0013% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0108/result.json) |
| n0109 / 완료 | b01→c003 / n0091 | bound: 0.5→0.3; half_life: 365→없음; num_leaves: 7→3 (여러 설정 동시 변경) | 12.8061 (-0.6282%) | 11.6381 (-0.1740%) | 0.028464 / -0.0053%, 0.0440% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0109/result.json) |
| n0110 / 완료 | b01→c003 / n0083 | learning_rate: 0.025→0.05; mode: multiplicative→additive; n_estimators: 300→80 (여러 설정 동시 변경) | 12.9401 (-0.5684%) | 11.5424 (-0.7793%) | 0.017673 / -0.0016%, -0.0071% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0110/result.json) |
| n0111 / 완료 | b01→c003 / n0089 | features: core→season; min_child_samples: 200→1000 (여러 설정 동시 변경) | 13.7634 (2.2390%) | 11.7703 (0.2507%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0111/result.json) |
| n0112 / 완료 | b01→c003 / n0086 | features: core→age; half_life: 없음→180; min_child_samples: 1000→500; n_estimators: 160→80 (여러 설정 동시 변경) | 12.7632 (-0.3764%) | 11.5801 (0.0536%) | 0.010259 / -0.0004%, 0.0091% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0112/result.json) |
| n0113 / 완료 | b01→c003 / n0081 | features: season→core; half_life: 없음→180; num_leaves: 7→15; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.8341 (-3.7272%) | 11.5833 (-1.8530%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0113/result.json) |
| n0114 / 완료 | b01→c003 / n0084 | bound: 0.2→0.1; reg_lambda: 10.0→10.5; shrink: 0.25→1.0 (여러 설정 동시 변경) | 14.0561 (9.1325%) | 11.9357 (3.0371%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0114/result.json) |
| n0115 / 완료 | b01→c003 / n0073 | half_life: 365→없음; n_estimators: 80→300; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 13.7112 (2.5656%) | 11.9769 (0.4723%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0115/result.json) |
| n0116 / 완료 | b01→c003 / n0080 | learning_rate: 0.025→0.05; n_estimators: 300→80; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 13.9726 (-1.0102%) | 11.8658 (-1.0926%) | 0.017413 / -0.0101%, 0.0026% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0116/result.json) |
| n0117 / 완료 | b01→c003 / n0105 | learning_rate: 0.025→0.05; shrink: 0.75→1.0 (여러 설정 동시 변경) | 14.3289 (5.8281%) | 12.3122 (3.3479%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0117/result.json) |
| n0118 / 완료 | b01→c003 / n0108 | bound: 0.3→0.2; features: season→age; half_life: 180→없음 (여러 설정 동시 변경) | 12.9219 (0.1597%) | 11.6391 (0.6450%) | 0.012094 / -0.0008%, 0.0111% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0118/result.json) |
| n0119 / 완료 | b01→c003 / n0113 | bound: 0.15→0.3; n_estimators: 80→160; num_leaves: 15→7 (여러 설정 동시 변경) | 12.8197 (-0.1121%) | 11.5719 (-0.0980%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0119/result.json) |
| n0120 / 완료 | b01→c003 / n0080 | features: core→season; min_child_samples: 1000→200; shrink: 1.0→0.5 (여러 설정 동시 변경) | 13.1540 (-6.8097%) | 11.7298 (-2.2268%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0120/result.json) |
| n0121 / 완료 | b01→c003 / n0087 | bound: 0.5→0.15; features: season→age; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.2808 (3.2182%) | 11.8015 (1.6710%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0121/result.json) |
| n0122 / 완료 | b01→c003 / n0092 | bound: 0.2→0.1; n_estimators: 160→300; num_leaves: 15→3 (여러 설정 동시 변경) | 13.0463 (-2.8044%) | 11.5375 (-1.2914%) | 0.020165 / -0.0044%, -0.0230% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0122/result.json) |
| n0123 / 완료 | b01→c003 / n0104 | features: core→season; half_life: 365→없음; mode: additive→multiplicative (여러 설정 동시 변경) | 12.8303 (-0.0912%) | 11.6294 (0.5002%) | 0.003962 / -0.0000%, 0.0043% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0123/result.json) |
| n0124 / 완료 | b01→c003 / n0109 | mode: multiplicative→additive; reg_lambda: 30.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.7763 (-0.2324%) | 11.5982 (-0.3426%) | 0.005787 / -0.0001%, 0.0063% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0124/result.json) |
| n0125 / 완료 | b01→c003 / n0071 | bound: 0.3→0.15; half_life: 365→180; min_child_samples: 500→200; shrink: 0.75→0.5 (여러 설정 동시 변경) | 13.0988 (-2.9137%) | 11.6264 (-1.3246%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0125/result.json) |
| n0126 / 완료 | b01→c003 / n0087 | bound: 0.5→0.1; min_child_samples: 1000→200; mode: multiplicative→additive (여러 설정 동시 변경) | 12.8520 (-0.1146%) | 11.6104 (0.0248%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0126/result.json) |
| n0127 / 완료 | b01→c003 / n0073 | bound: 0.5→0.15; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | 13.3794 (0.0832%) | 11.9368 (0.1356%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0127/result.json) |
| n0128 / 완료 | b02→c158 / n0128 | 변경 없음(비교 기준 자체) (기준 자체) | 12.9058 (0.0000%) | 11.9114 (0.0000%) | 0.035001 / -0.0117%, 0.0222% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0128/result.json) |
| n0129 / 완료 | b02→c158 / n0128 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | 12.9753 (0.5380%) | 11.9596 (0.4044%) | 0.019844 / -0.0044%, 0.0208% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0129/result.json) |
| n0130 / 완료 | b02→c158 / n0128 | half_life: 없음→365 (단일 설정 차이) | 12.9179 (0.0937%) | 11.9481 (0.3083%) | 0.030945 / -0.0096%, 0.0269% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0130/result.json) |
| n0131 / 완료 | b02→c158 / n0129 | half_life: 없음→365 (단일 설정 차이) | 12.9829 (0.0590%) | 12.0009 (0.3452%) | 0.018668 / -0.0037%, 0.0233% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0131/result.json) |
| n0132 / 실패 | b02→c158 / n0128 | bound: 0.2→0.1; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→500; n_estimators: 0→80; num_leaves: 0→3; reg_lambda: 0.0→10.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / -0.0849%, -0.0234% | 5/5 / 5 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T100255Z_failed_candidates_science.json) |
| n0133 / 완료 | b02→c158 / n0129 | features: core→season; half_life: 없음→180; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→200; n_estimators: 0→300; num_leaves: 0→15; reg_lambda: 0.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 13.1689 (1.4921%) | 12.0493 (0.7502%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0133/result.json) |
| n0134 / 완료 | b02→c158 / n0132 | features: core→age; half_life: 없음→180; min_child_samples: 500→1000; n_estimators: 80→300; reg_lambda: 10.0→2.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | 13.1868 | 11.9488 | 0.008695 / -0.0009%, -0.0018% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0134/result.json) |
| n0135 / 실패 | b02→c158 / n0132 | bound: 0.1→0.3; half_life: 없음→180; learning_rate: 0.025→0.05; mode: additive→multiplicative; reg_lambda: 10.0→30.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / -0.0123%, -0.0013% | 5/5 / 5 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T100255Z_failed_candidates_science.json) |
| n0136 / 완료 | b02→c158 / n0132 | features: core→season; half_life: 없음→365; learning_rate: 0.025→0.05; n_estimators: 80→300; num_leaves: 3→15; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 13.4397 | 11.9377 | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0136/result.json) |
| n0137 / 완료 | b02→c158 / n0132 | bound: 0.1→0.15; features: core→age; learning_rate: 0.025→0.05; min_child_samples: 500→1000; mode: additive→multiplicative (여러 설정 동시 변경) | 13.0126 | 11.7608 | 0.036219 / -0.0122%, 0.0026% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0137/result.json) |
| n0138 / 완료 | b02→c158 / n0133 | bound: 0.3→0.2; features: season→core; half_life: 180→없음; learning_rate: 0.025→0.05; min_child_samples: 200→1000; mode: multiplicative→additive (여러 설정 동시 변경) | 12.9181 (-1.9046%) | 11.9707 (-0.6522%) | 0.006512 / -0.0002%, 0.0065% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0138/result.json) |
| n0139 / 완료 | b02→c158 / n0135 | bound: 0.3→0.5; features: core→season; half_life: 180→없음; min_child_samples: 500→1000; n_estimators: 80→160; num_leaves: 3→15 (여러 설정 동시 변경) | 13.0459 | 11.7791 | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0139/result.json) |
| n0140 / 완료 | b02→c158 / n0132 | bound: 0.1→0.2; features: core→age; half_life: 없음→365; num_leaves: 3→7; shrink: 0.75→0.25 (여러 설정 동시 변경) | 13.1103 | 12.0292 | 0.006238 / -0.0004%, 0.0059% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0140/result.json) |
| n0141 / 완료 | b02→c158 / n0138 | bound: 0.2→0.15; half_life: 없음→180; mode: additive→multiplicative; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 13.0671 (1.1540%) | 12.0638 (0.7779%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0141/result.json) |
| n0142 / 실패 | b02→c158 / n0132 | bound: 0.1→0.2; features: core→season; min_child_samples: 500→200; reg_lambda: 10.0→2.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / -0.0875%, -0.0932% | 5/5 / 5 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T100255Z_failed_candidates_science.json) |
| n0143 / 완료 | b02→c158 / n0137 | bound: 0.15→0.3; n_estimators: 80→300; num_leaves: 3→7; reg_lambda: 10.0→2.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | 13.5565 (4.1793%) | 11.8669 (0.9023%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0143/result.json) |
| n0144 / 완료 | b02→c158 / n0136 | features: season→core; min_child_samples: 500→1000; n_estimators: 300→160; shrink: 0.75→0.25 (여러 설정 동시 변경) | 13.0145 (-3.1634%) | 12.0205 (0.6934%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0144/result.json) |
| n0145 / 완료 | b02→c158 / n0133 | n_estimators: 300→160; num_leaves: 15→7; reg_lambda: 2.0→30.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | 13.2186 (0.3778%) | 11.9387 (-0.9181%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0145/result.json) |
| n0146 / 완료 | b02→c158 / n0140 | bound: 0.2→0.1; n_estimators: 80→300 (여러 설정 동시 변경) | 13.1339 (0.1801%) | 12.0315 (0.0196%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0146/result.json) |
| n0147 / 완료 | b02→c158 / n0133 | features: season→core; min_child_samples: 200→500; num_leaves: 15→7; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.6416 (3.5898%) | 11.9884 (-0.5050%) | 0.012656 / -0.0035%, -0.0503% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0147/result.json) |
| n0148 / 완료 | b02→c158 / n0133 | learning_rate: 0.025→0.05; mode: multiplicative→additive; n_estimators: 300→160; num_leaves: 15→3 (여러 설정 동시 변경) | 13.0658 (-0.7829%) | 12.0217 (-0.2288%) | 0.007947 / -0.0005%, 0.0055% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0148/result.json) |
| n0149 / 완료 | b02→c158 / n0143 | bound: 0.3→0.15; min_child_samples: 1000→500; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 13.4660 (-0.6670%) | 11.8064 (-0.5100%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0149/result.json) |
| n0150 / 완료 | b02→c158 / n0132 | bound: 0.1→0.3; learning_rate: 0.025→0.05; num_leaves: 3→15; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | 13.3061 | 11.7478 | 0.019127 / -0.0075%, -0.0251% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0150/result.json) |
| n0151 / 완료 | b02→c158 / n0139 | half_life: 없음→365; min_child_samples: 1000→200; reg_lambda: 30.0→10.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 13.0747 (0.2209%) | 12.0010 (1.8844%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0151/result.json) |
| n0152 / 완료 | b02→c158 / n0140 | half_life: 365→없음; learning_rate: 0.025→0.05; shrink: 0.25→0.5 (여러 설정 동시 변경) | 13.1013 (-0.0679%) | 11.8535 (-1.4606%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0152/result.json) |
| n0153 / 완료 | b02→c158 / n0137 | features: age→core; half_life: 없음→365; learning_rate: 0.05→0.025; shrink: 0.75→0.5 (여러 설정 동시 변경) | 12.9431 (-0.5344%) | 11.8886 (1.0871%) | 0.038005 / -0.0129%, 0.0234% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0153/result.json) |
| n0154 / 완료 | b02→c158 / n0148 | bound: 0.3→0.1; reg_lambda: 2.0→2.5; shrink: 0.25→0.5 (여러 설정 동시 변경) | 13.0624 (-0.0256%) | 11.8898 (-1.0975%) | 0.008801 / -0.0007%, -0.0051% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0154/result.json) |
| n0155 / 완료 | b02→c158 / n0146 | bound: 0.1→0.3; half_life: 365→180; mode: additive→multiplicative (여러 설정 동시 변경) | 13.1902 (0.4290%) | 12.0817 (0.4174%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0155/result.json) |
| n0156 / 완료 | b02→c158 / n0148 | features: season→core; min_child_samples: 200→1000; n_estimators: 160→80 (여러 설정 동시 변경) | 13.0218 (-0.3364%) | 12.0167 (-0.0419%) | 0.018292 / -0.0043%, 0.0165% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0156/result.json) |
| n0157 / 완료 | b02→c158 / n0141 | features: core→season; half_life: 180→없음; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | 13.0149 (-0.3999%) | 11.9557 (-0.8960%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0157/result.json) |
| n0158 / 완료 | b02→c158 / n0152 | half_life: 없음→180; min_child_samples: 500→1000; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 13.1708 (0.5300%) | 12.0011 (1.2453%) | 0.000121 / -0.0000%, -0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0158/result.json) |
| n0159 / 완료 | b02→c158 / n0151 | features: season→core; num_leaves: 15→7; reg_lambda: 10.0→30.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.5971 (3.9958%) | 11.8140 (-1.5584%) | 0.041009 / -0.0237%, -0.1285% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0159/result.json) |
| n0160 / 완료 | b02→c158 / n0140 | features: age→season; min_child_samples: 500→1000; n_estimators: 80→160; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 13.0630 (-0.3605%) | 11.9984 (-0.2556%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0160/result.json) |
| n0161 / 완료 | b02→c158 / n0139 | features: season→age; min_child_samples: 1000→200; n_estimators: 160→300; num_leaves: 15→3 (여러 설정 동시 변경) | 13.0776 (0.2429%) | 11.8914 (0.9535%) | 0.017039 / -0.0036%, 0.0047% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0161/result.json) |
| n0162 / 완료 | b02→c158 / n0140 | features: age→core; learning_rate: 0.025→0.05; n_estimators: 80→160 (여러 설정 동시 변경) | 13.0145 (-0.7308%) | 12.0213 (-0.0650%) | 0.013607 / -0.0017%, 0.0102% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0162/result.json) |
| n0163 / 완료 | b02→c158 / n0139 | bound: 0.5→0.15; half_life: 없음→365 (여러 설정 동시 변경) | 13.2757 (1.7621%) | 11.8579 (0.6690%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0163/result.json) |
| n0164 / 완료 | b02→c158 / n0143 | half_life: 없음→365; min_child_samples: 1000→200; mode: multiplicative→additive; n_estimators: 300→80 (여러 설정 동시 변경) | 13.3612 (-1.4402%) | 11.8211 (-0.3860%) | 0.012502 / -0.0030%, -0.0315% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0164/result.json) |
| n0165 / 완료 | b02→c158 / n0147 | bound: 0.3→0.5; reg_lambda: 2.0→10.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.2486 (-2.8810%) | 11.9439 (-0.3713%) | 0.019059 / -0.0044%, -0.0494% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0165/result.json) |
| n0166 / 완료 | b02→c158 / n0142 | bound: 0.2→0.1; half_life: 없음→180; num_leaves: 3→7 (여러 설정 동시 변경) | 13.4917 | 11.7647 | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0166/result.json) |
| n0167 / 완료 | b02→c158 / n0140 | bound: 0.2→0.3; mode: additive→multiplicative; reg_lambda: 10.0→2.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | 13.0863 (-0.1830%) | 11.9497 (-0.6609%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0167/result.json) |
| n0168 / 완료 | b02→c158 / n0135 | learning_rate: 0.05→0.025; mode: multiplicative→additive; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 12.9093 | 11.8866 | 0.043031 / -0.0179%, 0.0117% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0168/result.json) |
| n0169 / 실패 | b02→c158 / n0142 | bound: 0.2→0.3; min_child_samples: 200→1000; mode: additive→multiplicative; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / -0.0392%, -0.0571% | 5/5 / 5 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T100255Z_failed_candidates_science.json) |
| n0170 / 완료 | b02→c158 / n0134 | bound: 0.1→0.2; half_life: 180→365; num_leaves: 3→7; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.6455 (3.4789%) | 11.9062 (-0.3559%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0170/result.json) |
| n0171 / 실패 | b02→c158 / n0135 | min_child_samples: 500→200; n_estimators: 80→160; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / -0.0200%, -0.1165% | 5/5 / 5 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T100255Z_failed_candidates_science.json) |
| n0172 / 완료 | b02→c158 / n0146 | features: age→season; half_life: 365→180; learning_rate: 0.025→0.05 (여러 설정 동시 변경) | 13.1283 (-0.0422%) | 12.0158 (-0.1305%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0172/result.json) |
| n0173 / 실패 | b02→c158 / n0139 | features: season→age; num_leaves: 15→7; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / -0.0065%, -0.0445% | 5/5 / 5 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T100255Z_failed_candidates_science.json) |
| n0174 / 실패 | b02→c158 / n0160 | features: season→core; n_estimators: 160→300; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / -0.0090%, -0.0490% | 5/5 / 5 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T100255Z_failed_candidates_science.json) |
| n0175 / 완료 | b02→c158 / n0145 | reg_lambda: 30.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.7018 (3.6553%) | 11.8327 (-0.8875%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0175/result.json) |
| n0176 / 완료 | b02→c158 / n0136 | features: season→age; min_child_samples: 500→1000; num_leaves: 15→7 (여러 설정 동시 변경) | 13.4760 (0.2703%) | 11.9507 (0.1093%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0176/result.json) |
| n0177 / 완료 | b02→c158 / n0147 | half_life: 180→없음; reg_lambda: 2.0→10.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.9055 (-5.3963%) | 11.8572 (-1.0950%) | 0.054808 / -0.0277%, 0.0132% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0177/result.json) |
| n0178 / 완료 | b02→c158 / n0170 | features: age→season; min_child_samples: 1000→200 (여러 설정 동시 변경) | 13.8428 (1.4453%) | 11.7754 (-1.0986%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0178/result.json) |
| n0179 / 완료 | b02→c158 / n0161 | bound: 0.5→0.15; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 13.0581 (-0.1488%) | 11.8841 (-0.0610%) | 0.019127 / -0.0045%, 0.0045% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0179/result.json) |
| n0180 / 완료 | b02→c158 / n0147 | bound: 0.3→0.2; learning_rate: 0.025→0.05; mode: multiplicative→additive; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 13.9162 (2.0131%) | 12.0812 (0.7738%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0180/result.json) |
| n0181 / 완료 | b02→c158 / n0139 | half_life: 없음→180; learning_rate: 0.05→0.025; num_leaves: 15→3; shrink: 0.5→0.25 (여러 설정 동시 변경) | 13.0758 (0.2297%) | 12.0463 (2.2688%) | 0.009381 / -0.0013%, 0.0096% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0181/result.json) |
| n0182 / 완료 | b02→c158 / n0176 | min_child_samples: 1000→200; n_estimators: 300→160 (여러 설정 동시 변경) | 13.3669 (-0.8100%) | 11.8592 (-0.7663%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0182/result.json) |
| n0183 / 완료 | b02→c158 / n0151 | features: season→core; n_estimators: 160→80; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 13.0250 (-0.3800%) | 12.0294 (0.2361%) | 0.006233 / -0.0003%, 0.0044% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0183/result.json) |
| n0184 / 완료 | b02→c158 / n0134 | features: age→season; learning_rate: 0.025→0.05; reg_lambda: 2.0→30.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.6596 (3.5851%) | 11.9112 (-0.3145%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0184/result.json) |
| n0185 / 완료 | b02→c158 / n0155 | half_life: 180→없음; n_estimators: 300→160; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.0743 (-0.8789%) | 11.7658 (-2.6153%) | 0.016476 / -0.0052%, -0.0166% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0185/result.json) |
| n0186 / 실패 | b02→c158 / n0134 | bound: 0.1→0.2; features: age→core; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / -0.0385%, -0.0863% | 5/5 / 5 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T100255Z_failed_candidates_science.json) |
| n0187 / 완료 | b02→c158 / n0136 | bound: 0.1→0.3; min_child_samples: 500→200; mode: additive→multiplicative; num_leaves: 15→3 (여러 설정 동시 변경) | 13.2045 (-1.7496%) | 11.7955 (-1.1913%) | 0.016479 / -0.0041%, -0.0292% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0187/result.json) |
| n0188 / 실패 | b02→c158 / n0168 | features: core→age; min_child_samples: 500→200; reg_lambda: 2.0→30.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / -0.0081%, -0.0198% | 5/5 / 5 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T100255Z_failed_candidates_science.json) |
| n0189 / 완료 | b02→c158 / n0135 | bound: 0.3→0.5; min_child_samples: 500→1000; num_leaves: 3→7; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 13.0527 | 11.9713 | 0.019776 / -0.0056%, -0.0099% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0189/result.json) |
| n0190 / 완료 | b02→c158 / n0148 | min_child_samples: 200→1000; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.2287 (1.2469%) | 11.8198 (-1.6800%) | 0.008149 / -0.0012%, -0.0137% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0190/result.json) |
| n0191 / 실패 | b02→c158 / n0181 | bound: 0.5→0.15; features: season→age; min_child_samples: 1000→500; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / -0.0070%, -0.0105% | 5/5 / 5 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T100255Z_failed_candidates_science.json) |
| n0192 / 완료 | b03→c174 / n0192 | 변경 없음(비교 기준 자체) (기준 자체) | 12.6381 (0.0000%) | 11.7258 (0.0000%) | 0.100398 / -0.0775%, 0.3127% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0192/result.json) |
| n0193 / 완료 | b03→c174 / n0192 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | 12.5817 (-0.4461%) | 11.7208 (-0.0425%) | 0.098045 / -0.0662%, 0.3247% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0193/result.json) |
| n0194 / 완료 | b03→c174 / n0192 | half_life: 없음→365 (단일 설정 차이) | 12.6089 (-0.2311%) | 11.7381 (0.1051%) | 0.101405 / -0.0748%, 0.3367% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0194/result.json) |
| n0195 / 완료 | b03→c174 / n0193 | half_life: 없음→365 (단일 설정 차이) | 12.5692 (-0.0999%) | 11.7262 (0.0460%) | 0.100161 / -0.0656%, 0.3470% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0195/result.json) |
| n0196 / 완료 | b03→c174 / n0192 | bound: 0.2→0.3; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→1000; n_estimators: 0→80; num_leaves: 0→15; reg_lambda: 0.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.5956 (-0.3367%) | 11.6458 (-0.6821%) | 0.091607 / -0.0654%, 0.2472% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0196/result.json) |
| n0197 / 완료 | b03→c174 / n0196 | bound: 0.3→0.5; features: core→season; half_life: 없음→180; min_child_samples: 1000→500; mode: additive→multiplicative; n_estimators: 80→300; num_leaves: 15→7 (여러 설정 동시 변경) | 12.6414 (0.3637%) | 11.6369 (-0.0766%) | 0.076021 / -0.0494%, 0.2008% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0197/result.json) |
| n0198 / 완료 | b03→c174 / n0196 | features: core→age; half_life: 없음→180; min_child_samples: 1000→200; n_estimators: 80→160; num_leaves: 15→3; shrink: 0.25→0.5 (여러 설정 동시 변경) | 12.6228 (0.2162%) | 11.6406 (-0.0452%) | 0.103515 / -0.0721%, 0.2834% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0198/result.json) |
| n0199 / 완료 | b03→c174 / n0196 | min_child_samples: 1000→200; mode: additive→multiplicative; num_leaves: 15→7; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 12.5800 (-0.1232%) | 11.6751 (0.2516%) | 0.099319 / -0.0651%, 0.2890% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0199/result.json) |
| n0200 / 완료 | b03→c174 / n0197 | bound: 0.5→0.2; half_life: 180→365; learning_rate: 0.025→0.05; mode: multiplicative→additive; n_estimators: 300→160; num_leaves: 7→3; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 12.5844 (-0.4510%) | 11.6474 (0.0900%) | 0.103498 / -0.0672%, 0.2895% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0200/result.json) |
| n0201 / 완료 | b03→c174 / n0197 | bound: 0.5→0.15; features: season→age; half_life: 180→365; n_estimators: 300→160; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.2249 (4.6159%) | 11.7445 (0.9244%) | 0.066838 / -0.0513%, 0.1545% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0201/result.json) |
| n0202 / 완료 | b03→c174 / n0197 | bound: 0.5→0.1; features: season→core; learning_rate: 0.025→0.05; mode: multiplicative→additive; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.1950 (4.3796%) | 11.5493 (-0.7531%) | 0.009274 / -0.0008%, -0.0036% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0202/result.json) |
| n0203 / 완료 | b03→c174 / n0197 | bound: 0.5→0.3; half_life: 180→365; min_child_samples: 500→200; num_leaves: 7→3; reg_lambda: 2.0→30.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.0048 (2.8753%) | 11.6958 (0.5059%) | 0.076814 / -0.0739%, 0.1677% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0203/result.json) |
| n0204 / 완료 | b03→c174 / n0196 | features: core→age; learning_rate: 0.025→0.05; n_estimators: 80→160; num_leaves: 15→7 (여러 설정 동시 변경) | 12.6362 (0.3228%) | 11.6574 (0.0989%) | 0.073503 / -0.0378%, 0.2095% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0204/result.json) |
| n0205 / 완료 | b03→c174 / n0204 | features: age→core; half_life: 없음→180; mode: additive→multiplicative; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.4092 (6.1172%) | 11.6271 (-0.2594%) | 0.025329 / -0.0125%, -0.0243% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0205/result.json) |
| n0206 / 완료 | b03→c174 / n0198 | features: age→season; half_life: 180→없음; num_leaves: 3→15; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 12.8821 (2.0544%) | 11.6785 (0.3260%) | 0.055930 / -0.0282%, 0.1434% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0206/result.json) |
| n0207 / 완료 | b03→c174 / n0201 | min_child_samples: 500→200; num_leaves: 7→3; reg_lambda: 2.0→30.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.5764 (-4.9032%) | 11.6710 (-0.6254%) | 0.102068 / -0.0693%, 0.2992% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0207/result.json) |
| n0208 / 완료 | b03→c174 / n0203 | bound: 0.3→0.2; features: season→core; mode: multiplicative→additive; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 13.0241 (0.1483%) | 11.5072 (-1.6123%) | 0.059528 / -0.0343%, 0.0646% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0208/result.json) |
| n0209 / 완료 | b03→c174 / n0197 | bound: 0.5→0.3; n_estimators: 300→80; num_leaves: 7→15; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.0444 (3.1884%) | 11.6761 (0.3371%) | 0.025990 / -0.0080%, 0.0605% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0209/result.json) |
| n0210 / 완료 | b03→c174 / n0196 | bound: 0.3→0.2; features: core→age; half_life: 없음→180; num_leaves: 15→7; shrink: 0.25→0.75 (여러 설정 동시 변경) | 12.8202 (1.7835%) | 11.6161 (-0.2551%) | 0.079950 / -0.0605%, 0.1876% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0210/result.json) |
| n0211 / 완료 | b03→c174 / n0199 | bound: 0.3→0.5; min_child_samples: 200→1000; n_estimators: 80→300 (여러 설정 동시 변경) | 12.5669 (-0.1045%) | 11.6381 (-0.3176%) | 0.114798 / -0.0968%, 0.3122% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0211/result.json) |
| n0212 / 완료 | b03→c174 / n0200 | half_life: 365→180; learning_rate: 0.05→0.025; shrink: 0.25→0.5 (여러 설정 동시 변경) | 12.6178 (0.2657%) | 11.6328 (-0.1254%) | 0.103286 / -0.0730%, 0.2794% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0212/result.json) |
| n0213 / 완료 | b03→c174 / n0209 | bound: 0.3→0.5; features: season→age; num_leaves: 15→3; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 12.7606 (-2.1758%) | 11.6520 (-0.2071%) | 0.066081 / -0.0409%, 0.1845% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0213/result.json) |
| n0214 / 완료 | b03→c174 / n0196 | half_life: 없음→180; num_leaves: 15→7; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.0644 (3.7220%) | 11.5157 (-1.1171%) | 0.031801 / -0.0152%, 0.0330% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0214/result.json) |
| n0215 / 완료 | b03→c174 / n0197 | bound: 0.5→0.15; half_life: 180→365; learning_rate: 0.025→0.05; min_child_samples: 500→1000; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.3205 (5.3727%) | 11.7875 (1.2940%) | 0.006660 / -0.0002%, 0.0147% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0215/result.json) |
| n0216 / 완료 | b03→c174 / n0208 | bound: 0.2→0.1; features: core→age; min_child_samples: 200→1000 (여러 설정 동시 변경) | 13.0275 (0.0259%) | 11.6688 (1.4042%) | 0.067503 / -0.0494%, 0.1548% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0216/result.json) |
| n0217 / 완료 | b03→c174 / n0203 | features: season→core; n_estimators: 300→80; num_leaves: 3→15 (여러 설정 동시 변경) | 13.1596 (1.1902%) | 11.6589 (-0.3152%) | 0.041767 / -0.0190%, 0.0840% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0217/result.json) |
| n0218 / 완료 | b03→c174 / n0206 | bound: 0.3→0.2; learning_rate: 0.025→0.05; reg_lambda: 10.0→2.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.3424 (3.5729%) | 11.7838 (0.9017%) | 0.018023 / -0.0060%, 0.0364% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0218/result.json) |
| n0219 / 완료 | b03→c174 / n0207 | learning_rate: 0.025→0.05; n_estimators: 160→80; shrink: 0.25→0.75 (여러 설정 동시 변경) | 12.7280 (1.2049%) | 11.6308 (-0.3449%) | 0.095864 / -0.0835%, 0.2563% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0219/result.json) |
| n0220 / 완료 | b03→c174 / n0208 | half_life: 365→없음; learning_rate: 0.025→0.05 (여러 설정 동시 변경) | 13.2819 (1.9792%) | 11.7167 (1.8206%) | 0.080536 / -0.0853%, 0.1198% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0220/result.json) |
| n0221 / 완료 | b03→c174 / n0215 | bound: 0.15→0.5; n_estimators: 300→80; num_leaves: 7→15; reg_lambda: 2.0→10.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | 12.8822 (-3.2908%) | 11.6204 (-1.4178%) | 0.035019 / -0.0120%, 0.0767% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0221/result.json) |
| n0222 / 완료 | b03→c174 / n0204 | bound: 0.3→0.1; n_estimators: 160→80; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 12.6120 (-0.1914%) | 11.6626 (0.0446%) | 0.074363 / -0.0465%, 0.2120% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0222/result.json) |
| n0223 / 완료 | b03→c174 / n0197 | features: season→core; half_life: 180→365; reg_lambda: 2.0→30.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.3160 (5.3370%) | 11.6347 (-0.0187%) | 0.062744 / -0.0477%, 0.0330% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0223/result.json) |
| n0224 / 완료 | b03→c174 / n0202 | features: core→season; half_life: 180→365; learning_rate: 0.05→0.025; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 13.2115 (0.1247%) | 11.6964 (1.2738%) | 0.043736 / -0.0226%, 0.0922% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0224/result.json) |
| n0225 / 완료 | b03→c174 / n0201 | min_child_samples: 500→200; shrink: 1.0→0.75 (여러 설정 동시 변경) | 12.9516 (-2.0664%) | 11.6612 (-0.7089%) | 0.064361 / -0.0450%, 0.1593% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0225/result.json) |
| n0226 / 완료 | b03→c174 / n0208 | n_estimators: 300→80; num_leaves: 3→15 (여러 설정 동시 변경) | 13.3659 (2.6241%) | 11.5523 (0.3917%) | 0.003429 / -0.0000%, 0.0024% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0226/result.json) |
| n0227 / 완료 | b03→c174 / n0215 | bound: 0.15→0.5; n_estimators: 300→80; shrink: 0.75→1.0 (여러 설정 동시 변경) | 13.2184 (-0.7671%) | 11.7502 (-0.3166%) | 0.060541 / -0.0411%, 0.1326% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0227/result.json) |
| n0228 / 완료 | b03→c174 / n0198 | half_life: 180→365; num_leaves: 3→7; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.2801 (5.2073%) | 11.7148 (0.6376%) | 0.047708 / -0.0271%, 0.1077% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0228/result.json) |
| n0229 / 완료 | b03→c174 / n0211 | learning_rate: 0.025→0.05; min_child_samples: 1000→500; num_leaves: 7→3; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 12.5377 (-0.2327%) | 11.6440 (0.0513%) | 0.130967 / -0.1096%, 0.3558% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0229/result.json) |
| n0230 / 완료 | b03→c174 / n0202 | features: core→season; num_leaves: 7→15; reg_lambda: 2.0→10.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | 12.7130 (-3.6534%) | 11.6006 (0.4441%) | 0.029086 / -0.0067%, 0.0655% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0230/result.json) |
| n0231 / 완료 | b03→c174 / n0205 | bound: 0.3→0.5; features: core→age; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.2335 (-1.3104%) | 11.6547 (0.2372%) | 0.022877 / -0.0085%, 0.0325% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0231/result.json) |
| n0232 / 완료 | b03→c174 / n0202 | bound: 0.1→0.3; learning_rate: 0.05→0.025; num_leaves: 7→15; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 13.3296 (1.0200%) | 11.5666 (0.1504%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0232/result.json) |
| n0233 / 완료 | b03→c174 / n0205 | bound: 0.3→0.15; features: core→season; min_child_samples: 1000→200; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.8487 (-4.1803%) | 11.6253 (-0.0159%) | 0.067504 / -0.0436%, 0.1489% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0233/result.json) |
| n0234 / 완료 | b03→c174 / n0200 | features: season→age; half_life: 365→없음; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | 12.5757 (-0.0691%) | 11.6596 (0.1046%) | 0.101628 / -0.0673%, 0.2923% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0234/result.json) |
| n0235 / 완료 | b03→c174 / n0217 | min_child_samples: 200→1000; num_leaves: 15→7; shrink: 1.0→0.75 (여러 설정 동시 변경) | 12.7631 (-3.0133%) | 11.6417 (-0.1479%) | 0.088562 / -0.0570%, 0.2383% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0235/result.json) |
| n0236 / 완료 | b03→c174 / n0218 | min_child_samples: 200→1000; n_estimators: 160→80; num_leaves: 15→3 (여러 설정 동시 변경) | 12.8588 (-3.6248%) | 11.6213 (-1.3790%) | 0.086426 / -0.0647%, 0.2122% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0236/result.json) |
| n0237 / 완료 | b03→c174 / n0211 | features: core→age; reg_lambda: 10.0→2.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.4019 (6.6448%) | 11.9088 (2.3268%) | 0.023624 / -0.0101%, 0.0561% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0237/result.json) |
| n0238 / 완료 | b03→c174 / n0235 | learning_rate: 0.025→0.05; mode: multiplicative→additive; n_estimators: 80→300; shrink: 0.75→0.5 (여러 설정 동시 변경) | 12.8378 (0.5853%) | 11.5278 (-0.9786%) | 0.068574 / -0.0393%, 0.0900% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0238/result.json) |
| n0239 / 완료 | b03→c174 / n0209 | bound: 0.3→0.15; reg_lambda: 2.0→2.5 (여러 설정 동시 변경) | 13.0612 (0.1284%) | 11.6762 (0.0009%) | 0.021761 / -0.0058%, 0.0501% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0239/result.json) |
| n0240 / 완료 | b03→c174 / n0222 | bound: 0.1→0.2; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | 12.6088 (-0.0253%) | 11.6693 (0.0579%) | 0.074159 / -0.0479%, 0.2166% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0240/result.json) |
| n0241 / 완료 | b03→c174 / n0205 | min_child_samples: 1000→500; n_estimators: 160→300; num_leaves: 7→15 (여러 설정 동시 변경) | 13.9773 (4.2364%) | 11.7916 (1.4150%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0241/result.json) |
| n0242 / 완료 | b03→c174 / n0200 | bound: 0.2→0.3; half_life: 365→없음; num_leaves: 3→15 (여러 설정 동시 변경) | 12.6604 (0.6040%) | 11.6645 (0.1468%) | 0.064694 / -0.0297%, 0.1833% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0242/result.json) |
| n0243 / 완료 | b03→c174 / n0207 | min_child_samples: 200→1000; n_estimators: 160→80; shrink: 0.25→1.0 (여러 설정 동시 변경) | 12.7863 (1.6684%) | 11.6787 (0.0654%) | 0.071800 / -0.0554%, 0.2149% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0243/result.json) |
| n0244 / 완료 | b03→c174 / n0202 | half_life: 180→없음; min_child_samples: 500→1000; num_leaves: 7→15; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 13.2093 (0.1082%) | 11.8014 (2.1834%) | 0.043301 / -0.0290%, 0.0805% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0244/result.json) |
| n0245 / 완료 | b03→c174 / n0203 | bound: 0.3→0.5; n_estimators: 300→160 (여러 설정 동시 변경) | 12.8796 (-0.9628%) | 11.6749 (-0.1786%) | 0.077608 / -0.0704%, 0.2033% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0245/result.json) |
| n0246 / 완료 | b03→c174 / n0234 | half_life: 없음→180; shrink: 0.25→0.5 (여러 설정 동시 변경) | 12.6592 (0.6642%) | 11.5937 (-0.5647%) | 0.102894 / -0.0827%, 0.2428% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0246/result.json) |
| n0247 / 완료 | b03→c174 / n0209 | bound: 0.3→0.15; features: season→core; min_child_samples: 500→200; shrink: 0.75→0.5 (여러 설정 동시 변경) | 12.7402 (-2.3324%) | 11.6010 (-0.6436%) | 0.044245 / -0.0158%, 0.0969% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0247/result.json) |
| n0248 / 완료 | b03→c174 / n0206 | half_life: 없음→365; learning_rate: 0.025→0.05; n_estimators: 160→80; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 12.9198 (0.2927%) | 11.6179 (-0.5190%) | 0.039292 / -0.0145%, 0.0929% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0248/result.json) |
| n0249 / 완료 | b03→c174 / n0198 | half_life: 180→365; mode: additive→multiplicative; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 12.6564 (0.2665%) | 11.6580 (0.1499%) | 0.090948 / -0.0657%, 0.2635% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0249/result.json) |
| n0250 / 완료 | b03→c174 / n0196 | bound: 0.3→0.1; half_life: 없음→365; num_leaves: 15→3; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 12.5757 (-0.1573%) | 11.6619 (0.1381%) | 0.086088 / -0.0537%, 0.2316% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0250/result.json) |
| n0251 / 완료 | b03→c174 / n0239 | half_life: 180→365; min_child_samples: 500→200; reg_lambda: 2.5→10.0 (여러 설정 동시 변경) | 12.9697 (-0.7000%) | 11.6772 (0.0081%) | 0.046104 / -0.0200%, 0.1226% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0251/result.json) |
| n0252 / 완료 | b03→c174 / n0210 | bound: 0.2→0.3; half_life: 180→365; n_estimators: 80→300; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 13.2271 (3.1739%) | 11.6809 (0.5576%) | 0.024324 / -0.0113%, 0.0415% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0252/result.json) |
| n0253 / 완료 | b03→c174 / n0241 | learning_rate: 0.05→0.025; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 13.6686 (-2.2084%) | 11.7199 (-0.6086%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0253/result.json) |
| n0254 / 완료 | b03→c174 / n0248 | bound: 0.3→0.1; learning_rate: 0.05→0.025; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.6302 (-2.2420%) | 11.6511 (0.2857%) | 0.070793 / -0.0417%, 0.1883% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0254/result.json) |
| n0255 / 완료 | b03→c174 / n0201 | n_estimators: 160→300; reg_lambda: 2.0→30.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.7971 (-3.2349%) | 11.6359 (-0.9246%) | 0.064528 / -0.0397%, 0.1616% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0255/result.json) |
| n0256 / 완료 | b04→c093 / n0256 | 변경 없음(비교 기준 자체) (기준 자체) | 13.0539 (0.0000%) | 11.9458 (0.0000%) | 0.093781 / -0.0800%, 0.3890% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0256/result.json) |
| n0257 / 완료 | b04→c093 / n0256 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | 13.0109 (-0.3292%) | 11.9249 (-0.1751%) | 0.090715 / -0.0747%, 0.3641% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0257/result.json) |
| n0258 / 완료 | b04→c093 / n0256 | half_life: 없음→365 (단일 설정 차이) | 12.9730 (-0.6200%) | 11.9934 (0.3984%) | 0.097511 / -0.0784%, 0.4461% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0258/result.json) |
| n0259 / 완료 | b04→c093 / n0257 | half_life: 없음→365 (단일 설정 차이) | 12.9639 (-0.3614%) | 11.9537 (0.2418%) | 0.093647 / -0.0752%, 0.4038% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0259/result.json) |
| n0260 / 완료 | b04→c093 / n0258 | bound: 0.2→0.1; learning_rate: 0.0→0.05; method: median→tree; min_child_samples: 0→200; n_estimators: 0→160; num_leaves: 0→3; reg_lambda: 0.0→10.0 (여러 설정 동시 변경) | 13.1167 (1.1078%) | 11.8346 (-1.3237%) | 0.077532 / -0.0641%, 0.2030% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0260/result.json) |
| n0261 / 완료 | b04→c093 / n0260 | bound: 0.1→0.15; features: core→season; half_life: 365→없음; learning_rate: 0.05→0.025; min_child_samples: 200→500; mode: additive→multiplicative; num_leaves: 3→15 (여러 설정 동시 변경) | 13.2610 (1.1004%) | 11.9667 (1.1157%) | 0.042482 / -0.0220%, 0.1450% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0261/result.json) |
| n0262 / 완료 | b04→c093 / n0260 | bound: 0.1→0.3; features: core→age; min_child_samples: 200→1000; n_estimators: 160→300; num_leaves: 3→7; reg_lambda: 10.0→30.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 13.0417 (-0.5715%) | 11.8563 (0.1835%) | 0.044138 / -0.0190%, 0.1255% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0262/result.json) |
| n0263 / 완료 | b04→c093 / n0262 | features: age→core; half_life: 365→180; learning_rate: 0.05→0.025; mode: additive→multiplicative; num_leaves: 7→15; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 13.0512 (0.0731%) | 11.8284 (-0.2358%) | 0.053430 / -0.0265%, 0.1400% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0263/result.json) |
| n0264 / 완료 | b04→c093 / n0262 | features: age→season; half_life: 365→없음; min_child_samples: 1000→200; n_estimators: 300→80; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 13.0411 (-0.0043%) | 11.8883 (0.2695%) | 0.073003 / -0.0555%, 0.2407% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0264/result.json) |
| n0265 / 완료 | b04→c093 / n0261 | features: season→age; half_life: 없음→180; learning_rate: 0.025→0.05; n_estimators: 160→300; num_leaves: 15→7; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.9756 (5.3889%) | 12.0587 (0.7695%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0265/result.json) |
| n0266 / 완료 | b04→c093 / n0260 | bound: 0.1→0.2; half_life: 365→180; learning_rate: 0.05→0.025; n_estimators: 160→300; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.2065 (0.6851%) | 11.8180 (-0.1406%) | 0.068777 / -0.0486%, 0.1181% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0266/result.json) |
| n0267 / 완료 | b04→c093 / n0261 | bound: 0.15→0.3; half_life: 없음→180; n_estimators: 160→80; num_leaves: 15→3; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.9237 (-2.5435%) | 11.8902 (-0.6385%) | 0.091451 / -0.0739%, 0.3371% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0267/result.json) |
| n0268 / 완료 | b04→c093 / n0266 | bound: 0.2→0.1; features: core→age; min_child_samples: 200→500; reg_lambda: 10.0→2.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | 13.0554 (-1.1447%) | 11.8194 (0.0122%) | 0.087194 / -0.0774%, 0.2315% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0268/result.json) |
| n0269 / 완료 | b04→c093 / n0260 | bound: 0.1→0.5; half_life: 365→180; mode: additive→multiplicative; reg_lambda: 10.0→30.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.9525 (-1.2517%) | 11.8430 (0.0706%) | 0.093871 / -0.0688%, 0.3015% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0269/result.json) |
| n0270 / 완료 | b04→c093 / n0262 | features: age→season; num_leaves: 7→3; shrink: 0.25→0.5 (여러 설정 동시 변경) | 13.1447 (0.7895%) | 11.8534 (-0.0245%) | 0.077178 / -0.0709%, 0.2029% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0270/result.json) |
| n0271 / 완료 | b04→c093 / n0262 | min_child_samples: 1000→200; mode: additive→multiplicative; reg_lambda: 30.0→10.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | 13.1971 (1.1913%) | 11.8865 (0.2541%) | 0.026107 / -0.0080%, 0.0666% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0271/result.json) |
| n0272 / 완료 | b04→c093 / n0260 | half_life: 365→없음; learning_rate: 0.05→0.025; min_child_samples: 200→1000; n_estimators: 160→300; num_leaves: 3→15 (여러 설정 동시 변경) | 13.2456 (0.9827%) | 11.9263 (0.7749%) | 0.068534 / -0.0471%, 0.2117% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0272/result.json) |
| n0273 / 완료 | b04→c093 / n0265 | bound: 0.15→0.5; features: age→season; n_estimators: 300→160; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | 13.8530 (-0.8773%) | 12.0635 (0.0396%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0273/result.json) |
| n0274 / 완료 | b04→c093 / n0260 | features: core→age; half_life: 365→없음; min_child_samples: 200→1000; reg_lambda: 10.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.9536 (-1.2432%) | 11.8837 (0.4148%) | 0.100802 / -0.0837%, 0.3543% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0274/result.json) |
| n0275 / 완료 | b04→c093 / n0270 | features: season→core; min_child_samples: 1000→500; mode: additive→multiplicative; num_leaves: 3→15 (여러 설정 동시 변경) | 13.3953 (1.9068%) | 11.9497 (0.8122%) | 0.018839 / -0.0034%, 0.0449% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0275/result.json) |
| n0276 / 완료 | b04→c093 / n0261 | bound: 0.15→0.2; learning_rate: 0.025→0.05; min_child_samples: 500→1000; mode: multiplicative→additive; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.7839 (3.9429%) | 12.1792 (1.7761%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0276/result.json) |
| n0277 / 완료 | b04→c093 / n0276 | bound: 0.2→0.5; features: season→age; mode: additive→multiplicative; num_leaves: 15→7 (여러 설정 동시 변경) | 13.2707 (-3.7229%) | 12.0107 (-1.3831%) | 0.062824 / -0.0435%, 0.1840% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0277/result.json) |
| n0278 / 완료 | b04→c093 / n0262 | bound: 0.3→0.2; features: age→core; min_child_samples: 1000→500; reg_lambda: 30.0→2.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.6162 (4.4049%) | 11.9116 (0.4663%) | 0.028345 / -0.0135%, 0.0311% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0278/result.json) |
| n0279 / 완료 | b04→c093 / n0264 | bound: 0.3→0.15; mode: additive→multiplicative; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.7054 (5.0935%) | 12.1392 (2.1104%) | 0.050907 / -0.0346%, 0.1891% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0279/result.json) |
| n0280 / 완료 | b04→c093 / n0264 | bound: 0.3→0.2; features: season→age; learning_rate: 0.05→0.025; n_estimators: 80→160; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.6204 (4.4419%) | 11.9458 (0.4835%) | 0.028185 / -0.0112%, 0.0481% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0280/result.json) |
| n0281 / 완료 | b04→c093 / n0261 | features: season→core; min_child_samples: 500→200; n_estimators: 160→300; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | 13.2214 (-0.2984%) | 11.9943 (0.2309%) | 0.076880 / -0.0585%, 0.2796% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0281/result.json) |
| n0282 / 완료 | b04→c093 / n0262 | bound: 0.3→0.2; features: age→season; half_life: 365→180; shrink: 0.25→1.0 (여러 설정 동시 변경) | 14.3358 (9.9230%) | 12.1989 (2.8894%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0282/result.json) |
| n0283 / 완료 | b04→c093 / n0271 | bound: 0.3→0.5; learning_rate: 0.05→0.025; reg_lambda: 10.0→30.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.3780 (1.3710%) | 11.9737 (0.7342%) | 0.016076 / -0.0022%, 0.0384% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0283/result.json) |
| n0284 / 완료 | b04→c093 / n0264 | features: season→core; min_child_samples: 200→500; num_leaves: 7→3; shrink: 0.25→0.5 (여러 설정 동시 변경) | 13.1780 (1.0492%) | 11.8773 (-0.0923%) | 0.086824 / -0.0741%, 0.2669% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0284/result.json) |
| n0285 / 완료 | b04→c093 / n0267 | bound: 0.3→0.5; n_estimators: 80→160; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.2107 (2.2208%) | 12.0289 (1.1665%) | 0.078500 / -0.0738%, 0.2911% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0285/result.json) |
| n0286 / 완료 | b04→c093 / n0268 | min_child_samples: 500→1000; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.1193 (0.4896%) | 11.8414 (0.1856%) | 0.099675 / -0.1027%, 0.2195% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0286/result.json) |
| n0287 / 완료 | b04→c093 / n0260 | bound: 0.1→0.15; half_life: 365→180; mode: additive→multiplicative; n_estimators: 160→300 (여러 설정 동시 변경) | 13.1032 (-0.1028%) | 11.8339 (-0.0058%) | 0.067365 / -0.0421%, 0.1533% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0287/result.json) |
| n0288 / 완료 | b04→c093 / n0278 | features: core→season; half_life: 365→180; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 13.7957 (1.3183%) | 11.9793 (0.5682%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0288/result.json) |
| n0289 / 완료 | b04→c093 / n0265 | min_child_samples: 500→200; n_estimators: 300→80; num_leaves: 7→3; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 13.2031 (-5.5277%) | 12.0712 (0.1032%) | 0.065669 / -0.0513%, 0.2579% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0289/result.json) |
| n0290 / 완료 | b04→c093 / n0278 | bound: 0.2→0.1; half_life: 365→없음; min_child_samples: 500→200; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 13.5612 (-0.4036%) | 11.9653 (0.4503%) | 0.036203 / -0.0197%, 0.0804% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0290/result.json) |
| n0291 / 완료 | b04→c093 / n0279 | bound: 0.15→0.3; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 13.6820 (-0.1708%) | 12.1549 (0.1292%) | 0.039819 / -0.0254%, 0.1511% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0291/result.json) |
| n0292 / 완료 | b04→c093 / n0262 | bound: 0.3→0.1; num_leaves: 7→3; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.5957 (4.2478%) | 12.0091 (1.2884%) | 0.056516 / -0.0400%, 0.1010% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0292/result.json) |
| n0293 / 완료 | b04→c093 / n0269 | num_leaves: 3→7; reg_lambda: 30.0→2.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.4242 (3.6418%) | 11.9364 (0.7891%) | 0.036409 / -0.0169%, 0.0623% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0293/result.json) |
| n0294 / 완료 | b04→c093 / n0262 | bound: 0.3→0.1; features: age→season; half_life: 365→없음; learning_rate: 0.05→0.025 (여러 설정 동시 변경) | 13.0216 (-0.1543%) | 11.8936 (0.3143%) | 0.071440 / -0.0483%, 0.2385% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0294/result.json) |
| n0295 / 완료 | b04→c093 / n0277 | bound: 0.5→0.3; learning_rate: 0.05→0.025; n_estimators: 160→300 (여러 설정 동시 변경) | 13.2727 (0.0150%) | 11.9969 (-0.1150%) | 0.060493 / -0.0338%, 0.1793% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0295/result.json) |
| n0296 / 완료 | b04→c093 / n0260 | bound: 0.1→0.3; learning_rate: 0.05→0.025; n_estimators: 160→80; num_leaves: 3→15 (여러 설정 동시 변경) | 13.2003 (0.6379%) | 11.8638 (0.2465%) | 0.048021 / -0.0244%, 0.1261% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0296/result.json) |
| n0297 / 완료 | b04→c093 / n0281 | features: core→season; reg_lambda: 2.0→30.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | 14.0401 (6.1921%) | 12.2809 (2.3896%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0297/result.json) |
| n0298 / 완료 | b04→c093 / n0295 | mode: multiplicative→additive; n_estimators: 300→80; shrink: 0.75→1.0 (여러 설정 동시 변경) | 13.4389 (1.2519%) | 11.9018 (-0.7933%) | 0.047193 / -0.0329%, 0.1082% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0298/result.json) |
| n0299 / 완료 | b04→c093 / n0279 | features: season→core; learning_rate: 0.05→0.025; reg_lambda: 2.0→10.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.9909 (-5.2134%) | 11.9029 (-1.9467%) | 0.095441 / -0.0743%, 0.3483% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0299/result.json) |
| n0300 / 완료 | b04→c093 / n0264 | bound: 0.3→0.2; half_life: 없음→180; learning_rate: 0.05→0.025; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 12.9774 (-0.4890%) | 11.8546 (-0.2830%) | 0.076276 / -0.0526%, 0.2445% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0300/result.json) |
| n0301 / 완료 | b04→c093 / n0267 | features: season→age; half_life: 180→365 (여러 설정 동시 변경) | 12.9240 (0.0020%) | 11.8991 (0.0744%) | 0.098023 / -0.0812%, 0.3718% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0301/result.json) |
| n0302 / 완료 | b04→c093 / n0264 | features: season→core; n_estimators: 80→160; num_leaves: 7→3 (여러 설정 동시 변경) | 13.0369 (-0.0326%) | 11.8585 (-0.2506%) | 0.091092 / -0.0703%, 0.2866% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0302/result.json) |
| n0303 / 완료 | b04→c093 / n0265 | bound: 0.15→0.5; features: age→season; min_child_samples: 500→1000; shrink: 1.0→0.5 (여러 설정 동시 변경) | 13.3089 (-4.7707%) | 11.8988 (-1.3263%) | 0.012705 / -0.0012%, 0.0289% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0303/result.json) |
| n0304 / 완료 | b04→c093 / n0264 | features: season→age; half_life: 없음→365; shrink: 0.25→0.5 (여러 설정 동시 변경) | 13.1528 (0.8561%) | 11.8672 (-0.1776%) | 0.052393 / -0.0298%, 0.1442% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0304/result.json) |
| n0305 / 완료 | b04→c093 / n0275 | learning_rate: 0.05→0.025; min_child_samples: 500→200; n_estimators: 300→160 (여러 설정 동시 변경) | 13.2389 (-1.1673%) | 11.9227 (-0.2258%) | 0.035735 / -0.0142%, 0.1011% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0305/result.json) |
| n0306 / 완료 | b04→c093 / n0264 | n_estimators: 80→300; reg_lambda: 2.0→30.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | 13.3027 (2.0055%) | 11.9771 (0.7470%) | 0.027713 / -0.0109%, 0.0903% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0306/result.json) |
| n0307 / 완료 | b04→c093 / n0277 | half_life: 없음→365; num_leaves: 7→3; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 13.1173 (-1.1561%) | 12.0023 (-0.0702%) | 0.086068 / -0.0794%, 0.3235% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0307/result.json) |
| n0308 / 완료 | b04→c093 / n0260 | reg_lambda: 10.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.9821 (-1.0259%) | 11.8398 (0.0437%) | 0.095623 / -0.0733%, 0.2942% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0308/result.json) |
| n0309 / 완료 | b04→c093 / n0285 | half_life: 180→365; min_child_samples: 500→200; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 13.2293 (0.1407%) | 12.0416 (0.1056%) | 0.082537 / -0.0850%, 0.3279% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0309/result.json) |
| n0310 / 완료 | b04→c093 / n0268 | bound: 0.1→0.2; half_life: 180→없음 (여러 설정 동시 변경) | 13.0727 (0.1329%) | 11.9032 (0.7087%) | 0.085247 / -0.0684%, 0.2882% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0310/result.json) |
| n0311 / 완료 | b04→c093 / n0285 | features: season→core; half_life: 180→없음 (여러 설정 동시 변경) | 13.3817 (1.2944%) | 12.0274 (-0.0125%) | 0.083121 / -0.0798%, 0.3099% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0311/result.json) |
| n0312 / 완료 | b04→c093 / n0288 | bound: 0.2→0.1; num_leaves: 7→15; shrink: 0.75→0.5 (여러 설정 동시 변경) | 13.4558 (-2.4635%) | 11.9128 (-0.5552%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0312/result.json) |
| n0313 / 완료 | b04→c093 / n0291 | features: season→age (단일 설정 차이) | 13.5365 (-1.0630%) | 12.1152 (-0.3264%) | 0.032026 / -0.0149%, 0.1057% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0313/result.json) |
| n0314 / 완료 | b04→c093 / n0272 | min_child_samples: 1000→200; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 13.2730 (0.2069%) | 11.9283 (0.0163%) | 0.046706 / -0.0245%, 0.1353% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0314/result.json) |
| n0315 / 완료 | b04→c093 / n0275 | bound: 0.3→0.5; features: core→season; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 13.4451 (0.3719%) | 11.9866 (0.3086%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0315/result.json) |
| n0316 / 완료 | b04→c093 / n0286 | half_life: 180→없음; num_leaves: 3→7 (여러 설정 동시 변경) | 13.4083 (2.2033%) | 11.9377 (0.8135%) | 0.019622 / -0.0055%, 0.0406% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0316/result.json) |
| n0317 / 완료 | b04→c093 / n0269 | half_life: 180→365; n_estimators: 160→80; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | 12.9399 (-0.0973%) | 11.8838 (0.3444%) | 0.101125 / -0.0813%, 0.3678% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0317/result.json) |
| n0318 / 완료 | b04→c093 / n0270 | n_estimators: 300→160; reg_lambda: 30.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.4391 (2.2400%) | 11.9330 (0.6713%) | 0.080813 / -0.0904%, 0.1641% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0318/result.json) |
| n0319 / 완료 | b04→c093 / n0285 | features: season→age; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 13.2190 (0.0629%) | 12.0529 (0.1990%) | 0.074158 / -0.0693%, 0.2842% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0319/result.json) |
| n0320 / 완료 | b05→c185 / n0320 | 변경 없음(비교 기준 자체) (기준 자체) | 12.7788 (0.0000%) | 12.1132 (0.0000%) | 0.160392 / -0.3356%, 0.7227% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0320/result.json) |
| n0321 / 완료 | b05→c185 / n0320 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | 12.7585 (-0.1592%) | 12.0841 (-0.2401%) | 0.165297 / -0.3298%, 0.7307% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0321/result.json) |
| n0322 / 완료 | b05→c185 / n0320 | half_life: 없음→365 (단일 설정 차이) | 12.7139 (-0.5082%) | 12.1597 (0.3838%) | 0.167266 / -0.3394%, 0.8330% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0322/result.json) |
| n0323 / 완료 | b05→c185 / n0321 | half_life: 없음→365 (단일 설정 차이) | 12.7115 (-0.3680%) | 12.1055 (0.1768%) | 0.168326 / -0.3357%, 0.7935% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0323/result.json) |
| n0324 / 완료 | b05→c185 / n0320 | bound: 0.2→0.3; learning_rate: 0.0→0.05; method: median→tree; min_child_samples: 0→500; n_estimators: 0→160; num_leaves: 0→7; reg_lambda: 0.0→30.0 (여러 설정 동시 변경) | 13.1416 (2.8391%) | 11.9675 (-1.2030%) | 0.131783 / -0.2591%, 0.3730% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0324/result.json) |
| n0325 / 완료 | b05→c185 / n0324 | features: core→season; min_child_samples: 500→1000; mode: additive→multiplicative; n_estimators: 160→300; num_leaves: 7→15; reg_lambda: 30.0→10.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.8782 (-2.0046%) | 12.0500 (0.6898%) | 0.112409 / -0.1543%, 0.4073% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0325/result.json) |
| n0326 / 완료 | b05→c185 / n0324 | bound: 0.3→0.1; features: core→age; half_life: 없음→180; learning_rate: 0.05→0.025; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.8363 (-2.3233%) | 11.9535 (-0.1171%) | 0.144868 / -0.2396%, 0.4559% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0326/result.json) |
| n0327 / 완료 | b05→c185 / n0325 | features: season→core; half_life: 없음→180; learning_rate: 0.05→0.025; min_child_samples: 1000→200; num_leaves: 15→7; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.6653 (6.1121%) | 12.0266 (-0.1942%) | 0.086379 / -0.1299%, 0.0403% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0327/result.json) |
| n0328 / 완료 | b05→c185 / n0324 | features: core→season; half_life: 없음→365; min_child_samples: 500→200; num_leaves: 7→15; reg_lambda: 30.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | 14.3277 (9.0254%) | 12.1295 (1.3534%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0328/result.json) |
| n0329 / 완료 | b05→c185 / n0325 | features: season→age; half_life: 없음→180; learning_rate: 0.05→0.025; num_leaves: 15→3; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 12.7496 (-0.9985%) | 12.0129 (-0.3083%) | 0.162868 / -0.3155%, 0.6131% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0329/result.json) |
| n0330 / 완료 | b05→c185 / n0324 | bound: 0.3→0.1; min_child_samples: 500→1000; num_leaves: 7→3 (여러 설정 동시 변경) | 13.1261 (-0.1183%) | 11.9551 (-0.1039%) | 0.125692 / -0.2570%, 0.3415% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0330/result.json) |
| n0331 / 완료 | b05→c185 / n0325 | half_life: 없음→365; min_child_samples: 1000→500; n_estimators: 300→80; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | 12.8761 (-0.0166%) | 12.0070 (-0.3575%) | 0.132991 / -0.2209%, 0.4596% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0331/result.json) |
| n0332 / 완료 | b05→c185 / n0328 | bound: 0.3→0.1; features: season→age; n_estimators: 160→300; num_leaves: 15→7; shrink: 1.0→0.5 (여러 설정 동시 변경) | 13.1370 (-8.3108%) | 11.8893 (-1.9798%) | 0.074512 / -0.0680%, 0.1118% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0332/result.json) |
| n0333 / 완료 | b05→c185 / n0327 | bound: 0.3→0.5; half_life: 180→365; min_child_samples: 200→1000; num_leaves: 7→3; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.9351 (-5.3440%) | 12.0063 (-0.1689%) | 0.141090 / -0.2936%, 0.4807% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0333/result.json) |
| n0334 / 완료 | b05→c185 / n0326 | features: age→season; half_life: 180→없음; n_estimators: 160→80; reg_lambda: 30.0→2.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.5477 (5.5417%) | 12.0326 (0.6623%) | 0.097642 / -0.2049%, 0.2990% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0334/result.json) |
| n0335 / 완료 | b05→c185 / n0325 | features: season→age; num_leaves: 15→7; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | 12.8121 (-0.5133%) | 11.9678 (-0.6822%) | 0.141518 / -0.2476%, 0.4521% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0335/result.json) |
| n0336 / 완료 | b05→c185 / n0324 | bound: 0.3→0.1; half_life: 없음→365; n_estimators: 160→80; reg_lambda: 30.0→10.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.3794 (1.8089%) | 11.8976 (-0.5839%) | 0.101174 / -0.1751%, 0.1699% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0336/result.json) |
| n0337 / 완료 | b05→c185 / n0329 | features: age→season; min_child_samples: 1000→200; n_estimators: 300→80 (여러 설정 동시 변경) | 12.7173 (-0.2536%) | 12.0481 (0.2930%) | 0.164408 / -0.3226%, 0.6727% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0337/result.json) |
| n0338 / 완료 | b05→c185 / n0326 | bound: 0.1→0.3; half_life: 180→365; n_estimators: 160→80; num_leaves: 7→3; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | 12.7045 (-1.0268%) | 12.0396 (0.7203%) | 0.171692 / -0.3448%, 0.6896% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0338/result.json) |
| n0339 / 완료 | b05→c185 / n0324 | bound: 0.3→0.15; half_life: 없음→365; mode: additive→multiplicative; n_estimators: 160→80 (여러 설정 동시 변경) | 13.0039 (-1.0481%) | 11.9937 (0.2194%) | 0.137214 / -0.2890%, 0.4418% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0339/result.json) |
| n0340 / 완료 | b05→c185 / n0334 | bound: 0.1→0.2; half_life: 없음→180; learning_rate: 0.025→0.05; min_child_samples: 500→1000; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 13.7447 (1.4547%) | 11.9789 (-0.4463%) | 0.063744 / -0.0834%, 0.0461% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0340/result.json) |
| n0341 / 완료 | b05→c185 / n0335 | bound: 0.3→0.15; reg_lambda: 2.0→30.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | 13.0717 (2.0261%) | 11.9765 (0.0724%) | 0.098609 / -0.1338%, 0.2483% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0341/result.json) |
| n0342 / 완료 | b05→c185 / n0325 | bound: 0.3→0.1; features: season→core; mode: multiplicative→additive; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.5404 (5.1421%) | 12.1634 (0.9404%) | 0.089223 / -0.1285%, 0.2633% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0342/result.json) |
| n0343 / 완료 | b05→c185 / n0325 | bound: 0.3→0.5; learning_rate: 0.05→0.025; n_estimators: 300→80; reg_lambda: 10.0→30.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | 13.0328 (1.2002%) | 12.0744 (0.2020%) | 0.127030 / -0.2333%, 0.4941% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0343/result.json) |
| n0344 / 완료 | b05→c185 / n0326 | reg_lambda: 30.0→10.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.7047 (6.7650%) | 11.9434 (-0.0845%) | 0.056116 / -0.0656%, 0.0346% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0344/result.json) |
| n0345 / 완료 | b05→c185 / n0325 | bound: 0.3→0.5; features: season→core; half_life: 없음→180; min_child_samples: 1000→200; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 12.9075 (0.2277%) | 11.9422 (-0.8945%) | 0.113546 / -0.1559%, 0.2956% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0345/result.json) |
| n0346 / 완료 | b05→c185 / n0328 | half_life: 365→180; min_child_samples: 200→500; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.9331 (-2.7544%) | 11.9868 (-1.1757%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0346/result.json) |
| n0347 / 완료 | b05→c185 / n0335 | bound: 0.3→0.15; min_child_samples: 1000→200; n_estimators: 300→80 (여러 설정 동시 변경) | 12.7868 (-0.1972%) | 12.0123 (0.3712%) | 0.152011 / -0.2969%, 0.5577% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0347/result.json) |
| n0348 / 완료 | b05→c185 / n0338 | bound: 0.3→0.2; features: age→core; num_leaves: 3→15 (여러 설정 동시 변경) | 12.8364 (1.0383%) | 11.9664 (-0.6080%) | 0.155443 / -0.2844%, 0.5023% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0348/result.json) |
| n0349 / 완료 | b05→c185 / n0325 | bound: 0.3→0.5; learning_rate: 0.05→0.025; min_child_samples: 1000→500 (여러 설정 동시 변경) | 12.8531 (-0.1948%) | 12.0618 (0.0973%) | 0.135194 / -0.2263%, 0.5235% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0349/result.json) |
| n0350 / 완료 | b05→c185 / n0338 | min_child_samples: 500→200; reg_lambda: 10.0→30.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | 12.8131 (0.8545%) | 12.0314 (-0.0681%) | 0.161477 / -0.3289%, 0.6449% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0350/result.json) |
| n0351 / 완료 | b05→c185 / n0327 | half_life: 180→없음; min_child_samples: 200→1000; n_estimators: 300→160 (여러 설정 동시 변경) | 13.6317 (-0.2461%) | 12.1290 (0.8514%) | 0.104677 / -0.2669%, 0.3191% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0351/result.json) |
| n0352 / 완료 | b05→c185 / n0328 | bound: 0.3→0.2; reg_lambda: 2.0→2.5; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.6832 (-4.4981%) | 12.0963 (-0.2735%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0352/result.json) |
| n0353 / 완료 | b05→c185 / n0329 | min_child_samples: 1000→500; reg_lambda: 30.0→2.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | 12.8901 (1.1015%) | 11.9953 (-0.1464%) | 0.140026 / -0.2777%, 0.4857% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0353/result.json) |
| n0354 / 완료 | b05→c185 / n0324 | bound: 0.3→0.2; min_child_samples: 500→200; n_estimators: 160→300; num_leaves: 7→15 (여러 설정 동시 변경) | 13.1991 (0.4371%) | 12.0110 (0.3635%) | 0.095215 / -0.1147%, 0.2661% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0354/result.json) |
| n0355 / 완료 | b05→c185 / n0339 | bound: 0.15→0.5; features: core→season; min_child_samples: 500→200; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | 13.0114 (0.0573%) | 11.9894 (-0.0361%) | 0.125293 / -0.2142%, 0.4080% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0355/result.json) |
| n0356 / 완료 | b05→c185 / n0338 | bound: 0.3→0.2; num_leaves: 3→7 (여러 설정 동시 변경) | 12.7731 (0.5399%) | 11.9926 (-0.3906%) | 0.152149 / -0.2825%, 0.5377% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0356/result.json) |
| n0357 / 완료 | b05→c185 / n0330 | bound: 0.1→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | 12.9836 (-1.0856%) | 12.0480 (0.7773%) | 0.146745 / -0.3181%, 0.5315% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0357/result.json) |
| n0358 / 완료 | b05→c185 / n0328 | min_child_samples: 200→500; n_estimators: 160→300; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 14.4876 (1.1162%) | 12.2459 (0.9601%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0358/result.json) |
| n0359 / 완료 | b05→c185 / n0353 | half_life: 180→365; learning_rate: 0.025→0.05; n_estimators: 300→160 (여러 설정 동시 변경) | 12.8969 (0.0535%) | 12.0308 (0.2959%) | 0.145622 / -0.2947%, 0.5368% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0359/result.json) |
| n0360 / 완료 | b05→c185 / n0330 | half_life: 없음→180; min_child_samples: 1000→500; n_estimators: 160→300; reg_lambda: 30.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.6670 (4.1205%) | 11.9448 (-0.0855%) | 0.071330 / -0.0994%, 0.0007% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0360/result.json) |
| n0361 / 완료 | b05→c185 / n0324 | features: core→season; mode: additive→multiplicative; reg_lambda: 30.0→10.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.3369 (1.4858%) | 12.1067 (1.1636%) | 0.103769 / -0.2018%, 0.3328% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0361/result.json) |
| n0362 / 완료 | b05→c185 / n0347 | bound: 0.15→0.2; min_child_samples: 200→500; mode: multiplicative→additive (여러 설정 동시 변경) | 12.8134 (0.2079%) | 11.9797 (-0.2708%) | 0.156198 / -0.2900%, 0.5323% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0362/result.json) |
| n0363 / 완료 | b05→c185 / n0327 | bound: 0.3→0.5; learning_rate: 0.025→0.05; n_estimators: 300→80; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | 13.4586 (-1.5128%) | 12.0068 (-0.1653%) | 0.085114 / -0.1211%, 0.1266% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0363/result.json) |
| n0364 / 완료 | b05→c185 / n0343 | bound: 0.5→0.3; mode: multiplicative→additive; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.8726 (-1.2291%) | 12.0350 (-0.3259%) | 0.143145 / -0.2648%, 0.5302% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0364/result.json) |
| n0365 / 완료 | b05→c185 / n0335 | n_estimators: 300→160; reg_lambda: 2.0→30.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.6679 (6.6795%) | 12.0907 (1.0269%) | 0.064404 / -0.0962%, 0.1220% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0365/result.json) |
| n0366 / 완료 | b05→c185 / n0330 | bound: 0.1→0.2; half_life: 없음→365; n_estimators: 160→80; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.7776 (-2.6546%) | 11.9914 (0.3040%) | 0.157668 / -0.3177%, 0.5552% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0366/result.json) |
| n0367 / 완료 | b05→c185 / n0337 | half_life: 180→없음; min_child_samples: 200→1000; reg_lambda: 30.0→2.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | 12.9185 (1.5819%) | 12.1070 (0.4888%) | 0.145983 / -0.3243%, 0.6390% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0367/result.json) |
| n0368 / 완료 | b05→c185 / n0326 | half_life: 180→365; min_child_samples: 500→1000; n_estimators: 160→300; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.9350 (8.5592%) | 12.0004 (0.3922%) | 0.035480 / -0.0294%, -0.0067% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0368/result.json) |
| n0369 / 완료 | b05→c185 / n0327 | bound: 0.3→0.5; n_estimators: 300→80 (여러 설정 동시 변경) | 13.1993 (-3.4100%) | 12.0552 (0.2376%) | 0.113890 / -0.1940%, 0.3557% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0369/result.json) |
| n0370 / 완료 | b05→c185 / n0330 | features: core→season; half_life: 없음→180; learning_rate: 0.05→0.025; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 12.8208 (-2.3261%) | 11.9574 (0.0194%) | 0.154500 / -0.3028%, 0.5223% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0370/result.json) |
| n0371 / 완료 | b05→c185 / n0347 | min_child_samples: 200→500; shrink: 0.25→0.5 (여러 설정 동시 변경) | 12.9338 (1.1490%) | 11.9994 (-0.1067%) | 0.139132 / -0.2595%, 0.4826% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0371/result.json) |
| n0372 / 완료 | b05→c185 / n0368 | features: age→core; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.4887 (-3.2029%) | 11.9476 (-0.4394%) | 0.093350 / -0.1556%, 0.1314% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0372/result.json) |
| n0373 / 완료 | b05→c185 / n0343 | min_child_samples: 1000→200; n_estimators: 80→160 (여러 설정 동시 변경) | 13.0912 (0.4480%) | 12.0570 (-0.1440%) | 0.118697 / -0.2032%, 0.4258% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0373/result.json) |
| n0374 / 완료 | b05→c185 / n0338 | half_life: 365→180; learning_rate: 0.025→0.05; n_estimators: 80→300; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.2885 (4.5967%) | 11.8713 (-1.3976%) | 0.098982 / -0.1527%, 0.1084% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0374/result.json) |
| n0375 / 완료 | b05→c185 / n0351 | bound: 0.3→0.15; half_life: 없음→180; num_leaves: 7→3; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | 13.0899 (-3.9748%) | 12.0616 (-0.5563%) | 0.120030 / -0.2218%, 0.4186% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0375/result.json) |
| n0376 / 완료 | b05→c185 / n0334 | bound: 0.1→0.2; half_life: 없음→180; n_estimators: 80→300 (여러 설정 동시 변경) | 14.1393 (4.3673%) | 11.9764 (-0.4674%) | 0.024112 / -0.0103%, -0.0106% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0376/result.json) |
| n0377 / 완료 | b05→c185 / n0338 | learning_rate: 0.025→0.05; min_child_samples: 500→200; mode: additive→multiplicative; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.0687 (2.8662%) | 12.1432 (0.8602%) | 0.120736 / -0.2301%, 0.4936% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0377/result.json) |
| n0378 / 완료 | b05→c185 / n0372 | bound: 0.1→0.2; half_life: 365→180; n_estimators: 300→160; num_leaves: 7→15 (여러 설정 동시 변경) | 13.6185 (0.9625%) | 11.9050 (-0.3565%) | 0.067650 / -0.0773%, 0.0310% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0378/result.json) |
| n0379 / 완료 | b05→c185 / n0331 | bound: 0.3→0.15; learning_rate: 0.05→0.025; min_child_samples: 500→200; n_estimators: 80→300 (여러 설정 동시 변경) | 12.8847 (0.0671%) | 12.0196 (0.1057%) | 0.122063 / -0.1853%, 0.4286% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0379/result.json) |
| n0380 / 완료 | b05→c185 / n0332 | bound: 0.1→0.3; min_child_samples: 200→1000; n_estimators: 300→80 (여러 설정 동시 변경) | 13.0768 (-0.4582%) | 11.8930 (0.0306%) | 0.101305 / -0.1549%, 0.2305% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0380/result.json) |
| n0381 / 완료 | b05→c185 / n0335 | features: age→core; min_child_samples: 1000→200 (여러 설정 동시 변경) | 12.8080 (-0.0317%) | 12.0245 (0.4739%) | 0.165612 / -0.3446%, 0.6050% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0381/result.json) |
| n0382 / 완료 | b05→c185 / n0325 | half_life: 없음→180; min_child_samples: 1000→200; mode: multiplicative→additive; n_estimators: 300→80 (여러 설정 동시 변경) | 12.9095 (0.2428%) | 11.9930 (-0.4732%) | 0.115237 / -0.1692%, 0.3633% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0382/result.json) |
| n0383 / 완료 | b05→c185 / n0325 | features: season→age; n_estimators: 300→160; num_leaves: 15→3 (여러 설정 동시 변경) | 12.7544 (-0.9616%) | 12.0571 (0.0586%) | 0.165809 / -0.3294%, 0.6689% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0383/result.json) |
| n0384 / 완료 | b06→c117 / n0384 | 변경 없음(비교 기준 자체) (기준 자체) | 12.7363 (0.0000%) | 12.0553 (0.0000%) | 0.193391 / -0.3535%, 0.9759% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0384/result.json) |
| n0385 / 완료 | b06→c117 / n0384 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | 12.7134 (-0.1797%) | 12.0348 (-0.1694%) | 0.191947 / -0.3459%, 0.9534% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0385/result.json) |
| n0386 / 완료 | b06→c117 / n0384 | half_life: 없음→365 (단일 설정 차이) | 12.6594 (-0.6037%) | 12.1074 (0.4328%) | 0.198038 / -0.3607%, 1.0920% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0386/result.json) |
| n0387 / 완료 | b06→c117 / n0385 | half_life: 없음→365 (단일 설정 차이) | 12.6573 (-0.4411%) | 12.0652 (0.2525%) | 0.196930 / -0.3555%, 1.0407% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0387/result.json) |
| n0388 / 완료 | b06→c117 / n0384 | half_life: 없음→180; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→200; n_estimators: 0→80; num_leaves: 0→15; reg_lambda: 0.0→30.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.7172 (-0.1499%) | 11.9368 (-0.9831%) | 0.167058 / -0.2508%, 0.6280% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0388/result.json) |
| n0389 / 완료 | b06→c117 / n0385 | features: core→season; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→200; n_estimators: 0→160; num_leaves: 0→3; reg_lambda: 0.0→10.0 (여러 설정 동시 변경) | 12.8216 (0.8514%) | 12.0332 (-0.0138%) | 0.170440 / -0.3264%, 0.7657% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0389/result.json) |
| n0390 / 완료 | b06→c117 / n0389 | bound: 0.3→0.1; features: season→age; mode: multiplicative→additive; n_estimators: 160→80; shrink: 0.5→0.75 (여러 설정 동시 변경) | 12.8029 (-0.1461%) | 12.0179 (-0.1271%) | 0.170479 / -0.3252%, 0.7614% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0390/result.json) |
| n0391 / 완료 | b06→c117 / n0389 | bound: 0.3→0.15; features: season→core; half_life: 없음→365; learning_rate: 0.025→0.05; min_child_samples: 200→500; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.1187 (2.3170%) | 12.0307 (-0.0209%) | 0.116396 / -0.2177%, 0.3253% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0391/result.json) |
| n0392 / 완료 | b06→c117 / n0391 | bound: 0.15→0.1; features: core→season; half_life: 365→180; mode: multiplicative→additive; n_estimators: 160→300; num_leaves: 3→15 (여러 설정 동시 변경) | 14.2963 (8.9767%) | 12.2901 (2.1560%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0392/result.json) |
| n0393 / 완료 | b06→c117 / n0390 | bound: 0.1→0.15; half_life: 없음→180; min_child_samples: 200→1000; mode: additive→multiplicative; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | 12.7345 (-0.5341%) | 12.0174 (-0.0040%) | 0.167947 / -0.3024%, 0.7563% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0393/result.json) |
| n0394 / 완료 | b06→c117 / n0391 | bound: 0.15→0.3; mode: multiplicative→additive; n_estimators: 160→300; num_leaves: 3→7; reg_lambda: 10.0→2.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | 13.0421 (-0.5840%) | 11.9321 (-0.8195%) | 0.120866 / -0.1495%, 0.2796% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0394/result.json) |
| n0395 / 완료 | b06→c117 / n0393 | features: age→season; n_estimators: 80→300; num_leaves: 3→15; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 13.5548 (6.4414%) | 12.0322 (0.1233%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0395/result.json) |
| n0396 / 완료 | b06→c117 / n0392 | features: season→age; learning_rate: 0.05→0.025; num_leaves: 15→7; reg_lambda: 10.0→2.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.7397 (-10.8885%) | 11.9066 (-3.1198%) | 0.158705 / -0.2244%, 0.5312% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0396/result.json) |
| n0397 / 완료 | b06→c117 / n0391 | bound: 0.15→0.5; learning_rate: 0.05→0.025; num_leaves: 3→15; reg_lambda: 10.0→30.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.3117 (1.4712%) | 12.0595 (0.2398%) | 0.093268 / -0.1048%, 0.2421% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0397/result.json) |
| n0398 / 완료 | b06→c117 / n0392 | bound: 0.1→0.2; half_life: 180→365; n_estimators: 300→160; reg_lambda: 10.0→2.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.6320 (-4.6469%) | 12.1196 (-1.3865%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0398/result.json) |
| n0399 / 완료 | b06→c117 / n0393 | bound: 0.15→0.5; learning_rate: 0.025→0.05; n_estimators: 80→300; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 12.9030 (1.3230%) | 11.9729 (-0.3706%) | 0.123859 / -0.2346%, 0.2749% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0399/result.json) |
| n0400 / 완료 | b06→c117 / n0392 | features: season→core; min_child_samples: 500→1000; reg_lambda: 10.0→2.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.5648 (-5.1170%) | 11.9842 (-2.4886%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0400/result.json) |
| n0401 / 완료 | b06→c117 / n0389 | half_life: 없음→180; min_child_samples: 200→1000; n_estimators: 160→80; num_leaves: 3→15 (여러 설정 동시 변경) | 12.8563 (0.2703%) | 11.9747 (-0.4864%) | 0.128577 / -0.1913%, 0.4816% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0401/result.json) |
| n0402 / 완료 | b06→c117 / n0396 | half_life: 180→없음; min_child_samples: 500→1000; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 12.6960 (-0.3428%) | 11.9439 (0.3134%) | 0.165411 / -0.2748%, 0.6191% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0402/result.json) |
| n0403 / 완료 | b06→c117 / n0389 | features: season→core; half_life: 없음→365; learning_rate: 0.025→0.05 (여러 설정 동시 변경) | 12.8084 (-0.1031%) | 11.9575 (-0.6288%) | 0.163381 / -0.2868%, 0.5991% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0403/result.json) |
| n0404 / 완료 | b06→c117 / n0392 | half_life: 180→없음; min_child_samples: 500→1000; n_estimators: 300→80; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | 13.8558 (-3.0816%) | 12.2545 (-0.2892%) | 0.039872 / -0.0213%, 0.1263% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0404/result.json) |
| n0405 / 완료 | b06→c117 / n0389 | bound: 0.3→0.15; features: season→age; learning_rate: 0.025→0.05; n_estimators: 160→80; num_leaves: 3→7; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 12.7884 (-0.2586%) | 12.0023 (-0.2569%) | 0.158704 / -0.2852%, 0.6411% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0405/result.json) |
| n0406 / 완료 | b06→c117 / n0404 | bound: 0.1→0.2; features: season→core; min_child_samples: 1000→500; num_leaves: 15→3 (여러 설정 동시 변경) | 13.3561 (-3.6064%) | 11.9497 (-2.4876%) | 0.109651 / -0.2125%, 0.2751% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0406/result.json) |
| n0407 / 완료 | b06→c117 / n0399 | bound: 0.5→0.3; features: age→season; reg_lambda: 30.0→2.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | 12.7916 (-0.8633%) | 11.9343 (-0.3218%) | 0.148737 / -0.2785%, 0.4490% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0407/result.json) |
| n0408 / 완료 | b06→c117 / n0390 | half_life: 없음→365; min_child_samples: 200→500; reg_lambda: 10.0→30.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | 12.6525 (-1.1748%) | 11.9716 (-0.3849%) | 0.188268 / -0.3504%, 0.8129% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0408/result.json) |
| n0409 / 완료 | b06→c117 / n0389 | features: season→core; n_estimators: 160→80; reg_lambda: 10.0→2.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | 12.8853 (0.4969%) | 12.0314 (-0.0153%) | 0.156931 / -0.2906%, 0.6907% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0409/result.json) |
| n0410 / 완료 | b06→c117 / n0407 | half_life: 180→365; mode: multiplicative→additive; reg_lambda: 2.0→30.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.7489 (-0.3333%) | 11.9507 (0.1369%) | 0.170693 / -0.2931%, 0.6508% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0410/result.json) |
| n0411 / 완료 | b06→c117 / n0391 | bound: 0.15→0.5; features: core→age; num_leaves: 3→7; reg_lambda: 10.0→2.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.7066 (-3.1410%) | 11.9665 (-0.5337%) | 0.163587 / -0.2617%, 0.6405% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0411/result.json) |
| n0412 / 완료 | b06→c117 / n0400 | half_life: 180→없음; learning_rate: 0.05→0.025; n_estimators: 300→160; shrink: 0.75→0.5 (여러 설정 동시 변경) | 13.0130 (-4.0679%) | 11.9879 (0.0309%) | 0.131082 / -0.2117%, 0.4358% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0412/result.json) |
| n0413 / 완료 | b06→c117 / n0407 | half_life: 180→없음; num_leaves: 3→7; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 12.9527 (1.2594%) | 12.1076 (1.4514%) | 0.111636 / -0.1389%, 0.4467% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0413/result.json) |
| n0414 / 완료 | b06→c117 / n0408 | learning_rate: 0.025→0.05; min_child_samples: 500→1000; n_estimators: 80→160; shrink: 0.25→0.5 (여러 설정 동시 변경) | 12.7526 (0.7910%) | 11.9712 (-0.0034%) | 0.169532 / -0.2952%, 0.6397% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0414/result.json) |
| n0415 / 완료 | b06→c117 / n0391 | min_child_samples: 500→1000; num_leaves: 3→7; reg_lambda: 10.0→30.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.1771 (0.4452%) | 12.0305 (-0.0017%) | 0.122073 / -0.2282%, 0.2948% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0415/result.json) |
| n0416 / 완료 | b06→c117 / n0398 | half_life: 365→없음; learning_rate: 0.05→0.025; n_estimators: 160→300 (여러 설정 동시 변경) | 13.5557 (-0.5592%) | 12.1820 (0.5141%) | 0.020295 / -0.0078%, 0.0648% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0416/result.json) |
| n0417 / 완료 | b06→c117 / n0388 | bound: 0.2→0.3; features: core→age; mode: additive→multiplicative; num_leaves: 15→7 (여러 설정 동시 변경) | 12.6851 (-0.2523%) | 11.9760 (0.3286%) | 0.174513 / -0.2942%, 0.7465% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0417/result.json) |
| n0418 / 완료 | b06→c117 / n0400 | n_estimators: 300→80; num_leaves: 15→7; shrink: 0.75→0.5 (여러 설정 동시 변경) | 12.8591 (-5.2019%) | 11.8696 (-0.9566%) | 0.137208 / -0.2094%, 0.3379% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0418/result.json) |
| n0419 / 완료 | b06→c117 / n0401 | half_life: 180→365; learning_rate: 0.025→0.05; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.3314 (3.6956%) | 12.0921 (0.9809%) | 0.060681 / -0.0437%, 0.1915% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0419/result.json) |
| n0420 / 완료 | b06→c117 / n0394 | bound: 0.3→0.1; features: core→age; min_child_samples: 500→200; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 12.9467 (-0.7316%) | 11.9654 (0.2789%) | 0.089409 / -0.0765%, 0.2388% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0420/result.json) |
| n0421 / 완료 | b06→c117 / n0399 | features: age→core; half_life: 180→없음; learning_rate: 0.05→0.025; shrink: 0.75→0.25 (여러 설정 동시 변경) | 12.6955 (-1.6083%) | 11.9989 (0.2170%) | 0.181980 / -0.3521%, 0.7821% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0421/result.json) |
| n0422 / 완료 | b06→c117 / n0398 | half_life: 365→180; num_leaves: 15→7; reg_lambda: 2.0→30.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | 12.7666 (-6.3480%) | 11.9011 (-1.8032%) | 0.153661 / -0.2196%, 0.5030% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0422/result.json) |
| n0423 / 완료 | b06→c117 / n0399 | bound: 0.5→0.3; min_child_samples: 1000→200; n_estimators: 300→160; shrink: 0.75→1.0 (여러 설정 동시 변경) | 13.0288 (0.9754%) | 12.0611 (0.7371%) | 0.115932 / -0.2237%, 0.3437% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0423/result.json) |
| n0424 / 완료 | b06→c117 / n0388 | bound: 0.2→0.1; min_child_samples: 200→1000; num_leaves: 15→3; shrink: 0.25→0.75 (여러 설정 동시 변경) | 12.7513 (0.2681%) | 11.9730 (0.3035%) | 0.171449 / -0.2985%, 0.6619% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0424/result.json) |
| n0425 / 완료 | b06→c117 / n0416 | bound: 0.2→0.3; half_life: 없음→365; mode: additive→multiplicative; shrink: 0.75→0.25 (여러 설정 동시 변경) | 12.7925 (-5.6302%) | 11.9874 (-1.5972%) | 0.140474 / -0.1790%, 0.5418% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0425/result.json) |
| n0426 / 완료 | b06→c117 / n0390 | bound: 0.1→0.3; n_estimators: 80→160; num_leaves: 3→7 (여러 설정 동시 변경) | 12.9981 (1.5246%) | 11.9692 (-0.4049%) | 0.110362 / -0.1553%, 0.3060% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0426/result.json) |
| n0427 / 완료 | b06→c117 / n0394 | bound: 0.3→0.5; mode: additive→multiplicative (여러 설정 동시 변경) | 13.0310 (-0.0851%) | 11.9672 (0.2946%) | 0.120219 / -0.1660%, 0.3240% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0427/result.json) |
| n0428 / 완료 | b06→c117 / n0398 | min_child_samples: 500→200; n_estimators: 160→80; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 13.4043 (-1.6698%) | 12.0611 (-0.4829%) | 0.042290 / -0.0229%, 0.1090% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0428/result.json) |
| n0429 / 완료 | b06→c117 / n0411 | learning_rate: 0.05→0.025; n_estimators: 160→80; reg_lambda: 2.0→10.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.0185 (2.4541%) | 12.1447 (1.4894%) | 0.107208 / -0.1582%, 0.4486% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0429/result.json) |
| n0430 / 완료 | b06→c117 / n0388 | min_child_samples: 200→1000; n_estimators: 80→300; num_leaves: 15→3; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 12.6846 (-0.2558%) | 11.9213 (-0.1294%) | 0.180463 / -0.3187%, 0.6681% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0430/result.json) |
| n0431 / 완료 | b06→c117 / n0425 | min_child_samples: 500→1000; n_estimators: 300→80; num_leaves: 15→3 (여러 설정 동시 변경) | 12.6532 (-1.0889%) | 11.9857 (-0.0143%) | 0.192798 / -0.3459%, 0.8633% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0431/result.json) |
| n0432 / 완료 | b06→c117 / n0389 | features: season→age; mode: multiplicative→additive; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 12.7603 (-0.4778%) | 11.9813 (-0.4311%) | 0.172391 / -0.3077%, 0.7222% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0432/result.json) |
| n0433 / 완료 | b06→c117 / n0389 | bound: 0.3→0.15; features: season→core; num_leaves: 3→7; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.4805 (5.1387%) | 12.1964 (1.3563%) | 0.105910 / -0.1972%, 0.3940% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0433/result.json) |
| n0434 / 완료 | b06→c117 / n0404 | reg_lambda: 2.0→2.5 (단일 설정 차이) | 13.8558 (0.0000%) | 12.2545 (0.0000%) | 0.039872 / -0.0213%, 0.1263% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0434/result.json) |
| n0435 / 완료 | b06→c117 / n0390 | bound: 0.1→0.3; learning_rate: 0.025→0.05; min_child_samples: 200→500; mode: additive→multiplicative (여러 설정 동시 변경) | 12.8414 (0.3009%) | 12.0959 (0.6490%) | 0.163734 / -0.3092%, 0.7877% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0435/result.json) |
| n0436 / 완료 | b06→c117 / n0412 | num_leaves: 15→3; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.3325 (2.4558%) | 11.9557 (-0.2689%) | 0.114611 / -0.2370%, 0.3003% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0436/result.json) |
| n0437 / 완료 | b06→c117 / n0401 | min_child_samples: 1000→200; n_estimators: 80→300; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | 13.1267 (2.1035%) | 11.9565 (-0.1519%) | 0.050151 / -0.0290%, 0.1381% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0437/result.json) |
| n0438 / 완료 | b06→c117 / n0420 | bound: 0.1→0.3; min_child_samples: 200→1000; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.7616 (6.2943%) | 12.3198 (2.9626%) | 0.005878 / -0.0003%, 0.0044% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0438/result.json) |
| n0439 / 완료 | b06→c117 / n0403 | bound: 0.3→0.15; learning_rate: 0.05→0.025; n_estimators: 160→300; num_leaves: 3→15 (여러 설정 동시 변경) | 13.0489 (1.8779%) | 11.9956 (0.3181%) | 0.103713 / -0.1162%, 0.3144% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0439/result.json) |
| n0440 / 완료 | b06→c117 / n0424 | features: core→season; n_estimators: 80→300; shrink: 0.75→0.5 (여러 설정 동시 변경) | 12.7508 (-0.0035%) | 11.9098 (-0.5273%) | 0.169021 / -0.2951%, 0.5438% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0440/result.json) |
| n0441 / 완료 | b06→c117 / n0402 | bound: 0.1→0.5; mode: additive→multiplicative; n_estimators: 300→80 (여러 설정 동시 변경) | 12.6531 (-0.3376%) | 11.9868 (0.3587%) | 0.189143 / -0.3496%, 0.8382% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0441/result.json) |
| n0442 / 완료 | b06→c117 / n0418 | half_life: 180→365; min_child_samples: 1000→200; reg_lambda: 2.0→30.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.4649 (4.7109%) | 11.9704 (0.8494%) | 0.059456 / -0.0426%, 0.0680% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0442/result.json) |
| n0443 / 완료 | b06→c117 / n0419 | bound: 0.3→0.15; half_life: 365→180; num_leaves: 15→7 (여러 설정 동시 변경) | 12.9811 (-2.6272%) | 12.0325 (-0.4930%) | 0.113512 / -0.1702%, 0.3928% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0443/result.json) |
| n0444 / 완료 | b06→c117 / n0390 | bound: 0.1→0.2; half_life: 없음→365; n_estimators: 80→160; shrink: 0.75→0.25 (여러 설정 동시 변경) | 12.6593 (-1.1213%) | 11.9633 (-0.4541%) | 0.182310 / -0.3293%, 0.7612% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0444/result.json) |
| n0445 / 완료 | b06→c117 / n0433 | learning_rate: 0.025→0.05; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 13.6931 (1.5774%) | 12.2524 (0.4593%) | 0.095751 / -0.1898%, 0.3175% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0445/result.json) |
| n0446 / 완료 | b06→c117 / n0388 | features: core→season; num_leaves: 15→7; reg_lambda: 30.0→2.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.0812 (2.8627%) | 12.0009 (0.5376%) | 0.090068 / -0.1063%, 0.2407% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0446/result.json) |
| n0447 / 완료 | b06→c117 / n0429 | min_child_samples: 500→200; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.7676 (-1.9272%) | 11.9953 (-1.2298%) | 0.158660 / -0.2583%, 0.6714% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0447/result.json) |
| n0448 / 완료 | b07→c000 / n0448 | 변경 없음(비교 기준 자체) (기준 자체) | 12.9466 (0.0000%) | 12.5632 (0.0000%) | 0.037992 / -0.0182%, 0.0860% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0448/result.json) |
| n0449 / 완료 | b07→c000 / n0448 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | 12.9051 (-0.3208%) | 12.5370 (-0.2090%) | 0.028205 / -0.0098%, 0.0639% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0449/result.json) |
| n0450 / 완료 | b07→c000 / n0448 | half_life: 없음→365 (단일 설정 차이) | 12.9468 (0.0015%) | 12.6654 (0.8128%) | 0.035005 / -0.0153%, 0.0939% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0450/result.json) |
| n0451 / 완료 | b07→c000 / n0449 | half_life: 없음→365 (단일 설정 차이) | 12.9083 (0.0245%) | 12.6338 (0.7725%) | 0.025452 / -0.0087%, 0.0654% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0451/result.json) |
| n0452 / 완료 | b07→c000 / n0448 | half_life: 없음→180; learning_rate: 0.0→0.05; method: median→tree; min_child_samples: 0→500; n_estimators: 0→160; num_leaves: 0→3; reg_lambda: 0.0→10.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.9421 (-0.0353%) | 12.6595 (0.7664%) | 0.028317 / -0.0113%, 0.0644% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0452/result.json) |
| n0453 / 완료 | b07→c000 / n0452 | bound: 0.2→0.3; features: core→season; half_life: 180→없음; learning_rate: 0.05→0.025; mode: additive→multiplicative; num_leaves: 3→7 (여러 설정 동시 변경) | 12.8759 (-0.5112%) | 12.4954 (-1.2965%) | 0.014421 / -0.0017%, 0.0303% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0453/result.json) |
| n0454 / 완료 | b07→c000 / n0452 | features: core→age; half_life: 180→365; min_child_samples: 500→1000; n_estimators: 160→80; reg_lambda: 10.0→2.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | 13.1331 (1.4758%) | 12.6619 (0.0187%) | 0.000076 / -0.0000%, 0.0002% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0454/result.json) |
| n0455 / 완료 | b07→c000 / n0453 | bound: 0.3→0.5; features: season→core; n_estimators: 160→80; num_leaves: 7→15; reg_lambda: 10.0→2.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.2832 (3.1636%) | 12.3074 (-1.5046%) | 0.039417 / -0.0195%, 0.0582% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0455/result.json) |
| n0456 / 완료 | b07→c000 / n0453 | mode: multiplicative→additive; n_estimators: 160→300; num_leaves: 7→3; shrink: 0.25→0.5 (여러 설정 동시 변경) | 12.8858 (0.0770%) | 12.2165 (-2.2324%) | 0.040659 / -0.0228%, 0.0563% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0456/result.json) |
| n0457 / 완료 | b07→c000 / n0453 | bound: 0.3→0.15; features: season→age; num_leaves: 7→3; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.1411 (2.0594%) | 12.5679 (0.5798%) | 0.018924 / -0.0037%, 0.0469% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0457/result.json) |
| n0458 / 완료 | b07→c000 / n0456 | features: season→core; n_estimators: 300→160; reg_lambda: 10.0→30.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.0742 (1.4618%) | 12.2122 (-0.0348%) | 0.097995 / -0.1418%, 0.1964% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0458/result.json) |
| n0459 / 완료 | b07→c000 / n0453 | bound: 0.3→0.5; half_life: 없음→365; learning_rate: 0.025→0.05; n_estimators: 160→80; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.9495 (8.3377%) | 12.1237 (-2.9747%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0459/result.json) |
| n0460 / 완료 | b07→c000 / n0454 | bound: 0.2→0.3; n_estimators: 80→160; reg_lambda: 2.0→30.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.8503 (5.4614%) | 12.4999 (-1.2794%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0460/result.json) |
| n0461 / 완료 | b07→c000 / n0455 | bound: 0.5→0.3; n_estimators: 80→300; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 13.4039 (0.9084%) | 12.3130 (0.0459%) | 0.050343 / -0.0403%, 0.0755% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0461/result.json) |
| n0462 / 완료 | b07→c000 / n0453 | bound: 0.3→0.1; mode: multiplicative→additive; n_estimators: 160→80; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.6231 (5.8028%) | 11.9114 (-4.6738%) | 0.014143 / -0.0043%, -0.0071% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0462/result.json) |
| n0463 / 완료 | b07→c000 / n0457 | bound: 0.15→0.5; half_life: 없음→365; learning_rate: 0.025→0.05; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.1513 (0.0782%) | 12.5883 (0.1628%) | 0.013778 / -0.0021%, 0.0194% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0463/result.json) |
| n0464 / 완료 | b07→c000 / n0458 | half_life: 없음→180; min_child_samples: 500→200; n_estimators: 160→80; num_leaves: 3→15; shrink: 0.75→0.25 (여러 설정 동시 변경) | 12.9940 (-0.6135%) | 12.6880 (3.8958%) | 0.013412 / -0.0015%, 0.0267% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0464/result.json) |
| n0465 / 완료 | b07→c000 / n0453 | half_life: 없음→180; n_estimators: 160→80; reg_lambda: 10.0→2.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.7471 (6.7661%) | 12.2956 (-1.5987%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0465/result.json) |
| n0466 / 완료 | b07→c000 / n0454 | bound: 0.2→0.3; half_life: 365→180; n_estimators: 80→300; shrink: 0.5→0.25 (여러 설정 동시 변경) | 13.1560 (0.1749%) | 12.7078 (0.3627%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0466/result.json) |
| n0467 / 완료 | b07→c000 / n0455 | bound: 0.5→0.15; learning_rate: 0.025→0.05; num_leaves: 15→7; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 13.2117 (-0.5387%) | 12.2862 (-0.1722%) | 0.056288 / -0.0523%, 0.0980% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0467/result.json) |
| n0468 / 완료 | b07→c000 / n0453 | bound: 0.3→0.1; half_life: 없음→365; mode: multiplicative→additive; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 12.9620 (0.6687%) | 12.5578 (0.4992%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0468/result.json) |
| n0469 / 완료 | b07→c000 / n0459 | features: season→age; half_life: 365→180; min_child_samples: 500→200; n_estimators: 80→300; shrink: 1.0→0.25 (여러 설정 동시 변경) | 13.1509 (-5.7249%) | 12.6411 (4.2678%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0469/result.json) |
| n0470 / 완료 | b07→c000 / n0461 | mode: multiplicative→additive; shrink: 0.75→0.25 (여러 설정 동시 변경) | 12.9010 (-3.7520%) | 12.5191 (1.6737%) | 0.021513 / -0.0029%, 0.0500% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0470/result.json) |
| n0471 / 완료 | b07→c000 / n0465 | half_life: 180→없음; learning_rate: 0.025→0.05; min_child_samples: 500→200; n_estimators: 80→300 (여러 설정 동시 변경) | 13.9853 (1.7329%) | 11.9310 (-2.9655%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0471/result.json) |
| n0472 / 완료 | b07→c000 / n0454 | n_estimators: 80→160; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 13.1948 (0.4703%) | 12.6012 (-0.4797%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0472/result.json) |
| n0473 / 완료 | b07→c000 / n0453 | features: season→core; half_life: 없음→365; num_leaves: 7→15; shrink: 0.25→0.5 (여러 설정 동시 변경) | 13.0651 (1.4694%) | 12.5216 (0.2094%) | 0.022462 / -0.0048%, 0.0364% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0473/result.json) |
| n0474 / 완료 | b07→c000 / n0456 | bound: 0.3→0.2; n_estimators: 300→80; reg_lambda: 10.0→30.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.8724 (-0.1041%) | 12.5751 (2.9358%) | 0.031924 / -0.0097%, 0.0829% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0474/result.json) |
| n0475 / 완료 | b07→c000 / n0463 | learning_rate: 0.05→0.025; min_child_samples: 500→1000; num_leaves: 3→7; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 13.1018 (-0.3763%) | 12.5753 (-0.1033%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0475/result.json) |
| n0476 / 완료 | b07→c000 / n0454 | features: age→core; learning_rate: 0.05→0.025; n_estimators: 80→300 (여러 설정 동시 변경) | 12.9178 (-1.6391%) | 12.4923 (-1.3394%) | 0.062853 / -0.0510%, 0.1367% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0476/result.json) |
| n0477 / 완료 | b07→c000 / n0455 | bound: 0.5→0.15; features: core→season; min_child_samples: 500→200; num_leaves: 15→3 (여러 설정 동시 변경) | 12.9553 (-2.4687%) | 12.2211 (-0.7016%) | 0.047202 / -0.0286%, 0.0887% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0477/result.json) |
| n0478 / 완료 | b07→c000 / n0456 | features: season→age; half_life: 없음→365; n_estimators: 300→80 (여러 설정 동시 변경) | 13.1204 (1.8209%) | 12.7240 (4.1549%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0478/result.json) |
| n0479 / 완료 | b07→c000 / n0471 | features: season→core; half_life: 없음→365; num_leaves: 7→3; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 13.8789 (-0.7612%) | 12.4163 (4.0675%) | 0.042608 / -0.0371%, 0.0271% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0479/result.json) |
| n0480 / 완료 | b07→c000 / n0462 | half_life: 없음→180; learning_rate: 0.025→0.05; min_child_samples: 500→200; reg_lambda: 10.0→2.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.4085 (-1.5751%) | 12.2840 (3.1283%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0480/result.json) |
| n0481 / 완료 | b07→c000 / n0469 | bound: 0.5→0.15; num_leaves: 7→3; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 13.1071 (-0.3328%) | 12.6960 (0.4342%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0481/result.json) |
| n0482 / 완료 | b07→c000 / n0464 | half_life: 180→365; min_child_samples: 200→500 (여러 설정 동시 변경) | 12.9744 (-0.1503%) | 12.6302 (-0.4550%) | 0.014380 / -0.0014%, 0.0304% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0482/result.json) |
| n0483 / 완료 | b07→c000 / n0475 | bound: 0.5→0.15; features: age→season; learning_rate: 0.025→0.05; num_leaves: 7→15 (여러 설정 동시 변경) | 13.6420 (4.1231%) | 12.1307 (-3.5353%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0483/result.json) |
| n0484 / 완료 | b07→c000 / n0454 | bound: 0.2→0.1; num_leaves: 3→7; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.5142 (2.9023%) | 12.3803 (-2.2238%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0484/result.json) |
| n0485 / 완료 | b07→c000 / n0458 | bound: 0.3→0.15; half_life: 없음→180; min_child_samples: 500→200; mode: additive→multiplicative (여러 설정 동시 변경) | 13.0817 (0.0573%) | 12.5238 (2.5515%) | 0.053451 / -0.0470%, 0.1260% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0485/result.json) |
| n0486 / 완료 | b07→c000 / n0462 | learning_rate: 0.025→0.05; num_leaves: 7→3; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.0302 (-4.3516%) | 12.0699 (1.3307%) | 0.058439 / -0.0463%, 0.0692% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0486/result.json) |
| n0487 / 완료 | b07→c000 / n0485 | features: core→age; num_leaves: 3→7 (여러 설정 동시 변경) | 13.2228 (1.0787%) | 12.6143 (0.7229%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0487/result.json) |
| n0488 / 완료 | b07→c000 / n0482 | n_estimators: 80→160 (단일 설정 차이) | 12.9793 (0.0374%) | 12.6041 (-0.2069%) | 0.008896 / -0.0004%, 0.0165% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0488/result.json) |
| n0489 / 완료 | b07→c000 / n0483 | half_life: 365→180; min_child_samples: 1000→200; shrink: 0.75→1.0 (여러 설정 동시 변경) | 14.4427 (5.8689%) | 12.2474 (0.9619%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0489/result.json) |
| n0490 / 완료 | b07→c000 / n0475 | bound: 0.5→0.3; min_child_samples: 1000→200; mode: multiplicative→additive; n_estimators: 160→300 (여러 설정 동시 변경) | 13.2974 (1.4925%) | 12.4016 (-1.3811%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0490/result.json) |
| n0491 / 완료 | b07→c000 / n0476 | bound: 0.2→0.5; min_child_samples: 1000→200; mode: additive→multiplicative; num_leaves: 3→7 (여러 설정 동시 변경) | 12.9927 (0.5801%) | 12.5088 (0.1324%) | 0.033078 / -0.0132%, 0.0619% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0491/result.json) |
| n0492 / 완료 | b07→c000 / n0452 | features: core→season; learning_rate: 0.05→0.025; reg_lambda: 10.0→2.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.5907 (5.0119%) | 12.2646 (-3.1197%) | 0.008217 / -0.0013%, 0.0030% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0492/result.json) |
| n0493 / 완료 | b07→c000 / n0469 | half_life: 180→365; reg_lambda: 10.0→2.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.8112 (5.0213%) | 12.5442 (-0.7668%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0493/result.json) |
| n0494 / 완료 | b07→c000 / n0464 | num_leaves: 15→7; reg_lambda: 30.0→2.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | 12.9321 (-0.4763%) | 12.6210 (-0.5276%) | 0.046658 / -0.0252%, 0.1027% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0494/result.json) |
| n0495 / 완료 | b07→c000 / n0453 | bound: 0.3→0.5; n_estimators: 160→300; num_leaves: 7→15 (여러 설정 동시 변경) | 12.9032 (0.2122%) | 12.4314 (-0.5124%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0495/result.json) |
| n0496 / 완료 | b07→c000 / n0480 | features: season→age; min_child_samples: 200→500; n_estimators: 80→160; shrink: 0.75→0.5 (여러 설정 동시 변경) | 13.1443 (-1.9705%) | 12.6063 (2.6241%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0496/result.json) |
| n0497 / 완료 | b07→c000 / n0467 | num_leaves: 7→3 (단일 설정 차이) | 13.0832 (-0.9726%) | 12.2551 (-0.2532%) | 0.074496 / -0.0901%, 0.1539% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0497/result.json) |
| n0498 / 완료 | b07→c000 / n0452 | features: core→season; num_leaves: 3→7; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.7449 (6.2037%) | 12.3033 (-2.8142%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0498/result.json) |
| n0499 / 완료 | b07→c000 / n0466 | half_life: 180→없음; min_child_samples: 1000→200; mode: additive→multiplicative; n_estimators: 300→160 (여러 설정 동시 변경) | 13.0285 (-0.9695%) | 12.6504 (-0.4521%) | 0.009360 / -0.0006%, 0.0229% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0499/result.json) |
| n0500 / 완료 | b07→c000 / n0458 | min_child_samples: 500→1000; n_estimators: 160→80; num_leaves: 3→7; shrink: 0.75→1.0 (여러 설정 동시 변경) | 13.8597 (6.0085%) | 12.1240 (-0.7225%) | 0.044574 / -0.0409%, 0.0175% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0500/result.json) |
| n0501 / 완료 | b07→c000 / n0453 | bound: 0.3→0.5; learning_rate: 0.025→0.05; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.2480 (2.8900%) | 12.0204 (-3.8016%) | 0.011415 / -0.0015%, 0.0033% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0501/result.json) |
| n0502 / 완료 | b07→c000 / n0462 | features: season→age; half_life: 없음→180; min_child_samples: 500→200; n_estimators: 80→300 (여러 설정 동시 변경) | 13.8013 (1.3082%) | 12.5704 (5.5330%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0502/result.json) |
| n0503 / 완료 | b07→c000 / n0459 | features: season→core; num_leaves: 7→3; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.8607 (-7.8051%) | 12.5273 (3.3289%) | 0.054934 / -0.0384%, 0.1451% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0503/result.json) |
| n0504 / 완료 | b07→c000 / n0464 | bound: 0.3→0.2; features: core→season; min_child_samples: 200→1000; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.5359 (4.1705%) | 12.3559 (-2.6170%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0504/result.json) |
| n0505 / 완료 | b07→c000 / n0457 | bound: 0.15→0.5; learning_rate: 0.025→0.05; min_child_samples: 500→1000; n_estimators: 160→300 (여러 설정 동시 변경) | 13.6431 (3.8203%) | 12.3810 (-1.4870%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0505/result.json) |
| n0506 / 완료 | b07→c000 / n0472 | features: age→core; learning_rate: 0.05→0.025; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.0631 (-0.9979%) | 12.3939 (-1.6448%) | 0.077102 / -0.0927%, 0.1641% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0506/result.json) |
| n0507 / 완료 | b07→c000 / n0461 | features: core→season; half_life: 없음→365; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | 13.6385 (1.7506%) | 12.1787 (-1.0910%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0507/result.json) |
| n0508 / 완료 | b07→c000 / n0484 | min_child_samples: 1000→500; reg_lambda: 2.0→10.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.0969 (-3.0880%) | 12.4430 (0.5060%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0508/result.json) |
| n0509 / 완료 | b07→c000 / n0467 | half_life: 없음→180; num_leaves: 7→15; reg_lambda: 10.0→30.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | 13.1149 (-0.7327%) | 12.6404 (2.8827%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0509/result.json) |
| n0510 / 완료 | b07→c000 / n0480 | min_child_samples: 200→500; shrink: 0.75→0.5 (여러 설정 동시 변경) | 13.0782 (-2.4633%) | 12.4279 (1.1710%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0510/result.json) |
| n0511 / 완료 | b07→c000 / n0475 | half_life: 365→180; n_estimators: 160→80; shrink: 0.75→0.25 (여러 설정 동시 변경) | 13.0890 (-0.0976%) | 12.7594 (1.4642%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0511/result.json) |
| n0512 / 완료 | b08→c186 / n0512 | 변경 없음(비교 기준 자체) (기준 자체) | 12.9173 (0.0000%) | 12.6877 (0.0000%) | 0.170596 / -0.3282%, 1.1548% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0512/result.json) |
| n0513 / 완료 | b08→c186 / n0512 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | 12.9140 (-0.0252%) | 12.6494 (-0.3023%) | 0.154265 / -0.3071%, 0.9920% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0513/result.json) |
| n0514 / 완료 | b08→c186 / n0512 | half_life: 없음→365 (단일 설정 차이) | 12.8888 (-0.2206%) | 12.7991 (0.8779%) | 0.171672 / -0.3206%, 1.2574% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0514/result.json) |
| n0515 / 완료 | b08→c186 / n0513 | half_life: 없음→365 (단일 설정 차이) | 12.8871 (-0.2085%) | 12.7502 (0.7971%) | 0.157917 / -0.3055%, 1.0936% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0515/result.json) |
| n0516 / 완료 | b08→c186 / n0514 | learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→500; n_estimators: 0→80; num_leaves: 0→15; reg_lambda: 0.0→10.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | 14.0156 (8.7422%) | 12.8538 (0.4276%) | 0.068782 / -0.1293%, 0.2950% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0516/result.json) |
| n0517 / 완료 | b08→c186 / n0513 | bound: 0.3→0.5; features: core→season; half_life: 없음→180; learning_rate: 0.0→0.05; method: median→tree; min_child_samples: 0→200; n_estimators: 0→300; num_leaves: 0→7; reg_lambda: 0.0→30.0 (여러 설정 동시 변경) | 13.0567 (1.1044%) | 12.7403 (0.7185%) | 0.033967 / -0.0139%, 0.1522% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0517/result.json) |
| n0518 / 완료 | b08→c186 / n0516 | features: core→age; learning_rate: 0.025→0.05; min_child_samples: 500→1000; num_leaves: 15→7; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 13.8389 (-1.2607%) | 13.0140 (1.2459%) | 0.015668 / -0.0062%, 0.0721% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0518/result.json) |
| n0519 / 완료 | b08→c186 / n0517 | bound: 0.5→0.15; features: season→core; half_life: 180→없음; min_child_samples: 200→1000; n_estimators: 300→160; reg_lambda: 30.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.6378 (-3.2080%) | 12.7563 (0.1262%) | 0.196582 / -0.3433%, 1.4573% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0519/result.json) |
| n0520 / 완료 | b08→c186 / n0516 | features: core→season; learning_rate: 0.025→0.05; min_child_samples: 500→200; n_estimators: 80→300; shrink: 1.0→0.5 (여러 설정 동시 변경) | 13.0102 (-7.1730%) | 12.5236 (-2.5689%) | 0.005359 / -0.0002%, 0.0212% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0520/result.json) |
| n0521 / 완료 | b08→c186 / n0519 | features: core→age; half_life: 없음→180; num_leaves: 7→3; reg_lambda: 2.0→10.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.1513 (4.0628%) | 13.0582 (2.3662%) | 0.060236 / -0.0644%, 0.3500% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0521/result.json) |
| n0522 / 완료 | b08→c186 / n0516 | half_life: 365→없음; n_estimators: 80→300; num_leaves: 15→3; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.8228 (-8.5106%) | 12.6693 (-1.4354%) | 0.178342 / -0.4076%, 1.1469% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0522/result.json) |
| n0523 / 완료 | b08→c186 / n0517 | learning_rate: 0.05→0.025; num_leaves: 7→15; reg_lambda: 30.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | 14.7344 (12.8496%) | 12.9397 (1.5653%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0523/result.json) |
| n0524 / 완료 | b08→c186 / n0520 | bound: 0.2→0.1; features: season→age; num_leaves: 15→3; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 13.0500 (0.3055%) | 12.8978 (2.9878%) | 0.064810 / -0.0608%, 0.3728% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0524/result.json) |
| n0525 / 완료 | b08→c186 / n0523 | features: season→core; half_life: 180→없음; n_estimators: 300→160; num_leaves: 15→3 (여러 설정 동시 변경) | 13.7384 (-6.7599%) | 12.9019 (-0.2921%) | 0.124848 / -0.3424%, 0.7707% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0525/result.json) |
| n0526 / 완료 | b08→c186 / n0518 | bound: 0.2→0.1; features: age→season; half_life: 365→180; num_leaves: 7→3; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 13.5720 (-1.9282%) | 12.7578 (-1.9682%) | 0.072301 / -0.1180%, 0.3920% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0526/result.json) |
| n0527 / 완료 | b08→c186 / n0521 | min_child_samples: 1000→500; reg_lambda: 10.0→2.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | 13.4555 (2.3130%) | 13.2322 (1.3327%) | 0.040410 / -0.0317%, 0.2243% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0527/result.json) |
| n0528 / 완료 | b08→c186 / n0519 | bound: 0.15→0.2; half_life: 없음→180; min_child_samples: 1000→500; mode: multiplicative→additive; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.5803 (7.4575%) | 12.9155 (1.2475%) | 0.069169 / -0.0967%, 0.3134% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0528/result.json) |
| n0529 / 완료 | b08→c186 / n0517 | bound: 0.5→0.3; learning_rate: 0.05→0.025; num_leaves: 7→3; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | 12.8557 (-1.5390%) | 12.8085 (0.5357%) | 0.119318 / -0.1755%, 0.7526% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0529/result.json) |
| n0530 / 완료 | b08→c186 / n0522 | bound: 0.2→0.3; features: core→age; min_child_samples: 500→1000; reg_lambda: 10.0→30.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.7767 (-0.3595%) | 12.8223 (1.2073%) | 0.130536 / -0.1989%, 0.8869% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0530/result.json) |
| n0531 / 완료 | b08→c186 / n0529 | features: season→core; half_life: 180→365; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.2139 (2.7863%) | 12.9002 (0.7159%) | 0.124408 / -0.2638%, 0.7971% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0531/result.json) |
| n0532 / 완료 | b08→c186 / n0520 | bound: 0.2→0.3; n_estimators: 300→160; num_leaves: 15→3; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | 12.8687 (-1.0882%) | 12.6973 (1.3864%) | 0.118136 / -0.1869%, 0.7036% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0532/result.json) |
| n0533 / 완료 | b08→c186 / n0517 | features: season→age; half_life: 180→365; learning_rate: 0.05→0.025; min_child_samples: 200→500; n_estimators: 300→160 (여러 설정 동시 변경) | 12.8430 (-1.6362%) | 12.8869 (1.1512%) | 0.119435 / -0.1554%, 0.7706% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0533/result.json) |
| n0534 / 완료 | b08→c186 / n0525 | bound: 0.5→0.1; min_child_samples: 200→1000; mode: multiplicative→additive; shrink: 1.0→0.75 (여러 설정 동시 변경) | 12.9691 (-5.5992%) | 12.6674 (-1.8174%) | 0.179897 / -0.5222%, 1.1550% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0534/result.json) |
| n0535 / 완료 | b08→c186 / n0525 | features: core→season; n_estimators: 160→80; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.6646 (-7.8161%) | 12.7290 (-1.3399%) | 0.178733 / -0.2963%, 1.2825% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0535/result.json) |
| n0536 / 완료 | b08→c186 / n0524 | half_life: 365→없음; min_child_samples: 200→500; n_estimators: 300→160; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.7893 (-1.9974%) | 12.8255 (-0.5610%) | 0.129287 / -0.1912%, 0.8766% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0536/result.json) |
| n0537 / 완료 | b08→c186 / n0519 | min_child_samples: 1000→200; n_estimators: 160→300; shrink: 0.25→0.5 (여러 설정 동시 변경) | 12.7014 (0.5032%) | 12.7352 (-0.1658%) | 0.178961 / -0.3567%, 1.2142% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0537/result.json) |
| n0538 / 완료 | b08→c186 / n0526 | num_leaves: 3→7; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.9543 (-4.5516%) | 12.7650 (0.0561%) | 0.081608 / -0.0896%, 0.4547% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0538/result.json) |
| n0539 / 완료 | b08→c186 / n0517 | bound: 0.5→0.3; features: season→age; learning_rate: 0.05→0.025; min_child_samples: 200→1000 (여러 설정 동시 변경) | 12.9719 (-0.6492%) | 12.9226 (1.4314%) | 0.081644 / -0.0856%, 0.4604% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0539/result.json) |
| n0540 / 완료 | b08→c186 / n0534 | bound: 0.1→0.2; num_leaves: 3→15; shrink: 0.75→0.5 (여러 설정 동시 변경) | 12.8863 (-0.6387%) | 12.6198 (-0.3755%) | 0.153510 / -0.2543%, 0.8671% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0540/result.json) |
| n0541 / 완료 | b08→c186 / n0517 | min_child_samples: 200→500; n_estimators: 300→80; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.7624 (-2.2539%) | 12.8064 (0.5192%) | 0.124409 / -0.1686%, 0.8118% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0541/result.json) |
| n0542 / 완료 | b08→c186 / n0530 | learning_rate: 0.025→0.05; min_child_samples: 1000→200; n_estimators: 300→80; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 12.7684 (-0.0646%) | 12.8288 (0.0511%) | 0.134841 / -0.2050%, 0.9436% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0542/result.json) |
| n0543 / 완료 | b08→c186 / n0525 | bound: 0.5→0.15; half_life: 없음→365; num_leaves: 3→15; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.7984 (-6.8417%) | 12.8210 (-0.6266%) | 0.155699 / -0.2423%, 1.0074% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0543/result.json) |
| n0544 / 완료 | b08→c186 / n0538 | half_life: 180→없음; min_child_samples: 1000→500; num_leaves: 7→15 (여러 설정 동시 변경) | 12.7830 (-1.3220%) | 12.5540 (-1.6527%) | 0.108024 / -0.1246%, 0.5667% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0544/result.json) |
| n0545 / 완료 | b08→c186 / n0539 | half_life: 180→365; min_child_samples: 1000→200; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.8552 (-0.8999%) | 12.7975 (-0.9683%) | 0.123936 / -0.1734%, 0.7732% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0545/result.json) |
| n0546 / 완료 | b08→c186 / n0516 | half_life: 365→없음; min_child_samples: 500→200; reg_lambda: 10.0→30.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.3821 (-4.5196%) | 12.6740 (-1.3988%) | 0.107369 / -0.1843%, 0.5143% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0546/result.json) |
| n0547 / 완료 | b08→c186 / n0535 | half_life: 없음→365; num_leaves: 3→7; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.2791 (4.8526%) | 12.8411 (0.8804%) | 0.062732 / -0.0765%, 0.3595% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0547/result.json) |
| n0548 / 완료 | b08→c186 / n0536 | n_estimators: 160→300; reg_lambda: 30.0→10.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.3324 (4.2460%) | 12.8752 (0.3874%) | 0.041563 / -0.0294%, 0.2125% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0548/result.json) |
| n0549 / 완료 | b08→c186 / n0519 | half_life: 없음→180; learning_rate: 0.05→0.025; min_child_samples: 1000→200 (여러 설정 동시 변경) | 12.7026 (0.5128%) | 12.8416 (0.6686%) | 0.169936 / -0.2717%, 1.2457% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0549/result.json) |
| n0550 / 완료 | b08→c186 / n0529 | min_child_samples: 200→500; mode: multiplicative→additive; n_estimators: 300→80 (여러 설정 동시 변경) | 12.7541 (-0.7909%) | 12.8010 (-0.0584%) | 0.139490 / -0.2207%, 0.9562% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0550/result.json) |
| n0551 / 완료 | b08→c186 / n0521 | min_child_samples: 1000→200; num_leaves: 3→7 (여러 설정 동시 변경) | 13.3431 (1.4587%) | 12.7559 (-2.3152%) | 0.021064 / -0.0078%, 0.0549% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0551/result.json) |
| n0552 / 완료 | b08→c186 / n0516 | min_child_samples: 500→1000; n_estimators: 80→160; num_leaves: 15→7; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.7110 (-9.3080%) | 12.7774 (-0.5949%) | 0.173516 / -0.2836%, 1.2150% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0552/result.json) |
| n0553 / 완료 | b08→c186 / n0541 | bound: 0.5→0.3; n_estimators: 80→160; num_leaves: 7→15; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | 12.8319 (0.5445%) | 12.7421 (-0.5019%) | 0.075648 / -0.0722%, 0.4150% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0553/result.json) |
| n0554 / 완료 | b08→c186 / n0518 | half_life: 365→180; reg_lambda: 30.0→2.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.9045 (-6.7522%) | 12.8389 (-1.3456%) | 0.105834 / -0.1372%, 0.6693% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0554/result.json) |
| n0555 / 완료 | b08→c186 / n0539 | features: age→core; learning_rate: 0.025→0.05; n_estimators: 300→80 (여러 설정 동시 변경) | 12.8429 (-0.9948%) | 12.9295 (0.0532%) | 0.136467 / -0.2222%, 0.9324% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0555/result.json) |
| n0556 / 완료 | b08→c186 / n0520 | half_life: 365→180; learning_rate: 0.05→0.025; n_estimators: 300→160; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.7660 (5.8090%) | 12.7412 (1.7373%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0556/result.json) |
| n0557 / 완료 | b08→c186 / n0518 | bound: 0.2→0.15; mode: additive→multiplicative; n_estimators: 80→300; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | 13.8582 (0.1398%) | 13.0152 (0.0095%) | 0.000366 / -0.0000%, 0.0011% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0557/result.json) |
| n0558 / 완료 | b08→c186 / n0540 | learning_rate: 0.025→0.05; n_estimators: 160→80; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.5486 (5.1397%) | 12.6723 (0.4156%) | 0.097209 / -0.1722%, 0.4358% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0558/result.json) |
| n0559 / 완료 | b08→c186 / n0558 | bound: 0.2→0.5; features: core→season; mode: additive→multiplicative; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 13.4445 (-0.7684%) | 12.6970 (0.1954%) | 0.037550 / -0.0192%, 0.1684% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0559/result.json) |
| n0560 / 완료 | b08→c186 / n0531 | features: core→age; mode: multiplicative→additive; n_estimators: 300→160 (여러 설정 동시 변경) | 13.0977 (-0.8792%) | 12.9384 (0.2964%) | 0.064917 / -0.0639%, 0.4014% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0560/result.json) |
| n0561 / 완료 | b08→c186 / n0541 | features: season→core; n_estimators: 80→160; num_leaves: 7→15 (여러 설정 동시 변경) | 12.7637 (0.0101%) | 12.8162 (0.0766%) | 0.132650 / -0.1936%, 0.8358% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0561/result.json) |
| n0562 / 완료 | b08→c186 / n0536 | features: age→season; num_leaves: 3→7; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 12.7398 (-0.3869%) | 12.6352 (-1.4832%) | 0.135126 / -0.1962%, 0.8262% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0562/result.json) |
| n0563 / 완료 | b08→c186 / n0527 | bound: 0.15→0.3; min_child_samples: 500→200; num_leaves: 3→7 (여러 설정 동시 변경) | 13.6738 (1.6226%) | 12.7911 (-3.3340%) | 0.010953 / -0.0044%, 0.0180% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0563/result.json) |
| n0564 / 완료 | b08→c186 / n0520 | features: season→core; half_life: 365→없음; min_child_samples: 200→1000 (여러 설정 동시 변경) | 12.8850 (-0.9625%) | 12.4337 (-0.7186%) | 0.124594 / -0.1719%, 0.5777% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0564/result.json) |
| n0565 / 완료 | b08→c186 / n0562 | bound: 0.1→0.3; mode: additive→multiplicative; shrink: 0.25→1.0 (여러 설정 동시 변경) | 14.1436 (11.0189%) | 12.8746 (1.8941%) | 0.039825 / -0.0381%, 0.1760% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0565/result.json) |
| n0566 / 완료 | b08→c186 / n0526 | features: season→age; min_child_samples: 1000→200; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 13.5242 (-0.3526%) | 12.9614 (1.5954%) | 0.027081 / -0.0192%, 0.1405% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0566/result.json) |
| n0567 / 완료 | b08→c186 / n0550 | bound: 0.3→0.15; features: season→core; mode: additive→multiplicative (여러 설정 동시 변경) | 12.7117 (-0.3324%) | 12.8556 (0.4260%) | 0.184798 / -0.3235%, 1.4473% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0567/result.json) |
| n0568 / 완료 | b08→c186 / n0526 | bound: 0.1→0.2; half_life: 180→없음; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 13.8663 (2.1678%) | 12.6872 (-0.5536%) | 0.083295 / -0.1729%, 0.4350% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0568/result.json) |
| n0569 / 완료 | b08→c186 / n0551 | min_child_samples: 200→500; n_estimators: 160→80 (여러 설정 동시 변경) | 13.0571 (-2.1434%) | 12.7632 (0.0575%) | 0.062061 / -0.0597%, 0.2439% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0569/result.json) |
| n0570 / 완료 | b08→c186 / n0522 | bound: 0.2→0.1; num_leaves: 3→7; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.6823 (-1.0954%) | 12.6991 (0.2352%) | 0.190579 / -0.3264%, 1.3216% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0570/result.json) |
| n0571 / 완료 | b08→c186 / n0541 | learning_rate: 0.05→0.025; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | 12.7513 (-0.0865%) | 12.8297 (0.1816%) | 0.129097 / -0.1868%, 0.8778% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0571/result.json) |
| n0572 / 완료 | b08→c186 / n0550 | features: season→age; learning_rate: 0.025→0.05; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 12.9582 (1.6010%) | 12.9048 (0.8107%) | 0.083935 / -0.0951%, 0.5293% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0572/result.json) |
| n0573 / 완료 | b08→c186 / n0543 | bound: 0.15→0.3; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 12.8683 (0.5460%) | 12.8155 (-0.0432%) | 0.134330 / -0.2165%, 0.8198% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0573/result.json) |
| n0574 / 완료 | b08→c186 / n0538 | learning_rate: 0.05→0.025; min_child_samples: 1000→200; num_leaves: 7→15 (여러 설정 동시 변경) | 12.9552 (0.0071%) | 12.7676 (0.0206%) | 0.061960 / -0.0499%, 0.3314% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0574/result.json) |
| n0575 / 완료 | b08→c186 / n0517 | features: season→age; reg_lambda: 30.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.9197 (-1.0488%) | 12.7217 (-0.1460%) | 0.096259 / -0.1217%, 0.4927% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0575/result.json) |
| n0576 / 완료 | b09→c030 / n0576 | 변경 없음(비교 기준 자체) (기준 자체) | 12.8997 (0.0000%) | 12.4822 (0.0000%) | 0.105922 / -0.1487%, 0.3707% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0576/result.json) |
| n0577 / 완료 | b09→c030 / n0576 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | 12.8363 (-0.4919%) | 12.4798 (-0.0195%) | 0.103043 / -0.1346%, 0.3731% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0577/result.json) |
| n0578 / 완료 | b09→c030 / n0576 | half_life: 없음→365 (단일 설정 차이) | 12.9066 (0.0535%) | 12.5658 (0.6696%) | 0.106212 / -0.1411%, 0.4154% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0578/result.json) |
| n0579 / 완료 | b09→c030 / n0577 | half_life: 없음→365 (단일 설정 차이) | 12.8496 (0.1039%) | 12.5642 (0.6763%) | 0.105053 / -0.1295%, 0.4203% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0579/result.json) |
| n0580 / 완료 | b09→c030 / n0576 | bound: 0.2→0.3; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→1000; n_estimators: 0→80; num_leaves: 0→15; reg_lambda: 0.0→10.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.6804 (6.0517%) | 12.2360 (-1.9725%) | 0.049780 / -0.0493%, 0.0189% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0580/result.json) |
| n0581 / 완료 | b09→c030 / n0580 | bound: 0.3→0.5; features: core→season; learning_rate: 0.025→0.05; mode: additive→multiplicative; n_estimators: 80→160; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | 13.9769 (2.1675%) | 12.0361 (-1.6336%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0581/result.json) |
| n0582 / 실패 | b09→c030 / n0580 | features: core→age; learning_rate: 0.025→0.05; min_child_samples: 1000→500; n_estimators: 80→160; num_leaves: 15→7; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / -0.0121%, -0.0071% | 5/5 / 5 | NumPy bool 결과 저장 오류; 학습 영수증 보존, 최종 결과 미기록; 독립 감사에서 탐색 조건 통과 확인, 최종 선택·추가 시드·제출 검증은 미완료 [기록](../../analysis_outputs/research_22h_20261107/hourly_checks/20261107T100255Z_failed_candidates_science.json) |
| n0583 / 완료 | b09→c030 / n0581 | features: season→core; n_estimators: 160→80; num_leaves: 15→7; reg_lambda: 2.0→30.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | 12.9425 (-7.4010%) | 12.3267 (2.4138%) | 0.095076 / -0.1206%, 0.2008% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0583/result.json) |
| n0584 / 완료 | b09→c030 / n0580 | bound: 0.3→0.1; features: core→season; half_life: 없음→180; min_child_samples: 1000→500; reg_lambda: 10.0→2.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.1424 (-3.9324%) | 12.2843 (0.3945%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0584/result.json) |
| n0585 / 완료 | b09→c030 / n0582 | half_life: 없음→365; min_child_samples: 500→200; mode: additive→multiplicative; n_estimators: 160→300; num_leaves: 7→3; shrink: 0.75→0.25 (여러 설정 동시 변경) | 12.9282 | 12.6052 | 0.074987 / -0.0684%, 0.2373% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0585/result.json) |
| n0586 / 완료 | b09→c030 / n0585 | bound: 0.3→0.2; features: age→core; learning_rate: 0.05→0.025; mode: multiplicative→additive; n_estimators: 300→160; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 12.7789 (-1.1549%) | 12.6063 (0.0094%) | 0.119798 / -0.1562%, 0.5263% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0586/result.json) |
| n0587 / 완료 | b09→c030 / n0581 | bound: 0.5→0.15; learning_rate: 0.05→0.025; n_estimators: 160→80; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.6933 (-9.1837%) | 12.2883 (2.0953%) | 0.069224 / -0.0476%, 0.1526% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0587/result.json) |
| n0588 / 완료 | b09→c030 / n0582 | num_leaves: 7→3; shrink: 0.75→0.25 (여러 설정 동시 변경) | 12.9503 | 12.5732 | 0.075874 / -0.0725%, 0.2757% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0588/result.json) |
| n0589 / 완료 | b09→c030 / n0585 | features: age→core; half_life: 365→180; learning_rate: 0.05→0.025; min_child_samples: 200→1000; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 12.8022 (-0.9748%) | 12.6453 (0.3188%) | 0.104803 / -0.1166%, 0.4206% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0589/result.json) |
| n0590 / 완료 | b09→c030 / n0584 | bound: 0.1→0.2; learning_rate: 0.025→0.05; num_leaves: 15→3; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 12.7561 (-2.9396%) | 12.2709 (-0.1088%) | 0.092034 / -0.1122%, 0.1999% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0590/result.json) |
| n0591 / 완료 | b09→c030 / n0588 | bound: 0.3→0.15; half_life: 없음→180; mode: additive→multiplicative; shrink: 0.25→0.5 (여러 설정 동시 변경) | 12.9114 (-0.3007%) | 12.6038 (0.2432%) | 0.069795 / -0.0598%, 0.1873% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0591/result.json) |
| n0592 / 완료 | b09→c030 / n0580 | bound: 0.3→0.2; num_leaves: 15→7; reg_lambda: 10.0→30.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.6854 (-7.2733%) | 12.3690 (1.0868%) | 0.117391 / -0.1398%, 0.3665% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0592/result.json) |
| n0593 / 완료 | b09→c030 / n0581 | min_child_samples: 1000→200; n_estimators: 160→300; num_leaves: 15→7; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 13.6129 (-2.6041%) | 11.9887 (-0.3940%) | 0.007152 / -0.0010%, -0.0051% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0593/result.json) |
| n0594 / 완료 | b09→c030 / n0582 | bound: 0.3→0.2; half_life: 없음→180; min_child_samples: 500→200; n_estimators: 160→300; shrink: 0.75→1.0 (여러 설정 동시 변경) | 13.7857 | 12.4921 | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0594/result.json) |
| n0595 / 완료 | b09→c030 / n0581 | features: season→core; half_life: 없음→180; learning_rate: 0.05→0.025; min_child_samples: 1000→500; num_leaves: 15→7 (여러 설정 동시 변경) | 13.3754 (-4.3036%) | 12.4836 (3.7180%) | 0.066385 / -0.0775%, 0.0880% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0595/result.json) |
| n0596 / 완료 | b09→c030 / n0580 | features: core→season; learning_rate: 0.025→0.05; min_child_samples: 1000→200; reg_lambda: 10.0→30.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.7678 (-6.6710%) | 12.4500 (1.7487%) | 0.072135 / -0.0535%, 0.2142% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0596/result.json) |
| n0597 / 완료 | b09→c030 / n0591 | num_leaves: 3→7; reg_lambda: 10.0→30.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.2588 (2.6912%) | 12.3940 (-1.6644%) | 0.014665 / -0.0040%, -0.0596% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0597/result.json) |
| n0598 / 완료 | b09→c030 / n0584 | bound: 0.1→0.2; features: season→core; num_leaves: 15→3; shrink: 0.75→0.25 (여러 설정 동시 변경) | 12.8442 (-2.2688%) | 12.6528 (3.0002%) | 0.108224 / -0.1394%, 0.4755% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0598/result.json) |
| n0599 / 완료 | b09→c030 / n0581 | half_life: 없음→180; min_child_samples: 1000→200; n_estimators: 160→80; shrink: 1.0→0.5 (여러 설정 동시 변경) | 12.8959 (-7.7340%) | 12.3617 (2.7048%) | 0.012165 / -0.0007%, 0.0114% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0599/result.json) |
| n0600 / 완료 | b09→c030 / n0582 | bound: 0.3→0.1; min_child_samples: 500→200; n_estimators: 160→80; num_leaves: 7→3; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | 12.7624 | 12.3018 | 0.089808 / -0.0920%, 0.2473% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0600/result.json) |
| n0601 / 완료 | b09→c030 / n0580 | bound: 0.3→0.15; half_life: 없음→365; min_child_samples: 1000→200; mode: additive→multiplicative; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.8333 (-6.1920%) | 12.6269 (3.1944%) | 0.091511 / -0.0905%, 0.3457% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0601/result.json) |
| n0602 / 완료 | b09→c030 / n0580 | features: core→season; half_life: 없음→365; min_child_samples: 1000→500; n_estimators: 80→300 (여러 설정 동시 변경) | 14.1506 (3.4371%) | 12.0976 (-1.1312%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0602/result.json) |
| n0603 / 완료 | b09→c030 / n0597 | reg_lambda: 30.0→30.5 (단일 설정 차이) | 13.2588 (0.0000%) | 12.4365 (0.3428%) | 0.014665 / -0.0040%, -0.0650% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0603/result.json) |
| n0604 / 완료 | b09→c030 / n0586 | half_life: 365→180; learning_rate: 0.025→0.05; min_child_samples: 200→1000 (여러 설정 동시 변경) | 12.8114 (0.2540%) | 12.6410 (0.2746%) | 0.113236 / -0.1299%, 0.4715% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0604/result.json) |
| n0605 / 완료 | b09→c030 / n0593 | bound: 0.5→0.3; n_estimators: 300→160 (여러 설정 동시 변경) | 13.4915 (-0.8919%) | 12.0079 (0.1604%) | 0.029921 / -0.0137%, -0.0082% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0605/result.json) |
| n0606 / 완료 | b09→c030 / n0588 | bound: 0.3→0.2; min_child_samples: 500→200; shrink: 0.25→0.5 (여러 설정 동시 변경) | 12.8421 (-0.8355%) | 12.3980 (-1.3930%) | 0.074234 / -0.0654%, 0.2231% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0606/result.json) |
| n0607 / 완료 | b09→c030 / n0586 | bound: 0.2→0.15; mode: additive→multiplicative; n_estimators: 160→300 (여러 설정 동시 변경) | 12.7743 (-0.0358%) | 12.6153 (0.0712%) | 0.109274 / -0.1295%, 0.4473% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0607/result.json) |
| n0608 / 완료 | b09→c030 / n0596 | bound: 0.3→0.1; min_child_samples: 200→1000; n_estimators: 80→300; num_leaves: 15→3 (여러 설정 동시 변경) | 12.7808 (0.1018%) | 12.4757 (0.2066%) | 0.096307 / -0.1090%, 0.3440% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0608/result.json) |
| n0609 / 완료 | b09→c030 / n0583 | features: core→age; half_life: 없음→180; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | 12.8149 (-0.9861%) | 12.3546 (0.2267%) | 0.065015 / -0.0496%, 0.0225% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0609/result.json) |
| n0610 / 완료 | b09→c030 / n0586 | bound: 0.2→0.1; reg_lambda: 30.0→2.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 12.9052 (0.9885%) | 12.2171 (-3.0879%) | 0.165304 / -0.3563%, 0.4888% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0610/result.json) |
| n0611 / 완료 | b09→c030 / n0593 | min_child_samples: 200→500; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.7002 (-6.7050%) | 12.4370 (3.7390%) | 0.090976 / -0.0832%, 0.2931% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0611/result.json) |
| n0612 / 완료 | b09→c030 / n0600 | bound: 0.1→0.2; half_life: 없음→365; min_child_samples: 200→1000; n_estimators: 80→160 (여러 설정 동시 변경) | 13.0265 (2.0690%) | 12.4422 (1.1419%) | 0.048732 / -0.0310%, 0.1018% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0612/result.json) |
| n0613 / 완료 | b09→c030 / n0602 | features: season→core; mode: additive→multiplicative; num_leaves: 15→7 (여러 설정 동시 변경) | 13.4933 (-4.6446%) | 12.3776 (2.3143%) | 0.059618 / -0.0607%, 0.0232% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0613/result.json) |
| n0614 / 완료 | b09→c030 / n0590 | min_child_samples: 500→200; num_leaves: 3→7; shrink: 0.75→0.25 (여러 설정 동시 변경) | 12.8520 (0.7516%) | 12.5783 (2.5049%) | 0.070085 / -0.0533%, 0.2204% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0614/result.json) |
| n0615 / 완료 | b09→c030 / n0589 | features: core→age; min_child_samples: 1000→200; n_estimators: 300→160; shrink: 0.25→0.75 (여러 설정 동시 변경) | 12.8734 (0.5564%) | 12.5815 (-0.5052%) | 0.070569 / -0.0623%, 0.2016% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0615/result.json) |
| n0616 / 완료 | b09→c030 / n0590 | features: season→core; half_life: 180→365; min_child_samples: 500→1000 (여러 설정 동시 변경) | 12.6707 (-0.6692%) | 12.2974 (0.2155%) | 0.174410 / -0.3203%, 0.6137% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0616/result.json) |
| n0617 / 완료 | b09→c030 / n0585 | features: age→season; n_estimators: 300→160; reg_lambda: 10.0→2.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | 12.6590 (-2.0824%) | 12.3810 (-1.7786%) | 0.094943 / -0.1018%, 0.2733% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0617/result.json) |
| n0618 / 완료 | b09→c030 / n0600 | half_life: 없음→365; n_estimators: 80→160; shrink: 0.75→0.5 (여러 설정 동시 변경) | 12.9482 (1.4558%) | 12.5387 (1.9255%) | 0.060544 / -0.0447%, 0.1753% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0618/result.json) |
| n0619 / 완료 | b09→c030 / n0581 | features: season→core; min_child_samples: 1000→200; n_estimators: 160→300; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.1715 (-5.7627%) | 12.3199 (2.3575%) | 0.068662 / -0.0497%, 0.0938% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0619/result.json) |
| n0620 / 완료 | b09→c030 / n0584 | num_leaves: 15→3; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 12.6584 (-3.6831%) | 12.3820 (0.7952%) | 0.118891 / -0.1452%, 0.4099% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0620/result.json) |
| n0621 / 완료 | b09→c030 / n0581 | bound: 0.5→0.3; features: season→age; num_leaves: 15→3 (여러 설정 동시 변경) | 12.9499 (-7.3480%) | 12.2887 (2.0986%) | 0.066460 / -0.0578%, 0.1151% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0621/result.json) |
| n0622 / 완료 | b09→c030 / n0598 | half_life: 180→365; n_estimators: 80→300; num_leaves: 3→7; shrink: 0.25→0.75 (여러 설정 동시 변경) | 13.0787 (1.8256%) | 12.4176 (-1.8593%) | 0.089831 / -0.1099%, 0.1450% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0622/result.json) |
| n0623 / 완료 | b09→c030 / n0599 | min_child_samples: 200→500; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.9031 (0.0557%) | 12.5719 (1.7003%) | 0.045402 / -0.0225%, 0.1219% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0623/result.json) |
| n0624 / 완료 | b09→c030 / n0600 | half_life: 없음→180; min_child_samples: 200→500; n_estimators: 80→300 (여러 설정 동시 변경) | 13.2473 (3.7988%) | 12.5884 (2.3301%) | 0.014848 / -0.0043%, 0.0127% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0624/result.json) |
| n0625 / 완료 | b09→c030 / n0583 | learning_rate: 0.05→0.025; n_estimators: 80→300; reg_lambda: 30.0→10.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | 12.6573 (-2.2033%) | 12.4270 (0.8138%) | 0.131766 / -0.1528%, 0.4638% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0625/result.json) |
| n0626 / 완료 | b09→c030 / n0621 | features: age→season; mode: multiplicative→additive (여러 설정 동시 변경) | 13.3457 (3.0565%) | 11.9805 (-2.5084%) | 0.079700 / -0.1200%, 0.0669% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0626/result.json) |
| n0627 / 완료 | b09→c030 / n0595 | features: core→age; half_life: 180→없음; min_child_samples: 500→200; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.9249 (-3.3678%) | 12.6034 (0.9593%) | 0.077385 / -0.0733%, 0.2722% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0627/result.json) |
| n0628 / 완료 | b09→c030 / n0589 | bound: 0.3→0.1; mode: multiplicative→additive; n_estimators: 300→80 (여러 설정 동시 변경) | 12.8448 (0.3325%) | 12.6538 (0.0672%) | 0.108655 / -0.1387%, 0.4777% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0628/result.json) |
| n0629 / 완료 | b09→c030 / n0623 | learning_rate: 0.05→0.025; num_leaves: 15→7; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 12.8587 (-0.3445%) | 12.6274 (0.4414%) | 0.069976 / -0.0618%, 0.2473% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0629/result.json) |
| n0630 / 완료 | b09→c030 / n0600 | n_estimators: 80→160; reg_lambda: 2.0→30.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | 12.9929 (1.8055%) | 12.2204 (-0.6617%) | 0.060740 / -0.0467%, 0.1186% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0630/result.json) |
| n0631 / 완료 | b09→c030 / n0619 | half_life: 없음→365; n_estimators: 300→160; num_leaves: 15→7 (여러 설정 동시 변경) | 12.9628 (-1.5840%) | 12.4391 (0.9678%) | 0.087651 / -0.1055%, 0.1680% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0631/result.json) |
| n0632 / 완료 | b09→c030 / n0602 | min_child_samples: 500→200; num_leaves: 15→7; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 13.7231 (-3.0208%) | 12.0635 (-0.2817%) | 0.011074 / -0.0024%, -0.0118% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0632/result.json) |
| n0633 / 완료 | b09→c030 / n0596 | features: season→age; mode: additive→multiplicative; num_leaves: 15→7 (여러 설정 동시 변경) | 12.8999 (1.0351%) | 12.6242 (1.3991%) | 0.077235 / -0.0773%, 0.2751% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0633/result.json) |
| n0634 / 완료 | b09→c030 / n0580 | bound: 0.3→0.1; half_life: 없음→365; n_estimators: 80→160 (여러 설정 동시 변경) | 13.6572 (-0.1694%) | 12.3695 (1.0911%) | 0.029704 / -0.0119%, -0.0233% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0634/result.json) |
| n0635 / 완료 | b09→c030 / n0587 | bound: 0.15→0.5; half_life: 없음→365; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 12.7897 (0.7593%) | 12.3799 (0.7451%) | 0.047547 / -0.0179%, 0.0938% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0635/result.json) |
| n0636 / 완료 | b09→c030 / n0630 | learning_rate: 0.05→0.025; n_estimators: 160→80 (여러 설정 동시 변경) | 12.6892 (-2.3372%) | 12.2137 (-0.0544%) | 0.120550 / -0.1361%, 0.3450% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0636/result.json) |
| n0637 / 완료 | b09→c030 / n0591 | bound: 0.15→0.5; features: age→core; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | 12.6906 (-1.7097%) | 12.5219 (-0.6495%) | 0.119628 / -0.1490%, 0.3910% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0637/result.json) |
| n0638 / 완료 | b09→c030 / n0590 | min_child_samples: 500→200; n_estimators: 80→300; shrink: 0.75→1.0 (여러 설정 동시 변경) | 13.5460 (6.1929%) | 12.2527 (-0.1481%) | 0.021435 / -0.0092%, -0.0082% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0638/result.json) |
| n0639 / 완료 | b09→c030 / n0613 | features: core→age; n_estimators: 300→80; reg_lambda: 10.0→2.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.9757 (-3.8361%) | 12.6202 (1.9605%) | 0.073233 / -0.0699%, 0.2413% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0639/result.json) |
| n0640 / 완료 | b10→c142 / n0640 | 변경 없음(비교 기준 자체) (기준 자체) | 12.7582 (0.0000%) | 11.8366 (0.0000%) | 0.058875 / -0.0272%, 0.1908% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0640/result.json) |
| n0641 / 완료 | b10→c142 / n0640 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | 12.7063 (-0.4068%) | 11.8365 (-0.0002%) | 0.056156 / -0.0210%, 0.1864% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0641/result.json) |
| n0642 / 완료 | b10→c142 / n0640 | half_life: 없음→365 (단일 설정 차이) | 12.7235 (-0.2719%) | 11.8713 (0.2936%) | 0.056767 / -0.0250%, 0.2010% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0642/result.json) |
| n0643 / 완료 | b10→c142 / n0641 | half_life: 없음→365 (단일 설정 차이) | 12.6900 (-0.1276%) | 11.8624 (0.2183%) | 0.055872 / -0.0206%, 0.1980% | 5/5 / 0 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0643/result.json) |
| n0644 / 완료 | b10→c142 / n0642 | bound: 0.2→0.1; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→1000; n_estimators: 0→300; num_leaves: 0→7; reg_lambda: 0.0→30.0 (여러 설정 동시 변경) | 12.9819 (2.0315%) | 11.7941 (-0.6507%) | 0.018397 / -0.0035%, 0.0278% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0644/result.json) |
| n0645 / 완료 | b10→c142 / n0641 | bound: 0.3→0.15; features: core→season; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→500; n_estimators: 0→80; num_leaves: 0→15; reg_lambda: 0.0→2.0 (여러 설정 동시 변경) | 12.9416 (1.8521%) | 11.8965 (0.5067%) | 0.038264 / -0.0131%, 0.1151% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0645/result.json) |
| n0646 / 완료 | b10→c142 / n0645 | bound: 0.15→0.1; features: season→age; learning_rate: 0.025→0.05; mode: multiplicative→additive; n_estimators: 80→160; num_leaves: 15→3; shrink: 0.5→1.0 (여러 설정 동시 변경) | 13.2463 (2.3543%) | 11.9486 (0.4376%) | 0.052192 / -0.0280%, 0.1213% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0646/result.json) |
| n0647 / 완료 | b10→c142 / n0645 | bound: 0.15→0.5; features: season→core; half_life: 없음→180; reg_lambda: 2.0→30.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.0871 (1.1244%) | 11.8894 (-0.0600%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0647/result.json) |
| n0648 / 완료 | b10→c142 / n0644 | bound: 0.1→0.2; features: core→season; half_life: 365→180; learning_rate: 0.025→0.05; num_leaves: 7→15; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 13.3882 (3.1291%) | 11.8729 (0.6686%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0648/result.json) |
| n0649 / 완료 | b10→c142 / n0646 | bound: 0.1→0.3; mode: additive→multiplicative; num_leaves: 3→7 (여러 설정 동시 변경) | 13.6197 (2.8192%) | 12.1502 (1.6878%) | 0.007375 / -0.0012%, 0.0138% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0649/result.json) |
| n0650 / 완료 | b10→c142 / n0649 | features: age→core; half_life: 없음→180; min_child_samples: 500→200; mode: multiplicative→additive (여러 설정 동시 변경) | 13.6538 (0.2500%) | 11.9939 (-1.2864%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0650/result.json) |
| n0651 / 완료 | b10→c142 / n0645 | bound: 0.15→0.5; n_estimators: 80→300; reg_lambda: 2.0→30.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | 12.8219 (-0.9251%) | 11.8561 (-0.3399%) | 0.016704 / -0.0034%, 0.0470% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0651/result.json) |
| n0652 / 완료 | b10→c142 / n0644 | bound: 0.1→0.3; features: core→age; n_estimators: 300→80; num_leaves: 7→3; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 12.7543 (-1.7537%) | 11.7534 (-0.3449%) | 0.066340 / -0.0338%, 0.1619% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0652/result.json) |
| n0653 / 완료 | b10→c142 / n0647 | half_life: 180→없음; n_estimators: 80→300; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 13.3477 (1.9910%) | 12.0492 (1.3445%) | 0.023510 / -0.0096%, 0.0558% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0653/result.json) |
| n0654 / 완료 | b10→c142 / n0644 | bound: 0.1→0.2; features: core→season; min_child_samples: 1000→200; num_leaves: 7→3; reg_lambda: 30.0→10.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.0339 (0.3999%) | 11.7594 (-0.2941%) | 0.058068 / -0.0253%, 0.0778% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0654/result.json) |
| n0655 / 완료 | b10→c142 / n0647 | bound: 0.5→0.3; features: core→age; num_leaves: 15→3; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | 12.8537 (-1.7833%) | 11.8490 (-0.3393%) | 0.048077 / -0.0184%, 0.1360% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0655/result.json) |
| n0656 / 완료 | b10→c142 / n0644 | bound: 0.1→0.2; half_life: 365→180; min_child_samples: 1000→200; num_leaves: 7→15 (여러 설정 동시 변경) | 13.1096 (0.9835%) | 11.7359 (-0.4933%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0656/result.json) |
| n0657 / 완료 | b10→c142 / n0645 | half_life: 없음→180; learning_rate: 0.025→0.05; min_child_samples: 500→1000 (여러 설정 동시 변경) | 13.1638 (1.7168%) | 11.8607 (-0.3006%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0657/result.json) |
| n0658 / 완료 | b10→c142 / n0644 | features: core→age; half_life: 365→180; reg_lambda: 30.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | 14.0044 (7.8761%) | 12.0481 (2.1544%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0658/result.json) |
| n0659 / 완료 | b10→c142 / n0650 | half_life: 180→365; mode: additive→multiplicative; num_leaves: 7→15; shrink: 1.0→0.25 (여러 설정 동시 변경) | 12.7980 (-6.2677%) | 11.7919 (-1.6848%) | 0.015226 / -0.0011%, 0.0337% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0659/result.json) |
| n0660 / 완료 | b10→c142 / n0646 | features: age→season; half_life: 없음→365; learning_rate: 0.05→0.025; num_leaves: 3→15; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 13.8662 (4.6801%) | 12.0784 (1.0866%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0660/result.json) |
| n0661 / 완료 | b10→c142 / n0651 | features: season→age; half_life: 없음→365; num_leaves: 15→3; reg_lambda: 30.0→10.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | 13.1298 (2.4017%) | 11.9895 (1.1254%) | 0.064838 / -0.0503%, 0.1385% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0661/result.json) |
| n0662 / 완료 | b10→c142 / n0650 | bound: 0.3→0.1; n_estimators: 160→80; num_leaves: 7→15; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 13.7800 (0.9246%) | 11.9946 (0.0056%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0662/result.json) |
| n0663 / 완료 | b10→c142 / n0657 | half_life: 180→365; num_leaves: 15→7; reg_lambda: 2.0→10.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | 13.2168 (0.4026%) | 11.8941 (0.2813%) | 0.020225 / -0.0054%, 0.0421% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0663/result.json) |
| n0664 / 완료 | b10→c142 / n0658 | bound: 0.1→0.3; num_leaves: 7→3; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | 13.1742 (-5.9285%) | 11.8532 (-1.6179%) | 0.047269 / -0.0287%, 0.0100% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0664/result.json) |
| n0665 / 완료 | b10→c142 / n0647 | bound: 0.5→0.3; min_child_samples: 500→200; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | 13.0817 (-0.0412%) | 11.8718 (-0.1476%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0665/result.json) |
| n0666 / 완료 | b10→c142 / n0662 | bound: 0.1→0.2; features: core→season; half_life: 180→365 (여러 설정 동시 변경) | 14.0756 (2.1449%) | 12.0153 (0.1727%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0666/result.json) |
| n0667 / 완료 | b10→c142 / n0655 | bound: 0.3→0.15; n_estimators: 80→300; num_leaves: 3→7 (여러 설정 동시 변경) | 13.4701 (4.7950%) | 11.9268 (0.6563%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0667/result.json) |
| n0668 / 완료 | b10→c142 / n0646 | features: age→core; num_leaves: 3→7; reg_lambda: 2.0→30.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | 13.1990 (-0.3572%) | 11.8668 (-0.6843%) | 0.059054 / -0.0358%, 0.1090% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0668/result.json) |
| n0669 / 완료 | b10→c142 / n0657 | bound: 0.15→0.3; min_child_samples: 1000→200 (여러 설정 동시 변경) | 13.0968 (-0.5085%) | 11.8778 (0.1437%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0669/result.json) |
| n0670 / 완료 | b10→c142 / n0655 | learning_rate: 0.025→0.05; mode: multiplicative→additive; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 12.8868 (0.2572%) | 11.7427 (-0.8970%) | 0.063112 / -0.0362%, 0.0898% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0670/result.json) |
| n0671 / 완료 | b10→c142 / n0653 | half_life: 없음→365; learning_rate: 0.025→0.05; min_child_samples: 500→200 (여러 설정 동시 변경) | 13.5793 (1.7352%) | 12.0443 (-0.0407%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0671/result.json) |
| n0672 / 완료 | b10→c142 / n0654 | min_child_samples: 200→1000; reg_lambda: 10.0→30.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | 13.2929 (1.9872%) | 11.8623 (0.8757%) | 0.055694 / -0.0406%, 0.0580% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0672/result.json) |
| n0673 / 완료 | b10→c142 / n0649 | learning_rate: 0.05→0.025; num_leaves: 7→3; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | 13.0528 (-4.1621%) | 11.9893 (-1.3241%) | 0.065809 / -0.0539%, 0.2307% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0673/result.json) |
| n0674 / 완료 | b10→c142 / n0653 | bound: 0.5→0.1; mode: multiplicative→additive; shrink: 0.75→1.0 (여러 설정 동시 변경) | 13.8681 (3.8991%) | 12.0758 (0.2204%) | 0.000000 / 0.0000%, 0.0000% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0674/result.json) |
| n0675 / 완료 | b10→c142 / n0655 | bound: 0.3→0.5; features: age→season; min_child_samples: 500→1000; shrink: 0.75→1.0 (여러 설정 동시 변경) | 12.9511 (0.7575%) | 11.9061 (0.4821%) | 0.042160 / -0.0144%, 0.1181% | 5/5 / 5 |  [기록](../../analysis_outputs/research_22h_20261107/trials/n0675/result.json) |
| n0676 / 진행 중 | b10→c142 / n0658 | half_life: 180→없음; reg_lambda: 2.0→10.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 2/5 / 2 |  — |
| n0677 / 대기 | b10→c142 / n0663 | features: season→core; learning_rate: 0.05→0.025; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0678 / 대기 | b10→c142 / n0654 | half_life: 365→180; min_child_samples: 200→500 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0679 / 대기 | b10→c142 / n0651 | features: season→age; learning_rate: 0.025→0.05; min_child_samples: 500→1000; num_leaves: 15→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0680 / 대기 | b10→c142 / n0650 | learning_rate: 0.05→0.025; reg_lambda: 2.0→10.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0681 / 대기 | b10→c142 / n0651 | min_child_samples: 500→200; num_leaves: 15→3; reg_lambda: 30.0→10.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0682 / 대기 | b10→c142 / n0658 | bound: 0.1→0.2; reg_lambda: 2.0→10.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0683 / 대기 | b10→c142 / n0661 | bound: 0.5→0.3; features: age→core; half_life: 365→180 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0684 / 대기 | b10→c142 / n0664 | features: age→season; learning_rate: 0.025→0.05; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0685 / 대기 | b10→c142 / n0652 | mode: additive→multiplicative; num_leaves: 3→7; reg_lambda: 2.0→30.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0686 / 대기 | b10→c142 / n0654 | features: season→core; min_child_samples: 200→500; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0687 / 대기 | b10→c142 / n0660 | bound: 0.1→0.5; min_child_samples: 500→1000; mode: additive→multiplicative; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0688 / 대기 | b10→c142 / n0652 | learning_rate: 0.025→0.05; n_estimators: 80→300; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0689 / 대기 | b10→c142 / n0647 | learning_rate: 0.025→0.05; min_child_samples: 500→1000; n_estimators: 80→160; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0690 / 대기 | b10→c142 / n0669 | learning_rate: 0.05→0.025; mode: multiplicative→additive; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0691 / 대기 | b10→c142 / n0688 | bound: 0.3→0.15; mode: additive→multiplicative; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0692 / 대기 | b10→c142 / n0646 | bound: 0.1→0.2; features: age→core; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0693 / 대기 | b10→c142 / n0673 | features: age→season; min_child_samples: 500→1000; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0694 / 대기 | b10→c142 / n0668 | bound: 0.1→0.2; features: core→age; learning_rate: 0.05→0.025; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0695 / 대기 | b10→c142 / n0653 | bound: 0.5→0.15; min_child_samples: 500→200; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0696 / 대기 | b10→c142 / n0675 | bound: 0.5→0.1; mode: multiplicative→additive; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0697 / 대기 | b10→c142 / n0679 | bound: 0.5→0.15; n_estimators: 300→160; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0698 / 대기 | b10→c142 / n0656 | half_life: 180→365; learning_rate: 0.025→0.05 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0699 / 대기 | b10→c142 / n0657 | min_child_samples: 1000→500; reg_lambda: 2.0→10.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0700 / 대기 | b10→c142 / n0670 | bound: 0.3→0.2; half_life: 180→365; n_estimators: 80→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0701 / 대기 | b10→c142 / n0683 | bound: 0.3→0.15; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0702 / 대기 | b10→c142 / n0658 | features: age→season; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0703 / 대기 | b10→c142 / n0685 | bound: 0.3→0.15; min_child_samples: 1000→200; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0704 / 대기 | b11→c046 / n0704 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0705 / 대기 | b11→c046 / n0704 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0706 / 대기 | b11→c046 / n0704 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0707 / 대기 | b11→c046 / n0705 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0708 / 대기 | b11→c046 / n0704 | bound: 0.2→0.3; half_life: 없음→180; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→500; n_estimators: 0→80; num_leaves: 0→15; reg_lambda: 0.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0709 / 대기 | b11→c046 / n0708 | features: core→season; half_life: 180→없음; min_child_samples: 500→200; mode: additive→multiplicative; num_leaves: 15→7; reg_lambda: 2.0→30.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0710 / 대기 | b11→c046 / n0708 | bound: 0.3→0.2; features: core→age; n_estimators: 80→300; num_leaves: 15→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0711 / 대기 | b11→c046 / n0707 | learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→1000; n_estimators: 0→300; num_leaves: 0→15; reg_lambda: 0.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0712 / 대기 | b11→c046 / n0709 | bound: 0.3→0.1; half_life: 없음→365; mode: multiplicative→additive; n_estimators: 80→160; num_leaves: 7→3; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0713 / 대기 | b11→c046 / n0710 | bound: 0.2→0.3; half_life: 180→365; min_child_samples: 500→1000; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0714 / 대기 | b11→c046 / n0708 | n_estimators: 80→300; num_leaves: 15→3; reg_lambda: 2.0→10.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0715 / 대기 | b11→c046 / n0713 | bound: 0.3→0.15; features: age→season; half_life: 365→180; learning_rate: 0.025→0.05; n_estimators: 300→160; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0716 / 대기 | b11→c046 / n0713 | mode: multiplicative→additive; n_estimators: 300→160; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0717 / 대기 | b11→c046 / n0708 | min_child_samples: 500→200; mode: additive→multiplicative; n_estimators: 80→160; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0718 / 대기 | b11→c046 / n0709 | bound: 0.3→0.2; mode: multiplicative→additive; reg_lambda: 30.0→2.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0719 / 대기 | b11→c046 / n0713 | min_child_samples: 1000→500; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0720 / 대기 | b11→c046 / n0708 | half_life: 180→없음; learning_rate: 0.025→0.05; num_leaves: 15→7; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0721 / 대기 | b11→c046 / n0709 | bound: 0.3→0.5; half_life: 없음→365; learning_rate: 0.025→0.05; num_leaves: 7→15; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0722 / 대기 | b11→c046 / n0716 | bound: 0.3→0.1; learning_rate: 0.025→0.05; num_leaves: 3→7; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0723 / 대기 | b11→c046 / n0715 | bound: 0.15→0.5; features: season→core; half_life: 180→365; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0724 / 대기 | b11→c046 / n0710 | bound: 0.2→0.3; features: age→season; half_life: 180→365; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0725 / 대기 | b11→c046 / n0709 | features: season→age; half_life: 없음→365; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0726 / 대기 | b11→c046 / n0714 | bound: 0.3→0.1; half_life: 180→없음; min_child_samples: 500→200; num_leaves: 3→15; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0727 / 대기 | b11→c046 / n0709 | bound: 0.3→0.15; learning_rate: 0.025→0.05; n_estimators: 80→300; num_leaves: 7→3; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0728 / 대기 | b11→c046 / n0722 | half_life: 365→없음; learning_rate: 0.05→0.025; reg_lambda: 30.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0729 / 대기 | b11→c046 / n0721 | features: season→core; n_estimators: 80→300; num_leaves: 15→7; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0730 / 대기 | b11→c046 / n0724 | bound: 0.3→0.2; n_estimators: 300→160; num_leaves: 3→15; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0731 / 대기 | b11→c046 / n0715 | features: season→age; reg_lambda: 2.0→10.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0732 / 대기 | b11→c046 / n0716 | features: age→core; half_life: 365→없음; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0733 / 대기 | b11→c046 / n0715 | bound: 0.15→0.5; n_estimators: 160→300; num_leaves: 7→15; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0734 / 대기 | b11→c046 / n0710 | bound: 0.2→0.1; min_child_samples: 500→200; n_estimators: 300→80; reg_lambda: 2.0→10.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0735 / 대기 | b11→c046 / n0723 | bound: 0.5→0.3; min_child_samples: 1000→500; reg_lambda: 30.0→10.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0736 / 대기 | b11→c046 / n0724 | learning_rate: 0.025→0.05; min_child_samples: 500→1000; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0737 / 대기 | b11→c046 / n0719 | learning_rate: 0.025→0.05; n_estimators: 300→80; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0738 / 대기 | b11→c046 / n0714 | bound: 0.3→0.2; num_leaves: 3→15; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0739 / 대기 | b11→c046 / n0709 | bound: 0.3→0.5; min_child_samples: 200→1000 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0740 / 대기 | b11→c046 / n0712 | features: season→age; learning_rate: 0.025→0.05; n_estimators: 160→300; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0741 / 대기 | b11→c046 / n0729 | min_child_samples: 200→500; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0742 / 대기 | b11→c046 / n0720 | bound: 0.3→0.2; features: core→season; num_leaves: 7→3; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0743 / 대기 | b11→c046 / n0713 | min_child_samples: 1000→500; n_estimators: 300→80; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0744 / 대기 | b11→c046 / n0708 | bound: 0.3→0.2; learning_rate: 0.025→0.05; min_child_samples: 500→1000; reg_lambda: 2.0→10.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0745 / 대기 | b11→c046 / n0719 | features: age→season; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0746 / 대기 | b11→c046 / n0718 | bound: 0.2→0.3; features: season→age; n_estimators: 80→300; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0747 / 대기 | b11→c046 / n0729 | bound: 0.5→0.3; half_life: 365→180; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0748 / 대기 | b11→c046 / n0712 | learning_rate: 0.025→0.05; n_estimators: 160→300; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0749 / 대기 | b11→c046 / n0725 | min_child_samples: 200→1000; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0750 / 대기 | b11→c046 / n0736 | bound: 0.3→0.2; features: season→core; half_life: 365→없음 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0751 / 대기 | b11→c046 / n0745 | half_life: 365→180; min_child_samples: 500→200; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0752 / 대기 | b11→c046 / n0710 | bound: 0.2→0.1; reg_lambda: 2.0→2.5; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0753 / 대기 | b11→c046 / n0743 | features: age→core; learning_rate: 0.025→0.05 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0754 / 대기 | b11→c046 / n0748 | half_life: 365→없음; min_child_samples: 200→500 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0755 / 대기 | b11→c046 / n0731 | bound: 0.15→0.5; min_child_samples: 1000→500; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0756 / 대기 | b11→c046 / n0710 | features: age→core; n_estimators: 300→160; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0757 / 대기 | b11→c046 / n0724 | bound: 0.3→0.5; learning_rate: 0.025→0.05; mode: additive→multiplicative; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0758 / 대기 | b11→c046 / n0722 | bound: 0.1→0.3; half_life: 365→180; n_estimators: 160→80; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0759 / 대기 | b11→c046 / n0709 | bound: 0.3→0.15; features: season→core; num_leaves: 7→15; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0760 / 대기 | b11→c046 / n0753 | features: core→season; mode: multiplicative→additive; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0761 / 대기 | b11→c046 / n0749 | half_life: 365→180 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0762 / 대기 | b11→c046 / n0708 | bound: 0.3→0.1; reg_lambda: 2.0→30.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0763 / 대기 | b11→c046 / n0709 | min_child_samples: 200→500; n_estimators: 80→160; num_leaves: 7→3; reg_lambda: 30.0→10.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0764 / 대기 | b11→c046 / n0740 | bound: 0.1→0.3; half_life: 365→180 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0765 / 대기 | b11→c046 / n0723 | min_child_samples: 1000→500; num_leaves: 7→3; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0766 / 대기 | b11→c046 / n0748 | bound: 0.1→0.3; num_leaves: 15→7; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0767 / 대기 | b11→c046 / n0717 | features: core→age; num_leaves: 15→7; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0768 / 대기 | b12→c081 / n0768 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0769 / 대기 | b12→c081 / n0768 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0770 / 대기 | b12→c081 / n0768 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0771 / 대기 | b12→c081 / n0769 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0772 / 대기 | b12→c081 / n0768 | bound: 0.2→0.3; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→500; n_estimators: 0→160; num_leaves: 0→15; reg_lambda: 0.0→30.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0773 / 대기 | b12→c081 / n0772 | features: core→season; mode: additive→multiplicative; n_estimators: 160→300; num_leaves: 15→3; reg_lambda: 30.0→2.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0774 / 대기 | b12→c081 / n0772 | features: core→age; half_life: 없음→365; min_child_samples: 500→1000; num_leaves: 15→3; reg_lambda: 30.0→10.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0775 / 대기 | b12→c081 / n0771 | bound: 0.3→0.5; learning_rate: 0.0→0.05; method: median→tree; min_child_samples: 0→200; n_estimators: 0→80; num_leaves: 0→7; reg_lambda: 0.0→30.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0776 / 대기 | b12→c081 / n0773 | bound: 0.3→0.1; half_life: 없음→365; learning_rate: 0.025→0.05; min_child_samples: 500→1000; mode: multiplicative→additive; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0777 / 대기 | b12→c081 / n0775 | bound: 0.5→0.3; features: core→age; n_estimators: 80→160; reg_lambda: 30.0→2.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0778 / 대기 | b12→c081 / n0776 | bound: 0.1→0.2; features: season→core; half_life: 365→180; n_estimators: 300→80; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0779 / 대기 | b12→c081 / n0772 | features: core→season; half_life: 없음→365; min_child_samples: 500→200; mode: additive→multiplicative; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0780 / 대기 | b12→c081 / n0773 | bound: 0.3→0.2; features: season→age; min_child_samples: 500→200; mode: multiplicative→additive; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0781 / 대기 | b12→c081 / n0773 | features: season→core; reg_lambda: 2.0→10.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0782 / 대기 | b12→c081 / n0776 | learning_rate: 0.05→0.025; min_child_samples: 1000→500; n_estimators: 300→80; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0783 / 대기 | b12→c081 / n0777 | bound: 0.3→0.15; half_life: 365→180; min_child_samples: 200→500; n_estimators: 160→80; num_leaves: 7→3; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0784 / 대기 | b12→c081 / n0772 | half_life: 없음→365; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0785 / 대기 | b12→c081 / n0773 | half_life: 없음→180; min_child_samples: 500→1000; num_leaves: 3→7; reg_lambda: 2.0→30.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0786 / 대기 | b12→c081 / n0774 | n_estimators: 160→80; reg_lambda: 10.0→2.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0787 / 대기 | b12→c081 / n0772 | bound: 0.3→0.5; half_life: 없음→180; mode: additive→multiplicative; reg_lambda: 30.0→2.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0788 / 대기 | b12→c081 / n0782 | half_life: 365→180; learning_rate: 0.025→0.05; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0789 / 대기 | b12→c081 / n0773 | bound: 0.3→0.5; features: season→age; half_life: 없음→180 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0790 / 대기 | b12→c081 / n0784 | half_life: 365→180; num_leaves: 15→7; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0791 / 대기 | b12→c081 / n0779 | bound: 0.3→0.15; min_child_samples: 200→1000; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0792 / 대기 | b12→c081 / n0772 | features: core→age; learning_rate: 0.025→0.05; num_leaves: 15→7; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0793 / 대기 | b12→c081 / n0785 | bound: 0.3→0.15; features: season→core; min_child_samples: 1000→500; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0794 / 대기 | b12→c081 / n0776 | bound: 0.1→0.2; half_life: 365→180; n_estimators: 300→160; num_leaves: 3→7; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0795 / 대기 | b12→c081 / n0773 | features: season→age; min_child_samples: 500→1000; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0796 / 대기 | b12→c081 / n0776 | features: season→core; half_life: 365→없음; min_child_samples: 1000→200; reg_lambda: 30.0→2.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0797 / 대기 | b12→c081 / n0791 | bound: 0.15→0.5; num_leaves: 15→3; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0798 / 대기 | b12→c081 / n0772 | bound: 0.3→0.2; features: core→age; n_estimators: 160→300; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0799 / 대기 | b12→c081 / n0775 | learning_rate: 0.05→0.025; n_estimators: 80→160; reg_lambda: 30.0→10.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0800 / 대기 | b12→c081 / n0788 | bound: 0.1→0.2; learning_rate: 0.05→0.025 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0801 / 대기 | b12→c081 / n0793 | features: core→age; half_life: 180→없음; n_estimators: 300→80; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0802 / 대기 | b12→c081 / n0772 | bound: 0.3→0.2; min_child_samples: 500→200; reg_lambda: 30.0→10.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0803 / 대기 | b12→c081 / n0788 | bound: 0.1→0.3; mode: additive→multiplicative; n_estimators: 80→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0804 / 대기 | b12→c081 / n0774 | learning_rate: 0.025→0.05; n_estimators: 160→300; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0805 / 대기 | b12→c081 / n0778 | bound: 0.2→0.3; learning_rate: 0.05→0.025; mode: additive→multiplicative; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0806 / 대기 | b12→c081 / n0799 | bound: 0.5→0.1; features: core→season; mode: multiplicative→additive; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0807 / 대기 | b12→c081 / n0777 | min_child_samples: 200→500; num_leaves: 7→3; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0808 / 대기 | b12→c081 / n0805 | half_life: 180→없음; mode: multiplicative→additive; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0809 / 대기 | b12→c081 / n0779 | bound: 0.3→0.5; half_life: 365→180; n_estimators: 160→300; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0810 / 대기 | b12→c081 / n0784 | features: core→age; n_estimators: 160→80; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0811 / 대기 | b12→c081 / n0805 | min_child_samples: 1000→200; n_estimators: 80→300; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0812 / 대기 | b12→c081 / n0794 | half_life: 180→365; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0813 / 대기 | b12→c081 / n0795 | min_child_samples: 1000→500; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0814 / 대기 | b12→c081 / n0784 | bound: 0.3→0.1; learning_rate: 0.025→0.05; n_estimators: 160→300; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0815 / 대기 | b12→c081 / n0779 | half_life: 365→없음; n_estimators: 160→80; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0816 / 대기 | b12→c081 / n0813 | bound: 0.3→0.1; mode: multiplicative→additive; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0817 / 대기 | b12→c081 / n0783 | bound: 0.15→0.3; features: age→core; min_child_samples: 500→1000; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0818 / 대기 | b12→c081 / n0784 | features: core→season; half_life: 365→180; min_child_samples: 500→200 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0819 / 대기 | b12→c081 / n0795 | learning_rate: 0.025→0.05; n_estimators: 160→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0820 / 대기 | b12→c081 / n0778 | n_estimators: 80→300; num_leaves: 3→7; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0821 / 대기 | b12→c081 / n0775 | features: core→season; learning_rate: 0.05→0.025; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0822 / 대기 | b12→c081 / n0774 | half_life: 365→180; num_leaves: 3→7; reg_lambda: 10.0→2.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0823 / 대기 | b12→c081 / n0789 | features: age→core; half_life: 180→365; learning_rate: 0.025→0.05 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0824 / 대기 | b12→c081 / n0796 | bound: 0.1→0.2; features: core→season; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0825 / 대기 | b12→c081 / n0785 | features: season→age; n_estimators: 300→80; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0826 / 대기 | b12→c081 / n0774 | bound: 0.3→0.1; features: age→core; half_life: 365→180; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0827 / 대기 | b12→c081 / n0803 | bound: 0.3→0.5; half_life: 180→없음; n_estimators: 160→300; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0828 / 대기 | b12→c081 / n0780 | bound: 0.2→0.3; half_life: 없음→180; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0829 / 대기 | b12→c081 / n0805 | min_child_samples: 1000→200 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0830 / 대기 | b12→c081 / n0776 | half_life: 365→없음; learning_rate: 0.05→0.025; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0831 / 대기 | b12→c081 / n0777 | bound: 0.3→0.5; half_life: 365→180; min_child_samples: 200→500; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0832 / 대기 | b13→c010 / n0832 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0833 / 대기 | b13→c010 / n0832 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0834 / 대기 | b13→c010 / n0832 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0835 / 대기 | b13→c010 / n0833 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0836 / 대기 | b13→c010 / n0832 | bound: 0.2→0.3; learning_rate: 0.0→0.05; method: median→tree; min_child_samples: 0→1000; n_estimators: 0→300; num_leaves: 0→7; reg_lambda: 0.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0837 / 대기 | b13→c010 / n0833 | bound: 0.3→0.5; features: core→season; half_life: 없음→180; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→200; n_estimators: 0→160; num_leaves: 0→3; reg_lambda: 0.0→2.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0838 / 대기 | b13→c010 / n0836 | features: core→age; half_life: 없음→180; n_estimators: 300→160; num_leaves: 7→3; reg_lambda: 30.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0839 / 대기 | b13→c010 / n0838 | features: age→core; half_life: 180→없음; mode: additive→multiplicative; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0840 / 대기 | b13→c010 / n0837 | bound: 0.5→0.2; half_life: 180→365; mode: multiplicative→additive; num_leaves: 3→15; reg_lambda: 2.0→10.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0841 / 대기 | b13→c010 / n0838 | bound: 0.3→0.5; min_child_samples: 1000→500; mode: additive→multiplicative; n_estimators: 160→300; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0842 / 대기 | b13→c010 / n0836 | half_life: 없음→365; num_leaves: 7→15; reg_lambda: 30.0→10.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0843 / 대기 | b13→c010 / n0837 | learning_rate: 0.025→0.05; min_child_samples: 200→500; num_leaves: 3→7; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0844 / 대기 | b13→c010 / n0836 | bound: 0.3→0.2; features: core→age; min_child_samples: 1000→500; n_estimators: 300→80; reg_lambda: 30.0→10.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0845 / 대기 | b13→c010 / n0839 | min_child_samples: 1000→200; num_leaves: 3→15; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0846 / 대기 | b13→c010 / n0840 | min_child_samples: 200→500; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0847 / 대기 | b13→c010 / n0837 | bound: 0.5→0.3; features: season→age; min_child_samples: 200→1000; n_estimators: 160→80; num_leaves: 3→7; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0848 / 대기 | b13→c010 / n0840 | bound: 0.2→0.3; features: season→core; learning_rate: 0.025→0.05 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0849 / 대기 | b13→c010 / n0846 | bound: 0.2→0.15; mode: additive→multiplicative; n_estimators: 160→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0850 / 대기 | b13→c010 / n0838 | bound: 0.3→0.1; num_leaves: 3→7; reg_lambda: 2.0→30.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0851 / 대기 | b13→c010 / n0837 | features: season→core; min_child_samples: 200→1000; n_estimators: 160→80; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0852 / 대기 | b13→c010 / n0840 | half_life: 365→180; learning_rate: 0.025→0.05; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0853 / 대기 | b13→c010 / n0841 | learning_rate: 0.05→0.025; min_child_samples: 500→1000; n_estimators: 300→160; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0854 / 대기 | b13→c010 / n0851 | bound: 0.5→0.1; mode: multiplicative→additive; num_leaves: 3→15; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0855 / 대기 | b13→c010 / n0837 | num_leaves: 3→7; reg_lambda: 2.0→10.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0856 / 대기 | b13→c010 / n0844 | bound: 0.2→0.3; learning_rate: 0.05→0.025; num_leaves: 7→3; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0857 / 대기 | b13→c010 / n0841 | features: age→core; half_life: 180→없음; num_leaves: 3→7; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0858 / 대기 | b13→c010 / n0842 | bound: 0.3→0.2; features: core→season; n_estimators: 300→80; num_leaves: 15→7; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0859 / 대기 | b13→c010 / n0855 | bound: 0.5→0.3; features: season→age; half_life: 180→없음; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0860 / 대기 | b13→c010 / n0842 | num_leaves: 15→3; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0861 / 대기 | b13→c010 / n0843 | bound: 0.5→0.15; half_life: 180→365; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0862 / 대기 | b13→c010 / n0850 | half_life: 180→365; reg_lambda: 30.0→10.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0863 / 대기 | b13→c010 / n0847 | features: age→core; min_child_samples: 1000→200; n_estimators: 80→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0864 / 대기 | b13→c010 / n0837 | bound: 0.5→0.2; mode: multiplicative→additive; n_estimators: 160→80; reg_lambda: 2.0→30.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0865 / 대기 | b13→c010 / n0838 | half_life: 180→365; mode: additive→multiplicative; n_estimators: 160→80; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0866 / 대기 | b13→c010 / n0840 | features: season→core; min_child_samples: 200→1000; num_leaves: 15→3; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0867 / 대기 | b13→c010 / n0837 | bound: 0.5→0.15; half_life: 180→없음; n_estimators: 160→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0868 / 대기 | b13→c010 / n0836 | features: core→age; min_child_samples: 1000→500; n_estimators: 300→160; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0869 / 대기 | b13→c010 / n0851 | bound: 0.5→0.3; learning_rate: 0.025→0.05; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0870 / 대기 | b13→c010 / n0852 | bound: 0.2→0.3; learning_rate: 0.05→0.025; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0871 / 대기 | b13→c010 / n0859 | bound: 0.3→0.15; half_life: 없음→365 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0872 / 대기 | b13→c010 / n0867 | bound: 0.15→0.2; features: season→core; mode: multiplicative→additive (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0873 / 대기 | b13→c010 / n0839 | features: core→season; min_child_samples: 1000→500; n_estimators: 160→80; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0874 / 대기 | b13→c010 / n0847 | bound: 0.3→0.1; half_life: 180→365; mode: multiplicative→additive; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0875 / 대기 | b13→c010 / n0857 | bound: 0.5→0.15; min_child_samples: 500→200; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0876 / 대기 | b13→c010 / n0840 | bound: 0.2→0.3; n_estimators: 160→300; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0877 / 대기 | b13→c010 / n0836 | features: core→age; half_life: 없음→180; min_child_samples: 1000→200; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0878 / 대기 | b13→c010 / n0838 | bound: 0.3→0.1; features: age→core; num_leaves: 3→15; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0879 / 대기 | b13→c010 / n0860 | features: core→season; min_child_samples: 1000→500; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0880 / 대기 | b13→c010 / n0838 | min_child_samples: 1000→500; num_leaves: 3→7; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0881 / 대기 | b13→c010 / n0863 | half_life: 180→365; num_leaves: 7→15; reg_lambda: 10.0→2.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0882 / 대기 | b13→c010 / n0864 | min_child_samples: 200→500; num_leaves: 3→7; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0883 / 대기 | b13→c010 / n0847 | bound: 0.3→0.15; learning_rate: 0.025→0.05; min_child_samples: 1000→200; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0884 / 대기 | b13→c010 / n0848 | bound: 0.3→0.2; half_life: 365→180; min_child_samples: 200→500; num_leaves: 15→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0885 / 대기 | b13→c010 / n0879 | bound: 0.3→0.5; min_child_samples: 500→200; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0886 / 대기 | b13→c010 / n0885 | bound: 0.5→0.2; features: season→age; mode: multiplicative→additive (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0887 / 대기 | b13→c010 / n0863 | bound: 0.3→0.15; min_child_samples: 200→500; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0888 / 대기 | b13→c010 / n0836 | features: core→season; num_leaves: 7→3; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0889 / 대기 | b13→c010 / n0860 | bound: 0.3→0.15; features: core→age; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0890 / 대기 | b13→c010 / n0884 | half_life: 180→365; reg_lambda: 10.0→30.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0891 / 대기 | b13→c010 / n0839 | features: core→season; min_child_samples: 1000→200; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0892 / 대기 | b13→c010 / n0846 | features: season→age; num_leaves: 15→7; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0893 / 대기 | b13→c010 / n0845 | bound: 0.3→0.5; reg_lambda: 30.0→30.5; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0894 / 대기 | b13→c010 / n0836 | bound: 0.3→0.1; features: core→season; min_child_samples: 1000→200; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0895 / 대기 | b13→c010 / n0853 | bound: 0.5→0.15; half_life: 180→365; reg_lambda: 30.0→2.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0896 / 대기 | b14→c191 / n0896 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0897 / 대기 | b14→c191 / n0896 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0898 / 대기 | b14→c191 / n0896 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0899 / 대기 | b14→c191 / n0897 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0900 / 대기 | b14→c191 / n0896 | bound: 0.2→0.1; half_life: 없음→180; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→500; n_estimators: 0→80; num_leaves: 0→3; reg_lambda: 0.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0901 / 대기 | b14→c191 / n0900 | bound: 0.1→0.5; features: core→season; learning_rate: 0.025→0.05; min_child_samples: 500→200; mode: additive→multiplicative; n_estimators: 80→300; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0902 / 대기 | b14→c191 / n0900 | bound: 0.1→0.2; features: core→age; min_child_samples: 500→1000; reg_lambda: 2.0→10.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0903 / 대기 | b14→c191 / n0900 | bound: 0.1→0.5; half_life: 180→365; mode: additive→multiplicative; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0904 / 대기 | b14→c191 / n0900 | features: core→season; min_child_samples: 500→200; n_estimators: 80→300; num_leaves: 3→7; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0905 / 대기 | b14→c191 / n0901 | bound: 0.5→0.3; features: season→age; half_life: 180→365; n_estimators: 300→160; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0906 / 대기 | b14→c191 / n0900 | num_leaves: 3→7 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0907 / 대기 | b14→c191 / n0901 | num_leaves: 3→15; reg_lambda: 2.0→30.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0908 / 대기 | b14→c191 / n0906 | features: core→age; learning_rate: 0.025→0.05; n_estimators: 80→300; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0909 / 대기 | b14→c191 / n0907 | bound: 0.5→0.3; features: season→core; min_child_samples: 200→500; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0910 / 대기 | b14→c191 / n0901 | bound: 0.5→0.3; half_life: 180→없음; min_child_samples: 200→500; mode: multiplicative→additive; reg_lambda: 2.0→10.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0911 / 대기 | b14→c191 / n0903 | bound: 0.5→0.3; features: core→age; num_leaves: 3→7; reg_lambda: 2.0→10.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0912 / 대기 | b14→c191 / n0900 | bound: 0.1→0.2; half_life: 180→없음; n_estimators: 80→160; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0913 / 대기 | b14→c191 / n0904 | bound: 0.1→0.5; min_child_samples: 200→500; mode: additive→multiplicative; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0914 / 대기 | b14→c191 / n0904 | bound: 0.1→0.2; features: season→age; half_life: 180→없음; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0915 / 대기 | b14→c191 / n0909 | bound: 0.3→0.15; n_estimators: 80→160; reg_lambda: 30.0→10.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0916 / 대기 | b14→c191 / n0901 | bound: 0.5→0.3; mode: multiplicative→additive; n_estimators: 300→160; num_leaves: 3→7; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0917 / 대기 | b14→c191 / n0911 | bound: 0.3→0.15; learning_rate: 0.025→0.05; min_child_samples: 500→1000; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0918 / 대기 | b14→c191 / n0902 | features: age→core; half_life: 180→365; min_child_samples: 1000→200; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0919 / 대기 | b14→c191 / n0901 | bound: 0.5→0.3; reg_lambda: 2.0→10.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0920 / 대기 | b14→c191 / n0910 | features: season→age; min_child_samples: 500→1000; reg_lambda: 10.0→2.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0921 / 대기 | b14→c191 / n0909 | bound: 0.3→0.15; learning_rate: 0.05→0.025 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0922 / 대기 | b14→c191 / n0914 | features: age→season; learning_rate: 0.025→0.05; n_estimators: 300→160; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0923 / 대기 | b14→c191 / n0911 | bound: 0.3→0.15; n_estimators: 80→160; num_leaves: 7→3; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0924 / 대기 | b14→c191 / n0906 | bound: 0.1→0.2; learning_rate: 0.025→0.05; n_estimators: 80→160; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0925 / 대기 | b14→c191 / n0907 | half_life: 180→365; learning_rate: 0.05→0.025; num_leaves: 15→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0926 / 대기 | b14→c191 / n0914 | half_life: 없음→365; min_child_samples: 200→1000; reg_lambda: 10.0→2.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0927 / 대기 | b14→c191 / n0909 | bound: 0.3→0.5; reg_lambda: 30.0→30.5; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0928 / 대기 | b14→c191 / n0916 | half_life: 180→365; learning_rate: 0.05→0.025; min_child_samples: 200→1000; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0929 / 대기 | b14→c191 / n0905 | bound: 0.3→0.5; learning_rate: 0.05→0.025; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0930 / 대기 | b14→c191 / n0912 | reg_lambda: 10.0→30.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0931 / 대기 | b14→c191 / n0919 | half_life: 180→없음; n_estimators: 300→160; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0932 / 대기 | b14→c191 / n0917 | bound: 0.15→0.2; half_life: 365→없음; mode: multiplicative→additive (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0933 / 대기 | b14→c191 / n0909 | min_child_samples: 500→200; num_leaves: 15→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0934 / 대기 | b14→c191 / n0902 | bound: 0.2→0.1; features: age→season; learning_rate: 0.025→0.05; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0935 / 대기 | b14→c191 / n0929 | learning_rate: 0.025→0.05; min_child_samples: 200→1000; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0936 / 대기 | b14→c191 / n0905 | bound: 0.3→0.2; features: age→core; mode: multiplicative→additive (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0937 / 대기 | b14→c191 / n0935 | features: age→season; n_estimators: 160→80; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0938 / 대기 | b14→c191 / n0916 | features: season→age; learning_rate: 0.05→0.025; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0939 / 대기 | b14→c191 / n0916 | features: season→core; mode: additive→multiplicative; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0940 / 대기 | b14→c191 / n0926 | features: age→season; learning_rate: 0.025→0.05; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0941 / 대기 | b14→c191 / n0917 | half_life: 365→180; n_estimators: 80→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0942 / 대기 | b14→c191 / n0922 | features: season→core; num_leaves: 15→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0943 / 대기 | b14→c191 / n0937 | half_life: 365→없음; learning_rate: 0.05→0.025; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0944 / 대기 | b14→c191 / n0900 | features: core→age; learning_rate: 0.025→0.05; n_estimators: 80→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0945 / 대기 | b14→c191 / n0943 | bound: 0.5→0.3; features: season→core; reg_lambda: 10.0→2.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0946 / 대기 | b14→c191 / n0912 | bound: 0.2→0.3; features: core→season; min_child_samples: 500→1000; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0947 / 대기 | b14→c191 / n0929 | min_child_samples: 200→500; n_estimators: 160→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0948 / 대기 | b14→c191 / n0910 | features: season→core; half_life: 없음→365; num_leaves: 3→15; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0949 / 대기 | b14→c191 / n0945 | features: core→season; learning_rate: 0.025→0.05 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0950 / 대기 | b14→c191 / n0926 | bound: 0.2→0.1; learning_rate: 0.025→0.05; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0951 / 대기 | b14→c191 / n0901 | features: season→core; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0952 / 대기 | b14→c191 / n0946 | bound: 0.3→0.1; n_estimators: 160→300; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0953 / 대기 | b14→c191 / n0941 | learning_rate: 0.05→0.025; min_child_samples: 1000→200; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0954 / 대기 | b14→c191 / n0916 | bound: 0.3→0.1; features: season→core; half_life: 180→365 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0955 / 대기 | b14→c191 / n0946 | half_life: 없음→180; mode: additive→multiplicative; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0956 / 대기 | b14→c191 / n0926 | min_child_samples: 1000→200; num_leaves: 7→3; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0957 / 대기 | b14→c191 / n0901 | bound: 0.5→0.3; features: season→core; half_life: 180→없음 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0958 / 대기 | b14→c191 / n0907 | bound: 0.5→0.2; mode: multiplicative→additive; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0959 / 대기 | b14→c191 / n0911 | half_life: 365→180; min_child_samples: 500→200; reg_lambda: 10.0→30.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0960 / 대기 | b15→c170 / n0960 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0961 / 대기 | b15→c170 / n0960 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0962 / 대기 | b15→c170 / n0960 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0963 / 대기 | b15→c170 / n0961 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0964 / 대기 | b15→c170 / n0960 | learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→200; n_estimators: 0→160; num_leaves: 0→7; reg_lambda: 0.0→10.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0965 / 대기 | b15→c170 / n0964 | bound: 0.2→0.15; features: core→season; half_life: 없음→365; min_child_samples: 200→500; mode: additive→multiplicative; n_estimators: 160→300; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0966 / 대기 | b15→c170 / n0964 | bound: 0.2→0.1; features: core→age; half_life: 없음→365; learning_rate: 0.025→0.05; min_child_samples: 200→500; num_leaves: 7→3; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0967 / 대기 | b15→c170 / n0964 | bound: 0.2→0.5; min_child_samples: 200→1000; mode: additive→multiplicative; num_leaves: 7→3; reg_lambda: 10.0→30.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0968 / 대기 | b15→c170 / n0964 | features: core→season; half_life: 없음→365; min_child_samples: 200→1000; n_estimators: 160→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0969 / 대기 | b15→c170 / n0965 | bound: 0.15→0.3; features: season→age; half_life: 365→180; n_estimators: 300→80; reg_lambda: 10.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0970 / 대기 | b15→c170 / n0965 | bound: 0.15→0.1; features: season→core; half_life: 365→180; learning_rate: 0.025→0.05; mode: multiplicative→additive; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0971 / 대기 | b15→c170 / n0965 | half_life: 365→없음; learning_rate: 0.025→0.05; min_child_samples: 500→1000; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0972 / 대기 | b15→c170 / n0971 | bound: 0.15→0.2; features: season→age; mode: multiplicative→additive; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0973 / 대기 | b15→c170 / n0967 | half_life: 없음→180; min_child_samples: 1000→500; num_leaves: 3→15; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0974 / 대기 | b15→c170 / n0970 | features: core→season; min_child_samples: 500→1000; n_estimators: 300→80; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0975 / 대기 | b15→c170 / n0969 | bound: 0.3→0.5; half_life: 180→365 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0976 / 대기 | b15→c170 / n0964 | learning_rate: 0.025→0.05; min_child_samples: 200→500; num_leaves: 7→3; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0977 / 대기 | b15→c170 / n0969 | features: age→season; half_life: 180→365; num_leaves: 7→3; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0978 / 대기 | b15→c170 / n0970 | features: core→age; half_life: 180→365; learning_rate: 0.05→0.025; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0979 / 대기 | b15→c170 / n0973 | half_life: 180→365; learning_rate: 0.025→0.05; min_child_samples: 500→200; n_estimators: 160→80; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0980 / 대기 | b15→c170 / n0966 | bound: 0.1→0.3; features: age→season; half_life: 365→180; num_leaves: 3→15; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0981 / 대기 | b15→c170 / n0969 | half_life: 180→365; n_estimators: 80→160; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0982 / 대기 | b15→c170 / n0966 | features: age→core; min_child_samples: 500→200; num_leaves: 3→15; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0983 / 대기 | b15→c170 / n0968 | bound: 0.2→0.3; half_life: 365→180; mode: additive→multiplicative; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0984 / 대기 | b15→c170 / n0972 | half_life: 없음→180; reg_lambda: 10.0→30.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0985 / 대기 | b15→c170 / n0983 | features: season→core; min_child_samples: 1000→200; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0986 / 대기 | b15→c170 / n0964 | bound: 0.2→0.3; features: core→season; half_life: 없음→180; n_estimators: 160→300; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0987 / 대기 | b15→c170 / n0969 | half_life: 180→365; learning_rate: 0.025→0.05; n_estimators: 80→300; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0988 / 대기 | b15→c170 / n0978 | features: age→core; half_life: 365→없음; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0989 / 대기 | b15→c170 / n0973 | bound: 0.5→0.15; features: core→season; learning_rate: 0.025→0.05; num_leaves: 15→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0990 / 대기 | b15→c170 / n0969 | learning_rate: 0.025→0.05; mode: multiplicative→additive; reg_lambda: 2.0→10.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0991 / 대기 | b15→c170 / n0971 | bound: 0.15→0.3; features: season→core; half_life: 없음→180; min_child_samples: 1000→200; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0992 / 대기 | b15→c170 / n0986 | half_life: 180→없음; reg_lambda: 10.0→2.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0993 / 대기 | b15→c170 / n0971 | features: season→age; learning_rate: 0.05→0.025; n_estimators: 300→80; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0994 / 대기 | b15→c170 / n0988 | bound: 0.1→0.3; reg_lambda: 30.0→30.5; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0995 / 대기 | b15→c170 / n0965 | reg_lambda: 10.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0996 / 대기 | b15→c170 / n0966 | half_life: 365→없음; reg_lambda: 10.0→2.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0997 / 대기 | b15→c170 / n0979 | half_life: 365→없음; num_leaves: 15→7; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0998 / 대기 | b15→c170 / n0986 | n_estimators: 300→80; reg_lambda: 10.0→30.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n0999 / 대기 | b15→c170 / n0969 | half_life: 180→365; learning_rate: 0.025→0.05; num_leaves: 7→3; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1000 / 대기 | b15→c170 / n0973 | bound: 0.5→0.1; half_life: 180→없음; mode: multiplicative→additive; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1001 / 대기 | b15→c170 / n0969 | bound: 0.3→0.5; features: age→season; learning_rate: 0.025→0.05; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1002 / 대기 | b15→c170 / n0966 | bound: 0.1→0.2; half_life: 365→180; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1003 / 대기 | b15→c170 / n0967 | bound: 0.5→0.3; num_leaves: 3→7; reg_lambda: 30.0→2.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1004 / 대기 | b15→c170 / n0968 | min_child_samples: 1000→200; n_estimators: 80→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1005 / 대기 | b15→c170 / n0965 | features: season→age; half_life: 365→없음; learning_rate: 0.025→0.05; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1006 / 대기 | b15→c170 / n1000 | min_child_samples: 500→1000; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1007 / 대기 | b15→c170 / n0977 | min_child_samples: 500→1000; n_estimators: 80→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1008 / 대기 | b15→c170 / n0988 | bound: 0.1→0.3; features: core→age; min_child_samples: 500→1000 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1009 / 대기 | b15→c170 / n0987 | bound: 0.3→0.15; features: age→core; min_child_samples: 500→1000; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1010 / 대기 | b15→c170 / n0992 | learning_rate: 0.025→0.05; num_leaves: 7→15; reg_lambda: 2.0→30.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1011 / 대기 | b15→c170 / n0993 | half_life: 없음→180; min_child_samples: 1000→500; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1012 / 대기 | b15→c170 / n0991 | learning_rate: 0.05→0.025; min_child_samples: 200→500; mode: multiplicative→additive (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1013 / 대기 | b15→c170 / n0965 | learning_rate: 0.025→0.05; num_leaves: 7→15; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1014 / 대기 | b15→c170 / n0972 | bound: 0.2→0.1; half_life: 없음→365; num_leaves: 3→7; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1015 / 대기 | b15→c170 / n0967 | n_estimators: 160→80; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1016 / 대기 | b15→c170 / n0968 | n_estimators: 80→300; num_leaves: 7→15; reg_lambda: 10.0→2.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1017 / 대기 | b15→c170 / n1009 | features: core→age; half_life: 365→180; min_child_samples: 1000→200 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1018 / 대기 | b15→c170 / n0984 | bound: 0.2→0.3; features: age→core; half_life: 180→365; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1019 / 대기 | b15→c170 / n0971 | min_child_samples: 1000→200; n_estimators: 300→80; num_leaves: 3→7; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1020 / 대기 | b15→c170 / n0981 | mode: multiplicative→additive; num_leaves: 7→3; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1021 / 대기 | b15→c170 / n1011 | features: age→core; learning_rate: 0.025→0.05; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1022 / 대기 | b15→c170 / n1016 | bound: 0.2→0.3; learning_rate: 0.025→0.05 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1023 / 대기 | b15→c170 / n0971 | features: season→age; min_child_samples: 1000→200; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1024 / 대기 | b16→c128 / n1024 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1025 / 대기 | b16→c128 / n1024 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1026 / 대기 | b16→c128 / n1024 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1027 / 대기 | b16→c128 / n1025 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1028 / 대기 | b16→c128 / n1024 | bound: 0.2→0.3; half_life: 없음→180; learning_rate: 0.0→0.05; method: median→tree; min_child_samples: 0→500; n_estimators: 0→80; num_leaves: 0→3; reg_lambda: 0.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1029 / 대기 | b16→c128 / n1028 | features: core→season; half_life: 180→없음; mode: additive→multiplicative; num_leaves: 3→7; reg_lambda: 2.0→30.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1030 / 대기 | b16→c128 / n1028 | bound: 0.3→0.2; features: core→age; half_life: 180→없음; n_estimators: 80→300; num_leaves: 3→7; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1031 / 대기 | b16→c128 / n1029 | bound: 0.3→0.15; features: season→core; learning_rate: 0.05→0.025; min_child_samples: 500→200; num_leaves: 7→15; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1032 / 대기 | b16→c128 / n1030 | features: age→season; half_life: 없음→365; learning_rate: 0.05→0.025; min_child_samples: 500→200; num_leaves: 7→15; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1033 / 대기 | b16→c128 / n1028 | bound: 0.3→0.5; features: core→age; half_life: 180→없음; min_child_samples: 500→1000; mode: additive→multiplicative; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1034 / 대기 | b16→c128 / n1028 | half_life: 180→365; learning_rate: 0.05→0.025; n_estimators: 80→160; num_leaves: 3→7; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1035 / 대기 | b16→c128 / n1029 | bound: 0.3→0.5; learning_rate: 0.05→0.025; n_estimators: 80→300; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1036 / 대기 | b16→c128 / n1028 | features: core→age; min_child_samples: 500→200; n_estimators: 80→300; num_leaves: 3→7; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1037 / 대기 | b16→c128 / n1028 | half_life: 180→없음; mode: additive→multiplicative; num_leaves: 3→15; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1038 / 대기 | b16→c128 / n1032 | min_child_samples: 200→1000; n_estimators: 300→160; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1039 / 대기 | b16→c128 / n1030 | bound: 0.2→0.15; min_child_samples: 500→200; mode: additive→multiplicative; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1040 / 대기 | b16→c128 / n1036 | features: age→core; half_life: 180→365; min_child_samples: 200→1000; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1041 / 대기 | b16→c128 / n1031 | features: core→season; half_life: 없음→180; min_child_samples: 200→1000; num_leaves: 15→3; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1042 / 대기 | b16→c128 / n1028 | bound: 0.3→0.2; features: core→age; min_child_samples: 500→1000; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1043 / 대기 | b16→c128 / n1033 | features: age→core; half_life: 없음→365; learning_rate: 0.05→0.025; min_child_samples: 1000→200; n_estimators: 80→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1044 / 대기 | b16→c128 / n1038 | half_life: 365→180; num_leaves: 7→3; reg_lambda: 30.0→10.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1045 / 대기 | b16→c128 / n1029 | features: season→age; learning_rate: 0.05→0.025; num_leaves: 7→3; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1046 / 대기 | b16→c128 / n1040 | learning_rate: 0.05→0.025; n_estimators: 300→80; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1047 / 대기 | b16→c128 / n1032 | bound: 0.2→0.5; half_life: 365→180; min_child_samples: 200→1000; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1048 / 대기 | b16→c128 / n1034 | bound: 0.3→0.1; features: core→age; n_estimators: 160→300; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1049 / 대기 | b16→c128 / n1043 | bound: 0.5→0.3; half_life: 365→180; reg_lambda: 2.0→10.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1050 / 대기 | b16→c128 / n1032 | num_leaves: 15→7; reg_lambda: 30.0→10.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1051 / 대기 | b16→c128 / n1045 | min_child_samples: 500→200; n_estimators: 80→160; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1052 / 대기 | b16→c128 / n1031 | bound: 0.15→0.2; half_life: 없음→365; learning_rate: 0.025→0.05; mode: multiplicative→additive (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1053 / 대기 | b16→c128 / n1037 | bound: 0.3→0.15; features: core→season; half_life: 없음→180; n_estimators: 80→300; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1054 / 대기 | b16→c128 / n1033 | bound: 0.5→0.1; mode: multiplicative→additive; n_estimators: 80→300; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1055 / 대기 | b16→c128 / n1045 | features: age→core; learning_rate: 0.025→0.05; min_child_samples: 500→200 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1056 / 대기 | b16→c128 / n1032 | n_estimators: 300→80; num_leaves: 15→3; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1057 / 대기 | b16→c128 / n1045 | learning_rate: 0.025→0.05; n_estimators: 80→160; reg_lambda: 30.0→10.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1058 / 대기 | b16→c128 / n1036 | bound: 0.3→0.2; features: age→core; half_life: 180→없음; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1059 / 대기 | b16→c128 / n1033 | features: age→season; learning_rate: 0.05→0.025; num_leaves: 3→15; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1060 / 대기 | b16→c128 / n1058 | features: core→age; n_estimators: 160→80; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1061 / 대기 | b16→c128 / n1028 | mode: additive→multiplicative; n_estimators: 80→300; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1062 / 대기 | b16→c128 / n1040 | bound: 0.3→0.1; features: core→season; n_estimators: 300→80; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1063 / 대기 | b16→c128 / n1039 | half_life: 없음→180; learning_rate: 0.05→0.025; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1064 / 대기 | b16→c128 / n1062 | features: season→core; n_estimators: 80→160; num_leaves: 7→3; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1065 / 대기 | b16→c128 / n1037 | features: core→season; half_life: 없음→180; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1066 / 대기 | b16→c128 / n1036 | num_leaves: 7→3; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1067 / 대기 | b16→c128 / n1043 | reg_lambda: 2.0→10.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1068 / 대기 | b16→c128 / n1038 | half_life: 365→180; min_child_samples: 1000→500; n_estimators: 160→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1069 / 대기 | b16→c128 / n1029 | bound: 0.3→0.5; features: season→age; half_life: 없음→180; min_child_samples: 500→200 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1070 / 대기 | b16→c128 / n1031 | bound: 0.15→0.3; mode: multiplicative→additive; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1071 / 대기 | b16→c128 / n1067 | features: core→season; half_life: 365→180 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1072 / 대기 | b16→c128 / n1036 | half_life: 180→365; n_estimators: 300→80; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1073 / 대기 | b16→c128 / n1037 | learning_rate: 0.05→0.025; n_estimators: 80→160; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1074 / 대기 | b16→c128 / n1056 | bound: 0.2→0.3; n_estimators: 80→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1075 / 대기 | b16→c128 / n1045 | min_child_samples: 500→1000; n_estimators: 80→160; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1076 / 대기 | b16→c128 / n1058 | bound: 0.2→0.1; half_life: 없음→180; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1077 / 대기 | b16→c128 / n1074 | learning_rate: 0.025→0.05; mode: additive→multiplicative; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1078 / 대기 | b16→c128 / n1036 | bound: 0.3→0.2; min_child_samples: 200→500; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1079 / 대기 | b16→c128 / n1029 | features: season→core; n_estimators: 80→160; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1080 / 대기 | b16→c128 / n1044 | bound: 0.2→0.1; learning_rate: 0.025→0.05; num_leaves: 3→7; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1081 / 대기 | b16→c128 / n1066 | learning_rate: 0.05→0.025; mode: additive→multiplicative; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1082 / 대기 | b16→c128 / n1068 | bound: 0.2→0.1; features: season→core (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1083 / 대기 | b16→c128 / n1041 | half_life: 180→365; min_child_samples: 1000→200; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1084 / 대기 | b16→c128 / n1048 | half_life: 365→없음; learning_rate: 0.025→0.05; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1085 / 대기 | b16→c128 / n1047 | features: season→core; half_life: 180→365 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1086 / 대기 | b16→c128 / n1044 | min_child_samples: 1000→200; num_leaves: 3→7; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1087 / 대기 | b16→c128 / n1033 | num_leaves: 3→7; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1088 / 대기 | b17→c115 / n1088 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1089 / 대기 | b17→c115 / n1088 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1090 / 대기 | b17→c115 / n1088 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1091 / 대기 | b17→c115 / n1089 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1092 / 대기 | b17→c115 / n1088 | bound: 0.2→0.3; half_life: 없음→180; learning_rate: 0.0→0.05; method: median→tree; min_child_samples: 0→1000; n_estimators: 0→160; num_leaves: 0→7; reg_lambda: 0.0→30.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1093 / 대기 | b17→c115 / n1089 | features: core→season; half_life: 없음→180; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→500; n_estimators: 0→300; num_leaves: 0→15; reg_lambda: 0.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1094 / 대기 | b17→c115 / n1092 | bound: 0.3→0.1; features: core→age; half_life: 180→없음; learning_rate: 0.05→0.025; n_estimators: 160→80; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1095 / 대기 | b17→c115 / n1092 | mode: additive→multiplicative; n_estimators: 160→300; reg_lambda: 30.0→2.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1096 / 대기 | b17→c115 / n1092 | bound: 0.3→0.2; features: core→season; min_child_samples: 1000→200; n_estimators: 160→80; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1097 / 대기 | b17→c115 / n1093 | bound: 0.3→0.15; features: season→age; learning_rate: 0.025→0.05; min_child_samples: 500→200; num_leaves: 15→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1098 / 대기 | b17→c115 / n1092 | bound: 0.3→0.1; half_life: 180→없음; n_estimators: 160→300; num_leaves: 7→15; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1099 / 대기 | b17→c115 / n1093 | bound: 0.3→0.15; half_life: 180→없음; num_leaves: 15→7; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1100 / 대기 | b17→c115 / n1093 | bound: 0.3→0.1; features: season→age; mode: multiplicative→additive; num_leaves: 15→7; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1101 / 대기 | b17→c115 / n1095 | half_life: 180→365; num_leaves: 7→15; reg_lambda: 2.0→10.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1102 / 대기 | b17→c115 / n1093 | half_life: 180→365; mode: multiplicative→additive; n_estimators: 300→160; reg_lambda: 2.0→10.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1103 / 대기 | b17→c115 / n1094 | bound: 0.1→0.5; mode: additive→multiplicative; num_leaves: 7→3; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1104 / 대기 | b17→c115 / n1096 | bound: 0.2→0.1; features: season→core; min_child_samples: 200→500 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1105 / 대기 | b17→c115 / n1093 | half_life: 180→없음; n_estimators: 300→160; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1106 / 대기 | b17→c115 / n1094 | bound: 0.1→0.3; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1107 / 대기 | b17→c115 / n1093 | features: season→core; half_life: 180→없음; num_leaves: 15→3; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1108 / 대기 | b17→c115 / n1102 | n_estimators: 160→80; num_leaves: 15→3; reg_lambda: 10.0→2.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1109 / 대기 | b17→c115 / n1108 | features: season→age; min_child_samples: 500→200; mode: additive→multiplicative; n_estimators: 80→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1110 / 대기 | b17→c115 / n1092 | learning_rate: 0.05→0.025; min_child_samples: 1000→200; n_estimators: 160→300; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1111 / 대기 | b17→c115 / n1099 | half_life: 없음→365; learning_rate: 0.025→0.05; reg_lambda: 2.0→30.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1112 / 대기 | b17→c115 / n1100 | bound: 0.1→0.3; n_estimators: 300→80; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1113 / 대기 | b17→c115 / n1101 | bound: 0.3→0.5; learning_rate: 0.05→0.025; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1114 / 대기 | b17→c115 / n1108 | half_life: 365→없음; learning_rate: 0.025→0.05 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1115 / 대기 | b17→c115 / n1109 | bound: 0.3→0.5; min_child_samples: 200→500; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1116 / 대기 | b17→c115 / n1098 | half_life: 없음→365; min_child_samples: 1000→500; num_leaves: 15→3; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1117 / 대기 | b17→c115 / n1095 | features: core→season; reg_lambda: 2.0→10.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1118 / 대기 | b17→c115 / n1112 | bound: 0.3→0.2; num_leaves: 7→3; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1119 / 대기 | b17→c115 / n1113 | num_leaves: 15→7 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1120 / 대기 | b17→c115 / n1102 | learning_rate: 0.025→0.05; min_child_samples: 500→1000; reg_lambda: 10.0→2.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1121 / 대기 | b17→c115 / n1103 | bound: 0.5→0.15; min_child_samples: 1000→500; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1122 / 대기 | b17→c115 / n1108 | features: season→core; n_estimators: 80→160; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1123 / 대기 | b17→c115 / n1111 | min_child_samples: 500→200; num_leaves: 7→15; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1124 / 대기 | b17→c115 / n1092 | features: core→age; half_life: 180→365; min_child_samples: 1000→200; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1125 / 대기 | b17→c115 / n1101 | bound: 0.3→0.5; min_child_samples: 1000→200; n_estimators: 300→160; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1126 / 대기 | b17→c115 / n1096 | half_life: 180→365; learning_rate: 0.05→0.025; n_estimators: 80→160; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1127 / 대기 | b17→c115 / n1099 | features: season→age (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1128 / 대기 | b17→c115 / n1110 | bound: 0.3→0.2; half_life: 180→없음 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1129 / 대기 | b17→c115 / n1105 | min_child_samples: 500→200; n_estimators: 160→80; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1130 / 대기 | b17→c115 / n1100 | bound: 0.1→0.3; reg_lambda: 2.0→2.5; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1131 / 대기 | b17→c115 / n1095 | learning_rate: 0.05→0.025; n_estimators: 300→160; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1132 / 대기 | b17→c115 / n1100 | features: age→season; half_life: 180→365; min_child_samples: 500→1000 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1133 / 대기 | b17→c115 / n1097 | min_child_samples: 200→1000; n_estimators: 300→80; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1134 / 대기 | b17→c115 / n1110 | bound: 0.3→0.2; num_leaves: 7→15; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1135 / 대기 | b17→c115 / n1111 | half_life: 365→180; min_child_samples: 500→1000; reg_lambda: 30.0→10.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1136 / 대기 | b17→c115 / n1130 | num_leaves: 7→3; reg_lambda: 2.5→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1137 / 대기 | b17→c115 / n1107 | bound: 0.3→0.15; n_estimators: 300→160; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1138 / 대기 | b17→c115 / n1107 | bound: 0.3→0.2; features: core→season; mode: multiplicative→additive (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1139 / 대기 | b17→c115 / n1103 | min_child_samples: 1000→500 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1140 / 대기 | b17→c115 / n1114 | features: season→core; min_child_samples: 500→1000; n_estimators: 80→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1141 / 대기 | b17→c115 / n1129 | bound: 0.3→0.5; learning_rate: 0.025→0.05; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1142 / 대기 | b17→c115 / n1102 | features: season→age; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1143 / 대기 | b17→c115 / n1125 | n_estimators: 160→80; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1144 / 대기 | b17→c115 / n1114 | half_life: 없음→180; n_estimators: 80→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1145 / 대기 | b17→c115 / n1111 | features: season→age; n_estimators: 300→80; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1146 / 대기 | b17→c115 / n1128 | n_estimators: 300→160; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1147 / 대기 | b17→c115 / n1096 | bound: 0.2→0.5; min_child_samples: 200→1000; mode: additive→multiplicative; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1148 / 대기 | b17→c115 / n1118 | bound: 0.2→0.3; learning_rate: 0.025→0.05; min_child_samples: 500→1000 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1149 / 대기 | b17→c115 / n1103 | features: age→core; half_life: 없음→180; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1150 / 대기 | b17→c115 / n1126 | min_child_samples: 200→500; n_estimators: 160→300; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1151 / 대기 | b17→c115 / n1139 | num_leaves: 3→7; reg_lambda: 30.0→10.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1152 / 대기 | b18→c038 / n1152 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1153 / 대기 | b18→c038 / n1152 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1154 / 대기 | b18→c038 / n1152 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1155 / 대기 | b18→c038 / n1153 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1156 / 대기 | b18→c038 / n1152 | half_life: 없음→180; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→1000; n_estimators: 0→300; num_leaves: 0→7; reg_lambda: 0.0→30.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1157 / 대기 | b18→c038 / n1156 | bound: 0.2→0.5; features: core→season; learning_rate: 0.025→0.05; min_child_samples: 1000→500; mode: additive→multiplicative; n_estimators: 300→160; num_leaves: 7→3; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1158 / 대기 | b18→c038 / n1157 | bound: 0.5→0.1; features: season→age; half_life: 180→없음; mode: multiplicative→additive; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1159 / 대기 | b18→c038 / n1156 | bound: 0.2→0.15; half_life: 180→없음; min_child_samples: 1000→200; mode: additive→multiplicative; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1160 / 대기 | b18→c038 / n1157 | bound: 0.5→0.2; min_child_samples: 500→200; mode: multiplicative→additive; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1161 / 대기 | b18→c038 / n1157 | features: season→age; min_child_samples: 500→1000; n_estimators: 160→80; reg_lambda: 2.0→30.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1162 / 대기 | b18→c038 / n1154 | learning_rate: 0.0→0.05; method: median→tree; min_child_samples: 0→500; n_estimators: 0→80; num_leaves: 0→7; reg_lambda: 0.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1163 / 대기 | b18→c038 / n1161 | features: age→season; n_estimators: 80→300; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1164 / 대기 | b18→c038 / n1156 | bound: 0.2→0.3; features: core→age; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1165 / 대기 | b18→c038 / n1163 | bound: 0.5→0.3; features: season→core; half_life: 180→365 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1166 / 대기 | b18→c038 / n1159 | bound: 0.15→0.3; features: core→season; half_life: 없음→365; mode: multiplicative→additive; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1167 / 대기 | b18→c038 / n1157 | bound: 0.5→0.15; features: season→age; num_leaves: 3→7; reg_lambda: 2.0→10.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1168 / 대기 | b18→c038 / n1158 | features: age→core; half_life: 없음→180; min_child_samples: 500→200; n_estimators: 160→300; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1169 / 대기 | b18→c038 / n1163 | half_life: 180→없음; learning_rate: 0.05→0.025; n_estimators: 300→160; num_leaves: 3→15; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1170 / 대기 | b18→c038 / n1158 | bound: 0.1→0.2; learning_rate: 0.05→0.025; min_child_samples: 500→200; n_estimators: 160→300; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1171 / 대기 | b18→c038 / n1157 | features: season→core; half_life: 180→365; min_child_samples: 500→200; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1172 / 대기 | b18→c038 / n1157 | bound: 0.5→0.1; half_life: 180→365; mode: multiplicative→additive; n_estimators: 160→80; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1173 / 대기 | b18→c038 / n1165 | features: core→age; min_child_samples: 1000→500; num_leaves: 3→7; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1174 / 대기 | b18→c038 / n1168 | half_life: 180→365; min_child_samples: 200→1000 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1175 / 대기 | b18→c038 / n1157 | learning_rate: 0.05→0.025; reg_lambda: 2.0→10.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1176 / 대기 | b18→c038 / n1164 | half_life: 180→365; learning_rate: 0.025→0.05; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1177 / 대기 | b18→c038 / n1165 | bound: 0.3→0.15; min_child_samples: 1000→200; reg_lambda: 30.0→10.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1178 / 대기 | b18→c038 / n1164 | bound: 0.3→0.1; features: age→season; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1179 / 대기 | b18→c038 / n1170 | bound: 0.2→0.3; half_life: 없음→180; min_child_samples: 200→500; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1180 / 대기 | b18→c038 / n1164 | features: age→core; half_life: 180→365; min_child_samples: 1000→200 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1181 / 대기 | b18→c038 / n1159 | bound: 0.15→0.3; features: core→season; learning_rate: 0.025→0.05; n_estimators: 300→80; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1182 / 대기 | b18→c038 / n1158 | bound: 0.1→0.3; min_child_samples: 500→1000; num_leaves: 3→7; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1183 / 대기 | b18→c038 / n1171 | half_life: 365→없음; num_leaves: 3→15; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1184 / 대기 | b18→c038 / n1158 | bound: 0.1→0.2; features: age→season; n_estimators: 160→300; num_leaves: 3→15; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1185 / 대기 | b18→c038 / n1161 | min_child_samples: 1000→200; n_estimators: 80→300; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1186 / 대기 | b18→c038 / n1162 | bound: 0.2→0.3; reg_lambda: 10.0→10.5; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1187 / 대기 | b18→c038 / n1181 | bound: 0.3→0.5; num_leaves: 15→7; reg_lambda: 30.0→2.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1188 / 대기 | b18→c038 / n1158 | num_leaves: 3→7; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1189 / 대기 | b18→c038 / n1161 | bound: 0.5→0.15; features: age→core; half_life: 180→없음; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1190 / 대기 | b18→c038 / n1160 | bound: 0.2→0.3; num_leaves: 3→7; reg_lambda: 10.0→2.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1191 / 대기 | b18→c038 / n1179 | half_life: 180→없음; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1192 / 대기 | b18→c038 / n1162 | bound: 0.2→0.1; learning_rate: 0.05→0.025; n_estimators: 80→160; num_leaves: 7→15; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1193 / 대기 | b18→c038 / n1179 | bound: 0.3→0.15; features: age→season; min_child_samples: 500→200 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1194 / 대기 | b18→c038 / n1182 | min_child_samples: 1000→200; reg_lambda: 30.0→10.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1195 / 대기 | b18→c038 / n1193 | bound: 0.15→0.5; features: season→core; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1196 / 대기 | b18→c038 / n1164 | features: age→season; n_estimators: 300→160; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1197 / 대기 | b18→c038 / n1175 | features: season→age; half_life: 180→없음; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1198 / 대기 | b18→c038 / n1192 | half_life: 365→없음; min_child_samples: 500→200; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1199 / 대기 | b18→c038 / n1177 | features: core→season; min_child_samples: 200→500; num_leaves: 3→15; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1200 / 대기 | b18→c038 / n1179 | mode: multiplicative→additive; n_estimators: 300→80; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1201 / 대기 | b18→c038 / n1171 | half_life: 365→없음 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1202 / 대기 | b18→c038 / n1166 | min_child_samples: 200→1000; n_estimators: 300→160; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1203 / 대기 | b18→c038 / n1179 | learning_rate: 0.025→0.05; n_estimators: 300→160; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1204 / 대기 | b18→c038 / n1158 | bound: 0.1→0.3; features: age→core; half_life: 없음→365; min_child_samples: 500→200 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1205 / 대기 | b18→c038 / n1163 | reg_lambda: 30.0→10.0 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1206 / 대기 | b18→c038 / n1197 | bound: 0.5→0.1; mode: multiplicative→additive; n_estimators: 160→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1207 / 대기 | b18→c038 / n1159 | half_life: 없음→180; min_child_samples: 200→1000; n_estimators: 300→160; reg_lambda: 30.0→2.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1208 / 대기 | b18→c038 / n1178 | bound: 0.1→0.2; learning_rate: 0.025→0.05; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1209 / 대기 | b18→c038 / n1173 | half_life: 365→없음; min_child_samples: 500→1000; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1210 / 대기 | b18→c038 / n1162 | n_estimators: 80→160; num_leaves: 7→3; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1211 / 대기 | b18→c038 / n1181 | n_estimators: 80→160; reg_lambda: 30.0→10.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1212 / 대기 | b18→c038 / n1160 | features: season→age; learning_rate: 0.05→0.025; n_estimators: 160→80; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1213 / 대기 | b18→c038 / n1211 | features: season→core; half_life: 없음→180 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1214 / 대기 | b18→c038 / n1160 | reg_lambda: 10.0→2.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1215 / 대기 | b18→c038 / n1189 | features: core→age; min_child_samples: 1000→200; n_estimators: 80→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1216 / 대기 | b19→c226 / n1216 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1217 / 대기 | b19→c226 / n1216 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1218 / 대기 | b19→c226 / n1216 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1219 / 대기 | b19→c226 / n1217 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1220 / 대기 | b19→c226 / n1218 | bound: 0.2→0.3; learning_rate: 0.0→0.05; method: median→tree; min_child_samples: 0→200; n_estimators: 0→300; num_leaves: 0→15; reg_lambda: 0.0→30.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1221 / 대기 | b19→c226 / n1220 | features: core→season; half_life: 365→180; mode: additive→multiplicative; num_leaves: 15→3; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1222 / 대기 | b19→c226 / n1220 | features: core→age; min_child_samples: 200→1000; num_leaves: 15→7; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1223 / 대기 | b19→c226 / n1220 | bound: 0.3→0.15; half_life: 365→없음; mode: additive→multiplicative; n_estimators: 300→80; num_leaves: 15→7; reg_lambda: 30.0→10.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1224 / 대기 | b19→c226 / n1222 | features: age→season; half_life: 365→없음; min_child_samples: 1000→500; n_estimators: 300→160; reg_lambda: 30.0→2.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1225 / 대기 | b19→c226 / n1222 | learning_rate: 0.05→0.025; mode: additive→multiplicative; n_estimators: 300→80; num_leaves: 7→3; reg_lambda: 30.0→2.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1226 / 대기 | b19→c226 / n1224 | bound: 0.3→0.2; features: season→core; learning_rate: 0.05→0.025; num_leaves: 7→3; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1227 / 대기 | b19→c226 / n1224 | half_life: 없음→365; mode: additive→multiplicative; n_estimators: 160→300; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1228 / 대기 | b19→c226 / n1222 | bound: 0.3→0.2; half_life: 365→180; n_estimators: 300→80; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1229 / 대기 | b19→c226 / n1220 | bound: 0.3→0.15; min_child_samples: 200→500; mode: additive→multiplicative; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1230 / 대기 | b19→c226 / n1224 | half_life: 없음→365; min_child_samples: 500→200; reg_lambda: 2.0→10.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1231 / 대기 | b19→c226 / n1225 | bound: 0.3→0.5; learning_rate: 0.025→0.05; min_child_samples: 1000→500; n_estimators: 80→160; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1232 / 대기 | b19→c226 / n1222 | bound: 0.3→0.1; features: age→core; min_child_samples: 1000→500; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1233 / 대기 | b19→c226 / n1227 | half_life: 365→180; n_estimators: 300→160; num_leaves: 7→15; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1234 / 대기 | b19→c226 / n1225 | half_life: 365→180; mode: multiplicative→additive; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1235 / 대기 | b19→c226 / n1220 | bound: 0.3→0.5; half_life: 365→180; learning_rate: 0.05→0.025; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1236 / 대기 | b19→c226 / n1224 | bound: 0.3→0.1; min_child_samples: 500→1000; n_estimators: 160→80; num_leaves: 7→15; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1237 / 대기 | b19→c226 / n1227 | features: season→age (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1238 / 대기 | b19→c226 / n1232 | half_life: 365→없음; min_child_samples: 500→1000; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1239 / 대기 | b19→c226 / n1235 | features: core→season; min_child_samples: 200→1000; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1240 / 대기 | b19→c226 / n1228 | half_life: 180→없음; learning_rate: 0.05→0.025 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1241 / 대기 | b19→c226 / n1226 | bound: 0.2→0.5; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1242 / 대기 | b19→c226 / n1226 | features: core→season (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1243 / 대기 | b19→c226 / n1221 | bound: 0.3→0.15; features: season→age; half_life: 180→없음 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1244 / 대기 | b19→c226 / n1226 | half_life: 없음→365; learning_rate: 0.025→0.05; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1245 / 대기 | b19→c226 / n1223 | features: core→season; half_life: 없음→180; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1246 / 대기 | b19→c226 / n1240 | min_child_samples: 1000→500; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1247 / 대기 | b19→c226 / n1223 | bound: 0.15→0.5; reg_lambda: 10.0→2.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1248 / 대기 | b19→c226 / n1222 | features: age→season; min_child_samples: 1000→500; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1249 / 대기 | b19→c226 / n1231 | bound: 0.5→0.3; half_life: 365→없음; n_estimators: 160→80; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1250 / 대기 | b19→c226 / n1226 | half_life: 없음→180; n_estimators: 160→300; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1251 / 대기 | b19→c226 / n1233 | bound: 0.3→0.15; min_child_samples: 500→1000; num_leaves: 15→3; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1252 / 대기 | b19→c226 / n1222 | bound: 0.3→0.1; n_estimators: 300→160; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1253 / 대기 | b19→c226 / n1241 | half_life: 없음→365; n_estimators: 160→80; num_leaves: 3→7; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1254 / 대기 | b19→c226 / n1242 | half_life: 없음→180; num_leaves: 3→7; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1255 / 대기 | b19→c226 / n1243 | num_leaves: 3→7; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1256 / 대기 | b19→c226 / n1220 | bound: 0.3→0.1; half_life: 365→180; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1257 / 대기 | b19→c226 / n1251 | learning_rate: 0.05→0.025; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1258 / 대기 | b19→c226 / n1230 | bound: 0.3→0.2; features: season→age; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1259 / 대기 | b19→c226 / n1224 | features: season→core; min_child_samples: 500→1000; mode: additive→multiplicative; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1260 / 대기 | b19→c226 / n1236 | half_life: 없음→365; learning_rate: 0.05→0.025; min_child_samples: 1000→500; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1261 / 대기 | b19→c226 / n1225 | bound: 0.3→0.15; learning_rate: 0.025→0.05; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1262 / 대기 | b19→c226 / n1238 | learning_rate: 0.05→0.025; min_child_samples: 1000→500; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1263 / 대기 | b19→c226 / n1239 | half_life: 180→365; num_leaves: 15→3; reg_lambda: 10.0→30.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1264 / 대기 | b19→c226 / n1252 | half_life: 365→180; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1265 / 대기 | b19→c226 / n1229 | learning_rate: 0.05→0.025; min_child_samples: 500→1000; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1266 / 대기 | b19→c226 / n1230 | bound: 0.3→0.1; half_life: 365→없음; learning_rate: 0.05→0.025; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1267 / 대기 | b19→c226 / n1243 | n_estimators: 300→80; reg_lambda: 30.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1268 / 대기 | b19→c226 / n1266 | features: season→core; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1269 / 대기 | b19→c226 / n1261 | features: age→season; num_leaves: 3→15; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1270 / 대기 | b19→c226 / n1222 | bound: 0.3→0.2; min_child_samples: 1000→500; n_estimators: 300→80; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1271 / 대기 | b19→c226 / n1247 | num_leaves: 7→15; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1272 / 대기 | b19→c226 / n1254 | bound: 0.2→0.1; reg_lambda: 10.0→30.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1273 / 대기 | b19→c226 / n1225 | bound: 0.3→0.5; half_life: 365→180; num_leaves: 3→7; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1274 / 대기 | b19→c226 / n1266 | features: season→core; half_life: 없음→365; n_estimators: 160→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1275 / 대기 | b19→c226 / n1225 | features: age→season; num_leaves: 3→7; reg_lambda: 2.0→30.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1276 / 대기 | b19→c226 / n1222 | half_life: 365→180; min_child_samples: 1000→500; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1277 / 대기 | b19→c226 / n1227 | features: season→core; num_leaves: 7→3; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1278 / 대기 | b19→c226 / n1262 | features: core→season; half_life: 없음→180; min_child_samples: 500→200; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1279 / 대기 | b19→c226 / n1235 | features: core→age; min_child_samples: 200→500; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1280 / 대기 | b20→c014 / n1280 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1281 / 대기 | b20→c014 / n1280 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1282 / 대기 | b20→c014 / n1280 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1283 / 대기 | b20→c014 / n1281 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1284 / 대기 | b20→c014 / n1282 | learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→200; n_estimators: 0→300; num_leaves: 0→7; reg_lambda: 0.0→2.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1285 / 대기 | b20→c014 / n1281 | bound: 0.3→0.5; features: core→season; learning_rate: 0.0→0.05; method: median→tree; min_child_samples: 0→500; n_estimators: 0→80; num_leaves: 0→3; reg_lambda: 0.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1286 / 대기 | b20→c014 / n1284 | bound: 0.2→0.1; features: core→age; half_life: 365→180; min_child_samples: 200→500; n_estimators: 300→80; num_leaves: 7→3; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1287 / 대기 | b20→c014 / n1285 | bound: 0.5→0.3; features: season→core; half_life: 없음→180; n_estimators: 80→160; num_leaves: 3→15; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1288 / 대기 | b20→c014 / n1284 | features: core→season; half_life: 365→없음; min_child_samples: 200→1000; n_estimators: 300→160; num_leaves: 7→3; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1289 / 대기 | b20→c014 / n1287 | features: core→age; half_life: 180→없음; num_leaves: 15→3; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1290 / 대기 | b20→c014 / n1284 | bound: 0.2→0.1; learning_rate: 0.025→0.05; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1291 / 대기 | b20→c014 / n1285 | bound: 0.5→0.3; half_life: 없음→180; min_child_samples: 500→200; num_leaves: 3→7; reg_lambda: 2.0→10.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1292 / 대기 | b20→c014 / n1284 | features: core→age; n_estimators: 300→160; num_leaves: 7→3; reg_lambda: 2.0→30.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1293 / 대기 | b20→c014 / n1287 | bound: 0.3→0.5; half_life: 180→365; min_child_samples: 500→200; n_estimators: 160→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1294 / 대기 | b20→c014 / n1290 | bound: 0.1→0.2; features: core→season; half_life: 365→없음; num_leaves: 7→15; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1295 / 대기 | b20→c014 / n1284 | bound: 0.2→0.5; features: core→age; mode: additive→multiplicative; reg_lambda: 2.0→30.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1296 / 대기 | b20→c014 / n1287 | bound: 0.3→0.1; min_child_samples: 500→1000; mode: multiplicative→additive; num_leaves: 15→7; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1297 / 대기 | b20→c014 / n1285 | bound: 0.5→0.15; learning_rate: 0.05→0.025; n_estimators: 80→300; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1298 / 대기 | b20→c014 / n1286 | min_child_samples: 500→200; n_estimators: 80→300; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1299 / 대기 | b20→c014 / n1285 | bound: 0.5→0.3; features: season→core; half_life: 없음→365; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1300 / 대기 | b20→c014 / n1288 | bound: 0.2→0.3; min_child_samples: 1000→500; n_estimators: 160→300; num_leaves: 3→7; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1301 / 대기 | b20→c014 / n1287 | features: core→age; learning_rate: 0.05→0.025; min_child_samples: 500→1000; n_estimators: 160→300; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1302 / 대기 | b20→c014 / n1292 | features: age→core; half_life: 365→180; learning_rate: 0.025→0.05; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1303 / 대기 | b20→c014 / n1285 | bound: 0.5→0.3; min_child_samples: 500→1000; n_estimators: 80→160; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1304 / 대기 | b20→c014 / n1294 | features: season→age; num_leaves: 15→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1305 / 대기 | b20→c014 / n1284 | bound: 0.2→0.15; min_child_samples: 200→1000; mode: additive→multiplicative; num_leaves: 7→3; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1306 / 대기 | b20→c014 / n1290 | features: core→season; num_leaves: 7→15; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1307 / 대기 | b20→c014 / n1287 | features: core→age; learning_rate: 0.05→0.025; num_leaves: 15→3; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1308 / 대기 | b20→c014 / n1284 | min_child_samples: 200→500; n_estimators: 300→80; num_leaves: 7→15; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1309 / 대기 | b20→c014 / n1305 | bound: 0.15→0.5; features: core→season; half_life: 365→없음; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1310 / 대기 | b20→c014 / n1290 | features: core→age; num_leaves: 7→3; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1311 / 대기 | b20→c014 / n1293 | bound: 0.5→0.15; n_estimators: 80→160; reg_lambda: 2.0→30.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1312 / 대기 | b20→c014 / n1288 | bound: 0.2→0.1; half_life: 없음→365; num_leaves: 3→15; reg_lambda: 2.0→10.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1313 / 대기 | b20→c014 / n1285 | features: season→age; n_estimators: 80→300; num_leaves: 3→7; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1314 / 대기 | b20→c014 / n1296 | half_life: 180→365; learning_rate: 0.05→0.025; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1315 / 대기 | b20→c014 / n1291 | half_life: 180→없음; min_child_samples: 200→1000; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1316 / 대기 | b20→c014 / n1284 | features: core→age; reg_lambda: 2.0→30.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1317 / 대기 | b20→c014 / n1305 | learning_rate: 0.025→0.05; num_leaves: 3→7; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1318 / 대기 | b20→c014 / n1300 | half_life: 없음→365; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1319 / 대기 | b20→c014 / n1313 | n_estimators: 300→80; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1320 / 대기 | b20→c014 / n1300 | bound: 0.3→0.1; features: season→core; learning_rate: 0.025→0.05; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1321 / 대기 | b20→c014 / n1297 | half_life: 없음→365; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1322 / 대기 | b20→c014 / n1289 | bound: 0.3→0.1; mode: multiplicative→additive; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1323 / 대기 | b20→c014 / n1305 | bound: 0.15→0.5; learning_rate: 0.025→0.05; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1324 / 대기 | b20→c014 / n1288 | bound: 0.2→0.1; half_life: 없음→180; min_child_samples: 1000→200; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1325 / 대기 | b20→c014 / n1307 | half_life: 180→365; min_child_samples: 500→1000; n_estimators: 160→80; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1326 / 대기 | b20→c014 / n1308 | bound: 0.2→0.3; half_life: 365→없음; n_estimators: 80→160; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1327 / 대기 | b20→c014 / n1287 | features: core→season; half_life: 180→없음; min_child_samples: 500→200; n_estimators: 160→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1328 / 대기 | b20→c014 / n1322 | learning_rate: 0.05→0.025; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1329 / 대기 | b20→c014 / n1311 | bound: 0.15→0.3; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1330 / 대기 | b20→c014 / n1292 | bound: 0.2→0.3; features: age→season; n_estimators: 160→300; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1331 / 대기 | b20→c014 / n1295 | bound: 0.5→0.3; n_estimators: 300→80; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1332 / 대기 | b20→c014 / n1284 | bound: 0.2→0.1; num_leaves: 7→3; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1333 / 대기 | b20→c014 / n1285 | bound: 0.5→0.15; half_life: 없음→365; min_child_samples: 500→200; n_estimators: 80→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1334 / 대기 | b20→c014 / n1298 | half_life: 180→365; learning_rate: 0.025→0.05; min_child_samples: 200→500 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1335 / 대기 | b20→c014 / n1323 | half_life: 365→없음; min_child_samples: 1000→500; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1336 / 대기 | b20→c014 / n1288 | min_child_samples: 1000→500; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1337 / 대기 | b20→c014 / n1289 | bound: 0.3→0.5; min_child_samples: 500→200; num_leaves: 3→7; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1338 / 대기 | b20→c014 / n1308 | half_life: 365→180; num_leaves: 15→7; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1339 / 대기 | b20→c014 / n1285 | bound: 0.5→0.3; n_estimators: 80→300; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1340 / 대기 | b20→c014 / n1319 | bound: 0.5→0.1; half_life: 없음→180; mode: multiplicative→additive (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1341 / 대기 | b20→c014 / n1301 | bound: 0.3→0.5; features: age→core; half_life: 180→365 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1342 / 대기 | b20→c014 / n1336 | learning_rate: 0.025→0.05; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1343 / 대기 | b20→c014 / n1337 | min_child_samples: 200→1000; n_estimators: 160→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1344 / 대기 | b21→c232 / n1344 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1345 / 대기 | b21→c232 / n1344 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1346 / 대기 | b21→c232 / n1344 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1347 / 대기 | b21→c232 / n1345 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1348 / 대기 | b21→c232 / n1344 | bound: 0.2→0.3; learning_rate: 0.0→0.05; method: median→tree; min_child_samples: 0→1000; n_estimators: 0→300; num_leaves: 0→7; reg_lambda: 0.0→30.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1349 / 대기 | b21→c232 / n1348 | bound: 0.3→0.15; features: core→season; min_child_samples: 1000→200; mode: additive→multiplicative; num_leaves: 7→15; reg_lambda: 30.0→2.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1350 / 대기 | b21→c232 / n1348 | bound: 0.3→0.2; features: core→age; min_child_samples: 1000→200; num_leaves: 7→3; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1351 / 대기 | b21→c232 / n1348 | half_life: 없음→180; min_child_samples: 1000→500; mode: additive→multiplicative; n_estimators: 300→160; num_leaves: 7→15; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1352 / 대기 | b21→c232 / n1349 | bound: 0.15→0.2; min_child_samples: 200→1000; mode: multiplicative→additive; num_leaves: 15→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1353 / 대기 | b21→c232 / n1351 | features: core→age; learning_rate: 0.05→0.025; n_estimators: 160→80; num_leaves: 15→3; reg_lambda: 10.0→30.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1354 / 대기 | b21→c232 / n1349 | bound: 0.15→0.1; features: season→core; learning_rate: 0.05→0.025; mode: multiplicative→additive; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1355 / 대기 | b21→c232 / n1349 | min_child_samples: 200→500; num_leaves: 15→7; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1356 / 대기 | b21→c232 / n1353 | bound: 0.3→0.2; half_life: 180→365; mode: multiplicative→additive; reg_lambda: 30.0→10.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1357 / 대기 | b21→c232 / n1353 | features: age→core; half_life: 180→365; n_estimators: 80→160; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1358 / 대기 | b21→c232 / n1348 | features: core→season; half_life: 없음→180; min_child_samples: 1000→200; num_leaves: 7→3; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1359 / 대기 | b21→c232 / n1353 | bound: 0.3→0.5; min_child_samples: 500→1000; num_leaves: 3→7; reg_lambda: 30.0→2.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1360 / 대기 | b21→c232 / n1348 | bound: 0.3→0.2; n_estimators: 300→80; num_leaves: 7→15; reg_lambda: 30.0→10.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1361 / 대기 | b21→c232 / n1355 | half_life: 없음→365; reg_lambda: 2.0→10.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1362 / 대기 | b21→c232 / n1350 | bound: 0.2→0.1; reg_lambda: 30.0→2.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1363 / 대기 | b21→c232 / n1357 | min_child_samples: 500→1000; num_leaves: 3→15; reg_lambda: 2.0→30.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1364 / 대기 | b21→c232 / n1348 | bound: 0.3→0.1; features: core→season; learning_rate: 0.05→0.025; n_estimators: 300→80; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1365 / 대기 | b21→c232 / n1359 | min_child_samples: 1000→200; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1366 / 대기 | b21→c232 / n1354 | half_life: 없음→180; min_child_samples: 200→1000; n_estimators: 300→80; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1367 / 대기 | b21→c232 / n1349 | num_leaves: 15→3; reg_lambda: 2.0→10.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1368 / 대기 | b21→c232 / n1362 | half_life: 없음→180; num_leaves: 3→7; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1369 / 대기 | b21→c232 / n1357 | bound: 0.3→0.15; min_child_samples: 500→1000; n_estimators: 160→80; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1370 / 대기 | b21→c232 / n1348 | features: core→season; half_life: 없음→365; n_estimators: 300→80; num_leaves: 7→3; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1371 / 대기 | b21→c232 / n1348 | features: core→age; mode: additive→multiplicative; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1372 / 대기 | b21→c232 / n1360 | learning_rate: 0.05→0.025; n_estimators: 80→160; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1373 / 대기 | b21→c232 / n1355 | bound: 0.15→0.3; n_estimators: 300→80; num_leaves: 7→15; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1374 / 대기 | b21→c232 / n1356 | half_life: 365→180; n_estimators: 80→300; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1375 / 대기 | b21→c232 / n1351 | bound: 0.3→0.5; n_estimators: 160→80; num_leaves: 15→7; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1376 / 대기 | b21→c232 / n1360 | bound: 0.2→0.1; features: core→season; min_child_samples: 1000→200; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1377 / 대기 | b21→c232 / n1353 | min_child_samples: 500→200 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1378 / 대기 | b21→c232 / n1356 | features: age→core; half_life: 365→없음; num_leaves: 3→7; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1379 / 대기 | b21→c232 / n1358 | mode: additive→multiplicative; n_estimators: 300→80; num_leaves: 3→7; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1380 / 대기 | b21→c232 / n1368 | learning_rate: 0.05→0.025; min_child_samples: 200→500; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1381 / 대기 | b21→c232 / n1367 | features: season→core; min_child_samples: 200→1000; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1382 / 대기 | b21→c232 / n1358 | half_life: 180→없음; n_estimators: 300→160; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1383 / 대기 | b21→c232 / n1371 | bound: 0.3→0.5; reg_lambda: 30.0→10.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1384 / 대기 | b21→c232 / n1358 | features: season→core; half_life: 180→365; learning_rate: 0.05→0.025 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1385 / 대기 | b21→c232 / n1349 | bound: 0.15→0.5; half_life: 없음→365; learning_rate: 0.05→0.025; n_estimators: 300→160; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1386 / 대기 | b21→c232 / n1357 | bound: 0.3→0.1; features: core→age; learning_rate: 0.025→0.05; mode: multiplicative→additive (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1387 / 대기 | b21→c232 / n1378 | bound: 0.2→0.5; mode: additive→multiplicative; n_estimators: 80→160; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1388 / 대기 | b21→c232 / n1354 | features: core→season; min_child_samples: 200→1000; n_estimators: 300→160; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1389 / 대기 | b21→c232 / n1353 | half_life: 180→365; num_leaves: 3→7; reg_lambda: 30.0→10.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1390 / 대기 | b21→c232 / n1372 | half_life: 없음→180; min_child_samples: 1000→200; num_leaves: 15→7; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1391 / 대기 | b21→c232 / n1355 | learning_rate: 0.05→0.025; min_child_samples: 500→1000 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1392 / 대기 | b21→c232 / n1362 | bound: 0.1→0.3; n_estimators: 300→160; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1393 / 대기 | b21→c232 / n1381 | half_life: 없음→180; n_estimators: 300→160; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1394 / 대기 | b21→c232 / n1370 | half_life: 365→180; learning_rate: 0.05→0.025; n_estimators: 80→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1395 / 대기 | b21→c232 / n1353 | half_life: 180→없음; n_estimators: 80→160; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1396 / 대기 | b21→c232 / n1348 | bound: 0.3→0.1; half_life: 없음→180; reg_lambda: 30.0→10.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1397 / 대기 | b21→c232 / n1361 | bound: 0.15→0.5; n_estimators: 300→160; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1398 / 대기 | b21→c232 / n1380 | half_life: 180→365; learning_rate: 0.025→0.05; reg_lambda: 2.0→30.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1399 / 대기 | b21→c232 / n1363 | bound: 0.3→0.15; min_child_samples: 1000→200; n_estimators: 160→300; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1400 / 대기 | b21→c232 / n1378 | features: core→season; num_leaves: 7→3; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1401 / 대기 | b21→c232 / n1359 | bound: 0.5→0.3; half_life: 180→없음; learning_rate: 0.025→0.05 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1402 / 대기 | b21→c232 / n1356 | features: age→core (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1403 / 대기 | b21→c232 / n1401 | features: age→season; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1404 / 대기 | b21→c232 / n1350 | half_life: 없음→365; min_child_samples: 200→1000; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1405 / 대기 | b21→c232 / n1365 | features: age→core; half_life: 180→없음; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1406 / 대기 | b21→c232 / n1348 | features: core→season; half_life: 없음→180; num_leaves: 7→15; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1407 / 대기 | b21→c232 / n1359 | learning_rate: 0.025→0.05; min_child_samples: 1000→200; num_leaves: 7→3; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1408 / 대기 | b22→c136 / n1408 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1409 / 대기 | b22→c136 / n1408 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1410 / 대기 | b22→c136 / n1408 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1411 / 대기 | b22→c136 / n1409 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1412 / 대기 | b22→c136 / n1408 | half_life: 없음→180; learning_rate: 0.0→0.05; method: median→tree; min_child_samples: 0→500; n_estimators: 0→80; num_leaves: 0→7; reg_lambda: 0.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1413 / 대기 | b22→c136 / n1412 | bound: 0.2→0.15; features: core→season; learning_rate: 0.05→0.025; mode: additive→multiplicative; n_estimators: 80→300; num_leaves: 7→15; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1414 / 대기 | b22→c136 / n1412 | bound: 0.2→0.3; features: core→age; half_life: 180→365; min_child_samples: 500→200; n_estimators: 80→160; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1415 / 대기 | b22→c136 / n1413 | bound: 0.15→0.5; features: season→core; half_life: 180→없음; min_child_samples: 500→200; n_estimators: 300→160; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1416 / 대기 | b22→c136 / n1412 | bound: 0.2→0.3; features: core→season; min_child_samples: 500→1000; num_leaves: 7→15; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1417 / 대기 | b22→c136 / n1414 | bound: 0.3→0.15; min_child_samples: 200→1000; mode: additive→multiplicative; n_estimators: 160→80; reg_lambda: 2.0→30.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1418 / 대기 | b22→c136 / n1412 | half_life: 180→365; min_child_samples: 500→200; reg_lambda: 2.0→30.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1419 / 대기 | b22→c136 / n1413 | bound: 0.15→0.3; min_child_samples: 500→200; n_estimators: 300→160; reg_lambda: 10.0→30.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1420 / 대기 | b22→c136 / n1414 | half_life: 365→없음; reg_lambda: 2.0→30.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1421 / 대기 | b22→c136 / n1415 | n_estimators: 160→80; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1422 / 대기 | b22→c136 / n1418 | bound: 0.2→0.1; features: core→season; half_life: 365→180; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1423 / 대기 | b22→c136 / n1417 | min_child_samples: 1000→200; reg_lambda: 30.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1424 / 대기 | b22→c136 / n1412 | learning_rate: 0.05→0.025; min_child_samples: 500→200; n_estimators: 80→160; num_leaves: 7→3; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1425 / 대기 | b22→c136 / n1421 | features: core→season; min_child_samples: 200→500; num_leaves: 7→3; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1426 / 대기 | b22→c136 / n1414 | bound: 0.3→0.1; min_child_samples: 200→1000; num_leaves: 3→7; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1427 / 대기 | b22→c136 / n1415 | bound: 0.5→0.3; half_life: 없음→180; min_child_samples: 200→1000; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1428 / 대기 | b22→c136 / n1422 | half_life: 180→없음; learning_rate: 0.05→0.025; reg_lambda: 30.0→10.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1429 / 대기 | b22→c136 / n1414 | half_life: 365→180; learning_rate: 0.05→0.025; min_child_samples: 200→500; mode: additive→multiplicative; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1430 / 대기 | b22→c136 / n1418 | bound: 0.2→0.3; min_child_samples: 200→1000; n_estimators: 80→300; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1431 / 대기 | b22→c136 / n1416 | mode: additive→multiplicative; reg_lambda: 2.0→10.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1432 / 대기 | b22→c136 / n1414 | half_life: 365→없음; n_estimators: 160→80; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1433 / 대기 | b22→c136 / n1413 | features: season→core; half_life: 180→없음; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1434 / 대기 | b22→c136 / n1419 | mode: multiplicative→additive; reg_lambda: 30.0→10.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1435 / 대기 | b22→c136 / n1414 | min_child_samples: 200→1000; mode: additive→multiplicative; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1436 / 대기 | b22→c136 / n1412 | bound: 0.2→0.1; half_life: 180→없음; reg_lambda: 2.0→10.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1437 / 대기 | b22→c136 / n1413 | min_child_samples: 500→1000; n_estimators: 300→160; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1438 / 대기 | b22→c136 / n1414 | bound: 0.3→0.2; learning_rate: 0.05→0.025; min_child_samples: 200→500; reg_lambda: 2.0→10.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1439 / 대기 | b22→c136 / n1414 | features: age→core; mode: additive→multiplicative; num_leaves: 3→7; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1440 / 대기 | b22→c136 / n1421 | bound: 0.5→0.2; features: core→season; mode: multiplicative→additive; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1441 / 대기 | b22→c136 / n1417 | bound: 0.15→0.3; min_child_samples: 1000→500; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1442 / 대기 | b22→c136 / n1430 | num_leaves: 7→15; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1443 / 대기 | b22→c136 / n1419 | bound: 0.3→0.15; half_life: 180→365; num_leaves: 15→3; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1444 / 대기 | b22→c136 / n1438 | bound: 0.2→0.3; min_child_samples: 500→1000; n_estimators: 160→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1445 / 대기 | b22→c136 / n1427 | n_estimators: 160→80; num_leaves: 7→3; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1446 / 대기 | b22→c136 / n1424 | features: core→season; min_child_samples: 200→1000; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1447 / 대기 | b22→c136 / n1437 | features: season→age; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1448 / 대기 | b22→c136 / n1418 | min_child_samples: 200→500; n_estimators: 80→160; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1449 / 대기 | b22→c136 / n1417 | features: age→season; half_life: 365→180; n_estimators: 80→160; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1450 / 대기 | b22→c136 / n1414 | bound: 0.3→0.2; n_estimators: 160→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1451 / 대기 | b22→c136 / n1439 | bound: 0.3→0.15; min_child_samples: 200→500; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1452 / 대기 | b22→c136 / n1413 | bound: 0.15→0.1; mode: multiplicative→additive; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1453 / 대기 | b22→c136 / n1443 | features: season→age; half_life: 365→없음; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1454 / 대기 | b22→c136 / n1418 | min_child_samples: 200→1000; num_leaves: 7→15; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1455 / 대기 | b22→c136 / n1421 | features: core→season; learning_rate: 0.025→0.05; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1456 / 대기 | b22→c136 / n1444 | n_estimators: 300→160 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1457 / 대기 | b22→c136 / n1433 | bound: 0.15→0.3; min_child_samples: 500→200 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1458 / 대기 | b22→c136 / n1452 | half_life: 180→365; min_child_samples: 500→200 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1459 / 대기 | b22→c136 / n1427 | bound: 0.3→0.5; features: core→age; min_child_samples: 1000→500 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1460 / 대기 | b22→c136 / n1427 | bound: 0.3→0.1; mode: multiplicative→additive; reg_lambda: 10.0→30.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1461 / 대기 | b22→c136 / n1433 | features: core→season; min_child_samples: 500→1000; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1462 / 대기 | b22→c136 / n1414 | reg_lambda: 2.0→2.5; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1463 / 대기 | b22→c136 / n1435 | bound: 0.3→0.5; features: age→core; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1464 / 대기 | b22→c136 / n1431 | half_life: 180→365; min_child_samples: 1000→200; mode: multiplicative→additive (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1465 / 대기 | b22→c136 / n1421 | features: core→age; min_child_samples: 200→1000; n_estimators: 80→300; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1466 / 대기 | b22→c136 / n1424 | bound: 0.2→0.3; n_estimators: 160→300; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1467 / 대기 | b22→c136 / n1413 | learning_rate: 0.025→0.05; min_child_samples: 500→1000; reg_lambda: 10.0→2.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1468 / 대기 | b22→c136 / n1441 | learning_rate: 0.05→0.025; mode: multiplicative→additive; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1469 / 대기 | b22→c136 / n1417 | features: age→core; learning_rate: 0.05→0.025; reg_lambda: 30.0→10.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1470 / 대기 | b22→c136 / n1436 | features: core→season; half_life: 없음→365; min_child_samples: 500→1000 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1471 / 대기 | b22→c136 / n1459 | min_child_samples: 500→200; n_estimators: 160→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1472 / 대기 | b23→c098 / n1472 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1473 / 대기 | b23→c098 / n1472 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1474 / 대기 | b23→c098 / n1472 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1475 / 대기 | b23→c098 / n1473 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1476 / 대기 | b23→c098 / n1472 | bound: 0.2→0.1; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→500; n_estimators: 0→80; num_leaves: 0→3; reg_lambda: 0.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1477 / 대기 | b23→c098 / n1476 | bound: 0.1→0.15; features: core→season; half_life: 없음→180; learning_rate: 0.025→0.05; min_child_samples: 500→200; mode: additive→multiplicative; num_leaves: 3→7; reg_lambda: 10.0→30.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1478 / 대기 | b23→c098 / n1476 | bound: 0.1→0.3; features: core→age; half_life: 없음→365; min_child_samples: 500→1000; num_leaves: 3→7; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1479 / 대기 | b23→c098 / n1475 | bound: 0.3→0.5; learning_rate: 0.0→0.05; method: median→tree; min_child_samples: 0→1000; n_estimators: 0→160; num_leaves: 0→3; reg_lambda: 0.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1480 / 대기 | b23→c098 / n1478 | features: age→season; min_child_samples: 1000→500; n_estimators: 80→300; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1481 / 대기 | b23→c098 / n1479 | bound: 0.5→0.15; features: core→age; n_estimators: 160→300; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1482 / 대기 | b23→c098 / n1478 | features: age→core; half_life: 365→180; min_child_samples: 1000→500; n_estimators: 80→160; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1483 / 대기 | b23→c098 / n1477 | bound: 0.15→0.5; half_life: 180→365; learning_rate: 0.05→0.025 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1484 / 대기 | b23→c098 / n1476 | features: core→age; half_life: 없음→365; n_estimators: 80→160; reg_lambda: 10.0→2.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1485 / 대기 | b23→c098 / n1476 | bound: 0.1→0.5; min_child_samples: 500→200; mode: additive→multiplicative; n_estimators: 80→160; num_leaves: 3→15; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1486 / 대기 | b23→c098 / n1480 | bound: 0.3→0.1; learning_rate: 0.025→0.05; min_child_samples: 500→200; reg_lambda: 30.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1487 / 대기 | b23→c098 / n1478 | bound: 0.3→0.5; half_life: 365→없음; learning_rate: 0.025→0.05; mode: additive→multiplicative; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1488 / 대기 | b23→c098 / n1476 | half_life: 없음→365; n_estimators: 80→300; reg_lambda: 10.0→30.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1489 / 대기 | b23→c098 / n1486 | bound: 0.1→0.15; half_life: 365→없음; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1490 / 대기 | b23→c098 / n1476 | features: core→age; n_estimators: 80→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1491 / 대기 | b23→c098 / n1477 | features: season→core; learning_rate: 0.05→0.025; n_estimators: 80→300; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1492 / 대기 | b23→c098 / n1480 | bound: 0.3→0.2; n_estimators: 300→160; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1493 / 대기 | b23→c098 / n1479 | features: core→age; min_child_samples: 1000→200; reg_lambda: 2.0→30.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1494 / 대기 | b23→c098 / n1476 | num_leaves: 3→7 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1495 / 대기 | b23→c098 / n1490 | bound: 0.1→0.3; features: age→season; mode: additive→multiplicative; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1496 / 대기 | b23→c098 / n1478 | bound: 0.3→0.1; n_estimators: 80→160; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1497 / 대기 | b23→c098 / n1479 | bound: 0.5→0.3; learning_rate: 0.05→0.025; min_child_samples: 1000→200; n_estimators: 160→300; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1498 / 대기 | b23→c098 / n1477 | bound: 0.15→0.1; mode: multiplicative→additive; n_estimators: 80→300; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1499 / 대기 | b23→c098 / n1484 | bound: 0.1→0.3; half_life: 365→180; min_child_samples: 500→200; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1500 / 대기 | b23→c098 / n1482 | bound: 0.3→0.2; min_child_samples: 500→200; reg_lambda: 30.0→10.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1501 / 대기 | b23→c098 / n1477 | bound: 0.15→0.5; half_life: 180→없음; n_estimators: 80→300; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1502 / 대기 | b23→c098 / n1498 | bound: 0.1→0.2; features: season→age; half_life: 180→없음; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1503 / 대기 | b23→c098 / n1483 | features: season→core; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1504 / 대기 | b23→c098 / n1486 | half_life: 365→없음; n_estimators: 300→80; num_leaves: 15→7; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1505 / 대기 | b23→c098 / n1487 | learning_rate: 0.05→0.025; min_child_samples: 1000→500; reg_lambda: 10.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1506 / 대기 | b23→c098 / n1476 | bound: 0.1→0.2; n_estimators: 80→300; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1507 / 대기 | b23→c098 / n1499 | features: age→season; reg_lambda: 2.0→30.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1508 / 대기 | b23→c098 / n1478 | bound: 0.3→0.2; min_child_samples: 1000→500; reg_lambda: 30.0→10.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1509 / 대기 | b23→c098 / n1497 | learning_rate: 0.025→0.05; min_child_samples: 200→500; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1510 / 대기 | b23→c098 / n1494 | bound: 0.1→0.3; features: core→season; min_child_samples: 500→200; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1511 / 대기 | b23→c098 / n1481 | bound: 0.15→0.5; reg_lambda: 30.0→10.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1512 / 대기 | b23→c098 / n1504 | bound: 0.1→0.3; features: season→core; half_life: 없음→180; min_child_samples: 200→1000 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1513 / 대기 | b23→c098 / n1477 | half_life: 180→없음; min_child_samples: 200→500; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1514 / 대기 | b23→c098 / n1512 | bound: 0.3→0.2; features: core→age; learning_rate: 0.05→0.025 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1515 / 대기 | b23→c098 / n1482 | learning_rate: 0.025→0.05; mode: additive→multiplicative; num_leaves: 7→3; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1516 / 대기 | b23→c098 / n1504 | half_life: 없음→180; min_child_samples: 200→500; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1517 / 대기 | b23→c098 / n1499 | min_child_samples: 200→1000; num_leaves: 3→7; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1518 / 대기 | b23→c098 / n1480 | features: season→core; n_estimators: 300→80; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1519 / 대기 | b23→c098 / n1480 | bound: 0.3→0.5; mode: additive→multiplicative; n_estimators: 300→160; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1520 / 대기 | b23→c098 / n1484 | min_child_samples: 500→1000; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1521 / 대기 | b23→c098 / n1497 | learning_rate: 0.025→0.05; num_leaves: 15→7; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1522 / 대기 | b23→c098 / n1490 | bound: 0.1→0.2; features: age→season; half_life: 없음→180 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1523 / 대기 | b23→c098 / n1517 | bound: 0.3→0.5; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1524 / 대기 | b23→c098 / n1480 | features: season→core; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1525 / 대기 | b23→c098 / n1483 | bound: 0.5→0.15; min_child_samples: 200→1000; reg_lambda: 30.0→10.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1526 / 대기 | b23→c098 / n1484 | bound: 0.1→0.3; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1527 / 대기 | b23→c098 / n1485 | n_estimators: 160→300; num_leaves: 15→7; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1528 / 대기 | b23→c098 / n1495 | min_child_samples: 500→200; mode: multiplicative→additive; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1529 / 대기 | b23→c098 / n1517 | learning_rate: 0.025→0.05; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1530 / 대기 | b23→c098 / n1494 | reg_lambda: 10.0→30.0 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1531 / 대기 | b23→c098 / n1489 | half_life: 없음→365; min_child_samples: 200→500; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1532 / 대기 | b23→c098 / n1514 | bound: 0.2→0.3; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1533 / 대기 | b23→c098 / n1479 | half_life: 365→180; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1534 / 대기 | b23→c098 / n1486 | min_child_samples: 200→500; n_estimators: 300→80; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1535 / 대기 | b23→c098 / n1493 | bound: 0.5→0.3; half_life: 365→없음; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1536 / 대기 | b24→c223 / n1536 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1537 / 대기 | b24→c223 / n1536 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1538 / 대기 | b24→c223 / n1536 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1539 / 대기 | b24→c223 / n1537 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1540 / 대기 | b24→c223 / n1536 | half_life: 없음→180; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→1000; n_estimators: 0→80; num_leaves: 0→15; reg_lambda: 0.0→30.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1541 / 대기 | b24→c223 / n1540 | bound: 0.2→0.5; features: core→season; learning_rate: 0.025→0.05; min_child_samples: 1000→500; mode: additive→multiplicative; n_estimators: 80→160; reg_lambda: 30.0→10.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1542 / 대기 | b24→c223 / n1540 | bound: 0.2→0.1; features: core→age; learning_rate: 0.025→0.05; n_estimators: 80→160; num_leaves: 15→7; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1543 / 대기 | b24→c223 / n1540 | bound: 0.2→0.3; min_child_samples: 1000→500; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1544 / 대기 | b24→c223 / n1542 | features: age→season; min_child_samples: 1000→500; n_estimators: 160→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1545 / 대기 | b24→c223 / n1543 | features: core→age; half_life: 180→365; min_child_samples: 500→200; num_leaves: 15→3; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1546 / 대기 | b24→c223 / n1544 | bound: 0.1→0.3; features: season→core; half_life: 180→없음; reg_lambda: 30.0→10.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1547 / 대기 | b24→c223 / n1541 | bound: 0.5→0.15; half_life: 180→365; min_child_samples: 500→1000; num_leaves: 15→3; reg_lambda: 10.0→30.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1548 / 대기 | b24→c223 / n1542 | bound: 0.1→0.2; half_life: 180→365; min_child_samples: 1000→500; n_estimators: 160→300; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1549 / 대기 | b24→c223 / n1546 | half_life: 없음→365; mode: additive→multiplicative; reg_lambda: 10.0→2.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1550 / 대기 | b24→c223 / n1544 | bound: 0.1→0.3; n_estimators: 80→300; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1551 / 대기 | b24→c223 / n1545 | bound: 0.3→0.5; half_life: 365→180; reg_lambda: 30.0→10.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1552 / 대기 | b24→c223 / n1546 | half_life: 없음→180; learning_rate: 0.05→0.025; n_estimators: 80→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1553 / 대기 | b24→c223 / n1546 | features: core→season; mode: additive→multiplicative; n_estimators: 80→160; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1554 / 대기 | b24→c223 / n1548 | half_life: 365→없음; learning_rate: 0.05→0.025; n_estimators: 300→160; num_leaves: 7→3; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1555 / 대기 | b24→c223 / n1551 | bound: 0.5→0.15; features: age→core; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1556 / 대기 | b24→c223 / n1547 | bound: 0.15→0.2; min_child_samples: 1000→500; mode: multiplicative→additive; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1557 / 대기 | b24→c223 / n1541 | features: season→age; half_life: 180→365; num_leaves: 15→7; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1558 / 대기 | b24→c223 / n1552 | bound: 0.3→0.1; half_life: 180→365; n_estimators: 160→300; num_leaves: 7→15; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1559 / 대기 | b24→c223 / n1543 | bound: 0.3→0.5; features: core→season; min_child_samples: 500→200; n_estimators: 80→300; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1560 / 대기 | b24→c223 / n1540 | bound: 0.2→0.3; features: core→age; num_leaves: 15→7; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1561 / 대기 | b24→c223 / n1546 | bound: 0.3→0.15; min_child_samples: 500→1000; mode: additive→multiplicative; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1562 / 대기 | b24→c223 / n1544 | n_estimators: 80→160; num_leaves: 7→3; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1563 / 대기 | b24→c223 / n1547 | bound: 0.15→0.5; features: season→age; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1564 / 대기 | b24→c223 / n1552 | n_estimators: 160→80; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1565 / 대기 | b24→c223 / n1552 | features: core→season; min_child_samples: 500→1000; mode: additive→multiplicative; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1566 / 대기 | b24→c223 / n1540 | bound: 0.2→0.1; features: core→age; half_life: 180→없음; num_leaves: 15→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1567 / 대기 | b24→c223 / n1561 | bound: 0.15→0.3; half_life: 없음→180; n_estimators: 80→300; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1568 / 대기 | b24→c223 / n1544 | half_life: 180→없음; min_child_samples: 500→200; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1569 / 대기 | b24→c223 / n1553 | bound: 0.3→0.15; features: season→age; min_child_samples: 500→200; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1570 / 대기 | b24→c223 / n1546 | min_child_samples: 500→200; n_estimators: 80→300; num_leaves: 7→3; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1571 / 대기 | b24→c223 / n1545 | features: age→season; n_estimators: 80→160; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1572 / 대기 | b24→c223 / n1548 | n_estimators: 300→80; num_leaves: 7→3; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1573 / 대기 | b24→c223 / n1570 | bound: 0.3→0.5; mode: additive→multiplicative; reg_lambda: 10.0→2.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1574 / 대기 | b24→c223 / n1554 | features: age→season; min_child_samples: 500→200; n_estimators: 160→300; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1575 / 대기 | b24→c223 / n1569 | n_estimators: 160→300; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1576 / 대기 | b24→c223 / n1558 | reg_lambda: 2.0→2.5; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1577 / 대기 | b24→c223 / n1559 | bound: 0.5→0.3; half_life: 180→365; num_leaves: 7→15; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1578 / 대기 | b24→c223 / n1542 | bound: 0.1→0.3; min_child_samples: 1000→200; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1579 / 대기 | b24→c223 / n1577 | bound: 0.3→0.15; features: season→core; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1580 / 대기 | b24→c223 / n1546 | features: core→season; num_leaves: 7→15; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1581 / 대기 | b24→c223 / n1545 | half_life: 365→180; n_estimators: 80→160; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1582 / 대기 | b24→c223 / n1567 | mode: multiplicative→additive; reg_lambda: 10.0→2.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1583 / 대기 | b24→c223 / n1574 | bound: 0.2→0.15; mode: additive→multiplicative; n_estimators: 300→80; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1584 / 대기 | b24→c223 / n1581 | bound: 0.3→0.2; mode: multiplicative→additive; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1585 / 대기 | b24→c223 / n1549 | bound: 0.3→0.15; half_life: 365→없음; n_estimators: 80→160; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1586 / 대기 | b24→c223 / n1574 | bound: 0.2→0.3; half_life: 없음→365; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1587 / 대기 | b24→c223 / n1557 | learning_rate: 0.05→0.025; n_estimators: 160→80; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1588 / 대기 | b24→c223 / n1576 | bound: 0.1→0.3; num_leaves: 15→3; reg_lambda: 2.5→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1589 / 대기 | b24→c223 / n1541 | half_life: 180→없음; learning_rate: 0.05→0.025; reg_lambda: 10.0→30.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1590 / 대기 | b24→c223 / n1578 | n_estimators: 160→80; num_leaves: 7→3; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1591 / 대기 | b24→c223 / n1567 | half_life: 180→365; num_leaves: 15→3; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1592 / 대기 | b24→c223 / n1560 | bound: 0.3→0.1; features: age→season; n_estimators: 80→300; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1593 / 대기 | b24→c223 / n1553 | features: season→age; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1594 / 대기 | b24→c223 / n1570 | num_leaves: 3→15; reg_lambda: 10.0→30.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1595 / 대기 | b24→c223 / n1563 | features: age→season; num_leaves: 3→15; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1596 / 대기 | b24→c223 / n1550 | bound: 0.3→0.1; features: season→age; learning_rate: 0.05→0.025; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1597 / 대기 | b24→c223 / n1585 | learning_rate: 0.05→0.025; min_child_samples: 500→1000; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1598 / 대기 | b24→c223 / n1586 | bound: 0.3→0.1; min_child_samples: 200→1000; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1599 / 대기 | b24→c223 / n1585 | features: core→age; half_life: 없음→180; min_child_samples: 500→1000 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1600 / 대기 | b25→c238 / n1600 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1601 / 대기 | b25→c238 / n1600 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1602 / 대기 | b25→c238 / n1600 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1603 / 대기 | b25→c238 / n1601 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1604 / 대기 | b25→c238 / n1602 | bound: 0.2→0.1; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→1000; n_estimators: 0→80; num_leaves: 0→7; reg_lambda: 0.0→30.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1605 / 대기 | b25→c238 / n1604 | bound: 0.1→0.3; features: core→season; mode: additive→multiplicative; n_estimators: 80→300; num_leaves: 7→3; reg_lambda: 30.0→2.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1606 / 대기 | b25→c238 / n1604 | bound: 0.1→0.3; features: core→age; min_child_samples: 1000→500; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1607 / 대기 | b25→c238 / n1605 | bound: 0.3→0.15; features: season→core; n_estimators: 300→160; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1608 / 대기 | b25→c238 / n1605 | bound: 0.3→0.2; learning_rate: 0.025→0.05; min_child_samples: 1000→500; mode: multiplicative→additive; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1609 / 대기 | b25→c238 / n1606 | half_life: 365→180; learning_rate: 0.025→0.05; mode: additive→multiplicative; n_estimators: 80→300; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1610 / 대기 | b25→c238 / n1608 | bound: 0.2→0.1; features: season→core; min_child_samples: 500→200; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1611 / 대기 | b25→c238 / n1609 | features: age→season; n_estimators: 300→80; num_leaves: 7→3; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1612 / 대기 | b25→c238 / n1606 | half_life: 365→180; learning_rate: 0.025→0.05; min_child_samples: 500→1000; n_estimators: 80→160; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1613 / 대기 | b25→c238 / n1611 | features: season→core; half_life: 180→없음; reg_lambda: 30.0→2.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1614 / 대기 | b25→c238 / n1608 | learning_rate: 0.05→0.025; n_estimators: 300→160; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1615 / 대기 | b25→c238 / n1609 | bound: 0.3→0.5; half_life: 180→365; min_child_samples: 500→200; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1616 / 대기 | b25→c238 / n1606 | features: age→core; half_life: 365→180; n_estimators: 80→160; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1617 / 대기 | b25→c238 / n1609 | bound: 0.3→0.15; features: age→season; min_child_samples: 500→200; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1618 / 대기 | b25→c238 / n1610 | bound: 0.1→0.3; features: core→age; reg_lambda: 2.0→30.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1619 / 대기 | b25→c238 / n1609 | features: age→core; n_estimators: 300→160; reg_lambda: 30.0→2.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1620 / 대기 | b25→c238 / n1618 | features: age→season; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1621 / 대기 | b25→c238 / n1615 | bound: 0.5→0.15; min_child_samples: 200→1000; n_estimators: 160→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1622 / 대기 | b25→c238 / n1616 | bound: 0.3→0.1; half_life: 180→없음; num_leaves: 7→15; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1623 / 대기 | b25→c238 / n1615 | bound: 0.5→0.15; features: age→season; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1624 / 대기 | b25→c238 / n1611 | features: season→age; half_life: 180→없음; min_child_samples: 500→1000; mode: multiplicative→additive (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1625 / 대기 | b25→c238 / n1619 | bound: 0.3→0.15; half_life: 180→없음; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1626 / 대기 | b25→c238 / n1608 | bound: 0.2→0.1; half_life: 365→180; num_leaves: 3→15; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1627 / 대기 | b25→c238 / n1609 | bound: 0.3→0.5; learning_rate: 0.05→0.025; num_leaves: 7→3; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1628 / 대기 | b25→c238 / n1606 | features: age→core; half_life: 365→없음; min_child_samples: 500→200; n_estimators: 80→300; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1629 / 대기 | b25→c238 / n1605 | n_estimators: 300→80; num_leaves: 3→15; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1630 / 대기 | b25→c238 / n1604 | features: core→age; half_life: 365→180; min_child_samples: 1000→200; reg_lambda: 30.0→2.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1631 / 대기 | b25→c238 / n1621 | features: age→core; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1632 / 대기 | b25→c238 / n1612 | features: age→season; learning_rate: 0.05→0.025; n_estimators: 160→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1633 / 대기 | b25→c238 / n1617 | features: season→age; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1634 / 대기 | b25→c238 / n1626 | features: season→core; num_leaves: 15→7; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1635 / 대기 | b25→c238 / n1617 | bound: 0.15→0.5; half_life: 180→없음; learning_rate: 0.05→0.025; min_child_samples: 200→500; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1636 / 대기 | b25→c238 / n1630 | bound: 0.1→0.2; n_estimators: 80→300; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1637 / 대기 | b25→c238 / n1613 | bound: 0.3→0.15; reg_lambda: 2.0→2.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1638 / 대기 | b25→c238 / n1605 | mode: multiplicative→additive; n_estimators: 300→80; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1639 / 대기 | b25→c238 / n1609 | num_leaves: 7→3; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1640 / 대기 | b25→c238 / n1616 | bound: 0.3→0.2; reg_lambda: 30.0→10.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1641 / 대기 | b25→c238 / n1623 | half_life: 365→없음; learning_rate: 0.05→0.025; min_child_samples: 200→500; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1642 / 대기 | b25→c238 / n1624 | min_child_samples: 1000→500; n_estimators: 80→300; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1643 / 대기 | b25→c238 / n1625 | bound: 0.15→0.3; min_child_samples: 500→200; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1644 / 대기 | b25→c238 / n1629 | bound: 0.3→0.2; mode: multiplicative→additive; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1645 / 대기 | b25→c238 / n1627 | bound: 0.5→0.3; n_estimators: 300→160; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1646 / 대기 | b25→c238 / n1622 | bound: 0.1→0.3; min_child_samples: 500→1000; num_leaves: 15→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1647 / 대기 | b25→c238 / n1611 | bound: 0.3→0.5; reg_lambda: 30.0→30.5; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1648 / 대기 | b25→c238 / n1606 | min_child_samples: 500→1000; n_estimators: 80→300; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1649 / 대기 | b25→c238 / n1625 | bound: 0.15→0.5; learning_rate: 0.05→0.025; n_estimators: 160→300; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1650 / 대기 | b25→c238 / n1621 | bound: 0.15→0.3; features: age→season; mode: multiplicative→additive; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1651 / 대기 | b25→c238 / n1609 | half_life: 180→365; min_child_samples: 500→200; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1652 / 대기 | b25→c238 / n1604 | n_estimators: 80→300; num_leaves: 7→15; reg_lambda: 30.0→10.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1653 / 대기 | b25→c238 / n1605 | bound: 0.3→0.15; half_life: 365→없음; learning_rate: 0.025→0.05; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1654 / 대기 | b25→c238 / n1626 | features: season→age; num_leaves: 15→7; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1655 / 대기 | b25→c238 / n1635 | bound: 0.5→0.15; features: season→core; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1656 / 대기 | b25→c238 / n1606 | features: age→season; learning_rate: 0.025→0.05; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1657 / 대기 | b25→c238 / n1607 | bound: 0.15→0.5; features: core→age; half_life: 365→없음; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1658 / 대기 | b25→c238 / n1626 | bound: 0.1→0.2; features: season→core; min_child_samples: 500→1000; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1659 / 대기 | b25→c238 / n1611 | half_life: 180→없음; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1660 / 대기 | b25→c238 / n1642 | bound: 0.3→0.1; learning_rate: 0.05→0.025; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1661 / 대기 | b25→c238 / n1628 | mode: additive→multiplicative; reg_lambda: 30.0→10.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1662 / 대기 | b25→c238 / n1605 | half_life: 365→없음; min_child_samples: 1000→500; mode: multiplicative→additive; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1663 / 대기 | b25→c238 / n1615 | min_child_samples: 200→500; reg_lambda: 30.0→10.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1664 / 대기 | b26→c127 / n1664 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1665 / 대기 | b26→c127 / n1664 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1666 / 대기 | b26→c127 / n1664 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1667 / 대기 | b26→c127 / n1665 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1668 / 대기 | b26→c127 / n1664 | learning_rate: 0.0→0.05; method: median→tree; min_child_samples: 0→200; n_estimators: 0→300; num_leaves: 0→3; reg_lambda: 0.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1669 / 대기 | b26→c127 / n1668 | bound: 0.2→0.3; features: core→season; half_life: 없음→180; min_child_samples: 200→500; mode: additive→multiplicative; num_leaves: 3→15; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1670 / 대기 | b26→c127 / n1668 | bound: 0.2→0.3; features: core→age; half_life: 없음→365; min_child_samples: 200→1000; num_leaves: 3→7; reg_lambda: 2.0→30.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1671 / 대기 | b26→c127 / n1669 | bound: 0.3→0.5; features: season→core; min_child_samples: 500→1000; n_estimators: 300→80; reg_lambda: 2.0→10.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1672 / 대기 | b26→c127 / n1669 | bound: 0.3→0.1; half_life: 180→없음; learning_rate: 0.05→0.025; mode: multiplicative→additive; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1673 / 대기 | b26→c127 / n1670 | half_life: 365→없음; learning_rate: 0.05→0.025; min_child_samples: 1000→200; mode: additive→multiplicative; n_estimators: 300→160; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1674 / 대기 | b26→c127 / n1668 | bound: 0.2→0.3; num_leaves: 3→7; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1675 / 대기 | b26→c127 / n1669 | bound: 0.3→0.15; half_life: 180→365; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1676 / 대기 | b26→c127 / n1670 | bound: 0.3→0.1; half_life: 365→180; n_estimators: 300→160; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1677 / 대기 | b26→c127 / n1675 | bound: 0.15→0.5; features: season→core; learning_rate: 0.05→0.025 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1678 / 대기 | b26→c127 / n1669 | min_child_samples: 500→200; mode: multiplicative→additive; n_estimators: 300→80; num_leaves: 15→3; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1679 / 대기 | b26→c127 / n1673 | learning_rate: 0.025→0.05; n_estimators: 160→300; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1680 / 대기 | b26→c127 / n1672 | features: season→core; half_life: 없음→365; n_estimators: 160→80; num_leaves: 15→7; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1681 / 대기 | b26→c127 / n1669 | half_life: 180→365; learning_rate: 0.05→0.025; num_leaves: 15→3; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1682 / 대기 | b26→c127 / n1680 | bound: 0.1→0.2; features: core→age; half_life: 365→180; n_estimators: 80→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1683 / 대기 | b26→c127 / n1677 | bound: 0.5→0.15; reg_lambda: 10.0→2.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1684 / 대기 | b26→c127 / n1678 | learning_rate: 0.05→0.025; min_child_samples: 200→500; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1685 / 대기 | b26→c127 / n1673 | min_child_samples: 200→500; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1686 / 대기 | b26→c127 / n1680 | bound: 0.1→0.2; half_life: 365→180; learning_rate: 0.025→0.05; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1687 / 대기 | b26→c127 / n1669 | half_life: 180→없음; learning_rate: 0.05→0.025; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1688 / 대기 | b26→c127 / n1670 | bound: 0.3→0.2; n_estimators: 300→80; reg_lambda: 30.0→10.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1689 / 대기 | b26→c127 / n1677 | bound: 0.5→0.15; min_child_samples: 500→1000; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1690 / 대기 | b26→c127 / n1669 | bound: 0.3→0.2; mode: multiplicative→additive; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1691 / 대기 | b26→c127 / n1685 | reg_lambda: 30.0→30.5; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1692 / 대기 | b26→c127 / n1672 | bound: 0.1→0.3; features: season→core; n_estimators: 160→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1693 / 대기 | b26→c127 / n1684 | mode: additive→multiplicative; num_leaves: 3→15; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1694 / 대기 | b26→c127 / n1688 | bound: 0.2→0.1; half_life: 365→180; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1695 / 대기 | b26→c127 / n1673 | bound: 0.3→0.5; features: age→core; half_life: 없음→180; num_leaves: 3→7; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1696 / 대기 | b26→c127 / n1674 | features: core→season; half_life: 없음→365; learning_rate: 0.05→0.025; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1697 / 대기 | b26→c127 / n1691 | half_life: 없음→365; reg_lambda: 30.5→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1698 / 대기 | b26→c127 / n1692 | n_estimators: 80→160; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1699 / 대기 | b26→c127 / n1687 | bound: 0.3→0.5; min_child_samples: 500→200; n_estimators: 300→80; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1700 / 대기 | b26→c127 / n1672 | features: season→age; min_child_samples: 500→1000; num_leaves: 15→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1701 / 대기 | b26→c127 / n1677 | bound: 0.5→0.3; half_life: 365→180; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1702 / 대기 | b26→c127 / n1668 | bound: 0.2→0.3; features: core→season; half_life: 없음→365; min_child_samples: 200→1000 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1703 / 대기 | b26→c127 / n1699 | features: season→age; learning_rate: 0.025→0.05; num_leaves: 15→7; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1704 / 대기 | b26→c127 / n1674 | min_child_samples: 200→1000; n_estimators: 300→160; num_leaves: 7→15; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1705 / 대기 | b26→c127 / n1668 | bound: 0.2→0.15; features: core→season; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1706 / 대기 | b26→c127 / n1680 | features: core→age; num_leaves: 7→3; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1707 / 대기 | b26→c127 / n1695 | bound: 0.5→0.15; n_estimators: 160→300; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1708 / 대기 | b26→c127 / n1671 | bound: 0.5→0.1; features: core→season; half_life: 180→365; min_child_samples: 1000→200; mode: multiplicative→additive (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1709 / 대기 | b26→c127 / n1691 | bound: 0.3→0.15; learning_rate: 0.025→0.05; reg_lambda: 30.5→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1710 / 대기 | b26→c127 / n1668 | half_life: 없음→365; min_child_samples: 200→500; reg_lambda: 2.0→10.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1711 / 대기 | b26→c127 / n1669 | bound: 0.3→0.15; n_estimators: 300→160; num_leaves: 15→7; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1712 / 대기 | b26→c127 / n1674 | features: core→age; n_estimators: 300→160; reg_lambda: 30.0→10.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1713 / 대기 | b26→c127 / n1701 | bound: 0.3→0.15; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1714 / 대기 | b26→c127 / n1690 | min_child_samples: 500→200; num_leaves: 15→7; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1715 / 대기 | b26→c127 / n1670 | bound: 0.3→0.15; half_life: 365→180; mode: additive→multiplicative; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1716 / 대기 | b26→c127 / n1673 | bound: 0.3→0.2; features: age→core; min_child_samples: 200→1000; mode: multiplicative→additive (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1717 / 대기 | b26→c127 / n1693 | learning_rate: 0.025→0.05; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1718 / 대기 | b26→c127 / n1673 | half_life: 없음→180; min_child_samples: 200→500; mode: multiplicative→additive; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1719 / 대기 | b26→c127 / n1669 | features: season→core; min_child_samples: 500→1000; n_estimators: 300→160; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1720 / 대기 | b26→c127 / n1694 | features: age→season; n_estimators: 80→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1721 / 대기 | b26→c127 / n1679 | bound: 0.3→0.5; reg_lambda: 30.0→2.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1722 / 대기 | b26→c127 / n1668 | half_life: 없음→180; num_leaves: 3→15; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1723 / 대기 | b26→c127 / n1687 | half_life: 없음→180; min_child_samples: 500→200; num_leaves: 15→7; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1724 / 대기 | b26→c127 / n1673 | min_child_samples: 200→500; mode: multiplicative→additive; n_estimators: 160→300; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1725 / 대기 | b26→c127 / n1670 | features: age→core; mode: additive→multiplicative; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1726 / 대기 | b26→c127 / n1672 | bound: 0.1→0.2; min_child_samples: 500→200; reg_lambda: 2.0→10.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1727 / 대기 | b26→c127 / n1721 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1728 / 대기 | b27→c064 / n1728 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1729 / 대기 | b27→c064 / n1728 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1730 / 대기 | b27→c064 / n1728 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1731 / 대기 | b27→c064 / n1729 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1732 / 대기 | b27→c064 / n1730 | learning_rate: 0.0→0.05; method: median→tree; min_child_samples: 0→500; n_estimators: 0→300; num_leaves: 0→15; reg_lambda: 0.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1733 / 대기 | b27→c064 / n1732 | bound: 0.2→0.15; features: core→season; learning_rate: 0.05→0.025; min_child_samples: 500→1000; mode: additive→multiplicative; n_estimators: 300→160; num_leaves: 15→3; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1734 / 대기 | b27→c064 / n1732 | bound: 0.2→0.3; features: core→age; learning_rate: 0.05→0.025; n_estimators: 300→80; num_leaves: 15→7; reg_lambda: 2.0→30.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1735 / 대기 | b27→c064 / n1729 | half_life: 없음→180; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→200; n_estimators: 0→160; num_leaves: 0→15; reg_lambda: 0.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1736 / 대기 | b27→c064 / n1734 | features: age→season; half_life: 365→180; n_estimators: 80→300; num_leaves: 7→3; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1737 / 대기 | b27→c064 / n1735 | features: core→age; learning_rate: 0.025→0.05; num_leaves: 15→7; reg_lambda: 10.0→30.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1738 / 대기 | b27→c064 / n1734 | features: age→core; learning_rate: 0.025→0.05; min_child_samples: 500→200; n_estimators: 80→160; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1739 / 대기 | b27→c064 / n1733 | bound: 0.15→0.3; min_child_samples: 1000→200; reg_lambda: 2.0→30.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1740 / 대기 | b27→c064 / n1734 | bound: 0.3→0.2; half_life: 365→없음; min_child_samples: 500→1000; n_estimators: 80→160; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1741 / 대기 | b27→c064 / n1735 | learning_rate: 0.025→0.05; min_child_samples: 200→1000; n_estimators: 160→300; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1742 / 대기 | b27→c064 / n1732 | bound: 0.2→0.1; features: core→season; half_life: 365→없음; min_child_samples: 500→200; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1743 / 대기 | b27→c064 / n1734 | bound: 0.3→0.15; half_life: 365→없음; learning_rate: 0.025→0.05; mode: additive→multiplicative; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1744 / 대기 | b27→c064 / n1732 | half_life: 365→180; min_child_samples: 500→1000; num_leaves: 15→3; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1745 / 대기 | b27→c064 / n1741 | features: core→season; half_life: 180→365; min_child_samples: 1000→200; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1746 / 대기 | b27→c064 / n1734 | bound: 0.3→0.2; num_leaves: 7→3; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1747 / 대기 | b27→c064 / n1743 | bound: 0.15→0.5; features: age→core; n_estimators: 80→300; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1748 / 대기 | b27→c064 / n1737 | bound: 0.3→0.2; features: age→season; half_life: 180→없음; mode: multiplicative→additive (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1749 / 대기 | b27→c064 / n1737 | n_estimators: 160→80; num_leaves: 7→3; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1750 / 대기 | b27→c064 / n1736 | features: season→core; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1751 / 대기 | b27→c064 / n1733 | half_life: 365→180; min_child_samples: 1000→200; n_estimators: 160→80; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1752 / 대기 | b27→c064 / n1742 | features: season→age; min_child_samples: 200→1000; num_leaves: 15→3; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1753 / 대기 | b27→c064 / n1732 | bound: 0.2→0.5; min_child_samples: 500→1000; mode: additive→multiplicative; n_estimators: 300→80; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1754 / 대기 | b27→c064 / n1736 | half_life: 180→없음; learning_rate: 0.025→0.05; min_child_samples: 500→200; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1755 / 대기 | b27→c064 / n1734 | half_life: 365→없음; min_child_samples: 500→1000; mode: additive→multiplicative; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1756 / 대기 | b27→c064 / n1732 | bound: 0.2→0.1; half_life: 365→180; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1757 / 대기 | b27→c064 / n1735 | features: core→season; reg_lambda: 10.0→30.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1758 / 대기 | b27→c064 / n1734 | learning_rate: 0.025→0.05; reg_lambda: 30.0→10.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1759 / 대기 | b27→c064 / n1737 | features: age→core; half_life: 180→없음; learning_rate: 0.05→0.025; n_estimators: 160→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1760 / 대기 | b27→c064 / n1734 | bound: 0.3→0.2; features: age→season; half_life: 365→180; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1761 / 대기 | b27→c064 / n1743 | half_life: 없음→180; learning_rate: 0.05→0.025; min_child_samples: 500→1000; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1762 / 대기 | b27→c064 / n1750 | half_life: 180→없음; min_child_samples: 500→200; num_leaves: 3→7; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1763 / 대기 | b27→c064 / n1757 | bound: 0.3→0.5; learning_rate: 0.025→0.05 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1764 / 대기 | b27→c064 / n1758 | half_life: 365→없음; n_estimators: 80→300; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1765 / 대기 | b27→c064 / n1735 | bound: 0.3→0.15; learning_rate: 0.025→0.05; min_child_samples: 200→500; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1766 / 대기 | b27→c064 / n1738 | bound: 0.3→0.1; features: core→season; learning_rate: 0.05→0.025; n_estimators: 160→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1767 / 대기 | b27→c064 / n1737 | reg_lambda: 30.0→2.0 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1768 / 대기 | b27→c064 / n1741 | bound: 0.3→0.2; mode: multiplicative→additive; n_estimators: 300→80; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1769 / 대기 | b27→c064 / n1751 | num_leaves: 15→7; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1770 / 대기 | b27→c064 / n1738 | bound: 0.3→0.1; features: core→age; half_life: 365→180; n_estimators: 160→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1771 / 대기 | b27→c064 / n1759 | bound: 0.3→0.15; n_estimators: 300→80; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1772 / 대기 | b27→c064 / n1754 | reg_lambda: 30.0→2.0 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1773 / 대기 | b27→c064 / n1753 | features: core→age; min_child_samples: 1000→500; n_estimators: 80→160; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1774 / 대기 | b27→c064 / n1766 | features: season→core; min_child_samples: 200→500; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1775 / 대기 | b27→c064 / n1747 | features: core→season; learning_rate: 0.05→0.025; reg_lambda: 30.0→2.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1776 / 대기 | b27→c064 / n1736 | bound: 0.3→0.1; features: season→age; min_child_samples: 500→200; reg_lambda: 30.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1777 / 대기 | b27→c064 / n1759 | bound: 0.3→0.5; n_estimators: 300→80; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1778 / 대기 | b27→c064 / n1733 | bound: 0.15→0.3; half_life: 365→180; mode: multiplicative→additive (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1779 / 대기 | b27→c064 / n1741 | bound: 0.3→0.5; features: core→age; half_life: 180→365; num_leaves: 15→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1780 / 대기 | b27→c064 / n1756 | bound: 0.1→0.2; n_estimators: 300→80; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1781 / 대기 | b27→c064 / n1733 | min_child_samples: 1000→200; reg_lambda: 2.0→10.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1782 / 대기 | b27→c064 / n1776 | learning_rate: 0.025→0.05; min_child_samples: 200→1000; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1783 / 대기 | b27→c064 / n1753 | learning_rate: 0.05→0.025; min_child_samples: 1000→500; reg_lambda: 2.0→30.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1784 / 대기 | b27→c064 / n1778 | half_life: 180→365; learning_rate: 0.025→0.05; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1785 / 대기 | b27→c064 / n1752 | bound: 0.1→0.3; mode: additive→multiplicative; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1786 / 대기 | b27→c064 / n1780 | half_life: 180→없음; n_estimators: 80→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1787 / 대기 | b27→c064 / n1769 | min_child_samples: 200→500; n_estimators: 80→300; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1788 / 대기 | b27→c064 / n1734 | half_life: 365→없음; n_estimators: 80→160; reg_lambda: 30.0→2.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1789 / 대기 | b27→c064 / n1741 | bound: 0.3→0.5; min_child_samples: 1000→500 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1790 / 대기 | b27→c064 / n1734 | bound: 0.3→0.1; features: age→season; half_life: 365→없음; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1791 / 대기 | b27→c064 / n1738 | bound: 0.3→0.15; features: core→age; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1792 / 대기 | b28→c183 / n1792 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1793 / 대기 | b28→c183 / n1792 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1794 / 대기 | b28→c183 / n1792 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1795 / 대기 | b28→c183 / n1793 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1796 / 대기 | b28→c183 / n1792 | bound: 0.2→0.1; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→200; n_estimators: 0→160; num_leaves: 0→3; reg_lambda: 0.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1797 / 대기 | b28→c183 / n1796 | bound: 0.1→0.15; features: core→season; half_life: 없음→180; min_child_samples: 200→1000; mode: additive→multiplicative; reg_lambda: 10.0→30.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1798 / 대기 | b28→c183 / n1796 | features: core→age; half_life: 없음→180; n_estimators: 160→80; num_leaves: 3→7; reg_lambda: 10.0→30.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1799 / 대기 | b28→c183 / n1796 | bound: 0.1→0.5; half_life: 없음→365; mode: additive→multiplicative; num_leaves: 3→15; reg_lambda: 10.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1800 / 대기 | b28→c183 / n1797 | bound: 0.15→0.1; mode: multiplicative→additive; n_estimators: 160→300; num_leaves: 3→15; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1801 / 대기 | b28→c183 / n1797 | features: season→age; min_child_samples: 1000→500; n_estimators: 160→300; reg_lambda: 30.0→10.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1802 / 대기 | b28→c183 / n1796 | bound: 0.1→0.3; min_child_samples: 200→1000; n_estimators: 160→80; reg_lambda: 10.0→30.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1803 / 대기 | b28→c183 / n1800 | bound: 0.1→0.15; min_child_samples: 1000→500; mode: additive→multiplicative; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1804 / 대기 | b28→c183 / n1798 | half_life: 180→없음; min_child_samples: 200→500; n_estimators: 80→160; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1805 / 대기 | b28→c183 / n1799 | learning_rate: 0.025→0.05; min_child_samples: 200→500; n_estimators: 160→80; reg_lambda: 2.0→10.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1806 / 대기 | b28→c183 / n1800 | bound: 0.1→0.2; half_life: 180→365; n_estimators: 300→80; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1807 / 대기 | b28→c183 / n1802 | features: core→age; half_life: 없음→365; learning_rate: 0.025→0.05; mode: additive→multiplicative; n_estimators: 80→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1808 / 대기 | b28→c183 / n1805 | bound: 0.5→0.1; min_child_samples: 500→200; mode: multiplicative→additive; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1809 / 대기 | b28→c183 / n1801 | features: age→season; half_life: 180→365; learning_rate: 0.025→0.05; num_leaves: 3→7; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1810 / 대기 | b28→c183 / n1800 | bound: 0.1→0.2; features: season→age; half_life: 180→없음; num_leaves: 15→7; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1811 / 대기 | b28→c183 / n1801 | features: age→core; learning_rate: 0.025→0.05; n_estimators: 300→80; reg_lambda: 10.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1812 / 대기 | b28→c183 / n1806 | half_life: 365→없음; n_estimators: 80→300; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1813 / 대기 | b28→c183 / n1810 | bound: 0.2→0.3; min_child_samples: 1000→200; mode: additive→multiplicative; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1814 / 대기 | b28→c183 / n1808 | bound: 0.1→0.3; half_life: 365→180; min_child_samples: 200→500; n_estimators: 80→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1815 / 대기 | b28→c183 / n1805 | bound: 0.5→0.3; features: core→season; half_life: 365→없음; min_child_samples: 500→200; n_estimators: 80→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1816 / 대기 | b28→c183 / n1796 | features: core→age; learning_rate: 0.025→0.05; n_estimators: 160→80; reg_lambda: 10.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1817 / 대기 | b28→c183 / n1797 | features: season→core; half_life: 180→없음; min_child_samples: 1000→500; n_estimators: 160→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1818 / 대기 | b28→c183 / n1800 | half_life: 180→365; min_child_samples: 1000→500; num_leaves: 15→3; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1819 / 대기 | b28→c183 / n1801 | learning_rate: 0.025→0.05; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1820 / 대기 | b28→c183 / n1796 | learning_rate: 0.025→0.05; min_child_samples: 200→500; num_leaves: 3→7; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1821 / 대기 | b28→c183 / n1803 | bound: 0.15→0.3; half_life: 180→365; learning_rate: 0.025→0.05; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1822 / 대기 | b28→c183 / n1819 | bound: 0.15→0.1; mode: multiplicative→additive; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1823 / 대기 | b28→c183 / n1813 | bound: 0.3→0.15; features: age→core; min_child_samples: 200→1000; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1824 / 대기 | b28→c183 / n1815 | bound: 0.3→0.2; mode: multiplicative→additive; reg_lambda: 10.0→2.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1825 / 대기 | b28→c183 / n1801 | bound: 0.15→0.5; half_life: 180→365; n_estimators: 300→80; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1826 / 대기 | b28→c183 / n1806 | features: season→core; half_life: 365→180; min_child_samples: 1000→500; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1827 / 대기 | b28→c183 / n1805 | bound: 0.5→0.15; features: core→season; min_child_samples: 500→1000 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1828 / 대기 | b28→c183 / n1826 | bound: 0.2→0.3; features: core→age; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1829 / 대기 | b28→c183 / n1796 | bound: 0.1→0.5; min_child_samples: 200→500; mode: additive→multiplicative; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1830 / 대기 | b28→c183 / n1818 | half_life: 365→없음; learning_rate: 0.025→0.05; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1831 / 대기 | b28→c183 / n1801 | bound: 0.15→0.3; half_life: 180→없음; min_child_samples: 500→200; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1832 / 대기 | b28→c183 / n1808 | min_child_samples: 200→1000; n_estimators: 80→300; num_leaves: 15→3; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1833 / 대기 | b28→c183 / n1812 | bound: 0.2→0.15; mode: additive→multiplicative; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1834 / 대기 | b28→c183 / n1798 | bound: 0.1→0.3; num_leaves: 7→3; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1835 / 대기 | b28→c183 / n1817 | bound: 0.15→0.5; min_child_samples: 500→1000; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1836 / 대기 | b28→c183 / n1812 | learning_rate: 0.025→0.05; min_child_samples: 1000→200; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1837 / 대기 | b28→c183 / n1828 | bound: 0.3→0.5; mode: additive→multiplicative; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1838 / 대기 | b28→c183 / n1796 | bound: 0.1→0.2; n_estimators: 160→80; num_leaves: 3→7; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1839 / 대기 | b28→c183 / n1803 | bound: 0.15→0.3; half_life: 180→없음; num_leaves: 15→7; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1840 / 대기 | b28→c183 / n1796 | features: core→age; min_child_samples: 200→1000; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1841 / 대기 | b28→c183 / n1805 | bound: 0.5→0.15; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1842 / 대기 | b28→c183 / n1839 | mode: multiplicative→additive; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1843 / 대기 | b28→c183 / n1835 | bound: 0.5→0.3; features: core→age; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1844 / 대기 | b28→c183 / n1832 | bound: 0.1→0.2; reg_lambda: 10.0→2.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1845 / 대기 | b28→c183 / n1843 | features: age→season; learning_rate: 0.025→0.05; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1846 / 대기 | b28→c183 / n1798 | half_life: 180→없음; reg_lambda: 30.0→2.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1847 / 대기 | b28→c183 / n1799 | half_life: 365→없음; reg_lambda: 2.0→30.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1848 / 대기 | b28→c183 / n1812 | half_life: 없음→180; min_child_samples: 1000→200; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1849 / 대기 | b28→c183 / n1843 | n_estimators: 80→160; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1850 / 대기 | b28→c183 / n1796 | num_leaves: 3→15; reg_lambda: 10.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1851 / 대기 | b28→c183 / n1809 | half_life: 365→없음; min_child_samples: 500→1000; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1852 / 대기 | b28→c183 / n1816 | bound: 0.1→0.2; half_life: 없음→180; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1853 / 대기 | b28→c183 / n1797 | features: season→core; learning_rate: 0.025→0.05; min_child_samples: 1000→500 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1854 / 대기 | b28→c183 / n1802 | features: core→season; min_child_samples: 1000→200; n_estimators: 80→300; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1855 / 대기 | b28→c183 / n1849 | half_life: 없음→365; n_estimators: 160→300; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1856 / 대기 | b29→c095 / n1856 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1857 / 대기 | b29→c095 / n1856 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1858 / 대기 | b29→c095 / n1856 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1859 / 대기 | b29→c095 / n1857 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1860 / 대기 | b29→c095 / n1856 | bound: 0.2→0.3; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→500; n_estimators: 0→300; num_leaves: 0→3; reg_lambda: 0.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1861 / 대기 | b29→c095 / n1860 | bound: 0.3→0.5; features: core→season; half_life: 없음→365; min_child_samples: 500→200; mode: additive→multiplicative; n_estimators: 300→80; reg_lambda: 10.0→2.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1862 / 대기 | b29→c095 / n1860 | bound: 0.3→0.1; features: core→age; learning_rate: 0.025→0.05; num_leaves: 3→7; reg_lambda: 10.0→2.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1863 / 대기 | b29→c095 / n1861 | features: season→core; half_life: 365→없음; n_estimators: 80→160; num_leaves: 3→7; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1864 / 대기 | b29→c095 / n1861 | bound: 0.5→0.2; half_life: 365→180; min_child_samples: 200→1000; mode: multiplicative→additive; n_estimators: 80→160; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1865 / 대기 | b29→c095 / n1862 | bound: 0.1→0.3; half_life: 없음→180; min_child_samples: 500→200; mode: additive→multiplicative; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1866 / 대기 | b29→c095 / n1862 | bound: 0.1→0.2; features: age→core; half_life: 없음→365; min_child_samples: 500→1000; reg_lambda: 2.0→30.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1867 / 대기 | b29→c095 / n1861 | half_life: 365→180; min_child_samples: 200→1000; n_estimators: 80→160; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1868 / 대기 | b29→c095 / n1862 | learning_rate: 0.05→0.025; min_child_samples: 500→200; n_estimators: 300→80; reg_lambda: 2.0→10.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1869 / 대기 | b29→c095 / n1861 | features: season→core; min_child_samples: 200→500; n_estimators: 80→300; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1870 / 대기 | b29→c095 / n1864 | bound: 0.2→0.3; half_life: 180→365; learning_rate: 0.025→0.05; min_child_samples: 1000→200 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1871 / 대기 | b29→c095 / n1865 | bound: 0.3→0.5; min_child_samples: 200→500; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1872 / 대기 | b29→c095 / n1868 | features: age→core; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1873 / 대기 | b29→c095 / n1861 | bound: 0.5→0.15; learning_rate: 0.025→0.05; n_estimators: 80→300; reg_lambda: 2.0→30.0; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1874 / 대기 | b29→c095 / n1862 | reg_lambda: 2.0→10.0; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1875 / 대기 | b29→c095 / n1866 | bound: 0.2→0.5; mode: additive→multiplicative; n_estimators: 300→160; num_leaves: 7→15; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1876 / 대기 | b29→c095 / n1864 | half_life: 180→없음; min_child_samples: 1000→200; num_leaves: 15→3; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1877 / 대기 | b29→c095 / n1863 | features: core→age; learning_rate: 0.025→0.05; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1878 / 대기 | b29→c095 / n1866 | bound: 0.2→0.1; half_life: 365→없음; n_estimators: 300→80; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1879 / 대기 | b29→c095 / n1867 | bound: 0.5→0.15; n_estimators: 160→300; num_leaves: 3→7; reg_lambda: 2.0→10.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1880 / 대기 | b29→c095 / n1868 | bound: 0.1→0.3; learning_rate: 0.025→0.05; n_estimators: 80→160; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1881 / 대기 | b29→c095 / n1863 | half_life: 없음→180; min_child_samples: 200→1000; n_estimators: 160→80; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1882 / 대기 | b29→c095 / n1862 | features: age→season; half_life: 없음→180; n_estimators: 300→80; num_leaves: 7→15; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1883 / 대기 | b29→c095 / n1865 | half_life: 180→365; min_child_samples: 200→500; num_leaves: 7→3; reg_lambda: 2.0→30.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1884 / 대기 | b29→c095 / n1862 | bound: 0.1→0.2; features: age→core; half_life: 없음→180; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1885 / 대기 | b29→c095 / n1879 | min_child_samples: 1000→200; n_estimators: 300→80; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1886 / 대기 | b29→c095 / n1880 | bound: 0.3→0.2; n_estimators: 160→300; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1887 / 대기 | b29→c095 / n1863 | bound: 0.5→0.3; reg_lambda: 10.0→10.5; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1888 / 대기 | b29→c095 / n1868 | features: age→season; n_estimators: 80→300; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1889 / 대기 | b29→c095 / n1877 | min_child_samples: 200→1000; n_estimators: 160→80; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1890 / 대기 | b29→c095 / n1873 | bound: 0.15→0.3; features: season→core; mode: multiplicative→additive; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1891 / 대기 | b29→c095 / n1877 | features: age→season; n_estimators: 160→300; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1892 / 대기 | b29→c095 / n1860 | features: core→age; half_life: 없음→365; learning_rate: 0.025→0.05 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1893 / 대기 | b29→c095 / n1860 | bound: 0.3→0.15; mode: additive→multiplicative; num_leaves: 3→15; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1894 / 대기 | b29→c095 / n1879 | bound: 0.15→0.3; half_life: 180→365; mode: multiplicative→additive (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1895 / 대기 | b29→c095 / n1887 | features: core→age; num_leaves: 7→3; reg_lambda: 10.5→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1896 / 대기 | b29→c095 / n1864 | features: season→core; half_life: 180→없음; n_estimators: 160→300; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1897 / 대기 | b29→c095 / n1873 | half_life: 365→없음; n_estimators: 300→80; num_leaves: 3→15; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1898 / 대기 | b29→c095 / n1868 | n_estimators: 80→160; reg_lambda: 10.0→30.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1899 / 대기 | b29→c095 / n1869 | min_child_samples: 500→200; reg_lambda: 30.0→10.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1900 / 대기 | b29→c095 / n1868 | features: age→season; half_life: 없음→365; reg_lambda: 10.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1901 / 대기 | b29→c095 / n1869 | bound: 0.5→0.3; features: core→age; half_life: 365→없음; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1902 / 대기 | b29→c095 / n1872 | bound: 0.1→0.2; reg_lambda: 10.0→30.0; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1903 / 대기 | b29→c095 / n1879 | min_child_samples: 1000→500; num_leaves: 7→3; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1904 / 대기 | b29→c095 / n1886 | bound: 0.2→0.3; min_child_samples: 200→1000 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1905 / 대기 | b29→c095 / n1869 | bound: 0.5→0.15; half_life: 365→없음; min_child_samples: 500→200 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1906 / 대기 | b29→c095 / n1864 | half_life: 180→없음; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1907 / 대기 | b29→c095 / n1873 | features: season→age; learning_rate: 0.05→0.025; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1908 / 대기 | b29→c095 / n1871 | bound: 0.5→0.3; features: age→core; mode: multiplicative→additive; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1909 / 대기 | b29→c095 / n1879 | learning_rate: 0.025→0.05; n_estimators: 300→80; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1910 / 대기 | b29→c095 / n1864 | features: season→age; learning_rate: 0.025→0.05; n_estimators: 160→80; num_leaves: 15→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1911 / 대기 | b29→c095 / n1863 | bound: 0.5→0.3; half_life: 없음→180; num_leaves: 7→15; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1912 / 대기 | b29→c095 / n1866 | bound: 0.2→0.1; features: core→season; n_estimators: 300→160; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1913 / 대기 | b29→c095 / n1907 | half_life: 365→없음; min_child_samples: 200→500; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1914 / 대기 | b29→c095 / n1872 | half_life: 없음→180; learning_rate: 0.025→0.05 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1915 / 대기 | b29→c095 / n1860 | features: core→season; min_child_samples: 500→1000; mode: additive→multiplicative; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1916 / 대기 | b29→c095 / n1874 | bound: 0.1→0.3; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1917 / 대기 | b29→c095 / n1863 | half_life: 없음→180; min_child_samples: 200→500; reg_lambda: 10.0→2.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1918 / 대기 | b29→c095 / n1888 | num_leaves: 7→15; reg_lambda: 10.0→30.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1919 / 대기 | b29→c095 / n1863 | features: core→age; min_child_samples: 200→1000; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1920 / 대기 | b30→c215 / n1920 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1921 / 대기 | b30→c215 / n1920 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1922 / 대기 | b30→c215 / n1920 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1923 / 대기 | b30→c215 / n1921 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1924 / 대기 | b30→c215 / n1922 | bound: 0.2→0.3; learning_rate: 0.0→0.05; method: median→tree; min_child_samples: 0→1000; n_estimators: 0→300; num_leaves: 0→3; reg_lambda: 0.0→30.0; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1925 / 대기 | b30→c215 / n1921 | bound: 0.3→0.15; features: core→season; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→200; n_estimators: 0→160; num_leaves: 0→15; reg_lambda: 0.0→30.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1926 / 대기 | b30→c215 / n1924 | bound: 0.3→0.2; features: core→age; min_child_samples: 1000→200; num_leaves: 3→7; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1927 / 대기 | b30→c215 / n1925 | bound: 0.15→0.3; features: season→core; half_life: 없음→180; n_estimators: 160→80; num_leaves: 15→7; reg_lambda: 30.0→10.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1928 / 대기 | b30→c215 / n1926 | bound: 0.2→0.1; features: age→season; half_life: 365→없음; reg_lambda: 30.0→2.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1929 / 대기 | b30→c215 / n1926 | bound: 0.2→0.3; half_life: 365→180; min_child_samples: 200→500; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1930 / 대기 | b30→c215 / n1927 | bound: 0.3→0.2; mode: multiplicative→additive; n_estimators: 80→160; reg_lambda: 10.0→2.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1931 / 대기 | b30→c215 / n1925 | bound: 0.15→0.3; min_child_samples: 200→1000; reg_lambda: 30.0→2.0; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1932 / 대기 | b30→c215 / n1924 | bound: 0.3→0.1; features: core→age; half_life: 365→180; min_child_samples: 1000→200; n_estimators: 300→160 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1933 / 대기 | b30→c215 / n1929 | bound: 0.3→0.5; features: age→core; num_leaves: 7→15; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1934 / 대기 | b30→c215 / n1928 | bound: 0.1→0.2; half_life: 없음→365; min_child_samples: 200→1000; n_estimators: 300→160; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1935 / 대기 | b30→c215 / n1929 | half_life: 180→없음; n_estimators: 300→160; num_leaves: 7→3; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1936 / 대기 | b30→c215 / n1924 | bound: 0.3→0.2; half_life: 365→없음; min_child_samples: 1000→500; n_estimators: 300→80; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1937 / 대기 | b30→c215 / n1925 | bound: 0.15→0.5; half_life: 없음→180; learning_rate: 0.025→0.05; reg_lambda: 30.0→10.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1938 / 대기 | b30→c215 / n1932 | half_life: 180→365; reg_lambda: 30.0→2.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1939 / 대기 | b30→c215 / n1927 | bound: 0.3→0.15; min_child_samples: 200→1000; reg_lambda: 10.0→30.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1940 / 대기 | b30→c215 / n1924 | features: core→season; min_child_samples: 1000→200; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1941 / 대기 | b30→c215 / n1929 | bound: 0.3→0.15; min_child_samples: 500→1000; n_estimators: 300→160; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1942 / 대기 | b30→c215 / n1930 | half_life: 180→없음; learning_rate: 0.025→0.05; num_leaves: 7→3; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1943 / 대기 | b30→c215 / n1931 | half_life: 없음→180; n_estimators: 160→80; num_leaves: 15→3; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1944 / 대기 | b30→c215 / n1932 | bound: 0.1→0.3; half_life: 180→365; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1945 / 대기 | b30→c215 / n1927 | bound: 0.3→0.5; half_life: 180→365; min_child_samples: 200→1000; n_estimators: 80→160; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1946 / 대기 | b30→c215 / n1944 | features: age→season; learning_rate: 0.05→0.025; min_child_samples: 200→500; shrink: 0.75→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1947 / 대기 | b30→c215 / n1935 | bound: 0.3→0.5; half_life: 없음→365; min_child_samples: 500→1000; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1948 / 대기 | b30→c215 / n1930 | min_child_samples: 200→1000; num_leaves: 7→3; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1949 / 대기 | b30→c215 / n1945 | features: core→season; min_child_samples: 1000→500; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1950 / 대기 | b30→c215 / n1925 | bound: 0.15→0.1; features: season→age; mode: multiplicative→additive; n_estimators: 160→80; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1951 / 대기 | b30→c215 / n1947 | features: age→core; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1952 / 대기 | b30→c215 / n1946 | half_life: 365→없음; n_estimators: 160→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1953 / 대기 | b30→c215 / n1929 | bound: 0.3→0.15; half_life: 180→365; num_leaves: 7→3; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1954 / 대기 | b30→c215 / n1948 | half_life: 180→365; reg_lambda: 2.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1955 / 대기 | b30→c215 / n1927 | features: core→season; half_life: 180→없음; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1956 / 대기 | b30→c215 / n1931 | features: season→age; mode: multiplicative→additive; n_estimators: 160→300; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1957 / 대기 | b30→c215 / n1935 | bound: 0.3→0.15; features: age→core; half_life: 없음→365 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1958 / 대기 | b30→c215 / n1924 | features: core→season; n_estimators: 300→160; num_leaves: 3→7; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1959 / 대기 | b30→c215 / n1947 | half_life: 365→없음; learning_rate: 0.05→0.025; n_estimators: 160→300; shrink: 0.75→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1960 / 대기 | b30→c215 / n1936 | half_life: 없음→365; num_leaves: 3→15; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1961 / 대기 | b30→c215 / n1949 | half_life: 365→180; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1962 / 대기 | b30→c215 / n1948 | features: core→age; reg_lambda: 2.0→30.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1963 / 대기 | b30→c215 / n1939 | half_life: 180→없음; min_child_samples: 1000→200; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1964 / 대기 | b30→c215 / n1946 | bound: 0.3→0.2; n_estimators: 160→300; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1965 / 대기 | b30→c215 / n1935 | min_child_samples: 500→200; n_estimators: 160→80; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1966 / 대기 | b30→c215 / n1928 | features: season→core; min_child_samples: 200→1000; n_estimators: 300→80; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1967 / 대기 | b30→c215 / n1939 | features: core→season; n_estimators: 80→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1968 / 대기 | b30→c215 / n1958 | features: season→age; half_life: 365→180; n_estimators: 160→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1969 / 대기 | b30→c215 / n1955 | features: season→core (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1970 / 대기 | b30→c215 / n1931 | mode: multiplicative→additive; num_leaves: 15→3; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1971 / 대기 | b30→c215 / n1959 | half_life: 없음→180; n_estimators: 300→80; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1972 / 대기 | b30→c215 / n1942 | half_life: 없음→180; n_estimators: 160→300; reg_lambda: 2.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1973 / 대기 | b30→c215 / n1961 | min_child_samples: 500→1000; n_estimators: 160→300; reg_lambda: 30.0→30.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1974 / 대기 | b30→c215 / n1938 | min_child_samples: 200→500; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1975 / 대기 | b30→c215 / n1957 | bound: 0.15→0.3; min_child_samples: 500→1000; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1976 / 대기 | b30→c215 / n1928 | half_life: 없음→365; min_child_samples: 200→500; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1977 / 대기 | b30→c215 / n1935 | learning_rate: 0.05→0.025; n_estimators: 160→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1978 / 대기 | b30→c215 / n1976 | bound: 0.1→0.3; features: season→core (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1979 / 대기 | b30→c215 / n1931 | bound: 0.3→0.5; learning_rate: 0.025→0.05; min_child_samples: 1000→500; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1980 / 대기 | b30→c215 / n1956 | learning_rate: 0.025→0.05; reg_lambda: 2.0→30.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1981 / 대기 | b30→c215 / n1939 | num_leaves: 7→15; reg_lambda: 30.0→2.0; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1982 / 대기 | b30→c215 / n1940 | half_life: 365→없음; min_child_samples: 200→500 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1983 / 대기 | b30→c215 / n1965 | half_life: 없음→180; min_child_samples: 200→500; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1984 / 대기 | b31→c151 / n1984 | 변경 없음(비교 기준 자체) (기준 자체) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1985 / 대기 | b31→c151 / n1984 | bound: 0.2→0.3; mode: additive→multiplicative (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1986 / 대기 | b31→c151 / n1984 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1987 / 대기 | b31→c151 / n1985 | half_life: 없음→365 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1988 / 대기 | b31→c151 / n1984 | bound: 0.2→0.3; half_life: 없음→180; learning_rate: 0.0→0.025; method: median→tree; min_child_samples: 0→1000; n_estimators: 0→160; num_leaves: 0→7; reg_lambda: 0.0→30.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1989 / 대기 | b31→c151 / n1988 | bound: 0.3→0.5; features: core→season; half_life: 180→없음; mode: additive→multiplicative; n_estimators: 160→80; num_leaves: 7→3; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1990 / 대기 | b31→c151 / n1988 | bound: 0.3→0.1; features: core→age; half_life: 180→없음; min_child_samples: 1000→500; n_estimators: 160→300; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1991 / 대기 | b31→c151 / n1988 | half_life: 180→365; mode: additive→multiplicative; n_estimators: 160→80; num_leaves: 7→15; reg_lambda: 30.0→10.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1992 / 대기 | b31→c151 / n1988 | bound: 0.3→0.1; features: core→season; learning_rate: 0.025→0.05; min_child_samples: 1000→500; n_estimators: 160→80; num_leaves: 7→15; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1993 / 대기 | b31→c151 / n1991 | features: core→age; learning_rate: 0.025→0.05; n_estimators: 80→300; num_leaves: 15→3; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1994 / 대기 | b31→c151 / n1988 | half_life: 180→없음; num_leaves: 7→15; reg_lambda: 30.0→2.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1995 / 대기 | b31→c151 / n1989 | bound: 0.5→0.15; num_leaves: 3→15; reg_lambda: 2.0→30.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1996 / 대기 | b31→c151 / n1988 | features: core→age; min_child_samples: 1000→200; n_estimators: 160→300; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1997 / 대기 | b31→c151 / n1990 | bound: 0.1→0.3; features: age→core; learning_rate: 0.025→0.05; mode: additive→multiplicative; reg_lambda: 10.0→2.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1998 / 대기 | b31→c151 / n1992 | bound: 0.1→0.2; learning_rate: 0.05→0.025; reg_lambda: 30.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n1999 / 대기 | b31→c151 / n1988 | bound: 0.3→0.5; features: core→age; min_child_samples: 1000→200; mode: additive→multiplicative; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2000 / 대기 | b31→c151 / n1994 | num_leaves: 15→3; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2001 / 대기 | b31→c151 / n1995 | half_life: 없음→365; num_leaves: 15→7; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2002 / 대기 | b31→c151 / n1990 | half_life: 없음→365; n_estimators: 300→80; reg_lambda: 10.0→2.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2003 / 대기 | b31→c151 / n1991 | bound: 0.3→0.5; min_child_samples: 1000→200; n_estimators: 80→160; num_leaves: 15→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2004 / 대기 | b31→c151 / n1996 | features: age→season; half_life: 180→365; min_child_samples: 200→1000 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2005 / 대기 | b31→c151 / n1993 | min_child_samples: 1000→500; n_estimators: 300→160; num_leaves: 3→7; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2006 / 대기 | b31→c151 / n1991 | bound: 0.3→0.1; learning_rate: 0.025→0.05; mode: multiplicative→additive; shrink: 0.25→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2007 / 대기 | b31→c151 / n1999 | features: age→season; num_leaves: 7→3; reg_lambda: 2.0→10.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2008 / 대기 | b31→c151 / n2002 | bound: 0.1→0.2; learning_rate: 0.025→0.05; min_child_samples: 500→1000; n_estimators: 80→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2009 / 대기 | b31→c151 / n1988 | bound: 0.3→0.15; half_life: 180→365; mode: additive→multiplicative; num_leaves: 7→3; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2010 / 대기 | b31→c151 / n2004 | bound: 0.3→0.2; min_child_samples: 1000→200; num_leaves: 3→15; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2011 / 대기 | b31→c151 / n1996 | bound: 0.3→0.5; half_life: 180→없음; mode: additive→multiplicative; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2012 / 대기 | b31→c151 / n2006 | bound: 0.1→0.2; half_life: 365→180; min_child_samples: 1000→200 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2013 / 대기 | b31→c151 / n2011 | features: age→season; learning_rate: 0.025→0.05; num_leaves: 3→7 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2014 / 대기 | b31→c151 / n1993 | mode: multiplicative→additive; n_estimators: 300→80; reg_lambda: 10.0→2.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2015 / 대기 | b31→c151 / n1989 | features: season→core; learning_rate: 0.025→0.05; reg_lambda: 2.0→10.0; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2016 / 대기 | b31→c151 / n2010 | bound: 0.2→0.3; learning_rate: 0.025→0.05; reg_lambda: 30.0→2.0; shrink: 0.75→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2017 / 대기 | b31→c151 / n1993 | bound: 0.3→0.15; min_child_samples: 1000→200; num_leaves: 3→7; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2018 / 대기 | b31→c151 / n1991 | bound: 0.3→0.2; mode: multiplicative→additive; num_leaves: 15→3; shrink: 0.25→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2019 / 대기 | b31→c151 / n1989 | min_child_samples: 1000→500; n_estimators: 80→300 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2020 / 대기 | b31→c151 / n1992 | features: season→age; half_life: 180→365; min_child_samples: 500→200; n_estimators: 80→160; num_leaves: 15→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2021 / 대기 | b31→c151 / n2009 | bound: 0.15→0.5; half_life: 365→180; learning_rate: 0.025→0.05 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2022 / 대기 | b31→c151 / n1990 | features: age→season; half_life: 없음→365; min_child_samples: 500→200; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2023 / 대기 | b31→c151 / n1999 | bound: 0.5→0.15; reg_lambda: 2.0→2.5; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2024 / 대기 | b31→c151 / n2000 | min_child_samples: 1000→500; reg_lambda: 2.0→30.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2025 / 대기 | b31→c151 / n2001 | learning_rate: 0.025→0.05; min_child_samples: 1000→500; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2026 / 대기 | b31→c151 / n1990 | bound: 0.1→0.2; min_child_samples: 500→200; reg_lambda: 10.0→2.0; shrink: 1.0→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2027 / 대기 | b31→c151 / n2001 | features: season→core; learning_rate: 0.025→0.05; min_child_samples: 1000→200; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2028 / 대기 | b31→c151 / n1992 | n_estimators: 80→300; num_leaves: 15→3; reg_lambda: 30.0→2.0; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2029 / 대기 | b31→c151 / n2021 | features: core→age; n_estimators: 160→80; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2030 / 대기 | b31→c151 / n2006 | half_life: 365→없음; min_child_samples: 1000→500; num_leaves: 15→3; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2031 / 대기 | b31→c151 / n1988 | features: core→season; learning_rate: 0.025→0.05; min_child_samples: 1000→200; mode: additive→multiplicative; num_leaves: 7→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2032 / 대기 | b31→c151 / n1996 | min_child_samples: 200→500; shrink: 1.0→0.5 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2033 / 대기 | b31→c151 / n2019 | bound: 0.5→0.15; features: season→core; min_child_samples: 500→200 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2034 / 대기 | b31→c151 / n1992 | learning_rate: 0.05→0.025; min_child_samples: 500→1000; n_estimators: 80→160; reg_lambda: 30.0→10.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2035 / 대기 | b31→c151 / n1989 | bound: 0.5→0.15; features: season→age; half_life: 없음→365; min_child_samples: 1000→500 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2036 / 대기 | b31→c151 / n1994 | n_estimators: 160→300; shrink: 0.5→0.25 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2037 / 대기 | b31→c151 / n2005 | bound: 0.3→0.5; features: age→season; n_estimators: 160→80; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2038 / 대기 | b31→c151 / n2032 | learning_rate: 0.025→0.05 (단일 설정 차이) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2039 / 대기 | b31→c151 / n2015 | min_child_samples: 1000→200; reg_lambda: 10.0→30.0; shrink: 0.5→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2040 / 대기 | b31→c151 / n1992 | min_child_samples: 500→200; num_leaves: 15→3; shrink: 0.5→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2041 / 대기 | b31→c151 / n2001 | features: season→age; n_estimators: 80→160; num_leaves: 7→3 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2042 / 대기 | b31→c151 / n1991 | min_child_samples: 1000→500; mode: multiplicative→additive; shrink: 0.25→1.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2043 / 대기 | b31→c151 / n1993 | features: age→season; min_child_samples: 1000→500; reg_lambda: 10.0→30.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2044 / 대기 | b31→c151 / n2032 | bound: 0.3→0.2; n_estimators: 300→80 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2045 / 대기 | b31→c151 / n2021 | bound: 0.5→0.3; n_estimators: 160→300; num_leaves: 3→15 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2046 / 대기 | b31→c151 / n1988 | bound: 0.3→0.2; features: core→season; half_life: 180→365; reg_lambda: 30.0→2.0 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |
| n2047 / 대기 | b31→c151 / n2035 | bound: 0.15→0.5; reg_lambda: 2.0→10.0; shrink: 1.0→0.75 (여러 설정 동시 변경) | — | — | — / —%, —% | 0/5 / 0 |  — |

### 보정 학습용 OOF 기초 모델

| 기초 ID → 발전 모델 | 상태 | 확인된 새 학습 횟수 | 설명·근거 |
|---|---|---:|---|
| b00 → c206 | 완료 | 8 | 기존 c206 설정 재사용; 보정 학습용 시간 순서 OOF 생성 [기록](../../analysis_outputs/research_22h_20261107/bases/b00/result.json) |
| b01 → c003 | 완료 | 8 | 기존 c003 설정 재사용; 보정 학습용 시간 순서 OOF 생성 [기록](../../analysis_outputs/research_22h_20261107/bases/b01/result.json) |
| b02 → c158 | 완료 | 8 | 기존 c158 설정 재사용; 보정 학습용 시간 순서 OOF 생성 [기록](../../analysis_outputs/research_22h_20261107/bases/b02/result.json) |
| b03 → c174 | 완료 | 8 | 기존 c174 설정 재사용; 보정 학습용 시간 순서 OOF 생성 [기록](../../analysis_outputs/research_22h_20261107/bases/b03/result.json) |
| b04 → c093 | 완료 | 8 | 기존 c093 설정 재사용; 보정 학습용 시간 순서 OOF 생성 [기록](../../analysis_outputs/research_22h_20261107/bases/b04/result.json) |
| b05 → c185 | 완료 | 8 | 기존 c185 설정 재사용; 보정 학습용 시간 순서 OOF 생성 [기록](../../analysis_outputs/research_22h_20261107/bases/b05/result.json) |
| b06 → c117 | 완료 | 8 | 기존 c117 설정 재사용; 보정 학습용 시간 순서 OOF 생성 [기록](../../analysis_outputs/research_22h_20261107/bases/b06/result.json) |
| b07 → c000 | 완료 | 8 | 기존 c000 설정 재사용; 보정 학습용 시간 순서 OOF 생성 [기록](../../analysis_outputs/research_22h_20261107/bases/b07/result.json) |
| b08 → c186 | 완료 | 8 | 기존 c186 설정 재사용; 보정 학습용 시간 순서 OOF 생성 [기록](../../analysis_outputs/research_22h_20261107/bases/b08/result.json) |
| b09 → c030 | 완료 | 8 | 기존 c030 설정 재사용; 보정 학습용 시간 순서 OOF 생성 [기록](../../analysis_outputs/research_22h_20261107/bases/b09/result.json) |
| b10 → c142 | 완료 | 8 | 기존 c142 설정 재사용; 보정 학습용 시간 순서 OOF 생성 [기록](../../analysis_outputs/research_22h_20261107/bases/b10/result.json) |
| b11 → c046 | 대기 | 0 | 기존 c046 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b12 → c081 | 대기 | 0 | 기존 c081 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b13 → c010 | 대기 | 0 | 기존 c010 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b14 → c191 | 대기 | 0 | 기존 c191 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b15 → c170 | 대기 | 0 | 기존 c170 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b16 → c128 | 대기 | 0 | 기존 c128 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b17 → c115 | 대기 | 0 | 기존 c115 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b18 → c038 | 대기 | 0 | 기존 c038 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b19 → c226 | 대기 | 0 | 기존 c226 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b20 → c014 | 대기 | 0 | 기존 c014 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b21 → c232 | 대기 | 0 | 기존 c232 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b22 → c136 | 대기 | 0 | 기존 c136 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b23 → c098 | 대기 | 0 | 기존 c098 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b24 → c223 | 대기 | 0 | 기존 c223 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b25 → c238 | 대기 | 0 | 기존 c238 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b26 → c127 | 대기 | 0 | 기존 c127 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b27 → c064 | 대기 | 0 | 기존 c064 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b28 → c183 | 대기 | 0 | 기존 c183 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b29 → c095 | 대기 | 0 | 기존 c095 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b30 → c215 | 대기 | 0 | 기존 c215 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
| b31 → c151 | 대기 | 0 | 기존 c151 설정 재사용; 보정 학습용 시간 순서 OOF 생성 — |
