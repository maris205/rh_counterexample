# Prime dynamics, Mertens, and zeta-family zero search

## Research objective

We are testing whether anomalies in prime-derived symbolic dynamics can provide
useful, reproducible search directions for zeros of the actual Riemann zeta
function. A model anomaly is only a candidate generator. A Riemann-Hypothesis
counterexample requires a zero of the actual `zeta(s)` away from
`Re(s)=1/2`, independently evaluated and certified by an off-line contour
count.

## What has already been established

* The k3/k5 symbol models are finite-periodic, zero-mean sequences with exact
  finite Hurwitz-zeta representations. They have no automatic Euler product,
  so their zero patterns are model diagnostics rather than Riemann-zeta zeros.
* The original high-height symbol-window survey and shuffled controls did not
  show a stable original-sequence advantage.
* A direct basin census near `t=10^14` produced eight off-line numerical
  minima. All eight free-sigma Newton refinements returned to the critical
  line. None is an off-line zero candidate.
* Independent Arb/mpmath evaluations agree at high precision for the leading
  minima. The remaining issue was therefore mechanism discrimination, not
  simply spending more DE iterations in the same rectangle.

## Unified hypotheses

### H0: optimizer basin artifact

An off-line minimum of `|zeta(s)|` is frequently an attraction basin of an
ordinary critical-line zero. Free-sigma Newton convergence to `1/2` is the
diagnostic.

### H1: shared arithmetic spectral atom

A genuine arithmetic mode may appear in more than one channel as

`exp((sigma-1/2)u) cos(t*u + phase)`, `u=log(x)`.

The pair `(sigma,t)` must be shared across channels and survive shuffled
controls and held-out scales.

### H2: one or two off-line symmetry orbits

If `rho=sigma+i*t` is off the line, symmetry produces the four-point orbit
`{rho, conjugate(rho), 1-rho, 1-conjugate(rho)}`. Our operational priors are
one orbit first, two orbits second; the latter is a k3/k5 stress hypothesis,
not a conclusion.

## Unified channels

1. `mu(n)` and `M(x)=sum_{n<=x} mu(n)` (Mertens channel; reciprocal-zeta
   spectrum).
2. `Lambda(n)-1` and `psi(x)-x` (explicit-formula channel).
3. Prime indicator minus `1/log(x)` (local prime-count channel).
4. Short-interval residuals
   `psi(x+x^theta)-psi(x)-x^theta`, with `theta=0.50,0.525,0.60`.
5. Prime-gap words and the original k3/k5 symbol dynamics.

Every channel receives the same log-time features: block signs, lag
correlations, recurrence statistics, spectral atoms, envelope fits, and
held-out coherence.

## Family-level controls

The benchmark compares structural classes rather than assuming all zeta-like
functions behave alike:

* Riemann zeta: target object, RH unresolved;
* k3/k5 periodic Hurwitz combinations: symmetry-rich negative controls;
* Davenport--Heilbronn/Epstein-type examples: functional-equation controls
  with known off-line behavior;
* Dirichlet and automorphic `L`-functions: Euler-product positive controls
  with conjectural generalized RH;
* function-field zeta toy models: positive controls with a proven analogue;
* Beurling generalized-prime systems: tunable stress controls.

The purpose is to identify which features require Euler products, coefficient
multiplicativity, positivity, or a self-adjoint spectral mechanism.

The first minimal panel will use explicit fixtures: primitive characters
`chi_4` modulo 4 and real quadratic `chi_5` modulo 5 as intermediate
Euler-product controls; the elliptic curve `E/F_7: y^2=x^3+x`, whose zeta
numerator is `1+7u^2`, as an exact finite-field critical-line calibration; and
the standard period-5 Davenport--Heilbronn combination as a symmetry-only
negative control. The reported off-line fixture for the latter must be checked
by high-precision residuals and an argument-principle count before use.

## Current selected experiment: Mertens calibration

The first implementation is deliberately modest and reproducible:

1. Linear-sieve `mu(n)` up to a chosen `N`.
2. Uniform resampling in `u=log(x)` of `M(x)/sqrt(x)`.
3. Global and block-preserving shuffles with the same value counts.
4. A synthetic off-line envelope with known `(sigma,t)` for calibration.
5. Train/hold-out tone coherence, not just the largest FFT peak.

The real arithmetic signal is promoted only if its frequency and envelope are
stable in held-out `u`, stronger than both controls, and reproducible under
multiple `N` and block scales.

Initial calibration status: at `N=10^7`, the first known critical-line
ordinate `t=14.134725...` has Mertens cumulative held-out projection `R^2`
about `0.524`; at `N=5*10^7` it is about `0.539`, while the unconstrained
training peak moves from roughly `13.99` to `14.32`. Those cumulative values
are not independent evidence: small block shuffles reproduce them because
they preserve cumulative block sums. They remain useful as a warning about
finite-window leakage, not as a new-zero result.

