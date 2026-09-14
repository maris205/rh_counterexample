"""Combine path nonzero and shared-endpoint branch diagnostics for DH."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--derivative', type=Path, required=True)
    ap.add_argument('--phase', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    d = json.loads(args.derivative.read_text(encoding='utf-8'))
    p = json.loads(args.phase.read_text(encoding='utf-8'))
    same_edge = d['configuration']['edge_points'] == p['configuration']['edge_points']
    same_box = all(d['configuration'][k] == p['configuration'][k] for k in ('sigma','t','ds','dt'))
    positive = int(d['summary']['segments_positive_taylor_lower'])
    total = int(d['boundary_segments'])
    branch_ok = p['minimum_branch_margin'] > 0.1 and p['branch_steps_near_ambiguity'] == 0
    result = {
        'status': 'NONCERTIFIED_COMBINED_CONTOUR_DIAGNOSTIC',
        'inputs': {'derivative': str(args.derivative), 'phase': str(args.phase)},
        'same_configuration': same_edge and same_box,
        'path_segments': total,
        'path_segments_with_positive_taylor_lower': positive,
        'all_path_disks_exclude_zero': positive == total,
        'shared_endpoint_nominal_winding': p['nominal_winding'],
        'shared_endpoint_branch_margin': p['minimum_branch_margin'],
        'branch_stable': branch_ok,
        'combined_diagnostic_pass': same_edge and same_box and positive == total and branch_ok and abs(p['nominal_winding'] - 1) < 1e-8,
        'interpretation': 'Same-rectangle Taylor path and shared-endpoint branch diagnostics agree. This remains non-rigorous until derivative/remainder bounds and in-segment phase continuity are certified.'
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'combined_diagnostic_pass': result['combined_diagnostic_pass'], 'output': str(args.output)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
