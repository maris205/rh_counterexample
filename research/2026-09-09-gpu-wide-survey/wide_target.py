"""Run the already verified actual-zeta worker against the wide-survey manifest."""
from collections import Counter,defaultdict
from pathlib import Path
import statistics
import sys
import multiprocessing

HERE=Path(__file__).resolve().parent
TARGET=HERE/'true_zeta'
sys.path.insert(0,str(HERE.parent/'2026-09-09-gpu-gap-screen'))
import target_pipeline as previous
common=previous.common
runner=previous.run_search
common.HERE=TARGET
runner.HERE=TARGET
previous.HERE=HERE
previous.TARGET=TARGET


def report(manifest,digest,state):
    rows=runner.collect(manifest,digest)
    groups=defaultdict(list)
    key=lambda x:(x['anchor'],x['k'],x['rule'],x['source'])
    expected=Counter(key(c) for c in manifest['cells'])
    generated=Counter(key(w) for w in manifest['windows'])
    for k in expected:
        groups[k]
    for r in rows:
        groups[key(r['window'])].append(r)
    output=[]
    for k,group in sorted(groups.items(),key=lambda v:(int(v[0][0]),*v[0][1:])):
        completed=[r for r in group if r['status'] in ('COMPLETED','NEEDS_CHECK')]
        a=[r['center_check']['abs_zeta'] for r in completed]
        b=[r['best_check']['abs_zeta'] for r in completed]
        output.append({'anchor':k[0],'k':k[1],'rule':k[2],'source':k[3],
            'expected_slots':expected[k],'generated_windows':generated[k],'finished_windows':len(completed),
            'center_median':statistics.median(a) if a else None,'best_median':statistics.median(b) if b else None})
    result={'status':state['status'],'manifest_sha256':digest,'groups':output,
        'maximum_slots':manifest['maximum_slots'],'generated_windows':len(manifest['windows']),
        'status_counts':dict(Counter(r['status'] for r in rows)),
        'completed_objective_evaluations':sum(r.get('optimization',{}).get('optimizer',{}).get('nfev',0) for r in rows),
        'flagged_windows':[r['id'] for r in rows if r['status']=='NEEDS_CHECK'],
        'window_sha256':{r['id']:common.sha(runner.window_path(r['window'])) for r in rows},
        'independent_high_height_library_validation':False,'certified_off_line_zero':False,'updated_utc':common.utc()}
    common.save(TARGET/'RESULTS.json',result)
    fmt=lambda x:'—' if x is None else f'{x:.8g}'
    lines=['# 符号模型候选：真实ζ结果','',
        '- 固定分层模型选窗，未按ζ分数反向选样。各个高度带分别报告。',
        f"- 状态：{state['status']}，{result['status_counts']}。",
        f"- 已保存完整优化求值数：{result['completed_objective_evaluations']}。",'',
        '| 高度带 | 阶段 | 规则 | 来源 | 完成/槽位 | 中心ζ中位数 | 最佳ζ中位数 |',
        '|---|---|---|---|---:|---:|---:|']
    for g in output:
        lines.append(f"| {g['anchor']} | {g['k']} | {g['rule']} | {g['source']} | {g['finished_windows']}/{g['expected_slots']} | {fmt(g['center_median'])} | {fmt(g['best_median'])} |")
    lines+=['','缺额、超时、错误不删除。小样本相关且经过模型筛选，没有p值或一般预测优势结论。',
        '高位复核使用同一Arb库40/80位；独立实现尚未执行。最佳点小盒排零不等于整个搜索窗无零。',
        '没有认证RH反例；NEEDS_CHECK是后续复查标记。','',
        '[完整数据](RESULTS.json) · [实时状态](JOB_STATUS.json)','']
    (TARGET/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    return result


runner.report=report


if __name__=='__main__':
    multiprocessing.freeze_support()
    runner.run()