The first control revision exposed a second leakage mode: very small block
shuffles preserve cumulative block sums and therefore preserve much of `M(x)`.
They are useful local-structure controls but are not independent nulls. With
large blocks and the log-scale increment signal, the first-zero projection at
`N=5*10^7` was roughly `R^2=0.033`, versus about `0.0083` for 1-million
blocks and `0.0038` for 5-million blocks. This is still only a known-line
calibration effect; it must be repeated across seeds and held-out cut points
before being called a robust arithmetic signal. The latest eight-replicate
run (`runs/mertens-null-5e7-v2.json`) gives, for the log-scale increment
signal, real `R^2=0.03298` and amplitude `2.464`, versus mean `R^2=0.00812`
and amplitude `1.220` for 1-million blocks, and mean `R^2=0.00430` and
amplitude `0.833` for 5-million blocks. This is a sensible known-line
calibration separation at the default two-thirds cut, but it is still not an
unknown-frequency or off-line zero claim. A first multi-cut check at
`N=10^7` gives real increment `R^2` about `0.055` at all three cuts
(`0.55,0.67,0.80`), while the `100000`-block control rises to about `0.050`
at the last cut. Thus even a large-block control can leak at some cut points;
the separation is not yet a significance result. The next gate is to report
cut-point stability explicitly, then add the independent `Lambda/psi` channel.

The first independent `Lambda/psi` smoke at `N=10^7`
(`runs/lambda-psi-1e7.json`) gives another control-design warning. For the
known first critical-line ordinate, the `psi` and `theta` log-increment
projections are roughly `R^2=0.0068--0.0075` across cuts `0.55,0.67,0.80`;
the corresponding block controls are usually smaller, but the `10^6`-block
`theta` control at the last cut is already about `0.0065`. This is a
cross-channel calibration, not evidence for a new zero. Any blind search must
require joint frequency and phase stability across `M`, `psi`, and `theta`,
with controls evaluated at every cut.

The short-interval run at the same scale (`runs/short-interval-5e7.json`)
adds a useful negative result. The `h=x^{1/2}` channel has tiny known-line
increment projections (`R^2` below `0.002`), while the fixed-log-width channel
has `R^2` around `0.002--0.007` and its large-block controls are essentially
the same. The gap-residual channel shows a larger raw projection, but its
shuffle control destroys the ordering information, so that comparison is not
an independent null for gap dynamics. Short-interval features therefore do
not currently provide a new shared spectral atom; they are retained as
stress tests for the control design.

A direct top-spectrum comparison reinforces that caution. At `N=5*10^7`, the
Mertens, `psi`, and `theta` spectra all place their largest bins at
approximately `t=14.016`, `14.385`, `21.025`, and `25.08`; these are the same
log-grid bins around known ordinates, not independently fitted off-line
frequencies. The short fixed-log window is dominated by low bins near
`t=0.407`, while the `h=x^{1/2}` channel has unrelated high-bin peaks. Shared
bins across cumulative error observables therefore cannot be counted as an
independent arithmetic discovery until a common-window and leakage analysis
removes the grid/trend mechanism.

An independent-grid demodulation check is recorded in `MULTI_GRID_DEMOD.md`
and `runs/multi-grid-demod-1e7-v2.json`. It replaces fixed FFT-bin lookup by
a continuous-frequency least-squares scan of the log derivatives, using four
sample counts and endpoint trims from 0% through 10%. After excluding the five
known critical-line ordinates, the only apparent cross-grid/cross-channel
cluster is a weak high-frequency residual around `t=37.5`; it wanders over
`37.25--37.60`, with maximum `R^2=0.0225` and most independent windows below
`0.015`. It fails the stability gate and is not sent to zeta refinement.

At `N=5*10^7` with eight replicates (`runs/lambda-psi-5e7.json`), the first
known-line `psi` and `theta` increment projections are stable near
`R^2=0.0032--0.0037` at cuts `0.55,0.67,0.80`. The corresponding block-control
means range from about `0.0008` to `0.0029` for `psi` and `0.0013` to
`0.0024` for `theta`, with individual replicates reaching or exceeding the
real value at some cuts. This is a reproducible calibration scale, but the
replicate overlap means it is not a significance result and says nothing by
itself about an off-line zero.

The short-interval/prime-gap channel is implemented in
`short_interval_dynamics.py` (see `SHORT_INTERVAL_CHANNEL.md`). It measures
standardized prime counts in power windows `h=x^theta` and fixed-log windows,
plus the local gap residual `(p_{i+1}-p_i)log(p_i)-1`. The same increment,
multi-cut, known-line calibration, and global/large-block controls are emitted
in the common JSON schema. This channel is intentionally a lightweight
feature extractor: the `h/log(x)` baseline and the gap normalization are
heuristics, so a peak must survive controls and independent zeta evaluation.

## Candidate generation and zeta certification

For k3/k5 support ratios, generate phase candidates from

`t = 2*pi*k/abs(log(a/b))`

and the three-event curvature ratio

`t = 2*pi*k/abs(log(a[j]*a[j+2]/a[j+1]^2))`.

