"""Frozen horizon/group-transfer research, with serial resumable fit jobs.

Only the new namespace is writable. Earlier recipes, models, and receipts are
immutable inputs. All development outcomes have already been exposed.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import shutil
import sys
import time

os.environ.update(OMP_NUM_THREADS="4", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1")
ROOT = Path(__file__).resolve().parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


prior_feature = sys.modules.get("features")
sys.modules["features"] = module("frozen_22h_features", ROOT / "submission/score_push_22h/features.py")
legacy = module("frozen_22h_engine", ROOT / "submission/score_push_22h/engine.py")
if prior_feature is None:
    del sys.modules["features"]
else:
    sys.modules["features"] = prior_feature
transfer = module("transfer_23kst_features", Path(__file__).with_name("features.py"))
old, SOURCE = legacy.old, legacy.SOURCE
import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow as pa
from threadpoolctl import threadpool_limits
pa.set_cpu_count(4)
pa.set_io_thread_count(1)

OUT = ROOT / "analysis_outputs/research_23kst_20261108"
CANDIDATE = ROOT / "submission/research_23kst_candidate_20261108"
DEADLINE = "2026-11-08T14:00:00+00:00"
SEARCH_STOP = "2026-11-08T12:00:00+00:00"
KEYS, DATA = old.KEYS, old.DATA
ANNUAL = {key: dict(value, kind="annual", horizon_days=366) for key, value in old.FOLDS.items()}
QUARTER = {"q" + stamp.strftime("%Y%m"): dict(origin=str(stamp.date()),
    end=str((stamp + pd.DateOffset(months=3)).date()), kind="quarter", horizon_days=92)
    for stamp in pd.date_range("2022-06-01", "2024-12-01", freq="QS-MAR")}
FOLDS = {**ANNUAL, **QUARTER}
ORIGINS = [str(ts.date()) for ts in pd.date_range("2021-06-01", "2024-12-01", freq="QS-MAR")]
BASE_IDS = transfer.BASE_IDS
AUDIT = legacy.OUT / "hourly_checks/20261107T125827Z_failed_candidates_science.json"
sha, read, now, kst = old.sha, old.read, old.now, old.kst
metric, parquet = old.metric, old.write_parquet


def plain(value):
    """Strict JSON boundary includes the formerly failing numpy.bool_ path."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    return value


def save(path, value):
    old.save(Path(path), plain(value))


@contextmanager
def locked():
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "engine.lock").open("a+b") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


class BudgetFinished(Exception):
    pass


def guard(deadline=SEARCH_STOP, estimate=30, completion=False):
    remaining = (datetime.fromisoformat(deadline.replace("Z", "+00:00")) - datetime.now(timezone.utc)).total_seconds()
    if remaining < max(90, estimate * 1.5 + 30):
        raise BudgetFinished("TIME_BUDGET_EXHAUSTED")
    if shutil.disk_usage(ROOT).free < (2 if completion else 3) * 1024**3:
        raise BudgetFinished("STORAGE_BUDGET_EXHAUSTED")


def configurations():
    settings = [dict(regularization="small", num_leaves=3, n_estimators=160, learning_rate=.03,
                     min_child_samples=500, reg_lambda=10., anchor_penalty=0.),
                dict(regularization="medium", num_leaves=7, n_estimators=240, learning_rate=.03,
                     min_child_samples=500, reg_lambda=20., anchor_penalty=0.),
                dict(regularization="large", num_leaves=15, n_estimators=320, learning_rate=.025,
                     min_child_samples=1000, reg_lambda=30., anchor_penalty=0.),
                dict(regularization="anchored", num_leaves=7, n_estimators=240, learning_rate=.03,
                     min_child_samples=500, reg_lambda=20., anchor_penalty=.25)]
    rows = []
    # Latin-style order rotates every axis early, with bases round-robin.
    combinations = list(itertools.product(range(2), range(3), range(3), range(4)))
    combinations.sort(key=lambda item: (sum(item), item))
    for feature, weight, group, setting in combinations:
        for base in BASE_IDS:
            rows.append(dict(id=f"r{len(rows):04d}", base_id=base,
                features=("weather_spread", "rich_spread")[feature],
                weighting=("money", "horizon", "horizon_groupseason")[weight],
                group_mix=(0., .5, 1.)[group], mode="additive", shrink=.5, bound=.2,
                **settings[setting]))
    assert len(rows) == 288
    return rows


