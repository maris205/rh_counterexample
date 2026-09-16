"""Fixed-frequency transfer diagnostics on new Euler-model phase designs.

No frequency/threshold selection or discovery claims. Paired differences use
an exact unit-weight model available only in this synthetic experiment.
"""
import argparse
import hashlib
import json
from pathlib import Path
import traceback
import numpy as np
import common_spectrum_v2_batch_py3 as batch
import common_spectrum_v2 as core
import euler_coupled_batch_py3 as euler


def fit(u, y, end, cut, t, beta, origin):
    v = u - origin
    baseline = np.column_stack((np.ones(len(u)), v))
    envelope = np.exp(beta * v)
    full = np.column_stack((baseline, envelope*np.cos(t*v), envelope*np.sin(t*v)))
    b0 = np.linalg.lstsq(baseline[:end], y[:end], rcond=None)[0]
    b1, _, rank, singular = np.linalg.lstsq(full[:end], y[:end], rcond=None)
    err0 = float(np.sum((y[cut:]-baseline[cut:]@b0)**2))
    err1 = float(np.sum((y[cut:]-full[cut:]@b1)**2))
    train0 = float(np.sum((y[:end]-baseline[:end]@b0)**2))
    train1 = float(np.sum((y[:end]-full[:end]@b1)**2))
    if rank != 4 or min(err0, train0) <= 1e-20:
        return {"status": "INVALID", "rank": int(rank), "gain": None, "train_gain": None}
    return {"status": "VALID", "gain": (err0-err1)/err0, "train_gain": (train0-train1)/train0,
            "baseline_holdout_sse": err0, "model_holdout_sse": err1,
            "coefficients": b1.tolist(), "tone_phase_at_origin": float(np.arctan2(-b1[3], b1[2])),
            "tone_amplitude_at_origin": float(np.hypot(b1[2], b1[3])),
            "condition_number": float(singular[0]/singular[-1])}