Only intersections of independent ratios and channels become zeta search
windows. Search sigma strata separately (`0.5001--0.55`, `0.55--0.65`,
`0.65--0.90`) with original and shuffled controls under identical budgets.

The mandatory gates are:

1. independent Arb/mpmath point agreement;
2. free-sigma Newton does not return to `1/2`;
3. a local Arb box does not incorrectly contain an inconclusive value;
4. an off-line rectangle count certifies the zero orbit representative.

No local minimum, finite-window fit, or zero-free box is a whole-window
statement.

## Interpretation rules

* A Mertens excursion is not by itself a zeta zero.
* `pi(x)-li(x)` and `pi(x)-x/log(x)` are baseline residual choices, not
  independent zero detectors.
* At `t~10^14`, the phase period in `log(x)` is about `6e-14`; ordinary
  prime-count grids are under-sampled, so use low-height calibration or local
  demodulation.
* A shared frequency without held-out stability is a finite-window resonance.
* Only `off_line_certified=True` is eligible for an RH-counterexample claim.

## Deliverables

* Mertens calibration JSON at multiple `N` and block scales;
* a common-spectrum channel schema for `mu`, `Lambda`, and short intervals;
* a family-level control panel and diagnostic report;
* candidate windows with provenance and symmetry deduplication;
* strict zeta rectangle-count reports for any surviving representative.

The current joint diagnostic is recorded in
`CROSS_CHANNEL_SUMMARY.md` and `runs/cross-channel-summary.json`. It sets the
next blind-search gate at three independent channels, the 95th percentile of
their control distributions, all three cut points, two `N` scales, and phase
circular resultant at least `0.80`, followed by free-`sigma` zeta refinement
and rectangle certification. No current frequency passes that unknown-
frequency gate.

The independent-grid demodulation check (`MULTI_GRID_DEMOD.md`) used four
trimmed log grids and continuous frequency scans on `N=10^7` Mertens,
`psi`, and `theta` data. After removing known ordinates, the only apparent
three-channel cluster was near `t=37.5`; it wandered from `37.25` to `37.60`
under endpoint trims, with `R^2` falling from `0.0225` to roughly
`0.005--0.015`. It therefore fails the stability gate and was not sent to
zeta refinement. This is the first direct check that the shared FFT buckets
were discretization/window artifacts rather than stable unknown frequencies.

A focused global-shuffle quantile check for the rejected `t~37.5` residual
(`MULTI_GRID_CONTROL.md`) gives real maximum `R^2=0.00504` versus empirical
control 95th percentile `0.01077` at `N=10^6`; it therefore fails before any
zeta evaluation. This focused result is a null-design diagnostic, not a
theorem about all cumulative arithmetic signals.

The stratified control follow-up (`STRATIFIED_CONTROLS.md`) preserves local
block structure instead of globally randomizing everything. At `N=10^6`, the
real `t~37.5` maximum is `R^2=0.00504`; 8-replicate 95% control quantiles are
`0.01024` for block permutation and `0.01058` for within-block permutation.
The weak residual fails both controls, including the more conservative local
shape-preserving null.

Repeating the stratified control at `N=10^7` with 200,000-point blocks gives
real `R^2=0.00313` against block-permutation q95 `0.01689` and within-block
q95 `0.01214` (`runs/stratified-controls-1e7.json`). The same residual is
therefore rejected at both tested arithmetic scales.

The expanded demodulation control (`STRATIFIED_SHUFFLE_CONTROL.md`) also
includes global shuffle, block permutation, and within-block shuffle, with
the incomplete tail block handled without padding. At `N=10^7`, the Mertens
score near `t=37.5` slightly exceeds one block-control q95 at one endpoint,
but the excess is absent synchronously in `psi` and `theta` and drifts under
endpoint trims. The blind-top control ranges cover the residual, so no new
frequency enters zeta verification.

The density-preserving short-interval null (`DENSITY_PRESERVING_SHORT_CONTROLS.md`)
keeps prime counts in logarithmic bins while resampling positions. At
`N=10^6`, the pre-registered `t=37.5` consensus minimum is
`2.32e-6`, below surrogate q95 `2.67e-5`; the geometric consensus is
`2.23e-4`, below q95 `5.05e-4`. A window-max statistic slightly exceeds its
q95, but that is a post-selection effect and is not promoted to a candidate.

At `N=10^7` with 128 logarithmic bins, the target consensus is `3.97e-6`
versus surrogate q95 `7.87e-6`, and the scanned-window consensus is
`1.99e-5` versus q95 `2.85e-5`. Bin-count sensitivity checks with 32 and 256
bins also remain below their q95 values. The density-preserving null therefore
rejects the residual at multiple local-density resolutions.

At `N=5*10^7` with 256 bins and four surrogate repetitions, the same
pre-registered `t=37.5` consensus is `2.84e-6` versus q95 `4.20e-6`. The
three-channel target values are `4.87e-4`, `2.84e-6`, and `8.70e-5`; the
fixed-log channel remains the limiting statistic. A scanned-window maximum
slightly exceeds its small-sample q95, but that is post-selection and does not
override the pre-registered target gate.

