"""Resumable GPU survey, using the verified previous GPU kernel unchanged."""
from collections import defaultdict
import hashlib
import json
import math
import random
import sqlite3
import sys
import time
import traceback
from wide_common import HERE,RESEARCH,read,save,sha,utc,inputs,lock

sys.path.insert(0,str(RESEARCH/'2026-09-09-gpu-gap-screen'))
import gpu_screen as engine
np=engine.np


def sources(model,patterns,plan):
    original=model['signs']
    shuffled=original[:]
    rng=random.Random(plan['shuffle_seed_base']+model['k'])
    for _ in range(32):
        rng.shuffle(shuffled)
        if shuffled!=original and shuffled!=[-x for x in original]:
            break
    else:
        raise ValueError('No distinct control')
    out=[]
    for kind,signs in [('original',original),('shuffled',shuffled)]:
        ix=np.flatnonzero(np.all(patterns==np.array(signs)[None,:],axis=1))
        assert len(ix)==1
        out.append({'source':kind,'signs':signs[:],'pattern_index':int(ix[0])})
    return out


def region_base(anchor,index,plan):
    return str(int(anchor)+plan['first_offset']+index*plan['stride'])


def group_key(row,selected,plan):
    return (row['anchor'],row['k'],row['rule'],selected['source'],
            row['region_index']//(plan['regions_per_anchor']//plan['strata_per_anchor']))


def select_winners(rows,plan):
    groups=defaultdict(list)
    for row in rows:
        for selected in row['selected_sources']:
            key=group_key(row,selected,plan)
            groups[key]
            if selected['bracket_index']>=0:
                groups[key].append((row,selected))
    winners=[]
    for key,items in sorted(groups.items(),key=lambda item:(int(item[0][0]),*item[0][1:])):
        chosen=min(items,key=lambda x:(x[1]['grid_merit'],int(x[0]['base']),x[1]['bracket_index'])) if items else None
        winners.append((key,chosen))
    return winners


def survey():
    frozen,digest=inputs(create=True)
    plan=read(HERE/'WIDE_PLAN.json')
    setup=read(HERE/'SETUP_CHECKS.json')
    if setup['status']!='PASS' or setup['input_sha256']!=frozen['input_sha256']:
        raise ValueError('Preflight checks not passed')
    if (HERE/'FROZEN_WINDOWS_GPU.json').exists():
        result=read(HERE/'FROZEN_WINDOWS_GPU.json')
        assert result['frozen_inputs_sha256']==digest
        assert sha(HERE/'survey.sqlite3')==result['database_sha256']
        print('ALREADY_SURVEYED',flush=True)
        return
    models=read(RESEARCH/plan['source_plan'])['models']
    db=sqlite3.connect(HERE/'survey.sqlite3')
    db.execute('PRAGMA synchronous=FULL')
    db.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY,value TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS cells (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
    prior=db.execute('SELECT value FROM meta WHERE key=?',('frozen_inputs_sha256',)).fetchone()
    if prior and prior[0]!=digest:
        raise ValueError('Checkpoint belongs to different inputs')
    db.execute('INSERT OR IGNORE INTO meta VALUES (?,?)',('frozen_inputs_sha256',digest));db.commit()
    existing={r[0] for r in db.execute('SELECT id FROM cells')}
    patterns={m['k']:engine.all_patterns(m['signs']) for m in models}
    source_map={m['k']:sources(m,patterns[m['k']],plan) for m in models}
    co={(m['k'],r):engine.coefficients(patterns[m['k']],r) for m in models for r in plan['rules']}
    total_cells=len(plan['anchors'])*plan['regions_per_anchor']*len(models)*len(plan['rules'])
    started=time.perf_counter()
    backend=plan['backend']
    status={'status':'RUNNING','pid':__import__('os').getpid(),'started_utc':utc(),
            'frozen_inputs_sha256':digest,'resumed_cells':len(existing),'total_cells':total_cells,
            'total_regions':len(plan['anchors'])*plan['regions_per_anchor'],
            'backend':backend,
            'versions':{'numpy':np.__version__,'mpmath':engine.mp.__version__}}
    if backend=='gpu':
        status['gpu']=engine.cp.cuda.runtime.getDeviceProperties(0)['name'].decode()
        status['versions'].update(cupy=engine.cp.__version__,cuda_runtime=engine.cp.cuda.runtime.runtimeGetVersion())
    save(HERE/'GPU_STATUS.json',status)
    for anchor in plan['anchors']:
        for region in range(plan['regions_per_anchor']):
            if (HERE/'STOP_AFTER_CURRENT').exists() or time.perf_counter()-started>plan['gpu_session_seconds']:
                status.update(status='PAUSED',updated_utc=utc(),completed_cells=len(existing))
                save(HERE/'GPU_STATUS.json',status);db.close();return
            base=region_base(anchor,region,plan)
            for model in models:
                k=model['k']
                for rule in plan['rules']:
                    ident=f'{anchor}_{region}_k{k}_{rule}'
                    if ident in existing:
                        continue
                    cosine,derivative,phase_time=engine.phase_grid(model['support'],rule,base,plan)
                    result,elapsed=engine.screen(co[k,rule],cosine,derivative,rule,plan,backend)
                    indices,scores,counts=result
                    selected=[]
                    for src in source_map[k]:
                        j=src['pattern_index']
                        selected.append({**src,'bracket_index':int(indices[j]),
                                         'grid_merit':float(scores[j]) if int(indices[j])>=0 else None,
                                         'located_crossings':int(counts[j])})
                    check=None
                    if region in (0,plan['regions_per_anchor']-1):
                        check=engine.validate_precision(model,patterns[k],rule,base,plan,cosine,derivative,backend)
                    result_hash=hashlib.sha256(b''.join(x.tobytes() for x in result)).hexdigest()
                    payload={'id':ident,'anchor':anchor,'region_index':region,'base':base,'k':k,'rule':rule,
                             'pattern_count':len(patterns[k]),'pattern_grid_positions':len(patterns[k])*plan['grid_points'],
                             'missing_patterns':int(np.sum(indices<0)),
                             'selected_sources':selected,'result_arrays_sha256':result_hash,
                             'gpu_seconds':elapsed,'phase_seconds':phase_time,'precision_check':check}
                    db.execute('INSERT INTO cells VALUES (?,?)',(ident,json.dumps(payload,allow_nan=False)))
                    existing.add(ident)
            db.commit()
            status.update(updated_utc=utc(),completed_cells=len(existing),completed_regions=len(existing)//4,
                          elapsed_session_seconds=time.perf_counter()-started,anchor=anchor,region_index=region)
            save(HERE/'GPU_STATUS.json',status)
            if region%16==0:
                print('GPU_REGIONS',len(existing)//4,'/',status['total_regions'],flush=True)
    assert len(existing)==total_cells
    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
    rows=[json.loads(r[0]) for r in db.execute('SELECT payload FROM cells ORDER BY id')]
    db.close()
    inputs()
    winners=select_winners(rows,plan)
    assert len(winners)==plan['maximum_windows']
    models_by_k={m['k']:m for m in models}
    windows=[];cells=[]
    for key,chosen in winners:
        anchor,k,rule,source,stratum=key
        ident=f'wide_{anchor}_k{k}_{rule}_{source}_q{stratum}'
        cell={'id':ident,'anchor':anchor,'k':k,'rule':rule,'source':source,'stratum':stratum,
              'selected_count':0,'missing_slots':1}
        if chosen:
            row,src=chosen
            point=engine.refine(models_by_k[k],src['signs'],rule,row['base'],src['bracket_index'],plan)
            cell.update(base=row['base'],region_index=row['region_index'],support=models_by_k[k]['support'],
                        signs=src['signs'],grid_merit=src['grid_merit'],bracket_index=src['bracket_index'])
            if point is not None:
                cell.update(selected_count=1,missing_slots=0)
                windows.append({'id':ident,'cell_id':ident,'k':k,'source':source,'rule':rule,'anchor':anchor,
                                'regime':'high_search' if int(row['base'])>3000000000000 else 'low_calibration',
                                'block_id':row['base'],'t_base':row['base'],
                                'center':point,'sigma_bounds':plan['sigma_bounds'],'offset_bounds':point['offset_bounds']})
        cells.append(cell)
    for i,w in enumerate(windows):
        w['seed']=plan['cpu']['seed_base']+i
    model_positions=sum(r['pattern_grid_positions'] for r in rows)
    output={'status':'FROZEN_BEFORE_ZETA','utc':utc(),'frozen_inputs_sha256':digest,
            'input_sha256':frozen['input_sha256'],'plan':plan,'windows':windows,'cells':cells,
            'maximum_slots':plan['maximum_windows'],'database_sha256':sha(HERE/'survey.sqlite3'),
            'model_grid_positions':model_positions,'surveyed_regions':status['total_regions'],
            'sum_disjoint_height_widths':status['total_regions']*plan['block_width'],
            'backend':backend,'screen_seconds':sum(r['gpu_seconds'] for r in rows),
            'gpu_seconds':sum(r['gpu_seconds'] for r in rows) if backend=='gpu' else None,
            'precision_checks':[r['precision_check'] for r in rows if r['precision_check']],
            'selection_used_zeta':False,'certified_off_line_zero':False,
            'not_continuous_coverage_between_regions':True,'same_spectra_not_independent_samples':True}
    save(HERE/'FROZEN_WINDOWS_GPU.json',output)
    status.update(status='COMPLETE',finished_utc=utc(),generated_windows=len(windows),
                  model_grid_positions=model_positions,manifest_sha256=sha(HERE/'FROZEN_WINDOWS_GPU.json'),
                  elapsed_session_seconds=time.perf_counter()-started)
    save(HERE/'GPU_STATUS.json',status)
    lines=['# 符号模型筛选完成','',
           '- 原异常整数差字及固定置乱；A谷值和B峰值规则。全部筛选不调用ζ。',
           f"- {len(plan['anchors'])}个高度带共{status['total_regions']}个不相连区间，每区间宽128。",
           f"- 共{model_positions:,}个模型网格位置；生成{len(windows)}/{plan['maximum_windows']}个待验证窗。",
           f"- 后端{backend}，累计筛选{output['screen_seconds']:.2f}秒，本次启动总耗时{status['elapsed_session_seconds']:.2f}秒。",'',
           f"每高度带划{plan['strata_per_anchor']}组；每个阶段/规则/来源在每组取1个最强网格信号。",
           '候选细化到80位并冻结；模型信号强不代表真实ζ小。后续CPU阶段对所有选中窗使用同预算。',
           '模型网格数与真实ζ求值数分别统计。没有覆盖区间之间的空隙，没有认证RH反例。',
           '', '[冻结清单](FROZEN_WINDOWS_GPU.json) · [GPU状态](GPU_STATUS.json) · [总体任务](PIPELINE_STATUS.json)','']
    (HERE/'GPU_RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    print('GPU_SURVEY_COMPLETE',len(windows),model_positions,flush=True)


if __name__=='__main__':
    with lock('gpu.lock'):
        try:
            survey()
        except BaseException as exc:
            state=read(HERE/'GPU_STATUS.json') if (HERE/'GPU_STATUS.json').exists() else {}
            state.update(status='ERROR',error=str(exc),traceback=traceback.format_exc(),updated_utc=utc())
            save(HERE/'GPU_STATUS.json',state)
            raise
