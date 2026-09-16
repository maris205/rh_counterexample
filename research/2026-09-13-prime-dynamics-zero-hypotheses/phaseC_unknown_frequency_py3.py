"""Unknown-frequency transfer calibration for periodic family fixtures."""
import argparse
from pathlib import Path
import hashlib
import json
import traceback

import common_spectrum_v2 as core
import common_spectrum_v2_batch_py3 as batch
import family_detector_transfer as fdt
import numpy as np


def select_and_holdout(y, u, frequencies, cuts, top_k=3):
    boundary = min(cuts)
    train = u < u[int(boundary * len(u))]
    scores = []
    for t in frequencies:
        base, full = core.designs(u[train], float(t), 0.)
        b0 = np.linalg.lstsq(base, y[train], rcond=None)[0]
        b1 = np.linalg.lstsq(full, y[train], rcond=None)[0]
        e0 = float(np.sum((y[train] - base @ b0) ** 2))
        e1 = float(np.sum((y[train] - full @ b1) ** 2))
        scores.append((float(t), (e0 - e1) / e0 if e0 > 1e-20 else -1e6))
    scores.sort(key=lambda row: (-row[1], row[0]))
    selected = []
    for t, s in scores:
        if all(abs(t - x["t"]) >= .5 for x in selected):
            selected.append({"t": t, "training_gain": s})
            if len(selected) == top_k:
                break
    for row in selected:
        gains = []
        for split in cuts:
            cut = int(split * len(u))
            g, _ = core.prediction_gains(u, y[:, None], cut, row["t"], 0., cut)
            gains.append(float(g[0]))
        row["holdout_gains"] = gains
        row["joint_score"] = min(gains)
        row["positive_all_cuts"] = all(g > 0 for g in gains)
    return selected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    outdir = args.output_dir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    config = {"families": ["dh", "chi4", "chi5"], "n": 200000, "samples": 1024,
              "cuts": [.55, .75], "control_reps": 19, "block_size": 5000,
              "t_min": 4., "t_max": 100., "t_step": .25, "top_k": 3, "seed": 20260916,
              "scope": "periodic-family detector transfer; no zeta inference"}
    manifest = batch.manifest_for(config)
    for name in (Path(__file__).name, "family_detector_transfer.py"):
        manifest["source_sha256"][name] = hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
    manifest.pop("run_id")
    manifest["run_id"] = batch.fingerprint(manifest)
    with batch.run_lock(outdir):
        batch.check_manifest(outdir, manifest)
        tasks = [(f"{family}-real", family, None, 0) for family in config["families"]]
        tasks += [(f"{family}-{mode}-{rep:04d}", family, mode, rep)
                  for family in config["families"] for mode in ("global", "block") for rep in range(config["control_reps"])]
        artifacts = {}
        for key, family, mode, rep in tasks:
            path = outdir / f"task-{key}.json"
            row = batch.completed_task(path, manifest["run_id"], key)
            if row is None:
                try:
                    spec = fdt.FAMILIES[family]
                    a = fdt.coefficient_array(spec["period"], config["n"], False)
                    u, idx = fdt.log_grid(config["n"], config["samples"])
                    if mode is not None:
                        seed = int.from_bytes(hashlib.sha256(f"{config['seed']}:{family}:{mode}:{rep}".encode()).digest()[:8], "big")
                        a = fdt.shuffled(a, np.random.default_rng(seed), mode, config["block_size"])
                    _, signal = fdt.signal_from_coefficients(a, u, idx, spec["target"]["sigma"])
                    frequencies = np.arange(config["t_min"], config["t_max"] + .125, config["t_step"])
                    selected = select_and_holdout(signal, u, frequencies, config["cuts"], config["top_k"])
                    target = float(spec["target"]["t"])
                    row = {"status": "COMPLETED", "family": family, "mode": mode, "replicate": rep,
                           "selected": selected, "target_t": target,
                           "target_recovered": any(abs(x["t"] - target) <= .25 for x in selected),
                           "max_statistic": max((x["joint_score"] for x in selected), default=-1e6)}
                    json.dumps(row, allow_nan=False)
                except Exception as exc:
                    traceback.print_exc()
                    row = {"status": "FAILED", "error": repr(exc), "family": family, "mode": mode, "replicate": rep}
                row.update(run_id=manifest["run_id"], task_id=key)
                batch.atomic_json(path, row)
            artifacts[key] = row
            batch.atomic_json(outdir / "progress.json", {"status": "RUNNING", "run_id": manifest["run_id"],
                              "completed_count": sum(v["status"] == "COMPLETED" for v in artifacts.values()),
                              "failed_count": sum(v["status"] == "FAILED" for v in artifacts.values()),
                              "total_tasks": len(tasks), "last_task": key, "updated": batch.now()})
        summary_rows = []
        for family in config["families"]:
            real = artifacts[f"{family}-real"]
            for mode in ("global", "block"):
                nulls = [artifacts[f"{family}-{mode}-{r:04d}"]["max_statistic"] for r in range(config["control_reps"])]
                score = real["max_statistic"]
                summary_rows.append({"family": family, "target_t": real["target_t"], "target_recovered": real["target_recovered"],
                                     "control": mode, "observed_max_statistic": score,
                                     "empirical_rank_p": (1 + sum(x >= score for x in nulls)) / (len(nulls) + 1),
                                     "replicates": len(nulls), "scan_adjusted": True})
        failed = sum(v["status"] == "FAILED" for v in artifacts.values())
        summary = {"schema": "phaseC-unknown-frequency-v1", "status": "COMPLETED_WITH_FAILURES" if failed else "COMPLETED",
                   "run_id": manifest["run_id"], "configuration": config, "completed_count": len(artifacts) - failed,
                   "failed_count": failed, "total_tasks": len(tasks), "rows": summary_rows,
                   "candidate_count": None, "gate_status": "NOT_EVALUATED", "full_protocol_status": "INCOMPLETE",
                   "interpretation": "This is a detector transfer calibration on periodic family fixtures. Each surrogate repeats unknown-frequency selection and frozen holdout scoring. It is not an actual zeta search, family-zero certification, or evidence that a family fixture transfers to zeta.",
                   "missing_gates": ["certified family targets", "cross-channel arithmetic joint gate", "actual zeta evaluation", "Arb/FLINT certification"]}
        batch.atomic_json(outdir / "summary.json", summary)
        batch.atomic_json(outdir / "progress.json", {k: summary[k] for k in ("status", "completed_count", "failed_count", "total_tasks")})
        lines = ["# Phase C unknown-frequency family transfer", "", summary["interpretation"], "",
                 "| family | target t | control | recovered | observed max | empirical p | B |", "|---|---:|---|---|---:|---:|---:|"]
        lines += [f"| {r['family']} | {r['target_t']:.6g} | {r['control']} | {r['target_recovered']} | {r['observed_max_statistic']:.6g} | {r['empirical_rank_p']:.6g} | {r['replicates']} |" for r in summary_rows]
        (outdir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(json.dumps({k: summary[k] for k in ("status", "completed_count", "failed_count", "candidate_count")}))
        raise SystemExit(bool(failed))


if __name__ == "__main__":
    main()
