# 2026 POSTECH OIBC 빅데이터 챌린지 — 통합 리서치 메모

작성일: 2026-10-26. 통합 대상: R1(공식 규칙), R2(역대 수상팀·경쟁자), R3(방법론 SOTA), R4(한국 시장·기상), R5(갭 보완) + 로컬 데이터 분석 3건(`smp_weights_report.md`, `spatial_corr_report.md`, `gen_quality_report.md`).

**근거 등급 표기**
- **[A]** 공식 1차 자료(dataen.ai 규정·공지, 배포 README/baseline.py, KPX 공고)
- **[B]** 공고 전재·보도
- **[C]** 2차 설명회 녹취(참가자 공개 전사) 또는 참가자·수상팀 저장소 자가보고
- **[로컬]** 참가자 폴더 데이터로 직접 계산한 값
- **[추정]** 추론·미확인

---

## 1. 공식 규정 요약 — 확정 vs 미확인

### 1.1 확정 사항 [A]

| 항목 | 내용 |
|---|---|
| 과제 | 253개소(합계 42,655.4 kW)를 G1·G2에 배정(각 집합 용량 ≥ 20,000 kW, 전부 정확히 한 집합, 한 제출 안에서 1년 고정) + 집합별 시간별 kWh 하루 전 예측 |
| 점수식 | `S = Σ SMP(t)·실적(t) − 0.10 × Σ SMP(t)·k(t)·|예측(t)−실적(t)|`, k=3 (ts 시각 11~15), 그 외 1 (README 원문) |
| 순위 | S 내림차순. 규정 탭: "실질적으로는 페널티(W)를 최소화하는 경쟁", "리더보드에는 S(원)가 표시" |
| 채점 시각 | `smp.csv` 8,760행 (2025-06-01 01:00 ~ 2026-06-01 00:00 KST, **우측닫힘**) 전부. 야간도 채점 |
| 예측시점 | 대상일 전일 17:00 KST. round 10·17 예보 모두 사용 가능(둘 다 17시 이전 발행) |
| 제출 파일 | `composition.csv` 헤더 포함 254행(`site_id,group`, G1/G2) / `forecast.csv` 헤더 포함 17,521행(`group,ts,forecast_kwh`, ts 타임존 필수, 값 ≥ 0) |
| 제출 횟수 | 일 3회, 대회 기간 총 20회 |
| 대회 기간 | 2026-11-02(월) 10:00 ~ 11-13(금) (설명회: 13일 23:59:59 마감 [C]) |
| 최종 순위 | 리더보드 상위 7팀 → 코드(전처리~추론 전 과정)·발표자료 11/23(월)까지 competition@dershare.xyz → 온라인 발표 11/23~27 중 하루 → 최종 순위 |
| 시상 | 대상 1팀 500만 / 최우수 2팀(대학생·대학원생 각 1) 200만 / 우수 4팀 100만 / 장려 10팀 40만 (총 17팀). 시상식 12/04 부산 BPEX |
| 금지 | 외부 데이터 사용 금지 **"이에 따라 외부 데이터로 학습된 모델은 사용할 수 없습니다"** / 예측시점 이후 생성 정보(평가구간 실측·실적) 사용 금지 / 계정 중복·팀 간 담합(유사도 초과 시 소명, 실패 시 실격) / 좌표로 발전소·사업자 특정(실격) |
| 데이터 | 평가구간 A사 예보 결손 264행(0.0247%) — **결손 시각도 채점 대상**, 통째 제외 불가 / 좌표 ≤2 km 이동·4자리 반올림 / 다운로드 최초 1회 |
| 허용 언어 | Python, R |
| 공지 현황 | 2026 관련 공지 3건(10/02 휴학생, 10/02 자격검증, 10/06 문의창구). **10/06 이후 신규 공지 없음(10/26 라이브)** |

### 1.2 설명회 발언으로만 확인된 사항 [C] (2차 온라인 설명회 2026-10-13, ruby9915 전사)
- 문제정의서 = README와 "거의 동일". `scoring.py`·문제정의서는 **원래 배포 목록에 없음**(제3자 starter 미러로 재확인 [A]). 채점은 서버에서, 코드 비공개.
- 제출마다 채점, **팀 최고점 유지**. 형식 오류(타임존 누락 등)도 1회 차감.
- "8,760시간이 전부 채점" → public/private 분할 언급 없음.
- 페널티는 G1, G2 **각각의 집합 합계 오차 절댓값**을 더함.
- 한 제출 안에서 구성 고정, **다음 제출에서는 구성 변경 가능**. `current_group`은 "랜덤 배정이지 최적이 아님".
- 허용: 평가구간 SMP·k를 학습 가중치로 사용 / 학습구간 실측기상으로 예보오차 분석 / 청천·태양고도 수식 피처 / 학습기간 고정값 후처리 / 생성형 AI 코드 작성.
- 긴장 관계: "파운데이션 모델·딥러닝 계열도 큰 무리 없음"(설명회) vs "외부 데이터로 학습된 모델 사용 불가"(공식 규정 탭). → **서면 확인 전까지 제공 데이터로만 학습한 모델 사용**이 안전.
- 수상 취소 사유: 평가기간 실제 실적 조회("스코어링 상에서도 드러남"), 데이터를 외부 API·생성형 AI 서비스·공유 저장소에 업로드. 자체 서버는 가능하되 종료 후 30일 내 폐기.
- 평가 요소 언급: "이상치·결측 처리 방식이 가장 중요한 요소", 전략 논리성, 실험 기록. "리더보드 2~3등도 발표로 대상 가능", "장려상까지 코드 제출 요구 가능".
- 10/13 기준 약 260팀 이상 접수.

