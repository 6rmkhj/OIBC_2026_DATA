# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "pandas"]
# ///
# How to run: python submission/score_push_verify_calibration_data.py
"""Check original calibration inputs and exercise the actual scalar functions."""
from __future__ import annotations

import csv
import json
import sys
from math import fsum, isclose, isnan
from typing import Final

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from score_push_verify_group_data import ROOT, sha

OUT: Final = ROOT / "analysis_outputs/renew_20261105/calibration_wave"
sys.path.insert(0, str(ROOT / "submission/score_push_renew"))


def fixtures() -> dict[str, bool]:
    import pandas as pd  # noqa: PANDAS_OK -- exercise the existing calibration API on synthetic inputs
    from cal_math import apply, conditions, fit, fit_factor
    frame = pd.DataFrame({"ts": pd.date_range("2020-01-01 12:00", periods=180, tz="Asia/Seoul"), "grp": "G1",
                          "p_reference": 100., "y": [90.] * 160 + [110.] * 20, "smp": [1.] * 160 + [1000.] * 20,
                          "k": 1., "wa_temp": 5., "extra_wa_snow": .001, "static_capacity": 1000.})
    mask = np.ones(180, dtype=bool)
    factor = fit_factor(frame, mask)
    assert isclose(factor.raw_median, 1.1) and factor.support_rows == factor.support_days == 180
    assert isclose(fit_factor(frame.assign(smp=frame.smp * 7), mask).factor, factor.factor)
    assert np.median(frame.y / frame.p_reference) == .9
    assert not fit_factor(frame.iloc[:149], mask[:149]).supported
    assert not fit_factor(frame.assign(ts=frame.ts.iloc[0]), mask).supported
    assert fit_factor(frame.assign(smp=0.), mask).factor == 1.
    assert fit_factor(frame.assign(p_reference=0.), mask).factor == 1.
    fitted = fit(frame)
    assert isclose(fitted.conditional_snow.factor, 1., abs_tol=1e-12)
    combined = apply(frame, fitted, "temperature_then_snow")
    np.testing.assert_allclose(combined.effective_factor, 1.05, rtol=1e-12)
    np.testing.assert_array_equal(apply(frame.assign(y=-1e30, smp=1e30, k=1e30), fitted, "temperature_then_snow").p, combined.p)
    probe = frame.iloc[:6].assign(wa_temp=[-.1, 0., 10., 20., 30., np.nan], extra_wa_snow=[0., .0009, .001, .1, np.nan, np.nan])
    bins, snow = conditions(probe)
    np.testing.assert_array_equal(bins, [0, 1, 2, 3, 4, -1])
    np.testing.assert_array_equal(snow, [False, False, True, True, False, False])
    assert apply(probe, fitted, "temperature_then_snow").effective_factor.iloc[-1] == 1.
    np.testing.assert_array_equal(apply(frame.assign(static_capacity=100.), fitted, "temperature_only").p, 100.)
    np.testing.assert_array_equal(apply(frame.assign(p_reference=0.), fitted, "snow_only").p, 0.)
    negative_rejected = False
    try:
        apply(frame.assign(p_reference=-1.), fitted, "snow_only")
    except AssertionError:
        negative_rejected = True
    assert negative_rejected
    return {"weighted_median_differs_from_unweighted": True, "weight_scaling_invariant": True,
            "zero_and_unsupported_identity": True, "boundaries_missingness_capacity_night": True,
            "combined_full_temperature_before_second_fit_and_once_shrink": True, "adversarial_labels_ignored_by_apply": True,
            "negative_reference_rejected": negative_rejected}


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol = json.loads((OUT / "protocol.json").read_text())
    for name, digest in protocol["input_sha256"].items():
        assert sha(ROOT / name) == digest, name
    for name, record in protocol["own_sources"].items():
        assert sha(ROOT / record["original"]) == sha(OUT / "sources/own" / name) == record["sha256"]
    for name, digest in json.loads((OUT / "prepared_manifest.json").read_text()).items():
        assert sha(OUT / name) == digest, name
    assignment = json.loads((ROOT / "analysis_outputs/autoresearch_20261103/cache/assignment.json").read_text())
    with (ROOT / "handover 2/01_participant_dataset/sites.csv").open(encoding="utf-8", newline="") as handle:
        sites = list(csv.DictReader(handle))
    assert len(sites) == len({r["site_id"] for r in sites}) == len(assignment) == 253
    capacity = {group: fsum(float(r["capacity_kw"]) for r in sites if assignment[r["site_id"]] == group) for group in ("G1", "G2")}
    stored_capacity = json.loads((OUT / "static_capacity.json").read_text())
    assert all(isclose(capacity[g], stored_capacity[g], rel_tol=1e-12) for g in capacity)
    records = []
    for fold in ("primary", "recent"):
        directory = OUT / "data" / fold
        reference = pq.read_table(ROOT / "analysis_outputs/renew_20261105/recency_wave/comparisons/decay180/ensemble" / fold / "predictions.parquet", columns=["ts", "grp", "y", "smp", "k", "p"]).to_pylist()
        original = pq.read_table(ROOT / "analysis_outputs/score_push_gpu_20261104/data" / fold / "evaluation.parquet", columns=["ts", "grp", "wa_temp", "extra_wa_snow"])
        assert pq.read_table(directory / "feature_projection.parquet").equals(original)
        weather = {(r["ts"], r["grp"]): r for r in original.to_pylist()}
        oracle = {(r["ts"], r["grp"]): r for r in reference}
        rows = pq.read_table(directory / "rows.parquet").to_pylist()
        apply_table = pq.read_table(directory / "apply_inputs.parquet")
        assert set(apply_table.column_names) == {"ts", "grp", "p_reference", "wa_temp", "extra_wa_snow", "static_capacity"}
        inputs = apply_table.to_pylist()
        assert len(rows) == len(inputs) == len(oracle) == (17568 if fold == "primary" else 13104)
        assert {(r["ts"], r["grp"]) for r in rows} == set(oracle)
        for row, apply_row in zip(rows, inputs, strict=True):
            key = row["ts"], row["grp"]
            assert all(row[n] == oracle[key][n] for n in ("y", "smp", "k")) and row["p_reference"] == oracle[key]["p"]
            assert row["night"] == (key not in weather)
            assert not row["night"] or row["p_reference"] == 0.
            assert isclose(row["static_capacity"], capacity[row["grp"]], rel_tol=1e-12)
            for field in ("wa_temp", "extra_wa_snow"):
                expected = weather[key][field] if key in weather else None
                if expected is None or isnan(expected):
                    assert row[field] is None or isnan(row[field])
                else:
                    assert row[field] == expected
            for field in apply_table.column_names:
                actual, expected = apply_row[field], row[field]
                if isinstance(expected, float) and isnan(expected):
                    assert actual is None or isnan(actual)
                else:
                    assert actual == expected
        records.append({"fold": fold, "rows": len(rows), "weather_rows": len(weather), "night_identity_rows": len(rows) - len(weather)})
    result = {"status": "PASS", "protocol_sha256": sha(OUT / "protocol.json"), "prepared_manifest_sha256": sha(OUT / "prepared_manifest.json"),
              "static_capacity": capacity, "records": records, "synthetic_fixtures": fixtures(), "actual_calibration_coefficients_fitted": False}
    (OUT / "independent_data_check.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
