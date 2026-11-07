"""Serial, checkpointed rolling-origin research; no network or leaderboard writes.

`prepare` freezes 256 configurations and the pre-March search protocol without
fitting. `trial --id cNNN` fits five origins. `complete` freezes a development
recipe before opening late-audit targets. `report` never fits a model.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import zipfile

os.environ.update(OMP_NUM_THREADS="4", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
                  NUMEXPR_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from threadpoolctl import threadpool_limits

import data as source

ROOT, OUT, DATA, FOLDS, KEYS = source.ROOT, source.OUT, source.DATA, source.FOLDS, source.KEYS
FINAL = ROOT / "analysis_outputs/renew_20261105/final"
CANDIDATE = ROOT / "submission/research_10h_candidate_20261107"
DEADLINE = "2026-11-07T08:56:33+00:00"
sha, read, kst = source.sha, source.read, source.kst
pa.set_cpu_count(2)
pa.set_io_thread_count(2)


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


@contextmanager
def locked():
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "engine.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def normalizer(frame):
    cosine = np.maximum(frame.cosz.to_numpy(dtype=float), 0)
    exponent = np.divide(-.059, cosine, out=np.zeros_like(cosine), where=cosine > 0)
    return np.maximum(1.098 * cosine * np.exp(exponent), .05)


def write_parquet(frame, path):
    temporary = path.with_name(path.name + ".tmp")
    frame.to_parquet(temporary, index=False)
    with temporary.open("rb") as stream:
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def metric(frame, column="p"):
    values = frame[[column, "y", "smp", "k"]].to_numpy(dtype=float)
    assert np.isfinite(values).all()
    weight = values[:, 2] * values[:, 3]
    assert (weight >= 0).all()
    penalty = float(np.sum(weight * np.abs(values[:, 0] - values[:, 1])))
    denominator = float(np.sum(weight * values[:, 1]))
    revenue = float(np.sum(values[:, 2] * values[:, 1]))
    assert denominator > 0
    return {"W": penalty, "W_pct": 100 * penalty / denominator,
            "revenue": revenue, "S": revenue - .1 * penalty, "rows": len(frame)}


def alpha_optimum(frame):
    difference = frame.p.to_numpy() - frame.p_reference.to_numpy()
    monetary = frame.smp.to_numpy() * frame.k.to_numpy()
    active = (difference != 0) & (monetary > 0)
    if not active.any():
        return 0.
    ratio = (frame.y.to_numpy()[active] - frame.p_reference.to_numpy()[active]) / difference[active]
    weight = monetary[active] * np.abs(difference[active])
    order = np.argsort(ratio, kind="stable")
    index = np.searchsorted(np.cumsum(weight[order]), weight.sum() / 2, side="left")
    return float(np.clip(ratio[order[min(index, len(order) - 1)]], 0, 1))


def configurations():
    baseline = dict(features="station", objective="regression_l1", target="original_cf",
                    weighting="legacy", half_life=180, n_estimators=400,
                    learning_rate=.03, num_leaves=63, min_child_samples=50,
                    reg_lambda=0., colsample_bytree=.8, subsample=.8)
    rows = [baseline, {**baseline, "target": "exact_energy", "weighting": "monetary"},
            {**baseline, "features": "rich", "target": "exact_energy", "weighting": "monetary"},
            {**baseline, "features": "rich"}]
    rng = np.random.default_rng(20261107)
    while len(rows) < 256:
        index = len(rows)
        objective = "regression_l2" if index % 8 == 7 else "regression_l1"
        legacy = index % 16 == 14 or index % 32 == 31
        candidate = dict(features=("rich" if (index % 2 + index // 16) % 2 == 0 else "station"),
            objective=objective, target="original_cf" if legacy else "exact_energy",
            weighting="legacy" if legacy else "monetary",
            half_life=[None, 90, 180, 365][int(rng.integers(4))],
            n_estimators=int(rng.choice([400, 700, 1000, 1400, 2000])),
            learning_rate=float(rng.choice([.015, .025, .04, .055, .07])),
            num_leaves=int(rng.choice([15, 31, 63, 127])),
            min_child_samples=int(rng.choice([50, 100, 200, 300])),
            reg_lambda=float(rng.choice([0., 2., 8., 20.])),
            colsample_bytree=float(rng.choice([.65, .8, 1.])), subsample=.8)
        if candidate not in rows:
            rows.append(candidate)
    return [{"id": f"c{index:03d}", **row} for index, row in enumerate(rows)]


def prepare():
    source.ensure_prepare()
    config_path, protocol_path = OUT / "configs.json", OUT / "protocol.json"
    if protocol_path.exists():
        verify_protocol()
        return read(protocol_path)
    assert not config_path.exists(), "Interrupted protocol creation requires inspection"
    save(config_path, configurations())
    protocol = dict(created_utc=now(), configs_sha256=sha(config_path),
        data_manifest_sha256=sha(DATA / "manifest.json"),
        source_sha256={str(path.relative_to(ROOT)): sha(path) for path in [Path(__file__), Path(source.__file__)]},
        folds=FOLDS, baseline_id="c000", search_end_kst=str(kst("2025-03-01")),
        target="exact all-site group y / (capacity_kw * max(Haurwitz, .05)); original_cf arms are explicit comparators",
        monetary_l1="normalized SMP*k*inverse_kwh*recency; without recency this is exactly monetary absolute energy loss",
        monetary_l2="normalized SMP*k*inverse_kwh**2*recency; monetary energy squared loss complement",
        legacy_weight="Haurwitz * recency / mean(recency), preserving original baseline scale",
        recency="exp2(-age_days/half_life), age measured from each training cutoff; none=1",
        features="rich100 or station904, drop constants using training values only; native missing values",
        clipping="raw model component clipped to [0, fixed group installed capacity]; all-night prediction zero; no historical weather correction",
        selection=dict(standalone_mean_W_ratio_below=1., standalone_worst_W_ratio_at_most=1.02,
                       standalone_improved_folds_at_least=3, primary_blend_minimum_alpha=.02,
                       primary_and_recent_blend_strict_improvement=True,
                       order="mean fivefold W ratio, then worst ratio, then id",
                       diversity="first differing (features, objective, target, half_life), up to three",
                       seed_ensemble=[0, 1, 2], equal_model_weights=True,
                       alpha="monetary-L1 optimum on primary only; unchanged transfer to recent and deployment"),
        late_audit="March-May 2025 latest-cutoff labels opened only after development selection/alpha frozen; descriptive, never reselect",
        late_audit_labels_hash_only_sha256=sha(FINAL / "predictions/latest_cutoff_march_may/scored_predictions.parquet"),
        completion_budget="up to three diverse eligible configs; reduce count before freeze using measured fit time and final-hour remaining budget",
        all_history_previously_exposed=True, new_independent_holdout=False,
        forecast_horizons_overlap=True, five_origins_are_not_five_independent_samples=True,
        hard_deadline_utc=DEADLINE, candidate_count=256, search_seeds=[0],
        environment=dict(python=platform.python_version(), lightgbm=lgb.__version__, numpy=np.__version__,
                         pandas=pd.__version__, cpu_threads=4, blas_threads=1, parallel_fits=1),
        deployment_input_sha256={str(path.relative_to(ROOT)): sha(path)
            for split in ("latest_cutoff_march_may", "test")
            for path in [FINAL / "data" / ("test" if split == "test" else "march_may") / "evaluation.parquet",
                         FINAL / "data" / ("test" if split == "test" else "march_may") / "coverage.parquet",
                         FINAL / "predictions" / split / "predictions.parquet"]},
        official_best_sha256=source.BEST_SHA, official_best_user_reported=6454220836,
        official_score_available=False, uploaded=False)
    save(protocol_path, protocol)
    return protocol


def verify_protocol():
    protocol = read(OUT / "protocol.json")
    assert sha(OUT / "configs.json") == protocol["configs_sha256"]
    assert read(OUT / "configs.json") == configurations()
    assert sha(DATA / "manifest.json") == protocol["data_manifest_sha256"]
    for name, expected in protocol["source_sha256"].items():
        assert sha(ROOT / name) == expected, f"Frozen implementation changed: {name}"
    source.verify_ready()
    assert sha(FINAL / "predictions/latest_cutoff_march_may/scored_predictions.parquet") == protocol["late_audit_labels_hash_only_sha256"]
    assert sha(source.BEST_ZIP) == source.BEST_SHA
    for name, expected in protocol["deployment_input_sha256"].items():
        assert sha(ROOT / name) == expected, name
    return protocol


def verify_files(folder, receipt):
    for name, expected in receipt["files_sha256"].items():
        assert sha(folder / name) == expected, folder / name


def transform(train, config, origin):
    norm = normalizer(train)
    inverse = norm * train.capacity_kw.to_numpy(dtype=float)
    age = (kst(origin) - train.ts).dt.total_seconds().to_numpy() / 86400
    assert (age >= 0).all()
    decay = np.ones(len(train)) if config["half_life"] is None else np.exp2(-age / config["half_life"])
    target = train.cf.to_numpy() / norm if config["target"] == "original_cf" else train.y.to_numpy() / inverse
    if config["weighting"] == "legacy":
        weight = norm * decay / decay.mean()
    else:
        exponent = 2 if config["objective"] == "regression_l2" else 1
        weight = train.smp.to_numpy() * train.k.to_numpy() * inverse ** exponent * decay
        weight /= weight.mean()
    assert np.isfinite(target).all() and np.isfinite(weight).all() and (weight >= 0).all() and weight.sum() > 0
    return target, weight


def assemble(evaluation, full, raw):
    daylight = evaluation[KEYS].copy()
    daylight["p"] = raw * normalizer(evaluation) * evaluation.capacity_kw.to_numpy()
    result = full.merge(daylight, on=KEYS, how="left", sort=False, validate="one_to_one", indicator=True)
    assert result._merge.eq("left_only").equals(result.night)
    assert result.loc[~result.night, "p"].notna().all()
    result["p"] = np.clip(result.p.fillna(0).to_numpy(), 0, result.static_capacity.to_numpy())
    result.loc[result.night, "p"] = 0.
    return result.drop(columns="_merge")


def fit_one(config, seed, fold, folder, resume=False, deployment=None):
    """Each receipt is committed only after native model reload/replay succeeds."""
    if (folder / "receipt.json").exists():
        receipt = read(folder / "receipt.json")
        assert receipt["config"] == config and receipt["seed"] == seed and receipt["fold"] == fold
        verify_files(folder, receipt)
        return receipt
    if folder.exists():
        assert resume, f"Partial fit preserved at {folder}; inspect and use --resume explicitly"
        archive = folder.with_name(folder.name + ".interrupted." + str(time.time_ns()))
        os.rename(folder, archive)
    folder.mkdir(parents=True)
    started = time.monotonic()
    save(folder / "started.json", dict(utc=now(), config=config, seed=seed, fold=fold))
    if deployment is None:
        base = DATA / fold
        train = pd.read_parquet(base / "train.parquet")
        evaluation = pd.read_parquet(base / "evaluation.parquet")
        full = pd.read_parquet(base / "labels.parquet")
        features = read(base / "features.json")["selected"][config["features"]]
        origin = FOLDS[fold]["origin"]
    else:
        train, evaluation, full, origin = deployment
        candidates = read(DATA / "features.json")[config["features"]]
        features = [name for name in candidates if train[name].nunique(dropna=True) > 1]
    assert train.ts.max() <= kst(origin) < evaluation.ts.min()
    target, weight = transform(train, config, origin)
    save(folder / "transform.json", dict(features=features, origin=origin,
        training_rows=len(train), evaluation_rows=len(evaluation), training_start=str(train.ts.min()),
        training_end=str(train.ts.max()), weight_min=float(weight.min()), weight_max=float(weight.max()),
        weight_mean=float(weight.mean()), target_min=float(target.min()), target_max=float(target.max())))
    params = {key: config[key] for key in ["objective", "n_estimators", "learning_rate", "num_leaves",
              "min_child_samples", "reg_lambda", "colsample_bytree", "subsample"]}
    params.update(subsample_freq=1, n_jobs=4, verbose=-1, random_state=seed,
                  deterministic=True, force_col_wise=True)
    model = lgb.LGBMRegressor(**params)
    with threadpool_limits(limits=1, user_api="blas"):
        model.fit(train[features], target, sample_weight=weight)
        raw = model.predict(evaluation[features], num_threads=4)
        model.booster_.save_model(str(folder / "model.txt"))
        restored = lgb.Booster(model_file=str(folder / "model.txt"))
        replay = restored.predict(evaluation[features], num_threads=4)
    np.testing.assert_array_equal(raw, replay)
    predictions = assemble(evaluation, full, raw)
    write_parquet(predictions, folder / "predictions.parquet")
    receipt = dict(status="PASS", config=config, seed=seed, fold=fold, utc=now(),
                   elapsed_seconds=time.monotonic() - started, native_saved_model_replay=True,
                   train_only_feature_mask=True, real_model_fits=1,
                   score=metric(predictions) if "y" in predictions else None,
                   files_sha256={name: sha(folder / name) for name in ["model.txt", "predictions.parquet", "transform.json"]})
    save(folder / "receipt.json", receipt)
    return receipt


def blend_scores(frames):
    alpha = alpha_optimum(frames["primary"])
    scores = {}
    for fold, frame in frames.items():
        blended = frame.assign(p_blend=frame.p_reference + alpha * (frame.p - frame.p_reference))
        scores[fold] = {"reference": metric(frame, "p_reference"), "component": metric(frame),
                        "blend": metric(blended, "p_blend")}
    eligible = alpha >= .02 and all(item["blend"]["W"] < item["reference"]["W"] for item in scores.values())
    return dict(alpha=alpha, scores=scores, primary_only_alpha=True,
                recent_unchanged_transfer=True, eligible=eligible)


def trial(identifier, resume=False):
    verify_protocol()
    config = next(item for item in read(OUT / "configs.json") if item["id"] == identifier)
    folder = OUT / "trials" / identifier
    if (folder / "result.json").exists():
        result = read(folder / "result.json")
        for fold in FOLDS:
            verify_files(folder / fold, read(folder / fold / "receipt.json"))
        return result
    records = {}
    for fold in FOLDS:
        records[fold] = fit_one(config, 0, fold, folder / fold, resume=resume)
    frames = {fold: pd.read_parquet(folder / fold / "predictions.parquet") for fold in ("primary", "recent")}
    result = dict(id=identifier, config=config, utc=now(), status="PASS", folds=records,
                  blend=blend_scores(frames), real_model_fits=5, all_history_previously_exposed=True,
                  march_may_targets_loaded=False, protocol_sha256=sha(OUT / "protocol.json"))
    save(folder / "result.json", result)
    return result


def ranked_results():
    files = sorted((OUT / "trials").glob("c*/result.json"))
    results = [read(path) for path in files]
    if not results:
        return []
    baseline = next(item for item in results if item["id"] == "c000")
    ranked = []
    for result in results:
        ratios = {fold: result["folds"][fold]["score"]["W"] / baseline["folds"][fold]["score"]["W"] for fold in FOLDS}
        mean, worst = float(np.mean(list(ratios.values()))), max(ratios.values())
        improved = sum(value < 1 for value in ratios.values())
        robust = mean < 1 and worst <= 1.02 and improved >= 3
        ranked.append(dict(id=result["id"], config=result["config"], ratios=ratios,
            mean_W_ratio=mean, worst_W_ratio=worst, improved_folds=improved,
            robust=robust, blend=result["blend"], eligible=robust and result["blend"]["eligible"],
            elapsed_seconds=sum(item["elapsed_seconds"] for item in result["folds"].values())))
    return sorted(ranked, key=lambda item: (item["mean_W_ratio"], item["worst_W_ratio"], item["id"]))


def remaining(deadline):
    return (datetime.fromisoformat(deadline.replace("Z", "+00:00")) - datetime.now(timezone.utc)).total_seconds()


class BudgetFinished(Exception):
    pass


def check_budget(deadline, expected=60):
    if remaining(deadline) < max(90, expected * 1.5 + 45):
        raise BudgetFinished("Insufficient remaining time to safely begin the next fit")


def ensemble_frames(identifiers, fold, completion):
    frames = []
    for identifier in identifiers:
        for seed in (0, 1, 2):
            folder = OUT / "trials" / identifier / fold if seed == 0 else completion / "validation" / identifier / f"seed{seed}" / fold
            receipt = read(folder / "receipt.json")
            verify_files(folder, receipt)
            frames.append(pd.read_parquet(folder / "predictions.parquet"))
    anchor = frames[0].copy()
    for frame in frames:
        pd.testing.assert_frame_equal(frame[KEYS], anchor[KEYS], check_exact=True)
    anchor["p"] = np.mean([frame.p.to_numpy() for frame in frames], axis=0)
    return anchor


def deployment_data(split):
    """Called only after selection_frozen.json exists; never invoked by search."""
    assert (OUT / "completion/selection_frozen.json").exists()
    selection = read(OUT / "completion/selection_frozen.json")
    assert selection["eligible"] and selection["before_late_audit_target_reads"]
    feature_split = "test" if split == "test" else "march_may"
    origin = "2025-06-01" if split == "test" else "2025-03-01"
    filters = [("ts", "<=", kst(origin))]
    train = pq.read_table(source.FULL_FEATURES, filters=filters).to_pandas()
    site = pq.read_table(source.SITE_LABELS, columns=["ts", "site_id", "energy"], filters=filters).to_pandas()
    site["grp"] = site.site_id.map(read(source.ASSIGNMENT))
    assert site.grp.notna().all()
    truth = site.groupby(KEYS, as_index=False).agg(y=("energy", "sum"))
    prices = pq.read_table(source.SMP, columns=["ts", "smp", "k"], filters=filters).to_pandas()
    truth = truth.merge(prices, on="ts", validate="many_to_one")
    train = source.checked_join(train, truth, ["y", "smp", "k"])
    evaluation = pd.read_parquet(FINAL / "data" / feature_split / "evaluation.parquet")
    coverage = pd.read_parquet(FINAL / "data" / feature_split / "coverage.parquet")
    full = pd.read_parquet(FINAL / "predictions" / split / "predictions.parquet",
                           columns=[*KEYS, "p", "static_capacity"]).rename(columns={"p": "p_reference"})
    full = source.checked_join(full, coverage, ["night"])
    assert full.loc[full.night, "p_reference"].eq(0).all()
    return train, evaluation, full, origin


def export_candidate(test, selection, audit):
    with zipfile.ZipFile(source.BEST_ZIP) as archive:
        composition = archive.read("composition.csv")
        original = pd.read_csv(io.BytesIO(archive.read("forecast.csv")))
    original["ts"] = pd.to_datetime(original.ts).dt.tz_convert("Asia/Seoul")
    original = original.rename(columns={"group": "grp"}).sort_values(["grp", "ts"]).reset_index(drop=True)
    test = test.sort_values(["grp", "ts"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(test[KEYS], original[KEYS], check_exact=True)
    np.testing.assert_array_equal(np.round(test.p_reference, 3), original.forecast_kwh)
    assert len(test) == 17520 and np.isfinite(test.p).all() and test.p.ge(0).all()
    assert (test.p <= test.static_capacity + 1e-9).all() and test.loc[test.night, "p"].eq(0).all()
    if CANDIDATE.exists():
        if (CANDIDATE / "manifest.json").exists():
            manifest = read(CANDIDATE / "manifest.json")
            for name, expected in manifest["files_sha256"].items():
                assert sha(CANDIDATE / name) == expected
            return manifest
        os.rename(CANDIDATE, CANDIDATE.with_name(CANDIDATE.name + ".interrupted." + str(time.time_ns())))
    CANDIDATE.mkdir()
    (CANDIDATE / "composition.csv").write_bytes(composition)
    pd.DataFrame({"group": test.grp, "ts": test.ts.astype(str), "forecast_kwh": np.round(test.p, 3)}).to_csv(
        CANDIDATE / "forecast.csv", index=False, lineterminator="\r\n")
    with zipfile.ZipFile(CANDIDATE / "submission_files.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name in ("composition.csv", "forecast.csv"):
            archive.write(CANDIDATE / name, arcname=name)
    check = subprocess.run([sys.executable, str(ROOT / "submission/validate_artifacts.py"), str(CANDIDATE), "--self-check"],
                           capture_output=True, text=True, timeout=90)
    (CANDIDATE / "validation.log").write_text(check.stdout + check.stderr)
    assert check.returncode == 0, check.stdout + check.stderr
    validation = json.loads(check.stdout)
    assert validation["rows_above_own_capacity"] == 0
    manifest = dict(created_utc=now(), selection=selection, audit=audit, validation=validation,
        original_composition_bytes_preserved=True, official_best_sha256=source.BEST_SHA,
        files_sha256={name: sha(CANDIDATE / name) for name in ["composition.csv", "forecast.csv", "submission_files.zip"]},
        all_history_previously_exposed=True, official_score_available=False, uploaded=False)
    save(CANDIDATE / "manifest.json", manifest)
    return manifest


def complete(deadline):
    deadline = min(datetime.fromisoformat(deadline.replace("Z", "+00:00")), datetime.fromisoformat(DEADLINE)).isoformat()
    verify_protocol()
    completion = OUT / "completion"
    completion.mkdir(exist_ok=True)
    if (completion / "result.json").exists():
        return read(completion / "result.json")
    state_path = completion / "state.json"
    try:
        if not (completion / "shortlist.json").exists():
            ranking = ranked_results()
            chosen, groups, estimated = [], set(), 0.
            for item in ranking:
                config = item["config"]
                group = tuple(config[key] for key in ("features", "objective", "target", "half_life"))
                if not item["eligible"] or group in groups:
                    continue
                # Four new validation fits and six deployment fits per config.
                cost = item["elapsed_seconds"] / 5 * 10 * 1.8
                if estimated + cost + 240 > remaining(deadline):
                    continue
                chosen.append(item)
                groups.add(group)
                estimated += cost
                if len(chosen) == 3:
                    break
            save(completion / "shortlist.json", dict(utc=now(), candidates=chosen,
                ranking=ranking, budget_seconds_remaining=remaining(deadline), estimated_seconds=estimated,
                before_late_audit_target_reads=True))
        chosen = read(completion / "shortlist.json")["candidates"]
        if not chosen:
            result = dict(status="NO_QUALIFYING_RECIPE", utc=now(), exported=False,
                          reason="No candidate passed fixed development gates within remaining finalization budget",
                          march_may_targets_loaded=False, all_history_previously_exposed=True)
            save(completion / "result.json", result)
            return result
        identifiers = [item["id"] for item in chosen]
        if not (completion / "selection_frozen.json").exists():
            for item in chosen:
                expected = item["elapsed_seconds"] / 5
                for seed in (1, 2):
                    for fold in ("primary", "recent"):
                        folder = completion / "validation" / item["id"] / f"seed{seed}" / fold
                        if not (folder / "receipt.json").exists():
                            check_budget(deadline, expected)
                        save(state_path, dict(stage="seed_validation", id=item["id"], seed=seed, fold=fold, utc=now()))
                        fit_one(item["config"], seed, fold, folder, resume=True)
            frames = {fold: ensemble_frames(identifiers, fold, completion) for fold in ("primary", "recent")}
            stability = blend_scores(frames)
            for fold, frame in frames.items():
                write_parquet(frame, completion / f"{fold}_ensemble.parquet")
            selection = dict(utc=now(), ids=identifiers, configs=[item["config"] for item in chosen],
                seeds=[0, 1, 2], equal_weights=True, **stability,
                primary_ensemble_sha256=sha(completion / "primary_ensemble.parquet"),
                recent_ensemble_sha256=sha(completion / "recent_ensemble.parquet"),
                shortlist_sha256=sha(completion / "shortlist.json"),
                before_late_audit_target_reads=True, all_history_previously_exposed=True,
                no_reselection_after_latest_audit=True)
            save(completion / "selection_frozen.json", selection)
        selection = read(completion / "selection_frozen.json")
        if not selection["eligible"]:
            result = dict(status="SEED_STABILITY_GATE_FAILED", utc=now(), exported=False,
                          selection=selection, march_may_targets_loaded=False)
            save(completion / "result.json", result)
            return result
        # Audit predictions are fixed before opening its targets. Full-history
        # training is then permitted; those same targets cannot change selection.
        for split in ("latest_cutoff_march_may", "test"):
            path = completion / split / "predictions.parquet"
            if not path.exists():
                check_budget(deadline, 90)
                deployment = deployment_data(split)
                frames = []
                for item in chosen:
                    for seed in (0, 1, 2):
                        folder = completion / split / item["id"] / f"seed{seed}"
                        if not (folder / "receipt.json").exists():
                            check_budget(deadline, item["elapsed_seconds"] / 5 * 1.35)
                        save(state_path, dict(stage="deployment_fit", split=split, id=item["id"], seed=seed, utc=now()))
                        fit_one(item["config"], seed, split, folder, resume=True, deployment=deployment)
                        frames.append(pd.read_parquet(folder / "predictions.parquet"))
                output = frames[0].copy()
                for frame in frames:
                    pd.testing.assert_frame_equal(frame[KEYS], output[KEYS], check_exact=True)
                output["p_component"] = np.mean([frame.p.to_numpy() for frame in frames], axis=0)
                output["p"] = output.p_reference + selection["alpha"] * (output.p_component - output.p_reference)
                write_parquet(output, path)
                save(path.parent / "frozen.json", dict(utc=now(), prediction_sha256=sha(path),
                    selection_sha256=sha(completion / "selection_frozen.json"), before_audit_scoring=True))
            else:
                assert sha(path) == read(path.parent / "frozen.json")["prediction_sha256"]
            if split == "latest_cutoff_march_may" and not (completion / "audit.json").exists():
                labels_path = FINAL / "predictions" / split / "scored_predictions.parquet"
                labels = pd.read_parquet(labels_path, columns=[*KEYS, "y", "smp", "k"])
                scored = source.checked_join(pd.read_parquet(path), labels, ["y", "smp", "k"])
                write_parquet(scored, completion / split / "scored_predictions.parquet")
                save(completion / "audit.json", dict(utc=now(), reference=metric(scored, "p_reference"),
                     candidate=metric(scored), used_for_selection=False, all_history_previously_exposed=True,
                     prediction_sha256=sha(path), labels_source_sha256=sha(labels_path),
                     selection_sha256=sha(completion / "selection_frozen.json")))
        check_budget(deadline, 30)
        exported = export_candidate(pd.read_parquet(completion / "test/predictions.parquet"),
                                    selection, read(completion / "audit.json"))
        result = dict(status="EXPORTED_UNSCORED_CANDIDATE", utc=now(), exported=True,
                      candidate=str(CANDIDATE), manifest_sha256=sha(CANDIDATE / "manifest.json"),
                      audit=exported["audit"], uploaded=False)
        save(completion / "result.json", result)
        return result
    except BudgetFinished as error:
        result = dict(status="BUDGET_EXHAUSTED", utc=now(), exported=False,
                      reason=str(error), state=read(state_path) if state_path.exists() else None,
                      checkpoint_preserved=True)
        save(completion / "budget_stop.json", result)
        return result


def report():
    ranking = ranked_results()
    completion = OUT / "completion"
    finished = read(completion / "result.json") if (completion / "result.json").exists() else None
    search_fits = len(list((OUT / "trials").glob("c*/*/receipt.json")))
    completion_fits = len(list(completion.glob("**/receipt.json")))
    final = dict(updated_utc=now(), completed_trials=len(ranking), planned_trials=256,
        search_real_model_fits=search_fits, completion_real_model_fits=completion_fits,
        total_completed_model_fits=search_fits + completion_fits, eligible_trials=sum(item["eligible"] for item in ranking),
        ranking=ranking, completion=finished, all_history_previously_exposed=True,
        official_best_preserved=sha(source.BEST_ZIP) == source.BEST_SHA,
        official_score_available=False, uploaded=False)
    save(OUT / "report.json", final)
    lines = ["# 10-hour chronological model research", "", f"Updated UTC: {final['updated_utc']}", "",
             f"Completed {len(ranking)}/256 configurations ({search_fits} completed search fits and {completion_fits} completion fits).",
             f"Fixed development gates passed: {final['eligible_trials']} configurations.", "",
             "All historical periods were previously exposed. Overlapping rolling origins are not independent holdouts.",
             "March-May targets are excluded from search and are descriptive only after recipe freeze.",
             "The original officially scored ZIP is preserved; this campaign has no official score or upload.", "",
             "| ID | Mean W ratio | Worst W ratio | Improved folds | Primary alpha | Eligible |",
             "|---|---:|---:|---:|---:|---|"]
    for item in ranking[:20]:
        lines.append(f"| {item['id']} | {item['mean_W_ratio']:.6f} | {item['worst_W_ratio']:.6f} | {item['improved_folds']} | {item['blend']['alpha']:.5f} | {item['eligible']} |")
    lines += ["", "Completion: " + (finished["status"] if finished else "pending/checkpointed")]
    (OUT / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {key: final[key] for key in ("completed_trials", "eligible_trials", "completion", "official_best_preserved")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("prepare")
    trial_parser = commands.add_parser("trial")
    trial_parser.add_argument("--id", required=True, choices=[f"c{i:03d}" for i in range(256)])
    trial_parser.add_argument("--resume", action="store_true", help="Archive interrupted fit folders and retry; completed receipts are verified and reused")
    completion_parser = commands.add_parser("complete")
    completion_parser.add_argument("--deadline-utc", default=DEADLINE)
    commands.add_parser("report")
    args = parser.parse_args()
    with locked():
        if args.command == "prepare":
            result = prepare()
        elif args.command == "trial":
            result = trial(args.id, args.resume)
        elif args.command == "complete":
            result = complete(args.deadline_utc)
        else:
            result = report()
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
