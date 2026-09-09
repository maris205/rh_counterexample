"""Portable bounded pipeline. Child process groups are owned by this run only."""
import os
import signal
import subprocess
import sys
import time
import traceback
from wide_common import HERE, read, save, sha, utc, inputs, lock


def terminate(child):
    if os.name == 'nt':
        if child.poll() is None:
            subprocess.run(['taskkill', '/PID', str(child.pid), '/T', '/F'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
    else:
        # start_new_session gives each stage its own group, including spawned workers.
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if child.poll() is None:
        child.wait(timeout=15)


def interrupted(signum, frame):
    raise InterruptedError('Process interrupted; run the same directory to resume')


def run():
    with lock('pipeline.lock'):
        if '--resume' in sys.argv:
            for marker in (HERE / 'STOP_AFTER_CURRENT', HERE / 'true_zeta/STOP_AFTER_CURRENT'):
                marker.unlink(missing_ok=True)
        _, digest = inputs(create=True)
        plan = read(HERE / 'WIDE_PLAN.json')
        state = {'status': 'RUNNING', 'phase': 'STARTING', 'pid': os.getpid(),
                 'started_utc': utc(), 'frozen_inputs_sha256': digest, 'stages': []}
        save(HERE / 'PIPELINE_STATUS.json', state)
        active = None
        started = time.perf_counter()
        old_handler = signal.signal(signal.SIGTERM, interrupted)

        def stage(name, script, limit):
            nonlocal active
            state['phase'] = name
            stamp = str(time.time_ns())
            record = {'name': name, 'started_utc': utc(), 'script': script,
                      'stdout': f'{name.lower()}-{stamp}.stdout.log',
                      'stderr': f'{name.lower()}-{stamp}.stderr.log'}
            state['stages'].append(record)
            options = {'creationflags': subprocess.CREATE_NO_WINDOW} if os.name == 'nt' else {'start_new_session': True}
            with (HERE / record['stdout']).open('w', encoding='utf-8') as out, (HERE / record['stderr']).open('w', encoding='utf-8') as err:
                print('STAGE', name, flush=True)
                active = subprocess.Popen([sys.executable, '-X', 'utf8', str(HERE / script)],
                                          cwd=HERE, stdout=out, stderr=err,
                                          stdin=subprocess.DEVNULL, **options)
                record['pid'] = active.pid
                before = time.perf_counter()
                while active.poll() is None:
                    if name == 'TRUE_ZETA' and (HERE / 'STOP_AFTER_CURRENT').exists():
                        (HERE / 'true_zeta/STOP_AFTER_CURRENT').touch(exist_ok=True)
                    if time.perf_counter() - before > limit:
                        raise TimeoutError(name + ' exceeded its session limit')
                    record['elapsed_seconds'] = time.perf_counter() - before
                    state.update(updated_utc=utc(), elapsed_seconds=time.perf_counter() - started)
                    save(HERE / 'PIPELINE_STATUS.json', state)
                    time.sleep(1)
                record.update(exit_code=active.returncode, finished_utc=utc())
                if active.returncode:
                    raise RuntimeError(name + ' failed; see ' + record['stderr'])
                active = None

        try:
            if (HERE / 'STOP_AFTER_CURRENT').exists():
                state['status'] = 'PAUSED'
                return
            stage('PREFLIGHT', 'verify_wide.py', 300)
            stage('SYMBOL_SURVEY', 'wide_scan.py', plan['gpu_session_seconds'] + 120)
            if read(HERE / 'GPU_STATUS.json')['status'] != 'COMPLETE':
                state['status'] = 'PAUSED_SURVEY'
                return
            stage('PREPARE', 'prepare_target.py', max(300, plan['maximum_windows'] * 2))
            stage('TRUE_ZETA', 'wide_target.py', plan['cpu']['session_seconds'] + 120)
            final = read(HERE / 'true_zeta/JOB_STATUS.json')
            state.update(status=final['status'], phase='FINISHED',
                         results_sha256=sha(HERE / 'true_zeta/RESULTS.json'),
                         target_summary={k: final.get(k) for k in ('status', 'status_counts', 'pending_windows')})
        except BaseException as exc:
            state.update(status='ERROR', error=str(exc), traceback=traceback.format_exc())
            raise
        finally:
            if active is not None:
                terminate(active)
            signal.signal(signal.SIGTERM, old_handler)
            state.update(updated_utc=utc(), finished_utc=utc(), elapsed_seconds=time.perf_counter() - started)
            save(HERE / 'PIPELINE_STATUS.json', state)
        print('PIPELINE_FINISHED', state['status'], flush=True)
        if state['status'] == 'FINISHED_WITH_ERRORS':
            raise SystemExit(2)


if __name__ == '__main__':
    run()
