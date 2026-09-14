"""Record the current Python 3 interval-arithmetic capability boundary.

The result is intentionally an audit artifact.  mpmath's interval context is
useful for elementary functions, but its complex Hurwitz-zeta path is not a
working rigorous enclosure in the installed release.  We must not silently
label a sampled winding computation as an interval proof.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import mpmath as mp


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    box = mp.iv.mpc(["0.808", "0.809"], ["85.698", "85.700"])
    result = {
        "status": "COMPLETED",
        "python": "3.x",
        "mpmath_version": mp.__version__,
        "test": "mp.iv.zeta(complex_interval)",
        "interval_input": str(box),
        "supported": False,
        "error": None,
        "interpretation": (
            "The installed mpmath interval context does not currently provide a "
            "working complex Hurwitz-zeta enclosure. Existing 32/64/128-point "
            "winding results remain discretized numerical checks only. A rigorous "
            "contour gate requires Arb/python-flint or an independently bounded "
            "Euler-Maclaurin implementation."
        ),
    }
    try:
        result["value_repr"] = repr(mp.iv.zeta(box))
        result["supported"] = True
    except Exception as exc:  # capability audit, not a numerical failure
        result["error"] = f"{type(exc).__name__}: {exc}"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = args.output.with_suffix(".md")
    md.write_text(
        "# DH interval capability audit\n\n"
        f"- Python: `{result['python']}`\n"
        f"- mpmath: `{result['mpmath_version']}`\n"
        f"- complex interval Hurwitz-zeta support: **{result['supported']}**\n\n"
        f"Error: `{result['error']}`\n\n"
        "This is a tooling boundary, not evidence about the zero. The current "
        "winding check is still non-rigorous until an Arb or hand-bounded evaluator "
        "is installed.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": result["status"], "supported": result["supported"], "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
