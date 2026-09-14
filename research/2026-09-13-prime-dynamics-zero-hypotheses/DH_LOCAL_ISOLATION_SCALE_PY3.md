# DH local isolation scale comparison

The combined path and shared-endpoint diagnostics were checked at two local
rectangle scales around the same refined DH root:

| half-width | positive Taylor path segments | minimum path lower | nominal winding | branch margin |
|---:|---:|---:|---:|---:|
| `0.01` | 256/256 at 64 segments/edge | positive | `1.0000000000000007` | `3.11028654401` |
| `0.001` | 64/64 at 16 segments/edge | `0.0011791396` | `1.0000000000000002` | `3.01720906799` |

The smaller box remains locally isolated, but independent endpoint-angle
intervals are still broad. This indicates that shrinking the rectangle alone
does not solve the phase-accumulation problem; correlated path enclosures and
certified derivative/remainder bounds are the next targets.
