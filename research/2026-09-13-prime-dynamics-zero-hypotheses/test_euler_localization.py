import unittest
import numpy as np
import euler_frequency_localization_py3 as diagnostic
from test_common_spectrum_v2 import synthetic_cells


class LocalizationTests(unittest.TestCase):
    def test_fine_grid_localizes_synthetic_off_coarse_frequency(self):
        cells=synthetic_cells()
        for c in cells:
            c.y=np.column_stack([.1*c.u+np.cos(18.125*(c.u-4.6)+phase) for phase in (.2,1.,2.,3.)])
        frequencies=np.round(np.arange(16,20.001,.025),8)
        scan=diagnostic.training_scan(cells,frequencies,(0.,)*4,4.6)
        selected=diagnostic.nominations(frequencies,scan['joint'])
        self.assertEqual(frequencies[selected[0]],18.125)
        prediction=diagnostic.heldout(cells,float(frequencies[selected[0]]),(0.,)*4,4.6)
        self.assertGreater(prediction['joint_score'],.999999)

    def test_entire_training_curve_ignores_holdout(self):
        cells=synthetic_cells(); frequencies=np.arange(16,20.01,.25)
        before=diagnostic.training_scan(cells,frequencies,(0.,)*4,4.6)
        boundary=min(c.u[c.cut] for c in cells)
        for c in cells:
            c.y[c.u>=boundary]+=1234
        after=diagnostic.training_scan(cells,frequencies,(0.,)*4,4.6)
        np.testing.assert_array_equal(before['gains'],after['gains'])
        self.assertLess(after['support_max'],after['boundary'])


if __name__=='__main__':
    unittest.main()
