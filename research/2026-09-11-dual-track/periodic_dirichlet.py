"""Exact periodic Dirichlet-series decomposition for the sieve-difference models.

For e(n) = 1[gcd(n+m,P)=1] - 1[gcd(n,P)=1], e is P-periodic and has mean zero.
For Re(s)>1, its Dirichlet series is exactly

    sum_{n>=1} e(n)n^{-s} = P^{-s} sum_{r=1}^P e(r) zeta(s,r/P).

The script records the mean and additive Fourier support and checks the identity
against a direct finite partial sum (the truncation error is reported).
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import mpmath as mp
import numpy as np


MODELS = [
    {"k": 3, "m": 22, "N": 26, "P": 30},
    {"k": 5, "m": 112, "N": 56, "P": 2310},
]


def sequence(m: int, p: int) -> list[int]:
    return [int(math.gcd(n + m, p) == 1) - int(math.gcd(n, p) == 1)
            for n in range(1, p + 1)]


def hurwitz_decomposition(values: list[int], p: int, s: mp.mpc) -> mp.mpc:
    return p ** (-s) * mp.fsum(
        values[r - 1] * mp.zeta(s, mp.mpf(r) / p)
        for r in range(1, p + 1)
    )


def direct_partial(values: list[int], p: int, s: mp.mpc, blocks: int = 80) -> mp.mpc:
    nmax = p * blocks
    return mp.fsum(values[(n - 1) % p] * mp.power(n, -s)
                   for n in range(1, nmax + 1))


def analyze(model: dict, s_values: list[mp.mpc]) -> dict:
    p = model["P"]
    values = sequence(model["m"], p)
    fft = np.fft.fft(np.asarray(values, dtype=float)) / p
    modes = np.flatnonzero(np.abs(fft) > 1e-12)
    checks = []
    with mp.workdps(60):
        for s in s_values:
            exact = hurwitz_decomposition(values, p, s)
            partial = direct_partial(values, p, s)
            checks.append({
                "s": [str(s.real), str(s.imag)],
                "decomposition_abs": float(abs(exact)),
                "partial_sum_abs": float(abs(partial)),
                "partial_difference": mp.nstr(abs(exact - partial), 12),
            })
    return {
        **model,
        "periodic_mean": sum(values) / p,
        "nonzero_fourier_modes": int(len(modes)),
        "max_fourier_amplitude": float(np.abs(fft[modes]).max()) if len(modes) else 0.0,
        "sample_checks": checks,
        "interpretation": (
            "The model is a finite Hurwitz-zeta combination with the pole at s=1 "
            "cancelled by its zero periodic mean; this is a structural diagnostic, "
            "not a RH-zero correspondence."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    s_values = [mp.mpc("1.7", "0.4"), mp.mpc("2.3", "1.1")]
    with mp.workdps(60):
        report = {
            "status": "COMPLETED",
            "identity": "E(s)=P^(-s) sum_r e(r) HurwitzZeta(s,r/P), Re(s)>1",
            "models": [analyze(model, s_values) for model in MODELS],
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"status": report["status"], "output": str(args.output)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