### 1.3 미확인 사항 (1:1 문의 권장, 우선순위 순)
1. **리더보드 범위**: 8,760시간 전체 S 단일 값인지, public/private 분할인지. 공식 문구는 "S(원) 표시"뿐. 2024 선례는 "대회 기간 누적 → 상위 7팀 순위별 공지" [A].
2. **발표 배점**: 2026 미공개. 선례 2022·2023·2025 모두 정확도 50 / 창의성 30 / 발표 20 [B]. 2024는 상위 7팀을 리더보드 순위 공개 상태로 3시간(팀당 ~25분) 발표 [A].
3. **동점 처리·무효 제출 정본**: 어디에도 없음(공지 16건·FAQ 5건·규정 탭·참가자 저장소 6곳 전수 확인 [A]). S가 원 단위 소수까지 계산되므로 실무 영향은 낮음.
4. 리더보드 표시 항목 상충: 규정 탭 "S만" vs 공고 전재본 "S·W·절대오차·정규화 점수" [A/B]. 정규화 점수 산식 미공개.
5. 평가구간 SMP를 **입력 피처**로 쓰는 것(가중치 용도만 허용 확인).
6. 결측 실적 시각의 채점 처리(0 처리 vs 제외). 통제 불가.
7. 유사도(담합) 기준값. baseline 그대로 반복 제출은 다수 팀과 유사할 위험.

---

## 2. 채점식의 수학적 함의

### 2.1 무엇이 점수를 가르는가
- 수익항 Σ SMP·실적은 253개소 전부의 실적 합이라 **모든 참가자에게 동일** → 순위는 **페널티 W = 0.10·Σ SMP·k·(|e_G1|+|e_G2|)** 만으로 결정 [A, 규정 탭 명시].
- 판돈 규모 [로컬, `smp_weights`]: 기후학적 발전 58.81 GWh, 수익항 약 66.25억 원(추정). 가중 MAE 10%면 페널티 1.51억(수익의 2.3%), 15%면 2.27억. **가중 MAE 1%p = 연 1,511만 원**, 12.5% 수준에서 상대 1% 개선 = 189만 원. 즉 S의 95% 이상은 공통이고 순위는 ~2% 스케일 안에서 갈린다.
- 2025 대회 선례: 1~7위 MAE 격차 2.9% [C, 재시도 발표자료 18p]. AMS 2013-14도 상위 7팀이 1위의 95% 부트스트랩 CI 안 [B]. **상위권은 박빙이며 미세 차이는 운**이 섞인다.

### 2.2 시간·계절 집중 [로컬]
| 지표 | 11~15시(k=3) 비중 |
|---|---|
| Σ SMP·k (가중치 합) | **44.7%** (주간 6~20시 기준 59.6%) |
| 포트폴리오 kWh | 65.5% |
| 실질 노출 w×kWh_clim | **84.2%** (12·13·14시 3개 시각만으로 52.6%) |
| 설명회 "기준선 페널티의 81~82%" [C] | 로컬 84.2%와 정합 |

- **우측닫힘 함정**: ts 11:00~15:00 = 실제 10:00~15:00 구간. 제출 ts 표기 기준으로 k가 붙으므로 시프트 실수 금지.
- 월별 노출: 6월 11.2%, 8월 10.9%, 4월 10.5%, 5월 10.4% (4개월 43%) vs 11~1월 각 5.5~5.9%. **승부처 = 4~9월 평일 정오**. 6월 평일 정오 1 kWh 오차 ≈ 39원 손실(수익 1 kWh ≈ 130원의 30%).
- SMP 0원 시각 18개(전부 13시 또는 14시, 10~3월 주말·명절·맑은 날), ≤10원 26개. 이 시각들의 발전량은 연간 0.67~0.98% → **페널티 0, 예측 무의미**. ts가 공개돼 있으므로 w_t=0을 그대로 쓰면 됨.
- 1 MWh 오차의 페널티: 11~15시 평균 33,037원, 그 외 주간 11,182원.

### 2.3 최적 점예측 = (가중) 조건부 중앙값
- 절대오차 스코어 하에서 최적 점예측은 예측분포의 **중앙값**(Gneiting 2011, JASA [A]). 시각별 가중치 w(t)=SMP·k > 0은 상수 배율이라 **시각별 최적 함수형을 바꾸지 않는다**. w는 "어느 시각을 더 정확히 맞출지"의 자원 배분과 모델 선택·블렌딩 기준만 바꾼다.
- 따라서 **평균(L2)이 아니라 L1/τ=0.5 분위 손실**로 학습. LightGBM `regression_l1`은 잎 값·초기값을 (가중) 백분위 0.5로 계산함을 소스에서 확인 [A, `regression_objective.hpp`] → `objective='regression_l1'` + `sample_weight=SMP(t)·k(t)`가 목적함수의 정확한 표본 근사. 참가자 실험: L2→L1만으로 팀오차 13.31%→12.89% [C, ruby9915].
- "고가격 시각에 예측을 올리거나 내리는" 식의 조정은 근거 없음(최적해는 여전히 중앙값) [로컬 권고].
- 가중치 설계 [로컬]: 테스트 연도 (월,시) 평균 w가 테스트 w 분산의 R² 0.917을 설명(k만 쓰면 0.852, 검증연도 (월,시) 프로파일 0.885). 학습 sample_weight는 **테스트 (월,시) 평균 w**(공개 `smp.csv` 기반이라 합법) 권장. 검증 점수는 검증연도 실제 w로 계산.
- 테스트 연도 SMP 평균 108.02원은 검증연도(PV2024) 121.9원보다 11.4% 낮고, 계절성이 뒤집혔다(겨울 저가·봄여름 고가, 덕커브 깊이 9.1%로 5년 중 최대) [로컬]. 수준 차이는 순위에 무관하지만 월별 가중 배분은 다르다.