def run(outdir):
    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    cfg = {"scales": [30000, 100000], "grids": [[192, 0.], [256, .08]], "splits": [.55, .75],
           "theta": .525, "x_min": 100, "frequencies": [18., 27.], "amplitudes": [.1, .3],
           "phase_seeds": [2, 3, 4, 5], "betas": [0., .2625, .5],
           "views": ["full", "paired_difference"], "origin": "log(100)",
           "scope": "fixed-frequency per-channel model diagnosis; all comparisons reported, no promotion",
           "envelope_rationale": "0 original; .5 cumulative sqrt-x normalization stress; theta/2 short-window sqrt-h stress. No justified common Mertens envelope assumed.",
           "paired_baseline": "exact unit-weight reference; not available for unknown signals in real data"}
    manifest = batch.manifest_for(cfg)
    for name in (Path(__file__).name, "euler_coupled_batch_py3.py"):
        manifest["source_sha256"][name] = hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
    manifest.pop("run_id")
    manifest["run_id"] = batch.fingerprint(manifest)
    with batch.run_lock(outdir):
        batch.check_manifest(outdir, manifest)
        struct = euler.structure(max(cfg["scales"]))
        primes = struct[1]
        _, ordinary = euler.coefficients(struct, np.ones(len(primes)))
        reference = core.build_cells(ordinary, cfg["scales"], cfg["grids"], cfg["splits"], cfg["theta"], cfg["x_min"])
        tasks = [(t, amp, seed) for t in cfg["frequencies"] for amp in cfg["amplitudes"] for seed in cfg["phase_seeds"]]
        completed = []
        for t, amp, seed in tasks:
            key = f"t{t:g}-a{amp:g}-seed{seed}"
            path = outdir/f"task-{key}.json"
            row = batch.completed_task(path, manifest["run_id"], key)
            if row is None:
                try:
                    phase = float(np.random.default_rng(20260916+seed).uniform(-np.pi, np.pi))
                    _, source = euler.coefficients(struct, 1+amp*np.cos(t*np.log(primes)+phase))
                    cells = core.build_cells(source, cfg["scales"], cfg["grids"], cfg["splits"], cfg["theta"], cfg["x_min"])
                    records = []
                    for cell, ref in zip(cells, reference):
                        assert cell.support_end_u[cell.train_end-1] < cell.u[cell.cut]
                        for view in cfg["views"]:
                            values = cell.y if view == "full" else cell.y-ref.y
                            for ci, channel in enumerate(core.CHANNELS):
                                for beta in cfg["betas"]:
                                    records.append({"cell": cell.key, "channel": channel, "view": view, "beta": beta,
                                        "train_support_max": float(cell.support_end_u[cell.train_end-1]),
                                        "holdout_min": float(cell.u[cell.cut]),
                                        "train_rms": float(np.sqrt(np.mean(values[:cell.train_end,ci]**2))),
                                        "holdout_rms": float(np.sqrt(np.mean(values[cell.cut:,ci]**2))),
                                        **fit(cell.u, values[:,ci], cell.train_end, cell.cut, t, beta, np.log(cfg["x_min"]))})
                    row = {"status": "COMPLETED", "t": t, "amplitude": amp, "phase_seed": seed, "phase": phase, "records": records}
                    json.dumps(row, allow_nan=False)
                except Exception as exc:
                    traceback.print_exc()
                    row = {"status": "FAILED", "error": repr(exc)}
                row.update(task_id=key, run_id=manifest["run_id"])
                batch.atomic_json(path, row)
            completed.append(row)
            batch.atomic_json(outdir/"progress.json", {"status": "RUNNING", "completed_count": sum(r["status"]=="COMPLETED" for r in completed),
                "failed_count": sum(r["status"]=="FAILED" for r in completed), "total_tasks": len(tasks), "last_task": key, "updated": batch.now()})
        aggregate = []
        for view in cfg["views"]:
            for channel in core.CHANNELS:
                for beta in cfg["betas"]:
                    groups = [[r for r in task["records"] if r["view"]==view and r["channel"]==channel and r["beta"]==beta]
                              for task in completed if task["status"]=="COMPLETED"]
                    valid = [r for group in groups for r in group if r["status"]=="VALID"]
                    aggregate.append({"view": view, "channel": channel, "beta": beta, "valid_cells": len(valid),
                        "invalid_cells": sum(len(g) for g in groups)-len(valid),
                        "positive_cells": sum(r["gain"]>0 for r in valid), "designs": len(groups),
                        "positive_all_cells_designs": sum(len(g)==8 and all(r["status"]=="VALID" and r["gain"]>0 for r in g) for g in groups),
                        "median_gain": float(np.median([r["gain"] for r in valid])) if valid else None,
                        "median_train_gain": float(np.median([r["train_gain"] for r in valid])) if valid else None})
        failed = sum(r["status"]=="FAILED" for r in completed)
        summary = {"status": "COMPLETED_WITH_FAILURES" if failed else "COMPLETED", "run_id": manifest["run_id"], "configuration": cfg,
            "completed_count": len(completed)-failed, "failed_count": failed, "total_tasks": len(tasks), "aggregate": aggregate,
            "candidate_count": None, "gate_status": "DIAGNOSTIC_ONLY", "interpretation": "New phases on previously used arithmetic scales, not independent arithmetic replication. Frequencies and envelopes are supplied calibration parameters. Paired differences need a known model reference. No controls, discovery p-values, actual zeta search or interval certification in this diagnostic."}
        batch.atomic_json(outdir/"summary.json", summary)
        batch.atomic_json(outdir/"progress.json", {k: summary[k] for k in ("status", "completed_count", "failed_count", "total_tasks")})
        lines = ["# Fixed-frequency Euler transfer diagnostic", "", summary["interpretation"], "", "| view | channel | beta | all-cell positive designs | median train gain | median held-out gain |", "|---|---|---|---|---|---|"]
        lines += [f"| {r['view']} | {r['channel']} | {r['beta']} | {r['positive_all_cells_designs']}/{r['designs']} | {r['median_train_gain']:.4f} | {r['median_gain']:.4f} |" for r in aggregate]
        (outdir/"report.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
        return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    result = run(parser.parse_args().output_dir)
    print(json.dumps({k: result[k] for k in ("status", "completed_count", "failed_count")}))
    raise SystemExit(bool(result["failed_count"]))
