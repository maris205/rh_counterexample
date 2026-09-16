# Correction and executed validation — 2026-09-16

This round repairs misleading evidence labels and implements a limited joint
prediction screen. It does not complete every gate of the broader protocol.
Historical artifacts were not edited. All paths below are relative to the
repository root; on this host the root is
`C:/Users/wangl/Documents/rh_counter/rh_counterexample`.

## Corrections

- Enumerate known critical-line ordinates over the entire scan and exclusion
  margin. The sixth ordinate is `37.58617815882567`; peaks at 37.5/37.6 are
  known-line-neighborhood diagnostics, not discoveries. The numerical catalogue
  is computed with mpmath; it is not an interval certificate.
- Withdraw cross-channel/mixed-frequency phase pooling and unmatched q95
  comparisons as candidate rejection evidence. Exact same-channel/frequency
  phase groups can remain descriptive. Prime-count, psi, and theta are related
  observables, not three independent votes.
- Correct raw-coefficient versus cumulative-array control inputs, inclusive
  Mertens endpoints, and the observed/control derivative mismatch. Use stable
  SHA-derived seeds rather than process-randomized Python hashes.
- Correct short-window expected counts to actual support and normalize gaps
  by division by `log(p)`. Restrict prime-position shuffles to indices >=2;
  otherwise a surrogate can produce `p=1`, making the gap normalization invalid.
- Actually execute density and gap controls in B; report per-grid/per-cut
  descriptive effects and ranks. Old holdout refits remain labeled projections.
  C labels borrowed character probes and incomplete family coverage honestly.
- Unevaluated joint gates use `null` counts. Resume requires matching source,
  runtime and configuration provenance; failures are persisted and counted.

## Executed runs

| Run directory under `runs/` | Completed / total | Failed | Joint screen result |
| --- | ---: | ---: | --- |
| `common-spectrum-v2-smoke-purged-20260916` | 7 / 7 | 0 | NOT_EVALUATED; insufficient control resolution |
| `common-spectrum-v2-validation-20260916` | 58 / 58 | 0 | EVALUATED; 0 finite screen candidates |
| `common-spectrum-v2-long-20260916` | 598 / 598 | 0 | EVALUATED; 0 finite screen candidates |
| `common-spectrum-v2-power-20260916` | 121 / 121 | 0 | Observation-layer injection diagnostic; no candidate gate |
| `short-interval-phaseB-v2-validation-20260916` | 0 / 4 | 4 | Failed initial expanded B run; preserved |
| `short-interval-phaseB-v2-validation-r2-20260916` | 4 / 4 | 0 | Corrected B controls; NOT_EVALUATED joint gate |
| `family-phaseC-v2-smoke` | 4 / 4 | 0 | NOT_EVALUATED |

The initial expanded B run exposed `p=1` in shuffled prime positions and
nonfinite gap metrics. Its four failed JSONs remain in the original directory.
After restricting the shuffle domain to indices >=2 and adding a 50-seed/mode
regression check, all four new B artifacts succeeded without warnings. They
cover N=100,000/300,000, theta=0.525/0.60, grids 192/256 with trims 0/0.08,
cuts 0.55/0.75, and 19 replicates each for global, two block, density and gap
controls. Their metrics remain descriptive projections, not a joint gate.

The tracked [machine-readable evidence](VALIDATION_EVIDENCE_2026-09-16.json)
contains summary hashes, frozen manifests, control scores and prediction cells;
individual task JSONs remain in the local run directories.

The production run used `N=1,000,000,5,000,000`, 512/768 samples with trims
0/0.08, split fractions 0.55/0.75, `theta=0.525`, `x_min=100`, and
`4<=t<=40` with step 0.1, exclusion margin 0.35, `beta=0` and three
training-nominated separated frequencies. Each of global shuffle, within-block
shuffle (250,000 entries), and log-density-preserving shuffle (64 bins) has
199 replicates. One permutation of coefficient tuples is shared by Mertens
and prime observables in each replicate. These are empirical stress models,
not justified exchangeable probability models of arithmetic.

All frequency selection uses the earliest common training prefix. Each
observable has its own train-only trend/amplitude/phase; coefficients freeze
for held-out predictions. Short training windows ending in a holdout are
purged. The score is the minimum predictive SSE improvement across Mertens,
global psi, local short-psi and every scale/grid/cut. Prime count is an
additional correlated diagnostic. Each surrogate repeats selection and takes
the maximum of its nominated scores before ranking the observed score.

| Nominated t | Minimum held-out improvement | Global rank | Block rank | Density rank |
| ---: | ---: | ---: | ---: | ---: |
| 24.6 | -0.122782 | 0.815 | 0.775 | 0.910 |
| 20.5 | -0.204106 | 0.925 | 0.915 | 0.985 |
| 13.7 | -0.537586 | 0.995 | 0.990 | 1.000 |

