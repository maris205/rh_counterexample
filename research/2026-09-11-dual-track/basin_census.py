"""Cheap multi-seed census of the direct-zeta optimization basin.

This deliberately stops before mpmath/Newton/contour diagnosis.  It measures
whether independent Arb objective searches repeatedly return similar sigma and
|zeta| values in one finite high-height rectangle.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "2026-09-08-zeta-global-search"))

from zeta_de import optimize_box


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--count", type=int, default=8)
    ap.add_argument("--t-base", default="100000000000000")
    args = ap.parse_args()
    report = {
        "status": "RUNNING",
        "rectangle": {"sigma": ["0.5001", "0.99"], "offset": ["0", "128"],
                       "t_base": args.t_base},
        "configuration": {"maxiter": 5, "popsize": 5, "dps": 35,
                           "workers": 1, "seed_base": 2026091200},
        "known_zero_heights_used_in_objective_or_initial_population": False,
        "runs": [],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for i in range(args.count):
        result = optimize_box("0.5001", "0.99", "0", "128",
                              t_base=args.t_base, dps=35, maxiter=5,
                              popsize=5, seed=2026091200 + i, workers=1)
        result["seed_index"] = i
        report["runs"].append(result)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
        best = result["best"]
        print(json.dumps({"seed": i, "sigma": best["sigma"],
                          "t": best["t"], "abs_zeta": best["approx_abs_zeta"]},
                         ensure_ascii=False), flush=True)
    report["status"] = "COMPLETED"
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(args.output)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
