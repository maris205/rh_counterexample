# A1-PILOT-002: bounded rectangle-count audit

Frozen 2026-09-16 before running this protocol. Direction `RC:A1`; follow-up to
A1-PILOT-001's initial-condition dependence. Question: can the existing rigorous
counter decide a small actual-zeta region without Newton seeds?

## Fixed jobs and stopping conditions

- Target closed rectangle: `[0.5001, 0.70] x [10010, 10011]`, wholly right of
  the critical line. The strip between .5 and .5001 is NOT included.
- Comparison rectangle: `[0.49, 0.51] x [10010, 10011]`, crossing the line and
  containing the two numerical endpoints of the preceding pilot. A count of
  two is a consistency check, not a proof of either endpoint's exact location.
- Repeat each rectangle independently at 40 and 70 decimal digits: four jobs.
- Maximum subdivision depth 26, maximum evaluations 30000, soft wall budget
  60 seconds per count. Time is checked before each function evaluation, so a
  single library call can exceed that budget. No automatic larger budget or
  rectangle changes. All jobs are serial under an output-directory lock.
- Before the four jobs, run the seven existing fixtures from
  `certification/run_checks.py` under python-flint 0.9.0 (old records used 0.8.0).
  Add rejection checks for floating-point coordinates and invalid rectangles.
  These are calibration repeats for the present runtime, not new search windows.
- Preserve each subtask JSON, immutable config/source/runtime fingerprint,
  atomic progress, summary and Markdown report. An interrupted count may be
  rerun; terminal artifacts are retained and never silently retried.
- Runtime: Python 3.14.3 because the requested Python 3.10 is unavailable.

## Audit of the reused counter

The implementation is `research/2026-09-08-zero-lab/certification/rectangle_count.py`.
It is reused without changing its mathematical decisions:

1. Exact decimal strings become rational coordinates. Floats are rejected.
2. The boundary is a closed, counterclockwise rectangle; a region containing
   the zeta pole at 1 is rejected. Zeta is analytic elsewhere in the region.
3. Each accepted segment has a finite convex acb rectangle enclosing the image
   of the entire input segment, and that image rectangle excludes zero.
4. Such a convex image lies in an open half-plane avoiding zero. A continuous
   argument branch on it has range less than pi, so the true argument change
   equals the endpoint quotient's principal argument when the computed interval
   is strictly inside (-pi,pi).
5. Summing rigorous argument intervals and dividing by an enclosure of 2*pi
   gives an interval containing the integer winding number. `unique_fmpz()`
   must find exactly one integer; the pole-free argument principle then counts
   zeros with multiplicity. An unresolved enclosure never becomes count zero.

The wrapper additionally checks exact segment continuity, membership of every
segment in the correct rectangle edge, counterclockwise orientation, closure,
accepted-segment counts and restored precision context. This structural check
does not replace the interval computations in the counter.

Primary references checked: [acb rectangular enclosures and argument](https://python-flint.readthedocs.io/en/latest/acb.html),
[arb and unique integer extraction](https://python-flint.readthedocs.io/en/latest/arb.html),
and [zeta's analytic continuation and pole](https://dlmf.nist.gov/25.2).
The preexisting detailed argument is in
[RECTANGLE_CERTIFICATION.md](../2026-09-08-zero-lab/certification/RECTANGLE_CERTIFICATION.md).

## Interpretation

- All smoke fixtures must match their declared certified/rejected/unresolved
  outcomes before main work begins.
- If both target counts are certified zero, both comparisons are certified two,
  and structural checks pass: END this local question at RC:E1. A zero count
  plus a certified zero-free boundary excludes zeros from the exact CLOSED
  target rectangle. It does not exclude the whole height band or RH counterexamples.
- Any unresolved main count, discrepancy, failed calibration or exception:
  HOLD, count undecided where appropriate; archive the exact reason.
- A positive off-line certified count: HOLD for independent reproduction and
  targeted review, not automatic promotion of the project to RC:E2.
- Library value/argument intervals saved as display strings are an audit record,
  not a stand-alone formal proof object. The computer-assisted conclusion depends
  on the audited algorithm and FLINT/Arb implementation, not on a proof assistant.

No new broad scan or automatic follow-up is part of this protocol.
