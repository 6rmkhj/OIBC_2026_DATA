# LENS 3 — 방법론 / 최신 연구 동향 (2026 POSTECH OIBC 빅데이터 경진대회)

작성일: 2026-10-26. 대상: 태양광 253개소(42,655.4 kW)를 G1/G2(각 ≥20,000 kW)로 나누고, 전일 17:00 발행 예보로 집합별 시간당 kWh를 하루 전 예측하는 과제.
점수 S = Σ SMP·실적 − 0.10·Σ SMP·k·|예측−실적| (k=3 @ 11~15시, 그 외 1). 첫 항은 참가자와 무관하므로 **실질 목표 = Σ_t w(t)·(|e_G1(t)|+|e_G2(t)|) 최소화, w = SMP·k**.

> 표기 규칙: 【검증】= 원문/공식 문서/로컬 데이터로 직접 확인. 【요약】= 검색 결과 요약·초록 수준으로 확인(본문 수치 미확인). 【미검증】= 확인 못 했거나 추론. 【로컬】= 참가자 폴더의 README/sites.csv/smp.csv에서 직접 계산.

---

## 0. 한눈에 보는 결론 (실행 우선순위)

1. **구성(G1/G2)은 "쌍둥이 포트폴리오"로.** 벌점은 집합별 절대오차의 합이므로 |e1|+|e2| ≥ |e1+e2| (등호 ⇔ 같은 부호). 두 집합의 오차가 **최대한 같은 방향**으로 움직이도록, 즉 지역·기상관측지점·용량·데이터 보유기간을 **층화 후 교대로(interleave)** 배정한다. 지역별로 가르는 "분산투자"는 정확히 반대 방향이며 손해다(§5 유도, 참가자 실험치: 동서 분할 +7.9%, 남북 +11.8%, 무작위 섞기 +1.6%, 최적화 +1.3% vs 하한 【요약: 제3자 참가자 README】).
2. **손실함수 = L1(가중 중앙값), 표본가중치 = 과거 SMP·k.** 절대오차 하에서 최적 점예측은 조건부 중앙값(Gneiting 2011)이고, 양의 가중치 w(t)는 시각별 최적 함수형을 바꾸지 않는다. LightGBM `regression_l1`은 잎 값과 초기값을 **가중 백분위(중앙값)** 로 계산함을 소스에서 확인했다【검증】. 11~15시가 전체 벌점 가중치의 **44.7%**【로컬 계산】.
3. **입력 없는 일사량은 청천(clear-sky) 모델 × 운량 매핑으로 대체.** pvlib Ineichen/Haurwitz 청천 GHI + Kasten–Czeplak/Larson 선형(offset 0.35) 또는 Campbell–Norman(투과율 0.75·(1−운량)) 프록시, 태양고도·cosZ, 운량 A/B 평균·차이, UV지수/청천UV 비, 운고·시정·이슬점차·강설 누적치. 목표변수는 설비이용률(CF) 또는 "청천 성능지수"(실적/청천 기대출력)로 정규화.
4. **두 제공사·두 라운드는 "모두 피처로"** 넣은 단일 모델 + 라운드17 주력. 다중 NWP 입력 결합은 문헌에서 일관되게 기량 향상(Pierro 2016: 42%→46%; IEA PVPS T16: 47%→51% 비선형 블렌딩)【요약/검증】.
5. **검증은 시간 블록(연·계절 단위 롤링), 조기종료·앙상블 가중치는 "집합 합계의 SMP·k 가중 MAE"로.** 무작위 행 분할은 점수를 약 26% 낙관 보고(참가자 실험)【요약】.
6. **예측 수준은 (i) 발전소 풀링 모델 합산 + (ii) 집합 총량 직접 모델**을 둘 다 만들고 홀드아웃에서 블렌딩. 중앙값은 합산 시 보존되지 않으므로(Σ중앙값 ≠ 중앙값Σ) 집합 수준 재보정(L1 2단계) 필수.
7. **데이터 정제:** 결측은 0으로 메우지 말 것(행 없음=결측【로컬 README】), 클리핑/출력제어 의심 구간 탐지(pvanalytics), 유효용량(최근 12개월 99.5% 분위) 재추정, 적설 지속 피처, 열화·용량변경은 "최근 데이터 가중/추세 피처"로 흡수.

---

## 1. (a) 다중 NWP 제공사를 쓰는 하루 전 지역·집합 PV 예측

### 문헌이 말하는 것
- **다중 NWP 결합은 거의 항상 이득.** Pierro et al. (2016, *Solar Energy* 134:132–146)은 IFS·WRF 두 NWP를 각각 입력으로 한 데이터 기반 모델들을 비교했고, "같은 ML 알고리즘도 어떤 NWP를 입력으로 받느냐에 따라 성능이 달라지며(입력 편향 보정 능력 차이), 정확도가 비슷하되 **NWP 입력과 알고리즘이 다양한** 멤버를 평균하면 기량(skill)이 단일 최고 42%→앙상블 46%"로 올랐다【요약】.
- IEA PVPS Task 16 "Regional solar power forecasting" (2020) 요약본: 이탈리아 전체 24h 예측에서 벤치마크 RMSE 기량 28~47%, **비선형 블렌딩으로 47%→51%**; 위트레흐트 150개 시스템 집합은 42~44%. 모든 업스케일링 방법은 "집합 전체를 하나의 가상 발전소로 보고 지역 발전량을 직접 예측"했다【검증: PDF 텍스트】.
- Li et al. (2016, IEEE PESGM; Stony Brook/IBM): 지리 클러스터별 모델 → ISO 존 합산, 서로 다른 NWP 기반 보정 결과를 최적 계수로 블렌딩, 하루 전 NRMSE 5.28%(단일 최고 대비 −30.6%)【요약】.
- Visser, AlSkaif & van Sark (2019, IEEE PVSC): 152개 PV 시스템, 하루 전, 지역 기상예보 입력. GBDT 기량 41.4%, RF 41.3%가 최고; **집합화로 모든 모델 MAE ≥18%, RMSE ≥20% 감소**【검증: 초록】. 같은 그룹의 2022 *Renewable Energy* 183:267–282: 12개 모델, **시스템 간 거리↑·집합 규모↑ → 기술적 정확도↑**, 다만 경제성 평가에선 물리모델이 1위(목적함수에 맞춰 모델을 골라야 함)【검증: 초록】.
- ASHRAE GEPIII 교훈 논문(arXiv 2202.02898): 상위권은 GBM 트리 앙상블(LightGBM 최다), 참가자들은 **전처리·피처 추출이 가장 중요**했다고 응답【검증: 초록】.

