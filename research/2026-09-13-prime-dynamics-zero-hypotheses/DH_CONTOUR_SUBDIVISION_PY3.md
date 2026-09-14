# Davenport--Heilbronn contour subdivision (Python 3)

`dh_contour_subdivision_py3.py` evaluates small complex boxes on the four
edges of the known DH root rectangle using the Arb-backed
Euler--Maclaurin prototype.

For the rectangle centered at

```text
0.8085171824566373855533519606 + 85.69934848537759217192926771 i
```

with half-widths `0.01` in both coordinates:

| boxes per edge | boundary boxes | boxes containing 0 | midpoint winding |
|---:|---:|---:|---:|
| 16 | 64 | 0 | 1 |
| 64 | 256 | 0 | 1 |

The two JSON outputs are `runs/dh-contour-subdivision-py3-e16.json` and
`runs/dh-contour-subdivision-py3-e64.json`.

This is not yet a rigorous argument-principle certificate. The box evaluator
has an explicit Euler--Maclaurin remainder bound, but interval argument
accumulation and independent validation of the remainder inequality are still
needed. The correct status is therefore `NONCERTIFIED_SUBDIVISION`.
