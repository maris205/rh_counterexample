from contextlib import contextmanager
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import time

HERE=Path(__file__).resolve().parent
RESEARCH=HERE.parent


def utc():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path,obj):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('w',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False)
        f.write('\n');f.flush();os.fsync(f.fileno())
    deadline=time.monotonic()+3
    while True:
        try:
            tmp.replace(path)
            return
        except PermissionError:
            if time.monotonic()>deadline:
                raise
            time.sleep(.05)


@contextmanager
def lock(name):
    f=(HERE/name).open('a+b')
    if f.tell()==0:
        f.write(b'0');f.flush()
    f.seek(0)
    try:
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield
    finally:
        f.close()


def input_files():
    names=['WIDE_PLAN.json','EXPERIMENT_PLAN.md','wide_common.py','wide_scan.py',
           'verify_wide.py','prepare_target.py','wide_target.py','run_pipeline.py']
    files=[HERE/n for n in names]
    files += [RESEARCH/n for n in ('2026-09-09-pc-gap-search/PLAN.json',
        '2026-09-09-pc-gap-search/common.py','2026-09-09-pc-gap-search/resume_safe.py',
        '2026-09-09-pc-gap-search/run_search.py','2026-09-09-gpu-gap-screen/gpu_screen.py',
        '2026-09-09-gpu-gap-screen/target_pipeline.py','2026-09-08-zeta-global-search/zeta_de.py',
        '2026-09-08-zero-lab/zero_lab.py','2026-09-08-zero-lab/certification/rectangle_count.py')]
    return files


def inputs(create=False):
    path=HERE/'FROZEN_INPUTS.json'
    now={str(p.relative_to(RESEARCH)).replace('\\','/'):sha(p) for p in input_files()}
    if path.exists():
        frozen=read(path)
        if now!=frozen['input_sha256']:
            raise ValueError('Frozen survey inputs changed')
    elif create:
        frozen={'status':'FROZEN_BEFORE_SURVEY','utc':utc(),'input_sha256':now}
        save(path,frozen)
    else:
        raise ValueError('Inputs not frozen')
    return frozen,sha(path)