### 라운드(발행시각) 선택
- 직접 비교 문헌은 못 찾았다【미검증】. 다만 리드타임이 짧을수록 오차가 작다는 것은 일관된다: Lorenz et al. (2008, EU PVSEC): 단일 지점 rRMSE 1일차 36.9% → 3일차 46.3%, 독일 전체 앙상블 13.4% → 22.5%【검증: PDF 텍스트】. 라운드 17은 라운드 10보다 7시간 최신이므로 **주력 입력은 round=17**.
- 주최 측 baseline.py는 라운드별 별도 LightGBM(L2, 이용률 타깃)을 학습해 **두 라운드 예측을 단순 평균**한다【검증: 로컬】. 권장 개선: (i) 한 행에 round10·round17 값을 모두 피처로(차분 = "예보 추세/불확실성" 신호), (ii) 라운드별 모델을 홀드아웃에서 가중 블렌딩(균등 평균보다 17 쪽에 더 큰 가중치가 나올 가능성이 큼 — 데이터로 확인할 것).

### 예보오차 인지(forecast-error-aware) 학습
- 운영 예측은 "예보 기상"으로 이뤄지므로 **학습도 예보 기상으로** 해야 한다(MOS식). 실측 기상으로 학습하고 예보로 추론하면 입력 분포 불일치가 생긴다【요약: arXiv 1709.08135 등】. 제공된 `observed_wa/wb`는 (1) 증강 데이터(예보 대신 실측을 넣은 행 추가), (2) 관측지점별 **예보 편향 통계**(예: A사 운량의 계절·시간대별 평균 오차) 피처 생성에 쓰되, 학습 구간 통계만 사용(누수 방지).
- 참가자(ruby9915) 실험【요약, 제3자】: NN에 예보오차 모사 노이즈 주입 시 팀 합계 오차 12.63%→12.04%(시드 편차도 거의 소멸); 실측 기상 행 추가 시 GBDT 12.26→12.17; **GBDT에 노이즈 복제는 해로움**. arXiv 2607.12954는 NWP 오차가 "시간상관·상태의존·변수 간 결합"이라 단순 백색잡음 섭동은 비현실적이라고 지적【검증: 초록】 → 노이즈를 넣으려면 실측−예보 잔차를 **일 단위 블록으로 리샘플**해 주입하는 편이 현실적(추론).

---

## 2. (b) 청천지수·이용률 정규화, 태양기하, pvlib 청천 모델

- **왜 정규화하나:** 청천 모델로 나누면 결정론적 일주기·계절 주기가 제거되고 "기상(구름) 성분"만 남아 ML이 배우기 쉽다【요약: SciTePress 2018; HAL hal-03964785 "청천 정규화는 모델 종류와 무관하게 성능 향상"】. PV 출력에 대한 대응물은 **clear-sky performance index**(실적/청천 기대출력)로, Bolzano 그룹은 이를 써서 하루 전 기량 35~39% 보고【요약】. Lorenz 2008도 ECMWF 3h 값을 시간 보간할 때 **청천지수 kt\* 공간에서 보간**하고 kt\*·천정각의 함수로 편향 보정(V3)해 지역 예측이 크게 개선됨을 보였다【검증: PDF】.
- **pvlib 도구【검증: 공식 문서】:** `clearsky.ineichen`(Linke 탁도 필요, `lookup_linke_turbidity`로 월별 기후값 조회), `clearsky.haurwitz`(천정각만으로 GHI), `clearsky.simplified_solis`, `clearsky.bird`, `Location.get_clearsky`, `clearsky.detect_clearsky`(Reno–Hansen). 태양위치는 `solarposition` 모듈(SPA). 좌표가 ≤2 km 이동·반올림되어 있어도【로컬 README】 태양기하·청천 GHI에는 영향이 무시할 수준.
- **운량→일사 매핑(일사 입력이 없을 때)【검증: pvlib v0.9.5 forecast.py 소스】:**
  - 선형(Larson et al. 2016): `ghi = (0.35 + 0.65·(1 − cloud/100))·ghi_clear` (100% 운량이면 청천의 35%).
  - Campbell–Norman: 투과율 `τ = 0.75·(1 − cloud/100)` → `irradiance.campbell_norman(zenith, τ)`로 GHI/DNI/DHI.
  - Kasten–Czeplak(1980, *Solar Energy* 24:177–190): G/G₀ = 1 − 0.75·(N/8)^3.4 형태가 흔히 인용되나 **원문 계수는 직접 확인 못 함**【미검증】; 캐나다 검증(Ahamed 2019)에서 원계수로 R² 0.69–0.82, 지역 재적합 시 개선 → **계수를 우리 데이터로 재적합(= GBDT가 알아서 학습)** 하는 편이 낫다.
  - 결론: 매핑식 자체를 "정답"으로 쓰기보다 **청천 GHI, cosZ, 운량(A,B), 매핑 프록시 2~3종**을 모두 피처로 주고 트리가 비선형을 학습하게 한다. 트리 모델은 단조 제약(`monotone_constraints`: 운량↑→출력↓)을 걸 수 있다【검증: LightGBM 문서】.
