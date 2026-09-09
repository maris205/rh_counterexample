"""Connect frozen GPU-selected windows to the existing CPU zeta worker.

Only paths, I/O retry, and group-size reporting are adapted here. The original
zeta worker and differential-evolution numerical implementation are reused.
"""
from collections import Counter,defaultdict
from pathlib import Path
import statistics
import sys
import multiprocessing

HERE=Path(__file__).resolve().parent
TARGET=HERE/'true_zeta'
SOURCE=HERE.parent/'2026-09-09-pc-gap-search'
sys.path.insert(0,str(SOURCE))
import common
import run_search
import resume_safe

# Module import is repeated in Windows spawned children.
common.HERE=TARGET
run_search.HERE=TARGET


def report(manifest,digest,state):
    rows=run_search.collect(manifest,digest)
    grouped=defaultdict(list)
    allocated=Counter((c['k'],c['rule'],c['source']) for c in manifest['cells'])
    generated=Counter((w['k'],w['rule'],w['source']) for w in manifest['windows'])
    for key in allocated:
        grouped[key]
    for row in rows:
        w=row['window']
        grouped[(w['k'],w['rule'],w['source'])].append(row)
    groups=[]
    for key,group in sorted(grouped.items()):
        complete=[r for r in group if r['status'] in ('COMPLETED','NEEDS_CHECK')]
        a=[r['center_check']['abs_zeta'] for r in complete]
        b=[r['best_check']['abs_zeta'] for r in complete]
        groups.append({'k':key[0],'rule':key[1],'source':key[2],'expected_slots':allocated[key],
                       'generated_windows':generated[key],'finished_windows':len(complete),
                       'center_median':statistics.median(a) if a else None,
                       'best_median':statistics.median(b) if b else None,
                       'best_minimum':min(b) if b else None})
    result={'status':state['status'],'manifest_sha256':digest,'groups':groups,
            'maximum_slots':manifest['maximum_slots'],'generated_windows':len(manifest['windows']),
            'status_counts':dict(Counter(r['status'] for r in rows)),
            'completed_objective_evaluations':sum(r.get('optimization',{}).get('optimizer',{}).get('nfev',0) for r in rows),
            'flagged_windows':[r['id'] for r in rows if r['status']=='NEEDS_CHECK'],
            'window_sha256':{r['id']:common.sha(run_search.window_path(r['window'])) for r in rows},
            'independent_high_height_library_validation':False,'certified_off_line_zero':False,
            'whole_search_window_exclusion_claimed':False,'updated_utc':common.utc()}
    common.save(TARGET/'RESULTS.json',result)
    lines=['# GPU选窗后的真实ζ检查','','## Material Passport','',
           '- 输入：GPU筛选预先冻结的原符号和固定置乱高位窗口。',
           '- GPU筛选速度不能作为ζ候选质量证据；本页仅报告真实ζ计算。',
           f"- 状态：{state['status']}；{result['status_counts']}。",
           f"- 完整优化已保存求值数：{result['completed_objective_evaluations']}。",'',
           '| 阶段 | 规则 | 来源 | 完成/槽位 | 中心ζ绝对值中位数 | 最佳值中位数 |',
           '|---|---|---|---:|---:|---:|']
    fmt=lambda x:'—' if x is None else f'{x:.8g}'
    for g in groups:
        lines.append(f"| {g['k']} | {g['rule']} | {g['source']} | {g['finished_windows']}/{g['expected_slots']} | {fmt(g['center_median'])} | {fmt(g['best_median'])} |")
    lines+=['','缺额与失败保留。样本小且来源相关，没有显著性或一般预测优势结论。',
            '高位使用同一Arb库40/80位复核；独立库验证尚未完成。1e-8最佳点小盒排零不覆盖整个搜索窗。',
            'NEEDS_CHECK仅标记后续复查；没有认证RH反例。','',
            '[完整数据](RESULTS.json) · [实时状态](JOB_STATUS.json)','']
    (TARGET/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    return result


run_search.report=report


if __name__=='__main__':
    multiprocessing.freeze_support()
    run_search.run()