### 2.4 집합 구성(composition)의 이론
- 삼각부등식: |e₁|+|e₂| ≥ |e₁+e₂|, 등호 ⇔ e₁·e₂ ≥ 0. 초과분 = 2·min(|e₁|,|e₂|)·𝟙[부호 불일치]. 발전소별 예측을 합산하면 e₁+e₂ = e_total은 **분할과 무관** → P ≥ Σ w|e_total| ("한 팀 하한"). 분할이 할 수 있는 일은 **부호 불일치 시각(특히 w 큰 11~15시)을 줄이는 것뿐** [R3 §5 유도].
- 최적 구성 = **쌍둥이 포트폴리오(twin split)**: 두 집합이 같은 날씨에 같은 방식으로 틀리도록 지역·관측지점·용량대·데이터 보유기간을 **층화 후 교대 배정**. 금융식 "분산투자"는 집합 **내부**에서만 유효하고 집합 **사이**에서는 정반대(집합 간 상쇄는 정산식에 없음).
- 지역 분할은 이중으로 손해: (i) 집합 간 부호 불일치↑, (ii) 집합 내 공간 다양성↓로 |e_g| 자체 증가.
- **로컬 검증** [`spatial_corr`, CF 편차를 오차 대용으로]: 기준 A/B 분할 corr(E1,E2)=0.984·부호 일치 93.8% / 덴드로그램 인터리브 0.993·96.1% → 기준 대비 **−0.28%** / 북·남 분할 **+5.5%**, 서·동 +3.5%. 참가자 실험 [C, ruby9915]: 동서 +7.9%, 남북 +11.8%, 참조 +2.2%, 무작위 +1.6%, 최적화 +1.3%(하한 대비). → **구성으로 얻는 이득 ≤ 0.3%p, 잃을 수 있는 손실 3.5~12%**. 큰 실수만 피하면 되고 승부는 예측 품질.
- 평활 효과 [로컬]: 무작위 12~20개소에서 포화(0.84), 127개소 ≈ 253개소(0.824 vs 0.823). 평균 쌍 편차상관 0.654 → 유효 독립 사이트 수 ≈1.5. 남동부 전체가 거의 한 날씨 체계이므로 **어떤 구성으로도 CF 변동의 80%+는 남는다**.
- 제약 [로컬]: 각 집합 허용 범위 [20,000, 22,655.37] kW(폭 2,655 kW). 참조 A=20,465.655(134개소), B=22,189.715(119개소). **A의 하한 여유 465.655 kW** → A의 465 kW 초과 대형 11개소는 스왑으로만 이동 가능. 무작위 동전던지기의 실행가능 비율 44.7% → 용량 자동 검사 스크립트 필수.

### 2.5 합산 편향과 집합 수준 보정
- Σ(발전소별 중앙값) ≠ 중앙값(Σ) [A, arXiv 1710.02669·1507.08444]. PV 분포는 시각·날씨에 따라 비대칭이라 발전소별 L1 예측 합산은 집합 중앙값에서 체계적으로 벗어남 → **집합 총량 직접 L1 모델** 또는 **집합 수준 2단계 L1 보정(OOF 위에서)** 필수. 보정 지표는 SMP·k 가중.
- 확률 집계 SOTA [A, Moradi et al. 2025 arXiv 2502.07010, MISO 751개소]: 분위수 단순 합(Q-sum)은 구간이 코퓰라의 ~2배로 과대(90% 명목 PICP 97.2%), 독립 가정은 ~1/10로 과소(PICP 13.7%), 가우시안 코퓰라 78.2%. → 집합 분포를 만들 때 **Q-sum·독립 가정 금지**, 학습구간 OOF 잔차로 코퓰라 → 집합 시나리오 → 시각별 가중 중앙값. 2026 후속 CoCopula(arXiv 2602.02583)는 집계 후 conformal 보정.
- 안전한 후처리(벌점을 절대 늘리지 않음): 야간 0 고정, 음수 클립, 유효용량 합 상한 클립.

---

## 3. 역대 수상팀·올해 경쟁자 전략

### 3.1 심사가 보상해 온 것 [B/C]
- 배점 50/30/20(정확도/창의성/발표) — 2021·2022·2023·2025 동일. 2026 미공개.
- **감점**: 단순 평균 앙상블(2023 공고 명시), 지표 꼼수(2024 음수가격 구간 상수 입력 → 수상 제외).
- **가점 서사**: 평가지표를 손실함수로 직접 구현(2022), 물리 기반 파생 피처(2023 대기외 일사량 Q), 인접 발전소 공간정보(2025), 문제 구조 분석("그룹 구성 전략"을 공고가 핵심 설계요소로 지목, 2026).
- 발표 순위 역전 사례: 2023 폭풍대기 예선 4위 → 최종 3위 [C].

### 3.2 역대 대상팀 실제 방법 (1차 자료 기준)
| 회차 | 대상팀 | 실제 방법 | 교훈 |
|---|---|---|---|
| 2022(4회) | POSTECH Sun Capturer [C, 발표 PDF+코드] | 비인과 WaveNet(μ,σ 출력), **대회 지표를 미분가능 손실로 구현**, 이용률 정규화로 21개소 단일 모델, 시간순 홀드아웃, 구간 k=0.01로 거의 점예측 | 지표-손실 정렬이 핵심. 전 변수 투입 > 선별 |
| 2023(5회) | 경북대 김최신이 [C, 노트북] | 5종 예측+기상을 피처로 한 **단일 XGBoost**(8,000 trees, lr 0.01), 무작위 80/20 분할, 예측 ×1.03 스케일 | 모델은 평범. "학습된 비선형 결합"으로 창의성 요건 충족 + 리더보드 1위 |
| 2025(7회) | 성균관대·KAIST 재시도 [C, 노트북+슬라이드 22장] | **ML 아님**: 선형보간 이상치 탐지 → K-NN Nadaraya–Watson 커널 회귀(k=55, p=2, 탐욕적 순서) → 시간 평활(1,3,6,7,6,3,1)/27 → 물리 제약(0~1,300). **LOGO-CV**(검증 39 → 대회 44.51). 1~7위 격차 2.9% | "시스템의 구조를 읽어, 단순함으로 답하다". 데이터 분석 4장(완결성·외생변수·공간·시공간)이 발표의 핵심 |
| 2025 2위 | CHIDIES [C] | LightGBM 베이스라인 → 보간 → 물리 감쇠 → NN → IDW → 앙상블 | 2위도 IDW+물리 |
| 2025 ~7위 | qewr1234 [C] | LightGBM Tweedie 20,000 trees, GroupSplit 홀드아웃 34.05 → 대회 45.77 (낙관 11.7) | 트리 모델은 그룹 분할을 해도 공간 일반화에서 커널 회귀에 졌음 |

### 3.3 타 대회 공식 [B]
- Kaggle AMS 2013-14: 상위 4팀 전원 GBRT, MAE(laplace) 손실, 전 관측소 통합 단일 모델 > 관측소별 모델, 12개 GBRT 앙상블, Nelder-Mead MAE 가중 블렌딩, ×1.01 편향보정.
- DACON 동서발전 2021: GBM + **가장 늦은 예보 발행분** 선택, 청천 보정 일사량이 설명력↑.
- KPX 제도 연구(경희대 JIIS 2023): "평균 오차율 최소화 ≠ 정산금 최대화", 탐욕+국소탐색 할당 절차 재사용 가능(2026은 선형 절대오차라 임계값 효과 없음).