- **UV 지수(B사)의 가치:** UV지수는 청천 UV × 구름변조계수로 만들어지므로 GHI와 강하게 연동되지만, 구름은 UV보다 GHI를 더 많이 감쇠(한국 4개소 연구: 운량↑ → UVER/GHI 비 상승)【요약: MDPI Energies 2020】. 즉 UV지수는 **훌륭한 비선형 일사 프록시**이지만 1:1은 아니다 → `uv_idx`, `uv_idx / 청천UV근사(같은 시각·계절의 상위분위)`를 함께 넣는다.
- **타깃 선택 실무:** CF = energy/capacity(기준선 방식【로컬】) 또는 CSI_pv = energy/(capacity·청천GHI/1000). CSI_pv는 일출·일몰 부근에서 분모가 작아 폭주하므로 clip(0~1.5)·해당 시각 가중치 축소 필요(arXiv 2608.02088도 주간 외 0, [0,1.5] 클립 사용【요약】). 안전한 절충: **타깃은 CF, 청천 GHI는 피처**.
- **명판용량 대신 유효용량:** 최근 12개월 시간별 energy의 99.5% 분위(일중 시각별)를 "유효 피크"로 재추정(pvanalytics `clipping.threshold`가 쓰는 방식과 동일 발상【검증: 문서】). DC/AC 비, 인버터 제한, 열화·고장 반영.

---

## 3. (c) (가중) 절대오차의 최적 점예측 = (가중) 중앙값, L1/분위 목적함수, 합산 편향

- **이론:** 절대오차 스코어 하에서 최적 점예측은 예측분포의 중앙값(Gneiting 2011, *JASA* "Making and evaluating point forecasts"; 강의자료에 "under absolute error, optimal point forecast is any median")【검증: 초록/슬라이드】. 우리 벌점은 시각 t마다 w(t)·|f−y| 이고 w(t)>0 는 상수 배율이므로 **시각별 최적 함수형은 여전히 조건부 중앙값**이다. 표본가중치 w(t)는 "어느 시각을 더 정확히 맞출지"의 자원 배분만 바꾼다. (가중 표본의 Σw|f−y| 최소화 해가 가중 중앙값이라는 것은 LAD 회귀의 기본 사실; Koenker–Bassett 분위회귀의 τ=0.5 특수경우.)
- **LightGBM 구현【검증: `src/objective/regression_objective.hpp`】:** `regression_l1`은 `RenewTreeOutput`에서 잎별 잔차의 **백분위(α=0.5)**, 가중치가 있으면 `WeightedPercentileFun`(누적가중 0.5 교차점 보간)으로 잎 값을 갱신하고, `BoostFromScore`도 (가중) 중앙값으로 초기화한다(L2는 가중 평균). `quantile` 목적함수는 `alpha`로 분위를 지정(비대칭 기울기 (1−α)/−α). 따라서 **`objective='regression_l1'` + `sample_weight = SMP(t)·k(t)`** 가 정확히 우리 목적함수의 표본 근사다. 평가 지표도 `metric='l1'`(가중 적용됨).
- **문서 확인 사항【검증】:** `alpha`(기본 0.9)는 huber/quantile에만 사용; `weight`는 음수 불가; `early_stopping_round`, `first_metric_only`; `boost_from_average`(L1에선 중앙값 초기화로 동작).
- **실무 팁(일부 추론):** L1 기울기는 ±1 상수라 수렴이 느리고 잎 값이 중앙값으로 "스냅"된다 → 학습률을 낮추고 트리 수를 늘리거나, `huber`/`fair`로 워밍업 후 L1 미세조정, 또는 L2 모델 예측을 피처로 한 2단계 L1. 참가자 실험에서 L2→L1 전환만으로 CF MAE 0.0766→0.0737, 팀 합계 오차 13.31%→12.89%【요약, 제3자】.
- **가중치 설계:** 학습 구간엔 `train/smp.csv`(k 없음)【로컬】가 있으므로 w_train = SMP_hist(t)·k(hour). 평가 구간 SMP는 `smp.csv`로 주어지지만 **모델 입력으로 쓰지 말고 가중치/후처리 검증에만** 쓰는 것이 안전(규정 해석 불확실【미검증】). 가중치 분포【로컬 계산, 평가 구간】: 11~15시가 44.7%(시간당 8.4~9.3%), 그 외 시각 2.4~3.3%/시; SMP 0원 시각 18개(벌점 0); SMP 평균 108.0원, 최대 193.75원.
- **합산 편향(핵심):** Σ(발전소별 중앙값) ≠ 중앙값(Σ) — 반례는 계층 함수형 시계열 논문(arXiv 1710.02669)과 여행시간 논문(arXiv 1507.08444; "sum of medians is not necessarily equal to the median of the sum")에 명시【요약】. PV는 시각·날씨에 따라 분포가 비대칭(아침·저녁·부분운량 시 오른쪽/왼쪽 꼬리)이라 발전소별 L1 예측을 합치면 **집합 중앙값에서 체계적으로 벗어난다**. 해결: (1) 집합 총량을 타깃으로 한 L1 모델을 별도로 학습, (2) 발전소 합산 예측을 입력으로 한 **집합 수준 2단계 L1 보정**(시간대·계절·운량 구간별 가중 중앙값 회귀 또는 소형 LightGBM)을 OOF 예측 위에서 적합. 보정 지표는 반드시 SMP·k 가중.
- **야간 0 고정, 음수 클립, 상한(유효용량 합) 클립**은 벌점을 결코 늘리지 않는 안전한 후처리.

---

## 4. (d) 다수 발전소 집합화: 평활효과, 집합 오차의 거동, 계층 예측

