"""Second-order Taylor boundary diagnostic for Davenport--Heilbronn (Python 3).

Centre derivatives are evaluated with high-precision mpmath and the quadratic
model is explicitly labelled NONCERTIFIED: derivative suprema and the
third-order remainder are not interval proved.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import mpmath as mp


def dh(s: mp.mpc) -> mp.mpc:
    kappa = (mp.sqrt(10 - 2 * mp.sqrt(5)) - 2) / (mp.sqrt(5) - 1)
    coeff = (1, kappa, -kappa, -1, 0)
    return 5 ** (-s) * sum(coeff[r - 1] * mp.zeta(s, mp.mpf(r) / 5) for r in range(1, 6))


def phase_interval(phases: list[float], eps: list[float]) -> tuple[float, float, float, float]:
    unwrapped = [phases[0]]
    for p in phases[1:]:
        q = p
        while q - unwrapped[-1] > math.pi:
            q -= 2 * math.pi
        while q - unwrapped[-1] < -math.pi:
            q += 2 * math.pi
        unwrapped.append(q)
    deltas = []
    for i in range(len(unwrapped)):
        q = phases[(i + 1) % len(phases)]
        while q - unwrapped[i] > math.pi:
            q -= 2 * math.pi
        while q - unwrapped[i] < -math.pi:
            q += 2 * math.pi
        deltas.append(q - unwrapped[i])
    nominal = float(sum(deltas))
    uncertainty = float(2 * sum(eps))
    return nominal, uncertainty, (nominal - uncertainty) / (2 * math.pi), (nominal + uncertainty) / (2 * math.pi)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--dps", type=int, default=50)
    ap.add_argument("--delta", type=str, default="1e-4", help="finite-difference step for diagnostic derivatives")
    args = ap.parse_args()
    mp.mp.dps = args.dps
    delta = mp.mpf(args.delta)
    src = json.loads(args.input.read_text(encoding="utf-8"))
    rows = src.get("segments", [])
    if not isinstance(rows, list) or not rows:
        raise ValueError("input must contain a non-empty segments list")
    details = []
    phases = []
    eps = []
    for row in src["segments"]:
        z = mp.mpc(mp.mpf(row["centre"][0]), mp.mpf(row["centre"][1]))
        h = mp.mpf(row["half_length"])
        f = dh(z)
        # Centred finite differences keep this diagnostic tractable for a
        # contour with many segments. They are deliberately not a certificate.
        fm, fp = dh(z - delta), dh(z + delta)
        d1 = (fp - fm) / (2 * delta)
        d2 = (fp - 2 * f + fm) / (delta * delta)
        centre_abs = abs(f)
        first_radius = mp.mpf(str(row.get("derivative_abs_upper", abs(d1)))) * h
        second_radius = abs(d1) * h + mp.mpf("0.5") * abs(d2) * h * h
        first_eps = mp.asin(min(mp.mpf("0.999999999999"), first_radius / centre_abs))
        second_eps = mp.asin(min(mp.mpf("0.999999999999"), second_radius / centre_abs))
        phases.append(float(mp.arg(f)))
        eps.append(float(second_eps))
        details.append({"index": int(row["index"]), "centre_abs": float(centre_abs), "d1_abs": float(abs(d1)), "d2_abs": float(abs(d2)), "half_length": float(h), "first_order_radius": float(first_radius), "second_order_radius": float(second_radius), "radius_ratio_second_over_first": float(second_radius / first_radius) if first_radius else None, "first_order_lower": float(centre_abs - first_radius), "second_order_lower": float(centre_abs - second_radius), "first_order_phase_eps": float(first_eps), "second_order_phase_eps": float(second_eps)})
    nominal, uncertainty, lo, hi = phase_interval(phases, eps)
    first_uncertainty = 2 * sum(x["first_order_phase_eps"] for x in details)
    result = {"status": "NONCERTIFIED_SECOND_ORDER_TAYLOR_DIAGNOSTIC", "input": str(args.input), "dps": args.dps, "segments": len(details), "positive_second_order_lower": sum(x["second_order_lower"] > 0 for x in details), "minimum_first_order_lower": min(x["first_order_lower"] for x in details), "minimum_second_order_lower": min(x["second_order_lower"] for x in details), "maximum_second_order_radius": max(x["second_order_radius"] for x in details), "phase_uncertainty_radius_first_order": first_uncertainty, "phase_uncertainty_radius_second_order": uncertainty, "phase_uncertainty_reduction_fraction": 1 - uncertainty / first_uncertainty if first_uncertainty else None, "nominal_winding": nominal / (2 * math.pi), "winding_interval_second_order": [lo, hi], "interpretation": "Second-order radii use mpmath centre derivatives and a sampled quadratic model. They are a refinement diagnostic only: derivative suprema and the third-order remainder are not interval-certified.", "segments_detail": details}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "segments", "positive_second_order_lower", "minimum_second_order_lower", "phase_uncertainty_reduction_fraction", "winding_interval_second_order")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