### 3.4 2026 경쟁자 공개 저장소 (GitHub API 전수, 10/26 [A]) — 6곳, 블로그 후기 0건
| 저장소 | 핵심 |
|---|---|
| **ruby9915/OIBC** (유일하게 수치 있음) [C] | 무작위 분할은 **26% 낙관** → 시간순 분할. L2→L1 −3~4%. **GBDT+NN 50:50 → 팀오차 12.89%→11.88%(−7.8%)**; GBDT끼리 오차 상관 0.92~0.98(앙상블 무효), GBDT–NN 0.82~0.88. NN 사다리: 조기종료+전체데이터 → L1 → **발전소 임베딩** → 큰 네트워크 → 예보오차 노이즈 주입(12.63→12.04%). 수작업 피처는 NN에 무효. 시드 차이 최대 0.23 → 0.3 이하 차이는 단일 시드로 판단 금지. 그룹핑 수치 §2.4. 계획: 분위수+오차상관 시나리오 → 중앙값, 스태킹(예보→실측) |
| Max-JI64/OIBC-2026-DATA_TADA [C] | A·B 예보 정준상관 0.90~0.98이나 설명분산 41%/32%. 집합 오차의 97~98.5%가 합산 후에도 남음. **plant-ID 범주형 1개 추가가 W −1.0~−3.0%**. 용량가중 L1·교차피처·A/B 결합입력·G1 피크 편향보정은 기각(+0.7~+29%). 기각 로그 운영 |
| kwonjh0721-pixel [C] | 이용률 타깃 LightGBM, SMP×k×용량 가중 L1, 태양고도 ≤−6° → 0, 1-이동/2-교환 국소탐색 그룹핑. 수치 없음 |
| KTHYEONG/oibc-2026 [C] | 채택 규칙: 모든 폴드 개선 + 풀링 개선폭 > 시드 노이즈 + 분기별 일관성 |
| ksmini0928-blip, lce2005 | starter 미러 / LICENSE만 |
- 2025 대회 저장소 중 2025-11 이후에도 갱신된 숙련자 8곳(JinseokChun, DohyunBu, fosemfhtm, qewr1234 등) → 2026 참가 가능성 [추정].
- **공개 경쟁자들은 이미 L1 + 시간순 검증 + GBDT/NN 앙상블 + 혼합 그룹핑에 도달.** 차별화는 (a) 집합 수준 보정·시나리오 중앙값, (b) 예보→실측 스태킹, (c) 발표 서사.

---

## 4. 추천 모델링 레시피 (우선순위 순)

### P0. 검증 하네스 먼저 (모든 결정의 전제)
1. **시간 블록 롤링 CV**: PV2022/2023/2024(각 6월~익년 5월) 폴드. 무작위 분할 금지(26% 낙관 [C]). 48개소는 2024-06 이후만 데이터 → plant-held-out 보조 검증(2025 대상의 LOGO-CV 번역) [R5].
2. **지표 = 집합 합계의 SMP·k 가중 MAE**를 커스텀 `feval`로(행 단위 MAE 최적 ≠ 집합 최적). 조기종료 폴드와 블렌딩 폴드 분리. 시드 ≥3.
3. 채택 규칙: 모든 폴드 개선 + 개선폭 > 시드 노이즈 (KTHYEONG 방식) [C].
4. 검증 점수는 검증연도 실제 w, 보조로 테스트 (월,시) 프로파일 가중 점수 병기(두 프로파일 상관 0.986) [로컬].

### P1. 기준선 재현 → L1 + 가중치 (가장 싼 큰 개선)
5. `baseline.py`(참조 배정 + LightGBM L2 이용률 + round 10/17 평균, 야간 0) 재현 → 첫 제출(형식 검증용).
6. `objective='regression_l1'`, `sample_weight = 테스트 (월,시) 평균 w` [로컬 R² 0.917], `metric='l1'`. 하이퍼파라미터 출발점: lr 0.02~0.03, 2,000~5,000 trees + 조기종료, min_data_in_leaf 100~300, feature_fraction 0.7~0.8, bagging 0.8 [R3]. L1은 수렴이 느리므로 huber 워밍업 또는 L2 예측을 피처로 한 2단계 L1도 고려.
7. 타깃 = CF(energy/capacity), `site_id` 범주형(TADA: W −1~3% [C]), 야간(고도 ≤ −6°) 학습 제외·0 고정.
8. 학습 기간: 전체 vs 최근 2년 vs 시간 감쇠 가중을 CV로 비교(기준선은 2년만).

### P2. 피처 (일사량 미제공 조건)
9. 태양기하: 고도·방위·cosZ·대기외 일사량·doy sin/cos (pvlib `solarposition`). 좌표 ≤2 km 교란은 무시 가능.
10. **청천 GHI**(pvlib `haurwitz`/`ineichen`) × 운량 A·B(+평균·차·절대차) + 운량→일사 프록시 2~3종(Larson 선형 0.35+0.65·(1−cloud), Campbell–Norman τ=0.75·(1−cloud)) — 식을 정답으로 쓰지 말고 **트리가 재적합**하게. `monotone_constraints`(운량 −, 청천GHI +).
11. B사 고유: `wb_uv_idx` 및 청천 대비 비, `wb_ceiling`(0/16,337 구간화), `wb_vis`, 이슬점차, 강수확률(캡 90). A사: 기압 제외 시 악화 [C, TADA].
12. **round 10·17을 한 행에 모두**(차분 = 예보 추세/불확실성) + 라운드별 모델 홀드아웃 블렌딩(17 쪽 가중↑ 예상 [추정]). 인접 시간(±1~3h) 예보, 일 요약(일 최대 운량·UV).
13. 적설: `wb_snow`·`wb_snow_prob`·`wa_snow` 최근 24/48/72h 누적 × 기온<0 지속시간 [추정, 데이터로 확인]. 관측지점 ID·거리.
14. 예보오차 인지: 학습구간 `observed_wa/wb`로 지점·계절·시간대별 예보 편향 통계(학습구간만, 누수 방지) → 피처 또는 2단계(예보→실측 OOF) 스태킹. GBDT에 노이즈 복제는 해로움 [C].
15. 사용 금지 피처: 예측시점 이후 실적·실측, 평가구간 SMP(입력 용도 미확인).

