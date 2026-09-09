import copy
from fractions import Fraction
from pathlib import Path
import sys
import wide_target as target
from wide_common import HERE,RESEARCH,read,save,sha,utc,inputs


def prepare():
    frozen,input_digest=inputs()
    result=read(HERE/'FROZEN_WINDOWS_GPU.json')
    status=read(HERE/'GPU_STATUS.json')
    assert status['status']=='COMPLETE'
    assert status['manifest_sha256']==sha(HERE/'FROZEN_WINDOWS_GPU.json')
    assert result['frozen_inputs_sha256']==input_digest
    assert result['database_sha256']==sha(HERE/'survey.sqlite3')
    if (target.TARGET/'FREEZE_RECEIPT.json').exists():
        target.common.verify_frozen()
        print('ALREADY_PREPARED',flush=True);return
    sys.path.insert(0,str(target.common.LAB/'.deps'))
    import mpmath as mp
    cells={c['id']:c for c in result['cells']}
    with mp.workdps(100):
        for w in result['windows']:
            c=cells[w['id']];a=c['support'];e=c['signs']
            hop=1 if c['rule']=='A_min' else 2
            qs=[Fraction(a[j+1],a[j]) if hop==1 else Fraction(a[j]*a[j+2],a[j+1]**2) for j in range(len(a)-hop)]
            fs=[mp.log(mp.mpf(q.numerator)/q.denominator) for q in qs]
            co=[e[j]*e[j+hop] for j in range(len(a)-hop)]
            t=mp.mpf(w['center']['t'])
            d=-mp.fsum(x*f*mp.sin(t*f) for x,f in zip(co,fs))/len(fs)
            assert abs(d)<mp.mpf('1e-24')
            assert abs(t-mp.mpf(w['t_base'])-mp.mpf(w['center']['offset']))<mp.mpf('1e-54')
            aa,bb=map(Fraction,w['sigma_bounds']);cc,dd=map(Fraction,w['offset_bounds'])
            assert Fraction(1,2)<aa<bb<1 and cc<Fraction(w['center']['offset'])<dd
    plan=copy.deepcopy(read(RESEARCH/result['plan']['source_plan']))
    limits=result['plan']['cpu']
    plan.update(version='wide-gpu-zeta-v1',centers_per_cell=1,workers=limits['workers'],
                session_seconds=limits['session_seconds'],per_window_seconds=limits['per_window_seconds'])
    with mp.workdps(80):
        plan['center_sigma']=mp.nstr(sum(map(mp.mpf,result['plan']['sigma_bounds']))/2,70)
    plan['de'].update(maxiter=limits['de_maxiter'],popsize=limits['de_popsize'],
                      maximum_evaluations=limits['maximum_evaluations_per_window'],seed_base=limits['seed_base'])
    plan['blocks']=[{'id':w['t_base'],'regime':w['regime'],'base':w['t_base'],'width':'128'} for w in result['windows']]
    hashes=dict(frozen['input_sha256'])
    hashes.update({str(p.relative_to(RESEARCH)).replace('\\','/'):sha(p) for p in (HERE/'FROZEN_INPUTS.json',HERE/'FROZEN_WINDOWS_GPU.json')})
    payload={'status':'FROZEN_BEFORE_TARGET_ZETA','plan':plan,'windows':result['windows'],
             'cells':result['cells'],'maximum_slots':result['maximum_slots'],'input_sha256':hashes,
             'gpu_manifest_sha256':sha(HERE/'FROZEN_WINDOWS_GPU.json'),'equivalent_sources':[],
             'created_utc':utc()}
    save(target.TARGET/'FROZEN_WINDOWS.json',payload)
    digest=sha(target.TARGET/'FROZEN_WINDOWS.json')
    save(target.TARGET/'FREEZE_RECEIPT.json',{'manifest_sha256':digest,'utc':utc()})
    save(target.TARGET/'FROZEN_CHECKS.json',{'status':'PASS','manifest_sha256':digest,
             'windows_checked':len(result['windows']),'model_dps':100,'target_zeta_called':False})
    target.common.verify_frozen()
    print('TARGET_PREPARED',len(result['windows']),digest,flush=True)


if __name__=='__main__':
    prepare()
