"""Paired diagnostic of scan spacing and Mertens background; no discovery gate."""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import traceback
import numpy as np
import common_spectrum_v2_batch_py3 as batch
import common_spectrum_v2 as core
import euler_coupled_batch_py3 as euler
import euler_envelope_comparison_py3 as comparison
from euler_transfer_diagnostics_py3 import fit
from known_ordinates import known_mask


def training_scan(cells, frequencies, betas, origin):
    boundary = min(c.u[c.cut] for c in cells)
    anchor = min(cells,key=lambda c:(c.n,c.grid,c.split))
    support = anchor.u if anchor.support_end_u is None else anchor.support_end_u
    prefix = support < boundary
    u,y = anchor.u[prefix],anchor.y[prefix]
    if len(u)<16:
        raise ValueError('short common prefix')
    gains=[]
    for ci in range(len(core.CHANNELS)):
        base, pinv, full, inverse = comparison.scan_matrices(tuple(u),tuple(map(float,frequencies)),betas[ci],origin)
        baseline = np.sum((y[:,ci]-base@(pinv@y[:,ci]))**2)
        if baseline<=1e-20 or not np.isfinite(baseline):
            raise ValueError('invalid baseline')
        prediction=np.einsum('tmk,tk->tm',full,np.einsum('tkm,m->tk',inverse,y[:,ci]))
        gains.append((baseline-np.sum((y[None,:,ci]-prediction)**2,axis=1))/baseline)
    gains=np.asarray(gains).T
    return {'gains':gains,'joint':np.min(gains[:,core.PRIMARY],axis=1),
            'span':float(u[-1]-u[0]),'support_max':float(support[prefix][-1]),'boundary':float(boundary)}


def nominations(frequencies,scores):
    selected=[]
    for i in np.argsort(-scores,kind='stable'):
        if all(abs(float(frequencies[i])-float(frequencies[j]))>=.5 for j in selected):
            selected.append(int(i))
            if len(selected)==3:
                break
    return selected


def heldout(cells,t,betas,origin):
    minimum={name:float('inf') for name in core.CHANNELS}
    for cell in cells:
        end=cell.cut if cell.train_end is None else cell.train_end
        for ci,name in enumerate(core.CHANNELS):
            value=fit(cell.u,cell.y[:,ci],end,cell.cut,t,betas[ci],origin)
            if value['status']!='VALID':
                raise ValueError('invalid prediction')
            minimum[name]=min(minimum[name],value['gain'])
    joint=min(minimum[core.CHANNELS[i]] for i in core.PRIMARY)
    return {'minimum_gains':minimum,'joint_score':joint,'positive_all_primary_cells':joint>0}


