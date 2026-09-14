# DH Taylor/Lipschitz boundary diagnostic (Python 3)

`dh_taylor_lipschitz_py3.py` compares the existing Arb Euler--Maclaurin complex
box on each contour segment with a centre-value disk.  For a segment midpoint
`s0` and half-length `h`, it uses

\[
 |F(s)-F(s_0)| \leq Lh,
 \qquad L=1.25\max_j|F'(s_0+q_jh)|,
\]

where the derivative is a high-precision central finite difference and the
maximum is sampled at five points.  This often removes the dependency
inflation of direct complex boxes and is useful for choosing a future Taylor
model subdivision.

The derivative maximum is not an interval enclosure and the multiplier is a
heuristic safety factor.  Therefore the output status is always
`NONCERTIFIED_TAYLOR_LIPSCHITZ_DIAGNOSTIC`; it is not a zero certificate or a
rigorous argument-principle calculation.

Example:

```powershell
py -3.10 research/2026-09-13-prime-dynamics-zero-hypotheses/dh_taylor_lipschitz_py3.py `
  --edge-points 16 --output runs/dh-taylor-lipschitz-py310-e16.json
```

For the known Davenport--Heilbronn root and a `0.01 x 0.01` rectangle, the
16-segment run produced 64/64 positive heuristic Taylor lower bounds, with
minimum lower bound `0.011574478671040427`, while the minimum direct Arb-box
lower bound rounded to zero because of dependency widening.  The midpoint
winding remained 1. These figures are diagnostic only and do not upgrade the
existing `NONCERTIFIED_SUBDIVISION` status.
