#!/usr/bin/env python3
"""Small exact arithmetic check for the proposed phase statistic."""
import cmath
import json
from pathlib import Path

L = [1+0j, 1+0j, 1j, -1j]
models = [1+0j, 1j, -1+0j, cmath.exp(1j*0.731)]

def phase(z):
    if abs(z) == 0:
        raise ValueError("phase is undefined at zero")
    return z / abs(z)

def R(Lvals, M):
    m = phase(M)
    return abs(sum(phase(x) * m.conjugate() for x in Lvals) / len(Lvals))

values = [R(L, m) for m in models]
mean_L_phase = abs(sum(phase(x) for x in L) / len(L))
# A separate vector check: multiplying every model by a random unit phase leaves R unchanged.
rotations = [cmath.exp(1j*a) for a in (0.13, 1.7, 4.2)]
rotated = [R(L, models[0]*q) for q in rotations]
assert max(abs(v - mean_L_phase) for v in values) < 1e-12
assert max(abs(v - values[0]) for v in rotated) < 1e-12

out = {
    "L": [[z.real, z.imag] for z in L],
    "models": [[z.real, z.imag] for z in models],
    "abs_mean_L_phase": mean_L_phase,
    "R_by_model": values,
    "R_after_model_phase_rotations": rotated,
    "all_model_equal_within_1e-12": max(values)-min(values) < 1e-12,
    "all_rotations_equal_within_1e-12": max(rotated)-min(rotated) < 1e-12,
}
Path(__file__).with_suffix('.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps(out, indent=2))