Repeating the blind gate with both `N=10^7` and `N=5*10^7` inputs also gives
zero candidates (`runs/blind-candidates-multiN.json`), and the companion zeta
report schedules no evaluations. The result is therefore stable across the
two available arithmetic scales, while remaining only a finite candidate
screen.

The shared FFT bins were also sent through free-`sigma` Newton refinement on
the actual zeta function. All 16 seeds converged back to known critical-line
zeros; see `SHARED_BIN_ZETA_REFINEMENT.md` and
`runs/shared-bin-zeta-refine.json`. This closes the current calibration loop:
the shared bins reproduce known line zeros when forced into zeta, but produce
no off-line candidate.

The family-level panel is now also available in
`family_control_panel.py` with its report in `FAMILY_CONTROL_PANEL.md` and
fixture output `runs/family-control-smoke.json`. The `chi_4` and `chi_5`
periodic coefficient controls have zero multiplicativity defects, while the
finite-field curve `E/F_7: y^2=x^3+x` maps exactly to the critical line via
`P(u)=1+7u^2`. Davenport--Heilbronn remains deliberately disabled until its
non-scalar functional equation and an off-line zero can be independently
certified.

The detector-transfer experiment is also complete
(`family_detector_transfer.py`). On `N=200000` periodic coefficient controls,
the known Davenport--Heilbronn height `t=85.6993...` does not appear as a
stable positive peak in the weighted partial-sum log derivative
(`R^2` is strongly negative under the held-out projection convention). This
is a useful negative sensitivity result: a function may have an off-line zero
without its raw coefficient partial sums exposing that frequency. Therefore
the blind search below is restricted to cross-channel prime observables and
never treats generic periodic-family spectra as zeta evidence.

The transfer test in `FAMILY_ZERO_SURFACE.md` applies a free-`sigma` surface
scan to the corrected family fixtures. In the common height window
`83 <= t <= 88`, the Davenport--Heilbronn grid minimum refines to
`0.808517182456637... + 85.699348485377592... i`, while zeta, `chi_4`, and
`chi_5` refine to line-confined roots. This demonstrates detector sensitivity
to a known off-line family root, without weakening the certification gate for
the actual Riemann zeta function.

A corrected Davenport--Heilbronn audit is now available in
`DAVENPORT_HEILBRONN_AUDIT.md` and `runs/davenport-heilbronn-audit.json`.
Using the standard
`kappa=(sqrt(10-2*sqrt(5))-2)/(sqrt(5)-1)`, the rounded reported point has
residual about `6.1e-11`, and high-precision refinement reaches
`0.808517182456637... + 85.699348485377592... i` with residual below
`2.4e-80`. This validates the numerical family fixture, while the
argument-principle certificate remains disabled until its non-scalar
functional equation is implemented and the contour is enclosed rigorously.

The first unknown-frequency blind pass is now implemented in
`blind_candidate_generator.py`. After removing known-line neighborhoods and
low-frequency trend bins, it found 11 residual FFT clusters but zero clusters
with at least three independent observable channels
(`runs/blind-candidates-5e7.json`). The zeta verifier consequently scheduled
zero evaluations (`runs/blind-zeta-verification-5e7.json`). This is a finite
candidate-gate result, not a zero-free statement; the next expansion should
use independent log grids and direct demodulation.

A separate numerical winding check around a `0.01 x 0.01` box gives winding
number `1` with 256 samples per side (`runs/davenport-heilbronn-winding.json`).
It is a useful discretized sanity check, but it remains explicitly
non-rigorous until interval bounds control the entire contour.

The density-preserving short-interval control was repeated at `N=10^7` with
32, 128, and 256 logarithmic bins. The pre-registered target statistic at
`t=37.5` is `3.97e-6`; surrogate q95 values are respectively `4.88e-6`,
`7.87e-6`, and `7.63e-6`. The real statistic remains below all three
empirical thresholds. The `37 <= t <= 38` window-consensus score is likewise
below its 128-bin q95 (`1.99e-5` versus `2.85e-5`). These surrogates preserve
coarse prime density but are still empirical controls, not a theorem-level
null model.

At `N=5*10^7` (256 bins, four replicates), the pre-registered target
consensus is `2.84e-6` versus surrogate q95 `4.20e-6`. A scanned `37--38`
window maximum is marginally above its small-replicate q95; this is treated as
post-selection and does not override the target/cross-channel gate.

The next blind handoff is now frozen in `PREREGISTERED_BLIND_MANIFEST.json`
and replayed by `preregistered_blind_runner.py`. It fixes
`4 <= t <= 40`, removes the first five known ordinates by radius `0.75`,
requires three channels, three independent log grids, both `N=10^6` and
`N=10^7`, and phase resultant at least `0.80`. The control threshold is the
conservative maximum q95 already measured (`0.016892465431210348`), and the
manifest hash is recorded in `runs/preregistered-blind-20260913.json`.

