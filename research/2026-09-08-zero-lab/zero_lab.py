"""Direct Riemann-zeta candidate diagnostics; decimal inputs, no RH assumption.

check: evaluate a supplied point at increasing precision and enclose the WHOLE
user-specified box with Arb. A zero-containing value ball is inconclusive.
refine: unconstrained-in-sigma complex Newton, with strip-preserving damping.
count: rigorous adaptive rectangle count, including boxes off the critical line.
demo: known-zero calibration and deliberately misleading near-zero examples.
"""
from __future__ import annotations
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / '.deps'))
import mpmath as mp
import flint
from flint import acb, arb, ctx, fmpq


def real_ball(text, radius='0'):
    mid, rad = Fraction(str(text)), Fraction(str(radius))
    if rad < 0:
        raise ValueError('radius must be nonnegative')
    return arb(fmpq(mid.numerator, mid.denominator), fmpq(rad.numerator, rad.denominator))


def zeta_box(sigma, t, radius, dps=100):
    """Rigorous enclosure for every point in a closed rectangular input box."""
    a, b, r = Fraction(str(sigma)), Fraction(str(t)), Fraction(str(radius))
    if r <= 0:
        raise ValueError('positive box radius required')
    ctx.dps = dps
    z = acb(real_ball(sigma, radius), real_ball(t, radius))
    if a-r <= 1 <= a+r and b-r <= 0 <= b+r:
        return {'status':'REJECTED_POLE_IN_BOX', 'certified_zero_free':False}
    value = z.zeta()
    excludes = value.is_finite() and not value.contains(0)
    off_line = (a+r < Fraction(1,2) or a-r > Fraction(1,2))
    inside_strip = 0 < a-r and a+r < 1 and b-r > 0
    return {'status':'CERTIFIED_ZERO_FREE_BOX' if excludes else 'INCONCLUSIVE_VALUE_ENCLOSURE',
            'box_center_sigma':str(sigma), 'box_center_t':str(t), 'box_radius_each_coordinate':str(radius),
            'input_rectangle_avoids_critical_line':off_line,
            'input_rectangle_inside_positive_critical_strip':inside_strip,
            'arb_dps':dps, 'zeta_enclosure':str(value),
            'zeta_abs_lower_bound':str(value.abs_lower()),
            'certified_zero_free':excludes,
            'note':'Containing zero is not a proof of any root; excludes-zero certifies the whole input rectangle.'}


def check_point(sigma, t, radius='0.000001', precisions=(50,100,160)):
    rows=[]
    for dps in precisions:
        with mp.workdps(dps):
            s=mp.mpc(mp.mpf(str(sigma)), mp.mpf(str(t)))
            if not (mp.isfinite(s.real) and mp.isfinite(s.imag)):
                raise ValueError('finite coordinates required')
            value=mp.zeta(s)
            derivative=mp.zeta(s, derivative=1)
            correction=abs(value/derivative) if derivative else mp.inf
            delta=abs(s.real-mp.mpf('0.5'))
            ctx.dps=dps
            exact_input=acb(real_ball(sigma),real_ball(t))
            independent=exact_input.zeta()
            # mpmath is a rounded point estimate: do NOT require it to lie in
            # an often much narrower Arb value ball at the same precision.
            midpoint=mp.mpc(independent.real.mid().str(dps+10,radius=False),
                            independent.imag.mid().str(dps+10,radius=False))
            disagreement=abs(value-midpoint)
            agreement_scale=max(mp.mpf(1),abs(value))
            agrees=disagreement < mp.power(10, -dps+10)*agreement_scale
            rows.append({'dps':dps,
                         'zeta_real':mp.nstr(value.real,dps),
                         'zeta_imag':mp.nstr(value.imag,dps),
                         'abs_zeta':mp.nstr(abs(value),dps),
                         'abs_zeta_derivative':mp.nstr(abs(derivative),dps),
                         'newton_correction_magnitude':mp.nstr(correction,dps),
                         'distance_to_critical_line':mp.nstr(delta,dps),
                         'arb_point_enclosure':str(independent),
                         'mpmath_arb_midpoint_difference':mp.nstr(disagreement,12),
                         'independent_point_evaluations_agree':bool(agrees)})
    box=zeta_box(sigma,t,radius,max(precisions))
    return {'input_sigma':str(sigma),'input_t':str(t),
            'evaluation_rows':rows, 'box_check':box,
            'status':box['status'],
            'numeric_point_is_not_a_root_certificate':True}


