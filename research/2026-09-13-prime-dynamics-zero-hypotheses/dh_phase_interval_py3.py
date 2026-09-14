"""Accumulate phase intervals from analytic-derivative Taylor disks.

For each ordered boundary segment, a disk radius L*h is combined with the
high-precision centre value.  The angular uncertainty is bounded by
asin(radius/|centre|).  This is an interval phase diagnostic; its rigor is
limited by the derivative/remainder assumptions in the input JSON.
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
    data = json.loads(args.input.read_text(encoding="utf-8"))
    mp.mp.dps = 80
    rows = data["segments"]
    phases = []
    eps = []
    disk_rows = []
    for row in rows:
        z = mp.mpc(mp.mpf(row["centre"][0]), mp.mpf(row["centre"][1]))
        value = dh(z)
        radius = mp.mpf(str(row["derivative_abs_upper"])) * mp.mpf(row["half_length"])
        modulus = abs(value)
        ratio = radius / modulus
        if ratio >= 1:
            raise RuntimeError(f"Taylor disk reaches zero at segment {row['index']}: ratio={ratio}")
        angle_eps = mp.asin(ratio)
        phases.append(float(mp.arg(value)))
        eps.append(float(angle_eps))
        disk_rows.append({"index": row["index"], "centre_abs": float(modulus), "disk_radius": float(radius), "angle_half_width": float(angle_eps), "ratio": float(ratio)})
    unwrapped = [phases[0]]
    for p in phases[1:]:
        q = p
        while q - unwrapped[-1] > math.pi:
            q -= 2 * math.pi
        while q - unwrapped[-1] < -math.pi:
            q += 2 * math.pi
        unwrapped.append(q)
    deltas = []
    uncertainties = []
    for i in range(len(unwrapped)):
        j = (i + 1) % len(unwrapped)
        q = phases[j]
        while q - unwrapped[i] > math.pi:
            q -= 2 * math.pi
        while q - unwrapped[i] < -math.pi:
            q += 2 * math.pi
        deltas.append(q - unwrapped[i])
        uncertainties.append(eps[i] + eps[j])
    nominal = sum(deltas)
    uncertainty = sum(uncertainties)
    lo, hi = (nominal - uncertainty) / (2 * math.pi), (nominal + uncertainty) / (2 * math.pi)
    result = {
        "status": "NONCERTIFIED_PHASE_INTERVAL_DIAGNOSTIC",
        "input": str(args.input),
        "segments": len(rows),
        "nominal_phase_change": nominal,
        "phase_uncertainty_radius": uncertainty,
        "winding_interval": [lo, hi],
        "nominal_winding": nominal / (2 * math.pi),
        "all_disks_exclude_zero": all(x["ratio"] < 1 for x in disk_rows),
        "maximum_disk_to_center_ratio": max(x["ratio"] for x in disk_rows),
        "interpretation": "The interval winding diagnostic uses analytic-derivative Taylor disks. It is not a rigorous certificate until the derivative/remainder bounds are independently proved as complex interval bounds.",
        "segments_detail": disk_rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "winding_interval": result["winding_interval"], "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