def prepare():
    if (OUT / "protocol.json").exists():
        return verify_protocol()
    legacy.verify_protocol()
    old.verify_protocol()
    bases = [item for item in read(legacy.OUT / "bases.json") if item["id"] in BASE_IDS]
    audit = read(AUDIT)
    assert len(audit["rows"]) == 12 and all(item["gate_recomputed"] for item in audit["rows"])
    configs = configurations()
    for path in ("bases.json", "configs.json", "jobs.json", "completion_jobs.json", "finalizer_job.json"):
        assert not (OUT / path).exists(), "Interrupted prepare requires inspection"
    save(OUT / "bases.json", bases)
    save(OUT / "configs.json", configs)
    prefix = [sys.executable, str(Path(__file__))]
    jobs = [dict(id="recover", argv=prefix + ["recover"], estimated_seconds=20, requires_success=[])]
    jobs += [dict(id="validate_" + row["id"], argv=prefix + ["validate", "--id", row["id"]],
                  estimated_seconds=60, requires_success=["recover"]) for row in audit["rows"]]
    jobs += [dict(id=base, argv=prefix + ["crossfit", "--id", base], estimated_seconds=300,
                  requires_success=[]) for base in BASE_IDS]
    jobs.append(dict(id="assemble", argv=prefix + ["assemble"], estimated_seconds=120, requires_success=list(BASE_IDS)))
    jobs += [dict(id=cfg["id"], argv=prefix + ["trial", "--id", cfg["id"]],
                  estimated_seconds=180 if cfg["features"] == "weather_spread" else 360,
                  requires_success=["assemble"]) for cfg in configs]
    save(OUT / "jobs.json", jobs)
    save(OUT / "completion_jobs.json", [dict(id="completion", argv=prefix+["complete", "--deadline-utc", DEADLINE],
         estimated_seconds=3600, requires_success=[])])
    save(OUT / "finalizer_job.json", dict(id="report", argv=prefix+["report"], estimated_seconds=30))
    protocol = dict(status="FROZEN", created_utc=now(), deadline_utc=DEADLINE, search_stop_utc=SEARCH_STOP,
        bases_sha256=sha(OUT / "bases.json"), configs_sha256=sha(OUT / "configs.json"), jobs_sha256=sha(OUT / "jobs.json"),
        completion_jobs_sha256=sha(OUT/"completion_jobs.json"), finalizer_job_sha256=sha(OUT/"finalizer_job.json"),
        old_protocol_sha256=sha(legacy.OUT / "protocol.json"), old_data_manifest_sha256=sha(DATA / "manifest.json"),
        source_sha256={str(p.relative_to(ROOT)): sha(p) for p in
            [Path(__file__), Path(transfer.__file__), Path(legacy.__file__), Path(legacy.residual.__file__),
             Path(old.__file__), Path(SOURCE.__file__)]},
        input_audit_path=str(AUDIT.relative_to(ROOT)), input_audit_sha256=sha(AUDIT),
        annual_folds=ANNUAL, quarter_folds=QUARTER, folds=FOLDS, inner_origins=ORIGINS,
        search_seeds=[0, 1, 2], generation_seed=0, candidate_count=288, base_count=4,
        fixed_base_ids=list(BASE_IDS), recovered_ids=[row["id"] for row in audit["rows"]],
        recovered_policy="All12 recovered seed0 summaries and frozen-alpha seeds1/2 checks are DIAGNOSTICS_ONLY; excluded from novel selection",
        target="signed exact all-site (y-raw_p)/(capacity*max(Haurwitz,.05)); no target clipping",
        weights="SMP*k*scale / duplicate_count(ts,grp) recomputed after horizon filter, normalized mean1",
        robust_weighting="horizon_groupseason then equalizes total weights across observed group×meteorological-season cells; deliberately different from monetary L1",
        anchor="anchored arm appends identical X with zero residual target and .25 times original weights; explicit correction penalty",
        horizons="Quarter OOF age<=92days for matched arms; annual<=366days. money arm retains all<=366days",
        group_structure="pooled only, .5pooled+.5separate-group, or separate-group only; no fitted mixture coefficient",
        features="target-free weather/season or rich100, plus four raw same-origin prediction contrasts/spread; constant mask from selected training rows only",
        chronology="Every OOF row: generating origin<target timestamp<=outer training cutoff; same (origin,ts,grp) for all4 cross predictions",
        quarterly_scope="11 disjoint right-closed quarterly windows; annual5 overlap these and each other, evaluated separately",
        new_generation_models="Only Sep/Dec2024 for each4base; all matching prior generation fits reused, prediction extensions are not fits",
        fit_limits=dict(cpu_threads=4, blas_threads=1, parallel_fits=1, search_free_gib=3, completion_free_gib=2),
        selection=dict(quarter_mean_ratio_max=.995, quarter_improved_min=7, quarter_worst_ratio_max=1.02,
            quarter_group_aggregate_ratio_max=1., each_seed_quarter_aggregate_ratio_below=1.,
            annual_mean_ratio_below=1., annual_improved_min=3, annual_worst_ratio_max=1.02,
            primary_alpha_min=.02, primary_and_recent_blend_ratio_max=.9999, blend_group_ratio_max=1.001,
            minimum_complete_seeded_recipes=12, minimum_complete_per_base=3,
            ranking="worst aggregate quarterly group ratio, meanquarterratio, annualmeanratio, mean primary/recent blendratio,id",
            maximum_selected_bases=3, maximum_recipes_per_base=1, seed_weights="equal thirds", base_weights="equal across selected bases",
            ensemble="recompute same gates using equal-weight p AND p_base; each seed checked before seed mean",
            alpha="one primary-only monetaryL1 optimum on3seed component average; recent uses unchanged alpha and is also development selection evidence"),
        all_history_previously_exposed=True, independent_holdout=False, late_targets_for_selection=False,
        late_audit="March-May2025 accessed only after final recipe,weights,alpha and latest predictions frozen; descriptive; no reselection",
        original_best_sha256=SOURCE.BEST_SHA, uploaded=False, official_score_available=False)
    save(OUT / "protocol.json", protocol)
    return protocol


def verify_protocol():
    protocol = read(OUT / "protocol.json")
    for key in ("bases", "configs", "jobs", "completion_jobs", "finalizer_job"):
        assert sha(OUT / f"{key}.json") == protocol[f"{key}_sha256"]
    for path, expected in protocol["source_sha256"].items():
        assert sha(ROOT / path) == expected, path
    assert sha(legacy.OUT / "protocol.json") == protocol["old_protocol_sha256"]
    assert sha(DATA / "manifest.json") == protocol["old_data_manifest_sha256"]
    assert sha(AUDIT) == protocol["input_audit_sha256"]
    assert sha(SOURCE.BEST_ZIP) == protocol["original_best_sha256"]
    return protocol


def base_by_id(identifier):
    value = next(item for item in read(OUT / "bases.json") if item["id"] == identifier)
    assert value == legacy.base_by_id(identifier)
    return value


def receipt(folder):
    value = read(folder / "receipt.json")
    old.verify_files(folder, value)
    if value.get("model_source"):
        assert sha(ROOT / value["model_source"]) == value["model_source_sha256"]
    return value


def pending(folder):
    if folder.exists():
        os.rename(folder, folder.with_name(folder.name + ".interrupted." + str(time.time_ns())))
    folder.mkdir(parents=True)


def recover():
    verify_protocol()
    rows = []
    configs = {item["id"]: item for item in read(legacy.OUT / "configs.json")}
    for audited in read(AUDIT)["rows"]:
        identifier = audited["id"]
        folder = legacy.OUT / "trials" / identifier
        assert not (folder / "result.json").exists()
        assert sha(folder / "result.json.tmp") == audited["temporary_summary_sha256"]
        records = {}
        for fold in ANNUAL:
            assert sha(folder / fold / "receipt.json") == audited["fold_receipt_sha256"][fold]
            records[fold] = receipt(folder / fold)
            assert records[fold]["config"] == configs[identifier]
        result = dict(id=identifier, status="RECOVERED_DIAGNOSTIC", old_status="FAILED_SUMMARY_SERIALIZATION",
            config=configs[identifier], base_id=audited["base_id"], alpha=audited["alpha"],
            folds=records, previous_scientific_gate=True, eligible=False, diagnostics_only=True,
            real_model_fits=0, source_audit_sha256=sha(AUDIT), source_audit_row=audited,
            source_directory=str(folder.relative_to(ROOT)), old_summary_unchanged=True)
        target = OUT / "recovered" / identifier / "result.json"
        if target.exists():
            assert read(target) == plain(result)
        else:
            save(target, result)
        rows.append(identifier)
    result = dict(status="PASS", recovered_ids=rows, real_model_fits=0, diagnostics_only=True)
    save(OUT / "recovered/result.json", result)
    return result


