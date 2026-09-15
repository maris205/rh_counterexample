# Phase A theory note: why common finite spectra are weak evidence

The Phase A `t≈37.5` cluster is compatible with a shared observation window
effect. All channels are sampled on a finite interval in `u=log(x)`, and the
Mertens and psi/theta signals are cumulative sums before interpolation. A
polynomial trend, endpoint trim, and numerical derivative define a filter
whose leakage pattern is shared by channels. Nearby frequencies can therefore
land in the same grid bucket without a common arithmetic atom.

The phase audit in `phase-concordance-audit.json` gives circular phase
resultants `0.614` at `N=10^6` and `0.334` at `N=5*10^6`; the conservative
cross-scale value is `0.334`, far below the preregistered `0.80` gate. The
maximum observed R² is also below the largest control top-q95 in both scales.
This is a finite-screen rejection of the residual, not a statement about the
zeta function.

Useful next tests are:

1. Fit a joint sinusoid with a shared `(t, sigma)` but channel-specific
   amplitudes/phases, and compare its held-out likelihood with a model whose
   frequency is independently fitted per channel. Calibrate the likelihood
   ratio by the same global, block, density-preserving, and phase-randomized
   surrogates.
2. Replace FFT buckets by continuous frequency scans on at least four endpoint
   trims. Require frequency spread below `0.05`, phase resultant above `0.80`,
   and control-adjusted family-wise p-value below `0.05` before any zeta work.
3. Use a leakage baseline made from synthetic tones and the exact sampling
   operator. Subtract or report the operator's transfer function so a shared
   response caused by interpolation is not counted as arithmetic evidence.
4. Treat cumulative and derivative observables as correlated tests. Effective
   test counts should be estimated from surrogate covariance, with a
   multiplicity correction across scales, grids, trims, frequencies, and
   channels.

None of these diagnostics establishes an off-line zero. Actual zeta numerical
   candidates still require independent high-precision evaluation and an
   Arb/FLINT rectangular argument-principle certificate.