### 평활(smoothing) 효과 — 왜 집합 오차는 작아지나
- Lorenz et al. (2009, IEEE JSTARS): 독일 단일 지점 하루 전 일사 rRMSE 36% → 독일 전체 13%【검증: 초록】. Lorenz 2008: 36.9% vs 13.4%(1일차)【검증: PDF】. 2007년 논문: 단일 0.13 Wh/Wp vs 독일 규모 앙상블 0.05 Wh/Wp(RMSE)【요약】.
- IEA PVPS T16: 이탈리아에서 RMSE가 **관할 면적의 제곱근에 따라 지수/쌍곡선형으로 감소**, 시장권역 평균 5.5%(설비용량 대비) → 이탈리아 전체 3.6%【검증: PDF】.
- Hoff & Perez(2009 초안/2010 *Solar Energy*): 상대 출력 변동성은 독립 시스템이면 1/√N, "밀집(crowded)" 영역(구름이 한 간격 내 여러 시스템을 덮는 경우)에선 시스템을 더 넣어도 이득 없음; 핵심 입력은 **지점 간 상관(거리·시간척도에 따라 감소)**【검증: PDF 텍스트】. 하루 전·1시간 해상도에서는 NWP 오차의 공간상관이 수십~수백 km에 이르므로 42.6 MW·253개소라도 "독립"은 아니며, 집합 오차의 대부분은 **광역 예보 오차(공통 성분)**다. 즉 집합을 더 잘게 나눠도 공통 성분은 사라지지 않는다 — 이것이 §5의 결론(쌍둥이 분할)과 맞물린다.
- 우리 데이터 공간 범위【로컬 계산】: 위도 35.06~38.09°, 경도 126.56~129.39°(제주 없음, 남한 중남부 육지 ≈ 남북 330 km × 동서 250 km), A사 관측지점 61개·B사 73개(중앙값 거리 6.9 km/5.0 km).

### 집합 우선(aggregate-first) vs 상향식(bottom-up) vs 조정(reconciliation)
- IEA PVPS T16의 업스케일링 벤치마크는 **모두 지역 총량 직접 예측**(가상 발전소)【검증】. Visser 2019/2022는 시스템별 모델 후 합산과 집합 수준 모두 다뤘고 집합화 이득을 확인【검증: 초록】. MSTL-TFT(arXiv 2301.05911) 검색 요약은 "발전소별 예측 합산이 직접 예측보다 손실이 낮았다"고 했으나 초록에서 확인 불가【미검증】.
- Yang et al. (2017, *Solar Energy* 146:276–286 "Reconciling solar forecasts: Geographical hierarchy")는 캘리포니아 모의 PV 계층에 지리적 조정 적용; 후속 Di Fonzo & Girolimetto(2023, *Solar Energy* 251)는 순차 조정의 비음·일관성 문제를 지적하고 **시공간 동시 조정이 모든 계층 수준에서 개선**(NWP 3TIER 대비 nRMSE 4.7~18.4% 개선)【요약; Yang 2017 초록은 API에서 비공개라 수치 미확인】. 순수 계층 분석 문헌: 하향식은 편향 유발 가능(Hyndman 2011), MinT는 공분산 오추정 시 악화 가능【요약: arXiv 2012.03854】.
- Montero-Manso & Hyndman(2021, *IJF*; arXiv 2008.00444): **전역(풀링) 모델은 국소 모델보다 제약이 더 크지 않으며**, 선형 전역 모델이 국소 대비 2자릿수 적은 파라미터로 경쟁력 있는 정확도; 전역 모델은 더 긴 메모리/복잡도를 감당【검증: 초록】 → 253개소를 `site_id` 범주형 + 용량·위치 피처로 **하나의 풀링 GBDT**로 학습하는 것이 표준(기준선도 그렇게 함【로컬】; 48개소는 2024-06부터만 데이터【요약, 제3자】라 풀링이 특히 중요).
- **권장:** 2개 집합·단일 계층이라 MinT류 정식 조정은 과하다. 대신 (i) 풀링 발전소 모델 합산, (ii) 집합 총량 직접 L1 모델(피처: 집합 내 용량가중 운량·UV·청천GHI 평균, 지점별 분산 등), (iii) 둘의 **집합 수준 홀드아웃 블렌딩**(가중치는 SMP·k 가중 MAE 최소화로, 비음 제약). 이것이 사실상 "L1 목적에 맞춘 2수준 조정"이다. 참가자 실험에서 GBDT–NN 오차 상관 0.82~0.88, 50:50 앙상블로 팀 합계 오차 12.89%→11.88%(−7.8%)【요약, 제3자】 — 모델 다양성(GBDT+NN, 발전소 수준+집합 수준, 제공사 A 중심+B 중심)이 가장 싼 개선책.

---

## 5. (e) 이 목적함수의 구조: 두 집합 오차는 "같은 방향"이어야 한다 (유도·검증)

**설정.** 시각 t의 집합 오차 e₁(t)=f₁−y₁, e₂(t)=f₂−y₂. 벌점 P = Σ_t w(t)(|e₁|+|e₂|), w = SMP·k ≥ 0.

**부등식.** 삼각부등식으로 |e₁|+|e₂| ≥ |e₁+e₂| 이며, 등호는 e₁·e₂ ≥ 0(같은 부호이거나 하나가 0)일 때만 성립. 초과분은 정확히
  |e₁|+|e₂| − |e₁+e₂| = 2·min(|e₁|,|e₂|)·𝟙[sign e₁ ≠ sign e₂].

**함의 1 (하한).** 발전소별 예측을 합산해 집합 예측을 만들면 e₁+e₂ = e_total은 **분할과 무관**하다. 따라서 P ≥ Σ w|e_total| =: P_min("한 팀 하한"). 분할이 할 수 있는 일은 **부호가 어긋나는 시각(특히 w가 큰 11~15시)을 줄이는 것뿐**이다.

**함의 2 (최적 구성 = 쌍둥이).** 초과분이 0이 되는 충분조건은 모든 t에서 e₁(t)=e₂(t)·c (c>0), 가장 자연스럽게 e₁ ≈ e₂ ≈ e_total/2. 즉 두 집합이 **같은 날씨에 같은 방식으로 틀리도록** — 지역·기상지점·용량대·설치 유형·데이터 보유기간 분포가 **서로 닮은 두 반쪽**(stratified interleaved split, "twin portfolios"). 금융의 분산투자 직관(서로 다른 것을 묶어 변동을 상쇄)은 **집합 내부**에서만 유효하고(각 집합을 내부적으로는 최대한 다양하게), **집합 사이**에서는 정반대다: 상쇄는 같은 집합 안에서만 일어나고, 집합을 넘어서는 상쇄(netting)는 정산식에 없다.

