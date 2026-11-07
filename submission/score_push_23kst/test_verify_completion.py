#!/usr/bin/env python3
"""Small, target-free regression checks for the independent terminal verifier.

Run with the project Python; all controller/process evidence is synthetic and
all writes stay in temporary directories. No model is loaded or trained.
"""
from __future__ import annotations

import ast
from contextlib import ExitStack
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).with_name('verify_completion.py')
SPEC = importlib.util.spec_from_file_location('terminal_verifier_under_test', SOURCE)
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)
pd, np = VERIFIER.pd, VERIFIER.np


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def identity(pid=101, pgid=101, start_ticks=1001, boot_id='fixture-boot'):
    return dict(pid=pid, pgid=pgid, start_ticks=start_ticks, boot_id=boot_id)


class TerminalGateTests(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.out = self.root / 'output'
        self.directory = self.out / 'controller_state'
        controller = self.root / 'submission/score_push_23kst/controller.py'
        controller.parent.mkdir(parents=True)
        controller.write_text('# synthetic controller source\n')
        pinned = self.root / 'pinned.txt'
        pinned.write_text('immutable fixture\n')
        self.manifest = dict(deadline_utc='2026-11-08T14:00:00Z', jobs=[], completion_jobs=[],
                             input_sha256={'pinned.txt': digest(pinned)})
        self.state = dict(phase='finished', current_job=None, jobs={},
                          deadline_utc=self.manifest['deadline_utc'],
                          controller_identity=identity(), controller_sha256=digest(controller))
        self.processes = {}
        self.save()
        self.stack.enter_context(patch.object(VERIFIER, 'ROOT', self.root))
        self.stack.enter_context(patch.object(VERIFIER, 'OUT', self.out))
        original_read_text, original_iterdir = Path.read_text, Path.iterdir

        def read_text(path, *args, **kwargs):
            if str(path) == '/proc/sys/kernel/random/boot_id':
                return 'fixture-boot\n'
            if path.parent.parent == Path('/proc') and path.name == 'stat':
                process = self.processes[int(path.parent.name)]
                if isinstance(process, Exception):
                    raise process
                fields = ['0'] * 20
                fields[0] = process.get('state', 'S')
                fields[2] = str(process['pgid'])
                fields[19] = str(process['start_ticks'])
                return f'{path.parent.name} (name with ) parentheses) ' + ' '.join(fields)
            return original_read_text(path, *args, **kwargs)

        def iterdir(path):
            if path == Path('/proc'):
                return iter([Path('/proc/sys')] + [Path('/proc') / str(pid) for pid in self.processes])
            return original_iterdir(path)

        self.stack.enter_context(patch.object(Path, 'read_text', read_text))
        self.stack.enter_context(patch.object(Path, 'iterdir', iterdir))

    def save(self):
        write_json(self.out / 'controller_manifest.json', self.manifest)
        self.state['manifest_sha256'] = digest(self.out / 'controller_manifest.json')
        write_json(self.directory / 'state.json', self.state)

    def job(self, status='completed', *, completion=False, wrapper=None):
        self.manifest['completion_jobs' if completion else 'jobs'].append({'id': 'fixture'})
        self.state['jobs']['fixture'] = dict(status=status, nonce='fixture-nonce', exit_code=0)
        if wrapper is not None:
            self.state['jobs']['fixture']['wrapper_identity'] = wrapper
        self.save()

    def receipt(self, **changes):
        entry = self.state['jobs']['fixture']
        receipt = dict(nonce=entry['nonce'], manifest_sha256=self.state['manifest_sha256'],
                       status=entry['status'], exit_code=entry['exit_code'])
        receipt.update(changes)
        path = self.directory / 'jobs/fixture/receipt.json'
        write_json(path, receipt)
        entry['receipt_sha256'] = digest(path)
        write_json(self.directory / 'state.json', self.state)
        return path

    def test_finished_dead_processes_and_pins_pass(self):
        ready, evidence = VERIFIER.terminal_gate(self.directory)
        self.assertTrue(ready)
        self.assertEqual(evidence['live_recorded_group_pids'], [])

    def test_missing_or_unfinished_controller_is_checkpoint(self):
        self.assertFalse(VERIFIER.terminal_gate(self.root / 'missing')[0])
        self.state['phase'] = 'search'
        self.save()
        self.assertFalse(VERIFIER.terminal_gate(self.directory)[0])

    def test_changed_controller_manifest_or_pin_is_rejected(self):
        paths = [self.root / 'submission/score_push_23kst/controller.py',
                 self.out / 'controller_manifest.json', self.root / 'pinned.txt']
        for path in paths:
            with self.subTest(path=path.name):
                previous = path.read_bytes()
                path.write_bytes(previous + b' ')
                try:
                    with self.assertRaises(AssertionError):
                        VERIFIER.terminal_gate(self.directory)
                finally:
                    path.write_bytes(previous)

    def test_deadline_mismatch_is_rejected(self):
        self.state['deadline_utc'] = '2026-11-08T15:00:00Z'
        self.save()
        with self.assertRaisesRegex(AssertionError, 'deadline'):
            VERIFIER.terminal_gate(self.directory)

    def test_missing_manifest_job_or_unknown_job_status_is_rejected(self):
        self.manifest['jobs'] = [{'id': 'not-in-state'}]
        self.save()
        with self.assertRaises(AssertionError):
            VERIFIER.terminal_gate(self.directory)
        self.manifest['jobs'] = []
        self.job(status='running')
        with self.assertRaisesRegex(AssertionError, 'unresolved'):
            VERIFIER.terminal_gate(self.directory)

    def test_pending_job_and_failed_completion_remain_checkpoints(self):
        self.job(status='pending', completion=True)
        self.assertFalse(VERIFIER.terminal_gate(self.directory)[0])
        self.state['jobs']['fixture']['status'] = 'failed'
        self.save()
        self.assertFalse(VERIFIER.terminal_gate(self.directory)[0])

    def test_only_declared_finalizer_may_be_an_extra_job(self):
        self.state['jobs']['final-report'] = dict(status='completed', nonce='final', exit_code=0)
        self.manifest['finalizer'] = {'id': 'final-report'}
        self.save()
        self.assertTrue(VERIFIER.terminal_gate(self.directory)[0])
        self.manifest['finalizer']['id'] = 'different-report'
        self.save()
        with self.assertRaisesRegex(AssertionError, 'Unexpected controller job'):
            VERIFIER.terminal_gate(self.directory)

    def test_receipt_hash_and_identity_contract_are_checked(self):
        self.job(completion=True)
        path = self.receipt()
        ready, evidence = VERIFIER.terminal_gate(self.directory)
        self.assertTrue(ready)
        self.assertEqual(evidence['controller_receipts_verified'], 1)
        path.write_text(path.read_text() + ' ')
        with self.assertRaisesRegex(AssertionError, 'receipt changed'):
            VERIFIER.terminal_gate(self.directory)
        for key, value in [('nonce', 'wrong'), ('manifest_sha256', 'wrong'),
                           ('status', 'failed'), ('exit_code', 1)]:
            with self.subTest(field=key):
                self.receipt(**{key: value})
                with self.assertRaises(AssertionError):
                    VERIFIER.terminal_gate(self.directory)

    def test_live_controller_blocks_audit(self):
        self.processes[101] = identity()
        ready, evidence = VERIFIER.terminal_gate(self.directory)
        self.assertFalse(ready)
        self.assertEqual(evidence['live_recorded_identity_pids'], [101])

    def test_live_state_only_wrapper_blocks_without_started_file(self):
        self.job(wrapper=identity(202, 202, 2002))
        self.processes[202] = identity(202, 202, 2002)
        self.assertFalse(VERIFIER.terminal_gate(self.directory)[0])

    def test_live_descendant_group_blocks_when_anchor_is_dead(self):
        self.processes[303] = identity(303, 101, 3003)
        ready, evidence = VERIFIER.terminal_gate(self.directory)
        self.assertFalse(ready)
        self.assertEqual(evidence['live_recorded_identity_pids'], [])
        self.assertEqual(evidence['live_recorded_group_pids'], [303])

    def test_recycled_pid_outside_group_and_old_boot_do_not_block(self):
        self.processes[101] = identity(101, 999, 9999)
        self.assertTrue(VERIFIER.terminal_gate(self.directory)[0])
        self.state['controller_identity']['boot_id'] = 'previous-boot'
        self.save()
        self.processes[101] = identity()
        self.assertTrue(VERIFIER.terminal_gate(self.directory)[0])

    def test_zombie_and_disappeared_process_are_terminal(self):
        self.processes[101] = {**identity(), 'state': 'Z'}
        self.processes[303] = FileNotFoundError('synthetic exited process')
        self.assertTrue(VERIFIER.terminal_gate(self.directory)[0])

    def test_unreadable_process_cannot_prove_termination(self):
        self.processes[303] = PermissionError('synthetic inaccessible process')
        ready, evidence = VERIFIER.terminal_gate(self.directory)
        self.assertFalse(ready)
        self.assertIn('unreadable', str(evidence).lower())

    def test_started_worker_identity_and_nonce_are_checked(self):
        self.job()
        started = dict(manifest_sha256=self.state['manifest_sha256'], nonce='fixture-nonce',
                       worker_identity=identity(404, 404, 4004))
        path = self.directory / 'jobs/fixture/started.json'
        write_json(path, started)
        self.processes[404] = identity(404, 404, 4004)
        self.assertFalse(VERIFIER.terminal_gate(self.directory)[0])
        started['nonce'] = 'wrong'
        write_json(path, started)
        with self.assertRaises(AssertionError):
            VERIFIER.terminal_gate(self.directory)


class PredictionContractTests(unittest.TestCase):
    def frame(self):
        return pd.DataFrame(dict(ts=pd.date_range('2024-01-01', periods=3, tz='Asia/Seoul'),
                                 grp=['G1', 'G2', 'G1'], y=[2., 3., 4.], p=[4., 6., 8.],
                                 p_reference=[0., 0., 0.], smp=[1., 2., 3.], k=[1., 1., 1.],
                                 night=[False, False, False], static_capacity=[10., 20., 10.]))

    def test_join_preserves_left_order_despite_shuffled_right(self):
        left = self.frame()[['ts', 'grp', 'y']]
        right = self.frame()[['ts', 'grp', 'p']].iloc[::-1]
        actual = VERIFIER.joined(left, right, ['p'])
        pd.testing.assert_frame_equal(actual, self.frame()[['ts', 'grp', 'y', 'p']])

    def test_join_rejects_missing_duplicate_and_null_keys(self):
        left = self.frame()[['ts', 'grp', 'y']]
        right = self.frame()[['ts', 'grp', 'p']]
        null = right.copy()
        null.loc[0, 'grp'] = None
        for invalid in [right.iloc[:-1], pd.concat([right, right.iloc[[0]]]), null]:
            with self.subTest(rows=len(invalid)), self.assertRaises((AssertionError, pd.errors.MergeError)):
                VERIFIER.joined(left, invalid, ['p'])
        with self.assertRaises(AssertionError):
            VERIFIER.joined(pd.concat([left, left.iloc[[0]]]), right, ['p'])

    def test_weighted_alpha_and_constrained_boundaries(self):
        frame = self.frame()
        frame['p'] = 10.
        frame['y'] = [2., 4., 9.]
        frame['smp'] = [1., 4., 1.]
        VERIFIER.alpha_optimal(frame, .4)
        for wrong in [0., .2, .9, 1., -0.1, 1.1, np.nan]:
            with self.subTest(alpha=wrong), self.assertRaises(AssertionError):
                VERIFIER.alpha_optimal(frame, wrong)
        frame['y'] = -2.
        VERIFIER.alpha_optimal(frame, 0.)
        frame['y'] = 20.
        VERIFIER.alpha_optimal(frame, 1.)
        frame['p'] = frame.p_reference
        VERIFIER.alpha_optimal(frame, 0.)
        with self.assertRaises(AssertionError):
            VERIFIER.alpha_optimal(frame, .4)

    def test_combination_is_equal_weight_and_preserves_inputs(self):
        first, second = self.frame(), self.frame()
        second['p'] = first.p + 4.
        first['p_base'] = first.p + 1.
        second['p_base'] = first.p + 7.
        original = first.copy(deep=True)
        combined = VERIFIER.combined([first, second])
        np.testing.assert_array_equal(combined.p, first.p + 2.)
        np.testing.assert_array_equal(combined.p_base, first.p + 4.)
        pd.testing.assert_frame_equal(first, original)

    def test_combination_rejects_reordered_keys_or_changed_evidence(self):
        first = self.frame()
        invalid_frames = [first.iloc[::-1]]
        for column in ['y', 'smp', 'k', 'p_reference', 'night', 'static_capacity']:
            changed = first.copy()
            changed.loc[0, column] = True if column == 'night' else first.loc[0, column] + 1.
            invalid_frames.append(changed)
        for invalid in invalid_frames:
            with self.subTest(columns=invalid.columns.tolist()), self.assertRaises(AssertionError):
                VERIFIER.combined([first, invalid])


class DevelopmentGateTests(unittest.TestCase):
    annual = ['early2022', 'primary', 'winter', 'spring', 'recent']
    quarters = [f'quarter-{index:02}' for index in range(11)]

    def fixtures(self):
        names = self.annual + self.quarters
        return {seed: {name: pd.DataFrame(dict(
            ts=[pd.Timestamp('2023-01-01', tz='Asia/Seoul') + pd.Timedelta(days=index)] * 2,
            grp=['G1', 'G2'], y=[10., 10.], p=[11., 11.], p_base=[12., 12.],
            p_reference=[0., 0.], smp=[1., 1.], k=[1., 1.], night=[False, False]))
            for index, name in enumerate(names)} for seed in (0, 1, 2)}

    def evaluate(self, frames, alpha=None):
        return VERIFIER.evaluate_development(frames, self.annual, self.quarters, alpha=alpha)[0]

    def test_known_improvements_pass_all_predeclared_gates(self):
        report = self.evaluate(self.fixtures())
        self.assertTrue(report['eligible'])
        self.assertTrue(all(report['gate_checks'].values()))
        self.assertAlmostEqual(report['alpha'], 10. / 11.)
        self.assertEqual(set(report['annual_ratios'].values()), {.5})
        self.assertEqual(set(report['quarter_ratios'].values()), {.5})
        self.assertEqual(set(report['quarter_group_ratios'].values()), {.5})
        self.assertEqual(set(report['seed_quarter_aggregate_ratios'].values()), {.5})
        self.assertEqual(set(report['blend_ratios'].values()), {0.})

    def test_quarter_group_and_seed_regressions_each_block_eligibility(self):
        cases = [('quarter', 'quarter_worst_at_most_102'),
                 ('group', 'quarter_each_group_at_most_1'),
                 ('seed', 'each_seed_quarter_aggregate_below_1')]
        for change, expected_gate in cases:
            frames = self.fixtures()
            for seed in (0, 1, 2):
                if change == 'quarter':
                    frames[seed][self.quarters[0]]['p'] = 13.
                for name in self.quarters:
                    if change == 'group':
                        frames[seed][name]['p'] = [12.2, 10.]
                    elif change == 'seed':
                        frames[seed][name]['p'] = 13. if seed == 2 else 9.5
            with self.subTest(regression=change):
                report = self.evaluate(frames)
                self.assertFalse(report['eligible'])
                self.assertFalse(report['gate_checks'][expected_gate])
                self.assertEqual([name for name, passed in report['gate_checks'].items() if not passed], [expected_gate])

    def test_quarter_target_keys_cannot_be_counted_twice(self):
        frames = self.fixtures()
        for seed in (0, 1, 2):
            frames[seed][self.quarters[1]]['ts'] = frames[seed][self.quarters[0]].ts
        with self.assertRaises(AssertionError):
            self.evaluate(frames)

    def test_recent_labels_never_choose_alpha_and_wrong_frozen_alpha_fails(self):
        frames = self.fixtures()
        primary_alpha = self.evaluate(frames)['alpha']
        for seed in (0, 1, 2):
            frames[seed]['recent']['y'] = 10.5
        report = self.evaluate(frames)
        self.assertEqual(report['alpha'], primary_alpha)
        self.assertAlmostEqual(report['blend_ratios']['recent'], 1. / 21.)
        self.assertEqual(self.evaluate(frames, primary_alpha)['alpha'], primary_alpha)
        with self.assertRaises(AssertionError):
            self.evaluate(frames, .5)


class NovelFeatureAlgebraTests(unittest.TestCase):
    cutoff = '2024-07-01'
    rich = ['wa_cloud', 'wa_humidity', 'wb_cloud', 'only_future_varies']

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('production_feature_algebra_under_test', SOURCE.with_name('features.py'))
        cls.features = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.features)

    def fixture(self):
        ts = pd.to_datetime(['2024-03-01', '2024-03-01', '2024-03-02', '2024-03-03',
                             '2024-06-01', '2024-06-02', '2024-07-02']).tz_localize('Asia/Seoul')
        frame = pd.DataFrame({name: np.arange(7, dtype=float) for name in self.features.WEATHER})
        frame['ts'], frame['grp'] = ts, ['G1', 'G1', 'G1', 'G2', 'G1', 'G2', 'G1']
        frame['model_origin'] = ts - pd.to_timedelta([30, 120, 30, 30, 30, 30, 30], unit='D')
        frame['row'] = np.arange(7)
        frame['train_history_days'] = np.arange(7) + 400.
        frame['night'] = False
        frame['p'] = np.arange(10., 3., -1.)
        frame['y'] = [12., 12., 13., 14., 15., 16., 17.]
        frame['capacity_kw'] = [100., 100., 100., 200., 100., 200., 100.]
        frame['smp'], frame['k'] = [1., 1., 2., 3., 4., 5., 6.], [1., 1., 1., 2., 1., 1., 1.]
        frame['cosz'] = [0., 0., .25, .5, .75, .9, 1.]
        frame['grp_code'] = frame.grp.map({'G1': 0., 'G2': 1.})
        frame['wa_humidity'] = 7.
        frame['wb_cloud'] = np.inf
        frame['only_future_varies'] = [4., 4., 4., 4., 4., 4., 5.]
        for offset, base in enumerate(self.features.BASE_IDS):
            frame[f'cross_{base}'] = frame.p + offset
        return frame

    def units(self, frame):
        # Scalar independent expression also exercises the zero-sun floor.
        return np.asarray([capacity * max(1.098 * cosine * np.exp(-.059 / cosine), .05)
                           if cosine > 0 else capacity * .05
                           for capacity, cosine in zip(frame.capacity_kw, frame.cosz)])

    def test_feature_algebra_matches_and_never_uses_target_or_price(self):
        frame = self.fixture()
        for family in ['weather_spread', 'rich_spread']:
            config = {'features': family}
            with self.subTest(family=family):
                expected = self.features.engineer(frame, config, self.rich)
                actual = VERIFIER.novel_engineered(frame, config, self.rich)
                pd.testing.assert_frame_equal(actual, expected, check_exact=True)
                np.testing.assert_allclose(actual.cross_mean, (frame.p + 1.5) / self.units(frame))
                np.testing.assert_allclose(actual.cross_range, 3. / self.units(frame))
                changed = frame.copy()
                changed['y'], changed['smp'], changed['k'] = -12345., 0., 99.
                changed['cf'], changed['energy'], changed['p_reference'] = 100., -1., 1000.
                pd.testing.assert_frame_equal(VERIFIER.novel_engineered(changed, config, self.rich), actual)
        with self.assertRaises(AssertionError):
            VERIFIER.novel_engineered(frame, {'features': 'rich_spread'}, ['y'])

    def test_cutoff_horizon_and_duplicate_counts_are_recomputed_before_weights(self):
        pool = self.fixture()
        bounded = pool.loc[pool.ts.le(VERIFIER.kst(self.cutoff))].reset_index(drop=True)
        for weighting, expected_rows, multiplicity in [
                ('money', [0, 1, 2, 3, 4, 5], [2., 2., 1., 1., 1., 1.]),
                ('horizon', [0, 2, 3, 4, 5], [1., 1., 1., 1., 1.])]:
            with self.subTest(weighting=weighting):
                config = {'features': 'rich_spread', 'weighting': weighting}
                actual = VERIFIER.novel_training(pool, config, self.cutoff, 90, self.rich)
                expected = self.features.training(bounded, config, self.cutoff, 90, self.rich)
                train, matrix, target, weight = actual
                pd.testing.assert_frame_equal(train, expected[0], check_exact=True)
                pd.testing.assert_frame_equal(matrix, expected[1], check_exact=True)
                np.testing.assert_array_equal(target, expected[2])
                np.testing.assert_array_equal(weight, expected[3])
                self.assertEqual(train.row.tolist(), expected_rows)
                self.assertNotIn('wa_humidity', matrix)
                self.assertNotIn('wb_cloud', matrix)
                self.assertNotIn('only_future_varies', matrix)
                units = self.units(train)
                raw_weight = train.smp.to_numpy() * train.k.to_numpy() * units / multiplicity
                np.testing.assert_allclose(weight, raw_weight / raw_weight.mean())
                np.testing.assert_allclose(target, (train.y - train.p) / units)
                self.assertAlmostEqual(float(weight.mean()), 1.)

    def test_group_season_objective_equalizes_cell_mass_after_filtering(self):
        pool = self.fixture()
        config = {'features': 'weather_spread', 'weighting': 'horizon_groupseason'}
        actual = VERIFIER.novel_training(pool, config, self.cutoff, 90, self.rich)
        bounded = pool.loc[pool.ts.le(VERIFIER.kst(self.cutoff))].reset_index(drop=True)
        expected = self.features.training(bounded, config, self.cutoff, 90, self.rich)
        train, matrix, target, weight = actual
        pd.testing.assert_frame_equal(train, expected[0], check_exact=True)
        pd.testing.assert_frame_equal(matrix, expected[1], check_exact=True)
        np.testing.assert_array_equal(target, expected[2])
        np.testing.assert_array_equal(weight, expected[3])
        self.assertEqual(train.row.tolist(), [0, 2, 3, 4, 5])
        cells = pd.Series(['G1_spring', 'G1_spring', 'G2_spring', 'G1_summer', 'G2_summer'])
        mass = pd.Series(weight).groupby(cells).sum()
        np.testing.assert_allclose(mass.to_numpy(), np.full(4, 5. / 4.))


