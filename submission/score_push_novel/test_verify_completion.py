"""Synthetic no-fit tests of terminal barriers and independent checks."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import numpy as np
import pandas as pd

SPEC = importlib.util.spec_from_file_location("novel_independent_verifier_test_target", Path(__file__).with_name("verify_completion.py"))
V = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


class TerminalBarrierTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.out = self.root / "analysis_outputs/research_novel_20261108"
        self.directory = self.out / "controller_state"
        self.source = self.root / "submission/score_push_novel/controller.py"
        self.source.parent.mkdir(parents=True)
        self.source.write_text("synthetic controller only\n")
        self.manifest = {"deadline_utc": V.DEADLINE, "jobs": [{"id": "t000"}],
            "completion_jobs": [{"id": "completion"}], "finalizer": {"id": "report"}, "input_sha256": {}}
        put(self.out / "controller_manifest.json", self.manifest)
        self.identity = {"pid": 12345, "pgid": 12345, "start_ticks": 7, "boot_id": "synthetic-boot"}
        self.state = {"phase": "finished", "controller_sha256": V.sha(self.source),
            "manifest_sha256": V.sha(self.out / "controller_manifest.json"), "deadline_utc": V.DEADLINE,
            "controller_identity": self.identity, "jobs": {name: {"status": "completed"} for name in ("t000", "completion", "report")}}
        self.save_state()

    def tearDown(self):
        self.tmp.cleanup()

    def save_state(self):
        put(self.directory / "state.json", self.state)

    def call(self, live=None, errors=None):
        return V.terminal_gate(self.directory, self.root, self.out,
            lambda: ("synthetic-boot", live or {}, errors or []))

    def test_missing_and_active_state_do_not_open_research_artifacts(self):
        self.assertFalse(V.terminal_gate(self.out / "missing", self.root, self.out)[0])
        self.state["phase"] = "search"
        self.save_state()
        self.assertFalse(self.call()[0])
        # No data, config, model or late label file exists in this fixture.

    def test_terminal_no_processes_passes(self):
        ready, evidence, _ = self.call()
        self.assertTrue(ready)
        self.assertEqual(evidence["live_recorded_identity_pids"], [])

    def test_exact_identity_or_descendant_group_blocks(self):
        self.assertFalse(self.call({12345: self.identity})[0])
        child = {**self.identity, "pid": 12346, "start_ticks": 8}
        self.assertFalse(self.call({12346: child})[0])

    def test_pid_reuse_in_different_group_does_not_imply_worker_live(self):
        reused = {**self.identity, "pgid": 99999, "start_ticks": 777}
        self.assertTrue(self.call({12345: reused})[0])

    def test_unreadable_process_scan_fails_closed(self):
        self.assertFalse(self.call(errors=[{"pid": 5, "error": "PermissionError"}])[0])

    def test_controller_source_or_deadline_change_rejected(self):
        self.source.write_text("changed bytes")
        with self.assertRaises(AssertionError):
            self.call()
        self.state["controller_sha256"] = V.sha(self.source)
        self.state["deadline_utc"] = "2026-11-08T15:00:00Z"
        self.save_state()
        with self.assertRaises(AssertionError):
            self.call()

    def test_pending_completion_or_report_failure_is_checkpoint(self):
        for name, status in (("t000", "pending"), ("completion", "failed"), ("report", "time_limit")):
            with self.subTest(name=name):
                self.state["jobs"][name]["status"] = status
                self.save_state()
                self.assertFalse(self.call()[0])
                self.state["jobs"][name]["status"] = "completed"

    def test_controller_receipt_nonce_and_bytes_checked(self):
        receipt = {"nonce": "correct", "manifest_sha256": self.state["manifest_sha256"], "status": "completed", "exit_code": 0}
        path = self.directory / "jobs/t000/receipt.json"
        put(path, receipt)
        self.state["jobs"]["t000"].update(nonce="correct", exit_code=0, receipt_sha256=V.sha(path))
        self.save_state()
        self.assertTrue(self.call()[0])
        receipt["nonce"] = "wrong"
        put(path, receipt)
        self.state["jobs"]["t000"]["receipt_sha256"] = V.sha(path)
        self.save_state()
        with self.assertRaises(AssertionError):
            self.call()

    def test_checkpoint_never_written_as_terminal_pass(self):
        self.assertIsNone(V.persist_terminal({"verification_status": "CHECKPOINT_ONLY"}, self.out))
        result = {"verification_status": "PASS", "outcome": "NO_QUALIFYING_RECIPE", "utc": "old"}
        path = V.persist_terminal(result, self.out)
        V.persist_terminal({**result, "utc": "new"}, self.out)
        self.assertEqual(V.read(path)["utc"], "old")
        with self.assertRaises(AssertionError):
            V.persist_terminal({**result, "outcome": "EXPORTED_UNSCORED_CANDIDATE"}, self.out)


class ScientificCheckTests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame({"ts": pd.to_datetime(["2024-06-01 08:00", "2024-06-01 08:00", "2024-06-01 09:00", "2024-06-01 09:00"]).tz_localize("Asia/Seoul"),
            "grp": ["G1", "G2", "G1", "G2"], "p_reference": [30., 20., 10., 40.], "static_capacity": [100.] * 4,
            "night": [False] * 4, "y": [20., 20., 20., 20.], "smp": [1., 2., 3., 4.], "k": [2.] * 4})

    def test_monetary_weighted_error_is_not_unweighted_mae(self):
        frame = self.frame()
        result = V.score(frame, frame.p_reference)
        self.assertEqual(result["W"], 240.)
        self.assertEqual(result["revenue"], 200.)
        self.assertEqual(result["S"], 176.)

    def test_energy_preservation_is_family_specific(self):
        f = self.frame()
        V.physical(f, [25., 25., 15., 35.], "temporal")
        V.physical(f, [25., 25., 5., 45.], "spatial")
        with self.assertRaises(AssertionError):
            V.physical(f, [25., 25., 5., 45.], "temporal")
        with self.assertRaises(AssertionError):
            V.physical(f, [25., 25., 15., 40.], "spatial")

    def test_capacity_and_night_zero_are_checked(self):
        f = self.frame()
        with self.assertRaises(AssertionError):
            V.physical(f, [-1., 51., 10., 40.], "spatial")
        with self.assertRaises(AssertionError):
            V.physical(f, [101., -51., 10., 40.], "spatial")
        f.loc[0, "night"] = True
        with self.assertRaises(AssertionError):
            V.physical(f, f.p_reference, "temporal")

    def test_gate_uses_fixed_recent_quarters_and_groups(self):
        timestamps = [pd.Timestamp(x, tz="Asia/Seoul") for x in ("2024-07-01", "2024-10-01", "2025-01-01") for _ in range(2)]
        recent = pd.DataFrame({"ts": timestamps, "grp": ["G1", "G2"] * 3,
            "y": [50.] * 6, "smp": [1.] * 6, "k": [1.] * 6, "p_reference": [60.] * 6})
        primary = recent.copy()
        _, quarters, groups, flags = V.development(primary, recent, np.full(6, 59.), np.full(6, 59.))
        self.assertEqual(set(quarters), {"jun_aug", "sep_nov", "dec_feb"})
        self.assertTrue(all(flags.values()))
        worse = np.array([59., 59., 62., 62., 59., 59.])
        _, _, _, flags = V.development(primary, recent, np.full(6, 59.), worse)
        self.assertFalse(flags["recent_quarters"])

    def test_path_escape_and_result_float_comparison(self):
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaises(AssertionError):
                V.contained(Path(name), "../outside")
        V.compare_numbers([1.000000000001, "id"], [1., "id"])
        with self.assertRaises(AssertionError):
            V.compare_numbers([1.01, "id"], [1., "id"])

    def test_equal_predictions_have_zero_weekly_interval(self):
        f = self.frame().assign(p=lambda frame: frame.p_reference)
        recorded = {"replicates": 2000, "random_seed": 20261108, "weeks": 1,
            "relative_W_change_pct": 0., "CI95": [0., 0.], "zero_in_CI": True,
            "selection_use": False, "conditional_on_saved_model_and_development_selection": True}
        V.check_weekly_bootstrap(f, recorded)
        with self.assertRaises(AssertionError):
            V.check_weekly_bootstrap(f, {**recorded, "CI95": [-.01, .01]})

    def test_zip_checks_preserved_composition_baseline_and_exact_rounding(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            candidate = root / "candidate"
            candidate.mkdir()
            times = pd.date_range("2025-06-01 01:00", periods=8760, freq="h", tz="Asia/Seoul")
            frame = pd.DataFrame({"ts": times.repeat(2), "grp": ["G1", "G2"]*8760,
                "p_reference": 1., "p": 1.12549, "night": False, "static_capacity": 5.})
            composition = b"site,group\na,G1\nb,G2\n"
            reference_csv = pd.DataFrame({"group": frame.grp, "ts": frame.ts.astype(str), "forecast_kwh": frame.p_reference}).to_csv(index=False).encode()
            forecast = pd.DataFrame({"group": frame.grp, "ts": frame.ts.astype(str), "forecast_kwh": np.round(frame.p, 3)}).to_csv(index=False).encode()
            (candidate / "composition.csv").write_bytes(composition)
            (candidate / "forecast.csv").write_bytes(forecast)
            best = root / "best.zip"
            with zipfile.ZipFile(best, "w") as archive:
                archive.writestr("composition.csv", composition)
                archive.writestr("forecast.csv", reference_csv)
            with zipfile.ZipFile(candidate / "submission_files.zip", "w") as archive:
                archive.writestr("composition.csv", composition)
                archive.writestr("forecast.csv", forecast)
            self.assertEqual(V.verify_zip(candidate, frame, best), V.sha(candidate / "submission_files.zip"))
            (candidate / "composition.csv").write_bytes(b"changed")
            with self.assertRaises(AssertionError):
                V.verify_zip(candidate, frame, best)


if __name__ == "__main__":
    unittest.main()
