"""Frozen train-only spatial PCA experiment, preserving every historical artifact.

Use --prepare for two unsupervised TRAIN-only PCA fits (no generation fits),
then --run for six serial LightGBM fits and one primary-only blend coefficient.
"""
from __future__ import annotations

import argparse
import fcntl
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
import sklearn
from sklearn.decomposition import PCA
from threadpoolctl import threadpool_limits

from shift_linux import (ROOT, SOURCE as SHIFT_SOURCE, POISSON, FOLDS, KEYS, GENERATION_PARAMS, EXPECTED_REFERENCE,
                        sha, read, save, now, assert_keys, check_hashes, metric,
                        alpha_optimum, weather, historical_hashes)

OUT = ROOT / "analysis_outputs/renew_20261107/pca_station"
COMPONENT_COUNT = 16
COMPONENTS = [f"station_pc{i:02d}" for i in range(1, COMPONENT_COUNT + 1)]
COPIES = ("training_transform.parquet", "evaluation_transform.parquet",
          "application_inputs.parquet", "coverage.parquet", "labels.parquet")


def station_columns(names):
    return [n for n in names if n.startswith(("wa_station_", "wb_station_"))]


def fit_pca(train, columns, n_components=COMPONENT_COUNT):
    """Fit accepts TRAIN features only; future covariates and targets are absent."""
    assert len(columns) == len(set(columns)) and set(columns) <= set(train)
    assert columns == station_columns(columns)
    selected = [n for n in columns if train[n].nunique(dropna=True) > 1]
    values = np.asarray(train[selected].to_numpy(dtype=np.float64), order="C")
    assert not np.isinf(values).any() and min(values.shape) >= n_components
    medians = np.nanmedian(values, axis=0)
    imputed = np.where(np.isnan(values), medians[None, :], values)
    mean = imputed.mean(axis=0)
    scale = imputed.std(axis=0, ddof=0)
    assert np.isfinite(medians).all() and np.isfinite(mean).all() and (scale > 0).all()
    standardized = (imputed - mean) / scale
    estimator = PCA(n_components=n_components, svd_solver="full", whiten=False)
    estimator.fit(standardized)
    fitted = dict(medians=medians, mean=mean, scale=scale, center=estimator.mean_,
                  components=estimator.components_, eigenvalues=estimator.explained_variance_,
                  variance_ratio=estimator.explained_variance_ratio_, singular_values=estimator.singular_values_)
    transformed = transform_pca(train, selected, fitted)
    np.testing.assert_allclose(transformed, estimator.transform(standardized), rtol=1e-12, atol=1e-12)
    np.testing.assert_allclose(fitted["components"] @ fitted["components"].T,
                               np.eye(n_components), rtol=1e-12, atol=1e-12)
    return selected, fitted, transformed


def transform_pca(frame, columns, fitted):
    values = np.asarray(frame[columns].to_numpy(dtype=np.float64), order="C")
    assert not np.isinf(values).any()
    imputed = np.where(np.isnan(values), fitted["medians"][None, :], values)
    standardized = (imputed - fitted["mean"]) / fitted["scale"]
    projected = (standardized - fitted["center"]) @ fitted["components"].T
    assert np.isfinite(projected).all()
    return projected


def self_check():
    rng = np.random.default_rng(20261107)
    names = [f"wa_station_WA{i:03d}_wa_cloud" for i in range(18)]
    train = pd.DataFrame(rng.normal(size=(40, 18)), columns=names)
    train.iloc[0, 0] = np.nan
    train[names[-1]] = np.nan
    train[names[-2]] = 0.
    selected, fitted, original = fit_pca(train, names)
    assert names[-1] not in selected and names[-2] not in selected
    snapshot = {key: value.copy() for key, value in fitted.items()}
    future = train.iloc[:3].copy()
    future[names[-1]] = 1e12
    future[names[-2]] = -1e12
    future[selected] += 1e6
    transform_pca(future.assign(y=np.nan, cf=1e30), selected, fitted)
    for key in fitted:
        np.testing.assert_array_equal(fitted[key], snapshot[key])
    np.testing.assert_array_equal(transform_pca(train, selected, fitted), original)
    # Refitting on unchanged TRAIN after arbitrary future changes is identical.
    selected_again, fitted_again, values_again = fit_pca(train.assign(y=1e30), names)
    assert selected_again == selected
    for key in fitted:
        np.testing.assert_array_equal(fitted[key], fitted_again[key])
    np.testing.assert_array_equal(values_again, original)
    # A deliberate future-inclusive scaler has to fail the invariance fixture.
    leaked_mean = pd.concat([train[selected], future[selected]]).mean().to_numpy()
    assert not np.allclose(leaked_mean, fitted["mean"])
    return dict(status="PASS", tests=["TRAIN-only constant/all-missing exclusion", "TRAIN median NaN fill",
        "future/target perturbation leaves every fitted array unchanged", "TRAIN replay exact",
        "orthonormal components", "future-inclusive scaler mutation rejected"])


