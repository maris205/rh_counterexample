"""Joint finite-observable prediction screen; no zeta root finding.

Training selects a common frequency, each observable gets its own coefficients.
The primary families are Mertens, global psi, and local short-psi. Prime count
is a correlated diagnostic, not an extra vote. All fitted coefficients freeze
before held-out prediction. The grids/scales are correlated robustness checks.
"""
from dataclasses import dataclass
from functools import lru_cache
import math

import numpy as np
from scipy.special import expi

from known_ordinates import known_ordinates, known_mask
from mertens_dynamics import mobius_sieve
from lambda_psi_dynamics import von_mangoldt_theta_linear_sieve

CHANNELS = ("mertens", "psi", "prime_count", "short_psi")
PRIMARY = (0, 1, 3)
CONTROL_MODES = ("global_shuffle", "block_shuffle", "density_preserving")


def arithmetic_coefficients(n):
    mu = mobius_sieve(n)
    lam, theta = von_mangoldt_theta_linear_sieve(n)
    return {"mu": mu, "lambda": lam, "prime": (theta > 0).astype(np.uint8)}


def surrogate(coefficients, mode, rng, block_size, log_bins):
    """One shared permutation preserves cross-coefficient dependence.

    In the density mode, permutation is restricted to log bins: exact prime
    counts and coefficient multisets in every bin are retained. These are
    empirical stress models, not exchangeability claims about arithmetic.
    """
    n = len(coefficients["mu"]) - 1
    order = np.arange(n + 1)
    if mode == "global_shuffle":
        rng.shuffle(order[2:])
    elif mode == "block_shuffle":
        for lo in range(2, n + 1, block_size):
            rng.shuffle(order[lo:min(n + 1, lo + block_size)])
    elif mode == "density_preserving":
        edges = np.unique(np.rint(np.geomspace(2, n + 1, log_bins + 1)).astype(int))
        edges[0], edges[-1] = 2, n + 1
        for lo, hi in zip(edges[:-1], edges[1:]):
            rng.shuffle(order[lo:hi])
    else:
        raise ValueError(mode)
    return {name: a[order] for name, a in coefficients.items()}


@dataclass
class Cell:
    key: str
    n: int
    grid: int
    split: float
    u: np.ndarray
    y: np.ndarray
    cut: int
    train_end: int | None = None
    support_end_u: np.ndarray | None = None


def build_cells(coefficients, scales, grids, splits, theta=.525, x_min=100):
    cumul = {k: np.cumsum(v, dtype=np.float64) for k, v in coefficients.items()}
    cells = []
    for n in scales:
        lo, hi = math.log(x_min), math.log(.8 * n)
        for gi, (samples, trim) in enumerate(grids):
            u = np.linspace(lo + trim * (hi - lo), hi - trim * (hi - lo), samples)
            x = np.floor(np.exp(u)).astype(int)
            u = np.log(x.astype(float))
            h = np.maximum(4, np.rint(x.astype(float) ** theta).astype(int))
            if np.any(x + h > n):
                raise ValueError("grid requires a complete short interval below N")
            sqrtx = np.sqrt(x)
            y = np.column_stack((
                cumul["mu"][x] / sqrtx,
                (cumul["lambda"][x] - x) / sqrtx,
                (cumul["prime"][x] - (expi(np.log(x)) - expi(math.log(2)))) * np.log(x) / sqrtx,
                (cumul["lambda"][x + h] - cumul["lambda"][x] - h) / np.sqrt(h),
            ))
            for split in splits:
                cut = int(len(u) * split)
                train_end = min(cut, int(np.searchsorted(x + h, x[cut], side="left")))
                if min(train_end, len(u) - cut) < 16:
                    raise ValueError("need at least 16 train and holdout samples")
                cells.append(Cell(f"n{n}-g{gi}-s{split:g}", n, gi, split, u, y, cut,
                                  train_end, np.log((x + h).astype(float))))
    return cells


def designs(u, t, origin):
    v = u - origin
    baseline = np.column_stack((np.ones_like(v), v))
    full = np.column_stack((baseline, np.cos(t * v), np.sin(t * v)))
    return baseline, full


def prediction_gains(u, y, cut, t, origin, train_end=None):
    """All trend/tone coefficients use train only; no holdout detrending."""
    baseline, full = designs(u, t, origin)
    train_end = cut if train_end is None else train_end
    b0 = np.linalg.lstsq(baseline[:train_end], y[:train_end], rcond=None)[0]
    b1 = np.linalg.lstsq(full[:train_end], y[:train_end], rcond=None)[0]
    err0 = np.sum((y[cut:] - baseline[cut:] @ b0) ** 2, axis=0)
    err1 = np.sum((y[cut:] - full[cut:] @ b1) ** 2, axis=0)
    if np.any(err0 <= 1e-20) or not np.all(np.isfinite([err0, err1])):
        raise ValueError("degenerate or nonfinite holdout baseline: screen invalid")
    gains = (err0 - err1) / err0
    return gains, b1


