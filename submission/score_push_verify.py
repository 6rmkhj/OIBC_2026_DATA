# /// script
# requires-python = ">=3.12"
# dependencies = ["pyarrow"]
# ///
# Run: python submission/score_push_verify.py
"""Check primary experiment scores without importing the model or evaluator."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from math import fsum, isclose, isfinite
from pathlib import Path
from typing import Final

import pyarrow as pa
import pyarrow.parquet as pq

ROOT: Final = Path(__file__).resolve().parent.parent
OUT: Final = ROOT / "analysis_outputs/score_push_20261104"
OLD: Final = ROOT / "analysis_outputs/autoresearch_20261103"


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    manifest = json.loads((OUT / "cache/manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["inputs_sha256"].items():
        assert digest(ROOT / name) == expected, name
    for name, expected in manifest["cache_sha256"].items():
        assert digest(OUT / "cache" / name) == expected, name
    for name, expected in manifest["source_sha256"].items():
        assert digest(OUT / "sources" / name) == expected, name
    label_path = OLD / "cache/selection_labels.parquet"
    assert digest(label_path) == manifest["evaluation_label_sha256"]
    assert not {"energy", "cf", "y"} & set(pq.ParquetFile(OUT / "cache/selection.parquet").schema.names)
    labels = pq.read_table(label_path).to_pylist()
    keys = {(row["ts"], row["grp"]) for row in labels}
    assert len(labels) == len(keys) == 17568
    denominator = fsum(row["smp"] * row["k"] * row["y"] for row in labels)
    journal = [json.loads(line) for line in (OUT / "journal.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len({record["id"] for record in journal}) == len(journal)
    scores = []
    best = float("inf")
    for record in journal:
        trial = OUT / "trials" / record["id"]
        config = json.loads((trial / "config.json").read_text(encoding="utf-8"))
        features = json.loads((trial / "features.json").read_text(encoding="utf-8"))
        assert not {"energy", "cf", "y"} & set(features)
        assert digest(trial / "predictions.parquet") == record["predictions_sha256"]
        predictions = pq.read_table(trial / "predictions.parquet").to_pylist()
        direct = {(row["ts"], row["grp"]): row["p_dir"] for row in predictions}
        assert len(predictions) == len(direct) == len(keys) and set(direct) == keys
        assert all(isfinite(value) and value >= 0 for value in direct.values())
        alpha = config["direct_weight"]
        assert 0 <= alpha <= 1 and alpha == record["direct_weight"]
        penalty = fsum(row["smp"] * row["k"] * abs(
            (1 - alpha) * row["p_bu"] + alpha * direct[row["ts"], row["grp"]] - row["y"]
        ) for row in labels)
        percentage = 100 * penalty / denominator
        assert isclose(penalty, record["W"], rel_tol=1e-12, abs_tol=.001), record["id"]
        assert isclose(percentage, record["W_pct"], rel_tol=1e-12), record["id"]
        assert record["decision"] == ("keep" if percentage < best else "discard")
        best = min(best, percentage)
        if record["model_fits"]:
            runtime = json.loads((trial / "runtime.json").read_text(encoding="utf-8"))
            assert runtime["parallel_fits"] == 1 and runtime["model_n_jobs"] == 2
            assert runtime["priority_class"] == 16384
            assert runtime["environment"] == {"OMP_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "1",
                                              "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1"}
        else:
            assert digest(trial / "config.json") == record["config_sha256"]
            assert digest(trial / "features.json") == record["features_sha256"]
        scores.append({"id": record["id"], "W": penalty, "W_pct": percentage, "model_fits": record["model_fits"]})
    assert isclose(scores[0]["W_pct"], 12.695950143757269, abs_tol=1e-10)
    assert digest(OUT / "trials/baseline_exact/predictions.parquet") == digest(OLD / "trials/w5_lgb_calibrated/predictions.parquet")
    ranking = json.loads((OUT / "ranking.json").read_text(encoding="utf-8"))
    assert isclose(best, ranking["calibrated"]["W_pct"], rel_tol=1e-12)
    print(json.dumps({"status": "PASS", "method": "PyArrow and math.fsum, no model/evaluator imports",
        "records": len(scores), "rows_per_record": len(labels), "source_input_cache_hashes": "PASS",
        "exact_incumbent_predictions": "PASS", "resource_receipts": "PASS", "scores": scores}, indent=2))


def development(include_learners: bool = False, include_profiles: bool = False) -> None:
    """Recompute recent and site-wave scores using frozen independent labels."""
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    primary_end = datetime.fromisoformat("2024-06-01T00:00:00+09:00")
    recent_end = datetime.fromisoformat("2025-03-01T00:00:00+09:00")
    primary = pq.read_table(OLD / "cache/selection_labels.parquet").to_pylist()
    recent = pq.read_table(OLD / "final/outer_predictions.parquet",
        columns=["ts", "grp", "y", "smp", "k"],
        filters=[("ts", ">", primary_end), ("ts", "<=", recent_end)]).to_pylist()
    references = {"primary": {(r["ts"], r["grp"]): r for r in primary},
                  "recent": {(r["ts"], r["grp"]): r for r in recent}}
    assert len(primary) == len(references["primary"]) == 17568
    assert len(recent) == len(references["recent"]) == 13104
    hash_count = 0
    waves = [("recent", "inputs_sha256", "outputs_sha256"),
             ("site_wave", "input_sha256", "output_sha256")]
    if include_learners:
        waves.append(("learner_wave", "input_sha256", "output_sha256"))
    if include_profiles:
        waves.append(("profile_wave", "input_sha256", "output_sha256"))
    for wave, input_key, output_key in waves:
        base = OUT / wave
        manifest = json.loads((base / "manifest.json").read_text())
        for key, parent in [(input_key, ROOT), (output_key, base)]:
            for path, expected in manifest[key].items():
                assert digest(parent / path) == expected, path
                hash_count += 1
        for source_dir in sorted(base.glob("*sources")):
            source_hashes = json.loads((source_dir / "hashes.json").read_text())
            for name, expected in source_hashes.items():
                assert digest(source_dir / name) == expected, name
                hash_count += 1
    calibration = json.loads((OUT / "site_wave/calibration_summary.json").read_text())
    assert calibration["recent_alpha_fits"] == 0
    for path, expected in calibration["outputs_sha256"].items():
        assert digest(OUT / "site_wave" / path) == expected, path
        hash_count += 1
    scores = []
    alpha_by_pair = {}
    incumbent_alpha = json.loads((OLD / "final/config.json").read_text())["direct_weight"]
    profile_reference = {}
    if include_profiles:
        chosen = json.loads((OUT / "refinement_wave/chosen_recipe.json").read_text())["id"]
        for fold in ("primary", "recent"):
            members = pq.read_table(OUT / "refinement_wave" / fold / "recipes" / chosen / "predictions.parquet").to_pylist()
            profile_reference[fold] = {(r["ts"], r["grp"]): r["p"] for r in members}
    paths = [path for wave, _, _ in waves for path in sorted((OUT / wave).rglob("score.json"))]
    for score_path in paths:
        part = score_path.relative_to(OUT)
        site_wave = part.parts[0] == "site_wave"
        learner_wave = part.parts[0] in {"learner_wave", "profile_wave"}
        fold = part.parts[1] if site_wave or learner_wave else "recent"
        reference = references[fold]
        rows = pq.read_table(score_path.with_name("predictions.parquet")).to_pylist()
        assert len(rows) == len(reference)
        assert {(r["ts"], r["grp"]) for r in rows} == set(reference)
        for row in rows:
            truth = reference[row["ts"], row["grp"]]
            assert all(row[name] == truth[name] for name in ("y", "smp", "k")), str(part)
            assert row["k"] == (3 if 11 <= row["ts"].hour <= 15 else 1)
            if part.parts[0] == "profile_wave":
                assert row["p_reference"] == profile_reference[fold][row["ts"], row["grp"]]
            assert isfinite(row["p"]) and row["p"] >= 0
            alpha = row.get("alpha", 1. if learner_wave else incumbent_alpha)
            assert 0 <= alpha <= 1
            if learner_wave:
                base_name = "p_reference" if score_path.parent.name in {"richer_reference", "complement"} else "p_bu_old"
                reconstructed = alpha * row["p_new"] + (1 - alpha) * row[base_name]
            else:
                bottom = row["p_bu_new"] if site_wave else row["p_bu"]
                reconstructed = (1 - alpha) * bottom + alpha * row.get("p_dir", 0.)
            assert isclose(reconstructed, row["p"], rel_tol=1e-12, abs_tol=1e-8), str(part)
        alphas = {r.get("alpha", 1. if learner_wave else incumbent_alpha) for r in rows}
        assert len(alphas) == 1
        if site_wave or learner_wave:
            pair = str(Path(part.parts[0], *part.parts[2:]))
            if fold == "primary":
                alpha_by_pair[pair] = alphas
            else:
                assert alphas == alpha_by_pair[pair], pair
        penalty = fsum(r["smp"] * r["k"] * abs(r["p"] - r["y"]) for r in rows)
        denominator = fsum(r["smp"] * r["k"] * r["y"] for r in rows)
        expected = json.loads(score_path.read_text())
        assert isclose(penalty, expected["W"], rel_tol=1e-12, abs_tol=.001), str(part)
        assert isclose(100 * penalty / denominator, expected["W_pct"], rel_tol=1e-12), str(part)
        scores.append({"path": str(part), "rows": len(rows), "W": penalty,
                       "W_pct": 100 * penalty / denominator})
    result = {"status": "PASS", "method": "PyArrow and math.fsum; no scorer/model imports",
              "confirmation_labels_loaded": False, "verified_hashes": hash_count,
              "primary_alphas_transferred_unchanged": True, "records": len(scores), "scores": scores}
    output = OUT / ("independent_learner_check.json" if include_learners else "independent_development_check.json")
    if include_profiles:
        output = OUT / "independent_profile_check.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "records": len(scores), "verified_hashes": hash_count,
                      "output": str(output)}, indent=2))


if __name__ == "__main__":
    if "--development" in sys.argv:
        development()
    elif "--learners" in sys.argv:
        development(include_learners=True)
    elif "--profiles" in sys.argv:
        development(include_learners=True, include_profiles=True)
    else:
        main()
