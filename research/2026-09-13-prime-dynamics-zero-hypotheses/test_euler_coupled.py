import unittest
import numpy as np
import euler_coupled_batch_py3 as model
import common_spectrum_v2 as core


class EulerIdentityTests(unittest.TestCase):
    def test_unit_weights_reproduce_arithmetic(self):
        struct = model.structure(1000)
        a, source = model.coefficients(struct, np.ones(len(struct[1])))
        actual = core.arithmetic_coefficients(1000)
        np.testing.assert_array_equal(a[1:], 1.)
        for key in source:
            np.testing.assert_allclose(source[key], actual[key], atol=1e-12)

    def test_inverse_and_log_derivative_identities(self):
        struct = model.structure(500)
        weights = 1 + .3 * np.cos(18 * np.log(struct[1]) + .7)
        a, source = model.coefficients(struct, weights)
        for n in range(1, 501):
            divisors = [d for d in range(1, n + 1) if n % d == 0]
            inverse = sum(a[d] * source['mu'][n // d] for d in divisors)
            logderiv = sum(source['lambda'][d] * a[n // d] for d in divisors)
            self.assertAlmostEqual(inverse, float(n == 1), places=10)
            self.assertAlmostEqual(logderiv, a[n] * np.log(n), places=10)

    def test_weight_controls_preserve_multiset_and_euler_identity(self):
        struct = model.structure(1000)
        primes = struct[1]
        weights = 1 + .1 * np.sin(np.log(primes))
        for mode in ('global', 'log_bin', 'block'):
            shuffled = model.shuffled_weights(primes, weights, mode, 1)
            np.testing.assert_allclose(np.sort(shuffled), np.sort(weights))
            a, source = model.coefficients(struct, shuffled)
            self.assertAlmostEqual(source['lambda'][4], a[4] * np.log(2))
            self.assertAlmostEqual(source['mu'][6], a[6])


if __name__ == '__main__':
    unittest.main()
