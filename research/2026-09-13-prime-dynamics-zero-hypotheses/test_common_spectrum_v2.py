"""Scientific regression tests: prediction, leakage, nulls, and recovery."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import common_spectrum_v2 as core
import common_spectrum_v2_batch_py3 as batch
from known_ordinates import known_ordinates, known_mask
import mertens_dynamics
import stratified_shuffle_controls
import phase_concordance_audit_py3
import json
from common_spectrum_power_py3 import add_tone
from prime_consistent_power_py3 import weighted_indicator, lambda_from_indicator


def synthetic_cells():
    cells = []
    for n in (10000, 20000):
        for gi, (samples, trim) in enumerate(((128, 0.), (160, .08))):
            u = np.linspace(4.6 + trim, 10 - trim, samples)
            y = np.column_stack([.1 * u + (1 + i / 4) * np.cos(18 * (u - 4.6) + p)
                                 for i, p in enumerate((.2, 1.6, -1.1, 2.8))])
            for split in (.55, .75):
                cells.append(core.Cell(f"{n}-{gi}-{split}", n, gi, split, u, y.copy(), int(samples * split)))
    return cells


class ScientificTests(unittest.TestCase):
    def test_prime_consistent_injection_preserves_binary_log_bin_counts(self):
        indicator, _ = __import__("short_interval_dynamics").prime_indicator_linear_sieve(5000)
        out = weighted_indicator(indicator, 18., 1., .3, 32, np.random.default_rng(3))
        self.assertTrue(np.all((out == 0) | (out == 1)))
        edges = np.unique(np.rint(np.geomspace(2, 5001, 33)).astype(int))
        for lo, hi in zip(edges[:-1], edges[1:]):
            self.assertEqual(int(out[lo:hi].sum()), int(indicator[lo:hi].sum()))

    def test_prime_consistent_lambda_rebuilds_prime_powers(self):
        indicator = np.zeros(40, dtype=np.uint8)
        indicator[[2, 3, 5]] = 1
        lam = lambda_from_indicator(indicator)
        self.assertAlmostEqual(lam[2], np.log(2.))
        self.assertAlmostEqual(lam[4], np.log(2.))
        self.assertAlmostEqual(lam[8], np.log(2.))
        self.assertAlmostEqual(lam[9], np.log(3.))
        self.assertEqual(lam[6], 0.)

    def test_degenerate_signal_is_invalid_not_a_favorable_zero(self):
        u = np.linspace(0, 8, 128)
        with self.assertRaisesRegex(ValueError, "degenerate"):
            core.prediction_gains(u, np.ones((len(u), 4)), 70, 18., 0.)

    def test_injection_is_exact_and_does_not_mutate_arithmetic_cells(self):
        cells = synthetic_cells()
        original = cells[0].y.copy()
        scales = np.array([1., 2., 3., 4.])
        phases = np.array([.2, 1.6, -1.1, 2.8])
        injected = add_tone(cells, 18., 2., scales, phases, 4.6)
        np.testing.assert_array_equal(cells[0].y, original)
        expected = 2 * scales[None, :] * np.cos(18 * (cells[0].u[:, None] - 4.6) + phases[None, :])
        np.testing.assert_allclose(injected[0].y - original, expected)

    def test_short_training_windows_end_before_holdout(self):
        cells = core.build_cells(core.arithmetic_coefficients(10000), [5000, 10000], [(128, 0), (160, .08)], [.55, .75])
        for cell in cells:
            self.assertLess(cell.support_end_u[cell.train_end - 1], cell.u[cell.cut])
        result = core.evaluate(cells, np.arange(16, 20.01, .25), np.log(100))
        self.assertLess(result["selection_support_u_max"], result["earliest_holdout_u"])

    def test_phase_audit_never_pools_channels_or_different_frequencies(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "peaks.json"
            path.write_text(json.dumps({"records": [
                {"channel": channel, "samples": samples, "phase": 0., "peaks": [{"t": t, "phase": phase}]}
                for channel, samples, t, phase in [("psi", 100, 37.5, 0.), ("psi", 200, 37.5, 0.),
                    ("psi", 300, 37.6, 3.14), ("mertens", 100, 37.5, 3.14)]]}))
            result = phase_concordance_audit_py3.audit(path)
        self.assertEqual(len(result["same_channel_same_frequency_groups"]), 3)
        self.assertEqual(result["same_channel_same_frequency_groups"][0]["descriptive_resultant"], 1.)
        self.assertIsNone(result["eligible_candidate_count"])
        self.assertTrue(all(r["classification"] == "KNOWN_LINE_NEIGHBORHOOD" for r in result["hits"]))

    def test_known_zeros_cover_sixth_and_band_edge(self):
        self.assertTrue(any(abs(t - 37.58617815882567) < 1e-10 for t in known_ordinates(4, 40)))
        self.assertTrue(any(abs(t - 40.9187190121475) < 1e-10 for t in known_ordinates(40, 40.6)))
        self.assertTrue(known_mask([37.5, 37.6]).all())

    def test_mertens_endpoint_includes_current_integer(self):
        mu = np.array([0, 1, -1, -1, 0], dtype=np.int8)
        _, y = mertens_dynamics.log_signal(mu, 10)
        self.assertAlmostEqual(y[0], 0.)
        self.assertAlmostEqual(y[-1], -.5)

    def test_stratified_control_integrates_coefficients(self):
        weights = np.array([0., 1., -1., 1.])
        seen = []
        def sample(cumulative, n, m, trim, name):
            seen.append(cumulative.copy())
            return np.arange(4.), np.arange(4.)
        with patch.object(stratified_shuffle_controls, "cumulative_grid", sample):
            with patch.object(stratified_shuffle_controls, "demod_scan", return_value=[]):
                stratified_shuffle_controls.score({"mertens": weights}, 3, [(4, 0)], np.array([37.5]))
        np.testing.assert_array_equal(seen[0], np.cumsum(weights))

    def test_tone_recovered_with_different_channel_phases(self):
        result = core.evaluate(synthetic_cells(), np.arange(16, 20.01, .25), 4.6)
        peak = result["candidates"][0]
        self.assertEqual(peak["t"], 18)
        self.assertGreater(peak["joint_score"], .99)
        self.assertLess(result["selection_u_max"], result["earliest_holdout_u"])

    def test_holdout_phase_reversal_is_rejected_without_refitting(self):
        u = np.linspace(0, 8, 160)
        cut = 88
        y = np.cos(18 * u)[:, None]
        y[cut:] *= -1
        gains, _ = core.prediction_gains(u, y, cut, 18, 0)
        self.assertLess(gains[0], 0)

    def test_selection_is_unchanged_by_any_holdout_values(self):
        cells = synthetic_cells()
        original = core.evaluate(cells, np.arange(16, 20.01, .25), 4.6)
        boundary = min(c.u[c.cut] for c in cells)
        for c in cells:
            c.y[c.u >= boundary] = np.random.default_rng(42).normal(size=c.y[c.u >= boundary].shape) * 10
        modified = core.evaluate(cells, np.arange(16, 20.01, .25), 4.6)
        self.assertEqual([c["t"] for c in original["candidates"]], [c["t"] for c in modified["candidates"]])

    def test_density_surrogate_preserves_bins_and_joint_dependence(self):
        n, bins = 500, 8
        coefficients = {"mu": np.arange(n + 1), "lambda": 2 * np.arange(n + 1), "prime": (np.arange(n + 1) % 3 == 0).astype(int)}
        out = core.surrogate(coefficients, "density_preserving", np.random.default_rng(2), 30, bins)
        np.testing.assert_array_equal(out["lambda"], 2 * out["mu"])
        edges = np.unique(np.rint(np.geomspace(2, n + 1, bins + 1)).astype(int))
        for lo, hi in zip(edges[:-1], edges[1:]):
            self.assertEqual(sum(out["prime"][lo:hi]), sum(coefficients["prime"][lo:hi]))

    def test_candidate_count_is_computed_and_insufficient_controls_are_null(self):
        real = {"candidates": [{"t": 18., "joint_score": .9, "positive_in_every_primary_cell": True}]}
        controls = {mode: [-.1] * 19 for mode in core.CONTROL_MODES}
        result = core.gate(real, controls, 19)
        self.assertEqual(result["candidate_count"], 1)
        self.assertEqual(result["tested_candidates"][0]["control_p"]["global_shuffle"], .05)
        self.assertIsNone(core.gate(real, {m: [-.1] * 2 for m in controls}, 2)["candidate_count"])
        controls["block_shuffle"] = [1.] * 19
        self.assertEqual(core.gate(real, controls, 19)["candidate_count"], 0)


class RecoveryTests(unittest.TestCase):
    def config(self):
        return {"control_reps": 2, "alpha": .05, "seed": 1, "scales": [5000, 10000],
                "t_min": 4., "t_max": 40., "t_step": .25, "known_margin": .35, "top_k": 1,
                "max_seconds": 60}

    def test_failure_count_resume_and_configuration_mismatch(self):
        with tempfile.TemporaryDirectory() as root:
            config = self.config()
            calls = []
            def worker(key, mode, rep):
                calls.append(key)
                if key == "real":
                    raise RuntimeError("intentional failed task")
                return {"max_statistic": -.1, "candidates": []}
            with patch("traceback.print_exc"):
                result = batch.run_batch(root, config, worker)
            self.assertEqual(result["failed_count"], 1)
            self.assertEqual(result["completed_count"], 6)
            self.assertIsNone(result["candidate_count"])
            calls.clear()
            def repaired(key, mode, rep):
                calls.append(key)
                return {"max_statistic": .8, "candidates": [{"t": 18., "joint_score": .8, "positive_in_every_primary_cell": True}]}
            resumed = batch.run_batch(root, config, repaired)
            self.assertEqual(calls, ["real"])
            self.assertEqual(resumed["failed_count"], 0)
            self.assertEqual(resumed["completed_count"], 7)
            before = (Path(root) / "config.json").read_bytes()
            with self.assertRaisesRegex(ValueError, "changed"):
                batch.run_batch(root, {**config, "seed": 2}, repaired)
            self.assertEqual((Path(root) / "config.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
