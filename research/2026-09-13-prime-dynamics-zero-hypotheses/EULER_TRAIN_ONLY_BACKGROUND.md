# Training-only known-line background model — 2026-09-16

This round tests an implementable nuisance regression after the oracle
background-subtraction diagnostic. It does not subtract a unit-weight
reference, use holdout data to fit a background, or give the modulation
frequency to the unknown-frequency selector. The actual-arithmetic discovery
runner and its thresholds are unchanged.

## Frozen comparison

The original model uses the baseline `1,u-u0`. The nuisance model adds
cosine/sine terms at all six numerical critical-line ordinates between 4 and
40. The catalogue is computed with mpmath and is calibration metadata, not
an interval certificate. It is fixed before evaluation and does not depend on
which unknown modulation is tested.

For each candidate frequency t, jointly fit baseline plus target cosine/sine
on training data. The null regression contains the **same background basis**
but no target. Both sets of coefficients freeze before holdout prediction.
This avoids sequentially removing a background and then treating the removed
target component as data. It does not guarantee that a misspecified background
cannot attenuate a real target; sensitivity must be measured.

All channels use constant envelopes and separate coefficients. Mertens,
global psi and local short-psi remain mandatory primary families; weighted
prime count remains diagnostic. Six known tones add 12 background columns:
14 baseline parameters and 16 parameters with the candidate tone. Matrices
must have full rank, condition number <=1e8, and a common training sample
count at least twice the full parameter count. Invalid fits fail the task.

N=30,000/100,000; grids 192/256 at trims 0/.08; cuts .55/.75; theta=.525.
The scan is 4..40 at step .25, excluding .35 neighborhoods of the known
ordinates, with three nominations separated by .5. The common earliest
training prefix and short-window support purge are retained. The score is
the minimum gain over all primary families and eight cells.

Modulation t=18/27, epsilon=.03/.1/.3, new phase seeds 14--17 yield 24
designs. The .03 amplitude adds a weaker-signal check to the earlier .1/.3
cases. The same coupled Euler weights generate all coefficient arrays;
each of 19 global, 19 log-bin and 19 integer-block weight shuffles rebuilds
them and repeats selection under both models. Control maxima pool both
models and every nomination, separately for each design. The budget's rank
resolution is .05; this is not the >=199-replicate production protocol.

24*(1+3*19)+1 = 1,393 resumable tasks, including a unit-weight reference.
Each task contains both models, coefficients, prediction SSEs, gains and
matrix condition numbers. Source/runtime/configuration provenance is fixed
before evaluating tasks; changed manifests cannot reuse an output directory.
Windows sharing errors receive bounded atomic-write retries. Smoke uses
N=5,000/10,000, one new phase and one control replicate: 25/25 completed,
zero failures. Smoke does not evaluate significance.

## Executed results

The run at `runs/euler-background-20260916/` completed **1,393/1,393**
tasks with zero failures in approximately 125 seconds. Stderr was empty;
the process exited. All outputs retain the frozen pre-run configuration.

| epsilon | Model | Modulation neighborhood nominated | Modulation positive in all primary cells | Modulation descriptive control pass | Designs |
|---|---|---:|---:|---:|---:|
| .03 | Original linear baseline | 0 | 0 | 0 | 8 |
| .03 | Known-line nuisance | 1 | 0 | 0 | 8 |
| .1 | Original linear baseline | 0 | 0 | 0 | 8 |
| .1 | Known-line nuisance | 4 | 0 | 0 | 8 |
| .3 | Original linear baseline | 1 | 0 | 0 | 8 |
| .3 | Known-line nuisance | 8 | 5 | 5 | 8 |

Neighborhood recovery allows error <=.25 and is not exact recovery. The
five passing designs are all four t=18, epsilon=.3 phase designs and one
t=27, epsilon=.3 design (seed 16). The latter has two passing nominations,
so there are six passing nominations across five designs, not five zeta
candidates. No design passes at either weaker amplitude.

| Modulation t | Seed | Nominated t | Minimum held-out gain |
|---:|---:|---:|---:|
| 18 | 14 | 17.75 | .002353 |
| 18 | 15 | 17.75 | .002553 |
| 18 | 16 | 18 | .187088 |
| 18 | 17 | 18 | .023766 |
| 27 | 16 | 26.75 | .055719 |
| 27 | 16 | 27.25 | .008236 |

All listed ranks are exactly .05 for all three controls: no exceedance out
of only 19 replicates, reported with the add-one formula. This is the
smallest resolvable rank, not a precision estimate of a population tail.
Two gains are only about .0024/.0026 and must not be described as strong
predictive effects. New phases and >=199 replicates per control are needed
before treating the improvement as stable model sensitivity.

The unit-weight reference has negative best joint scores under both models
(-.139798 original; -.020709 nuisance). It is one reference dataset, not a
false-positive study. The regression tests plus this reference do not rule
out weak-signal absorption or spurious nominations elsewhere.

**Decision:** retain the candidate generator used for actual arithmetic.
The nuisance model is promising on the strongest injected Euler-model
perturbations but has not passed production calibration. A separate frozen
confirmation should increase control resolution to B>=199, use unused phase
seeds, retain weak perturbations and test a declared boundary of excluded
known-line neighborhoods. That follow-up must not tune parameters using
these holdout outcomes or reinterpret weights as inserted zeta zeros.

All 16 Euler regression tests and Python 3.14 syntax checks passed. Raw task
JSONs remain in the run directory; the tracked evidence records source
hashes, summary and every task hash. Python 3.10 is unavailable on this host.

## Evidence boundaries

A positive prediction plus all three within-design ranks <=.05 is labeled
only a descriptive *model* control pass. The comparison does not correct
across all 24 designs, establish arithmetic exchangeability, or manufacture
a zeta zero through modulation. Ordinary-unit-weight output is a reference,
not an estimated false-positive rate. Candidate count remains null with
MODEL_CALIBRATION_ONLY. There is no actual zeta root search or Arb/FLINT
certification, even if a model row meets the descriptive conditions.

New regression tests verify original-detector equivalence when no nuisance
frequencies are present, unchanged background/target coefficients and
selection under altered holdouts, and recovery of a .01-amplitude tone amid
strong known-tone background in a correctly specified synthetic case.
The last test validates implementation; it does not establish sensitivity
to true zeros or to the more complicated Euler-weight model response.
