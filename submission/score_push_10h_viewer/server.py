#!/usr/bin/env python3
"""Read-only, loopback-only view of the original and continuation campaigns."""

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import threading
import time
from urllib.parse import urlsplit


HERE = Path(__file__).resolve().parent
CAMPAIGN = HERE.parents[1] / "analysis_outputs/research_10h_20261107"
KST = timezone(timedelta(hours=9), "KST")
FOLDS = ("early2022", "primary", "winter", "spring", "recent")
_METADATA_CACHE = {}


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (AttributeError, TypeError, ValueError):
        return None


def process_alive(saved):
    """Use PID, process group, start ticks and boot ID, never a PID alone."""
    if not isinstance(saved, dict):
        return False
    try:
        pid = int(saved["pid"])
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return (fields[0] not in {"Z", "X"}
                and int(fields[2]) == saved["pgid"]
                and int(fields[19]) == saved["start_ticks"]
                and Path("/proc/sys/kernel/random/boot_id").read_text().strip() == saved["boot_id"])
    except (OSError, KeyError, TypeError, ValueError, IndexError):
        return False


def _build_campaign_status(campaign, now, continuation=False, baseline_campaign=None):
    """Read JSON receipts only, keeping reused predictions separate from fits."""
    campaign = Path(campaign)
    now = now or datetime.now(timezone.utc)
    warnings = []

    def read(path, required=False):
        try:
            metadata = path.stat()
            signature = (metadata.st_mtime_ns, metadata.st_size, metadata.st_ino)
            cached = _METADATA_CACHE.get(path)
            value = cached[1] if cached and cached[0] == signature else json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                raise ValueError("expected a JSON object")
            _METADATA_CACHE[path] = (signature, value)
            return value
        except FileNotFoundError:
            if required:
                warnings.append(f"Missing metadata: {path}")
        except (OSError, ValueError) as error:
            warnings.append(f"Unreadable metadata: {path} ({type(error).__name__})")
        return {}

    contract = read(campaign / "launch_contract.json", required=not continuation)
    protocol = read(campaign / "protocol.json", required=not continuation)
    state = read(campaign / "controller_state/state.json", required=not continuation)
    jobs = state.get("jobs", {})
    job_id = state.get("current_job")
    job = jobs.get(job_id, {})
    started = {}
    if isinstance(job_id, str) and re.fullmatch(r"[A-Za-z0-9_-]+", job_id):
        started = read(campaign / "controller_state/jobs" / job_id / "started.json")
        terminal = (campaign / "controller_state/jobs" / job_id / "receipt.json").exists()
        if terminal or started.get("nonce") != job.get("nonce"):
            started = {}
    controller_alive = process_alive(state.get("controller_identity"))
    worker_alive = process_alive(started.get("worker_identity"))
    wrapper_alive = process_alive(started.get("identity"))
    phase = state.get("phase", "unknown")
    runtime_status = "finished" if phase == "finished" else "running" if controller_alive else "controller_not_alive"
    if phase == "blocked":
        runtime_status = "blocked"
    if not controller_alive and phase not in {"finished", "unknown"}:
        warnings.append("Recorded controller identity is not alive; worker liveness is checked separately.")

    current_fold = None
    current_fold_started = None
    current_fit = None
    current_fit_expected = None
    if worker_alive:
        fit_root = (campaign / "trials" / job_id) if re.fullmatch(r"[cn]\d+", job_id or "") else (campaign / "bases" / job_id) if re.fullmatch(r"b\d+", job_id or "") else campaign / "completion" if job_id == "completion" else None
        if fit_root:
            active = []
            for path in fit_root.rglob("started.json"):
                if any(".interrupted." in part for part in path.parts):
                    continue
                if not (path.parent / "receipt.json").exists():
                    value = read(path)
                    if value:
                        active.append((value.get("utc", ""), path, value))
            if active:
                _, path, fit = max(active, key=lambda item: item[0])
                current_fold, current_fold_started = fit.get("fold"), fit.get("utc")
                current_fit = str(path.parent.relative_to(campaign))
                current_fit_expected = fit.get("real_model_fit_expected", True)
                if len(active) > 1:
                    warnings.append("Multiple unfinished fit receipts exist; showing the newest, not asserting concurrent training.")

    results = []
    for path in (campaign / "trials").glob("n*/result.json" if continuation else "c*/result.json"):
        result = read(path)
        if result.get("status") == "PASS":
            results.append(result)
    baseline_id = protocol.get("baseline_id", "c000")
    baseline = read(Path(baseline_campaign) / "trials/c000/result.json") if continuation and baseline_campaign else next((result for result in results if result.get("id") == baseline_id), None)
    selection = protocol.get("selection", {})
    ranking = []
    for result in results:
        try:
            ratios = result.get("baseline_ratios") if continuation else None
            ratios = ratios or {fold: result["folds"][fold]["score"]["W"] / baseline["folds"][fold]["score"]["W"] for fold in FOLDS}
            mean, worst = sum(ratios.values()) / len(ratios), max(ratios.values())
            improved = sum(value < 1 for value in ratios.values())
            robust = (mean < selection.get("standalone_mean_W_ratio_below", 1)
                      and worst <= selection.get("standalone_worst_W_ratio_at_most", 1.02)
                      and improved >= selection.get("standalone_improved_folds_at_least", 3))
            blend = result["blend"]
            if continuation:
                mean, robust = result["mean_W_ratio"], result.get("robust", False)
            deltas = {fold: blend["scores"][fold]["blend"]["W"] - blend["scores"][fold]["reference"]["W"] for fold in ("primary", "recent")}
            ranking.append(dict(id=result["id"], completed_utc=result.get("utc"),
                mean_W_ratio=mean, worst_W_ratio=worst, improved_folds=improved,
                eligible=bool(result["eligible"] if continuation else robust and blend["eligible"]), robust=robust,
                alpha=blend["alpha"], primary_delta_W=deltas["primary"], recent_delta_W=deltas["recent"],
                ratios=ratios, config=result.get("config", {}), base_id=result.get("base_id"),
                worst_raw_W_ratio=result.get("worst_raw_W_ratio")))
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            warnings.append(f"Cannot compute ranking for {result.get('id', 'unknown')}; required receipt fields are missing or invalid.")
    ranking.sort(key=lambda item: (item["mean_W_ratio"], item["worst_raw_W_ratio"] if continuation else item["worst_W_ratio"], item["id"]))
    bases = [read(path) for path in (campaign / "bases").glob("b*/result.json")] if continuation else []
    def receipts(paths):
        return [receipt for path in paths if not any(".interrupted." in part for part in path.parts)
                if (receipt := read(path)).get("status") == "PASS"]
    trial_receipts = receipts((campaign / "trials").glob("n*/*/receipt.json" if continuation else "c*/*/receipt.json"))
    base_receipts = receipts((campaign / "bases").glob("b*/origins/*/receipt.json")) if continuation else []
    search_receipts = trial_receipts + base_receipts
    completion_receipts = receipts((campaign / "completion").glob("**/receipt.json"))
    search_fits = sum(receipt.get("real_model_fits", 1 if not continuation else 0) for receipt in search_receipts)
    completion_fits = sum(receipt.get("real_model_fits", 1 if not continuation else 0) for receipt in completion_receipts)
    counts = Counter(value.get("status", "unknown") for value in jobs.values())
    failed_jobs = sum(count for status, count in counts.items() if status in {"failed", "interrupted"} or status.startswith("blocked"))
    start = timestamp(state.get("started_utc"))
    requested_start = timestamp(contract.get("requested_start_utc"))
    deadline = timestamp(contract.get("deadline_utc") or state.get("deadline_utc") or protocol.get("deadline_utc"))
    search_deadline = timestamp(contract.get("search_deadline_utc") or protocol.get("search_stop_utc"))
    finished = timestamp(state.get("finished_utc"))
    elapsed_end = min(now, finished) if finished else now
    heartbeat = timestamp(state.get("heartbeat_utc"))
    progress = max(0., min(1., (now - requested_start).total_seconds() / (deadline - requested_start).total_seconds())) if requested_start and deadline and deadline > requested_start else None
    iso = lambda value: value.isoformat() if value else None
    kst = lambda value: value.astimezone(KST).isoformat() if value else None
    completion = read(campaign / "completion/result.json")
    return dict(
        schema_version=1, observed_utc=now.isoformat(),
        counters=dict(planned_trials=protocol.get("candidates", 2048) if continuation else protocol.get("candidate_count", 256), completed_trials=len(results),
            completed_search_trials=sum(result.get("id") != baseline_id for result in results),
            completed_bases=sum(base.get("status") == "PASS" for base in bases), planned_bases=protocol.get("bases", 32) if continuation else 0,
            search_fit_receipts=len(search_receipts), completion_fit_receipts=len(completion_receipts),
            total_fit_receipts=len(search_receipts) + len(completion_receipts),
            total_model_fits=search_fits + completion_fits,
            completed_generation_fits=sum(receipt.get("real_model_fits", 0) for receipt in base_receipts),
            completed_calibration_fits=sum(receipt.get("real_model_fits", 0) for receipt in trial_receipts) if continuation else 0,
            failed_jobs=failed_jobs,
            qualifying_trials=sum(item["eligible"] for item in ranking), job_status_counts=dict(counts)),
        runtime=dict(phase=phase, status=runtime_status, current_job=job_id,
            current_job_status=job.get("status"), current_fold=current_fold,
            current_fold_started_utc=current_fold_started, current_fit=current_fit,
            current_fit_expected=current_fit_expected,
            controller_alive=controller_alive, worker_alive=worker_alive, wrapper_alive=wrapper_alive,
            controller_pid=state.get("controller_identity", {}).get("pid"),
            worker_pid=started.get("worker_identity", {}).get("pid"),
            heartbeat_age_seconds=max(0., (now - heartbeat).total_seconds()) if heartbeat else None,
            stop_reason=state.get("stop_reason"), finished_utc=state.get("finished_utc")),
        time=dict(start_utc=iso(start), requested_start_utc=iso(requested_start),
            deadline_utc=iso(deadline), search_deadline_utc=iso(search_deadline),
            start_kst=kst(start), requested_start_kst=kst(requested_start), deadline_kst=kst(deadline),
            search_deadline_kst=kst(search_deadline),
            elapsed_seconds=max(0., (elapsed_end - start).total_seconds()) if start else None,
            remaining_seconds=max(0., (deadline - now).total_seconds()) if deadline else None,
            progress_fraction=progress, progress_basis="requested_start_to_hard_deadline"),
        latest_trials=sorted(ranking, key=lambda item: (item["completed_utc"] or "", item["id"]), reverse=True)[:20],
        ranking=dict(best_standalone=ranking[0] if ranking else None,
            best_primary_blend=min(ranking, key=lambda item: (item["primary_delta_W"], item["recent_delta_W"], item["id"])) if ranking else None),
        completion=completion or None,
        honesty=dict(official_score_queried=False, official_score_available=False,
            all_history_previously_exposed=True, new_independent_holdout=False,
            standalone_reference="c000 five-fold W; lower is better",
            blend_delta_definition="blend W minus official-best local replay W; negative is better"),
        warnings=warnings[:30], warning_count=len(warnings))


