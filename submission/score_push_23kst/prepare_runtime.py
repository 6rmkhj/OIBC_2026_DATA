"""Freeze a serial campaign manifest and check it immediately before launch.

This program never launches training. Reuse the exact manifest/state directory
for restarts; completed jobs remain terminal and in-flight jobs are adopted by
the copied controller. STOP files are never removed or ignored.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import controller as runtime


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "analysis_outputs/research_23kst_20261108"
CONTROLLER = HERE / "controller.py"
DEADLINE = "2026-11-08T14:00:00Z"
SEARCH_STOP = "2026-11-08T12:00:00Z"
ORIGINAL_CONTROLLER_SHA256 = "c42ef72565eb49e1a0f72cb8098ca3c0a3a43e76514d18ef859db02c71d295ac"
OLD_CAMPAIGNS = [ROOT / "analysis_outputs" / name for name in ("research_10h_20261107", "research_22h_20261107")]
OLD_STATE_DIRS = [path / "controller_state" for path in OLD_CAMPAIGNS]
OLD_ENGINE_FILES = [ROOT / "submission" / name / "engine.py" for name in ("score_push_10h", "score_push_22h")]
OLD_CONTROLLER_FILES = [path.with_name("controller.py") for path in OLD_ENGINE_FILES]


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def resolve(path, working_directory):
    path = Path(path)
    return (path if path.is_absolute() else Path(working_directory) / path).resolve()


def strict_identity(pid):
    """An inaccessible process is unknown, never evidence of termination."""
    try:
        fields = Path(f"/proc/{int(pid)}/stat").read_text().rsplit(")", 1)[1].split()
        return dict(pid=int(pid), pgid=int(fields[2]), start_ticks=int(fields[19]), state=fields[0],
                    boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip())
    except (FileNotFoundError, ProcessLookupError):
        return None
    except (PermissionError, OSError, ValueError, IndexError) as error:
        raise RuntimeError(f"Cannot verify process identity for PID {pid}: {type(error).__name__}; no launch permitted") from error


def strict_alive(saved):
    if not saved:
        return False
    current = strict_identity(saved["pid"])
    return bool(current and current["state"] not in {"Z", "X"} and
                all(current[key] == saved[key] for key in ("pid", "pgid", "start_ticks", "boot_id")))


def process_arguments(path):
    try:
        return path.joinpath("cmdline").read_bytes().decode(errors="replace").split("\0")
    except (FileNotFoundError, ProcessLookupError):
        return []
    except (PermissionError, OSError) as error:
        raise RuntimeError(f"Cannot inspect PID {path.name}: {type(error).__name__}; no launch permitted") from error


def prior_campaigns_terminal(state_dirs, engine_files=()):
    """Read-only gate including descendants whose recorded leaders have died."""
    records, anchors = [], []
    for directory in map(Path, state_dirs):
        for stop in (directory / "STOP", directory.parent / "supervisor_state/STOP"):
            require(not stop.exists(), f"STOP exists and requires explicit resolution: {stop}")
        state_path = directory / "state.json"
        state = runtime.read(state_path)
        require(state.get("phase") == "finished", f"Prior campaign is not finished: {directory}")
        require(state.get("stop_reason") != "stopped", f"Prior campaign was explicitly stopped: {directory}")
        require(state.get("controller_sha256") == ORIGINAL_CONTROLLER_SHA256, f"Unexpected prior controller source: {directory}")
        jobs = state.get("jobs", {})
        require(all(job.get("status") in runtime.TERMINAL | {"pending"} for job in jobs.values()),
                f"Prior campaign has in-flight or blocked job records: {directory}")
        anchors.append(state.get("controller_identity"))
        for path in (directory / "jobs").glob("*/started.json"):
            started = runtime.read(path)
            job = jobs.get(path.parent.name, {})
            require(started.get("nonce") == job.get("nonce") and started.get("manifest_sha256") == state["manifest_sha256"],
                    f"Prior job execution identity mismatch: {path}")
            anchors.extend((started.get("identity"), started.get("worker_identity")))
        anchors.extend(job.get("wrapper_identity") for job in jobs.values())
        supervisor_path = directory.parent / "supervisor_state/state.json"
        supervisor = runtime.read(supervisor_path) if supervisor_path.exists() else None
        if supervisor:
            require(supervisor.get("phase") == "finished", f"Prior supervisor is not finished: {supervisor_path}")
            anchors.append(supervisor.get("supervisor_identity"))
            for path in supervisor_path.parent.glob("checkpoints/*/started.json"):
                started = runtime.read(path)
                require(started.get("manifest_sha256") == supervisor["spec_sha256"], f"Prior checkpoint identity mismatch: {path}")
                anchors.extend((started.get("identity"), started.get("worker_identity")))
        records.append(dict(state_dir=str(directory.resolve()), state_sha256=runtime.digest(state_path),
            manifest_sha256=state["manifest_sha256"], controller_sha256=state["controller_sha256"],
            finished_utc=state.get("finished_utc"), jobs=len(jobs),
            supervisor_state_sha256=runtime.digest(supervisor_path) if supervisor else None))
    anchors = [anchor for anchor in anchors if anchor]
    require(not any(strict_alive(anchor) for anchor in anchors), "A recorded prior controller/supervisor/wrapper/worker is still alive")
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    groups = {anchor["pgid"] for anchor in anchors if anchor.get("boot_id") == boot}
    entrypoints = {str(Path(path).resolve()) for path in engine_files}
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        identity = strict_identity(int(path.name))
        if not identity or identity["state"] in {"Z", "X"}:
            continue
        require(identity["pgid"] not in groups, f"A prior process group still has a live member: PID {path.name}")
        if int(path.name) == os.getpid():
            continue
        arguments = process_arguments(path)
        require(not entrypoints.intersection(arguments), f"A known prior learning entrypoint is still running: PID {path.name}")
    return records


def validate_jobs(jobs, completion, finalizer):
    require(isinstance(jobs, list) and isinstance(completion, list), "jobs and completion_jobs must be lists")
    require(bool(completion), "At least one bounded completion job is required")
    ordered = jobs + completion
    all_jobs = ordered + [finalizer]
    require(len({job["id"] for job in all_jobs}) == len(all_jobs), "Job IDs must be unique, including finalizer")
    preceding = set()
    for job in all_jobs:
        runtime.validate_job(job)
        require(math.isfinite(float(job.get("estimated_seconds", 0))), "Estimated duration must be finite")
        require(set(job.get("requires_success", [])).issubset(preceding), f"Dependencies must precede their job: {job['id']}")
        preceding.add(job["id"])
        if "complete" in job["argv"]:
            require("--deadline-utc" in job["argv"], "Completion must receive the absolute deadline")
            offset = job["argv"].index("--deadline-utc") + 1
            require(offset < len(job["argv"]) and runtime.timestamp(job["argv"][offset]) == runtime.timestamp(DEADLINE),
                    "Completion deadline does not match the authorized deadline")
    require(finalizer["argv"][-1] == "report", "Finalizer must be the report-only CLI command")
    require(not finalizer.get("requires_success"), "The terminal report must run even when search/completion fails")


def check_learning_processes(entrypoints, state_dir, state):
    """Allow only the verified new campaign's existing group during adoption."""
    anchors, terminal_groups, active_workers = [], set(), []
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    if state:
        for path in (Path(state_dir) / "jobs").glob("*/started.json"):
            started = runtime.read(path)
            job = state.get("jobs", {}).get(path.parent.name, {})
            require(started.get("manifest_sha256") == state["manifest_sha256"] and started.get("nonce") == job.get("nonce"),
                    f"Current job execution identity mismatch: {path}")
            recorded = [started.get("identity"), started.get("worker_identity")]
            if job.get("status") in runtime.TERMINAL:
                require(not any(strict_alive(anchor) for anchor in recorded if anchor),
                        f"Terminal job still owns a live process: {path.parent.name}")
                terminal_groups.update(anchor["pgid"] for anchor in recorded if anchor and anchor.get("boot_id") == boot)
            else:
                require(job.get("status") in {"launching", "running"}, f"Ambiguous current job needs inspection: {path.parent.name}")
                anchors.extend(recorded)
                if strict_alive(started.get("worker_identity")):
                    active_workers.append(started["worker_identity"])
    owned_groups = {anchor["pgid"] for anchor in anchors if anchor and strict_alive(anchor)}
    require(len(owned_groups) <= 1 and len(active_workers) <= 1, "Multiple active learning workers/groups; no new launch permitted")
    expected = {str(Path(path).resolve()) for path in entrypoints}
    adopted = []
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        identity = strict_identity(int(path.name))
        if not identity or identity["state"] in {"Z", "X"}:
            continue
        require(identity["pgid"] not in terminal_groups, f"Terminal job process group still has a live member: PID {path.name}")
        if int(path.name) == os.getpid():
            continue
        arguments = process_arguments(path)
        if expected.intersection(arguments):
            require(identity["pgid"] in owned_groups, f"Unowned learning entrypoint is still active: PID {path.name}")
            adopted.append(identity)
    require(len(adopted) <= 1, "Multiple active learning entrypoints; no new launch permitted")
    return adopted


