"""Temporary fake-process checks; no model imports or production launches."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import prepare_runtime as p


class RuntimePreparationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="runtime23_test_")
        self.root = Path(self.temporary.name)
        self.old = self.root / "old/controller_state"
        self.old.mkdir(parents=True)
        self.output = self.root / "new"
        self.output.mkdir()
        self.state_dir = self.output / "controller_state"
        self.old_state = dict(phase="finished", stop_reason="queue_exhausted", jobs={},
            controller_sha256=p.ORIGINAL_CONTROLLER_SHA256, manifest_sha256="a" * 64, finished_utc=p.runtime.now())
        self.save(self.old / "state.json", self.old_state)
        self.engine = self.root / "fake_engine.py"
        self.engine.write_text("import sys,time,json\nfrom pathlib import Path\n"
            "if sys.argv[1]=='hold': time.sleep(5)\n"
            "elif sys.argv[1]=='storage':\n"
            " Path(sys.argv[2]).write_text(json.dumps({'status':'STORAGE_BUDGET_EXHAUSTED','free_bytes':0}))\n"
            " if len(sys.argv)>3: Path(sys.argv[3]).touch()\n"
            " sys.exit(75)\n"
            "else:\n p=Path('calls.txt');p.write_text((p.read_text() if p.exists() else '')+sys.argv[1]+'\\n')\n")
        self.jobs = self.output / "jobs.json"
        self.protocol = self.output / "protocol.json"
        self.completion = self.output / "completion_jobs.json"
        self.finalizer = self.output / "finalizer_job.json"
        self.manifest = self.output / "controller_manifest.json"
        self.contract = self.output / "launch_contract.json"
        self.save(self.jobs, [dict(id="trial", argv=[sys.executable, str(self.engine), "trial"], estimated_seconds=1)])
        self.save(self.protocol, dict(source_sha256={str(self.engine): p.runtime.digest(self.engine)}, jobs_sha256=p.runtime.digest(self.jobs)))
        self.save(self.completion, [dict(id="completion", argv=[sys.executable, str(self.engine), "complete", "--deadline-utc", p.DEADLINE])])
        self.save(self.finalizer, dict(id="report_final", argv=[sys.executable, str(self.engine), "report"]))
        self.children = []

    def tearDown(self):
        for child in self.children:
            if child.poll() is None:
                child.terminate()
            child.wait(timeout=3)
        self.temporary.cleanup()

    @staticmethod
    def save(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        p.runtime.atomic(path, value)

    def build(self):
        return p.build(self.jobs, self.protocol, self.completion, self.finalizer,
            manifest_path=self.manifest, contract_path=self.contract, state_dir=self.state_dir,
            working_directory=self.root, old_state_dirs=[self.old], old_engine_files=[], old_controller_files=[])

    def test_deadline_reserve_and_idempotent_build(self):
        first = self.build()
        original = self.manifest.read_bytes()
        self.assertEqual(self.build(), first)
        self.assertEqual(self.manifest.read_bytes(), original)
        manifest = p.runtime.read(self.manifest)
        self.assertEqual(manifest["completion_reserve_seconds"], 7200)
        self.assertEqual(p.runtime.timestamp(manifest["deadline_utc"]) - 7200, p.runtime.timestamp(p.SEARCH_STOP))
        self.assertEqual(p.preflight(self.manifest)["status"], "ready_to_start")

    def test_old_live_identity_blocks_build(self):
        self.old_state["controller_identity"] = p.runtime.identity(os.getpid())
        self.save(self.old / "state.json", self.old_state)
        with self.assertRaisesRegex(RuntimeError, "still alive"):
            self.build()
        self.assertFalse(self.manifest.exists())

    def test_old_unowned_group_blocks_even_after_identity_mismatch(self):
        child = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(5)"], start_new_session=True)
        self.children.append(child)
        anchor = p.runtime.identity(child.pid)
        anchor["start_ticks"] += 1
        self.old_state["controller_identity"] = anchor
        self.save(self.old / "state.json", self.old_state)
        with self.assertRaisesRegex(RuntimeError, "process group"):
            self.build()

    def test_stop_files_never_removed(self):
        stop = self.old / "STOP"
        stop.touch()
        with self.assertRaisesRegex(RuntimeError, "STOP"):
            self.build()
        self.assertTrue(stop.exists())
        stop.unlink()  # Only this temporary fixture, never production STOP.
        self.build()
        self.state_dir.mkdir()
        current_stop = self.state_dir / "STOP"
        current_stop.touch()
        with self.assertRaisesRegex(RuntimeError, "STOP"):
            p.preflight(self.manifest)
        self.assertTrue(current_stop.exists())

    def test_changed_source_and_wrong_state_directory_block(self):
        self.build()
        with self.assertRaisesRegex(RuntimeError, "exact frozen state"):
            p.preflight(self.manifest, self.output / "other_state")
        self.engine.write_text(self.engine.read_text() + "# changed\n")
        with self.assertRaises((AssertionError, RuntimeError)):
            p.preflight(self.manifest)

    def test_duplicate_ids_and_late_dependencies_rejected(self):
        jobs = p.runtime.read(self.jobs)
        finalizer = p.runtime.read(self.finalizer)
        duplicate = [dict(id="trial", argv=[sys.executable, str(self.engine), "complete", "--deadline-utc", p.DEADLINE])]
        with self.assertRaisesRegex(RuntimeError, "unique"):
            p.validate_jobs(jobs, duplicate, finalizer)
        jobs[0]["requires_success"] = ["completion"]
        with self.assertRaisesRegex(RuntimeError, "precede"):
            p.validate_jobs(jobs, p.runtime.read(self.completion), finalizer)

    def test_report_only_finalizer_and_completion_deadline(self):
        finalizer = p.runtime.read(self.finalizer)
        finalizer["argv"][-1] = "trial"
        with self.assertRaisesRegex(RuntimeError, "report-only"):
            p.validate_jobs(p.runtime.read(self.jobs), p.runtime.read(self.completion), finalizer)
        completion = p.runtime.read(self.completion)
        completion[0]["argv"][-1] = "2026-11-09T14:00:00Z"
        with self.assertRaisesRegex(RuntimeError, "deadline"):
            p.validate_jobs(p.runtime.read(self.jobs), completion, p.runtime.read(self.finalizer))

    def test_unowned_new_engine_blocks_but_owned_inflight_is_adoptable(self):
        self.build()
        child = subprocess.Popen([sys.executable, str(self.engine), "hold"], start_new_session=True)
        self.children.append(child)
        with self.assertRaisesRegex(RuntimeError, "Unowned learning"):
            p.preflight(self.manifest)
        identity = p.runtime.identity(child.pid)
        spec_path = self.state_dir / "jobs/trial/spec.json"
        self.save(spec_path, dict(nonce="owned"))
        state = dict(manifest_sha256=p.runtime.digest(self.manifest), controller_sha256=p.runtime.digest(p.CONTROLLER),
            phase="search", current_job="trial", jobs={"trial": dict(status="running", nonce="owned", attempts=1, spec_sha256=p.runtime.digest(spec_path))})
        self.save(self.state_dir / "state.json", state)
        self.save(self.state_dir / "jobs/trial/started.json", dict(nonce="owned", manifest_sha256=state["manifest_sha256"], identity=identity, worker_identity=identity))
        checked = p.preflight(self.manifest)
        self.assertEqual(checked["status"], "ready_to_resume")
        self.assertEqual(checked["adopted_learning_processes"][0]["pid"], child.pid)
        state["jobs"]["trial"]["status"] = "completed"
        self.save(self.state_dir / "state.json", state)
        with self.assertRaisesRegex(RuntimeError, "Terminal job"):
            p.preflight(self.manifest)

    def test_prior_supervisor_must_be_terminal(self):
        supervisor = self.old.parent / "supervisor_state/state.json"
        self.save(supervisor, dict(phase="waiting_old"))
        with self.assertRaisesRegex(RuntimeError, "supervisor is not finished"):
            self.build()
        self.save(supervisor, dict(phase="finished", supervisor_identity=p.runtime.identity(os.getpid())))
        with self.assertRaisesRegex(RuntimeError, "still alive"):
            self.build()

    def test_process_access_failure_is_not_treated_as_dead(self):
        original = Path.read_text
        denied = Path(f"/proc/{os.getpid()}/stat")
        def guarded(path, *args, **kwargs):
            if path == denied:
                raise PermissionError("fixture access unavailable")
            return original(path, *args, **kwargs)
        with patch.object(Path, "read_text", guarded):
            with self.assertRaisesRegex(RuntimeError, "PermissionError.*no launch"):
                self.build()

    def test_terminal_orphan_group_and_multiple_active_groups_block(self):
        children = [subprocess.Popen([sys.executable, "-c", "import time;time.sleep(5)"], start_new_session=True) for _ in range(2)]
        self.children.extend(children)
        manifest_hash = "c" * 64
        state = dict(manifest_sha256=manifest_hash, jobs={})
        for index, child in enumerate(children):
            identity = p.runtime.identity(child.pid)
            job_id = f"job{index}"
            state["jobs"][job_id] = dict(status="running", nonce=job_id)
            self.save(self.state_dir / "jobs" / job_id / "started.json", dict(nonce=job_id, manifest_sha256=manifest_hash, identity=identity, worker_identity=identity))
        with self.assertRaisesRegex(RuntimeError, "Multiple active"):
            p.check_learning_processes([], self.state_dir, state)
        for index, child in enumerate(children):
            job_id = f"job{index}"
            state["jobs"][job_id]["status"] = "completed"
            path = self.state_dir / "jobs" / job_id / "started.json"
            started = p.runtime.read(path)
            started["identity"]["start_ticks"] += 1
            started["worker_identity"]["start_ticks"] += 1
            self.save(path, started)
        with self.assertRaisesRegex(RuntimeError, "Terminal job process group"):
            p.check_learning_processes([], self.state_dir, state)

    def test_frozen_manifest_cannot_be_amended_before_initial_launch(self):
        self.build()
        changed = p.runtime.read(self.manifest)
        changed["jobs"][0]["argv"][-1] = "different"
        self.save(self.manifest, changed)
        with self.assertRaisesRegex(RuntimeError, "Frozen manifest changed"):
            p.preflight(self.manifest)

    def storage_manifest(self, stop=False):
        argv = [sys.executable, str(self.engine), "storage", str(self.output / "budget_stop.json")]
        if stop:
            argv.append(str(self.state_dir / "STOP"))
        self.save(self.jobs, [dict(id="storage", argv=argv), dict(id="must_skip", argv=[sys.executable, str(self.engine), "trial"])])
        protocol = p.runtime.read(self.protocol)
        protocol["jobs_sha256"] = p.runtime.digest(self.jobs)
        self.save(self.protocol, protocol)
        self.build()
        return [sys.executable, str(p.CONTROLLER), "--manifest", str(self.manifest), "--state-dir", str(self.state_dir)]

    def test_storage_marker_defers_search_completes_and_resumes_without_retraining(self):
        command = self.storage_manifest()
        result = subprocess.run(command, capture_output=True, text=True, timeout=15, start_new_session=True,
                                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(result.returncode, 0, result.stderr)
        state = p.runtime.read(self.state_dir / "state.json")
        self.assertEqual(state["jobs"]["storage"]["exit_code"], 75)
        self.assertEqual(state["jobs"]["must_skip"]["status"], "deferred_budget")
        self.assertEqual(state["jobs"]["must_skip"]["deferred_reason"], "storage")
        self.assertEqual(state["stop_reason"], "storage_budget_exhausted")
        calls = (self.root / "calls.txt").read_text()
        self.assertEqual(calls, "complete\nreport\n")
        again = subprocess.run(command, capture_output=True, text=True, timeout=15, start_new_session=True,
                               env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual((self.root / "calls.txt").read_text(), calls)

    def test_stop_overrides_storage_handoff_to_completion(self):
        command = self.storage_manifest(stop=True)
        result = subprocess.run(command, capture_output=True, text=True, timeout=15, start_new_session=True,
                                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(result.returncode, 0, result.stderr)
        state = p.runtime.read(self.state_dir / "state.json")
        self.assertEqual(state["stop_reason"], "stopped")
        self.assertEqual(state["jobs"]["completion"]["status"], "pending")
        self.assertEqual((self.root / "calls.txt").read_text(), "report\n")
        with self.assertRaisesRegex(RuntimeError, "STOP"):
            p.preflight(self.manifest)

    def test_resource_marker_must_stay_inside_new_campaign(self):
        self.build()
        manifest = p.runtime.read(self.manifest)
        manifest["resource_stop"]["path"] = str(self.root / "outside.json")
        self.save(self.manifest, manifest)
        with self.assertRaisesRegex(AssertionError, "inside this campaign"):
            p.runtime.Controller(self.manifest, self.state_dir)

    def test_completed_jobs_and_terminal_report_are_reused_on_restart(self):
        self.build()
        command = [sys.executable, str(p.CONTROLLER), "--manifest", str(self.manifest), "--state-dir", str(self.state_dir)]
        first = subprocess.run(command, capture_output=True, text=True, timeout=15, start_new_session=True,
                               env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(first.returncode, 0, first.stderr)
        calls = (self.root / "calls.txt").read_text()
        self.assertEqual(calls, "trial\ncomplete\nreport\n")
        checked = p.preflight(self.manifest)
        self.assertEqual(checked["status"], "already_finished")
        self.assertEqual(checked["completed_jobs_reused"], 3)
        second = subprocess.run(command, capture_output=True, text=True, timeout=15, start_new_session=True,
                                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual((self.root / "calls.txt").read_text(), calls)


if __name__ == "__main__":
    unittest.main()
