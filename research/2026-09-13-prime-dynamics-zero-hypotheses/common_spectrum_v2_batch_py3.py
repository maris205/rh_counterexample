"""Recoverable joint screen: immutable manifest, individual surrogate JSONs.

Example: py -3.14 common_spectrum_v2_batch_py3.py --profile validation
         --output-dir C:/absolute/path/runs/common-spectrum-v2-validation
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time
import traceback

for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(name, "1")

import numpy as np
import scipy
import mpmath
import common_spectrum_v2 as core
from known_ordinates import known_ordinates, known_mask

HERE = Path(__file__).resolve().parent


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@contextmanager
def run_lock(outdir):
    with (outdir / ".run.lock").open("a+b") as handle:
        handle.write(b"0")
        handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def manifest_for(config):
    sources = ("common_spectrum_v2.py", Path(__file__).name, "known_ordinates.py",
               "mertens_dynamics.py", "lambda_psi_dynamics.py")
    content = {"schema": "common-spectrum-v2", "configuration": config,
               "source_sha256": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in sources},
               "runtime": {"python": sys.version, "executable": sys.executable,
                           "numpy": np.__version__, "scipy": scipy.__version__, "mpmath": mpmath.__version__,
                           "platform": platform.platform()},
               "interpretation": "empirical finite joint prediction screen; no mathematical null, zeta roots or interval certification"}
    return {**content, "run_id": fingerprint(content)}


def check_manifest(outdir, manifest):
    path = outdir / "config.json"
    if path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))
        if previous.get("run_id") != manifest["run_id"]:
            raise ValueError("configuration, sources or runtime changed: use a new output directory")
    elif list(outdir.glob("task-*.json")):
        raise ValueError("artifacts without a manifest: use a new output directory")
    else:
        atomic_json(path, manifest)


def task_list(reps):
    return [("real", None, 0)] + [(f"{mode}-{rep:04d}", mode, rep)
                                      for mode in core.CONTROL_MODES for rep in range(reps)]


def completed_task(path, run_id, task_id):
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
        if result.get("run_id") == run_id and result.get("task_id") == task_id and result.get("status") == "COMPLETED":
            return result
    except (OSError, ValueError):
        pass
    return None


def summarize(results, config, run_id):
    expected = task_list(config["control_reps"])
    done = {key: value for key, value in results.items() if value.get("status") == "COMPLETED"}
    failed = {key: value for key, value in results.items() if value.get("status") == "FAILED"}
    controls = {mode: [done[key]["result"]["max_statistic"] for key, kind, _ in expected if kind == mode and key in done]
                for mode in core.CONTROL_MODES}
    real = done.get("real", {}).get("result")
    gate = core.gate(real, controls, config["control_reps"], config["alpha"]) if real else {
        "gate_status": "NOT_EVALUATED", "gate_reason": "real-data task missing or failed", "candidate_count": None,
        "tested_candidates": []}
    status = "COMPLETED" if len(done) == len(expected) else ("COMPLETED_WITH_FAILURES" if failed else "INCOMPLETE")
    return {"schema": "common-spectrum-v2-summary", "run_id": run_id, "status": status,
            "updated": now(), "configuration": config, "total_tasks": len(expected),
            "completed_count": len(done), "failed_count": len(failed), "failed_tasks": list(failed),
            "pending_count": len(expected) - len(done) - len(failed), **gate,
            "controls": {mode: {"replicates": len(vals), "max_statistic_q95": float(np.quantile(vals, .95)) if vals else None,
                                "scores": vals} for mode, vals in controls.items()},
            "zeta_root_search_status": "NOT_PERFORMED", "arb_flint_certification_status": "NOT_PERFORMED",
            "full_protocol_status": "INCOMPLETE", "eligible_for_zeta_handoff_count": None,
            "missing_protocol_gates": ["operator-level synthetic sensitivity calibration",
                "complete Phase B and Phase C gates", "shared growth-parameter validation"],
            "production_control_resolution": config["control_reps"] >= 199,
            "interpretation": "candidate_count is computed only after the empirical gate is evaluable. Nested scales, grids and prime observables are dependent; p-values describe surrogate ranks, not a theorem about primes or RH."}


def run_batch(outdir, config, executor=None):
    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = manifest_for(config)
    run_id = manifest["run_id"]
    with run_lock(outdir):
        check_manifest(outdir, manifest)
        tasks = task_list(config["control_reps"])
        results = {}
        for key, _, _ in tasks:
            saved = completed_task(outdir / f"task-{key}.json", run_id, key)
            if saved:
                results[key] = saved
        start = time.monotonic()

        def progress(status, current):
            atomic_json(outdir / "progress.json", {"schema": "common-spectrum-v2-progress", "run_id": run_id,
                "status": status, "pid": os.getpid(), "updated": now(), "current_task": current,
                "completed_count": sum(x["status"] == "COMPLETED" for x in results.values()),
                "failed_count": sum(x["status"] == "FAILED" for x in results.values()),
                "total_tasks": len(tasks), "elapsed_s_this_session": time.monotonic() - start})

        progress("RUNNING", "prepare")
        coeff = None
        frequencies = np.arange(config["t_min"], config["t_max"] + config["t_step"] / 2, config["t_step"])
        frequencies = frequencies[~known_mask(frequencies, config["known_margin"])]
        if len(frequencies) < config["top_k"]:
            raise ValueError("too few frequencies remain after known-line exclusion")
        for index, (key, mode, rep) in enumerate(tasks):
            if key in results:
                continue
            if time.monotonic() - start > config["max_seconds"]:
                break
            progress("RUNNING", key)
            task_start = time.monotonic()
            try:
                if executor is not None:
                    result = executor(key, mode, rep)
                else:
                    if coeff is None:
                        coeff = core.arithmetic_coefficients(max(config["scales"]))
                    if mode is None:
                        source = coeff
                    else:
                        seed = int.from_bytes(hashlib.sha256(f"{config['seed']}:{mode}:{rep}".encode()).digest()[:8], "big")
                        source = core.surrogate(coeff, mode, np.random.default_rng(seed), config["block_size"], config["log_bins"])
                    cells = core.build_cells(source, config["scales"], config["grids"], config["splits"], config["theta"], config["x_min"])
                    result = core.evaluate(cells, frequencies, math_log(config["x_min"]), config["top_k"])
                json.dumps(result, allow_nan=False)  # serialization/nonfinite failures belong to this task
                artifact = {"status": "COMPLETED", "result": result}
            except Exception as exc:
                traceback.print_exc()
                artifact = {"status": "FAILED", "error": repr(exc)}
            artifact.update({"run_id": run_id, "task_id": key, "control_mode": mode, "replicate": rep,
                             "finished": now(), "elapsed_s": time.monotonic() - task_start})
            atomic_json(outdir / f"task-{key}.json", artifact)
            results[key] = artifact
            progress("RUNNING", key)
            print(json.dumps({"task": key, "status": artifact["status"], "done": len(results), "total": len(tasks)}), flush=True)
        summary = summarize(results, config, run_id)
        atomic_json(outdir / "summary.json", summary)
        (outdir / "report.md").write_text("# Joint common-spectrum v2\n\n"
            + f"Status: {summary['status']}\n\nTasks completed: {summary['completed_count']}/{summary['total_tasks']}; failed: {summary['failed_count']}.\n\n"
            + f"Gate: {summary['gate_status']}; computed screen candidates: {summary['candidate_count']}.\n\n"
            + "Shared frequency is selected on the common training prefix; each observable has separate coefficients frozen for prediction.\n\n"
            + "The broader research protocol is INCOMPLETE: operator sensitivity, complete B/C gates and growth-parameter validation remain. No handoff is authorized by this screen alone.\n\n"
            + summary["interpretation"] + "\n\nNo actual zeta root search or Arb/FLINT certification was performed.\n", encoding="utf-8")
        progress(summary["status"], None)
        return summary


def math_log(x):
    return float(np.log(x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--profile", choices=("smoke", "validation", "long", "disjoint"), default="validation")
    ap.add_argument("--control-reps", type=int)
    ap.add_argument("--scales")
    ap.add_argument("--max-seconds", type=float, default=14400)
    args = ap.parse_args()
    config = {"profile": args.profile, "scales": [100000, 300000], "grids": [[192, 0.0], [256, .08]],
              "splits": [.55, .75], "control_reps": 19, "seed": 20260916, "theta": .525,
              "x_min": 100, "t_min": 4., "t_max": 40., "t_step": .25,
              "known_margin": .35, "top_k": 3, "alpha": .05, "block_size": 30000,
              "log_bins": 32, "max_seconds": args.max_seconds,
              "primary_families": {"mertens": "mertens", "global_prime": "psi", "local_prime": "short_psi"},
              "diagnostic_channels": ["prime_count"], "growth_parameter": 0.0,
              "selection_objective": "min_primary_training_gain", "selection_separation": .5,
              "training_window_purge": "short-window support strictly before each held-out x"}
    if args.profile == "smoke":
        config.update(scales=[5000, 10000], grids=[[64, 0.], [96, .08]], control_reps=2, block_size=1000)
    elif args.profile == "long":
        config.update(scales=[1000000, 5000000], grids=[[512, 0.], [768, .08]], control_reps=199,
                      block_size=250000, log_bins=64, t_step=.1)
    elif args.profile == "disjoint":
        config.update(scales=[10000000, 30000000], grids=[[192, 0.], [256, .08]],
                      control_reps=19, block_size=1000000, log_bins=64, x_min=6000000,
                      t_step=.25)
    if args.control_reps is not None:
        config["control_reps"] = args.control_reps
    if args.scales:
        config["scales"] = sorted(set(map(int, args.scales.split(","))))
    if config["control_reps"] < 1 or len(config["scales"]) < 2:
        ap.error("need positive control reps and at least two distinct scales")
    config["known_ordinates_excluded"] = known_ordinates(config["t_min"], config["t_max"], config["known_margin"])
    result = run_batch(args.output_dir, config)
    print(json.dumps({k: result[k] for k in ("status", "completed_count", "failed_count", "gate_status", "candidate_count")}))
    if result["failed_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
