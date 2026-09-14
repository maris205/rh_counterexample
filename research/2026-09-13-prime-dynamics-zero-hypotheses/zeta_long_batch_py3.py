"""Resumable long batch for actual-zeta free-sigma screening.

The batch freezes height and sigma windows before evaluating zeta.  Each child
has its own JSON result and timeout, so an interrupted desktop run can resume
without changing completed windows.  Outputs are numerical diagnostics only.
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CHILD = HERE / "zeta_window_scan_py3.py"


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp-{os.getpid()}")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def jobs(profile: str) -> list[dict]:
    if profile == "smoke":
        return [{"t_min": 40, "t_max": 80, "t_step": 1, "sigma_min": .52,
                 "sigma_max": .98, "sigma_step": .04, "dps": 35, "refine_dps": 60}]
    if profile == "extended":
        out = []
        for t0 in range(2000, 4000, 80):
            for s0, s1 in ((.52, .72), (.70, .92), (.90, .98)):
                out.append({"t_min": t0, "t_max": t0 + 80, "t_step": 1.0,
                            "sigma_min": s0, "sigma_max": s1, "sigma_step": .01,
                            "dps": 45, "refine_dps": 80})
        return out
    if profile == "extended2":
        out = []
        for t0 in range(4000, 6000, 80):
            for s0, s1 in ((.52, .72), (.70, .92), (.90, .98)):
                out.append({"t_min": t0, "t_max": t0 + 80, "t_step": 1.0,
                            "sigma_min": s0, "sigma_max": s1, "sigma_step": .01,
                            "dps": 50, "refine_dps": 90})
        return out
    # Three overlapping sigma bands and contiguous height blocks.  The overlap
    # gives a simple consistency check at sigma=.70 and .90 without selecting
    # windows using zeta values.
    out = []
    for t0 in range(40, 2000, 80):
        for s0, s1 in ((.52, .72), (.70, .92), (.90, .98)):
            out.append({"t_min": t0, "t_max": t0 + 80, "t_step": 1.0,
                        "sigma_min": s0, "sigma_max": s1, "sigma_step": .01,
                        "dps": 40, "refine_dps": 70})
    return out


def stem(i: int, job: dict) -> str:
    return f"job-{i:03d}-t{int(job['t_min'])}-{int(job['t_max'])}-s{job['sigma_min']:.2f}-{job['sigma_max']:.2f}"


def valid(path: Path, job: dict) -> bool:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        c = d.get("configuration", {})
        return d.get("status") == "COMPLETED_NUMERICAL" and all(float(c[k]) == float(v) for k, v in job.items())
    except Exception:
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=("long", "extended", "extended2", "smoke"), default="long")
    ap.add_argument("--output-dir", type=Path, default=Path("runs/zeta-long-batch-py3"))
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--max-jobs", type=int, default=0)
    ap.add_argument("--start", type=int, default=0)
    args = ap.parse_args()
    outdir = args.output_dir if args.output_dir.is_absolute() else Path.cwd() / args.output_dir
    planned = jobs(args.profile)
    selected = planned[args.start:]
    if args.max_jobs:
        selected = selected[: args.max_jobs]
    manifest = {"schema": "zeta-long-batch-py3-v1", "status": "RUNNING", "created_utc": utc(),
                "profile": args.profile, "planned_jobs": selected, "child": str(CHILD),
                "timeout_s": args.timeout,
                "interpretation": "Actual-zeta finite screening; no RH or zero certification."}
    manifest["manifest_sha256"] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    atomic(outdir / "manifest.json", manifest)
    entries = []
    progress = outdir / "progress.json"
    for local, job in enumerate(selected):
        i = local + args.start
        output = outdir / (stem(i, job) + ".json")
        if valid(output, job):
            rec = {"index": i, "status": "SKIPPED_EXISTING", "output": str(output), **job}
            entries.append(rec); atomic(progress, {"updated_utc": utc(), "entries": entries}); continue
        cmd = [sys.executable, str(CHILD)]
        for k, v in job.items(): cmd.extend([f"--{k.replace('_', '-')}", str(v)])
        cmd.extend(["--output", str(output)])
        start = time.monotonic()
        try:
            p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=args.timeout)
            rec = {"index": i, "status": "COMPLETED" if p.returncode == 0 else "FAILED",
                   "returncode": p.returncode, "elapsed_s": time.monotonic()-start,
                   "stdout_tail": p.stdout[-2000:], "stderr_tail": p.stderr[-2000:],
                   "output": str(output), **job}
        except subprocess.TimeoutExpired as exc:
            rec = {"index": i, "status": "TIMEOUT", "elapsed_s": time.monotonic()-start,
                   "stdout_tail": str(exc.stdout)[-1000:], "stderr_tail": str(exc.stderr)[-1000:],
                   "output": str(output), **job}
        entries.append(rec); atomic(progress, {"updated_utc": utc(), "entries": entries})
        print(json.dumps({"index": i, "status": rec["status"], "elapsed_s": rec.get("elapsed_s")}, ensure_ascii=False), flush=True)
    counts = {}
    for e in entries: counts[e["status"]] = counts.get(e["status"], 0) + 1
    final = "COMPLETED" if not any(k in counts for k in ("FAILED", "TIMEOUT")) else "COMPLETED_WITH_ERRORS"
    result = {"schema": manifest["schema"], "status": final, "finished_utc": utc(),
              "planned": len(selected), "counts": counts, "entries": entries,
              "interpretation": "Every child output is a numerical candidate screen; independent Arb contour work is still required."}
    atomic(outdir / "summary.json", result); atomic(outdir / "manifest.json", {**manifest, "status": final, "counts": counts})
    print(json.dumps({"status": final, "counts": counts, "summary": str(outdir/"summary.json")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
