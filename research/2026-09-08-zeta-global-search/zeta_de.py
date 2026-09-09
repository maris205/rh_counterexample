"""Parallel differential evolution on the actual Riemann zeta function.

The optimizer proposes points. Independent high precision evaluations and
whole-box enclosures check them. Only a rigorous off-line contour count can
certify an RH counterexample. Low-height demo runs are calibration experiments.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
import multiprocessing as multiprocessing
import os
from pathlib import Path
import platform
import sys
import time

# Set before numpy/scipy are imported, including in spawned Windows workers.
for variable in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[variable] = '1'

HERE = Path(__file__).resolve().parent
LAB = HERE.parent / '2026-09-08-zero-lab'
for directory in (HERE / '.deps', LAB / '.deps', LAB, LAB / 'certification'):
    sys.path.insert(0, str(directory))
import flint
from flint import acb, ctx, fmpq
import mpmath as mp
import numpy as np
import scipy
from scipy.optimize import differential_evolution
from zero_lab import check_point, refine
from rectangle_count import count_rectangle


def rational(value):
    """Public numeric parameters are decimal strings; floats use repr first."""
    return Fraction(repr(float(value)) if isinstance(value, (float, np.floating)) else str(value))


def decimal_text(value):
    """An exact finite decimal for sums of decimal input coordinates."""
    value = Fraction(value)
    denominator = value.denominator
    powers = []
    for prime in (2, 5):
        exponent = 0
        while denominator % prime == 0:
            denominator //= prime
            exponent += 1
        powers.append(exponent)
    if denominator != 1:
        raise ValueError('Only terminating decimal coordinates are supported')
    places = max(powers)
    if not places:
        return str(value.numerator)
    scaled = abs(value.numerator) * 2**(places-powers[0]) * 5**(places-powers[1])
    digits = str(scaled).zfill(places+1)
    sign = '-' if value < 0 else ''
    return sign + digits[:-places] + '.' + digits[-places:]


def ball_rational(value):
    value = Fraction(value)
    return fmpq(value.numerator, value.denominator)


@dataclass(frozen=True)
class ZetaObjective:
    t_base: str = '0'
    dps: int = 40

    def __call__(self, parameters):
        sigma, offset = map(rational, parameters)
        height = rational(self.t_base) + offset
        previous_precision = ctx.dps
        try:
            # Insufficiently accurate value enclosures are never scored as zeros.
            for precision in (self.dps, self.dps * 2, self.dps * 3):
                ctx.dps = precision
                value = acb(ball_rational(sigma), ball_rational(height)).zeta()
                if not value.is_finite() or value.rel_accuracy_bits() < 30:
                    continue
                magnitude = float(abs(value).mid())
                if magnitude > 0 and math.isfinite(magnitude):
                    # Same minimizers as |zeta| or |zeta|^2, without squaring
                    # very small numbers. This is not the gamma-scaled xi.
                    return math.log10(magnitude)
            raise ArithmeticError('Could not obtain an accurate finite nonzero zeta estimate')
        finally:
            ctx.dps = previous_precision


def optimize_box(sigma_min, sigma_max, t_min, t_max, *, t_base='0',
                 dps=40, maxiter=35, popsize=8, seed=20260908, workers=1):
    a, b, c, d, base = map(rational, (sigma_min, sigma_max, t_min, t_max, t_base))
    if not (0 < a <= b and c < d and base + c > 0):
        raise ValueError('Need 0 < sigma_min <= sigma_max and 0 < base+t_min < base+t_max')
    if dps < 20 or maxiter < 1 or popsize < 5:
        raise ValueError('Need dps >= 20, maxiter >= 1, popsize >= 5')
    history = []
    started = time.perf_counter()

    def record(intermediate_result):
        history.append({'generation':int(intermediate_result.nit),
                        'best_sigma':repr(float(intermediate_result.x[0])),
                        'best_t_offset':repr(float(intermediate_result.x[1])),
                        'best_log10_abs_zeta':float(intermediate_result.fun)})

    try:
        bounds = [(float(a), float(b)), (float(c), float(d))]
    except OverflowError as error:
        raise ValueError('Optimizer bounds exceed binary64 range') from error
    if not all(math.isfinite(v) for pair in bounds for v in pair):
        raise ValueError('Optimizer bounds must be finite binary64 values')
    fa, fb = map(rational, bounds[0])
    fc, fd = map(rational, bounds[1])
    if fa <= 0 or base + fc <= 0:
        raise ValueError('Positive sigma or height is lost at binary64 precision')
    if (a < b and fa >= fb) or fc >= fd:
        raise ValueError('Bounds collapse at binary64 precision; use smaller local offsets')
    if (b < Fraction(1,2) and fb >= Fraction(1,2)) or (a > Fraction(1,2) and fa <= Fraction(1,2)):
        raise ValueError('Requested line exclusion is lost at binary64 precision')
    result = differential_evolution(
        ZetaObjective(decimal_text(base), dps), bounds,
        strategy='best1bin', maxiter=maxiter, popsize=popsize,
        tol=1e-8, atol=0, rng=np.random.default_rng(seed),
        updating='deferred', workers=workers, polish=False, callback=record)
    sigma, offset = map(rational, result.x)
    height = base + offset
    return {
        'requested_bounds':{'sigma':[str(sigma_min), str(sigma_max)],
                            't_offset':[str(t_min), str(t_max)], 't_base':str(t_base)},
        'effective_float_bounds':[[repr(x), repr(y)] for x,y in bounds],
        'configuration':{'strategy':'best1bin', 'maxiter':maxiter, 'popsize':popsize,
                         'rng_seed':seed, 'updating':'deferred', 'polish':False,
                         'tol':1e-8, 'arb_search_dps':dps,
                         'objective':'log10(abs(zeta(sigma + i*(t_base+t_offset))))'},
        'optimizer':{'success':bool(result.success), 'message':str(result.message),
                     'nit':int(result.nit), 'nfev':int(result.nfev),
                     'elapsed_seconds':time.perf_counter()-started},
        'best':{'sigma':decimal_text(sigma), 't_offset':decimal_text(offset),
                't':decimal_text(height), 'log10_abs_zeta':float(result.fun),
                'approx_abs_zeta':10.0**float(result.fun),
                'distance_to_line':decimal_text(abs(sigma-Fraction(1,2)))},
        'history':history,
        'optimizer_success_is_not_a_global_minimum_or_root_certificate':True,
        'certified_off_line_zero':False}


def diagnose(result, dps=100):
    """Use both mpmath and Arb, then allow Newton to move sigma freely."""
    best = result['best']
    sigma, height = rational(best['sigma']), rational(best['t'])
    delta = abs(sigma-Fraction(1,2))
    radius = min(Fraction(1,10**8), delta/4) if delta else Fraction(1,10**12)
    # For tiny custom gaps choose enough precision to resolve the gap.
    needed = max(dps, int(-math.log10(float(radius))) + 40)
    check = check_point(best['sigma'], best['t'], decimal_text(radius),
                        precisions=(50, needed))
    result['point_check'] = check
    if not all(row['independent_point_evaluations_agree'] for row in check['evaluation_rows']):
        raise ArithmeticError('Independent evaluations disagree; inspect candidate')
    row = check['evaluation_rows'][-1]
    with mp.workdps(needed):
        ratio = (mp.mpf(row['newton_correction_magnitude']) / mp.mpf(decimal_text(delta))) if delta else mp.inf
        result['newton_correction_over_line_distance'] = mp.nstr(ratio, 20)
    if 0 < sigma < 1:
        root = refine(best['sigma'], best['t'], dps=needed,
                      max_height=max(10000, int(height)+100))
        result['free_sigma_newton'] = root
        if root.get('classification') == 'OFF_LINE_NUMERICAL_CANDIDATE':
            a, t = rational(root['final_sigma']), rational(root['final_t'])
            r = min(abs(a-Fraction(1,2))/4, a/4, (1-a)/4, t/4, Fraction(1,10**6))
            certificate = count_rectangle(decimal_text(a-r), decimal_text(a+r),
                                          decimal_text(t-r), decimal_text(t+r),
                                          dps=needed, max_seconds=30,
                                          include_segments=True)
            result['root_candidate_contour'] = certificate
            result['certified_off_line_zero'] = bool(certificate.get('off_line_certified', False))
    return result


def metadata():
    return {'python':platform.python_version(), 'numpy':np.__version__,
            'scipy':scipy.__version__, 'python_flint':flint.__version__,
            'mpmath':mp.__version__, 'cpu_count':os.cpu_count(),
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'verifier_sha256':hashlib.sha256((LAB/'zero_lab.py').read_bytes()).hexdigest(),
            'contour_sha256':hashlib.sha256((LAB/'certification/rectangle_count.py').read_bytes()).hexdigest()}


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # A checkpoint never replaces the last complete JSON with a partial write.
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temporary.replace(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='mode', required=True)
    for name in ('demo', 'search'):
        parser = sub.add_parser(name)
        parser.add_argument('--workers', type=int, default=min(12, os.cpu_count() or 1))
        parser.add_argument('--maxiter', type=int, default=35)
        parser.add_argument('--popsize', type=int, default=8)
        parser.add_argument('--dps', type=int, default=40)
        parser.add_argument('--seed', type=int, default=20260908)
        parser.add_argument('--output', type=Path, default=HERE/(name+'_results.json'))
        if name == 'search':
            parser.add_argument('--sigma-min', required=True)
            parser.add_argument('--sigma-max', required=True)
            parser.add_argument('--t-min', required=True, help='Local offset from t-base')
            parser.add_argument('--t-max', required=True, help='Local offset from t-base')
            parser.add_argument('--t-base', default='0', help='Exact decimal base; not added in binary64')
    args = ap.parse_args()
    if args.workers < 1:
        ap.error('--workers must be positive')
    jobs = []
    if args.mode == 'demo':
        for sigma in ('3', '5'):
            jobs.append((f'axis_{sigma}', sigma, sigma, '1', '50', '0', None))
        for gap in ('0.1', '0.01', '0.001'):
            for side, a, b in (
                ('left', '0.05', decimal_text(Fraction(1,2)-rational(gap))),
                ('right', decimal_text(Fraction(1,2)+rational(gap)), '0.95')):
                for c,d in ((1,10),(10,20),(20,30),(30,40),(40,50)):
                    jobs.append((f'gap_{gap}_{side}_{c}_{d}', a,b,str(c),str(d),'0',gap))
    else:
        jobs.append(('custom', args.sigma_min, args.sigma_max,
                     args.t_min, args.t_max, args.t_base, None))
    report = {'status':'RUNNING', 'mode':args.mode, 'metadata':metadata(),
              'workers_requested':args.workers, 'planned_runs':len(jobs),
              'known_zero_heights_used_in_objective_or_initial_population':False,
              'scope':('Calibration at 1 <= t <= 50. Not a search beyond established RH verification.'
                       if args.mode == 'demo' else 'Only the explicitly requested finite rectangle.'),
              'runs':[], 'certified_off_line_zero':False}
    started = time.perf_counter()
    pool = multiprocessing.get_context('spawn').Pool(args.workers) if args.workers > 1 else None
    mapper = pool.map if pool else 1
    try:
        for index, (name,a,b,c,d,base,gap) in enumerate(jobs):
            result = optimize_box(a,b,c,d,t_base=base,dps=args.dps,
                                  maxiter=args.maxiter,popsize=args.popsize,
                                  seed=args.seed+index,workers=mapper)
            result['name'] = name
            result['prespecified_line_exclusion_gap'] = gap
            diagnose(result)
            report['runs'].append(result)
            report['certified_off_line_zero'] |= result['certified_off_line_zero']
            report['elapsed_seconds'] = time.perf_counter()-started
            write_json(args.output, report)
            print(f"[{index+1}/{len(jobs)}] {name}: sigma={result['best']['sigma']} "
                  f"t={result['best']['t']} |zeta|={result['best']['approx_abs_zeta']:.9g} "
                  f"{result['point_check']['status']}", flush=True)
        report['status'] = 'COMPLETED'
    except Exception as error:
        report['status'] = 'FAILED'
        report['error'] = repr(error)
        raise
    finally:
        if pool:
            pool.terminate()
            pool.join()
        report['elapsed_seconds'] = time.perf_counter()-started
        write_json(args.output, report)
    print(json.dumps({'status':report['status'], 'output':str(args.output),
                      'total_function_evaluations':sum(r['optimizer']['nfev'] for r in report['runs']),
                      'certified_off_line_zero':report['certified_off_line_zero']}, ensure_ascii=False))


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
