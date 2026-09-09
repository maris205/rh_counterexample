"""Meaningful positive, negative, near-line and failure-mode calibrations."""
import hashlib
import json
from pathlib import Path

from rectangle_count import count_rectangle
import flint


HERE = Path(__file__).resolve().parent
FIXTURES = [
    ("zeta_first_zero_crosses_line", ("0.49", "0.51", "14.13", "14.14"), {}, "certified", 1),
    ("zeta_off_axis_empty", ("0.6", "0.8", "14", "15"), {}, "certified", 0),
    ("zeta_near_line_empty", ("0.500001", "0.500003", "14.13472", "14.13473"), {}, "certified", 0),
    ("synthetic_off_axis_root", ("0.29", "0.31", "13.99", "14.01"),
     {"func": "synthetic_linear"}, "certified", 1),
    ("synthetic_exact_boundary", ("0.3", "0.4", "13.9", "14.1"),
     {"func": "synthetic_linear", "max_depth": 8}, "unresolved", None),
    ("zeta_pole_rejected", ("0.9", "1.1", "-0.1", "0.1"), {}, "rejected", None),
    ("zeta_budget_unresolved", ("0.49", "0.51", "14.13", "14.14"),
     {"max_evaluations": 1}, "unresolved", None),
]


def main():
    results = []
    for name, rectangle, kwargs, expected_status, expected_count in FIXTURES:
        result = count_rectangle(*rectangle, **kwargs)
        assert result["status"] == expected_status, (name, result.get("reason"))
        assert result["count"] == expected_count, (name, result["count"])
        assert result["off_line_certified"] is False, name
        result["check_name"] = name
        result["expected_status"] = expected_status
        result["expected_count"] = expected_count
        results.append(result)
        print(json.dumps({k: v for k, v in result.items() if k != "segments"}), flush=True)
    data = {"python_flint_version": flint.__version__,
            "source_sha256": hashlib.sha256((HERE / "rectangle_count.py").read_bytes()).hexdigest(),
            "checks_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "all_checks_passed": True, "checks": results}
    (HERE / "certification_checks.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
