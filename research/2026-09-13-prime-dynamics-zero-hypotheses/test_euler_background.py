import unittest
import numpy as np
import common_spectrum_v2 as core
import euler_background_batch_py3 as nuisance
from known_ordinates import known_ordinates
from test_common_spectrum_v2 import synthetic_cells


class NuisanceTests(unittest.TestCase):
    def test_empty_background_reproduces_original(self):
        cells=synthetic_cells(); frequencies=np.arange(16,20.01,.25)
        original=core.evaluate(cells,frequencies,4.6)
        result=nuisance.evaluate(cells,frequencies,(),4.6)
        self.assertEqual([c['t'] for c in original['candidates']],[c['t'] for c in result['selected']])
        np.testing.assert_allclose([c['joint_score'] for c in original['candidates']],
                                   [c['joint_score'] for c in result['selected']],atol=1e-10)

    def test_weak_tone_survives_joint_background_fit(self):
        cells=synthetic_cells(); background=known_ordinates(4,40,0)
        for c in cells:
            v=c.u-4.6
            common=sum(5*np.cos(t*v+.2) for t in background)
            c.y=np.column_stack([.1*v+common+.01*np.cos(18*v+phase) for phase in (.1,1.,2.,3.)])
        result=nuisance.evaluate(cells,np.arange(16,20.01,.25),background,4.6)
        self.assertEqual(result['selected'][0]['t'],18.)
        self.assertGreater(result['selected'][0]['joint_score'],.99999)

    def test_holdout_cannot_change_background_coefficients_or_selection(self):
        cells=synthetic_cells(); background=known_ordinates(4,40,0); scan=np.arange(16,20.01,.25)
        initial=nuisance.evaluate(cells,scan,background,4.6)
        coeff=nuisance.fit_cell(cells[0],18.,background,4.6)
        boundary=min(c.u[c.cut] for c in cells)
        for c in cells:
            c.y[c.u>=boundary]*=-10
        changed=nuisance.evaluate(cells,scan,background,4.6)
        changed_coeff=nuisance.fit_cell(cells[0],18.,background,4.6)
        self.assertEqual([r['t'] for r in initial['selected']],[r['t'] for r in changed['selected']])
        np.testing.assert_array_equal(coeff['train_coefficients'],changed_coeff['train_coefficients'])
        np.testing.assert_array_equal(coeff['baseline_train_coefficients'],changed_coeff['baseline_train_coefficients'])


if __name__=='__main__':
    unittest.main()
