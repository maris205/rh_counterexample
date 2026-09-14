"""Shared-endpoint phase-branch audit for a DH contour.

This diagnostic computes each boundary endpoint once, unwraps consecutive
phase differences, and checks the distance from the +/-pi branch ambiguity.
It does not certify endpoint disks or the path between endpoints.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import mpmath as mp


def dh(s: mp.mpc) -> mp.mpc:
    c = (mp.sqrt(10 - 2 * mp.sqrt(5)) - 2) / (mp.sqrt(5) - 1)
    a = [1, c, -c, -1, 0]
    return 5 ** (-s) * sum(a[r - 1] * mp.zeta(s, mp.mpf(r) / 5) for r in range(1, 6))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sigma", default="0.8085171824566373855533519606")
    ap.add_argument("--t", default="85.69934848537759217192926771")
    ap.add_argument("--ds", default="0.01")
    ap.add_argument("--dt", default="0.01")
    ap.add_argument("--edge-points", type=int, default=64)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    mp.mp.dps = 60
    s0, t0, ds, dt = map(mp.mpf, (args.sigma, args.t, args.ds, args.dt))
    corners = [(s0 - ds, t0 - dt), (s0 + ds, t0 - dt), (s0 + ds, t0 + dt), (s0 - ds, t0 + dt)]
    endpoints = []
    e = args.edge_points
    for side in range(4):
        a, b = corners[side], corners[(side + 1) % 4]
        for j in range(e):
            u = mp.mpf(j) / e
            endpoints.append(mp.mpc(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    phases = [float(mp.arg(dh(z))) for z in endpoints]
    unwrapped = [phases[0]]
    deltas = []
    margins = []
    for p in phases[1:] + [phases[0]]:
        q = p
        while q - unwrapped[-1] > math.pi:
            q -= 2 * math.pi
        while q - unwrapped[-1] < -math.pi:
            q += 2 * math.pi
        delta = q - unwrapped[-1]
        deltas.append(delta)
        margins.append(math.pi - abs(delta))
        unwrapped.append(q)
    total = sum(deltas)
    result = {
        "status": "NONCERTIFIED_SHARED_ENDPOINT_PHASE_DIAGNOSTIC",
        "configuration": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
        "unique_endpoints": len(endpoints),
        "nominal_winding": total / (2 * math.pi),
        "max_abs_endpoint_phase_step": max(abs(x) for x in deltas),
        "minimum_branch_margin": min(margins),
        "branch_steps_near_ambiguity": sum(m < 0.1 for m in margins),
        "interpretation": "Shared endpoints remove duplicated endpoint phase variables and test branch stability. This is still non-certified until endpoint/path enclosures exclude zero and the branch choice is proven over each segment.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "nominal_winding": result["nominal_winding"], "minimum_branch_margin": result["minimum_branch_margin"], "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
