# Hurwitz Euler–Maclaurin remainder stress audit (Python 3)

This audit evaluates the Euler–Maclaurin approximation and its analytic derivative at 800 point samples around the known Davenport–Heilbronn root
`0.8085171824566373855533519606 + 85.69934848537759217192926771 i`.
It uses Python 3.10 and mpmath at 80 decimal digits, with `N in {32,64,128,256}`, `M in {8,10,12,14,16}`, eight nearby points, and the five Hurwitz components `a=r/5`.

The scalar remainder majorant was respected at every sampled point:

- maximum value-error / scalar-bound ratio: `0.08260584717544682`
- scalar-majorant violations: `0 / 800`

The analytic derivative implementation was independently compared with mpmath differentiation of the truncated Euler–Maclaurin expression before the stress run. Against mpmath Hurwitz-zeta derivatives, the diagnostic derivative ratio was:

- maximum derivative-error / heuristic-derivative-bound ratio: `0.058107083464680985`
- heuristic violations: `0 / 800`

The derivative bound is explicitly **heuristic**: it multiplies the scalar majorant by a log-derivative factor. It is not an Arb complex-box enclosure and does not prove a differentiated remainder theorem. The audit therefore supports the next implementation step (an interval remainder and derivative enclosure), but it does not certify the Davenport–Heilbronn contour.

Data: `runs/hurwitz-remainder-stress-py310.json`.

Reproduce with:

```powershell
py -3.10 research/2026-09-13-prime-dynamics-zero-hypotheses/hurwitz_remainder_stress_py3.py `
  --dps 80 `
  --output runs/hurwitz-remainder-stress-py310.json
```
