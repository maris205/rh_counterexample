"""Finite Euler-factor model calibration; never an actual-zeta search.

F_w(s)=product_p (1-w_p*p**(-s))**(-1), formally:
a(p**k)=w_p**k, inverse b(n)=mu(n)*a(n), L(p**k)=w_p**k*log(p).
All three coefficient arrays come from the SAME weights on actual primes.
Keeping these formal identities does not preserve the ordinary prime law.
"""
import argparse
import hashlib
import json
from pathlib import Path
import traceback
import common_spectrum_v2_batch_py3 as batch
import common_spectrum_v2 as core
from known_ordinates import known_mask
import numpy as np


def structure(n):
    spf = np.arange(n + 1)
    for p in range(2, int(n ** .5) + 1):
        if spf[p] == p:
            block = spf[p*p::p]
            np.minimum(block, p, out=block)
    primes = np.flatnonzero(spf[2:] == np.arange(2, n + 1)) + 2
    return spf, primes, core.mobius_sieve(n)


def coefficients(struct, weights):
    spf, primes, mu = struct
    n = len(spf) - 1
    at_prime = np.zeros(n + 1)
    at_prime[primes] = weights
    a = np.ones(n + 1)
    a[0] = 0.
    for k in range(2, n + 1):
        a[k] = at_prime[spf[k]] * a[k // spf[k]]
    lam = np.zeros(n + 1)
    for p, w in zip(primes, weights):
        power, wk = int(p), float(w)
        while power <= n:
            lam[power] = wk * np.log(float(p))
            power *= int(p)
            wk *= w
    return a, {"mu": mu * a, "lambda": lam, "prime": at_prime}


def shuffled_weights(primes, weights, mode, seed):
    rng = np.random.default_rng(seed)
    out = weights.copy()
    if mode == "global":
        rng.shuffle(out)
    else:
        bins = (np.log(primes) / np.log(primes[-1]) * 16).astype(int) if mode == "log_bin" else primes // 10000
        for label in np.unique(bins):
            idx = np.flatnonzero(bins == label)
            out[idx] = rng.permutation(out[idx])
    return out


def run(outdir, smoke=False):
    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    cfg = {"scales": [30000, 100000] if not smoke else [5000, 10000],
           "grids": [[192, 0.], [256, .08]], "splits": [.55, .75], "theta": .525,
           "x_min": 100, "frequencies": [18., 27.], "amplitudes": [.1, .3],
           "phase_seeds": [0, 1], "control_reps": 19 if not smoke else 1,
           "controls": ["global", "log_bin", "block"], "scan": [4., 40., .25],
           "known_margin": .35, "scope": "Euler-factor toy calibration",
           "baseline": "ordinary x and li baselines retained; possible model-baseline mismatch",
           "weight_formula": "1 + epsilon*cos(t*log(p)+phase)",
           "selection": "unchanged joint minimum training gain, top 3 separated by .5",
           "notes": "No injected zero is implied by modulated Euler weights. Phase trials are not independent datasets."}
    manifest = batch.manifest_for(cfg)
    manifest["source_sha256"][Path(__file__).name] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest.pop("run_id")
    manifest["run_id"] = batch.fingerprint(manifest)
    designs = [(t, amp, seed) for t in cfg["frequencies"] for amp in cfg["amplitudes"] for seed in cfg["phase_seeds"]]
    tasks = [("ordinary", None, None, 0)]
    for i, design in enumerate(designs):
        tasks.append((f"design{i}-real", design, None, 0))
        tasks.extend((f"design{i}-{mode}-{rep}", design, mode, rep) for mode in cfg["controls"] for rep in range(cfg["control_reps"]))
    with batch.run_lock(outdir):
        batch.check_manifest(outdir, manifest)
        struct = structure(max(cfg["scales"]))
        primes = struct[1]
        scan = np.arange(4., 40.125, .25)
        scan = scan[~known_mask(scan, cfg["known_margin"])]
        results = {}
        for key, design, mode, rep in tasks:
            path = outdir / f"task-{key}.json"
            row = batch.completed_task(path, manifest["run_id"], key)
            if row is None:
                try:
                    weights = np.ones(len(primes))
                    if design is not None:
                        t, amp, seed = design
                        phase = np.random.default_rng(20260916 + seed).uniform(-np.pi, np.pi)
                        weights += amp * np.cos(t * np.log(primes) + phase)
                    if mode:
                        token = f"{design}:{mode}:{rep}"
                        rngseed = int.from_bytes(hashlib.sha256(token.encode()).digest()[:8], "big")
                        weights = shuffled_weights(primes, weights, mode, rngseed)
                    _, source = coefficients(struct, weights)
                    cells = core.build_cells(source, cfg["scales"], cfg["grids"], cfg["splits"], cfg["theta"], cfg["x_min"])
                    result = core.evaluate(cells, scan, np.log(cfg["x_min"]), 3)
                    row = {"status": "COMPLETED", "result": result, "design": design, "control": mode}
                    json.dumps(row, allow_nan=False)
                except Exception as exc:
                    traceback.print_exc()
                    row = {"status": "FAILED", "error": repr(exc)}
                row.update(run_id=manifest["run_id"], task_id=key)
                batch.atomic_json(path, row)
            results[key] = row
            batch.atomic_json(outdir / "progress.json", {"status": "RUNNING", "completed_count": sum(r["status"] == "COMPLETED" for r in results.values()),
                "failed_count": sum(r["status"] == "FAILED" for r in results.values()), "total_tasks": len(tasks), "current_task": key, "updated": batch.now()})
        curves = []
        for i, (t, amp, seed) in enumerate(designs):
            observed = results[f"design{i}-real"]
            if observed["status"] != "COMPLETED":
                curves.append({"design": [t, amp, seed], "status": "FAILED"})
                continue
            selected = observed["result"]["candidates"]
            ranks = {}
            for mode in cfg["controls"]:
                nulls = [results[f"design{i}-{mode}-{r}"]["result"]["max_statistic"] for r in range(cfg["control_reps"]) if results[f"design{i}-{mode}-{r}"]["status"] == "COMPLETED"]
                ranks[mode] = {"replicates": len(nulls), "max_statistic_scores": nulls,
                    "rank": core.empirical_p(observed["result"]["max_statistic"], nulls) if len(nulls) == cfg["control_reps"] else None}
            match = [c for c in selected if abs(c["t"] - t) <= .25]
            curves.append({"design": [t, amp, seed], "status": "COMPLETED", "modulation_frequency_selected": bool(match),
                "modulation_positive_prediction": any(c["positive_in_every_primary_cell"] for c in match),
                "best_joint_score": observed["result"]["max_statistic"], "selected_t": [c["t"] for c in selected], "controls": ranks})
        failed = sum(r["status"] == "FAILED" for r in results.values())
        summary = {"status": "COMPLETED_WITH_FAILURES" if failed else "COMPLETED", "run_id": manifest["run_id"],
            "configuration": cfg, "completed_count": len(results)-failed, "failed_count": failed, "total_tasks": len(tasks),
            "curves": curves, "candidate_count": None, "gate_status": "MODEL_CALIBRATION_ONLY",
            "interpretation": "Formal Euler-product coefficients are coupled, but weighted primes are not ordinary prime counting. Modulation does not insert a known zero. Surrogate ranks are descriptive within this toy family, not RH probabilities. Baseline mismatch and operator attenuation remain possible. No actual zeta search or interval certification."}
        batch.atomic_json(outdir / "summary.json", summary)
        batch.atomic_json(outdir / "progress.json", {k: summary[k] for k in ("status", "completed_count", "failed_count", "total_tasks")})
        lines = ["# Coupled Euler-factor calibration", "", summary["interpretation"], "", "| t | epsilon | seed | selected | positive prediction | best minimum gain |", "|---|---|---|---|---|---|"]
        lines += [f"| {r['design'][0]} | {r['design'][1]} | {r['design'][2]} | {r.get('modulation_frequency_selected')} | {r.get('modulation_positive_prediction')} | {r.get('best_joint_score')} |" for r in curves]
        (outdir / "report.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
        return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    summary = run(args.output_dir, args.smoke)
    print(json.dumps({k: summary[k] for k in ("status", "completed_count", "failed_count", "total_tasks")}))
    raise SystemExit(bool(summary["failed_count"]))
