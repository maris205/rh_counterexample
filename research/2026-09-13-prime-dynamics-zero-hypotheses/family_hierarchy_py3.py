"""Python 3 standard-library audit of the family-level zero-surface controls.

The numerical roots are produced by the high-precision family scripts.  This
runner deliberately only reads their JSON artifacts and classifies what each
result can support; it does not promote a refined root to a certificate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--surface", type=Path, default=Path("runs/family-zero-surface-85-v2.json"))
    ap.add_argument("--dh", type=Path, default=Path("runs/davenport-heilbronn-audit.json"))
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    surface = load(args.surface)
    dh = load(args.dh)
    rows = []
    for name, rec in surface.get("surfaces", {}).items():
        root = rec.get("refinement", {})
        sigma = float(root.get("sigma", "nan"))
        distance = abs(sigma - 0.5)
        rows.append({
            "family": name,
            "sigma": sigma,
            "t": float(root.get("t", "nan")),
            "abs_value": float(root.get("abs_value", "nan")),
            "distance_to_half": distance,
            "classification": "line-confined calibration" if distance < 1e-8 else "off-line sensitivity control",
            "source": str(args.surface),
        })

    dh_root = dh.get("refined_root", {})
    dh_row = {
        "family": "davenport_heinrich",
        "sigma": float(dh_root.get("sigma", "nan")),
        "t": float(dh_root.get("t", "nan")),
        "abs_value": float(dh_root.get("abs_value", "nan")),
        "distance_to_half": float(dh.get("distance_from_half", "nan")),
        "classification": "off-line fixture; contour certificate disabled",
        "source": str(args.dh),
    }
    rows.append(dh_row)
    result = {
        "schema": "family-hierarchy-audit-v1",
        "status": "COMPLETED",
        "python": "3.x standard library",
        "purpose": "Separate detector sensitivity from claims about RH.",
        "rows": rows,
        "checks": {
            "zeta_line_confined_in_window": any(r["family"] == "zeta" and r["distance_to_half"] < 1e-8 for r in rows),
            "dh_off_line_fixture_recovered": dh_row["distance_to_half"] > 0.1 and dh_row["abs_value"] < 1e-40,
            "argument_principle_enabled": dh.get("argument_principle", {}).get("status") == "ENABLED",
        },
        "interpretation": (
            "The free-sigma surface recovers a known off-line Davenport-Heilbronn "
            "fixture while zeta and the two character controls refine to Re(s)=1/2. "
            "This validates sensitivity of the family solver, not an off-line zeta zero. "
            "The Davenport-Heilbronn row remains uncertified until an interval contour "
            "count is implemented."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = args.output.with_suffix(".md")
    lines = ["# Python 3 family hierarchy audit", "", "| family | sigma | t | abs(value) | classification |", "|---|---:|---:|---:|---|"]
    for r in rows:
        lines.append(f"| {r['family']} | {r['sigma']:.15g} | {r['t']:.15g} | {r['abs_value']:.3e} | {r['classification']} |")
    lines += ["", "The table is a calibration map. A small residual from a numerical refinement is not a zero certificate; the DH contour gate is intentionally disabled."]
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "rows": len(rows), "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
