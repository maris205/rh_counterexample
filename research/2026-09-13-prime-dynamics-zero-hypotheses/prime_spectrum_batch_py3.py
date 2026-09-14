"""Resumable Phase A common-spectrum batch runner.

Each (scale, task) is an independent JSON artifact.  ``progress.json`` is
updated atomically after every task so an interrupted run can resume without
repeating completed work.  Results are finite numerical/surrogate diagnostics;
they are never a zeta-zero certificate.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def run_task(task: str, n: int, samples: int, reps: int, blocks: tuple[int, ...],
             splits: tuple[float, ...], grids: list[tuple[int, float]], seed: int,
             out: Path) -> dict[str, Any]:
    if task == "mertens":
        mod = importlib.import_module("mertens_dynamics")
        result = mod.run(n, samples, seed, reps, blocks, splits)
    elif task == "lambda_psi":
        mod = importlib.import_module("lambda_psi_dynamics")
        result = mod.run(n, samples, seed, reps, blocks, splits)
    elif task == "short_interval":
        mod = importlib.import_module("short_interval_dynamics")
        result = mod.run(n, samples, seed, reps, blocks, splits, 0.5, 0.5)
    elif task == "multi_grid":
        mod = importlib.import_module("multi_grid_demod")
        result = mod.run(n, 4.0, 40.0, 0.10, grids, reps, blocks, seed)
    elif task == "density_surrogate":
        mod = importlib.import_module("density_preserving_short_controls")
        result = mod.run(n, samples, seed, reps, 64, 0.5, 0.5, 37.5, (37.0, 38.0))
    elif task == "stratified_controls":
        mod = importlib.import_module("stratified_shuffle_controls")
        # Reuse the module's tested control implementation while keeping the
        # artifact independent and resumable.
        result = mod.run(n, samples, reps, max(blocks), seed)
    else:
        raise ValueError(f"unknown task {task}")
    result["batch_task"] = task
    result["batch_scale_n"] = n
    result["source_sha256"] = hashlib.sha256(Path(mod.__file__).read_bytes()).hexdigest()
    atomic_json(out, result)
    return result


def summarize(artifacts: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    screen_candidates: list[dict[str, Any]] = []
    failures = [a for a in artifacts if a.get("status") != "COMPLETED"]
    for a in artifacts:
        for row in a.get("blind_consensus", []):
            # A common-spectrum candidate must have at least three channels,
            # two grids, and explicit hold-out/control evidence.  The current
            # demodulator reports only the first two, so no row is promoted
            # without a separate hold-out/control gate.
            if row.get("channel_count", 0) >= 3 and row.get("grid_count", 0) >= 2:
                screen_candidates.append({"n": a.get("batch_scale_n"), **row,
                                          "eligible_for_zeta": False,
                                          "reason": "finite screen; holdout/control gate not encoded in this row"})
    # A zeta handoff requires the same frequency to recur across both scales;
    # this batch intentionally does not promote screen rows because its
    # per-task artifacts do not encode the full joint hold-out/control test.
    eligible: list[dict[str, Any]] = []
    for row in screen_candidates:
        if sum(abs(float(row["t_mean"]) - float(x["t_mean"])) <= 0.25
               for x in screen_candidates) >= len({a.get("batch_scale_n") for a in artifacts}):
            row = dict(row)
            row["reason"] = "cross-scale screen hit, but full holdout/control gate is absent"
            eligible.append(row)
    return {
        "status": "COMPLETED" if not failures else "COMPLETED_WITH_FAILURES",
        "purpose": "Phase A common-spectrum finite numerical and surrogate screening",
        "configuration": config,
        "completed_artifacts": len(artifacts),
        "failed_artifacts": len(failures),
        "screen_candidate_count": len(screen_candidates),
        "eligible_candidate_count": 0,
        "candidate_count": len(screen_candidates),
        "candidates": screen_candidates,
        "interpretation": (
            "Mertens, Lambda/psi, prime-count and short-interval outputs are finite feature diagnostics. "
            "Random, density-preserving, and block controls are empirical surrogates. "
            "No row is an actual zeta numerical candidate or Arb/FLINT interval certification. "
            "Only a cross-channel, cross-grid, cross-scale hit that passes every hold-out and control gate "
            "may be sent to a zeta root finder."
        ),
        "artifacts": [a.get("artifact") for a in artifacts],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--scales", default="1000000,5000000")
    ap.add_argument("--samples", type=int, default=2048)
    ap.add_argument("--control-reps", type=int, default=4)
    ap.add_argument("--blocks", default="100000,1000000")
    ap.add_argument("--splits", default="0.55,0.67,0.80")
    ap.add_argument("--grids", default="1024:0,1536:0.08")
    ap.add_argument("--seed", type=int, default=20260914)
    ap.add_argument("--smoke", action="store_true", help="use one small scale and one replicate")
    args = ap.parse_args()
    outdir = args.output_dir.resolve()
    scales = [int(x) for x in args.scales.split(",") if x.strip()]
    blocks = tuple(int(x) for x in args.blocks.split(",") if x.strip())
    splits = tuple(float(x) for x in args.splits.split(",") if x.strip())
    grids = [(int(a), float(b)) for a, b in (x.split(":") for x in args.grids.split(","))]
    if args.smoke:
        scales, args.samples, args.control_reps = [50_000], 256, 1
    tasks = ["mertens", "lambda_psi", "short_interval", "multi_grid",
             "density_surrogate", "stratified_controls"]
    config = {"scales": scales, "samples": args.samples, "control_reps": args.control_reps,
              "blocks": list(blocks), "splits": list(splits), "grids": grids,
              "seed": args.seed, "python": sys.version, "platform": platform.platform(),
              "requested_python": "py -3.10 (unavailable; executed with Python 3.14)",
              "tasks": tasks}
    outdir.mkdir(parents=True, exist_ok=True)
    atomic_json(outdir / "config.json", config)
    progress_path = outdir / "progress.json"
    previous = load_json(progress_path) or {"completed": [], "failed": []}
    completed = list(previous.get("completed", []))
    failed = list(previous.get("failed", []))
    artifacts: list[dict[str, Any]] = []
    for n in scales:
        for task in tasks:
            key = f"n{n}-{task}"
            artifact = outdir / f"{key}.json"
            if key in completed and artifact.exists():
                obj = load_json(artifact)
                if obj is not None:
                    artifacts.append({"key": key, "artifact": str(artifact), **obj})
                    continue
            started = time.time()
            try:
                obj = run_task(task, n, args.samples, args.control_reps, blocks, splits,
                               grids, args.seed + n + len(task), artifact)
                completed.append(key)
                failed = [x for x in failed if x != key]
                status = "COMPLETED"
                artifacts.append({"key": key, "artifact": str(artifact), **obj})
            except Exception as exc:  # persist failure and continue to next route
                status = "FAILED"
                failed.append(key)
                atomic_json(artifact, {"status": "FAILED", "batch_task": task,
                                       "batch_scale_n": n, "error": repr(exc)})
            atomic_json(progress_path, {"status": "RUNNING", "updated": time.time(),
                                        "completed": sorted(set(completed)),
                                        "failed": sorted(set(failed)), "last_task": key,
                                        "last_status": status, "elapsed_s": time.time() - started})
    summary = summarize(artifacts, config)
    atomic_json(outdir / "summary.json", summary)
    lines = ["# Phase A prime-spectrum batch", "", f"Status: **{summary['status']}**", "",
             f"Completed artifacts: {summary['completed_artifacts']}",
             f"Failed artifacts: {summary['failed_artifacts']}",
             f"Cross-channel candidates: {summary['candidate_count']}", "",
             "This report is a finite numerical screen. Controls are empirical surrogates; "
             "no Mertens, prime-count, Lambda/psi, or short-interval anomaly is a zeta zero. "
             "No Arb/FLINT interval certification was attempted.", ""]
    (outdir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    atomic_json(progress_path, {"status": summary["status"], "updated": time.time(),
                                "completed": sorted(set(completed)), "failed": sorted(set(failed)),
                                "last_task": "summary", "summary": str(outdir / "summary.json")})
    print(json.dumps({"status": summary["status"], "output_dir": str(outdir),
                      "completed": summary["completed_artifacts"],
                      "failed": summary["failed_artifacts"],
                      "candidates": summary["candidate_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
