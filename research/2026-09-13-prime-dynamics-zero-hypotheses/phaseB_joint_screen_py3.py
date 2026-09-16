"""Joint unknown-frequency screen with multiple short-window powers and gaps."""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import traceback

import common_spectrum_v2 as core
import common_spectrum_v2_batch_py3 as batch
from short_interval_dynamics import gap_signal
from known_ordinates import known_mask
import numpy as np


def cells_for(coefficients, config):
    rows = []
    for theta in config["thetas"]:
        cells = core.build_cells(coefficients, config["scales"], config["grids"], config["splits"], theta, config["x_min"])
        primes = np.flatnonzero(coefficients["prime"] > .5).astype(np.int64)
        for cell in cells:
            gap = gap_signal(primes, cell.u)
            rows.append(replace(cell, key=f"theta{theta:g}-" + cell.key,
                                y=np.column_stack((cell.y, gap))))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    outdir = args.output_dir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    config = {"scales": [100000, 300000], "grids": [[192, 0.0], [256, .08]],
              "splits": [.55, .75], "thetas": [.50, .525, .60], "x_min": 100,
              "t_min": 4., "t_max": 40., "t_step": .25, "known_margin": .35,
              "top_k": 3, "alpha": .05, "control_reps": 19, "block_size": 30000,
              "log_bins": 64, "seed": 20260916,
              "scope": "joint unknown-frequency B robustness; gap is diagnostic and not an extra independent vote"}
    manifest = batch.manifest_for(config)
    manifest["source_sha256"][Path(__file__).name] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest["source_sha256"]["short_interval_dynamics.py"] = hashlib.sha256((Path(__file__).parent / "short_interval_dynamics.py").read_bytes()).hexdigest()
    manifest.pop("run_id")
    manifest["run_id"] = batch.fingerprint(manifest)
    with batch.run_lock(outdir):
        batch.check_manifest(outdir, manifest)
        # Extend output labels with a fifth, explicitly diagnostic column.
        core.CHANNELS = tuple(core.CHANNELS) + ("gap",)
        frequencies = np.arange(config["t_min"], config["t_max"] + .125, config["t_step"])
        frequencies = frequencies[~known_mask(frequencies, config["known_margin"])]
        tasks = [("real", None, 0)] + [(f"{mode}-{rep:04d}", mode, rep)
                                       for mode in core.CONTROL_MODES for rep in range(config["control_reps"])]
        coeff = None
        results = {}
        for key, mode, rep in tasks:
            path = outdir / f"task-{key}.json"
            row = batch.completed_task(path, manifest["run_id"], key)
            if row is None:
                try:
                    if coeff is None:
                        coeff = core.arithmetic_coefficients(max(config["scales"]))
                    if mode is None:
                        source = coeff
                    else:
                        seed = int.from_bytes(hashlib.sha256(f"{config['seed']}:{mode}:{rep}".encode()).digest()[:8], "big")
                        source = core.surrogate(coeff, mode, np.random.default_rng(seed), config["block_size"], config["log_bins"])
                    result = core.evaluate(cells_for(source, config), frequencies, float(np.log(config["x_min"])), config["top_k"])
                    row = {"status": "COMPLETED", "result": result, "control_mode": mode, "replicate": rep}
                    json.dumps(row, allow_nan=False)
                except Exception as exc:
                    traceback.print_exc()
                    row = {"status": "FAILED", "error": repr(exc), "control_mode": mode, "replicate": rep}
                row.update(run_id=manifest["run_id"], task_id=key)
                batch.atomic_json(path, row)
            results[key] = row
            batch.atomic_json(outdir / "progress.json", {"schema": "phaseB-joint-progress", "status": "RUNNING",
                              "run_id": manifest["run_id"], "completed_count": sum(r["status"] == "COMPLETED" for r in results.values()),
                              "failed_count": sum(r["status"] == "FAILED" for r in results.values()), "total_tasks": len(tasks),
                              "last_task": key, "updated": batch.now()})
        done = {k: r for k, r in results.items() if r["status"] == "COMPLETED"}
        real = done.get("real", {}).get("result")
        controls = {mode: [done[f"{mode}-{rep:04d}"]["result"]["max_statistic"] for rep in range(config["control_reps"])
                           if f"{mode}-{rep:04d}" in done] for mode in core.CONTROL_MODES}
        gate = core.gate(real, controls, config["control_reps"], config["alpha"]) if real else {
            "gate_status": "NOT_EVALUATED", "candidate_count": None, "tested_candidates": []}
        failed = len(tasks) - len(done)
        summary = {"schema": "phaseB-joint-summary-v1", "status": "COMPLETED_WITH_FAILURES" if failed else "COMPLETED",
                   "run_id": manifest["run_id"], "configuration": config, "completed_count": len(done),
                   "failed_count": failed, "total_tasks": len(tasks), **gate,
                   "full_protocol_status": "INCOMPLETE", "gap_role": "correlated diagnostic; not an independent vote",
                   "missing_gates": ["prime-consistent three-family injection", "complete Phase C family gate", "actual zeta evaluation", "Arb/FLINT certification"],
                   "zeta_root_search_status": "NOT_PERFORMED", "arb_flint_certification_status": "NOT_PERFORMED",
                   "interpretation": "Three short-window powers are robustness cells sharing the same arithmetic source. Gap is a correlated diagnostic. The empirical gate is finite and surrogate-based; it is not an RH probability or theorem."}
        batch.atomic_json(outdir / "summary.json", summary)
        batch.atomic_json(outdir / "progress.json", {k: summary[k] for k in ("status", "completed_count", "failed_count", "total_tasks")})
        (outdir / "report.md").write_text("# Phase B joint unknown-frequency screen\n\n"
            + summary["interpretation"] + "\n\n"
            + f"Tasks: {summary['completed_count']}/{summary['total_tasks']}; failures: {summary['failed_count']}.\n\n"
            + f"Gate: {summary['gate_status']}; candidate count: {summary.get('candidate_count')}.\n\n"
            + "The gap column is diagnostic and does not create an independent fourth vote. No zeta root search or interval certification was performed.\n", encoding="utf-8")
        print(json.dumps({k: summary.get(k) for k in ("status", "completed_count", "failed_count", "gate_status", "candidate_count")}))
        raise SystemExit(bool(failed))


if __name__ == "__main__":
    main()
