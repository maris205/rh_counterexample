# Common-spectrum protocol V2

Version: 2026-09-16. Scope: prospective finite-data candidate generation.
This protocol supersedes incompatible phase, independence, control-quantile,
and candidate-count claims in the older Phase A/B/C notes. It does not itself
record an executed or successful experiment. Previously inspected data are
exploratory reanalysis; a manifest hash does not retroactively make them blind.

## 1. Freeze the experiment before reading candidate output

Write and hash a manifest containing source and input hashes, interpreter and
library versions, observable formulas, `N` values, absolute log-time intervals,
sample counts, endpoint trims, split boundaries, preprocessing support,
frequency/envelope grids, exclusion radius, candidate budget and separation,
objective and tie-breaking rule, surrogate families, replicate counts, seeds,
and every gate. Resume only when the entire manifest and source hashes match.
Record the actual runtime (`py -3.14` on this host); do not claim Python 3.10.

A reasonable starting profile is two scales `N=10^6, 5*10^6`, grids
`(1024,0)` and `(1536,0.08)`, cut fractions `0.55,0.67,0.80`, frequencies
`4 <= t <= 40` spaced by `0.05`, exclusion radius `0.75`, `beta=0`,
and three training-nominated candidates separated by at least `0.30`.
These values become operative only in the frozen run manifest. A changed
configuration is a new experiment. Reduced smoke profiles test execution and
must explicitly fail the production-completeness gate.

Optional envelope search uses a separately declared finite `beta` grid. Every
searched value belongs to the multiplicity budget. Continuous refinement is
allowed only on training data, with frozen brackets, tolerances, and evaluation
budget; it must also run in every surrogate replicate.

## 2. Observables and dependence

| Observable family | Required primary representative | Related diagnostics |
| --- | --- | --- |
| Mertens | `M(x)/sqrt(x)` or its preregistered log increment | Other normalizations and derivatives |
| Global prime | `(psi(x)-x)/sqrt(x)` | `theta`, prime-count residuals |
| Local prime | One fixed short-interval residual | Other window powers, fixed-log windows, gap words |

One representative per family contributes to the primary score. Select the
representative before candidate inspection. If multiple columns are used,
freeze within-family weights summing to one; never take the best column after
seeing results. `psi`, `theta`, and prime counting alone cannot satisfy the
three-family condition. Mertens is mandatory in the three-family profile.

These are distinct observable families, not statistically independent
samples: local prime counts are functions of the same primes used by global
counts, and Mertens also reflects prime arithmetic. Nested `N`, endpoint trims,
and multiple grids are robustness checks, not independent replication. A
significance statement must respect their dependencies.

For short windows use actual support `h_eff=min(N,x+h)-x` in every baseline
and normalization, or discard truncated windows by a frozen rule. A gap
residual under the mean-gap heuristic is `(p_next-p)/log(p)-1`, not
`(p_next-p)*log(p)-1`. A prime-count window and a von-Mangoldt-weighted window
are different observables and must be named and normalized accordingly.

## 3. Sampling, training, and holdout boundaries

Keep a fixed global origin, preferably `u0=0`, for `u=log(x)`. Apply identical
sampling operators to observed data and controls. Record actual coordinates
after integer rounding and deduplication; an irregular grid cannot be treated
as a uniform FFT grid without explicit resampling.

Determine the raw-data support of every feature. A centered derivative or a
forward short window near a split can touch future data. Remove a guard region
large enough for that support or compute features separately on the two
segments. A resampler must not interpolate a training point using a holdout
endpoint. Fit centering, scale, polynomial trend, smoothing choices, and any
covariance estimates using training data only.

Select the shared frequency using a common training prefix ending no later
than the earliest absolute holdout boundary among all required cells. Otherwise
the large-`N` or late-cut training data can contain a smaller-`N` holdout.
Subsequent fits at later cuts may use their own prefixes at that fixed
frequency; their overlapping holdouts are dependent robustness evaluations.
Record that overlap. A fresh disjoint later interval is required to call a
subsequent run an external replication.

## 4. Shared-frequency regression and predictive score

For channel `c` and fixed candidate `(t,beta)`, fit on training data