def validate(identifier):
    verify_protocol()
    recovered = read(OUT / "recovered" / identifier / "result.json")
    folder = OUT / "validation" / identifier
    if (folder / "result.json").exists():
        return read(folder / "result.json")
    config, base = recovered["config"], base_by_id(recovered["base_id"])
    pool_path = legacy.OUT / "bases" / base["id"] / "pool.parquet"
    assert sha(pool_path) == read(pool_path.parent / "result.json")["pool_sha256"]
    pool = pd.read_parquet(pool_path)
    scores, records = {}, []
    for fold in ("primary", "recent"):
        daylight, full = legacy.application(base, fold)
        scores[fold] = {}
        for seed in (1, 2):
            target = folder / f"seed{seed}" / fold
            if not (target / "receipt.json").exists():
                guard()
            record = legacy.fit_calibration(config, seed, fold, target, pool, daylight, full,
                                            ANNUAL[fold]["origin"], resume=True)
            frame = pd.read_parquet(target / "predictions.parquet")
            frame["p"] = frame.p_reference + recovered["alpha"] * (frame.p - frame.p_reference)
            scores[fold][str(seed)] = dict(reference=metric(frame, "p_reference"), blend=metric(frame))
            records.append(record)
    result = dict(status="PASS", id=identifier, diagnostics_only=True, eligible=False,
        new_seeds=[1, 2], frozen_alpha=recovered["alpha"], scores=scores,
        real_model_fits=sum(item["real_model_fits"] for item in records),
        source_recovered_sha256=sha(OUT / "recovered" / identifier / "result.json"))
    save(folder / "result.json", result)
    return result


def known_generation(base, origin):
    for location in (OUT / "bases" / base["id"] / "origins" / origin,
                     OUT / "completion/generation" / base["id"] / origin):
        if (location / "receipt.json").exists() and (location / "model.txt").exists():
            receipt(location)
            return location
    return legacy.known_model(base, origin)


def generation(base, origin, end, folder, tables, deadline=SEARCH_STOP, completion=False):
    if (folder / "receipt.json").exists():
        value = receipt(folder)
        if "origin" not in value:
            # Recover a fit whose native model committed before wrapper metadata.
            assert value["config"] == base["config"] and value["seed"] == 0
            assert value["fold"] == "inner_" + origin
            transform = read(folder / "transform.json")
            value.update(origin=origin, end=end, model_reused=False,
                         train_history_days=(kst(origin) - pd.Timestamp(transform["training_start"])).total_seconds()/86400)
            save(folder / "receipt.json", value)
        assert value["origin"] == origin and value["end"] == end
        return value
    guard(deadline, base["generation_fit_estimate_seconds"], completion)
    features, labels = tables
    train = features.loc[features.ts.le(kst(origin))].reset_index(drop=True)
    evaluation = features.loc[features.ts.gt(kst(origin)) & features.ts.le(kst(end))].reset_index(drop=True)
    full = labels.loc[labels.ts.gt(kst(origin)) & labels.ts.le(kst(end))].reset_index(drop=True)
    assert len(train) and len(evaluation) and train.ts.max() <= kst(origin) < evaluation.ts.min()
    model_folder = known_generation(base, origin)
    if model_folder is None:
        value = old.fit_one(base["config"], 0, "inner_" + origin, folder, resume=True,
                            deployment=(train, evaluation, full, origin))
        value.update(origin=origin, end=end, model_reused=False,
                     train_history_days=(kst(origin)-train.ts.min()).total_seconds()/86400)
        save(folder / "receipt.json", value)
        return value
    pending(folder)
    started = time.monotonic()
    transform = read(model_folder / "transform.json")
    assert transform["origin"] == origin
    model_path = model_folder / "model.txt"
    model = lgb.Booster(model_file=str(model_path))
    raw = model.predict(evaluation[transform["features"]], num_threads=4)
    replay = lgb.Booster(model_file=str(model_path)).predict(evaluation[transform["features"]], num_threads=4)
    np.testing.assert_array_equal(raw, replay)
    frame = old.assemble(evaluation, full, raw)
    parquet(frame, folder / "predictions.parquet")
    save(folder / "transform.json", transform)
    value = dict(status="PASS", utc=now(), origin=origin, end=end, config=base["config"], seed=0,
        model_reused=True, model_source=str(model_path.relative_to(ROOT)), model_source_sha256=sha(model_path),
        train_history_days=(kst(origin)-train.ts.min()).total_seconds()/86400, real_model_fits=0,
        native_saved_model_replay=True, elapsed_seconds=time.monotonic()-started,
        files_sha256={name:sha(folder/name) for name in ("predictions.parquet", "transform.json")})
    save(folder / "receipt.json", value)
    return value


def crossfit(identifier):
    verify_protocol()
    old.verify_protocol()
    base = legacy.base_by_id(identifier)
    assert base == base_by_id(identifier)
    folder = OUT / "bases" / identifier
    if (folder / "result.json").exists():
        result = read(folder / "result.json")
        for path, expected in result["origin_receipts_sha256"].items():
            assert sha(ROOT/path) == expected
        return result
    tables = legacy.search_tables()
    origins = []
    for origin in ORIGINS:
        end = str(min(kst(origin)+pd.Timedelta(days=366), kst("2025-03-01")).date())
        origins.append(generation(base, origin, end, folder / "origins" / origin, tables))
    result = dict(status="PASS", id=identifier, source_id=base["source_id"], origins=origins,
        real_model_fits=sum(row["real_model_fits"] for row in origins),
        origin_receipts_sha256={str((folder/"origins"/o/"receipt.json").relative_to(ROOT)):
                                sha(folder/"origins"/o/"receipt.json") for o in ORIGINS})
    save(folder / "result.json", result)
    return result


