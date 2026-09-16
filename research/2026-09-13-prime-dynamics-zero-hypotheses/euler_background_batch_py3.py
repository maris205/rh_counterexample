"""Train-only known-line nuisance regression on coupled Euler-model signals.

No unit-weight subtraction, no known target supplied to selection. The same
background basis appears in null and tone regressions, both jointly fitted
on training only. Controls repeat nomination under both frozen model variants.
"""
import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import time
import traceback
import common_spectrum_v2_batch_py3 as batch
import common_spectrum_v2 as core
import euler_coupled_batch_py3 as euler
from euler_envelope_comparison_py3 import atomic
from known_ordinates import known_ordinates, known_mask
import numpy as np


def basis(u, background, t=None, origin=np.log(100.)):
    v=np.asarray(u)-origin
    cols=[np.ones(len(v)),v]
    for frequency in background:
        cols += [np.cos(frequency*v),np.sin(frequency*v)]
    if t is not None:
        cols += [np.cos(t*v),np.sin(t*v)]
    return np.column_stack(cols)


@lru_cache(maxsize=64)
def designs(u_tuple, background, frequencies, origin):
    base=basis(u_tuple,background,origin=origin)
    full=np.stack([basis(u_tuple,background,t,origin) for t in frequencies])
    for matrices in (base[None,:,:],full):
        singular=np.linalg.svd(matrices,compute_uv=False)
        if np.any(singular[:,0]/singular[:,-1]>1e8):
            raise ValueError('ill-conditioned nuisance model')
    return base,np.linalg.pinv(base),full,np.linalg.pinv(full)


def fit_cell(cell,t,background,origin):
    end=cell.cut if cell.train_end is None else cell.train_end
    base=basis(cell.u,background,origin=origin)
    full=basis(cell.u,background,t,origin)
    b0,_,r0,_=np.linalg.lstsq(base[:end],cell.y[:end],rcond=None)
    b1,_,r1,singular=np.linalg.lstsq(full[:end],cell.y[:end],rcond=None)
    if r0!=base.shape[1] or r1!=full.shape[1] or singular[0]/singular[-1]>1e8:
        raise ValueError('invalid prediction design')
    e0=np.sum((cell.y[cell.cut:]-base[cell.cut:]@b0)**2,axis=0)
    e1=np.sum((cell.y[cell.cut:]-full[cell.cut:]@b1)**2,axis=0)
    if np.any(e0<=1e-20) or not np.all(np.isfinite([e0,e1])):
        raise ValueError('invalid heldout baseline')
    return {'gains':dict(zip(core.CHANNELS,map(float,(e0-e1)/e0))),
            'baseline_sse':e0.tolist(),'model_sse':e1.tolist(),
            'train_coefficients':b1.tolist(),'baseline_train_coefficients':b0.tolist(),
            'condition_number':float(singular[0]/singular[-1])}


def evaluate(cells,frequencies,background,origin):
    anchor=min(cells,key=lambda c:(c.n,c.grid,c.split))
    boundary=min(c.u[c.cut] for c in cells)
    support=anchor.u if anchor.support_end_u is None else anchor.support_end_u
    prefix=support<boundary
    u,y=anchor.u[prefix],anchor.y[prefix]
    if len(u)<2*(4+2*len(background)):
        raise ValueError('too few common training samples')
    base,pinv,full,inverses=designs(tuple(u),tuple(background),tuple(map(float,frequencies)),origin)
    e0=np.sum((y-base@(pinv@y))**2,axis=0)
    if np.any(e0<=1e-20):
        raise ValueError('invalid training baseline')
    coefficients=np.einsum('tkm,mc->tkc',inverses,y)
    pred=np.einsum('tmk,tkc->tmc',full,coefficients)
    gains=(e0[None,:]-np.sum((y[None,:,:]-pred)**2,axis=1))/e0[None,:]
    score=np.min(gains[:,core.PRIMARY],axis=1)
    selected=[]
    for i in np.argsort(-score,kind='stable'):
        t=float(frequencies[i])
        if all(abs(t-r['t'])>=.5 for r in selected):
            selected.append({'t':t,'training_score':float(score[i])})
            if len(selected)==3:
                break
    for row in selected:
        records=[]
        for cell in cells:
            records.append({'key':cell.key,**fit_cell(cell,row['t'],background,origin)})
        minimum=min(r['gains'][core.CHANNELS[i]] for r in records for i in core.PRIMARY)
        row.update(joint_score=minimum,positive_all_cells=minimum>0,cells=records)
    return {'selected':selected,'max_statistic':max(r['joint_score'] for r in selected),
            'training_support_max':float(support[prefix][-1]),'earliest_holdout':float(boundary)}


