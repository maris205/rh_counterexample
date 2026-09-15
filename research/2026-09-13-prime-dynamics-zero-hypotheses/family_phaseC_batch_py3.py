"""Resumable Phase C family hierarchy and negative-control batch."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, sys, time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
import family_control_panel as fcp
import family_detector_transfer as fdt

def atomic(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+'.tmp'); tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); os.replace(tmp,path)

def detector(family,n,samples,reps,splits,seed):
    spec=fdt.FAMILIES[family]; sigma=float(spec['target']['sigma']); target=float(spec['target']['t']); period=list(spec['period'])
    a=fdt.coefficient_array(period,n,False); u,idx=fdt.log_grid(n,samples); signal=fdt.run_one(a,u,idx,sigma,target,splits,8)
    rng=np.random.default_rng(seed); controls={'global_shuffle':[],'block_shuffle':[]}
    for _ in range(reps):
        controls['global_shuffle'].append(fdt.run_one(fdt.shuffled(a,rng,'global',5000),u,idx,sigma,target,splits,8))
        controls['block_shuffle'].append(fdt.run_one(fdt.shuffled(a,rng,'block',5000),u,idx,sigma,target,splits,8))
    return {'schema':'family-detector-transfer-v1','status':'COMPLETED','purpose':'method-sensitivity calibration only; not a zeta zero certificate','configuration':{'family':family,'description':spec['description'],'period':period,'n':n,'samples':samples,'sigma':sigma,'target_t':target,'splits':splits,'control_reps':reps,'seed':seed},'signal':signal,'controls':controls,'interpretation':'Periodic-family responses test detector sensitivity. Davenport-Heilbronn is an off-line fixture with no contour certification and cannot transfer to zeta.'}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output-dir',type=Path,required=True); ap.add_argument('--n',type=int,default=200000); ap.add_argument('--samples',type=int,default=2048); ap.add_argument('--control-reps',type=int,default=3); ap.add_argument('--splits',default='0.55,0.67,0.80'); ap.add_argument('--seed',type=int,default=20260915); ap.add_argument('--smoke',action='store_true'); args=ap.parse_args()
    outdir=args.output_dir.resolve(); n=args.n; samples=args.samples; reps=args.control_reps
    if args.smoke: n,samples,reps=20000,256,1
    splits=[float(x) for x in args.splits.split(',') if x.strip()]; tasks=['panel','dh','chi4','chi5']; atomic(outdir/'config.json',{'n':n,'samples':samples,'control_reps':reps,'splits':splits,'seed':args.seed,'python':sys.version,'platform':platform.platform(),'tasks':tasks})
    prog=outdir/'progress.json'; old={}
    try: old=json.loads(prog.read_text(encoding='utf-8'))
    except Exception: pass
    done=list(old.get('completed',[])); failed=list(old.get('failed',[])); artifacts=[]
    for task in tasks:
        key=f'n{n}-{task}'; out=outdir/(key+'.json')
        if key in done and out.exists():
            try: artifacts.append({'key':key,'artifact':str(out),**json.loads(out.read_text(encoding='utf-8'))}); continue
            except Exception: pass
        try:
            obj=fcp.build_report(80) if task=='panel' else detector(task,n,samples,reps,splits,args.seed+n+len(task))
            obj['batch_task']=task; obj['source_sha256']=hashlib.sha256(Path((fcp if task=='panel' else fdt).__file__).read_bytes()).hexdigest(); atomic(out,obj); done.append(key); failed=[x for x in failed if x!=key]; artifacts.append({'key':key,'artifact':str(out),**obj}); status='COMPLETED'
        except Exception as exc:
            failed.append(key); status='FAILED'; atomic(out,{'status':'FAILED','batch_task':task,'error':repr(exc)})
        atomic(prog,{'status':'RUNNING','updated':time.time(),'completed':sorted(set(done)),'failed':sorted(set(failed)),'last_task':key,'last_status':status})
    summary={'status':'COMPLETED' if not failed else 'COMPLETED_WITH_FAILURES','purpose':'Phase C family hierarchy and negative-control finite calibration','configuration':{'n':n,'samples':samples,'control_reps':reps,'splits':splits,'tasks':tasks},'completed_artifacts':len(artifacts),'failed_artifacts':len(failed),'screen_candidate_count':0,'eligible_candidate_count':0,'candidates':[],'interpretation':'Character and finite-field rows are calibration controls. The Davenport-Heilbronn off-line fixture remains uncertified; no family result transfers to the Riemann zeta function.','artifacts':[a['artifact'] for a in artifacts]}
    atomic(outdir/'summary.json',summary); (outdir/'report.md').write_text('# Phase C family hierarchy batch\n\nStatus: **%s**\n\nCompleted artifacts: %d\nFailed artifacts: %d\nScreen candidates: 0\nEligible for zeta handoff: 0\n\nFamily controls measure detector sensitivity only; no row is an Arb/FLINT certificate or an RH result.\n' % (summary['status'],len(artifacts),len(failed)),encoding='utf-8'); atomic(prog,{'status':summary['status'],'updated':time.time(),'completed':sorted(set(done)),'failed':sorted(set(failed)),'last_task':'summary','summary':str(outdir/'summary.json')}); print(json.dumps({'status':summary['status'],'completed':len(artifacts),'failed':len(failed),'output_dir':str(outdir)}))
if __name__=='__main__': main()
