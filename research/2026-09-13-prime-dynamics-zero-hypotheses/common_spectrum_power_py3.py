"""Observation-layer injection sensitivity, not operator or RH validation."""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import time
import traceback

import common_spectrum_v2_batch_py3 as batch
import common_spectrum_v2 as core
import numpy as np
from known_ordinates import known_mask


def add_tone(cells, t, amplitude, scales, phases, origin):
    return [replace(c, y=c.y + amplitude * scales[None, :] *
                    np.cos(t * (c.u[:, None] - origin) + phases[None, :])) for c in cells]


def run(outdir):
    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    config = {"scales": [100000, 300000], "grids": [[192, 0.], [256, .08]],
              "splits": [.55, .75], "theta": .525, "x_min": 100,
              "frequencies": [18., 27., 35.], "amplitudes": [.5, 1., 2., 4.],
              "phase_seeds": list(range(10)), "t_min": 4., "t_max": 40., "t_step": .25,
              "known_margin": .35, "top_k": 3, "recovery_radius": .25,
              "amplitude_units": "channel standard deviation on common purged training prefix",
              "scope": "exploratory observation-layer sensitivity; no pre-operator injection or surrogate rank gate"}
    manifest = batch.manifest_for(config)
    manifest["source_sha256"][Path(__file__).name] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest.pop("run_id")
    manifest["run_id"] = batch.fingerprint(manifest)
    with batch.run_lock(outdir):
        batch.check_manifest(outdir, manifest)
        cells = core.build_cells(core.arithmetic_coefficients(max(config["scales"])), config["scales"],
                                 config["grids"], config["splits"], config["theta"], config["x_min"])
        anchor = min(cells, key=lambda c: (c.n, c.grid, c.split))
        boundary = min(c.u[c.cut] for c in cells)
        amplitudes = np.std(anchor.y[anchor.support_end_u < boundary], axis=0)
        origin = float(np.log(config["x_min"]))
        scan = np.arange(config["t_min"], config["t_max"] + .125, config["t_step"])
        scan = scan[~known_mask(scan, config["known_margin"])]
        cases = [("baseline", 0., 0., 0)] + [
            (f"t{t:g}-a{a:g}-seed{s}", t, a, s) for t in config["frequencies"]
            for a in config["amplitudes"] for s in config["phase_seeds"]]
        results = []
        start = time.monotonic()
        for key, t, amplitude, seed in cases:
            path = outdir / f"task-{key}.json"
            obj = batch.completed_task(path, manifest["run_id"], key)
            if obj is None:
                try:
                    phases = np.random.default_rng(20260916 + seed).uniform(-np.pi, np.pi, len(core.CHANNELS))
                    injected = add_tone(cells, t, amplitude, amplitudes, phases, origin)
                    result = core.evaluate(injected, scan, origin, config["top_k"])
                    matches = [r for r in result["candidates"] if amplitude > 0 and abs(r["t"] - t) <= config["recovery_radius"]]
                    obj = {"status": "COMPLETED", "injected_t": t if amplitude else None,
                           "amplitude": amplitude, "phase_seed": seed, "phases": phases.tolist(),
                           "frequency_recovered": bool(matches) if amplitude else None,
                           "recovered_with_all_positive_predictions": any(r["positive_in_every_primary_cell"] for r in matches) if amplitude else None,
                           "any_positive_candidate": any(r["positive_in_every_primary_cell"] for r in result["candidates"]),
                           "result": result}
                    json.dumps(obj, allow_nan=False)
                except Exception as exc:
                    traceback.print_exc()
                    obj = {"status": "FAILED", "error": repr(exc)}
                obj.update(run_id=manifest["run_id"], task_id=key)
                batch.atomic_json(path, obj)
            results.append(obj)
            batch.atomic_json(outdir / "progress.json", {"status": "RUNNING", "completed_count": sum(r["status"] == "COMPLETED" for r in results),
                              "failed_count": sum(r["status"] == "FAILED" for r in results),
                              "total_tasks": len(cases), "last_task": key, "updated": batch.now()})
        curves = []
        for t in config["frequencies"]:
            for a in config["amplitudes"]:
                rows = [r for r in results if r["status"] == "COMPLETED" and r.get("injected_t") == t and r["amplitude"] == a]
                curves.append({"t": t, "amplitude": a, "trials": len(rows),
                               "frequency_recovery_count": sum(r["frequency_recovered"] for r in rows),
                               "positive_prediction_recovery_count": sum(r["recovered_with_all_positive_predictions"] for r in rows)})
        failed = sum(r["status"] == "FAILED" for r in results)
        summary = {"schema": "common-spectrum-power-v2", "status": "COMPLETED_WITH_FAILURES" if failed else "COMPLETED",
                   "run_id": manifest["run_id"], "configuration": config, "amplitude_scales": dict(zip(core.CHANNELS, map(float, amplitudes))),
                   "completed_count": len(results) - failed, "failed_count": failed, "total_tasks": len(cases),
                   "baseline_any_positive_prediction": results[0].get("any_positive_candidate"), "curves": curves,
                   "elapsed_s": time.monotonic() - start, "candidate_count": None, "gate_status": "NOT_EVALUATED",
                   "interpretation": "Ten phase settings are design trials, not independent arithmetic datasets. This post-resampling injection validates only the regression/selection layer. It does not calibrate arithmetic observation operators, full surrogate gates, off-line zeta zeros or interval certificates."}
        batch.atomic_json(outdir / "summary.json", summary)
        batch.atomic_json(outdir / "progress.json", {k: summary[k] for k in ("status", "completed_count", "failed_count", "total_tasks")})
        table = ["# Observation-layer injection sensitivity", "", summary["interpretation"], "",
                 "| t | amplitude | selected / trials | positive predictions / trials |", "|---|---|---|---|"]
        table += [f"| {r['t']} | {r['amplitude']} | {r['frequency_recovery_count']}/{r['trials']} | {r['positive_prediction_recovery_count']}/{r['trials']} |" for r in curves]
        (outdir / "report.md").write_text("\n".join(table) + "\n", encoding="utf-8")
        return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    result = run(parser.parse_args().output_dir)
    print(json.dumps({k: result[k] for k in ("status", "completed_count", "failed_count", "baseline_any_positive_prediction")}))
    raise SystemExit(bool(result["failed_count"]))
