"""Chain actual-zeta screening rounds after the current batch finishes.

This supervisor is intentionally conservative: it only launches the next
finite numerical screen after the preceding summary exists, and records every
round independently.  It never promotes a Newton point to a zero certificate.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUNNER = HERE / "zeta_long_batch_py3.py"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def wait_for_summary(path: Path, timeout_s: int) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if data.get("status") in {"COMPLETED", "COMPLETED_WITH_ERRORS"}:
                    return True
            except Exception:
                pass
        time.sleep(30)
    return False


def run_round(profile: str, outdir: Path, timeout: int) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    log = (outdir / "supervisor-child.log").open("a", encoding="utf-8")
    try:
        cmd = [sys.executable, str(RUNNER), "--profile", profile,
               "--output-dir", str(outdir), "--timeout", str(timeout)]
        p = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                           text=True, check=False)
        summary = outdir / "summary.json"
        result = {"profile": profile, "returncode": p.returncode,
                  "summary": str(summary), "finished_utc": now()}
        if summary.exists():
            try:
                result["batch"] = json.loads(summary.read_text(encoding="utf-8"))
            except Exception as exc:
                result["summary_error"] = repr(exc)
        return result
    finally:
        log.close()


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--current-summary", type=Path, default=Path("runs/zeta-long-batch-py3/summary.json"))
    ap.add_argument("--wait-timeout", type=int, default=172800)
    ap.add_argument("--child-timeout", type=int, default=3600)
    ap.add_argument("--output", type=Path, default=Path("runs/zeta-chain-supervisor"))
    args = ap.parse_args()
    current = args.current_summary if args.current_summary.is_absolute() else ROOT / args.current_summary
    args.output.mkdir(parents=True, exist_ok=True)
    state = {"schema": "zeta-chain-supervisor-v1", "started_utc": now(),
             "current_summary": str(current), "status": "WAITING"}
    write(args.output / "state.json", state)
    if not wait_for_summary(current, args.wait_timeout):
        state.update(status="BLOCKED_WAIT_TIMEOUT", finished_utc=now())
        write(args.output / "state.json", state)
        return
    state["current_round_ready"] = True
    state["rounds"] = []
    write(args.output / "state.json", state)
    for profile, name in (("extended", "zeta-extended-batch-py3"),
                          ("extended2", "zeta-extended2-batch-py3")):
        result = run_round(profile, ROOT / "runs" / name, args.child_timeout)
        state["rounds"].append(result)
        state["last_round"] = profile
        state["status"] = "RUNNING" if result.get("returncode") == 0 else "ROUND_FAILED"
        write(args.output / "state.json", state)
        if result.get("returncode") != 0:
            break
    state.update(status="COMPLETED", finished_utc=now())
    write(args.output / "state.json", state)


if __name__ == "__main__":
    main()