def combine_raw(origins, location):
    """Return common same-origin predictions; no estimator is fitted here."""
    rows, pins = [], {}
    for origin in origins:
        common = None
        for base in BASE_IDS:
            folder = location(base, origin)
            record = receipt(folder)
            assert record["origin"] == origin
            frame = pd.read_parquet(folder / "predictions.parquet")
            assert frame.ts.gt(kst(origin)).all()
            assert (frame.ts-kst(origin)).dt.total_seconds().le(366*86400).all()
            if common is None:
                common = frame.drop(columns=["p"]).copy()
                common["model_origin"] = kst(origin)
                common["train_history_days"] = record["train_history_days"]
            else:
                pd.testing.assert_frame_equal(common[KEYS], frame[KEYS], check_exact=True)
                for name in ("y", "night", "smp", "k"):
                    if name in common:
                        np.testing.assert_array_equal(common[name], frame[name])
                assert common.train_history_days.eq(record["train_history_days"]).all()
            common[f"cross_{base}"] = frame.p.to_numpy()
            pins[str((folder / "receipt.json").relative_to(ROOT))] = sha(folder / "receipt.json")
            pins[str((folder / "predictions.parquet").relative_to(ROOT))] = sha(folder / "predictions.parquet")
        rows.append(common)
    joined = pd.concat(rows, ignore_index=True)
    assert not joined.duplicated(["model_origin", *KEYS]).any()
    return joined, pins


def assemble():
    verify_protocol()
    folder = OUT / "shared"
    if (folder / "search_data_manifest.json").exists():
        return shared_manifest()
    guard(estimate=90)
    folder.mkdir(exist_ok=True)
    features, _ = legacy.search_tables()
    rich = SOURCE.read(SOURCE.FEATURE_SPEC)["rich"]
    columns = list(dict.fromkeys([*KEYS, "capacity_kw", *rich, *transfer.WEATHER]))
    feature_frame = features[columns]
    parquet(feature_frame, folder / "features.parquet")
    combined, pins = combine_raw(ORIGINS, lambda b,o:OUT/"bases"/b/"origins"/o)
    pool = combined.loc[~combined.night & combined.ts.le(kst("2024-12-01"))].reset_index(drop=True)
    parquet(pool, folder / "pool.parquet")
    files = ["features.parquet", "pool.parquet"]
    metadata = {}
    for fold, item in FOLDS.items():
        frame = combined.loc[combined.model_origin.eq(kst(item["origin"])) &
            combined.ts.gt(kst(item["origin"])) & combined.ts.le(kst(item["end"]))].reset_index(drop=True)
        if fold in ANNUAL:
            labels = pd.read_parquet(DATA/fold/"labels.parquet")
            pd.testing.assert_frame_equal(frame[KEYS], labels[KEYS], check_exact=True)
            for name in ("y", "smp", "k", "night"):
                np.testing.assert_array_equal(frame[name], labels[name])
            if "p_reference" in labels:
                frame["p_reference"] = labels.p_reference.to_numpy()
        assert len(frame) and frame.ts.gt(kst(item["origin"])).all() and frame.ts.le(kst(item["end"])).all()
        name = fold + ".parquet"
        parquet(frame, folder / name)
        files.append(name)
        metadata[fold] = dict(rows=len(frame), first_ts=str(frame.ts.min()), last_ts=str(frame.ts.max()),
                              daylight_rows=int((~frame.night).sum()), **item)
    quarter_keys = pd.concat([pd.read_parquet(folder/(fold+".parquet"), columns=KEYS) for fold in QUARTER])
    assert not quarter_keys.duplicated(KEYS).any()
    manifest = dict(status="PASS", real_model_fits=0, feature_columns=rich, folds=metadata,
        pool_rows=len(pool), unique_pool_targets=len(pool[KEYS].drop_duplicates()),
        target_end=str(pool.ts.max()), score_target_end=str(combined.ts.max()), quarter_keys_disjoint=True,
        files_sha256={name:sha(folder/name) for name in files}, origin_source_sha256=pins,
        feature_source_manifest_sha256=sha(DATA/"manifest.json"), all_history_previously_exposed=True)
    save(folder / "search_data_manifest.json", manifest)
    save(OUT / "assemble/result.json", dict(status="PASS", real_model_fits=0,
        shared_manifest_sha256=sha(folder/"search_data_manifest.json")))
    return manifest


def shared_manifest():
    value = read(OUT / "shared/search_data_manifest.json")
    for name, expected in value["files_sha256"].items():
        assert sha(OUT/"shared"/name) == expected, name
    for name, expected in value["origin_source_sha256"].items():
        assert sha(ROOT/name) == expected, name
    return value


def sidecar(frame, features):
    columns = [name for name in features if name not in frame and name not in KEYS]
    before = frame[KEYS].reset_index(drop=True)
    # OOF pool repeats target keys across origins, while sidecar keys are unique.
    assert not features.duplicated(KEYS).any()
    result = frame.merge(features[KEYS+columns], on=KEYS, how="left", sort=False, validate="many_to_one", indicator=True)
    pd.testing.assert_frame_equal(result[KEYS], before, check_exact=True)
    assert result._merge.eq("both").all()
    return result.drop(columns="_merge")


def base_frame(frame, base):
    result = frame.copy()
    result["p"] = result[f"cross_{base}"].to_numpy()
    return result


