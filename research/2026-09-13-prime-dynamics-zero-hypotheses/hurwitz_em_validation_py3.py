"""Validate the Euler--Maclaurin Hurwitz-zeta formula at point precision.

This is a preparatory check for the later Arb interval evaluator.  It compares
the finite Euler--Maclaurin expansion with mpmath's independent Hurwitz-zeta
implementation; it is not itself an interval proof.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import mpmath as mp


def hurwitz_em(s: mp.mpc, a: mp.mpf, n: int, m: int) -> mp.mpc:
    q = mp.mpc(0)
    for j in range(n):
        q += (j + a) ** (-s)
    x = n + a
    q += x ** (1 - s) / (s - 1) + mp.mpf("0.5") * x ** (-s)
    for k in range(1, m + 1):
        b = mp.bernpoly(2 * k, 0)
        q += b / mp.factorial(2 * k) * mp.rf(s, 2 * k - 1) * x ** (-s - 2 * k + 1)
    return q


def dh_from_hurwitz(s: mp.mpc, fun) -> mp.mpc:
    c = (mp.sqrt(10 - 2 * mp.sqrt(5)) - 2) / (mp.sqrt(5) - 1)
    coeff = [1, c, -c, -1, 0]
    return 5 ** (-s) * sum(coeff[r - 1] * fun(s, mp.mpf(r) / 5) for r in range(1, 6))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dps", type=int, default=80)
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--m", type=int, default=8)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    mp.mp.dps = args.dps
    s = mp.mpc("0.8085171824566373855533519606", "85.69934848537759217192926771")
    rows = []
    for r in range(1, 6):
        a = mp.mpf(r) / 5
        exact = mp.zeta(s, a)
        approx = hurwitz_em(s, a, args.n, args.m)
        rows.append({"r": r, "abs_error": mp.nstr(abs(approx - exact), 30)})
    exact_dh = dh_from_hurwitz(s, mp.zeta)
    em_dh = dh_from_hurwitz(s, lambda z, a: hurwitz_em(z, a, args.n, args.m))
    result = {
        "status": "COMPLETED",
        "precision_dps": args.dps,
        "N": args.n,
        "M": args.m,
        "root_seed": [mp.nstr(mp.re(s), 30), mp.nstr(mp.im(s), 30)],
        "hurwitz_component_errors": rows,
        "dh_abs_error": mp.nstr(abs(em_dh - exact_dh), 30),
        "interpretation": "Point-precision validation only; the Euler--Maclaurin remainder must still be enclosed with Arb before contour certification.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "dh_abs_error": result["dh_abs_error"], "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
