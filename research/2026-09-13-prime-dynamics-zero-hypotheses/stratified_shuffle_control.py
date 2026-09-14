"""Density-preserving shuffle controls for the prime-dynamics demodulator.

These controls are empirical finite-sample nulls.  They are deliberately
stronger than a global permutation but are not probabilistic models for the
Möbius or von Mangoldt sequences.  Two transformations are compared:

* ``block_permutation``: preserve every block's complete multiset and permute
  the order of blocks;
* ``within_block_shuffle``: preserve each block's exact multiset (and hence
  its local density and weighted sum), while randomising the order inside it.

The score is computed on log-x cumulative signals followed by a local log
increment, as in ``multi_grid_demod``.  We report q95 at t=37.5 and for the
blind maximum over 4<=t<=40 after excluding known zeta ordinates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from mertens_dynamics import mobius_sieve
from lambda_psi_dynamics import von_mangoldt_theta_linear_sieve
from multi_grid_demod import KNOWN_T, cumulative_grid, demod_scan


def block_permutation(weights: np.ndarray, rng: np.random.Generator,
                      block_size: int) -> np.ndarray:
    """Permute whole local-density blocks, retaining each block's contents."""
    body = np.asarray(weights[1:], dtype=np.float64)
    size = int(block_size)
    starts = list(range(0, len(body), size))
    order = rng.permutation(len(starts))
    blocks = [body[s:min(len(body), s + size)] for s in starts]
    out = np.zeros_like(weights, dtype=np.float64)
    out[1:] = np.concatenate([blocks[int(i)] for i in order])
    return out


def within_block_shuffle(weights: np.ndarray, rng: np.random.Generator,
                         block_size: int) -> np.ndarray:
    """Shuffle values within each block, retaining block sum and density."""
    body = np.asarray(weights[1:], dtype=np.float64)
    size = int(block_size)
    out_body = body.copy()
    for start in range(0, len(body), size):
        rng.shuffle(out_body[start:min(len(body), start + size)])
    out = np.zeros_like(weights, dtype=np.float64)
    out[1:] = out_body
    return out


def global_shuffle(weights: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    out = np.asarray(weights, dtype=np.float64).copy()
    rng.shuffle(out[1:])
    return out


def score(cumulative: np.ndarray, n: int, samples: int, phase: float,
          channel: str, t_grid: np.ndarray) -> tuple[float, float, float]:
    u, y = cumulative_grid(cumulative, n, samples, phase, channel)
    dy = np.gradient(y, u)
    rows = demod_scan(u, dy, t_grid, 1)
    candidate = min(rows, key=lambda r: abs(r["t"] - 37.5))
    blind = [r["r2"] for r in rows if np.min(np.abs(KNOWN_T - r["t"])) >= 0.35]
    return float(candidate["r2"]), float(max(blind) if blind else 0.0), float(
        rows[int(np.argmax([r["r2"] for r in rows]))]["t"])


def run(n: int, samples: int, phases: tuple[float, ...], block_size: int,
        reps: int, seed: int, t_step: float) -> dict:
    mu = mobius_sieve(n)
    lam, theta = von_mangoldt_theta_linear_sieve(n)
    channels = {"mertens": mu, "psi": lam, "theta": theta}
    t_grid = np.arange(4.0, 40.0 + 0.5 * t_step, t_step)
    methods = {"global_shuffle": lambda w, r: global_shuffle(w, r),
               "block_permutation": lambda w, r: block_permutation(w, r, block_size),
               "within_block_shuffle": lambda w, r: within_block_shuffle(w, r, block_size)}
    observed = []
    controls = []
    for phase in phases:
        for channel, weights in channels.items():
            c = np.cumsum(weights, dtype=np.float64)
            cand, blind, top_t = score(c, n, samples, phase, channel, t_grid)
            observed.append({"phase": phase, "channel": channel,
                             "candidate_r2": cand, "blind_top_r2": blind,
                             "blind_top_t": top_t})
            for method_index, (method, transform) in enumerate(methods.items()):
                cand_scores, blind_scores, top_ts = [], [], []
                for rep in range(reps):
                    # Avoid Python's salted hash so JSON results are reproducible.
                    local_seed = seed + 100003 * method_index + 1009 * rep \
                        + 97 * list(channels).index(channel) + int(round(phase * 10000))
                    rng = np.random.default_rng(local_seed)
                    shuffled = transform(weights, rng)
                    c_shuf = np.cumsum(shuffled, dtype=np.float64)
                    ca, bl, tt = score(c_shuf, n, samples, phase, channel, t_grid)
                    cand_scores.append(ca); blind_scores.append(bl); top_ts.append(tt)
                controls.append({"phase": phase, "channel": channel, "method": method,
                                 "block_size": block_size, "reps": reps,
                                 "candidate_t": 37.5,
                                 "candidate_q95": float(np.quantile(cand_scores, .95)),
                                 "blind_q95": float(np.quantile(blind_scores, .95)),
                                 "candidate_mean": float(np.mean(cand_scores)),
                                 "blind_mean": float(np.mean(blind_scores)),
                                 "candidate_scores": cand_scores,
                                 "blind_scores": blind_scores,
                                 "top_t_values": top_ts})
    return {"status": "COMPLETED", "purpose": "empirical density-preserving shuffle controls; heuristic only",
            "configuration": {"n": n, "samples": samples, "phases": list(phases),
                               "block_size": block_size, "reps": reps,
                               "seed": seed, "t_min": 4.0, "t_max": 40.0,
                               "t_step": t_step},
            "known_ordinates_excluded": KNOWN_T.tolist(),
            "observed": observed, "controls": controls,
            "interpretation": "A q95 exceedance is only unusual relative to these finite-sample transformations; it is not a zero certificate or a theorem-level null model."}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1_000_000)
    ap.add_argument("--samples", type=int, default=1024)
    ap.add_argument("--phases", default="0,0.05,0.1")
    ap.add_argument("--block-size", type=int, default=100_000)
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--seed", type=int, default=20260913)
    ap.add_argument("--t-step", type=float, default=0.1)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.n, args.samples, tuple(float(x) for x in args.phases.split(",") if x.strip()),
                 args.block_size, args.reps, args.seed, args.t_step)
    result["source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(args.output),
                      "observed": len(result["observed"]), "controls": len(result["controls"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
