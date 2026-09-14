# Hurwitz Euler--Maclaurin prototype (Python 3 + Arb/FLINT)

`hurwitz_em_flint_py3.py` implements a complex-box Euler--Maclaurin evaluator
for

\[
\zeta(s,a)=\sum_{j=0}^{N-1}(j+a)^{-s}+\frac{(N+a)^{1-s}}{s-1}
 +\frac12(N+a)^{-s} + \sum_{k=1}^{m}\frac{B_{2k}}{(2k)!}(s)_{2k-1}(N+a)^{-s-2k+1}+R_m.
\]

The remainder is bounded using

\[
|R_m|\le \frac{2\zeta(2m)}{(2\pi)^{2m}}
\frac{|(s)_{2m}|}{\Re(s)+2m-1}(N+a)^{-\Re(s)-2m+1},
\]

with all quantities evaluated on an Arb/FLINT complex box. The unknown
remainder is enclosed by a square of the resulting radius. This is a useful
bounded-evaluation prototype, not a completed argument-principle certificate.

Example (DH fixture root neighbourhood):

```powershell
py -3.10 research/2026-09-13-prime-dynamics-zero-hypotheses/hurwitz_em_flint_py3.py `
  --ds 1e-4 --dt 1e-4 --n 128 --m 12 `
  --output runs/dh-hurwitz-em-py310.json
```

At the (0.0001\times0.0001) box around
`0.8085171824566373855533519606 + 85.69934848537759217192926771 i`, all five
Hurwitz remainder bounds are finite (about `1.1e-24`--`1.3e-24`). The final
Davenport--Heilbronn enclosure contains zero because the box is much larger
than the numerical residual and because dependency/cancellation widths are
preserved. Thus the output is intentionally labelled `NONCERTIFIED_PROTOTYPE`.

The next strict step is edge subdivision: evaluate each small boundary box,
reject any box whose enclosure contains zero, and accumulate a certified
interval argument change. Until that is implemented, no zero count is claimed.