### P3. 집합 수준 보정 (합산 편향 제거)
16. (i) 풀링 발전소 모델 합산, (ii) **집합 총량 직접 L1 모델**(피처: 집합 내 용량가중 운량·UV·청천GHI 평균, 지점별 분산), (iii) 둘의 집합 수준 홀드아웃 블렌딩(비음 가중, SMP·k 가중 MAE 최소화). 또는 OOF 위 소형 L1 보정 모델(시간대·계절·운량 구간).
17. 두 집합에 **같은 모델·시드·후처리**를 써서 오차 부호 일치도↑ [R3 추론].

### P4. 모델 다양성 (단일 최대 개선: −7.8% [C])
18. NN: 발전소 임베딩 + L1 + 시간순 조기종료 + 예보오차 블록 리샘플 노이즈 주입. GBDT+NN 50:50. CatBoost(`loss_function='MAE'`)는 범주형 ID에 유리할 수 있음 [추정].
19. 동종 GBDT 다수 앙상블은 이득 작음(5모델 평균 12.83→12.37% [C]) → 이질성(입력셋 A중심/B중심, 발전소/집합 수준) 우선.

### P5. 구성(composition)
20. **층화 교대 배정**: 쌍둥이(편차상관 최대 사이트, 중앙값 2.2 km·ρ 0.974 [로컬])를 반대편에, 지역·관측지점·용량대·데이터 시작월 균등. 기준 분할은 쌍둥이 동일 그룹 82.6%(인터리브와 거리 멀고 북쪽 두 군집 27:4, 5:27 편중) [로컬].
21. 대형·위험 발전소 분산 [로컬 `gen_quality`]: PV004(1,388 kW, 정지 이력), PV011(1,276 kW, 2024-12 편입·VAL 결측 57.9%), PV188(992 kW, 만성 저성능 0.80), PV241(999), PV240(995)를 한 그룹에 몰지 말 것. PV059+PV246(동일 사업장 동시 정지 131일) 분리. 이력 1년 미만 48개소(9,491 kW, B에 8,292 kW 집중)와 A의 열화 12개소도 균등 분산. 깨끗한 용량 24,571 kW만으로는 두 그룹 20,000 kW를 못 채움.
22. OOF 잔차로 1-이동/2-교환 탐욕 스왑 1~2회(연도별 OOS 검증), 과최적화 금지(기대 이득 ≤0.3%p). 즉시 가능한 저위험 예: PV215(A)↔PV240(B).
23. 용량 하한 자동 검사 + 253개소 정확히 1회 + ts 완비 + 음수/NaN/Inf/tz 검사 스크립트.

### P6. 후처리·운영
24. 야간 0, 음수 0, 상한 클립(유효용량 합·최근 12개월 99.5% 분위), SMP=0 시각은 무관. 발전소별 최근 12개월 상대성능(0.80~0.90)을 스케일 팩터로 bias 제거 [로컬].
25. 데이터 정제는 최소: 학습 결측은 전부 "편입 전"(내부 gap 1건 7시간), 클리핑·출력제한 신호 없음, 음수 40건·CF>1 9건·야간 발전 0.004% → **보간 로직 불필요**, 결측 타깃은 제외(0 채움 금지) [로컬]. 실측 기상 이상값(wb_cloud>100, wa_wind 9999 등)은 클립.
26. 제출 운영: 1회차 = 형식 검증 → 한 번에 한 변경 → 리더보드 튜닝 금지(private 없으면 과적합이 벌 받지 않지만 발표에서 설명 불가). 11/2 이후 dataen 공지 매일 확인(2024는 대회 중 거의 매일 운영 공지).

### P7. 차별화 옵션 (발표 소재, 시간 남을 때)
27. 발전소별 분위수 모델 → OOF 잔차 가우시안 코퓰라(관측지점 공유 구조가 상관 설명) → 집합 시나리오 → 시각별 가중 중앙값. Q-sum·독립 가정과 ablation [A, 2502.07010]. ruby9915도 계획 중 → 먼저 구현하면 차별화.
28. 정오 피크(ts 11~15) 전용 보정 모델 ablation.

---

## 5. 한국 시장·기상 맥락과 리스크

### 5.1 제도 배경 (발표용; 모델 입력 금지)
- **왜 20,000 kW·두 집합**: KPX 재생에너지 발전량 예측제도(2021-10 시행)의 참여 단위가 20 MW 이상 개별자원 또는 1 MW 이하 소규모 자원을 모은 집합전력자원 [A, KPX 규칙 연표]. 데이터 평균 169 kW → 전형적 소규모 집합. 대회는 "집합자원 2개 등록 중개사업자" 시뮬레이션.
- **정산단가 개정**: 태양광 2025년 6월부터 오차율 ≤4% 4원/kWh, 4~6% 3원(구 6%/8%) [B, 전기신문 2025-02-25; A, KPX 2025.2.12 시행 개정 패키지]. 풍력·혼합 1년 유예. 평가 첫날과 같은 달("6월 1일"은 해줌 해석 [B]). 오차율 분모는 설비용량, 이용률 <10% 제외. **대회 지표는 선형 절대오차 가중합이라 임계값 게임이 아님** → 제도 숫자는 "왜 20 MW·왜 11~15시·왜 가격가중인가"의 배경으로만.
- 업계 벤치마크(발표 맥락용): KPX 평균 오차율 8.3%→5.7%(도입 후) [B], 해줌 2.6%(2025 이행능력시험)·2024 5% 이내 [B]. 분모가 달라 대회 지표와 직접 비교 불가.
- **왜 11~15시 k=3** [추정]: 육지 출력제어·SMP 0원이 집중되는 시간대(KPX 출력제어 예정 10~15시, 최소수요 13시경) + 절대오차 kWh 최대 시간대.
- 입찰제도 과도기: 제주 시범(2024-06, 음수 −79원까지), 육지 2026년 확대 논의 [B, 2차 자료]. 대회 설계는 "예측 인센티브 → 불균형 책임" 전환을 반영 [추정].