**함의 3 (지역 분할이 이중으로 나쁜 이유).** (i) 집합 간: 동/서가 서로 다른 날씨를 겪으면 부호 불일치 빈도↑ → 초과분↑. (ii) 집합 내: 각 집합의 공간 다양성이 줄어 |e_g| 자체가 커진다(평활효과 감소, §4). 쌍둥이 분할은 둘 다 최선.

**경험적 확인【요약, 제3자 참가자 README】:** 하한 대비 동서 분할 +7.9%, 남북 +11.8%, 참조 A/B +2.2%, 무작위 섞기 +1.6%, OOS 최적화 +1.3%; 섞기만 해도 두 집합 오차 상관 0.93. → 최적화 여지는 작다(1.6%→1.3%). **과최적화 금지**: 과거 오차로 조합을 짜면 평가 연도에 일반화되지 않을 수 있으니, 층화 교대 배정 + 가벼운 탐욕 스왑(연도별 OOS 검증)으로 충분.

**제약.** 각 집합 ≥20,000 kW【로컬 README】; 총 42,655.4 kW이므로 가능한 범위는 20,000~22,655.4 kW(거의 반반). 참조 구성은 A 134개소 20,465.7 kW / B 119개소 22,189.7 kW【로컬 계산】. 20 MW 기준은 KPX 재생에너지 발전량 예측제도의 집합자원 참여 요건(20 MW 초과)과 일치【요약; 공식 규칙 원문 미확인】.

**집합 수준 모델을 쓸 때의 보정.** 집합 총량 직접 모델을 쓰면 e₁+e₂가 분할에 약하게 의존하지만, 두 집합이 쌍둥이면 두 모델의 입력 분포가 같아 오차도 같은 방향으로 움직이므로 결론은 유지된다(추론). 추가로 **두 집합에 같은 모델/같은 시드/같은 후처리**를 쓰면 부호 일치도가 더 올라간다.

**문헌.** "VPP를 두 입찰 단위로 쪼개는 최적 분할" 자체를 다룬 논문은 찾지 못했다【미검증】. 인접 문헌: 재생 사업자 연합 형성(arXiv 1502.00679: 가장 큰 연합이 유리), 포트폴리오 효과로 불균형 비용 감소(RTU 발틱 연구; Pexapark: "자산 불균형과 계통 불균형의 상관이 양일수록 수익에 불리"), smartPulse: "발전소 수준 최적 예측이 포트폴리오 수준 최적은 아니다"【요약】. 이들은 모두 "집합 내부 상쇄"를 말하며 본 유도와 모순되지 않는다.

**간단 수치 예(검산용).** e_total=−10 인 시각에 (e₁,e₂)=(−5,−5) → 벌점 10; (−8,−2) → 10; (−12,+2) → 14; (+5,−15) → 20. 분할이 바꿀 수 있는 것은 뒤의 두 경우를 앞의 두 경우로 옮기는 것뿐.

---

## 6. (f) 결측·중도절단 발전량, 출력제어·클리핑, 적설·오염, 열화

- **결측【로컬 README】:** `generation.parquet`는 행이 없는 (site, ts)가 결측이고 NaN은 없음; 설비 편입 전·통신·수집 지연으로 빈 시각 존재; 발전소마다 행 수 다름. → 학습 시 **결측 타깃은 제외**(0으로 채우면 중앙값이 아래로 끌림). 평가 시 결측 실적 처리 방식은 문제정의서 확인 필요【미검증】.
- **클리핑/포화/출력제어 탐지:** pvanalytics `features.clipping.threshold`(일중 시각별 99.5% 분위 곡선 대비 평탄·고출력 1시간↑ 구간)와 `clipping.geometric`(예제에서 정확도 99.2%), NREL PV Validation Hub는 논리 기반 + XGBoost로 클리핑·출력제어 마스크 검증【검증: 문서/요약】. 시간 해상도 1h에서는 민감도가 떨어지므로 "맑은 날(양사 운량 낮음·UV 높음)인데 11~15시 출력이 유효용량 대비 비정상 평탄/저하"인 날을 플래그하는 규칙이 현실적.
- **한국 출력제어 현황:** 제주는 2024년 56일(풍력+태양광 51회 등)【요약: KPX 2024 제주 운영실적】; 육지는 2024년 26~27회 → 2025년 10월까지 56회로 급증, 호남권 중심【요약: haezoom 블로그/전기신문】. 육지 제어 대상은 사실상 **500 kW 이상** 사업자 중심(선별적)【요약: 전기신문 2026】. 우리 데이터【로컬 계산】: 제주 발전소 0개, ≥500 kW 18개소(용량의 37.1%), ≥1 MW 2개소(6.2%), 중앙값 99.4 kW. → 대부분 소규모라 출력제어 노출은 제한적이지만, 용량 상위 18개소는 봄·가을 맑은 휴일 정오(k=3 시간대!)에 제어 가능성이 있으므로 학습 데이터에서 의심 구간을 **가중치 0 또는 제외**. 평가 연도의 제어는 예측 불가 → 중앙값 관점에서 제어 확률이 50% 미만인 시각이면 무시하는 것이 최적(추론).
- **적설:** 2022년 12월 폭설일 국내 태양광 최대 발전량이 설비의 1/10 수준이었다는 보도, 동서발전 보고서는 목포·전주·안동·홍성 4개소의 적설 일조 손실을 연 477.63시간으로 추산(가정 많음)【요약: 세계일보 2026-04】. pvlib `snow.loss_townsend`(월 단위)·pvanalytics "Quantifying the effects of snow cover" 예제 존재【검증: 문서 목록】. 실무: B사 `wb_snow`(cm)·`wb_snow_prob`, A사 `wa_snow`로 **최근 24/48/72h 누적 강설 × 기온<0 지속시간** 피처를 만들면 트리가 "눈 덮임 지속" 패턴을 학습한다(이 피처가 유효한지는 데이터로 확인【미검증】). 한국은 적설 후 수일 내 녹는 경우가 많아 이벤트가 드물지만 발생 시 오차가 크고, 1~2월 SMP가 높은 시기라 가중치도 크다.
- **오염(soiling):** IEA PVPS T13-21(2022, 한국어 번역본 존재) 일반론(강우로 세정, 건기 누적 0.1~0.3%/일)【요약】; 한국 황사·미세먼지의 정량 손실 연구는 찾지 못함【미검증】. 하루 전 예측 오차(10%대) 대비 작아 우선순위 낮음; 봄철 `doy`·최근 무강우 일수 피처로 간접 흡수.
- **열화:** Jordan & Kurtz(2013, *Prog. Photovolt.*) 약 2,000개 보고치 중앙값 0.5%/년(평균 0.8%/년; 후속 메타분석 0.9%/년)【검증: 초록/NREL 자료】. 한국 KEPRI 50 kWp(1999~) 사례는 연 2.8%p 감소 보고이나 일사 변동 등과 혼재된 오래된 자료【요약】. 1년 평가에서 열화는 0.5~1% 수준의 **체계적 하향**이라 무시해도 되진 않는다 → 발전소별 "데이터 시작 후 경과월", 최근 1년 가중, 유효용량 재추정으로 흡수. 용량 변경(증설·인버터 고장)은 pvanalytics "Data Shift Detection"(변화점)로 탐지【검증: 문서 목록】.
- **실측 기상 이상치【로컬 README】:** `wb_cloud`>100(433건), `wb_uv_idx`>15(394), `wa_wind_speed` 9999 등 — 실측을 피처/증강에 쓰기 전 클립.

