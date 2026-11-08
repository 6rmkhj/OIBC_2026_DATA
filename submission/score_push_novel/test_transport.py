"""Meaningful synthetic checks for conservation and convex fitting; no real data."""
import copy
import unittest

import numpy as np
import pandas as pd

import transport


def sample(days=3):
    hours = pd.date_range("2024-01-01 01:00", periods=24*days, freq="h", tz="Asia/Seoul")
    rows = []
    for ts in hours:
        h = (ts-pd.Timedelta(hours=1)).hour
        solar = max(0., np.sin((h-6)*np.pi/12)) if 6 <= h <= 18 else 0.
        for group, amplitude in [("G1", 70.), ("G2", 55.)]:
            shape = 1.-0.55*np.exp(-((h-11)/1.5)**2)
            rows.append(dict(ts=ts, grp=group, p_reference=amplitude*solar*shape,
                             static_capacity=100., night=solar < 1e-12, cosz=solar,
                             wa_cloud=25.+3*h+(0 if group == "G1" else 20.),
                             y=0., smp=1.+h/24., k=1.))
    frame = pd.DataFrame(rows)
    frame.loc[frame.night, "p_reference"] = 0.
    return frame


def mixture(config, metadata, mass=None):
    count = metadata['scenarios_per_context']
    mass = config['budget'] if mass is None else mass
    weights = np.zeros(len(metadata['columns']))
    weights[::count] = mass
    return dict(version=1, config=copy.deepcopy(config), columns=metadata['columns'], coefficients=weights.tolist())


