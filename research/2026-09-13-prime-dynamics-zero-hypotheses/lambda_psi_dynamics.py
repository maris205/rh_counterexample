"""Lambda/Psi and theta channel for prime-dynamics calibration.

This module is deliberately a numerical feature extractor.  It computes the
von Mangoldt weights Lambda(n), the Chebyshev functions

    psi(x)   = sum_{n <= x} Lambda(n),
    theta(x) = sum_{p <= x} log(p),

on a uniform log(x) grid, then reports detrended/locally differentiated
signals, fixed projections at known critical-line ordinates, and shuffled
controls.  A projection is a calibration statistic; it is not a zero
certificate and cannot establish an off-line zero of zeta.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np


def von_mangoldt_theta_linear_sieve(n: int) -> tuple[np.ndarray, np.ndarray]:
    """Return Lambda(0..n) and prime-only log weights via a linear sieve."""
    lam = np.zeros(n + 1, dtype=np.float64)
    theta_w = np.zeros(n + 1, dtype=np.float64)
    is_composite = np.zeros(n + 1, dtype=np.bool_)
    is_prime_power = np.zeros(n + 1, dtype=np.bool_)
    primes: list[int] = []
    for i in range(2, n + 1):
        if not is_composite[i]:
            primes.append(i)
            logp = math.log(i)
            lam[i] = logp
            theta_w[i] = logp
            is_prime_power[i] = True
        for p in primes:
            v = i * p
            if v > n:
                break
            is_composite[v] = True
            if i % p == 0:
                # v is a pure p-power iff i was one.  In either case its
                # von Mangoldt weight is log(p); the remaining composites get 0.
                is_prime_power[v] = bool(is_prime_power[i])
                lam[v] = math.log(p) if is_prime_power[i] else 0.0
                break
            is_prime_power[v] = False
            lam[v] = 0.0
    return lam, theta_w


def log_signal(weights: np.ndarray, samples: int, baseline: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Construct (weight cumulative - x)/sqrt(x) on a uniform log grid."""
    n = len(weights) - 1
    xs = np.unique(np.maximum(2, np.geomspace(2, n, samples).astype(np.int64)))
    cumulative = np.cumsum(weights, dtype=np.float64)
    cumulative_x = cumulative[xs]
    u = np.log(xs.astype(np.float64))
    if baseline:
        y = (cumulative_x - xs.astype(np.float64)) / np.sqrt(xs.astype(np.float64))
    else:
        y = cumulative_x / np.sqrt(xs.astype(np.float64))
    ug = np.linspace(float(u[0]), float(u[-1]), len(xs))
    yg = np.interp(ug, u, y)
    return ug, yg


def top_spectrum(u: np.ndarray, y: np.ndarray, count: int = 8) -> list[dict]:
    if len(y) < 8:
        return []
    z = y - np.polyval(np.polyfit(u, y, 1), u)
    z = z * np.hanning(len(z))
    power = np.abs(np.fft.rfft(z)) ** 2
    power[0] = 0.0
    order = np.argsort(power)[::-1][:count]
    span = float(u[-1] - u[0])
    return [{"bin": int(k), "angular_frequency_t": float(2.0 * np.pi * k / span),
             "power": float(power[k])} for k in order]


def tone_power(u: np.ndarray, y: np.ndarray, t: float, detrend_degree: int = 3) -> dict:
    if len(y) < 8:
        return {"t": float(t), "r2": 0.0, "amplitude": 0.0, "phase": 0.0}
    degree = max(0, min(int(detrend_degree), len(y) - 2))
    z = y - np.polyval(np.polyfit(u, y, degree), u)
    design = np.column_stack((np.cos(t * u), np.sin(t * u)))
    coef, *_ = np.linalg.lstsq(design, z, rcond=None)
    fitted = design @ coef
    variance = float(np.sum(z * z))
    explained = float(np.sum(fitted * fitted))
    return {"t": float(t), "r2": float(explained / variance) if variance else 0.0,
            "amplitude": float(np.hypot(coef[0], coef[1])),
            "phase": float(math.atan2(coef[1], coef[0]))}


