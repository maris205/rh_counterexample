# Localization versus model background — 2026-09-16

Completed 16/16 new-phase design tasks with zero failures, after a 4/4 smoke.
Run: `runs/euler-localization-20260916/`. The same design is examined with
coarse and fine frequency grids and with full versus paired-difference data.
This is an explicitly descriptive model experiment, not a surrogate gate.

## Design fixed before evaluation

Use t=18/27, epsilon=.1/.3, new phase seeds 10--13, N=30,000/100,000,
192/256 sample grids at trims 0/.08, cuts .55/.75, short theta=.525.
Both models are unchanged from the previous comparison: constant envelope,
and channel envelopes (Mertens=0, psi/prime-count=.5, short-psi=.2625).
All models use full observations without reference subtraction, except the
explicitly marked paired-difference diagnostic view.

Scan 4..40 at steps .25 and .025 with the same .35 known-line exclusion,
three nominations separated by .5, minimum primary training-gain objective,
and the same common purged prefix. The target frequency is never used to
choose nominations or to restrict a local search bracket. Separately, a
forced-target prediction records what would happen if the modulation
frequency were supplied; it is always an oracle diagnostic.

The prefix log-span is approximately 2.92638. The associated scale
2*pi/span is approximately 2.14708; this is a descriptive finite-window
scale, not a theorem limiting frequency estimation precision. A finer grid
does not lengthen the training window or add arithmetic samples.

## Results

Recovery counts mean at least one of the three training nominations is
within .25 of the modulation frequency. Positive counts mean at least one
nomination predicts positively in every primary-family/scale/grid/cut cell;
they do not mean a surrogate gate passed. All counts are out of 16 designs.

| View | Model | Step | Within .25 | Within .05 | Any all-positive nomination | Supplied-target all-positive |
|---|---|---:|---:|---:|---:|---:|
| Full | Constant | .25 | 0 | 0 | 0 | 2 |
| Full | Constant | .025 | 0 | 0 | 0 | 2 |
| Full | Channel envelopes | .25 | 1 | 0 | 0 | 2 |
| Full | Channel envelopes | .025 | 0 | 0 | 0 | 2 |
| Paired difference | Constant | .25 | 16 | 10 | 11 | 11 |
| Paired difference | Constant | .025 | 15 | 4 | 12 | 11 |
| Paired difference | Channel envelopes | .25 | 15 | 10 | 11 | 11 |
| Paired difference | Channel envelopes | .025 | 14 | 4 | 11 | 11 |

For full constant-envelope data, median nearest-nomination error changes
from 1.625 to 1.4875 when the grid is refined. This does not recover the
modulation neighborhood in any design. In paired constant-envelope data,
the median error changes from 0 to .0875: with finite-window/background
effects, a sampled objective optimum need not equal the imposed frequency.
Both imposed frequencies happen to lie on the coarse grid, so its apparent
exact recovery must not be generalized to off-grid signals.

At the imposed frequency, median full-data training gain is .01096 for
Mertens versus .21591 for psi and .19306 for short psi under the constant
model. In paired differences those values are .16857, .64894 and .78620.
The paired comparison changes all channels, not Mertens alone. Thus it
supports a background/model-response limitation, but does not uniquely
attribute every failed nomination to the Mertens background.

## Decision and limits

Do not enlarge the discovery scan merely by making its step ten times
smaller: this comparison gives no full-data recovery benefit sufficient to
justify it. Do not relax the all-primary-cell gate or substitute a supplied
target frequency. The discovery runner and its thresholds remain unchanged.

Paired subtraction uses an exact unit-weight reference known only in the
synthetic construction. Those positive predictions are not deployable
arithmetic discoveries. These new phases reuse arithmetic data and are not
independent replications; candidate count is null, DIAGNOSTIC_ONLY. No
controls, discovery significance, actual zeta roots or interval certificates
were evaluated here.

Next priority is a training-only background model that requires no oracle
subtraction, with explicit checks that it does not remove weak injected
modes. Such a model must be frozen and tested on further phases, and the
complete unknown-frequency selection must run inside every surrogate before
any actual screening use. This diagnostic does not authorize that promotion.

## Verification

Two new tests check precise localization of an off-coarse-grid synthetic
tone and invariance of the entire training score curve to changed holdouts.
Together with the prior Euler tests, 13 regression tests pass. Python 3.14
syntax checks pass; Python 3.10 is unavailable on this host. All 16 artifacts
have matching source/configuration IDs and satisfy the purged support
boundary. The tracked evidence stores all per-task diagnostics and hashes.
