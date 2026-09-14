# Third-order Taylor diagnostic

The third-order centre expansion was tested on the 64 boundary segments of
the `0.01 x 0.01` DH rectangle. All 64 lower bounds remain positive; the
minimum is `0.011769737816714674`, and the winding interval is
`[-0.12327832, 2.12327832]`.

The third-order term changes the interval only in the seventh decimal place
relative to the second-order diagnostic. Thus the dominant uncertainty is not
the local Taylor truncation; it is the non-certified derivative supremum and
the independent phase-interval accumulation. Further Taylor order is
deprioritized in favor of a true Arb derivative/remainder enclosure.
