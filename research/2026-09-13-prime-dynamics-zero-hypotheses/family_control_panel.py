"""Small, auditable family-level calibration panel.

This module compares coefficient-level diagnostics for two primitive Dirichlet
characters and a proven function-field analogue.  It is deliberately a
calibration fixture: no row is evidence for or against RH for zeta.

The periodic Dirichlet series are evaluated from the finite Hurwitz identity
  sum_{n>=1} a(n)n^{-s} = q^{-s} sum_{r=1}^q a(r) zeta(s,r/q),
using mpmath.  The finite-field panel uses the exact curve
E/F_7: y^2=x^3+x, whose numerator is 1+7 u^2.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Callable

import mpmath as mp


CHARACTERS: dict[str, tuple[int, tuple[int, ...], str]] = {
    # Entries are ordered by residues r=1,...,q, as required by the Hurwitz
    # identity q^{-s} sum_r a(r) zeta(s,r/q).
    "chi4": (4, (1, 0, -1, 0), "primitive real character modulo 4"),
    "chi5": (5, (1, -1, -1, 1, 0), "real quadratic character modulo 5"),
}


def coefficient(spec: tuple[int, tuple[int, ...], str], n: int) -> int:
    q, values, _ = spec
    # `values` is ordered by residues 1,...,q, while Python indexes from zero.
    return int(values[(n - 1) % q])


def mean_and_growth(spec: tuple[int, tuple[int, ...], str], n: int) -> dict[str, float]:
    vals = [coefficient(spec, k) for k in range(1, n + 1)]
    return {
        "sample_size": n,
        "mean": sum(vals) / n,
        "mean_abs": sum(abs(v) for v in vals) / n,
        "max_abs": max(abs(v) for v in vals),
    }


def multiplicativity_defect(spec: tuple[int, tuple[int, ...], str], n: int) -> dict[str, Any]:
    # Characters are completely multiplicative on integers, including zeros.
    # Evaluate all ordered pairs to make this smoke diagnostic deterministic.
    checked = 0
    bad = 0
    max_defect = 0
    examples: list[dict[str, int]] = []
    for a in range(1, n + 1):
        for b in range(1, n + 1):
            if math.gcd(a, b) != 1:
                continue
            checked += 1
            lhs = coefficient(spec, a * b)
            rhs = coefficient(spec, a) * coefficient(spec, b)
            d = abs(lhs - rhs)
            max_defect = max(max_defect, d)
            if d:
                bad += 1
                if len(examples) < 3:
                    examples.append({"a": a, "b": b, "lhs": lhs, "rhs": rhs})
    return {"pairs": checked, "bad_pairs": bad, "bad_fraction": bad / checked if checked else None,
            "max_abs_defect": max_defect, "examples": examples}


def hurwitz_value(spec: tuple[int, tuple[int, ...], str], s: complex) -> complex:
    q, values, _ = spec
    z = mp.mpc(s)
    return q ** (-z) * sum(values[r - 1] * mp.zeta(z, mp.mpf(r) / q) for r in range(1, q + 1))


def dirichlet_feature(spec: tuple[int, tuple[int, ...], str]) -> dict[str, Any]:
    sample_points = [(1.35, 2.1), (1.75, 5.0), (0.82, 3.7)]
    rows = []
    for re, im in sample_points:
        value = hurwitz_value(spec, complex(re, im))
        rows.append({"s": [re, im], "abs": float(abs(value)), "real": float(mp.re(value)),
                     "imag": float(mp.im(value))})
    return {"identity": "q^(-s) * sum_r a(r) HurwitzZeta(s,r/q)", "samples": rows}


def finite_field_fixture() -> dict[str, Any]:
    p = 7
    affine = 0
    points_by_x: list[int] = []
    for x in range(p):
        rhs = (x**3 + x) % p
        count = sum(1 for y in range(p) if (y * y) % p == rhs)
        points_by_x.append(count)
        affine += count
    projective = affine + 1
    trace = p + 1 - projective
    # P(u)=1-a*u+p*u^2, so with a=0 this is exactly 1+7u^2.
    roots = [complex(0.0, 1.0 / math.sqrt(p)), complex(0.0, -1.0 / math.sqrt(p))]
    re_s = [-math.log(abs(u), p) for u in roots]
    return {
        "curve": "E/F_7: y^2 = x^3 + x",
        "p": p,
        "affine_point_count": affine,
        "projective_point_count": projective,
        "points_per_x": points_by_x,
        "trace": trace,
        "numerator": "1 + 7*u^2",
        "numerator_roots": [[u.real, u.imag] for u in roots],
        "mapped_real_parts": re_s,
        "line_residual": max(abs(x - 0.5) for x in re_s),
        "status": "exact finite-field RH analogue calibration",
    }


def build_report(pair_n: int = 40) -> dict[str, Any]:
    families: dict[str, Any] = {}
    for name, spec in CHARACTERS.items():
        families[name] = {
            "modulus": spec[0], "description": spec[2], "period": list(spec[1]),
            "mean_growth": mean_and_growth(spec, pair_n),
            "multiplicativity": multiplicativity_defect(spec, pair_n),
            "dirichlet_feature": dirichlet_feature(spec),
            "status": "Euler-product positive-control fixture; GRH itself remains conjectural",
        }
    return {
        "schema": "family-control-panel-v1",
        "purpose": "structural calibration, not an RH certificate",
        "families": families,
        "finite_field": finite_field_fixture(),
        "davenport_heinrich": {
            "status": "disabled",
            "reason": "fixture requires high-precision functional-equation and argument-principle validation",
            "reported_off_line_zero": [0.8085171825, 85.6993484854],
            "use": "placeholder only; never treated as a certified zero",
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair-n", type=int, default=40)
    ap.add_argument("--output", type=Path, default=Path("runs/family-control-smoke.json"))
    args = ap.parse_args()
    report = build_report(max(1, args.pair_n))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "finite_field_line_residual": report["finite_field"]["line_residual"],
                      "chi4_bad_pairs": report["families"]["chi4"]["multiplicativity"]["bad_pairs"],
                      "chi5_bad_pairs": report["families"]["chi5"]["multiplicativity"]["bad_pairs"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
