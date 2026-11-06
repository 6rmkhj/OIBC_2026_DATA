# /// script
# requires-python = ">=3.12"
# dependencies = ["pyarrow"]
# ///
# How to run: python submission/score_push_verify_hour.py AFTER worker terminal.
"""Independent weighted-median, transferred-hour and manifest verification."""
from __future__ import annotations

import json
from math import isclose
from zoneinfo import ZoneInfo

import pyarrow as pa
import pyarrow.parquet as pq

from autoresearch_verify_final import metrics
from score_push_verify_hour_data import ROOT, OUT, digest
from score_push_verify_calibration import verify_factor, ensure_terminal


def read(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8-sig"))


def bin_index(row) -> int:
    hour = row["ts"].astimezone(ZoneInfo("Asia/Seoul")).hour
    return sum(hour >= edge for edge in (10, 12, 14, 16))


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    protocol, amendment = read("protocol.json"), read("source_amendment.json")
    data = read("independent_data_check.json")
    assert data["status"] == "PASS" and data["protocol_sha256"] == digest(OUT / "protocol.json")
    assert data["prepared_manifest_sha256"] == digest(OUT / "prepared_manifest.json")
    for mapping in (protocol["input_sha256"], protocol["protected_sha256"]):
        for path, expected in mapping.items():
            assert digest(ROOT / path) == expected, path
    active = protocol["own_sources"] | amendment["own_sources"]
    for name, record in active.items():
        assert digest(ROOT / record["original"]) == record["sha256"]
        assert digest(OUT / record.get("snapshot", "sources/own/" + name)) == record["sha256"]
    for name, record in protocol["snapshots"].items():
        assert digest(ROOT / record["original"]) == digest(OUT / "sources" / f"{name}.py") == record["sha256"]
    release = read("release.json")
    for key, path in (("protocol_sha256", "protocol.json"), ("prepared_manifest_sha256", "prepared_manifest.json"), ("source_amendment_sha256", "source_amendment.json")):
        assert release[key] == digest(OUT / path)
    assert release["approved"]
    for manifest in ("prepared_manifest.json", "terminal_manifest.json"):
        for path, expected in read(manifest).items():
            assert digest(OUT / path) == expected, path
    coefficients = read("coefficients.json")
    assert coefficients["fit_period"] == ["2023-06-01", "2024-06-01"]
    assert coefficients["target_source"] == "data/primary/rows.parquet"
    assert coefficients["target_source_sha256"] == digest(OUT / coefficients["target_source"])
    assert coefficients["fit_columns"] == ["ts", "p_reference", "y", "smp", "k"]
    assert coefficients["timezone"] == "Asia/Seoul"
    assert coefficients["hour_bins"] == ["[0,10)", "[10,12)", "[12,14)", "[14,16)", "[16,24)"]
    primary = pq.read_table(OUT / "data/primary/rows.parquet").to_pylist()
    assert len(coefficients["factors"]["hours"]) == 5
    bins, ones = [bin_index(row) for row in primary], [1.] * len(primary)
    factors = [verify_factor(primary, [b == i for b in bins], saved, ones)
               for i, saved in enumerate(coefficients["factors"]["hours"])]
    result = read("results.json")
    assert result["candidate_count"] == 1 and result["real_scalar_fit_count"] == 5 and result["tree_fits"] == 0
    assert not result["loaded_existing_coefficients"] and not result["confirmation_loaded"] and not result["test_loaded"]
    assert result["primary_fit_partly_in_sample"] and len(result["records"]) == 1
    record = result["records"][0]
    assert record["arm"] == "hour_bias" and record["fixed_hour_shrink"] == .5 and not record["alpha_optimization"]
    scores = {}
    for fold in ("primary", "recent"):
        source = pq.read_table(OUT / "data" / fold / "rows.parquet").to_pylist()
        original = {(r["ts"], r["grp"]): r for r in source}
        directory = OUT / "comparisons/hour_bias" / fold
        rows = pq.read_table(directory / "predictions.parquet").to_pylist()
        assert len(rows) == len(original) and {(r["ts"], r["grp"]) for r in rows} == set(original)
        clipped = 0
        for row in rows:
            base = original[(row["ts"], row["grp"])]
            assert all(row[n] == base[n] for n in ("y", "smp", "k", "p_reference", "static_capacity"))
            index = bin_index(base)
            effective = 1 + .5 * (factors[index] - 1)
            before = base["p_reference"] * effective
            prediction = max(0., min(base["static_capacity"], before))
            assert row["hour_bin"] == index
            for name, value in (("bounded_hour_factor", factors[index]), ("effective_hour_factor", effective), ("before_capacity_clip", before), ("p", prediction)):
                assert isclose(row[name], value, rel_tol=1e-12, abs_tol=1e-8), name
            assert row["capacity_clipped"] == (before > base["static_capacity"])
            assert 0 <= row["p"] <= base["static_capacity"]
            assert base["p_reference"] != 0 or row["p"] == 0
            clipped += row["capacity_clipped"]
        scores[fold] = {name: metrics(rows, name) for name in ("p", "p_reference")}
        saved = read(f"comparisons/hour_bias/{fold}/metrics.json")
        for name, measurements in scores[fold].items():
            for metric, value in measurements.items():
                assert isclose(value, record["scores"][fold][name][metric], rel_tol=1e-12, abs_tol=1e-4)
                assert saved[name][metric] == record["scores"][fold][name][metric]
        receipt = read(f"comparisons/hour_bias/{fold}/application.json")
        assert receipt["passed"] and receipt["exact_replay"] and receipt["zero_reference_stays_zero"] and receipt["labels_not_used_in_apply"]
        assert receipt["rows"] == len(rows) and receipt["capacity_clip_count"] == clipped
        assert receipt["prediction_sha256"] == digest(directory / "predictions.parquet")
        assert receipt["coefficient_sha256"] == digest(OUT / "coefficients.json")
    eligible = all(scores[f]["p"]["W"] < scores[f]["p_reference"]["W"] for f in scores)
    assert record["eligible"] == eligible and read("comparisons/hour_bias/decision.json") == record
    assert result["selected"] == (record if eligible else None) and result["reference_retained"] == (not eligible)
    controller = read("controller_receipt.json")
    assert controller["exit_code"] == 0 and controller["real_scalar_fit_count"] == 5 and controller["tree_fits"] == 0
    identity = controller["identity"]
    assert identity["priority_class"] == 32 and identity["pyarrow_cpu"] == identity["pyarrow_io"] == 4
    assert all(pool["num_threads"] == 16 for pool in identity["threadpools"])
    ensure_terminal(identity)
    assert not (OUT / "tmp").exists()
    evidence = {"status": "PASS", "factors": factors, "scores": scores, "eligible": eligible,
                "protected_files": len(protocol["protected_sha256"]), "coefficient_sha256": digest(OUT / "coefficients.json"),
                "terminal_manifest_sha256": digest(OUT / "terminal_manifest.json"),
                "limits": "Primary partly in-sample and all history exposed; official score of this stage unknown."}
    (OUT / "independent_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
