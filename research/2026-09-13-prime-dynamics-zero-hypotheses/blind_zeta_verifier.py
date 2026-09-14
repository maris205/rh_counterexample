"""Verify blind prime-dynamics candidates against the actual Riemann zeta.

The candidate generator is deliberately decoupled from this verifier.  Its
output may be a JSON list or a mapping containing ``candidates``.  A candidate
is only a proposal: each proposal is evaluated independently with mpmath and
Arb, refined from several free-sigma seeds, and (for an off-line numerical
candidate) passed to a local rectangle check.  No RH conclusion is inferred
from an empty list or from Newton convergence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Both labs live below the repository's ``research`` directory.  Keeping the
# path explicit avoids resolving to ``<repo>/2026-09-08-zero-lab`` when this
# verifier is launched from an arbitrary working directory.
LAB = HERE.parent.parent / "research" / "2026-09-08-zero-lab"
for directory in (LAB / ".deps", LAB, LAB / "certification"):
    sys.path.insert(0, str(directory))

import mpmath as mp
import flint
from zero_lab import check_point, refine
from rectangle_count import count_rectangle


def _load_candidates(path: Path):
    if not path.exists():
        return [], {"input_status": "MISSING_INPUT", "input_path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        rows = data.get("candidates", data.get("rows", data.get("frequency_candidates", [])))
    else:
        rows = []
    if not isinstance(rows, list):
        rows = []
    return rows, {"input_status": "READ", "input_path": str(path),
                  "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _number(row, names, default=None):
    for name in names:
        if isinstance(row, dict) and name in row and row[name] is not None:
            try:
                return str(row[name])
            except Exception:
                return default
    return default


def _candidate(row, index):
    if not isinstance(row, dict):
        row = {"t": row}
    t = _number(row, ("t", "center_t", "height", "frequency", "imag", "imaginary"))
    sigma = _number(row, ("sigma", "real", "real_part"), "0.75")
    if t is None:
        return None
    try:
        if not (0 < mp.mpf(sigma) < 1 and mp.mpf(t) > 0):
            return None
    except Exception:
        return None
    return {"candidate_index": index, "sigma": sigma, "t": t,
            "source": row.get("source", row.get("channel", "blind")),
            "raw": row}


def _seed_points(candidate):
    sigma = mp.mpf(candidate["sigma"])
    t = mp.mpf(candidate["t"])
    # Several real-part seeds and tiny height offsets test basin dependence.
    sigmas = [sigma, mp.mpf("0.55"), mp.mpf("0.65"), mp.mpf("0.75"),
              mp.mpf("0.85"), mp.mpf("0.95")]
    out = []
    seen = set()
    for ss in sigmas:
        for dt in (mp.mpf("0"), mp.mpf("-0.02"), mp.mpf("0.02")):
            if not (0 < ss < 1 and t + dt > 0):
                continue
            key = (mp.nstr(ss, 18), mp.nstr(t + dt, 18))
            if key not in seen:
                seen.add(key)
                out.append((mp.nstr(ss, 30), mp.nstr(t + dt, 30)))
    return out


def _local_rectangle(final_sigma, final_t, radius):
    """Return an exact-decimal off-line box, or None when a box is unsafe."""
    sigma = mp.mpf(str(final_sigma)); height = mp.mpf(str(final_t)); r = mp.mpf(str(radius))
    if not (mp.isfinite(sigma) and mp.isfinite(height) and mp.isfinite(r) and r > 0):
        return None
    # The contour routine requires a positive-strip rectangle wholly on one
    # side of Re(s)=1/2.  Do not silently shrink a user-requested box.
    if not (0 < sigma-r and sigma+r < 1 and height-r > 0):
        return None
    if not (sigma-r > mp.mpf("0.5") or sigma+r < mp.mpf("0.5")):
        return None
    return tuple(mp.nstr(x, 40) for x in (sigma-r, sigma+r, height-r, height+r))


def _verify_one(candidate, dps=80, box_radius="1e-7", max_height=100000,
                rectangle_dps=None, rectangle_seconds=30.0):
    started = time.perf_counter()
    refinements = []
    for seed_sigma, seed_t in _seed_points(candidate):
        try:
            root = refine(seed_sigma, seed_t, dps=dps, max_steps=50,
                          max_height=max_height)
            row = {"seed_sigma": seed_sigma, "seed_t": seed_t, **root}
            if root.get("status") == "NUMERICAL_CONVERGENCE":
                final_sigma, final_t = root["final_sigma"], root["final_t"]
                try:
                    check = check_point(final_sigma, final_t, box_radius,
                                        precisions=(50, dps))
                    row["point_check"] = check
                    row["independent_point_evaluations_agree"] = all(
                        e.get("independent_point_evaluations_agree", False)
                        for e in check.get("evaluation_rows", []))
                except Exception as exc:
                    row["point_check_error"] = repr(exc)
                    row["independent_point_evaluations_agree"] = False
            refinements.append(row)
        except Exception as exc:
            refinements.append({"seed_sigma": seed_sigma, "seed_t": seed_t,
                                "status": "ERROR", "error": repr(exc)})

    converged = [r for r in refinements if r.get("status") == "NUMERICAL_CONVERGENCE"]
    off_line = [r for r in converged if r.get("classification") == "OFF_LINE_NUMERICAL_CANDIDATE"]
    # Only a numerical off-line point is eligible for the contour gate.  A
    # critical-line convergence is retained as calibration evidence, but is
    # never sent to the off-line certification routine.
    contour_rows = []
    for r in off_line:
        try:
            rect = _local_rectangle(r["final_sigma"], r["final_t"], box_radius)
            if rect is None:
                contour_rows.append({"status": "SKIPPED_UNSAFE_BOX",
                                     "reason": "candidate is not strictly inside the positive strip and off the critical line"})
                continue
            contour = count_rectangle(*rect, func="zeta",
                                       dps=int(rectangle_dps or min(dps, 80)),
                                       max_seconds=float(rectangle_seconds))
            contour_rows.append({"rectangle": {"sigma_min": rect[0], "sigma_max": rect[1],
                                                  "t_min": rect[2], "t_max": rect[3]},
                                 "result": contour})
            r["rectangle_count"] = contour
        except Exception as exc:
            contour_rows.append({"status": "ERROR", "error": repr(exc)})
    final = off_line or converged
    unique = []
    for r in final:
        try:
            key = (round(float(r["final_sigma"]), 10), round(float(r["final_t"]), 8))
        except Exception:
            continue
        if key not in {(x[0], x[1]) for x in unique}:
            unique.append(key)
    return {
        **candidate,
        "seed_count": len(refinements),
        "converged_count": len(converged),
        "off_line_numerical_count": len(off_line),
        "distinct_final_points": [{"sigma": x[0], "t": x[1]} for x in unique],
        "refinements": refinements,
        "rectangle_checks": contour_rows,
        "certified_off_line_zero": any(
            x.get("result", {}).get("off_line_certified", False)
            for x in contour_rows if isinstance(x, dict)),
        "interpretation": (
            "No numerical convergence from the candidate seeds." if not converged else
            "All converged seeds return near the critical line; no off-line candidate." if not off_line else
            "Off-line numerical points require a rigorous contour count; not certified."
        ),
        "elapsed_seconds": time.perf_counter() - started,
    }


def verify(input_path: Path, output_path: Path, dps=80, box_radius="1e-7",
           rectangle_dps=None, rectangle_seconds=30.0):
    rows, meta = _load_candidates(input_path)
    candidates = []
    for i, row in enumerate(rows):
        c = _candidate(row, i)
        if c is not None:
            candidates.append(c)
    started = time.perf_counter()
    if not candidates:
        result = {
            "status": "EMPTY_CANDIDATE_SET" if meta.get("input_status") == "READ" else "NO_INPUT_CANDIDATE_FILE",
            **meta,
            "candidate_count": 0,
            "rows": [],
            "certified_off_line_zero": False,
            "interpretation": "The blind generator supplied no valid (sigma,t) proposals. This is a candidate-generation result, not evidence for or against RH.",
        }
    else:
        checked = [_verify_one(c, dps=dps, box_radius=box_radius,
                               rectangle_dps=rectangle_dps,
                               rectangle_seconds=rectangle_seconds) for c in candidates]
        result = {
            "status": "COMPLETED",
            **meta,
            "candidate_count": len(checked), "rows": checked,
            "certified_off_line_zero": any(x.get("certified_off_line_zero", False) for x in checked),
            "interpretation": "Numerical verification only; an RH counterexample requires an independent rigorous off-line contour certificate.",
        }
    result["configuration"] = {"dps": dps, "box_radius": box_radius,
                                "rectangle_dps": rectangle_dps or min(dps, 80),
                                "rectangle_seconds": rectangle_seconds,
                                "free_sigma": True, "seed_policy": "candidate sigma, 0.55/0.65/0.75/0.85/0.95 and t +/- 0.02"}
    result["versions"] = {"python": platform.python_version(), "mpmath": mp.__version__, "python_flint": flint.__version__}
    result["verifier_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result["elapsed_seconds"] = time.perf_counter() - started
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=Path("runs/blind-candidates.json"))
    ap.add_argument("--output", type=Path, default=Path("runs/blind-zeta-verification.json"))
    ap.add_argument("--dps", type=int, default=80)
    ap.add_argument("--box-radius", default="1e-7")
    ap.add_argument("--rectangle-dps", type=int, default=None)
    ap.add_argument("--rectangle-seconds", type=float, default=30.0)
    args = ap.parse_args()
    result = verify(args.input, args.output, args.dps, args.box_radius,
                    args.rectangle_dps, args.rectangle_seconds)
    print(json.dumps({"status": result["status"], "candidate_count": result["candidate_count"], "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
