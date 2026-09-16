"""Regression coverage for corrected control data, provenance, and incomplete gates."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / 'research/2026-09-13-prime-dynamics-zero-hypotheses'
sys.path.insert(0, str(RESEARCH))
import short_interval_dynamics as sid
import short_interval_phaseB_batch_py3 as phase_b
import family_phaseC_batch_py3 as phase_c


class PhaseControlsV2(unittest.TestCase):
    def test_shuffle_never_creates_prime_at_one(self):
        indicator, _ = sid.prime_indicator_linear_sieve(500)
        for block in (None, 50):
            for seed in range(25):
                out = sid.shuffled_indicator(indicator, np.random.default_rng(seed), block)
                self.assertEqual(int(out[:2].sum()), 0)
                self.assertEqual(int(out.sum()), int(indicator.sum()))
                self.assertTrue(np.isfinite(sid.gap_signal(np.flatnonzero(out), np.linspace(2, 6, 20))).all())

    def test_truncated_windows_use_actual_length(self):
        indicator = np.zeros(101, dtype=np.uint8)
        indicator[100] = 1
        xs = np.array([98, 100])
        power, fixed, counts = sid.short_signal(indicator, xs, .5, .5)
        expected = 2 / np.log(98)
        value = (1 - expected) / np.sqrt(expected)
        np.testing.assert_allclose(power, [value, 0])
        np.testing.assert_allclose(fixed, [value, 0])
        np.testing.assert_array_equal(counts, [[1, 1], [0, 0]])

    def test_gap_scale_divides_by_mean_gap(self):
        primes = np.array([11, 13, 17, 19])
        u = np.log(primes[:-1])
        np.testing.assert_allclose(sid.gap_signal(primes, u), np.diff(primes) / np.log(primes[:-1]) - 1)

    def test_density_controls_are_executed_and_reused_on_each_grid(self):
        with mock.patch.object(phase_b.dpsc, 'density_surrogate', wraps=phase_b.dpsc.density_surrogate) as density:
            result = phase_b.run_one(1000, .525, 64, 1, (100,), (.55, .80), 42,
                                     grids=[(64, 0), (80, .08)], density_bins=12)
        self.assertEqual(density.call_count, 1)
        self.assertEqual(len(result['grids']), 2)
        for row in result['grids']:
            self.assertEqual(len(row['controls']['density_preserving']), 1)
            self.assertEqual(len(row['controls']['gap_preserving_shuffle']), 1)
            summaries = row['control_metric_summary']
            self.assertEqual({x['cut'] for x in summaries}, {.55, .80})
            self.assertTrue(any(abs(x['t'] - 37.5861781588) < 1e-6 for x in summaries))
            self.assertTrue(all(x['minimum_rank_p'] == .5 for x in summaries))
            self.assertTrue(all(not x['significance_claim'] for x in summaries))
        self.assertIsNone(result['screen_candidate_count'])
        self.assertEqual(result['candidate_gate_status'], 'NOT_EVALUATED')

    def test_no_replicates_produces_incomplete_quantiles(self):
        result = phase_b.metric_summary(.1, [])
        self.assertEqual(result['status'], 'INCOMPLETE')
        self.assertIsNone(result['q95'])
        self.assertIsNone(result['empirical_rank_p'])

    def test_gap_surrogate_preserves_gap_multiset(self):
        indicator, primes = sid.prime_indicator_linear_sieve(1000)
        surrogate = phase_b.gap_preserving_indicator(indicator, 64, np.random.default_rng(11))
        new_primes = np.flatnonzero(surrogate)
        np.testing.assert_array_equal(np.sort(np.diff(primes)), np.sort(np.diff(new_primes)))
        self.assertEqual(new_primes[-1], primes[-1])

    def test_manifest_rejects_changed_config_and_source_for_both_runners(self):
        for module in (phase_b, phase_c):
            with self.subTest(module=module.__name__), tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp)
                config = {'seed': 42, 'control_reps': 1}
                first = module.prepare_manifest(out, config)
                self.assertEqual(first, module.prepare_manifest(out, copy.deepcopy(config)))
                with self.assertRaises(ValueError):
                    module.prepare_manifest(out, {**config, 'control_reps': 2})
                with mock.patch.object(module, 'source_hashes', return_value={'changed.py': 'different'}):
                    with self.assertRaises(ValueError):
                        module.prepare_manifest(out, config)
                self.assertEqual(json.loads((out / 'config.json').read_text())['control_reps'], 1)

    def test_legacy_output_is_not_silently_reused(self):
        for module in (phase_b, phase_c):
            with self.subTest(module=module.__name__), tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp)
                (out / 'progress.json').write_text('{"completed": ["old"]}')
                with self.assertRaises(ValueError):
                    module.prepare_manifest(out, {})

    def test_failed_artifacts_are_retried_and_failure_count_clears(self):
        cfg_b = {'scales': [1000], 'thetas': [.525], 'samples': 64, 'control_reps': 0,
                 'blocks': [100], 'splits': [.67], 'seed': 42, 'grids': [[64, 0]], 'density_bins': 12}
        cfg_c = {'n': 1000, 'samples': 64, 'control_reps': 0, 'splits': [.67],
                 'seed': 42, 'tasks': ['dh']}
        for module, config, method in ((phase_b, cfg_b, 'run_one'), (phase_c, cfg_c, 'detector')):
            with self.subTest(module=module.__name__), tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp)
                with mock.patch.object(module, method, side_effect=RuntimeError('deliberate failure')):
                    first = module.run_batch(out, config)
                self.assertEqual(first['failed_artifacts'], 1)
                self.assertEqual(first['completed_artifacts'], 0)
                with mock.patch.object(module, method, return_value={'status': 'COMPLETED'}) as retry:
                    second = module.run_batch(out, config)
                    retry.assert_called_once()
                self.assertEqual(second['failed_artifacts'], 0)
                self.assertEqual(second['completed_artifacts'], 1)
                self.assertEqual(second['candidate_gate_status'], 'NOT_EVALUATED')
                self.assertIsNone(second['screen_candidate_count'])
                with mock.patch.object(module, method, side_effect=AssertionError('must resume')):
                    third = module.run_batch(out, config)
                self.assertEqual(third['completed_artifacts'], 1)

    def test_character_targets_are_labeled_probes_not_family_zeros(self):
        result = phase_c.detector('chi4', 1000, 64, 1, [.55, .80], 42)
        self.assertIn('not asserted', result['target_role'])
        self.assertIsNone(result['eligible_candidate_count'])
        self.assertEqual(len(result['control_metric_summary']), 4)
        self.assertTrue(all(not x['significance_claim'] for x in result['control_metric_summary']))


if __name__ == '__main__':
    unittest.main()
