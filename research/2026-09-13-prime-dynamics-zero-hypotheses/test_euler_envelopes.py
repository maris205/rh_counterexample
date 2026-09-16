import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
import common_spectrum_v2 as core
import euler_envelope_comparison_py3 as compare
from test_common_spectrum_v2 import synthetic_cells


class EnvelopeComparisonTests(unittest.TestCase):
    def test_constant_model_reproduces_original_detector(self):
        cells = synthetic_cells()
        frequencies = np.arange(16,20.01,.25)
        old = core.evaluate(cells,frequencies,4.6)
        new = compare.evaluate(cells,frequencies,compare.MODELS['constant'],4.6)
        self.assertEqual([r['t'] for r in old['candidates']],[r['t'] for r in new['selected']])
        np.testing.assert_allclose([r['joint_score'] for r in old['candidates']],
                                   [r['joint_score'] for r in new['selected']],atol=1e-10)

    def test_channel_envelopes_recover_exact_synthetic_signal(self):
        cells = synthetic_cells()
        for c in cells:
            v = c.u-4.6
            c.y = np.column_stack([.1*v + np.exp(beta*v)*np.cos(18*v+phase)
                                  for beta,phase in zip(compare.MODELS['channel_envelopes'],(.1,1.,2.,3.))])
        result = compare.evaluate(cells,np.arange(16,20.01,.25),compare.MODELS['channel_envelopes'],4.6)
        self.assertEqual(result['selected'][0]['t'],18.)
        self.assertGreater(result['selected'][0]['joint_score'],.999999)

    def test_any_holdout_change_cannot_change_frequency_selection(self):
        cells = synthetic_cells()
        frequencies = np.arange(16,20.01,.25)
        before = compare.evaluate(cells,frequencies,compare.MODELS['channel_envelopes'],4.6)
        boundary = min(c.u[c.cut] for c in cells)
        for cell in cells:
            cell.y[cell.u>=boundary] *= -100.
        after = compare.evaluate(cells,frequencies,compare.MODELS['channel_envelopes'],4.6)
        self.assertEqual([r['t'] for r in before['selected']],[r['t'] for r in after['selected']])

    def test_control_max_includes_both_models(self):
        self.assertEqual(compare.pooled_max({'constant':{'max_statistic':-.2},'adaptive':{'max_statistic':.8}}),.8)

    def test_atomic_write_retries_bounded_permission_error(self):
        with tempfile.TemporaryDirectory() as root:
            original = compare.batch.atomic_json
            calls = []
            def fail_once(path,obj):
                calls.append(1)
                if len(calls)==1:
                    raise PermissionError('simulated sharing violation')
                return original(path,obj)
            with patch.object(compare.batch,'atomic_json',side_effect=fail_once), patch.object(compare.time,'sleep'):
                compare.atomic(Path(root)/'progress.json',{'ok':True})
            self.assertEqual(len(calls),2)
            self.assertTrue((Path(root)/'progress.json').exists())


if __name__ == '__main__':
    unittest.main()
