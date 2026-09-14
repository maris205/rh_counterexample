# Shared FFT-bin zeta refinement

The cross-channel spectra share four discrete log-grid bins near
`t=14.016, 14.385, 21.025, 25.080`. These values were passed directly to the
actual Riemann zeta function with free real part. For each bin we used four
seeds, `sigma=0.55,0.65,0.75,0.85`, 70 decimal digits, and damped complex
Newton refinement.

All 16 refinements converged to known critical-line zeros:

* the two bins near 14.1347 converge to
  `0.5 + 14.134725141734693... i`;
* the 21.025 bin converges to
  `0.5 + 21.022039638771555... i`;
* the 25.080 bin converges to
  `0.5 + 25.010857580145689... i`.

The machine-readable output is `runs/shared-bin-zeta-refine.json`. Every row
has `classification=CONVERGED_NEAR_CRITICAL_LINE` and
`certified_off_line_zero=false`. This is exactly the expected result for a
known-line calibration artifact; it supplies no off-line candidate.
