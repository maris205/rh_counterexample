"""Summarise shared-frequency calibration across arithmetic channels.

This is a calibration report, not a zero finder.  Every frequency used here is
one of the first known critical-line ordinates.  The script intentionally keeps
the control distribution alongside the signal so that cumulative-window
leakage cannot be mistaken for a common arithmetic frequency.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean, median
from typing import Any


KNOWN_T = [
    14.134725141734695,
    21.022039638771556,
    25.01085758014569,
    30.424876125859512,
    32.93506158773919,
]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def wrap_phase(x: float) -> float:
    return (x + math.pi) % (2.0 * math.pi) - math.pi


def phase_stats(values: list[float]) -> dict[str, float | None]:
    vals = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if not vals:
        return {"circular_resultant": None, "max_pairwise_distance": None}
    z = sum(complex(math.cos(v), math.sin(v)) for v in vals) / len(vals)
    distances = [abs(wrap_phase(a - b)) for a in vals for b in vals]
    return {
        "circular_resultant": abs(z),
        "max_pairwise_distance": max(distances) if distances else 0.0,
    }


def metric_summary(rows: list[dict[str, float]]) -> dict[str, Any]:
    if not rows:
        return {"n": 0, "r2": {}, "amplitude": {}, "phase": {}}
    out: dict[str, Any] = {"n": len(rows)}
    for key in ("r2", "amplitude"):
        values = [float(r[key]) for r in rows if key in r and r[key] is not None]
        if values:
            ordered = sorted(values)
            pos = 0.95 * (len(ordered) - 1)
            lo, hi = math.floor(pos), math.ceil(pos)
            q95 = ordered[lo] if lo == hi else ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)
        else:
            q95 = None
        out[key] = {
            "mean": mean(values) if values else None,
            "median": median(values) if values else None,
            "min": min(values) if values else None,
            "max": max(values) if values else None,
            "q95": q95,
        }
    out["phase"] = phase_stats([r["phase"] for r in rows if "phase" in r])
    return out


def projection_rows(projection: dict[str, Any], t: float) -> list[dict[str, float]]:
    """Read split -> {holdout_projection:{r2, amplitude, phase}}."""
    rows: list[dict[str, float]] = []
    # Some Mertens reports store one projection directly rather than wrapping
    # it in a split key (the replicated controls use this form).
    if isinstance(projection, dict) and "holdout_projection" in projection:
        projection = {"direct": projection}
    for split in sorted(projection, key=str):
        item = projection[split]
        if not isinstance(item, dict):
            continue
        hp = item.get("holdout_projection", {})
        if hp.get("r2") is not None:
            try:
                split_value = float(split)
            except (TypeError, ValueError):
                split_value = float("nan")
            rows.append({
                "split": split_value,
                "t": float(hp.get("t", t)),
                "r2": float(hp["r2"]),
                "amplitude": float(hp.get("amplitude", float("nan"))),
                "phase": float(hp.get("phase", float("nan"))),
            })
    return rows


def known_channel_rows(data: dict[str, Any], channel: str, t: float) -> list[dict[str, float]]:
    """Extract a known-line increment projection from lambda/short files."""
    item = data.get("channels", {}).get(channel, {})
    proj = item.get("known_critical_line_increment", {}).get(str(t), {})
    return projection_rows(proj, t)


def known_mertens_rows(data: dict[str, Any], t: float) -> list[dict[str, float]]:
    for probe in data.get("known_critical_line_probes", []):
        if abs(float(probe.get("t", -1.0)) - t) < 1e-8:
            proj = probe.get("mertens_increment_projection", {})
            return projection_rows(proj, t)
    return []


def control_rows(data: dict[str, Any], channel: str, t: float) -> dict[str, list[dict[str, float]]]:
    """Return control_type -> flattened split rows for the increment metric."""
    out: dict[str, list[dict[str, float]]] = {}
    # Mertens replicated controls live under control_replicates and expose a
    # fixed-first-zero increment projection.  The old global/block summaries
    # do not carry fixed-frequency rows and are therefore not silently reused.
    source = data.get("control_replicates", {}) if channel == "mertens" else data.get("controls", {})
    for control_type, repetitions in source.items():
        rows: list[dict[str, float]] = []
        if isinstance(repetitions, dict):
            repetitions = [repetitions]
        for rep in repetitions or []:
            if not isinstance(rep, dict):
                continue
            if channel == "mertens":
                proj = rep.get("fixed_first_zero_increment", {}) if abs(t - KNOWN_T[0]) < 1e-8 else {}
            else:
                item = rep.get(channel, {})
                proj = item.get("known_critical_line_increment", {}).get(str(t), {})
            rows.extend(projection_rows(proj, t))
        out[control_type] = rows
    return out


def control_threshold(control: dict[str, dict[str, Any]]) -> float | None:
    vals = []
    for summary in control.values():
        mx = summary.get("r2", {}).get("max")
        if mx is not None:
            vals.append(float(mx))
    return max(vals) if vals else None


def control_q95(control: dict[str, dict[str, Any]]) -> float | None:
    vals: list[float] = []
    for summary in control.values():
        # The per-control summary retains max/mean/median but not raw rows;
        # use the maximum as a conservative fallback when a report has very
        # few repetitions.  New reports can provide q95 directly below.
        q = summary.get("r2", {}).get("q95")
        if q is not None:
            vals.append(float(q))
        elif summary.get("r2", {}).get("max") is not None:
            vals.append(float(summary["r2"]["max"]))
    return max(vals) if vals else None


def summarise_file(path: Path) -> dict[str, Any]:
    data = load(path)
    config = data.get("configuration", {})
    is_mertens = "known_critical_line_probes" in data
    channels = ["mertens"] if is_mertens else list(data.get("channels", {}).keys())
    if not is_mertens:
        channels = [c for c in channels if c not in {"counts_summary"}]
    records: dict[str, Any] = {}
    for channel in channels:
        records[channel] = {}
        for t in KNOWN_T:
            signal = (known_mertens_rows(data, t) if is_mertens else known_channel_rows(data, channel, t))
            controls = control_rows(data, channel if not is_mertens else "mertens", t)
            control_summaries = {k: metric_summary(v) for k, v in controls.items()}
            sig = metric_summary(signal)
            threshold = control_threshold(control_summaries)
            q95 = control_q95(control_summaries)
            sig_r2 = sig.get("r2", {}).get("mean")
            records[channel][str(t)] = {
                "signal": sig,
                "controls": control_summaries,
                "control_max_r2": threshold,
                "control_q95_r2": q95,
                "signal_beats_control_q95": bool(
                    sig_r2 is not None and q95 is not None and sig_r2 > q95
                ),
            }
    return {
        "file": str(path),
        "status": data.get("status"),
        "purpose": data.get("purpose"),
        "configuration": config,
        "channels": records,
    }


def joint_summary(file_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    # A frequency is a calibration pass only if all available channels have a
    # usable signal row.  The strict blind-search gate below is deliberately
    # stronger than this diagnostic and is never applied to the known probes.
    rows_by_t: dict[str, list[dict[str, Any]]] = {str(t): [] for t in KNOWN_T}
    for fs in file_summaries:
        for channel, freqs in fs["channels"].items():
            for t, rec in freqs.items():
                rows_by_t[t].append({"file": fs["file"], "channel": channel, **rec})
    joint: dict[str, Any] = {}
    for t, rows in rows_by_t.items():
        usable = [r for r in rows if r["signal"].get("n", 0) > 0]
        beating = [r for r in usable if r["signal_beats_control_q95"]]
        beating_channel_set = sorted({r["channel"] for r in beating})
        joint[t] = {
            "available_channel_records": len(usable),
            "records_beating_control_q95": len(beating),
            "beating_channels": beating_channel_set,
            "passes_min_three_independent_channels": len(beating_channel_set) >= 3,
            "interpretation": "known critical-line calibration only; not an unknown-zero candidate",
        }
    return joint


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Cross-channel zero-frequency calibration",
        "",
        "> This report is a calibration artifact. The tested frequencies are known critical-line ordinates; no entry below is evidence for a new or off-line zeta zero.",
        "",
        "## Blind-search gate",
        "",
        "A future unknown frequency may be passed to zeta only if it appears in at least three independent channels (Mertens increment, psi/theta increment, short-interval or gap channel), beats the 95th-percentile control distribution for each channel, survives splits 0.55/0.67/0.80 and two N scales, and has phase concentration R >= 0.80. It must then pass free-sigma Newton refinement, a local box exclusion/count, and high-precision residual checks for the actual Riemann zeta function.",
        "",
        "The top FFT lists currently share grid buckets near 14.016, 14.385, 21.025 and 25.08 across Mertens/psi/theta. Because the channels use the same log grid and finite window, this overlap is treated as a grid/trend artifact until it survives independent grids, detrending, and block/global controls.",
        "",
        "## Known-frequency joint diagnostic",
        "",
        "| t | channel records | records beating control q95 | interpretation |",
        "|---:|---:|---:|---|",
    ]
    for t, rec in report["joint"].items():
        lines.append(f"| {float(t):.12f} | {rec['available_channel_records']} | {rec['records_beating_control_q95']} | {rec['interpretation']} |")
    lines += ["", "## Per-file details", ""]
    for fs in report["files"]:
        lines += [f"### `{fs['file']}`", "", f"Configuration: `{json.dumps(fs['configuration'], ensure_ascii=False)}`", ""]
        lines.append("| channel | t | signal holdout R2 mean | signal amplitude mean | phase resultant | control q95 R2 | beats q95 |")
        lines.append("|---|---:|---:|---:|---:|---:|---|")
        for channel, freqs in fs["channels"].items():
            for t, rec in freqs.items():
                sig = rec["signal"]
                r2 = sig.get("r2", {}).get("mean")
                amp = sig.get("amplitude", {}).get("mean")
                resultant = sig.get("phase", {}).get("circular_resultant")
                mx = rec.get("control_q95_r2")
                lines.append(f"| {channel} | {float(t):.6f} | {r2 if r2 is not None else 'n/a'} | {amp if amp is not None else 'n/a'} | {resultant if resultant is not None else 'n/a'} | {mx if mx is not None else 'n/a'} | {rec['signal_beats_control_q95']} |")
        lines.append("")
    lines += ["## Reading the current result", "", "The report is intentionally conservative: a shared known frequency calibrates the measurement pipeline, while a putative RH counterexample requires an unknown frequency plus direct certification on zeta. Control overlap or split instability is a failure of the candidate-generation gate, not a zero.", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", default=[
        "runs/mertens-split-1e7.json",
        "runs/mertens-null-5e7-v2.json",
        "runs/lambda-psi-1e7.json",
        "runs/lambda-psi-5e7.json",
        "runs/short-interval-5e7.json",
    ])
    parser.add_argument("--json-output", default="runs/cross-channel-summary.json")
    parser.add_argument("--markdown-output", default="research/2026-09-13-prime-dynamics-zero-hypotheses/CROSS_CHANNEL_SUMMARY.md")
    args = parser.parse_args()
    summaries = [summarise_file(Path(p)) for p in args.inputs if Path(p).exists()]
    report = {
        "status": "COMPLETED",
        "purpose": "cross-channel known-line calibration; not a zeta-zero certificate",
        "known_frequencies": KNOWN_T,
        "files": summaries,
        "joint": joint_summary(summaries),
        "blind_search_gate": {
            "min_independent_channels": 3,
            "control_quantile": 0.95,
            "required_splits": [0.55, 0.67, 0.80],
            "required_scales": 2,
            "min_phase_circular_resultant": 0.80,
            "zeta_certification": ["free_sigma_newton", "local_box_count", "high_precision_residual"],
        },
        "fft_overlap_warning": {
            "shared_grid_buckets": [14.016, 14.385, 21.025, 25.08],
            "channels": ["mertens", "psi_error", "theta_error"],
            "interpretation": "likely shared log-grid/finite-window trend artifact; not a zero candidate",
        },
    }
    Path(args.json_output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    Path(args.markdown_output).write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"json": args.json_output, "markdown": args.markdown_output, "files": len(summaries)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
