"""Pre-observation operator injection calibration for the joint screen.

The perturbation is added to coefficient arrays before cumulative sums and
short-window differences.  It is a synthetic observation-operator test, not a
model of primes and not evidence for a zeta zero.
"""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import traceback

import common_spectrum_v2 as core
import common_spectrum_v2_batch_py3 as batch
import numpy as np
from known_ordinates import known_ordinates, known_mask


def cumulative_atom(n, t, beta, amplitude, phase):
    x = np.arange(n + 1, dtype=float)
    out = np.zeros(n + 1, dtype=float)
    valid = x >= 2
    u = np.log(x[valid])
    out[valid] = amplitude * np.exp(beta * (u - np.log(100.0))) * np.sqrt(x[valid]) * np.cos(t * u + phase)
    return np.diff(out, prepend=0.0)


def inject(coefficients, t, beta, amplitude, phases):
    out = {name: value.astype(float, copy=True) for name, value in coefficients.items()}
    for i, name in enumerate(("mu", "lambda", "prime")):
        out[name] += cumulative_atom(len(out[name]) - 1, t, beta, amplitude, phases[i])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    outdir = args.output_dir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    config = {
        "scales": [100000, 300000], "grids": [[192, 0.0], [256, 0.08]],
        "splits": [0.55, 0.75], "theta": 0.525, "x_min": 100,
        "frequencies": [18.0, 37.58617815882567], "betas": [0.0, 0.05],
        "amplitudes": [0.5, 1.0, 2.0], "phase_seeds": [0, 1, 2, 3],
        "scan_min": 4.0, "scan_max": 40.0, "scan_step": 0.25,
        "known_margin": 0.35, "top_k": 3, "origin": "log(100)",
        "scope": "pre-observation coefficient injection; synthetic operator calibration only",
    }
    manifest = batch.manifest_for(config)
    manifest["source_sha256"][Path(__file__).name] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest.pop("run_id")
    manifest["run_id"] = batch.fingerprint(manifest)
    with batch.run_lock(outdir):
        batch.check_manifest(outdir, manifest)
        base = core.arithmetic_coefficients(max(config["scales"]))
        origin = float(np.log(100.0))
        scan = np.arange(config["scan_min"], config["scan_max"] + .125, config["scan_step"])
        discovery_scan = scan[~known_mask(scan, config["known_margin"])]
        known = known_ordinates(0.0, 41.0, config["known_margin"])
        cases = [("baseline", None, None, 0.0, 0)]
        for t in config["frequencies"]:
            for beta in config["betas"]:
                for amplitude in config["amplitudes"]:
                    for seed in config["phase_seeds"]:
                        cases.append((f"t{t:.12g}-b{beta:g}-a{amplitude:g}-s{seed}", t, beta, amplitude, seed))
        results = []
        for key, t, beta, amplitude, seed in cases:
            path = outdir / f"task-{key}.json"
            row = batch.completed_task(path, manifest["run_id"], key)
            if row is None:
                try:
                    if t is None:
                        result = core.evaluate(core.build_cells(base, config["scales"], config["grids"], config["splits"], config["theta"], config["x_min"]), discovery_scan, origin, config["top_k"])
                        row = {"status": "COMPLETED", "injected": False, "result": result}
                    else:
                        phases = np.random.default_rng(20260916 + seed).uniform(-np.pi, np.pi, 3)
                        source = inject(base, t, beta, amplitude, phases)
                        cells = core.build_cells(source, config["scales"], config["grids"], config["splits"], config["theta"], config["x_min"])
                        result = core.evaluate(cells, discovery_scan, origin, config["top_k"])
                        calibration = core.evaluate(cells, np.unique(np.r_[discovery_scan, t]), origin, config["top_k"])
                        recovered = [c for c in result["candidates"] if abs(c["t"] - t) <= .25]
                        calibrated = [c for c in calibration["candidates"] if abs(c["t"] - t) <= .25]
                        row = {"status": "COMPLETED", "injected": True, "t": t, "beta": beta,
                               "amplitude": amplitude, "phase_seed": seed, "phases": phases.tolist(),
                               "discovery_recovered": bool(recovered), "calibration_recovered": bool(calibrated),
                               "discovery_positive": any(c["positive_in_every_primary_cell"] for c in recovered),
                               "calibration_positive": any(c["positive_in_every_primary_cell"] for c in calibrated),
                               "result": result, "calibration_result": calibration}
                    json.dumps(row, allow_nan=False)
                except Exception as exc:
                    traceback.print_exc()
                    row = {"status": "FAILED", "error": repr(exc)}
                row.update(run_id=manifest["run_id"], task_id=key)
                batch.atomic_json(path, row)
            results.append(row)
            batch.atomic_json(outdir / "progress.json", {"status": "RUNNING", "completed_count": sum(r["status"] == "COMPLETED" for r in results),
                              "failed_count": sum(r["status"] == "FAILED" for r in results), "total_tasks": len(cases),
                              "last_task": key, "updated": batch.now()})
        curves = []
        for t in config["frequencies"]:
            for beta in config["betas"]:
                for amplitude in config["amplitudes"]:
                    rows = [r for r in results if r.get("t") == t and r.get("beta") == beta and r.get("amplitude") == amplitude]
                    curves.append({"t": t, "beta": beta, "amplitude": amplitude, "trials": len(rows),
                                   "discovery_recovery": sum(r["discovery_recovered"] for r in rows),
                                   "calibration_recovery": sum(r["calibration_recovered"] for r in rows),
                                   "discovery_positive": sum(r["discovery_positive"] for r in rows),
                                   "calibration_positive": sum(r["calibration_positive"] for r in rows)})
        failed = sum(r["status"] == "FAILED" for r in results)
        summary = {"schema": "common-spectrum-operator-power-v1", "status": "COMPLETED_WITH_FAILURES" if failed else "COMPLETED",
                   "run_id": manifest["run_id"], "configuration": config, "known_ordinates": known,
                   "completed_count": len(results) - failed, "failed_count": failed, "total_tasks": len(cases),
                   "curves": curves, "candidate_count": None, "gate_status": "NOT_EVALUATED",
                   "interpretation": "Pre-observation coefficient perturbations are synthetic transfer tests. They preserve no prime law, do not define a null, and do not support a zeta-zero claim. The known-line frequency is intentionally reported only as calibration; discovery excludes its neighborhood. beta is an observation-model stress parameter, not zeta sigma.",
                   "missing_gates": ["prime-consistent injection law", "full surrogate gate", "disjoint external validation", "actual zeta evaluation", "Arb/FLINT certification"]}
        batch.atomic_json(outdir / "summary.json", summary)
        batch.atomic_json(outdir / "progress.json", {k: summary[k] for k in ("status", "completed_count", "failed_count", "total_tasks")})
        lines = ["# Pre-observation operator injection power", "", summary["interpretation"], "",
                 "| t | beta | amplitude | discovery | known-line calibration | discovery positive | calibration positive |", "|---:|---:|---:|---:|---:|---:|---:|"]
        lines += [f"| {r['t']} | {r['beta']} | {r['amplitude']} | {r['discovery_recovery']}/{r['trials']} | {r['calibration_recovery']}/{r['trials']} | {r['discovery_positive']}/{r['trials']} | {r['calibration_positive']}/{r['trials']} |" for r in curves]
        (outdir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(json.dumps({k: summary[k] for k in ("status", "completed_count", "failed_count", "candidate_count")}))
        raise SystemExit(bool(failed))


if __name__ == "__main__":
    main()
