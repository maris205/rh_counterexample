# Phase interval diagnostic (Python 3)

`dh_phase_interval_py3.py` turns each Taylor disk into an angular interval
using

\[
|\Delta\arg|\le \arcsin(r/|F(s_0)|).
\]

For the known DH root rectangle:

| segments per edge | all disks exclude 0 | nominal winding | winding interval |
|---:|---:|---:|---:|
| 16 | yes | 1.0000 | `[-0.16961, 2.16961]` |
| 32 | yes | 1.0000 | `[-0.14554, 2.14554]` |

The interval contains the integer 1 but is still too wide to certify a unique
winding number. The width is dominated by summing local angular uncertainties.
The next improvement is adaptive edge subdivision and/or a second-order Taylor
remainder, followed by an independent proof of the derivative and Hurwitz
remainder bounds. Current status remains `NONCERTIFIED_PHASE_INTERVAL_DIAGNOSTIC`.
