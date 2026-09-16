"""Prime-density-preserving spectral power calibration.

Each synthetic indicator remains binary and preserves the observed prime count
in every fixed log bin.  Lambda/psi is regenerated from that indicator.  The
Mertens array is held fixed and is explicitly excluded from claims about this
local-prime calibration.
"""
import argparse
import hashlib
import json
from pathlib import Path
import traceback

import common_spectrum_v2 as core
import common_spectrum_v2_batch_py3 as batch
from short_interval_dynamics import prime_indicator_linear_sieve
from known_ordinates import known_mask
import numpy as np


def weighted_indicator(indicator, t, epsilon, phase, bins, rng):
    n = len(indicator) - 1
    out = np.zeros_like(indicator)
    edges = np.unique(np.rint(np.geomspace(2, n + 1, bins + 1)).astype(int))
    edges[0], edges[-1] = 2, n + 1
    for lo, hi in zip(edges[:-1], edges[1:]):
        slots = np.arange(int(lo), int(hi), dtype=np.int64)
        k = int(np.count_nonzero(indicator[slots]))
        if k == 0:
            continue
        u = np.log(slots.astype(float))
        weight = np.exp(epsilon * np.cos(t * u + phase) - epsilon)
        out[rng.choice(slots, size=k, replace=False, p=weight / weight.sum())] = 1
    return out


def lambda_from_indicator(indicator):
    n = len(indicator) - 1
    out = np.zeros(n + 1, dtype=float)
    for p in np.flatnonzero(indicator[2:]) + 2:
        lp = np.log(float(p))
        power = int(p)
        while power <= n:
            out[power] = lp
            power *= int(p)
    return out


def train_gain(u, y, t, origin):
    base, full = core.designs(u, t, origin)
    b0 = np.linalg.lstsq(base, y, rcond=None)[0]
    b1 = np.linalg.lstsq(full, y, rcond=None)[0]
    e0 = float(np.sum((y - base @ b0) ** 2))
    e1 = float(np.sum((y - full @ b1) ** 2))
    return (e0 - e1) / e0 if e0 > 1e-20 else -1e6


