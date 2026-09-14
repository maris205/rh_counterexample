"""Density-preserving surrogate controls for short-interval prime signals.

For each logarithmic x-bin this script keeps the observed number of primes and
resamples their positions uniformly inside that bin.  It therefore preserves
coarse local prime density while destroying arithmetic ordering.  This is an
empirical null generator only; it is not a probabilistic theorem about primes
and cannot certify or disprove a zeta zero.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from short_interval_dynamics import (
    gap_signal,
    grid,
    prime_indicator_linear_sieve,
    short_signal,
    tone_power,
)


def density_surrogate(indicator: np.ndarray, n_bins: int, rng: np.random.Generator) -> np.ndarray:
    """Keep prime count in each log bin, randomize occupied positions."""
    n = len(indicator) - 1
    out = np.zeros_like(indicator)
    out[0] = 0
    # Include 2 in the first bin, and use half-open integer intervals.
    edges = np.unique(np.maximum(2, np.rint(np.geomspace(2, n + 1, n_bins + 1)).astype(np.int64)))
    edges[0] = 2
    edges[-1] = n + 1
    for lo, hi in zip(edges[:-1], edges[1:]):
        if hi <= lo:
            continue
        slots = np.arange(int(lo), int(hi), dtype=np.int64)
        k = int(np.count_nonzero(indicator[slots]))
        if k:
            chosen = rng.choice(slots, size=k, replace=False)
            out[chosen] = 1
    return out


def increment(y: np.ndarray, u: np.ndarray) -> np.ndarray:
    return np.gradient(y, u)


def summarize(indicator: np.ndarray, xs: np.ndarray, u: np.ndarray, theta: float,
              log_width: float, target: float, window: tuple[float, float]) -> dict:
    primes = np.flatnonzero(indicator).astype(np.int64)
    power, fixed, counts = short_signal(indicator, xs, theta, log_width)
    gap = gap_signal(primes, u)
    channels = {"short_power": power, "short_fixed_log": fixed, "gap": gap}
    rows = {}
    for name, y in channels.items():
        dy = increment(y, u)
        at = tone_power(u, dy, target, degree=1)
        ts = np.arange(window[0], window[1] + 1e-9, 0.05)
        scan = [tone_power(u, dy, float(t), degree=1) for t in ts]
        best = max(scan, key=lambda r: r["r2"])
        rows[name] = {"target": at, "window_best": best,
                      "rms_increment": float(np.sqrt(np.mean(dy * dy)))}
    target_r2 = [rows[k]["target"]["r2"] for k in channels]
    best_r2 = [rows[k]["window_best"]["r2"] for k in channels]
    return {"channels": rows,
            "target_consensus_min_r2": float(min(target_r2)),
            "target_consensus_geom_r2": float(np.prod(np.maximum(target_r2, 0.0)) ** (1.0 / len(target_r2))),
            "window_consensus_min_r2": float(min(best_r2)),
            "prime_count": int(len(primes)),
            "count_means": {"power": float(np.mean(counts[:, 0])), "fixed_log": float(np.mean(counts[:, 1]))}}


def run(n: int, samples: int, seed: int, reps: int, n_bins: int,
        theta: float, log_width: float, target: float,
        window: tuple[float, float]) -> dict:
    indicator, primes = prime_indicator_linear_sieve(n)
    xs, u = grid(n, samples)
    real = summarize(indicator, xs, u, theta, log_width, target, window)
    controls = []
    for rep in range(reps):
        rng = np.random.default_rng(seed + 7919 * (rep + 1))
        surrogate = density_surrogate(indicator, n_bins, rng)
        controls.append({"rep": rep, **summarize(surrogate, xs, u, theta, log_width, target, window)})
    def q(key: str) -> dict:
        vals = np.asarray([r[key] for r in controls], dtype=float)
        return {"mean": float(np.mean(vals)), "q95": float(np.quantile(vals, .95)),
                "min": float(np.min(vals)), "max": float(np.max(vals))}
    return {
        "status": "COMPLETED",
        "purpose": "Log-bin prime-count-preserving short-interval surrogate control; not a zeta-zero certificate",
        "configuration": {"n": n, "samples": samples, "seed": seed, "reps": reps,
                          "log_bins": n_bins, "theta": theta, "log_width": log_width,
                          "target_t": target, "window": list(window)},
        "real": real,
        "controls": controls,
        "control_summary": {k: q(k) for k in ("target_consensus_min_r2", "target_consensus_geom_r2", "window_consensus_min_r2")},
        "primes": int(len(primes)),
        "interpretation": "Surrogates retain coarse logarithmic density but destroy exact arithmetic locations; exceedance is only an empirical diagnostic.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1_000_000)
    ap.add_argument("--samples", type=int, default=1024)
    ap.add_argument("--seed", type=int, default=20260913)
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--log-bins", type=int, default=64)
    ap.add_argument("--theta", type=float, default=.5)
    ap.add_argument("--log-width", type=float, default=.5)
    ap.add_argument("--target", type=float, default=37.5)
    ap.add_argument("--window", default="37,38")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    window = tuple(float(x) for x in args.window.split(","))
    result = run(args.n, args.samples, args.seed, args.reps, args.log_bins,
                 args.theta, args.log_width, args.target, window)
    result["source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(args.output),
                      "real": result["real"]["target_consensus_min_r2"],
                      "q95": result["control_summary"]["target_consensus_min_r2"]["q95"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
