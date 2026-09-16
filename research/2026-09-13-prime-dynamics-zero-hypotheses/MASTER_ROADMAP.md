# Prime dynamics and zeta: evidence-gated research roadmap

Updated 2026-09-16. This is the authoritative current plan. The previous roadmap
is preserved in [the historical record](MASTER_ROADMAP_HISTORY_2026-09-16.md);
its headings such as "current experiment", completion claims, and shared-envelope
hypotheses are historical, not current scientific acceptance criteria.

## Objective and present decision

**The objective is a rigorously confirmed RH counterexample.** The current
[four-direction visual roadmap](COUNTEREXAMPLE_ROADMAP_2026-09-16.md) is the
portfolio-level plan: direct zeta search; explicit-formula/arithmetic clues;
dynamical and spectral representations; and equivalent-criterion violations.
Existing experiments are reference material, not a requirement to keep developing
their method. A certified violation of an applicable RH-equivalent criterion is
an independent route and need not first produce an explicit zeta-zero coordinate.

**The existing arithmetic branch is validating its measurement method.** Its bottlenecks
are unknown-frequency sensitivity, background separation, and the missing
channel-specific connection from a genuine zero to the measured statistic.
More tasks, larger N, or finer frequency grids do not by themselves resolve them.

No new experiment is launched by this roadmap reset. Completed-run monitoring
stays paused. Select a bounded problem under the new portfolio before running
another batch. The two tracks below remain a conditional plan for continuing the
arithmetic branch, not prerequisites for direct zeta or equivalent-criterion
search. Neither track's completion substitutes for the other within that branch.

Each round should seek a reproducible candidate, a rigorously scoped exclusion,
or a concrete missing bridge/capability boundary that determines the next test.
Finite non-detection or budget exhaustion alone does not exclude a direction.

## Evidence ledger

| Evidence level | What is available | What it establishes |
| --- | --- | --- |
| Actual zeta finite numerical search | Historical record: 305 windows, 40 <= t <= 10000, no off-line numerical candidate | A finite negative numerical screen; the original raw batches have not all been reverified in this reset |
| Corrected arithmetic common-spectrum screen | v2 long: 598/598 tasks, zero failures, zero passing screen candidates | No passing nomination under that finite configuration; the full validation protocol remains incomplete |
| Coupled Euler model calibration | Latest background comparison: 1393/1393 tasks, zero failures | At epsilon=.3, background-model neighborhood recovery 8/8, with descriptive control passes in 5/8 designs; no passes at .03 or .1 |
| Actual new zeta root candidate | None supplied by the recent calibration work | No new off-line root claim |
| Arb/FLINT interval certification | None for an off-line zeta zero | No certified RH counterexample |

The latest 5/8 refers to synthetic designs, not five arithmetic or zeta candidates.
All their control ranks equal the B=19 Monte Carlo floor .05; some held-out gains
are very small. These are within-design comparisons, not a correction for the
whole adaptive research history or a measured arithmetic false-positive rate.
See [background report](EULER_TRAIN_ONLY_BACKGROUND.md),
[background evidence](EULER_BACKGROUND_EVIDENCE_2026-09-16.json), and
[correction report](CORRECTION_REPORT_2026-09-16.md).

## Interpretation corrections that constrain future work

- Distinct channels, grids, cuts, and N values reuse arithmetic information.
  Agreement is robustness evidence, not independent replications or independent
  probability multipliers. Psi, prime count, and short psi are especially related.
- The run named `common-spectrum-v2-disjoint-20260916` separates sampled x
  endpoints from earlier work, but cumulative M and psi still include earlier
  coefficients. It is not validation on independent raw arithmetic support.
- `prime_consistent_power_py3.py` preserves binary occupancy and bin counts,
  while allowing composite locations and holding Mertens fixed. Its name does
  not establish consistency with the actual primes or a zero-injection law.
- Coupled Euler weights satisfy the tested formal coefficient identities, but
  imposed modulation at t is not a constructed zero at sigma + i*t. Recovering
  that modulation does not calibrate sensitivity to an actual off-line zero.
- The 117-task Phase C scan calls full-window derivative, polynomial detrending,
  and scaling before splitting in `family_detector_transfer.py`. It is not a
  valid frozen-preprocessing holdout benchmark. Its chi4/chi5 reference t values
  are borrowed from zeta, not verified zeros of those families. Do not interpret
  their non-recovery as a measured failure to detect genuine family zeros.
- Earlier shared-frequency/shared-envelope hypotheses are proposals. In
  particular, a common envelope across cumulative and short-interval operators
  must not be assumed when converting a fitted growth rate into sigma.

