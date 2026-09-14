# Stratified and local-density shuffle controls

This experiment adds two empirical controls to the continuous demodulation
scan. They are intended to be more informative than a single global shuffle
while remaining explicitly heuristic:

* **block permutation** partitions the coefficient sequence into blocks and
  permutes whole blocks. Every block's multiset, zero density, and weighted
  sum is retained, but the block order is destroyed;
* **within-block shuffle** shuffles values inside each block. Each block keeps
  its exact multiset and therefore its local count/density and weighted sum,
  while fine phase ordering is destroyed.

The signal is formed on a uniform log-`x` grid from the cumulative
Mertens/psi/theta sequence, followed by a local log increment. The scan covers
`4 <= t <= 40` and excludes the first five known Riemann ordinates when the
blind maximum is reported. A q95 is only an empirical finite-sample quantile
of the named transformation; it is not a probabilistic null model and cannot
certify a zeta zero.

## Run

The reproducible smoke run used `N=10^6`, 1024 log-grid samples, three endpoint
trims (`0, 0.05, 0.10`), block size `100000`, and eight repetitions per
channel/method/grid:

```powershell
& "D:\26-aimath\rh_counterexample\.venv\Scripts\python.exe" `
  research/2026-09-13-prime-dynamics-zero-hypotheses/stratified_shuffle_control.py `
  --n 1000000 --samples 1024 --phases 0,0.05,0.1 `
  --block-size 100000 --reps 8 --t-step 0.1 `
  --output runs/stratified-control-1e6.json
```

Raw output: [stratified-control-1e6.json](../../runs/stratified-control-1e6.json).

## Results

The observed score at `t=37.5` is between `0.0147` and `0.0198` across
channels and trims. The largest blind peak is still the known critical-line
frequency near `t=14.1` (which is excluded from the blind interpretation).
After exclusion, the largest observed blind value is only `0.0231`.

At the untrimmed grid (`phase=0`), the empirical q95 values were:

| channel | global shuffle q95 at 37.5 | block permutation q95 | within-block q95 | observed at 37.5 |
|---|---:|---:|---:|---:|
| Mertens | 0.00980 | 0.00588 | 0.01007 | 0.01717 |
| psi | 0.01136 | 0.01416 | 0.00843 | 0.01852 |
| theta | 0.01047 | 0.01264 | 0.00725 | 0.01982 |

The apparent exceedances at `t=37.5` do not constitute evidence for a zero:
they are weak, change with endpoint trimming, and are not a frequency that
has passed the multi-`N`, multi-grid, cross-channel, and independent-zeta
gates. The blind-top q95 values are generally `0.022`–`0.035`, so the
observed residuals are well inside the control envelope once the full scan is
considered.

The result supports using both local-density controls in the next blind run.
It does **not** select one control as mathematically canonical: preserving
block sums can also preserve part of a cumulative finite-window shape, while
whole-block permutation can be too destructive. Both should therefore be
reported together.

## Larger scale check

The same panel was repeated at `N=10^7`, with block size `10^6` and the same
eight repetitions and three trims. Raw output:
[stratified-control-1e7.json](../../runs/stratified-control-1e7.json).
At phase zero the observed `t=37.5` scores were `0.01732` (Mertens),
`0.01982` (psi), and `0.02103` (theta). The corresponding q95 values were:

| channel | global | block permutation | within-block |
|---|---:|---:|---:|
| Mertens | 0.00701 | 0.01687 | 0.00827 |
| psi | 0.00807 | 0.00516 | 0.01022 |
| theta | 0.00529 | 0.00951 | 0.00595 |

The small Mertens excess over the block-permutation q95 disappears as a
cross-channel claim: psi and theta do not show a matching excess, and the
scores move with endpoint trimming. The largest blind score remains in the
known-ordinate neighbourhood or is below the corresponding full-scan control
envelope. Thus this larger run still produces no admissible unknown-frequency
candidate.
