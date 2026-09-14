# Independent log-grid demodulation check

`multi_grid_demod.py` tests whether the apparent common FFT buckets in the
Mertens, ψ, and θ channels survive a change of numerical window. It builds the
arithmetic arrays once, samples each cumulative signal on four independently
trimmed uniform grids in `log x`, and scans continuous angular frequency by a
two-column least-squares demodulator. The known Riemann ordinates are removed
from the blind-consensus stage.

The (N=10^7) run is in
[`multi-grid-demod-1e7-v2.json`](../../runs/multi-grid-demod-1e7-v2.json). The
grids used 1024, 1536, 2048, and 3072 samples with endpoint trims 0%, 2%, 5%,
and 10%; the scan was (4\le t\le40) with step 0.05. The derivative in
`log x` was used to suppress the cumulative-shape leakage seen in the earlier
Mertens experiments.

The known line frequencies still dominate each individual record: for example,
the Mertens scores at (t\approx14.1) are 0.145, 0.102, 0.078, and 0.056 as
the sample count increases. These are calibration peaks, not unknown-zero
evidence.

After removing neighborhoods of the first five known ordinates, the only
cross-grid/cross-channel cluster is a broad high-frequency feature around
(t\approx37.5):

* it spans 4 grids and all 3 channels, but its frequency wanders from 37.25 to
  37.60 under the endpoint trims;
* the largest (R^2) is 0.0225 on the untrimmed 1024-point grid and falls to
  0.005--0.015 on most independent windows;
* the cluster is therefore a weak finite-window/high-frequency residual, not a
  stable spectral atom.

No non-known frequency meets the stronger acceptance gate (tight frequency
spread, substantial held-out score, and two independent (N) values). In
particular, this run does **not** produce a candidate to send to a
free-σ ζ-refinement. It does provide the intended check: continuous
demodulation plus independent grids prevents a fixed FFT bin from being
mistaken for an arithmetic zero signal.

This remains a feature diagnostic. A zero claim would require direct
high-precision evaluation of the actual Riemann ζ function, free-σ Newton
refinement, and an argument-principle/interval count.
