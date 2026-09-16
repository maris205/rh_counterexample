"""Short-interval and prime-gap feature calibration.

This script is a numerical diagnostic only.  It generates prime indicators with a
linear sieve, measures prime counts in power-law and fixed-log windows, and builds
a normalized local-gap signal on a uniform log(x) grid.  Spectral peaks and
projections at known critical-line ordinates are instrument calibration; they are
not evidence for, or a certificate of, an off-line zero of zeta.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from known_ordinates import known_ordinates

KNOWN_T = known_ordinates(0.0, 40.0)


def prime_indicator_linear_sieve(n: int) -> tuple[np.ndarray, np.ndarray]:
    """Return indicator[0:n+1] and sorted prime indices."""
    indicator = np.zeros(n + 1, dtype=np.uint8)
    composite = np.zeros(n + 1, dtype=np.bool_)
    primes: list[int] = []
    for i in range(2, n + 1):
        if not composite[i]:
            primes.append(i)
            indicator[i] = 1
        for p in primes:
            v = i * p
            if v > n:
                break
            composite[v] = True
            if i % p == 0:
                break
    return indicator, np.asarray(primes, dtype=np.int64)


def grid(n: int, samples: int, trim: float = 0.0) -> tuple[np.ndarray, np.ndarray]:
    if n < 11 or samples < 16 or not 0 <= trim < 0.45:
        raise ValueError("require n>=11, samples>=16, and 0<=trim<0.45")
    lo, hi = math.log(10), math.log(n)
    margin = trim * (hi - lo)
    xs = np.unique(np.clip(np.exp(np.linspace(lo + margin, hi - margin, samples)).astype(np.int64), 10, n))
    return xs, np.log(xs.astype(np.float64))


def short_signal(indicator: np.ndarray, xs: np.ndarray, theta: float = 0.5,
                 log_width: float = 0.50) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return power-window and fixed-log-window standardized count residuals."""
    n = len(indicator) - 1
    prefix = np.cumsum(indicator, dtype=np.int64)
    x = xs.astype(np.int64)
    logx = np.log(x.astype(np.float64))

    h_power = np.maximum(4, np.rint(np.power(x.astype(np.float64), theta)).astype(np.int64))
    hi_power = np.minimum(n, x + h_power)
    cp = prefix[hi_power] - prefix[x]
    # The count uses a truncated window, so the baseline must use that same
    # window. At x=n the zero-support diagnostic is zero, not a negative spike.
    expected_power = (hi_power - x).astype(np.float64) / np.maximum(logx, 1.0)

    h_log = np.maximum(4, np.rint(x.astype(np.float64) * math.expm1(log_width)).astype(np.int64))
    hi_log = np.minimum(n, x + h_log)
    cl = prefix[hi_log] - prefix[x]
    expected_log = (hi_log - x).astype(np.float64) / np.maximum(logx, 1.0)

    power_resid = (cp.astype(np.float64) - expected_power) / np.sqrt(np.maximum(expected_power, 1e-9))
    log_resid = (cl.astype(np.float64) - expected_log) / np.sqrt(np.maximum(expected_log, 1e-9))
    return power_resid, log_resid, np.stack((cp, cl), axis=1)


def gap_signal(primes: np.ndarray, u: np.ndarray) -> np.ndarray:
    """Interpolate normalized consecutive-prime gaps onto a log grid."""
    if np.any(primes < 2):
        raise ValueError("prime/surrogate positions must be at least 2")
    if len(primes) < 4:
        return np.zeros_like(u)
    p = primes.astype(np.float64)
    gaps = np.diff(p)
    # Poisson heuristic predicts gap approximately log p; use a dimensionless
    # residual.  This is a feature signal, not a theorem about independence.
    vals = gaps / np.log(p[:-1]) - 1.0
    up = np.log(p[:-1])
    return np.interp(u, up, vals, left=float(vals[0]), right=float(vals[-1]))


def top_spectrum(u: np.ndarray, y: np.ndarray, count: int = 8) -> list[dict]:
    if len(y) < 8:
        return []
    deg = min(1, len(y) - 2)
    z = y - np.polyval(np.polyfit(u, y, deg), u)
    z = z * np.hanning(len(z))
    power = np.abs(np.fft.rfft(z)) ** 2
    power[0] = 0.0
    order = np.argsort(power)[::-1][:count]
    span = float(u[-1] - u[0])
    return [{"bin": int(k), "angular_frequency_t": float(2 * np.pi * k / span),
             "power": float(power[k])} for k in order]


def tone_power(u: np.ndarray, y: np.ndarray, t: float, degree: int = 3) -> dict:
    if len(y) < 8:
        return {"t": float(t), "r2": 0.0, "amplitude": 0.0, "phase": 0.0}
    degree = max(0, min(int(degree), len(y) - 2))
    z = y - np.polyval(np.polyfit(u, y, degree), u)
    design = np.column_stack((np.cos(t * u), np.sin(t * u)))
    coef, *_ = np.linalg.lstsq(design, z, rcond=None)
    fit = design @ coef
    den = float(np.sum(z * z))
    return {"t": float(t), "r2": float(np.sum(fit * fit) / den) if den else 0.0,
            "amplitude": float(np.hypot(coef[0], coef[1])),
            "phase": float(math.atan2(coef[1], coef[0]))}