def frozen_write(path, value):
    path = Path(path)
    if path.exists():
        require(runtime.read(path) == value, f"Refusing to replace a different frozen artifact: {path}")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        runtime.atomic(path, value)


def build(jobs_path, protocol_path, completion_path, finalizer_path, pins=(),
          manifest_path=OUT / "controller_manifest.json", contract_path=OUT / "launch_contract.json",
          state_dir=OUT / "controller_state", working_directory=ROOT,
          old_state_dirs=OLD_STATE_DIRS, old_engine_files=OLD_ENGINE_FILES,
          old_controller_files=OLD_CONTROLLER_FILES):
    working_directory = Path(working_directory).resolve()
    state_dir = Path(state_dir).resolve()
    manifest_path, contract_path = Path(manifest_path).resolve(), Path(contract_path).resolve()
    controller_sha256 = runtime.digest(CONTROLLER)
    for old in map(Path, old_state_dirs):
        require(not state_dir.is_relative_to(old.resolve()), "New state must not be inside a prior campaign state directory")
        require(not manifest_path.is_relative_to(old.parent.resolve()), "New manifest must not modify a prior campaign")
    require(not (state_dir / "STOP").exists(), "New campaign STOP exists; do not remove it automatically")
    prior = prior_campaigns_terminal(old_state_dirs, old_engine_files)
    for source in map(Path, old_controller_files):
        require(runtime.digest(source) == ORIGINAL_CONTROLLER_SHA256, f"Prior controller source changed: {source}")
    jobs_path, protocol_path, completion_path, finalizer_path = map(Path, (jobs_path, protocol_path, completion_path, finalizer_path))
    jobs, protocol = runtime.read(jobs_path), runtime.read(protocol_path)
    completion, finalizer = runtime.read(completion_path), runtime.read(finalizer_path)
    validate_jobs(jobs, completion, finalizer)
    source_pins = protocol.get("source_sha256")
    require(isinstance(source_pins, dict) and bool(source_pins), "Protocol must identify frozen source_sha256 inputs")
    expected = {**source_pins, **protocol.get("input_sha256", {})}
    pinned = {}
    for name, digest in expected.items():
        path = resolve(name, working_directory)
        require(runtime.digest(path) == digest, f"Protocol input hash mismatch: {path}")
        pinned[str(path)] = digest
    for name, path in (("jobs_sha256", jobs_path), ("configs_sha256", protocol_path.parent / "configs.json"),
                       ("bases_sha256", protocol_path.parent / "bases.json")):
        if name in protocol:
            require(runtime.digest(path) == protocol[name], f"Protocol {name} does not match its artifact")
            pinned[str(path.resolve())] = protocol[name]
    fixed_files = [jobs_path, protocol_path, completion_path, finalizer_path, CONTROLLER, Path(__file__),
                   *map(Path, pins), *map(Path, old_controller_files),
                   *(Path(item["state_dir"]) / "state.json" for item in prior)]
    fixed_files.extend(Path(item["state_dir"]).parent / "supervisor_state/state.json"
                       for item in prior if item["supervisor_state_sha256"])
    for job in jobs + completion + [finalizer]:
        scripts = [resolve(argument, working_directory) for argument in job["argv"] if argument.endswith(".py")]
        require(bool(scripts), f"Expected an explicit pinned Python entrypoint: {job['id']}")
        fixed_files.extend(scripts)
    for path in fixed_files:
        path = resolve(path, working_directory)
        actual = runtime.digest(path)
        require(str(path) not in pinned or pinned[str(path)] == actual, f"Conflicting input pins: {path}")
        pinned[str(path)] = actual
    manifest = dict(version=1, deadline_utc=DEADLINE, working_directory=str(working_directory),
        reserve_seconds=60, completion_reserve_seconds=7200, poll_seconds=2, heartbeat_seconds=15,
        termination_grace_seconds=10, environment={"PYTHONDONTWRITEBYTECODE": "1"},
        input_sha256=pinned, jobs=jobs, completion_jobs=completion, finalizer=finalizer,
        finalizer_timeout_seconds=90,
        resource_stop={"path": str(manifest_path.parent / "budget_stop.json")},
        runtime_preflight=dict(old_state_dirs=[str(Path(path).resolve()) for path in old_state_dirs],
            old_engine_files=[str(Path(path).resolve()) for path in old_engine_files],
            old_controller_files=[str(Path(path).resolve()) for path in old_controller_files],
            learning_entrypoints=sorted({str(resolve(argument, working_directory))
                for job in jobs + completion + [finalizer] for argument in job["argv"] if argument.endswith(".py")}
                | {str(Path(path).resolve()) for path in old_engine_files}
                | {str(path.resolve()) for path in (ROOT / "submission").glob("score_push_*/engine.py")}
                | {str(ROOT / "submission/autoresearch/train.py")}),
            state_dir=str(state_dir), search_stop_utc=SEARCH_STOP, prior_campaigns=prior,
            controller_sha256=controller_sha256, contract_file=str(contract_path)))
    frozen_write(manifest_path, manifest)
    if contract_path.exists():
        existing = runtime.read(contract_path)
        require(existing.get("controller_manifest_sha256") == runtime.digest(manifest_path), "Existing launch contract belongs to a different manifest")
        return existing
    contract = dict(version=1, created_utc=runtime.now(), status="prepared_not_launched",
        deadline_utc=DEADLINE, deadline_kst="2026-11-08T23:00:00+09:00", search_stop_utc=SEARCH_STOP,
        completion_reserve_seconds=7200, controller_manifest=str(manifest_path),
        controller_manifest_sha256=runtime.digest(manifest_path), controller_sha256=controller_sha256,
        original_controller_sha256=ORIGINAL_CONTROLLER_SHA256,
        prepare_runtime_sha256=runtime.digest(__file__), state_dir=str(state_dir),
        thread_limits={"ML_parallel_fits": 1, "CPU": 4, "BLAS": 1},
        queued_search_jobs=len(jobs), queued_completion_jobs=len(completion), fixed_input_count=len(pinned),
        prior_campaigns=prior, fresh_preflight_required_before_launch=True,
        preflight_argv=[sys.executable, str(Path(__file__).resolve()), "preflight", "--manifest", str(manifest_path), "--state-dir", str(state_dir)],
        start_or_resume_argv=[sys.executable, str(CONTROLLER), "--manifest", str(manifest_path), "--state-dir", str(state_dir), "--detach"],
        completed_jobs_reused=True, automatic_job_retries=False, stop_files_respected=True,
        official_score_available=False, uploaded=False)
    frozen_write(contract_path, contract)
    return contract