The replay finds one residual cluster near `t=37.5056`. Its channel and
grid-wise `R^2` values clear the conservative control threshold, but its
phase resultant is only `0.21484`, so it fails the pre-registered coherence
gate. The final candidate count is therefore zero. This is a finite,
pre-registered screening result: the residual is currently classified as a
phase-unstable finite-window feature and is not sent to a zeta root solver.

The next family-level calibration is now reproducible with Python 3.10 in
`family_hierarchy_py3.py`, using the already computed high-precision surface
artifacts. In the common height window, free-`sigma` refinement gives
`Re(s)=1/2` for zeta, chi_4, and chi_5, while it recovers the known
Davenport--Heilbronn fixture at `sigma=0.808517182456637...`. The DH residual
is therefore a sensitivity control, not a transfer to zeta; its contour gate
is still disabled. See `FAMILY_HIERARCHY_PY3.md`,
`runs/family-hierarchy-py3.json`, and the independently replayed
`runs/family-hierarchy-audit-py3.json`.

The first Python 3.10 contour sanity checks for the DH fixture now give
winding number `1` at 32, 64, and 128 samples per edge (`runs/dh-winding-
py310-32.json`, `runs/dh-winding-py310-64.json`, and
`runs/dh-winding-py310-128.json`). The minimum boundary modulus and the
discretization details are recorded in each file. This is a stable numerical
sanity check, not an interval-rigorous certification; the next audit should
bound the contour evaluation error before upgrading the claim.

The first interval-capability audit is recorded in
`dh_interval_capability_py3.py` and `runs/dh-interval-capability-py3.json`.
With Python 3.10 and mpmath `1.4.1`, calling `mp.iv.zeta` on a complex interval
currently raises an `ivmpc` internal type error. Therefore the project does
not silently treat mpmath interval output as a proof. The rigorous next route
is an Arb/python-flint evaluator or a hand-bounded Euler--Maclaurin contour
implementation; until then the winding results remain discretized checks.

`python-flint 0.9.0` is now installed and can evaluate Riemann `zeta` on a
small complex box, but its Python `acb` API exposes no Hurwitz-zeta evaluator.
The capability probe is in `dh_arb_capability_py3.py` with output
`runs/dh-arb-capability-py3.json`; it therefore leaves the DH interval gate
disabled and identifies the next concrete implementation target: an Arb-backed
Hurwitz Euler--Maclaurin evaluator.

As a preparatory validation, `hurwitz_em_validation_py3.py` now evaluates the
finite Euler--Maclaurin formula against mpmath's point Hurwitz-zeta routine at
the DH seed. With `N=100, M=16`, the five component errors are about
`3.5e-31`--`4.6e-31` and the combined DH error is `6.7e-32`
(`runs/hurwitz-em-validation-py3-n100-m16.json`). This validates the algebraic
expansion at point precision; it does not yet enclose the remainder on a
complex box and therefore does not change the certification status.

The first boundary subdivision using the Arb-backed prototype is now complete
(`dh_contour_subdivision_py3.py`). For the `0.01 x 0.01` DH box, both 16 and
64 subdivisions per edge had zero boundary boxes whose enclosure contained
zero, and the midpoint phase traversal gave winding `1`
(`runs/dh-contour-subdivision-py3-e16.json` and
`runs/dh-contour-subdivision-py3-e64.json`). This is a stronger numerical
sanity check than the earlier point-sampled winding, but it remains
`NONCERTIFIED_SUBDIVISION`: interval argument accumulation and a fully
independent remainder proof are still required before calling it a rigorous
zero count.

A resumable long-run sweep is now running in the background via
`dh_long_batch_py3.py`. It covers 52 rectangle, edge-density, and
Euler--Maclaurin parameter combinations, writes one JSON per task under
`runs/dh-long-batch-py3-full/`, records progress after every task, and skips
completed files on restart. The first completed jobs at 16, 32, 64, and 128
edge boxes all report zero boundary boxes containing zero and sampled winding
`1`; this is an early progress snapshot, not the final batch conclusion.

The 52-job batch has now completed. Every task completed without a process
error; all 52 report zero boundary sub-boxes containing zero and midpoint
winding `1`. This strengthens the numerical stability evidence across the
tested rectangle sizes and `(N,M)` choices, but the batch remains explicitly
non-certified because it does not accumulate interval arguments and the
Euler--Maclaurin contour proof is still a prototype.

The next dependency-reduction diagnostic is now implemented in
`dh_taylor_lipschitz_py3.py`. For the `0.01 x 0.01` box with 16 segments per
edge, all 64 segments have positive centre-value plus sampled-derivative
Taylor lower bounds; the minimum is `0.011574478671040427`, while direct Arb
complex-box lower bounds all widen to zero. The midpoint winding remains `1`.
This demonstrates why a Taylor model is the right next representation, but
the derivative maximum is sampled with a heuristic safety factor, so the
result remains `NONCERTIFIED_TAYLOR_LIPSCHITZ_DIAGNOSTIC`.

