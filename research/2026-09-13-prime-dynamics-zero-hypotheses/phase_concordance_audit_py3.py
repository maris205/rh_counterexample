"""Classify legacy peaks without pooling incomparable phases.

Old pooled phase resultants are withdrawn as candidate-rejection evidence.
Only same-channel, exactly same-frequency phases have a descriptive resultant.
Legacy fits use the common u=0 phase origin; peak lists cannot evaluate a
joint holdout gate.
"""
import argparse
import json
import math
from pathlib import Path
from known_ordinates import known_ordinates


def audit(path, target=37.5, tol=.15):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    known = known_ordinates(max(0., target - tol), target + tol)
    hits, groups = [], {}
    for rec in data.get("records", []):
        for peak in rec.get("peaks", []):
            if abs(peak["t"] - target) > tol:
                continue
            matches = [t for t in known if abs(peak["t"] - t) <= .35]
            row = {"channel": rec["channel"], "samples": rec["samples"], "trim": rec["phase"],
                   **peak, "matched_known_ordinates": matches,
                   "classification": "KNOWN_LINE_NEIGHBORHOOD" if matches else "UNCLASSIFIED_FINITE_PEAK"}
            hits.append(row)
            groups.setdefault((rec["channel"], peak["t"]), []).append(row)
    phase_groups = []
    for (channel, t), rows in groups.items():
        grids = {(r["samples"], r["trim"]) for r in rows}
        resultant = None
        if len(grids) >= 2:
            resultant = abs(sum(complex(math.cos(r["phase"]), math.sin(r["phase"])) for r in rows) / len(rows))
        phase_groups.append({"channel": channel, "t": t, "u_origin": 0., "grid_count": len(grids),
                             "descriptive_resultant": resultant, "significance_test": "NOT_EVALUATED"})
    return {"source": str(Path(path).resolve()), "n": data.get("batch_scale_n"), "hits": hits,
            "same_channel_same_frequency_groups": phase_groups,
            "legacy_pooled_phase_resultant": "WITHDRAWN_AS_REJECTION_EVIDENCE",
            "gate_status": "NOT_EVALUATED", "eligible_candidate_count": None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--target", type=float, default=37.5)
    ap.add_argument("--tolerance", type=float, default=.15)
    args = ap.parse_args()
    if args.output.exists():
        raise SystemExit("preserve existing audit: choose a new output path")
    rows = [audit(p, args.target, args.tolerance) for p in args.inputs]
    out = {"schema": "phase-concordance-correction-v2", "status": "COMPLETED", "rows": rows,
           "gate_status": "NOT_EVALUATED", "eligible_candidate_count": None,
           "interpretation": "Known-line neighborhood classification does not prove the origin of every peak. No mixed-frequency/cross-channel phase vote or unmatched q95 comparison is valid."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    args.output.with_suffix(".md").write_text("# Correction of legacy phase audit\n\n"
        "The pooled 0.614/0.334 phase results are withdrawn as rejection evidence. "
        "Channel-specific phases need not agree; frequencies 37.5 and 37.6 cannot be pooled. "
        "Both lie near known critical-line ordinate 37.58617815882567. "
        "Peak-list data alone cannot evaluate the joint held-out gate.\n", encoding="utf-8")
    print(json.dumps({"status": "COMPLETED", "gate_status": "NOT_EVALUATED", "output": str(args.output)}))


if __name__ == "__main__":
    main()
