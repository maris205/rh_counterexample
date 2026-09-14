"""Analytic derivative enclosure for the DH Euler--Maclaurin prototype.

This is a Python 3 diagnostic.  It differentiates every finite
Euler--Maclaurin term with respect to ``s`` using Arb/FLINT complex
intervals.  The differentiated remainder is bounded by differentiating
the scalar majorant used by :mod:`hurwitz_em_flint_py3` (product-rule bound,
including the denominator and N-power terms).  Consequently the result is
substantially stronger than sampled finite differences, but remains marked
NONCERTIFIED: the scalar majorant is not yet a published interval theorem
for the complex Hurwitz remainder and the contour argument is not closed.
"""
from __future__ import annotations
import argparse, json, math, sys
from pathlib import Path
import mpmath as mp
from flint import arb, acb, ctx as flint_ctx

def cbox(sigma, t, ds, dt):
    return acb(arb(str(sigma), str(ds)), arb(str(t), str(dt)))

def bernoulli_even(k):
    return arb(str(mp.bernoulli(2*k)))

def _prod_and_deriv(s, count):
    p, dp = acb(1), acb(0)
    for q in range(count):
        f = s + q
        dp = dp*f + p
        p = p*f
    return p, dp

def _abs_up(z):
    return float(z.abs_upper())

def hurwitz_em_with_derivative(s, a, n=128, m=12):
    """Return H(s), H'(s), metadata, using differentiated EM terms."""
    aa = arb(str(a)); N = arb(n) + aa; out, dout = acb(0), acb(0)
    logN = acb(N.log())
    for j in range(n):
        base = arb(j) + aa
        p = acb(base) ** (-s)
        out += p
        dout += -acb(base.log()) * p
    den = s - 1
    main = N**(1-s) / den
    out += main
    dout += main * (-logN - 1/den)
    half = acb(arb('0.5')) * N**(-s)
    out += half; dout += -logN * half
    for k in range(1, m+1):
        rise, drise = _prod_and_deriv(s, 2*k-1)
        coef = acb(bernoulli_even(k) / math.factorial(2*k))
        npow = N**(-s-2*k+1)
        term = coef * rise * npow
        out += term
        dout += coef * (drise*npow - rise*logN*npow)

    # Scalar majorant used by the earlier prototype, plus its product-rule
    # derivative.  This is an explicit finite bound, not an interval proof
    # of the Hurwitz remainder derivative.
    rise_m, drise_m = _prod_and_deriv(s, 2*m)
    r_up, dr_up = _abs_up(rise_m), _abs_up(drise_m)
    sigma_lo = float(s.real.lower())
    d = sigma_lo + 2*m - 1
    nlo = float(N.lower())
    coef = 2*float(mp.zeta(2*m))/(2*math.pi)**(2*m)
    if d <= 0 or nlo <= 0:
        meta = {'remainder_status':'FAILED_DIVERGENT_BOUND', 'sigma_lower':sigma_lo}
        return out, dout, meta
    npow = nlo**(-sigma_lo-2*m+1)
    rem = coef * r_up/d * npow
    drem = coef * npow * (dr_up/d + r_up*(1/d**2 + math.log(nlo)/d))
    # Enclose the value and derivative remainder in centred discs.  The
    # derivative disc is what supplies the Lipschitz constant below.
    out += acb(arb(0, str(rem)))
    dout += acb(arb(0, str(drem)))
    meta = {'remainder_status':'BOUNDED_SCALAR_MAJORANT',
            'remainder_bound':rem, 'remainder_derivative_bound':drem,
            'n':n, 'm':m, 'sigma_lower':sigma_lo,
            'rising_upper':r_up, 'rising_derivative_upper':dr_up}
    return out, dout, meta

def dh_em_with_derivative(s, n=128, m=12):
    kap=(mp.sqrt(10-2*mp.sqrt(5))-2)/(mp.sqrt(5)-1)
    coeff=[1,kap,-kap,-1,0]
    total, dtotal, metas = acb(0), acb(0), []
    for r,c in enumerate(coeff,1):
        h, dh, meta = hurwitz_em_with_derivative(s, r/5, n=n, m=m)
        cc=acb(str(c)); total += cc*h; dtotal += cc*dh; metas.append({'r':r,'coefficient':str(c),**meta})
    p5=arb(5)**(-s)
    dp5=-acb(arb(5).log())*p5
    return p5*total, p5*dtotal + dp5*total, metas

