# Prime-dynamics clues to possible off-line zeta zeros

## Scope

This is a falsifiable hypothesis sheet, not a claim that an off-line zero has
been found. Every candidate must eventually be checked on the actual Riemann
zeta function and, if it survives, certified by an off-line rectangle count.

## What the completed pilot says

The eight-seed basin census at `10^14 <= t <= 10^14+128` found numerical
off-line minima, but all eight free-sigma Newton refinements converged to the
critical line. Thus the current landscape is consistent with attraction basins
of ordinary critical-line zeros. The original k3/k5 symbol windows also did
not show a stable advantage over shuffled controls in the completed high-height
survey. This is negative evidence against the present window score, not against
the broader prime-dynamics idea.

## Symmetry and a count hypothesis

If `rho = sigma + i t` is a non-trivial zero with `sigma != 1/2`, the
functional equation and conjugation generate the orbit

`{sigma+it, sigma-it, 1-sigma+it, 1-sigma-it}`.

Therefore the search should count representatives with `sigma > 1/2` and
`t > 0`, then report one orbit as four zeros counting symmetry. We use three
explicit hypotheses:

* H0: no off-line orbit in the tested rectangle.
* H1: one isolated off-line orbit, with a four-zero symmetry orbit.
* H2: two related orbits, one associated with the k3 mode family and one with
  k5; this would mean eight zeros counting symmetry.

H2 is a deliberately aggressive upper prior, not an inference from the
current data. A repeated zero or a cluster would need separate multiplicity
evidence.

## Where to look

The old search window `0.55 <= sigma <= 0.65` was a heuristic prior. The broad
basin census did not validate it, so the next scan should stratify the strip:

1. `0.5001 <= sigma < 0.55` (near-line control);
2. `0.55 <= sigma <= 0.65` (old symbolic prior);
3. `0.65 < sigma <= 0.9` (far-line stress test).

Do not use the joking values `3` or `5` as zeta real parts: non-trivial zeros
are in the critical strip. If those values are useful, treat them as labels for
the k3/k5 symbol models or as transformed parameters.

## Generating height candidates from the symbol sequence

For a support pair `(a,b)`, generate phase candidates from

`t = 2*pi*k / |log(a/b)|`.

For the three-event curvature rule, use

`t = 2*pi*k / |log(a_j*a_{j+2}/a_{j+1}^2)|`.

Keep only heights where several independent ratios agree within a prescribed
phase tolerance, and record the harmonic index `k`; do not optimize `t` first
and then retroactively select a symbolic explanation. Intersect the k3 and k5
candidate lists, then compare against independently shuffled sign controls.

## Prime-counting cross-check

The two common smooth approximations `x/log(x)` and `li(x)` should be treated
as baseline models, not as two independent zero detectors. Their difference is
mostly a deterministic asymptotic correction. Use smoothed residuals of

`psi(x)-x`, `theta(x)-x`, and `pi(x)-li(x)` after fitting the smooth baseline.

For a hypothetical zero `rho=sigma+i*t`, fit across `u=log(x)`:

`Y(u) = A*exp((sigma-1/2)*u)*cos(t*u + phi)`

and compare the fitted `(sigma,t)` across all three observables, smoothing
kernels, and held-out x-scales. Original symbol sequences must beat shuffled
controls on both fit and held-out coherence before they are allowed to guide a
new zeta search.

At heights near `10^14`, the phase period in `u` is approximately `2*pi/t`,
about `6e-14`. Ordinary prime-counting grids cannot resolve that directly.
Therefore use low-height calibration first, or a locally demodulated statistic;
never treat an under-sampled high-t fit as evidence for a zero.

## Next numerical run

1. Build the k3/k5 ratio-candidate tables with harmonic indices and exact
   decimal phase residuals.
2. Run the three sigma strata with identical budgets for original and shuffled
   sequences; keep candidate generation blind to zeta scores.
3. Deduplicate candidates by the symmetry representative `(sigma,t)` and by
   Newton convergence height.
4. Apply independent Arb/mpmath checks, then a small zero-free box.
5. Only a candidate that remains off-line after free-sigma Newton proceeds to
   rectangle counting. A local zero-free box is not a whole-window result.

## Decision table

* all candidates return to `sigma=1/2`: reject the current symbolic-to-zeta
  mechanism, retain the periodic Dirichlet interpretation only;
* original beats shuffled but no stable `(sigma,t)` survives: treat as a
  symbol-model resonance, not a zeta signal;
* one stable off-line representative survives independent checks: test H1;
* two independent representatives survive and are tied to k3/k5 with held-out
  explicit-formula coherence: test H2, then certify each orbit separately.
