# Euler-coupled calibration — 2026-09-16

This experiment changes all arithmetic model channels consistently, rather
than holding the Mertens sequence fixed when prime observables change.
It is a finite toy-model calibration, not a constructed zeta zero.

For each actual prime, set
`w_p=1+epsilon*cos(t*log(p)+phase)`. Define a completely multiplicative
sequence `a(p)=w_p`. The formal Euler product then has reciprocal coefficients
`b(n)=mu(n)*a(n)` and logarithmic-derivative coefficients
`L(p^k)=w_p^k*log(p)`, zero away from prime powers. Weighted prime counting
uses `w_p` on actual primes. Thus the same weights generate every channel.

Tests check `a*b=delta`, `L*a=a(n)*log(n)`, and exact recovery of the ordinary
arithmetic arrays at unit weights. This is a formal coefficient identity;
we neither assume an analytic continuation nor claim a zero at modulation t.
Prime counting here is weighted and is explicitly not binary.

## Frozen design and results

Output: `runs/euler-coupled-20260916/`; smoke:
`runs/euler-coupled-smoke-20260916/`.

- N=30,000 and 100,000; grids 192/256 with trims 0/0.08; cuts 0.55/0.75.
- Modulation t=18/27, epsilon=0.1/0.3, two fixed phase seeds: eight designs.
- Unchanged beta=0 joint detector, t scan 4..40 step 0.25, known exclusion
  radius 0.35, three separated training nominations; short theta=0.525.
- For each design, 19 global prime-weight shuffles, 19 log-bin weight
  shuffles and 19 integer-block weight shuffles. Every shuffle rebuilds all
  coefficients from the new weights before repeating frequency selection.
- One unit-weight reference plus eight sets of 58 tasks = **465/465**,
  zero numerical task failures. Smoke completed 33/33.

Neither modulation frequency appeared among its design's three joint
training nominations: **0/8 recovery**. No nominated frequency had positive
prediction in every primary cell; the best minimum gains ranged from
-0.138017 to -0.070242. This only measures this detector/configuration on
these models. It does not establish why recovery fails or how another
amplitude, envelope or observable would behave.

The ordinary x/li baseline was deliberately retained, and can be mismatched
to a weighted Euler model. A sinusoidal weight on primes is not necessarily
a single sinusoid in the reciprocal cumulative channel. Therefore failure
to nominate t is not failure to detect a known injected zero. Surrogate ranks
are descriptive per-design ranks; eight designs are not a calibrated combined
discovery procedure. Candidate count is **null**, with MODEL_CALIBRATION_ONLY.

One Windows PermissionError interrupted replacement of progress.json. The
unchanged runner resumed from matching successful JSONs and completed. This
is recorded separately from the zero numerical-task failure count. The
tracked evidence file contains the manifest, full summary, summary hash and
hash of every task. Raw artifacts are preserved locally.

## What this changes

There is now a model with tested algebraic coupling between the three
families. This does not establish a prime-consistent zero-injection law or
complete Phase C. Before changing discovery thresholds, the next useful
diagnostic is channel-by-channel train-only transfer at the prescribed
modulation frequency, with a preregistered comparison of model-specific
baselines and envelopes on new phase designs.

The previous local position-resampling experiment preserves binary values
and bin counts, but resampled positions may be composite integers; it is not
ordinary prime arithmetic. Also, the previous Phase C unknown-frequency
runner still calls full-window detrending/scaling in
`family_detector_transfer.signal_from_coefficients`: freezing the later
regression alone does not make that run leakage-free. Its chi4/chi5 target
values are borrowed zeta probes, not verified character zero ordinates.
These historical results must not be used as completed family validation.

No actual zeta search or Arb/FLINT certification was performed in this run.
