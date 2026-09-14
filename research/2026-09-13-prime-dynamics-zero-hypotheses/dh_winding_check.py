"""Numerical (not interval-rigorous) winding check around the DH fixture root."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import mpmath as mp


def kappa():
    return (mp.sqrt(10 - 2 * mp.sqrt(5)) - 2) / (mp.sqrt(5) - 1)


def dh(s):
    c = kappa()
    a = [1, c, -c, -1, 0]
    return mp.power(5, -s) * sum(a[r - 1] * mp.zeta(s, mp.mpf(r) / 5)
                                   for r in range(1, 6))


def contour(sigma0, t0, ds, dt, n):
    corners = [mp.mpc(sigma0 - ds, t0 - dt), mp.mpc(sigma0 + ds, t0 - dt),
               mp.mpc(sigma0 + ds, t0 + dt), mp.mpc(sigma0 - ds, t0 + dt)]
    pts = []
    for z0, z1 in zip(corners, corners[1:] + corners[:1]):
        for j in range(n):
            pts.append(z0 + (z1 - z0) * j / n)
    vals = [dh(z) for z in pts]
    phases = [mp.arg(v) for v in vals]
    unwrapped = [phases[0]]
    for p in phases[1:]:
        q = p
        while q - unwrapped[-1] > mp.pi:
            q -= 2 * mp.pi
        while q - unwrapped[-1] < -mp.pi:
            q += 2 * mp.pi
        unwrapped.append(q)
    q = phases[0]
    while q - unwrapped[-1] > mp.pi:
        q -= 2 * mp.pi
    while q - unwrapped[-1] < -mp.pi:
        q += 2 * mp.pi
    total = unwrapped[-1] + (q - unwrapped[-1]) - unwrapped[0]
    return int(mp.nint(total / (2 * mp.pi))), min(abs(v) for v in vals), len(vals)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dps', type=int, default=80)
    ap.add_argument('--sigma', default='0.8085171824566373855533519606')
    ap.add_argument('--t', default='85.69934848537759217192926771')
    ap.add_argument('--ds', default='0.01')
    ap.add_argument('--dt', default='0.01')
    ap.add_argument('--edge-points', type=int, default=256)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    mp.mp.dps = args.dps
    count, min_boundary, samples = contour(mp.mpf(args.sigma), mp.mpf(args.t),
                                           mp.mpf(args.ds), mp.mpf(args.dt),
                                           args.edge_points)
    out = {'status': 'COMPLETED', 'purpose': 'numerical DH winding check; not interval-rigorous',
           'center': {'sigma': args.sigma, 't': args.t},
           'half_widths': {'sigma': args.ds, 't': args.dt},
           'edge_points_per_side': args.edge_points, 'contour_samples': samples,
           'winding_count': count, 'minimum_boundary_abs_value': mp.nstr(min_boundary, args.dps),
           'interpretation': 'A winding count of one supports one enclosed zero numerically; interval enclosure is still required for certification.'}
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': out['status'], 'winding_count': count, 'output': str(args.output)}))


if __name__ == '__main__':
    main()
