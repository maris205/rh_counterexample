"""Finite, free-sigma scan of the actual Riemann zeta function.

This is a candidate generator only.  It evaluates ``|zeta(s)|`` on a fixed
rectangular grid with ``1/2 < Re(s) < 1`` and then runs damped, free-sigma
Newton refinement from the best grid points.  A converged point is never
called a zero certificate; the output is intended for a later independent
Arb rectangle audit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import time
from pathlib import Path

import mpmath as mp

HERE = Path(__file__).resolve().parent
LAB = HERE.parent.parent / "research" / "2026-09-08-zero-lab"
import sys
sys.path.insert(0, str(LAB))
from zero_lab import refine  # noqa: E402


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp-{__import__('os').getpid()}")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def grid(start: float, stop: float, step: float) -> list[float]:
    n = int(math.floor((stop - start) / step + 1e-10))
    return [start + i * step for i in range(n + 1)]


def scan(args: argparse.Namespace) -> dict:
    started = time.perf_counter()
    sigmas = grid(args.sigma_min, args.sigma_max, args.sigma_step)
    heights = grid(args.t_min, args.t_max, args.t_step)
    rows: list[dict] = []
    with mp.workdps(args.dps):
        for t in heights:
            for sigma in sigmas:
                s = mp.mpc(sigma, t)
                value = abs(mp.zeta(s))
                rows.append({"sigma": sigma, "t": t, "abs_zeta": float(value)})
    rows.sort(key=lambda r: r["abs_zeta"])
    # Keep separated seeds so one broad valley does not dominate every start.
    seeds: list[dict] = []
    for row in rows:
        if all(abs(row["t"] - old["t"]) > args.seed_t_separation or
               abs(row["sigma"] - old["sigma"]) > args.seed_sigma_separation
               for old in seeds):
            seeds.append(row)
        if len(seeds) >= args.seed_count:
            break

    refinements = []
    for seed in seeds:
        try:
            root = refine(str(seed["sigma"]), str(seed["t"]), dps=args.refine_dps,
                          max_steps=args.max_steps, max_height=int(args.max_height))
            refinements.append({"seed": seed, "refinement": root})
        except Exception as exc:  # keep the whole window resumable
            refinements.append({"seed": seed, "refinement": {"status": "ERROR", "error": repr(exc)}})

    converged = [x for x in refinements if x.get("refinement", {}).get("status") == "NUMERICAL_CONVERGENCE"]
    off_line = [x for x in converged if x["refinement"].get("classification") == "OFF_LINE_NUMERICAL_CANDIDATE"]
    config = {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()}
    result = {
        "schema": "zeta-window-scan-py3-v1",
        "status": "COMPLETED_NUMERICAL",
        "configuration": config,
        "grid_size": {"sigma": len(sigmas), "t": len(heights), "total": len(rows)},
        "best_grid_points": rows[: min(args.report_count, len(rows))],
        "seed_count": len(seeds),
        "refinements": refinements,
        "converged_count": len(converged),
        "off_line_numerical_count": len(off_line),
        "certified_off_line_zero": False,
        "interpretation": "Finite grid and free-sigma Newton diagnostics only. Every candidate requires an independent interval contour certificate.",
        "versions": {"python": platform.python_version(), "mpmath": mp.__version__},
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "elapsed_seconds": time.perf_counter() - started,
    }
    if args.output:
        atomic_json(args.output, result)
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--t-min", type=float, required=True)
    ap.add_argument("--t-max", type=float, required=True)
    ap.add_argument("--t-step", type=float, default=1.0)
    ap.add_argument("--sigma-min", type=float, default=0.52)
    ap.add_argument("--sigma-max", type=float, default=0.98)
    ap.add_argument("--sigma-step", type=float, default=0.02)
    ap.add_argument("--dps", type=int, default=40)
    ap.add_argument("--refine-dps", type=int, default=70)
    ap.add_argument("--max-height", type=float, default=100000)
    ap.add_argument("--max-steps", type=int, default=40)
    ap.add_argument("--seed-count", type=int, default=12)
    ap.add_argument("--seed-t-separation", type=float, default=3.0)
    ap.add_argument("--seed-sigma-separation", type=float, default=0.06)
    ap.add_argument("--report-count", type=int, default=24)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = scan(args)
    print(json.dumps({"status": result["status"], "grid_size": result["grid_size"],
                      "off_line_numerical_count": result["off_line_numerical_count"],
                      "output": str(args.output)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
