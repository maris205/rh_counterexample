"""Transfer the log-grid detector to periodic Dirichlet coefficient families.

This is a method-sensitivity fixture, not a zero certificate.  A periodic
coefficient sequence is sampled through a weighted partial sum

    S_sigma(x) = sum_{n <= x} a(n) n**(-sigma),

on an evenly spaced log x grid.  We remove the cumulative shape by taking a
log-grid derivative, compute a top FFT list, and measure fixed-frequency
train/holdout projections.  Global and block permutation controls are rebuilt
from the coefficient sequence, so the same detector can be compared across
families without importing any zeta-specific assumptions.

The Davenport--Heilbronn fixture uses the corrected period-five coefficients
(1, kappa, -kappa, -1, 0), with

    kappa = (sqrt(10 - 2*sqrt(5)) - 2)/(sqrt(5) - 1),

and the reported numerical root near sigma=0.8085171825, t=85.6993484854.
The target is metadata for a sensitivity test only; no claim is made that a
periodic Dirichlet series root transfers to a Riemann-zeta zero.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


def dh_kappa() -> float:
    return (math.sqrt(10.0 - 2.0 * math.sqrt(5.0)) - 2.0) / (math.sqrt(5.0) - 1.0)


FAMILIES: dict[str, dict[str, Any]] = {
    "dh": {
        "description": "Davenport-Heilbronn period-five fixture",
        "period": [1.0, dh_kappa(), -dh_kappa(), -1.0, 0.0],
        "indexing": "a(n)=period[(n-1) mod q]",
        "target": {"sigma": 0.8085171824566374, "t": 85.6993484853776},
    },
    "chi4": {
        "description": "primitive real Dirichlet character modulo 4",
        "period": [1.0, 0.0, -1.0, 0.0],
        "indexing": "a(n)=period[(n-1) mod q], entries ordered by residues r=1,...,q",
        "target": {"sigma": 0.5, "t": 14.1347251417347},
    },
    "chi5": {
        "description": "real quadratic Dirichlet character modulo 5",
        "period": [1.0, -1.0, -1.0, 1.0, 0.0],
        "indexing": "a(n)=period[(n-1) mod q], entries ordered by residues r=1,...,q",
        "target": {"sigma": 0.5, "t": 14.1347251417347},
    },
}


def coefficient_array(period: list[float], n: int, residue_zero: bool = False) -> np.ndarray:
    p = np.asarray(period, dtype=np.float64)
    if residue_zero:
        return p[np.arange(1, n + 1) % len(p)]
    return p[np.arange(n) % len(p)]


def log_grid(n: int, samples: int, n_min: int = 16) -> tuple[np.ndarray, np.ndarray]:
    n_min = max(2, min(n_min, n // 2))
    u = np.linspace(math.log(n_min), math.log(n), samples, dtype=np.float64)
    idx = np.floor(np.exp(u)).astype(np.int64)
    idx = np.clip(idx, 1, n)
    return u, idx


def signal_from_coefficients(a: np.ndarray, u: np.ndarray, idx: np.ndarray, sigma: float) -> tuple[np.ndarray, np.ndarray]:
    n = np.arange(1, len(a) + 1, dtype=np.float64)
    weighted = a * np.power(n, -float(sigma))
    prefix = np.cumsum(weighted, dtype=np.float64)
    y = prefix[idx - 1]
    # This is the detector's primary signal.  The derivative suppresses the
    # constant limit of a convergent weighted Dirichlet sum and avoids treating
    # cumulative finite-window shape as an oscillatory zero.
    dy = np.gradient(y, u)
    dy = dy - np.polyval(np.polyfit(u, dy, 3), u)
    scale = float(np.std(dy))
    if scale > 0:
        dy = dy / scale
    return y, dy


def projection(y: np.ndarray, u: np.ndarray, t: float, train_end: int | None = None, degree: int = 3) -> dict[str, float]:
    n = len(y)
    cut = n if train_end is None else max(8, min(int(train_end), n - 4))
    cols = [u ** k for k in range(degree + 1)] + [np.cos(t * u), np.sin(t * u)]
    X = np.column_stack(cols)
    beta = np.linalg.lstsq(X[:cut], y[:cut], rcond=None)[0]
    pred = X @ beta
    hold = slice(cut, n)
    actual = y[hold]
    fitted = pred[hold]
    denom = float(np.sum((actual - np.mean(actual)) ** 2))
    r2 = 1.0 - float(np.sum((actual - fitted) ** 2)) / denom if denom > 1e-18 else None
    c, s = float(beta[-2]), float(beta[-1])
    return {
        "r2": r2,
        "amplitude": float(math.hypot(c, s)),
        "phase": float(math.atan2(-s, c)),
        "train_samples": cut,
        "holdout_samples": n - cut,
        "t": float(t),
    }


def split_projections(y: np.ndarray, u: np.ndarray, t: float, splits: list[float]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for split in splits:
        cut = int(round(float(split) * len(y)))
        out[str(split)] = projection(y, u, t, cut)
    return out


def top_spectrum(y: np.ndarray, u: np.ndarray, count: int = 8) -> list[dict[str, float]]:
    z = y - np.polyval(np.polyfit(u, y, 3), u)
    spec = np.fft.rfft(z)
    freq = 2.0 * math.pi * np.fft.rfftfreq(len(z), d=float(u[1] - u[0]))
    power = np.abs(spec) ** 2
    order = np.argsort(power[1:])[::-1] + 1
    rows = []
    for i in order[:count]:
        rows.append({"t": float(freq[i]), "power": float(power[i])})
    return rows


def shuffled(a: np.ndarray, rng: np.random.Generator, kind: str, block: int) -> np.ndarray:
    if kind == "global":
        return a[rng.permutation(len(a))]
    if kind == "block":
        b = max(1, int(block))
        # Shuffle *inside* each block.  Permuting whole blocks would be a
        # degenerate control for an exactly periodic sequence whenever the
        # block size is a multiple of its period: every block would be the
        # same word and the control would equal the signal.
        chunks = []
        for i in range(0, len(a), b):
            chunk = np.array(a[i : i + b], copy=True)
            rng.shuffle(chunk)
            chunks.append(chunk)
        return np.concatenate(chunks)
    raise ValueError(f"unknown control kind: {kind}")


def run_one(a: np.ndarray, u: np.ndarray, idx: np.ndarray, sigma: float, t: float, splits: list[float], top_count: int) -> dict[str, Any]:
    raw, signal = signal_from_coefficients(a, u, idx, sigma)
    return {
        "raw_prefix_range": [float(np.min(raw)), float(np.max(raw))],
        "signal_std": float(np.std(signal)),
        "top_spectrum": top_spectrum(signal, u, top_count),
        "fixed_target": split_projections(signal, u, t, splits),
    }


def markdown(report: dict[str, Any]) -> str:
    cfg = report["configuration"]
    lines = [
        "# Periodic-family detector transfer",
        "",
        "> This is a method-sensitivity experiment. It is not a Riemann-zeta zero certificate and does not transfer a zero of a periodic Dirichlet series to ζ.",
        "",
        f"Family: **{cfg['family']}** — {cfg['description']}",
        f"Period: `{cfg['period']}`; N={cfg['n']:,}; log-grid samples={cfg['samples']}; sigma={cfg['sigma']}; target t={cfg['target_t']}",
        "",
        "The primary signal is the derivative in log x of a weighted partial sum. Polynomial detrending and train/holdout splits are applied before fixed-frequency projection. Controls permute coefficients globally or in large blocks.",
        "",
        "## Target projection",
        "",
        "| split | R² | amplitude | phase |",
        "|---:|---:|---:|---:|",
    ]
    for split, row in report["signal"]["fixed_target"].items():
        lines.append(f"| {split} | {row['r2'] if row['r2'] is not None else 'null'} | {row['amplitude']:.6g} | {row['phase']:.6g} |")
    lines += ["", "## Top spectrum", "", "| t | power |", "|---:|---:|"]
    for row in report["signal"]["top_spectrum"]:
        lines.append(f"| {row['t']:.8f} | {row['power']:.6g} |")
    lines += ["", "## Controls", "", "| control | repetition | mean R² | mean amplitude |", "|---|---:|---:|---:|"]
    for kind, reps in report["controls"].items():
        rows = [r["fixed_target"] for r in reps]
        vals = [list(x.values())[0] for x in rows if x]
        r2 = [v["r2"] for v in vals if v["r2"] is not None]
        amp = [v["amplitude"] for v in vals]
        lines.append(f"| {kind} | {len(reps)} | {float(np.mean(r2)) if r2 else float('nan'):.6g} | {float(np.mean(amp)) if amp else float('nan'):.6g} |")
    lines += ["", "## Interpretation", "", "The target frequency is supplied as an external fixture parameter. A large projection only says that this detector responds to the chosen periodic coefficient signal at that frequency. It does not certify the reported Davenport–Heilbronn root, prove a functional equation, or imply an off-line zero of the Riemann zeta function.", ""]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=sorted(FAMILIES), default="dh")
    ap.add_argument("--n", type=int, default=200_000)
    ap.add_argument("--samples", type=int, default=2048)
    ap.add_argument("--sigma", type=float, default=None)
    ap.add_argument("--target-t", type=float, default=None)
    ap.add_argument("--splits", default="0.55,0.67,0.80")
    ap.add_argument("--control-reps", type=int, default=3)
    ap.add_argument("--block-size", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20260913)
    ap.add_argument("--top-count", type=int, default=8)
    ap.add_argument("--output", type=Path, default=Path("runs/family-detector-transfer.json"))
    args = ap.parse_args()
    if args.n < 100 or args.samples < 64:
        raise SystemExit("--n must be >=100 and --samples >=64")
    spec = FAMILIES[args.family]
    sigma = float(spec["target"]["sigma"] if args.sigma is None else args.sigma)
    target_t = float(spec["target"]["t"] if args.target_t is None else args.target_t)
    splits = [float(x) for x in args.splits.split(",") if x.strip()]
    period = list(spec["period"])
    # Every fixture is stored as a(1),...,a(q), matching the finite Hurwitz
    # identity used by family_control_panel.py.
    a = coefficient_array(period, args.n, residue_zero=False)
    u, idx = log_grid(args.n, args.samples)
    signal = run_one(a, u, idx, sigma, target_t, splits, args.top_count)
    rng = np.random.default_rng(args.seed)
    controls: dict[str, list[dict[str, Any]]] = {"global_shuffle": [], "block_shuffle": []}
    for rep in range(max(0, args.control_reps)):
        for kind in controls:
            aa = shuffled(a, rng, "global" if kind == "global_shuffle" else "block", args.block_size)
            controls[kind].append(run_one(aa, u, idx, sigma, target_t, splits, args.top_count))
    report: dict[str, Any] = {
        "schema": "family-detector-transfer-v1",
        "status": "COMPLETED",
        "purpose": "method sensitivity calibration only; not a zeta zero certificate",
        "configuration": {
            "family": args.family, "description": spec["description"], "period": period,
            "indexing": spec["indexing"], "n": args.n, "samples": args.samples,
            "sigma": sigma, "target_t": target_t, "target": spec["target"],
            "splits": splits, "control_reps": args.control_reps,
            "block_size": args.block_size, "seed": args.seed,
        },
        "signal": signal,
        "controls": controls,
        "interpretation": "Fixed target and family roots are external calibration metadata. Results test detector transfer only; they do not certify any zero of zeta or of the periodic Dirichlet series.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path = args.output.with_suffix(".md")
    md_path.write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(args.output), "markdown": str(md_path), "family": args.family}, ensure_ascii=False))


if __name__ == "__main__":
    main()