def prepare():
    assert not OUT.exists(), "Preserve existing PCA experiment; use its recorded checkpoint"
    source_manifest = read(POISSON / "prepared_manifest.json")
    inputs = {f"data/{fold}/{name}": sha(POISSON / "data" / fold / name)
              for fold in FOLDS for name in (*COPIES, "train.parquet", "evaluation.parquet", "feature_mask.json")}
    normalized_manifest = {k.replace("\\", "/"): v for k, v in source_manifest.items()}
    lineage = historical_hashes(POISSON, {k: normalized_manifest[k] for k in inputs})
    independent = OUT.parent / "independent_input_check.json"
    assert read(independent)["status"] == "PASS"
    external = {str(p.relative_to(ROOT)): sha(p) for p in
                (SHIFT_SOURCE / "original_weather_coefficients.json", independent)}
    best = ROOT / "submission/renew_candidate_20261105/submission_files.zip"
    assert sha(best) == "ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434"
    OUT.mkdir(parents=True)
    (OUT / "sources").mkdir()
    sources = {}
    for path in (Path(__file__), Path(__file__).with_name("shift_linux.py")):
        shutil.copyfile(path, OUT / "sources" / path.name)
        sources[str(path.relative_to(ROOT))] = sha(path)
    protocol = dict(created_utc=now(), arm="rich100_station_pca16_decay180", source="analysis_outputs/renew_20261106/poisson_wave",
        inputs_sha256=inputs, historical_lineage=lineage, source_sha256=sources,
        external_inputs_sha256=external, generation_parameters=GENERATION_PARAMS,
        pca=dict(n_components=16, whiten=False, svd_solver="full", fit_scope="TRAIN-only, unweighted",
            imputation="TRAIN median", scaling="TRAIN mean and std(ddof=0)",
            columns="wa_station_/wb_station_ only, >1 TRAIN non-null unique value", future_clipping=False),
        features="TRAIN-varying rich100 plus 16 fixed principal components", seeds=[None, 1, 2],
        target="unchanged cf/Haurwitz", weights="unchanged Haurwitz*mean1_decay180", inverse="unchanged Haurwitz*capacity_kw",
        calibration="original temperature_then_snow only, once after signed 3-seed mean and static cap",
        selection="one primary-only L1 optimal alpha, transferred unchanged to recent; strict both W improve and alpha >= .02",
        best_zip=str(best.relative_to(ROOT)), best_zip_sha256=sha(best), cpu_threads=4, blas_threads=1,
        sklearn_version=sklearn.__version__, numpy_version=np.__version__, lightgbm_version=lgb.__version__,
        lightgbm_library=str(Path(lgb.basic._LIB._name).resolve()),
        lightgbm_library_sha256=sha(Path(lgb.basic._LIB._name).resolve()),
        generation_fit_budget=6, pca_fit_budget=2, all_history_exposed=True, confirmation_loaded=False, test_loaded=False)
    save(OUT / "protocol.json", protocol)
    save(OUT / "self_check.json", self_check())
    receipts = []
    for fold in FOLDS:
        tick = time.monotonic()
        source = POISSON / "data" / fold
        destination = OUT / "data" / fold
        destination.mkdir(parents=True)
        mask = read(source / "feature_mask.json")
        candidates = mask["candidate_columns"]
        spatial = station_columns(candidates)
        rich = [n for n in candidates if n not in spatial]
        assert len(rich) == 100 and len(spatial) == 804
        train = pd.read_parquet(source / "train.parquet")
        future = pd.read_parquet(source / "evaluation.parquet")
        assert "cf" in train and "cf" not in future
        assert train.ts.max() <= pd.Timestamp(mask["cutoff"]) < future.ts.min()
        selected, fitted, train_pc = fit_pca(train, spatial)
        future_pc = transform_pca(future, selected, fitted)
        np.savez(destination / "pca_arrays.npz", **fitted)
        with np.load(destination / "pca_arrays.npz", allow_pickle=False) as archive:
            restored = {key: archive[key] for key in archive.files}
        np.testing.assert_array_equal(transform_pca(train, selected, restored), train_pc)
        np.testing.assert_array_equal(transform_pca(future, selected, restored), future_pc)
        save(destination / "pca_features.json", dict(candidate_columns=spatial, selected_columns=selected,
            components=COMPONENTS, training_rows=len(train), fit_scope="TRAIN only", future_rows_used_for_fit=0,
            cumulative_explained_variance=float(fitted["variance_ratio"].sum())))
        train_out = train[[*KEYS, "cf", *rich]].copy()
        future_out = future[[*KEYS, *rich]].copy()
        for i, name in enumerate(COMPONENTS):
            train_out[name] = train_pc[:, i]
            future_out[name] = future_pc[:, i]
        names = [n for n in rich if train[n].nunique(dropna=True) > 1] + COMPONENTS
        train_out.to_parquet(destination / "train.parquet", index=False)
        future_out.to_parquet(destination / "evaluation.parquet", index=False)
        save(destination / "feature_mask.json", {**mask, "candidate_columns": rich + COMPONENTS,
            "selected_columns": names, "dropped_columns": [n for n in rich if n not in names],
            "selected_dtypes": {n: str(train_out[n].dtype) for n in names}, "fitted_on": "TRAIN only"})
        for name in COPIES:
            shutil.copyfile(source / name, destination / name)
            assert sha(destination / name) == sha(source / name)
        assert_keys(train_out, pd.read_parquet(destination / "training_transform.parquet"))
        assert_keys(future_out, pd.read_parquet(destination / "evaluation_transform.parquet"))
        receipts.append(dict(fold=fold, train_rows=len(train), evaluation_rows=len(future),
            spatial_dimensions=len(selected), model_features=len(names), pca_fit_count=1,
            explained_variance=float(fitted["variance_ratio"].sum()), generation_fits=0,
            persisted_transform_replay_exact=True, seconds=time.monotonic() - tick))
        print("PCA PREPARED", fold, receipts[-1], flush=True)
    check_hashes(POISSON, inputs)
    save(OUT / "preparation.json", dict(status="PASS", receipts=receipts, generation_fit_count=0, pca_fit_count=2))
    manifest = {str(p.relative_to(OUT)): sha(p) for p in sorted((OUT / "data").rglob("*")) if p.is_file()}
    save(OUT / "prepared_manifest.json", manifest)