class CorrectionReplayTests(unittest.TestCase):
    """Synthetic files and a fake Booster exercise replay without any model load."""
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.folder = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.stack.enter_context(patch.object(VERIFIER, 'ROOT', self.folder))
        NovelFeatureAlgebraTests.setUpClass()
        helper = NovelFeatureAlgebraTests()
        self.pool, self.rich = helper.fixture(), helper.rich
        self.config = dict(features='rich_spread', weighting='horizon', group_mix=.5,
                           anchor_penalty=.25, bound=1., shrink=.5, n_estimators=5,
                           learning_rate=.1, num_leaves=4, min_child_samples=2, reg_lambda=1.)
        self.cutoff, self.horizon, self.seed, self.fold = helper.cutoff, 90, 2, 'fixture'
        self.provenance = {'matched_cross_base_ids': list(VERIFIER.BASE_IDS), 'fixture': True}
        self.application = self.pool.iloc[[0, 2, 3, 4, 5]].copy().reset_index(drop=True)
        self.application['ts'] = pd.date_range('2024-07-02', periods=5, tz='Asia/Seoul')
        self.application['model_origin'] = VERIFIER.kst(self.cutoff)
        self.application['p'] = [2., 99., 1., 10., 20.]
        self.application['y'] = [6., 100., 2., 9., 19.]
        self.application['cosz'], self.application['capacity_kw'] = 0., 100.
        self.application['static_capacity'], self.application['p_reference'] = 100., 10.
        night = self.application.iloc[[0]].copy()
        night['ts'] = VERIFIER.kst('2024-07-07')
        night['grp'], night['night'], night['p'], night['y'] = 'G2', True, 0., -3.
        night['capacity_kw'], night['p_reference'] = np.nan, 0.
        self.application = pd.concat([self.application, night], ignore_index=True)
        bounded = self.pool.loc[self.pool.ts.le(VERIFIER.kst(self.cutoff))].reset_index(drop=True)
        train, matrix, target, weight = helper.features.training(bounded, self.config, self.cutoff, self.horizon, self.rich)
        self.columns = list(matrix)
        self.transform = dict(features=self.columns, cutoff=self.cutoff, horizon_days=self.horizon,
            training_rows=len(train), unique_targets=len(train[['ts', 'grp']].drop_duplicates()),
            training_target_start=str(train.ts.min()), training_target_end=str(train.ts.max()),
            generating_origin_start=str(train.model_origin.min()), generating_origin_end=str(train.model_origin.max()),
            chronology_keys_sha256=hashlib.sha256(pd.util.hash_pandas_object(train[['model_origin', 'ts', 'grp']], index=False).to_numpy().tobytes()).hexdigest(),
            every_origin_precedes_target=True, train_only_feature_mask=True, group_mix=.5, anchor_penalty=.25,
            provenance=self.provenance, weight_min=float(weight.min()), weight_max=float(weight.max()),
            weight_mean=float(weight.mean()), target_min=float(target.min()), target_max=float(target.max()),
            model_files=['pooled.txt', 'G1.txt', 'G2.txt'])
        expected = self.application.rename(columns={'p': 'p_base'}).copy()
        expected['p'] = [4.5, 100., 0., 11., 20.5, 0.]
        self.expected = expected[['ts', 'grp', 'y', 'smp', 'k', 'night', 'capacity_kw', 'static_capacity', 'p_reference', 'p_base', 'p']]
        self.expected.to_parquet(self.folder / 'predictions.parquet', index=False)
        for name in self.transform['model_files']:
            (self.folder / name).write_text('synthetic placeholder, never loaded\n')
        self.record = dict(status='PASS', config=self.config, seed=self.seed, fold=self.fold,
            native_saved_model_replay=True, model_files=self.transform['model_files'], real_model_fits=3,
            score=VERIFIER.score(self.expected, self.expected.p), raw_score=VERIFIER.score(self.expected, self.expected.p_base))
        self.record['model_params'] = dict(num_leaves=4, n_estimators=5, learning_rate=.1,
            min_child_samples=2, reg_lambda=1., objective='regression_l1', colsample_bytree=.9,
            subsample=.8, subsample_freq=1, n_jobs=4, verbose=-1, random_state=2,
            deterministic=True, force_col_wise=True)
        self.save()
        self.fault = None
        owner = self
        class FakeBooster:
            def __init__(self, model_file):
                self.name = Path(model_file).stem
                self.params = dict(objective='regression_l1', seed=2, num_iterations=5, learning_rate=.1,
                    num_leaves=4, min_data_in_leaf=2, lambda_l2=1., feature_fraction=.9, bagging_fraction=.8,
                    bagging_freq=1, num_threads=4, deterministic=True, force_col_wise=True)
                if owner.fault == 'missing_parameter':
                    self.params.pop('seed')
                elif owner.fault == 'wrong_parameter':
                    self.params['seed'] = 99
            def feature_name(self):
                return owner.columns[:-1] if owner.fault == 'wrong_features' else owner.columns
            def predict(self, frame, num_threads):
                self_test.assertEqual(num_threads, 1)
                self_test.assertEqual(list(frame), owner.columns)
                return np.asarray({'pooled': [2., 2., -2., .2, .2],
                                   'G1': [4., 4., 999., .6, 999.],
                                   'G2': [999., 999., -4., 999., .2]}[self.name])
        self_test = self
        self.booster = self.stack.enter_context(patch.object(VERIFIER.lgb, 'Booster', side_effect=FakeBooster))
        self.audit = object.__new__(VERIFIER.Audit)
        self.audit.rich, self.audit.replayed, self.audit.training_checks = self.rich, 0, 0

    def save(self):
        write_json(self.folder / 'transform.json', self.transform)
        self.record['files_sha256'] = {name: digest(self.folder / name) for name in
                                      [*self.transform['model_files'], 'transform.json', 'predictions.parquet']}
        write_json(self.folder / 'receipt.json', self.record)

    def replay(self):
        return self.audit.correction(self.folder, self.config, self.seed, self.fold, self.pool,
                                     self.application, self.cutoff, self.horizon, self.provenance)

    def evaluation(self):
        fixture = DevelopmentGateTests()
        computed = fixture.evaluate(fixture.fixtures())
        names = ['quarter_mean', 'quarter_improved', 'quarter_worst', 'quarter_groups', 'each_seed_quarter',
                 'annual_mean', 'annual_improved', 'annual_worst', 'alpha', 'reference_periods', 'reference_groups']
        actual = dict(eligible=True, all_history_previously_exposed=True, independent_holdout=False,
                      annual_and_quarter_metrics_not_pooled=True, gates=dict.fromkeys(names, True),
                      seed_quarter_aggregate_ratios={'0': .5, '1': .5, '2': .5},
                      blend=dict(alpha=10./11., ratios={'primary': 0., 'recent': 0.}, mean_ratio=0.,
                                 primary_only_alpha=True, recent_unchanged_transfer=True,
                                 group_ratios=computed['blend_group_ratios'], scores=computed['blend_scores']),
                      folds={name: dict(score=metrics['corrected'], raw_score=metrics['raw'])
                             for name, metrics in computed['metrics'].items()})
        for kind, folds in [('annual', fixture.annual), ('quarter', fixture.quarters)]:
            actual[kind + '_summary'] = dict(ratios=dict.fromkeys(folds, .5), mean_ratio=.5,
                                             worst_ratio=.5, improved_folds=len(folds))
        actual['quarter_summary']['group_aggregate_ratios'] = {'G1': .5, 'G2': .5}
        return actual, computed

    def test_fake_native_replay_restores_group_mix_clipping_nights_and_evaluation(self):
        pd.testing.assert_frame_equal(self.replay(), self.expected, check_exact=True)
        self.assertEqual((self.booster.call_count, self.audit.replayed, self.audit.training_checks), (3, 3, 1))
        self.assertEqual(self.expected.iloc[-1].y, -3.)
        self.assertEqual(self.transform['anchor_penalty'], .25)
        VERIFIER.check_evaluation(*self.evaluation())

    def test_corrupt_hash_features_parameters_anchor_and_evaluation_are_rejected(self):
        (self.folder / 'pooled.txt').write_text('changed synthetic bytes\n')
        with self.assertRaises(AssertionError):
            self.replay()
        self.booster.assert_not_called()
        self.save()
        for fault in ['wrong_features', 'missing_parameter', 'wrong_parameter']:
            self.fault = fault
            with self.subTest(fault=fault), self.assertRaises((AssertionError, KeyError)):
                self.replay()
        self.fault = None
        valid_params = self.record['model_params'].copy()
        for missing in [False, True]:
            if missing:
                self.record.pop('model_params')
            else:
                self.record['model_params']['random_state'] = 99
            self.save()
            with self.subTest(receipt_params_missing=missing), self.assertRaises((AssertionError, KeyError)):
                self.replay()
            self.record['model_params'] = valid_params.copy()
        for value in [0., None]:
            changed = copy.deepcopy(self.transform)
            if value is None:
                self.transform.pop('anchor_penalty')
            else:
                self.transform['anchor_penalty'] = value
            self.save()
            with self.subTest(anchor=value), self.assertRaises((AssertionError, KeyError)):
                self.replay()
            self.transform = changed
        actual, computed = self.evaluation()
        actual['blend']['alpha'] = .5
        with self.assertRaises(AssertionError):
            VERIFIER.check_evaluation(actual, computed)


