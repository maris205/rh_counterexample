"""Recoverable, bounded interval counts; A1_PILOT_002_PROTOCOL.md."""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import traceback

import flint
from a1_seed_probe_batch_py3 import atomic, now
import common_spectrum_v2_batch_py3 as support

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CERT = HERE.parent / "2026-09-08-zero-lab/certification"
sys.path.insert(0, str(CERT))
import rectangle_count as counter
from run_checks import FIXTURES


def config_for(profile):
    tasks = []
    if profile == "smoke":
        fixtures = list(FIXTURES) + [
            ("float_coordinate_rejected", (.49, "0.51", "14.13", "14.14"), {}, "rejected", None),
            ("invalid_rectangle_rejected", ("0.7", "0.6", "14", "15"), {}, "rejected", None)]
        for key, rect, kwargs, status, count in fixtures:
            tasks.append({"task_id": key, "rectangle": list(rect), "kwargs": kwargs,
                          "expected_status": status, "expected_count": count, "role": "calibration"})
    else:
        for role, rect in [("target", ["0.5001", "0.70", "10010", "10011"]),
                           ("comparison", ["0.49", "0.51", "10010", "10011"])]:
            for dps in [40, 70]:
                tasks.append({"task_id": f"{role}-dps{dps}", "rectangle": rect,
                              "kwargs": {"dps": dps}, "role": role})
    return {"profile": profile, "tasks": tasks, "defaults": {"dps": 60, "max_depth": 26,
            "max_evaluations": 30000, "max_seconds": 60.0, "include_segments": True},
            "protocol": "A1_PILOT_002_PROTOCOL.md", "record_id": "A1-PILOT-002"}


def manifest(config):
    files = [Path(__file__), CERT / "rectangle_count.py", CERT / "run_checks.py",
             HERE / "a1_seed_probe_batch_py3.py", Path(support.__file__), HERE / config["protocol"]]
    payload = {"schema": "a1-rectangle-probe-v1", "configuration": config,
               "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
               "runtime": {"python": sys.version, "executable": sys.executable,
                           "platform": platform.platform(), "python_flint": flint.__version__}}
    return {**payload, "run_id": support.fingerprint(payload)}


def audit_segments(result):
    """Check exact boundary coverage independently of display interval strings."""
    if result["status"] != "certified":
        assert result["count"] is None and not result["off_line_certified"]
        return {"status": "NOT_APPLICABLE"}
    a, b, c, d = (Fraction(result["rectangle_exact"][key]) for key in "abcd")
    vertices = [(a, c), (b, c), (b, d), (a, d), (a, c)]
    segments = result["segments"]
    assert len(segments) == result["accepted_segments"] and segments
    expected_start = vertices[0]
    edge = 0
    for segment in segments:
        start = tuple(map(Fraction, segment["start_exact"]))
        stop = tuple(map(Fraction, segment["stop_exact"]))
        assert start == expected_start and start != stop and edge < 4
        if edge == 0:
            valid = start[1] == stop[1] == c and a <= start[0] < stop[0] <= b
        elif edge == 1:
            valid = start[0] == stop[0] == b and c <= start[1] < stop[1] <= d
        elif edge == 2:
            valid = start[1] == stop[1] == d and a <= stop[0] < start[0] <= b
        else:
            valid = start[0] == stop[0] == a and c <= stop[1] < start[1] <= d
        assert valid and segment["image_finite_and_excludes_zero"]
        assert segment["increment_strictly_between_minus_pi_and_pi"]
        expected_start = stop
        if stop == vertices[edge + 1]:
            edge += 1
    assert edge == 4 and expected_start == vertices[0]
    assert result["boundary_certified_zero_free"]
    return {"status": "PASSED", "closed_counterclockwise_exact_boundary": True,
            "accepted_segments": len(segments), "interval_decisions_recomputed_here": False}


def evaluate(job, config):
    previous = flint.ctx.prec
    result = counter.count_rectangle(*job["rectangle"], **{**config["defaults"], **job["kwargs"]})
    assert flint.ctx.prec == previous, "global precision context was not restored"
    audit = audit_segments(result)
    if config["profile"] == "smoke":
        assert result["status"] == job["expected_status"] and result["count"] == job["expected_count"]
        assert not result["off_line_certified"]
    return {"count_result": result, "structural_audit": audit, "precision_context_restored": True}


def summarize(rows, config, run_id):
    done = [row for row in rows.values() if row["status"] == "COMPLETED"]
    failed = [row for row in rows.values() if row["status"] == "FAILED"]
    pending = len(config["tasks"]) - len(rows)
    status = "INCOMPLETE" if pending else ("COMPLETED_WITH_FAILURES" if failed else "COMPLETED")
    result = {"schema": "a1-rectangle-probe-summary-v1", "run_id": run_id, "status": status,
              "updated_utc": now(), "record_id": "A1-PILOT-002", "route": "RC:A1",
              "current_node": "RC:E1", "total_tasks": len(config["tasks"]),
              "completed_count": len(done), "failed_count": len(failed), "pending_count": pending,
              "configuration": config, "research_status": "HOLD", "certified_target_zero_free": False,
              "target_zero_count": None, "comparison_zero_count": None,
              "candidate_rectangle_count": None, "counterexample_claim": False,
              "task_results": [{"task_id": r["task_id"], "role": r["job"]["role"],
                                "count_status": r["result"]["count_result"]["status"],
                                "count": r["result"]["count_result"]["count"],
                                "evaluations": r["result"]["count_result"].get("function_evaluations", 0),
                                "elapsed_s": r["elapsed_s"]} for r in done]}
    if config["profile"] == "smoke":
        result.update(current_node="RC:C1", all_checks_passed=status == "COMPLETED",
                      research_status="GO" if status == "COMPLETED" else "HOLD")
        return result
    if status == "COMPLETED":
        counts = {}
        for role in ("target", "comparison"):
            records = [r["result"]["count_result"] for r in done if r["job"]["role"] == role]
            counts[role] = records[0]["count"] if len(records) == 2 and all(
                r["status"] == "certified" and r["count"] == records[0]["count"] for r in records) else None
        result.update(target_zero_count=counts["target"], comparison_zero_count=counts["comparison"],
                      candidate_rectangle_count=(int(counts["target"] > 0) if counts["target"] is not None else None))
        if counts["target"] == 0 and counts["comparison"] == 2:
            result.update(research_status="END", certified_target_zero_free=True)
    result["interpretation"] = "Scoped interval zero counts, conditional on audited code and FLINT; display strings are not a standalone proof object. No whole-band/RH conclusion."
    return result