def train_holdout(u: np.ndarray, y: np.ndarray, split: float = 0.67) -> dict:
    cut = max(8, min(len(y) - 8, int(len(y) * split)))
    peaks = top_spectrum(u[:cut], y[:cut], 4)
    if not peaks:
        return {"train": [], "selected": None, "train_projection": None,
                "holdout_projection": None}
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


def channel_record(u: np.ndarray, y: np.ndarray, splits: tuple[float, ...]) -> dict:
    dy = log_increment(u, y)
    return {"metric_interpretation": "Fixed-frequency holdout projections refit trend, amplitude and phase on holdout; not frozen prediction. FFT peaks are descriptive on the rounded log grid.",
            "rms": float(np.sqrt(np.mean(y * y))),
            "top_spectrum": top_spectrum(u, y),
            "train_holdout": train_holdout(u, y),
            "increment_rms": float(np.sqrt(np.mean(dy * dy))),
            "increment_train_holdout": train_holdout(u, dy),
            "known_critical_line": {
                str(t): {str(s): fixed_train_holdout(u, y, t, s, 3) for s in splits}
                for t in KNOWN_T},
            "known_critical_line_increment": {
                str(t): {str(s): fixed_train_holdout(u, dy, t, s, 1) for s in splits}
                for t in KNOWN_T}}


def shuffled_indicator(indicator: np.ndarray, rng: np.random.Generator,
                       block_size: int | None) -> np.ndarray:
    out = indicator.copy()
    if block_size is None:
        body = out[2:]
        rng.shuffle(body)
        out[2:] = body
        return out
    for start in range(2, len(out), block_size):
        stop = min(len(out), start + block_size)
        body = out[start:stop]
        rng.shuffle(body)
        out[start:stop] = body
    return out


def channels_for_indicator(indicator: np.ndarray, xs: np.ndarray, u: np.ndarray,
                           theta: float, log_width: float, splits: tuple[float, ...]) -> dict:
    p = np.flatnonzero(indicator).astype(np.int64)
    power, fixed, counts = short_signal(indicator, xs, theta, log_width)
    gap = gap_signal(p, u)
    return {"short_power_error": channel_record(u, power, splits),
            "short_fixed_log_error": channel_record(u, fixed, splits),
            "gap_residual": channel_record(u, gap, splits),
            "counts_summary": {"power_mean": float(np.mean(counts[:, 0]),),
                               "fixed_log_mean": float(np.mean(counts[:, 1]))}}


def run(n: int, samples: int, seed: int, control_reps: int,
        block_sizes: tuple[int, ...], splits: tuple[float, ...], theta: float,
        log_width: float) -> dict:
    indicator, primes = prime_indicator_linear_sieve(n)
    xs, u = grid(n, samples)
    channels = channels_for_indicator(indicator, xs, u, theta, log_width, splits)
    controls: dict[str, list[dict]] = {}
    for block in (None,) + block_sizes:
        label = "global_shuffle" if block is None else f"block_shuffle_{block}"
        rows = []
        for rep in range(control_reps):
            rr = np.random.default_rng(seed + 1009 * (rep + 1) + (block or 0))
            sh = shuffled_indicator(indicator, rr, block)
            rows.append({"rep": rep, **channels_for_indicator(sh, xs, u, theta, log_width, splits)})
        controls[label] = rows
    return {"status": "COMPLETED",
            "purpose": "Short-interval and prime-gap feature calibration; not a zeta-zero certificate",
            "configuration": {"n": n, "samples": samples, "seed": seed,
                               "control_reps": control_reps, "block_sizes": list(block_sizes),
                               "splits": list(splits), "theta": theta, "log_width": log_width},
            "log_range": [float(u[0]), float(u[-1])],
            "primes": int(len(primes)), "channels": channels, "controls": controls,
            "interpretation": "A frequency is only a calibration candidate if it survives local increments, multiple held-out cuts, large-block/global controls, and independent zeta evaluation."}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=1_000_000)
    ap.add_argument("--samples", type=int, default=2048)
    ap.add_argument("--seed", type=int, default=20260913)
    ap.add_argument("--control-reps", type=int, default=4)
    ap.add_argument("--block-sizes", default="100000,1000000")
    ap.add_argument("--splits", default="0.55,0.67,0.80")
    ap.add_argument("--theta", type=float, default=0.5)
    ap.add_argument("--log-width", type=float, default=0.5)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.n, args.samples, args.seed, args.control_reps,
                  tuple(int(x) for x in args.block_sizes.split(",") if x.strip()),
                  tuple(float(x) for x in args.splits.split(",") if x.strip()),
                  args.theta, args.log_width)
    result["source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(args.output),
                      "n": args.n, "samples": args.samples, "primes": result["primes"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