def preflight(manifest_path, state_dir=None):
    manifest_path = Path(manifest_path).resolve()
    manifest = runtime.read(manifest_path)
    details = manifest["runtime_preflight"]
    contract = runtime.read(details["contract_file"])
    require(contract["controller_manifest_sha256"] == runtime.digest(manifest_path), "Frozen manifest changed after preparation")
    state_dir = Path(state_dir or details["state_dir"]).resolve()
    require(str(state_dir) == details["state_dir"], "Use the exact frozen state directory for launch/restart")
    require(not (state_dir / "STOP").exists(), "New campaign STOP exists; explicit resolution is required")
    require(runtime.timestamp(manifest["deadline_utc"]) == runtime.timestamp(DEADLINE), "Unexpected hard deadline")
    require(manifest["completion_reserve_seconds"] == 7200 and
            runtime.timestamp(manifest["deadline_utc"]) - 7200 == runtime.timestamp(SEARCH_STOP), "Search/completion budget changed")
    require(runtime.digest(CONTROLLER) == details["controller_sha256"] == contract["controller_sha256"], "Controller source changed")
    runtime.check_inputs(manifest["input_sha256"], manifest["working_directory"])
    prior = prior_campaigns_terminal(details["old_state_dirs"], details["old_engine_files"])
    for source in details["old_controller_files"]:
        require(runtime.digest(source) == ORIGINAL_CONTROLLER_SHA256, f"Prior controller source changed: {source}")
    state_path = state_dir / "state.json"
    state = runtime.read(state_path) if state_path.exists() else {}
    if state:
        require(state["manifest_sha256"] == runtime.digest(manifest_path), "Existing state belongs to another manifest")
        require(state["controller_sha256"] == details["controller_sha256"], "Existing state belongs to another controller")
        known_jobs = {job["id"] for job in manifest["jobs"] + manifest["completion_jobs"] + [manifest["finalizer"]]}
        for job_id, job in state.get("jobs", {}).items():
            require(job_id in known_jobs, f"Unknown job in existing controller state: {job_id}")
            folder = state_dir / "jobs" / job_id
            if job.get("status") in {"launching", "running", "completed", "failed", "interrupted", "time_limit", "stopped"}:
                require(job.get("attempts") == 1, f"Unexpected attempt count for recorded execution: {job_id}")
            if job.get("attempts", 0):
                require(runtime.digest(folder / "spec.json") == job.get("spec_sha256"), f"Stored job spec changed: {job_id}")
            if job.get("receipt_sha256"):
                require(runtime.digest(folder / "receipt.json") == job["receipt_sha256"], f"Stored terminal receipt changed: {job_id}")
    adopted = check_learning_processes(details["learning_entrypoints"], state_dir, state)
    status = "already_running" if strict_alive(state.get("controller_identity")) else "already_finished" if state.get("phase") == "finished" else "ready_to_resume" if state else "ready_to_start"
    require(runtime.timestamp(DEADLINE) > runtime.datetime.now(runtime.timezone.utc).timestamp() or status == "already_finished",
            "Authorized hard deadline has passed; no new launch")
    return dict(status=status, checked_utc=runtime.now(), manifest_sha256=runtime.digest(manifest_path),
        state_dir=str(state_dir), prior_campaigns=prior, fixed_inputs_verified=len(manifest["input_sha256"]),
        completed_jobs_reused=sum(job.get("status") == "completed" for job in state.get("jobs", {}).values()),
        recorded_current_job=state.get("current_job"), automatic_retries=False,
        adopted_learning_processes=adopted,
        deadline_utc=DEADLINE, search_stop_utc=SEARCH_STOP)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    builder = subparsers.add_parser("build")
    builder.add_argument("--jobs", type=Path, required=True)
    builder.add_argument("--protocol", type=Path, required=True)
    builder.add_argument("--completion-jobs", type=Path, required=True)
    builder.add_argument("--finalizer-job", type=Path, required=True)
    builder.add_argument("--pin", type=Path, action="append", default=[])
    builder.add_argument("--manifest", type=Path, default=OUT / "controller_manifest.json")
    builder.add_argument("--contract", type=Path, default=OUT / "launch_contract.json")
    builder.add_argument("--state-dir", type=Path, default=OUT / "controller_state")
    checker = subparsers.add_parser("preflight")
    checker.add_argument("--manifest", type=Path, default=OUT / "controller_manifest.json")
    checker.add_argument("--state-dir", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        result = build(args.jobs, args.protocol, args.completion_jobs, args.finalizer_job,
                       pins=args.pin, manifest_path=args.manifest, contract_path=args.contract, state_dir=args.state_dir)
    else:
        result = preflight(args.manifest, args.state_dir)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
