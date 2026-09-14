"""Taylor/Lipschitz diagnostic for Davenport--Heilbronn contour boxes.

Compares Arb Euler--Maclaurin boxes with centre-value disks using sampled
finite-difference derivatives. This is explicitly non-certified.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
import mpmath as mp

sys.path.insert(0, str(Path(__file__).parent))
from hurwitz_em_flint_py3 import cbox, dh_em_box  # noqa: E402


def dh(s):
    kap = (mp.sqrt(10 - 2 * mp.sqrt(5)) - 2) / (mp.sqrt(5) - 1)
    a = [1, kap, -kap, -1, 0]
    return 5 ** (-s) * sum(a[r - 1] * mp.zeta(s, mp.mpf(r) / 5) for r in range(1, 6))


def derivative(s, h):
    return (dh(s + h) - dh(s - h)) / (2 * h)


def segments(sig, tt, ds, dt, e):
    for j in range(e):
        u0, u1 = -ds + 2 * ds * j / e, -ds + 2 * ds * (j + 1) / e
        yield sig + (u0 + u1) / 2, tt - dt, (u1 - u0) / 2, 1
    for j in range(e):
        v0, v1 = -dt + 2 * dt * j / e, -dt + 2 * dt * (j + 1) / e
        yield sig + ds, tt + (v0 + v1) / 2, (v1 - v0) / 2, 1j
    for j in range(e - 1, -1, -1):
        u0, u1 = -ds + 2 * ds * j / e, -ds + 2 * ds * (j + 1) / e
        yield sig + (u0 + u1) / 2, tt + dt, (u1 - u0) / 2, 1
    for j in range(e - 1, -1, -1):
        v0, v1 = -dt + 2 * dt * j / e, -dt + 2 * dt * (j + 1) / e
        yield sig - ds, tt + (v0 + v1) / 2, (v1 - v0) / 2, 1j


def winding(phases):
    if not phases: return 0
    u = [phases[0]]
    for p in phases[1:]:
        q = p
        while q - u[-1] > math.pi: q -= 2 * math.pi
        while q - u[-1] < -math.pi: q += 2 * math.pi
        u.append(q)
    return int(round((u[-1] - u[0]) / (2 * math.pi)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sigma', default='0.8085171824566373855533519606')
    ap.add_argument('--t', default='85.69934848537759217192926771')
    ap.add_argument('--ds', default='0.01'); ap.add_argument('--dt', default='0.01')
    ap.add_argument('--edge-points', type=int, default=64)
    ap.add_argument('--derivative-samples', type=int, default=5)
    ap.add_argument('--derivative-step', default='1e-7'); ap.add_argument('--safety-factor', default='1.25')
    ap.add_argument('--n', type=int, default=128); ap.add_argument('--m', type=int, default=12)
    ap.add_argument('--output', type=Path, required=True); args = ap.parse_args()
    mp.mp.dps = 70
    sig, tt, ds, dt = map(mp.mpf, (args.sigma, args.t, args.ds, args.dt))
    hdiff, safety = mp.mpf(args.derivative_step), mp.mpf(args.safety_factor)
    ns = max(3, args.derivative_samples)
    fracs = [mp.mpf(-1) + 2 * mp.mpf(k) / (ns - 1) for k in range(ns)]
    rows, phases = [], []
    for idx, (sc, tc, half, tangent) in enumerate(segments(sig, tt, ds, dt, args.edge_points)):
        sw, tw = (half, 0) if tangent == 1 else (0, half)
        box, _ = dh_em_box(cbox(str(sc), str(tc), str(sw), str(tw)), n=args.n, m=args.m)
        naive_lower = float(abs(box).lower())
        z, center = mp.mpc(sc, tc), dh(mp.mpc(sc, tc))
        sampled = max(abs(derivative(z + tangent * q * half, hdiff)) for q in fracs)
        lower = max(mp.mpf(0), abs(center) - safety * sampled * half)
        phases.append(float(mp.arg(center)))
        rows.append({'index': idx, 'centre': [str(sc), str(tc)], 'half_length': str(half),
                     'naive_abs_lower': naive_lower, 'centre_abs': float(abs(center)),
                     'sampled_derivative_max': float(sampled), 'heuristic_L': float(safety * sampled),
                     'taylor_disk_lower': float(lower), 'taylor_improves': bool(lower > naive_lower)})
    naive = [r['naive_abs_lower'] for r in rows]; tay = [r['taylor_disk_lower'] for r in rows]
    result = {
        'status': 'NONCERTIFIED_TAYLOR_LIPSCHITZ_DIAGNOSTIC',
        'method': 'centre value plus sampled finite-difference derivative disk',
        'configuration': {k: str(v) if k == 'output' else v for k, v in vars(args).items()},
        'boundary_segments': len(rows),
        'naive': {'segments_excluding_zero_by_arb_lower': sum(x > 0 for x in naive),
                  'minimum_abs_lower': min(naive) if naive else 0.0,
                  'median_abs_lower': sorted(naive)[len(naive)//2] if naive else 0.0},
        'taylor_disk': {'segments_excluding_zero_by_heuristic_lower': sum(x > 0 for x in tay),
                        'minimum_lower': min(tay) if tay else 0.0,
                        'median_lower': sorted(tay)[len(tay)//2] if tay else 0.0,
                        'segments_improved_over_naive': sum(r['taylor_improves'] for r in rows),
                        'sampled_midpoint_winding': winding(phases)},
        'segments': rows,
        'interpretation': 'Sampled finite differences and a safety multiplier are not an interval bound on F\'; this output is not a rigorous contour certificate.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'segments': len(rows), 'naive_min': result['naive']['minimum_abs_lower'],
                      'taylor_min': result['taylor_disk']['minimum_lower'], 'improved': result['taylor_disk']['segments_improved_over_naive'],
                      'output': str(args.output)}, ensure_ascii=False))


if __name__ == '__main__': main()
