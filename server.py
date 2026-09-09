"""Create isolated experiments, run/resume, inspect progress and request a pause."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
from importlib.metadata import version, PackageNotFoundError
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
SURVEY = Path('research/2026-09-09-gpu-wide-survey')
PACKAGES = ('numpy', 'scipy', 'mpmath', 'python-flint')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def versions(backend):
    packages = PACKAGES + (('cupy-cuda12x',) if backend == 'gpu' else ())
    return {p: version(p) for p in packages}


def config(args):
    plan = read(ROOT / SURVEY / 'WIDE_PLAN.json')
    smoke = args.profile == 'smoke'
    plan.update(backend=args.backend,
                anchors=args.anchors or (['4096'] if smoke else plan['anchors']),
                regions_per_anchor=args.regions_per_anchor if args.regions_per_anchor is not None else (2 if smoke else 256),
                strata_per_anchor=args.strata if args.strata is not None else (1 if smoke else 4),
                first_offset=args.first_offset if args.first_offset is not None else (4096 if smoke else 2097152),
                gpu_session_seconds=args.screen_seconds,
                sigma_bounds=[args.sigma_min, args.sigma_max])
    plan.pop('prior_cpu_job', None)
    plan.pop('dependency_wait_seconds', None)
    plan['maximum_windows'] = len(plan['anchors']) * plan['strata_per_anchor'] * 8
    plan['selection'] = 'One smallest oriented grid-merit bracket per anchor/stratum/k/rule/source; ties by base and grid index; no zeta scores used.'
    workers = args.workers if args.workers is not None else (2 if smoke else min(28, max(1, (os.cpu_count() or 1) - 2)))
    maxiter = args.maxiter if args.maxiter is not None else (1 if smoke else 15)
    plan['cpu'].update(workers=workers, de_maxiter=maxiter, de_popsize=args.popsize,
                       maximum_evaluations_per_window=(maxiter + 1) * args.popsize * 2,
                       per_window_seconds=args.window_seconds, session_seconds=args.session_seconds)
    if sys.version_info < (3, 11):
        raise ValueError('Python 3.11 or newer is required')
    if workers < 1 or maxiter < 1 or args.popsize < 5:
        raise ValueError('workers >= 1, maxiter >= 1 and popsize >= 5 required')
    if plan['regions_per_anchor'] < 1 or not 1 <= plan['strata_per_anchor'] <= plan['regions_per_anchor']:
        raise ValueError('Need 1 <= strata <= regions-per-anchor')
    if plan['regions_per_anchor'] % plan['strata_per_anchor']:
        raise ValueError('regions-per-anchor must be divisible by strata')
    if not Fraction('0.5') < Fraction(args.sigma_min) < Fraction(args.sigma_max) < 1:
        raise ValueError('Need 0.5 < sigma-min < sigma-max < 1')
    if min(args.window_seconds, args.screen_seconds, args.session_seconds) <= 0:
        raise ValueError('Time limits must be positive')
    if plan['first_offset'] < 0 or any(int(a) <= 0 or str(int(a)) != a for a in plan['anchors']):
        raise ValueError('Anchors must be positive integer strings; first-offset must be nonnegative')
    # Avoid overlapping blocks across anchors as well as inside a band.
    starts = sorted(int(a) + plan['first_offset'] + j * plan['stride']
                    for a in plan['anchors'] for j in range(plan['regions_per_anchor']))
    if any(b < a + plan['block_width'] for a, b in zip(starts, starts[1:])):
        raise ValueError('Requested blocks overlap; choose distinct anchors/offsets')
    return plan


def init(args):
    plan = config(args)
    runtime = versions(plan['backend'])
    directory = args.directory.resolve()
    if directory.exists():
        raise ValueError('Run directory already exists; use run/resume or choose a new name')
    directory.mkdir(parents=True)
    # Snapshot only tracked templates. No local results, dependencies or PID records.
    files = sorted(p for p in (ROOT / 'research').rglob('*')
                   if p.is_file() and p.suffix in ('.py', '.json', '.md')
                   and '.deps' not in p.parts and '__pycache__' not in p.parts)
    for source in files:
        target = directory / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    write(directory / SURVEY / 'WIDE_PLAN.json', plan)
    snapshot = {p.relative_to(ROOT).as_posix(): sha(directory / p.relative_to(ROOT)) for p in files}
    write(directory / 'RUN.json', {'schema': 1, 'created_utc': datetime.now(timezone.utc).isoformat(),
                                 'profile': args.profile, 'config': plan, 'source_sha256': snapshot,
                                 'packages': runtime, 'python_minor': list(sys.version_info[:2]),
                                 'launcher_sha256': sha(__file__)})
    print(json.dumps({'run': str(directory), 'backend': plan['backend'], 'workers': plan['cpu']['workers'],
                      'regions': len(plan['anchors']) * plan['regions_per_anchor'],
                      'maximum_windows': plan['maximum_windows'],
                      'max_DE_evaluations_per_window': plan['cpu']['maximum_evaluations_per_window']}, indent=2))


def verify(directory):
    receipt = read(directory / 'RUN.json')
    for name, digest in receipt['source_sha256'].items():
        path = (directory / name).resolve()
        if not path.is_relative_to(directory) or sha(path) != digest:
            raise ValueError('Run snapshot changed: ' + name)
    if read(directory / SURVEY / 'WIDE_PLAN.json') != receipt['config']:
        raise ValueError('Saved plan does not match run configuration')
    if versions(receipt['config']['backend']) != receipt['packages'] or list(sys.version_info[:2]) != receipt['python_minor']:
        raise ValueError('Python/dependency versions differ from the saved run; restore its environment or start a new run')
    return receipt


def run(args):
    directory = args.directory.resolve()
    verify(directory)
    script = directory / SURVEY / 'run_pipeline.py'
    return subprocess.call([sys.executable, '-X', 'utf8', str(script)] + (['--resume'] if args.resume else []))


def status(args):
    directory = args.directory.resolve()
    receipt = read(directory / 'RUN.json')
    result = {'run': str(directory), 'backend': receipt['config']['backend'],
              'workers': receipt['config']['cpu']['workers'],
              'note': 'Saved progress. A RUNNING record alone does not prove the process survived a reboot.'}
    for name, relative in [('pipeline', 'PIPELINE_STATUS.json'), ('screen', 'GPU_STATUS.json'),
                           ('zeta', 'true_zeta/JOB_STATUS.json'), ('results', 'true_zeta/RESULTS.json')]:
        path = directory / SURVEY / relative
        if path.exists():
            row = read(path)
            keys = ('status', 'phase', 'pid', 'updated_utc', 'finished_utc', 'elapsed_seconds',
                    'completed_regions', 'total_regions', 'pending_windows', 'status_counts',
                    'active_workers', 'generated_windows', 'completed_objective_evaluations', 'flagged_windows', 'error')
            result[name] = {k: row[k] for k in keys if k in row}
    print(json.dumps(result, ensure_ascii=False, indent=2))


def doctor(args):
    print(json.dumps({'python': sys.version, 'packages': versions(args.backend), 'cpu_count': os.cpu_count()}, indent=2))
    from flint import acb, ctx
    ctx.dps = 50
    value = acb(2).zeta()
    if not value.is_finite() or value.contains(0):
        raise ArithmeticError('Arb zeta smoke check failed')
    print('Arb zeta(2):', value)
    if args.backend == 'gpu':
        sys.path.insert(0, str(ROOT / 'research/2026-09-09-gpu-gap-screen'))
        import gpu_screen
        cp = gpu_screen.cp
        if cp is None:
            raise RuntimeError('CuPy is unavailable')
        print('GPU:', cp.cuda.runtime.getDeviceProperties(0)['name'].decode())
        print('CuPy kernel check:', float(cp.sum(cp.arange(100, dtype=cp.float64)).get()))


def main():
    if not __debug__ or os.environ.get('PYTHONOPTIMIZE'):
        raise SystemExit('Do not use python -O or PYTHONOPTIMIZE; validation assertions must remain enabled')
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('init', help='Create a new immutable experiment snapshot')
    p.add_argument('directory', type=Path)
    p.add_argument('--profile', choices=('server', 'smoke'), default='server')
    p.add_argument('--backend', choices=('cpu', 'gpu'), default='cpu')
    p.add_argument('--workers', type=int)
    p.add_argument('--anchors', nargs='+', help='Exact positive integer heights')
    p.add_argument('--regions-per-anchor', type=int)
    p.add_argument('--strata', type=int)
    p.add_argument('--first-offset', type=int)
    p.add_argument('--sigma-min', default='0.55')
    p.add_argument('--sigma-max', default='0.65')
    p.add_argument('--maxiter', type=int)
    p.add_argument('--popsize', type=int, default=8)
    p.add_argument('--window-seconds', type=int, default=1800)
    p.add_argument('--session-seconds', type=int, default=86400)
    p.add_argument('--screen-seconds', type=int, default=14400)
    p.set_defaults(func=init)
    for name in ('run', 'status', 'stop'):
        p = sub.add_parser(name)
        p.add_argument('directory', type=Path)
        if name == 'run':
            p.add_argument('--resume', action='store_true', help='Clear a requested pause after acquiring the run lock')
        p.set_defaults(func={'run': run, 'status': status, 'stop': stop}[name])
    p = sub.add_parser('doctor')
    p.add_argument('--backend', choices=('cpu', 'gpu'), default='cpu')
    p.set_defaults(func=doctor)
    args = parser.parse_args()
    try:
        return args.func(args)
    except (ValueError, FileNotFoundError, PackageNotFoundError) as exc:
        parser.exit(2, str(exc) + '\n')


def stop(args):
    directory = args.directory.resolve()
    read(directory / 'RUN.json')
    (directory / SURVEY / 'STOP_AFTER_CURRENT').touch(exist_ok=True)
    print('Pause requested: current region/windows will finish first.')


if __name__ == '__main__':
    raise SystemExit(main())