An analytic derivative prototype now replaces the sampled finite difference:
`dh_interval_derivative_py3.py` differentiates each Euler--Maclaurin term with
Arb/FLINT and uses a differentiated scalar remainder majorant. On the same
box and 16 segments, all 64 Taylor lower bounds remain positive, with minimum
`0.011739566087598489` and maximum derivative upper bound
`1.3207268355063309` (`runs/dh-interval-derivative-py310-e16.json`). The
remainder majorant is not yet an independently proved complex interval bound,
and phase accumulation is absent, so the status remains
`NONCERTIFIED_INTERVAL_DERIVATIVE_DIAGNOSTIC`.

The first phase-interval accumulation is now implemented in
`dh_phase_interval_py3.py`. Converting each Taylor disk to an angular interval
gives nominal winding `1` and all disks exclude zero. At 16 and 32 segments
per edge the resulting winding intervals are respectively
`[-0.16961, 2.16961]` and `[-0.14554, 2.14554]`; both contain 1 but are too wide
to certify uniqueness. Adaptive subdivision and second-order Taylor bounds are
the next numerical improvements, followed by independent proof of the
remainder majorants.

Uniform phase refinement through 128 segments per edge has now been tested.
The winding remains nominally `1`, every Taylor disk excludes zero, but the
intervals only narrow from `[-0.16961,2.16961]` at 16 segments to
`[-0.12797,2.12797]` at 128 segments. This slow convergence shows that a
first-order local angle bound will not isolate the integer efficiently. The
next implementation should use a second-order Taylor remainder or a global
tangent-variation bound instead of merely doubling the mesh.

A sampled second-order Taylor diagnostic is now available in
`dh_second_order_taylor_py3.py`. On the 64-segment boundary it keeps all
lower bounds positive, with minimum `0.011769738069959792`, and narrows the
phase interval to `[-0.12327793,2.12327793]`. This is an improvement over the
first-order interval, but the first and second derivative maxima are sampled;
the strict implementation still needs Arb derivative boxes and a validated
remainder derivative bound.

The shared-endpoint phase audit is now implemented in
`dh_shared_endpoint_phase_py3.py`. With 64 segments per edge it uses 256
unique endpoints, obtains nominal winding `1.0000000000000007`, and finds a
maximum phase step of `0.0313061` radians with a minimum branch margin of
`3.1102865` radians. No step is near the `+/-pi` ambiguity. This removes a
large source of repeated error counting; the remaining proof obligation is to
enclose each endpoint/path segment away from zero with validated Arb/Taylor
bounds.

The second-order sweep now includes 16, 32, and 64 segments per edge. All
segments remain positive; the winding intervals are approximately
`[-0.12328,2.12328]`, `[-0.12252,2.12252]`, and `[-0.12231,2.12231]`.
The marginal gain is already saturating, so further uniform mesh refinement is
deprioritized in favor of certified Arb derivative boxes and a third-order
Taylor remainder.

The path and branch checks are now combined by
`dh_combined_contour_audit_py3.py`. On the 64-segment-per-edge rectangle, all
256 path segments have positive Taylor lower bounds, the shared endpoint
branch margin is `3.11028654401` radians, and the nominal winding is
`1.0000000000000007`. The combined diagnostic passes its consistency checks,
but remains non-certified until the derivative/remainder bounds and in-segment
phase continuity are independently enclosed.

The scalar Hurwitz remainder majorant has now passed a point-precision stress
test (`hurwitz_remainder_stress_py3.py`): 700 comparisons across seven complex
points, four truncation lengths, five correction orders, and all five rational
shifts produced zero violations. The maximum observed error-to-majorant ratio
was `0.0826058472`. This validates the scale of the point bound, but not its
complex interval or differentiated remainder theorem; the contour status is
unchanged.

A third-order centre Taylor check has also run on the 64 boundary segments.
All lower bounds remain positive (`min=0.011769737816714674`), but the phase
interval is `[-0.12327832,2.12327832]`, essentially unchanged from second
order. This confirms that higher local Taylor order is no longer the main
bottleneck; the next implementation must certify derivative suprema and
correlated phase/path enclosures with Arb.

A local isolation run at half-width `0.001` is also complete. With 64 path segments, all Taylor lower bounds are positive (`min=0.0011791395987688189`), the shared endpoint nominal winding is `1.0000000000000002`, and the branch margin is `3.01720906799` radians. The combined diagnostic passes, but remains non-certified.

A local isolation scale comparison is now recorded in
`DH_LOCAL_ISOLATION_SCALE_PY3.md`: both half-width `0.01` and `0.001` boxes
pass the combined nonzero-path and shared-branch diagnostics with nominal
winding 1. Shrinking the box alone does not narrow the independent phase
interval enough, so the next strict work remains certified Arb derivative,
remainder, and correlated path phase bounds.

## 2026-09-13: v2 long batch running

