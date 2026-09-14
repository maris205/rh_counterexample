# Unknown-frequency blind-search gate

The first blind pass reads only the top FFT summaries from the (N=5\times10^7)
Mertens, `psi/theta`, and short-interval runs. It excludes frequencies within
0.75 of the five known Riemann zero ordinates and removes bins below
`t=2`, which are dominated by smooth finite-window trends. Remaining bins are
clustered within `Delta t=0.5` and counted by independent observable channel.

The output is `runs/blind-candidates-5e7.json`. It contains 11 residual
clusters but zero candidates meeting the minimum three-channel gate. Thus no
frequency was passed to the actual zeta verifier. This is a conservative
methodological result, not a zero-free theorem: the FFT summaries are a
candidate generator, not an exhaustive scan of the strip.

Repeating the gate with both `N=10^7` and `N=5\times10^7` inputs still gives
zero candidates (`runs/blind-candidates-multiN.json`), so the empty result is
not caused by using only one arithmetic scale. The companion report
`runs/blind-zeta-verification-multiN.json` records that no zeta evaluations
were scheduled.

The next blind-search expansion should use independent log grids and direct
demodulation rather than simply increasing FFT resolution. Any future
candidate still needs two (N) scales, all held-out cuts, control quantiles,
free-σ Newton refinement, and a certified local rectangle count.

That expansion has now been run in `MULTI_GRID_DEMOD.md`. The only residual
three-channel cluster was near `t=37.5`, but it drifted across endpoint trims
and lost most of its held-out score. It was rejected before any zeta call.
