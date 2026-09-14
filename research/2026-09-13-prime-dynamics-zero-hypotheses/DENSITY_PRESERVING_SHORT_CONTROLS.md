# Density-preserving short-interval controls

This experiment keeps the number of observed primes in each logarithmic
`x`-bin fixed and resamples the occupied integer positions uniformly within
that bin. It is designed to test whether a candidate frequency survives after
coarse local prime density has been retained but exact arithmetic ordering has
been removed.

The control is deliberately modest. It is an empirical surrogate, not a
probability model for primes and not a theorem-level null hypothesis. Passing
or failing its quantiles cannot certify or disprove RH.

## Configuration

The runs use the short-interval power window (`h=x^1/2`), a fixed-log window
(`log(1+h/x)=0.5`), and normalized consecutive-prime gaps. Signals are
converted to local log increments before demodulation. The target is the
previous residual band `t=37.5`, with a `37 <= t <= 38` scan for the window
score.

## Results

| run | real target consensus min $R^2$ | surrogate q95 | real window consensus min $R^2$ | surrogate window q95 |
|---|---:|---:|---:|---:|
| $N=10^6$, 64 bins | 2.32e-6 | 2.67e-5 | see JSON | see JSON |
| $N=10^7$, 128 bins | 3.97e-6 | 7.87e-6 | 1.99e-5 | 2.85e-5 |

Changing the density partition gives the same decision at $N=10^7$:

| log bins | real target min $R^2$ | surrogate q95 |
|---:|---:|---:|
| 32 | 3.97e-6 | 4.88e-6 |
| 128 | 3.97e-6 | 7.87e-6 |
| 256 | 3.97e-6 | 7.63e-6 |

An additional $N=5\times10^7$ run (256 bins, four surrogates) gives real
target consensus $2.84\times10^{-6}$ versus q95 $4.20\times10^{-6}$. Its
post-selected window maximum is marginally above the small-replicate q95
($2.14\times10^{-5}$ versus $2.04\times10^{-5}$); this is precisely why the
pre-registered target and cross-channel minimum, rather than a scanned maximum,
are used for promotion decisions.

For $N=10^7$, the three target-channel values were approximately

* power-window: $9.03\times10^{-4}$;
* fixed-log: $3.97\times10^{-6}$;
* gap: $1.51\times10^{-5}$.

The minimum across channels is therefore controlled by the fixed-log channel;
it is below the density-preserving surrogate 95th percentile. The scanned
window score is also below its surrogate q95. No candidate is promoted.

## Reproducibility

```powershell
& "D:\\26-aimath\\rh_counterexample\\.venv\\Scripts\\python.exe" `
  research/2026-09-13-prime-dynamics-zero-hypotheses/density_preserving_short_controls.py `
  --n 10000000 --samples 2048 --reps 8 --log-bins 128 `
  --target 37.5 --window 37,38 `
  --output runs/density-preserving-short-1e7.json
```

Machine-readable outputs:

* [density-preserving-short-1e6.json](../../runs/density-preserving-short-1e6.json)
* [density-preserving-short-1e7.json](../../runs/density-preserving-short-1e7.json)

The result supports the current conservative decision: the $t\approx37.5$
residual is not a stable cross-channel arithmetic feature under this additional
local-density control. It should not be passed to a zeta root finder.
