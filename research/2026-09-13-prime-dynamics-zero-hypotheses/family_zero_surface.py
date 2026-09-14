"""Direct surface scan for periodic Dirichlet-family controls.

The scan is deliberately modest: it tests whether a generic sigma/t minimizer
can recover a known Davenport--Heilbronn off-line zero in the same window where
the Riemann zeta function has no corresponding zero. It is a family diagnostic,
not an RH certificate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import mpmath as mp


def kappa():
    return (mp.sqrt(10 - 2 * mp.sqrt(5)) - 2) / (mp.sqrt(5) - 1)


def coeffs(name):
    if name == 'dh':
        c = kappa(); return [mp.mpf(1), c, -c, mp.mpf(-1), mp.mpf(0)]
    if name == 'chi4':
        return [mp.mpf(1), mp.mpf(0), mp.mpf(-1), mp.mpf(0)]
    if name == 'chi5':
        return [mp.mpf(1), mp.mpf(-1), mp.mpf(-1), mp.mpf(1), mp.mpf(0)]
    raise ValueError(name)


def periodic_value(name, s):
    a = coeffs(name); q = len(a)
    return mp.power(q, -s) * sum(a[r - 1] * mp.zeta(s, mp.mpf(r) / q)
                                  for r in range(1, q + 1))


def value(name, s):
    return mp.zeta(s) if name == 'zeta' else periodic_value(name, s)


def refine(name, sigma, t):
    seed = mp.mpc(sigma, t)
    f = lambda z: value(name, z)
    try:
        root = mp.findroot(f, (seed, seed + mp.mpc('0.0001', '0.0001')),
                           solver='secant', tol=mp.mpf('1e-45'), maxsteps=60)
        return {'status': 'CONVERGED', 'sigma': mp.nstr(mp.re(root), 60),
                't': mp.nstr(mp.im(root), 60),
                'abs_value': mp.nstr(abs(f(root)), 30),
                'distance_to_half': mp.nstr(abs(mp.re(root)-mp.mpf('0.5')), 30)}
    except Exception as exc:
        return {'status': 'FAILED', 'error': str(exc)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dps', type=int, default=60)
    ap.add_argument('--sigma-min', default='0.55')
    ap.add_argument('--sigma-max', default='0.90')
    ap.add_argument('--sigma-steps', type=int, default=15)
    ap.add_argument('--t-min', default='83')
    ap.add_argument('--t-max', default='88')
    ap.add_argument('--t-steps', type=int, default=21)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args(); mp.mp.dps = args.dps
    sigmas = [mp.mpf(args.sigma_min)+(mp.mpf(args.sigma_max)-mp.mpf(args.sigma_min))*i/(args.sigma_steps-1) for i in range(args.sigma_steps)]
    ts = [mp.mpf(args.t_min)+(mp.mpf(args.t_max)-mp.mpf(args.t_min))*i/(args.t_steps-1) for i in range(args.t_steps)]
    surfaces = {}
    for name in ('dh', 'zeta', 'chi4', 'chi5'):
        rows=[]
        for s in sigmas:
            for t in ts:
                z=value(name,mp.mpc(s,t)); rows.append({'sigma':str(s),'t':str(t),'abs_value':mp.nstr(abs(z),30)})
        best=min(rows,key=lambda r: mp.mpf(r['abs_value']))
        surfaces[name]={'best_grid_point':best,
                        'refinement':refine(name,best['sigma'],best['t']),
                        'grid_shape':[len(sigmas),len(ts)]}
    out={'status':'COMPLETED','purpose':'periodic family surface scan; not an RH certificate',
         'configuration':{'dps':args.dps,'sigma_range':[args.sigma_min,args.sigma_max],
                          't_range':[args.t_min,args.t_max],'sigma_steps':args.sigma_steps,'t_steps':args.t_steps},
         'surfaces':surfaces,
         'interpretation':'DH should recover an off-line minimum near the reported root; zeta is an independent negative comparison in the same window.'}
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':out['status'],'output':str(args.output)}))


if __name__=='__main__': main()
