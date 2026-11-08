"""No-fit tests for descriptive audit labels, uncertainty, and process barrier."""
import json
from pathlib import Path
import shutil
import tempfile
import types
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

import audit_saved


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, allow_nan=False))


def data():
    rows = []
    for date, cloud in (("2024-07-02 12:00", 10.), ("2024-07-09 12:00", 90.), ("2024-08-06 12:00", 50.)):
        for group, power, target, pred in (("G1", 10., 9., 9.8), ("G2", 20., 21., 20.2)):
            rows.append(dict(ts=pd.Timestamp(date, tz="Asia/Seoul"), grp=group, p_reference=power, p=pred,
                             y=target, smp=2., k=3., night=False, static_capacity=100., wa_cloud=cloud))
    return pd.DataFrame(rows)


class AuditTests(unittest.TestCase):
    def test_paired_weeks_keep_both_groups_and_reproducibility(self):
        result = audit_saved.paired_week_bootstrap(data(), replicates=400)
        self.assertEqual(result, audit_saved.paired_week_bootstrap(data(), replicates=400))
        self.assertEqual(result["weeks"], 3)
        np.testing.assert_allclose(result["CI95_relative_W_change_pct"], [-20., -20.], atol=1e-10)
        self.assertFalse(result["zero_in_CI"])
        self.assertFalse(result["selection_use"])

    def test_zero_error_night_does_not_invent_ratios(self):
        frame = data().iloc[:2].copy()
        frame[["p_reference", "p", "y"]] = 0.
        frame["night"] = True
        result = audit_saved.statistics(frame)
        self.assertTrue(result["zero_reference_error"])
        self.assertIsNone(result["relative_W_change_pct"])
        self.assertIsNone(result["candidate_W_pct"])
        json.dumps(result, allow_nan=False)

    def test_month_is_hour_ending_and_weather_is_forecast_only(self):
        saved = data().iloc[:2].drop(columns="wa_cloud").copy()
        saved["ts"] = pd.Timestamp("2024-08-01 00:00", tz="Asia/Seoul")
        features = saved[audit_saved.KEYS].assign(wa_cloud=[np.nan, 80.])
        result = audit_saved.joined_features(saved, features)
        self.assertEqual(set(result.month), {"2024-07"})
        self.assertEqual(result.weather.tolist(), ["missing_forecast", "mixed_20_to80"])
        changed = saved.assign(y=999999.)
        self.assertEqual(audit_saved.joined_features(changed, features).weather.tolist(), result.weather.tolist())

    def test_active_process_barrier_before_any_parquet(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "campaign"
            write(out / "protocol.json", {})
            fake = types.SimpleNamespace(terminal_gate=lambda *a, **k: (False, {"reason": "worker alive"}, None))
            with patch.object(audit_saved, "pinned_verifier", return_value=fake), \
                    patch.object(pd, "read_parquet", side_effect=AssertionError("must not read data")):
                result = audit_saved.run(root, out)
            self.assertEqual(result["status"], "CHECKPOINT_ONLY")
            self.assertFalse(result["data_read"])
            self.assertFalse((out / "audits").exists())

    def test_only_committed_saved_outputs_audited_and_no_model_values_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "campaign"
            (out / "data").mkdir(parents=True)
            helper = root / Path(audit_saved.__file__).resolve().relative_to(audit_saved.ROOT)
            helper.parent.mkdir(parents=True)
            shutil.copyfile(audit_saved.__file__, helper)
            saved = data().drop(columns="wa_cloud")
            for split in ("primary", "recent"):
                data().drop(columns="p").to_parquet(out / "data" / (split + ".parquet"), index=False)
            configs = [{"id": "s000", "family": "spatial"}, {"id": "s001", "family": "spatial"}]
            write(out / "configs.json", configs)
            protocol = {"source_sha256": {}, "input_sha256": {}, "configs_sha256": audit_saved.sha(out / "configs.json"),
                        "prepared_data_sha256": {split + ".parquet": audit_saved.sha(out / "data" / (split + ".parquet")) for split in ("primary", "recent")}}
            write(out / "protocol.json", protocol)
            folder = out / "trials/s000"
            folder.mkdir(parents=True)
            for split in ("primary", "recent"):
                saved.to_parquet(folder / (split + ".parquet"), index=False)
            write(folder / "model.json", {"private_learned_coefficients": [0.123456789]})
            receipt = {"protocol_sha256": audit_saved.sha(out / "protocol.json"),
                       "files_sha256": {name: audit_saved.sha(folder / name) for name in ("primary.parquet", "recent.parquet", "model.json")}}
            write(folder / "receipt.json", receipt)
            write(folder / "result.json", {"id": "s000", "config": configs[0], "status": "PASS", "eligible": False,
                                          "receipt_sha256": audit_saved.sha(folder / "receipt.json")})
            write(out / "completion/result.json", {"completed_trials": 1, "exported": False, "files_sha256": {}})
            write(out / "independent_completion_check.json", {"verification_status": "PASS", "protocol_sha256": audit_saved.sha(out / "protocol.json"),
                                                               "completion_result_sha256": audit_saved.sha(out / "completion/result.json")})
            def verify_mapping(directory, mapping):
                for name, expected in mapping.items():
                    self.assertEqual(audit_saved.sha(Path(directory) / name), expected)
            fake = types.SimpleNamespace(terminal_gate=lambda *a, **k: (True, {}, None), verify_mapping=verify_mapping)
            original_read = audit_saved.read
            def read_without_model(path):
                self.assertNotEqual(Path(path).name, "model.json")
                return original_read(path)
            before = {str(p): audit_saved.sha(p) for p in out.rglob("*") if p.is_file()}
            with patch.object(audit_saved, "pinned_verifier", return_value=fake), \
                    patch.object(audit_saved, "read", side_effect=read_without_model):
                result = audit_saved.run(root, out)
            self.assertEqual(result["completed_trial_count"], 1)
            self.assertEqual(result["model_fits"], 0)
            self.assertEqual(result["predictions_computed"], 0)
            self.assertFalse(result["late_audit_included"])
            text = Path(result["audit"]).read_text()
            self.assertNotIn("private_learned_coefficients", text)
            self.assertNotIn("0.123456789", text)
            report = json.loads(text)
            self.assertEqual(report["missing_trial_ids"], ["s001"])
            self.assertFalse(report["selection_changed"])
            self.assertFalse(report["official_improvement_verified"])
            self.assertEqual(before, {path: audit_saved.sha(path) for path in before})


if __name__ == "__main__":
    unittest.main()