### 5.2 SMP 국면 [로컬 + B]
- `smp.csv`는 **육지 SMP** [추정, 근거: KPX 월평균과 1~2원 차이로 일관, 2025-10-08 추석 13시 0원 보도 일치, 음수 없음].
- 학습구간 연평균: 2021 93.0 → 2022 193.7(에너지위기) → 2023 163.3 → 2024 125.4(0원 첫 출현 6h) → 2025(1~5월) 117.6(0원 11h). 평가구간 108.02(0원 18h). **과거 SMP 패턴 학습은 의미 작음**, 평가 SMP는 어차피 주어짐.
- 시간대: 04시 89.4 최저 → 10시 116.3 → **13시 103.7(낮 골)** → **20시 120.8 최고**. 월별 12월 88.8 최저, 5월 120.1 최고. 겨울 주말 정오는 평일의 70%.
- 저가 시각은 매년 증가(0원 PV2023 3 → PV2024 14 → PV2025 18) — 평가 연도 내 추세는 이미 `smp.csv`에 반영.

### 5.3 기상 제공사 [추정, 스키마 기반 고신뢰]
- **B ≈ AccuWeather**(RealFeel/WetBulb/Ceiling ft/Visibility mile/UVIndex/Ice·Rain·Snow Probability/TotalLiquid 필드명 1:1, °F·mile·ft 환산 흔적). **A ≈ OpenWeatherMap**(temp=temp_min=temp_max, grnd_level, clouds %, wind m/s, rain/snow mm). 둘 다 일사량 없음. 주최 미확인, 식별해도 외부 데이터 사용 금지 → 변수 해석·전처리 설계에만.
- 품질: 한국 대상 독립 비교 문헌 없음. **학습구간 `forecast ↔ observed ↔ generation` 자체 백테스트가 유일한 합법 검증**. A 풍속 m/s vs B km/h, A 평가구간 264행 결손, B 학습구간 강수 8열 1,298행 결손, 실측 센티널(9999 등).
- 관측지점 공유: A 61개(최대 20개소/지점), B 73개(최대 18). 거리 통제 시 관측소 공유가 **실제 발전** 상관에 주는 추가 효과는 +0.02 수준으로 미미하나, **예보 오차는 같은 입력을 받으므로 공통(상관)일 가능성 높음** [로컬; 모델 잔차로 검증 필요]. 2025 대상팀이 발견한 "군집별 기상 데이터 전부 일치" 구조와 동일.

### 5.4 평가기간 실제 날씨 (리스크 이해 전용, 모델 입력 금지) [B, 기상청 보도자료]
- 여름 2025: 역대 최고 더위(25.7℃), 역대 2번째 짧은 장마(남부 6/19~7/1), 7월 일조 251h(역대 2위) 뒤 7/16~20 광주 426 mm 극한 호우. → 가중 최대 구간이 "맑고 더운" 달: 고온 효율 저하 보정이 관건, 7월 중순 과대예측 리스크 집중.
- 가을 2025: 9월 강수일수 15.1일(역대 2위), 뇌전 최다; **10월 기온·강수량·강수일수 모두 역대 1위**(강릉 22일 연속 비). → 학습구간 가을 평균 패턴으로 예측하면 체계적 과대예측. 운량·강수 예보 신호를 얼마나 신뢰할지가 핵심.
- 겨울: 11월·2026년 1~2월 역대급 건조·맑음(1월 일조 219h 역대 1위) **단 호남 서해안 폭설(목포 42.1 cm, 1/11 무안 19.7 cm)** → 전국 맑음인데 호남 적설로 지역 편차 극대. 1/21~23 한파 오전 10시 SMP 185~190원.
- 봄 2026: 2위 고온(5월 18.6℃ 역대 1위), 4월 강수 87.6%가 상순 집중, 3월 하순 평일에도 0원 출현(출력제어 시즌).
- 종합: "여름·겨울은 이례적으로 맑고, 가을은 이례적으로 흐린" 비대칭 해 [B]. **합법적 대비**: 학습구간에서 유사 구간(흐린 가을 2023-09~10, 서해안 폭설 2022-12/2023-01, 짧은 장마)을 골라 스트레스 검증 세트 구성.

### 5.5 데이터 측 리스크 [로컬 `gen_quality`]
- 커버리지: 편입 후 99.98~100%, 탈락 0개소, VAL 전체 보유 205개소. 테스트 연도 결측은 신규 편입/탈락에서만 발생 가능. "결측=0 채점" 규칙이라면 PV011 1개소만으로 VAL w-결측의 41%.
- 이력 길이: 용량의 57%(24,252 kW)가 1~2년 이력, 3년 이상은 8%. 48개소(9,491 kW)는 1년 미만 → 자기 데이터로 계절성 못 배움, 풀링 필수.
- 참조 A vs B: A는 "오래됐지만 열화·정지 이력 많음"(음수 39/40건, 열화 −5%/yr 이하 12개소 전부 A, 최근 상대성능 0.938), B는 "성능 좋지만 이력 짧음"(용량가중 CF 0.1618 vs 0.1534, 1년 미만 8,292 kW).
- 행동 이상치: PV188(−0.199 거리보정 잔차, 트래킹/출력제한/계량 의심), PV011(0인 날 24.7%), PV073, PV059/PV246 동일 운영자. 서향 추정 3개소(PV244·PV210·PV086, 피크 14시) → 사이트 고정효과 필요.
- 출력제어: 데이터 제주 0개소, ≥500 kW 18개소(용량 37.1%). 육지 제어는 500 kW 이상 중심 [B] → 대부분 소규모라 노출 제한적이나 대형 18개소는 봄·가을 맑은 휴일 정오(k=3!) 제어 가능성. 학습 데이터에서 클리핑/제한 신호는 발견되지 않음 [로컬].
- 열화: 문헌 중앙값 0.5%/yr [A, Jordan & Kurtz], 로컬 용량가중 −0.17%/yr → 테스트 연도 내 추가 하락 작음, 최근 12개월 상대성능 스케일로 흡수.

### 5.6 규정 리스크
- 외부 사전학습 모델 금지(공식) vs 설명회 발언 상충 → 보수적 선택.
- 데이터 외부 업로드(생성형 AI 서비스 포함) 수상 취소 → 코드·집계값만 AI 도구에 노출.
- private 분할 부재 시 리더보드 과적합이 벌 받지 않음 → 역설적으로 20회를 "실제 실적에 대한 질의"로 쓸 수 있으나 발표에서 설명 가능해야 함.
- 유사도 기준 미공개 → baseline 그대로 반복 제출 금지.

