# Actual-zeta long batch (Python 3)

This round transfers the free-sigma screening from the Davenport–Heilbronn
calibration family to the actual Riemann zeta function.  The child process
evaluates a preregistered rectangular grid

\[
  0.52\leq\sigma\leq0.98,
  \qquad 40\leq t\leq2000,
\]

in overlapping sigma bands and 80-unit height blocks.  The grid is fixed
before any zeta value is read.  The lowest finite-grid values are used only as
initial seeds for unconstrained, damped Newton iteration in both sigma and t.

The long profile contains 75 windows (25 height blocks times three overlapping
sigma bands), with one-unit height spacing and 0.01 sigma spacing.  Every
window gets an independent JSON result and a per-process timeout.  The runner
can resume after interruption by reusing valid child outputs.

## Run

```powershell
py -3.10 research/2026-09-13-prime-dynamics-zero-hypotheses/zeta_long_batch_py3.py `
  --profile long `
  --output-dir runs/zeta-long-batch-py3 `
  --timeout 1800
```

For a quick check:

```powershell
py -3.10 research/2026-09-13-prime-dynamics-zero-hypotheses/zeta_long_batch_py3.py `
  --profile smoke --output-dir runs/zeta-long-smoke
```

`progress.json` is updated after each window; `summary.json` is written only
after the planned prefix completes.  `TIMEOUT` and `FAILED` entries are kept
for auditability.

## Interpretation boundary

The output is a finite numerical screen, not a search proof and not evidence
that RH is false.  A free-sigma Newton convergence is only a numerical
candidate.  Any apparent off-line point must be rerun at independent
precision and passed to an interval argument-principle/rectangle count before
it can be discussed as a possible zero.  The current child intentionally sets
`certified_off_line_zero` to `false`.