def refine(sigma,t,dps=70,max_steps=40,max_height=10000):
    """Damped complex Newton. Sigma is never fixed/projected to one half."""
    with mp.workdps(dps):
        s=mp.mpc(str(sigma),str(t)); start=s
        if not (0<s.real<1 and 0<s.imag<max_height):
            return {'status':'OUTSIDE_CONFIGURED_SEARCH_BOX','seed_sigma':str(sigma),'seed_t':str(t)}
        trajectory=[]
        target=mp.power(10,-dps+15)
        status='ITERATION_LIMIT'
        for iteration in range(max_steps):
            f=mp.zeta(s); df=mp.zeta(s,derivative=1)
            trajectory.append({'iteration':iteration,'sigma':mp.nstr(s.real,dps),
                               't':mp.nstr(s.imag,dps),'residual':mp.nstr(abs(f),12)})
            if abs(f)<target:
                status='NUMERICAL_CONVERGENCE';break
            if not df:
                status='DERIVATIVE_ZERO';break
            step=f/df;accepted=False
            for k in range(16):
                trial=s-step/(2**k)
                if 0<trial.real<1 and 0<trial.imag<max_height and abs(mp.zeta(trial))<abs(f):
                    s=trial;accepted=True;break
            if not accepted:
                status='NO_DESCENT_STEP';break
        delta=abs(s.real-mp.mpf('0.5'))
        # Heuristic label only. Box count is required to certify an off-line root.
        label=('CONVERGED_NEAR_CRITICAL_LINE' if delta < mp.power(10,-dps//2)
               else 'OFF_LINE_NUMERICAL_CANDIDATE') if status=='NUMERICAL_CONVERGENCE' else status
        return {'status':status,'classification':label,
                'seed_sigma':mp.nstr(start.real,dps),'seed_t':mp.nstr(start.imag,dps),
                'final_sigma':mp.nstr(s.real,dps),'final_t':mp.nstr(s.imag,dps),
                'abs_zeta':mp.nstr(abs(mp.zeta(s)),dps),
                'distance_to_line':mp.nstr(delta,dps),
                'precision_dps':dps,'trajectory':trajectory,
                'sigma_was_free':True,'certified_off_line_zero':False}


def demo():
    started=time.perf_counter()
    with mp.workdps(180):
        height=mp.nstr(mp.im(mp.zetazero(1)),170)
    points=[('known_first_zero','0.5',height,'1e-12'),
            ('offset_can_fool_residual_only_test','0.50000001',height,'1e-12'),
            ('clearly_off_line','0.7',height,'1e-6')]
    checks={name:check_point(sigma,t,radius) for name,sigma,t,radius in points}
    assert not checks['known_first_zero']['box_check']['certified_zero_free']
    assert checks['offset_can_fool_residual_only_test']['box_check']['certified_zero_free']
    assert checks['clearly_off_line']['box_check']['certified_zero_free']
    for row in checks.values():
        assert all(v['independent_point_evaluations_agree'] for v in row['evaluation_rows'])
    search=[]
    for t in ('14','21','25'):
        for sigma in ('0.2','0.8'):
            root=refine(sigma,t)
            assert root['status']=='NUMERICAL_CONVERGENCE'
            assert root['classification']=='CONVERGED_NEAR_CRITICAL_LINE'
            search.append(root)
    # Xi is exponentially scaled at large height; small |xi| alone is deceptive.
    with mp.workdps(80):
        s=mp.mpc('0.7','1000')
        z=mp.zeta(s)
        xi=s*(s-1)/2*mp.power(mp.pi,-s/2)*mp.gamma(s/2)*z
        scaled={'sigma':'0.7','t':'1000','abs_zeta':mp.nstr(abs(z),40),
                'abs_xi':mp.nstr(abs(xi),40),
                'message':'A tiny xi value can come from the gamma factor, not from a nearby zeta zero.'}
        assert abs(z)>mp.mpf('0.01') and abs(xi)<mp.mpf('1e-200')
    return {'status':'PASS','scope':'Low-height diagnostics and controls; not a complete zero search',
            'point_checks':checks,'off_axis_newton_seeds':search,
            'xi_scaling_negative_control':scaled,'elapsed_seconds':time.perf_counter()-started}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest='mode',required=True)
    for name in ('check','refine'):
        p=sub.add_parser(name)
        p.add_argument('--sigma',required=True)
        p.add_argument('--t',required=True)
        p.add_argument('--output',type=Path)
        if name=='check': p.add_argument('--radius',default='0.000001')
        else:
            p.add_argument('--dps',type=int,default=70)
            p.add_argument('--max-height',type=int,default=10000)
    p=sub.add_parser('demo');p.add_argument('--output',type=Path,default=HERE/'demo_results.json')
    p=sub.add_parser('count')
    p.add_argument('--sigma-min',required=True);p.add_argument('--sigma-max',required=True)
    p.add_argument('--t-min',required=True);p.add_argument('--t-max',required=True)
    p.add_argument('--dps',type=int,default=60)
    p.add_argument('--max-seconds',type=float,default=30)
    p.add_argument('--output',type=Path)
    args=ap.parse_args()
    if args.mode=='check': result=check_point(args.sigma,args.t,args.radius)
    elif args.mode=='refine': result=refine(args.sigma,args.t,dps=args.dps,max_height=args.max_height)
    elif args.mode=='count':
        sys.path.insert(0,str(HERE/'certification'))
        from rectangle_count import count_rectangle
        result=count_rectangle(args.sigma_min,args.sigma_max,args.t_min,args.t_max,
                               dps=args.dps,max_seconds=args.max_seconds)
    else: result=demo()
    result['versions']={'mpmath':mp.__version__,'python_flint':flint.__version__}
    result['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    text=json.dumps(result,indent=2,ensure_ascii=False)+'\n'
    if args.output:
        args.output.write_text(text,encoding='utf-8')
        print(json.dumps({'status':result['status'],'output':str(args.output)},ensure_ascii=False))
    else: print(text)


if __name__=='__main__': main()