def run():
    protocol = read(OUT / "protocol.json")
    assert not (OUT / "results.json").exists(), "No repeated experiment"
    check_hashes(ROOT, protocol["source_sha256"])
    check_hashes(ROOT, protocol["external_inputs_sha256"])
    assert sha(Path(lgb.basic._LIB._name).resolve()) == protocol["lightgbm_library_sha256"]
    check_hashes(OUT, read(OUT / "prepared_manifest.json"))
    assert read(OUT / "preparation.json")["status"] == "PASS"
    intervals = []
    for fold in FOLDS:
        data = OUT / "data" / fold
        names = read(data / "feature_mask.json")["selected_columns"]
        train = pd.read_parquet(data / "train.parquet", columns=names)
        future = pd.read_parquet(data / "evaluation.parquet", columns=names)
        target = pd.read_parquet(data / "training_transform.parquet")
        inverse = pd.read_parquet(data / "evaluation_transform.parquet")
        for seed in range(3):
            trial = OUT / fold / f"generation_seed{seed}"
            trial.mkdir(parents=True, exist_ok=False)
            params = {**GENERATION_PARAMS, "random_state": None if seed == 0 else seed}
            started, tick = now(), time.monotonic()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                estimator = lgb.LGBMRegressor(**params)
                estimator.fit(train, target.target_normalized.to_numpy(), sample_weight=target.sample_weight.to_numpy())
            model = estimator.booster_
            assert model.current_iteration() == 400 and model.feature_name() == names
            model.save_model(str(trial / "model.txt"))
            prediction = model.predict(future, num_threads=4, validate_features=True) * inverse.inverse_kwh.to_numpy()
            assert np.isfinite(prediction).all()
            inverse[KEYS].assign(p_raw=prediction).to_parquet(trial / "daylight_raw.parquet", index=False)
            replay = lgb.Booster(model_file=str(trial / "model.txt")).predict(future, num_threads=1, validate_features=True) * inverse.inverse_kwh.to_numpy()
            np.testing.assert_array_equal(prediction, replay)
            receipt = dict(kind="generation", fold=fold, seed=seed, parameters=params, features=names,
                started_utc=started, finished_utc=now(), seconds=time.monotonic() - tick, pid=os.getpid(),
                train_rows=len(train), evaluation_rows=len(future), fit_count=1, saved_replay_exact=True,
                warnings=[dict(category=w.category.__name__, message=str(w.message)) for w in caught], model_sha256=sha(trial / "model.txt"))
            save(trial / "receipt.json", receipt)
            intervals.append(receipt)
            print("PCA GENERATION COMPLETE", fold, seed, receipt["seconds"], flush=True)
    frames = {}
    for fold in FOLDS:
        data = OUT / "data" / fold
        inputs = pd.read_parquet(data / "application_inputs.parquet")
        labels = pd.read_parquet(data / "labels.parquet")
        coverage = pd.read_parquet(data / "coverage.parquet")
        assert_keys(inputs, labels)
        assert_keys(inputs, coverage)
        members = []
        for seed in range(3):
            raw = pd.read_parquet(OUT / fold / f"generation_seed{seed}" / "daylight_raw.parquet")
            full = inputs[KEYS].merge(raw, on=KEYS, how="left", sort=False, validate="one_to_one")
            assert_keys(full, inputs)
            assert full.p_raw.isna().eq(coverage.night).all()
            members.append(full.p_raw.fillna(0.).to_numpy())
        mean = np.mean(members, axis=0, dtype=np.float64)
        clipped, corrected = weather(inputs, mean)
        frame = labels.assign(signed_seed_mean=mean, p_component=clipped, p_new=corrected,
            static_capacity=inputs.static_capacity.to_numpy(), night=coverage.night.to_numpy())
        assert frame.loc[frame.night, "p_new"].eq(0).all()
        frames[fold] = frame
    alpha = alpha_optimum(frames["primary"])
    scores = {}
    for fold, frame in frames.items():
        frame["alpha"] = alpha
        frame["p"] = (1 - alpha) * frame.p_reference + alpha * frame.p_new
        frame.to_parquet(OUT / fold / "predictions.parquet", index=False)
        scores[fold] = {name: metric(frame, name) for name in ("p", "p_reference", "p_new")}
        assert abs(scores[fold]["p_reference"]["W_pct"] - EXPECTED_REFERENCE[fold]) < 1e-10
        save(OUT / fold / "metrics.json", scores[fold])
    both = all(scores[f]["p"]["W"] < scores[f]["p_reference"]["W"] for f in FOLDS)
    result = dict(arm=protocol["arm"], alpha_primary_only=alpha, scores=scores, both_folds_improve=both,
        eligible=both and alpha >= .02, real_generation_fit_count=6, real_pca_fit_count=2,
        real_alpha_fit_count=1, all_history_exposed=True, primary_alpha_partly_in_sample=True,
        transductive_future_weather=False, confirmation_loaded=False, test_loaded=False, exported=False)
    assert len(intervals) == 6 and all(a["finished_utc"] <= b["started_utc"] for a, b in zip(intervals, intervals[1:]))
    save(OUT / "fit_intervals.json", intervals)
    save(OUT / "results.json", result)
    check_hashes(POISSON, protocol["inputs_sha256"])
    check_hashes(ROOT, protocol["external_inputs_sha256"])
    check_hashes(OUT, read(OUT / "prepared_manifest.json"))
    assert sha(ROOT / protocol["best_zip"]) == protocol["best_zip_sha256"]
    save(OUT / "completed.json", dict(finished_utc=now(), pid=os.getpid(), generation_fit_count=6,
        best_zip_unchanged=True, prepared_inputs_unchanged=True))
    save(OUT / "terminal_manifest.json", {str(p.relative_to(OUT)): sha(p) for p in sorted(OUT.rglob("*"))
        if p.is_file() and p.name not in {"controller.lock", "terminal_manifest.json", "run.log", "prepare.log"}})
    print(result, flush=True)


def main():
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare", action="store_true")
    action.add_argument("--run", action="store_true")
    action.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    pa.set_cpu_count(2)
    pa.set_io_thread_count(2)
    with threadpool_limits(limits=1, user_api="blas"):
        if args.prepare:
            prepare()
        elif args.self_check:
            print(self_check())
        else:
            with (OUT / "controller.lock").open("a+b") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                run()


if __name__ == "__main__":
    main()
