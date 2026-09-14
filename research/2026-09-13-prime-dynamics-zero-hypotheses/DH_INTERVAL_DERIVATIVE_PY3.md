# Analytic derivative interval diagnostic (Python 3)

`dh_interval_derivative_py3.py` differentiates every finite
Euler--Maclaurin term with Arb/FLINT rather than estimating the derivative by
finite differences. On the `0.01 x 0.01` DH rectangle with 16 segments per
edge:

- 64/64 boundary segments have positive centre-value plus derivative lower bounds;
- the minimum lower bound is `0.011739566087598489`;
- the largest interval derivative upper bound is `1.3207268355063309`;
- direct complex-box lower bounds still widen to zero.

The differentiated remainder is currently based on a scalar majorant and has
not been independently proved as a complex interval theorem. Phase interval
accumulation is also not implemented. The JSON status is therefore
`NONCERTIFIED_INTERVAL_DERIVATIVE_DIAGNOSTIC`; this is a stronger diagnostic
than sampled finite differences, not a zero certificate.

Output: `runs/dh-interval-derivative-py310-e16.json`.
