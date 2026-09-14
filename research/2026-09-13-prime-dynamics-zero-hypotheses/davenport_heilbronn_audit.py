"""High-precision sanity check for the Davenport--Heilbronn fixture.

This is a family-control diagnostic, not a Riemann-zeta computation and not
an argument-principle certificate.  The standard period-five coefficients are
generated from the two conjugate characters modulo five with
kappa=(sqrt(10-2*sqrt(5))-2)/(sqrt(5)-1).
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import mpmath as mp


def kappa() -> mp.mpf:
    return (mp.sqrt(10 - 2 * mp.sqrt(5)) - 2) / (mp.sqrt(5) - 1)


def coefficients() -> list[mp.mpf]:
    c = kappa()
    return [mp.mpf(1), c, -c, mp.mpf(-1), mp.mpf(0)]


def dh(s: mp.mpc) -> mp.mpc:
    """Finite Hurwitz-zeta continuation of the period-five Dirichlet series."""
    a = coefficients()
    return mp.power(5, -s) * sum(a[r - 1] * mp.zeta(s, mp.mpf(r) / 5)
                                   for r in range(1, 6))


def refine(seed: mp.mpc) -> mp.mpc:
    return mp.findroot(dh, (seed, seed + mp.mpc("0.0001", "0.0001")),
                       solver="secant", tol=mp.mpf("1e-70"), maxsteps=80)


def multiplicativity_defect(limit: int = 80) -> int:
    a = [0] + [coefficients()[(n - 1) % 5] for n in range(1, limit + 1)]
    bad = 0
    for m in range(1, limit + 1):
        for n in range(1, limit // m + 1):
            if abs(a[m * n] - a[m] * a[n]) > mp.mpf("1e-60"):
                bad += 1
    return bad


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dps", type=int, default=100)
    ap.add_argument("--sigma", default="0.8085171825")
    ap.add_argument("--t", default="85.6993484854")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    mp.mp.dps = args.dps
    seed = mp.mpc(args.sigma, args.t)
    root = refine(seed)
    result = {
        "status": "COMPLETED",
        "purpose": "Davenport-Heilbronn family-control residual; not an RH or zeta certificate",
        "precision_dps": args.dps,
        "kappa": mp.nstr(kappa(), args.dps),
        "period5_coefficients": [mp.nstr(x, args.dps) for x in coefficients()],
        "seed": {"sigma": args.sigma, "t": args.t,
                 "abs_value": mp.nstr(abs(dh(seed)), args.dps),
                 "value": [mp.nstr(mp.re(dh(seed)), args.dps),
                           mp.nstr(mp.im(dh(seed)), args.dps)]},
        "refined_root": {"sigma": mp.nstr(mp.re(root), args.dps),
                         "t": mp.nstr(mp.im(root), args.dps),
                         "abs_value": mp.nstr(abs(dh(root)), args.dps)},
        "distance_from_half": mp.nstr(abs(mp.re(root) - mp.mpf("0.5")), args.dps),
        "multiplicativity_bad_pairs_limit80": multiplicativity_defect(80),
        "argument_principle": {
            "status": "DISABLED",
            "reason": "family-specific completed functional equation and contour enclosure still need independent implementation"
        },
        "interpretation": "A high-precision residual supports the fixture only; a refined point is not a certified zero without an interval contour count.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(args.output),
                      "abs_value": result["refined_root"]["abs_value"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
