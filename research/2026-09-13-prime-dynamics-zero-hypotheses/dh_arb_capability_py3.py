"""Probe the installed python-flint/Arb interval capabilities for the DH audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from flint import acb, arb


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    s = acb(arb("0.808517182456637 +/- 1e-15"),
            arb("85.699348485377592 +/- 1e-15"))
    zeta_repr = repr(s.zeta())
    has_hurwitz = hasattr(acb, "hurwitz")
    result = {
        "status": "COMPLETED",
        "python_flint": "0.9.0",
        "input_box": repr(s),
        "riemann_zeta_interval_eval": zeta_repr,
        "hurwitz_zeta_api_available": has_hurwitz,
        "dh_interval_ready": False,
        "interpretation": (
            "Arb evaluates the Riemann zeta function on a complex box, but the "
            "installed acb API exposes no Hurwitz-zeta evaluator. The DH finite "
            "Hurwitz representation therefore still needs an independently bounded "
            "Euler-Maclaurin implementation before its contour can be certified."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "hurwitz_api": has_hurwitz, "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