def train_holdout(u: np.ndarray, y: np.ndarray, split: float = 0.67) -> dict:
    cut = max(8, min(len(y) - 8, int(len(y) * split)))
    peaks = top_spectrum(u[:cut], y[:cut], count=4)
    if not peaks:
        return {"train": [], "selected": None, "holdout": None}
    t = float(peaks[0]["angular_frequency_t"])
    return {"train": peaks, "selected": t,
            "train_projection": tone_power(u[:cut], y[:cut], t),
            "holdout_projection": tone_power(u[cut:], y[cut:], t)}


def fixed_train_holdout(u: np.ndarray, y: np.ndarray, t: float, split: float,
                        degree: int = 3) -> dict:
    cut = max(8, min(len(y) - 8, int(len(y) * split)))
    return {"t": float(t), "train_projection": tone_power(u[:cut], y[:cut], t, degree),
            "holdout_projection": tone_power(u[cut:], y[cut:], t, degree)}


def log_increment(u: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.gradient(y, u)


def shuffled_weights(weights: np.ndarray, rng: np.random.Generator,
                     block_size: int | None) -> np.ndarray:
    out = weights.copy()
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


KNOWN_T = [14.134725141734694, 21.022039638771555, 25.01085758014569,
           30.424876125859513, 32.93506158773919]


def channel_record(u: np.ndarray, y: np.ndarray, splits: tuple[float, ...]) -> dict:
    dy = log_increment(u, y)
    return {"rms": float(np.sqrt(np.mean(y * y))),
            "top_spectrum": top_spectrum(u, y),
            "train_holdout": train_holdout(u, y),
            "increment_rms": float(np.sqrt(np.mean(dy * dy))),
            "increment_train_holdout": train_holdout(u, dy),
            "known_critical_line": {
                str(t): {str(split): fixed_train_holdout(u, y, t, split, 3)
                         for split in splits}
                for t in KNOWN_T},
            "known_critical_line_increment": {
                str(t): {str(split): fixed_train_holdout(u, dy, t, split, 1)
                         for split in splits}
                for t in KNOWN_T}}


def run(n: int, samples: int, seed: int, control_reps: int,
        block_sizes: tuple[int, ...], splits: tuple[float, ...]) -> dict:
    rng = np.random.default_rng(seed)
    lam, theta_w = von_mangoldt_theta_linear_sieve(n)
    u, psi = log_signal(lam, samples)
    _, theta = log_signal(theta_w, samples)
    channels = {"psi_error": channel_record(u, psi, splits),
                "theta_error": channel_record(u, theta, splits)}
    controls: dict[str, list[dict]] = {}
    for block in (None,) + block_sizes:
        label = "global_shuffle" if block is None else f"block_shuffle_{block}"
        rows = []
        for rep in range(control_reps):
            rr = np.random.default_rng(seed + 1009 * (rep + 1) + (block or 0))
            ls = shuffled_weights(lam, rr, block)
            ts = shuffled_weights(theta_w, rr, block)
            us, pys = log_signal(ls, samples)
            _, ths = log_signal(ts, samples)
            rows.append({"rep": rep, "psi_error": channel_record(us, pys, splits),
                         "theta_error": channel_record(us, ths, splits)})
        controls[label] = rows
    return {"status": "COMPLETED",
            "purpose": "Lambda/Psi/theta feature calibration; not a zeta-zero certificate",
            "configuration": {"n": n, "samples": samples, "seed": seed,
                               "control_reps": control_reps, "block_sizes": list(block_sizes),
                               "splits": list(splits)},
            "log_range": [float(u[0]), float(u[-1])],
            "weights": {"lambda_nonzero": int(np.count_nonzero(lam)),
                        "prime_nonzero": int(np.count_nonzero(theta_w))},
            "channels": channels, "controls": controls,
            "interpretation": "A common frequency must beat large-block/global controls and survive held-out ranges; this remains heuristic until an actual zeta zero is independently certified."}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1_000_000)
    ap.add_argument("--samples", type=int, default=2048)
    ap.add_argument("--seed", type=int, default=20260913)
    ap.add_argument("--control-reps", type=int, default=4)
    ap.add_argument("--block-sizes", default="100000,1000000")
    ap.add_argument("--splits", default="0.55,0.67,0.80")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.n, args.samples, args.seed, args.control_reps,
                 tuple(int(x) for x in args.block_sizes.split(",") if x.strip()),
                 tuple(float(x) for x in args.splits.split(",") if x.strip()))
    result["source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(args.output),
                      "n": args.n, "samples": args.samples}, ensure_ascii=False))


if __name__ == "__main__":
    main()
