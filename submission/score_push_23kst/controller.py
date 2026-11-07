"""Durable serial experiment queue with an absolute UTC wall-time deadline.

Use --manifest FILE --state-dir DIR [--detach]. A STOP file requests cancellation.
Every fit runs through a separately supervised session; even a lost controller
cannot disable the worker's deadline. Existing/ambiguous jobs are never retried.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
import uuid

THREAD_ENV = {"OMP_NUM_THREADS": "4", "OPENBLAS_NUM_THREADS": "1",
              "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1",
              "PYTHONDONTWRITEBYTECODE": "1"}
TERMINAL = {"completed", "failed", "interrupted", "time_limit", "stopped", "deferred_budget", "skipped_dependency"}


def now():
    return datetime.now(timezone.utc).isoformat()


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("deadline_utc must include a timezone")
    return parsed.timestamp()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def atomic(path, value):
    path = Path(path)
    temp = path.with_name(path.name + f".tmp.{os.getpid()}")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def identity(pid):
    try:
        parts = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return {"pid": int(pid), "pgid": int(parts[2]), "start_ticks": int(parts[19]),
                "boot_id": Path("/proc/sys/kernel/random/boot_id").read_text().strip(),
                "state": parts[0]}
    except (FileNotFoundError, ProcessLookupError):
        return None


def alive(saved):
    if not saved:
        return False
    current = identity(saved["pid"])
    return bool(current and current["state"] not in {"Z", "X"} and
                all(current[k] == saved[k] for k in ("pid", "pgid", "start_ticks", "boot_id")))


def group_members(pgid, exclude=()):
    found = []
    for path in Path("/proc").iterdir():
        if path.name.isdigit() and int(path.name) not in exclude:
            record = identity(int(path.name))
            if record and record["pgid"] == pgid and record["state"] not in {"Z", "X"}:
                found.append(record)
    return found


def signal_owned_group(anchors, sig):
    """Never signal a numeric PID/PGID unless a recorded live identity matches."""
    for anchor in anchors:
        if alive(anchor):
            assert anchor["pgid"] > 1 and anchor["pgid"] != os.getpgrp()
            try:
                os.killpg(anchor["pgid"], sig)
                return True
            except ProcessLookupError:
                pass
    return False


def validate_job(job):
    assert re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", job["id"])
    assert isinstance(job["argv"], list) and job["argv"]
    assert all(isinstance(x, str) and x and "\x00" not in x for x in job["argv"])
    assert float(job.get("estimated_seconds", 0)) >= 0


def check_inputs(mapping, cwd):
    for filename, expected in mapping.items():
        path = Path(filename)
        if not path.is_absolute():
            path = Path(cwd) / path
        assert digest(path) == expected, f"Pinned input changed: {filename}"


def wrapper(spec_path, spec_hash):
    """Session anchor, execution receipt and independent deadline watchdog."""
    assert digest(spec_path) == spec_hash
    spec = read(spec_path)
    assert digest(__file__) == spec["controller_sha256"]
    check_inputs(spec.get("input_sha256", {}), spec["working_directory"])
    directory = Path(spec_path).parent
    assert os.getpgrp() == os.getpid(), "Wrapper must own its process session"
    with (directory / "execution.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not (directory / "started.json").exists(), "No repeated execution"
        cancelled = [None]
        signal.signal(signal.SIGTERM, lambda *_: cancelled.__setitem__(0, cancelled[0] or "signal"))
        signal.signal(signal.SIGINT, lambda *_: cancelled.__setitem__(0, cancelled[0] or "signal"))
        record = {"nonce": spec["nonce"], "manifest_sha256": spec["manifest_sha256"],
                  "identity": identity(os.getpid()), "started_utc": now(), "argv": spec["argv"]}
        atomic(directory / "started.json", record)
        # A delayed scheduler or a STOP racing with controller launch must not
        # start a fresh fit after its budget has already expired.
        precluded = "time_limit" if time.time() >= spec["deadline_timestamp"] else cancelled[0]
        if spec.get("stop_file") and Path(spec["stop_file"]).exists():
            precluded = "stopped"
        if precluded:
            atomic(directory / "receipt.json", {**record, "finished_utc": now(),
                   "exit_code": None, "status": precluded, "worker_launched": False,
                   "all_worker_processes_terminal": True})
            return 0
        environment = {**os.environ, **spec.get("environment", {}), **THREAD_ENV}
        process = subprocess.Popen(spec["argv"], cwd=spec["working_directory"], env=environment,
                                   close_fds=True, stdin=subprocess.DEVNULL)
        record["worker_identity"] = identity(process.pid)
        record["worker_launched"] = True
        atomic(directory / "started.json", record)
        term_sent = None
        while True:
            code = process.poll()
            if time.time() >= spec["deadline_timestamp"]:
                cancelled[0] = "time_limit"
            if spec.get("stop_file") and Path(spec["stop_file"]).exists():
                cancelled[0] = "stopped"
            others = group_members(os.getpgrp(), exclude=(os.getpid(),))
            if code is not None and not others:
                status = cancelled[0] or ("completed" if code == 0 else "failed")
                atomic(directory / "receipt.json", {**record, "finished_utc": now(),
                       "exit_code": code, "status": status, "all_worker_processes_terminal": True})
                return 0
            if code is not None and others and not cancelled[0]:
                cancelled[0] = "worker_left_descendants"
            if cancelled[0] and term_sent is None:
                term_sent = time.monotonic()
                atomic(directory / "termination_requested.json", {"reason": cancelled[0], "utc": now(),
                       "identity": record["identity"], "escalated": False})
                os.killpg(os.getpgrp(), signal.SIGTERM)
            elif term_sent is not None and time.monotonic() - term_sent >= spec["termination_grace_seconds"]:
                atomic(directory / "termination_requested.json", {"reason": cancelled[0], "utc": now(),
                       "identity": record["identity"], "escalated": True})
                os.killpg(os.getpgrp(), signal.SIGKILL)
            time.sleep(min(.5, spec["poll_seconds"]))


class Controller:
    def __init__(self, manifest_path, directory):
        self.path, self.directory = Path(manifest_path).resolve(), Path(directory).resolve()
        self.manifest = read(self.path)
        assert self.manifest.get("version") == 1
        self.deadline = timestamp(self.manifest["deadline_utc"])
        self.cwd = str(Path(self.manifest["working_directory"]).resolve())
        assert Path(self.cwd).is_dir()
        self.poll = max(.05, min(10., float(self.manifest.get("poll_seconds", 2))))
        self.heartbeat = max(.1, float(self.manifest.get("heartbeat_seconds", 15)))
        self.grace = max(.1, float(self.manifest.get("termination_grace_seconds", 10)))
        self.reserve = max(0., float(self.manifest.get("reserve_seconds", 60)))
        self.completion_reserve = max(0., float(self.manifest.get("completion_reserve_seconds", 0)))
        resource_stop = self.manifest.get("resource_stop")
        self.resource_stop = Path(resource_stop["path"]).resolve() if resource_stop else None
        if self.resource_stop:
            assert self.resource_stop.is_relative_to(self.path.parent) and self.resource_stop != self.path, "Resource stop must be inside this campaign"
        self.jobs = self.manifest["jobs"]
        self.completion = self.manifest.get("completion_jobs", [])
        self.all_jobs = self.jobs + self.completion
        assert isinstance(self.jobs, list) and isinstance(self.completion, list)
        assert len({j["id"] for j in self.all_jobs}) == len(self.all_jobs)
        for job in self.all_jobs:
            validate_job(job)
            assert all(dependency in {j["id"] for j in self.all_jobs}
                       for dependency in job.get("requires_success", []))
        if self.manifest.get("finalizer"):
            validate_job(self.manifest["finalizer"])
            assert self.manifest["finalizer"]["id"] not in {j["id"] for j in self.all_jobs}
        self.manifest_hash, self.source_hash = digest(self.path), digest(__file__)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.state_path = self.directory / "state.json"
        self.lock = None
        self.state = None
        self.child_handles = {}
        self.last_heartbeat = 0.

    def persist(self, event=None, **details):
        self.state["heartbeat_utc"] = now()
        atomic(self.state_path, self.state)
        self.last_heartbeat = time.monotonic()
        if event:
            with (self.directory / "events.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"utc": now(), "event": event, **details}) + "\n")
                handle.flush()
                os.fsync(handle.fileno())

    def initialize(self):
        self.lock = (self.directory / "controller.lock").open("a+b")
        fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if self.state_path.exists():
            self.state = read(self.state_path)
            assert self.state["manifest_sha256"] == self.manifest_hash, "Manifest changed; no implicit amendment"
            assert self.state["controller_sha256"] == self.source_hash, "Controller changed; no implicit amendment"
        else:
            self.state = {"version": 1, "manifest_sha256": self.manifest_hash, "controller_sha256": self.source_hash,
                          "started_utc": now(), "deadline_utc": self.manifest["deadline_utc"], "jobs": {},
                          "phase": "starting", "current_job": None}
            for job in self.all_jobs:
                self.state["jobs"][job["id"]] = {"status": "pending", "attempts": 0}
        check_inputs(self.manifest.get("input_sha256", {}), self.cwd)
        self.state["controller_identity"] = identity(os.getpid())
        self.persist("controller_started")

    def execute(self, job, deadline=None, finalizer=False):
        job_id = job["id"]
        deadline = self.deadline if deadline is None else deadline
        entry = self.state["jobs"].setdefault(job_id, {"status": "pending", "attempts": 0})
        if entry["status"] in TERMINAL:
            return entry["status"]
        directory = self.directory / "jobs" / job_id
        directory.mkdir(parents=True, exist_ok=True)
        self.state["current_job"] = job_id
        if entry["status"] == "pending":
            assert not (directory / "started.json").exists(), "Unrecorded prior execution"
            pinned = {**self.manifest.get("input_sha256", {}), **job.get("input_sha256", {})}
            check_inputs(pinned, self.cwd)
            nonce = uuid.uuid4().hex
            spec = {"nonce": nonce, "manifest_sha256": self.manifest_hash, "argv": job["argv"],
                    "controller_sha256": self.source_hash, "input_sha256": pinned,
                    "working_directory": self.cwd, "environment": self.manifest.get("environment", {}),
                    "deadline_timestamp": deadline, "termination_grace_seconds": self.grace, "poll_seconds": self.poll,
                    "stop_file": None if finalizer else str(self.directory / "STOP")}
            atomic(directory / "spec.json", spec)
            entry.update(status="launching", attempts=1, nonce=nonce, launched_utc=now(),
                         spec_sha256=digest(directory / "spec.json"))
            self.persist("job_launching", job_id=job_id)
            with (directory / "run.log").open("ab", buffering=0) as log:
                process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--job-wrapper",
                    str(directory / "spec.json"), "--spec-sha256", entry["spec_sha256"]],
                    cwd=self.cwd, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                    start_new_session=True, close_fds=True, env={**os.environ, **THREAD_ENV})
            self.child_handles[job_id] = process
            entry["wrapper_identity"] = identity(process.pid)
            entry["effective_deadline_timestamp"] = deadline
            self.persist("job_spawned", job_id=job_id, identity=entry["wrapper_identity"])
        else:
            deadline = read(directory / "spec.json")["deadline_timestamp"]
        started_path, receipt_path = directory / "started.json", directory / "receipt.json"
        # A crash between Popen and identity persistence cannot safely imply no fit.
        if not entry.get("wrapper_identity") and not started_path.exists():
            limit = time.monotonic() + 10
            while time.monotonic() < limit and not started_path.exists():
                time.sleep(self.poll)
            if not started_path.exists():
                entry["status"] = "blocked_ambiguous_launch"
                self.persist("ambiguous_launch_no_retry", job_id=job_id)
                return entry["status"]
        termination = None
        while True:
            started = read(started_path) if started_path.exists() else None
            if started:
                assert started["nonce"] == entry["nonce"] and started["manifest_sha256"] == self.manifest_hash
                entry["wrapper_identity"] = started["identity"]
                if entry["status"] == "launching":
                    entry["status"] = "running"
                    self.persist("job_running", job_id=job_id)
            anchor = entry.get("wrapper_identity")
            anchors = [anchor] + ([started.get("worker_identity")] if started else [])
            anchors = [a for a in anchors if a]
            handle = self.child_handles.get(job_id)
            if handle:
                handle.poll()  # Reap a completed child before evaluating its /proc identity.
            if receipt_path.exists() and not alive(anchor):
                receipt = read(receipt_path)
                assert receipt["nonce"] == entry["nonce"] and receipt["manifest_sha256"] == self.manifest_hash
                status = receipt["status"]
                if status not in TERMINAL:
                    status = "stopped" if finalizer else "failed"
                entry.update(status=status, exit_code=receipt["exit_code"], finished_utc=receipt["finished_utc"],
                             receipt_sha256=digest(receipt_path))
                break
            reason = "time_limit" if time.time() >= deadline else None
            if not finalizer and (self.directory / "STOP").exists():
                reason = "stopped"
            if reason and termination is None:
                termination = time.monotonic()
                entry["termination_reason"] = reason
                signal_owned_group(anchors, signal.SIGTERM)
                self.persist("job_termination_requested", job_id=job_id, reason=reason)
            elif termination is not None and time.monotonic() - termination >= self.grace:
                signal_owned_group(anchors, signal.SIGKILL)
            if not alive(anchor):
                members = group_members(anchor["pgid"]) if anchor else []
                if members:
                    if not signal_owned_group(anchors, signal.SIGTERM):
                        entry["status"] = "blocked_orphan_group"
                        entry["unresolved_group_id"] = anchor["pgid"]
                        self.persist("unverified_orphan_group_no_new_fit", job_id=job_id)
                        return entry["status"]
                else:
                    entry.update(status=reason or entry.get("termination_reason") or "interrupted",
                                 exit_code=None, finished_utc=now(), no_terminal_receipt=True)
                    break
            if time.monotonic() - self.last_heartbeat >= self.heartbeat:
                self.persist()
            time.sleep(self.poll)
        self.state["current_job"] = None
        self.persist("job_terminal", job_id=job_id, status=entry["status"], exit_code=entry.get("exit_code"))
        return entry["status"]

    def run(self):
        self.initialize()
        try:
            self.state["phase"] = "running"
            self.persist()
            # First adopt any recorded in-flight work; never race it with a new fit.
            for job in self.all_jobs:
                if self.state["jobs"][job["id"]]["status"] not in TERMINAL | {"pending"}:
                    if self.execute(job).startswith("blocked"):
                        self.state["phase"] = "blocked"
                        self.persist("controller_blocked")
                        return 2
            reason = "queue_exhausted"
            phases = [("search", self.jobs, self.deadline - self.completion_reserve),
                      ("completion", self.completion, self.deadline)]
            for phase, jobs, phase_deadline in phases:
                self.state["phase"] = phase
                self.persist("phase_started", phase=phase)
                for job in jobs:
                    entry = self.state["jobs"][job["id"]]
                    if entry["status"] != "pending":
                        continue
                    if (self.directory / "STOP").exists():
                        reason = "stopped"
                        break
                    if phase == "search" and self.resource_stop and self.resource_stop.exists():
                        assert self.resource_stop.resolve().is_relative_to(self.path.parent), "Resource stop escaped this campaign"
                        marker = read(self.resource_stop)
                        if marker.get("status") == "STORAGE_BUDGET_EXHAUSTED":
                            entry.update(status="deferred_budget", deferred_reason="storage",
                                         resource_stop_status=marker["status"])
                            reason = "storage_budget_exhausted"
                            self.persist("job_deferred", job_id=job["id"], phase=phase, reason="storage")
                            continue
                    remaining = phase_deadline - time.time()
                    if remaining <= self.reserve or float(job.get("estimated_seconds", 0)) + self.reserve > remaining:
                        entry.update(status="deferred_budget", deferred_insufficient_seconds=remaining)
                        reason = "time_limit" if time.time() >= self.deadline else "budget_reserved"
                        self.persist("job_deferred", job_id=job["id"], phase=phase, remaining_seconds=remaining)
                        continue
                    dependencies = job.get("requires_success", [])
                    if any(self.state["jobs"][d]["status"] != "completed" for d in dependencies):
                        entry.update(status="skipped_dependency", requires_success=dependencies)
                        self.persist("dependency_not_successful", job_id=job["id"])
                        continue
                    status = self.execute(job, phase_deadline)
                    if status.startswith("blocked"):
                        self.state["phase"] = "blocked"
                        self.persist("controller_blocked")
                        return 2
                    if status in {"stopped", "time_limit"}:
                        reason = status if phase == "completion" else "search_budget_finished"
                if (self.directory / "STOP").exists():
                    reason = "stopped"
                    break
            self.state["work_finished_utc"] = now()
            self.state["stop_reason"] = reason
            if self.manifest.get("finalizer"):
                self.state["phase"] = "finalizing"
                self.persist("finalizer_started")
                timeout = min(120., max(1., float(self.manifest.get("finalizer_timeout_seconds", 30))))
                self.execute(self.manifest["finalizer"], time.time() + timeout, finalizer=True)
            self.state["phase"] = "finished"
            self.state["finished_utc"] = now()
            self.state["counts"] = {status: sum(j["status"] == status for j in self.state["jobs"].values())
                                    for status in sorted({j["status"] for j in self.state["jobs"].values()})}
            self.persist("controller_finished", stop_reason=reason, counts=self.state["counts"])
            return 0
        finally:
            self.lock.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--detach", action="store_true")
    parser.add_argument("--job-wrapper", type=Path)
    parser.add_argument("--spec-sha256")
    args = parser.parse_args()
    if args.job_wrapper:
        return wrapper(args.job_wrapper, args.spec_sha256)
    assert args.manifest and args.state_dir
    controller = Controller(args.manifest, args.state_dir)
    if args.detach:
        # The child's lock is authoritative; launcher waits for its identity, not
        # merely successful Popen, before claiming background execution started.
        existing = read(controller.state_path) if controller.state_path.exists() else {}
        if alive(existing.get("controller_identity")):
            raise RuntimeError("Controller already running")
        with (controller.directory / "controller.log").open("ab", buffering=0) as log:
            process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--manifest",
                str(controller.path), "--state-dir", str(controller.directory)], cwd=controller.cwd,
                stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                start_new_session=True, close_fds=True, env={**os.environ, **THREAD_ENV})
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            state = read(controller.state_path) if controller.state_path.exists() else {}
            if state.get("controller_identity", {}).get("pid") == process.pid:
                atomic(controller.directory / "launcher.json", {"launched_utc": now(),
                    "identity": state["controller_identity"], "manifest_sha256": controller.manifest_hash,
                    "state_file": str(controller.state_path)})
                print(json.dumps({"status": "started", "pid": process.pid,
                    "state_file": str(controller.state_path), "deadline_utc": state["deadline_utc"]}))
                return 0
            if process.poll() is not None:
                raise RuntimeError(f"Controller failed to start: exit {process.returncode}; see controller.log")
            time.sleep(.1)
        raise RuntimeError("Controller startup unconfirmed; inspect controller.log/state before retrying")
    return controller.run()


if __name__ == "__main__":
    raise SystemExit(main())