def run(outdir,smoke=False):
    outdir=Path(outdir).resolve(); outdir.mkdir(parents=True,exist_ok=True)
    backgrounds={'linear':(), 'known_line_nuisance':known_ordinates(4.,40.,0.)}
    cfg={'scales':[30000,100000] if not smoke else [5000,10000],'grids':[[192,0.],[256,.08]],
         'splits':[.55,.75],'theta':.525,'x_min':100,'frequencies':[18.,27.],
         'amplitudes':[.03,.1,.3],'phase_seeds':[14,15,16,17] if not smoke else [14],
         'backgrounds':backgrounds,'scan':[4.,40.,.25],'known_margin':.35,'top_k':3,'separation':.5,
         'controls':['global','log_bin','block'],'control_reps':19 if not smoke else 1,
         'scope':'train-only nuisance model sensitivity; same constant-envelope target and mandatory Mertens',
         'reference_subtraction':False,'ranks':'within-design maximum across both backgrounds and all nominations',
         'condition_limit':1e8,'alpha':.05}
    manifest=batch.manifest_for(cfg)
    for name in (Path(__file__).name,'euler_coupled_batch_py3.py','euler_envelope_comparison_py3.py','euler_transfer_diagnostics_py3.py'):
        manifest['source_sha256'][name]=hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
    manifest.pop('run_id'); manifest['run_id']=batch.fingerprint(manifest)
    experiments=[(t,a,s) for t in cfg['frequencies'] for a in cfg['amplitudes'] for s in cfg['phase_seeds']]
    tasks=[('ordinary',None,None,0)]
    for i,design in enumerate(experiments):
        tasks.append((f'design{i}-real',design,None,0))
        tasks += [(f'design{i}-{mode}-{rep}',design,mode,rep) for mode in cfg['controls'] for rep in range(cfg['control_reps'])]
    with batch.run_lock(outdir):
        batch.check_manifest(outdir,manifest)
        struct=euler.structure(max(cfg['scales'])); primes=struct[1]
        scan=np.arange(4.,40.125,.25); scan=scan[~known_mask(scan,cfg['known_margin'])]
        start=time.monotonic(); results={}
        for key,design,mode,rep in tasks:
            path=outdir/f'task-{key}.json'; row=batch.completed_task(path,manifest['run_id'],key)
            if row is None:
                try:
                    weights=np.ones(len(primes))
                    if design is not None:
                        t,amp,seed=design
                        phase=np.random.default_rng(20260916+seed).uniform(-np.pi,np.pi)
                        weights += amp*np.cos(t*np.log(primes)+phase)
                    if mode:
                        seed=int.from_bytes(hashlib.sha256(f'{design}:{mode}:{rep}'.encode()).digest()[:8],'big')
                        weights=euler.shuffled_weights(primes,weights,mode,seed)
                    _,source=euler.coefficients(struct,weights)
                    cells=core.build_cells(source,cfg['scales'],cfg['grids'],cfg['splits'],cfg['theta'],cfg['x_min'])
                    models={name:evaluate(cells,scan,tuple(bg),np.log(cfg['x_min'])) for name,bg in backgrounds.items()}
                    row={'status':'COMPLETED','design':design,'control':mode,'models':models,
                         'pooled_max_statistic':max(m['max_statistic'] for m in models.values())}
                    json.dumps(row,allow_nan=False)
                except Exception as exc:
                    traceback.print_exc(); row={'status':'FAILED','error':repr(exc)}
                row.update(task_id=key,run_id=manifest['run_id']); atomic(path,row)
            results[key]=row
            atomic(outdir/'progress.json',{'status':'RUNNING','completed_count':sum(r['status']=='COMPLETED' for r in results.values()),
                'failed_count':sum(r['status']=='FAILED' for r in results.values()),'total_tasks':len(tasks),'last_task':key,'updated':batch.now()})
        comparisons=[]
        for i,design in enumerate(experiments):
            real=results[f'design{i}-real']
            if real['status']!='COMPLETED':
                continue
            controls={mode:[results[f'design{i}-{mode}-{r}']['pooled_max_statistic'] for r in range(cfg['control_reps'])
                if results[f'design{i}-{mode}-{r}']['status']=='COMPLETED'] for mode in cfg['controls']}
            complete=all(len(v)==cfg['control_reps'] for v in controls.values())
            for name,model in real['models'].items():
                rows=[]
                for candidate in model['selected']:
                    ranks={mode:core.empirical_p(candidate['joint_score'],vals) for mode,vals in controls.items() if len(vals)==cfg['control_reps']}
                    passes=complete and cfg['control_reps']>=19 and candidate['positive_all_cells'] and all(p<=cfg['alpha'] for p in ranks.values())
                    rows.append({'t':candidate['t'],'joint_score':candidate['joint_score'],'positive':candidate['positive_all_cells'],
                                 'modulation_near':abs(candidate['t']-design[0])<=.25,'pooled_ranks':ranks,'descriptive_control_pass':passes})
                comparisons.append({'design':design,'model':name,'controls_complete':complete,'nominations':rows})
        aggregate=[]
        for amp in cfg['amplitudes']:
            for model in backgrounds:
                rows=[r for r in comparisons if r['model']==model and r['design'][1]==amp]
                aggregate.append({'amplitude':amp,'model':model,'designs':len(rows),
                    'modulation_selected':sum(any(c['modulation_near'] for c in r['nominations']) for r in rows),
                    'modulation_positive':sum(any(c['modulation_near'] and c['positive'] for c in r['nominations']) for r in rows),
                    'any_positive':sum(any(c['positive'] for c in r['nominations']) for r in rows),
                    'modulation_control_pass':sum(any(c['modulation_near'] and c['descriptive_control_pass'] for c in r['nominations']) for r in rows),
                    'any_control_pass':sum(any(c['descriptive_control_pass'] for c in r['nominations']) for r in rows)})
        failed=sum(r['status']=='FAILED' for r in results.values())
        summary={'status':'COMPLETED_WITH_FAILURES' if failed else 'COMPLETED','run_id':manifest['run_id'],'configuration':cfg,
            'completed_count':len(results)-failed,'failed_count':failed,'total_tasks':len(tasks),'aggregate':aggregate,
            'comparisons':comparisons,'elapsed_s_this_session':time.monotonic()-start,'candidate_count':None,'gate_status':'MODEL_CALIBRATION_ONLY',
            'interpretation':'Background and target coefficients are jointly fitted on training data only. No oracle subtraction. Ranks pool both models within each design but not 24 designs together; passing is descriptive model sensitivity only. Ordinary-unit-weight run is a reference, not a false-positive rate. No actual-zeta evaluation or Arb/FLINT certificate.'}
        atomic(outdir/'summary.json',summary)
        atomic(outdir/'progress.json',{k:summary[k] for k in ('status','completed_count','failed_count','total_tasks')})
        lines=['# Train-only nuisance model comparison','',summary['interpretation'],'',
            '| amplitude | model | nominated near modulation | modulation positive | modulation control pass | any control pass | designs |','|---|---|---|---|---|---|---|']
        lines += [f"| {r['amplitude']} | {r['model']} | {r['modulation_selected']} | {r['modulation_positive']} | {r['modulation_control_pass']} | {r['any_control_pass']} | {r['designs']} |" for r in aggregate]
        (outdir/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--output-dir',type=Path,required=True); parser.add_argument('--smoke',action='store_true')
    args=parser.parse_args(); summary=run(args.output_dir,args.smoke)
    print(json.dumps({k:summary[k] for k in ('status','completed_count','failed_count','aggregate')}))
    raise SystemExit(bool(summary['failed_count']))
