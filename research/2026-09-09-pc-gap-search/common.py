"""File utilities for this independent, resumable experiment."""
from datetime import datetime, timezone
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
SEARCH = RESEARCH / '2026-09-08-zeta-global-search'
LAB = RESEARCH / '2026-09-08-zero-lab'


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + '.tmp')
    with pending.open('w', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    pending.replace(path)


def verify_frozen():
    receipt = read(HERE / 'FREEZE_RECEIPT.json')
    path = HERE / 'FROZEN_WINDOWS.json'
    if sha(path) != receipt['manifest_sha256']:
        raise ValueError('Frozen window manifest changed')
    manifest = read(path)
    for name, digest in manifest['input_sha256'].items():
        if sha(RESEARCH / name) != digest:
            raise ValueError('Frozen input changed: ' + name)
    return manifest, receipt['manifest_sha256']


@contextmanager
def lock():
    handle = (HERE / 'run.lock').open('a+b')
    if handle.tell() == 0:
        handle.write(b'0')
        handle.flush()
    handle.seek(0)
    try:
        if os.name == 'nt':
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        handle.close()
