# /// script
# requires-python = ">=3.12"
# dependencies = ["pyarrow"]
# ///
# Run: python submission/score_push_verify_refinement.py
"""Independently verify convex blends against frozen labels and member files."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from math import fsum, isclose, isfinite
from typing import Final

import pyarrow as pa
import pyarrow.parquet as pq

from score_push_verify import OLD, OUT, ROOT, digest

WAVE: Final = OUT / "refinement_wave"


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    end = datetime.fromisoformat("2025-03-01T00:00:00+09:00")
    labels = {
        "primary": pq.read_table(OLD / "cache/selection_labels.parquet").to_pylist(),
        "recent": pq.read_table(OLD / "final/outer_predictions.parquet",
            columns=["ts", "grp", "y", "smp", "k"], filters=[("ts", "<=", end)]).to_pylist(),
    }
    references = {fold: {(r["ts"], r["grp"]): r for r in rows} for fold, rows in labels.items()}
    assert len(references["primary"]) == len(labels["primary"]) == 17568
    assert len(references["recent"]) == len(labels["recent"]) == 13104
    manifest = json.loads((WAVE / "manifest.json").read_text())
    hash_count = 0
    final_manifest = json.loads((WAVE / "final_manifest.json").read_text())
    hash_sets = [(manifest["input_sha256"], ROOT),
                 (final_manifest["artifact_sha256"], WAVE),
                 (final_manifest["current_source_sha256"], ROOT)]
    for hashes, parent in hash_sets:
        for name, expected in hashes.items():
            assert digest(parent / name) == expected, name
            hash_count += 1
    results = json.loads((WAVE / final_manifest["selection_results"]).read_text())
    chosen = json.loads((WAVE / "chosen_recipe.json").read_text())
    assert chosen["weights_fit_on"] == "primary only"
    assert chosen["id"] == results["selected_recipe"]["id"]
    checked = []
    for record in results["records"]:
        weights = record["weights_primary_only"]
        assert len(weights) == len(record["members"])
        assert all(isfinite(w) and w >= 0 for w in weights) and isclose(fsum(weights), 1., abs_tol=1e-10)
        for fold, truth in references.items():
            path = WAVE / fold / "recipes" / record["id"] / "predictions.parquet"
            rows = pq.read_table(path).to_pylist()
            assert len(rows) == len(truth) and {(r["ts"], r["grp"]) for r in rows} == set(truth)
            for row in rows:
                oracle = truth[row["ts"], row["grp"]]
                assert all(row[k] == oracle[k] for k in ("y", "smp", "k"))
                predicted = fsum(w * row[name] for w, name in zip(weights, record["members"], strict=True))
                assert isfinite(row["p"]) and row["p"] >= 0
                assert isclose(predicted, row["p"], rel_tol=1e-12, abs_tol=1e-8)
            penalty = fsum(r["smp"] * r["k"] * abs(r["p"] - r["y"]) for r in rows)
            denominator = fsum(r["smp"] * r["k"] * r["y"] for r in rows)
            score = 100 * penalty / denominator
            assert isclose(score, record["scores"][fold], rel_tol=1e-12)
            if record["id"] == chosen["id"]:
                for name in record["members"]:
                    artifact = chosen["member_artifacts_relative_to_score_push_output"][name]
                    members = pq.read_table(OUT / artifact["path_pattern"].format(fold=fold)).to_pylist()
                    values = {(r["ts"], r["grp"]): r[artifact["column"]] for r in members}
                    assert len(members) == len(values) == len(truth) and set(values) == set(truth)
                    assert all(r[name] == values[r["ts"], r["grp"]] for r in rows), name
            checked.append({"id": record["id"], "fold": fold, "rows": len(rows), "W": penalty, "W_pct": score})
    result = {"status": "PASS", "method": "Raw member Parquet, independent frozen labels, math.fsum",
        "confirmation_labels_loaded": False, "hashes_verified": hash_count,
        "chosen": chosen["id"], "records": checked}
    output = OUT / "independent_refinement_check.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "records": len(checked), "hashes": hash_count,
                      "chosen": chosen["id"], "output": str(output)}, indent=2))


def closing() -> None:
    """Check the final no-fit decision from unchanged parent member files."""
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    wave = OUT / "closing_wave"
    result = json.loads((wave / "selected_recipe.json").read_text())
    assert result["search_closed"] and result["no_later_tuning_from_confirmation"] and result["model_fits"] == 0
    for path, expected in json.loads((wave / "input_manifest.json").read_text()).items():
        assert digest(ROOT / path) == expected, path
    final_manifest = json.loads((wave / "final_manifest.json").read_text())
    for field, parent in (("artifact_sha256", wave), ("current_source_sha256", ROOT)):
        for path, expected in final_manifest[field].items():
            assert digest(parent / path) == expected, path
    candidate = result["candidate_weights_primary_only"]
    adopted = all(result["candidate_scores"][f] < result["reference_scores"][f] for f in ("primary", "recent"))
    assert adopted == result["adopted_closing_blend"]
    assert result["selected_weights"] == (candidate if adopted else [1., 0., 0.])
    cutoff = datetime.fromisoformat("2025-03-01T00:00:00+09:00")
    scores = []
    for fold, count in (("primary", 17568), ("recent", 13104)):
        members = []
        for name in result["member_order"]:
            relative, column = result["source_members_relative_to_profile_wave"][name]
            source = OUT / "profile_wave" / fold / relative
            rows = pq.read_table(source, filters=[("ts", "<=", cutoff)]).to_pylist()
            assert pq.ParquetFile(source).metadata.num_rows == len(rows) == count
            members.append({(r["ts"], r["grp"]): {**r, "value": r[column]} for r in rows})
        assert all(set(member) == set(members[0]) for member in members)
        for kind, weights in (("candidate", candidate), ("selected", result["selected_weights"])):
            assert all(isfinite(w) and w >= 0 for w in weights) and isclose(fsum(weights), 1., abs_tol=1e-10)
            path = wave / fold / kind / "predictions.parquet"
            rows = pq.read_table(path, filters=[("ts", "<=", cutoff)]).to_pylist()
            assert pq.ParquetFile(path).metadata.num_rows == len(rows) == count
            assert {(r["ts"], r["grp"]) for r in rows} == set(members[0])
            for row in rows:
                key = row["ts"], row["grp"]
                assert all(row[k] == m[key][k] for m in members for k in ("y", "smp", "k"))
                expected = fsum(w * m[key]["value"] for w, m in zip(weights, members, strict=True))
                assert isclose(row["p"], expected, rel_tol=1e-12, abs_tol=1e-8)
            penalty = fsum(r["smp"] * r["k"] * abs(r["p"] - r["y"]) for r in rows)
            denominator = fsum(r["smp"] * r["k"] * r["y"] for r in rows)
            score = 100 * penalty / denominator
            assert isclose(score, result[f"{kind}_scores"][fold], rel_tol=1e-12)
            scores.append({"fold": fold, "kind": kind, "rows": count, "W": penalty, "W_pct": score})
    output = OUT / "independent_closing_check.json"
    output.write_text(json.dumps({"status": "PASS", "model_fits": 0, "adopted": adopted,
        "confirmation_labels_loaded": False, "records": scores}, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "records": len(scores), "adopted": adopted, "output": str(output)}))


if __name__ == "__main__":
    if "--closing" in sys.argv:
        closing()
    else:
        main()