def build_status(campaign=CAMPAIGN, now=None, continuation_campaign=None):
    """Keep the initial campaign visible until the continuation actually starts."""
    campaign = Path(campaign)
    following = Path(continuation_campaign) if continuation_campaign else campaign.parent / "research_22h_20261107"
    now = now or datetime.now(timezone.utc)
    initial = _build_campaign_status(campaign, now)
    next_view = _build_campaign_status(following, now, continuation=True, baseline_campaign=campaign)
    warnings = initial["warnings"] + next_view["warnings"]
    def metadata(path):
        try:
            value = json.loads(path.read_text())
            if not isinstance(value, dict):
                raise ValueError("expected object")
            return value
        except FileNotFoundError:
            return {}
        except (OSError, ValueError):
            warnings.append(f"Unreadable continuation metadata: {path.name}")
            return {}
    authorization = metadata(following / "authorization.json")
    supervisor = metadata(following / "supervisor_state/state.json")
    next_started = bool(next_view["time"]["start_utc"] and next_view["runtime"]["controller_pid"])
    selected = next_view if next_started else initial
    runtime, timing = selected["runtime"], selected["time"]
    overall_deadline = timestamp(authorization.get("deadline_utc")) or timestamp(timing["deadline_utc"])
    requested = timestamp(initial["time"]["requested_start_utc"])
    timing.update(stage_deadline_utc=timing["deadline_utc"], stage_deadline_kst=timing["deadline_kst"],
        deadline_utc=overall_deadline.isoformat() if overall_deadline else None,
        deadline_kst=overall_deadline.astimezone(KST).isoformat() if overall_deadline else None,
        requested_start_utc=initial["time"]["requested_start_utc"], requested_start_kst=initial["time"]["requested_start_kst"],
        remaining_seconds=max(0., (overall_deadline - now).total_seconds()) if overall_deadline else None,
        overall_elapsed_seconds=sum(view["time"]["elapsed_seconds"] or 0 for view in (initial, next_view)),
        progress_fraction=max(0., min(1., (now - requested).total_seconds() / (overall_deadline - requested).total_seconds())) if requested and overall_deadline and overall_deadline > requested else None)
    job_id, phase = runtime["current_job"], runtime["phase"]
    if phase == "finished":
        stage = "finished" if next_started or not authorization else "waiting_continuation"
    elif phase == "blocked":
        stage = "blocked"
    elif phase in {"completion", "finalizing"}:
        stage = phase
    elif job_id and job_id.startswith("report"):
        stage = "reporting"
    elif next_started and not job_id:
        stage = "next_preparing"
    elif next_started and re.fullmatch(r"b\d+", job_id or ""):
        stage = "crossfit"
    elif next_started:
        stage = "calibration"
    else:
        stage = "initial_search"
    labels = dict(initial_search="기존 후보 탐색", crossfit="시계열 교차검증 기반 예측 준비",
        calibration="잔차 보정 후보 검증", completion="최종 재검증·재학습", finalizing="최종 보고서 정리",
        reporting="진행 보고서 정리", waiting_continuation="기존 작업 종료 · 연장 실행 대기",
        next_preparing="연장 연구 다음 작업 준비", finished="연구 실행 종료", blocked="실행 상태 확인 필요")
    heartbeat = timestamp(supervisor.get("heartbeat_utc"))
    checkpoint = supervisor.get("checkpoint_history", [])
    selected.update(schema_version=2,
        campaign=dict(id="continuation" if next_started else "initial", label="연장 연구" if next_started else "기존 10시간 연구",
            stage=stage, stage_label=labels[stage], overall_finished=stage == "finished"),
        supervisor=dict(phase=supervisor.get("phase", "not_started"),
            alive=process_alive(supervisor.get("supervisor_identity")),
            pid=supervisor.get("supervisor_identity", {}).get("pid"),
            heartbeat_age_seconds=max(0., (now - heartbeat).total_seconds()) if heartbeat else None,
            handoff_reason=supervisor.get("handoff_reason"), stop_reason=supervisor.get("stop_reason"),
            checkpoint_active=(supervisor.get("checkpoint_active") or {}).get("id"),
            last_checkpoint=checkpoint[-1] if checkpoint else None, checkpoint_blocked=supervisor.get("checkpoint_blocked")),
        previous_campaign=dict(completed_trials=initial["counters"]["completed_trials"], planned_trials=initial["counters"]["planned_trials"],
            total_model_fits=initial["counters"]["total_model_fits"], phase=initial["runtime"]["phase"]),
        cumulative=dict(completed_trials=initial["counters"]["completed_trials"] + next_view["counters"]["completed_trials"],
            total_model_fits=initial["counters"]["total_model_fits"] + next_view["counters"]["total_model_fits"]),
        extension=authorization or None, warnings=warnings[:30], warning_count=len(warnings))
    selected["honesty"].update(official_score_changed=False,
        standalone_reference="c000 five-fold W; lower is better; continuation raw-base ratios are separate")
    return selected


