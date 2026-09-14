"""Mertens-channel calibration for the family-level zero benchmark.

This is a feature extractor, not a RH test.  It computes M(x), a log-scale
signal M(x)/sqrt(x), shuffled controls, and a synthetic known-spectrum control.
The synthetic control is used to measure frequency leakage before interpreting
any arithmetic data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np


def mobius_sieve(n: int) -> np.ndarray:
    """Linear sieve for mu(1..n), returned with index equal to the integer."""
    mu = np.zeros(n + 1, dtype=np.int8)
    primes: list[int] = []
    is_composite = np.zeros(n + 1, dtype=np.bool_)
    mu[1] = 1
    for i in range(2, n + 1):
        if not is_composite[i]:
            primes.append(i)
            mu[i] = -1
        for p in primes:
            v = i * p
            if v > n:
                break
            is_composite[v] = True
            if i % p == 0:
                mu[v] = 0
                break
            mu[v] = -mu[i]
    return mu


def log_signal(mu: np.ndarray, samples: int) -> tuple[np.ndarray, np.ndarray]:
    n = len(mu) - 1
    xs = np.unique(np.maximum(2, np.geomspace(2, n, samples).astype(np.int64)))
    cumulative = np.cumsum(mu, dtype=np.int64)
    m = cumulative[xs - 1]
    u = np.log(xs.astype(np.float64))
    y = m.astype(np.float64) / np.sqrt(xs.astype(np.float64))
    # Resample on a uniform log grid so FFT frequencies have a direct meaning.
    ug = np.linspace(float(u[0]), float(u[-1]), len(xs))
    yg = np.interp(ug, u, y)
    return ug, yg


def top_spectrum(u: np.ndarray, y: np.ndarray, count: int = 8) -> list[dict]:
    if len(y) < 8:
        return []
    z = y - np.polyval(np.polyfit(u, y, 1), u)
    z = z * np.hanning(len(z))
    coeff = np.fft.rfft(z)
    power = np.abs(coeff) ** 2
    power[0] = 0.0
    order = np.argsort(power)[::-1][:count]
    span = float(u[-1] - u[0])
    return [
        {
            "bin": int(k),
            "angular_frequency_t": float(2.0 * np.pi * k / span),
            "power": float(power[k]),
        }
        for k in order
    ]


def tone_power(u: np.ndarray, y: np.ndarray, t: float, detrend_degree: int = 3) -> dict:
    """Project a detrended signal onto a fixed angular frequency."""
    if len(y) < 8:
        return {"t": float(t), "r2": 0.0, "amplitude": 0.0}
    degree = max(0, min(int(detrend_degree), len(y) - 2))
    z = y - np.polyval(np.polyfit(u, y, degree), u)
    design = np.column_stack((np.cos(t * u), np.sin(t * u)))
    coef, *_ = np.linalg.lstsq(design, z, rcond=None)
    fitted = design @ coef
    variance = float(np.sum(z * z))
    explained = float(np.sum(fitted * fitted))
    return {
        "t": float(t),
        "r2": float(explained / variance) if variance else 0.0,
        "amplitude": float(np.hypot(coef[0], coef[1])),
        "phase": float(math.atan2(coef[1], coef[0])),
    }


def train_holdout(u: np.ndarray, y: np.ndarray, split: float = 0.67) -> dict:
    cut = max(8, min(len(y) - 8, int(len(y) * split)))
    train_u, train_y = u[:cut], y[:cut]
    hold_u, hold_y = u[cut:], y[cut:]
    peaks = top_spectrum(train_u, train_y, count=4)
    if not peaks:
        return {"train": [], "selected": None, "holdout": None}
    selected = float(peaks[0]["angular_frequency_t"])
    return {
        "train": peaks,
        "selected": selected,
        "train_projection": tone_power(train_u, train_y, selected),
        "holdout_projection": tone_power(hold_u, hold_y, selected),
    }


def fixed_train_holdout(u: np.ndarray, y: np.ndarray, t: float, split: float = 0.67,
                        detrend_degree: int = 3) -> dict:
    cut = max(8, min(len(y) - 8, int(len(y) * split)))
    return {
        "t": float(t),
        "train_projection": tone_power(u[:cut], y[:cut], t, detrend_degree),
        "holdout_projection": tone_power(u[cut:], y[cut:], t, detrend_degree),
    }


def log_increment(u: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Local derivative in log(x), reducing cumulative-shape leakage."""
    return np.gradient(y, u)


def shuffled_signal(mu: np.ndarray, rng: np.random.Generator, block_size: int | None) -> np.ndarray:
    out = mu.copy()
    if block_size is None:
        body = out[1:]
        rng.shuffle(body)
        out[1:] = body
        return out
    for start in range(1, len(out), block_size):
        stop = min(len(out), start + block_size)
        body = out[start:stop]
        rng.shuffle(body)
        out[start:stop] = body
    return out


def synthetic_signal(u: np.ndarray, sigma: float, t: float, phase: float) -> np.ndarray:
    return np.exp((sigma - 0.5) * u) * np.cos(t * u + phase)