---

## 7. (g) GBDT 실무: 가중치, 시계열 CV, 조기종료, 운량 vs 일사 프록시 중요도

- **표본가중치:** `sample_weight = SMP_hist(t)·k(hour)`(§3). 야간(고도≤0)은 학습에서 제외하고 0 고정(기준선 방식【로컬】). 가중치는 마지막 단계에 추가하고 비가중 L1과 비교해 득실 확인(참가자 권고【요약】).
- **검증 설계:** 시간 블록 CV(예: 2022, 2023, 2024-06~2025-05 롤링; `TimeSeriesSplit(gap=…)`【검증: sklearn 문서】). Bergmeir & Benítez(2012)는 블록 CV를 시계열 표준으로 권고【요약】. **무작위 행 분할은 26% 낙관**(참가자 실험: 행 분할 MAE 0.0565 vs 시간 분할 0.0766 vs 날 분할 0.0738)【요약, 제3자】. 평가 지표는 반드시 **집합 합계의 SMP·k 가중 MAE**를 커스텀 `feval`로 구현(행 단위 MAE 최적 ≠ 집합 최적). 조기종료용 폴드와 앙상블 가중치용 폴드를 분리(중첩), 시드 ≥3 평균(동일 설정 NN도 시드로 최대 0.23 kWh 차이【요약】).
- **학습 기간:** 기준선은 최근 2년만 사용【로컬】. 예보 제공사의 모델이 바뀌면 오래된 예보-실적 관계가 어긋날 수 있으므로, 전체 기간 vs 최근 2년 vs 시간 감쇠 가중을 CV로 비교(참가자: "조기종료+전체 데이터"가 NN 14.08→13.00 개선【요약】).
- **피처(일사 미제공 조건):** 태양기하(고도·방위·cosZ·`doy` sin/cos·시각), 청천 GHI(pvlib), 운량 A·B(+평균·차·절대차), 프록시 일사 2~3종(§2), UV지수와 청천대비 비, 운고(`wb_ceiling` 낮음=두꺼운 하층운), 시정·이슬점차(안개), 강수확률·강수량, 적설 누적, 기온(모듈 효율), 풍속, 기압, round10/round17 차, 관측지점 ID·발전소 ID(범주형), 용량, 위경도(비식별 좌표 그대로), 발전소별 최근 N일 CF 평균(예측시점 17:00 이전 데이터만 — 평가 구간엔 실적이 없으므로 **사용 불가**, 학습 시에도 넣지 말 것). 참가자 NN에선 수작업 피처가 효과 없었다【요약】 — GBDT에선 다를 수 있으니 ablation 필수.
- **중요도 증거:** 하루 전·NWP 입력·운량만 주어진 트리 모델의 SHAP 문헌은 찾지 못함【미검증】. 간접 증거: 일사형 변수(청천지수·GHI)가 있으면 SHAP의 90%+를 차지(arXiv 2607.12954)【요약】; GHI 예측에서 청천 변수가 지배적(리야드 XGB/LGBM 연구)【요약】; 한국 연구는 "예보 요소로 일사·일조를 먼저 추정한 뒤 발전량을 예측하는 2단계가 직접 예측보다 우수"【요약: KCI ART002302286】. 즉 **청천 GHI × 운량 프록시가 최상위 피처가 될 가능성이 높고**, 운량 원값은 그 다음. 메타분석(arXiv 2111.02092, 180편)은 "NWP 변수 포함, 정규화, 리샘플링"이 가장 효과적인 전처리이고 하이브리드 모델이 일관되게 우세하다고 보고【검증: 초록】.
- **하이퍼파라미터 출발점(기준선 기반, 권장 변경):** 기준선 L2·600트리·lr 0.06·127잎·min_child 200【로컬】 → L1, lr 0.02~0.03, 트리 2,000~5,000 + 조기종료, `min_data_in_leaf` 100~300, `feature_fraction` 0.7~0.8, `bagging` 0.8, `monotone_constraints`(운량 −, 청천GHI +), `cat_smooth`로 `site_id` 범주형. CatBoost는 `loss_function='MAE'`/`Quantile:alpha=0.5` + `sample_weight`로 동일 구성 가능(순서형 부스팅이 범주형 ID에 유리할 수 있음 — 미확인).
- **제출 운영:** 하루 3회·총 20회【로컬 README/요약】. 기준선 먼저 제출해 포맷 확인 → 한 번에 한 가지만 바꿔 효과 측정 → 공개 리더보드에 맞춰 튜닝하지 말 것(상위 7팀 발표평가 대비 재현 가능한 로그 유지).

