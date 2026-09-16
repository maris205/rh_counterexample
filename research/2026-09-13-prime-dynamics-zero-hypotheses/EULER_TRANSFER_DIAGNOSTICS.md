# Fixed-frequency channel transfer — 2026-09-16

The next calibration fixes the injected frequency rather than selecting it,
and examines each channel separately on new phase seeds 2,3,4,5 (previous
Euler calibration used 0,1). All 16 design tasks completed without failures:
t=18/27, epsilon=.1/.3, N=30,000/100,000, grids 192/256 with trims 0/.08,
cuts .55/.75, short-window theta=.525. There are 3,072 fit records.

The configuration and source hashes were saved before evaluating outcomes.
This is a new-phase, fixed-frequency diagnostic on reused arithmetic scales,
not blind arithmetic replication or an unknown-frequency test. The original
joint discovery runner was not changed. Data reside in
`runs/euler-transfer-diagnostics-20260916/`; tracked evidence includes every
task's SHA-256 plus the manifest and aggregate summary.

## Comparison fixed before running

Every cell fits its intercept, trend, cosine and sine on training data only;
short-window training support is purged before the holdout boundary. Holdout
SSE is compared with the separately fitted training-only trend baseline.
Frequency is the supplied modulation frequency. We compare beta=0,.2625,.5
in `exp(beta*(u-log(100)))`, reporting every model rather than selecting the
best against holdout data. The first is the original constant envelope; .5
tests cumulative sqrt-x growth and theta/2=.2625 tests short sqrt-h growth.
Neither is a claimed analytic envelope for the inverse/Mertens channel.

Two views are evaluated: the complete weighted-model observation, and its
paired difference from the exact unit-weight reference after the same
cumulative, short-window and normalization operations. The latter removes
the known ordinary background in this model experiment; such a reference is
not available for an unknown perturbation of actual arithmetic data.

## Results

Counts below require positive prediction in all eight scale/grid/cut cells
for that channel and design. They are not independent Bernoulli trials.

| Channel | Full signal, beta=0 | Paired difference, beta=0 | Full signal, beta=.5 |
|---|---:|---:|---:|
| Mertens | 3/16 | 15/16 | 0/16 |
| psi | 16/16 | 16/16 | 16/16 |
| weighted prime count | 16/16 | 16/16 | 16/16 |
| short psi | 16/16 | 16/16 | 3/16 |

For full psi, median held-out gain rises from .3540 at beta=0 to .8464 at
beta=.5. For full Mertens, the corresponding median changes from .0210 to
-.0632. For short psi, beta=.2625 raises median gain from .2718 to .3818,
but all-cell success drops from 16/16 to 14/16: a better median does not mean
a better strict robustness gate. Paired Mertens at beta=.2625 succeeds in
16/16 designs (median .4932). All detailed comparisons are retained.

These measurements support a weak/masked fixed-frequency response in the
full Mertens observable and channel-dependent envelope mismatch as limitations
of the current toy-model detector. They do not prove a unique failure cause
for the earlier unknown-frequency selection: different phase designs and
supplied frequencies make the tests different. No threshold was relaxed and
no per-channel envelope was selected as a new discovery model after this run.

## Limits and next experiment

The Euler weights are formal model perturbations, not inserted zeta zeros.
There is no surrogate significance test in this diagnostic; candidate count
is null. Neither actual zeta evaluation nor Arb/FLINT certification was done.
The new unit tests verify exact synthetic envelope recovery, invariance of
training coefficients to changed holdout data, and invalidation of a constant
baseline. All three passed, along with the prior Euler identity tests.

A sensible next experiment would compare *predeclared channel-dependent
transfer models* with the unchanged model on additional phase seeds, repeating
unknown-frequency selection inside every control. It must retain Mertens as
a required channel and must not use paired model subtraction as an available
operation on real unknown signals. Passing that experiment still would not
complete the full RH-search protocol.
