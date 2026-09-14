"""Run the fixed pre-registered multi-N blind frequency gate.

The manifest is deliberately data, not command-line options.  The runner reads
only the listed JSON outputs, validates the control q95 floor, and emits every
cluster plus the strict candidate table.  Passing this screen is a heuristic
handoff condition; it is never evidence of an off-critical-line zeta zero.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = Path(__file__).with_name("PREREGISTERED_BLIND_MANIFEST.json")


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_path(data: dict, dotted: str) -> float:
    cur: object = data
    for key in dotted.split(":", 1)[1].split("."):
        if not isinstance(cur, dict) or key not in cur:
            raise KeyError(dotted)
        cur = cur[key]
    return float(cur)


def control_floor(manifest: dict, root: Path) -> tuple[float, list[dict]]:
    values: list[dict] = []
    for ref in manifest["control_policy"]["expected_q95_sources"]:
        path_text, key = ref.split(":", 1)
        path = root / path_text
        data = json.loads(path.read_text(encoding="utf-8"))
        value = get_path(data, ":" + key)
        values.append({"source": ref, "value": value})
    floor = max(x["value"] for x in values)
    expected = float(manifest["control_policy"]["expected_q95_floor"])
    if not math.isclose(floor, expected, rel_tol=1e-12, abs_tol=1e-15):
        raise RuntimeError(f"control q95 changed: manifest={expected} observed={floor}")
    return floor, values


def within_known(t: float, manifest: dict) -> bool:
    radius = float(manifest["known_exclusion_radius"])
    return any(abs(t - float(z)) <= radius for z in manifest["known_ordinates"])


def read_rows(manifest: dict, root: Path) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    used: list[str] = []
    lo, hi = map(float, manifest["t_range"])
    grids = {(int(x["samples"]), float(x["trim"])) for x in manifest["grid_design"]}
    for rel in manifest["observation_inputs"]:
        path = root / rel
        data = json.loads(path.read_text(encoding="utf-8"))
        used.append(rel)
        n = int(data.get("configuration", {}).get("n", 0))
        for rec in data.get("records", []):
            grid = (int(rec.get("samples", -1)), float(rec.get("phase", rec.get("trim", -1))))
            if grid not in grids:
                continue
            channel = str(rec.get("channel", "unknown"))
            for peak in rec.get("peaks", []):
                t, r2 = float(peak.get("t", 0.0)), float(peak.get("r2", 0.0))
                if not (lo <= t <= hi) or within_known(t, manifest):
                    continue
                rows.append({"t": t, "r2": r2, "phase": float(peak.get("phase", 0.0)),
                             "channel": channel, "n": n, "grid": [grid[0], grid[1]], "source": rel})
    return rows, used


def clusters(rows: list[dict], tolerance: float) -> list[list[dict]]:
    groups: list[list[dict]] = []
    for row in sorted(rows, key=lambda x: x["t"]):
        target = next((g for g in groups if abs(row["t"] - sum(x["t"] for x in g) / len(g)) <= tolerance), None)
        if target is None:
            groups.append([row])
        else:
            target.append(row)
    return groups


def resultant(phases: list[float]) -> float:
    if not phases:
        return 0.0
    return abs(sum(complex(math.cos(p), math.sin(p)) for p in phases)) / len(phases)


def summarize(group: list[dict], q95: float, manifest: dict) -> dict:
    channels = sorted({x["channel"] for x in group})
    grids = sorted({(x["n"], x["grid"][0], x["grid"][1]) for x in group})
    scales = sorted({x["n"] for x in group})
    per_channel = {c: max(x["r2"] for x in group if x["channel"] == c) for c in channels}
    min_channel_r2 = min(per_channel.values()) if per_channel else 0.0
    phase_r = resultant([x["phase"] for x in group])
    gates = {
        "channels": len(channels) >= int(manifest["required_independent_channels"]),
        "grids": len(grids) >= int(manifest["required_independent_grids"]),
        "scales": len(scales) >= int(manifest["required_arithmetic_scales"]),
        "control_q95": min_channel_r2 > q95,
        "phase_resultant": phase_r >= float(manifest["phase_resultant_min"]),
    }
    return {"t_mean": sum(x["t"] for x in group) / len(group),
            "t_min": min(x["t"] for x in group), "t_max": max(x["t"] for x in group),
            "row_count": len(group), "channels": channels, "channel_count": len(channels),
            "grids": [list(x) for x in grids], "grid_count": len(grids), "scales": scales,
            "scale_count": len(scales), "per_channel_max_r2": per_channel,
            "min_channel_r2": min_channel_r2, "phase_resultant": phase_r,
            "control_q95": q95, "gates": gates,
            "passes_all_gates": all(gates.values()), "rows": group}


def run(manifest_path: Path, output: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    # .../<repo>/research/<date-dir>/PREREGISTERED_BLIND_MANIFEST.json
    root = manifest_path.parents[2]
    q95, controls = control_floor(manifest, root)
    rows, used = read_rows(manifest, root)
    all_clusters = [summarize(g, q95, manifest) for g in clusters(rows, float(manifest["cluster_tolerance"]))]
    accepted = [x for x in all_clusters if x["passes_all_gates"]]
    result = {"status": "COMPLETED", "purpose": manifest["purpose"],
              "manifest": str(manifest_path), "manifest_sha256": canonical_hash(manifest),
              "configuration": manifest, "observation_inputs_used": used,
              "control_q95": q95, "control_values": controls,
              "row_count": len(rows), "cluster_count": len(all_clusters),
              "clusters": all_clusters, "candidates": accepted,
              "candidate_count": len(accepted),
              "interpretation": "No candidate is a zeta claim. A nonempty table only authorizes independent zeta evaluation under a new audit artifact; an empty table is a valid preregistered negative result."}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.manifest, args.output)
    print(json.dumps({"status": result["status"], "candidate_count": result["candidate_count"],
                      "cluster_count": result["cluster_count"], "manifest_sha256": result["manifest_sha256"],
                      "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
