"""Direct frequency demodulation on several independent log-grid sizes."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np


def mobius_sieve(n):
    mu=np.zeros(n+1,dtype=np.int8); comp=np.zeros(n+1,dtype=np.bool_); ps=[]; mu[1]=1
    for i in range(2,n+1):
        if not comp[i]: ps.append(i); mu[i]=-1
        for p in ps:
            v=i*p
            if v>n: break
            comp[v]=True
            if i%p==0: mu[v]=0; break
            mu[v]=-mu[i]
    return mu


def demod(u,y,ts):
    z=y-np.polyval(np.polyfit(u,y,3),u)
    out=[]
    for t in ts:
        X=np.column_stack((np.cos(t*u),np.sin(t*u)))
        c=np.linalg.lstsq(X,z,rcond=None)[0]; fit=X@c
        out.append({'t':float(t),'r2':float(np.sum(fit*fit)/np.sum(z*z)),
                    'amplitude':float(np.hypot(c[0],c[1])),'phase':float(np.arctan2(c[1],c[0]))})
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--n',type=int,default=10_000_000)
    ap.add_argument('--grid-sizes',default='2048,3072,4096'); ap.add_argument('--t-offsets',default='0,0.125,0.25'); ap.add_argument('--t-min',type=float,default=5.0)
    ap.add_argument('--t-max',type=float,default=40.0); ap.add_argument('--t-step',type=float,default=.25)
    ap.add_argument('--output',type=Path,required=True); args=ap.parse_args()
    mu=mobius_sieve(args.n); xs=np.unique(np.maximum(2,np.geomspace(2,args.n,20000).astype(np.int64)))
    M=np.cumsum(mu,dtype=np.int64)[xs-1]; u=np.log(xs.astype(float)); y=M/np.sqrt(xs.astype(float))
    base_ts=np.arange(args.t_min,args.t_max+args.t_step/2,args.t_step); grids={}
    known=[14.1347251417,21.0220396388,25.0108575801,30.4248761259,32.9350615877]
    for m in [int(x) for x in args.grid_sizes.split(',')]:
        ug=np.linspace(u[0],u[-1],m); yg=np.interp(ug,u,y)
        for off in [float(x) for x in args.t_offsets.split(',')]:
            rows=demod(ug,yg,base_ts+off)
            rows=[r for r in rows if all(abs(r['t']-q)>.75 for q in known)]
            grids[f'{m}@{off:g}']={'top':sorted(rows,key=lambda r:r['r2'],reverse=True)[:12]}
    # A frequency is stable only if it has a nearby top row on every grid.
    stable=[]
    first_key=next(iter(grids))
    for row in grids[first_key]['top']:
        t=row['t']; matches=[]
        for v in grids.values():
            matches.append(min(((abs(x['t']-t),x) for x in v['top']), key=lambda pair: pair[0]))
        if all(d<=.5 for d,x in matches): stable.append({'t':t,'matches':[x for d,x in matches]})
    out={'status':'COMPLETED','purpose':'independent log-grid demodulation; not a zeta-zero certificate',
         'configuration':{'n':args.n,'grid_sizes':[int(x) for x in args.grid_sizes.split(',')],'t_offsets':[float(x) for x in args.t_offsets.split(',')],'t_range':[args.t_min,args.t_max]},
         'grids':grids,'stable_candidates':stable,
         'interpretation':'Different interpolation grid sizes are a discretization check; controls and direct zeta certification are still required.'}
    args.output.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); print(json.dumps({'status':out['status'],'stable_count':len(stable),'output':str(args.output)}))

if __name__=='__main__': main()
