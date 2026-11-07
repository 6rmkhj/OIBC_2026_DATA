"""Small fake-process tests; no model/data imports or real campaign mutations."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest

import continuation as c


class ContinuationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="continuation_test_")
        self.root = Path(self.tmp.name)
        self.old = self.root / "old"
        self.old.mkdir()
        self.marker = self.root / "fits.txt"
        self.old_state = dict(manifest_sha256="a" * 64, controller_sha256="b" * 64,
            deadline_utc="2026-01-01T00:00:00Z", phase="finished", jobs={}, stop_reason="queue_exhausted")
        self.contract = {key: self.old_state[key] for key in ("manifest_sha256", "controller_sha256", "deadline_utc")}
        self.write_old()
        self.children = []

    def tearDown(self):
        for process in self.children:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=3)
        self.tmp.cleanup()

    def write_old(self):
        c.runtime.atomic(self.old / "state.json", self.old_state)

    def make(self, deadline=None, job_seconds=.1, checkpoint=None):
        deadline = deadline if deadline is not None else time.time() + 20
        deadline_iso = c.runtime.datetime.fromtimestamp(deadline, c.runtime.timezone.utc).isoformat()
        code = f"from pathlib import Path;import time; p=Path({str(self.marker)!r});p.write_text(p.read_text()+'fit\\n' if p.exists() else 'fit\\n');time.sleep({job_seconds})"
        self.manifest_path = self.root / "manifest.json"
        self.manifest_path.write_text(json.dumps(dict(version=1, deadline_utc=deadline_iso,
            working_directory=str(self.root), reserve_seconds=0, poll_seconds=.05,
            heartbeat_seconds=.1, termination_grace_seconds=.1,
            jobs=[dict(id="fake_fit", argv=[sys.executable, "-c", code])])))
        self.spec_path = self.root / "spec.json"
        spec = dict(version=1, old_state_dir=str(self.old), next_manifest=str(self.manifest_path),
                    next_state_dir=str(self.root / "next"), deadline_utc=deadline_iso, poll_seconds=.05)
        if checkpoint:
            spec["checkpoint"] = checkpoint
        self.spec_path.write_text(json.dumps(spec))
        return c.Supervisor(self.spec_path, self.root / "supervisor")

    def test_old_terminal_and_identity_gates(self):
        self.assertEqual(c.old_handoff_status(self.old, self.contract)[0], True)
        self.old_state["phase"] = "search"
        self.write_old()
        self.assertEqual(c.old_handoff_status(self.old, self.contract)[0], False)
        self.old_state.update(phase="finished", controller_identity=c.runtime.identity(os.getpid()))
        self.write_old()
        self.assertEqual(c.old_handoff_status(self.old, self.contract)[1], "old_owned_process_alive")

    def test_old_orphan_group_blocks_even_when_identity_does_not_match(self):
        process = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(5)"], start_new_session=True)
        self.children.append(process)
        anchor = c.runtime.identity(process.pid)
        anchor["start_ticks"] += 1
        self.old_state["controller_identity"] = anchor
        self.write_old()
        self.assertEqual(c.old_handoff_status(self.old, self.contract)[1], "old_group_member_remains")

    def test_old_contract_change_and_stopped_campaign_block(self):
        self.old_state["manifest_sha256"] = "changed"
        self.write_old()
        with self.assertRaises(RuntimeError):
            c.old_handoff_status(self.old, self.contract)
        self.old_state.update(self.contract, stop_reason="stopped")
        self.write_old()
        self.assertFalse(c.old_handoff_status(self.old, self.contract)[0])
        self.assertTrue(c.old_handoff_status(self.old, self.contract, allow_stopped=True)[0])

    def test_wait_then_one_fit_and_idempotent_finished_restart(self):
        self.old_state["phase"] = "search"
        self.write_old()
        supervisor = self.make()
        def finish_old():
            time.sleep(.2)
            self.assertFalse(self.marker.exists())
            self.old_state["phase"] = "finished"
            self.write_old()
        thread = threading.Thread(target=finish_old)
        thread.start()
        self.assertEqual(supervisor.run(), 0)
        thread.join()
        self.assertEqual(self.marker.read_text(), "fit\n")
        self.assertEqual(c.Supervisor(self.spec_path, supervisor.directory).run(), 0)
        self.assertEqual(self.marker.read_text(), "fit\n")

    def test_existing_controller_adopted_without_second_fit(self):
        supervisor = self.make(job_seconds=.5)
        with (self.root / "external.log").open("wb") as log:
            process = subprocess.Popen([sys.executable, str(c.CONTROLLER), "--manifest", str(self.manifest_path),
                "--state-dir", str(self.root / "next")], stdout=log, stderr=log, start_new_session=True,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.children.append(process)
        until = time.monotonic() + 3
        while not self.marker.exists() and time.monotonic() < until:
            time.sleep(.02)
        self.assertTrue(self.marker.exists())
        self.assertEqual(supervisor.run(), 0)
        self.assertEqual(supervisor.state["controller_launches"], 0)
        self.assertEqual(self.marker.read_text(), "fit\n")

    def test_exclusive_supervisor_lock_and_immutable_spec(self):
        first = self.make()
        first.initialize()
        second = c.Supervisor(self.spec_path, first.directory)
        try:
            with self.assertRaises(BlockingIOError):
                second.run()
        finally:
            first.lock.close()
        spec = json.loads(self.spec_path.read_text())
        spec["poll_seconds"] = .1
        self.spec_path.write_text(json.dumps(spec))
        with self.assertRaises(AssertionError):
            c.Supervisor(self.spec_path, first.directory).run()

    def test_deadline_before_handoff_never_launches(self):
        supervisor = self.make(deadline=time.time() - 1)
        self.assertEqual(supervisor.run(), 0)
        self.assertFalse(self.marker.exists())
        self.assertEqual(supervisor.state["controller_launches"], 0)

    def test_live_old_process_is_never_overlapped(self):
        self.old_state["controller_identity"] = c.runtime.identity(os.getpid())
        self.write_old()
        supervisor = self.make(deadline=time.time() + .2)
        self.assertEqual(supervisor.run(), 0)
        self.assertFalse(self.marker.exists())

    def test_final_checkpoint_runs_once(self):
        publication = self.root / "publication.txt"
        checkpoint = dict(argv=[sys.executable, "-c", f"from pathlib import Path;Path({str(publication)!r}).write_text('published')"],
                          interval_seconds=3600, timeout_seconds=2)
        supervisor = self.make(checkpoint=checkpoint)
        self.assertEqual(supervisor.run(), 0)
        self.assertEqual(publication.read_text(), "published")
        self.assertEqual(len(supervisor.state["checkpoint_history"]), 1)
        self.assertEqual(supervisor.state["checkpoint_history"][0]["status"], "completed")

    def test_checkpoint_timeout_is_bounded(self):
        checkpoint = dict(argv=[sys.executable, "-c", "import time;time.sleep(10)"], interval_seconds=3600, timeout_seconds=.2)
        supervisor = self.make(checkpoint=checkpoint)
        start = time.monotonic()
        self.assertEqual(supervisor.run(), 0)
        self.assertLess(time.monotonic() - start, 4)
        self.assertEqual(supervisor.state["checkpoint_history"][0]["status"], "time_limit")

    def test_detached_launcher_persists_then_stops_at_deadline(self):
        self.old_state["phase"] = "search"
        self.write_old()
        supervisor = self.make(deadline=time.time() + .7)
        completed = subprocess.run([sys.executable, str(Path(c.__file__).resolve()), "--spec", str(self.spec_path),
            "--state-dir", str(supervisor.directory), "--detach"], capture_output=True, text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, timeout=3)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        launch = json.loads(completed.stdout)
        self.assertEqual(launch["status"], "started")
        state = c.runtime.read(supervisor.state_path)
        self.assertTrue(c.runtime.alive(state["supervisor_identity"]))
        until = time.monotonic() + 3
        while c.runtime.alive(state["supervisor_identity"]) and time.monotonic() < until:
            time.sleep(.05)
        state = c.runtime.read(supervisor.state_path)
        self.assertEqual(state["phase"], "finished")
        self.assertFalse(self.marker.exists())


if __name__ == "__main__":
    unittest.main()
