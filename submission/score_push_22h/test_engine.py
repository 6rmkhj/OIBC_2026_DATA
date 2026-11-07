"""No-fit invariants for the continuation engine, including real cache replay."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import engine


class EngineTests(unittest.TestCase):
    def test_unique_effective_calibrator_fits_and_interleaved_ids(self):
        fit_keys = ("method", "features", "mode", "half_life", "num_leaves",
                    "min_child_samples", "n_estimators", "learning_rate", "reg_lambda")
        all_rows = []
        for index in range(32):
            rows = engine.configs_for_base(index)
            self.assertEqual(len(rows), 64)
            self.assertEqual(len({tuple(row[key] for key in fit_keys) for row in rows}), 64)
            self.assertTrue(all(row["base_id"] == f"b{index:02d}" for row in rows))
            all_rows.extend(rows)
        self.assertEqual([row["id"] for row in all_rows], [f"n{i:04d}" for i in range(2048)])

    def test_quarterly_origins_and_search_boundary(self):
        self.assertEqual(len(engine.ORIGINS), 12)
        self.assertEqual(engine.ORIGINS[0], "2021-06-01")
        self.assertEqual(engine.ORIGINS[-1], "2024-03-01")
        self.assertEqual(sum(origin in engine.OLD_ORIGINS for origin in engine.ORIGINS), 4)

    def test_deployment_targets_require_a_frozen_selection(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(engine, "OUT", Path(temp)), \
                patch.object(engine.pq, "read_table") as reader:
            with self.assertRaises(AssertionError):
                engine.deployment_tables("2025-03-01")
            reader.assert_not_called()

    def test_interrupted_generation_receipt_upgrades_without_refit(self):
        config = {"id": "synthetic"}
        with tempfile.TemporaryDirectory() as temp, patch.object(engine.old, "fit_one") as fit:
            folder = Path(temp)
            engine.save(folder / "transform.json", {"training_start": "2021-01-01T00:00:00+09:00"})
            engine.save(folder / "receipt.json", dict(config=config, seed=0, fold="inner_2021-06-01",
                files_sha256={"transform.json": engine.sha(folder / "transform.json")}))
            receipt = engine.generation({"config": config}, "2021-06-01", "2022-06-02", folder, None)
            self.assertEqual(receipt["origin"], "2021-06-01")
            self.assertEqual(receipt["end"], "2022-06-02")
            self.assertEqual(receipt["train_history_days"], 151)
            fit.assert_not_called()

    def test_actual_native_model_reuse_and_pool_cutoff(self):
        config = next(row for row in engine.read(engine.OLD / "configs.json") if row["id"] == "c206")
        base = dict(id="test_only", source_id="c206", config=config)
        tables = engine.search_tables()
        with tempfile.TemporaryDirectory() as temp, patch.object(engine.old, "fit_one", side_effect=AssertionError("No fit allowed")):
            folder = Path(temp) / "origin"
            receipt = engine.generation(base, "2022-06-01", "2023-06-01", folder, tables)
            self.assertEqual(receipt["real_model_fits"], 0)
            predicted = engine.pd.read_parquet(folder / "predictions.parquet")
            original = engine.pd.read_parquet(engine.OLD / "trials/c206/early2022/predictions.parquet")
            engine.pd.testing.assert_frame_equal(predicted[engine.KEYS + ["p"]], original[engine.KEYS + ["p"]], check_exact=True)
            pool = engine.pool_from_origins(base, [("2022-06-01", folder)], tables[0], "2022-12-01")
            self.assertTrue(pool.ts.le(engine.kst("2022-12-01")).all())
            self.assertTrue(pool.ts.gt(pool.model_origin).all())
            self.assertFalse(pool.night.any())
            self.assertGreater(len(pool), 0)


if __name__ == "__main__":
    unittest.main()