def run(outdir, config, smoke_dir=None, max_tasks=0):
    meta = manifest(config)
    if config["profile"] == "pilot":
        if smoke_dir is None:
            raise ValueError("pilot requires --smoke-dir")
        smoke_summary = json.loads((smoke_dir / "summary.json").read_text())
        smoke_meta = json.loads((smoke_dir / "manifest.json").read_text())
        if smoke_meta["run_id"] != manifest(config_for("smoke"))["run_id"] or smoke_summary["run_id"] != smoke_meta["run_id"] or not smoke_summary.get("all_checks_passed"):
            raise ValueError("matching current-source smoke calibration required")
        meta["smoke_reference"] = {"run_id": smoke_meta["run_id"], "summary_sha256": hashlib.sha256((smoke_dir / "summary.json").read_bytes()).hexdigest()}
    outdir.mkdir(parents=True, exist_ok=True)
    with support.run_lock(outdir):
        path = outdir / "manifest.json"
        if path.exists():
            if json.loads(path.read_text()) != meta:
                raise ValueError("source/runtime/config/smoke changed; use a new directory")
        elif list(outdir.glob("task-*.json")):
            raise ValueError("artifacts without manifest")
        else:
            atomic(path, meta)
        rows = {}
        for job in config["tasks"]:
            path = outdir / f"task-{job['task_id']}.json"
            if path.exists():
                row = json.loads(path.read_text())
                if row["run_id"] != meta["run_id"] or row["job"] != job or row["status"] not in ("COMPLETED", "FAILED"):
                    raise ValueError("mismatched task")
                rows[job["task_id"]] = row
        started = time.monotonic()

        def progress(status, key):
            atomic(outdir / "progress.json", {"run_id": meta["run_id"], "status": status, "updated_utc": now(),
                   "current_task": key, "pid": __import__('os').getpid(), "total_tasks": len(config["tasks"]),
                   "completed_count": sum(r["status"] == "COMPLETED" for r in rows.values()),
                   "failed_count": sum(r["status"] == "FAILED" for r in rows.values()),
                   "pending_count": len(config["tasks"]) - len(rows)})

        launched = 0
        progress("RUNNING", None)
        for job in config["tasks"]:
            key = job["task_id"]
            if key in rows:
                continue
            if max_tasks and launched >= max_tasks:
                break
            progress("RUNNING", key)
            begin = time.monotonic()
            try:
                row = {"status": "COMPLETED", "result": evaluate(job, config)}
            except Exception as exc:
                traceback.print_exc()
                row = {"status": "FAILED", "error": repr(exc)}
            row.update(run_id=meta["run_id"], task_id=key, job=job, elapsed_s=time.monotonic() - begin, finished_utc=now())
            atomic(outdir / f"task-{key}.json", row)
            rows[key] = row
            launched += 1
            progress("RUNNING", key)
            print(json.dumps({"task": key, "status": row["status"], "count_status": row.get("result", {}).get("count_result", {}).get("status"),
                              "count": row.get("result", {}).get("count_result", {}).get("count"), "elapsed_s": round(row["elapsed_s"], 3)}), flush=True)
        summary = summarize(rows, config, meta["run_id"])
        summary.update(elapsed_s_this_session=time.monotonic() - started, launched_this_session=launched)
        atomic(outdir / "summary.json", summary)
        (outdir / "report.md").write_text("# A1-PILOT-002\n\n" + f"Route RC:A1; node {summary['current_node']}; disposition {summary['research_status']}.\n\n"
            + f"Completed {summary['completed_count']}/{summary['total_tasks']}; failed {summary['failed_count']}; pending {summary['pending_count']}.\n\n"
            + f"Target count: {summary['target_zero_count']}; comparison count: {summary['comparison_zero_count']}.\n\n"
            + "Only the exact configured rectangles are addressed. Display enclosures are audit logs, not standalone proof objects.\n", encoding="utf-8")
        progress(summary["status"], None)
        return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("smoke", "pilot"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--smoke-dir", type=Path)
    parser.add_argument("--max-tasks", type=int, default=0)
    args = parser.parse_args()
    if not args.output_dir.is_absolute() or args.max_tasks < 0:
        parser.error("absolute output directory and nonnegative max-tasks required")
    result = run(args.output_dir.resolve(), config_for(args.profile), args.smoke_dir, args.max_tasks)
    print(json.dumps({k: result[k] for k in ["status", "completed_count", "failed_count", "research_status", "target_zero_count", "comparison_zero_count"]}), flush=True)
    raise SystemExit(0 if result["status"] == "COMPLETED" else 1)
