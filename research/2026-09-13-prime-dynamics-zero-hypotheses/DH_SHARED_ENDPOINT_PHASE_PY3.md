# Shared-endpoint phase audit

The boundary phase calculation now reuses each endpoint once instead of adding
independent endpoint-angle errors to both adjacent segments. For the
`0.01 x 0.01` DH rectangle with 64 segments per edge:

- unique endpoints: `256`;
- nominal winding: `1.0000000000000007`;
- maximum absolute endpoint phase step: `0.03130610958` radians;
- minimum distance from the `+/- pi` branch ambiguity: `3.11028654401` radians;
- steps near branch ambiguity (<0.1 radians margin): `0`.

This is strong evidence that the branch choice is numerically stable and that
the previous wide interval came from repeated independent error addition. It is
still a diagnostic: endpoint/path enclosures must exclude zero and the branch
choice must be proven over each segment before this becomes an argument
principle certificate.

Output: `runs/dh-shared-endpoint-phase-py310-e64.json`.
