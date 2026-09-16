"""Small control-quantile audit for the rejected multi-grid residual near t=37.5."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from multi_grid_demod import cumulative_grid, demod_scan, select_peaks, KNOWN_T
from mertens_dynamics import mobius_sieve
from lambda_psi_dynamics import von_mangoldt_theta_linear_sieve


def score_window(cumulative, n, grids, t_grid, lo=37.0, hi=38.0):
    values=[]
    for samples, phase in grids:
        for name in ('mertens','psi','theta'):
            u,y=cumulative_grid(cumulative[name],n,samples,phase,name)
            rows=demod_scan(u,np.gradient(y,u),t_grid,1)
            values.extend(r['r2'] for r in rows if lo<=r['t']<=hi)
    return max(values) if values else 0.0


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--n',type=int,default=1_000_000)
    ap.add_argument('--reps',type=int,default=6); ap.add_argument('--seed',type=int,default=20260913)
    ap.add_argument('--output',type=Path,required=True); args=ap.parse_args()
    mu=mobius_sieve(args.n); lam,theta=von_mangoldt_theta_linear_sieve(args.n)
    grids=[(1024,0.0),(1536,0.02),(2048,0.05)]; t_grid=np.arange(37.0,38.0001,0.05)
    real={"mertens":mu.astype(float),"psi":lam.astype(float),"theta":theta.astype(float)}
    real_score=score_window({k: np.cumsum(v) for k,v in real.items()},args.n,grids,t_grid)
    rows=[]
    for rep in range(args.reps):
        rng=np.random.default_rng(args.seed+rep*1009); controls={}
        for name,arr in real.items():
            z=arr.copy(); rng.shuffle(z[1:]); controls[name]=np.cumsum(z)
        rows.append({'rep':rep,'global_shuffle_max_r2':score_window(controls,args.n,grids,t_grid)})
    q95=float(np.quantile([r['global_shuffle_max_r2'] for r in rows],.95))
    out={'status':'COMPLETED','purpose':'control quantile for rejected multi-grid residual; not a zeta certificate',
         'configuration':{'n':args.n,'reps':args.reps,'grids':grids,'t_window':[37.0,38.0]},
         'real_max_r2':real_score,'controls':rows,'control_q95':q95,
         'passes_q95':bool(real_score>q95),
         'interpretation':'This is a focused null check for the t~37.5 residual; global shuffles are not a theorem-level null for cumulative arithmetic.'}
    args.output.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); print(json.dumps({'status':out['status'],'real':real_score,'q95':q95,'passes':out['passes_q95']}))

if __name__=='__main__': main()