def fit_correction(config, seed, fold, folder, pool, application, rich, cutoff, horizon_days,
                   deadline=SEARCH_STOP, completion=False, provenance=None):
    if (folder / "receipt.json").exists():
        value = receipt(folder)
        assert value["config"] == config and value["seed"] == seed and value["fold"] == fold
        return value
    guard(deadline, 90 if config["features"] == "rich_spread" else 40, completion)
    pending(folder)
    started = time.monotonic()
    save(folder / "started.json", dict(utc=now(), config=config, seed=seed, fold=fold, stage="calibration"))
    chosen = pool.loc[pool.ts.le(kst(cutoff))].reset_index(drop=True)
    train, X, y, weight = transfer.training(chosen, config, cutoff, horizon_days, rich)
    daytime = application.loc[~application.night].reset_index(drop=True)
    prediction_X = transfer.engineer(daytime, config, rich)[list(X)]
    hashes = pd.util.hash_pandas_object(train[["model_origin", *KEYS]], index=False).to_numpy()
    transform = dict(features=list(X), cutoff=cutoff, horizon_days=horizon_days,
        training_rows=len(train), unique_targets=len(train[KEYS].drop_duplicates()),
        training_target_start=str(train.ts.min()), training_target_end=str(train.ts.max()),
        generating_origin_start=str(train.model_origin.min()), generating_origin_end=str(train.model_origin.max()),
        chronology_keys_sha256=hashlib.sha256(hashes.tobytes()).hexdigest(),
        every_origin_precedes_target=bool(train.model_origin.lt(train.ts).all()),
        weight_min=float(weight.min()), weight_max=float(weight.max()), weight_mean=float(weight.mean()),
        target_min=float(y.min()), target_max=float(y.max()),
        weight_formula="money*solar_capacity/selected-subset duplicate count; optional equal group-season totals; normalized mean1",
        provenance=provenance or {}, group_mix=config["group_mix"], anchor_penalty=config["anchor_penalty"],
        train_only_feature_mask=True, model_files=[])
    params = {key:config[key] for key in ("num_leaves", "n_estimators", "learning_rate", "min_child_samples", "reg_lambda")}
    params.update(objective="regression_l1", colsample_bytree=.9, subsample=.8, subsample_freq=1,
                  n_jobs=4, verbose=-1, random_state=seed, deterministic=True, force_col_wise=True)
    outputs = {}
    names = (["pooled"] if config["group_mix"] < 1 else []) + (["G1", "G2"] if config["group_mix"] > 0 else [])
    for name in names:
        guard(deadline, 30, completion)
        mask = np.ones(len(train), dtype=bool) if name == "pooled" else train.grp.eq(name).to_numpy()
        xp, yp, wp = X.loc[mask], y[mask], weight[mask]
        xp, yp, wp = transfer.anchored_training(xp, yp, wp, config["anchor_penalty"])
        model = lgb.LGBMRegressor(**params)
        model_name = name + ".txt"
        with threadpool_limits(limits=1, user_api="blas"):
            model.fit(xp, yp, sample_weight=wp)
            value = model.predict(prediction_X, num_threads=4)
            model.booster_.save_model(str(folder/model_name))
            replay = lgb.Booster(model_file=str(folder/model_name)).predict(prediction_X, num_threads=4)
        np.testing.assert_array_equal(value, replay)
        outputs[name] = value
        transform["model_files"].append(model_name)
    delta = transfer.combine_corrections(outputs, daytime.grp, config["group_mix"])
    corrected = transfer.apply(daytime, delta, config)
    result = application.rename(columns={"p":"p_base"}).copy()
    result["p"] = 0.
    result.loc[~result.night, "p"] = corrected
    # Keep prediction artifacts compact; source feature values remain in pinned shared data.
    keep = [*KEYS, "y", "smp", "k", "night", "capacity_kw", "static_capacity", "p_reference", "p_base", "p"]
    result = result[[name for name in keep if name in result]]
    parquet(result, folder / "predictions.parquet")
    save(folder / "transform.json", transform)
    model_files = transform["model_files"]
    value = dict(status="PASS", utc=now(), config=config, seed=seed, fold=fold, model_params=params,
        model_files=model_files, real_model_fits=len(model_files), native_saved_model_replay=True,
        elapsed_seconds=time.monotonic()-started, score=metric(result) if "y" in result else None,
        raw_score=metric(result, "p_base") if "y" in result else None,
        files_sha256={name:sha(folder/name) for name in [*model_files, "transform.json", "predictions.parquet"]})
    save(folder / "receipt.json", value)
    return value


def average(frames):
    result = frames[0].copy()
    for frame in frames[1:]:
        for name in (KEYS + ["y", "smp", "k", "night", "p_reference"]):
            if name in result:
                np.testing.assert_array_equal(result[name], frame[name])
    # Both corrected and uncorrected comparators use identical ensemble weights.
    for name in ("p", "p_base"):
        if name in result:
            result[name] = np.mean([frame[name].to_numpy(dtype=float) for frame in frames], axis=0)
    return result


def summary(frames, folds):
    scores = {fold:dict(score=metric(frames[fold]), raw_score=metric(frames[fold], "p_base")) for fold in folds}
    ratios = {fold:item["score"]["W"]/item["raw_score"]["W"] for fold,item in scores.items()}
    groups = {}
    for group in ("G1", "G2"):
        numerator = denominator = 0.
        for fold in folds:
            part = frames[fold].loc[frames[fold].grp.eq(group)]
            numerator += metric(part)["W"]
            denominator += metric(part, "p_base")["W"]
        groups[group] = numerator / denominator
    return dict(scores=scores, ratios=ratios, mean_ratio=float(np.mean(list(ratios.values()))),
        worst_ratio=max(ratios.values()), improved_folds=sum(value<1 for value in ratios.values()),
        aggregate_ratio=sum(row["score"]["W"] for row in scores.values()) /
                        sum(row["raw_score"]["W"] for row in scores.values()),
        group_aggregate_ratios=groups)


def blend(frames, fixed_alpha=None):
    alpha = old.alpha_optimum(frames["primary"]) if fixed_alpha is None else float(fixed_alpha)
    scores, ratios, groups = {}, {}, {}
    for fold in ("primary", "recent"):
        frame = frames[fold].copy()
        frame["p"] = frame.p_reference + alpha * (frame.p - frame.p_reference)
        scores[fold] = dict(reference=metric(frame, "p_reference"), blend=metric(frame))
        ratios[fold] = scores[fold]["blend"]["W"] / scores[fold]["reference"]["W"]
        groups[fold] = {group:metric(frame.loc[frame.grp.eq(group)])["W"] /
                       metric(frame.loc[frame.grp.eq(group)], "p_reference")["W"] for group in ("G1", "G2")}
    return dict(alpha=alpha, scores=scores, ratios=ratios, group_ratios=groups,
                mean_ratio=float(np.mean(list(ratios.values()))), primary_only_alpha=True,
                recent_is_development_selection=True, recent_unchanged_transfer=True)


