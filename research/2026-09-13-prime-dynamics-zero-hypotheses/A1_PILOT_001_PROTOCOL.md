# A1-PILOT-001: two-sided free-sigma seed probe

Frozen before execution, 2026-09-16. Route `RC:A1`; purpose: discover a numerical
anomaly or quantify whether a small, explicitly chosen collection of off-axis
starts instead returns to the critical line. This is a finite basin probe, not
a rectangular zero census or a test with established off-line detection power.

## Configuration

- Main heights: 10010, 10012, 10014. Real-part starts: .30, .49, .51, .70.
- Twelve tasks; each independently repeats the SAME start at 50 and 80 decimal
  digits using the existing `zero_lab.refine`, without fixing sigma to .5.
- Maximum 40 Newton steps per precision; existing damping keeps iterates in
  0 < sigma < 1 and 0 < t < 10050, not inside the seed-height interval.
- Reevaluate each converged higher-precision endpoint with mpmath and FLINT/Arb
  using the existing `check_point`, at 80 digits and box radius 1e-12. Its point
  agreement and value enclosure are not a root-existence/count certificate.
- Low/high endpoint agreement threshold: 1e-25. Near-line label threshold:
  |sigma-.5| <= 1e-30. Residual thresholds follow the solver: 10^(-dps+15).
  These are numerical screening cutoffs, not exclusion distances from RH.
- Smoke uses the same two outer starts at height 10010, 35/50 digits, agreement
  threshold 1e-15 and near-line threshold 1e-20. Its lower precision differentiates
  it from the main experiment. Smoke endpoints never select main starting points.
- Per-task process timeout: 90 seconds. Per-invocation budget: 900 seconds;
  no new task starts when the budget expires (one child can extend past it by
  up to its timeout). No parameter enlargement or adaptive extra seeds.
- Python 3.10 unavailable; actual interpreter is Python 3.14.3 with installed
  NumPy, SciPy, mpmath, and python-flint. Exact runtime and source hashes are in
  the immutable run manifest. Subtasks are separate JSONs with atomic progress.

The documented historical 305 windows ended at t=10000. Their original raw run
directories are absent from this checkout; this pilot does not claim to reverify
them. No matching local pilot was found. Main starts are new relative to that
record; Newton endpoints may migrate, and their actual coordinates are retained.

## Interpretation and disposition

- Stable, residual-small, independently checked endpoint outside the numerical
  near-line threshold: `OFF_LINE_NUMERICAL_CANDIDATE`; HOLD for targeted review.
- Low/high endpoint disagreement: `PRECISION_UNSTABLE`; HOLD as a numerical clue,
  not a zeta counterexample. A precision-dependent change of basin is possible.
- Failure of cross-library agreement or residual requirements: review required.
- Solver nonconvergence is counted separately from an execution exception or
  timeout. Neither is evidence that no zero exists.
- If all tasks finish consistently near the line: END this finite probe at C2,
  report the attraction counts and distinct endpoints. Do not claim the region
  or method class is excluded. D1/E1/E2 are not earned by small residuals alone.
- Budget exhaustion, missing work, failures or unresolved anomalies: HOLD with
  explicit counts and reason. GO/FORK require a separately stated next question.

No random surrogates are needed for this direct function-evaluation probe.
Two-sided starts, precision repeats, and a second numerical library are checks
on computation, not independent statistical samples. Strict certification of an
off-line root would require a separate rigorous existence/count argument.
