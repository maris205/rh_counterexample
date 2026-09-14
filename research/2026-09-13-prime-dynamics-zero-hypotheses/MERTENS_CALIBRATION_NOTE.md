# Mertens calibration note (2026-09-13)

This note records the current method gate for the reciprocal-zeta channel.
It is a calibration report, not a claim about an off-line zero.

## What was tested

The script `mertens_dynamics.py` computes the Möbius function by a linear
sieve, samples (M(x)/\sqrt{x}) uniformly in (u=\log x), and compares a
fixed known ordinate (t_1=14.1347251417\ldots) with shuffled controls. The
increment signal (d/du[M(e^u)/e^{u/2}]) is used because cumulative Mertens
values retain block-sum shape under local shuffles.

## Findings

* The cumulative fixed-frequency values near (R^2=0.52\) at (N=10^7) and
  (R^2=0.54\) at (N=5\times 10^7) are control-leakage warnings. Small block
  shuffles reproduce them and are not independent nulls.
* At (N=5\times 10^7), eight-replicate large-block controls at the default
  two-thirds split give real increment (R^2=0.03298), versus (0.00812) for
  (10^6)-blocks and (0.00430) for (5\times10^6)-blocks.
* A multi-cut check at (N=10^7) gives real increment (R^2\approx0.055) at
  cuts 0.55, 0.67, and 0.80. However, the (10^5)-block control reaches
  (R^2\approx0.050) at cut 0.80. The apparent separation is therefore not a
  significance result and cannot justify a zeta-zero interpretation.

The latest machine-readable result is
`runs/mertens-split-1e7.json`; the larger eight-replicate run is
`runs/mertens-null-5e7-v2.json`.

At `N=5*10^7`, the unconstrained FFT bins near `14.016` and `14.385` bracket
the known ordinate `14.134725...`; the neighboring `psi`/`theta` spectra show
the same bins because they share the log-grid and cumulative-trend geometry.
This bin alignment is a resolution artifact until an independently fitted
frequency survives window, cut-point, and control changes.

## Decision gate

Mertens is retained as a calibration and null-design channel. Unknown-frequency
search remains disabled until the same statistic survives multiple (N), cut
points, and independent arithmetic channels. The next channel is
\(\Lambda/\psi\), followed by short-interval and gap-word observables.