def run(n: int, samples: int, seed: int, control_reps: int = 8,
        block_sizes: tuple[int, ...] = (64, 256, 1024),
        splits: tuple[float, ...] = (0.55, 0.67, 0.80)) -> dict:
    rng = np.random.default_rng(seed)
    mu = mobius_sieve(n)
    u, y = log_signal(mu, samples)
    dy = log_increment(u, y)
    controls = {}
    for label, block in (("global_shuffle", None), ("block_shuffle_256", 256)):
        us, ys = log_signal(shuffled_signal(mu, rng, block), samples)
        controls[label] = {
            "rms": float(np.sqrt(np.mean(ys * ys))),
            "top_spectrum": top_spectrum(us, ys),
            "train_holdout": train_holdout(us, ys),
            "increment_train_holdout": train_holdout(us, log_increment(us, ys)),
        }

    # Replicated controls are the primary null distribution.  Fixed-frequency
    # projections prevent a low-frequency FFT winner from dominating the test.
    control_replicates: dict[str, list[dict]] = {}
    for block_size in block_sizes:
        label = f"block_shuffle_{block_size}"
        rows = []
        for rep in range(control_reps):
            rep_rng = np.random.default_rng(seed + 1009 * (rep + 1) + block_size)
            us, ys = log_signal(shuffled_signal(mu, rep_rng, block_size), samples)
            first_zero_t = 14.13472514173469379045725198356247
            rows.append({
                "rep": rep,
                "rms": float(np.sqrt(np.mean(ys * ys))),
                "train_holdout": train_holdout(us, ys),
                "fixed_first_zero": {
                    str(split): fixed_train_holdout(us, ys, first_zero_t, split=split,
                                                    detrend_degree=3)
                    for split in splits
                },
                "fixed_first_zero_increment": {
                    str(split): fixed_train_holdout(
                        us, log_increment(us, ys), first_zero_t, split=split,
                        detrend_degree=1)
                    for split in splits
                },
            })
        control_replicates[label] = rows

    # Calibration: frequencies are deliberately inside the resolvable range.
    sigma_cal, t_cal, phase_cal = 0.58, 7.0, 0.31
    synthetic = synthetic_signal(u, sigma_cal, t_cal, phase_cal)
    # First ordinates are used only as known critical-line calibration probes.
    # They are not fitted as evidence for any off-line zero.
    known_critical_ordinates = [
        14.134725141734693790457251983562470270784257115699,
        21.022039638771554992628479593896902777334340524902,
        25.010857580145688763213790992562821818659549672557,
        30.424876125859513210311897530584091320181560023715,
        32.935061587739189690662368964074903488812207327452,
    ]
    return {
        "status": "COMPLETED",
        "purpose": "feature calibration; not a zeta-zero certificate",
        "configuration": {"n": n, "samples": samples, "seed": seed,
                           "splits": list(splits)},
        "mu_counts": {
            "minus_one": int(np.count_nonzero(mu == -1)),
            "zero": int(np.count_nonzero(mu == 0)),
            "plus_one": int(np.count_nonzero(mu == 1)),
        },
        "log_range": [float(u[0]), float(u[-1])],
        "mertens": {
            "rms": float(np.sqrt(np.mean(y * y))),
            "top_spectrum": top_spectrum(u, y),
            "train_holdout": train_holdout(u, y),
            "increment_rms": float(np.sqrt(np.mean(dy * dy))),
            "increment_train_holdout": train_holdout(u, dy),
        },
        "controls": controls,
        "control_replicates": control_replicates,
        "synthetic_calibration": {
            "input_sigma": sigma_cal,
            "input_t": t_cal,
            "input_phase": phase_cal,
            "top_spectrum": top_spectrum(u, synthetic),
            "train_holdout": train_holdout(u, synthetic),
        },
        "known_critical_line_probes": [
            {"t": t,
             "mertens_projection": {
                 str(split): fixed_train_holdout(u, y, t, split=split,
                                                  detrend_degree=3)
                 for split in splits},
             "mertens_increment_projection": {
                 str(split): fixed_train_holdout(u, dy, t, split=split,
                                                  detrend_degree=1)
                 for split in splits},
             "synthetic_projection": {
                 str(split): fixed_train_holdout(u, synthetic, t, split=split,
                                                  detrend_degree=3)
                 for split in splits}}
            for t in known_critical_ordinates
        ],
        "interpretation": "A common frequency must beat both shuffled controls and survive held-out ranges before being linked to zeta zeros.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1_000_000)
    ap.add_argument("--samples", type=int, default=2048)
    ap.add_argument("--seed", type=int, default=20260913)
    ap.add_argument("--control-reps", type=int, default=8)
    ap.add_argument("--block-sizes", default="64,256,1024")
    ap.add_argument("--splits", default="0.55,0.67,0.80")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    block_sizes = tuple(int(x) for x in args.block_sizes.split(",") if x.strip())
    splits = tuple(float(x) for x in args.splits.split(",") if x.strip())
    result = run(args.n, args.samples, args.seed, args.control_reps, block_sizes, splits)
    result["source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
