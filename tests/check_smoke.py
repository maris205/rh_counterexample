"""Check completed integration output, including independent low-height values."""
import hashlib
import json
from pathlib import Path
import sys

directory = Path(sys.argv[1]) / 'research/2026-09-09-gpu-wide-survey/true_zeta'
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
manifest = read(directory / 'FROZEN_WINDOWS.json')
result = read(directory / 'RESULTS.json')
assert len(manifest['windows']) == 8
assert sum(result['status_counts'].get(s, 0) for s in ('COMPLETED', 'NEEDS_CHECK')) == 8
assert result['completed_objective_evaluations'] == 256
for ident, digest in result['window_sha256'].items():
    path = directory / 'windows' / (ident + '.json')
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    row = read(path)
    assert row['center_check']['independent_library_validation']
    assert row['best_check']['independent_library_validation']
    assert row['best_small_box']['certified_zero_free']
    assert not row['certified_off_line_zero']
print('SMOKE_VERIFIED: 8 windows, 256 DE evaluations, independent low-height checks, file hashes')
audit_path = Path(sys.argv[1]) / 'SMOKE_AUDIT.json'
digests = {'results': hashlib.sha256((directory / 'RESULTS.json').read_bytes()).hexdigest(),
           'windows': result['window_sha256']}
if audit_path.exists():
    assert read(audit_path) == digests, 'Completed results changed during resume'
    print('RESUME_VERIFIED: original result and window hashes unchanged')
else:
    audit_path.write_text(json.dumps(digests, indent=2) + '\n', encoding='utf-8')
