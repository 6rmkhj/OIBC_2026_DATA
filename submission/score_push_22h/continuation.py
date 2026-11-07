"""Durably hand a completed campaign to a new bounded, serial controller.

Use --spec FILE --state-dir DIR [--detach]. A local STOP prevents the handoff
or requests cancellation of the new controller; the old campaign is never edited.
Optional checkpoint.argv is an explicitly configured, bounded non-ML publisher.
"""
from __future__ import annotations

import argparse
import fcntl
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

sys.dont_write_bytecode = True
import controller as runtime


CONTROLLER = Path(__file__).resolve().with_name("controller.py")


def maybe_read(path):
    return runtime.read(path) if Path(path).exists() else None


def old_handoff_status(directory, contract, allow_stopped=False, require_finished=True):
    """Fail closed on missing/corrupt history or live/orphaned old groups."""
    directory = Path(directory)
    state = maybe_read(directory / "state.json")
    if not state:
        return False, "old_state_missing"
    for key, value in contract.items():
        if state.get(key) != value:
            raise RuntimeError(f"Old campaign immutable contract changed: {key}")
    if require_finished and state.get("phase") != "finished":
        return False, "old_campaign_not_finished"
    if state.get("stop_reason") == "stopped" and not allow_stopped:
        return False, "old_campaign_stopped_requires_explicit_override"
    if require_finished and any(job.get("status") not in runtime.TERMINAL | {"pending"} for job in state.get("jobs", {}).values()):
        return False, "old_inflight_or_blocked_job_record"
    anchors = [state.get("controller_identity")]
    for path in (directory / "jobs").glob("*/started.json"):
        started = runtime.read(path)
        if started.get("manifest_sha256") != contract["manifest_sha256"]:
            raise RuntimeError(f"Old job manifest identity mismatch: {path.parent.name}")
        job = state.get("jobs", {}).get(path.parent.name)
        if not job or started.get("nonce") != job.get("nonce"):
            raise RuntimeError(f"Old job execution identity mismatch: {path.parent.name}")
        anchors.extend((started.get("identity"), started.get("worker_identity")))
    anchors.extend(job.get("wrapper_identity") for job in state.get("jobs", {}).values())
    anchors = [anchor for anchor in anchors if anchor]
    if any(runtime.alive(anchor) for anchor in anchors):
        return False, "old_owned_process_alive"
    boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    groups = {anchor["pgid"] for anchor in anchors if anchor.get("boot_id") == boot}
    # A dead session leader can leave descendants. Read-only PGID checking is
    # deliberately conservative: possible reuse blocks a handoff, never a kill.
    for path in Path("/proc").iterdir():
        if path.name.isdigit():
            current = runtime.identity(int(path.name))
            if current and current["state"] not in {"Z", "X"} and current["pgid"] in groups:
                return False, "old_group_member_remains"
    return True, "old_campaign_finished_and_processes_terminal"