---

## 6. 발표평가 대비 포인트 (창의 30 + 발표 20 가정)

1. **대회 기간 중 발표 자료를 함께 축적**: 실험 로그, 기각 실험(TADA식 사전 기준·기각 로그), 시드 분산, 결측·이상치 처리 근거. 리더보드 1위 ≠ 대상(2023 4→3위 역전, 설명회 "2~3등도 대상 가능").
2. **구성(20장 내외, 7팀×25분)**: 문제 재정의(지표 분해: 수익항 공통, 11~15시 84% 노출, 우측닫힘) → 데이터 분석 4장(2025 대상 형식: 완결성·외생변수·공간·시공간) → 시스템 모델링 1장(그래프: 관측 가능/불가 변수) → 방법론 → ablation 표 → 결론 한 줄 → 회고.
3. **한 가지 창의 포인트를 한 줄로**: 예) "두 집합을 쌍둥이로 만들고, 가중 중앙값으로 답하다" / "합산 편향을 집합 수준에서 되돌리다" / "관측지점 공유 = 공통 예보오차를 구성과 보정에 쓰다"(2025 심사평 "인접 발전소 활용"과 연결).
4. **반드시 넣을 ablation**: (a) 무작위 vs 시간순 분할, (b) L2 vs L1 vs 가중 L1, (c) 지역 분할 vs 참조 vs 인터리브 구성(주최 측이 "그룹 구성 전략"을 핵심으로 지목), (d) 발전소 합산 vs 집합 직접 vs 블렌딩, (e) GBDT vs NN vs 앙상블, (f) round 10 vs 17 vs 동시.
5. **데이터 이슈 슬라이드**: A/B 단위 차이, 264행 결손, 센티널, 우측닫힘, 48개소 짧은 이력, 대형 이상치(PV188·PV011·PV004), 서향 3개소. 설명회가 "이상치·결측 처리가 가장 중요한 평가 요소"라고 했음.
6. **제도 맥락 1장**: 왜 20 MW·왜 11~15시·왜 가격가중(예측제도 → 입찰제도 전환, 4%/6% 개정, 출력제어·0원 SMP). 외부 날씨 사후정보는 "검증 설계 교훈"으로만 언급.
7. **피할 것**: 단순 평균 앙상블(명시 감점), 지표 꼼수, 재현 불가 코드, 수치 없는 주장. 코드는 전처리~추론 전 과정 재현(상위 7팀 필수, 17위까지 요구 가능).
8. 동점·배점 등 미확인 규칙은 1:1 문의로 확정하고 발표에서 규정 준수를 명시.

---

## 7. 출처 목록

### 공식 [A]
- https://dataen.ai/challenge , https://dataen.ai/challenge/2026 (대회 규정·제공 데이터 탭, 2026-10-26 열람), https://dataen.ai/challenge/history
- https://dataen.ai/notice (공지 16건), https://dataen.ai/notice?tab=faq , https://dataen.ai/notice/c3c1f3ca-0ae5-4d00-aa3c-ce1fdd699d45 (2024.11.18 발표평가 안내)
- 참가자 폴더 `README.md`, `baseline.py`, `sites.csv`, `smp.csv` (C:\Users\User\Downloads\OIBC_2026_DATA\handover 2\01_participant_dataset\)
- https://ime.postech.ac.kr/ime/news/seminar.do?mode=view&articleNo=49630 (POSTECH 안내 PDF), https://i-ai.postech.ac.kr/event/41
- KPX: https://www.kpx.or.kr/board.es?mid=a11002010000&bid=0030&act=view&list_no=74304 (2025.2.12 시행 개정 공고), https://marketrule.kpx.or.kr/lmxdata/attach/2025/5/upload_5127126665285383397_p749.pdf (개정이력 부록2), https://marketrule.kpx.or.kr/lmxsrv/law/joHistoryContent.do?SEQ=2&SEQ_CONTENTS=21489&DATE_START=20210501&DATE_END=20231230 (제14.1.1조), https://new.kpx.or.kr/smpMonthly.es?mid=a10606080300 , https://new.kpx.or.kr/board.es?mid=a10109050000&bid=0216&act=view&list_no=75189 (출력제어 전망)

### 공고 전재·보도 [B]
- 2026 공고: https://www.all-con.co.kr/view/contest/543104 , https://linkareer.com/activity/353328 , https://www.devtimes.co.kr/news/531990 , https://zdnet.co.kr/view/?no=20260922114405 , https://www.newstap.co.kr/news/articleView.html?idxno=334555 , https://www.g-enews.com/article/General-News/2026/09/202609220926382243f7ba87f45b_1
- 역대: https://m.news.nate.com/view/20251223n24813 (2025 결과, 프라임경제), https://www.kyongbuk.co.kr/news/articleView.html?idxno=4056124 , https://www.devtimes.co.kr/news/435023 , https://www.industrynews.co.kr/news/articleView.html?idxno=51733 (2023), https://www.contestkorea.com/sub/view.php?Txt_gbn=1&Txt_bcode=030410001&str_no=202309120082 (2023 공고), https://www.mt.co.kr/industry/2022/12/08/2022120813504263708 (2022), http://www.e2news.com/news/articleView.html?idxno=248583 , https://www.industrynews.co.kr/news/articleView.html?idxno=56693 (2024)
- 제도·시장: https://www.electimes.com/news/articleView.html?idxno=350873 (4%/6% 개정, 8.3→5.7%), https://blog.haezoom.com/notice_05/ , https://blog.haezoom.com/insight_vpp_19/ , https://blog.haezoom.com/news_03/ , https://blog.haezoom.com/insight_vpp_28/ , https://blog.haezoom.com/insight_vpp_48/ , https://kidd.co.kr/news/218609 , https://ksp.etri.re.kr/ksp/article/file/66174.pdf , https://m.ekn.kr/view.php?key=20251008029334262 (추석 0원), https://www.electimes.com/news/articleView.html?idxno=351562 , https://www.electimes.com/news/articleView.html?idxno=337975 (제주 음수), https://www.mt.co.kr/policy/2026/05/26/2026052609322861248 , https://m.news.nate.com/view/20260513n32610 (500 kW 이상 제어)
- 기상청: https://www.korea.kr/briefing/pressReleaseView.do?newsId=156713340 (2025 여름), https://www.korea.kr/briefing/pressReleaseView.do?newsId=156725042 (2025 10월), https://www.korea.kr/briefing/pressReleaseView.do?newsId=156738247 (2025 연), https://www.kma.go.kr/kma/news/press_01.jsp?bid=press&mode=view&num=1194607 (겨울), https://www.weather.go.kr/kma/flexer/html/press/2026/02/03/ATC202602031731562_92984048-2e9a-4cd9-94c3-9a042308c0a8.hwp.files/Sections1.html (2026 1월), https://m.news.nate.com/view/20260602n24271 (2026 봄), https://view.asiae.co.kr/article/2026011110212490879 (호남 폭설)
- 제공사 스키마: https://apidev.accuweather.com/developers/forecasts/general , https://openweathermap.org/api/hourly-forecast

