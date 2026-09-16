"""Evidence-boundary checks; synthetic records do not evaluate actual zeta."""
import unittest
import a1_seed_probe_batch_py3 as probe


class EvidenceBoundaryTests(unittest.TestCase):
    def roots(self, low_sigma, high_sigma, low_t="10010", high_t="10010"):
        return [{"status": "NUMERICAL_CONVERGENCE", "final_sigma": sigma,
                 "final_t": t, "abs_zeta": residual}
                for sigma, t, residual in ((low_sigma, low_t, "1e-40"), (high_sigma, high_t, "1e-70"))]

    def screen(self, roots, agree=True):
        return probe.classify(roots, {"evaluation_rows": [{"independent_point_evaluations_agree": agree}]},
                              probe.configuration("pilot"))["screen_status"]

    def test_sub_float_distance_retained(self):
        sigma = "0.5" + "0" * 27 + "1"
        self.assertEqual(self.screen(self.roots(sigma, sigma)), "OFF_LINE_NUMERICAL_CANDIDATE")

    def test_precision_drift_is_not_candidate(self):
        self.assertEqual(self.screen(self.roots("0.500001", "0.5")), "PRECISION_UNSTABLE")

    def test_independent_disagreement_blocks_candidate(self):
        self.assertEqual(self.screen(self.roots("0.500001", "0.500001"), False), "NUMERICAL_REVIEW_REQUIRED")

    def test_tiny_residual_does_not_override_nonconvergence(self):
        rows = self.roots("0.500001", "0.500001")
        rows[0]["status"] = "NO_DESCENT_STEP"
        self.assertEqual(self.screen(rows), "NO_CONVERGENCE")

    def test_incomplete_results_are_not_a_zero_candidate_claim(self):
        row = {"task_id": "seed-00", "status": "TIMEOUT"}
        summary = probe.summarize({"seed-00": row}, probe.configuration("pilot"), "test-only")
        self.assertEqual(summary["research_status"], "HOLD")
        self.assertEqual(summary["pending_count"], 11)
        self.assertIsNone(summary["off_line_numerical_task_count"])


if __name__ == "__main__":
    unittest.main()