def run(outdir,smoke=False):
    outdir=Path(outdir).resolve(); outdir.mkdir(parents=True,exist_ok=True)
    cfg={'scales':[30000,100000] if not smoke else [5000,10000], 'grids':[[192,0.],[256,.08]],
         'splits':[.55,.75],'theta':.525,'x_min':100,'frequencies':[18.,27.],
         'amplitudes':[.1,.3],'phase_seeds':[10,11,12,13] if not smoke else [10],
         'steps':[.25,.025],'models':comparison.MODELS,'views':['full','paired_difference'],
         'scan_bounds':[4.,40.],'known_margin':.35,'top_k':3,'separation':.5,
         'recovery_tolerances':[.25,.05],
         'purpose':'paired localization diagnostic; no controls or discovery claims',
         'paired_reference':'exact unit-weight model; diagnostic oracle unavailable for unknown arithmetic signal'}
    manifest=batch.manifest_for(cfg)
    for name in (Path(__file__).name,'euler_coupled_batch_py3.py','euler_envelope_comparison_py3.py','euler_transfer_diagnostics_py3.py'):
        manifest['source_sha256'][name]=hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
    manifest.pop('run_id'); manifest['run_id']=batch.fingerprint(manifest)
    with batch.run_lock(outdir):
        batch.check_manifest(outdir,manifest)
        struct=euler.structure(max(cfg['scales'])); primes=struct[1]
        _,base=euler.coefficients(struct,np.ones(len(primes)))
        reference=core.build_cells(base,cfg['scales'],cfg['grids'],cfg['splits'],cfg['theta'],cfg['x_min'])
        tasks=[(t,a,s) for t in cfg['frequencies'] for a in cfg['amplitudes'] for s in cfg['phase_seeds']]
        results=[]; origin=np.log(cfg['x_min'])
        for t,amp,seed in tasks:
            key=f't{t:g}-a{amp:g}-s{seed}'; path=outdir/f'task-{key}.json'
            row=batch.completed_task(path,manifest['run_id'],key)
            if row is None:
                try:
                    phase=np.random.default_rng(20260916+seed).uniform(-np.pi,np.pi)
                    _,source=euler.coefficients(struct,1+amp*np.cos(t*np.log(primes)+phase))
                    full=core.build_cells(source,cfg['scales'],cfg['grids'],cfg['splits'],cfg['theta'],cfg['x_min'])
                    views={'full':full,'paired_difference':[replace(c,y=c.y-r.y) for c,r in zip(full,reference)]}
                    records=[]
                    for view,cells in views.items():
                        for model,betas in comparison.MODELS.items():
                            fixed=heldout(cells,t,betas,origin)
                            for step in cfg['steps']:
                                frequencies=np.round(np.arange(4.,40.+step/2,step),8)
                                frequencies=frequencies[~known_mask(frequencies,cfg['known_margin'])]
                                scan=training_scan(cells,frequencies,betas,origin)
                                target=int(np.flatnonzero(np.isclose(frequencies,t,atol=1e-9))[0])
                                selected=nominations(frequencies,scan['joint'])
                                chosen=[{'t':float(frequencies[i]),'training_score':float(scan['joint'][i]),
                                    **heldout(cells,float(frequencies[i]),betas,origin)} for i in selected]
                                distance=min(abs(r['t']-t) for r in chosen)
                                records.append({'view':view,'model':model,'step':step,'selected':chosen,
                                    'nearest_nomination_error':distance,'near_025':distance<=.25+1e-9,'near_005':distance<=.05+1e-9,
                                    'any_positive':any(r['positive_all_primary_cells'] for r in chosen),
                                    'fixed_target_diagnostic':fixed,'training_only_target_rank':1+int(np.count_nonzero(scan['joint']>scan['joint'][target])),
                                    'training_gain_at_target':dict(zip(core.CHANNELS,map(float,scan['gains'][target]))),
                                    'training_peak_t_by_channel':{ch:float(frequencies[np.argmax(scan['gains'][:,i])]) for i,ch in enumerate(core.CHANNELS)},
                                    'training_span':scan['span'],'span_scale_2pi_over_L':float(2*np.pi/scan['span']),
                                    'selection_support_max':scan['support_max'],'earliest_holdout':scan['boundary']})
                    row={'status':'COMPLETED','design':[t,amp,seed],'records':records}
                    json.dumps(row,allow_nan=False)
                except Exception as exc:
                    traceback.print_exc(); row={'status':'FAILED','error':repr(exc)}
                row.update(task_id=key,run_id=manifest['run_id']); comparison.atomic(path,row)
            results.append(row)
            comparison.atomic(outdir/'progress.json',{'status':'RUNNING','completed_count':sum(r['status']=='COMPLETED' for r in results),
                'failed_count':sum(r['status']=='FAILED' for r in results),'total_tasks':len(tasks),'last_task':key,'updated':batch.now()})
        aggregate=[]
        for view in cfg['views']:
            for model in comparison.MODELS:
                for step in cfg['steps']:
                    rows=[r for task in results if task['status']=='COMPLETED' for r in task['records'] if (r['view'],r['model'],r['step'])==(view,model,step)]
                    aggregate.append({'view':view,'model':model,'step':step,'designs':len(rows),
                        'near_025':sum(r['near_025'] for r in rows),'near_005':sum(r['near_005'] for r in rows),
                        'any_positive':sum(r['any_positive'] for r in rows),
                        'fixed_target_positive':sum(r['fixed_target_diagnostic']['positive_all_primary_cells'] for r in rows),
                        'median_frequency_error':float(np.median([r['nearest_nomination_error'] for r in rows])) if rows else None,
                        'median_target_training_gains':{ch:float(np.median([r['training_gain_at_target'][ch] for r in rows])) if rows else None for ch in core.CHANNELS}})
        failed=sum(r['status']=='FAILED' for r in results)
        summary={'status':'COMPLETED_WITH_FAILURES' if failed else 'COMPLETED','run_id':manifest['run_id'],'configuration':cfg,
            'completed_count':len(results)-failed,'failed_count':failed,'total_tasks':len(tasks),'aggregate':aggregate,
            'candidate_count':None,'gate_status':'DIAGNOSTIC_ONLY',
            'interpretation':'Fine grid adds sampling density, not new arithmetic information. Paired differences require a known model reference. Fixed-target results are oracle diagnostics, never used for training nomination. No surrogate significance or zeta/Arb claim.'}
        comparison.atomic(outdir/'summary.json',summary)
        comparison.atomic(outdir/'progress.json',{k:summary[k] for k in ('status','completed_count','failed_count','total_tasks')})
        lines=['# Euler localization diagnostic','',summary['interpretation'],'',
            '| view | model | step | within .25 | within .05 | any all-positive nomination | fixed target all-positive | median error |','|---|---|---|---|---|---|---|---|']
        lines += [f"| {r['view']} | {r['model']} | {r['step']} | {r['near_025']}/{r['designs']} | {r['near_005']}/{r['designs']} | {r['any_positive']}/{r['designs']} | {r['fixed_target_positive']}/{r['designs']} | {r['median_frequency_error']} |" for r in aggregate]
        (outdir/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        return summary


if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--output-dir',type=Path,required=True); ap.add_argument('--smoke',action='store_true')
    args=ap.parse_args(); result=run(args.output_dir,args.smoke)
    print(json.dumps({k:result[k] for k in ('status','completed_count','failed_count')}))
    raise SystemExit(bool(result['failed_count']))
