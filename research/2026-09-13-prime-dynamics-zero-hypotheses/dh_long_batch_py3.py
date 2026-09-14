"""Resumable multi-hour DH contour subdivision batch (Python 3.10).

Each task invokes the existing Arb-backed boundary subdivision in a fresh
process, so one numerical failure cannot corrupt the rest of the sweep. The
batch is an audit of enclosure stability; it never upgrades a result to a
proof by itself.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).with_name("dh_contour_subdivision_py3.py")


def task_grid() -> list[dict]:
    jobs: list[dict] = []
    # Broad-to-tight rectangles at the baseline EM resolution.
    for ds in ("0.02", "0.01", "0.005", "0.002"):
        for edge in (16, 32, 64, 128, 256, 512, 1024):
            jobs.append({"ds": ds, "dt": ds, "edge_points": edge, "n": 128, "m": 12})
    # Higher EM orders on the two smallest rectangles.
    for ds in ("0.005", "0.002"):
        for edge in (64, 128, 256, 512):
            for n, m in ((64, 10), (256, 14), (384, 16)):
                jobs.append({"ds": ds, "dt": ds, "edge_points": edge, "n": n, "m": m})
    return jobs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, default=Path("runs/dh-long-batch-py3"))
    ap.add_argument("--timeout", type=int, default=1800, help="seconds per task")
    ap.add_argument("--max-jobs", type=int, default=0, help="0 means all planned tasks")
    args = ap.parse_args()
    outdir = args.output_dir
    outdir.mkdir(parents=True, exist_ok=True)
    jobs = task_grid()
    if args.max_jobs:
        jobs = jobs[:args.max_jobs]
    manifest = {"status": "RUNNING", "python": sys.version, "script": str(SCRIPT), "planned_jobs": jobs}
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    summary: list[dict] = []
    for idx, job in enumerate(jobs):
        stem = f"job-{idx:03d}-ds{job['ds']}-e{job['edge_points']}-n{job['n']}-m{job['m']}"
        output = outdir / f"{stem}.json"
        if output.exists():
            summary.append({"index": idx, "status": "SKIPPED_EXISTING", "output": str(output), **job})
            continue
        cmd = [sys.executable, str(SCRIPT), "--ds", job["ds"], "--dt", job["dt"],
               "--edge-points", str(job["edge_points"]), "--n", str(job["n"]),
               "--m", str(job["m"]), "--output", str(output)]
        started = time.time()
        try:
            proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=args.timeout)
            rec = {"index": idx, "status": "COMPLETED" if proc.returncode == 0 else "FAILED",
                   "returncode": proc.returncode, "elapsed_s": time.time() - started,
                   "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-2000:],
                   "output": str(output), **job}
        except subprocess.TimeoutExpired as exc:
            rec = {"index": idx, "status": "TIMEOUT", "elapsed_s": time.time() - started,
                   "stdout": str(exc.stdout)[-1000:], "stderr": str(exc.stderr)[-1000:],
                   "output": str(output), **job}
        summary.append(rec)
        (outdir / "progress.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"index": idx, "status": rec["status"], "elapsed_s": rec.get("elapsed_s"), "output": str(output)}), flush=True)
    result = {"status": "COMPLETED", "planned": len(jobs), "summary": summary,
              "interpretation": "Long-run stability sweep only; NONCERTIFIED unless a separate interval argument audit is completed."}
    (outdir / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "planned": len(jobs), "output": str(outdir / 'summary.json')}), flush=True)


if __name__ == "__main__":
    main()
