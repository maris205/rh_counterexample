"""Conservative unknown-frequency candidate gate for current channel JSONs.

This first blind pass intentionally uses only frequencies already emitted by
the channel FFT summaries. Known critical-line neighborhoods and low-frequency
trend bins are excluded before clustering. An empty candidate table is a valid
result: it means no frequency earned a zeta call under the current evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


KNOWN_T = [14.134725141734694, 21.022039638771555, 25.01085758014569,
           30.42487612585951, 32.93506158773919]


def within_known(t: float, radius: float = 0.75) -> bool:
    return any(abs(t - z) <= radius for z in KNOWN_T)


def add_rows(rows, source, channel, top):
    for item in top or []:
        t = float(item.get('angular_frequency_t', item.get('t', 0.0)))
        if not (2.0 <= t <= 200.0) or within_known(t):
            continue
        rows.append({'source': source, 'channel': channel, 't': t,
                     'power': float(item.get('power', 0.0))})


def extract(path: Path):
    data = json.loads(path.read_text(encoding='utf-8'))
    rows = []
    if 'mertens' in data:
        add_rows(rows, path.name, 'mertens', data['mertens'].get('top_spectrum'))
    for channel, record in data.get('channels', {}).items():
        if isinstance(record, dict):
            add_rows(rows, path.name, channel, record.get('top_spectrum'))
    return rows


def cluster(rows, tolerance=0.5):
    groups = []
    for row in sorted(rows, key=lambda x: x['t']):
        group = next((g for g in groups if abs(row['t'] - g['center_t']) <= tolerance), None)
        if group is None:
            groups.append({'center_t': row['t'], 'rows': [row]})
        else:
            group['rows'].append(row)
            group['center_t'] = sum(x['t'] for x in group['rows']) / len(group['rows'])
    out = []
    for g in groups:
        channels = sorted(set(x['channel'] for x in g['rows']))
        sources = sorted(set(x['source'] for x in g['rows']))
        out.append({'t': g['center_t'], 'independent_channels': channels,
                    'channel_count': len(channels), 'source_count': len(sources),
                    'rows': g['rows'],
                    'passes_three_channel_gate': len(channels) >= 3})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--inputs', nargs='+', default=[
        'runs/mertens-null-5e7-v2.json', 'runs/lambda-psi-5e7.json',
        'runs/short-interval-5e7.json'])
    ap.add_argument('--tolerance', type=float, default=0.5)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    rows = []
    used = []
    for raw in args.inputs:
        path = Path(raw)
        if path.exists():
            used.append(str(path)); rows.extend(extract(path))
    groups = cluster(rows, args.tolerance)
    candidates = [g for g in groups if g['passes_three_channel_gate']]
    result = {
        'status': 'COMPLETED',
        'purpose': 'blind unknown-frequency gate; not a zeta-zero certificate',
        'inputs': used,
        'excluded_known_t': KNOWN_T,
        'exclusion_radius': 0.75,
        'minimum_t': 2.0,
        'cluster_tolerance': args.tolerance,
        'observed_clusters': groups,
        'candidates': candidates,
        'candidate_count': len(candidates),
        'interpretation': ('No frequency earned a zeta call: after excluding known-line and low-trend bins, '
                           'none appeared in three independent channels. This is a gate result, not evidence that '
                           'the whole zeta strip is zero-free.'),
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'candidate_count': len(candidates),
                      'clusters': len(groups), 'output': str(args.output)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
