"""GPU finite-symbol screening and an equal-work CPU/GPU benchmark.

Absolute high phases are reduced in 80 decimal digits before float64 work.
No zeta function is imported or evaluated here.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import io
import itertools
import json
import math
import os
from pathlib import Path
import random
import statistics
import sys
import time

HERE=Path(__file__).resolve().parent
RESEARCH=HERE.parent
RUNTIME=os.environ.get('RH_CUPY_DEPS')
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='1'
if RUNTIME:
    sys.path.insert(0,RUNTIME)
sys.path.insert(0,str(RESEARCH/'2026-09-08-zero-lab/.deps'))
import numpy as np
try:
    import cupy as cp
except ImportError:
    cp=None
import mpmath as mp


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path,data):
    path=Path(path)
    pending=path.with_suffix(path.suffix+'.tmp')
    pending.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    deadline=time.monotonic()+3
    while True:
        try:
            pending.replace(path)
            return
        except PermissionError:
            if time.monotonic()>deadline:
                raise
            time.sleep(.05)


def all_patterns(signs):
    positive=sum(e==1 for e in signs)
    choices=list(itertools.combinations(range(len(signs)),positive))
    patterns=-np.ones((len(choices),len(signs)),dtype=np.int8)
    for i, positions in enumerate(choices):
        patterns[i,list(positions)]=1
    return patterns


def ratios(support,rule):
    if rule=='A_min':
        return [Fraction(b,a) for a,b in zip(support,support[1:])]
    return [Fraction(support[j]*support[j+2],support[j+1]**2) for j in range(len(support)-2)]


def coefficients(patterns,rule):
    step=1 if rule=='A_min' else 2
    return (patterns[:,:-step]*patterns[:,step:]).astype(np.float64)


def phase_grid(support,rule,base,plan):
    started=time.perf_counter()
    with mp.workdps(plan['phase_dps']):
        freq=[mp.log(mp.mpf(q.numerator)/q.denominator) for q in ratios(support,rule)]
        phase=[mp.fmod(mp.mpf(base)*w,2*mp.pi) for w in freq]
        w=np.array([float(v) for v in freq],dtype=np.float64)
        p=np.array([float(v) for v in phase],dtype=np.float64)
    offsets=np.arange(plan['grid_points'],dtype=np.float64)*float(plan['grid_step'])
    angles=p[:,None]+w[:,None]*offsets[None,:]
    cosine=np.cos(angles)
    derivative=-w[:,None]*np.sin(angles)
    return cosine,derivative,time.perf_counter()-started


def screen(coeff,cosine,derivative,rule,plan,backend):
    if backend not in ('cpu','gpu'):
        raise ValueError('backend must be cpu or gpu')
    if backend=='gpu' and cp is None:
        raise RuntimeError('GPU mode requires CuPy; install requirements-gpu.txt or select cpu')
    xp=np if backend=='cpu' else cp
    if backend=='gpu':
        cp.cuda.Stream.null.synchronize()
    started=time.perf_counter()
    co=xp.asarray(coeff)
    cs=xp.asarray(cosine)
    ds=xp.asarray(derivative)
    orientation=1 if rule=='A_min' else -1
    all_indices=[]
    all_scores=[]
    all_counts=[]
    for first in range(0,len(coeff),plan['patterns_per_chunk']):
        part=co[first:first+plan['patterns_per_chunk']]
        value=(part@cs)/co.shape[1]
        deriv=orientation*(part@ds)/co.shape[1]
        mask=(deriv[:,:-1]<0)&(deriv[:,1:]>0)
        # This intentionally defines a grid selection, not an exact-extremum ranking.
        merit=xp.where(mask,orientation*(value[:,:-1]+value[:,1:])/2,xp.inf)
        idx=xp.argmin(merit,axis=1)
        score=xp.min(merit,axis=1)
        count=xp.sum(mask,axis=1)
        idx=xp.where(count>0,idx,-1)
        all_indices.append(idx)
        all_scores.append(score)
        all_counts.append(count)
    result=[xp.concatenate(v) for v in (all_indices,all_scores,all_counts)]
    if backend=='gpu':
        result=[cp.asnumpy(v) for v in result]
        cp.cuda.Stream.null.synchronize()
    elapsed=time.perf_counter()-started
    return result,elapsed


def validate_precision(model,patterns,rule,base,plan,cosine,derivative,backend='gpu'):
    coeff=coefficients(patterns,rule)
    indices=sorted(set([0,len(patterns)//3,len(patterns)//2,len(patterns)-1]))
    grid=sorted(set([0,1,plan['grid_points']//4,plan['grid_points']//2,plan['grid_points']-1]))
    xp=np if backend=='cpu' else cp
    gpu_values=xp.asarray(coeff[indices])@xp.asarray(cosine)/coeff.shape[1]
    gpu_derivatives=xp.asarray(coeff[indices])@xp.asarray(derivative)/coeff.shape[1]
    if backend=='gpu':
        gpu_values=cp.asnumpy(gpu_values)
        gpu_derivatives=cp.asnumpy(gpu_derivatives)
    worst=0.0
    with mp.workdps(100):
        freq=[mp.log(mp.mpf(q.numerator)/q.denominator) for q in ratios(model['support'],rule)]
        for row,pi in enumerate(indices):
            for j in grid:
                t=mp.mpf(base)+mp.mpf(plan['grid_step'])*j
                c=coeff[pi]
                val=mp.fsum(int(c[k])*mp.cos(t*w) for k,w in enumerate(freq))/len(freq)
                der=-mp.fsum(int(c[k])*w*mp.sin(t*w) for k,w in enumerate(freq))/len(freq)
                worst=max(worst,float(abs(val-float(gpu_values[row,j]))),float(abs(der-float(gpu_derivatives[row,j]))))
    if worst>plan['validation_absolute_tolerance']:
        raise ArithmeticError(f'{backend}/high-precision mismatch: {worst}')
    return {'backend':backend,'samples':len(indices)*len(grid),'max_absolute_error':worst,'reference_dps':100}


def benchmark(plan,model):
    patterns=all_patterns(model['signs'])
    base=str(int(plan['high_base'])+plan['first_offset'])
    cosine,derivative,phase_seconds=phase_grid(model['support'],'A_min',base,plan)
    coeff=coefficients(patterns,'A_min')
    warm_started=time.perf_counter()
    cpu,_=screen(coeff,cosine,derivative,'A_min',plan,'cpu')
    gpu,_=screen(coeff,cosine,derivative,'A_min',plan,'gpu')
    warm_seconds=time.perf_counter()-warm_started
    if not np.array_equal(cpu[0],gpu[0]) or not np.array_equal(cpu[2],gpu[2]):
        raise ArithmeticError('CPU/GPU directed-crossing selection mismatch')
    finite=np.isfinite(cpu[1])&np.isfinite(gpu[1])
    difference=float(np.max(np.abs(cpu[1][finite]-gpu[1][finite])))
    if difference>plan['validation_absolute_tolerance']:
        raise ArithmeticError('CPU/GPU merit mismatch')
    timing={'cpu':[],'gpu':[]}
    for repeat in range(plan['benchmark_repeats']):
        for backend in (('cpu','gpu') if repeat%2==0 else ('gpu','cpu')):
            result,elapsed=screen(coeff,cosine,derivative,'A_min',plan,backend)
            assert np.array_equal(result[0],cpu[0])
            timing[backend].append(elapsed)
    precision=validate_precision(model,patterns,'A_min',base,plan,cosine,derivative)
    cpu_median=statistics.median(timing['cpu'])
    gpu_median=statistics.median(timing['gpu'])
    return {'status':'PASS','utc':utc(),'patterns':len(patterns),'grid_points':plan['grid_points'],
            'pattern_grid_positions':len(patterns)*plan['grid_points'],'phase_seconds':phase_seconds,
            'warmup_cpu_plus_gpu_seconds':warm_seconds,'seconds':timing,
            'cpu_median_seconds':cpu_median,'gpu_median_seconds':gpu_median,
            'cpu_over_gpu_ratio':cpu_median/gpu_median,'indices_and_counts_identical':True,
            'maximum_cpu_gpu_merit_difference':difference,'precision_check':precision,
            'timing_scope':'Equal-work screening, transfers and output included; shared 80-digit phase preparation reported separately; warm-up excluded.',
            'cpu_blas_threads':1,'is_zeta_speedup':False}


def refine(model,signs,rule,base,index,plan):
    with mp.workdps(80):
        freq=[mp.log(mp.mpf(q.numerator)/q.denominator) for q in ratios(model['support'],rule)]
        hop=1 if rule=='A_min' else 2
        co=[signs[j]*signs[j+hop] for j in range(len(signs)-hop)]
        orientation=1 if rule=='A_min' else -1
        def derivative(offset):
            return -orientation*mp.fsum(c*w*mp.sin((mp.mpf(base)+offset)*w) for c,w in zip(co,freq))/len(co)
        lo=mp.mpf(plan['grid_step'])*index
        hi=lo+mp.mpf(plan['grid_step'])
        if not (derivative(lo)<0<derivative(hi)):
            raise ArithmeticError('GPU selected bracket failed high-precision check')
        for _ in range(100):
            mid=(lo+hi)/2
            value=derivative(mid)
            if value<0:
                lo=mid
            elif value>0:
                hi=mid
            else:
                lo=hi=mid
                break
            if hi-lo<mp.mpf('1e-25'):
                break
        offset=(lo+hi)/2
        t=mp.mpf(base)+offset
        radius=mp.mpf(plan['height_radius'])
        if not (0<offset-radius<offset+radius<plan['block_width']):
            return None
        raw=mp.fsum(c*mp.cos(t*w) for c,w in zip(co,freq))/len(co)
        return {'t':mp.nstr(t,70),'offset':mp.nstr(offset,70),'value':mp.nstr(raw,70),
                'bracket_offset':[mp.nstr(lo,70),mp.nstr(hi,70)],
                'derivative_residual':mp.nstr(derivative(offset),30),
                'offset_bounds':[mp.nstr(offset-radius,70),mp.nstr(offset+radius,70)]}
