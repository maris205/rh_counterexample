import unittest
import numpy as np
from euler_transfer_diagnostics_py3 import fit


class TransferTests(unittest.TestCase):
    def test_correct_envelope_predicts_heldout(self):
        u = np.linspace(0, 6, 200)
        y = .3 + .1*u + np.exp(.5*u)*np.cos(18*u+.7)
        matched = fit(u, y, 100, 110, 18., .5, 0.)
        constant = fit(u, y, 100, 110, 18., 0., 0.)
        self.assertGreater(matched['gain'], .999999)
        self.assertGreater(matched['gain'], constant['gain'])

    def test_holdout_cannot_change_coefficients(self):
        u = np.linspace(0, 6, 200)
        y = np.cos(18*u+.7)
        original = fit(u, y, 100, 110, 18., 0., 0.)
        y[100:] *= -3
        modified = fit(u, y, 100, 110, 18., 0., 0.)
        np.testing.assert_array_equal(original['coefficients'], modified['coefficients'])
        self.assertLess(modified['gain'], 0.)

    def test_constant_baseline_is_invalid(self):
        result = fit(np.linspace(0, 6, 200), np.ones(200), 100, 110, 18., 0., 0.)
        self.assertEqual(result['status'], 'INVALID')
        self.assertIsNone(result['gain'])


if __name__ == '__main__':
    unittest.main()