---

## 8. 권장 실험 순서(최소 비용 → 최대 효과)

1. 데이터 QA: 결측 지도, 유효용량, 클리핑/제어 플래그, 실측 이상치 클립.
2. 기준선 재현 → L1 + SMP·k 가중 → 집합 합계 가중 MAE `feval`로 조기종료(연도 롤링 CV).
3. 피처: 청천 GHI·프록시·UV비·운고·적설 누적·양 라운드 동시 입력. ablation.
4. 집합 총량 직접 L1 모델 + 발전소 합산 모델의 집합 수준 블렌딩/2단계 보정.
5. 모델 다양성: NN(발전소 임베딩, L1, 노이즈 주입)·CatBoost 추가 → 홀드아웃 가중 블렌딩, 시드 평균.
6. 구성: 층화(관측지점·용량대·데이터 시작월) 교대 배정 → 연도별 OOS로 탐욕 스왑 1~2회 → 두 집합에 동일 파이프라인.
7. 후처리: 야간 0, 음수·상한 클립, SMP=0 시각은 무관.

---

## Sources (URL)

**경진대회·데이터**
- 참가자 폴더 `README.md`, `baseline.py`, `sites.csv`, `smp.csv` (로컬, 2026-10-26 확인)
- ruby9915/OIBC (2026 참가자 작업 공간; 제3자 실험치) — https://github.com/ruby9915/OIBC , https://raw.githubusercontent.com/ruby9915/OIBC/main/README.md
- 2026 POSTECH OIBC 빅데이터 경진대회 공고(all-con) — https://www.all-con.co.kr/view/contest/543104
- 과거 대회 기사: 머니투데이 2022 — https://www.mt.co.kr/industry/2022/12/08/2022120813504263708 ; 국토일보 2023 — https://www.ikld.kr/news/articleView.html?idxno=285654 ; 인더스트리뉴스 2023 — https://www.industrynews.co.kr/news/articleView.html?idxno=51733
- 재생에너지 발전량 예측제도(20 MW 집합자원) — https://blog.haezoom.com/insight_vpp_19/ ; https://kidd.co.kr/news/218609 ; http://www.epj.co.kr/news/articleView.html?idxno=30565

**(a) 다중 NWP·지역 예측**
- Pierro et al. 2016, Multi-Model Ensemble for day ahead prediction of PV power — https://ambiente.sostenibilita.enea.it/pubs/2344 ; https://art.torvergata.it/handle/2108/155469
- IEA PVPS T16-01:2020 Regional solar power forecasting (요약본) — https://iea-pvps.org/wp-content/uploads/2020/07/IEA_PVPS_T16_regional_forecasts_summary.pdf
- Li et al. 2016, ML approach for regional PV forecasting — https://researchconnect.stonybrook.edu/en/publications/a-machine-learning-approach-for-regional-photovoltaic-power-forec/
- Visser, AlSkaif, van Sark 2019 (PVSC) — https://research-portal.uu.nl/en/publications/benchmark-analysis-of-day-ahead-solar-power-forecasting-technique/
- Visser, AlSkaif, van Sark 2022 (Renewable Energy 183) — https://research-portal.uu.nl/en/publications/operational-day-ahead-solar-power-forecasting-for-aggregated-pv-s/ ; https://ideas.repec.org/a/eee/renene/v183y2022icp267-282.html
- Lorenz et al. 2008 (EU PVSEC) ensemble power forecast — https://52.iea-shc.org/Data/Sites/1/publications/23rd_EU_PVSEC_5AO.8.6_lorenz.pdf
- Lorenz et al. 2009 (IEEE JSTARS) — https://www.pure.fo/en/publications/irradiance-forecasting-for-the-power-prediction-of-grid-connected/
- Weather forecasting error in solar energy forecasting (arXiv 1709.08135) — https://arxiv.org/pdf/1709.08135
- Robustness of DL models under NWP errors (arXiv 2607.12954) — https://arxiv.org/abs/2607.12954
- ASHRAE GEPIII lessons (arXiv 2202.02898) — https://arxiv.org/abs/2202.02898
- Meta-analysis "What drives the accuracy of PV output forecasts?" (arXiv 2111.02092) — https://arxiv.org/abs/2111.02092
- Short-term solar forecasting review (UC3M) — https://e-archivo.uc3m.es/bitstream/10016/30150/2/shrot-term_SE_2020_ps.pdf

**(b) 청천·정규화·pvlib**
- pvlib clearsky reference — https://pvlib-python.readthedocs.io/en/stable/reference/clearsky.html
- pvlib forecast.py v0.9.5 (cloud→irradiance 식) — https://raw.githubusercontent.com/pvlib/pvlib-python/v0.9.5/pvlib/forecast.py
- pvlib.irradiance.campbell_norman — https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.irradiance.campbell_norman.html
- pvlib GFS.cloud_cover_to_irradiance (deprecated 안내) — https://pvlib-python.readthedocs.io/en/v0.9.1/reference/generated/pvlib.forecast.GFS.cloud_cover_to_irradiance.html
- Clear-sky index vs clearness index (HAL) — https://hal.univ-reunion.fr/hal-03964785v1
- Clear-sky normalization (SciTePress 2018) — https://www.scitepress.org/Papers/2018/68608/68608.pdf
- Clear sky performance index (unibz) — https://bia.unibz.it/esploro/outputs/journalArticle/Deterministic-and-stochastic-approaches-for-day/991005772807601241
- AI pipeline day-ahead PV (arXiv 2608.02088) — https://arxiv.org/pdf/2608.02088
- Kasten–Czeplak 검증(캐나다) — https://library.csbe-scgab.ca/docs/meetings/2017/CSBE17057.pdf ; https://doaj.org/article/271779d6044846f088941a181cf331b6
- UV vs GHI 구름 감쇠(한국 4개소) — https://www2.mdpi.com/1996-1073/13/6/1504