@lru_cache(maxsize=32)
def scan_designs(u_tuple, frequencies, origin):
    u = np.asarray(u_tuple)
    baseline = designs(u, frequencies[0], origin)[0]
    matrices = np.stack([designs(u, t, origin)[1] for t in frequencies])
    return baseline, np.linalg.pinv(baseline), matrices, np.linalg.pinv(matrices)


def select_frequencies(u, y, frequencies, origin, top_k=3, separation=.5):
    """Called solely on the common absolute-u training prefix."""
    frequencies = tuple(float(t) for t in frequencies)
    b0, pinv0, matrices, inverses = scan_designs(tuple(u), frequencies, origin)
    baseline_error = np.sum((y - b0 @ (pinv0 @ y)) ** 2, axis=0)
    if np.any(baseline_error <= 1e-20) or not np.all(np.isfinite(baseline_error)):
        raise ValueError("degenerate or nonfinite training baseline: screen invalid")
    betas = np.einsum("tkm,mc->tkc", inverses, y)
    residual = y[None, :, :] - np.einsum("tmk,tkc->tmc", matrices, betas)
    error = np.sum(residual ** 2, axis=1)
    gain = np.divide(baseline_error[None, :] - error, baseline_error[None, :],
                     out=np.full_like(error, -1e6), where=baseline_error[None, :] > 1e-20)
    scores = np.min(gain[:, PRIMARY], axis=1)
    selected = []
    for idx in np.argsort(-scores, kind="stable"):
        t = frequencies[idx]
        if all(abs(t - x["t"]) >= separation for x in selected):
            selected.append({"t": t, "selection_train_score": float(scores[idx])})
            if len(selected) == top_k:
                break
    return selected


def evaluate(cells, frequencies, origin, top_k=3):
    # Selecting from all cells' training data could leak into a smaller
    # scale/cut's holdout. Use only the earliest absolute-u boundary instead.
    common_boundary = min(float(c.u[c.cut]) for c in cells)
    anchor = min(cells, key=lambda c: (c.n, c.grid, c.split))
    support_end = anchor.u if anchor.support_end_u is None else anchor.support_end_u
    prefix = support_end < common_boundary
    if np.count_nonzero(prefix) < 16:
        raise ValueError("common training prefix too short")
    selected = select_frequencies(anchor.u[prefix], anchor.y[prefix], frequencies, origin, top_k)
    candidates = []
    for selected_row in selected:
        records, primary_gains = [], []
        for cell in cells:
            train_end = cell.cut if cell.train_end is None else cell.train_end
            gains, beta = prediction_gains(cell.u, cell.y, cell.cut, selected_row["t"], origin, train_end)
            primary_gains.extend(float(gains[i]) for i in PRIMARY)
            records.append({
                "key": cell.key, "n": cell.n, "grid": cell.grid, "split": cell.split,
                "train_u_max": float(cell.u[train_end - 1]),
                "train_support_u_max": float(cell.support_end_u[train_end - 1]) if cell.support_end_u is not None else float(cell.u[train_end - 1]),
                "purged_samples": cell.cut - train_end,
                "holdout_u_min": float(cell.u[cell.cut]),
                "holdout_samples": len(cell.u) - cell.cut,
                "gains": dict(zip(CHANNELS, map(float, gains))),
                "train_coefficients": {name: list(map(float, beta[:, i])) for i, name in enumerate(CHANNELS)},
            })
        candidates.append({**selected_row, "joint_score": min(primary_gains),
                           "positive_in_every_primary_cell": all(g > 0 for g in primary_gains),
                           "cells": records})
    return {"selection_u_max": float(anchor.u[prefix][-1]),
            "selection_support_u_max": float(support_end[prefix][-1]),
            "earliest_holdout_u": common_boundary, "candidates": candidates,
            "max_statistic": max(c["joint_score"] for c in candidates)}


def empirical_p(observed, null_maxima):
    return (1 + sum(x >= observed for x in null_maxima)) / (len(null_maxima) + 1)


def gate(real, controls, required_reps, alpha=.05):
    complete = all(len(controls.get(mode, [])) == required_reps for mode in CONTROL_MODES)
    resolution_ok = 1 / (required_reps + 1) <= alpha
    rows = []
    for candidate in real["candidates"]:
        p = {mode: empirical_p(candidate["joint_score"], controls[mode])
             for mode in CONTROL_MODES if controls.get(mode)}
        passed = complete and resolution_ok and candidate["positive_in_every_primary_cell"] and all(
            p[mode] <= alpha for mode in CONTROL_MODES)
        rows.append({**candidate, "control_p": p, "passes_screen": bool(passed)})
    return {"gate_status": "EVALUATED" if complete and resolution_ok else "NOT_EVALUATED",
            "gate_reason": ("finite empirical joint prediction screen" if complete and resolution_ok
                            else "incomplete controls or Monte Carlo resolution insufficient"),
            "candidate_count": sum(row["passes_screen"] for row in rows) if complete and resolution_ok else None,
            "monte_carlo_resolution": 1 / (required_reps + 1), "tested_candidates": rows}
