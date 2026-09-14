# Family control panel

`family_control_panel.py` is a small, reproducible fixture for the family
level comparison in `L_FUNCTION_FAMILY_UNIVERSALITY.md`. It keeps three cases
separate:

* `chi4`, the primitive real character modulo 4, with period by residues
  `r=1,...,4`: `(1, 0, -1, 0)`;
* `chi5`, the real quadratic character modulo 5, with period by residues
  `r=1,...,5`: `(1, -1, -1, 1, 0)`;
* the exact function-field calibration
  `E/F_7: y^2 = x^3 + x`.

The first two are Euler-product and functional-equation controls. Their
coefficient diagnostics should show zero mean over a period and zero
multiplicativity defect. The finite periodic Dirichlet series are evaluated
with the exact continuation identity

\[
 \sum_{n\ge1}a(n)n^{-s}=q^{-s}\sum_{r=1}^q a(r)\,\zeta(s,r/q),
\]

at a few off-axis sample points. These values are fingerprints for the
fixture, not zero certificates.

The finite-field curve has 8 projective points over `F_7`, trace `0`, and
numerator

\[
P(u)=1+7u^2.
\]

Its two numerator roots have modulus `7^(-1/2)`, so the change of variables
`u=7^{-s}` places both roots exactly on `Re(s)=1/2`. This is a proven toy
analogue and an independent check that the panel's line-mapping convention is
correct.

The Davenport--Heilbronn entry is intentionally disabled. A literature-reported
off-line point is retained as metadata only; before using it as a negative
control we need high-precision continuation, its correct functional equation,
and an argument-principle or interval certificate. The current smoke report
must never be read as a certified counterexample.

The coefficient parameter must be handled carefully. The standard normalization
uses

\[
\kappa=\frac{\sqrt{10-2\sqrt5}-2}{\sqrt5-1}\approx0.2840790438404,
\]

in the linear combination of the two conjugate modulo-5 characters. A previous
scratch value with `sqrt(10-sqrt(5))` gives a visibly nonzero residual at the
reported point and is not the Davenport--Heilbronn function.

Run the smoke fixture with the project Python 3 environment:

```powershell
& "D:\26-aimath\rh_counterexample\.venv\Scripts\python.exe" `
  research/2026-09-13-prime-dynamics-zero-hypotheses/family_control_panel.py `
  --pair-n 40 --output runs/family-control-smoke.json
```

The generated JSON records the exact point count, line residual, character
means, multiplicativity checks, and sample Hurwitz values. It is a structural
calibration artifact and is not evidence for or against the Riemann Hypothesis.

## Detector-transfer fixture

`family_detector_transfer.py` applies the same log-grid detector used by the
prime-dynamics experiments to a periodic coefficient family. It forms the
weighted partial sum

\[
 S_\sigma(x)=\sum_{n\le x}a(n)n^{-\sigma},
\]

samples its log-grid derivative, lists the strongest FFT frequencies, and
reports fixed-target train/holdout projections at splits `0.55`, `0.67`, and
`0.80`. Global and within-block coefficient shuffles are recomputed as null
controls. The Davenport--Heilbronn target is the high-precision fixture near
`0.8085171824566 + 85.6993484854 i`; `chi4` and `chi5` provide positive
Euler-product controls with a nominal critical-line target.

Example:

```powershell
& "D:\26-aimath\rh_counterexample\.venv\Scripts\python.exe" `
  research/2026-09-13-prime-dynamics-zero-hypotheses/family_detector_transfer.py `
  --family dh --n 200000 --samples 2048 --control-reps 8 `
  --output runs/family-detector-transfer-dh.json
```

The output is deliberately labelled **method sensitivity only**. A target
projection or an FFT peak does not certify a zero of the periodic Dirichlet
series, its functional equation, or the Riemann zeta function.
