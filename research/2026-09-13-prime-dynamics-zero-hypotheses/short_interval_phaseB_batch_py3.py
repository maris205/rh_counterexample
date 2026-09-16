"""Phase B descriptive controls; joint unknown-frequency screening is separate."""
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
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import short_interval_dynamics as sid
import density_preserving_short_controls as dpsc


def atomic(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def load_json(path):
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else None
    except (OSError, ValueError):
        return None


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def source_hashes():
    names = ('short_interval_phaseB_batch_py3.py', 'short_interval_dynamics.py',
             'density_preserving_short_controls.py', 'known_ordinates.py')
    return {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in names}


def prepare_manifest(outdir, config):
    """Reject stale configuration before overwriting an existing manifest."""
    manifest = {'schema': 'phaseB-manifest-v2', 'configuration': config, 'sources': source_hashes()}
    manifest['sha256'] = fingerprint(manifest)
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


def gap_preserving_indicator(indicator, block, rng):
    primes = np.flatnonzero(indicator).astype(np.int64)
    out = np.zeros_like(indicator)
    if len(primes) < 4:
        return indicator.copy()
    gaps = np.diff(primes).astype(np.int64)
    for start in range(0, len(gaps), block):
        rng.shuffle(gaps[start:min(len(gaps), start + block)])
    rebuilt = np.r_[primes[0], primes[0] + np.cumsum(gaps)]
    out[rebuilt] = 1
    return out


def metric_summary(observed, samples):
    vals = np.asarray([v for v in samples if v is not None and np.isfinite(v)], dtype=float)
    if observed is None or not np.isfinite(observed) or len(vals) == 0:
        return {'status': 'INCOMPLETE', 'observed': observed, 'replicates': len(vals),
                'mean': None, 'q95': None, 'difference_from_mean': None,
                'empirical_rank_p': None, 'minimum_rank_p': None}
    return {'status': 'DESCRIPTIVE', 'observed': float(observed), 'replicates': len(vals),
            'mean': float(np.mean(vals)), 'q95': float(np.quantile(vals, .95)),
            'difference_from_mean': float(observed - np.mean(vals)),
            'empirical_rank_p': (1 + int(np.count_nonzero(vals >= observed))) / (len(vals) + 1),
            'minimum_rank_p': 1 / (len(vals) + 1),
            'scan_adjusted': False, 'significance_claim': False}


def compare_controls(channels, controls):
    rows = []
    for channel in ('short_power_error', 'short_fixed_log_error', 'gap_residual'):
        for metric in ('known_critical_line', 'known_critical_line_increment'):
            for target, cuts in channels[channel][metric].items():
                for cut, observed in cuts.items():
                    for segment in ('train_projection', 'holdout_projection'):
                        for label, reps in controls.items():
                            vals = [r[channel][metric][target][cut][segment]['r2'] for r in reps]
                            rows.append({'channel': channel, 'metric': metric, 't': float(target),
                                         'cut': float(cut), 'segment': segment, 'control': label,
                                         **metric_summary(observed[segment]['r2'], vals)})
    return rows


def run_one(n, theta, samples, reps, blocks, splits, seed, out=None,
            grids=None, density_bins=64):
    grids = grids or [(samples, 0.0), (samples, .08)]
    indicator, _ = sid.prime_indicator_linear_sieve(n)
    designs = [(count, trim, *sid.grid(n, count, trim)) for count, trim in grids]
    rows = [{'samples': count, 'trim': trim, 'actual_samples': len(xs),
             'channels': sid.channels_for_indicator(indicator, xs, u, theta, .5, splits),
             'controls': {}} for count, trim, xs, u in designs]
    modes = [('global_shuffle', None)] + [(f'block_shuffle_{b}', b) for b in blocks]
    modes += [('density_preserving', None), ('gap_preserving_shuffle', None)]
    for mode, block in modes:
        for row in rows:
            row['controls'][mode] = []
        for rep in range(reps):
            token = f'{seed}:{mode}:{rep}'.encode()
            rng = np.random.default_rng(int.from_bytes(hashlib.sha256(token).digest()[:8], 'big'))
            if mode == 'density_preserving':
                surrogate = dpsc.density_surrogate(indicator, density_bins, rng)
            elif mode == 'gap_preserving_shuffle':
                surrogate = gap_preserving_indicator(indicator, max(64, min(blocks)), rng)
            else:
                surrogate = sid.shuffled_indicator(indicator, rng, block)
            # Reuse this same prime source across channels AND grids.
            for row, (_, _, xs, u) in zip(rows, designs):
                row['controls'][mode].append({'rep': rep, **sid.channels_for_indicator(
                    surrogate, xs, u, theta, .5, splits)})
    for row in rows:
        row['control_metric_summary'] = compare_controls(row['channels'], row['controls'])
    result = {'schema': 'phaseB-controls-v2', 'status': 'COMPLETED',
              'batch_task': 'short_interval_phaseB', 'batch_scale_n': n, 'batch_theta': theta,
              'configuration': {'n': n, 'theta': theta, 'grids': grids, 'reps': reps,
                                'blocks': list(blocks), 'splits': list(splits),
                                'seed': seed, 'density_bins': density_bins},
              'grids': rows, 'channels': rows[0]['channels'], 'controls': rows[0]['controls'],
              'candidate_gate_status': 'NOT_EVALUATED', 'screen_candidate_count': None,
              'eligible_candidate_count': None, 'candidates': None,
              'metric_interpretation': 'Known-line fixed-frequency projections refit on each segment. These are descriptive effect sizes, not frozen predictions or scan-adjusted tests.',
              'missing_gates': ['joint unknown-frequency training selection', 'frozen holdout prediction',
                                'three observable families', 'joint scan max-statistic controls'],
              'source_hashes': source_hashes()}
    if out is not None:
        atomic(out, result)
    return result


def run_batch(outdir, config):
    manifest_hash = prepare_manifest(outdir, config)
    artifacts, completed, failed = [], [], []
    for n in config['scales']:
        for theta in config['thetas']:
            key = f'n{n}-theta{theta:g}'
            path = outdir / (key + '.json')
            obj = resumable(path, manifest_hash, key)
            if obj is None:
                try:
                    obj = run_one(n, theta, config['samples'], config['control_reps'],
                                  tuple(config['blocks']), tuple(config['splits']),
                                  config['seed'] + n + int(theta * 1000),
                                  grids=config['grids'], density_bins=config['density_bins'])
                    if obj.get('status') != 'COMPLETED':
                        raise ValueError('Task returned a non-completed artifact')
                    obj.update(manifest_sha256=manifest_hash, task_key=key)
                    atomic(path, obj)
                except Exception as exc:
                    obj = {'status': 'FAILED', 'error': repr(exc), 'task_key': key,
                           'manifest_sha256': manifest_hash, 'batch_scale_n': n, 'batch_theta': theta}
                    atomic(path, obj)
            if obj['status'] == 'COMPLETED':
                completed.append(key)
            else:
                failed.append(key)
            artifacts.append({'key': key, 'artifact': str(path), 'status': obj['status']})
            atomic(outdir / 'progress.json', {'status': 'RUNNING', 'completed': completed,
                   'failed': failed, 'last_task': key, 'updated': time.time(), 'manifest_sha256': manifest_hash})
    summary = {'schema': 'phaseB-summary-v2', 'status': 'COMPLETED' if not failed else 'COMPLETED_WITH_FAILURES',
               'purpose': 'Descriptive short-interval and gap control comparison',
               'configuration': config, 'manifest_sha256': manifest_hash,
               'completed_artifacts': len(completed), 'failed_artifacts': len(failed),
               'candidate_gate_status': 'NOT_EVALUATED', 'screen_candidate_count': None,
               'eligible_candidate_count': None, 'candidates': None, 'artifacts': artifacts,
               'interpretation': 'Density and gap controls were executed per grid. Unknown-frequency joint candidate gates were not evaluated; null counts are not a zero-candidate result.'}
    atomic(outdir / 'summary.json', summary)
    (outdir / 'report.md').write_text(
        f"# Phase B controls V2\n\nExecution: {summary['status']}\n\n"
        f"Completed artifacts: {len(completed)}; failed artifacts: {len(failed)}.\n\n"
        'Joint candidate screen: **NOT_EVALUATED**; candidate counts: null.\n\n'
        'Per-grid, per-cut known-frequency effects and empirical quantiles are descriptive; '
        'the holdout projection refits coefficients and is not frozen prediction.\n', encoding='utf-8')
    atomic(outdir / 'progress.json', {'status': summary['status'], 'completed': completed, 'failed': failed,
           'last_task': 'summary', 'manifest_sha256': manifest_hash, 'updated': time.time()})
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output-dir', type=Path, required=True)
    ap.add_argument('--scales', default='1000000,5000000')
    ap.add_argument('--thetas', default='0.50,0.525,0.60')
    ap.add_argument('--samples', type=int, default=2048)
    ap.add_argument('--grids', default=None, help='samples:trim pairs; default uses samples at trims 0 and .08')
    ap.add_argument('--control-reps', type=int, default=4)
    ap.add_argument('--blocks', default='100000,1000000')
    ap.add_argument('--splits', default='0.55,0.67,0.80')
    ap.add_argument('--density-bins', type=int, default=64)
    ap.add_argument('--seed', type=int, default=20260915)
    ap.add_argument('--smoke', action='store_true')
    args = ap.parse_args()
    scales = [int(x) for x in args.scales.split(',')]
    thetas = [float(x) for x in args.thetas.split(',')]
    if args.smoke:
        scales, thetas, args.samples, args.control_reps = [50000], [.525], 256, 1
    grids = [[int(a), float(b)] for a, b in (x.split(':') for x in args.grids.split(','))] if args.grids else [[args.samples, 0.0], [args.samples, .08]]
    config = {'scales': scales, 'thetas': thetas, 'samples': args.samples, 'grids': grids,
              'control_reps': args.control_reps, 'blocks': [int(x) for x in args.blocks.split(',')],
              'splits': [float(x) for x in args.splits.split(',')], 'density_bins': args.density_bins,
              'seed': args.seed, 'python': sys.version, 'platform': platform.platform(), 'numpy': np.__version__,
              'profile': 'smoke' if args.smoke else 'descriptive'}
    if (min(scales) < 100 or args.control_reps < 0 or args.density_bins < 1
            or not config['blocks'] or min(config['blocks']) < 1
            or not all(0 < s < 1 for s in config['splits'])):
        ap.error('Invalid scales, controls, bins, blocks, or splits')
    result = run_batch(args.output_dir.resolve(), config)
    print(json.dumps({k: result[k] for k in ('status', 'completed_artifacts', 'failed_artifacts', 'candidate_gate_status')}))
    if result['failed_artifacts']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
