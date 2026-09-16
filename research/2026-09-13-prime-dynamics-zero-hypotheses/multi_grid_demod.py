"""Independent log-grid demodulation check for prime-dynamics channels.

The FFT reports from a single ``linspace(log(2), log(N))`` grid have a fixed
frequency resolution and can create common-looking bins in several channels.
This script deliberately changes both the number of samples and the end-point
phase of a uniform log grid.  It then scans continuous angular frequencies by
least-squares demodulation (rather than reading an FFT bin).  A peak is called
stable only if it survives these independent grids; the calculation is still
an exploratory feature test and never a zeta-zero certificate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from mertens_dynamics import mobius_sieve
from lambda_psi_dynamics import von_mangoldt_theta_linear_sieve
from known_ordinates import known_ordinates


KNOWN_T = np.array(known_ordinates(0.0, 40.0))  # legacy import compatibility


def cumulative_grid(cumulative: np.ndarray, n: int, samples: int,
                    phase: float, kind: str) -> tuple[np.ndarray, np.ndarray]:
    """Sample cumulative data on an independent, trimmed uniform log grid.

    ``phase`` is a fraction of the full log span trimmed from *each* end,
    rather than a fraction of one sample step.  This makes the windows truly
    independent enough to diagnose endpoint/window artefacts.
    """
    lo, hi = math.log(2.0), math.log(float(n))
    trim = max(0.0, min(0.45, float(phase))) * (hi - lo)
    u = np.linspace(lo + trim, hi - trim, samples)
    x = np.exp(u)
    idx = np.floor(x).astype(np.int64)
    idx = np.clip(idx, 2, n - 1)
    frac = x - idx
    vals = (1.0 - frac) * cumulative[idx] + frac * cumulative[idx + 1]
    if kind == "mertens":
        y = vals / np.sqrt(x)
    elif kind in ("psi", "theta"):
        y = (vals - x) / np.sqrt(x)
    else:
        raise ValueError(kind)
    return u, y


def demod_scan(u: np.ndarray, y: np.ndarray, t_grid: np.ndarray,
               detrend_degree: int = 2) -> list[dict]:
    """Return continuous-frequency R2/amplitude/phase scores."""
    degree = min(detrend_degree, max(0, len(y) - 2))
    z = y - np.polyval(np.polyfit(u, y, degree), u)
    var = float(np.dot(z, z))
    if var == 0.0:
        return []
    rows = []
    for t in t_grid:
        c, s = np.cos(t * u), np.sin(t * u)
        cc, ss, cs = float(np.dot(c, c)), float(np.dot(s, s)), float(np.dot(c, s))
        cz, sz = float(np.dot(c, z)), float(np.dot(s, z))
        det = cc * ss - cs * cs
        if det <= 1e-14:
            continue
        a, b = (cz * ss - sz * cs) / det, (sz * cc - cz * cs) / det
        explained = a * cz + b * sz
        rows.append({"t": float(t), "r2": float(max(0.0, explained / var)),
                     "amplitude": float(math.hypot(a, b)),
                     "phase": float(math.atan2(b, a))})
    return rows


def select_peaks(rows: list[dict], count: int = 8, min_sep: float = 0.30) -> list[dict]:
    chosen: list[dict] = []
    for row in sorted(rows, key=lambda q: q["r2"], reverse=True):
        if all(abs(row["t"] - q["t"]) >= min_sep for q in chosen):
            chosen.append(row)
            if len(chosen) >= count:
                break
    return chosen


def shuffled_coefficients(weights: np.ndarray, rng: np.random.Generator,
                          block_size: int | None) -> np.ndarray:
    """Return a coefficient shuffle used only as an empirical null.

    A global shuffle destroys the arithmetic ordering.  A block shuffle
    randomises coefficients *within* large blocks, retaining the coarse
    density but breaking the phase information.  Small-block shuffles are
    deliberately not used here: cumulative sums make them a leaky null.
    """
    out = np.asarray(weights, dtype=np.float64).copy()
    if block_size is None:
        body = out[1:]
        rng.shuffle(body)
        out[1:] = body
        return out
    for start in range(1, len(out), int(block_size)):
        stop = min(len(out), start + int(block_size))
        body = out[start:stop]
        rng.shuffle(body)
        out[start:stop] = body
    return out


def control_quantiles(base_weights: dict[str, np.ndarray], n: int,
                      grids: list[tuple[int, float]], t_grid: np.ndarray,
                      candidate_t: float, reps: int, block_sizes: tuple[int, ...],
                      seed: int) -> list[dict]:
    """Compute empirical q95 for candidate and blind-top scores per grid.

    This is intentionally a modest, reproducible control panel.  It does not
    turn a q95 exceedance into a mathematical claim; it only says whether the
    observed score is unusual relative to the chosen finite-sample null.
    """
    modes: list[tuple[str, int | None]] = [("global_shuffle", None)]
    modes.extend((f"block_shuffle_{b}", int(b)) for b in block_sizes)
    out: list[dict] = []
    known = np.array(known_ordinates(float(min(t_grid)), float(max(t_grid))))
    for samples, phase in grids:
        for channel, weights in base_weights.items():
            for label, block in modes:
                candidate_scores: list[float] = []
                top_scores: list[float] = []
                for rep in range(max(0, int(reps))):
                    token = f"{seed}:{rep}:{samples}:{phase}:{channel}:{label}"
                    stable_seed = int.from_bytes(hashlib.sha256(token.encode()).digest()[:8], "big")
                    rr = np.random.default_rng(stable_seed)
                    shuffled = shuffled_coefficients(weights, rr, block)
                    cumulative = np.cumsum(shuffled, dtype=np.float64)
                    u, y = cumulative_grid(cumulative, n, samples, phase, channel)
                    rows = demod_scan(u, np.gradient(y, u), t_grid, 1)
                    candidate = next((x["r2"] for x in rows
                                      if abs(x["t"] - candidate_t) <= 0.5 * (t_grid[1] - t_grid[0])), 0.0)
                    blind = [x["r2"] for x in rows
                             if not np.any(np.abs(known - x["t"]) <= 0.35)]
                    candidate_scores.append(float(candidate))
                    top_scores.append(float(max(blind) if blind else 0.0))
                out.append({"samples": samples, "phase": phase, "channel": channel,
                            "control": label, "reps": len(candidate_scores),
                            "candidate_t": float(candidate_t),
                            "candidate_q95": float(np.quantile(candidate_scores, 0.95)) if candidate_scores else 0.0,
                            "top_q95": float(np.quantile(top_scores, 0.95)) if top_scores else 0.0,
                            "candidate_scores": candidate_scores,
                            "top_scores": top_scores})
    return out


def run(n: int, t_min: float, t_max: float, t_step: float,
        grids: list[tuple[int, float]], control_reps: int = 0,
        block_sizes: tuple[int, ...] = (1_000_000,), seed: int = 20260913) -> dict:
    mu = mobius_sieve(n)
    lam, theta_w = von_mangoldt_theta_linear_sieve(n)
    cum_mu = np.cumsum(mu, dtype=np.float64)
    cum_lam = np.cumsum(lam, dtype=np.float64)
    cum_theta = np.cumsum(theta_w, dtype=np.float64)
    t_grid = np.arange(t_min, t_max + 0.5 * t_step, t_step)
    known = np.array(known_ordinates(t_min, float(t_grid[-1])))
    channels = {"mertens": cum_mu, "psi": cum_lam, "theta": cum_theta}
    records = []
    for samples, phase in grids:
        for name, cumulative in channels.items():
            u, y = cumulative_grid(cumulative, n, samples, phase, name)
            rows = demod_scan(u, np.gradient(y, u), t_grid, 1)
            records.append({"samples": samples, "phase": phase, "channel": name,
                            "log_span": float(u[-1] - u[0]),
                            "peaks": select_peaks(rows)})
    # Exclude known ordinates when forming blind consensus.  A frequency is a
    # consensus hit if it is within tolerance on at least two independent grids
    # and in at least two channels.
    candidates = []
    for rec in records:
        for p in rec["peaks"]:
            if np.any(np.abs(known - p["t"]) <= 0.35):
                continue
            candidates.append({"t": p["t"], "r2": p["r2"],
                               "channel": rec["channel"],
                               "samples": rec["samples"], "phase": rec["phase"]})
    clusters: list[list[dict]] = []
    for row in sorted(candidates, key=lambda q: q["t"]):
        hit = next((c for c in clusters if abs(np.mean([x["t"] for x in c]) - row["t"]) <= 0.25), None)
        if hit is None:
            clusters.append([row])
        else:
            hit.append(row)
    consensus = []
    for cluster in clusters:
        grids_seen = {(x["samples"], x["phase"]) for x in cluster}
        channels_seen = {x["channel"] for x in cluster}
        if len(grids_seen) >= 2 and len(channels_seen) >= 2:
            consensus.append({"t_mean": float(np.mean([x["t"] for x in cluster])),
                              "t_min": float(min(x["t"] for x in cluster)),
                              "t_max": float(max(x["t"] for x in cluster)),
                              "grid_count": len(grids_seen),
                              "channel_count": len(channels_seen),
                              "max_r2": float(max(x["r2"] for x in cluster)),
                              "hits": cluster})
    candidate_t = 37.5
    observed_candidate = []
    for rec in records:
        u, y = cumulative_grid(channels[rec["channel"]], n,
                               rec["samples"], rec["phase"], rec["channel"])
        rows = demod_scan(u, np.gradient(y, u), np.array([candidate_t]), 1)
        observed_candidate.append({"samples": rec["samples"], "phase": rec["phase"],
                                   "channel": rec["channel"],
                                   "candidate_t": candidate_t,
                                   "candidate_r2": float(rows[0]["r2"] if rows else 0.0)})
    controls = []
    if control_reps > 0:
        controls = control_quantiles({"mertens": mu, "psi": lam, "theta": theta_w},
                                     n, grids, t_grid, candidate_t, control_reps,
                                     block_sizes, seed)
    return {"status": "COMPLETED", "purpose": "independent-grid demodulation; heuristic only",
            "configuration": {"n": n, "t_min": t_min, "t_max": t_max,
                               "t_step": t_step, "grids": grids,
                               "control_reps": control_reps,
                               "block_sizes": list(block_sizes), "control_seed": seed},
            "known_ordinates_excluded": known.tolist(),
            "candidate_37_5_role": "known-line calibration neighborhood, not a blind candidate",
            "observable_dependence": "psi and theta share a prime source; not independent channel families",
            "records": records, "blind_consensus": consensus,
            "candidate_37_5": observed_candidate, "control_quantiles": controls,
            "interpretation": "Common FFT bins are not accepted unless continuous-frequency peaks survive independent log-grid starts, sample counts, and at least two channels."}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10_000_000)
    ap.add_argument("--t-min", type=float, default=4.0)
    ap.add_argument("--t-max", type=float, default=40.0)
    ap.add_argument("--t-step", type=float, default=0.05)
    ap.add_argument("--grids", default="1024:0,1536:0.02,2048:0.05,3072:0.10")
    ap.add_argument("--control-reps", type=int, default=0)
    ap.add_argument("--block-sizes", default="1000000")
    ap.add_argument("--seed", type=int, default=20260913)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    grids = [(int(a), float(b)) for a, b in (x.split(":") for x in args.grids.split(","))]
    blocks = tuple(int(x) for x in args.block_sizes.split(",") if x.strip())
    result = run(args.n, args.t_min, args.t_max, args.t_step, grids,
                 args.control_reps, blocks, args.seed)
    result["source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(args.output),
                      "records": len(result["records"]),
                      "blind_consensus": result["blind_consensus"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
