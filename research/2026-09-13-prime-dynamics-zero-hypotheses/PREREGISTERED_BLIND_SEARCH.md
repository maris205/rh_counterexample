# Pre-registered blind search

This artifact freezes the unknown-frequency handoff before inspecting a new
candidate table. The allowed window is (4\le t\le40), with the five known
Riemann ordinates removed by radius (0.75). The observation files and the
four log-grid designs are fixed in `PREREGISTERED_BLIND_MANIFEST.json`.

The runner requires at least three independent arithmetic channels, three
independent `(N, samples, trim)` grids, both listed arithmetic scales, a phase
resultant of at least `0.80`, and a conservative control threshold. The
threshold is the maximum q95 already measured by the listed controls, namely
`0.016892465431210348`. A cluster passes the control gate only when every
channel's best `R2` exceeds this value. This is deliberately conservative and
can yield no candidates.

Run:

```powershell
python research/2026-09-13-prime-dynamics-zero-hypotheses/preregistered_blind_runner.py `
  --output runs/preregistered-blind-20260913.json
```

The JSON records the manifest SHA-256, source files, all rejected clusters,
the per-channel scores, phase resultant, and the final candidate table. The
result is an exploratory handoff only. A passing row would require a separate
high-precision evaluation of the actual Riemann zeta function, free-
`sigma` Newton refinement, and a local contour/counting audit before it could
be discussed as a possible zero.

