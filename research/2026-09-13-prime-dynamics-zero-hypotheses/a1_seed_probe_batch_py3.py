"""Small recoverable actual-zeta probe; see A1_PILOT_001_PROTOCOL.md."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

import mpmath as mp
import flint
import numpy as np
import scipy
import common_spectrum_v2_batch_py3 as support

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LAB = HERE.parent / "2026-09-08-zero-lab"
sys.path.insert(0, str(LAB))
import zero_lab


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic(path, value):
    tmp = path.with_name(path.name + f".tmp-{os.getpid()}")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for attempt in range(8):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if attempt == 7:
                raise
            time.sleep(.05 * (attempt + 1))


def configuration(profile):
    smoke = profile == "smoke"
    return {"profile": profile, "heights": ["10010"] if smoke else ["10010", "10012", "10014"],
            "sigmas": ["0.30", "0.70"] if smoke else ["0.30", "0.49", "0.51", "0.70"],
            "precisions": [35, 50] if smoke else [50, 80], "max_steps": 40,
            "max_height": 10050, "agreement_tolerance": "1e-15" if smoke else "1e-25",
            "near_line_tolerance": "1e-20" if smoke else "1e-30",
            "box_radius": "1e-12", "task_timeout_s": 90, "max_seconds": 900,
            "protocol": "A1_PILOT_001_PROTOCOL.md", "route": "RC:A1", "record_id": "A1-PILOT-001"}


def jobs(config):
    return [{"task_id": f"seed-{i:02d}", "sigma": s, "t": t}
            for i, (t, s) in enumerate((t, s) for t in config["heights"] for s in config["sigmas"])]


def manifest(config):
    paths = [Path(__file__), LAB / "zero_lab.py", Path(support.__file__), HERE / config["protocol"]]
    payload = {"schema": "a1-seed-probe-v1", "configuration": config,
               "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
               "runtime": {"python": sys.version, "executable": sys.executable, "platform": platform.platform(),
                           "mpmath": mp.__version__, "python_flint": flint.__version__,
                           "numpy": np.__version__, "scipy": scipy.__version__}}
    return {**payload, "run_id": support.fingerprint(payload)}


def classify(refinements, point_check, config):
    if any(r["status"] != "NUMERICAL_CONVERGENCE" for r in refinements):
        return {"screen_status": "NO_CONVERGENCE", "precision_endpoint_distance": None}
    with mp.workdps(max(config["precisions"]) + 10):
        low, high = refinements
        a = mp.mpc(low["final_sigma"], low["final_t"])
        b = mp.mpc(high["final_sigma"], high["final_t"])
        distance = abs(a - b)
        residual_ok = all(mp.mpf(r["abs_zeta"]) < mp.power(10, -dps + 15)
                          for r, dps in zip(refinements, config["precisions"]))
        checks = point_check.get("evaluation_rows", []) if point_check else []
        independent_ok = bool(checks) and all(r["independent_point_evaluations_agree"] for r in checks)
        if not residual_ok or not independent_ok:
            label = "NUMERICAL_REVIEW_REQUIRED"
        elif distance > mp.mpf(config["agreement_tolerance"]):
            label = "PRECISION_UNSTABLE"
        elif abs(b.real - mp.mpf("0.5")) <= mp.mpf(config["near_line_tolerance"]):
            label = "STABLE_NEAR_LINE"
        else:
            label = "OFF_LINE_NUMERICAL_CANDIDATE"
        return {"screen_status": label, "precision_endpoint_distance": mp.nstr(distance, 20),
                "residual_requirements_met": residual_ok, "independent_point_agreement": independent_ok,
                "final_distance_to_line": mp.nstr(abs(b.real - mp.mpf("0.5")), 20),
                "endpoint_outside_seed_height_span": not (mp.mpf(min(config["heights"])) <= b.imag <= mp.mpf(max(config["heights"])))}


def evaluate(job, config):
    refinements = [zero_lab.refine(job["sigma"], job["t"], dps=dps,
                                  max_steps=config["max_steps"], max_height=config["max_height"])
                   for dps in config["precisions"]]
    high = refinements[-1]
    check = None
    if high["status"] == "NUMERICAL_CONVERGENCE":
        check = zero_lab.check_point(high["final_sigma"], high["final_t"], config["box_radius"],
                                    precisions=(max(config["precisions"]),))
    return {"seed": job, "refinements": refinements, "point_check": check,
            **classify(refinements, check, config), "certified_off_line_zero": False,
            "zero_existence_or_count_certification": "NOT_PERFORMED"}


def worker(outdir, index):
    saved = json.loads((outdir / "manifest.json").read_text(encoding="utf-8"))
    config = saved["configuration"]
    if manifest(config)["run_id"] != saved["run_id"]:
        raise ValueError("source/runtime mismatch")
    job = jobs(config)[index]
    started = time.monotonic()
    try:
        row = {"status": "COMPLETED", "result": evaluate(job, config)}
    except Exception as exc:
        traceback.print_exc()
        row = {"status": "FAILED", "error": repr(exc)}
    row.update(run_id=saved["run_id"], task_id=job["task_id"], seed=job,
               finished_utc=now(), elapsed_s=time.monotonic() - started)
    atomic(outdir / f"task-{job['task_id']}.json", row)
    return 0 if row["status"] == "COMPLETED" else 1


def load_task(path, run_id, job):
    if not path.exists():
        return None
    row = json.loads(path.read_text(encoding="utf-8"))
    if row.get("run_id") != run_id or row.get("seed") != job or row.get("task_id") != job["task_id"]:
        raise ValueError(f"mismatched task artifact: {path}")
    if row.get("status") not in ("COMPLETED", "FAILED", "TIMEOUT"):
        raise ValueError(f"invalid terminal task status: {path}")
    return row


def summarize(rows, config, run_id):
    done = [r for r in rows.values() if r["status"] == "COMPLETED"]
    failed = [r for r in rows.values() if r["status"] != "COMPLETED"]
    total = len(jobs(config))
    pending = total - len(rows)
    counts = {}
    endpoints = []
    with mp.workdps(max(config["precisions"]) + 10):
        for row in done:
            label = row["result"]["screen_status"]
            counts[label] = counts.get(label, 0) + 1
            root = row["result"]["refinements"][-1]
            if root["status"] == "NUMERICAL_CONVERGENCE":
                point = mp.mpc(root["final_sigma"], root["final_t"])
                old = next((r for r in endpoints if abs(point - mp.mpc(r["sigma"], r["t"])) <= mp.mpf(config["agreement_tolerance"])), None)
                if old is None:
                    endpoints.append({"sigma": root["final_sigma"], "t": root["final_t"], "task_ids": [row["task_id"]]})
                else:
                    old["task_ids"].append(row["task_id"])
    stable = counts.get("STABLE_NEAR_LINE", 0)
    disposition = "END" if stable == total and not failed and not pending else "HOLD"
    status = "INCOMPLETE" if pending else ("COMPLETED_WITH_FAILURES" if failed else "COMPLETED")
    return {"schema": "a1-seed-probe-summary-v1", "run_id": run_id, "status": status, "updated_utc": now(),
            "configuration": config, "total_tasks": total, "completed_count": len(done),
            "failed_count": len(failed), "timeout_count": sum(r["status"] == "TIMEOUT" for r in failed),
            "pending_count": pending, "screen_counts": counts,
            "off_line_numerical_task_count": counts.get("OFF_LINE_NUMERICAL_CANDIDATE", 0) if not failed and not pending else None,
            "numerical_review_task_count": len(done) - stable,
            "distinct_high_precision_endpoints": endpoints, "distinct_endpoint_count": len(endpoints),
            "research_status": disposition, "route": "RC:A1", "current_node": "RC:C2",
            "record_id": "A1-PILOT-001", "certified_off_line_zero": False,
            "zero_existence_or_count_certification": "NOT_PERFORMED",
            "interpretation": "Finite free-sigma starts only. Independent point agreement is not root certification; no region is excluded.",
            "next_step": "Choose a new discriminating question before any larger scan." if disposition == "END" else "Review incomplete tasks or numerical anomalies before assigning a candidate."}


def run(outdir, config, max_tasks=0):
    outdir.mkdir(parents=True, exist_ok=True)
    meta = manifest(config)
    with support.run_lock(outdir):
        saved_path = outdir / "manifest.json"
        if saved_path.exists():
            if json.loads(saved_path.read_text(encoding="utf-8"))["run_id"] != meta["run_id"]:
                raise ValueError("config/source/runtime changed; use a new directory")
        elif list(outdir.glob("task-*.json")):
            raise ValueError("task artifacts without a manifest")
        else:
            atomic(saved_path, meta)
        rows = {}
        for job in jobs(config):
            row = load_task(outdir / f"task-{job['task_id']}.json", meta["run_id"], job)
            if row:
                rows[job["task_id"]] = row
        started = time.monotonic()
        launched = 0

        def progress(status, task_id):
            atomic(outdir / "progress.json", {"schema": "a1-seed-probe-progress-v1", "run_id": meta["run_id"],
                   "status": status, "updated_utc": now(), "pid": os.getpid(), "current_task": task_id,
                   "total_tasks": len(jobs(config)), "completed_count": sum(r["status"] == "COMPLETED" for r in rows.values()),
                   "failed_count": sum(r["status"] != "COMPLETED" for r in rows.values()),
                   "pending_count": len(jobs(config)) - len(rows), "elapsed_s_this_session": time.monotonic() - started})

        progress("RUNNING", None)
        for i, job in enumerate(jobs(config)):
            if job["task_id"] in rows:
                continue
            if time.monotonic() - started >= config["max_seconds"] or (max_tasks and launched >= max_tasks):
                break
            progress("RUNNING", job["task_id"])
            path = outdir / f"task-{job['task_id']}.json"
            task_start = time.monotonic()
            error = None
            with (outdir / f"{job['task_id']}.stdout.log").open("w", encoding="utf-8") as stdout, (outdir / f"{job['task_id']}.stderr.log").open("w", encoding="utf-8") as stderr:
                try:
                    proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--output-dir", str(outdir), "--worker", str(i)],
                                          cwd=ROOT, stdout=stdout, stderr=stderr, timeout=config["task_timeout_s"])
                    row = load_task(path, meta["run_id"], job)
                    if row is None or (proc.returncode and row["status"] == "COMPLETED"):
                        error = ("FAILED", f"worker return code {proc.returncode}; missing or inconsistent output")
                except subprocess.TimeoutExpired:
                    error = ("TIMEOUT", "worker exceeded per-task timeout")
            if error:
                row = {"status": error[0], "error": error[1], "run_id": meta["run_id"], "task_id": job["task_id"],
                       "seed": job, "finished_utc": now(), "elapsed_s": time.monotonic() - task_start}
                atomic(path, row)
            rows[job["task_id"]] = row
            launched += 1
            progress("RUNNING", job["task_id"])
            print(json.dumps({"task": job["task_id"], "status": row["status"], "screen": row.get("result", {}).get("screen_status"),
                              "elapsed_s": round(time.monotonic() - task_start, 3)}), flush=True)
        summary = summarize(rows, config, meta["run_id"])
        summary["elapsed_s_this_session"] = time.monotonic() - started
        summary["launched_this_session"] = launched
        atomic(outdir / "summary.json", summary)
        report = ("# A1-PILOT-001: two-sided free-sigma probe\n\n"
                  f"Route: RC:A1; node: RC:C2; disposition: {summary['research_status']}.\n\n"
                  f"Tasks: {summary['completed_count']}/{summary['total_tasks']}; failures: {summary['failed_count']}; pending: {summary['pending_count']}.\n\n"
                  f"Screen counts: {summary['screen_counts']}. Distinct numerical endpoints: {summary['distinct_endpoint_count']}.\n\n"
                  + summary["interpretation"] + "\n\n" + summary["next_step"] + "\n")
        (outdir / "report.md").write_text(report, encoding="utf-8")
        progress(summary["status"], None)
        return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--profile", choices=("smoke", "pilot"), default="pilot")
    ap.add_argument("--worker", type=int)
    ap.add_argument("--max-tasks", type=int, default=0)
    args = ap.parse_args()
    if not args.output_dir.is_absolute():
        ap.error("--output-dir must be absolute")
    if args.max_tasks < 0:
        ap.error("--max-tasks must be nonnegative")
    outdir = args.output_dir.resolve()
    if args.worker is not None:
        return worker(outdir, args.worker)
    result = run(outdir, configuration(args.profile), args.max_tasks)
    print(json.dumps({k: result[k] for k in ("status", "completed_count", "failed_count", "screen_counts", "research_status")}), flush=True)
    return 0 if result["status"] == "COMPLETED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