## Arithmetic branch, Track T: establish what the instrument should measure

Deliver a channel-by-channel transfer note before interpreting model power as
zero-detection power. For Mertens, psi, prime count, and short intervals, specify:

1. The generating function and observable operator, including normalization,
   window support, smoothing, truncation, and background terms.
2. The predicted response to a hypothesized zero or symmetry orbit, with explicit
   assumptions, channel-specific envelopes/phases, and error terms or stated
   finite-range limitations. Separate derived statements from heuristics.
3. Which observable parameters can identify frequency or real part, and which
   can be mimicked by known-line background or finite-window artifacts.
4. A suitable positive benchmark with a verified zero of the actual function
   being tested, and a reason the chosen observable should reveal it. Repair
   preprocessing leakage before reusing the old family benchmark.

Acceptance: a checkable response prediction and a benchmark that tests that
prediction without supplying the target frequency to nomination. If this bridge
cannot be justified, retain the detector only as an exploratory arithmetic
statistic; do not present it as a validated guide to off-line zeros.

## Arithmetic branch, Track E: one bounded confirmation of background calibration

If this branch is selected, the training-only known-line nuisance model is its
sole current confirmation candidate. Freeze its source hash, frequency search, nuisance basis, holdout
rules, control statistic, and acceptance criteria before generating new results.

Design requirements for the next protocol, not an already-running batch:

- Fresh phase seeds; retain weak and strong amplitudes and add off-grid and
  near-known-line boundary cases. Keep at least two scales, grids, and cuts.
- At least 199 replicates of each of the three existing control types. Rerun
  nomination inside every control and include every compared model in the
  search correction. Declare how multiple designs will be summarized.
- Evaluate negative/reference cases alongside positive injections. A single
  unit-weight reference is not an estimate of false-positive rate; define what
  a model negative ensemble represents without calling it an arithmetic null.
- Report recovery counts, effect sizes including worst-cell gains, Monte Carlo
  uncertainty, and negative-case behavior. Do not accept on rank <= .05 alone.
- Specify a practically meaningful gain threshold, recovery criterion, negative
  error criterion, and compute cap prospectively in a separate locked protocol.
  These criteria are not yet fixed by this roadmap and must precede execution.

Stopping rule: conduct one locked confirmation. If it fails its declared
criteria, record the sensitivity limit and park this detector version. Do not
relabel failure as a reason for endless larger-N or denser-grid scans. A revised
method requires an explicit new mechanism and a new protocol, with previous
results treated as development data.

Even success accepts only a bounded model-calibration claim. Track T is still
required before an actual arithmetic result can be interpreted as zero-related.

## Subsequent gates for the arithmetic-guided zero-search branch

| Gate | Prerequisite and action | Permitted conclusion |
| --- | --- | --- |
| G1: method validation | Complete Track T and the appropriate frozen positive/negative benchmarks; document sensitivity and dependencies | A qualified instrument within stated ranges, not RH evidence |
| G2: actual arithmetic nomination | Freeze a revised protocol; run cross-channel, cross-grid, cross-scale held-out selection and all controls on prospectively reserved observations; disclose cumulative-support overlap | An arithmetic follow-up nomination only |
| G3: actual zeta evaluation | Only a common nomination passing the frozen arithmetic gate enters the arithmetic-guided root finder; use free sigma, higher precision, and repeatability checks | A numerical zeta candidate if an off-line root persists |
| G4: interval certification | Establish an off-line region with certified boundary conditions and a rigorous zero count using Arb/FLINT | A rigorous claim only if the certification actually succeeds |

A separately justified direct zeta search does not logically require the model
calibration route. It is the direct-search main line in the macro roadmap, but
no new search region or batch has been scheduled here. Historical finite scans
have no candidate. Do not repeat completed windows merely to keep a long process
running. The dynamical/spectral branch needs a proved connection to the actual
target before its model zeros can support zeta claims. Equivalent-criterion
work instead requires exact theorem hypotheses and rigorous violation bounds.

## Work deliberately deferred

No broad increase in N, tenfold finer scans, oracle paired-reference subtraction
as a discovery method, new surrogate variants without a specific hypothesis, or
automatic zeta handoff from a single-channel anomaly. Preserve the current
reproducible batch infrastructure and evidence artifacts; replace task-count
progress with accepted or failed scientific gates.

Operationally, a future approved protocol uses resumable per-task JSON, atomic
progress, source/config hashes, a smoke test, absolute run paths, and quiet
exception-only monitoring. The available interpreter in this environment is
`py -3.14`; the originally requested `py -3.10` is unavailable. Any new run must
record its actual runtime rather than imply Python 3.10 was used.
