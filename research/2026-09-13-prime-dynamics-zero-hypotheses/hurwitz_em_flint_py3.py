"""Arb-backed Euler--Maclaurin enclosure for Hurwitz zeta and DH combinations.

Prototype interval evaluator. Results are explicitly NONCERTIFIED until full
contour subdivision/argument-principle checks are added.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import mpmath as mp
from flint import arb, acb, ctx as flint_ctx

def cbox(sigma, t, ds, dt):
    return acb(arb(str(sigma), str(ds)), arb(str(t), str(dt)))

def bernoulli_even(k):
    return arb(str(mp.bernoulli(2*k)))

def hurwitz_em_box(s, a, n=64, m=12):
    aa=arb(str(a)); N=arb(n)+aa; out=acb(0)
    for j in range(n): out += (arb(j)+aa)**(-s)
    out += N**(1-s)/(s-1); out += acb(arb('0.5'))*N**(-s)
    for k in range(1,m+1):
        rising=acb(1)
        for q in range(2*k-1): rising *= s+q
        out += acb(bernoulli_even(k)/math.factorial(2*k))*rising*N**(-s-2*k+1)
    rising=acb(1)
    for q in range(2*m): rising *= s+q
    rs_up=float(abs(rising).upper()); sigma_lo=float(s.real.lower())
    if sigma_lo+2*m-1<=0: return out, {'remainder_status':'FAILED_DIVERGENT_BOUND','reason':'sigma+2m-1<=0'}
    zeta2m=float(mp.zeta(2*m)); coef=2*zeta2m/(2*math.pi)**(2*m); nlo=float(N.lower())
    bound=coef*rs_up/(sigma_lo+2*m-1)*nlo**(-sigma_lo-2*m+1)
    if not math.isfinite(bound): return out, {'remainder_status':'FAILED_NONFINITE_BOUND'}
    out += acb(arb(0,str(bound)),arb(0,str(bound)))
    return out, {'remainder_status':'BOUNDED','remainder_bound':bound,'n':n,'m':m,'sigma_lower':sigma_lo,'rising_upper':rs_up}

def dh_em_box(s,n=64,m=12):
    kap=(mp.sqrt(10-2*mp.sqrt(5))-2)/(mp.sqrt(5)-1); aa=[1,kap,-kap,-1,0]; total=acb(0); metas=[]
    for r,c in enumerate(aa,1):
        hz,meta=hurwitz_em_box(s,r/5,n=n,m=m); total+=acb(str(c))*hz; metas.append({'r':r,'coefficient':str(c),**meta})
    return total*(arb(5)**(-s)), metas

def scalar(z):
    return {'text':str(z),'abs_lower':float(abs(z).lower()),'abs_upper':float(abs(z).upper()),'contains_zero':bool(z.contains(0))}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--sigma',default='0.8085171824566373855533519606'); ap.add_argument('--t',default='85.69934848537759217192926771'); ap.add_argument('--ds',default='0.0001'); ap.add_argument('--dt',default='0.0001'); ap.add_argument('--n',type=int,default=128); ap.add_argument('--m',type=int,default=12); ap.add_argument('--output',type=Path,required=True); args=ap.parse_args(); mp.mp.dps=80
    flint_ctx.dps=100
    s=cbox(args.sigma,args.t,args.ds,args.dt); val,meta=dh_em_box(s,n=args.n,m=args.m)
    inp={k:(str(v) if isinstance(v,Path) else v) for k,v in vars(args).items()}
    out={'status':'NONCERTIFIED_PROTOTYPE','method':'Euler-Maclaurin Hurwitz zeta with Arb/FLINT complex boxes','input':inp,'dh_enclosure':scalar(val),'terms':meta,'interpretation':'Bounded remainder on the requested box; no contour subdivision or argument-principle proof.'}
    args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'status':out['status'],'contains_zero':out['dh_enclosure']['contains_zero'],'abs_lower':out['dh_enclosure']['abs_lower'],'output':str(args.output)}))
if __name__=='__main__': main()