### 설명회 녹취·참가자·수상팀 저장소 [C]
- 2026: https://github.com/ruby9915/OIBC (설명회 전사 docs/, 실험 README), https://github.com/Max-JI64/OIBC-2026-DATA_TADA , https://github.com/kwonjh0721-pixel/kwonjh0721 , https://github.com/KTHYEONG/oibc-2026 , https://github.com/ksmini0928-blip/OIBC2026 , https://github.com/lce2005/2026_OIBC
- 2025: https://github.com/JinseokChun/OIBC_Retry (대상 재시도: 노트북·슬라이드 22장), https://github.com/DohyunBu/OIBC_ReTry , https://github.com/fosemfhtm/2025_oibc_team_chidies (2위), https://github.com/qewr1234/POSTECH-OIBC-Solar , https://github.com/junseo5777/nins_prediction_obic
- 2024: https://github.com/kimjin1022/2024_POSTECH_OIBC_CHALLENGE (17위), https://github.com/myoungse/2024_POSTECH_OIBC_CHALLENGE (14위), https://github.com/bluelemon61/24-OIBC-WolgoksTears
- 2023: https://github.com/hjinshin/OIBC_2023 (대상 김최신이), https://github.com/lhk6565/2023_POSTECH_OIBC (2위), https://github.com/Glanceyes/2023-POSTECH-OIBC-Challenge (3위 폭풍대기, 발표 PDF)
- 2022: https://github.com/HiddenBeginner/2022_OIBC_Competition (대상 Sun Capturer, 발표 PDF·losses.py)
- GitHub 검색: https://api.github.com/search/repositories?q=OIBC+in:name,description,readme&sort=updated&per_page=50

### 학술·도구
- Gneiting 2011 (절대오차 → 중앙값): https://arxiv.org/abs/0912.0902
- LightGBM L1 가중 백분위: https://raw.githubusercontent.com/microsoft/LightGBM/master/src/objective/regression_objective.hpp , https://lightgbm.readthedocs.io/en/stable/Parameters.html
- 합산 편향: https://arxiv.org/pdf/1710.02669 , https://arxiv.org/pdf/1507.08444
- 확률 집계(Q-sum/Indep/Copula): https://arxiv.org/abs/2502.07010 ; CoCopula https://arxiv.org/abs/2602.02583
- 다중 NWP·지역 예측: Pierro 2016 https://ambiente.sostenibilita.enea.it/pubs/2344 ; IEA PVPS T16 https://iea-pvps.org/wp-content/uploads/2020/07/IEA_PVPS_T16_regional_forecasts_summary.pdf ; Lorenz 2008 https://52.iea-shc.org/Data/Sites/1/publications/23rd_EU_PVSEC_5AO.8.6_lorenz.pdf ; Visser 2019/2022 https://research-portal.uu.nl/en/publications/benchmark-analysis-of-day-ahead-solar-power-forecasting-technique/ , https://ideas.repec.org/a/eee/renene/v183y2022icp267-282.html
- 평활효과: Hoff & Perez https://www.cleanpower.com/wp-content/uploads/2012/02/081_QuantifyingPVPowerOutputVariability.pdf
- 전역 모델: Montero-Manso & Hyndman https://arxiv.org/abs/2008.00444
- 청천·pvlib: https://pvlib-python.readthedocs.io/en/stable/reference/clearsky.html , https://raw.githubusercontent.com/pvlib/pvlib-python/v0.9.5/pvlib/forecast.py , https://hal.univ-reunion.fr/hal-03964785v1
- 데이터 품질: https://pvanalytics.readthedocs.io/en/stable/generated/gallery/index.html , Jordan & Kurtz https://www.nrel.gov/docs/fy13osti/56690.pdf
- NWP 오차 구조: https://arxiv.org/abs/2607.12954 ; 메타분석 https://arxiv.org/abs/2111.02092 ; GEPIII https://arxiv.org/abs/2202.02898
- 시계열 CV: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html
- AMS 2013-14 (BAMS 2015): https://repository.library.noaa.gov/view/noaa/22258/noaa_22258_DS1.pdf
- DACON 동서발전: https://dacon.io/en/competitions/official/235720/overview/rules
- 경희대 JIIS 2023 집합구성: https://koreascience.kr/article/JAKO202302557628860.pdf ; 한혜승 외 2021 https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE10609786

### 로컬 분석 (이 세션)
- `C:\Users\User\AppData\Local\Temp\claude\C--Users-User-Downloads-OIBC-2026-DATA\dfcedbe5-607d-48a7-8c29-05284fe8d563\scratchpad\analysis\smp_weights_report.md`
- `...\scratchpad\analysis\spatial_corr_report.md`
- `...\scratchpad\analysis\gen_quality_report.md`
- 원 리서치: `C:\Users\User\Downloads\OIBC_2026_DATA\research\lens1_official_rules.md`, `lens2_past_winners_competitor_intel.md`, `LENS3_methods_state_of_the_art.md`, `lens4_korean_market_context.md`; `...\scratchpad\research\R5_gap_fill.md`

### 접근 실패
- https://competition.postech.ac.kr/ (2024 대회 사이트, DNS 소멸), web.archive.org(도구 차단), KPX 개정 조문 hwp 원문(미열람), 2023 대상팀 pptx(미열람)
