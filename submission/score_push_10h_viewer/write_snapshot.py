#!/usr/bin/env python3
"""Refresh saved viewer snapshots; reopening a file preview shows its latest save."""

import sys

sys.dont_write_bytecode = True

import argparse
from datetime import datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import stat
import tempfile
import time

import server


INDEX = Path(__file__).resolve().with_name("index.html")
MARKDOWN = server.CAMPAIGN / "LIVE_STATUS.md"
OPEN_TAG = b'<script id="oibc-snapshot-data" type="application/json">'
CLOSE_TAG = b"</script>"


class ConcurrentEdit(RuntimeError):
    pass


def atomic_write(path, contents, expected=None):
    """Replace one whole file, refusing a known concurrent template edit."""
    path = Path(path)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), mode)
            handle.write(contents)
            handle.flush()
            os.fsync(handle.fileno())
        if expected is not None and path.read_bytes() != expected:
            raise ConcurrentEdit("The HTML changed during the snapshot update")
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def replace_snapshot(index_path, snapshot, template_path=None):
    encoded = (json.dumps(snapshot, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
               .replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029").encode("utf-8"))
    for _ in range(5):
        source = Path(template_path) if template_path else Path(index_path)
        original = source.read_bytes()
        previous_output = Path(index_path).read_bytes() if Path(index_path).exists() else None
        if original.count(OPEN_TAG) != 1:
            raise ValueError("Expected exactly one oibc-snapshot-data script tag")
        start = original.index(OPEN_TAG) + len(OPEN_TAG)
        end = original.find(CLOSE_TAG, start)
        if end < 0:
            raise ValueError("Snapshot script tag is not closed")
        updated = original[:start] + encoded + original[end:]
        try:
            if source.read_bytes() != original:
                raise ConcurrentEdit("The template changed during the snapshot update")
            atomic_write(index_path, updated, expected=previous_output)
            return
        except ConcurrentEdit:
            continue
    raise ConcurrentEdit("HTML kept changing; snapshot update deferred")


def korean_snapshot(snapshot):
    runtime, counts, timing = (snapshot[key] for key in ("runtime", "counters", "time"))
    observed = server.timestamp(snapshot.get("observed_utc"))
    checked = observed.astimezone(server.KST).strftime("%Y-%m-%d %H:%M:%S KST") if observed else "확인 불가"
    best = snapshot["ranking"].get("best_standalone")
    latest = snapshot.get("latest_trials", [])
    elapsed = max(0, timing.get("elapsed_seconds") or 0)
    heartbeat = runtime.get("heartbeat_age_seconds")
    phase = {"search": "후보 탐색", "completion": "최종 검증·재학습", "finalizing": "보고서 정리", "finished": "실행 종료", "blocked": "실행 차단"}.get(runtime.get("phase"), runtime.get("phase", "확인 불가"))
    campaign = snapshot.get("campaign", {})
    phase = campaign.get("stage_label", phase)
    supervisor = snapshot.get("supervisor", {})

    def process(label, key):
        alive = runtime.get(key + "_alive")
        state = "실행 중 · PID·시작 시각·부팅 식별값 일치" if alive else "실행 중으로 확인되지 않음"
        return f"- {label}: {state} (PID {runtime.get(key + '_pid') or '없음'})"

    lines = ["# 모델 개선 작업 — 저장된 진행 상황", "", f"확인 시각: **{checked}**", "",
        "이 파일은 실행 중인 기록을 읽어 10초 간격으로 저장합니다. 파일 미리보기를 다시 열어 최신 저장본을 확인하세요. 열린 미리보기의 자동 갱신은 보장하지 않습니다.", "",
        f"- 표시 중인 연구: {campaign.get('label', '기존 연구')} · 상태: {phase} / {runtime.get('status', '확인 불가')}",
        f"- 이 단계 완료 후보: **{counts['completed_trials']} / {counts['planned_trials']}개** · 실제 모델 학습: **{counts.get('total_model_fits', counts['total_fit_receipts'])}회**",
        f"- 연장 교차검증 기반 준비: {counts.get('completed_bases', 0)} / {counts.get('planned_bases', 0)}개" if campaign.get("id") == "continuation" else "- 기존 연구를 계속 표시하며, 연장 컨트롤러 시작 후 새 연구로 전환합니다.",
        f"- 현재 작업: {runtime.get('current_job') or '없음'} · 현재 검증 기간: {runtime.get('current_fold') or '학습 사이 또는 종료'}",
        f"- 실제 자동 실행 시작: {timing.get('start_kst') or '확인 불가'}",
        f"- 현재 단계 실행 시간: {int(elapsed // 3600)}시간 {int(elapsed % 3600 // 60):02d}분",
        f"- 종료 기한: {timing.get('deadline_kst') or '확인 불가'}",
        f"- 실패한 작업: {counts['failed_jobs']}개 · 고정된 채택 조건 통과: **{counts['qualifying_trials']}개**",
        process("컨트롤러", "controller"), process("현재 학습 프로세스", "worker"),
        f"- 상태 기록 갱신: {round(heartbeat)}초 전" if heartbeat is not None else "- 상태 기록 갱신: 확인 불가", ""]
    if snapshot.get("extension"):
        status = "식별값 일치 · 실행 중" if supervisor.get("alive") else "실행 중으로 확인되지 않음"
        lines += [f"연장 감독기: {supervisor.get('phase', 'not_started')} · {status} (PID {supervisor.get('pid') or '없음'}).",
                  f"전체 누적 실제 모델 학습: {snapshot.get('cumulative', {}).get('total_model_fits', 0)}회. 재사용 예측과 중앙값 보정은 모델 학습 횟수에 포함하지 않습니다.", ""]
    if latest:
        newest = latest[0]
        ended = server.timestamp(newest.get("completed_utc"))
        ended_kst = ended.astimezone(server.KST).strftime("%H:%M:%S KST") if ended else "시각 불명"
        lines.append(f"최근 완료 후보: **{newest['id']}** ({ended_kst}).")
    if best:
        lines += ["", f"단일 기준 모델 c000 대비 최상위 후보는 **{best['id']}**입니다. 5개 기간의 평균 상대 W는 **{best['mean_W_ratio']:.6f}** ({(best['mean_W_ratio'] - 1) * 100:+.2f}%)이며 낮을수록 좋습니다."]
    lines += ["", "위 수치는 단일 기준 모델 대비 내부평가입니다. 공식 최고점 상승률이 아니며 공식 점수는 조회하지 않았습니다. 모든 과거 데이터는 이전에 노출되었고, 새로운 독립 홀드아웃 평가가 아닙니다."]
    completion = snapshot.get("completion")
    if completion:
        lines += ["", f"최종 처리 결과: {completion.get('status', '확인 불가')} · 후보 파일 내보내기: {'완료' if completion.get('exported') else '없음'}."]
    if runtime.get("stop_reason"):
        lines += ["", f"종료 사유: {runtime['stop_reason']}."]
    if snapshot.get("warnings"):
        lines += ["", "확인 사항: " + " · ".join(snapshot["warnings"])]
    return ("\n".join(lines) + "\n").encode("utf-8")


def write_once(snapshot, index_path=INDEX, markdown_path=MARKDOWN, template_path=None):
    if template_path is None and Path(index_path).resolve() == INDEX:
        template_path = Path(__file__).with_name("template.html")
    atomic_write(markdown_path, korean_snapshot(snapshot))
    replace_snapshot(index_path, snapshot, template_path=template_path)


def run(interval=10, once=False, index_path=INDEX, markdown_path=MARKDOWN,
        reader=server.build_status, now=lambda: datetime.now(timezone.utc), pause=time.sleep):
    stop_at = None
    while True:
        snapshot = reader()
        if stop_at is None:
            deadline = server.timestamp(snapshot.get("time", {}).get("deadline_utc"))
            if deadline is None:
                raise ValueError("Hard deadline is missing; refusing an unbounded snapshot writer")
            stop_at = deadline + timedelta(seconds=120)
        try:
            write_once(snapshot, index_path, markdown_path)
        except (OSError, ValueError, ConcurrentEdit) as error:
            print(f"Snapshot save failed: {error}", file=sys.stderr, flush=True)
            if once or now() >= stop_at:
                raise
        remaining = (stop_at - now()).total_seconds()
        if once or remaining <= 0:
            return
        pause(min(interval, remaining))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Save one snapshot and exit")
    parser.add_argument("--interval", type=float, default=10, help="Seconds between saved snapshots (default: 10)")
    args = parser.parse_args()
    if not math.isfinite(args.interval) or not 1 <= args.interval <= 60:
        parser.error("interval must be between 1 and 60 seconds")
    run(interval=args.interval, once=args.once)


if __name__ == "__main__":
    main()
