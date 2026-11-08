"""Synthetic orchestration tests; no production prediction or optimizer call."""
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

import engine


def frame(dates):
    rows = []
    for date in dates:
        for group, power, target in (("G1", 10., 9.), ("G2", 20., 21.)):
            rows.append(dict(ts=engine.kst(date), grp=group, p_reference=power,
                             static_capacity=100., night=False, cosz=.8,
                             wa_cloud=50., wb_cloud=50., y=target, smp=2., k=3.))
    return pd.DataFrame(rows)


class EngineFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.out = self.root / "campaign"
        self.out.mkdir()
        self.candidate = self.root / "candidate"
        self.labels = self.root / "late_labels.parquet"
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        for name, value in (("ROOT", self.root), ("OUT", self.out),
                            ("CANDIDATE", self.candidate), ("LATE_LABELS", self.labels)):
            self.stack.enter_context(patch.object(engine, name, value))
        self.stack.enter_context(patch.object(engine, "guard"))
        self.stack.enter_context(patch.object(engine, "no_other_training"))
        self.configs = engine.transport.configs()
        self.config = next(c for c in self.configs if c["id"] == "s000")
        self.primary = frame(["2023-07-01 12:00", "2024-05-31 12:00"])
        self.recent = frame(["2024-07-01 12:00", "2024-10-01 12:00", "2025-01-01 12:00"])
        self.latest = frame(["2025-03-02 12:00", "2025-03-10 12:00"])
        self.test = frame(["2025-06-02 12:00"])
        for split, data in (("primary", self.primary), ("recent", self.recent),
                            ("latest", self.latest), ("test", self.test)):
            saved = data if split in {"primary", "recent"} else data.drop(columns=["y", "smp", "k"])
            engine.parquet(self.out / "data" / (split + ".parquet"), saved)
        engine.parquet(self.labels, self.latest[engine.KEYS + ["y", "smp", "k"]])
        engine.save(self.out / "configs.json", self.configs)
        self.protocol = {"source_sha256": {}, "input_sha256": {"late_labels.parquet": engine.sha(self.labels)},
                         "prepared_data_sha256": {}, "selection_rule": "all12 rank recent, worst quarter, id"}
        engine.save(self.out / "protocol.json", self.protocol)
        self.stack.enter_context(patch.object(engine, "verify_protocol", return_value=self.protocol))

    def model(self):
        return dict(version=1, config=self.config,
                    columns=[dict(context=0, scenario="G2_to_G1"), dict(context=0, scenario="G1_to_G2")],
                    coefficients=[0., 0.])

    def completed(self, eligible=False):
        rows = [dict(id=c["id"], config=c, eligible=eligible and c["id"] == "s000",
                     rank=[.999, .999, c["id"]]) for c in self.configs]
        folder = self.out / "trials/s000"
        engine.save(folder / "model.json", dict(config=self.config, training={"fold": "primary"}, transport_model=self.model()))
        engine.save(folder / "result.json", rows[-4])
        return rows

    def fake_export(self, test, selection, audit):
        self.assertNotIn("model", selection)
        self.assertNotIn("coefficients", json.dumps(selection))
        self.candidate.mkdir()
        (self.candidate / "submission_files.zip").write_bytes(b"synthetic export")
        record = dict(selection=selection, files_sha256={"submission_files.zip": engine.sha(self.candidate / "submission_files.zip")},
                      recommendation="NOT_RECOMMENDED" if audit["metrics"]["ratio"] >= 1 else "UNSCORED_CANDIDATE_REQUIRES_OFFICIAL_EVALUATION")
        engine.save(self.candidate / "manifest.json", record)
        return record

    def test_strict_json_preserves_existing_on_nonfinite(self):
        path = self.out / "strict.json"
        engine.save(path, {"value": np.int64(4), "array": np.array([1., 2.])})
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            engine.save(path, {"bad": np.float64(np.nan)})
        self.assertEqual(path.read_bytes(), before)

    def test_metric_and_conservation_are_independent(self):
        data = self.primary.assign(p=self.primary.p_reference)
        self.assertEqual(engine.metric(data)["W"], 24.)
        self.assertEqual(engine.metric(data)["S"], 117.6)
        engine.physical(data, data.p.to_numpy(), self.config)
        bad = data.p.to_numpy().copy()
        bad[0] += .01
        with self.assertRaises(AssertionError):
            engine.physical(data, bad, self.config)

    def test_predict_receives_no_labels_and_fit_is_primary_only(self):
        actual_predict = engine.transport.predict
        actual_read = pd.read_parquet
        def fitted(data, config):
            pd.testing.assert_frame_equal(data, self.primary)
            self.assertLessEqual(data.ts.max(), engine.kst("2024-06-01"))
            return self.model(), {"synthetic_fixture": True}
        def predicting(data, config, model):
            self.assertFalse({"y", "smp", "k"} & set(data))
            return actual_predict(data, config, model)
        def reading(path, *args, **kwargs):
            if Path(path) == self.out / "data/recent.parquet":
                self.assertTrue((self.out / "trials/s000/model.json").exists())
            return actual_read(path, *args, **kwargs)
        with patch.object(engine.transport, "fit", side_effect=fitted) as fit_call, \
                patch.object(engine.transport, "predict", side_effect=predicting), \
                patch.object(pd, "read_parquet", side_effect=reading):
            result = engine.trial("s000")
            self.assertEqual(result["status"], "PASS")
            self.assertFalse(result["eligible"])
            self.assertEqual(engine.trial("s000"), result)
            self.assertEqual(fit_call.call_count, 1)
        receipt = engine.read(self.out / "trials/s000/receipt.json")
        self.assertFalse(receipt["late_targets_loaded"])
        self.assertFalse(receipt["recent_used_for_fit"])
        self.assertEqual(receipt["real_model_fits"], 1)

    def test_partial_fit_is_not_retrained(self):
        engine.save(self.out / "trials/s000/fit_started.json", {"id": "s000"})
        with patch.object(engine.transport, "fit", side_effect=AssertionError("must not fit")):
            with self.assertRaisesRegex(RuntimeError, "PARTIAL_FIT_EXISTS"):
                engine.trial("s000")

    def test_completed_trial_tampering_is_not_silently_reused(self):
        with patch.object(engine.transport, "fit", return_value=(self.model(), {})):
            engine.trial("s000")
        (self.out / "trials/s000/model.json").write_text("{}")
        with patch.object(engine.transport, "fit", side_effect=AssertionError("must not fit")):
            with self.assertRaises(AssertionError):
                engine.trial("s000")

    def test_all_twelve_successes_required_before_selection(self):
        with patch.object(engine, "completed_results", return_value=self.completed(True)[:-1]), \
                patch.object(pd, "read_parquet", side_effect=AssertionError("must not read labels")), \
                patch.object(engine.transport, "fit", side_effect=AssertionError("must not fit")):
            result = engine.complete()
        self.assertEqual(result["status"], "INSUFFICIENT_COMPLETED_COVERAGE")
        self.assertFalse(result["late_targets_loaded"])
        self.assertFalse(self.candidate.exists())
        self.assertFalse((self.out / "completion/selection_frozen.json").exists())

    def test_empty_shortlist_is_not_candidate_verification(self):
        with patch.object(engine, "completed_results", return_value=self.completed(False)), \
                patch.object(pd, "read_parquet", side_effect=AssertionError("must not read labels")):
            result = engine.complete()
        self.assertEqual(result["status"], "NO_QUALIFYING_RECIPE")
        self.assertFalse(result["exported"])
        self.assertFalse(result["official_improvement_verified"])

    def test_late_decode_occurs_after_both_freezes_and_never_refits(self):
        original_read = pd.read_parquet
        late_reads = []
        def reading(path, *args, **kwargs):
            if Path(path) == self.labels:
                late_reads.append(True)
                selection = engine.read(self.out / "completion/selection_frozen.json")
                frozen = engine.read(self.out / "completion/predictions_frozen.json")
                self.assertTrue(selection["before_late_targets"] and frozen["before_late_targets"])
                engine.files_checked(self.out / "completion", frozen)
            return original_read(path, *args, **kwargs)
        with patch.object(engine, "completed_results", return_value=self.completed(True)), \
                patch.object(pd, "read_parquet", side_effect=reading), \
                patch.object(engine.transport, "fit", side_effect=AssertionError("must not fit")), \
                patch.object(engine, "export", side_effect=self.fake_export) as export_call:
            result = engine.complete()
            self.assertEqual(result["recommendation"], "NOT_RECOMMENDED")
            self.assertEqual(result["real_model_fits"], 0)
            self.assertEqual(engine.complete(), result)
            self.assertEqual(export_call.call_count, 1)
        self.assertEqual(len(late_reads), 1)

    def test_resume_after_audit_preserves_freezes_without_decoding_late_again(self):
        rows = self.completed(True)
        with patch.object(engine, "completed_results", return_value=rows), \
                patch.object(engine, "export", side_effect=RuntimeError("synthetic interruption")):
            with self.assertRaisesRegex(RuntimeError, "synthetic interruption"):
                engine.complete()
        names = ["shortlist.json", "selection_frozen.json", "predictions_frozen.json", "audit.json"]
        before = {name: engine.sha(self.out / "completion" / name) for name in names}
        original_read = pd.read_parquet
        def no_late_read(path, *args, **kwargs):
            self.assertNotEqual(Path(path), self.labels)
            return original_read(path, *args, **kwargs)
        with patch.object(engine, "completed_results", return_value=rows), \
                patch.object(pd, "read_parquet", side_effect=no_late_read), \
                patch.object(engine, "export", side_effect=self.fake_export):
            result = engine.complete()
        self.assertTrue(result["exported"])
        self.assertEqual(before, {name: engine.sha(self.out / "completion" / name) for name in names})


if __name__ == "__main__":
    unittest.main()