def evaluate(seed_frames, fixed_alpha=None):
    frames = {fold:average([seed_frames[seed][fold] for seed in (0,1,2)]) for fold in FOLDS}
    annual, quarter = summary(frames, ANNUAL), summary(frames, QUARTER)
    seed_ratios = {str(seed):summary(seed_frames[seed], QUARTER)["aggregate_ratio"] for seed in (0,1,2)}
    combined = blend(frames, fixed_alpha)
    gates = dict(quarter_mean=quarter["mean_ratio"]<=.995, quarter_improved=quarter["improved_folds"]>=7,
        quarter_worst=quarter["worst_ratio"]<=1.02, quarter_groups=max(quarter["group_aggregate_ratios"].values())<=1.,
        each_seed_quarter=all(value<1. for value in seed_ratios.values()),
        annual_mean=annual["mean_ratio"]<1., annual_improved=annual["improved_folds"]>=3,
        annual_worst=annual["worst_ratio"]<=1.02, alpha=combined["alpha"]>=.02,
        reference_periods=max(combined["ratios"].values())<=.9999,
        reference_groups=max(value for groups in combined["group_ratios"].values() for value in groups.values())<=1.001)
    return dict(folds={**annual["scores"], **quarter["scores"]}, annual_summary=annual, quarter_summary=quarter,
        seed_quarter_aggregate_ratios=seed_ratios, blend=combined, gates=gates,
        eligible=bool(all(gates.values())), all_history_previously_exposed=True,
        independent_holdout=False, annual_and_quarter_metrics_not_pooled=True)


def trial(identifier):
    verify_protocol()
    folder = OUT / "trials" / identifier
    if (folder / "result.json").exists():
        value = read(folder / "result.json")
        for seed in (0,1,2):
            for fold in FOLDS:
                receipt(folder/f"seed{seed}"/fold)
        return value
    guard()
    config = next(row for row in read(OUT/"configs.json") if row["id"] == identifier)
    manifest = shared_manifest()
    features = pd.read_parquet(OUT/"shared/features.parquet")
    pool = sidecar(base_frame(pd.read_parquet(OUT/"shared/pool.parquet"), config["base_id"]), features)
    applications = {fold:sidecar(base_frame(pd.read_parquet(OUT/"shared"/(fold+".parquet")), config["base_id"])
                                 .loc[lambda frame:~frame.night].reset_index(drop=True), features) for fold in FOLDS}
    # Night rows have no weather; add only after preparing daylight sidecars.
    for fold in FOLDS:
        full = base_frame(pd.read_parquet(OUT/"shared"/(fold+".parquet")), config["base_id"])
        applications[fold] = full.merge(applications[fold][KEYS+[name for name in applications[fold] if name not in full]],
                                      on=KEYS, how="left", sort=False, validate="one_to_one")
    records, seed_frames = [], {}
    for seed in (0,1,2):
        seed_frames[seed] = {}
        for fold, item in FOLDS.items():
            location = folder/f"seed{seed}"/fold
            records.append(fit_correction(config, seed, fold, location, pool, applications[fold],
                manifest["feature_columns"], item["origin"], item["horizon_days"],
                provenance=dict(shared_manifest_sha256=sha(OUT/"shared/search_data_manifest.json"),
                                matched_cross_base_ids=list(BASE_IDS))))
            seed_frames[seed][fold] = pd.read_parquet(location/"predictions.parquet")
    result = dict(status="PASS", id=identifier, base_id=config["base_id"], config=config, utc=now(),
        seeds=[0,1,2], completed_seed_folds=48, real_model_fits=sum(r["real_model_fits"] for r in records),
        elapsed_seconds=sum(r["elapsed_seconds"] for r in records), protocol_sha256=sha(OUT/"protocol.json"),
        **evaluate(seed_frames))
    save(folder/"result.json", result)
    return result


def ranking():
    rows = [read(path) for path in sorted((OUT/"trials").glob("r*/result.json"))]
    return sorted(rows, key=lambda item:(max(item["quarter_summary"]["group_aggregate_ratios"].values()),
        item["quarter_summary"]["mean_ratio"], item["annual_summary"]["mean_ratio"], item["blend"]["mean_ratio"], item["id"]))


def coverage(rows):
    counts = {base:sum(item["base_id"]==base for item in rows) for base in BASE_IDS}
    return len(rows)>=12 and min(counts.values())>=3, counts


def completion_pool(cutoff, tables, deadline):
    """Extend all4 OOF components; no fitted/in-sample residual is admitted."""
    limit = kst(cutoff)
    origins = [str(ts.date()) for ts in pd.date_range("2021-06-01", limit.tz_localize(None), freq="QS-MAR") if kst(str(ts.date()))<limit]
    locations = {}
    for base_id in BASE_IDS:
        base = base_by_id(base_id)
        for origin in origins:
            end = str(min(kst(origin)+pd.Timedelta(days=366), limit).date())
            existing = OUT/"bases"/base_id/"origins"/origin
            if (existing/"receipt.json").exists() and read(existing/"receipt.json")["end"] == end:
                folder = existing
            else:
                folder = OUT/"completion/oof"/cutoff/base_id/origin
                generation(base, origin, end, folder, tables, deadline, True)
                if (folder/"model.txt").exists():
                    cache = OUT/"completion/generation"/base_id/origin
                    if not cache.exists():
                        cache.parent.mkdir(parents=True, exist_ok=True)
                        os.symlink(folder, cache, target_is_directory=True)
            locations[(base_id,origin)] = folder
    frame, pins = combine_raw(origins, lambda b,o:locations[(b,o)])
    assert frame.ts.le(limit).all() and frame.model_origin.lt(frame.ts).all()
    frame = frame.loc[~frame.night].reset_index(drop=True)
    rich = SOURCE.read(SOURCE.FEATURE_SPEC)["rich"]
    columns = list(dict.fromkeys([*KEYS, "capacity_kw", *rich, *transfer.WEATHER]))
    frame = sidecar(frame, tables[0][columns])
    return frame, pins


