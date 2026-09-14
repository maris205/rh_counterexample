# Stratified shuffle controls

The (t\approx37.5) residual was tested against controls that preserve more
local arithmetic structure than a global shuffle. At (N=10^6), eight
replicates used 50,000-point blocks and three trimmed log grids.

The real maximum (R^2) in (37\le t\le38) was `0.00504`. The empirical
control results were:

| control | mean max (R^2) | 95% quantile |
|---|---:|---:|
| block permutation | 0.00453 | 0.01024 |
| within-block permutation | 0.00576 | 0.01058 |

The residual fails both control quantiles. Within-block permutation is the
more conservative null because it retains local cumulative shape; block
permutation retains block distributions while disrupting long-range order.

Output: `runs/stratified-controls-1e6.json`.

The same test at (N=10^7), with 200,000-point blocks, gives real maximum
`R^2=0.00313`; the block-permutation and within-block 95% quantiles are
`0.01689` and `0.01214`, respectively. The weak residual is therefore also
rejected at the larger arithmetic scale. Output:
`runs/stratified-controls-1e7.json`.
