"""Operational-only wrapper: tolerate transient Windows file sharing conflicts.

Frozen mathematical sources remain unchanged. Spawned children import this
entrypoint too, applying the same bounded I/O retry in every owned process.
"""
import multiprocessing
import time
from pathlib import Path
import common
import run_search

original_save = common.save


def retry_save(path, value):
    deadline=time.monotonic()+3.0
    while True:
        try:
            return original_save(path,value)
        except PermissionError as exc:
            if getattr(exc,'winerror',None) not in (5,32,33) or time.monotonic()>=deadline:
                raise
            time.sleep(0.05)


common.save=retry_save
run_search.save=retry_save


if __name__=='__main__':
    multiprocessing.freeze_support()
    manifest,digest=common.verify_frozen()
    path=Path(__file__).resolve()
    common.save(common.HERE/'IO_PATCH_RECEIPT.json',{
        'utc':common.utc(),'manifest_sha256':digest,'wrapper_sha256':common.sha(path),
        'reason':'Prior parent stopped on Windows PermissionError while replacing JOB_STATUS.json.',
        'change':'Retry only Windows sharing/access PermissionErrors for at most 3 seconds; unchanged mathematical calculation.',
        'frozen_sources_unchanged':True,'completed_windows_preserved':True})
    run_search.run()