def deployment_application(split, cutoff, tables, deadline):
    part = "test" if split == "test" else "march_may"
    evaluation = pd.read_parquet(old.FINAL/"data"/part/"evaluation.parquet")
    coverage = pd.read_parquet(old.FINAL/"data"/part/"coverage.parquet")
    full = pd.read_parquet(old.FINAL/"predictions"/split/"predictions.parquet",
                          columns=[*KEYS,"p","static_capacity"]).rename(columns={"p":"p_reference"})
    full = SOURCE.checked_join(full, coverage, ["night"])
    common, pins = None, {}
    for base_id in BASE_IDS:
        base = base_by_id(base_id)
        folder = OUT/"completion"/split/"generation"/base_id
        if not (folder/"receipt.json").exists():
            guard(deadline, base["generation_fit_estimate_seconds"]*2, True)
            # A same-cutoff search/OOF model can be used for another horizon.
            known = known_generation(base, cutoff)
            if known is None:
                old.fit_one(base["config"], 0, split, folder, resume=True,
                            deployment=(tables[0], evaluation, full, cutoff))
            else:
                pending(folder)
                transform = read(known/"transform.json")
                raw = lgb.Booster(model_file=str(known/"model.txt")).predict(evaluation[transform["features"]], num_threads=4)
                replay = lgb.Booster(model_file=str(known/"model.txt")).predict(evaluation[transform["features"]], num_threads=4)
                np.testing.assert_array_equal(raw, replay)
                predicted = old.assemble(evaluation, full, raw)
                parquet(predicted, folder/"predictions.parquet")
                save(folder/"transform.json", transform)
                save(folder/"receipt.json", dict(status="PASS", real_model_fits=0, config=base["config"], seed=0,
                    model_source=str((known/"model.txt").relative_to(ROOT)), model_source_sha256=sha(known/"model.txt"),
                    native_saved_model_replay=True, files_sha256={name:sha(folder/name) for name in ("predictions.parquet","transform.json")}))
        record = receipt(folder)
        predicted = pd.read_parquet(folder/"predictions.parquet")
        if common is None:
            common = predicted.drop(columns="p").copy()
            common["model_origin"] = kst(cutoff)
            common["train_history_days"] = (kst(cutoff)-tables[0].ts.min()).total_seconds()/86400
        else:
            pd.testing.assert_frame_equal(common[KEYS], predicted[KEYS], check_exact=True)
        common[f"cross_{base_id}"] = predicted.p.to_numpy()
        pins[str((folder/"receipt.json").relative_to(ROOT))] = sha(folder/"receipt.json")
        if (folder/"model.txt").exists():
            cache = OUT/"completion/generation"/base_id/cutoff
            if not cache.exists():
                cache.parent.mkdir(parents=True, exist_ok=True)
                os.symlink(folder, cache, target_is_directory=True)
    rich = SOURCE.read(SOURCE.FEATURE_SPEC)["rich"]
    columns = list(dict.fromkeys([*KEYS, "capacity_kw", *rich, *transfer.WEATHER]))
    day = sidecar(common.loc[~common.night].reset_index(drop=True), evaluation[columns])
    common = common.merge(day[KEYS+[name for name in day if name not in common]], on=KEYS,
                          how="left", sort=False, validate="one_to_one")
    return common, pins


def deployment_tables(cutoff):
    import pyarrow.parquet as pq
    assert (OUT/"completion/selection_frozen.json").exists()
    limit, filters = kst(cutoff), [("ts", "<=", kst(cutoff))]
    features = pq.read_table(SOURCE.FULL_FEATURES, filters=filters).to_pandas()
    site = pq.read_table(SOURCE.SITE_LABELS, columns=["ts","site_id","energy","night"], filters=filters).to_pandas()
    site["grp"] = site.site_id.map(read(SOURCE.ASSIGNMENT))
    labels = site.groupby(KEYS, as_index=False).agg(y=("energy","sum"), night=("night","all"))
    prices = pq.read_table(SOURCE.SMP, columns=["ts","smp","k"], filters=filters).to_pandas()
    labels = labels.merge(prices, on="ts", validate="many_to_one")
    labels = labels.merge(features[KEYS+["capacity_kw"]], on=KEYS, how="left", validate="one_to_one")
    labels["static_capacity"] = labels.grp.map(read(SOURCE.STATIC_CAPACITY))
    assert labels.capacity_kw.isna().equals(labels.night) and labels.ts.le(limit).all()
    features = SOURCE.checked_join(features, labels, ["y","smp","k"])
    return features, labels


def export_candidate(test, selection, audit):
    # Only redirects an in-memory output parameter of the immutable helper.
    # The old source and every old artifact remain byte-for-byte unchanged.
    previous = legacy.CANDIDATE
    try:
        legacy.CANDIDATE = CANDIDATE
        return legacy.export_candidate(test, selection, audit)
    finally:
        legacy.CANDIDATE = previous