def dh_point(z):
    kap=(mp.sqrt(10-2*mp.sqrt(5))-2)/(mp.sqrt(5)-1)
    aa=[1,kap,-kap,-1,0]
    return 5**(-z)*sum(aa[r-1]*mp.zeta(z,mp.mpf(r)/5) for r in range(1,6))

def segments(sig, tt, ds, dt, e):
    for j in range(e):
        u0,u1=-ds+2*ds*j/e,-ds+2*ds*(j+1)/e
        yield sig+(u0+u1)/2,tt-dt,(u1-u0)/2,1
    for j in range(e):
        v0,v1=-dt+2*dt*j/e,-dt+2*dt*(j+1)/e
        yield sig+ds,tt+(v0+v1)/2,(v1-v0)/2,1j
    for j in range(e-1,-1,-1):
        u0,u1=-ds+2*ds*j/e,-ds+2*ds*(j+1)/e
        yield sig+(u0+u1)/2,tt+dt,(u1-u0)/2,1
    for j in range(e-1,-1,-1):
        v0,v1=-dt+2*dt*j/e,-dt+2*dt*(j+1)/e
        yield sig-ds,tt+(v0+v1)/2,(v1-v0)/2,1j

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--sigma',default='0.8085171824566373855533519606'); ap.add_argument('--t',default='85.69934848537759217192926771')
    ap.add_argument('--ds',default='0.01'); ap.add_argument('--dt',default='0.01'); ap.add_argument('--edge-points',type=int,default=64)
    ap.add_argument('--n',type=int,default=128); ap.add_argument('--m',type=int,default=12); ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args(); mp.mp.dps=80; flint_ctx.dps=100
    sig,tt,ds,dt=map(mp.mpf,(args.sigma,args.t,args.ds,args.dt)); rows=[]
    for idx,(sc,tc,half,tan) in enumerate(segments(sig,tt,ds,dt,args.edge_points)):
        sw,tw=(half,0) if tan==1 else (0,half)
        box,dbox,meta=dh_em_with_derivative(cbox(sc,tc,sw,tw),n=args.n,m=args.m)
        center=dh_point(mp.mpc(sc,tc)); L=_abs_up(dbox)
        lower=max(mp.mpf(0),abs(center)-mp.mpf(L)*half)
        rows.append({'index':idx,'centre':[str(sc),str(tc)],'half_length':str(half),
                     'box_abs_lower':float(abs(box).lower()),'derivative_abs_upper':L,
                     'centre_abs':float(abs(center)),'taylor_interval_lower':float(lower),
                     'remainder_status':sorted(set(x['remainder_status'] for x in meta))})
    lowers=[r['taylor_interval_lower'] for r in rows]; naive=[r['box_abs_lower'] for r in rows]
    out={'status':'NONCERTIFIED_INTERVAL_DERIVATIVE_DIAGNOSTIC',
         'method':'analytic EM derivative with Arb/FLINT + scalar differentiated remainder majorant',
         'configuration':{k:(str(v) if isinstance(v,Path) else v) for k,v in vars(args).items()},
         'boundary_segments':len(rows),
         'summary':{'segments_positive_taylor_lower':sum(x>0 for x in lowers),
                    'minimum_taylor_lower':min(lowers) if lowers else 0.0,
                    'minimum_naive_box_lower':min(naive) if naive else 0.0,
                    'maximum_derivative_upper':max(r['derivative_abs_upper'] for r in rows) if rows else 0.0},
         'segments':rows,
         'interpretation':'Analytic derivative enclosure replaces sampled finite differences. The differentiated remainder is only a scalar majorant and has not been independently proved as a complex interval bound; contour phase accumulation is still absent.'}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':out['status'],**out['summary'],'output':str(args.output)},ensure_ascii=False))
if __name__=='__main__': main()
