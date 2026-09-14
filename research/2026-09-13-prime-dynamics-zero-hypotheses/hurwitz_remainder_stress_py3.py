"""Point-precision stress audit for Hurwitz Euler--Maclaurin remainders.
This is an audit, not an interval proof. Derivative majorants are heuristic.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
from typing import Iterable
import mpmath as mp

def hurwitz_em(s: mp.mpc, a: mp.mpf, n: int, m: int) -> mp.mpc:
    q = mp.fsum((mp.mpc(j) + a) ** (-s) for j in range(n)); x = mp.mpf(n) + a
    q += x ** (1 - s) / (s - 1) + mp.mpf("0.5") * x ** (-s)
    for k in range(1, m + 1):
        q += mp.bernpoly(2*k,0)/mp.factorial(2*k)*mp.rf(s,2*k-1)*x**(-s-2*k+1)
    return q

def hurwitz_em_derivative(s: mp.mpc, a: mp.mpf, n: int, m: int) -> mp.mpc:
    q = mp.fsum(-mp.log(mp.mpc(j)+a)*(mp.mpc(j)+a)**(-s) for j in range(n)); x=mp.mpf(n)+a
    main=x**(1-s)/(s-1); q += main*(-mp.log(x)-1/(s-1)); q += mp.mpf("-0.5")*mp.log(x)*x**(-s)
    for k in range(1,m+1):
        L=2*k-1; term=mp.bernpoly(2*k,0)/mp.factorial(2*k)*mp.rf(s,L)*x**(-s-L)
        q += term*(mp.fsum(1/(s+j) for j in range(L))-mp.log(x))
    return q

def scalar_remainder_bound(s,a,n,m):
    sigma=mp.re(s); x=mp.mpf(n)+a; coef=2*mp.zeta(2*m)/(2*mp.pi)**(2*m)
    return coef*abs(mp.rf(s,2*m))/(sigma+2*m-1)*x**(-sigma-2*m+1)

def heuristic_derivative_bound(s,a,n,m):
    b=scalar_remainder_bound(s,a,n,m); sigma=mp.re(s); x=mp.mpf(n)+a; L=2*m
    factor=mp.log(x)+1/abs(sigma+2*m-1)+mp.fsum(abs(1/(s+j)) for j in range(L))
    return b*(1+factor)

def test_points(root):
    offsets=((0,0),(.01,0),(-.01,0),(0,.01),(0,-.01),(.005,.005),(-.005,.005),(.0025,-.0075))
    return (root+mp.mpc(str(x),str(y)) for x,y in offsets)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",type=Path,required=True); ap.add_argument("--dps",type=int,default=90); args=ap.parse_args(); mp.mp.dps=args.dps
    root=mp.mpc("0.8085171824566373855533519606","85.69934848537759217192926771"); rows=[]
    for n in (32,64,128,256):
      for m in (8,10,12,14,16):
       for s in test_points(root):
        for r in range(1,6):
         a=mp.mpf(r)/5; exact=mp.zeta(s,a); exact_d=mp.diff(lambda z:mp.zeta(z,a),s); approx=hurwitz_em(s,a,n,m); approx_d=hurwitz_em_derivative(s,a,n,m); err=abs(approx-exact); derr=abs(approx_d-exact_d); bound=scalar_remainder_bound(s,a,n,m); dbound=heuristic_derivative_bound(s,a,n,m)
         rows.append({"N":n,"M":m,"point_re":float(mp.re(s)),"point_im":float(mp.im(s)),"r":r,"value_error":float(err),"value_bound":float(bound),"value_ratio":float(err/bound) if bound else math.inf,"derivative_error":float(derr),"heuristic_derivative_bound":float(dbound),"derivative_ratio":float(derr/dbound) if dbound else math.inf})
    vr=[x["value_ratio"] for x in rows]; dr=[x["derivative_ratio"] for x in rows]; by_nm=[]
    for n in (32,64,128,256):
      for m in (8,10,12,14,16):
       sub=[x for x in rows if x["N"]==n and x["M"]==m]; by_nm.append({"N":n,"M":m,"max_value_ratio":max(x["value_ratio"] for x in sub),"max_derivative_ratio":max(x["derivative_ratio"] for x in sub),"value_violations":sum(x["value_ratio"]>1 for x in sub),"derivative_heuristic_violations":sum(x["derivative_ratio"]>1 for x in sub)})
    result={"status":"COMPLETED_POINT_REMAINDER_STRESS","precision_dps":args.dps,"root_seed":[mp.nstr(mp.re(root),35),mp.nstr(mp.im(root),35)],"rows":len(rows),"grid":{"N":[32,64,128,256],"M":[8,10,12,14,16],"points":8,"hurwitz_components":5},"max_value_error_to_bound_ratio":max(vr),"value_majorant_violations":sum(x>1 for x in vr),"max_derivative_error_to_heuristic_bound_ratio":max(dr),"derivative_heuristic_violations":sum(x>1 for x in dr),"by_N_M":by_nm,"interpretation":"Point-precision audit only. Value majorant is tested at sampled points; derivative bound is explicitly heuristic and is not an interval theorem.","rows_detail":rows}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); print(json.dumps({"status":result["status"],"rows":len(rows),"max_value_ratio":float(max(vr)),"value_violations":result["value_majorant_violations"],"max_derivative_ratio":float(max(dr)),"derivative_heuristic_violations":result["derivative_heuristic_violations"],"output":str(args.output)},ensure_ascii=False))

if __name__=="__main__": main()
