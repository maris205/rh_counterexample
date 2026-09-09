"""Rigorous rectangular zero counts using whole-segment Arb enclosures.

No endpoint-only or floating-point winding number is accepted as a certificate.
All decimal inputs pass through Fraction -> fmpq, without a float conversion.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import sys
import time

DEPS = Path(__file__).resolve().parents[1] / ".deps"
if str(DEPS) not in sys.path:
    sys.path.insert(0, str(DEPS))

from flint import acb, arb, ctx, fmpq  # noqa: E402


class Unresolved(Exception):
    pass


def rational(value) -> Fraction:
    if isinstance(value, (float, bool)):
        raise ValueError("Use exact decimal strings, integers, Decimal or Fraction, not float/bool")
    return Fraction(value)


def fq(value: Fraction) -> fmpq:
    return fmpq(value.numerator, value.denominator)


def point_ball(point: tuple[Fraction, Fraction]) -> acb:
    return acb(arb(fq(point[0])), arb(fq(point[1])))


def segment_ball(start, stop) -> acb:
    mid = tuple((a + b) / 2 for a, b in zip(start, stop))
    radius = tuple(abs(a - b) / 2 for a, b in zip(start, stop))
    return acb(arb(fq(mid[0]), fq(radius[0])), arb(fq(mid[1]), fq(radius[1])))


def count_rectangle(a, b, c, d, *, func: str = "zeta", dps: int = 60,
                    max_depth: int = 24, max_evaluations: int = 50000,
                    max_seconds: float = 30.0, include_segments: bool = True) -> dict:
    """Count zeros inside (a,b) x (c,d), with a certified zero-free boundary.

    status: certified | unresolved | rejected. count is None unless certified.
    off_line_certified can be true only for ZETA, count>0, and a rectangle
    strictly inside 0<Re(s)<1, Im(s)>0, wholly on one side of Re(s)=1/2.
    The synthetic function is s-(3/10+14i); it cannot certify a zeta claim.
    This uses flint's process-global precision context and should be called
    serially within one Python process, or from separate worker processes.
    """
    started = time.perf_counter()
    result = {"status": "rejected", "count": None, "off_line_certified": False,
              "function": func, "synthetic": func == "synthetic_linear",
              "method": "whole-segment acb image exclusion + rigorous argument principle",
              "requested_dps": dps, "max_depth": max_depth,
              "max_evaluations": max_evaluations, "max_seconds": max_seconds}
    try:
        a, b, c, d = map(rational, (a, b, c, d))
        if not (a < b and c < d):
            raise ValueError("Rectangle must have positive width and height")
        if func not in ("zeta", "synthetic_linear"):
            raise ValueError("Unsupported function; only known analytic fixtures are permitted")
        if not isinstance(dps, int) or dps < 20 or max_depth < 0 or max_evaluations < 1 or max_seconds <= 0:
            raise ValueError("Invalid precision or budget")
        result["rectangle_exact"] = {"a": str(a), "b": str(b), "c": str(c), "d": str(d)}
        if func == "zeta" and a <= 1 <= b and c <= 0 <= d:
            raise ValueError("The closed rectangle contains the zeta pole at s=1")
    except (TypeError, ValueError, ZeroDivisionError) as exc:
        result["reason"] = str(exc)
        return result

    old_precision = ctx.prec
    ctx.dps = dps
    evaluations, accepted, deepest = 0, 0, 0
    endpoint_cache, segments = {}, []
    total_argument = arb(0)
    pi = arb.pi()
    synthetic_root = point_ball((Fraction(3, 10), Fraction(14)))

    def evaluate(ball):
        nonlocal evaluations
        if evaluations >= max_evaluations:
            raise Unresolved("Function-evaluation budget exhausted")
        if time.perf_counter() - started > max_seconds:
            raise Unresolved("Wall-time budget exhausted")
        evaluations += 1
        return ball.zeta() if func == "zeta" else ball - synthetic_root

    def endpoint(point):
        if point not in endpoint_cache:
            endpoint_cache[point] = evaluate(point_ball(point))
        value = endpoint_cache[point]
        if not value.is_finite() or value.contains(0):
            raise Unresolved("A boundary endpoint value cannot be certified finite and nonzero at this precision")
        return value

    def follow(start, stop, depth):
        nonlocal total_argument, accepted, deepest
        deepest = max(deepest, depth)
        za, zb = endpoint(start), endpoint(stop)
        image = evaluate(segment_ball(start, stop))
        increment = None
        if image.is_finite() and not image.contains(0):
            quotient = zb / za
            if quotient.is_finite() and not quotient.contains(0):
                phase = quotient.arg()
                if phase.is_finite() and phase > -pi and phase < pi:
                    increment = phase
        if increment is None:
            if depth >= max_depth:
                raise Unresolved("Max subdivision depth reached before whole-segment exclusion and phase bound were certified")
            middle = tuple((x + y) / 2 for x, y in zip(start, stop))
            follow(start, middle, depth + 1)
            follow(middle, stop, depth + 1)
            return
        total_argument += increment
        accepted += 1
        if include_segments:
            segments.append({"start_exact": [str(x) for x in start],
                             "stop_exact": [str(x) for x in stop], "depth": depth,
                             "whole_segment_image_enclosure": str(image),
                             "argument_increment_enclosure": str(increment),
                             "image_finite_and_excludes_zero": True,
                             "increment_strictly_between_minus_pi_and_pi": True})

    try:
        vertices = [(a, c), (b, c), (b, d), (a, d), (a, c)]
        for start, stop in zip(vertices, vertices[1:]):
            follow(start, stop, 0)
        winding_ball = total_argument / (2 * pi)
        integer = winding_ball.unique_fmpz() if winding_ball.is_finite() else None
        result["total_argument_enclosure"] = str(total_argument)
        result["normalized_winding_enclosure"] = str(winding_ball)
        if integer is None:
            raise Unresolved("Normalized argument enclosure does not contain a unique integer")
        count = int(integer)
        if count < 0:
            raise Unresolved("Unexpected negative count for the declared pole-free analytic function")
        result.update({"status": "certified", "count": count,
                       "boundary_certified_zero_free": True,
                       "off_line_certified": bool(func == "zeta" and count > 0 and
                                                   0 < a < b < 1 and 0 < c < d and
                                                   (b < Fraction(1, 2) or a > Fraction(1, 2))),
                       "interpretation": "Synthetic polynomial calibration only; not a zeta result"
                                         if func == "synthetic_linear" else
                                         "Exact zeta zero count, with multiplicity, in the open rectangle"})
    except Unresolved as exc:
        result.update({"status": "unresolved", "reason": str(exc),
                       "count": None, "off_line_certified": False,
                       "boundary_certified_zero_free": False})
    except Exception as exc:
        # Library failures must never silently turn into a certified zero count.
        result.update({"status": "unresolved", "reason": f"Evaluation failure: {type(exc).__name__}: {exc}",
                       "count": None, "off_line_certified": False,
                       "boundary_certified_zero_free": False})
    finally:
        result.update({"working_bits": ctx.prec, "function_evaluations": evaluations,
                       "accepted_segments": accepted, "deepest_subdivision": deepest,
                       "elapsed_seconds": time.perf_counter() - started,
                       "segment_enclosures_are_display_strings": True})
        if include_segments:
            result["segments"] = segments
        ctx.prec = old_precision
    return result