class StatusCache:
    def __init__(self):
        self.lock = threading.Lock()
        self.updated = 0.
        self.payload = None

    def get(self):
        with self.lock:
            if self.payload is None or time.monotonic() - self.updated >= 5:
                self.payload = json.dumps(build_status(), ensure_ascii=False, allow_nan=False).encode("utf-8")
                self.updated = time.monotonic()
            return self.payload


def inject_live_status(template, payload):
    """Embed JSON only in server-delivered pages, with HTML-safe string escaping."""
    safe_json = (payload.decode("utf-8").replace("<", "\\u003c")
                 .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))
    bootstrap = '<script id="oibc-live-data" type="application/json">' + safe_json + "</script>"
    return template.replace(b"<!--OIBC_LIVE_BOOTSTRAP-->", bootstrap.encode("utf-8"), 1)


class Handler(BaseHTTPRequestHandler):
    cache = StatusCache()

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/status":
            try:
                body = self.cache.get()
            except Exception:
                self.send_error(503, "Campaign metadata is temporarily unavailable")
                return
            content_type = "application/json; charset=utf-8"
        elif path == "/":
            try:
                template = HERE / "template.html"
                body = inject_live_status((template if template.exists() else HERE / "index.html").read_bytes(), self.cache.get())
            except Exception:
                self.send_error(503, "Viewer or campaign metadata is temporarily unavailable")
                return
            content_type = "text/html; charset=utf-8"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format_string, *args):
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.daemon_threads = True
    print(f"Read-only campaign viewer: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