`y_c(u)=q_c(u)+exp(beta*(u-u0))*[a_c*cos(t*(u-u0))+b_c*sin(t*(u-u0))]+e_c(u)`.

The pair `(t,beta)` is shared; `a_c,b_c` and the preregistered polynomial
coefficients in `q_c` are channel-specific. Fit trend and tone jointly, using
stable least squares with a recorded rank tolerance. Fit the trend-only
baseline separately. Degenerate rank, inadequate sample support, nonfinite
values, or zero baseline variance yield an invalid cell, not a favorable zero.

For training selection use the equally weighted family mean of normalized
training SSE improvements (or another objective explicitly frozen in the
manifest). Each family has equal total weight regardless of its column count.
Choose the fixed number of separated training maxima, breaking ties by the
smallest `t` then smallest `beta`. Selecting candidates, optimizing a frequency,
or adjusting an envelope with holdout scores is prohibited.

Freeze the training trend, normalization, `a_c,b_c,t,beta` and compute

`Q_c = (SSE_baseline,holdout - SSE_atom,holdout) / SSE_baseline,holdout`.

Do not refit amplitude, phase, or trend on the holdout for this score. Keep
negative `Q_c`; report both SSE values and the number of valid points. Within
a family use its declared representative or frozen weighted SSE aggregation.
For a candidate use the conservative score

`S_candidate = min Q_family,N,grid,required_cut`.

All required cells must exist, and every `Q` must be positive before promotion.
This is a reproducibility requirement, not an assertion of independence.
An independently fitted per-channel-frequency model is a descriptive
alternative; because shared and unrestricted models have different fitting
freedom, a raw in-sample likelihood difference is not a significance result.

`beta` is a fitted envelope parameter. A field named `sigma_fit=0.5+beta`
must explicitly carry `not_a_zeta_zero_real_part=true`. Generic normalized
short-window signals do not automatically have the same envelope transfer
function as cumulative explicit-formula channels. Use `beta=0` as the primary
common-frequency model until synthetic operator tests justify a shared
envelope. Failure of this model does not rule out an actual zero.

## 5. Phase and frequency stability

For `a*cos(t*v)+b*sin(t*v)=A*cos(t*v+phi)`, store
`phi=atan2(-b,a)`, `A=hypot(a,b)`, and the declared basis convention.
Legacy `atan2(b,a)` represents the opposite sign convention and must be
converted before comparing. A local-origin fit with phase `phi_local` at
`u_local` converts to the common origin using
`phi_global=wrap(phi_local+t*(u0-u_local))`.

Compare phases only within the same channel, at the same fixed frequency and
envelope and the same global origin. Channel phases are allowed to differ.
Never pool phases from individually selected nearby frequencies. An optional
fixed-frequency holdout refit may diagnose phase transport but is explicitly
secondary and does not alter the frozen predictions. If amplitude is below a
preregistered detectability floor, phase is undefined and cannot pass a gate.

An optional within-channel cross-grid resultant threshold `R>=0.80`, and
training-only peak spread `max(t_hat)-min(t_hat)<=0.05`, are engineering
thresholds requiring injection calibration. They are not universal resolution
bounds or p-values. Include them in each surrogate's candidate procedure when
used for promotion; never use them to rescue a failed predictive score.

## 6. Known-zero exclusion and operator controls

Enumerate all known positive critical-line ordinates in
`[t_min-radius,t_max+radius]`, including the first ordinate beyond the upper
bound when checking catalogue coverage. Use the centralized catalogue
generator, store its values/precision/hash, and stop blind classification if
coverage cannot be established. Every candidate within the radius of any
listed ordinate is `KNOWN_LINE_CALIBRATION`, with nearest index and distance.

For `t<=40` the positive ordinates include
`14.1347251417, 21.0220396388, 25.0108575801, 30.4248761259,
32.9350615877, 37.5861781588`. In particular `37.5` lies within the sixth
known-zero neighborhood. Removing only the first five is invalid. Exclusion
is a discovery convention: it deliberately makes no claim about an additional
off-line zero sharing a known ordinate or lying inside an excluded window.

Inject known-line tones, unknown-frequency tones, and growth-envelope tones
before the observation operator, with frozen amplitudes and channel-specific
phases. Replay window clipping, integration/differentiation, resampling, and
normalization. Report recovery, leakage into unexcluded frequencies, and
missed injections. A tone added only after resampling does not validate the
entire measurement chain. Include pure trend/no-tone controls.

