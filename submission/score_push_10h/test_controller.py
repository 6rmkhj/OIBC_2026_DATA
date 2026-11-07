"""Short fake-job integration checks; no project data or ML fits are used."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest

SOURCE = Path(__file__).with_name('controller.py').resolve()
spec = importlib.util.spec_from_file_location('bounded_controller', SOURCE)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='oibc-controller-test-', dir='/tmp')
        self.root = Path(self.temp.name)
        self.state = self.root / 'state'
        self.path = self.root / 'manifest.json'
        self.handles = []

    def tearDown(self):
        self.state.mkdir(exist_ok=True)
        (self.state / 'STOP').touch()
        for handle in self.handles:
            if handle.poll() is None:
                handle.terminate()
                try:
                    handle.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    handle.kill()
                    handle.wait()
        started = self.state / 'jobs'
        for path in started.glob('*/started.json'):
            saved = module.read(path)
            module.signal_owned_group([saved['identity'], saved.get('worker_identity')], signal.SIGKILL)
        time.sleep(.05)
        self.temp.cleanup()

    def manifest(self, jobs, seconds=15, **kwargs):
        value = {'version': 1, 'deadline_utc': datetime.fromtimestamp(time.time() + seconds, timezone.utc).isoformat(),
                 'working_directory': str(self.root), 'reserve_seconds': 0, 'poll_seconds': .05,
                 'heartbeat_seconds': .1, 'termination_grace_seconds': .15, 'jobs': jobs, **kwargs}
        self.path.write_text(json.dumps(value))
        return value

    def job(self, name, code, **kwargs):
        return {'id': name, 'argv': [sys.executable, '-c', code], **kwargs}

    def launch(self, detach=False):
        command = [sys.executable, str(SOURCE), '--manifest', str(self.path), '--state-dir', str(self.state)]
        if detach:
            command.append('--detach')
        handle = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.handles.append(handle)
        return handle

    def wait_for(self, predicate, timeout=8):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if predicate():
                return
            time.sleep(.03)
        self.fail('Condition did not become true before timeout')

    def state_read(self):
        return module.read(self.state / 'state.json')

    def finished(self):
        return (self.state / 'state.json').exists() and self.state_read()['phase'] == 'finished'

    def assert_exit(self, handle, code=0):
        stdout, stderr = handle.communicate(timeout=10)
        self.assertEqual(handle.returncode, code, (stdout, stderr))

    def test_serial_failure_no_retry_and_dependencies(self):
        first = "from pathlib import Path;import time;Path('first').write_text('start');time.sleep(.2);Path('done').write_text('done')"
        second = "from pathlib import Path;assert Path('done').exists();Path('second').write_text('done')"
        self.manifest([self.job('one', first), self.job('two', second), self.job('failure', 'raise SystemExit(7)'),
                       self.job('skipped', "raise RuntimeError('Must never run')", requires_success=['failure'])])
        self.assert_exit(self.launch())
        before = self.state_read()
        self.assertEqual(before['jobs']['one']['status'], 'completed')
        self.assertEqual(before['jobs']['two']['status'], 'completed')
        self.assertEqual(before['jobs']['failure']['exit_code'], 7)
        self.assertEqual(before['jobs']['skipped']['status'], 'skipped_dependency')
        self.assert_exit(self.launch())
        after = self.state_read()
        self.assertEqual(after['jobs'], before['jobs'])

    def test_controller_restart_adopts_worker_exactly_once(self):
        code = "from pathlib import Path;import time;p=Path('count');p.write_text(str(int(p.read_text())+1) if p.exists() else '1');time.sleep(.8)"
        self.manifest([self.job('slow', code)])
        first = self.launch()
        self.wait_for(lambda: (self.root / 'count').exists())
        first.kill()
        first.communicate(timeout=2)
        self.assert_exit(self.launch())
        self.assertEqual((self.root / 'count').read_text(), '1')
        self.assertEqual(self.state_read()['jobs']['slow']['status'], 'completed')

    def test_controller_lock_excludes_second_worker(self):
        code = "from pathlib import Path;import time;Path('began').touch();time.sleep(.5)"
        self.manifest([self.job('slow', code)])
        first = self.launch()
        self.wait_for(lambda: (self.root / 'began').exists())
        second = self.launch()
        stdout, stderr = second.communicate(timeout=2)
        self.assertNotEqual(second.returncode, 0)
        self.assertIn('BlockingIOError', stderr)
        self.assert_exit(first)

    def test_restart_adopts_completion_worker(self):
        code = "from pathlib import Path;import time;p=Path('count');p.write_text(str(int(p.read_text())+1) if p.exists() else '1');time.sleep(.6)"
        self.manifest([], completion_jobs=[self.job('finish', code)])
        first = self.launch()
        self.wait_for(lambda: (self.root / 'count').exists())
        first.kill()
        first.communicate(timeout=2)
        self.assert_exit(self.launch())
        self.assertEqual((self.root / 'count').read_text(), '1')
        self.assertEqual(self.state_read()['jobs']['finish']['status'], 'completed')

    def test_deadline_kills_owned_group_and_descendant(self):
        code = ("from pathlib import Path;import signal,subprocess,sys,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);"
                "p=subprocess.Popen([sys.executable,'-c','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)']);"
                "Path('descendant').write_text(str(p.pid));time.sleep(60)")
        self.manifest([self.job('overrun', code)], seconds=1.2)
        start = time.monotonic()
        self.assert_exit(self.launch())
        self.assertLess(time.monotonic() - start, 4)
        self.assertEqual(self.state_read()['jobs']['overrun']['status'], 'time_limit')
        pid = int((self.root / 'descendant').read_text())
        state = module.identity(pid)
        self.assertTrue(state is None or state['state'] in {'Z', 'X'})

    def test_worker_deadline_survives_controller_death(self):
        self.manifest([self.job('overrun', "from pathlib import Path;import time;Path('began').touch();time.sleep(60)")], seconds=1)
        controller = self.launch()
        self.wait_for(lambda: (self.root / 'began').exists())
        started = module.read(self.state / 'jobs/overrun/started.json')
        controller.kill()
        controller.communicate(timeout=2)
        self.wait_for(lambda: not module.alive(started['identity']), timeout=3)
        self.assert_exit(self.launch())
        self.assertEqual(self.state_read()['jobs']['overrun']['status'], 'time_limit')

    def test_completion_reserve_and_report_finalizer(self):
        self.manifest([self.job('search', 'import time;time.sleep(60)')], seconds=2.2,
            completion_reserve_seconds=1.3,
            completion_jobs=[self.job('completion', "from pathlib import Path;Path('completion').touch()")],
            finalizer=self.job('report', "from pathlib import Path;Path('report').touch()"))
        self.assert_exit(self.launch())
        state = self.state_read()
        self.assertEqual(state['jobs']['search']['status'], 'time_limit')
        self.assertEqual(state['jobs']['completion']['status'], 'completed')
        self.assertTrue((self.root / 'report').exists())

    def test_oversized_search_deferred_completion_still_runs(self):
        self.manifest([self.job('too_long', "raise RuntimeError('Must never run')", estimated_seconds=30)],
            seconds=3, completion_reserve_seconds=1,
            completion_jobs=[self.job('finish', "from pathlib import Path;Path('finish').touch()")])
        self.assert_exit(self.launch())
        self.assertEqual(self.state_read()['jobs']['too_long']['status'], 'deferred_budget')
        self.assertEqual(self.state_read()['jobs']['finish']['status'], 'completed')

    def test_detach_and_stop(self):
        self.manifest([self.job('slow', "from pathlib import Path;import time;Path('began').touch();time.sleep(60)")])
        launcher = self.launch(detach=True)
        self.assert_exit(launcher)
        self.wait_for(lambda: (self.root / 'began').exists())
        saved = self.state_read()['controller_identity']
        self.assertTrue(module.alive(saved))
        (self.state / 'STOP').touch()
        self.wait_for(self.finished)
        self.assertEqual(self.state_read()['jobs']['slow']['status'], 'stopped')

    def test_reused_identity_never_signalled_and_manifest_pinned(self):
        live = module.identity(os.getpid())
        fake = {**live, 'start_ticks': live['start_ticks'] + 1}
        self.assertFalse(module.alive(fake))
        self.assertFalse(module.signal_owned_group([fake], signal.SIGKILL))
        self.manifest([])
        self.assert_exit(self.launch())
        manifest = module.read(self.path)
        manifest['jobs'] = [self.job('new', "raise RuntimeError('Must not run')")]
        self.path.write_text(json.dumps(manifest))
        handle = self.launch()
        stdout, stderr = handle.communicate(timeout=3)
        self.assertNotEqual(handle.returncode, 0)
        self.assertIn('Manifest changed', stderr)

    def test_input_hash_change_refuses_execution(self):
        file = self.root / 'script.py'
        file.write_text('print(1)')
        pinned = module.digest(file)
        self.manifest([self.job('script', 'print(2)')], input_sha256={'script.py': pinned})
        file.write_text('print(3)')
        handle = self.launch()
        stdout, stderr = handle.communicate(timeout=3)
        self.assertNotEqual(handle.returncode, 0)
        self.assertIn('Pinned input changed', stderr)

    def test_expired_wrapper_never_launches_worker(self):
        directory = self.root / 'direct-wrapper'
        directory.mkdir()
        spec_path = directory / 'spec.json'
        value = {'nonce': 'controlled-test', 'manifest_sha256': 'test-only',
                 'controller_sha256': module.digest(SOURCE), 'input_sha256': {},
                 'argv': [sys.executable, '-c', "from pathlib import Path;Path('must_not_exist').touch()"],
                 'working_directory': str(self.root), 'deadline_timestamp': time.time() - 1,
                 'termination_grace_seconds': .15, 'poll_seconds': .05, 'stop_file': None}
        spec_path.write_text(json.dumps(value))
        handle = subprocess.Popen([sys.executable, str(SOURCE), '--job-wrapper', str(spec_path),
                                   '--spec-sha256', module.digest(spec_path)],
                                  start_new_session=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.handles.append(handle)
        self.assert_exit(handle)
        self.assertFalse((self.root / 'must_not_exist').exists())
        receipt = module.read(directory / 'receipt.json')
        self.assertEqual(receipt['status'], 'time_limit')
        self.assertFalse(receipt['worker_launched'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
