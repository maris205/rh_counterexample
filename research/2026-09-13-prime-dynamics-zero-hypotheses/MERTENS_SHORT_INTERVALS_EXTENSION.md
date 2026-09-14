# Extending the prime-dynamics method: Mertens and short intervals

## Why Mertens is the right second channel

The Möbius summatory function

`M(x) = sum_{n <= x} mu(n)`

is directly tied to the reciprocal Dirichlet series

`1/zeta(s) = sum mu(n)n^{-s}`

in its half-plane of convergence. The zero locations are therefore shared with
zeta, while the amplitudes and cancellations are different from those in
`psi(x)-x`. This makes `mu(n)` a useful independent channel for a common
spectral atom, not a second proof of RH.

The Mertens inequality `|M(x)| < sqrt(x)` was disproved by Odlyzko and te
Riele. Their argument established the existence of violations without giving
an explicit first counterexample. This is exactly the kind of finite-sample
trap that belongs in the Discussion section: a long clean numerical record can
coexist with a theorem-level failure far outside the computed range.

## Dynamical observables

For each arithmetic channel `a(n)`, form the log-time signal

`A_a(u) = exp(-u/2) sum_{n <= exp(u)} a(n)`.

Use the following channels in parallel:

* `a_mu(n) = mu(n)`;
* `a_Lambda(n) = Lambda(n) - 1`;
* `a_prime(n) = 1_{n prime} - 1/log(n)`;
* `a_short(n; h) = psi(n+h) - psi(n) - h` for several `h=n^theta`.

Extract block means, lag correlations, sign words, recurrence statistics, and
windowed Fourier/Prony atoms from the same log-time grid. A candidate atom is
`(sigma,t)` if the fitted envelope is compatible with

`exp((sigma-1/2)u) cos(tu + phi)`

in at least two channels and remains present on held-out scales.

## Mertens-specific controls

Use three controls so that a result is not just a generic sparse-sequence
artifact:

1. block-shuffle `mu(n)` while preserving the exact counts of `-1,0,+1`;
2. prime-preserving shuffle, which keeps squarefree positions but randomizes
   signs;
3. a synthetic critical-line signal with known ordinates, passed through the
   same cumulative and normalization pipeline.

The synthetic control is mandatory. It calibrates leakage, finite-window
frequency bias, and false off-line envelope slopes before any interpretation of
the real `M(x)` data.

## Short-interval extension

Represent the prime sequence by gap words `g_n=p_{n+1}-p_n` and by interval
residuals

`R_theta(x) = psi(x+x^theta) - psi(x) - x^theta`.

Scan `theta` in the three regimes `0.50`, `0.525`, and `0.60`, with a separate
control for each scale. The exponent `0.525` is close to the best general
unconditional short-interval result; the square-root endpoint remains a hard
boundary, so an empty square-root interval must not be presented as a known
theorem.

For each block, encode signs of `R_theta`, unusually long gaps, and the local
ratio `g_n/log(p_n)`. Compare original blocks with gap-preserving and block-
shuffled controls. The output is a dynamical anomaly score and a spectral
candidate list, not a claim about a zero.

## Common-spectrum test

The strongest version of the extension is a joint fit:

`Y_c(u) = sum_j A_{c,j} exp((sigma_j-1/2)u)
          cos(t_j u + phi_{c,j}) + noise_c(u)`

where `c` ranges over Mertens, Chebyshev, prime-counting, and short-interval
channels. The frequencies `t_j` and exponents `sigma_j` are shared; amplitudes
and phases are channel-specific. A symbol-sequence anomaly is promoted only if
the shared atom beats all controls and remains stable under a held-out range of
`u`.

## Failure modes to report

* A Mertens excursion alone is not an off-line zeta zero.
* A common frequency in two cumulative sequences can be an integer-block or
  smoothing artifact.
* `x/log(x)` versus `li(x)` contains a large smooth baseline difference; it is
  not two independent zero observations.
* At `t` near `10^14`, the period in `u=log(x)` is about `6e-14`, so an ordinary
  prime-counting grid is severely under-sampled. Low-height calibration or
  local demodulation is required.
* A zero-free Arb box only rules out a zero in that box; an off-line rectangle
  count is required for a zero-count statement.

## Execution order

1. Implement the Mertens channel and synthetic critical-line calibration.
2. Measure common-spectrum recovery at low heights where the ground truth is
   known.
3. Add the short-interval/gap-word channel at `theta=0.50, 0.525, 0.60`.
4. Build candidate `(sigma,t)` intersections from original versus controls.
5. Send only surviving representatives to direct Arb zeta search and contour
   certification.