The resumable Python 3 batch driver `dh_long_batch_py3_v2.py` has been started
in the background with the `long` profile (108 planned jobs, per-job timeout
3600 s). It writes atomic `progress.json`, per-job JSON records, and a final
`summary.json` under `runs/dh-long-batch-py3-v2/`. The first seven completed
jobs, covering edge resolutions 16 through 1024 for the initial box, all report
`COMPLETED_NONCERTIFIED`, zero boundary boxes containing zero, and sampled
winding 1. This is a robustness sweep only; it does not certify a zero or RH
counterexample. A heartbeat monitor `rh-v2` is active and is configured to stay
quiet unless the process completes, fails, times out, or produces anomalous
logs.

The next long stability audit has been launched with the Python 3.10
resumable driver `dh_long_batch_py3_v2.py` using the `long` profile and a
per-child timeout of 3600 seconds. The plan contains 108 independent
rectangle, edge-density, and Euler--Maclaurin configurations; its immutable
manifest and SHA-256 hash are stored under
`runs/dh-long-batch-py3-v2/`. The first six completed configurations (the
`0.02 x 0.02` rectangle with 16 through 512 edge subdivisions, `N=128`,
`M=12`) all report zero boundary boxes containing zero and sampled midpoint
winding 1, with child status `COMPLETED_NONCERTIFIED`. The batch is still
running and remains an implementation-stability audit rather than a rigorous
argument-principle certificate; interval phase accumulation and an
independently proved complex Hurwitz remainder bound are still required.

## 2026-09-13: v2 long batch completed

The v2 sweep completed all 108 configurations with zero failures or timeouts. Across every tested rectangle, edge density, Euler--Maclaurin truncation, and correction order, it reported zero boundary boxes containing zero and sampled midpoint winding 1. The finest completed configuration used `ds=dt=0.001`, `edge_points=2048`, `N=512`, and `M=18`; its smallest reported Arb lower bound was approximately `0.001240236`. The aggregate is stored in `runs/dh-long-batch-py3-v2/summary.json`. This strengthens numerical robustness around the known DH fixture but remains a non-certified diagnostic: interval phase accumulation and an independently proved complex Hurwitz remainder bound are still required. The `rh-v2` heartbeat was paused after completion.

## 2026-09-13: actual-zeta free-sigma long batch launched

The next round transfers the free-sigma screening from the Davenport--Heilbronn calibration family to the actual Riemann zeta function. The Python 3 driver `zeta_long_batch_py3.py` uses a fixed grid `0.52 <= sigma <= 0.98`, `40 <= t <= 2000`, one-unit height spacing, and three overlapping sigma bands per 80-unit block. The long profile has 75 resumable windows, independent JSON outputs, and a 1800-second child timeout. Early windows have completed with `off_line_numerical_count=0`; all outputs are numerical-only and any apparent off-line Newton point still requires an independent interval rectangle count.

## 2026-09-13: chained follow-up rounds

A Python 3 supervisor `zeta_chain_supervisor_py3.py` now waits for the current
75-window actual-zeta batch to finish, then launches two resumable follow-up
profiles automatically: `extended` scans `2000 <= t <= 4000` at 45/80 decimal
working/refinement precision, and `extended2` scans `4000 <= t <= 6000` at
50/90 precision. Each round has its own output directory and summary. The
chain state is recorded under `runs/zeta-chain-supervisor/`; all rounds remain
finite numerical screens and any off-line Newton point still requires an
independent interval rectangle count.

## 2026-09-14: chained zeta scans completed

The three-round actual-zeta chain finished successfully. The baseline
`40 <= t <= 2000`, the first extension `2000 <= t <= 4000`, and the second
extension `4000 <= t <= 6000` each completed all 75 windows with zero failures
or timeouts. Summing the per-window `off_line_numerical_count` fields gives
zero in every round. Thus the finite free-sigma screen produced no numerical
off-critical-line candidate in the tested boxes. This is a negative numerical
screen only; it is not a zero-free proof or an RH proof. The chain state and
all round summaries remain under `runs/zeta-chain-supervisor/` and the three
`runs/zeta-*-batch-py3/` directories.

## 2026-09-14: next phase after finite zeta screening

The completed free-`sigma` scans give no numerical off-line candidate through
`t <= 6000`, so the next phase should increase **independence of observables**
rather than only extending the same zeta grid. The working hypothesis is
that a genuine off-line atom would leave a common, held-out signature in
several prime-derived channels. This is a candidate-generation hypothesis,
not an implication from the explicit formula and not a route around the
unsolved RH.

### Phase A: calibrated common-spectrum panel

Run the existing Mertens (`M(x)`), `Lambda/psi`, prime-counting, and
short-interval channels on identical log-time windows. Fit shared `(sigma,t)`
atoms while allowing channel-specific amplitudes and phases. Require all of:

* survival under two independent `N` scales and at least two cut points;
* survival on a held-out `u=log(x)` range;
* coherence in at least three arithmetic channels and two independent grids;
* passage of block-shuffle, prime-preserving sign-shuffle, and synthetic
  critical-line controls.

