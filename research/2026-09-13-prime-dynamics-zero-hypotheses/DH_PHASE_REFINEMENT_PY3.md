# Phase interval refinement (Python 3)

The first-order analytic-derivative phase diagnostic was rerun with uniform
edge refinements:

| segments per edge | all disks exclude 0 | phase uncertainty radius | winding interval |
|---:|---:|---:|---:|
| 16 | yes | 7.34887 | `[-0.16961, 2.16961]` |
| 32 | yes | 7.19764 | `[-0.14554, 2.14554]` |
| 64 | yes | 7.12377 | `[-0.13378, 2.13378]` |
| 128 | yes | 7.08725 | `[-0.12797, 2.12797]` |

The nominal winding remains 1 and every Taylor disk excludes zero. The slow
convergence shows that simply doubling the number of first-order segments will
not isolate the integer winding. The next useful step is a second-order Taylor
remainder or a global variation bound for the tangent direction; increasing
the mesh alone is inefficient. All rows remain non-certified diagnostics.
