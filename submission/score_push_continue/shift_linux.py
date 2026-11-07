"""Resume the frozen covariate-shift experiment on Linux without changing history.

Run with /workspace/.venvs/oibc-2026/bin/python and --prepare, then --run.
One process performs six domain fits then six LightGBM fits, serially.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import time
import warnings

os.environ.update(OMP_NUM_THREADS="4", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
                  NUMEXPR_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow as pa
import sklearn
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "analysis_outputs/renew_20261106/shift_wave"
POISSON = ROOT / "analysis_outputs/renew_20261106/poisson_wave"
OUT = ROOT / "analysis_outputs/renew_20261107/shift_linux"
FOLDS = ("primary", "recent")
KEYS = ["ts", "grp"]
EXPECTED_REFERENCE = {"primary": 11.959229078372204, "recent": 11.000952828788678}
DOMAIN_COLUMNS = ["wa_cloud", "wa_temp", "wa_humidity", "wa_ground_press", "wa_wind_speed", "wa_rain",
    "wb_cloud", "wb_uv_idx", "wb_temp", "wb_rel_hum", "wb_dew_point", "wb_vis", "wb_ceiling",
    "wb_precip_prob", "wb_total_liq", "cosz", "doy_sin", "doy_cos", "hour", "grp_code"]
DOMAIN_PARAMS = dict(C=.01, solver="lbfgs", max_iter=1000, tol=1e-6, class_weight="balanced", random_state=0)
GENERATION_PARAMS = dict(n_estimators=400, learning_rate=.03, num_leaves=63, min_child_samples=50,
    objective="regression_l1", subsample=.8, subsample_freq=1, colsample_bytree=.8, n_jobs=4, verbose=-1)
COPIES = ("train.parquet", "evaluation.parquet", "feature_mask.json", "training_transform.parquet",
          "evaluation_transform.parquet", "application_inputs.parquet", "coverage.parquet", "labels.parquet")


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def relocated(base, relative):
    parts = Path(relative.replace("\\", "/"))
    assert not parts.is_absolute() and ".." not in parts.parts
    return base / parts


def check_hashes(base, mapping):
    for name, expected in mapping.items():
        assert sha(relocated(base, name)) == expected, name


def historical_hashes(base, mapping):
    """Only accept exact bytes or a documented text line-ending migration."""
    records = {}
    for name, expected in mapping.items():
        path = relocated(base, name)
        actual = sha(path)
        status = "exact"
        if actual != expected:
            assert path.suffix.lower() in {".json", ".py", ".md", ".txt", ".csv", ".log"}, name
            content = path.read_bytes()
            content.decode("utf-8-sig")
            canonical = content.replace(b"\r\n", b"\n")
            candidates = (canonical, canonical.replace(b"\n", b"\r\n"))
            assert expected in [hashlib.sha256(candidate).hexdigest() for candidate in candidates], name
            status = "text_line_endings_only"
        records[name] = dict(historical_sha256=expected, current_sha256=actual, status=status)
    return records


def assert_keys(left, right):
    assert not left.duplicated(KEYS).any() and not right.duplicated(KEYS).any()
    pd.testing.assert_frame_equal(left[KEYS].reset_index(drop=True), right[KEYS].reset_index(drop=True), check_exact=True)


def metric(frame, column):
    assert np.isfinite(frame[[column, "y", "smp", "k"]].to_numpy()).all()
    weight = frame.smp.to_numpy() * frame.k.to_numpy()
    penalty = float(np.sum(weight * np.abs(frame[column].to_numpy() - frame.y.to_numpy())))
    denominator = float(np.sum(weight * frame.y.to_numpy()))
    revenue = float(np.sum(frame.smp.to_numpy() * frame.y.to_numpy()))
    assert denominator > 0 and (weight >= 0).all()
    return dict(W=penalty, W_pct=100 * penalty / denominator, revenue=revenue, S=revenue - .1 * penalty, rows=len(frame))


def alpha_optimum(frame):
    difference = frame.p_new.to_numpy() - frame.p_reference.to_numpy()
    monetary = frame.smp.to_numpy() * frame.k.to_numpy()
    active = (difference != 0) & (monetary > 0)
    if not active.any():
        return 0.
    ratio = (frame.y.to_numpy()[active] - frame.p_reference.to_numpy()[active]) / difference[active]
    weight = monetary[active] * np.abs(difference[active])
    order = np.argsort(ratio, kind="stable")
    index = np.searchsorted(np.cumsum(weight[order]), weight.sum() / 2, side="left")
    return float(np.clip(ratio[order[min(index, len(order) - 1)]], 0, 1))


def weather(inputs, signed_mean):
    factors = read(SOURCE / "original_weather_coefficients.json")["factors"]
    temperature = inputs.wa_temp.to_numpy(dtype=np.float64)
    snow = inputs.extra_wa_snow.to_numpy(dtype=np.float64)
    bins = np.full(len(inputs), -1, dtype=int)
    valid = np.isfinite(temperature)
    bins[valid] = np.searchsorted([0., 10., 20., 30.], temperature[valid], side="right")
    tf = np.array([1., *[r["factor"] for r in factors["temperature"]]])[bins + 1]
    sf = np.where(np.isfinite(snow) & (snow >= .001), factors["conditional_snow"]["factor"], 1.)
    correction = 1 + .5 * (np.clip(tf * sf, .85, 1.15) - 1)
    capacity = inputs.static_capacity.to_numpy(dtype=np.float64)
    clipped = np.clip(signed_mean, 0, capacity)
    return clipped, np.clip(clipped * correction, 0, capacity)


def validate_prepared():
    """Independent reconstruction of frozen arrays, split keys, target and weights."""
    old = read(SOURCE / "protocol.json")
    lineage = historical_hashes(ROOT, old["input_sha256"])
    prepared = historical_hashes(SOURCE, read(SOURCE / "prepared_manifest.json"))
    prior = read(POISSON / "independent_check.json")
    assert prior["status"] == "PASS"
    historical_hashes(POISSON, {"terminal_manifest.json": prior["terminal_manifest_sha256"]})
    assert old["domain_parameters"] == DOMAIN_PARAMS and old["domain_columns"] == DOMAIN_COLUMNS
    assert {**old["parameters"], "n_jobs": 4} == GENERATION_PARAMS
    records = []
    for fold in FOLDS:
        data = SOURCE / "data" / fold
        for name in COPIES:
            assert sha(data / name) == sha(POISSON / "data" / fold / name), (fold, name)
        frames = {kind: pd.read_parquet(data / (kind + ".parquet")) for kind in ("train", "evaluation")}
        matrices = {}
        for kind, frame in frames.items():
            projection = pd.read_parquet(data / ("domain_" + kind + "_inputs.parquet"))
            assert list(projection) == DOMAIN_COLUMNS
            pd.testing.assert_frame_equal(projection, frame[DOMAIN_COLUMNS], check_exact=True)
            matrices[kind] = np.asfortranarray(frame[DOMAIN_COLUMNS].to_numpy(dtype=np.float64))
            assert not np.isinf(matrices[kind]).any()
        source = matrices["train"]
        median = np.nanmedian(source, axis=0)
        imputed = np.where(np.isnan(source), median, source)
        mean, std = imputed.mean(axis=0), imputed.std(axis=0, ddof=0)
        scale = np.where(std == 0, 1., std)
        prep = read(data / "preprocessing.json")
        assert prep["columns"] == DOMAIN_COLUMNS and prep["clip"] == [-8, 8]
        assert prep["training_rows"] == len(source)
        for name, values in (("median", median), ("mean", mean), ("scale", scale)):
            np.testing.assert_allclose(prep[name], values, rtol=1e-14, atol=1e-12)
        for kind, values in matrices.items():
            expected = np.clip((np.where(np.isnan(values), median, values) - mean) / scale, -8, 8)
            stored = np.load(data / ("domain_" + kind + "_matrix.npy"), allow_pickle=False)
            assert stored.dtype == np.float64 and np.isfinite(stored).all()
            np.testing.assert_allclose(stored, expected, rtol=1e-14, atol=1e-12)
        partition = pd.read_parquet(data / "domain_fold.parquet")
        assert_keys(frames["train"], partition)
        ordinals = frames["train"].ts.dt.tz_convert("Asia/Seoul").dt.date.map(lambda d: d.toordinal()).to_numpy()
        np.testing.assert_array_equal(partition.date_ordinal, ordinals)
        np.testing.assert_array_equal(partition.domain_fold, ordinals % 3)
        tr = pd.read_parquet(data / "training_transform.parquet")
        inv = pd.read_parquet(data / "evaluation_transform.parquet")
        assert_keys(frames["train"], tr)
        assert_keys(frames["evaluation"], inv)
        np.testing.assert_allclose(tr.target_normalized, frames["train"].cf / tr.normalizer, rtol=1e-14, atol=1e-12)
        decay = np.exp2(-tr.age_days.to_numpy() / 180)
        np.testing.assert_allclose(tr.sample_weight, tr.normalizer.to_numpy() * decay / decay.mean(), rtol=1e-14, atol=1e-12)
        np.testing.assert_allclose(inv.inverse_kwh, inv.normalizer * inv.capacity_kw, rtol=1e-14, atol=1e-12)
        spec = read(data / "feature_mask.json")
        assert spec["fitted_on"] == "training only" and spec["native_nan"]
        assert not set(spec["selected_columns"]) & {"cf", "y", "smp", "k", "ts", "grp"}
        assert frames["train"].ts.max() <= pd.Timestamp(spec["cutoff"])
        assert frames["evaluation"].ts.min() > pd.Timestamp(spec["cutoff"])
        assert frames["evaluation"].ts.max() <= pd.Timestamp(spec["end"])
        inputs = pd.read_parquet(data / "application_inputs.parquet")
        coverage = pd.read_parquet(data / "coverage.parquet")
        labels = pd.read_parquet(data / "labels.parquet")
        assert_keys(inputs, coverage)
        assert_keys(inputs, labels)
        # Full coverage is timestamp-major; model matrices are group-major.
        # Production prediction assembly below joins explicit keys, never positions.
        assert_keys(inputs.loc[~coverage.night].sort_values(KEYS), frames["evaluation"].sort_values(KEYS))
        assert abs(metric(labels, "p_reference")["W_pct"] - EXPECTED_REFERENCE[fold]) < 1e-10
        records.append(dict(fold=fold, train_rows=len(source), evaluation_rows=len(inv), full_rows=len(labels),
            features=len(spec["selected_columns"]), domain_partition_rows=partition.groupby("domain_fold").size().tolist()))
    current = {name: sha(relocated(ROOT, name)) for name in old["protected_sha256"]}
    placeholders = [name for name in current if relocated(ROOT, name).stat().st_size < 200 and
                    relocated(ROOT, name).read_bytes().startswith(b"version https://git-lfs.github.com/spec/v1")]
    return dict(status="PASS", records=records, protected_files=len(current), protected_current_sha256=current,
                current_lfs_placeholders=placeholders, required_prepared_hash_check=prepared, required_lineage_hash_check=lineage,
                historical_preservation_claim="Required experiment inputs exact or text line endings only; remaining historical files pinned at current state, not asserted identical to old machine.",
                real_fits=0, domain_input_labels_excluded=True, future_weather_transductive=True)


def prepare():
    assert not OUT.exists(), "Preserve existing continuation; use its frozen protocol."
    checked = validate_prepared()
    OUT.mkdir(parents=True)
    shutil.copyfile(__file__, OUT / "shift_linux.py")
    best = ROOT / "submission/renew_candidate_20261105/submission_files.zip"
    assert sha(best) == "ff14806cd8e0f1de7d85a1763ac16ff13a3668c5232ecf8da5faccf358050434"
    library = Path(lgb.basic._LIB._name).resolve()
    environment = dict(python=platform.python_version(), platform=platform.platform(), pid=os.getpid(),
        packages={m.__name__: m.__version__ for m in (np, pd, pa, sklearn, lgb)},
        lightgbm_library=str(library), lightgbm_sha256=sha(library),
        cpu_threads=4, blas_threads=1, arrow_threads=2, parallel_fits=1)
    protocol = dict(created_utc=now(), original_protocol_sha256=sha(SOURCE / "protocol.json"),
        original_prepared_sha256=sha(SOURCE / "prepared_manifest.json"), source_sha256=sha(__file__),
        source_file=str(Path(__file__).relative_to(ROOT)),
        amendment="Linux runtime only: portable process/lock/library checks; CPU4 BLAS1 Arrow2 instead of Windows16/16/4. Scientific recipe unchanged. Cross-platform fit bits may differ.",
        domain_parameters=DOMAIN_PARAMS, generation_parameters=GENERATION_PARAMS, environment=environment,
        folds=list(FOLDS), seeds=[0, 1, 2], model_fit_budget=12, domain_fit_budget=6, generation_fit_budget=6,
        alpha_fit_budget=1, reference_scores=EXPECTED_REFERENCE,
        prepared_inputs={name: record["current_sha256"] for name, record in checked["required_prepared_hash_check"].items()},
        protected_current_sha256=checked["protected_current_sha256"],
        best_zip=str(best.relative_to(ROOT)), best_zip_sha256=sha(best),
        selection="One primary-only weighted L1 alpha transferred unchanged; both W improve and alpha>=.02.",
        all_history_exposed=True, confirmation_loaded=False, test_loaded=False, exported=False)
    save(OUT / "protocol.json", protocol)
    save(OUT / "preparation_check.json", {**checked, "protocol_sha256": sha(OUT / "protocol.json")})
    print(json.dumps({"status": "READY", "records": checked["records"], "protected_files": checked["protected_files"],
                      "current_lfs_placeholders": len(checked["current_lfs_placeholders"]), "real_fits": 0}), flush=True)


def run():
    protocol = read(OUT / "protocol.json")
    assert read(OUT / "preparation_check.json")["status"] == "PASS"
    assert read(OUT / "preparation_check.json")["protocol_sha256"] == sha(OUT / "protocol.json")
    assert sha(__file__) == sha(OUT / "shift_linux.py") == protocol["source_sha256"]
    assert sha(SOURCE / "protocol.json") == protocol["original_protocol_sha256"]
    assert sha(SOURCE / "prepared_manifest.json") == protocol["original_prepared_sha256"]
    check_hashes(SOURCE, protocol["prepared_inputs"])
    check_hashes(ROOT, protocol["protected_current_sha256"])
    assert sha(ROOT / protocol["best_zip"]) == protocol["best_zip_sha256"]
    assert sha(Path(lgb.basic._LIB._name).resolve()) == protocol["environment"]["lightgbm_sha256"]
    assert not (OUT / "run_started.json").exists(), "No implicit retries or extra fits."
    save(OUT / "run_started.json", dict(pid=os.getpid(), started_utc=now(), protocol_sha256=sha(OUT / "protocol.json")))
    intervals = []
    for fold in FOLDS:
        data = SOURCE / "data" / fold
        directory = OUT / fold
        directory.mkdir()
        source = np.load(data / "domain_train_matrix.npy", allow_pickle=False)
        target = np.load(data / "domain_evaluation_matrix.npy", allow_pickle=False)
        partition = pd.read_parquet(data / "domain_fold.parquet")
        logits = np.full(len(source), np.nan)
        for split in range(3):
            trial = directory / ("domain_split" + str(split))
            trial.mkdir()
            held = partition.domain_fold.to_numpy() == split
            assert set(partition.loc[held, "date_ordinal"]).isdisjoint(partition.loc[~held, "date_ordinal"])
            x = np.concatenate([source[~held], target])
            y = np.concatenate([np.zeros((~held).sum(), dtype=int), np.ones(len(target), dtype=int)])
            started, tick = now(), time.monotonic()
            model = LogisticRegression(**DOMAIN_PARAMS)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                model.fit(x, y)
            records = [dict(category=w.category.__name__, message=str(w.message)) for w in caught]
            assert not any(issubclass(w.category, ConvergenceWarning) for w in caught), records
            logits[held] = model.decision_function(source[held])
            joblib.dump(dict(classifier=model, preprocessing=read(data / "preprocessing.json")), trial / "classifier.joblib")
            replay = joblib.load(trial / "classifier.joblib")["classifier"].decision_function(source[held])
            np.testing.assert_array_equal(replay, logits[held])
            partition.loc[held].assign(row_index=np.flatnonzero(held), logit=logits[held]).to_parquet(trial / "oof.parquet", index=False)
            receipt = dict(kind="domain", fold=fold, split=split, started_utc=started, finished_utc=now(),
                seconds=time.monotonic() - tick, pid=os.getpid(), fit_count=1, parameters=DOMAIN_PARAMS,
                source_fit_rows=int((~held).sum()), future_fit_rows=len(target), held_rows=int(held.sum()),
                n_iter=model.n_iter_.tolist(), warnings=records, saved_replay_exact=True, model_sha256=sha(trial / "classifier.joblib"))
            save(trial / "receipt.json", receipt)
            intervals.append(receipt)
            print("DOMAIN COMPLETE", fold, split, receipt["seconds"], flush=True)
        assert np.isfinite(logits).all()
        base = pd.read_parquet(data / "training_transform.parquet")
        assert_keys(base, partition)
        ratio = np.exp(logits)
        modifier = np.sqrt(np.clip(ratio, .25, 4.))
        weight = base.sample_weight.to_numpy() * modifier
        weight *= base.sample_weight.sum() / weight.sum()
        assert np.isfinite(weight).all() and (weight > 0).all()
        np.testing.assert_allclose(weight.sum(), base.sample_weight.sum(), rtol=1e-14)
        partition.assign(logit=logits, ratio=ratio, modifier=modifier, base_weight=base.sample_weight.to_numpy(), sample_weight=weight).to_parquet(directory / "domain_weights.parquet", index=False)
    for fold in FOLDS:
        data = SOURCE / "data" / fold
        directory = OUT / fold
        names = read(data / "feature_mask.json")["selected_columns"]
        train = pd.read_parquet(data / "train.parquet", columns=names)
        future = pd.read_parquet(data / "evaluation.parquet", columns=names)
        transform = pd.read_parquet(data / "training_transform.parquet")
        inverse = pd.read_parquet(data / "evaluation_transform.parquet")
        weights = pd.read_parquet(directory / "domain_weights.parquet")
        assert_keys(transform, weights)
        for seed in range(3):
            trial = directory / ("generation_seed" + str(seed))
            trial.mkdir()
            params = {**GENERATION_PARAMS, "random_state": None if seed == 0 else seed}
            started, tick = now(), time.monotonic()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                estimator = lgb.LGBMRegressor(**params)
                estimator.fit(train, transform.target_normalized.to_numpy(), sample_weight=weights.sample_weight.to_numpy())
            model = estimator.booster_
            assert model.current_iteration() == 400 and model.feature_name() == names
            model.save_model(str(trial / "model.txt"))
            prediction = model.predict(future, num_threads=4, validate_features=True) * inverse.inverse_kwh.to_numpy()
            assert np.isfinite(prediction).all()
            inverse[KEYS].assign(p_raw=prediction).to_parquet(trial / "daylight_raw.parquet", index=False)
            replay = lgb.Booster(model_file=str(trial / "model.txt")).predict(future, num_threads=1, validate_features=True) * inverse.inverse_kwh.to_numpy()
            np.testing.assert_array_equal(replay, prediction)
            receipt = dict(kind="generation", fold=fold, seed=seed, started_utc=started, finished_utc=now(),
                seconds=time.monotonic() - tick, pid=os.getpid(), fit_count=1, parameters=params,
                features=names, train_rows=len(train), evaluation_rows=len(future), saved_replay_exact=True,
                warnings=[dict(category=w.category.__name__, message=str(w.message)) for w in caught], model_sha256=sha(trial / "model.txt"))
            save(trial / "receipt.json", receipt)
            intervals.append(receipt)
            print("GENERATION COMPLETE", fold, seed, receipt["seconds"], flush=True)
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
            assert_keys(full, inputs)
            assert full.p_raw.isna().eq(coverage.night).all()
            members.append(full.p_raw.fillna(0).to_numpy())
        mean = np.mean(members, axis=0, dtype=np.float64)
        clipped, corrected = weather(inputs, mean)
        frame = labels.assign(signed_seed_mean=mean, p_component=clipped, p_new=corrected, static_capacity=inputs.static_capacity.to_numpy(), night=coverage.night.to_numpy())
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
    result = dict(alpha_primary_only=alpha, scores=scores, both_folds_improve=both, eligible=both and alpha >= .02,
        real_model_fit_count=12, real_domain_fit_count=6, real_generation_fit_count=6, real_alpha_fit_count=1,
        all_history_exposed=True, primary_alpha_partly_in_sample=True, transductive_future_weather=True,
        confirmation_loaded=False, test_loaded=False, exported=False)
    assert len(intervals) == 12 and all(a["finished_utc"] <= b["started_utc"] for a, b in zip(intervals, intervals[1:]))
    save(OUT / "fit_intervals.json", intervals)
    save(OUT / "results.json", result)
    check_hashes(SOURCE, protocol["prepared_inputs"])
    check_hashes(ROOT, protocol["protected_current_sha256"])
    assert sha(ROOT / protocol["best_zip"]) == protocol["best_zip_sha256"]
    save(OUT / "completed.json", dict(finished_utc=now(), pid=os.getpid(), fit_count=12, best_zip_unchanged=True, prepared_inputs_unchanged=True))
    manifest = {str(p.relative_to(OUT)): sha(p) for p in sorted(OUT.rglob("*")) if p.is_file() and p.name not in {"controller.lock", "terminal_manifest.json", "run.log"}}
    save(OUT / "terminal_manifest.json", manifest)
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--prepare", action="store_true")
    action.add_argument("--run", action="store_true")
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
