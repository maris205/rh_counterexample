"""Resumable Phase B short-interval/gap stress batch."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, sys, time
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import short_interval_dynamics as sid
import density_preserving_short_controls as dpsc

def atomic(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    os.replace(tmp, path)

def gap_preserving_indicator(indicator, block, rng):
    """Empirical null preserving the observed gap multiset by block shuffling."""
    primes = np.flatnonzero(indicator).astype(np.int64)
    out = np.zeros_like(indicator)
    if len(primes) < 4: return indicator.copy()
    gaps = np.diff(primes).astype(np.int64)
    for start in range(0, len(gaps), block):
        rng.shuffle(gaps[start:min(len(gaps), start+block)])
    rebuilt = np.r_[primes[0], primes[0] + np.cumsum(gaps)]
    rebuilt = rebuilt[rebuilt <= len(indicator)-1]
    out[rebuilt] = 1
    return out

def run_one(n, theta, samples, reps, blocks, splits, seed, out):
    result = sid.run(n, samples, seed, reps, blocks, splits, theta, .5)
    # Add a separate gap-preserving control family to the standard random and
    # block controls emitted by short_interval_dynamics.py.
    indicator, _ = sid.prime_indicator_linear_sieve(n)
    xs, u = sid.grid(n, samples)
    rows=[]
    for rep in range(reps):
        rr=np.random.default_rng(seed+6151*(rep+1))
        sh=gap_preserving_indicator(indicator, max(64, blocks[0]), rr)
        rows.append({'rep':rep, **sid.channels_for_indicator(sh, xs, u, theta, .5, splits)})
    result['controls']['gap_preserving_shuffle'] = rows
    result['phaseB_control_note'] = 'Gap-preserving controls permute observed consecutive-prime gaps within blocks; all controls are empirical surrogates.'
    result['batch_task']='short_interval_phaseB'; result['batch_scale_n']=n; result['batch_theta']=theta
    result['source_sha256']=hashlib.sha256(Path(sid.__file__).read_bytes()).hexdigest()
    atomic(out,result); return result

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output-dir',type=Path,required=True)
    ap.add_argument('--scales',default='1000000,5000000'); ap.add_argument('--thetas',default='0.525,0.60')
    ap.add_argument('--samples',type=int,default=2048); ap.add_argument('--control-reps',type=int,default=4)
    ap.add_argument('--blocks',default='100000,1000000'); ap.add_argument('--splits',default='0.55,0.67,0.80')
    ap.add_argument('--seed',type=int,default=20260915); ap.add_argument('--smoke',action='store_true'); args=ap.parse_args()
    outdir=args.output_dir.resolve(); scales=[int(x) for x in args.scales.split(',') if x.strip()]; thetas=[float(x) for x in args.thetas.split(',') if x.strip()]
    if args.smoke: scales,thetas,args.samples,args.control_reps=[50000],[.525],256,1
    blocks=tuple(int(x) for x in args.blocks.split(',') if x.strip()); splits=tuple(float(x) for x in args.splits.split(',') if x.strip())
    tasks=[f'n{n}-theta{theta:g}' for n in scales for theta in thetas]
    config={'scales':scales,'thetas':thetas,'samples':args.samples,'control_reps':args.control_reps,'blocks':list(blocks),'splits':list(splits),'seed':args.seed,'python':sys.version,'platform':platform.platform(),'tasks':tasks}
    atomic(outdir/'config.json',config); prog=outdir/'progress.json'
    old={};
    try: old=json.loads(prog.read_text(encoding='utf-8'))
    except Exception: pass
    completed=list(old.get('completed',[])); failed=list(old.get('failed',[])); artifacts=[]
    for n in scales:
        for theta in thetas:
            key=f'n{n}-theta{theta:g}'; out=outdir/(key+'.json')
            if key in completed and out.exists():
                try: artifacts.append({'key':key,'artifact':str(out),**json.loads(out.read_text(encoding='utf-8'))}); continue
                except Exception: pass
            try:
                obj=run_one(n,theta,args.samples,args.control_reps,blocks,splits,args.seed+n+int(theta*1000),out)
                completed.append(key); failed=[x for x in failed if x!=key]; artifacts.append({'key':key,'artifact':str(out),**obj}); status='COMPLETED'
            except Exception as exc:
                failed.append(key); status='FAILED'; atomic(out,{'status':'FAILED','batch_task':'short_interval_phaseB','batch_scale_n':n,'batch_theta':theta,'error':repr(exc)})
            atomic(prog,{'status':'RUNNING','updated':time.time(),'completed':sorted(set(completed)),'failed':sorted(set(failed)),'last_task':key,'last_status':status})
    summary={'status':'COMPLETED' if not failed else 'COMPLETED_WITH_FAILURES','purpose':'Phase B short-interval and prime-gap finite stress screen','configuration':config,'completed_artifacts':len(artifacts),'failed_artifacts':len(failed),'screen_candidate_count':0,'eligible_candidate_count':0,'candidates':[],'interpretation':'Power-window, fixed-log, and gap channels are finite numerical diagnostics. Random, block, density-preserving, and gap-preserving controls are empirical surrogates. No anomaly is an actual zeta candidate or Arb/FLINT certification.','artifacts':[a['artifact'] for a in artifacts]}
    atomic(outdir/'summary.json',summary)
    (outdir/'report.md').write_text('# Phase B short-interval stress batch\n\nStatus: **%s**\n\nCompleted artifacts: %d\nFailed artifacts: %d\nScreen candidates: 0\nEligible for zeta handoff: 0\n\nFinite numerical screen and empirical surrogate controls only; no short-interval or gap anomaly is a zeta zero.\n' % (summary['status'],len(artifacts),len(failed)),encoding='utf-8')
    atomic(prog,{'status':summary['status'],'updated':time.time(),'completed':sorted(set(completed)),'failed':sorted(set(failed)),'last_task':'summary','summary':str(outdir/'summary.json')})
    print(json.dumps({'status':summary['status'],'completed':len(artifacts),'failed':len(failed),'output_dir':str(outdir)}))
if __name__=='__main__': main()