**(c) L1/가중 중앙값/LightGBM**
- Gneiting 2011 Making and Evaluating Point Forecasts — https://arxiv.org/abs/0912.0902 ; 슬라이드 — https://bundesbank.de/resource/blob/635740/f4d2bdedb156aeec8a97768c803f842f/472B63F073F071307366337C94F8C870/2012-06-01-eltville-11-gneiting-presentation-data.pdf
- LightGBM Parameters — https://lightgbm.readthedocs.io/en/stable/Parameters.html
- LightGBM regression_objective.hpp (가중 백분위 잎 값) — https://raw.githubusercontent.com/microsoft/LightGBM/master/src/objective/regression_objective.hpp
- Weighted median 정의 — https://en.wikipedia.org/wiki/Weighted_median
- Sum of medians ≠ median of sum — https://arxiv.org/pdf/1710.02669 ; https://arxiv.org/pdf/1507.08444

**(d) 평활효과·계층 예측**
- Hoff & Perez, Quantifying PV power output variability — https://www.cleanpower.com/wp-content/uploads/2012/02/081_QuantifyingPVPowerOutputVariability.pdf ; Modeling PV fleet output variability — https://www.cleanpower.com/wp-content/uploads/2012/02/071_ModelingPVFleetOutputVariability.pdf
- Input smoothing effect (Renewable Energy 2022) — https://art.torvergata.it/retrieve/e291c0da-0e95-cddb-e053-3a05fe0aa144/1-s2.0-S0960148122003184-main.pdf
- Yang et al. 2017 Reconciling solar forecasts: Geographical hierarchy (DOI 10.1016/j.solener.2017.02.010) — https://api.crossref.org/works/10.1016/j.solener.2017.02.010
- Di Fonzo & Girolimetto 2023 spatio-temporal reconciliation (Solar Energy 251) — https://www.research.unipd.it/handle/11577/3465343
- Cross-temporal reconciliation (arXiv 2209.07146) — https://arxiv.org/pdf/2209.07146
- Forecasting: theory and practice (arXiv 2012.03854) — https://arxiv.org/pdf/2012.03854
- Montero-Manso & Hyndman, Locality and Globality (arXiv 2008.00444) — https://arxiv.org/abs/2008.00444
- MSTL-TFT (arXiv 2301.05911) — https://arxiv.org/abs/2301.05911

**(e) 포트폴리오·불균형 비용(인접 문헌)**
- Coalition formation of renewable producers (arXiv 1502.00679) — https://arxiv.org/pdf/1502.00679
- RTU, Forecasting accuracy and portfolio effect on imbalance costs — https://ortus.rtu.lv/science/en/publications/41465
- Pexapark imbalance costs — https://help.platform.pexapark.com/en/articles/11172380-imbalance-costs
- smartPulse wind portfolio case — https://www.smartpulse.io/case-study-on-the-use-of-ensemble-method-combinations-in-wind-portfolio-management/

**(f) 데이터 품질·출력제어·적설·열화**
- pvanalytics gallery — https://pvanalytics.readthedocs.io/en/stable/generated/gallery/index.html ; clipping.threshold — https://pvanalytics.readthedocs.io/en/stable/generated/pvanalytics.features.clipping.threshold.html
- NREL PV Validation Hub — https://nrel.gov/docs/fy24osti/87931.pdf
- pvlib snow.loss_townsend — https://pvlib-python.readthedocs.io/en/v0.9.5/reference/generated/pvlib.snow.loss_townsend.html
- KPX 2024 제주 전력계통 운영실적 — https://www.kpx.or.kr/boardDownload.es?bid=0159&list_no=74566&seq=1
- 육지 출력제어 추이(haezoom) — https://blog.haezoom.com/insight_vpp_34/ ; 전기신문 — https://www.electimes.com/news/articleView.html?idxno=353235 ; 500 kW 이상 중심 보도 — https://m.news.nate.com/view/20260513n32610 ; 1 MW 의무화 — http://www.e2news.com/news/articleView.html?idxno=222051
- 폭설 태양광 손실 보도(세계일보 2026-04) — https://v.daum.net/v/20260405185903246
- 적설 제설 모듈 연구(CPR 2016) — https://www.koreascience.or.kr/article/JAKO201608259723492.pdf
- IEA PVPS T13-21 오염 손실(한국어) — https://iea-pvps.org/wp-content/uploads/2023/01/Korean-Translation-Report-IEA-PVPS-T13-21_2022-Soiling-Losses.pdf
- Jordan & Kurtz 2013 degradation review — https://research-hub.nrel.gov/en/publications/photovoltaic-degradation-rates-an-analytical-review-2/ ; https://www.nrel.gov/docs/fy13osti/56690.pdf
- KEPRI 장기운전 성능(한국) — https://koreascience.or.kr/article/JAKO201121641921152.pdf

**(g) 검증·피처 중요도**
- sklearn TimeSeriesSplit — https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html
- Bergmeir & Benítez 2012 — https://research.monash.edu/en/publications/on-the-use-of-cross-validation-for-time-series-predictor-evaluati/ ; Bergmeir, Hyndman, Koo 2018 — https://bridges.monash.edu/articles/journal_contribution/A_Note_on_the_Validity_of_Cross-Validation_for_Evaluating_Time_Series_Prediction/21521274/1
- 일기예보+예측 일사로 PV 예측(한국, 2단계) — https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART002302286
- SHAP 기반 피처 선택(한국, 2020) — https://scholarworks.bwise.kr/ssu/handle/2018.sw.ssu/39908
- 기상청 1 km 재생에너지 기상자료 기사 — https://www.industrynews.co.kr/news/articleView.html?idxno=86720
