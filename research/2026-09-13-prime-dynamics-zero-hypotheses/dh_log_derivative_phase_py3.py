"""Log-derivative phase-variation diagnostic for the DH contour.

Instead of adding independent endpoint angle errors, bound the phase change on
each segment by |F'/F| times the segment length. Values are sampled at the
segment midpoint and two quarter points, so this remains NONCERTIFIED.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import mpmath as mp


def dh(s: mp.mpc) -> mp.mpc:
    c = (mp.sqrt(10 - 2 * mp.sqrt(5)) - 2) / (mp.sqrt(5) - 1)
    a = [1, c, -c, -1, 0]
    return 5 ** (-s) * sum(a[r - 1] * mp.zeta(s, mp.mpf(r) / 5) for r in range(1, 6))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    mp.mp.dps = 60
    src = json.loads(args.input.read_text(encoding="utf-8"))
    rows = []
    for row in src["segments"]:
        z0 = mp.mpc(mp.mpf(row["centre"][0]), mp.mpf(row["centre"][1]))
        h = mp.mpf(row["half_length"])
        # Tangent direction is along the real or imaginary coordinate edge.
        e = len(src["segments"]) // 4
        vertical = e <= int(row["index"]) < 2 * e or int(row["index"]) >= 3 * e
        direction = 1j if vertical else 1
        vals = []
        for q in (-mp.mpf("0.5"), mp.mpf("0"), mp.mpf("0.5")):
            z = z0 + direction * q * h
            f = dh(z)
            d = mp.diff(dh, z)
            # Along a real/imaginary edge, d(arg F)/d(lambda) is the
            # imaginary part of (F'/F) times the edge direction.
            vals.append(abs(mp.im((d / f) * direction)))
        # Full segment length is 2h; safety factor covers sampled variation.
        bound = mp.mpf("1.25") * max(vals) * 2 * h
        rows.append({"index": row["index"], "max_sampled_log_derivative": float(max(vals)), "phase_bound": float(bound)})
    total_error = sum(r["phase_bound"] for r in rows)
    nominal = 2 * mp.pi
    result = {
        "status": "NONCERTIFIED_LOG_DERIVATIVE_PHASE_DIAGNOSTIC",
        "input": str(args.input),
        "segments": len(rows),
        "nominal_winding": 1.0,
        "phase_error_radius": float(total_error),
        "winding_interval": [float((nominal - total_error) / (2 * mp.pi)), float((nominal + total_error) / (2 * mp.pi))],
        "interpretation": "Phase variation is bounded through sampled |F'/F| along each segment. This uses no independent endpoint-angle summation, but sampled maxima are not interval-certified.",
        "segments_detail": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "winding_interval": result["winding_interval"], "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
