"""Resumable multi-hour DH contour audit (Python 3.10+).

This driver deliberately runs every numerical configuration in a fresh
process.  A failed or timed-out configuration is recorded and the remaining
grid continues.  Existing, valid JSON outputs are reused, so the command can
be interrupted and restarted safely.  The child evaluator currently reports
``NONCERTIFIED_SUBDIVISION``; this batch never upgrades that status to a
theorem-level zero count.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
# The research tree is nested one level below the repository.  Resolve this
# explicitly rather than assuming the workspace root; this keeps outputs under
# ``rh_counterexample_pc/runs`` when the command is launched from the repo.
_candidates = (HERE.parents[1], HERE.parents[2])
ROOT = next((p for p in _candidates if (p / "requirements.txt").exists()), HERE.parents[1])
CHILD = HERE / "dh_contour_subdivision_py3.py"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp-{os.getpid()}")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def planned_jobs(profile: str) -> list[dict[str, Any]]:
    if profile == "smoke":
        return [{"ds": "0.01", "dt": "0.01", "edge_points": e, "n": 64, "m": 10}
                for e in (16, 32)]
    # The long profile is intentionally broad-to-tight and includes high EM
    # orders.  On a desktop this is a multi-hour audit, not a short smoke run.
    jobs: list[dict[str, Any]] = []
    for ds in ("0.02", "0.01", "0.005", "0.002"):
        for edge in (16, 32, 64, 128, 256, 512, 1024, 2048, 4096):
            jobs.append({"ds": ds, "dt": ds, "edge_points": edge, "n": 128, "m": 12})
    for ds in ("0.005", "0.002", "0.001"):
        for edge in (64, 128, 256, 512, 1024, 2048):
            for n, m in ((64, 10), (256, 14), (384, 16), (512, 18)):
                jobs.append({"ds": ds, "dt": ds, "edge_points": edge, "n": n, "m": m})
    return jobs


def job_stem(index: int, job: dict[str, Any]) -> str:
    return (f"job-{index:03d}-ds{job['ds']}-dt{job['dt']}-e{job['edge_points']}"
            f"-n{job['n']}-m{job['m']}")


def valid_existing(path: Path, job: dict[str, Any]) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        cfg = data.get("configuration", {})
        return (str(data.get("status", "")).startswith("NONCERTIFIED")
                and str(cfg.get("ds")) == str(job["ds"])
                and str(cfg.get("dt")) == str(job["dt"])
                and int(cfg.get("edge_points")) == int(job["edge_points"])
                and int(cfg.get("n")) == int(job["n"])
                and int(cfg.get("m")) == int(job["m"]))
    except (OSError, ValueError, TypeError, KeyError):
        return False


def main() -> None:
    if sys.version_info < (3, 10):
        raise SystemExit("Python 3.10+ is required; use py -3.10")
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=("long", "smoke"), default="long")
    ap.add_argument("--output-dir", type=Path, default=Path("runs/dh-long-batch-py3-v2"))
    ap.add_argument("--timeout", type=int, default=3600, help="per-task timeout in seconds")
    ap.add_argument("--max-jobs", type=int, default=0, help="limit prefix; 0 means all")
    ap.add_argument("--start", type=int, default=0, help="skip planned jobs before this index")
    args = ap.parse_args()
    outdir = args.output_dir if args.output_dir.is_absolute() else Path.cwd() / args.output_dir
    outdir.mkdir(parents=True, exist_ok=True)
    jobs = planned_jobs(args.profile)
    if args.start:
        jobs = jobs[args.start:]
    if args.max_jobs:
        jobs = jobs[:args.max_jobs]

    manifest = {
        "schema": "dh-long-batch-v2",
        "status": "RUNNING",
        "created_utc": utc_now(),
        "python": sys.version,
        "python_executable": sys.executable,
        "child": str(CHILD),
        "profile": args.profile,
        "timeout_s": args.timeout,
        "planned_jobs": jobs,
        "interpretation": "Numerical enclosure stability audit only; every child result remains NONCERTIFIED_SUBDIVISION.",
    }
    manifest_bytes = json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode("utf-8")
    manifest["manifest_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
    atomic_json(outdir / "manifest.json", manifest)
    (outdir / "manifest.sha256").write_text(manifest["manifest_sha256"] + "  manifest.json\n", encoding="utf-8")

    entries: list[dict[str, Any]] = []
    progress_path = outdir / "progress.json"
    for local_idx, job in enumerate(jobs):
        # Keep the original global index in the output name when --start is used.
        idx = local_idx + args.start
        stem = job_stem(idx, job)
        output = outdir / f"{stem}.json"
        if valid_existing(output, job):
            rec = {"index": idx, "status": "SKIPPED_EXISTING", "output": str(output), **job}
            entries.append(rec)
            atomic_json(progress_path, {"updated_utc": utc_now(), "entries": entries})
            print(json.dumps({"index": idx, "status": rec["status"], "output": str(output)}, ensure_ascii=False), flush=True)
            continue

        cmd = [sys.executable, str(CHILD), "--ds", job["ds"], "--dt", job["dt"],
               "--edge-points", str(job["edge_points"]), "--n", str(job["n"]),
               "--m", str(job["m"]), "--output", str(output)]
        started = time.monotonic()
        try:
            proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                                  timeout=args.timeout)
            elapsed = time.monotonic() - started
            status = "COMPLETED_NONCERTIFIED" if proc.returncode == 0 else "FAILED"
            rec = {"index": idx, "status": status, "returncode": proc.returncode,
                   "elapsed_s": elapsed, "stdout_tail": proc.stdout[-2000:],
                   "stderr_tail": proc.stderr[-2000:], "output": str(output), **job}
        except subprocess.TimeoutExpired as exc:
            rec = {"index": idx, "status": "TIMEOUT", "elapsed_s": time.monotonic() - started,
                   "stdout_tail": str(exc.stdout)[-1000:], "stderr_tail": str(exc.stderr)[-1000:],
                   "output": str(output), **job}
        except OSError as exc:
            rec = {"index": idx, "status": "LAUNCH_ERROR", "error": repr(exc),
                   "elapsed_s": time.monotonic() - started, "output": str(output), **job}
        entries.append(rec)
        atomic_json(progress_path, {"updated_utc": utc_now(), "entries": entries})
        print(json.dumps({"index": idx, "status": rec["status"],
                          "elapsed_s": rec.get("elapsed_s"), "output": str(output)}, ensure_ascii=False), flush=True)

    counts: dict[str, int] = {}
    for rec in entries:
        counts[rec["status"]] = counts.get(rec["status"], 0) + 1
    final_status = "COMPLETED" if not any(k in counts for k in ("FAILED", "TIMEOUT", "LAUNCH_ERROR")) else "COMPLETED_WITH_ERRORS"
    result = {"schema": "dh-long-batch-v2", "status": final_status, "finished_utc": utc_now(),
              "planned": len(jobs), "counts": counts, "entries": entries,
              "interpretation": "NONCERTIFIED_SUBDIVISION outputs are diagnostics, not a rigorous argument-principle certificate."}
    atomic_json(outdir / "summary.json", result)
    atomic_json(outdir / "manifest.json", {**manifest, "status": final_status, "finished_utc": result["finished_utc"], "counts": counts})
    print(json.dumps({"status": final_status, "counts": counts, "summary": str(outdir / "summary.json")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
