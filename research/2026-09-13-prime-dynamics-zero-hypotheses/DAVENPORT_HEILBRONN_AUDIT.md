# Davenport--Heilbronn negative-control audit

The standard period-five Davenport--Heilbronn combination uses

\[
\kappa=\frac{\sqrt{10-2\sqrt5}-2}{\sqrt5-1}
       =0.2840790438404122960\ldots
\]

and periodic coefficients

\[
(a_1,a_2,a_3,a_4,a_5)=(1,\kappa,-\kappa,-1,0).
\]

The finite Hurwitz representation

\[
F(s)=5^{-s}\sum_{r=1}^5 a_r\,\zeta(s,r/5)
\]

was evaluated at 80 decimal digits. At the rounded literature point

\[
s=0.8085171825+85.6993484854i,
\]

the residual is about (6.13\times10^{-11}). Secant refinement gives

\[
s=0.80851718245663738555\ldots
  +85.69934848537759217193\ldots i,
\]

with residual below (2.4\times10^{-80}). This confirms the reported point
as a high-precision zero of the periodic Dirichlet combination.

The coefficient sequence is not multiplicative: a finite diagnostic over
integers up to 80 finds 52 bad pairs. This is exactly why the fixture is a
negative control for claims that functional equations and periodic bounded
coefficients alone force a critical-line theorem.

The argument-principle certificate remains disabled. The correct completed
functional equation for this non-scalar combination and a validated contour
enclosure still need to be implemented. Thus this audit confirms a family
fixture and a numerical zero, but it is not itself a formal zero-count
certificate.

Machine-readable output: `runs/davenport-heilbronn-audit.json`.

As a separate numerical sanity check, a (0.01\times0.01) rectangle centered
at the refined point was sampled with 256 points per side. The unwrapped
boundary phase gives winding number 1 and the boundary minimum is nonzero;
the output is `runs/davenport-heilbronn-winding.json`. This is a discretized
winding check only. It is useful for catching a wrong coefficient formula, but
it is not an interval-rigorous argument-principle certificate.