## 7. Surrogates, scan multiplicity, and Monte Carlo resolution

Freeze the nulls and their scientific meanings. Useful diagnostics include
global coefficient shuffle, large-block permutation/within-block shuffle,
prime-density-preserving position resampling, and gap-preserving controls.
They preserve different properties and cannot be substituted after seeing
which one passes. Very small block shuffles can preserve cumulative sums.
Apply a shared transformation to coupled observable columns and derive all
prime-related channels from the same surrogate prime source. If a proposed
null has no justified coupled Mertens/prime construction, label its joint
result model-dependent; a dependence-preserving multivariate block null can
be used alongside family-specific arithmetic stress tests. Independent
channel shuffles do not establish a valid joint arithmetic null by fiat.

For each null family and replicate, rerun the full declared pipeline:
preprocessing, training frequency/envelope selection, candidate separation,
frozen holdout prediction, and all robustness/phase gates. Define its maximum
`T_b=max(S_candidate)` over training-nominated candidates (use negative
infinity for none). This is a maximum over the entire permitted selection
procedure; taking a maximum after omitting searched settings is invalid.
With several optional model variants, pool their maxima too, or freeze a
separate family-wise allocation before running.

For observed candidate score `S`, report

`p_max=(1+count(T_b >= S))/(B+1)`.

Count ties conservatively. This is a scan-adjusted Monte Carlo rank p-value
under the declared exchangeable null, or an empirical surrogate rank when
exchangeability with real arithmetic data is not justified. It is not an RH
probability. Report `B`, the exceedance count, `1/(B+1)`, and Monte Carlo
uncertainty; never report `p=0`. A q95 can be descriptive but cannot replace
the rank test or compensate for a missing scan adjustment.

Require `p_max<=0.05` for every mandatory valid null family; this is an
intersection requirement, not a choice of the most favorable null. With
`B<19`, even zero exceedances cannot meet the threshold. The production
profile requires at least `B=199` per mandatory null (resolution `0.005`);
more may be needed near the decision boundary. Fixed replicate budgets avoid
optional-stopping inflation. Smoke runs and missing or insufficient nulls
set `CONTROL_GATE_INCOMPLETE`, regardless of a small observed q95.

## 8. Phase B/C completion and promotion records

Phase B must actually execute density-preserving and gap-preserving controls
for its declared powers/grids/cuts, with effect sizes and matching control
quantiles. Existing fixed-frequency refits may be retained as descriptive
projection metrics only. Phase C must separate family-fixture metadata,
implemented detector transfer, and missing methods. A known off-line
Davenport--Heilbronn fixture is a sensitivity control for that function, not
evidence for zeta; failure to recover it measures detector limitations.

Every output needs both execution status and gate status. Use `PASS`, `FAIL`,
`NOT_EVALUATED`, or `INCOMPLETE` for each gate and include its reason/evidence.
An unevaluated candidate count is JSON `null`; use integer zero only after
an actual candidate procedure has completed over its stated domain. A
program's refusal to hand off candidates is not a zero-candidate measurement.
Never reuse an old artifact after source/config mismatch; hash dependencies,
not just the outer runner. Failed artifacts remain failed until replaced by a
successfully validated matching artifact.

Promotion requires all required cells, known-zero coverage, training-only
selection, frozen positive prediction in all three observable families,
declared grid/scale robustness, completed sensitivity controls, and every
required multiplicity-adjusted control gate. Store all rejected rows and
specific reasons. Passing yields `SPECTRAL_SEARCH_CANDIDATE`, never a zeta
zero. No passing row means only no promoted candidate under this protocol.

An actual zeta search is a separate step: evaluate zeta at high precision with
independent implementations, refine with free real part, and require a
validated rectangle strictly off the critical line, a nonzero boundary
enclosure, and a positive integer argument-principle count. A fitted envelope,
numerical residual, pointwise interval containing zero, or sampled winding is
not that certificate. Zeta-zero symmetry and RH concern the zeros of zeta
itself ([NIST DLMF §25.10](https://dlmf.nist.gov/25.10)).
