# Frozen channel-envelope comparison — 2026-09-16

This model comparison follows the fixed-frequency transfer diagnostic.
Unlike that diagnostic, both models now select an unknown frequency from
training data, and every surrogate repeats selection. The two model variants
were fixed before the run and are reported side by side; the real arithmetic
discovery runner is unchanged.

## Frozen design

| Channel | Original model beta | Channel-envelope model beta |
|---|---:|---:|
| Mertens | 0 | 0 |
| global psi | 0 | .5 |
| weighted prime count (diagnostic) | 0 | .5 |
| short psi | 0 | .2625 |

The envelope is `exp(beta*(log(x)-log(100)))`. These are model transfer
parameters, not zeta real parts. Mertens remains a mandatory primary channel
and retains the original constant-envelope regression. No paired subtraction
of the known unit-weight model is used.

Both use N=30,000/100,000; grids 192/256 with trims 0/.08; cuts .55/.75;
short-window theta=.525. Modulation t=18/27 and epsilon=.1/.3 are crossed
with new phase seeds 6,7,8,9. There are 16 phase designs, using the same
arithmetic scales as earlier work. They are not independent arithmetic data.
The model weights remain `1+epsilon*cos(t*log(p)+phase)` on actual primes.
All coefficients are rebuilt from the same weights using the tested Euler
coefficient identities, including reciprocal/Mertens coefficients.

For each model: t scan 4..40 step .25, known-line exclusion radius .35,
three training nominations separated by at least .5. Selection maximizes
the minimum primary-family training gain on the common purged prefix.
Coefficients are fitted separately per channel and frozen for prediction;
the observed score is the minimum gain over all primary families and eight
scale/grid/cut cells. A positive median cannot replace positivity everywhere.

For each design, 19 global, 19 log-bin and 19 integer-block prime-weight
permutations are shared between models. Each transformation rebuilds all
coefficients and repeats training selection. The null maximum includes
**both models and every nominated frequency**. This accounts for these two
model variants in the within-design rank; it does not create a discovery
test pooled across all 16 designs. Rank resolution is .05, only a diagnostic
budget, not the >=199-replicate production budget of the wider protocol.

There are 16*(1+3*19)+1 = 929 tasks, including one unit-weight reference.
Each task stores both models, selected frequencies, per-cell gains and the
pooled maximum. JSONs are independently resumable under an immutable source,
runtime and configuration hash. Progress writes retry transient Windows
permission errors for a bounded interval. Existing results are not overwritten
under a changed manifest.

Smoke uses N=5,000/10,000, one phase per design and one replicate per control:
17/17 completed with zero failures. This verifies execution/schema only.

## Executed result

Output: `runs/euler-envelope-comparison-20260916/`. All **929/929** tasks
completed, zero failures, approximately 70 seconds, stderr empty. The process
exited; there is no background experiment left running. Each task's manifest
ID, shared model maximum and purged training boundary was checked. The tracked
`EULER_ENVELOPE_EVIDENCE_2026-09-16.json` retains manifest, full summary,
summary hash and 929 individual task hashes.

| Model | Modulation neighborhood nominated | Modulation passes positive prediction | Any all-positive nomination |
|---|---:|---:|---:|
| Constant envelope | 2/16 | 0/16 | 0/16 |
| Channel envelopes | 2/16 | 0/16 | 0/16 |

Recovery here means a nomination within .25 of modulation t, not an exact
frequency recovery. Both reported successes are the boundary nomination
26.75 for modulation 27, epsilon=.3, seeds 6 and 7. Neither achieves
positive prediction in every required cell.

For the best nomination of each design (a descriptive post-run analysis),
the minimum-score channel is Mertens in all 16 original-model designs.
With channel envelopes it is psi in 14 designs and Mertens in two. Thus
fixing the envelopes of prime channels does not solve the joint problem;
wrong/nearby nominated frequencies can also perform poorly when extrapolated
with a growing envelope. These statistics do not establish the unique cause.

The within-design pooled control ranks range from .05 to 1 for both models.
Even a .05 rank cannot rescue the failed positive-prediction condition, and
none is a pooled discovery result across model designs. Candidate count remains
null, not a measured zero count of actual-zeta candidates.

**Decision:** retain the existing discovery model. The proposed channel
envelopes have not improved joint recovery under this frozen comparison.
Before increasing computation, inspect training-only frequency localization
and Mertens signal/background separation in model data; any proposed change
must subsequently repeat the whole unknown-frequency control procedure on
new designs. The known modulation frequency must not be supplied to the
unknown-frequency selector to make that comparison pass.

## Validation and interpretation

Tests verify equivalence to the original constant-envelope detector; exact
recovery of synthetic channel-dependent envelopes; invariance of selection
to changed holdouts; inclusion of both models in the control maximum; and
bounded retry of a simulated Windows sharing violation. These tests are not
evidence that the model resembles zeta zeros.

All 11 Euler-model regression tests (five new plus six prior), Python 3.14
syntax checks and artifact integrity checks passed. Python 3.10 remains
unavailable on this host; the manifest records the actual 3.14 runtime.

The source data are weighted Euler-model observables, not ordinary prime
counting. Modulation need not produce a single tone in every observed
channel and does not insert a known zero. No passing model row can authorize
actual zeta root finding. Candidate count stays null with
MODEL_COMPARISON_ONLY. No actual zeta search or Arb/FLINT certification is
performed. Any later revised model requires another frozen comparison on
new designs, rather than selecting a favorable envelope on these holdouts.
