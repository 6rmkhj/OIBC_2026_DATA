# /// script
# requires-python = ">=3.12"
# dependencies = ["reportlab", "pypdf"]
# ///
"""Build the Korean team handoff from verified competition artifacts."""
from __future__ import annotations

import hashlib
import json
from html import escape
from pathlib import Path
from zipfile import ZipFile

from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "analysis_outputs/handoff_20261105"
DEST = ROOT / "output/pdf/OIBC_2026_팀공유_인수인계_20261105.pdf"


def sha(path: Path) -> str:
    return hashlib.file_digest(path.open("rb"), "sha256").hexdigest()


def main() -> None:
    best = ROOT / "submission/renew_candidate_20261105"
    hour = ROOT / "submission/renew_hour_candidate_20261105"
    sky = ROOT / "submission/renew_sky_candidate_20261105"
    expected = {
        best / "submission_files.zip": "ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434",
        best / "composition.csv": "68216d1f6b8b6f9c026703e3bfaf7b0470cc8e018580826c866ee0f7357cc141",
        best / "forecast.csv": "948c672c918732ce47ac181ac3ac0325a15d35429594e9c3375036d4c1c413c0",
        hour / "submission_files.zip": "df9aa33420aba686184c909f8332155013a221268d2fd6d699bb008b0bd50e5e",
        sky / "submission_files.zip": "7ad65bcd3053358b62cfbc316626ea64f2bb4af7419e393707cc43562601d1d7",
    }
    assert all(sha(path) == value for path, value in expected.items())
    with ZipFile(best / "submission_files.zip") as archive:
        assert set(archive.namelist()) == {"composition.csv", "forecast.csv"}
        for name in archive.namelist():
            assert archive.read(name) == (best / name).read_bytes()
    extra = sorted((ROOT / "submission/score_push_renew").glob("extra_*.py"))
    assert len(extra) == 6 and not (ROOT / "analysis_outputs/renew_20261105/extra_wave").exists()
    cleanup = json.loads((WORK / "resource_cleanup.json").read_text(encoding="utf-8-sig"))
    assert cleanup["research_process_count"] == 0 and all(item["absent_after"] for item in cleanup["targets"])
    for wave in ("final", "hour_final", "sky_final", "refresh_wave", "mlp_wave", "bounds_wave", "mono_wave", "incbound_wave"):
        evidence = json.loads((ROOT / "analysis_outputs/renew_20261105" / wave / "independent_check.json").read_text(encoding="utf-8-sig"))
        assert evidence["status"] == "PASS", wave

    pdfmetrics.registerFont(TTFont("Malgun", "C:/Windows/Fonts/malgun.ttf"))
    pdfmetrics.registerFont(TTFont("MalgunBold", "C:/Windows/Fonts/malgunbd.ttf"))
    pdfmetrics.registerFont(TTFont("Consolas", "C:/Windows/Fonts/consola.ttf"))
    pdfmetrics.registerFontFamily("Malgun", normal="Malgun", bold="MalgunBold", italic="Malgun", boldItalic="MalgunBold")
    styles = {
        "title": ParagraphStyle("title", fontName="MalgunBold", fontSize=22, leading=30, textColor=colors.black, spaceAfter=15),
        "h": ParagraphStyle("h", fontName="MalgunBold", fontSize=15, leading=22, textColor=colors.black, spaceBefore=12, spaceAfter=9),
        "sub": ParagraphStyle("sub", fontName="MalgunBold", fontSize=11, leading=17, textColor=colors.black, spaceBefore=11, spaceAfter=5),
        "body": ParagraphStyle("body", fontName="Malgun", fontSize=10.1, leading=16.5, wordWrap="CJK", spaceAfter=8),
        "small": ParagraphStyle("small", fontName="Malgun", fontSize=8.6, leading=13.8, wordWrap="CJK", spaceAfter=5),
        "cell": ParagraphStyle("cell", fontName="Malgun", fontSize=8.8, leading=13, wordWrap="CJK"),
        "head": ParagraphStyle("head", fontName="MalgunBold", fontSize=8.8, leading=13, textColor=colors.white, wordWrap="CJK"),
        "code": ParagraphStyle("code", fontName="Consolas", fontSize=8.0, leading=11.8, spaceBefore=4, spaceAfter=8),
    }
    story = []

    def p(text: str, style: str = "body") -> None:
        story.append(Paragraph(text, styles[style]))

    def plain(text: str, style: str = "body") -> None:
        p(escape(text), style)

    def code(text: str) -> None:
        story.append(Preformatted(text, styles["code"]))

    def table(headers: list[str], rows: list[list[str]], widths: list[float]) -> None:
        values = [[Paragraph(escape(value), styles["head"]) for value in headers]]
        values.extend([[Paragraph(escape(value), styles["cell"]) for value in row] for row in rows])
        grid = Table(values, colWidths=widths, repeatRows=1, hAlign="LEFT")
        grid.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#26364B")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F4F7")]),
            ("GRID", (0, 0), (-1, -1), .45, colors.HexColor("#D9D9D9")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.extend([grid, Spacer(1, 10)])

    def page(title: str) -> None:
        story.append(PageBreak())
        plain(title, "h")

    plain("OIBC 2026 성능 개선 인수인계", "title")
    plain("팀 공유용  |  2026년 11월 5일 기준", "small")
    p("<b>현재 사용할 파일은 renew_candidate_20261105의 submission_files.zip이다.</b> 사용자가 보고한 공식 최고점은 <b>6,454,220,836점</b>이다. 시간대 보정 후보는 공식 점수가 437,649점 낮아 채택하지 않는다. 개선 작업은 사용자 요청으로 일시 중단했다.")
    plain("공식 제출 결과", "sub")
    table(["후보", "공식 점수", "판단"], [
        ["기존 파일", "6,443,559,992", "최초 비교 기준"],
        ["리서치 추가 후보", "6,447,820,797", "이전 최고점"],
        ["renew_candidate", "6,454,220,836", "현재 최고점 유지"],
        ["renew_hour_candidate", "6,453,783,187", "최고점 대비 -437,649"],
        ["renew_sky_candidate", "미확인", "공식 성능 주장 불가"],
    ], [175, 130, 194])
    plain("최고점은 이전 최고점보다 6,400,039점, 최초 파일보다 10,660,844점 높다. 공식 점수는 모두 사용자의 제출 결과 보고이며 에이전트가 사이트에서 조회한 값은 아니다. 현재 순위는 미확인이다. 160등과 1등 65억점 초과는 이전 시점의 정보다.")
    plain("팀원이 먼저 확인할 항목", "sub")
    plain("1. 아래 최고점 ZIP과 구성 파일을 보존한다. 최상위 submission 폴더의 다른 composition.csv로 교체하지 않는다.")
    plain("2. 로컬 점수가 좋아진 후보를 공식 최고점으로 표시하지 않는다. 시간대 보정 후보가 그 차이를 보여 준다.")
    plain("3. ExtraTrees는 실행 전 소스 초안이다. 준비 데이터와 성능 결과가 없으므로 다음 후보로 전달하거나 제출하지 않는다.")
    code("submission/renew_candidate_20261105/submission_files.zip")
    plain("이 문서의 상대 경로는 다음 프로젝트 루트를 기준으로 한다.", "small")
    code("C:\\Users\\slowg\\Downloads\\OIBC_2026_DATA")

    page("현재 최고점 후보의 구성")
    plain("발전소 구성과 제출 형식", "sub")
    plain("첫 제출에 사용한 award_candidate 또는 autoresearch_candidate의 구성을 고정했다. 발전소는 253개이며 그룹 정격 용량은 G1 21,208.195kW, G2 21,447.175kW다. 새 후보마다 이 구성의 바이트가 같은지 확인했다.")
    plain("forecast.csv는 2개 그룹의 8,760시간, 총 17,520행이다. 기간은 한국시간 2025-06-01 01:00부터 2026-06-01 00:00까지이며 소수 셋째 자리로 출력한다. ZIP에는 composition.csv와 forecast.csv만 포함한다.")
    plain("예측 파이프라인", "sub")
    plain("기존 발전소 합산 예측과 풍부한 기상 특성의 직접 예측을 섞고, 물리 정규화 LightGBM과 원시 설비이용률 신경망을 결합한다. 관측소별 특성을 쓰는 LightGBM을 추가한 기존 CPU 앙상블에 180일 반감기 모델을 섞은 뒤 기온·눈 보정을 적용한다.")
    code("R = (1 - 0.7642694482340047) * bottom_up\n    + 0.7642694482340047 * rich_direct\nF = 0.380705173762783 * R\n    + 0.41926809371483975 * normalized_lgb\n    + 0.2000267325223772 * raw_cf_mlp\nC = (1 - 0.2808471620447986) * F\n    + 0.2808471620447986 * station_lgb\nT = (1 - 0.07794876465304705) * C\n    + 0.07794876465304705 * temporal180_lgb")
    plain("기온·눈 보정은 T에 적용한다. 기온 경계는 0·10·20·30도, 적설 조건은 extra_wa_snow >= 0.001이다. 첫 개발 기간에서 추정한 기온 계수와 조건부 적설 계수의 곱을 0.85~1.15로 제한하고 조정량의 절반만 반영한다. 마지막에 0~그룹 정격 용량으로 제한한다.")
    code("factor = 1 + 0.5 * (clip(temp_factor * snow_factor, 0.85, 1.15) - 1)\nprediction = clip(T * factor, 0, group_static_capacity)")
    plain("최고점 후보에는 시간대 보정과 B사 구름 보정이 포함되지 않는다. 모든 시드는 유지하며 부호가 있는 예측을 먼저 평균한 뒤 음수 제한을 적용한다. 혼합 비율과 보정계수는 평가 결과에 따라 제출 때 다시 조정하지 않는다.", "small")
    plain("구현 근거: submission/score_push/final_infer.py, submission/score_push_renew/renew_final_predict.py, cal_math.py. 최종 추가 학습은 최신 진단용 3개와 전체 학습용 3개의 시간 가중치 모델이다.", "small")

    page("검증 방식과 해석")
    plain("평가 구간", "sub")
    table(["구간", "학습 종료일", "평가 종료일 및 행 수"], [
        ["첫 개발 기간", "2023-06-01", "다음 시점부터 2024-06-01까지\n17,568개 그룹 시간 행"],
        ["최근 개발 기간", "2024-06-01", "다음 시점부터 2025-03-01까지\n13,104개 그룹 시간 행"],
        ["2025년 3~5월 진단", "2024-06-01 또는\n2025-03-01", "2025-03-01 다음 시점부터\n2025-06-01까지 4,416행"],
    ], [112, 126, 261])
    plain("모든 경계는 한국시간 기준이다. 학습은 종료 시각 이하, 평가는 시작 시각 초과·종료 시각 이하로 구분한다. 야간 행도 최종 점수 계산에 포함한다. 모델 학습의 주간 행 수와 평가 전체 행 수를 혼동하지 않는다.", "small")
    plain("로컬 지표", "sub")
    code("W = sum(SMP * k * abs(y - prediction))\nW_pct = 100 * W / sum(SMP * k * y)\nS = sum(SMP * y) - 0.1 * W")
    plain("W와 W_pct는 작을수록 좋고 공식 제출 점수는 클수록 좋다. k는 한국시간 11~15시에 3, 그 외에는 1이다. SMP와 실제 발전량은 평가와 학습 가중치 검증에 사용하며 미래 예측 입력으로 넣지 않는다.", "small")
    table(["후보", "첫 개발 W%", "최근 W%", "3~5월 오래된 종료일", "3~5월 최신 종료일"], [
        ["기온·눈 최고점", "11.959229", "11.000953", "9.760637", "9.390467"],
        ["시간대 추가", "11.912571", "10.998535", "9.733257", "9.378238"],
        ["구름 추가", "11.792837", "10.955416", "9.751805", "9.397596"],
    ], [107, 85, 85, 111, 111])
    p("<b>시간대 후보는 표의 네 로컬 비교가 모두 좋아졌지만 공식 점수는 낮아졌다.</b> 구름 후보는 개발 구간에서 좋아졌지만 3~5월 두 진단에서 모두 시간대 후보보다 나빴다. 따라서 다음 실험은 공식 최고점인 기온·눈 후보를 기준으로 한다.")
    plain("모든 과거 기간에는 연구 중 노출 이력이 있다. 독립 홀드아웃이나 수상 가능성의 증거로 주장하지 않는다. 첫 기간에서 혼합 비율·보정계수를 추정한 결과에는 표본 내 효과가 포함된다. 공식 점수의 일부 구간과 최종 순위가 같은지도 확인되지 않았다.", "small")

    page("완료한 실험과 반복하지 않을 작업")
    plain("아래 판정은 각 실험에서 미리 고정한 기준에 따른 것이다. 기준 후보가 다른 실험의 숫자를 직접 비교하지 않는다. 추가 모델은 보통 첫 기간에서 혼합 비율을 정하고 최근 기간에 그대로 적용했으며, 두 기간 개선과 혼합 비율 2% 이상을 요구했다.", "small")
    table(["실험", "계산 규모", "결과와 이유"], [
        ["시간 가중치 및 최근 창", "24개 학습", "180일 반감기 선택. 공식 최고점 파이프라인에 포함."],
        ["관측 구름 보조 학습", "보조 14 + 발전 12", "두 변형 모두 최근 구간 악화. 제외."],
        ["그룹 합산 손실", "18개 학습", "세 변형 모두 최적 혼합 비율 0. 제외."],
        ["전체 포트폴리오 예측", "12개 학습", "두 특성 변형 모두 최근 구간 악화. 제외."],
        ["금전 손실 가중치", "12개 학습", "피크·가격 가중 두 변형 모두 최근 악화. 제외."],
        ["발전소별 출력 정규화", "계수 2회 + 학습 6개", "첫 기간 11.946590, 최근 11.038143. 최근 기준 11.000953보다 나쁨."],
        ["기온·눈 및 추가 보정", "기온·눈 7 / 시간 5 / 구름 4계수", "기온·눈은 공식 최고점. 시간은 공식 악화. 구름은 공식 미확인."],
        ["보정계수 시간순 갱신", "32개 계수", "앞선 자료만으로 재추정. 여섯 비교 중 하나만 개선. 제외."],
        ["정규화 관측소 신경망", "6개 학습", "첫 기간 개선, 최근 10.982662로 기준 10.955416보다 악화."],
        ["관측소 신경망 입력 제한", "6회 추론 / 새 학습 0", "최근 11.062367로 악화. 제외."],
        ["fair 손실과 방향 제약", "12개 학습", "단독 제약 효과는 있으나 혼합 후 최근 10.979584 / 10.988034로 악화."],
        ["기존 신경망 입력 제한", "12회 추론 / 새 학습 0", "최근 10.955422703으로 아주 작게 악화. 고정 기준에 따라 제외."],
    ], [130, 110, 259])
    plain("선행 기록의 GPU 초기 8개·확장 24개 모델도 채택되지 않았다. 원시 CF의 최근 365일·730일 실험과 정규화 후 시간 가중치 실험은 구분해야 한다. 실패한 모델을 삭제하거나 이후 구간을 보고 계수·경계를 다시 맞추지 않았다.", "small")
    plain("각 wave의 independent_check.json이 독립 수치 검증 결과이며, terminal_manifest.json은 완료 시점 파일의 SHA256 목록이다. 과거 실행의 outer 종료 코드 누락 등 기록상 한계는 원래 notepad와 terminal_index에 그대로 남아 있다.", "small")

    page("파일 위치와 재현 방법")
    plain("프로젝트 루트에서 아래 상대 경로를 사용한다. 팀원 PC에서는 경로를 자신의 복사본에 맞추되 제출 파일과 학습 입력의 바이트는 유지한다.", "small")
    table(["용도", "경로"], [
        ["최고점 제출", "submission/renew_candidate_20261105/submission_files.zip"],
        ["실제 제출 형식 검사", "submission/validate_artifacts.py"],
        ["최고점 최종 재현 검사", "submission/score_push_verify_renew_final.py"],
        ["최종 생성 모듈", "submission/score_push_renew/renew_final_*.py"],
        ["연구 상세 기록", "analysis_outputs/renew_20261105_notepad.md"],
        ["기존 상세 보고서", "analysis_outputs/reports/renew_성능연구_20261105.md"],
        ["완료 증거", "analysis_outputs/renew_20261105/<wave>/independent_check.json 및 terminal_manifest.json"],
        ["공식 점수 피드백", "analysis_outputs/renew_20261105/official_feedback.json 및 official_feedback_hour_20261105.json"],
    ], [114, 385])
    plain("권장 확인 순서", "sub")
    plain("먼저 마지막 페이지의 해시와 ZIP 내부 파일을 확인한다. 다음으로 제출 형식을 검사하고, 필요하면 저장된 모델의 재현 검사를 실행한다. 이 명령들은 새 모델을 학습하거나 대회에 업로드하지 않는다.")
    code('$env:PYTHONIOENCODING="utf-8"\n$env:PYTHONDONTWRITEBYTECODE="1"\n$env:OMP_NUM_THREADS="1"\n$env:OPENBLAS_NUM_THREADS="1"\n$env:MKL_NUM_THREADS="1"\npython submission/validate_artifacts.py submission/renew_candidate_20261105 --self-check\npython submission/score_push_verify_renew_final.py')
    plain("실험 환경은 Windows의 Python 3.12, LightGBM 4.7.0, scikit-learn 1.9.1이다. 저장된 joblib 모델은 같은 라이브러리 버전에서 재현한다. 일반 학습 한도는 CPU·BLAS 16스레드, PyArrow 4스레드, Normal 우선순위, 동시에 모델 작업 1개다. 일부 과거 신경망 재현은 원래 계산 순서를 맞추기 위해 BLAS 1스레드를 사용했다.", "small")
    plain("검증 증거는 원본 키·정답 정합성, 학습 전용 전처리, 저장 모델 재추론, 부호 유지 후 평균, 고정 보정 계산, 지표·혼합 최적성, CSV 반올림·ZIP 바이트, 순차 실행·종료 및 보호 파일 해시를 포함한다. 최고점 제출 검증은 253개 발전소·17,520행·용량 초과 0건과 잘못된 입력 9개 검사에 통과했다.", "small")

    page("중단 시점과 재개할 때의 주의사항")
    plain("중단 상태", "sub")
    p("사용자 요청으로 개선 목표를 <b>paused</b>로 전환했다. 연구용 실행 프로세스는 없으며 각 완료 wave의 임시 폴더와 루트의 남은 임시 자원도 정리했다. 학습 모델·예측·로그·해시·실패 기록은 보존했다.")
    plain("ExtraTrees는 extra_common.py, extra_fit.py, extra_math.py, extra_prepare.py, extra_run.py, extra_score.py의 여섯 소스만 남아 있다. 정적 검사는 통과했지만 실행 검증은 하지 않았다. extra_wave 폴더, protocol, prepared manifest, release, trial, 성능 결과는 모두 없다. ExtraTrees 학습·추론 횟수는 0이다.")
    plain("중단 당시 계획은 기상 요약 100개 특성, 물리 정규화 목표, 180일 반감기 제곱오차 가중치, 600개 무작위 트리, 시드 0·1·2를 두 기간에 적용하는 단일 후보였다. 학습 n_jobs=16, 저장·예측 n_jobs=1로 계산 순서를 고정할 예정이었다. 시간·구름 보정은 제외하고 공식 최고점의 기온·눈 보정만 비교 기준으로 삼는다. 계획일 뿐 성능 개선 결과가 아니다.", "small")
    plain("팀이 재개를 결정하면 먼저 소스와 데이터 계약을 검토한 뒤 준비 단계만 실행한다. 작성된 score_push_verify_extra_data.py도 실제 준비 데이터로 실행 검증되지 않은 초안이다. 준비 검증을 통과하고 고정된 설정을 확인한 후에만 학습을 진행한다. 기존 release나 과거 후보 manifest를 수정해 새 실험을 승인하지 않는다.", "small")
    plain("최고점 파일 무결성", "sub")
    plain("아래 해시는 공유 문서 생성 시 실제 파일에서 다시 확인했다.", "small")
    code("submission_files.zip\nff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434\n\ncomposition.csv\n68216d1f6b8b6f9c026703e3bfaf7b0470cc8e018580826c866ee0f7357cc141\n\nforecast.csv\n948c672c918732ce47ac181ac3ac0325a15d35429594e9c3375036d4c1c413c0")
    plain("인수인계 결론", "sub")
    plain("지금 제출·공유할 성능 기준은 6,454,220,836점 파일이다. 시간대 후보의 공식 악화와 구름 후보의 진단 악화를 함께 전달한다. 미완료 ExtraTrees 소스를 검증된 모델로 취급하지 않으며, 새 점수나 순위·수상 가능성을 추정하지 않는다.")

    def footer(canvas, doc) -> None:
        canvas.saveState()
        canvas.setFont("Malgun", 8)
        canvas.setFillColor(colors.HexColor("#606873"))
        canvas.drawString(48, 27, "OIBC 2026 팀 공유 인수인계  |  2026년 11월 5일")
        canvas.drawRightString(A4[0] - 48, 27, str(doc.page))
        canvas.restoreState()

    DEST.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(DEST), pagesize=A4, leftMargin=48, rightMargin=48, topMargin=42, bottomMargin=46,
                            title="OIBC 2026 성능 개선 인수인계", author="OIBC 프로젝트 팀")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    reader = PdfReader(DEST)
    text = "\n".join(page.extract_text() for page in reader.pages)
    required = ["6,454,220,836", "6,453,783,187", "437,649", "ExtraTrees", "paused"]
    assert all(value in text for value in required)
    assert len(reader.pages) == 6, len(reader.pages)
    evidence = {"pdf": str(DEST.relative_to(ROOT)), "pages": len(reader.pages), "sha256": sha(DEST),
                "goal_status": "paused", "official_best": 6454220836, "hour_reported": 6453783187,
                "candidate_sha256": {str(path.relative_to(ROOT)): value for path, value in expected.items()},
                "unexecuted_extra_sources": {str(path.relative_to(ROOT)): sha(path) for path in extra},
                "extra_wave_exists": False, "research_processes": 0, "source_checks": "PASS; ExtraTrees runtime unverified"}
    (WORK / "handoff_manifest.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"pdf": str(DEST), "pages": len(reader.pages), "bytes": DEST.stat().st_size}, ensure_ascii=False))


if __name__ == "__main__":
    main()