class Supervisor:
    def __init__(self, spec_path, directory):
        self.path, self.directory = Path(spec_path).resolve(), Path(directory).resolve()
        self.spec = runtime.read(self.path)
        assert self.spec.get("version") == 1
        self.old = Path(self.spec["old_state_dir"]).resolve()
        self.manifest_path = Path(self.spec["next_manifest"]).resolve()
        self.next = Path(self.spec["next_state_dir"]).resolve()
        assert not self.next.is_relative_to(self.old) and not self.directory.is_relative_to(self.old)
        assert self.next != self.directory
        self.manifest = runtime.read(self.manifest_path)
        self.deadline = runtime.timestamp(self.spec["deadline_utc"])
        assert runtime.timestamp(self.manifest["deadline_utc"]) == self.deadline
        self.cwd = str(Path(self.manifest["working_directory"]).resolve())
        self.poll = max(.05, min(10., float(self.spec.get("poll_seconds", 5))))
        self.directory.mkdir(parents=True, exist_ok=True)
        self.state_path = self.directory / "state.json"
        self.hashes = dict(spec_sha256=runtime.digest(self.path),
            supervisor_sha256=runtime.digest(__file__), controller_sha256=runtime.digest(CONTROLLER),
            next_manifest_sha256=runtime.digest(self.manifest_path))
        self.checkpoint = self.spec.get("checkpoint")
        if self.checkpoint:
            runtime.validate_job({"id": "checkpoint", "argv": self.checkpoint["argv"]})
            assert float(self.checkpoint.get("interval_seconds", 3600)) >= 1
            assert 0 < float(self.checkpoint.get("timeout_seconds", 120)) <= 300
        self.state = None
        self.lock = None
        self.controller_handle = None
        self.checkpoint_handle = None
        self.last_save = 0.

    def save(self, event=None, **details):
        self.state["heartbeat_utc"] = runtime.now()
        runtime.atomic(self.state_path, self.state)
        self.last_save = time.monotonic()
        if event:
            with (self.directory / "events.jsonl").open("a", encoding="utf-8") as handle:
                import json
                handle.write(json.dumps({"utc": runtime.now(), "event": event, **details}) + "\n")
                handle.flush()
                os.fsync(handle.fileno())

    def initialize(self):
        self.lock = (self.directory / "supervisor.lock").open("a+b")
        fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.state = maybe_read(self.state_path)
        if self.state:
            assert all(self.state.get(key) == value for key, value in self.hashes.items()), "Immutable continuation inputs changed"
        else:
            old = runtime.read(self.old / "state.json")
            contract = {key: old[key] for key in ("manifest_sha256", "controller_sha256", "deadline_utc")}
            self.state = dict(version=1, **self.hashes, old_contract=contract,
                deadline_utc=self.spec["deadline_utc"], started_utc=runtime.now(),
                phase="waiting_old", controller_launches=0, checkpoint_attempts=0,
                checkpoint_history=[], next_checkpoint_timestamp=time.time() + float((self.checkpoint or {}).get("interval_seconds", 3600)))
        runtime.check_inputs(self.spec.get("input_sha256", {}), self.cwd)
        self.state["supervisor_identity"] = runtime.identity(os.getpid())
        self.save("supervisor_started")

    def next_state(self):
        value = maybe_read(self.next / "state.json")
        if value:
            assert value.get("manifest_sha256") == self.hashes["next_manifest_sha256"], "New campaign manifest mismatch"
            assert value.get("controller_sha256") == self.hashes["controller_sha256"], "New controller source mismatch"
            assert runtime.timestamp(value["deadline_utc"]) == self.deadline
        return value

    def start_controller(self):
        assert time.time() < self.deadline, "No launch after the absolute deadline"
        ready, reason = old_handoff_status(self.old, self.state["old_contract"], self.spec.get("allow_stopped_old", False))
        if not ready:
            raise RuntimeError(f"Handoff no longer safe: {reason}")
        assert runtime.digest(__file__) == self.hashes["supervisor_sha256"], "Supervisor changed before handoff"
        assert runtime.digest(CONTROLLER) == self.hashes["controller_sha256"], "New controller changed before handoff"
        assert runtime.digest(self.manifest_path) == self.hashes["next_manifest_sha256"], "New manifest changed before handoff"
        runtime.check_inputs(self.spec.get("input_sha256", {}), self.cwd)
        self.next.mkdir(parents=True, exist_ok=True)
        self.state.update(phase="launching_next", controller_launches=self.state["controller_launches"] + 1,
                          controller_launch_timestamp=time.time())
        self.save("next_controller_launch_intent")
        with (self.next / "controller.log").open("ab", buffering=0) as log:
            self.controller_handle = subprocess.Popen([sys.executable, str(CONTROLLER), "--manifest",
                str(self.manifest_path), "--state-dir", str(self.next)], cwd=self.cwd,
                stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                start_new_session=True, close_fds=True, env={**os.environ, **runtime.THREAD_ENV})
        self.state["launched_controller_identity"] = runtime.identity(self.controller_handle.pid)
        self.save("next_controller_spawned", identity=self.state["launched_controller_identity"])

    def checkpoint_tick(self, final=False):
        if not self.checkpoint:
            return True
        current = self.state.get("checkpoint_active")
        if current:
            folder = self.directory / "checkpoints" / current["id"]
            started, receipt = maybe_read(folder / "started.json"), maybe_read(folder / "receipt.json")
            if self.checkpoint_handle:
                self.checkpoint_handle.poll()
            if started:
                assert started["nonce"] == current["nonce"] and started["manifest_sha256"] == self.hashes["spec_sha256"]
                current["wrapper_identity"] = started["identity"]
            alive = runtime.alive(current.get("wrapper_identity"))
            anchors = [current.get("wrapper_identity"), (started or {}).get("worker_identity")]
            worker_alive = runtime.alive((started or {}).get("worker_identity"))
            groups = {anchor["pgid"] for anchor in anchors if anchor}
            members_remain = any(runtime.group_members(group) for group in groups)
            deadline = runtime.read(folder / "spec.json")["deadline_timestamp"]
            if time.time() >= deadline and (alive or worker_alive):
                if "termination_timestamp" not in current:
                    current["termination_timestamp"] = time.time()
                sig = signal.SIGKILL if time.time() - current["termination_timestamp"] >= 5 else signal.SIGTERM
                runtime.signal_owned_group([anchor for anchor in anchors if anchor], sig)
            if receipt and not alive and not worker_alive and not members_remain:
                assert receipt["nonce"] == current["nonce"] and receipt["manifest_sha256"] == self.hashes["spec_sha256"]
                assert receipt.get("all_worker_processes_terminal") is True
                self.state["checkpoint_history"].append(dict(id=current["id"], status=receipt["status"],
                    exit_code=receipt["exit_code"], finished_utc=receipt["finished_utc"]))
                self.state["checkpoint_active"] = None
                self.save("checkpoint_terminal", id=current["id"], status=receipt["status"])
                if current.get("final"):
                    self.state["final_checkpoint_done"] = True
                    self.save()
                return not final or self.state.get("final_checkpoint_done", False)
            if not alive and not worker_alive and members_remain:
                self.state["checkpoint_blocked"] = "unverified_orphan_group"
                self.save("checkpoint_orphan_group_no_new_publication")
                return False
            if not alive and not worker_alive and not members_remain and time.time() - current["launch_timestamp"] > 15:
                # The independent wrapper may have died before writing its
                # receipt. Never issue a possibly duplicate publication.
                self.state["checkpoint_blocked"] = "missing_terminal_receipt"
                self.save("checkpoint_ambiguous_no_retry")
                return True
            return False
        if self.state.get("checkpoint_blocked") or (final and self.state.get("final_checkpoint_done")):
            return True
        if not final and time.time() < self.state["next_checkpoint_timestamp"]:
            return True
        if time.time() >= self.deadline + 120:
            return True
        sequence = self.state["checkpoint_attempts"] + 1
        identifier, nonce = f"checkpoint_{sequence:04d}", uuid.uuid4().hex
        folder = self.directory / "checkpoints" / identifier
        folder.mkdir(parents=True, exist_ok=False)
        checkpoint_spec = dict(nonce=nonce, manifest_sha256=self.hashes["spec_sha256"],
            controller_sha256=self.hashes["controller_sha256"], argv=self.checkpoint["argv"],
            input_sha256=self.checkpoint.get("input_sha256", {}),
            working_directory=self.checkpoint.get("working_directory", self.cwd),
            environment=self.checkpoint.get("environment", {}),
            deadline_timestamp=min(self.deadline + 120, time.time() + float(self.checkpoint.get("timeout_seconds", 120))),
            termination_grace_seconds=5, poll_seconds=min(self.poll, .5),
            stop_file=str(self.directory / "STOP"))
        runtime.atomic(folder / "spec.json", checkpoint_spec)
        self.state.update(checkpoint_attempts=sequence,
            next_checkpoint_timestamp=time.time() + float(self.checkpoint.get("interval_seconds", 3600)),
            checkpoint_active=dict(id=identifier, nonce=nonce, launch_timestamp=time.time(), final=final))
        self.save("checkpoint_launch_intent", id=identifier)
        with (folder / "run.log").open("ab", buffering=0) as log:
            self.checkpoint_handle = subprocess.Popen([sys.executable, str(CONTROLLER), "--job-wrapper",
                str(folder / "spec.json"), "--spec-sha256", runtime.digest(folder / "spec.json")],
                cwd=self.cwd, stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                start_new_session=True, close_fds=True, env={**os.environ, **runtime.THREAD_ENV})
        self.state["checkpoint_active"]["wrapper_identity"] = runtime.identity(self.checkpoint_handle.pid)
        self.save("checkpoint_spawned", id=identifier)
        return False

    def run(self):
        launched_here = False
        try:
            self.initialize()
            if self.state.get("phase") == "finished":
                return 0
            while True:
                next_state = self.next_state()
                if self.controller_handle:
                    self.controller_handle.poll()
                next_alive = runtime.alive((next_state or {}).get("controller_identity"))
                stopped = (self.directory / "STOP").exists()
                if stopped and next_state:
                    # This directory belongs exclusively to the new campaign.
                    (self.next / "STOP").touch(exist_ok=True)
                if next_state and next_state.get("phase") == "finished" and not next_alive:
                    self.state.update(phase="finalizing", next_stop_reason=next_state.get("stop_reason"))
                    contract = {key: next_state[key] for key in ("manifest_sha256", "controller_sha256", "deadline_utc")}
                    terminal, reason = old_handoff_status(self.next, contract, allow_stopped=True)
                    self.state["next_terminal_check"] = reason
                    if terminal and self.checkpoint_tick(final=True):
                        self.state.update(phase="finished", finished_utc=runtime.now(), stop_reason="next_campaign_finished")
                        self.save("supervisor_finished")
                        return 0
                elif next_alive:
                    self.state.update(phase="monitoring_next", next_controller_identity=next_state["controller_identity"],
                                      next_phase=next_state.get("phase"), current_job=next_state.get("current_job"))
                    self.checkpoint_tick()
                elif stopped or time.time() >= self.deadline:
                    terminal = True
                    if next_state:
                        contract = {key: next_state[key] for key in ("manifest_sha256", "controller_sha256", "deadline_utc")}
                        terminal, reason = old_handoff_status(self.next, contract, allow_stopped=True, require_finished=False)
                        self.state["next_terminal_check"] = reason
                    if terminal and (not self.state.get("checkpoint_active") or self.checkpoint_tick()):
                        self.state.update(phase="finished", finished_utc=runtime.now(),
                                          stop_reason="stopped" if stopped else "absolute_deadline_reached")
                        self.save("supervisor_finished")
                        return 0
                elif launched_here:
                    # A concurrently starting controller can win controller.lock
                    # during a recovered Popen/state-write gap. Give its durable
                    # identity time to appear before reporting a failed launch.
                    if time.time() - self.state["controller_launch_timestamp"] > 15:
                        self.state.update(phase="blocked", stop_reason="next_controller_exited_or_startup_unconfirmed")
                        self.save("supervisor_blocked")
                        return 2
                else:
                    ready, reason = old_handoff_status(self.old, self.state["old_contract"], self.spec.get("allow_stopped_old", False))
                    self.state.update(phase="waiting_old", handoff_reason=reason)
                    if ready:
                        self.start_controller()
                        launched_here = True
                    else:
                        self.checkpoint_tick()
                if time.time() >= self.deadline + 150:
                    self.state.update(phase="blocked", finished_utc=runtime.now(), stop_reason="monitoring_grace_expired_unconfirmed_terminal")
                    self.save("supervisor_blocked")
                    return 2
                if time.monotonic() - self.last_save >= min(15, self.poll * 3):
                    self.save()
                time.sleep(self.poll)
        finally:
            if self.lock:
                self.lock.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--detach", action="store_true")
    args = parser.parse_args()
    supervisor = Supervisor(args.spec, args.state_dir)
    if not args.detach:
        return supervisor.run()
    existing = maybe_read(supervisor.state_path) or {}
    if runtime.alive(existing.get("supervisor_identity")):
        raise RuntimeError("Continuation supervisor already running")
    with (supervisor.directory / "supervisor.log").open("ab", buffering=0) as log:
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--spec", str(supervisor.path),
            "--state-dir", str(supervisor.directory)], cwd=supervisor.cwd,
            stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
            start_new_session=True, close_fds=True, env={**os.environ, **runtime.THREAD_ENV})
    until = time.monotonic() + 15
    while time.monotonic() < until:
        state = maybe_read(supervisor.state_path) or {}
        if state.get("supervisor_identity", {}).get("pid") == process.pid:
            runtime.atomic(supervisor.directory / "launcher.json", dict(utc=runtime.now(), identity=state["supervisor_identity"]))
            import json
            print(json.dumps(dict(status="started", pid=process.pid, state_file=str(supervisor.state_path), deadline_utc=supervisor.spec["deadline_utc"])))
            return 0
        if process.poll() is not None:
            raise RuntimeError(f"Supervisor failed to start: {process.returncode}; see supervisor.log")
        time.sleep(.1)
    raise RuntimeError("Supervisor startup unconfirmed; inspect durable state before retrying")


if __name__ == "__main__":
    raise SystemExit(main())
