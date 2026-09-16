# Phase A theory note: corrected interpretation (2026-09-16)

The old Phase A artifacts do not establish an unknown common spectral atom,
and they do not supply a valid test rejecting one. The prospective replacement
is [COMMON_SPECTRUM_PROTOCOL_V2.md](COMMON_SPECTRUM_PROTOCOL_V2.md). Existing
data have already been inspected; a corrected reanalysis of them is exploratory,
even if its program and random seeds are subsequently frozen.

## Corrections to the earlier note

1. **The `t≈37.5` feature is in a known-zero neighborhood.** The sixth
   positive critical-line ordinate is `37.58617815882567...`. The historical
   exclusion table listed only five zeros in a scan reaching `t=40`. A
   neighborhood of `37.5` must therefore be classified as known-line
   calibration, not an unknown-frequency residual. Exclusion now requires
   enumeration through the entire scanned interval and its exclusion margin.
2. **The pooled phase resultants `0.614` and `0.334` are not a rejection
   statistic.** The old audit pooled channel-specific phases at different
   fitted frequencies and grids. A shared frequency does not imply equal
   channel phases. We withdraw the statement that `0.334 < 0.80` rejects the
   common-atom hypothesis. Historical values may be retained only as invalid
   pooled-phase diagnostics. A new phase comparison must hold channel,
   frequency, basis convention, and log-time origin fixed.
3. **`psi` and `theta` are related measurements of the same prime source.**
   Adding prime counting does not create another independent source. Neither
   cumulative/derivative versions nor different resampling grids are
   independent replications. The V2 diversity requirement is Mertens,
   global-prime, and local-prime observable families; their statistical
   dependence still has to be retained in control calibration.
4. **Projection on held-out data was not frozen prediction.** The old
   `tone_power(hold_u, hold_y, t)` calls fit a new trend and new sine/cosine
   coefficients on the holdout. Those scores are descriptive fixed-frequency
   projections. They cannot establish that training amplitude and phase
   predict a later interval. V2 freezes every fitted prediction parameter.
5. **A few control quantiles do not establish a 5% scan-level result.** A
   selected maximum cannot be compared with an unrelated single-frequency
   q95. With `B` Monte Carlo replicates the rank p-value cannot be smaller
   than `1/(B+1)`; four replicates have minimum p-value `0.2`. Historical q95
   comparisons remain descriptive, including cases where the observed score
   is smaller than a control q95. They are not calibrated evidence that an
   arithmetic mode is absent.
6. **Program completion is distinct from candidate-gate completion.** The
   earlier Phase B and C summaries assigned candidate counts literal zero
   without implementing the joint candidate gate. Such zeroes mean no
   candidates were handed off by those programs; they are not measured
   zero-candidate results. The correct unevaluated count is `null`, accompanied
   by `NOT_EVALUATED` or `INCOMPLETE` and the missing tests.

## Model and interpretation

Use the joint regression

`y_c(u) = q_c(u) + exp(beta*(u-u0)) * [a_c*cos(t*(u-u0)) + b_c*sin(t*(u-u0))] + e_c(u)`.

Frequency `t` and, when preregistered, envelope `beta` are shared. Trend
`q_c`, amplitude, and phase are channel-specific. Fit baseline and atom models
on training data, select frequencies there, and evaluate their frozen
predictions on contiguous later log-time data. A negative predictive score is
meaningful and must not be clipped to zero. A separately refitted holdout
phase can be reported as a stability diagnostic, but cannot replace prediction.

The explicit-formula motivation does not identify every observable's fitted
envelope with a zeta zero. Cumulative summation, normalization, finite
differences, short-interval transfer functions, overlapping tones, and trends
change the measured response. If `sigma_fit = 0.5 + beta` is emitted, it is
only a regression parameter. It is not an estimate or certificate of the real
part of an actual zero. A single growing tone is also not the complete
contribution of an off-line symmetry orbit. Nontrivial zeta zeros have real-axis
and critical-line symmetries; RH concerns their actual positions, not fitted
spectral envelopes ([NIST DLMF §25.10](https://dlmf.nist.gov/25.10)).

Window leakage remains a plausible mechanism, not a demonstrated explanation
of every historical peak. Synthetic critical-line tones must pass through the
same sampling, truncation, interpolation, and derivative operators to quantify
their leakage. A null surrogate must be described by what it preserves and
destroys; it is not automatically a probability model for the primes.

The defensible present conclusion is that the historical pipeline did not
establish an eligible unknown-frequency candidate. The corrected checks can
measure predictive sensitivity and empirical false-positive behavior. Only
evaluation of the actual zeta function and a validated off-line zero count can
establish an RH counterexample; neither an empty candidate list nor a failed
finite-data prediction proves an RH-related absence statement.
