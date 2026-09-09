"""Numerical and persistence checks; no synthetic result is a zeta claim."""
import importlib.util
from fractions import Fraction
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'research/2026-09-09-gpu-gap-screen'))
sys.path.insert(0, str(ROOT / 'research/2026-09-09-gpu-wide-survey'))
sys.path.insert(0, str(ROOT / 'research/2026-09-08-zeta-global-search'))
import server
import gpu_screen as engine
import wide_scan
import zeta_de
from rectangle_count import count_rectangle


class Numerics(unittest.TestCase):
    def test_high_phase_cpu_against_100_digit_direct_trig(self):
        plan = server.read(ROOT / server.SURVEY / 'WIDE_PLAN.json')
        models = server.read(ROOT / 'research/2026-09-09-pc-gap-search/PLAN.json')['models']
        for model in models:
            patterns = engine.all_patterns(model['signs'])
            self.assertEqual(len(patterns), 70 if model['k'] == 3 else 11440)
            for rule in plan['rules']:
                cs, ds, _ = engine.phase_grid(model['support'], rule, '100000002097152', plan)
                result = engine.validate_precision(model, patterns, rule, '100000002097152', plan, cs, ds, 'cpu')
                self.assertLess(result['max_absolute_error'], 1e-11)

    def test_exact_high_coordinate_and_off_line_bounds(self):
        height = zeta_de.rational('100000000000000') + zeta_de.rational('0.000000000001')
        self.assertEqual(zeta_de.decimal_text(height), '100000000000000.000000000001')
        self.assertNotEqual(height, Fraction(float(height)))
        with self.assertRaisesRegex(ValueError, 'line exclusion'):
            zeta_de.optimize_box('0.5000000000000000000001', '0.6', '14', '15')

    def test_true_zeta_and_synthetic_counts_are_distinct(self):
        synthetic = count_rectangle('0.29', '0.31', '13.99', '14.01', func='synthetic_linear', max_seconds=5)
        self.assertEqual(synthetic['count'], 1)
        self.assertFalse(synthetic['off_line_certified'])
        known = count_rectangle('0.49', '0.51', '14.13', '14.14', max_seconds=10)
        self.assertEqual(known['count'], 1)
        self.assertFalse(known['off_line_certified'])
        empty = count_rectangle('0.59', '0.61', '14.13', '14.14', max_seconds=10)
        self.assertEqual(empty['count'], 0)
        self.assertFalse(empty['off_line_certified'])

    def test_selection_ties_and_missing_slots(self):
        plan = {'regions_per_anchor': 4, 'strata_per_anchor': 2}
        rows = [dict(anchor='1000', k=3, rule='A_min', region_index=i, base=str(1000+i),
                     selected_sources=[dict(source='original', bracket_index=(2 if i<2 else -1),
                                            grid_merit=(-.7 if i<2 else None))]) for i in range(4)]
        winners = wide_scan.select_winners(rows, plan)
        self.assertEqual(winners[0][1][0]['region_index'], 0)
        self.assertIsNone(winners[1][1])

    def test_snapshot_corruption_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve()
            file = directory / 'worker.py'
            file.write_text('original', encoding='utf-8')
            server.write(directory / 'RUN.json', {'source_sha256': {'worker.py': server.sha(file)}})
            file.write_text('changed', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'snapshot changed'):
                server.verify(directory)


if __name__ == '__main__':
    unittest.main()
