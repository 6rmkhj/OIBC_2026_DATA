# /// script
# requires-python = ">=3.12"
# dependencies = ["numpy", "pyarrow", "lightgbm"]
# ///
# How to run: python submission/score_push_verify_yield_transform.py AFTER wave completion.
"""Recompute site quantiles and group transforms from the original bounded targets."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from math import floor, fsum, isclose

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from score_push_verify_yield_data import OUT, digest


def physical(cosz: np.ndarray) -> np.ndarray:
    positive = np.maximum(cosz, 0.)
    exponent = np.divide(-.059, positive, out=np.zeros_like(positive, dtype=float), where=positive > 0)
    return 1.098 * positive * np.exp(exponent)


def quantile90(values: list[float]) -> float:
    ordered = sorted(values)
    index = .9 * (len(ordered) - 1)
    lower = floor(index)
    fraction = index - lower
    return ordered[lower] + fraction * (ordered[min(lower + 1, len(ordered) - 1)] - ordered[lower])


def main() -> None:
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    prefit = json.loads((OUT / "independent_data_check.json").read_text())
    assert prefit["status"] == "PASS" and prefit["prepared_manifest_sha256"] == digest(OUT / "prepared_manifest.json")
    for manifest in ("prepared_manifest.json", "transform_manifest.json"):
        for path, expected in json.loads((OUT / manifest).read_text()).items():
            assert digest(OUT / path) == expected, path
    receipt = json.loads((OUT / "coefficient_fit_receipt.json").read_text())
    assert receipt["training_only"] and receipt["shared_all_seeds"]
    assert len(receipt["records"]) == 2 and not any(r["loaded_existing_coefficients"] for r in receipt["records"])
    sites = pq.read_table(OUT / "data/sites.parquet").to_pylist()
    assignment = {r["site_id"]: r["grp"] for r in sites}
    checked = []
    for fold in ("primary", "recent"):
        directory = OUT / "data" / fold
        source = pq.read_table(directory / "site_train.parquet")
        values = {n: source[n].to_numpy() for n in ("cf", "cosz", "wa_cloud", "wb_cloud")}
        valid = np.ones(len(source), dtype=bool)
        for column in values.values():
            valid &= np.isfinite(column)
        valid &= (values["cf"] >= 0) & (values["cosz"] > .5)
        valid &= (values["wa_cloud"] >= 0) & (values["wa_cloud"] < 20)
        valid &= (values["wb_cloud"] >= 0) & (values["wb_cloud"] < 20)
        ratios = values["cf"][valid] / physical(values["cosz"][valid])
        global_q90 = quantile90(ratios.tolist())
        assert global_q90 > 0 and np.isfinite(ratios).all()
        ids, times = source["site_id"].to_pylist(), source["ts"].to_pylist()
        groups, dates = defaultdict(list), defaultdict(set)
        for index, ratio in zip(np.flatnonzero(valid), ratios, strict=True):
            groups[ids[index]].append(float(ratio))
            dates[ids[index]].add((times[index] - timedelta(hours=1)).date())
        observed = Counter(ids)
        stored = json.loads((OUT / "coefficients" / f"{fold}.json").read_text())
        assert stored["source_sha256"] == digest(directory / "site_train.parquet") and stored["training_only"]
        assert stored["quantile_method"] == "linear" and stored["clear_rows"] == int(valid.sum())
        assert isclose(stored["global_q90"], global_q90, rel_tol=1e-12, abs_tol=1e-12)
        cutoff = datetime.fromisoformat(stored["cutoff"])
        assert max(times) <= cutoff and datetime.fromisoformat(stored["max_target_ts"]) == max(times)
        assert len(stored["sites"]) == 253 and {r["site_id"] for r in stored["sites"]} == set(assignment)
        gains = {}
        for record in stored["sites"]:
            site = record["site_id"]
            count, days = len(groups[site]), len(dates[site])
            q90 = quantile90(groups[site]) if count else None
            relative = q90 / global_q90 if q90 is not None else None
            shrink = count / (count + 200)
            supported = count >= 100 and days >= 20 and q90 is not None and q90 > 0
            gain = max(.5, min(1.5, 1 + shrink * (relative - 1))) if supported else 1.
            reason = "supported" if supported else "no_clear_rows" if count == 0 else "insufficient_rows" if count < 100 else "insufficient_days" if days < 20 else "nonpositive_or_nonfinite_q90"
            assert record["observed_rows"] == observed[site] and record["clear_rows"] == count and record["clear_days"] == days
            assert record["fallback_reason"] == reason
            for name, expected in (("raw_q90", q90), ("raw_relative", relative), ("shrink", shrink), ("gain", gain)):
                assert record[name] is None if expected is None else isclose(record[name], expected, rel_tol=1e-12, abs_tol=1e-12), (site, name)
            gains[site] = gain
        for split in ("train", "evaluation"):
            panel = pq.read_table(directory / f"site_{split}.parquet", columns=["ts", "site_id", "capacity_kw"]).to_pylist()
            buckets = defaultdict(list)
            for row in panel:
                buckets[(row["ts"], assignment[row["site_id"]])].append((row["capacity_kw"], row["capacity_kw"] * gains[row["site_id"]]))
            aggregates = {key: (fsum(v[0] for v in part), fsum(v[1] for v in part)) for key, part in buckets.items()}
            saved = pq.read_table(directory / f"{split}_group_gain.parquet").to_pylist()
            assert len(saved) == len(aggregates) and {(r["ts"], r["grp"]) for r in saved} == set(aggregates)
            for row in saved:
                capacity, adjusted = aggregates[(row["ts"], row["grp"])]
                for name, expected in (("capacity_kw", capacity), ("yield_capacity", adjusted), ("group_gain", adjusted / capacity)):
                    assert isclose(row[name], expected, rel_tol=1e-12, abs_tol=1e-8)
            frame = pq.read_table(directory / f"{split}.parquet")
            transform = pq.read_table(directory / ("training_transform.parquet" if split == "train" else "evaluation_transform.parquet"))
            keys = [(r["ts"], r["grp"]) for r in frame.select(["ts", "grp"]).to_pylist()]
            assert transform.select(["ts", "grp"]).to_pylist() == frame.select(["ts", "grp"]).to_pylist()
            gain_array = np.array([aggregates[key][1] / aggregates[key][0] for key in keys])
            curve = physical(frame["cosz"].to_numpy())
            normalizer = np.maximum(.05, curve * gain_array)
            for name, expected in (("group_gain", gain_array), ("physical_haurwitz", curve), ("new_normalizer", normalizer)):
                np.testing.assert_allclose(transform[name].to_numpy(), expected, rtol=1e-12, atol=1e-12, err_msg=name)
            if split == "train":
                age = np.array([(cutoff - key[0]).total_seconds() / 86400 for key in keys])
                assert (age >= 0).all()
                decay = np.exp2(-age / 180)
                decay /= fsum(decay) / len(decay)
                for name, expected in (("age_days", age), ("decay", decay), ("target", frame["cf"].to_numpy() / normalizer), ("sample_weight", normalizer * decay)):
                    np.testing.assert_allclose(transform[name].to_numpy(), expected, rtol=1e-12, atol=1e-12, err_msg=name)
        checked.append({"fold": fold, "clear_rows": int(valid.sum()), "global_q90": global_q90,
                        "supported_sites": sum(r["fallback_reason"] == "supported" for r in stored["sites"]),
                        "gain_min": min(gains.values()), "gain_max": max(gains.values())})
    evidence = {"status": "PASS", "records": checked, "transform_manifest_sha256": digest(OUT / "transform_manifest.json"),
                "scope": "Independent linear-interpolated order statistics, every site support/fallback/gain, every capacity-weighted group gain, physical curve/floor, targets and decay weights. No new model fit."}
    (OUT / "independent_transform_check.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