class TestTransport(unittest.TestCase):
    def test_declared_arms(self):
        cfg = transport.configs()
        self.assertEqual([x['id'] for x in cfg], [f't{i:03d}' for i in range(8)]+[f's{i:03d}' for i in range(4)])
        self.assertEqual(len({str(x) for x in cfg}), 12)

    def test_temporal_each_scenario_and_mixture_conserves(self):
        frame = sample().sample(frac=1, random_state=7).reset_index(drop=True)
        day = (frame.ts.dt.tz_localize(None)-pd.Timedelta(hours=1)).dt.normalize()
        for config in transport.configs()[:8]:
            design, metadata = transport.make_design(frame, config)
            predictions = [frame.p_reference.to_numpy()+design[:, j] for j in range(design.shape[1])]
            predictions += [transport.predict(frame, config, mixture(config, metadata))]
            for p in predictions:
                self.assertGreaterEqual(p.min(), -1e-8)
                self.assertLessEqual(np.max(p-frame.static_capacity), 1e-8)
                np.testing.assert_allclose(p[frame.night], 0, atol=1e-8)
                for ix in pd.DataFrame({'day':day, 'grp':frame.grp}).groupby(['day','grp']).indices.values():
                    self.assertAlmostEqual(float(p[ix].sum()), float(frame.p_reference.iloc[ix].sum()), places=7)
            self.assertGreater(np.max(np.abs(design)), 1.)

    def test_zero_reference_and_incomplete_day_identity(self):
        frame = sample(1)
        config = transport.configs()[7]
        empty = frame.iloc[0:0].copy()
        self.assertEqual(transport.make_design(empty, config)[0].shape[0], 0)
        zero = frame.copy(); zero['p_reference'] = 0.
        self.assertFalse(transport.make_design(zero, config)[0].any())
        incomplete = frame[frame.ts != frame.ts.iloc[0]].copy()
        design, meta = transport.make_design(incomplete, config)
        self.assertFalse(design.any())
        self.assertEqual(meta['fallback_incomplete_units'], 2)

    def test_context_shared_for_entire_day_group_and_missing_neutral(self):
        frame = sample(1)
        config = transport.configs()[3]
        design, meta = transport.make_design(frame, config)
        self.assertEqual(meta['context_counts'], [0,0,2])
        self.assertTrue(np.all(design[:, :4] == 0))
        frame.loc[frame.index[10], 'wa_cloud'] = np.nan
        _, meta = transport.make_design(frame, config)
        # Row10 is before daylight; changing it does not affect daylight context.
        self.assertEqual(meta['context_counts'], [0,0,2])
        frame.loc[(frame.grp == 'G1') & ~frame.night, 'wa_cloud'] = np.nan
        design, meta = transport.make_design(frame, config)
        self.assertEqual(meta['context_counts'], [0,1,1])
        self.assertEqual(meta['neutral_missing_context_units'], 1)

    def test_spatial_pair_conservation_bounds_and_budget(self):
        frame = sample().sample(frac=1, random_state=2).reset_index(drop=True)
        for config in transport.configs()[8:]:
            design, meta = transport.make_design(frame, config)
            for j in range(design.shape[1]):
                p = frame.p_reference.to_numpy()+design[:,j]
                np.testing.assert_allclose(pd.Series(p-frame.p_reference).groupby(frame.ts).sum(),0,atol=1e-9)
                self.assertTrue((p >= -1e-9).all())
                self.assertTrue((p <= frame.static_capacity+1e-9).all())
                np.testing.assert_allclose(p[frame.night],0,atol=1e-9)
            model = mixture(config,meta)
            pred = transport.predict(frame,config,model)
            np.testing.assert_allclose(pd.Series(pred-frame.p_reference).groupby(frame.ts).sum(),0,atol=1e-9)
            bad = copy.deepcopy(model); bad['coefficients'][0]=config['budget']+0.01
            with self.assertRaises(ValueError):transport.predict(frame,config,bad)

    def test_application_labels_unused(self):
        frame=sample(1);config=transport.configs()[1]
        design,meta=transport.make_design(frame,config);model=mixture(config,meta)
        expected=transport.predict(frame,config,model)
        unlabeled=frame.drop(columns=['y','smp','k'])
        np.testing.assert_array_equal(transport.predict(unlabeled,config,model),expected)
        altered=frame.copy();altered['y']=np.nan;altered['smp']=-np.inf;altered['k']=1e20
        np.testing.assert_array_equal(transport.predict(altered,config,model),expected)

    def test_capped_projection(self):
        q=transport.project_energy(np.array([0.,100.,3.]),np.array([10.,12.,20.]),25.)
        self.assertAlmostEqual(q.sum(),25.,places=10)
        self.assertTrue((q >= 0).all());self.assertTrue((q <= [10.,12.,20.]).all())
        np.testing.assert_array_equal(transport.project_energy([1,2],[3,4],0),[0,0])
        with self.assertRaises(ValueError):transport.project_energy([1,2],[3,4],8)

    def test_lp_finds_improvement_and_satisfies_risk(self):
        frame=sample(5);config=transport.configs()[1]
        design,meta=transport.make_design(frame,config)
        target=transport.predict(frame,config,mixture(config,meta,mass=.18))
        frame['y']=target
        model,fitmeta=transport.fit(frame,config)
        pred=transport.predict(frame,config,model)
        self.assertLess(fitmeta['fitted_W'],fitmeta['baseline_W']*.01)
        self.assertGreater(sum(model['coefficients']),.1)
        self.assertLessEqual(sum(model['coefficients']),config['budget']+1e-10)
        for row in fitmeta['environment_risks']:
            self.assertLessEqual(row['candidate_W'],row['reference_W']*1.001+1e-6)
        np.testing.assert_allclose(pred,target,atol=1e-6)

    def test_lp_identity_feasible_under_opposed_group_targets(self):
        frame=sample(4);config=transport.configs()[9]
        design,meta=transport.make_design(frame,config)
        frame['y']=frame.p_reference+5*(~frame.night)
        model,info=transport.fit(frame,config)
        self.assertLessEqual(info['fitted_W'],info['baseline_W']*(1.001)+1e-6)
        self.assertLessEqual(sum(model['coefficients']),config['budget']+1e-10)
        for item in info['environment_risks']:
            self.assertLessEqual(item['candidate_W'],item['reference_W']*1.001+1e-6)

    def test_group_risk_constraint_prevents_sacrificing_small_group(self):
        frame=sample(4);config=transport.configs()[9]
        design,_=transport.make_design(frame,config)
        first=frame.grp.eq('G1').to_numpy()
        # The high-weight group wants coefficient .20, while G2 wants .01.
        # Unconstrained monetary L1 would prefer G1. G2's 0.1% risk allowance
        # instead caps the shared effective transfer at .02001.
        frame['y']=frame.p_reference+design[:,0]*np.where(first,.20,.01)
        frame['smp']=np.where(first,10.,1.)
        model,info=transport.fit(frame,config)
        effective=model['coefficients'][0]-model['coefficients'][1]
        self.assertGreater(effective,.0199)
        self.assertLess(effective,.0201)
        g2=next(x for x in info['environment_risks'] if x['environment'].endswith('/G2'))
        self.assertAlmostEqual(g2['ratio'],1.001,places=6)

    def test_invalid_input_rejected(self):
        frame=sample(1);config=transport.configs()[0]
        with self.assertRaises(ValueError):transport.make_design(pd.concat([frame,frame.iloc[:1]]),config)
        invalid=frame.copy();invalid.loc[0,'p_reference']=10.
        with self.assertRaises(ValueError):transport.make_design(invalid,config)
        bad=copy.deepcopy(config);bad['budget']=2.
        with self.assertRaises(ValueError):transport.make_design(frame,bad)
        model,meta=transport.fit(frame.assign(y=frame.p_reference),config)
        self.assertTrue(meta['identity_fallback'])
        self.assertFalse(any(model['coefficients']))


if __name__ == '__main__':
    unittest.main()
