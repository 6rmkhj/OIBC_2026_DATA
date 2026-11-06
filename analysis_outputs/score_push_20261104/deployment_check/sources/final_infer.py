"""Fixed member fitting, serialization replay and nested mixture."""
from wave_common import OUT, save_json, receipt
from final_build import DEST
from site_features import normalizer
from refine_models import normalized_fit
from learner_models import fit as neural_fit
from profile_models import fit as station_fit
import json
import time
import gc
import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd

ALPHA = .7642694482340047
WEIGHTS = [.380705173762783, .41926809371483975, .2000267325223772]
STATION = .2808471620447986


def locations(final: bool) -> dict[str, list]:
    if final:
        return {name: [DEST / "models" / name / f"seed{s}" for s in range(3)] for name in ("rich", "normalized", "mlp", "station")}
    return {
        "rich": [OUT / "recent/rich_fixed_alpha" / f"pooled_seed{s}.txt" for s in range(3)],
        "normalized": [OUT / "refinement_wave/recent/leaves63_trees400" / f"seed{s}" for s in range(3)],
        "mlp": [OUT / "learner_wave/recent/mlp_cf" / f"seed{s}" for s in range(3)],
        "station": [OUT / "profile_wave/recent/stations_lgb" / f"seed{s}" for s in range(3)],
    }


def inference(frame: pd.DataFrame, names: list[str], final: bool) -> pd.DataFrame:
    result = frame[["ts", "grp"]].copy()
    cap = frame.capacity_kw.to_numpy()
    scale = normalizer(frame.cosz.to_numpy())
    for member, paths in locations(final).items():
        preds = []
        for path in paths:
            selected = names
            if member == "station":
                selected = json.loads((path / "feature_mask.json").read_text())["selected_columns"]
            if member == "mlp":
                transform = joblib.load(path / "input_preprocessing.joblib")
                scaler = joblib.load(path / "target_scaler.joblib")
                model = joblib.load(path / "model.joblib")
                pred = scaler.inverse_transform(model.predict(transform.transform(frame[names])).reshape(-1, 1)).ravel()
            else:
                model = lgb.Booster(model_file=str(path if path.suffix == ".txt" else path / "model.txt"))
                pred = model.predict(frame[selected], num_threads=2)
                if member in ("normalized", "station"):
                    pred = pred * scale
            assert np.isfinite(pred).all()
            preds.append(pred if member == "rich" else pred * cap)
            del model
        if member == "rich":
            total = np.zeros(len(frame))
            for pred in preds:
                total += pred / 3
            result[member] = np.clip(total, 0, None) * cap
        else:
            raw = pd.concat([frame[["ts", "grp"]].assign(p_raw=p) for p in preds]).groupby(["ts", "grp"], as_index=False).p_raw.mean()
            result = result.merge(raw.rename(columns={"p_raw": member}), on=["ts", "grp"], validate="one_to_one")
            result[member] = result[member].clip(lower=0)
        gc.collect()
    assert set(map(tuple, result[["ts", "grp"]].to_numpy())) == set(map(tuple, frame[["ts", "grp"]].to_numpy()))
    assert np.isfinite(result[["rich", "normalized", "mlp", "station"]]).all().all()
    assert result[["rich", "normalized", "mlp", "station"]].ge(0).all().all()
    return result


def compose(base: pd.DataFrame, components: pd.DataFrame) -> pd.DataFrame:
    assert not components.duplicated(["ts", "grp"]).any()
    assert set(map(tuple, components[["ts", "grp"]].to_numpy())) <= set(map(tuple, base[["ts", "grp"]].to_numpy()))
    assert np.isfinite(components[["rich", "normalized", "mlp", "station"]]).all().all()
    assert components[["rich", "normalized", "mlp", "station"]].ge(0).all().all()
    frame = base.merge(components, on=["ts", "grp"], how="left", validate="one_to_one")
    frame[["rich", "normalized", "mlp", "station"]] = frame[["rich", "normalized", "mlp", "station"]].fillna(0.)
    reference = (1-ALPHA)*frame.p_bu + ALPHA*frame.rich
    refined = WEIGHTS[0]*reference + WEIGHTS[1]*frame.normalized + WEIGHTS[2]*frame.mlp
    frame["p_candidate"] = (1-STATION)*refined + STATION*frame.station
    assert np.isfinite(frame.p_candidate).all() and frame.p_candidate.ge(0).all()
    return frame


def fit_all(train: pd.DataFrame, test: pd.DataFrame, names: list[str], profile_names: list[str]) -> None:
    for member, paths in locations(True).items():
        for seed, directory in enumerate(paths):
            if member == "normalized":
                raw = normalized_fit(seed, 63, 400, train, test, names, directory)
            elif member == "mlp":
                raw = neural_fit("mlp_cf", seed, train, test, names, directory)
            elif member == "station":
                raw = station_fit("lgb", seed, train, test, profile_names, directory)
            else:
                directory.mkdir(parents=True, exist_ok=False)
                params = dict(n_estimators=400, learning_rate=.03, num_leaves=31, min_child_samples=50, subsample=.8, subsample_freq=1, colsample_bytree=.8, objective="regression_l1", verbose=-1, n_jobs=2, random_state=None if seed == 0 else seed)
                model = lgb.LGBMRegressor(**params)
                started = time.monotonic()
                model.fit(train[names], train.cf)
                raw = test[["ts", "grp"]].assign(p_raw=model.predict(test[names])*test.capacity_kw.to_numpy())
                raw.to_parquet(directory / "daylight_raw.parquet", index=False)
                model.booster_.save_model(str(directory / "model.txt"))
                save_json(directory / "config.json", {"parameters": params, "features": names, "train_end": str(train.ts.max())})
                receipt(directory / "runtime.json", [time.monotonic()-started])
                del model
            print("FINAL FIT COMPLETE", member, seed, flush=True)
            del raw
            gc.collect()
