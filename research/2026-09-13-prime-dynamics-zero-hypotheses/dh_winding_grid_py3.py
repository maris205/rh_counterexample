"""Multi-box, multi-density numerical winding audit for the DH fixture root.

This is deliberately a *discrete numerical sanity check*.  It does not provide
interval bounds on the function or contour, so a winding count here is not a
rigorous argument-principle certificate.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import mpmath as mp


def kappa() -> mp.mpf:
    return (mp.sqrt(10 - 2 * mp.sqrt(5)) - 2) / (mp.sqrt(5) - 1)


def dh(s: mp.mpc) -> mp.mpc:
    c = kappa()
    coeff = (mp.mpf(1), c, -c, mp.mpf(-1), mp.mpf(0))
    return mp.power(5, -s) * sum(
        coeff[r - 1] * mp.zeta(s, mp.mpf(r) / 5) for r in range(1, 6)
    )


def winding(sigma0: mp.mpf, t0: mp.mpf, ds: mp.mpf, dt: mp.mpf,
            edge_points: int) -> tuple[int, mp.mpf, int, mp.mpf]:
    corners = [
        mp.mpc(sigma0 - ds, t0 - dt), mp.mpc(sigma0 + ds, t0 - dt),
        mp.mpc(sigma0 + ds, t0 + dt), mp.mpc(sigma0 - ds, t0 + dt),
    ]
    points = []
    for z0, z1 in zip(corners, corners[1:] + corners[:1]):
        points.extend(z0 + (z1 - z0) * j / edge_points
                      for j in range(edge_points))
    values = [dh(z) for z in points]
    phases = [mp.arg(value) for value in values]
    unwrapped = [phases[0]]
    for phase in phases[1:]:
        value = phase
        while value - unwrapped[-1] > mp.pi:
            value -= 2 * mp.pi
        while value - unwrapped[-1] < -mp.pi:
            value += 2 * mp.pi
        unwrapped.append(value)
    closing = phases[0]
    while closing - unwrapped[-1] > mp.pi:
        closing -= 2 * mp.pi
    while closing - unwrapped[-1] < -mp.pi:
        closing += 2 * mp.pi
    total = unwrapped[-1] + (closing - unwrapped[-1]) - unwrapped[0]
    count = int(mp.nint(total / (2 * mp.pi)))
    return count, min(abs(value) for value in values), len(points), total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--dps', type=int, default=70)
    parser.add_argument('--sigma', default='0.8085171824566373855533519606')
    parser.add_argument('--t', default='85.69934848537759217192926771')
    parser.add_argument('--half-widths', default='0.005,0.01,0.02')
    parser.add_argument('--edge-points', default='32,64,128,256')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    mp.mp.dps = args.dps
    sigma0, t0 = mp.mpf(args.sigma), mp.mpf(args.t)
    widths = [mp.mpf(x.strip()) for x in args.half_widths.split(',') if x.strip()]
    densities = [int(x.strip()) for x in args.edge_points.split(',') if x.strip()]
    rows = []
    started = time.time()
    for width in widths:
        for density in densities:
            tic = time.time()
            count, min_boundary, samples, total = winding(
                sigma0, t0, width, width, density)
            rows.append({
                'half_width': mp.nstr(width, args.dps),
                'edge_points_per_side': density,
                'contour_samples': samples,
                'winding_count': count,
                'minimum_boundary_abs_value': mp.nstr(min_boundary, args.dps),
                'total_phase_change': mp.nstr(total, args.dps),
                'elapsed_seconds': round(time.time() - tic, 3),
            })
            print(json.dumps(rows[-1], ensure_ascii=False), flush=True)
    result = {
        'status': 'COMPLETED',
        'purpose': 'multi-box multi-density numerical DH winding sanity check; not interval-rigorous',
        'precision_dps': args.dps,
        'center': {'sigma': args.sigma, 't': args.t},
        'half_widths': [mp.nstr(x, args.dps) for x in widths],
        'edge_points_per_side': densities,
        'results': rows,
        'elapsed_seconds': round(time.time() - started, 3),
        'interpretation': ('Stable winding count one across boxes and mesh densities '
                           'supports one enclosed DH zero numerically. It is not a '
                           'rigorous zero certificate without interval contour bounds.'),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'output': str(args.output),
                      'rows': len(rows), 'elapsed_seconds': result['elapsed_seconds']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