All three fail the positive-prediction requirement. The empirical rank
resolution is 0.005; ranks are far from the 0.05 threshold. No confidence
claim about RH follows. Nested arithmetic scales and overlapping grids/cuts
are dependent robustness checks. This is exploratory reanalysis, not a fresh
blind external replication. Excluded neighborhoods can hide other signals;
the exclusion is a discovery convention, not an exclusion theorem.

The background production run completed in approximately 219 seconds; stderr
was empty and its process exited. Vectorization made an hours-long wait
unnecessary. The old 15-minute heartbeat remains paused; no completed-output
polling loop is required.

## Sensitivity and limitations

Observation-layer tones at t=18,27,35 were added with four separate channel
phases and amplitude units fixed from the common training prefix. There are
ten phase designs per frequency/amplitude and one unchanged baseline, for
121 cases. All 120 injected frequencies appeared in the top-three training
list. Requiring positive predictions in every primary cell was stricter:

| Amplitude / training channel SD | t=18 | t=27 | t=35 |
| ---: | ---: | ---: | ---: |
| 0.5 | 4/10 | 1/10 | 0/10 |
| 1.0 | 8/10 | 7/10 | 4/10 |
| 2.0 | 10/10 | 10/10 | 10/10 |
| 4.0 | 10/10 | 10/10 | 10/10 |

The unchanged baseline had no all-positive candidate. These design trials are
not independent samples of the primes and do not estimate an arithmetic false
positive probability. Tones were injected after observation/resampling; this
does not validate explicit-formula transfer, short-window attenuation, or
growth envelopes. Weak signals can be missed by this detector.

The next quantitative route is **pre-operator injection** of known-line and
off-line-orbit model terms, then the identical observation operators and full
surrogate screen. It should measure attenuation, leakage, recovery and missed
signals before widening searches. Complete B/C family-transfer gates and a
fresh disjoint validation interval remain open. No finite-spectrum row from
this round is eligible for an actual zeta search. No actual zeta root finding
or Arb/FLINT interval certification was done.

That route's first calibration is now executed at
`runs/common-spectrum-operator-power-20260916/`: 49/49 cases, two scales,
two grids, two cuts, `t=18` as an unknown discovery frequency and
`t=37.58617815882567` as an explicitly known-line calibration frequency,
`beta=0,0.05`, amplitudes 0.5/1/2, and four phase designs. Perturbations were
added to coefficient arrays before cumulative sums and short-window
transformations. The t=18 tone was selected in 24/24 discovery cases, while
all-primary-cell positive prediction was 0/24. The known-line calibration was
selected 24/24; its positive-prediction result was 4/24. This exposes
attenuation or phase/prediction incompatibility in the present strict gate.
The synthetic coefficients preserve no prime law and do not justify a null or
an RH inference. Growth `beta` is a transfer stress parameter, never a fitted
zeta real part.

## Runtime and verification

`py -3.10` is unavailable on this host. Actual execution used `py -3.14`,
Python 3.14.3, NumPy 2.5.3, SciPy 1.18.1, mpmath 1.4.1 and python-flint 0.9.0.
These are recorded in run provenance; Python 3.10 compatibility was not tested.
Regression coverage includes synthetic recovery, rejected holdout phase
reversal, selection leakage, window support, finite controls, inclusive
endpoints, phase grouping, domain-preserving shuffles, manifest mismatch,
failure accounting and resume. Tests intentionally inject failures; their
temporary failed-task lines are not failures of the scientific batches.
All 23 targeted regression tests and Python 3 syntax compilation passed.

## Preserved historical evidence

These hashes identify untouched old outputs. Their interpretation is corrected
above; they must not be silently reused as V2 results.

| Path under `runs/` | SHA-256 |
| --- | --- |
| `prime-spectrum-phaseA-py3/summary.json` | `42081cd7879ee20f426687c4ca32cf7a4845f0c49ff7695169a67aafcf58fe97` |
| `short-interval-phaseB-py3/summary.json` | `9272d756fb09bef8796a4b3f0d41530cacc1508f63bdec9c3261ef5debd95afa` |
| `family-phaseC-py3/summary.json` | `d8121b848e33e144e3e74878a50d90bbafb698c421aadf2c872739643779bce2` |
| `prime-spectrum-phaseA-py3/phase-concordance-audit.json` | `87df6c415506bd2164d9fdab20ab1ead445b96e986d5fec7fbaec12d6b208d3e` |

The corrected phase audit is stored separately at
`runs/phase-a-correction-20260916/phase-concordance.json`.
