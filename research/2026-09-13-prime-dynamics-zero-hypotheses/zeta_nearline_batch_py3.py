"""Resumable near-critical-line zeta screening (numerical only).

This batch intentionally starts above Re(s)=1/2 and scans new heights
6000<=Im(s)<=10000.  It is complementary to the earlier 0.52--0.98 scans:
the narrow bands and their overlap test whether a putative off-line valley
can hide very close to the critical line.  Outputs are candidate screens and
never constitute a zero certificate.
"""
from __future__ import annotations

import argparse, hashlib, json, os, subprocess, sys, time
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
        return [{"t_min": 6000, "t_max": 6010, "t_step": 1.0,
                 "sigma_min": .5005, "sigma_max": .54, "sigma_step": .005,
                 "dps": 45, "refine_dps": 80}]
    out = []
    # 40 disjoint height blocks, two overlapping near-line bands per block.
    for t0 in range(6000, 10000, 100):
        for s0, s1 in ((.5005, .54), (.53, .62)):
            out.append({"t_min": t0, "t_max": t0 + 100, "t_step": 1.0,
                        "sigma_min": s0, "sigma_max": s1, "sigma_step": .002,
                        "dps": 55, "refine_dps": 95})
    return out

def stem(i: int, j: dict) -> str:
    return f"job-{i:03d}-t{int(j['t_min'])}-{int(j['t_max'])}-s{j['sigma_min']:.4f}-{j['sigma_max']:.2f}"

def valid(path: Path, job: dict) -> bool:
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
        c = d.get("configuration", {})
        return d.get("status") == "COMPLETED_NUMERICAL" and all(float(c[k]) == float(v) for k, v in job.items())
    except Exception:
        return False

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=("long", "smoke"), default="long")
    ap.add_argument("--output-dir", type=Path, default=Path("runs/zeta-nearline-batch-py3"))
    ap.add_argument("--timeout", type=int, default=2400)
    ap.add_argument("--max-jobs", type=int, default=0)
    args = ap.parse_args()
    outdir = args.output_dir if args.output_dir.is_absolute() else Path.cwd() / args.output_dir
    planned = jobs(args.profile)
    if args.max_jobs: planned = planned[:args.max_jobs]
    manifest = {"schema":"zeta-nearline-batch-py3-v1", "status":"RUNNING", "created_utc":utc(),
                "profile":args.profile, "planned_jobs":planned, "child":str(CHILD), "timeout_s":args.timeout,
                "interpretation":"Finite near-critical-line actual-zeta screening; no RH or zero certification."}
    manifest["manifest_sha256"] = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    atomic(outdir / "manifest.json", manifest)
    entries=[]; progress=outdir / "progress.json"
    for i, job in enumerate(planned):
        output=outdir/(stem(i,job)+".json")
        if valid(output,job):
            rec={"index":i,"status":"SKIPPED_EXISTING","output":str(output),**job}
            entries.append(rec); atomic(progress,{"updated_utc":utc(),"entries":entries}); continue
        cmd=[sys.executable,str(CHILD)]
        for k,v in job.items(): cmd.extend([f"--{k.replace('_','-')}",str(v)])
        cmd.extend(["--output",str(output)])
        started=time.monotonic()
        try:
            p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=args.timeout)
            rec={"index":i,"status":"COMPLETED" if p.returncode==0 else "FAILED","returncode":p.returncode,
                 "elapsed_s":time.monotonic()-started,"stdout_tail":p.stdout[-2000:],"stderr_tail":p.stderr[-2000:],
                 "output":str(output),**job}
        except subprocess.TimeoutExpired as exc:
            rec={"index":i,"status":"TIMEOUT","elapsed_s":time.monotonic()-started,
                 "stdout_tail":str(exc.stdout)[-1000:],"stderr_tail":str(exc.stderr)[-1000:],"output":str(output),**job}
        entries.append(rec); atomic(progress,{"updated_utc":utc(),"entries":entries})
        print(json.dumps({"index":i,"status":rec["status"],"elapsed_s":rec.get("elapsed_s")},ensure_ascii=False),flush=True)
    counts={}
    for e in entries: counts[e["status"]]=counts.get(e["status"],0)+1
    final="COMPLETED" if not any(k in counts for k in ("FAILED","TIMEOUT")) else "COMPLETED_WITH_ERRORS"
    result={"schema":manifest["schema"],"status":final,"finished_utc":utc(),"planned":len(planned),"counts":counts,
            "entries":entries,"interpretation":"Numerical candidate screen only; independent Arb rectangle audit required."}
    atomic(outdir/"summary.json",result); atomic(outdir/"manifest.json",{**manifest,"status":final,"counts":counts})
    print(json.dumps({"status":final,"counts":counts,"summary":str(outdir/"summary.json")},ensure_ascii=False),flush=True)

if __name__ == "__main__": main()
