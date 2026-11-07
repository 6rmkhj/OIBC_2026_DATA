"""Fixed DART station candidate: prepare without fitting, then six serial fits.

The specification is frozen before candidate results. No early stopping,
parameter search, seed selection, or second-period coefficient tuning.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import time
import warnings

os.environ.update(OMP_NUM_THREADS="4", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
                  NUMEXPR_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")

import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow as pa
from threadpoolctl import threadpool_limits

from shift_linux import (ROOT, SOURCE, FOLDS, KEYS, GENERATION_PARAMS, EXPECTED_REFERENCE,
                        sha, read, save, now, assert_keys, check_hashes, metric,
                        alpha_optimum, weather)

OUT = ROOT / "analysis_outputs/renew_20261107/dart_station"
SHIFT = ROOT / "analysis_outputs/renew_20261107/shift_linux"
PARAMETERS = {**GENERATION_PARAMS, "boosting_type": "dart", "n_estimators": 800,
              "drop_rate": .1, "skip_drop": .5, "max_drop": 50,
              "uniform_drop": False, "xgboost_dart_mode": False}
DATA_FILES = ("train.parquet", "evaluation.parquet", "feature_mask.json", "training_transform.parquet",
              "evaluation_transform.parquet", "application_inputs.parquet", "coverage.parquet", "labels.parquet")


def self_check():
    # Pure numerical fixtures, deliberately no estimator construction or fit.
    primary = pd.DataFrame(dict(y=[2., 6., 3.], p_reference=[0., 2., 4.], p_new=[4., 10., 2.],
                                smp=[1., 2., 1.], k=[1., 1., 1.]))
    optimum = alpha_optimum(primary)
    assert optimum == .5
    losses = [np.sum(primary.smp * primary.k * np.abs(primary.y - ((1-a) * primary.p_reference + a * primary.p_new)))
              for a in (0., optimum, 1.)]
    assert losses[1] <= min(losses[0], losses[2])
    active = primary.assign(p=primary.p_reference * .5 + primary.p_new * .5)
    assert metric(active, "p")["W"] == 0.
    inputs = pd.DataFrame(dict(wa_temp=[10., np.nan, 10.], extra_wa_snow=[0., np.nan, 0.],
                               static_capacity=[100., 100., 100.]))
    signed = np.array([[-12., 0., 150.], [9., 0., 180.], [9., 0., 120.]]).mean(axis=0)
    clipped, corrected = weather(inputs, signed)
    np.testing.assert_array_equal(clipped, [2., 0., 100.])
    assert corrected[1] == 0 and np.isfinite(corrected).all()
    assert (corrected >= 0).all() and (corrected <= 100).all()
    return dict(status="PASS", real_model_fits=0,
                fixtures=["known weighted-L1 optimum", "metric zero on exact predictions",
                          "signed mean before clipping", "night zero", "static capacity bounds"])


def prepare():
    assert not OUT.exists(), "Preserve frozen candidate and all previous attempts."
    shift_protocol = read(SHIFT / "protocol.json")
    assert read(SHIFT / "preparation_check.json")["status"] == "PASS"
    assert read(SHIFT / "preparation_check.json")["protocol_sha256"] == sha(SHIFT / "protocol.json")
    # Reuse only verified original scientific inputs, never the shift model weights.
    inputs = {f"data/{fold}/{name}": sha(SOURCE / "data" / fold / name)
              for fold in FOLDS for name in DATA_FILES}
    canonical = {"/".join(Path(name.replace("\\", "/")).parts): value
                 for name, value in shift_protocol["prepared_inputs"].items()}
    assert all(value == canonical[name] for name, value in inputs.items())
    inputs["original_weather_coefficients.json"] = sha(SOURCE / "original_weather_coefficients.json")
    best = ROOT / "submission/renew_candidate_20261105/submission_files.zip"
    assert sha(best) == "ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434"
    fixtures = self_check()
    rows = []
    for fold in FOLDS:
        data = SOURCE / "data" / fold
        mask = read(data / "feature_mask.json")
        train = pd.read_parquet(data / "train.parquet", columns=KEYS + ["cf"])
        future = pd.read_parquet(data / "evaluation.parquet", columns=KEYS)
        transform = pd.read_parquet(data / "training_transform.parquet")
        inverse = pd.read_parquet(data / "evaluation_transform.parquet")
        assert_keys(train, transform)
        assert_keys(future, inverse)
        assert train.ts.max() <= pd.Timestamp(mask["cutoff"]) < future.ts.min()
        assert future.ts.max() <= pd.Timestamp(mask["end"])
        assert not set(mask["selected_columns"]) & {"cf", "y", "smp", "k", "ts", "grp"}
        np.testing.assert_allclose(transform.target_normalized, train.cf / transform.normalizer, rtol=1e-14, atol=1e-12)
        decay = np.exp2(-transform.age_days.to_numpy() / 180)
        np.testing.assert_allclose(transform.sample_weight, transform.normalizer.to_numpy() * decay / decay.mean(), rtol=1e-14, atol=1e-12)
        np.testing.assert_allclose(inverse.inverse_kwh, inverse.normalizer * inverse.capacity_kw, rtol=1e-14, atol=1e-12)
        rows.append(dict(fold=fold, training_rows=len(train), evaluation_rows=len(future),
                         features=len(mask["selected_columns"]), cutoff=mask["cutoff"], end=mask["end"]))
    OUT.mkdir(parents=True)
    (OUT / "sources").mkdir()
    sources = {}
    for path in (Path(__file__), Path(__file__).with_name("shift_linux.py")):
        shutil.copyfile(path, OUT / "sources" / path.name)
        sources[str(path.relative_to(ROOT))] = sha(path)
    library = Path(lgb.basic._LIB._name).resolve()
    protocol = dict(created_utc=now(), arm="dart800_station_decay180", source=str(SOURCE.relative_to(ROOT)),
        inputs_sha256=inputs, source_sha256=sources, source_preparation_protocol_sha256=sha(SHIFT / "protocol.json"),
        parameters=PARAMETERS, generation_parameters=PARAMETERS, seeds=[None, 1, 2],
        folds=list(FOLDS), fit_budget=6, generation_fit_budget=6, alpha_fit_budget=1,
        early_stopping=False, parameter_search=False, prior_dart_found=False,
        features="Original TRAIN-only selected station 904 candidates, 460/790 varying columns, native NaNs",
        target="Unchanged cf/Haurwitz", weights="Unchanged Haurwitz*mean1_decay180, no covariate-shift weights",
        inverse="Unchanged Haurwitz*capacity_kw", inference="signed mean3, static-cap clip, original temperature_then_snow once",
        selection="One primary-only weighted L1 alpha, unchanged recent; strict both W improve and alpha>=.02",
        reference_scores=EXPECTED_REFERENCE, cpu_threads=4, blas_threads=1, arrow_threads=2, parallel_fits=1,
        packages=dict(lightgbm=lgb.__version__, numpy=np.__version__, pandas=pd.__version__, pyarrow=pa.__version__),
        native_library=str(library), native_sha256=sha(library), best_zip=str(best.relative_to(ROOT)), best_zip_sha256=sha(best),
        all_history_exposed=True, primary_alpha_partly_in_sample=True, confirmation_loaded=False, test_loaded=False, exported=False)
    save(OUT / "protocol.json", protocol)
    save(OUT / "preparation_check.json", dict(status="PASS", records=rows, real_model_fits=0,
        protocol_sha256=sha(OUT / "protocol.json"), original_base_weights_verified=True, self_check=fixtures))
    print(json.dumps(dict(status="READY", records=rows, real_model_fits=0)), flush=True)


def run():
    protocol = read(OUT / "protocol.json")
    preparation = read(OUT / "preparation_check.json")
    assert preparation["status"] == "PASS" and preparation["protocol_sha256"] == sha(OUT / "protocol.json")
    assert protocol["parameters"] == PARAMETERS and protocol["fit_budget"] == 6
    assert not protocol["early_stopping"] and not protocol["parameter_search"]
    check_hashes(SOURCE, protocol["inputs_sha256"])
    check_hashes(ROOT, protocol["source_sha256"])
    for name, expected in protocol["source_sha256"].items():
        assert sha(OUT / "sources" / Path(name).name) == expected
    assert sha(ROOT / protocol["best_zip"]) == protocol["best_zip_sha256"]
    assert sha(Path(lgb.basic._LIB._name).resolve()) == protocol["native_sha256"]
    assert not (OUT / "run_started.json").exists(), "No implicit retry or extra fit."
    save(OUT / "run_started.json", dict(started_utc=now(), pid=os.getpid(), protocol_sha256=sha(OUT / "protocol.json")))
    intervals = []
    for fold in FOLDS:
        data = SOURCE / "data" / fold
        destination = OUT / fold
        destination.mkdir()
        names = read(data / "feature_mask.json")["selected_columns"]
        train = pd.read_parquet(data / "train.parquet", columns=names)
        future = pd.read_parquet(data / "evaluation.parquet", columns=names)
        transform = pd.read_parquet(data / "training_transform.parquet")
        inverse = pd.read_parquet(data / "evaluation_transform.parquet")
        for seed in range(3):
            trial = destination / ("generation_seed" + str(seed))
            trial.mkdir()
            params = {**PARAMETERS, "random_state": None if seed == 0 else seed}
            started, tick = now(), time.monotonic()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                estimator = lgb.LGBMRegressor(**params)
                estimator.fit(train, transform.target_normalized.to_numpy(), sample_weight=transform.sample_weight.to_numpy())
            model = estimator.booster_
            assert model.current_iteration() == model.num_trees() == 800 and model.feature_name() == names
            model.save_model(str(trial / "model.txt"))
            raw = model.predict(future, num_threads=4, validate_features=True) * inverse.inverse_kwh.to_numpy()
            assert np.isfinite(raw).all()
            inverse[KEYS].assign(p_raw=raw).to_parquet(trial / "daylight_raw.parquet", index=False)
            replay = lgb.Booster(model_file=str(trial / "model.txt")).predict(future, num_threads=1, validate_features=True) * inverse.inverse_kwh.to_numpy()
            np.testing.assert_array_equal(raw, replay)
            receipt = dict(kind="generation", fold=fold, seed=seed, started_utc=started, finished_utc=now(),
                seconds=time.monotonic() - tick, pid=os.getpid(), fit_count=1, parameters=params, features=names,
                train_rows=len(train), evaluation_rows=len(future), native_tree_count=model.num_trees(),
                early_stopping=False, saved_replay_exact=True, model_sha256=sha(trial / "model.txt"),
                warnings=[dict(category=w.category.__name__, message=str(w.message)) for w in caught])
            save(trial / "receipt.json", receipt)
            intervals.append(receipt)
            print("DART GENERATION COMPLETE", fold, seed, receipt["seconds"], flush=True)
    frames = {}
    for fold in FOLDS:
        data = SOURCE / "data" / fold
        inputs = pd.read_parquet(data / "application_inputs.parquet")
        labels = pd.read_parquet(data / "labels.parquet")
        coverage = pd.read_parquet(data / "coverage.parquet")
        assert_keys(inputs, labels)
        assert_keys(inputs, coverage)
        members = []
        for seed in range(3):
            raw = pd.read_parquet(OUT / fold / ("generation_seed" + str(seed)) / "daylight_raw.parquet")
            full = inputs[KEYS].merge(raw, on=KEYS, how="left", sort=False, validate="one_to_one")
            assert_keys(inputs, full)
            assert full.p_raw.isna().eq(coverage.night).all()
            assert int(full.p_raw.notna().sum()) == len(raw)
            members.append(full.p_raw.fillna(0).to_numpy())
        mean = np.mean(members, axis=0, dtype=np.float64)
        clipped, corrected = weather(inputs, mean)
        frames[fold] = labels.assign(signed_seed_mean=mean, p_component=clipped, p_new=corrected,
            static_capacity=inputs.static_capacity.to_numpy(), night=coverage.night.to_numpy())
        assert frames[fold].loc[frames[fold].night, "p_new"].eq(0).all()
    alpha = alpha_optimum(frames["primary"])
    scores = {}
    for fold, frame in frames.items():
        frame["alpha"] = alpha
        frame["p"] = (1-alpha) * frame.p_reference + alpha * frame.p_new
        frame.to_parquet(OUT / fold / "predictions.parquet", index=False)
        scores[fold] = {name: metric(frame, name) for name in ("p", "p_reference", "p_new")}
        assert abs(scores[fold]["p_reference"]["W_pct"] - EXPECTED_REFERENCE[fold]) < 1e-10
        save(OUT / fold / "metrics.json", scores[fold])
    both = all(scores[f]["p"]["W"] < scores[f]["p_reference"]["W"] for f in FOLDS)
    result = dict(arm="dart800_station_decay180", alpha_primary_only=alpha, scores=scores,
        both_folds_improve=both, eligible=both and alpha >= .02, real_model_fit_count=6,
        real_generation_fit_count=6, real_alpha_fit_count=1, early_stopping=False,
        all_history_exposed=True, primary_alpha_partly_in_sample=True,
        confirmation_loaded=False, test_loaded=False, exported=False)
    assert len(intervals) == 6 and all(a["finished_utc"] <= b["started_utc"] for a,b in zip(intervals, intervals[1:]))
    save(OUT / "fit_intervals.json", intervals)
    save(OUT / "results.json", result)
    check_hashes(SOURCE, protocol["inputs_sha256"])
    check_hashes(ROOT, protocol["source_sha256"])
    assert sha(ROOT / protocol["best_zip"]) == protocol["best_zip_sha256"]
    save(OUT / "completed.json", dict(finished_utc=now(), pid=os.getpid(), fit_count=6,
        original_inputs_unchanged=True, best_zip_unchanged=True))
    save(OUT / "terminal_manifest.json", {str(p.relative_to(OUT)): sha(p) for p in sorted(OUT.rglob("*"))
        if p.is_file() and p.name not in {"controller.lock", "run.log", "terminal_manifest.json"}})
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser()
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--prepare", action="store_true")
    choice.add_argument("--run", action="store_true")
    args = parser.parse_args()
    pa.set_cpu_count(2)
    pa.set_io_thread_count(2)
    with threadpool_limits(limits=1, user_api="blas"):
        if args.prepare:
            prepare()
        else:
            with (OUT / "controller.lock").open("a+b") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                run()


if __name__ == "__main__":
    main()
