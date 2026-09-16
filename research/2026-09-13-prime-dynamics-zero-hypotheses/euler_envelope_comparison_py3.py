"""Prospective new-phase comparison of two frozen Euler-model detectors.

Same raw model data and weight permutations for both models. No paired
background subtraction. Each control reselects unknown frequencies; ranks
use the maximum across both model variants and all their nominations.
These remain descriptive toy-model ranks, not an arithmetic discovery test.
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
from euler_transfer_diagnostics_py3 import fit
from known_ordinates import known_mask
import numpy as np

MODELS = {"constant": (0., 0., 0., 0.), "channel_envelopes": (0., .5, .5, .2625)}


def atomic(path, obj):
    # Windows readers can briefly prevent replace; preserve atomic writes
    # while retrying only sharing/access errors for a bounded interval.
    for attempt in range(8):
        try:
            batch.atomic_json(path, obj)
            return
        except PermissionError:
            if attempt == 7:
                raise
            time.sleep(.05 * (attempt + 1))


@lru_cache(maxsize=32)
def scan_matrices(u_tuple, frequencies, beta, origin):
    v = np.asarray(u_tuple) - origin
    base = np.column_stack((np.ones(len(v)), v))
    env = np.exp(beta*v)
    full = np.stack([np.column_stack((base, env*np.cos(t*v), env*np.sin(t*v))) for t in frequencies])
    if np.any(np.linalg.matrix_rank(full) != 4):
        raise ValueError("rank deficient scan design")
    return base, np.linalg.pinv(base), full, np.linalg.pinv(full)


def evaluate(cells, frequencies, betas, origin):
    boundary = min(float(c.u[c.cut]) for c in cells)
    anchor = min(cells, key=lambda c: (c.n, c.grid, c.split))
    support = anchor.u if anchor.support_end_u is None else anchor.support_end_u
    prefix = support < boundary
    u, y = anchor.u[prefix], anchor.y[prefix]
    if len(u) < 16:
        raise ValueError("insufficient common training prefix")
    scores = []
    for ci in core.PRIMARY:
        base, pinv, full, inv = scan_matrices(tuple(u), tuple(map(float, frequencies)), betas[ci], origin)
        baseline_sse = np.sum((y[:,ci]-base@(pinv@y[:,ci]))**2)
        if baseline_sse <= 1e-20 or not np.isfinite(baseline_sse):
            raise ValueError("degenerate training data")
        predictions = np.einsum('tmk,tk->tm', full, np.einsum('tkm,m->tk', inv, y[:,ci]))
        scores.append((baseline_sse-np.sum((y[None,:,ci]-predictions)**2, axis=1))/baseline_sse)
    scores = np.min(scores, axis=0)
    selected = []
    for index in np.argsort(-scores, kind='stable'):
        t = float(frequencies[index])
        if all(abs(t-r['t']) >= .5 for r in selected):
            selected.append({"t": t, "training_score": float(scores[index])})
            if len(selected) == 3:
                break
    for row in selected:
        records, minimum = [], []
        for cell in cells:
            end = cell.cut if cell.train_end is None else cell.train_end
            gains = {}
            for ci, channel in enumerate(core.CHANNELS):
                result = fit(cell.u, cell.y[:,ci], end, cell.cut, row['t'], betas[ci], origin)
                if result['status'] != 'VALID':
                    raise ValueError(f"invalid fit: {cell.key}/{channel}")
                gains[channel] = result['gain']
                if ci in core.PRIMARY:
                    minimum.append(result['gain'])
            records.append({"key": cell.key, "gains": gains})
        row.update(joint_score=float(min(minimum)), positive_all_cells=all(g>0 for g in minimum), cells=records)
    return {"selected": selected, "max_statistic": max(r['joint_score'] for r in selected),
            "selection_support_u_max": float(support[prefix][-1]), "earliest_holdout_u": boundary}


def pooled_max(models):
    return max(m['max_statistic'] for m in models.values())


def run(outdir, smoke=False):
    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    cfg = {"scales": [30000, 100000] if not smoke else [5000, 10000],
           "grids": [[192, 0.], [256, .08]], "splits": [.55, .75], "theta": .525, "x_min": 100,
           "frequencies": [18., 27.], "amplitudes": [.1, .3], "phase_seeds": [6,7,8,9] if not smoke else [6],
           "control_reps": 19 if not smoke else 1, "controls": ['global','log_bin','block'],
           "models": MODELS, "scan": [4.,40.,.25], "known_margin": .35,
           "top_k": 3, "separation": .5, "origin": "log(100)",
           "input_view": "full weighted-model observations; no paired subtraction",
           "ranks": "within-design control max across both models and their selected frequencies",
           "scope": "new-phase toy-model sensitivity; not actual-zeta or independent arithmetic replication"}
    manifest = batch.manifest_for(cfg)
    for name in (Path(__file__).name, 'euler_coupled_batch_py3.py', 'euler_transfer_diagnostics_py3.py'):
        manifest['source_sha256'][name] = hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
    manifest.pop('run_id')
    manifest['run_id'] = batch.fingerprint(manifest)
    designs = [(t,a,s) for t in cfg['frequencies'] for a in cfg['amplitudes'] for s in cfg['phase_seeds']]
    tasks = [('ordinary', None, None, 0)]
    for i, design in enumerate(designs):
        tasks.append((f'design{i}-real', design, None, 0))
        tasks += [(f'design{i}-{mode}-{rep}',design,mode,rep) for mode in cfg['controls'] for rep in range(cfg['control_reps'])]
    with batch.run_lock(outdir):
        batch.check_manifest(outdir, manifest)
        struct = euler.structure(max(cfg['scales']))
        primes = struct[1]
        scan = np.arange(4.,40.125,.25)
        scan = scan[~known_mask(scan,cfg['known_margin'])]
        results = {}
        started = time.monotonic()
        for key, design, mode, rep in tasks:
            path = outdir/f'task-{key}.json'
            row = batch.completed_task(path,manifest['run_id'],key)
            if row is None:
                try:
                    weights = np.ones(len(primes))
                    if design is not None:
                        t, amplitude, seed = design
                        phase = np.random.default_rng(20260916+seed).uniform(-np.pi,np.pi)
                        weights += amplitude*np.cos(t*np.log(primes)+phase)
                    if mode:
                        token = f'{design}:{mode}:{rep}'
                        seed = int.from_bytes(hashlib.sha256(token.encode()).digest()[:8],'big')
                        weights = euler.shuffled_weights(primes,weights,mode,seed)
                    _, source = euler.coefficients(struct,weights)
                    cells = core.build_cells(source,cfg['scales'],cfg['grids'],cfg['splits'],cfg['theta'],cfg['x_min'])
                    models = {name:evaluate(cells,scan,tuple(betas),np.log(cfg['x_min'])) for name,betas in MODELS.items()}
                    row = {'status':'COMPLETED','models':models,'pooled_max_statistic':pooled_max(models),'design':design,'control':mode}
                    json.dumps(row,allow_nan=False)
                except Exception as exc:
                    traceback.print_exc()
                    row = {'status':'FAILED','error':repr(exc)}
                row.update(task_id=key,run_id=manifest['run_id'])
                atomic(path,row)
            results[key] = row
            atomic(outdir/'progress.json',{'status':'RUNNING','completed_count':sum(r['status']=='COMPLETED' for r in results.values()),
                'failed_count':sum(r['status']=='FAILED' for r in results.values()),'total_tasks':len(tasks),'last_task':key,'updated':batch.now()})
        comparisons = []
        for i, design in enumerate(designs):
            real = results[f'design{i}-real']
            if real['status'] != 'COMPLETED':
                continue
            for name, observed in real['models'].items():
                nulls = {mode:[results[f'design{i}-{mode}-{r}']['pooled_max_statistic'] for r in range(cfg['control_reps'])
                    if results[f'design{i}-{mode}-{r}']['status']=='COMPLETED'] for mode in cfg['controls']}
                matched = [r for r in observed['selected'] if abs(r['t']-design[0])<=.25]
                comparisons.append({'design':design,'model':name,'selected_t':[r['t'] for r in observed['selected']],
                    'modulation_selected':bool(matched),'modulation_positive':any(r['positive_all_cells'] for r in matched),
                    'any_positive':any(r['positive_all_cells'] for r in observed['selected']), 'max_statistic':observed['max_statistic'],
                    'controls':{mode:{'completed':len(vals),'pooled_scores':vals,
                        'empirical_rank':core.empirical_p(observed['max_statistic'],vals) if len(vals)==cfg['control_reps'] else None}
                        for mode,vals in nulls.items()}})
        aggregate = {name:{'designs':sum(r['model']==name for r in comparisons),
            'modulation_selected':sum(r['model']==name and r['modulation_selected'] for r in comparisons),
            'modulation_positive':sum(r['model']==name and r['modulation_positive'] for r in comparisons),
            'any_positive':sum(r['model']==name and r['any_positive'] for r in comparisons)} for name in MODELS}
        failed = sum(r['status']=='FAILED' for r in results.values())
        summary = {'status':'COMPLETED_WITH_FAILURES' if failed else 'COMPLETED','run_id':manifest['run_id'],'configuration':cfg,
            'completed_count':len(results)-failed,'failed_count':failed,'total_tasks':len(tasks),'aggregate':aggregate,'comparisons':comparisons,
            'elapsed_s_this_session':time.monotonic()-started,'candidate_count':None,'gate_status':'MODEL_COMPARISON_ONLY',
            'interpretation':'Both models and all nominated frequencies are included in each within-design control maximum. No pooled discovery claim across the 16 model designs. New phases reuse arithmetic scales; fixed model envelopes are not zeta real parts. No paired reference subtraction, actual zeta search or Arb/FLINT certification.'}
        atomic(outdir/'summary.json',summary)
        atomic(outdir/'progress.json',{k:summary[k] for k in ('status','completed_count','failed_count','total_tasks')})
        lines = ['# Frozen channel-envelope model comparison','',summary['interpretation'],'',
            '| model | modulation selected | modulation positive | any positive nomination | designs |','|---|---|---|---|---|']
        lines += [f"| {name} | {r['modulation_selected']} | {r['modulation_positive']} | {r['any_positive']} | {r['designs']} |" for name,r in aggregate.items()]
        (outdir/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
        return summary


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output-dir',type=Path,required=True)
    ap.add_argument('--smoke',action='store_true')
    args = ap.parse_args()
    result = run(args.output_dir,args.smoke)
    print(json.dumps({k:result[k] for k in ('status','completed_count','failed_count','aggregate')}))
    raise SystemExit(bool(result['failed_count']))