Mertens excursions or a single short-interval anomaly are never promoted by
themselves: `M(x)` is a reciprocal-zeta channel, and finite cumulative
correlations can be caused by smoothing or block geometry.

### Phase B: short-interval and gap-word stress tests

Use `R_theta(x)=psi(x+x^theta)-psi(x)-x^theta` and prime-gap words at
`theta=0.50, 0.525, 0.60`. The square-root endpoint is a stress-test scale,
not an unconditional theorem. Compare original data with density-preserving
and gap-preserving controls, and report only effect sizes, control quantiles,
and reproducibility across scales.

### Phase C: family hierarchy and negative controls

Apply the same feature and candidate gates to zeta, `chi4`, `chi5`, the
periodic k3/k5 Hurwitz models, Davenport--Heilbronn, and the function-field
toy family. The purpose is to separate symmetry-only artifacts from signals
that track Euler-product or positivity structure. An off-line zero in a
Hurwitz or Davenport--Heilbronn control is a sensitivity fixture; it cannot be
transferred to zeta.

### Phase D: escalation gate for any candidate

Only a candidate surviving Phases A--C is sent to direct high-precision zeta
evaluation. It must then pass an independent rectangular argument-principle
count (validated Arb/FLINT derivative and Hurwitz-remainder bounds, nonzero
boundary enclosure, and integer winding interval). Until those obligations
are met, labels remain `NUMERICAL_CANDIDATE` or `NONCERTIFIED_DIAGNOSTIC`.

This ordering deliberately prioritizes independent channels and controls over
blindly pushing the height range higher. A null result is useful: it measures
the sensitivity and false-positive rate of the prime-dynamics pipeline, while
leaving the RH question open.

## 2026-09-14: near-critical-line extension launched

After the completed broad scan through `t=6000`, a focused Python 3 batch
`zeta_nearline_batch_py3.py` was launched for `6000 <= t <= 10000`. It uses two
overlapping near-line bands `[0.5005,0.54]` and `[0.53,0.62]`, sigma spacing
`0.002`, and working/refinement precision `55/95` digits across 80 resumable
windows. The purpose is to test whether a very small displacement from
`Re(s)=1/2` produces a persistent numerical signal that the wider grid could
miss. Outputs remain numerical-only and any candidate still requires a
validated rectangle count.

## 2026-09-14: near-critical-line batch completed

The focused near-line batch completed all 80 windows covering `6000 <= t <=
10000` in the overlapping bands `[0.5005,0.54]` and `[0.53,0.62]`, with
sigma spacing `0.002` and 55/95 digit working/refinement precision. There were
zero failures or timeouts and the sum of all per-window
`off_line_numerical_count` values is zero. This rules out no mathematical
possibility; it records a negative finite numerical screen in a region where a
small displacement from the critical line would have been visible to this
method. The final result is `runs/zeta-nearline-batch-py3/summary.json`.

## 2026-09-14: Phase A resumable common-spectrum batch

Implemented `prime_spectrum_batch_py3.py`, a per-artifact resumable runner for
Mertens, Lambda/psi, prime-count/short-interval, independent-grid demodulation,
density-preserving prime surrogates, and stratified shuffle controls. It uses
two arithmetic scales, two trimmed log grids, three held-out cut points, and
updates `progress.json` atomically after every subtask before producing
`summary.json` and `report.md`. A smoke run at `N=50,000` completed six
subtasks with zero failures and zero cross-channel candidates. The long run is
launched in `runs/prime-spectrum-phaseA-py3/` under Python 3.14 because this
host has no Python 3.10 runtime; every result records that interpreter fact.
All outputs remain finite numerical screens or empirical surrogate controls.
No Mertens, prime-count, Lambda/psi, or short-interval anomaly is an actual
zeta candidate, and no Arb/FLINT interval certification is claimed.

## 2026-09-15: Phase B short-interval stress batch completed

The resumable `short_interval_phaseB_batch_py3.py` completed four artifacts at
`N=10^6` and `5*10^6` for `theta=0.525` and `0.60`, with three held-out cuts,
two block scales, random/block controls, logarithmic-density-preserving
surrogates, and block-shuffled gap-preserving surrogates. All four tasks
completed with zero failures and zero screen or zeta-handoff candidates. The
outputs are in `runs/short-interval-phaseB-py3/`. This remains a finite
short-interval/gap stress screen with empirical controls; it provides no zeta
numerical candidate or Arb/FLINT certification.

## 2026-09-15: Phase C family-control batch completed

The resumable `family_phaseC_batch_py3.py` completed four artifacts at
`N=200,000`: the chi4/chi5 Euler-product fixtures, the Davenport--Heilbronn
periodic sensitivity fixture, and the exact finite-field curve panel. All
four tasks completed with zero failures and zero zeta-handoff candidates. The
Davenport--Heilbronn row remains an uncertified off-line sensitivity control;
periodic or finite-field behavior cannot transfer to the Riemann zeta
function. Outputs are in `runs/family-phaseC-py3/`.
