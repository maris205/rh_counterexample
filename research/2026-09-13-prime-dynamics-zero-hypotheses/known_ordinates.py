"""Numerical known-line calibration ordinates covering the requested band.

This is exclusion metadata computed by mpmath, not an interval certificate.
No off-line search is performed. Boundary neighborhoods are included.
"""
from functools import lru_cache
import math

import mpmath as mp
import numpy as np


@lru_cache(maxsize=64)
def known_ordinates(t_min: float, t_max: float, margin: float = 0.35) -> tuple[float, ...]:
    if not all(math.isfinite(v) for v in (t_min, t_max, margin)):
        raise ValueError("frequency bounds and margin must be finite")
    if t_min < 0 or t_max < t_min or margin < 0:
        raise ValueError("require 0 <= t_min <= t_max and margin >= 0")
    result = []
    with mp.workdps(35):
        index = 1
        while True:
            ordinate = float(mp.im(mp.zetazero(index)))
            if ordinate > t_max + margin:
                break
            if ordinate >= t_min - margin:
                result.append(ordinate)
            index += 1
    return tuple(result)


def known_mask(ts, margin: float = 0.35) -> np.ndarray:
    """True means exclude this frequency as known-line calibration/leakage."""
    values = np.asarray(ts, dtype=float)
    if not values.size:
        return np.zeros(values.shape, dtype=bool)
    ordinates = known_ordinates(float(values.min()), float(values.max()), margin)
    result = np.zeros(values.shape, dtype=bool)
    for ordinate in ordinates:
        result |= np.abs(values - ordinate) <= margin
    return result