def short_only(cells, frequencies, origin, target):
    anchor = min(cells, key=lambda c: (c.n, c.grid, c.split))
    boundary = min(float(c.u[c.cut]) for c in cells)
    support = anchor.support_end_u if anchor.support_end_u is not None else anchor.u
    prefix = support < boundary
    scores = [(float(t), train_gain(anchor.u[prefix], anchor.y[prefix, 3], float(t), origin)) for t in frequencies]
    scores.sort(key=lambda row: (-row[1], row[0]))
    selected = [row for row in scores[:3]]
    rows = []
    for t, training_score in selected:
        gains = []
        for cell in cells:
            end = cell.cut if cell.train_end is None else cell.train_end
            g, _ = core.prediction_gains(cell.u, cell.y[:, 3:4], cell.cut, t, origin, end)
            gains.append(float(g[0]))
        rows.append({"t": t, "training_score": training_score, "min_holdout_gain": min(gains),
                     "positive_all_cells": all(g > 0 for g in gains)})
    matching = [row for row in rows if abs(row["t"] - target) <= .25]
    return {"selected": rows, "target_selected": bool(matching),
            "target_positive": any(row["positive_all_cells"] for row in matching)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    outdir = args.output_dir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    config = {"scales": [100000, 300000], "grids": [[192, 0.0], [256, .08]],
              "splits": [.55, .75], "theta": .525, "x_min": 100, "bins": 128,
              "frequencies": [18.0, 37.58617815882567], "epsilons": [.25, .5, 1., 2.],
              "phase_seeds": [0, 1, 2, 3], "scan_min": 4., "scan_max": 40.,
              "scan_step": .25, "known_margin": .35, "top_k": 3,
              "scope": "binary prime-density preserving local calibration; Mertens held fixed; no full joint gate"}
    manifest = batch.manifest_for(config)
    manifest["source_sha256"][Path(__file__).name] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest.pop("run_id")
    manifest["run_id"] = batch.fingerprint(manifest)
    with batch.run_lock(outdir):
        batch.check_manifest(outdir, manifest)
        base = core.arithmetic_coefficients(max(config["scales"]))
        indicator, _ = prime_indicator_linear_sieve(max(config["scales"]))
        origin = float(np.log(100.))
        scan = np.arange(config["scan_min"], config["scan_max"] + .125, config["scan_step"])
        discovery = scan[~known_mask(scan, config["known_margin"])]
        cases = [("baseline", None, 0., 0)] + [(f"t{t:.12g}-e{e:g}-s{s}", t, e, s)
                  for t in config["frequencies"] for e in config["epsilons"] for s in config["phase_seeds"]]
        results = []
        for key, t, epsilon, seed in cases:
            path = outdir / f"task-{key}.json"
            row = batch.completed_task(path, manifest["run_id"], key)
            if row is None:
                try:
                    if t is None:
                        row = {"status": "COMPLETED", "injected": False}
                    else:
                        phase = float(np.random.default_rng(20260916 + seed).uniform(-np.pi, np.pi))
                        syn_indicator = weighted_indicator(indicator, t, epsilon, phase, config["bins"], np.random.default_rng(8128 + seed))
                        syn = dict(base)
                        syn["lambda"] = lambda_from_indicator(syn_indicator)
                        syn["prime"] = syn_indicator.astype(float)
                        cells = core.build_cells(syn, config["scales"], config["grids"], config["splits"], config["theta"], config["x_min"])
                        result = core.evaluate(cells, discovery, origin, config["top_k"])
                        local = short_only(cells, discovery, origin, t)
                        matches = [c for c in result["candidates"] if abs(c["t"] - t) <= .25]
                        row = {"status": "COMPLETED", "injected": True, "t": t, "epsilon": epsilon,
                               "phase_seed": seed, "phase": phase,
                               "prime_count_original": int(indicator.sum()), "prime_count_synthetic": int(syn_indicator.sum()),
                               "joint_discovery_recovered": bool(matches),
                               "joint_discovery_positive": any(c["positive_in_every_primary_cell"] for c in matches),
                               "joint_result": result, "short_only_result": local}
                    json.dumps(row, allow_nan=False)
                except Exception as exc:
                    traceback.print_exc()
                    row = {"status": "FAILED", "error": repr(exc)}
                row.update(run_id=manifest["run_id"], task_id=key)
                batch.atomic_json(path, row)
            results.append(row)
            batch.atomic_json(outdir / "progress.json", {"status": "RUNNING", "completed_count": sum(r["status"] == "COMPLETED" for r in results),
                              "failed_count": sum(r["status"] == "FAILED" for r in results), "total_tasks": len(cases), "last_task": key, "updated": batch.now()})
        curves = []
        for t in config["frequencies"]:
            for e in config["epsilons"]:
                rows = [r for r in results if r.get("t") == t and r.get("epsilon") == e]
                locals_ = [r["short_only_result"] for r in rows]
                curves.append({"t": t, "epsilon": e, "trials": len(rows),
                               "joint_recovery": sum(r["joint_discovery_recovered"] for r in rows),
                               "joint_positive": sum(r["joint_discovery_positive"] for r in rows),
                               "short_recovery": sum(r["target_selected"] if "target_selected" in r else x["target_selected"] for r, x in zip(rows, locals_)),
                               "short_positive": sum(x["target_positive"] for x in locals_)})
        failed = sum(r["status"] == "FAILED" for r in results)
        summary = {"schema": "prime-consistent-power-v1", "status": "COMPLETED_WITH_FAILURES" if failed else "COMPLETED",
                   "run_id": manifest["run_id"], "configuration": config, "completed_count": len(results) - failed,
                   "failed_count": failed, "total_tasks": len(cases), "curves": curves,
                   "candidate_count": None, "gate_status": "NOT_EVALUATED",
                   "interpretation": "Synthetic indicators remain binary and preserve per-log-bin prime counts; lambda/psi is regenerated from them. Mertens is held fixed, so this is a local-prime/global-psi calibration rather than a three-family joint test. It is not a prime probability model, zeta candidate, or interval certificate."}
        batch.atomic_json(outdir / "summary.json", summary)
        batch.atomic_json(outdir / "progress.json", {k: summary[k] for k in ("status", "completed_count", "failed_count", "total_tasks")})
        lines = ["# Prime-consistent local calibration", "", summary["interpretation"], "",
                 "| t | epsilon | trials | joint selected | joint positive | short selected | short positive |", "|---:|---:|---:|---:|---:|---:|---:|"]
        lines += [f"| {r['t']} | {r['epsilon']} | {r['trials']} | {r['joint_recovery']}/{r['trials']} | {r['joint_positive']}/{r['trials']} | {r['short_recovery']}/{r['trials']} | {r['short_positive']}/{r['trials']} |" for r in curves]
        (outdir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(json.dumps({k: summary[k] for k in ("status", "completed_count", "failed_count", "candidate_count")}))
        raise SystemExit(bool(failed))


if __name__ == "__main__":
    main()
