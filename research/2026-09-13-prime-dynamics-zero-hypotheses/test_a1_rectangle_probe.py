"""Failure-boundary tests for the rectangle wrapper, not numerical benchmarks."""
import copy
import unittest

import a1_rectangle_probe_batch_py3 as probe


class RectangleAuditTests(unittest.TestCase):
    def test_broken_boundary_is_rejected(self):
        result = probe.counter.count_rectangle("0.29", "0.31", "13.99", "14.01", func="synthetic_linear")
        self.assertEqual(probe.audit_segments(result)["status"], "PASSED")
        broken = copy.deepcopy(result)
        broken["segments"][0]["start_exact"] = ["0.30", "13.99"]
        with self.assertRaises(AssertionError):
            probe.audit_segments(broken)
        broken = copy.deepcopy(result)
        broken["segments"][0]["image_finite_and_excludes_zero"] = False
        with self.assertRaises(AssertionError):
            probe.audit_segments(broken)

    def test_unresolved_is_not_zero(self):
        config = probe.config_for("pilot")
        rows = {}
        for job in config["tasks"]:
            target = job["role"] == "target"
            rows[job["task_id"]] = dict(status="COMPLETED", task_id=job["task_id"], job=job,
                elapsed_s=0, result={"count_result": {"status": "unresolved" if target else "certified",
                                                       "count": None if target else 2}})
        summary = probe.summarize(rows, config, "test")
        self.assertEqual(summary["status"], "COMPLETED")
        self.assertEqual(summary["research_status"], "HOLD")
        self.assertIsNone(summary["candidate_rectangle_count"])
        self.assertIsNone(summary["target_zero_count"])
        self.assertFalse(summary["certified_target_zero_free"])
        self.assertFalse(summary["counterexample_claim"])


if __name__ == "__main__":
    unittest.main()
