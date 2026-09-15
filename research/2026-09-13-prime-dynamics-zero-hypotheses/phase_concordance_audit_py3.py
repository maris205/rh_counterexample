"""Audit phase coherence of existing Phase A screen clusters."""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import numpy as np

def audit(path: Path, target: float, tol: float) -> dict:
    d=json.loads(path.read_text(encoding='utf-8')); hits=[]
    for rec in d.get('records',[]):
        for row in rec.get('peaks',[]):
            if abs(float(row.get('t',0))-target)<=tol:
                hits.append({'channel':rec.get('channel'),'samples':rec.get('samples'),'trim':rec.get('phase'),'t':row['t'],'r2':row['r2'],'phase':row.get('phase',0.0)})
    if hits:
        z=np.asarray([complex(math.cos(x['phase']),math.sin(x['phase'])) for x in hits]); resultant=float(abs(np.mean(z))); mean_phase=float(math.atan2(np.mean(np.sin([x['phase'] for x in hits])),np.mean(np.cos([x['phase'] for x in hits]))))
    else: resultant=0.; mean_phase=0.
    controls=d.get('control_quantiles',[]); q95=[float(x.get('top_q95',0)) for x in controls if 'top_q95' in x]
    return {'source':str(path),'n':d.get('batch_scale_n'),'target_t':target,'tolerance':tol,'hit_count':len(hits),'grid_count':len({(x['samples'],x['trim']) for x in hits}),'channel_count':len({x['channel'] for x in hits}),'phase_resultant':resultant,'mean_phase':mean_phase,'max_r2':max([x['r2'] for x in hits],default=0.),'control_top_q95_max':max(q95,default=0.),'hits':hits}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--inputs',nargs='+',type=Path,required=True); ap.add_argument('--output',type=Path,required=True); ap.add_argument('--target',type=float,default=37.5); ap.add_argument('--tolerance',type=float,default=.15); args=ap.parse_args()
    rows=[audit(p.resolve(),args.target,args.tolerance) for p in args.inputs]; common=bool(len(rows)>=2 and all(r['hit_count']>=3 and r['grid_count']>=2 and r['channel_count']>=3 for r in rows)); min_res=min([r['phase_resultant'] for r in rows],default=0.)
    out={'schema':'phase-concordance-audit-v1','status':'COMPLETED','purpose':'phase-coherence audit of a finite Phase A screen cluster','rows':rows,'common_scale_screen':common,'min_phase_resultant':min_res,'eligible_for_zeta':False,'interpretation':'Phase resultant is a descriptive finite-window statistic. It is not a significance test, actual zeta candidate, or Arb/FLINT certification; no handoff is allowed without preregistered control and holdout gates.'}
    args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8'); md=args.output.with_suffix('.md'); md.write_text('# Phase coherence audit\n\nFinite phase-circle check for the pre-existing `t≈37.5` screen cluster.\n\n'+ '\n'.join(f"- N={r['n']}: hits={r['hit_count']}, grids={r['grid_count']}, channels={r['channel_count']}, phase resultant={r['phase_resultant']:.4f}, max R²={r['max_r2']:.4f}, control top-q95 max={r['control_top_q95_max']:.4f}" for r in rows)+'\n\nNo row is eligible for zeta refinement or Arb/FLINT certification.\n',encoding='utf-8'); print(json.dumps({'status':out['status'],'common_scale_screen':common,'min_phase_resultant':min_res,'output':str(args.output)}))
if __name__=='__main__': main()
