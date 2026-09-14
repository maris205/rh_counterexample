"""Subdivide a DH rectangle and test Arb Euler--Maclaurin boxes.

This is the next audit layer after the single-box prototype.  It reports how
many boundary boxes exclude zero.  A nonzero count is necessary for a contour
certificate but this script still does not implement interval argument
accumulation, so the status remains NONCERTIFIED unless every requested box is
nonzero and the phase audit agrees.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import mpmath as mp

sys.path.insert(0, str(Path(__file__).parent))
from hurwitz_em_flint_py3 import cbox, dh_em_box  # noqa: E402


def dh_point(s: complex) -> complex:
    c = (mp.sqrt(10 - 2 * mp.sqrt(5)) - 2) / (mp.sqrt(5) - 1)
    a = [1, c, -c, -1, 0]
    z = mp.mpc(s)
    return 5 ** (-z) * sum(a[r - 1] * mp.zeta(z, mp.mpf(r) / 5) for r in range(1, 6))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sigma", default="0.8085171824566373855533519606")
    ap.add_argument("--t", default="85.69934848537759217192926771")
    ap.add_argument("--ds", default="0.01")
    ap.add_argument("--dt", default="0.01")
    ap.add_argument("--edge-points", type=int, default=64)
    ap.add_argument("--n", type=int, default=128)
    ap.add_argument("--m", type=int, default=12)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    mp.mp.dps = 60
    sig, tt = mp.mpf(args.sigma), mp.mpf(args.t)
    ds, dt = mp.mpf(args.ds), mp.mpf(args.dt)
    e = args.edge_points
    boxes = []
    # Each boundary segment is represented by its midpoint and half-widths.
    # Counter-clockwise order: bottom, right, top (reversed), left (reversed).
    for j in range(e):
        u0, u1 = -ds + 2 * ds * j / e, -ds + 2 * ds * (j + 1) / e
        boxes.append((sig + (u0 + u1) / 2, tt - dt, (u1 - u0) / 2, mp.mpf("0")))
    for j in range(e):
        v0, v1 = -dt + 2 * dt * j / e, -dt + 2 * dt * (j + 1) / e
        boxes.append((sig + ds, tt + (v0 + v1) / 2, mp.mpf("0"), (v1 - v0) / 2))
    for j in range(e - 1, -1, -1):
        u0, u1 = -ds + 2 * ds * j / e, -ds + 2 * ds * (j + 1) / e
        boxes.append((sig + (u0 + u1) / 2, tt + dt, (u1 - u0) / 2, mp.mpf("0")))
    for j in range(e - 1, -1, -1):
        v0, v1 = -dt + 2 * dt * j / e, -dt + 2 * dt * (j + 1) / e
        boxes.append((sig - ds, tt + (v0 + v1) / 2, mp.mpf("0"), (v1 - v0) / 2))

    nonzero = 0
    min_lower = math.inf
    failed = []
    phase = []
    for idx, (sc, tc, sw, tw) in enumerate(boxes):
        val, meta = dh_em_box(cbox(str(sc), str(tc), str(sw), str(tw)), n=args.n, m=args.m)
        contains = bool(val.contains(0))
        lower = float(abs(val).lower())
        min_lower = min(min_lower, lower)
        if not contains:
            nonzero += 1
        elif len(failed) < 12:
            failed.append({"index": idx, "center": [str(sc), str(tc)], "enclosure": str(val)})
        z = dh_point(complex(float(sc), float(tc)))
        phase.append(math.atan2(float(mp.im(z)), float(mp.re(z))))

    unwrapped = [phase[0]] if phase else []
    for p in phase[1:]:
        q = p
        while q - unwrapped[-1] > math.pi:
            q -= 2 * math.pi
        while q - unwrapped[-1] < -math.pi:
            q += 2 * math.pi
        unwrapped.append(q)
    total = (unwrapped[-1] - unwrapped[0]) if unwrapped else 0.0
    winding = int(round(total / (2 * math.pi)))
    result = {
        "status": "NONCERTIFIED_SUBDIVISION",
        "configuration": {k: str(v) if isinstance(v, (mp.mpf, Path)) else v for k, v in vars(args).items()},
        "boundary_boxes": len(boxes),
        "boxes_excluding_zero": nonzero,
        "boxes_containing_zero": len(boxes) - nonzero,
        "minimum_arb_abs_lower": min_lower,
        "sampled_midpoint_winding": winding,
        "failed_examples": failed,
        "interpretation": "Boundary subdivision is a necessary diagnostic. The result is not a rigorous zero count because interval argument accumulation and a certified Hurwitz remainder proof are still incomplete.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "boundary_boxes": len(boxes), "boxes_containing_zero": len(boxes) - nonzero, "sampled_winding": winding, "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
