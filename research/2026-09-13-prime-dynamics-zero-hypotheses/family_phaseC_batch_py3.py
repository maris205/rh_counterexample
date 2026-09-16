"""Phase C family diagnostics; joint candidate screening is not implemented here."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path
import numpy as np
import mpmath
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import family_control_panel as fcp
import family_detector_transfer as fdt


def atomic(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def load_json(path):
    try:
        obj = json.loads(path.read_text(encoding='utf-8'))
        return obj if isinstance(obj, dict) else None
    except (OSError, ValueError):
        return None


def source_hashes():
    return {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
            for name in ('family_phaseC_batch_py3.py', 'family_control_panel.py', 'family_detector_transfer.py')}


def prepare_manifest(outdir, config):
    manifest = {'schema': 'phaseC-manifest-v2', 'configuration': config, 'sources': source_hashes()}
    manifest['sha256'] = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    old = load_json(outdir / 'manifest.json')
    if old is not None and old != manifest:
        raise ValueError('Resume configuration/source mismatch; use a new output directory.')
    if old is None and outdir.exists() and any(outdir.iterdir()):
        raise ValueError('Existing output has no valid V2 manifest; use a new output directory.')
    atomic(outdir / 'manifest.json', manifest)
    atomic(outdir / 'config.json', config)
    return manifest['sha256']


def resumable(path, manifest_hash, task_key):
    obj = load_json(path)
    if (obj is not None and obj.get('status') == 'COMPLETED'
            and obj.get('manifest_sha256') == manifest_hash and obj.get('task_key') == task_key):
        return obj
    return None


def detector(family, n, samples, reps, splits, seed):
    spec = fdt.FAMILIES[family]
    sigma, target, period = float(spec['target']['sigma']), float(spec['target']['t']), list(spec['period'])
    a = fdt.coefficient_array(period, n, False)
    u, idx = fdt.log_grid(n, samples)
    signal = fdt.run_one(a, u, idx, sigma, target, splits, 8)
    controls = {'global_shuffle': [], 'block_shuffle': []}
    for rep in range(reps):
        for mode in controls:
            rng = np.random.default_rng(seed + 1009 * (rep + 1) + (1 if mode == 'global_shuffle' else 2))
            shuffled = fdt.shuffled(a, rng, 'global' if mode == 'global_shuffle' else 'block', 5000)
            controls[mode].append(fdt.run_one(shuffled, u, idx, sigma, target, splits, 8))
    effects = []
    for cut, observed in signal['fixed_target'].items():
        for mode, rows in controls.items():
            vals = np.asarray([r['fixed_target'][cut]['r2'] for r in rows
                               if r['fixed_target'][cut]['r2'] is not None], dtype=float)
            vals = vals[np.isfinite(vals)]
            value = observed['r2']
            valid = value is not None and np.isfinite(value) and len(vals) > 0
            effects.append({'cut': float(cut), 'control': mode, 'observed_r2': value,
                            'replicates': len(vals), 'mean': float(np.mean(vals)) if valid else None,
                            'q95': float(np.quantile(vals, .95)) if valid else None,
                            'difference_from_mean': float(value - np.mean(vals)) if valid else None,
                            'empirical_rank_p': (1 + int(np.count_nonzero(vals >= value))) / (len(vals) + 1) if valid else None,
                            'minimum_rank_p': 1 / (len(vals) + 1) if len(vals) else None,
                            'scan_adjusted': False, 'significance_claim': False})
    return {'schema': 'family-detector-transfer-v2', 'status': 'COMPLETED',
            'purpose': 'Descriptive family detector sensitivity; no zeta zero inference',
            'configuration': {'family': family, 'description': spec['description'], 'period': period,
                              'n': n, 'samples': samples, 'sigma': sigma, 'target_t': target,
                              'splits': splits, 'control_reps': reps, 'seed': seed},
            'signal': signal, 'controls': controls, 'control_metric_summary': effects,
            'target_role': 'reported numerical off-line DH fixture' if family == 'dh' else 'fixed probe borrowed from zeta; not asserted to be a zero of this character L-function',
            'metric_interpretation': 'Target regression predicts later samples but its input was detrended and scaled on the full window. This legacy metric is descriptive, not leakage-free validation.',
            'candidate_gate_status': 'NOT_EVALUATED', 'screen_candidate_count': None,
            'eligible_candidate_count': None, 'candidates': None,
            'missing_gates': ['training-only preprocessing', 'joint unknown-frequency candidate selection',
                              'family-specific zero target calibration', 'complete common-spectrum controls']}


def run_batch(outdir, config):
    manifest_hash = prepare_manifest(outdir, config)
    artifacts, completed, failed = [], [], []
    for task in config['tasks']:
        key = f"n{config['n']}-{task}"
        path = outdir / (key + '.json')
        obj = resumable(path, manifest_hash, key)
        if obj is None:
            try:
                if task == 'panel':
                    obj = fcp.build_report(80)
                    obj['status'] = 'COMPLETED'
                    obj['candidate_gate_status'] = 'NOT_EVALUATED'
                    obj['screen_candidate_count'] = None
                    obj['eligible_candidate_count'] = None
                else:
                    obj = detector(task, config['n'], config['samples'], config['control_reps'],
                                   config['splits'], config['seed'] + config['n'] + len(task))
                if obj.get('status') != 'COMPLETED':
                    raise ValueError('Task returned a non-completed artifact')
                obj.update(batch_task=task, source_hashes=source_hashes(), task_key=key,
                           manifest_sha256=manifest_hash)
                atomic(path, obj)
            except Exception as exc:
                obj = {'status': 'FAILED', 'batch_task': task, 'error': repr(exc),
                       'task_key': key, 'manifest_sha256': manifest_hash}
                atomic(path, obj)
        if obj['status'] == 'COMPLETED':
            completed.append(key)
        else:
            failed.append(key)
        artifacts.append({'key': key, 'artifact': str(path), 'status': obj['status']})
        atomic(outdir / 'progress.json', {'status': 'RUNNING', 'completed': completed,
               'failed': failed, 'last_task': key, 'updated': time.time(), 'manifest_sha256': manifest_hash})
    summary = {'schema': 'phaseC-summary-v2', 'status': 'COMPLETED' if not failed else 'COMPLETED_WITH_FAILURES',
               'purpose': 'Family fixture and descriptive detector comparison', 'configuration': config,
               'manifest_sha256': manifest_hash, 'completed_artifacts': len(completed),
               'failed_artifacts': len(failed), 'candidate_gate_status': 'NOT_EVALUATED',
               'screen_candidate_count': None, 'eligible_candidate_count': None, 'candidates': None,
               'family_coverage': {'chi4': 'FIXED_PROBE_ONLY', 'chi5': 'FIXED_PROBE_ONLY',
                                   'dh': 'UNCERTIFIED_SENSITIVITY_FIXTURE',
                                   'finite_field': 'EXACT_STRUCTURAL_FIXTURE_ONLY',
                                   'zeta': 'NOT_RUN_IN_THIS_BATCH', 'k3': 'NOT_IMPLEMENTED', 'k5': 'NOT_IMPLEMENTED'},
               'interpretation': 'Executed fixtures are not the full family hierarchy gate. No joint unknown-frequency candidate test was run; null counts are not measured zeroes.',
               'artifacts': artifacts}
    atomic(outdir / 'summary.json', summary)
    (outdir / 'report.md').write_text(
        f"# Phase C family diagnostics V2\n\nExecution: {summary['status']}\n\n"
        f"Completed artifacts: {len(completed)}; failed artifacts: {len(failed)}.\n\n"
        'Joint candidate screen: **NOT_EVALUATED**; counts: null.\n\n'
        'The finite-field panel is a structural fixture; DH is an uncertified numerical sensitivity fixture. '
        'chi4/chi5 fixed probes are not asserted family zeroes. k3/k5 detector transfer is not implemented.\n', encoding='utf-8')
    atomic(outdir / 'progress.json', {'status': summary['status'], 'completed': completed,
           'failed': failed, 'last_task': 'summary', 'updated': time.time(), 'manifest_sha256': manifest_hash})
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output-dir', type=Path, required=True)
    ap.add_argument('--n', type=int, default=200000)
    ap.add_argument('--samples', type=int, default=2048)
    ap.add_argument('--control-reps', type=int, default=3)
    ap.add_argument('--splits', default='0.55,0.67,0.80')
    ap.add_argument('--seed', type=int, default=20260915)
    ap.add_argument('--smoke', action='store_true')
    args = ap.parse_args()
    if args.smoke:
        args.n, args.samples, args.control_reps = 20000, 256, 1
    splits = [float(x) for x in args.splits.split(',')]
    if args.n < 100 or args.samples < 64 or args.control_reps < 0 or not all(0 < s < 1 for s in splits):
        ap.error('Invalid n, samples, controls, or splits')
    config = {'n': args.n, 'samples': args.samples, 'control_reps': args.control_reps,
              'splits': splits, 'seed': args.seed, 'python': sys.version,
              'platform': platform.platform(), 'numpy': np.__version__, 'mpmath': mpmath.__version__,
              'tasks': ['panel', 'dh', 'chi4', 'chi5'], 'profile': 'smoke' if args.smoke else 'descriptive'}
    result = run_batch(args.output_dir.resolve(), config)
    print(json.dumps({k: result[k] for k in ('status', 'completed_artifacts', 'failed_artifacts', 'candidate_gate_status')}))
    if result['failed_artifacts']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
