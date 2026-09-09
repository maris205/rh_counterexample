"""Four owned processes; atomic per-window checkpoints and restart-safe resume."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import math
import multiprocessing as multiprocessing
import os
from pathlib import Path
import statistics
import sys
import time
import traceback
from common import HERE, SEARCH, LAB, read, save, sha, utc, verify_frozen, lock

TERMINAL = {'COMPLETED','NEEDS_CHECK','ERROR','TIMEOUT'}


def load_target():
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        os.environ[name]='1'
    sys.path.insert(0,str(SEARCH))
    import zeta_de
    return zeta_de


def point_check(sigma, height, independent):
    zeta = load_target()
    from flint import acb, ctx
    values, rows = [], []
    for dps in (40,80):
        ctx.dps = dps
        val = acb(zeta.ball_rational(sigma),zeta.ball_rational(height)).zeta()
        if not val.is_finite() or val.rel_accuracy_bits()<50:
            raise ArithmeticError('Insufficient accurate finite zeta enclosure')
        values.append(val)
        rows.append({'dps':dps,'enclosure':str(val),'approx_abs_zeta':float(abs(val).mid()),
                     'relative_accuracy_bits':int(val.rel_accuracy_bits()),
                     'contains_zero':bool(val.contains(0))})
    if not values[0].overlaps(values[1]):
        raise ArithmeticError('40/80 digit enclosures disagree')
    result = {'sigma':sigma,'t':height,'rows':rows,'precision_enclosures_overlap':True,
              'abs_zeta':rows[-1]['approx_abs_zeta'],'independent_library_validation':False}
    if independent:
        mp = zeta.mp
        with mp.workdps(80):
            mid = mp.mpc(values[-1].real.mid().str(90,radius=False),
                         values[-1].imag.mid().str(90,radius=False))
            with mp.workdps(50):
                other = mp.zeta(mp.mpc(sigma,height))
            difference = abs(mid-other)
            if difference >= mp.mpf('1e-40')*max(1,abs(mid)):
                raise ArithmeticError('Independent mpmath/Arb disagreement')
            result.update(independent_library_validation=True,
                          mpmath_dps=50,independent_difference=mp.nstr(difference,20))
    return result


def window_path(w):
    return HERE/'windows'/(w['id']+'.json')


def worker(w, expected_sha):
    path = window_path(w)
    row = {'id':w['id'],'manifest_sha256':expected_sha,'window':w,
           'status':'RUNNING','started_utc':utc(),'attempts':[],'phase':'IMPORTING'}
    try:
        manifest, actual = verify_frozen()
        if actual != expected_sha or w not in manifest['windows']:
            raise ValueError('Worker received an unfrozen window')
        if path.exists():
            previous = read(path)
            if previous['manifest_sha256']!=expected_sha or previous['window']!=w:
                raise ValueError('Checkpoint belongs to a different window/manifest')
            if previous['status'] in TERMINAL:
                return
            row = previous
        row['attempts'].append({'pid':os.getpid(),'started_utc':utc()})
        row['status']='RUNNING'
        save(path,row)
        started = time.perf_counter()
        zeta = load_target()
        plan = manifest['plan']
        row['versions']={'python':sys.version,'numpy':zeta.np.__version__,
                         'scipy':zeta.scipy.__version__,'python_flint':zeta.flint.__version__,
                         'mpmath':zeta.mp.__version__}
        if 'center_check' not in row:
            row['phase']='CENTER_CHECK'
            save(path,row)
            row['center_check']=point_check(plan['center_sigma'],w['center']['t'],w['regime']=='low_calibration')
            save(path,row)
        if 'optimization' not in row:
            row['phase']='OPTIMIZATION'
            save(path,row)
            row['optimization']=zeta.optimize_box(*w['sigma_bounds'],*w['offset_bounds'],
                t_base=w['t_base'],dps=plan['de']['dps'],maxiter=plan['de']['maxiter'],
                popsize=plan['de']['popsize'],seed=w['seed'],workers=1)
            if row['optimization']['optimizer']['nfev']>plan['de']['maximum_evaluations']:
                raise AssertionError('DE evaluation budget exceeded')
            save(path,row)
        best=row['optimization']['best']
        if 'best_check' not in row:
            row['phase']='BEST_CHECK'
            save(path,row)
            row['best_check']=point_check(best['sigma'],best['t'],w['regime']=='low_calibration')
            if not math.isclose(row['best_check']['abs_zeta'],best['approx_abs_zeta'],rel_tol=1e-10,abs_tol=1e-20):
                raise ArithmeticError('Optimizer value and saved best coordinate disagree')
            save(path,row)
        if 'best_small_box' not in row:
            from zero_lab import zeta_box
            row['phase']='SMALL_BOX'
            save(path,row)
            row['best_small_box']=zeta_box(best['sigma'],best['t'],plan['small_box_radius'],dps=80)
            save(path,row)
        reasons=[]
        if min(row['center_check']['abs_zeta'],row['best_check']['abs_zeta'])<plan['candidate_abs_threshold']:
            reasons.append('actual_zeta_below_1e_minus_6')
        if not row['best_small_box']['certified_zero_free']:
            reasons.append('tiny_box_exclusion_unresolved')
        row['followup_reasons']=reasons
        row['status']='NEEDS_CHECK' if reasons else 'COMPLETED'
        row['phase']='FINISHED'
        row['certified_off_line_zero']=False
        row['whole_search_window_zero_free_certified']=False
        row['last_attempt_seconds']=time.perf_counter()-started
        row['finished_utc']=utc()
        save(path,row)
    except BaseException as exc:
        row['status']='ERROR'
        row['error']=f'{type(exc).__name__}: {exc}'
        row['traceback']=traceback.format_exc()
        row['finished_utc']=utc()
        save(path,row)


def collect(manifest, digest):
    rows=[]
    for w in manifest['windows']:
        path=window_path(w)
        if path.exists():
            row=read(path)
            if row['manifest_sha256']!=digest or row['window']!=w:
                raise ValueError('Unexpected checkpoint content: '+w['id'])
            rows.append(row)
    return rows


def report(manifest, digest, state):
    rows=collect(manifest,digest)
    groups=defaultdict(list)
    generated=Counter((w['regime'],w['k'],w['rule'],w['source']) for w in manifest['windows'])
    for cell in manifest['cells']:
        groups[(cell['block']['regime'],cell['k'],cell['rule'],cell['source'])]
    for row in rows:
        w=row['window']
        groups[(w['regime'],w['k'],w['rule'],w['source'])].append(row)
    summaries=[]
    for key, group in sorted(groups.items()):
        finished=[r for r in group if r['status'] in ('COMPLETED','NEEDS_CHECK')]
        a=[r['center_check']['abs_zeta'] for r in finished]
        b=[r['best_check']['abs_zeta'] for r in finished]
        summaries.append({'regime':key[0],'k':key[1],'rule':key[2],'source':key[3],
                          'expected_slots':4,'generated_windows':generated[key],'finished_windows':len(finished),
                          'center_median':statistics.median(a) if a else None,
                          'best_median':statistics.median(b) if b else None,
                          'best_minimum':min(b) if b else None})
    output={'status':state['status'],'manifest_sha256':digest,'groups':summaries,
            'window_status_counts':dict(Counter(r['status'] for r in rows)),
            'maximum_slots':manifest['maximum_slots'],'generated_windows':len(manifest['windows']),
            'missing_model_slots':manifest['maximum_slots']-len(manifest['windows']),
            'completed_objective_evaluations':sum(r.get('optimization',{}).get('optimizer',{}).get('nfev',0) for r in rows),
            'equivalent_sources':manifest['equivalent_sources'],
            'flagged_windows':[r['id'] for r in rows if r['status']=='NEEDS_CHECK'],
            'window_sha256':{r['id']:sha(window_path(r['window'])) for r in rows},
            'certified_off_line_zero':False,'whole_search_window_exclusion_claimed':False,
            'independent_high_height_library_check_performed':False,'updated_utc':utc()}
    save(HERE/'RESULTS.json',output)
    lines=['# 相邻相关与三点曲率：PC搜索结果','','## Material Passport','',
           '- 输入：原异常整数差字；事先固定的置乱、A谷值和B峰值规则。',
           '- 性质：有界启发式真实ζ搜索；不构成模型对应定理或RH反例。',
           f"- 状态：{state['status']}；完成状态计数：{output['window_status_counts']}。",
           f"- 候选窗口：{len(manifest['windows'])}/64；模型缺额：{output['missing_model_slots']}。",
           f"- 已保存的完整优化目标求值数：{output['completed_objective_evaluations']}。",'',
           '| 区域 | 阶段 | 规则 | 来源 | 完成/预定槽 | 中心ζ绝对值中位数 | 寻优最佳值中位数 |',
           '|---|---:|---|---|---:|---:|---:|']
    def fmt(v):
        return '—' if v is None else f'{v:.8g}'
    for g in summaries:
        lines.append(f"| {g['regime']} | {g['k']} | {g['rule']} | {g['source']} | {g['finished_windows']}/4 | {fmt(g['center_median'])} | {fmt(g['best_median'])} |")
    lines += ['', '小样本描述性比较。缺少候选与计算错误均单独保留；中位数只用完成窗口，不把缺额偷偷计成命中。',
              'A与B分别报告；不根据ζ结果切换极值方向。置乱和原符号若同谱，不能当作独立重复。',
              '低高度中心及最佳点用Arb与mpmath交叉核对；高高度仅做同一Arb库40/80位复核，独立库认证尚未执行。',
              '最佳点周围半径1e-8小盒的严格排零，只覆盖该小盒，不能推广成整个搜索窗口无零。',
              '优化器未收敛不等于作业失败；固定预算最佳值也不是全局最优证明。',
              '没有执行完整窗口零点计数，没有认证任何RH反例。NEEDS_CHECK仅表示需要复查。',
              '', '[完整数据](RESULTS.json) · [任务状态](JOB_STATUS.json) · [冻结清单](FROZEN_WINDOWS.json)', '']
    (HERE/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    return output


def run():
    with lock():
        manifest,digest=verify_frozen()
        checks=read(HERE/'FROZEN_CHECKS.json')
        if checks['status']!='PASS' or checks['manifest_sha256']!=digest:
            raise ValueError('Frozen candidate checks have not passed for this manifest')
        plan=manifest['plan']
        status_path=HERE/'JOB_STATUS.json'
        old=read(status_path) if status_path.exists() else None
        if old and old['manifest_sha256']!=digest:
            raise ValueError('Job status belongs to different manifest')
        if old and old['status'] in ('COMPLETE','NEEDS_CHECK','FINISHED_WITH_ERRORS') and old.get('pending_windows',0)==0:
            if sha(HERE/'RESULTS.json')!=old['results_sha256']:
                raise ValueError('Final report changed')
            final=read(HERE/'RESULTS.json')
            for w in manifest['windows']:
                if sha(window_path(w))!=final['window_sha256'][w['id']]:
                    raise ValueError('Final window file changed')
            print('ALREADY_COMPLETE',flush=True)
            return
        (HERE/'windows').mkdir(exist_ok=True)
        prior={r['id']:r for r in collect(manifest,digest)}
        pending=[w for w in manifest['windows'] if prior.get(w['id'],{}).get('status') not in TERMINAL]
        state={'status':'RUNNING','pid':os.getpid(),'started_utc':utc(),'updated_utc':utc(),
               'manifest_sha256':digest,'total_windows':len(manifest['windows']),
               'workers':plan['workers'],'session_seconds':plan['session_seconds'],
               'per_window_seconds':plan['per_window_seconds'],'sessions':old.get('sessions',[]) if old else [],
               'completed_windows_at_resume':sum(r['status'] in TERMINAL for r in prior.values())}
        state['sessions'].append({'started_utc':state['started_utc'],'pid':os.getpid()})
        save(status_path,state)
        awake=None
        if os.name=='nt':
            import ctypes
            awake=ctypes.windll.kernel32.SetThreadExecutionState
            state['temporary_keep_awake_accepted']=bool(awake(0x80000001))
        context=multiprocessing.get_context('spawn')
        active={}
        started=time.perf_counter()
        paused=False
        try:
            while pending or active:
                elapsed=time.perf_counter()-started
                paused=(HERE/'STOP_AFTER_CURRENT').exists() or elapsed>=plan['session_seconds']
                while pending and len(active)<plan['workers'] and not paused:
                    w=pending.pop(0)
                    process=context.Process(target=worker,args=(w,digest))
                    process.start()
                    active[w['id']]=(process,w,time.perf_counter())
                for ident,(process,w,t0) in list(active.items()):
                    overdue=time.perf_counter()-t0>plan['per_window_seconds'] or elapsed>=plan['session_seconds']
                    if process.is_alive() and overdue:
                        print('HARD_TIMEOUT '+ident,flush=True)
                        process.terminate()
                        process.join(10)
                        if process.is_alive():
                            process.kill()
                            process.join(10)
                        row=read(window_path(w)) if window_path(w).exists() else {'id':ident,'window':w,'manifest_sha256':digest}
                        if row.get('status') not in TERMINAL:
                            row.update(status='TIMEOUT' if elapsed<plan['session_seconds'] else 'PAUSED_SESSION_LIMIT',finished_utc=utc())
                            save(window_path(w),row)
                    if not process.is_alive():
                        process.join()
                        path=window_path(w)
                        row=read(path) if path.exists() else {'id':ident,'window':w,'manifest_sha256':digest}
                        if row.get('status') not in TERMINAL|{'PAUSED_SESSION_LIMIT'}:
                            row.update(status='ERROR',error=f'Worker exited without terminal result: {process.exitcode}',finished_utc=utc())
                            save(path,row)
                        print(f"WINDOW_FINISHED {ident} {row['status']}",flush=True)
                        del active[ident]
                rows=collect(manifest,digest)
                state.update(updated_utc=utc(),elapsed_seconds=elapsed,
                             status_counts=dict(Counter(r['status'] for r in rows)),
                             pending_windows=len(pending),active_workers={ident:p.pid for ident,(p,w,t) in active.items()})
                save(status_path,state)
                if paused and not active:
                    break
                time.sleep(2)
            verify_frozen()
            rows=collect(manifest,digest)
            if len(rows)==len(manifest['windows']) and all(r['status']=='COMPLETED' for r in rows):
                state['status']='COMPLETE'
            elif pending or any(r['status']=='PAUSED_SESSION_LIMIT' for r in rows):
                state['status']='PAUSED'
            elif any(r['status'] in ('ERROR','TIMEOUT') for r in rows):
                state['status']='FINISHED_WITH_ERRORS'
            elif any(r['status']=='NEEDS_CHECK' for r in rows):
                state['status']='NEEDS_CHECK'
            else:
                state['status']='FINISHED_WITH_ERRORS'
            report(manifest,digest,state)
            state['results_sha256']=sha(HERE/'RESULTS.json')
        except BaseException as exc:
            state.update(status='ERROR',error=f'{type(exc).__name__}: {exc}',traceback=traceback.format_exc())
            raise
        finally:
            # Ordinary stop drains active windows. Exception cleanup owns only these processes.
            for process,w,t0 in active.values():
                if process.is_alive():
                    process.terminate()
                process.join(10)
            if awake:
                state['temporary_keep_awake_restored']=bool(awake(0x80000000))
            state.update(updated_utc=utc(),finished_utc=utc(),active_workers={},elapsed_seconds=time.perf_counter()-started)
            state['sessions'][-1].update(finished_utc=state['finished_utc'],elapsed_seconds=state['elapsed_seconds'],status=state['status'])
            save(status_path,state)
        print('SESSION_FINISHED '+state['status'],flush=True)


if __name__=='__main__':
    multiprocessing.freeze_support()
    run()
