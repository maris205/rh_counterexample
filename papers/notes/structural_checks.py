"""Exact small witnesses for the paper audit; these are NOT RH counterexamples.

Only Python's standard library is required. Analytic proofs and scope limitations
are in audit-paper-4.md and RESEARCH_DIRECTION.md. Original simulations are not run.
"""
from fractions import Fraction as Q
from pathlib import Path
import json


def mm(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(len(b)))
             for j in range(len(b[0]))] for i in range(len(a))]


def tr(a):
    return sum(a[i][i] for i in range(len(a)))


def transpose(a):
    return [list(r) for r in zip(*a)]


def det3(a):
    return (a[0][0] * (a[1][1]*a[2][2] - a[1][2]*a[2][1])
            - a[0][1] * (a[1][0]*a[2][2] - a[1][2]*a[2][0])
            + a[0][2] * (a[1][0]*a[2][1] - a[1][1]*a[2][0]))


def charpoly3(a):
    """Coefficients of det(z I-A), descending powers, exactly."""
    t = tr(a)
    return [Q(1), -t, (t*t-tr(mm(a, a)))/Q(2), -det3(a)]


def mean_matrix(ms):
    n = len(ms[0])
    return [[sum(Q(m[i][j]) for m in ms)/len(ms)
             for j in range(n)] for i in range(n)]


def ols(points):
    n = len(points)
    mx = sum(x for x, _ in points)/n
    my = sum(y for _, y in points)/n
    a = sum((x-mx)*(y-my) for x, y in points) / sum((x-mx)**2 for x, _ in points)
    b = my-a*mx
    sse = sum((a*x+b-y)**2 for x, y in points)
    return a, b, sse


def run():
    # A completely unrelated nonlinear target also has zero fitted intercept
    # after equally weighted sign pairing.
    positive = [(Q(1), Q(1)), (Q(2), Q(8)), (Q(3), Q(27))]
    signed = positive + [(-x, -y) for x, y in positive]
    a, b, sse = ols(signed)
    assert b == 0 and sse > 0

    # All three are nonnegative row-stochastic permutation matrices.
    B = [[0, 1, 0], [1, 0, 0], [0, 0, 1]]
    C = [[1, 0, 0], [0, 0, 1], [0, 1, 0]]
    A = transpose(mm(B, C))
    identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    abc = mm(mm(A, B), C)
    acb = mm(mm(A, C), B)
    assert all(sum(r) == 1 and min(r) >= 0 for m in [A, B, C] for r in m)
    assert mean_matrix([A, B, C]) == mean_matrix([A, C, B])
    assert abc == identity and acb != identity
    assert charpoly3(abc) == [1, -3, 3, -1]
    assert charpoly3(acb) == [1, 0, 0, -1]

    # Angles measured in units of pi, sorted in the upper half-plane.
    theta = [Q(1, 100), Q(1, 10), Q(2, 5), Q(7, 10), Q(99, 100)]
    phi = [theta[0]]
    wraps = []
    for left, right in zip(theta, theta[1:]):
        delta = right-left
        nwrap = (delta+1)//2
        wraps.append(nwrap)
        phi.append(phi[-1]+delta-2*nwrap)
    assert phi == theta and all(w == 0 for w in wraps)

    # A representative exact witness for the analytic first-return obstruction.
    # The proof in the report works for every u>1 and x<0 sufficiently near 0.
    u, x = Q(15437, 10000), Q(-1, 1000000)
    f = lambda z: 1-u*z*z
    first, second = f(x), f(f(x))
    derivative = 4*u*u*x*(1-u*x*x)
    assert x < 0 < first and second < 0 and abs(derivative) < 1

    return {
        "scope": "Exact witnesses for model/inference defects, not a zeta zero search or RH disproof",
        "symmetric_regression": {"slope": str(a), "intercept": str(b), "sse": str(sse)},
        "time_order": {"A": A, "B": B, "C": C, "ABC": abc, "ACB": acb,
                       "ABC_charpoly": [str(c) for c in charpoly3(abc)],
                       "ACB_charpoly": [str(c) for c in charpoly3(acb)],
                       "same_arithmetic_average": True},
        "upper_halfplane_unwrap": {"theta_over_pi": list(map(str, theta)),
                                    "phi_over_pi": list(map(str, phi)), "wraps": wraps},
        "first_return": {"u": str(u), "x": str(x), "return_time": 2,
                         "absolute_derivative": str(abs(derivative)), "below_one": True},
        "all_exact_assertions_passed": True,
    }


if __name__ == "__main__":
    result = run()
    destination = Path(__file__).with_name("structural_checks.json")
    destination.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
