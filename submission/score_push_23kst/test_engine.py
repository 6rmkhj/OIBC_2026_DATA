"""Zero-fit tests for the protocol's transformations, gates and serialization."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

SPEC = importlib.util.spec_from_file_location("research23_engine_test", Path(__file__).with_name("engine.py"))
engine = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(engine)
F = engine.transfer


def sample():
    dates = pd.date_range("2023-04-01 12:00", periods=8, freq="30D", tz="Asia/Seoul")
    rows = []
    for index, ts in enumerate(dates):
        for group in ("G1", "G2"):
            for age in (20, 140):
                row = dict(ts=ts, grp=group, model_origin=ts-pd.Timedelta(days=age),
                    train_history_days=400., capacity_kw=100., static_capacity=120.,
                    p=30.+index, y=-1. if index==0 else 29.+index, smp=2.+index, k=1.5, night=False)
                row.update({name:float(index) for name in F.WEATHER})
                row.update(cosz=.5, grp_code=0. if group=="G1" else 1.)
                row.update({f"cross_{base}":float(29+index+j) for j,base in enumerate(F.BASE_IDS)})
                rows.append(row)
    return pd.DataFrame(rows)


def config(**changes):
    return dict(engine.configurations()[0], **changes)


def scored(value=.99, raw=.8, reference=.9):
    return pd.DataFrame(dict(ts=pd.date_range("2023-01-01", periods=4, freq="h", tz="Asia/Seoul"),
        grp=["G1","G2","G1","G2"], y=[100.,100.,100.,100.], smp=[1.,2.,3.,4.], k=[1.,1.,1.,1.],
        night=[False]*4, p=[100*value]*4, p_base=[100*raw]*4, p_reference=[100*reference]*4))


class FeatureTests(unittest.TestCase):
    def test_negative_targets_and_exact_l1_identity(self):
        frame = sample()
        train, X, y, weight = F.training(frame, config(), "2024-01-01", 92, ["cosz","wa_temp"])
        self.assertLess(y.min(), 0)
        units = F.scale(train)
        dup = train.groupby(["ts","grp"]).ts.transform("size").to_numpy()
        original = train.smp.to_numpy()*train.k.to_numpy()*units/dup
        delta = np.linspace(-.1,.1,len(train))
        left = np.sum(weight*np.abs(y-delta))*original.mean()
        right = np.sum(train.smp.to_numpy()*train.k.to_numpy()/dup*np.abs(train.y-train.p-units*delta))
        self.assertAlmostEqual(left, right, places=7)
        self.assertTrue(len(X.columns)>0)

    def test_horizon_filter_recomputes_duplicates(self):
        train, _, _, weight = F.training(sample(), config(weighting="horizon"), "2024-01-01", 92, [])
        self.assertEqual(len(train), 16)
        self.assertFalse(train.duplicated(["ts","grp"]).any())
        expected = train.smp.to_numpy()*train.k.to_numpy()*F.scale(train)
        np.testing.assert_allclose(weight, expected/expected.mean())

    def test_group_season_balancing(self):
        train, _, _, weight = F.training(sample(), config(weighting="horizon_groupseason"), "2024-01-01", 92, [])
        season = (F.dates(train.ts).month%12)//3
        group = train.grp.to_numpy()+"_"+season.astype(str)
        totals = pd.Series(weight).groupby(group).sum().to_numpy()
        np.testing.assert_allclose(totals, np.full_like(totals, totals[0]))

    def test_features_ignore_targets_prices(self):
        frame = sample()
        original = F.engineer(frame, config(), [])
        frame[["y","smp","k"]] = 999999.
        pd.testing.assert_frame_equal(original, F.engineer(frame, config(), []))

    def test_rich_excludes_targets(self):
        with self.assertRaises(AssertionError):
            F.engineer(sample(), config(features="rich_spread"), ["y"])

    def test_future_target_and_non_oof_rejected(self):
        with self.assertRaises(AssertionError):
            F.training(sample(), config(), "2023-05-01", 92, [])
        frame = sample()
        frame.loc[0,"model_origin"] = frame.loc[0,"ts"]
        with self.assertRaises(AssertionError):
            F.training(frame, config(), "2024-01-01", 92, [])

    def test_application_inverse_and_clipping(self):
        frame = sample()
        delta = np.full(len(frame), .1)
        predicted = F.apply(frame, delta, config())
        np.testing.assert_allclose(predicted, frame.p+.5*.1*F.scale(frame))
        frame.loc[0,"night"] = True
        self.assertEqual(F.apply(frame, delta, config())[0], 0.)
        predicted = F.apply(frame, np.full(len(frame), 1000.), config())
        self.assertTrue((predicted<=frame.static_capacity).all())

    def test_anchor_penalty_and_group_formula(self):
        X = pd.DataFrame(dict(x=[1.,2.]))
        target, weight = np.array([-.2,.3]), np.array([2.,4.])
        xp, yp, wp = F.anchored_training(X,target,weight,.25)
        np.testing.assert_array_equal(yp,[-.2,.3,0.,0.])
        np.testing.assert_array_equal(wp,[2.,4.,.5,1.])
        self.assertEqual(len(xp),4)
        outputs = dict(pooled=np.array([1.,2.]),G1=np.array([3.,4.]),G2=np.array([5.,6.]))
        np.testing.assert_array_equal(F.combine_corrections(outputs,["G1","G2"],.5),[2.,4.])
        np.testing.assert_array_equal(F.combine_corrections(outputs,["G1","G2"],1.),[3.,6.])
        np.testing.assert_array_equal(F.combine_corrections(outputs,["G1","G2"],0.),[1.,2.])


class EngineTests(unittest.TestCase):
    def test_factorial_unique_round_robin(self):
        rows = engine.configurations()
        self.assertEqual(len(rows), 288)
        self.assertEqual(len({json.dumps({k:v for k,v in row.items() if k!="id"},sort_keys=True) for row in rows}), 288)
        for start in range(0,288,4):
            self.assertEqual([row["base_id"] for row in rows[start:start+4]], list(F.BASE_IDS))

    def test_quarters_disjoint_and_pre_march(self):
        parts = list(engine.QUARTER.values())
        self.assertEqual(len(parts), 11)
        self.assertEqual(parts[-1]["end"], "2025-03-01")
        for prior, following in zip(parts,parts[1:]):
            self.assertEqual(prior["end"], following["origin"])

    def test_average_both_raw_and_corrected(self):
        a,b = scored(.99,.8), scored(.95,.6)
        combined = engine.average([a,b])
        np.testing.assert_array_equal(combined.p, np.full(4,97.))
        np.testing.assert_array_equal(combined.p_base, np.full(4,70.))
        b.loc[0,"y"] = 200
        with self.assertRaises(AssertionError):
            engine.average([a,b])

    def test_true_gate_strict_json_numpy_bool(self):
        seeds = {seed:{fold:scored() for fold in engine.FOLDS} for seed in (0,1,2)}
        result = engine.evaluate(seeds)
        self.assertIs(result["eligible"], True)
        serialized = json.dumps(engine.plain(dict(result, old_failure=True and True and np.mean([.9,.95])<1)), allow_nan=False)
        self.assertTrue(json.loads(serialized)["old_failure"])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"receipt.json"
            engine.save(path, dict(eligible=np.bool_(True), count=np.int64(2)))
            self.assertEqual(json.loads(path.read_text()), dict(eligible=True,count=2))
            with self.assertRaises(ValueError):
                engine.save(path, dict(invalid=np.float64(np.nan)))

    def test_bad_group_and_bad_seed_fail_gates(self):
        seeds = {seed:{fold:scored() for fold in engine.FOLDS} for seed in (0,1,2)}
        for fold in engine.QUARTER:
            seeds[2][fold]["p"] = 0.
        result = engine.evaluate(seeds)
        self.assertFalse(result["gates"]["each_seed_quarter"])
        self.assertFalse(result["eligible"])

    def test_primary_alpha_unchanged_recent(self):
        a,b = scored(), scored()
        b["y"] = 200.
        alpha = engine.blend(dict(primary=a,recent=b))["alpha"]
        self.assertEqual(alpha, engine.old.alpha_optimum(a))

    def test_storage_budget_precedes_fit(self):
        with patch.object(engine.shutil,"disk_usage",return_value=type("Disk",(),{"free":1024})()):
            with self.assertRaisesRegex(engine.BudgetFinished,"STORAGE"):
                engine.guard("2099-01-01T00:00:00+00:00")

    def test_raw_spread_alignment(self):
        frame = sample()
        engineered = F.engineer(frame, config(), [])
        matrix = frame[[f"cross_{b}" for b in F.BASE_IDS]].to_numpy()
        np.testing.assert_allclose(engineered.cross_spread, matrix.std(axis=1)/F.scale(frame))

    def test_minimum_complete_coverage(self):
        rows = [dict(base_id=base) for base in F.BASE_IDS for _ in range(3)]
        self.assertTrue(engine.coverage(rows)[0])
        self.assertFalse(engine.coverage(rows[:-1])[0])
        self.assertFalse(engine.coverage([dict(base_id="b00")]*12)[0])

    def test_storage_marker_never_commits_trial_success(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(engine,"OUT",Path(directory)), \
             patch.object(engine.sys,"argv",["engine.py","trial","--id","r0000"]), \
             patch.object(engine,"trial",side_effect=engine.BudgetFinished("STORAGE_BUDGET_EXHAUSTED")):
            with self.assertRaises(SystemExit) as stopped:
                engine.main()
            self.assertEqual(stopped.exception.code,75)
            marker = json.loads((Path(directory)/"budget_stop.json").read_text())
            self.assertEqual(marker["status"],"STORAGE_BUDGET_EXHAUSTED")
            self.assertEqual(marker["id"],"r0000")
            self.assertFalse((Path(directory)/"trials/r0000/result.json").exists())


if __name__ == "__main__":
    unittest.main()
