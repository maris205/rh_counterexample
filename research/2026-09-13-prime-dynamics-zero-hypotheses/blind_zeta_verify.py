"""Command-line wrapper for the executable blind zeta verification gate."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from blind_zeta_verifier import verify


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--candidates', '--input', dest='input', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--dps', type=int, default=80)
    ap.add_argument('--box-radius', default='1e-7')
    ap.add_argument('--rectangle-dps', type=int, default=None)
    ap.add_argument('--rectangle-seconds', type=float, default=30.0)
    args = ap.parse_args()
    result = verify(args.input, args.output, dps=args.dps,
                    box_radius=args.box_radius,
                    rectangle_dps=args.rectangle_dps,
                    rectangle_seconds=args.rectangle_seconds)
    print(json.dumps({'status': result['status'],
                      'candidate_count': result['candidate_count'],
                      'certified_off_line_zero': result['certified_off_line_zero'],
                      'output': str(args.output)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