def complete(deadline=DEADLINE):
    deadline = min(datetime.fromisoformat(deadline.replace("Z","+00:00")),
                   datetime.fromisoformat(DEADLINE)).isoformat()
    verify_protocol()
    old.verify_protocol()
    folder = OUT/"completion"
    folder.mkdir(exist_ok=True)
    if (folder/"result.json").exists():
        return read(folder/"result.json")
    try:
        if not (folder/"shortlist.json").exists():
            rows = ranking()
            sufficient, counts = coverage(rows)
            selected, seen = [], set()
            if sufficient:
                for row in rows:
                    if row["eligible"] and row["base_id"] not in seen:
                        selected.append(dict(id=row["id"], base_id=row["base_id"], config=row["config"],
                            result_sha256=sha(OUT/"trials"/row["id"]/"result.json")))
                        seen.add(row["base_id"])
                        if len(selected)==3:
                            break
            save(folder/"shortlist.json", dict(utc=now(), selected=selected,
                completed_recipes=len(rows), completed_per_base=counts, minimum_coverage_passed=sufficient,
                before_late_targets=True, recovered_diagnostics_excluded=True))
        shortlist = read(folder/"shortlist.json")
        selected = shortlist["selected"]
        if not selected:
            result = dict(status="NO_QUALIFYING_RECIPE" if shortlist["minimum_coverage_passed"] else "INSUFFICIENT_COMPLETED_COVERAGE",
                          utc=now(), exported=False, march_may_targets_loaded=False)
            save(folder/"result.json", result)
            return result
        if not (folder/"selection_frozen.json").exists():
            seed_frames = {seed:{} for seed in (0,1,2)}
            for seed in seed_frames:
                for fold in FOLDS:
                    parts = []
                    for item in selected:
                        assert sha(OUT/"trials"/item["id"]/"result.json")==item["result_sha256"]
                        location = OUT/"trials"/item["id"]/f"seed{seed}"/fold
                        receipt(location)
                        parts.append(pd.read_parquet(location/"predictions.parquet"))
                    seed_frames[seed][fold] = average(parts)
            evidence = evaluate(seed_frames)
            selection = dict(utc=now(), selected=selected, alpha=evidence["blend"]["alpha"],
                eligible=evidence["eligible"], evidence=evidence, seed_weights={str(seed):1/3 for seed in (0,1,2)},
                base_weights={item["base_id"]:1/len(selected) for item in selected},
                protocol_sha256=sha(OUT/"protocol.json"), before_late_targets=True,
                primary_only_alpha=True, recent_used_for_development_selection=True)
            save(folder/"selection_frozen.json", selection)
        selection = read(folder/"selection_frozen.json")
        if not selection["eligible"]:
            result = dict(status="ENSEMBLE_GATE_FAILED", utc=now(), exported=False, march_may_targets_loaded=False)
            save(folder/"result.json", result)
            return result
        rich = SOURCE.read(SOURCE.FEATURE_SPEC)["rich"]
        for split, cutoff in (("latest_cutoff_march_may","2025-03-01"), ("test","2025-06-01")):
            destination = folder/split/"predictions.parquet"
            if not destination.exists():
                guard(deadline, 120, True)
                tables = deployment_tables(cutoff)
                pool, pool_pins = completion_pool(cutoff, tables, deadline)
                application, application_pins = deployment_application(split, cutoff, tables, deadline)
                parts = []
                for item in selected:
                    config = item["config"]
                    training_pool = base_frame(pool, item["base_id"])
                    full = base_frame(application, item["base_id"])
                    for seed in (0,1,2):
                        target = folder/split/item["id"]/f"seed{seed}"
                        fit_correction(config, seed, split, target, training_pool, full, rich, cutoff, 366,
                            deadline, True, provenance=dict(oof_source_sha256=pool_pins, application_source_sha256=application_pins,
                            selection_sha256=sha(folder/"selection_frozen.json"), matched_cross_base_ids=list(BASE_IDS)))
                        parts.append(pd.read_parquet(target/"predictions.parquet"))
                predicted = average(parts)
                predicted["p_component"] = predicted.p.to_numpy()
                predicted["p"] = predicted.p_reference + selection["alpha"]*(predicted.p_component-predicted.p_reference)
                destination.parent.mkdir(parents=True, exist_ok=True)
                parquet(predicted, destination)
                save(destination.parent/"frozen.json", dict(utc=now(), predictions_sha256=sha(destination),
                     selection_sha256=sha(folder/"selection_frozen.json"), before_late_scoring=True))
            else:
                assert sha(destination)==read(destination.parent/"frozen.json")["predictions_sha256"]
            if split=="latest_cutoff_march_may" and not (folder/"audit.json").exists():
                labels_path = old.FINAL/"predictions"/split/"scored_predictions.parquet"
                assert sha(labels_path)==read(old.OUT/"protocol.json")["late_audit_labels_hash_only_sha256"]
                labels = pd.read_parquet(labels_path, columns=[*KEYS,"y","smp","k"])
                scored = SOURCE.checked_join(pd.read_parquet(destination), labels, ["y","smp","k"])
                parquet(scored, destination.parent/"scored_predictions.parquet")
                save(folder/"audit.json", dict(utc=now(), reference=metric(scored,"p_reference"), candidate=metric(scored),
                    used_for_selection=False, all_history_previously_exposed=True, independent_holdout=False,
                    predictions_sha256=sha(destination), label_source_sha256=sha(labels_path),
                    selection_sha256=sha(folder/"selection_frozen.json")))
        guard(deadline, 30, True)
        exported = export_candidate(pd.read_parquet(folder/"test/predictions.parquet"), selection, read(folder/"audit.json"))
        result = dict(status="EXPORTED_UNSCORED_CANDIDATE", utc=now(), exported=True,
            candidate=str(CANDIDATE), audit=exported["audit"], manifest_sha256=sha(CANDIDATE/"manifest.json"), uploaded=False)
        save(folder/"result.json", result)
        return result
    except BudgetFinished as error:
        result = dict(status=str(error), utc=now(), checkpoint_preserved=True, exported=False,
                      free_bytes=shutil.disk_usage(ROOT).free)
        save(folder/"budget_stop.json", result)
        return result


def report():
    rows = ranking()
    completion = read(OUT/"completion/result.json") if (OUT/"completion/result.json").exists() else None
    value = dict(utc=now(), planned_recipes=288, completed_recipes=len(rows),
        eligible_recipes=sum(bool(item["eligible"]) for item in rows),
        completed_per_base={base:sum(row["base_id"]==base for row in rows) for base in BASE_IDS},
        recovered_diagnostic_count=len(list((OUT/"recovered").glob("n*/result.json"))),
        new_seed_diagnostic_count=len(list((OUT/"validation").glob("n*/result.json"))),
        completed_recipe_model_fits=sum(row["real_model_fits"] for row in rows),
        ranking=[dict(id=row["id"], base_id=row["base_id"], eligible=row["eligible"],
            quarter_mean_ratio=row["quarter_summary"]["mean_ratio"],
            quarter_group_ratios=row["quarter_summary"]["group_aggregate_ratios"],
            annual_mean_ratio=row["annual_summary"]["mean_ratio"], blend=row["blend"]) for row in rows],
        completion=completion, budget_stop=read(OUT/"budget_stop.json") if (OUT/"budget_stop.json").exists() else None,
        completion_budget_stop=read(OUT/"completion/budget_stop.json") if (OUT/"completion/budget_stop.json").exists() else None,
        all_history_previously_exposed=True, independent_holdout=False,
        original_best_preserved=sha(SOURCE.BEST_ZIP)==SOURCE.BEST_SHA, uploaded=False)
    save(OUT/"report.json", value)
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["prepare","recover","validate","crossfit","assemble","trial","complete","report"])
    parser.add_argument("--id")
    parser.add_argument("--deadline", "--deadline-utc", dest="deadline", default=DEADLINE)
    parser.add_argument("--resume", action="store_true", help="Compatibility; only valid receipt-backed checkpoints are reused")
    args = parser.parse_args()
    try:
        with locked():
            if args.command in ("validate","crossfit","trial"):
                result = globals()[args.command](args.id)
            elif args.command == "complete":
                result = complete(args.deadline)
            else:
                result = globals()[args.command]()
        print(json.dumps(plain({key:value for key,value in result.items() if key in
              ("status","id","eligible","completed_recipes","eligible_recipes","real_model_fits","exported")}), allow_nan=False))
    except BudgetFinished as error:
        save(OUT/"budget_stop.json", dict(status=str(error), utc=now(), stage=args.command, id=args.id,
             checkpoint_preserved=True, free_bytes=shutil.disk_usage(ROOT).free))
        raise SystemExit(75)


if __name__ == "__main__":
    main()
