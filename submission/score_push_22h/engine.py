"""Training-only chronological OOF correction of frozen raw solar models.

All old artifacts are read-only. Search stops before March 2025 targets;
the exposed rolling diagnostics are development evidence, not a new holdout.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import zipfile

os.environ.update(OMP_NUM_THREADS="4", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1")
ROOT = Path(__file__).resolve().parents[2]
OLD_CODE = ROOT / "submission/score_push_10h"
sys.path.insert(0, str(OLD_CODE))
spec = importlib.util.spec_from_file_location("frozen_tenhour_engine", OLD_CODE / "engine.py")
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
import lightgbm as lgb
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from threadpoolctl import threadpool_limits
import features as residual

SOURCE, OLD, DATA = old.source, old.OUT, old.DATA
OUT = ROOT / "analysis_outputs/research_22h_20261107"
FINAL = old.FINAL
CANDIDATE = ROOT / "submission/research_22h_candidate_20261107"
FOLDS, KEYS = old.FOLDS, old.KEYS
DEADLINE = "2026-11-07T20:56:33+00:00"
ORIGINS = [str(ts.date()) for ts in pd.date_range("2021-06-01", "2024-03-01", freq="QS-MAR")]
OLD_ORIGINS = {item["origin"]: fold for fold, item in FOLDS.items()}
sha, read, save, now, kst = old.sha, old.read, old.save, old.now, old.kst
metric, blend_scores, write_parquet = old.metric, old.blend_scores, old.write_parquet


@contextmanager
def locked():
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / "engine.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def configs_for_base(index):
    rng = np.random.default_rng(220000 + index)
    rows = []
    for method in ("median", "tree"):
        count = 4 if method == "median" else 60
        for position in range(count):
            mode = ("additive", "multiplicative")[position % 2]
            family = ("core", "season", "age")[position % 3]
            row = dict(method=method, features=family, mode=mode,
                half_life=[None, 180, 365][int(rng.integers(3))],
                shrink=float(rng.choice([.25, .5, .75, 1.])),
                bound=float(rng.choice([.1, .2, .3] if mode == "additive" else [.15, .3, .5])),
                num_leaves=int(rng.choice([3, 7] if family == "age" else [3, 7, 15])),
                min_child_samples=int(rng.choice([200, 500, 1000])),
                n_estimators=int(rng.choice([80, 160, 300])), learning_rate=float(rng.choice([.025, .05])),
                reg_lambda=float(rng.choice([2., 10., 30.])))
            if method == "median":
                row.update(features="core", half_life=None if position < 2 else 365,
                           shrink=.5, bound=.2 if mode == "additive" else .3,
                           num_leaves=0, min_child_samples=0, n_estimators=0, learning_rate=0., reg_lambda=0.)
            fit_keys=("method","features","mode","half_life","num_leaves","min_child_samples","n_estimators","learning_rate","reg_lambda")
            while any(all(row[key]==prior[key] for key in fit_keys) for prior in rows):
                row["reg_lambda"] += .5
            rows.append(row)
    assert len({json.dumps(item, sort_keys=True) for item in rows}) == 64
    return [dict(id=f"n{index * 64 + i:04d}", base_id=f"b{index:02d}", **item) for i, item in enumerate(rows)]


def select_bases():
    ranked = old.ranked_results()
    assert len(ranked) >= 200, "Continuation requires substantial completed first-stage evidence"
    lookup = {item["id"]: item for item in ranked}
    preferred = ["c206", "c003", "c174", "c093", "c185", "c117"]
    station = [item["id"] for item in ranked if item["config"]["features"] == "station"][:4]
    order = preferred[:2] + station[:1] + preferred[2:] + station[1:] + [item["id"] for item in ranked]
    selected, used, signatures = [], set(), set()
    for identifier in order:
        if identifier in used or identifier not in lookup:
            continue
        item = lookup[identifier]
        cfg = item["config"]
        signature = tuple(cfg[key] for key in ("features", "target", "objective", "half_life", "num_leaves"))
        if identifier not in preferred + station and signature in signatures:
            continue
        folder = OLD / "trials" / identifier
        result = read(folder / "result.json")
        files = {}
        for fold in FOLDS:
            receipt = read(folder / fold / "receipt.json")
            old.verify_files(folder / fold, receipt)
            for name in ("model.txt", "predictions.parquet", "transform.json", "receipt.json"):
                path = folder / fold / name
                files[str(path.relative_to(ROOT))] = sha(path)
        files[str((folder / "result.json").relative_to(ROOT))] = sha(folder / "result.json")
        selected.append(dict(id=f"b{len(selected):02d}", source_id=identifier, config=cfg,
            evidence=dict(mean_W_ratio=item["mean_W_ratio"], worst_W_ratio=item["worst_W_ratio"],
                          primary_alpha=item["blend"]["alpha"]), old_files_sha256=files,
            generation_fit_estimate_seconds=max(10., item["elapsed_seconds"] / 5),
            source_result_sha256=sha(folder / "result.json")))
        used.add(identifier)
        signatures.add(signature)
        if len(selected) == 32:
            break
    assert len(selected) == 32
    return selected, len(ranked)


def prepare():
    if (OUT / "protocol.json").exists():
        verify_protocol()
        return read(OUT / "protocol.json")
    old.verify_protocol()
    for name in ("bases.json", "configs.json", "jobs.json"):
        assert not (OUT / name).exists(), "Interrupted preparation requires inspection"
    bases, previously_completed = select_bases()
    configurations = [item for i in range(32) for item in configs_for_base(i)]
    save(OUT / "bases.json", bases)
    save(OUT / "configs.json", configurations)
    jobs = []
    for base in bases:
        estimate = base["generation_fit_estimate_seconds"]
        jobs.append(dict(id=base["id"], argv=[sys.executable, str(Path(__file__)), "crossfit", "--id", base["id"]],
                         estimated_seconds=max(120, int(estimate * 8 * 1.2)), requires_success=[]))
        for config in configurations:
            if config["base_id"] == base["id"]:
                jobs.append(dict(id=config["id"], argv=[sys.executable, str(Path(__file__)), "trial", "--id", config["id"]],
                    estimated_seconds=12 if config["method"] == "median" else 45,
                    requires_success=[base["id"]]))
    save(OUT / "jobs.json", jobs)
    protocol = dict(created_utc=now(), bases_sha256=sha(OUT / "bases.json"),
        configs_sha256=sha(OUT / "configs.json"), jobs_sha256=sha(OUT / "jobs.json"),
        old_protocol_sha256=sha(OLD / "protocol.json"), old_completed_trials_at_design=previously_completed,
        source_sha256={str(path.relative_to(ROOT)): sha(path) for path in
            [Path(__file__), Path(residual.__file__), OLD_CODE / "engine.py", OLD_CODE / "data.py"]},
        data_manifest_sha256=sha(DATA / "manifest.json"), folds=FOLDS, inner_origins=ORIGINS,
        search_calibration_targets_end_kst=str(kst("2024-06-01")), search_score_targets_end_kst=str(kst("2025-03-01")),
        method="Quarterly time-OOF generation residual calibration, never fitted/in-sample generation residuals",
        hypothesis="Cold/snow overprediction and hot-season underprediction; bounded weather/season correction first, low-complexity age interactions second",
        residual_target="(observed all-site y - raw clipped base p) / scale, with signed y preserved",
        scale="capacity*Haurwitz for additive; max(p,.05*capacity*Haurwitz) for multiplicative",
        calibration_weights="normalized SMP*k*scale*target-time-decay / duplicate_count(ts,grp) within outer train subset; exact transformed monetary L1",
        prediction="clip(raw p + shrink*clip(delta,-bound,bound)*scale,0,static_capacity); all-night p=0",
        chronology="Every calibration row satisfies actual generating origin < ts <= outer training cutoff; inner horizon <=366 days",
        reuse="Existing matching-origin generation models/forecasts reused; no first-stage seed0 outer fits repeated",
        selection=dict(mean_W_ratio_vs_raw_below=1., worst_W_ratio_vs_raw_at_most=1.02,
            improved_raw_folds_at_least=3, mean_W_ratio_vs_c000_below=1.,
            blend_alpha_minimum=.02, primary_and_recent_blend_strict_improvement=True,
            rank="mean fivefold W ratio versus c000, then worst ratio versus raw, then id",
            completion_diversity="different base_id preferred; up to three under measured conservative runtime budget",
            alpha="primary-only monetary-L1 optimum, fixed unchanged for recent and deployment",
            seeds="Residual model seeds0,1,2; generation seed0 remains fixed. Median correction is deterministic.",
            ensemble="equal-weight corrected components; primary-only final alpha; both development folds must improve"),
        completion_oof="After recipe freeze, extend quarterly actual OOF generation origins through Sep/Dec2024 and Mar2025; predictions remain after their generating model cutoff. Calibrator uses labels only up to current deployment training cutoff.",
        late_audit="March-May2025 labels excluded until recipe freeze; latest-cutoff predictions frozen before descriptive scoring; no reselection",
        deadline_utc=DEADLINE, search_stop_utc="2026-11-07T19:56:33+00:00", candidates=2048, bases=32,
        all_history_previously_exposed=True, base_selection_used_exposed_outer_results=True,
        chronological_oof_is_not_independent_holdout=True, folds_overlap=True,
        original_best_sha256=SOURCE.BEST_SHA, official_score_available=False, uploaded=False)
    save(OUT / "protocol.json", protocol)
    return protocol


def verify_protocol():
    protocol = read(OUT / "protocol.json")
    for name in ("bases", "configs", "jobs"):
        assert sha(OUT / f"{name}.json") == protocol[f"{name}_sha256"]
    for name, expected in protocol["source_sha256"].items():
        assert sha(ROOT / name) == expected, name
    assert sha(OLD / "protocol.json") == protocol["old_protocol_sha256"]
    assert sha(DATA / "manifest.json") == protocol["data_manifest_sha256"]
    assert sha(SOURCE.BEST_ZIP) == SOURCE.BEST_SHA
    return protocol


def base_by_id(identifier):
    base = next(item for item in read(OUT / "bases.json") if item["id"] == identifier)
    for name, expected in base["old_files_sha256"].items():
        assert sha(ROOT / name) == expected, name
    return base


def restart_partial(folder, resume):
    if folder.exists():
        assert resume, f"Partial artifact preserved at {folder}; inspect and use --resume"
        os.rename(folder, folder.with_name(folder.name + ".interrupted." + str(time.time_ns())))
    folder.mkdir(parents=True)


def verify_receipt(folder):
    receipt = read(folder / "receipt.json")
    old.verify_files(folder, receipt)
    return receipt


def search_tables():
    manifest = read(DATA / "manifest.json")
    for filename in ("search_features.parquet", "search_labels.parquet"):
        assert sha(DATA / filename) == manifest["data_sha256"][filename]
    return pd.read_parquet(DATA / "search_features.parquet"), pd.read_parquet(DATA / "search_labels.parquet")


def known_model(base, origin):
    if origin in OLD_ORIGINS:
        return OLD / "trials" / base["source_id"] / OLD_ORIGINS[origin]
    for folder in (OUT / "bases" / base["id"] / "origins" / origin,
                   OUT / "completion" / "generation" / base["id"] / origin):
        if (folder / "receipt.json").exists() and (folder / "model.txt").exists():
            verify_receipt(folder)
            return folder
    return None


def generation(base, origin, end, folder, tables, resume=False):
    if (folder / "receipt.json").exists():
        receipt = verify_receipt(folder)
        if "origin" not in receipt:
            assert receipt["fold"]==f"inner_{origin}" and receipt["config"]==base["config"] and receipt["seed"]==0
            transform=read(folder/"transform.json")
            receipt.update(origin=origin,end=end,model_reused=False,train_history_days=(kst(origin)-pd.Timestamp(transform["training_start"])).total_seconds()/86400)
            save(folder/"receipt.json",receipt)
        assert receipt["origin"] == origin and receipt["end"] == end
        return receipt
    features, labels = tables
    train = features.loc[features.ts.le(kst(origin))].reset_index(drop=True)
    evaluation = features.loc[features.ts.gt(kst(origin)) & features.ts.le(kst(end))].reset_index(drop=True)
    full = labels.loc[labels.ts.gt(kst(origin)) & labels.ts.le(kst(end))].reset_index(drop=True)
    assert len(train) and len(evaluation) and train.ts.max() <= kst(origin) < evaluation.ts.min()
    model_folder = known_model(base, origin)
    if model_folder is None:
        # The old fitting helper is read-only with respect to its own namespace;
        # every output is explicitly directed into this continuation namespace.
        receipt = old.fit_one(base["config"], 0, f"inner_{origin}", folder, resume=resume,
                             deployment=(train, evaluation, full, origin))
        receipt.update(origin=origin, end=end, model_reused=False, train_history_days=(kst(origin)-train.ts.min()).total_seconds()/86400)
        save(folder / "receipt.json", receipt)
        return receipt
    restart_partial(folder, resume)
    started = time.monotonic()
    transform = read(model_folder / "transform.json")
    assert transform["origin"] == origin
    columns = transform["features"]
    model = lgb.Booster(model_file=str(model_folder / "model.txt"))
    raw = model.predict(evaluation[columns], num_threads=4)
    replay = lgb.Booster(model_file=str(model_folder / "model.txt")).predict(evaluation[columns], num_threads=4)
    np.testing.assert_array_equal(raw, replay)
    predictions = old.assemble(evaluation, full, raw)
    write_parquet(predictions, folder / "predictions.parquet")
    save(folder / "transform.json", transform)
    receipt = dict(status="PASS", utc=now(), origin=origin, end=end, config=base["config"],
        model_reused=True, model_source=str((model_folder / "model.txt").relative_to(ROOT)),
        model_source_sha256=sha(model_folder / "model.txt"), real_model_fits=0,
        elapsed_seconds=time.monotonic()-started, train_history_days=(kst(origin)-train.ts.min()).total_seconds()/86400,
        native_saved_model_replay=True, files_sha256={name:sha(folder/name) for name in ("predictions.parquet","transform.json")})
    save(folder / "receipt.json", receipt)
    return receipt


def pool_from_origins(base, origin_folders, features, cutoff):
    rows = []
    weather_columns = list(dict.fromkeys([*residual.WEATHER, *residual.CALENDAR]))
    for origin, folder in origin_folders:
        receipt = verify_receipt(folder)
        prediction = pd.read_parquet(folder / "predictions.parquet")
        daylight = prediction.loc[~prediction.night & prediction.ts.le(kst(cutoff))].copy()
        daylight = SOURCE.checked_join(daylight, features, [name for name in weather_columns if name not in daylight])
        daylight["model_origin"] = kst(origin)
        daylight["train_history_days"] = receipt["train_history_days"]
        assert daylight.ts.gt(kst(origin)).all() and daylight.ts.le(kst(cutoff)).all()
        assert (daylight.ts-kst(origin)).dt.total_seconds().le(366*86400).all()
        rows.append(daylight)
    pool = pd.concat(rows, ignore_index=True)
    assert not pool.duplicated([*KEYS,"model_origin"]).any()
    return pool


def crossfit(identifier, resume=False):
    verify_protocol()
    old.verify_protocol()
    base = base_by_id(identifier)
    folder = OUT / "bases" / identifier
    if (folder / "result.json").exists():
        result = read(folder / "result.json")
        assert sha(folder / "pool.parquet") == result["pool_sha256"]
        return result
    tables = search_tables()
    records, origin_folders = [], []
    for origin in ORIGINS:
        end = str(min(kst(origin)+pd.Timedelta(days=366), kst("2024-06-01")).date())
        location = folder / "origins" / origin
        records.append(generation(base, origin, end, location, tables, resume))
        origin_folders.append((origin, location))
    pool = pool_from_origins(base, origin_folders, tables[0], "2024-06-01")
    write_parquet(pool, folder / "pool.parquet")
    result = dict(status="PASS", id=identifier, utc=now(), source_id=base["source_id"],
        pool_rows=len(pool), unique_targets=len(pool[KEYS].drop_duplicates()), pool_sha256=sha(folder/"pool.parquet"),
        real_model_fits=sum(item["real_model_fits"] for item in records), origins=records,
        target_start=str(pool.ts.min()), target_end=str(pool.ts.max()),
        train_only_oof=True, march_may_2025_targets_loaded=False)
    save(folder / "result.json", result)
    return result


def application(base, fold):
    full = pd.read_parquet(OLD / "trials" / base["source_id"] / fold / "predictions.parquet")
    evaluation_path=DATA/fold/"evaluation.parquet"
    assert sha(evaluation_path)==read(DATA/"manifest.json")["data_sha256"][f"{fold}/evaluation.parquet"]
    evaluation = pd.read_parquet(evaluation_path)
    daylight = full.loc[~full.night].copy()
    columns = list(dict.fromkeys([*residual.WEATHER,*residual.CALENDAR]))
    daylight = SOURCE.checked_join(daylight, evaluation, [name for name in columns if name not in daylight])
    daylight["model_origin"] = kst(FOLDS[fold]["origin"])
    transform = read(OLD / "trials" / base["source_id"] / fold / "transform.json")
    daylight["train_history_days"] = (kst(FOLDS[fold]["origin"])-pd.Timestamp(transform["training_start"])).total_seconds()/86400
    return daylight, full


def weighted_median(values, weights):
    order = np.argsort(values, kind="stable")
    index = np.searchsorted(np.cumsum(weights[order]), weights.sum()/2, side="left")
    return float(values[order[min(index, len(order)-1)]])


def fit_calibration(config, seed, fold, folder, pool, daylight, full, cutoff, resume=False):
    if (folder / "receipt.json").exists():
        receipt = verify_receipt(folder)
        assert receipt["config"] == config and receipt["seed"] == seed and receipt["fold"] == fold
        return receipt
    restart_partial(folder, resume)
    started = time.monotonic()
    save(folder/"started.json",dict(utc=now(),fold=fold,config=config,seed=seed,stage="calibration",real_model_fit_expected=config["method"]=="tree"))
    train = pool.loc[pool.ts.le(kst(cutoff))].reset_index(drop=True)
    X, target, weight = residual.training(train, config, cutoff)
    prediction_X = residual.engineer(daylight)[list(X)]
    save(folder / "transform.json", dict(features=list(X), training_rows=len(train),
        unique_targets=len(train[KEYS].drop_duplicates()), cutoff=cutoff,
        training_target_start=str(train.ts.min()), training_target_end=str(train.ts.max()),
        generating_origin_start=str(train.model_origin.min()), generating_origin_end=str(train.model_origin.max()),
        every_origin_precedes_target=bool((train.model_origin<train.ts).all()),
        weight_min=float(weight.min()),weight_max=float(weight.max()),weight_mean=float(weight.mean()),
        target_min=float(target.min()),target_max=float(target.max()), training_only=True))
    if config["method"] == "median":
        value = weighted_median(target, weight)
        save(folder / "model.json", dict(value=value, method="weighted_median"))
        delta = np.full(len(daylight), value)
        replay = np.full(len(daylight), read(folder / "model.json")["value"])
        model_name = "model.json"
    else:
        params = {key:config[key] for key in ("num_leaves","min_child_samples","n_estimators","learning_rate","reg_lambda")}
        model = lgb.LGBMRegressor(**params,objective="regression_l1",colsample_bytree=.9,
            subsample=.8,subsample_freq=1,n_jobs=4,verbose=-1,random_state=seed,deterministic=True,force_col_wise=True)
        with threadpool_limits(limits=1,user_api="blas"):
            model.fit(X,target,sample_weight=weight)
            delta = model.predict(prediction_X,num_threads=4)
            model.booster_.save_model(str(folder/"model.txt"))
            replay = lgb.Booster(model_file=str(folder/"model.txt")).predict(prediction_X,num_threads=4)
        model_name = "model.txt"
    np.testing.assert_array_equal(delta,replay)
    changed = daylight[KEYS].copy()
    changed["corrected"] = residual.apply(daylight,delta,config)
    prediction = full.rename(columns={"p":"p_base"}).merge(changed,on=KEYS,how="left",sort=False,validate="one_to_one")
    assert prediction.corrected.isna().equals(prediction.night)
    prediction["p"] = prediction.corrected.fillna(0)
    prediction = prediction.drop(columns="corrected")
    write_parquet(prediction,folder/"predictions.parquet")
    receipt = dict(status="PASS",utc=now(),config=config,seed=seed,fold=fold,
        native_saved_model_replay=True,real_model_fits=int(config["method"]=="tree"),
        elapsed_seconds=time.monotonic()-started, score=metric(prediction) if "y" in prediction else None,
        raw_score=metric(prediction,"p_base") if "y" in prediction else None,
        files_sha256={name:sha(folder/name) for name in (model_name,"transform.json","predictions.parquet")})
    save(folder/"receipt.json",receipt)
    return receipt


def trial(identifier,resume=False):
    verify_protocol()
    config = next(item for item in read(OUT/"configs.json") if item["id"]==identifier)
    base = base_by_id(config["base_id"])
    base_folder = OUT/"bases"/base["id"]
    result = read(base_folder/"result.json")
    assert sha(base_folder/"pool.parquet")==result["pool_sha256"]
    folder = OUT/"trials"/identifier
    if (folder/"result.json").exists():
        for fold in FOLDS:
            verify_receipt(folder/fold)
        return read(folder/"result.json")
    pool = pd.read_parquet(base_folder/"pool.parquet")
    records={}
    for fold in FOLDS:
        daylight,full=application(base,fold)
        records[fold]=fit_calibration(config,0,fold,folder/fold,pool,daylight,full,FOLDS[fold]["origin"],resume)
    frames={fold:pd.read_parquet(folder/fold/"predictions.parquet") for fold in ("primary","recent")}
    blend=blend_scores(frames)
    baseline=read(OLD/"trials/c000/result.json")
    raw_ratios={fold:records[fold]["score"]["W"]/records[fold]["raw_score"]["W"] for fold in FOLDS}
    reference_ratios={fold:records[fold]["score"]["W"]/baseline["folds"][fold]["score"]["W"] for fold in FOLDS}
    robust=float(np.mean(list(raw_ratios.values())))<1 and max(raw_ratios.values())<=1.02 and sum(x<1 for x in raw_ratios.values())>=3
    result=dict(id=identifier,base_id=base["id"],config=config,utc=now(),status="PASS",folds=records,
        blend=blend,raw_ratios=raw_ratios,baseline_ratios=reference_ratios,
        mean_W_ratio=float(np.mean(list(reference_ratios.values()))),worst_raw_W_ratio=max(raw_ratios.values()),
        robust=robust,eligible=robust and blend["eligible"] and np.mean(list(reference_ratios.values()))<1,
        all_history_previously_exposed=True,march_may_targets_loaded=False,protocol_sha256=sha(OUT/"protocol.json"))
    save(folder/"result.json",result)
    return result


def ranking():
    results=[read(path) for path in sorted((OUT/"trials").glob("n*/result.json"))]
    return sorted(results,key=lambda item:(item["mean_W_ratio"],item["worst_raw_W_ratio"],item["id"]))


def remaining(deadline):
    return (datetime.fromisoformat(deadline.replace("Z","+00:00"))-datetime.now(timezone.utc)).total_seconds()


class BudgetFinished(Exception):
    pass


def check_budget(deadline,estimate=60):
    if remaining(deadline)<max(90,estimate*1.7+45):
        raise BudgetFinished("Remaining budget is insufficient for another safely bounded fit")


def deployment_tables(cutoff):
    assert (OUT/"completion/selection_frozen.json").exists()
    limit=kst(cutoff)
    filters=[("ts","<=",limit)]
    features=pq.read_table(SOURCE.FULL_FEATURES,filters=filters).to_pandas()
    site=pq.read_table(SOURCE.SITE_LABELS,columns=["ts","site_id","energy","night"],filters=filters).to_pandas()
    site["grp"]=site.site_id.map(read(SOURCE.ASSIGNMENT))
    labels=site.groupby(KEYS,as_index=False).agg(y=("energy","sum"),night=("night","all"))
    prices=pq.read_table(SOURCE.SMP,columns=["ts","smp","k"],filters=filters).to_pandas()
    labels=labels.merge(prices,on="ts",validate="many_to_one")
    labels=labels.merge(features[KEYS+["capacity_kw"]],on=KEYS,how="left",validate="one_to_one")
    labels["static_capacity"]=labels.grp.map(read(SOURCE.STATIC_CAPACITY))
    assert labels.capacity_kw.isna().equals(labels.night)
    features=SOURCE.checked_join(features,labels,["y","smp","k"])
    return features,labels


def completion_pool(base,cutoff,tables,deadline):
    folders=[]
    for timestamp in pd.date_range("2021-06-01",kst(cutoff).tz_localize(None),freq="QS-MAR"):
        origin=str(timestamp.date())
        if kst(origin)>=kst(cutoff):
            continue
        end=str(min(kst(origin)+pd.Timedelta(days=366),kst(cutoff)).date())
        search_folder=OUT/"bases"/base["id"]/"origins"/origin
        if (search_folder/"receipt.json").exists() and read(search_folder/"receipt.json")["end"]==end:
            folder=search_folder
        else:
            folder=OUT/"completion"/"oof"/cutoff/base["id"]/origin
            if not (folder/"receipt.json").exists():
                check_budget(deadline,base["generation_fit_estimate_seconds"] if known_model(base,origin) is None else 15)
            generation(base,origin,end,folder,tables,resume=True)
            # Fresh inner models are available for the next deployment cutoff.
            if (folder/"model.txt").exists():
                cache=OUT/"completion/generation"/base["id"]/origin
                if not cache.exists():
                    cache.parent.mkdir(parents=True,exist_ok=True)
                    os.symlink(folder,cache,target_is_directory=True)
        folders.append((origin,folder))
    return pool_from_origins(base,folders,tables[0],cutoff)


def completion_application(base,split,cutoff,tables,deadline):
    part="test" if split=="test" else "march_may"
    evaluation=pd.read_parquet(FINAL/"data"/part/"evaluation.parquet")
    coverage=pd.read_parquet(FINAL/"data"/part/"coverage.parquet")
    full=pd.read_parquet(FINAL/"predictions"/split/"predictions.parquet",columns=[*KEYS,"p","static_capacity"]).rename(columns={"p":"p_reference"})
    full=SOURCE.checked_join(full,coverage,["night"])
    folder=OUT/"completion"/split/base["id"] / "generation"
    if not (folder/"receipt.json").exists():
        check_budget(deadline,base["generation_fit_estimate_seconds"]*1.5)
    old.fit_one(base["config"],0,split,folder,resume=True,deployment=(tables[0],evaluation,full,cutoff))
    predicted=pd.read_parquet(folder/"predictions.parquet")
    daylight=predicted.loc[~predicted.night].copy()
    columns=list(dict.fromkeys(["capacity_kw",*residual.WEATHER,*residual.CALENDAR]))
    daylight=SOURCE.checked_join(daylight,evaluation,[name for name in columns if name not in daylight])
    daylight["model_origin"]=kst(cutoff)
    daylight["train_history_days"]=(kst(cutoff)-tables[0].ts.min()).total_seconds()/86400
    # This freshly trained model can generate actual later OOF rows for full refit.
    cache=OUT/"completion/generation"/base["id"]/cutoff
    if not cache.exists():
        cache.parent.mkdir(parents=True,exist_ok=True)
        os.symlink(folder,cache,target_is_directory=True)
    return daylight,predicted


def ensemble(frames):
    result=frames[0].copy()
    for frame in frames:
        pd.testing.assert_frame_equal(result[KEYS],frame[KEYS],check_exact=True)
    result["p"]=np.mean([frame.p.to_numpy() for frame in frames],axis=0)
    return result


def export_candidate(test,selection,audit):
    with zipfile.ZipFile(SOURCE.BEST_ZIP) as archive:
        composition=archive.read("composition.csv")
        original=pd.read_csv(io.BytesIO(archive.read("forecast.csv")))
    original["ts"]=pd.to_datetime(original.ts).dt.tz_convert("Asia/Seoul")
    original=original.rename(columns={"group":"grp"}).sort_values(["grp","ts"]).reset_index(drop=True)
    test=test.sort_values(["grp","ts"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(test[KEYS],original[KEYS],check_exact=True)
    np.testing.assert_array_equal(np.round(test.p_reference,3),original.forecast_kwh)
    assert len(test)==17520 and test.loc[test.night,"p"].eq(0).all()
    assert np.isfinite(test.p).all() and test.p.ge(0).all() and (test.p<=test.static_capacity+1e-9).all()
    if CANDIDATE.exists():
        if (CANDIDATE/"manifest.json").exists():
            manifest=read(CANDIDATE/"manifest.json")
            assert manifest["selection"]==selection
            for name,expected in manifest["files_sha256"].items():
                assert sha(CANDIDATE/name)==expected,name
            return manifest
        os.rename(CANDIDATE,CANDIDATE.with_name(CANDIDATE.name+".interrupted."+str(time.time_ns())))
    CANDIDATE.mkdir()
    (CANDIDATE/"composition.csv").write_bytes(composition)
    pd.DataFrame({"group":test.grp,"ts":test.ts.astype(str),"forecast_kwh":np.round(test.p,3)}).to_csv(CANDIDATE/"forecast.csv",index=False,lineterminator="\r\n")
    with zipfile.ZipFile(CANDIDATE/"submission_files.zip","w",zipfile.ZIP_DEFLATED) as archive:
        for name in ("composition.csv","forecast.csv"):
            archive.write(CANDIDATE/name,arcname=name)
    checked=subprocess.run([sys.executable,str(ROOT/"submission/validate_artifacts.py"),str(CANDIDATE),"--self-check"],capture_output=True,text=True,timeout=90)
    (CANDIDATE/"validation.log").write_text(checked.stdout+checked.stderr)
    assert checked.returncode==0,checked.stdout+checked.stderr
    validation=json.loads(checked.stdout)
    assert validation["rows_above_own_capacity"]==0
    result=dict(utc=now(),selection=selection,audit=audit,validation=validation,
        files_sha256={name:sha(CANDIDATE/name) for name in ("composition.csv","forecast.csv","submission_files.zip")},
        original_best_sha256=SOURCE.BEST_SHA,all_history_previously_exposed=True,uploaded=False,official_score_available=False)
    save(CANDIDATE/"manifest.json",result)
    return result


def complete(deadline):
    deadline=min(datetime.fromisoformat(deadline.replace("Z","+00:00")),datetime.fromisoformat(DEADLINE)).isoformat()
    verify_protocol()
    old.verify_protocol()
    folder=OUT/"completion"
    folder.mkdir(exist_ok=True)
    if (folder/"result.json").exists():
        return read(folder/"result.json")
    try:
        if not (folder/"shortlist.json").exists():
            selected,seen,estimated=[],set(),0.
            for item in ranking():
                if not item["eligible"] or item["base_id"] in seen:
                    continue
                base=base_by_id(item["base_id"])
                # Two full base models, two new inner origins, plus residual
                # refits/replays. Conservative training-growth allowance.
                cost=base["generation_fit_estimate_seconds"]*4*3+360
                if estimated+cost+180>remaining(deadline):
                    continue
                selected.append(dict(id=item["id"],base_id=item["base_id"],config=item["config"],
                                     result_sha256=sha(OUT/"trials"/item["id"]/"result.json")))
                seen.add(item["base_id"])
                estimated+=cost
                if len(selected)==3:
                    break
            save(folder/"shortlist.json",dict(utc=now(),selected=selected,estimated_seconds=estimated,before_late_targets=True))
        selected=read(folder/"shortlist.json")["selected"]
        if not selected:
            result=dict(status="NO_QUALIFYING_RECIPE",utc=now(),exported=False,march_may_targets_loaded=False)
            save(folder/"result.json",result)
            return result
        if not (folder/"selection_frozen.json").exists():
            frames={fold:[] for fold in ("primary","recent")}
            for item in selected:
                base=base_by_id(item["base_id"])
                pool=pd.read_parquet(OUT/"bases"/base["id"]/"pool.parquet")
                for fold in frames:
                    daylight,full=application(base,fold)
                    for seed in (0,1,2):
                        location=OUT/"trials"/item["id"]/fold if seed==0 else folder/"validation"/item["id"]/f"seed{seed}"/fold
                        if seed:
                            check_budget(deadline,30)
                            fit_calibration(item["config"],seed,fold,location,pool,daylight,full,FOLDS[fold]["origin"],resume=True)
                        verify_receipt(location)
                        frames[fold].append(pd.read_parquet(location/"predictions.parquet"))
            combined={fold:ensemble(values) for fold,values in frames.items()}
            stability=blend_scores(combined)
            for fold,frame in combined.items():
                write_parquet(frame,folder/f"{fold}_ensemble.parquet")
            save(folder/"selection_frozen.json",dict(utc=now(),selected=selected,**stability,
                generation_seed=0,residual_seeds=[0,1,2],equal_weights=True,before_late_audit_target_reads=True,
                no_reselection_after_audit=True,all_history_previously_exposed=True,
                ensemble_sha256={fold:sha(folder/f"{fold}_ensemble.parquet") for fold in combined}))
        selection=read(folder/"selection_frozen.json")
        if not selection["eligible"]:
            result=dict(status="SEED_STABILITY_GATE_FAILED",utc=now(),exported=False,march_may_targets_loaded=False)
            save(folder/"result.json",result)
            return result
        for split,cutoff in (("latest_cutoff_march_may","2025-03-01"),("test","2025-06-01")):
            destination=folder/split/"predictions.parquet"
            if not destination.exists():
                check_budget(deadline,60)
                tables=deployment_tables(cutoff)
                frames=[]
                for item in selected:
                    base=base_by_id(item["base_id"])
                    pool=completion_pool(base,cutoff,tables,deadline)
                    daylight,full=completion_application(base,split,cutoff,tables,deadline)
                    for seed in (0,1,2):
                        location=folder/split/item["id"]/f"seed{seed}"
                        check_budget(deadline,30)
                        fit_calibration(item["config"],seed,split,location,pool,daylight,full,cutoff,resume=True)
                        frames.append(pd.read_parquet(location/"predictions.parquet"))
                predicted=ensemble(frames)
                predicted["p_component"]=predicted.p
                predicted["p"]=predicted.p_reference+selection["alpha"]*(predicted.p_component-predicted.p_reference)
                write_parquet(predicted,destination)
                save(destination.parent/"frozen.json",dict(utc=now(),predictions_sha256=sha(destination),selection_sha256=sha(folder/"selection_frozen.json")))
            else:
                assert sha(destination)==read(destination.parent/"frozen.json")["predictions_sha256"]
            if split=="latest_cutoff_march_may" and not (folder/"audit.json").exists():
                labels_path=FINAL/"predictions"/split/"scored_predictions.parquet"
                labels=pd.read_parquet(labels_path,columns=[*KEYS,"y","smp","k"])
                scored=SOURCE.checked_join(pd.read_parquet(destination),labels,["y","smp","k"])
                write_parquet(scored,destination.parent/"scored_predictions.parquet")
                save(folder/"audit.json",dict(utc=now(),reference=metric(scored,"p_reference"),candidate=metric(scored),
                    used_for_selection=False,all_history_previously_exposed=True,predictions_sha256=sha(destination),
                    label_source_sha256=sha(labels_path),selection_sha256=sha(folder/"selection_frozen.json")))
        check_budget(deadline,30)
        exported=export_candidate(pd.read_parquet(folder/"test/predictions.parquet"),selection,read(folder/"audit.json"))
        result=dict(status="EXPORTED_UNSCORED_CANDIDATE",utc=now(),exported=True,candidate=str(CANDIDATE),
                    audit=exported["audit"],manifest_sha256=sha(CANDIDATE/"manifest.json"),uploaded=False)
        save(folder/"result.json",result)
        return result
    except BudgetFinished as error:
        result=dict(status="BUDGET_EXHAUSTED",utc=now(),reason=str(error),checkpoint_preserved=True,exported=False)
        save(folder/"budget_stop.json",result)
        return result


def report():
    rows=ranking()
    bases=list((OUT/"bases").glob("b*/result.json"))
    summaries=[dict(id=item["id"],base_id=item["base_id"],mean_W_ratio=item["mean_W_ratio"],
                   worst_raw_W_ratio=item["worst_raw_W_ratio"],eligible=item["eligible"],blend=item["blend"]) for item in rows]
    completed=read(OUT/"completion/result.json") if (OUT/"completion/result.json").exists() else None
    generation_fits=sum(read(path).get("real_model_fits",0) for path in (OUT/"bases").glob("b*/origins/*/receipt.json"))
    calibration_fits=sum(receipt["real_model_fits"] for item in rows for receipt in item["folds"].values())
    result=dict(utc=now(),completed_bases=len(bases),planned_bases=32,completed_trials=len(rows),planned_trials=2048,
        completed_generation_fits=generation_fits,completed_calibration_fits=calibration_fits,
        eligible_trials=sum(item["eligible"] for item in rows),ranking=summaries,completion=completed,
        all_history_previously_exposed=True,official_best_preserved=sha(SOURCE.BEST_ZIP)==SOURCE.BEST_SHA,
        official_score_available=False,uploaded=False)
    save(OUT/"report.json",result)
    lines=["# Chronological OOF residual continuation","",f"Updated UTC: {result['utc']}","",
        f"Completed OOF bases: {len(bases)}/32. Calibration configurations: {len(rows)}/2048. Eligible: {result['eligible_trials']}.","",
        "All historical periods were previously exposed. Raw configurations were selected using those diagnostics. Time-OOF residuals prevent training on a model's own fitted outcomes, but do not create an independent holdout.",
        "Original officially scored ZIP is preserved; no leaderboard upload or new official score.","",
        "| ID | Base | Mean W ratio/c000 | Worst corrected/raw ratio | Primary alpha | Eligible |",
        "|---|---|---:|---:|---:|---|"]
    for item in summaries[:20]:
        lines.append(f"| {item['id']} | {item['base_id']} | {item['mean_W_ratio']:.6f} | {item['worst_raw_W_ratio']:.6f} | {item['blend']['alpha']:.5f} | {item['eligible']} |")
    lines += ["","Completion: "+(completed["status"] if completed else "pending/checkpointed")]
    (OUT/"REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return {key:result[key] for key in ("completed_bases","completed_trials","eligible_trials","completion","official_best_preserved")}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest="command",required=True)
    commands.add_parser("prepare")
    for name in ("crossfit","trial"):
        sub=commands.add_parser(name)
        sub.add_argument("--id",required=True)
        sub.add_argument("--resume",action="store_true")
    completion=commands.add_parser("complete")
    completion.add_argument("--deadline-utc",default=DEADLINE)
    commands.add_parser("report")
    args=parser.parse_args()
    with locked():
        if args.command=="prepare": result=prepare()
        elif args.command=="crossfit": result=crossfit(args.id,args.resume)
        elif args.command=="trial": result=trial(args.id,args.resume)
        elif args.command=="complete": result=complete(args.deadline_utc)
        else: result=report()
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=="__main__":
    main()
