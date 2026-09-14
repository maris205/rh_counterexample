# DH long batch v2 (Python 3)

`dh_long_batch_py3_v2.py` is a resumable, failure-isolated driver for the
Davenport--Heilbronn contour subdivision audit.  It is designed for a desktop
run lasting tens of minutes to several hours rather than an interactive
smoke test.

The default `long` profile has 100+ configurations.  It combines four
rectangle half-widths (`0.02`, `0.01`, `0.005`, `0.002`, with an additional
high-order `0.001` sweep), edge subdivisions up
to 4096, and several Euler--Maclaurin `(N,M)` pairs on the tight rectangles.
Every configuration runs in a separate Python 3 process.  A timeout, FLINT
exception, or launch failure is written to `progress.json` and the next
configuration starts automatically.

## Start a long run

From the repository root, use Python 3.10 explicitly:

```powershell
py -3.10 research/2026-09-13-prime-dynamics-zero-hypotheses/dh_long_batch_py3_v2.py `
  --profile long `
  --output-dir runs/dh-long-batch-py3-v2 `
  --timeout 3600
```

The process can be stopped with Ctrl-C or a machine restart.  Re-run the same
command afterwards; valid completed JSON files are detected by their
configuration and reported as `SKIPPED_EXISTING`.  An optional prefix is
useful for staged runs:

```powershell
py -3.10 .../dh_long_batch_py3_v2.py --profile long --start 40 --max-jobs 20
```

The output directory contains:

* `manifest.json` and `manifest.sha256`: immutable task plan and hash;
* one `job-*.json` per completed child evaluation;
* `progress.json`: atomically rewritten after every task;
* `summary.json`: final status and counts.

The child status remains `NONCERTIFIED_SUBDIVISION` even when every boundary
box excludes zero and the sampled midpoint winding is one.  This batch is a
stability and implementation audit; it does not provide a rigorous
argument-principle certificate.  In particular, interval phase accumulation
and an independently proved Hurwitz remainder bound are still separate gates.

The small `smoke` profile is useful for verifying the Python 3 environment:

```powershell
py -3.10 .../dh_long_batch_py3_v2.py --profile smoke `
  --output-dir runs/dh-long-batch-py3-v2-smoke --timeout 120
```
