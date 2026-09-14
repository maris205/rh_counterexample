# Periodic-family zero-surface transfer test

`family_zero_surface.py` applies the same free-σ numerical search idea to
four functions in the window (83\le t\le88): the corrected
Davenport--Heilbronn periodic combination, the Riemann zeta function, and the
primitive characters χ₄ and χ₅. It scans a coarse
((\sigma,t))-grid and refines the best point without fixing σ.

For the Davenport--Heilbronn fixture the grid minimum near ((0.8,85.75))
refines to the known off-line root

\[
0.80851718245663738555\ldots+85.69934848537759217\ldots i.
\]

In the same height window, zeta and both character controls refine to the
critical line. This is a useful sensitivity test: the free-σ solver can
recover a known line-off root when the function actually has one. It does not
say anything about untested zeta heights, and it is not a rectangle-count
certificate.

Output: `runs/family-zero-surface-85-v2.json`.
