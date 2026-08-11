"""Unit tests for the load bearing helpers, exercising the paths the golden
fixtures cannot reach: cosine weighting, masked cell exclusion, and the leap day
climatology policy.
"""
import unittest

import numpy as np

from enso_watch.nino34 import _area_average, _climatology_index
from enso_watch.status import _phase, _strength


class AreaAverageTest(unittest.TestCase):
    def test_cosine_latitude_weighting(self):
        lat = np.array([0.0, 60.0])  # cos = 1 and 0.5
        field = np.ma.array([[2.0, 2.0], [4.0, 4.0]], mask=False)
        # (2*1 + 2*1 + 4*0.5 + 4*0.5) / (1 + 1 + 0.5 + 0.5) = 8/3
        self.assertAlmostEqual(_area_average(field, lat), 8.0 / 3.0, places=10)

    def test_masked_cells_excluded_from_both_sides(self):
        lat = np.array([0.0, 0.0])  # cos = 1 everywhere, equal weights
        field = np.ma.array(
            [[1.0, 2.0], [3.0, 4.0]], mask=[[False, False], [True, False]]
        )
        # the masked cell (value 3) leaves numerator and denominator: (1+2+4)/3
        self.assertAlmostEqual(_area_average(field, lat), 7.0 / 3.0, places=10)


class ClimatologyIndexTest(unittest.TestCase):
    def setUp(self):
        self.cmonth = np.array([2, 2, 3])
        self.cday = np.array([27, 28, 1])

    def test_normal_date(self):
        self.assertEqual(_climatology_index(self.cmonth, self.cday, 3, 1), 2)

    def test_feb29_falls_back_to_feb28(self):
        self.assertEqual(_climatology_index(self.cmonth, self.cday, 2, 29), 1)

    def test_missing_date_raises(self):
        with self.assertRaises(ValueError):
            _climatology_index(self.cmonth, self.cday, 6, 15)


class PhaseStrengthTest(unittest.TestCase):
    def test_phase_boundaries(self):
        self.assertEqual(_phase(0.5), "el_nino")
        self.assertEqual(_phase(0.49), "neutral")
        self.assertEqual(_phase(0.0), "neutral")
        self.assertEqual(_phase(-0.49), "neutral")
        self.assertEqual(_phase(-0.5), "la_nina")

    def test_strength_boundaries(self):
        self.assertEqual(_strength(0.49), "none")
        self.assertEqual(_strength(0.5), "weak")
        self.assertEqual(_strength(0.99), "weak")
        self.assertEqual(_strength(1.0), "moderate")
        self.assertEqual(_strength(1.49), "moderate")
        self.assertEqual(_strength(1.5), "strong")
        self.assertEqual(_strength(1.99), "strong")
        self.assertEqual(_strength(2.0), "very_strong")
        self.assertEqual(_strength(-1.6), "strong")  # magnitude, not sign


if __name__ == "__main__":
    unittest.main()
