# Multi-grid control quantile check

The rejected (t\approx37.5) residual was tested against six global-shuffle
replicates on three trimmed log grids, using (N=10^6) and the same Mertens,
`psi`, and `theta` increment demodulator. In the focused window
(37\le t\le38), the real maximum (R^2) was `0.00504`; the empirical
95th-percentile control maximum was `0.01077`. The residual therefore fails
the control gate before any zeta evaluation.

Output: `runs/multi-grid-control-1e6.json`.

This is a focused null check rather than a theorem-level distribution for
cumulative arithmetic functions. Larger-N replicated controls remain useful
if a future grid-stable frequency appears.
