"""Offline gate for the forecast skill machinery (metrics, baselines, walk forward).

The load bearing test here is the leakage guard: over a synthetic series where
every value equals its index, persistence at lead L must produce a constant error
of exactly L, which is only possible if the forecaster never saw the future. A
leak would shrink the error toward zero and the test would fail loudly.
"""
import math
import unittest

from enso_watch import skill


class MetricsTest(unittest.TestCase):
    def test_rmse_known(self):
        self.assertAlmostEqual(skill.rmse([(1.0, 1.0), (2.0, 4.0)]), math.sqrt(2.0), places=10)

    def test_rmse_empty_is_none(self):
        self.assertIsNone(skill.rmse([]))

    def test_acc_perfect_positive(self):
        self.assertAlmostEqual(skill.acc([(1, 2), (2, 4), (3, 6)]), 1.0, places=10)

    def test_acc_perfect_negative(self):
        self.assertAlmostEqual(skill.acc([(1, -1), (2, -2), (3, -3)]), -1.0, places=10)

    def test_acc_constant_forecast_is_zero_not_crash(self):
        # climatology forecasts a constant zero: no variance, reported as no skill
        self.assertEqual(skill.acc([(5, 1), (5, 2), (5, 3)]), 0.0)


class BaselineTest(unittest.TestCase):
    def test_persistence_returns_last(self):
        self.assertEqual(skill.persistence([1.0, 2.0, 3.5], 2), 3.5)

    def test_climatology_returns_zero(self):
        self.assertEqual(skill.climatology([1.0, 2.0, 3.5], 4), 0.0)


class WalkForwardLeakageTest(unittest.TestCase):
    def test_no_future_leakage_via_index_series(self):
        values = list(range(10))  # value == index
        pairs = skill.walk_forward(values, skill.persistence, lead=3, min_train=1)
        # every forecast is the issue value i, every actual is i+3: error is exactly -3
        self.assertEqual(len(pairs), 7)
        self.assertTrue(all(a - f == 3 for f, a in pairs))
        self.assertAlmostEqual(skill.rmse(pairs), 3.0, places=10)
        self.assertAlmostEqual(skill.acc(pairs), 1.0, places=10)

    def test_min_train_shrinks_the_window(self):
        values = list(range(10))
        pairs = skill.walk_forward(values, skill.persistence, lead=1, min_train=5)
        # issues from index 4 to 8 inclusive: 5 pairs
        self.assertEqual(len(pairs), 5)

    def test_lead_below_one_raises(self):
        with self.assertRaises(ValueError):
            skill.walk_forward([1, 2, 3], skill.persistence, lead=0, min_train=1)


class EvaluateTest(unittest.TestCase):
    def test_board_shape_and_climatology_has_no_skill(self):
        values = [math.sin(i / 6.0) for i in range(200)]
        board = skill.evaluate(values, leads=(1, 3), min_train=24)
        self.assertEqual(set(board), {"persistence", "climatology"})
        self.assertEqual(set(board["persistence"]), {1, 3})
        for lead in (1, 3):
            self.assertEqual(board["climatology"][lead]["acc"], 0.0)
            self.assertGreater(board["persistence"][lead]["n"], 0)


if __name__ == "__main__":
    unittest.main()
