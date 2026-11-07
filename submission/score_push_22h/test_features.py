"""Synthetic invariants for calibration transformations; no model fits."""
import unittest

import numpy as np
import pandas as pd

import features


def example():
    frame = pd.DataFrame({
        "ts": pd.to_datetime(["2024-01-02", "2024-01-02", "2024-01-03", "2024-01-04"]).tz_localize("Asia/Seoul"),
        "grp": ["G1"] * 4,
        "model_origin": ["2023-01-01", "2023-06-01", "2023-06-01", "2023-06-01"],
        "train_history_days": [365.0] * 4,
        "capacity_kw": [100.0] * 4,
        "static_capacity": [120.0] * 4,
        "p": [20.0, 20.0, 0.0, 20.0],
        "y": [-5.0, -5.0, 10.0, 40.0],
        "smp": [2.0, 2.0, 2.0, 0.0],
        "k": [3, 3, 3, 3],
        "night": [False] * 4,
    })
    for column in (*features.WEATHER, *features.CALENDAR):
        frame[column] = 1.0
    return frame


class FeatureTests(unittest.TestCase):
    def test_targets_weights_and_duplicate_balance(self):
        frame = example()
        cfg = {"features": "age", "mode": "additive", "half_life": None}
        X, target, weight = features.training(frame, cfg, "2024-01-04")
        units = features.scale(frame, cfg)
        np.testing.assert_allclose(target * units, frame.y - frame.p)
        self.assertLess(target[0], 0)  # Negative observed generation is retained.
        np.testing.assert_allclose(weight, [1, 1, 2, 0])
        self.assertEqual(tuple(X.columns), features.FEATURE_FAMILIES["age"])
        self.assertEqual(X.forecast_age_days.iloc[0], 366.0)

    def test_weighted_target_loss_equals_energy_loss_up_to_constant(self):
        frame = example().iloc[[0, 2]].copy()
        frame.loc[frame.index[1], "capacity_kw"] = 200.0
        for mode in ("additive", "multiplicative"):
            cfg = {"mode": mode}
            _, target, weights = features.training(frame, cfg, "2024-01-04")
            units = features.scale(frame, cfg)
            delta = np.array([0.2, -0.1])
            energy_loss = np.sum(frame.smp * frame.k * np.abs(frame.p + delta * units - frame.y))
            target_loss = np.sum(weights * np.abs(delta - target))
            self.assertAlmostEqual(target_loss, energy_loss / np.mean(frame.smp * frame.k * units))

    def test_decay_and_zero_price(self):
        frame = example()
        _, _, weights = features.training(frame, {"half_life": 1}, "2024-01-04")
        np.testing.assert_allclose(weights, np.array([0.125, 0.125, 0.5, 0]) / 0.1875)

    def test_target_independence_and_missing_weather(self):
        frame = example()
        original = features.engineer(frame)
        frame["y"], frame["smp"], frame["k"] = -999, 99, 99
        pd.testing.assert_frame_equal(original, features.engineer(frame))
        frame.loc[0, "wa_cloud"] = np.nan
        self.assertTrue(np.isnan(features.engineer(frame).wa_cloud.iloc[0]))

    def test_guards(self):
        frame = example()
        with self.assertRaisesRegex(ValueError, "cutoff"):
            features.training(frame, {}, "2024-01-03")
        frame.loc[0, "model_origin"] = "2024-01-02"
        with self.assertRaisesRegex(ValueError, "strictly earlier"):
            features.training(frame, {}, "2024-01-04")
        frame = example()
        frame["smp"] = 0.0
        with self.assertRaisesRegex(ValueError, "positive total"):
            features.training(frame, {}, "2024-01-04")
        frame = example()
        frame.loc[0, "night"] = True
        with self.assertRaisesRegex(ValueError, "daylight"):
            features.training(frame, {}, "2024-01-04")

    def test_bounded_application_night_and_capacity(self):
        frame = example()
        frame.loc[3, "night"] = True
        cfg = {"mode": "additive", "bound": 0.5, "shrink": 0.5}
        units = features.scale(frame, cfg)
        actual = features.apply(frame, [99, -99, 0.1, 99], cfg)
        expected = np.clip(frame.p + np.array([0.25, -0.25, 0.05, 0.25]) * units, 0, frame.static_capacity)
        expected[3] = 0.0
        np.testing.assert_allclose(actual, expected)
        frame.loc[0, "p"] = 119.0
        self.assertEqual(features.apply(frame, [99, 0, 0, 0], cfg)[0], 120.0)
        cfg["mode"] = "multiplicative"
        self.assertGreater(features.scale(frame, cfg)[2], 0.0)
        frame.loc[3, ["capacity_kw", "cosz"]] = np.nan
        self.assertEqual(features.apply(frame, [0, 0, 0, 0], cfg)[3], 0.0)


if __name__ == "__main__":
    unittest.main()