class NoTrainingAndCheckpointTests(unittest.TestCase):
    def test_verifier_has_no_fit_or_train_calls(self):
        tree = ast.parse(SOURCE.read_text())
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, 'id', None)
                if name in {'fit', 'train', 'fit_transform'}:
                    calls.append((name, node.lineno))
        self.assertEqual(calls, [])

    def test_checkpoint_never_constructs_audit_or_reads_parquet(self):
        with tempfile.TemporaryDirectory() as temporary, ExitStack() as stack:
            directory = Path(temporary)
            stack.enter_context(patch.object(VERIFIER, 'COMP', directory))
            audit = stack.enter_context(patch.object(VERIFIER, 'Audit', side_effect=AssertionError('Audit constructed')))
            pandas_read = stack.enter_context(patch.object(VERIFIER.pd, 'read_parquet', side_effect=AssertionError('Target read')))
            arrow_read = stack.enter_context(patch.object(VERIFIER.pq, 'read_table', side_effect=AssertionError('Target read')))
            for ready in [False, True]:
                with self.subTest(terminal=ready), patch.object(VERIFIER, 'terminal_gate', return_value=(ready, {'reason': 'fixture'})):
                    report = VERIFIER.main(directory)
                    self.assertEqual(report['verification_status'], 'CHECKPOINT_ONLY')
                    self.assertFalse(report['improvement_verified'])
                    self.assertFalse(report['late_targets_loaded'])
            write_json(directory / 'result.json', {'status': 'EXPORTED_UNSCORED_CANDIDATE'})
            with patch.object(VERIFIER, 'terminal_gate', return_value=(False, {'reason': 'Live worker'})):
                self.assertEqual(VERIFIER.main(directory)['verification_status'], 'CHECKPOINT_ONLY')
            audit.assert_not_called()
            pandas_read.assert_not_called()
            arrow_read.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=2)
