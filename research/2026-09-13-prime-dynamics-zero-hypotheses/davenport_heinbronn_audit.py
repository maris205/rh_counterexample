"""High precision audit of the Davenport--Heilbronn negative control.

The period-five coefficients are (1, kappa, -kappa, -1, 0), where

    kappa = (sqrt(10 - 2*sqrt(5)) - 2)/(sqrt(5) - 1).

The Hurwitz identity is used for analytic continuation.  A second evaluation
uses the two complex primitive characters modulo five.  The completed function

    G(s) = (pi/5)^(-(s+1)/2) Gamma((s+1)/2) f(s)

satisfies G(s)=G(1-s).  A small argument-principle contour for G is included
as a numerical count only; the output is explicitly not a formal certificate.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import mpmath as mp


def kappa() -> mp.mpf:
    return (mp.sqrt(10 - 2 * mp.sqrt(5)) - 2) / (mp.sqrt(5) - 1)


def coeffs(k: mp.mpf | None = None) -> tuple[mp.mpf, ...]:
    k = kappa() if k is None else mp.mpf(k)
    return (mp.mpf(1), k, -k, mp.mpf(-1), mp.mpf(0))


def hurwitz_f(s: complex | mp.mpc, k: mp.mpf | None = None) -> mp.mpc:
    z = mp.mpc(s)
    a = coeffs(k)
    return mp.power(5, -z) * sum(a[r - 1] * mp.zeta(z, mp.mpf(r) / 5) for r in range(1, 6))


def character_l(s: complex | mp.mpc, conjugate: bool = False) -> mp.mpc:
    """Primitive character mod 5 with chi(2)=i, evaluated by Hurwitz identity."""
    z = mp.mpc(s)
    vals = (1, -1j if conjugate else 1j, 1j if conjugate else -1j, -1, 0)
    return mp.power(5, -z) * sum(vals[r - 1] * mp.zeta(z, mp.mpf(r) / 5) for r in range(1, 6))


def character_f(s: complex | mp.mpc) -> mp.mpc:
    z = mp.mpc(s)
    k = kappa()
    # [1,k,-k,-1] = A chi + conjugate(A) chi-bar, A=(1-i*k)/2.
    A = (1 - 1j * k) / 2
    return A * character_l(z) + mp.conj(A) * character_l(z, conjugate=True)


def completed(s: complex | mp.mpc) -> mp.mpc:
    z = mp.mpc(s)
    return mp.power(mp.pi / 5, -(z + 1) / 2) * mp.gamma((z + 1) / 2) * hurwitz_f(z)


def find_root(s0: complex | mp.mpc) -> mp.mpc:
    z0 = mp.mpc(s0)
    # Two nearby complex starts make this a genuine 2-D secant solve.
    return mp.findroot(hurwitz_f, (z0, z0 + mp.mpc('0.001', '0.001')),
                       solver="secant", verify=False, maxsteps=100,
                       tol=mp.eps * 10)


def contour(a: mp.mpf, b: mp.mpf, c: mp.mpf, d: mp.mpf, n: int) -> list[mp.mpc]:
    # Counter-clockwise rectangle, closed at the end.
    pts: list[mp.mpc] = []
    for j in range(n): pts.append(mp.mpc(a + (b - a) * j / n, c))
    for j in range(n): pts.append(mp.mpc(b, c + (d - c) * j / n))
    for j in range(n): pts.append(mp.mpc(b - (b - a) * j / n, d))
    for j in range(n): pts.append(mp.mpc(a, d - (d - c) * j / n))
    pts.append(pts[0])
    return pts


def argument_count(a: str, b: str, c: str, d: str, n: int = 100) -> dict[str, Any]:
    pts = contour(mp.mpf(a), mp.mpf(b), mp.mpf(c), mp.mpf(d), n)
    vals = [completed(z) for z in pts]
    phases = [float(mp.arg(v)) for v in vals]
    # numpy is deliberately avoided: unwrapping a short contour is trivial.
    unwrapped = [phases[0]]
    for p in phases[1:]:
        q = p
        while q - unwrapped[-1] > mp.pi: q -= 2 * mp.pi
        while q - unwrapped[-1] < -mp.pi: q += 2 * mp.pi
        unwrapped.append(q)
    winding = (unwrapped[-1] - unwrapped[0]) / (2 * mp.pi)
    return {
        "box": [a, b, c, d], "samples_per_edge": n,
        "winding_estimate": float(winding),
        "nearest_integer": int(mp.nint(winding)),
        "min_abs_completed_on_contour": float(min(abs(v) for v in vals)),
        "status": "numerical_argument_principle_count; contour and precision checks remain required",
    }


def build_report(dps: int = 80, contour_samples: int = 100) -> dict[str, Any]:
    mp.mp.dps = dps
    reported = mp.mpc('0.8085171825', '85.6993484854')
    root = find_root(reported)
    old_k = (mp.sqrt(10 - mp.sqrt(5)) - 2) / (mp.sqrt(5) - 1)
    f_report = hurwitz_f(reported)
    f_root = hurwitz_f(root)
    return {
        "schema": "davenport-heinbronn-audit-v1",
        "dps": dps,
        "purpose": "negative control for function-family experiments; not an RH statement",
        "kappa": mp.nstr(kappa(), dps - 5),
        "period": [mp.nstr(x, 20) for x in coeffs()],
        "reported_point": ["0.8085171825", "85.6993484854"],
        "reported_abs_f": float(abs(f_report)),
        "old_alpha_abs_f_at_reported": float(abs(hurwitz_f(reported, old_k))),
        "root": [mp.nstr(mp.re(root), dps - 5), mp.nstr(mp.im(root), dps - 5)],
        "root_abs_f": float(abs(f_root)),
        "character_parameterization_abs_difference": float(abs(hurwitz_f(root) - character_f(root))),
        "functional_equation_abs_defect": float(abs(completed(root) - completed(1 - root))),
        "argument_principle": argument_count('0.75', '0.85', '85.65', '85.75', contour_samples),
        "status": "validated numerical negative-control fixture; no formal zero certificate",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dps", type=int, default=80)
    ap.add_argument("--contour-samples", type=int, default=100)
    ap.add_argument("--output", type=Path, default=Path("runs/davenport-heinbronn-audit.json"))
    args = ap.parse_args()
    report = build_report(args.dps, args.contour_samples)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "root": report["root"],
                      "root_abs_f": report["root_abs_f"],
                      "argument_count": report["argument_principle"]["nearest_integer"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
