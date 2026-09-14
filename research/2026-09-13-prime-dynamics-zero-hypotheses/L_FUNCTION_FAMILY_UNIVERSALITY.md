# A family-level view of the critical line

## Research question

Which structural ingredients force, or merely suggest, a zero line
`Re(s)=1/2`? The useful question is not whether every zeta-like function obeys
an RH analogue. It is which axioms survive when one passes from a negative
control to a positive control.

## Axiom ladder

The properties should be treated as separate axes rather than one linear scale:

1. meromorphic continuation and a Riemann-type functional equation;
2. a Dirichlet series with controlled coefficients;
3. coefficient multiplicativity and an Euler product;
4. Ramanujan-type coefficient bounds and analytic continuation in a critical
   strip;
5. positivity or a Weil-style explicit-formula quadratic form;
6. a self-adjoint spectral realization.

Functional equation alone is too weak. Davenport--Heilbronn-type Dirichlet
series and some Epstein zeta functions have zeta-like continuation and symmetry
but off-line zeros. This is the negative-control class for our symbol models:
periodic/Hurwitz combinations can have rich zero patterns without implying
anything about the Riemann zeta function.

Standard Dirichlet and automorphic L-functions supply an intermediate class:
they have Euler products and functional equations, and their generalized RH is
expected but not known in general. They are useful positive controls, not
known counterexamples.

Function-field zeta functions supply a proven positive class, where the
analogue of RH follows from geometric/spectral positivity. Beurling-type
generalized-prime systems provide stress tests showing that prime-counting
asymptotics alone do not force a critical line.

## Where our k3/k5 models sit

The current symbol sequences are periodic and have exact finite Hurwitz-zeta
representations. After gcd-layer decomposition they can be compared with
Dirichlet L-combinations, but the shifted sequence is generally not
multiplicative and has no automatic Euler product. Hence their zeros belong to
the negative-control side of the ladder. An off-line zero of the model would
be evidence about the model's dynamics, not a ζ counterexample.

That makes them valuable: we can ask which dynamical statistics distinguish a
function with symmetry only from one with symmetry plus Euler product or
positivity.

## Common diagnostics for a family benchmark

For each family `F`, record:

* functional-equation residual;
* Euler-product/multiplicativity defect of its coefficients;
* coefficient growth and Ramanujan-type defect;
* positivity defect of a smoothed explicit-formula quadratic form;
* zero density away from the symmetry line;
* prime/gap-symbol dynamical statistics.

Use the same log-time features as in the Mertens extension and fit a shared
spectral model. The output is a structural map, not a classifier claiming RH.

## First comparison panel

* **Riemann zeta:** target object; RH is unresolved.
* **k3/k5 periodic Hurwitz combinations:** our negative controls.
* **Davenport--Heilbronn and selected Epstein zeta functions:** symmetry with
  known off-line behavior.
* **Primitive Dirichlet L-functions:** Euler product and functional equation;
  GRH remains conjectural.
* **Function-field zeta functions:** proven RH analogue.
* **Beurling generalized primes:** tunable prime-distribution stress tests.

The first computational question is whether the same “fractal” or recurrence
features occur in both positive and negative classes. If they do, those
features are dynamical artifacts rather than evidence for the ζ critical line.

## Falsifiable outcomes

* If symmetry-only families and Euler-product families have indistinguishable
  features, the current prime-dynamics signal is too weak to explain `1/2`.
* If only the positive/spectral classes suppress off-line atoms, add a
  positivity or self-adjointness observable to the ζ search.
* If k3/k5 share an off-line atom with a genuine Euler-product family, test
  whether it is a common explicit-formula frequency or only a finite-window
  alias.
* If the ζ data remain line-confined while the negative controls do not, that
  is useful evidence for a structural mechanism even without a proof.

## Immediate implementation

1. Finish the Mertens and short-interval channels.
2. Add a small Davenport--Heilbronn/Epstein negative-control dataset.
3. Add one Dirichlet L positive-control family and one function-field toy
   family with known line behavior.
4. Run identical basin, Newton, and zero-density diagnostics on all families.
5. Only then interpret a symbol-sequence anomaly as evidence about ζ.

The first lightweight fixture for items 3--4 is now available in
[`family_control_panel.py`](family_control_panel.py), with its interpretation
and limitations documented in [`FAMILY_CONTROL_PANEL.md`](FAMILY_CONTROL_PANEL.md).
It covers primitive `chi4`, real quadratic `chi5`, and the exact curve
`E/F_7: y^2=x^3+x`. The Davenport--Heilbronn row remains disabled until its
functional equation and an argument-principle certificate are implemented.

For that future fixture, use the standard parameter
`kappa=(sqrt(10-2*sqrt(5))-2)/(sqrt(5)-1)`, approximately
`0.2840790438404123`. A superficially similar expression with
`sqrt(10-sqrt(5))` is a different periodic combination and must not be used
to validate the reported off-line zero.
