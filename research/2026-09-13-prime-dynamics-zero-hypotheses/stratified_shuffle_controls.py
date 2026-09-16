"""Local-density-preserving shuffle controls for the multi-grid demodulator."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from multi_grid_demod import cumulative_grid, demod_scan
from mertens_dynamics import mobius_sieve
from lambda_psi_dynamics import von_mangoldt_theta_linear_sieve


def block_permute(arr, rng, block):
    out=arr.copy(); blocks=[out[i:min(len(out),i+block)].copy() for i in range(1,len(out),block)]
    rng.shuffle(blocks); pos=1
    for b in blocks: out[pos:pos+len(b)]=b; pos+=len(b)
    return out


def within_block(arr, rng, block):
    out=arr.copy()
    for i in range(1,len(out),block):
        j=min(len(out),i+block); rng.shuffle(out[i:j])
    return out


def score(chans,n,grids,tgrid,window=(37.,38.)):
    vals=[]
    for m,phase in grids:
        for name,a in chans.items():
            cumulative = np.cumsum(a, dtype=np.float64)
            u,y=cumulative_grid(cumulative,n,m,phase,name); rows=demod_scan(u,np.gradient(y,u),tgrid,1)
            vals += [r['r2'] for r in rows if window[0]<=r['t']<=window[1]]
    return max(vals) if vals else 0.


def run(n: int, samples: int, reps: int, block: int, seed: int = 20260914) -> dict:
    """Programmatic entry point used by the resumable Phase A runner."""
    mu = mobius_sieve(n)
    lam, theta = von_mangoldt_theta_linear_sieve(n)
    grids = [(max(128, samples // 2), 0.0), (samples, 0.08)]
    tg = np.arange(37., 38.0001, .05)
    base = {'mertens': mu.astype(float), 'psi': lam.astype(float), 'theta': theta.astype(float)}
    real = score(base, n, grids, tg)
    rows = []
    for rep in range(reps):
        rng = np.random.default_rng(seed + rep * 1009)
        g = {k: block_permute(v, rng, block) for k, v in base.items()}
        w = {k: within_block(v, rng, block) for k, v in base.items()}
        rows.append({'rep': rep, 'block_permute': score(g, n, grids, tg),
                     'within_block': score(w, n, grids, tg)})
    bp = [r['block_permute'] for r in rows]
    wb = [r['within_block'] for r in rows]
    return {'status': 'COMPLETED',
            'purpose': 'stratified block-permutation and within-block shuffle controls; not a zeta certificate',
            'configuration': {'n': n, 'samples': samples, 'reps': reps, 'block': block,
                              'grids': grids, 'window': [37., 38.]},
            'real_max_r2': real, 'replicates': rows,
            'quantiles': {'block_permute_q95': float(np.quantile(bp, .95)) if bp else 0.,
                         'within_block_q95': float(np.quantile(wb, .95)) if wb else 0.,
                         'block_permute_mean': float(np.mean(bp)) if bp else 0.,
                         'within_block_mean': float(np.mean(wb)) if wb else 0.},
            'interpretation': 'Empirical local-structure controls only; exceedance is not evidence of an off-line zeta zero.'}


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--n',type=int,default=1_000_000); ap.add_argument('--reps',type=int,default=8)
    ap.add_argument('--block',type=int,default=50_000); ap.add_argument('--output',type=Path,required=True); args=ap.parse_args()
    mu=mobius_sieve(args.n); lam,theta=von_mangoldt_theta_linear_sieve(args.n)
    base={'mertens':mu.astype(float),'psi':lam.astype(float),'theta':theta.astype(float)}
    grids=[(1024,0.0),(1536,0.02),(2048,0.05)]; tg=np.arange(37.,38.0001,.05)
    real=score(base,args.n,grids,tg); rows=[]
    for rep in range(args.reps):
        rng=np.random.default_rng(20260913+rep*1009)
        g={k:block_permute(v,rng,args.block) for k,v in base.items()}
        w={k:within_block(v,rng,args.block) for k,v in base.items()}
        rows.append({'rep':rep,'block_permute':score(g,args.n,grids,tg),'within_block':score(w,args.n,grids,tg)})
    bp=[r['block_permute'] for r in rows]; wb=[r['within_block'] for r in rows]
    out={'status':'COMPLETED','purpose':'stratified shuffle control quantiles; not a zeta certificate',
         'configuration':{'n':args.n,'reps':args.reps,'block':args.block,'grids':grids,'window':[37.,38.]},
         'real_max_r2':real,'replicates':rows,
         'quantiles':{'block_permute_q95':float(np.quantile(bp,.95)),'within_block_q95':float(np.quantile(wb,.95)),
                      'block_permute_mean':float(np.mean(bp)),'within_block_mean':float(np.mean(wb))},
         'interpretation':'Within-block controls preserve local cumulative shape and may be conservative; block permutation disrupts long-range order while retaining block distributions.'}
    args.output.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); print(json.dumps({'status':out['status'],'real':real,'quantiles':out['quantiles']}))

if __name__=='__main__': main()
