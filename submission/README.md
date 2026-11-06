# OIBC 2026 제출 파이프라인

## Autoresearch 후보 확인

새 후보는 `autoresearch_candidate/`에 있습니다. 해당 폴더의 `composition.csv`와 `forecast.csv`를 함께 사용하며, `submission_files.zip`에는 이 두 CSV만 들어 있습니다. 기존 `award_candidate/`는 비교 기준으로 보존합니다.

프로젝트 최상위 폴더에서 다음 명령으로 기록과 제출 파일을 검증합니다.

```bash
python submission/autoresearch_verify.py
python submission/autoresearch_verify_final.py
python submission/validate_artifacts.py submission/autoresearch_candidate --self-check
```

실험 기록은 `../analysis_outputs/autoresearch_20261103/results.tsv`, 최종 평가와 고정 설정은 그 아래 `final/`에 있습니다. `W_pct`는 내부 비교 지표이며 공식 리더보드 점수가 아닙니다. 선택 기간에서 찾은 설정을 고정한 뒤 후기 연도를 평가했으며, 후기 결과를 보고 다시 조정하지 않았습니다.

최종 재학습 명령은 `python submission/autoresearch/final_run.py`입니다. 기존 산출물 보호를 위해 출력 경로가 있으면 중단합니다. 재현 실행은 필요한 데이터·캐시·실험 기록을 유지한 별도 작업 복사본에서 `analysis_outputs/autoresearch_20261103/final/`과 `submission/autoresearch_candidate/`가 아직 없는 상태로 시작하세요. 원본 결과를 지우고 실행하지 마세요. 실행은 모델 한 개씩, 모델 스레드 2개, BLAS 스레드 1개, 낮은 Windows 우선순위를 사용합니다. 패키지 버전과 입력·소스 해시는 후보의 `manifest.json`에 기록합니다.

기존 분석을 구현한 파이프라인과, 구성 선택 기간을 분리해 재검증하는 실행 경로입니다. 기존 `cache/val_summary.json`의 11.5515%는 같은 기간의 오차로 발전소 구성을 선택한 개발 점수입니다. 독립 검증 점수나 공식 리더보드 점수로 해석하면 안 됩니다.

## 검증 후 제출 후보 만들기

프로젝트 최상위 폴더에서 실행합니다.

```bash
python submission/validate_pipeline.py
python submission/validate_artifacts.py submission/award_candidate --self-check
python submission/verify_run.py
python submission/check_pipeline.py
```

`validate_pipeline.py`는 2023년 6월까지 학습하고 다음 1년에서 구성과 블렌드 비중을 선택합니다. 설정을 고정한 후 2024년 6월~2025년 5월을 평가하고, 전 기간 재학습으로 `award_candidate/composition.csv`, `award_candidate/forecast.csv`를 생성합니다. 결과와 월별·전체 발전소 구간 분석은 `../analysis_outputs/award_run/`에 있습니다. 입력·코드·설정·패키지 버전으로 캐시를 구분하고 내용 해시도 검사합니다. 기존 제출 CSV는 보존합니다.

발전량 행이 없는 시각은 실적 0으로 만들지 않고 평가에서 제외합니다. 초기 검증 구간은 편입 전 발전소가 있으므로 모든 발전소가 갖춰진 2025년 1~5월 결과도 확인해야 합니다. 기존 모델 설계 자체는 과거 분석에서 후기 평가 연도를 보았으므로 이 재검증도 완전히 미공개인 최종 테스트를 대신하지 않습니다.

## 기존 실행 경로

아래 명령은 `submission/` 폴더에서 실행합니다.

```bash
python make_submission.py all        # 전체 실행 (약 20~30분)
python make_submission.py check      # 제출 파일 형식 검사만
```

단계별 실행도 됩니다: `features | val | compose | predict | check`. 이 기존 경로는 출력 파일이 있으면 건너뜁니다. 설정이나 입력을 바꿔도 자동 무효화하지 않으므로 새로운 실험은 위 `validate_pipeline.py`를 사용하세요. 기존 캐시와 제출 파일을 혼합해 성능을 비교하지 마세요.

| 단계 | 하는 일 | 산출물 |
|---|---|---|
| features | 원본 parquet에서 발전소×시각 피처 생성. 17시 라운드 A+B 예보, 결손은 10시 라운드로 보간, 태양기하(고도·방위·cosz·대기외일사·일조비율), 야간 = 구간 시작·끝 모두 고도 ≤ 0° | `cache/feat_train.parquet`, `cache/feat_test.parquet`, `cache/smp.parquet` |
| val | 학습 ≤ 2024-05, 검증 2024-06~2025-05. pooled LightGBM L1 5시드 + 발전소별 L2 10% (bottom-up) | `cache/val_pred_site.parquet`, `cache/val_bottom_up.json` |
| compose | 검증 오차 상관으로 쌍둥이 짝을 만들어 교차 배정(각 집합 20,000~22,655.4 kW). 같은 구성으로 그룹 직접 모델을 검증 학습해 최종 레시피의 검증 점수 산출 | `composition.csv`, `cache/val_summary.json` |
| predict | 전 기간(2021-01~2025-05) 재학습: pooled 5시드 + 발전소별 + 그룹 직접 모델 → 50:50 블렌드 → 테스트 연도 예측 | `forecast.csv`, `cache/test_pred_site.parquet` |
| check | 254행/17,521행, smp.csv 시각 일치, 용량 범위, 음수·NaN 없음 등 형식 검사 | 콘솔 출력 |

## 고정된 설계 결정 (바꾸려면 상단 상수)

- `SEEDS`(5개), `SITE_W`=0.10, `DIRECT_W`=0.50, `MIN_SITE_ROWS`=1000 (이력이 이보다 짧은 발전소는 pooled 예측만 사용)
- 후처리 없음: 스케일 보정·저출력 0 처리·상한 캡은 검증에서 전부 손해였음
- 야간 0 처리는 "그 시각에 해를 보는 발전소가 하나도 없을 때"만 적용. 박명 시각은 모델값

## 제출 전 체크리스트

1. `python make_submission.py check` 통과
2. 제출 후보의 `manifest.json`과 `../analysis_outputs/award_run/outer_metrics.json` 확인. `W_pct`는 내부 비교 지표이며 공식 점수는 수익에서 가중 절대오차의 0.1배를 차감한 값
3. 하나의 평가 연도에는 같은 구성을 유지. 제출 간 변경 가능 여부·횟수·무효 조건은 공식 문제정의서에서 확인. 제공 README는 첫 제출 후 영구 고정을 명시하지 않음
4. 원본 데이터는 로컬에 보관. 외부 데이터·모델·공유 제한은 공식 문제정의서의 최신 규정 확인
