"""Offline gate for the peak forecast (timing and magnitude with uncertainty)."""
import math
import unittest

import numpy as np

from enso_watch import peak


class EventPeakTest(unittest.TestCase):
    def test_finds_the_window_maximum(self):
        nb = {"1997-08": 0.9, "1997-09": 1.4, "1997-10": 1.9, "1997-11": 2.2,
              "1997-12": 2.6, "1998-01": 2.1, "1998-02": 1.6}
        pk = peak._event_peak(nb, 1997)
        self.assertEqual(pk["peak_ym"], "1997-12")
        self.assertEqual(pk["peak_value"], 2.6)

    def test_incomplete_window_is_skipped(self):
        nb = {"1997-11": 2.0, "1997-12": 2.2}  # fewer than 5 months
        self.assertIsNone(peak._event_peak(nb, 1997))


class ForecastPeakTest(unittest.TestCase):
    def _series(self):
        """Synthetic events peaking each December, with June warmth and warm water
        volume both scaled to the eventual peak, so the model has a real signal."""
        nino, wwv = [], []
        years = list(range(1990, 2011)) + [2011]
        for Y in years:
            peak_mag = 1.0 + 0.35 * ((Y - 1990) % 5)  # varies 1.0 to 2.4
            last_mm = 6 if Y == 2011 else 12          # the ongoing year ends in June
            for mm in range(1, last_mm + 1):
                dist = 12 - mm  # a ramp up through the year to a December peak (not cyclic)
                val = peak_mag * math.exp(-(dist ** 2) / (2 * 3.0 ** 2))
                nino.append({"ym": f"{Y}-{mm:02d}", "mean": round(val, 3)})
                wwv.append({"ym": f"{Y}-{mm:02d}", "anomaly": round(peak_mag if mm == 6 else 0.4, 3)})
        return nino, wwv

    def test_forecasts_timing_magnitude_and_uncertainty(self):
        nino, wwv = self._series()
        p = peak.forecast_peak(nino, wwv)
        self.assertTrue(p["available"])
        self.assertEqual(p["issue_month"], "2011-06")
        # timing: phase locked to the late-year window
        self.assertIn(p["timing"]["modal_month"], (11, 12, 1))
        # magnitude carries an out of sample uncertainty and an ordered band
        self.assertGreaterEqual(p["magnitude"]["sigma"], 0.0)
        self.assertLessEqual(p["magnitude"]["low"], p["magnitude"]["estimate"])
        self.assertGreaterEqual(p["magnitude"]["high"], p["magnitude"]["estimate"])
        self.assertEqual(p["magnitude"]["low"], round(p["magnitude"]["estimate"] - p["magnitude"]["sigma"], 2))
        # the estimate is never below what the event already reached
        self.assertGreaterEqual(p["magnitude"]["estimate"], p["observed_max"]["value"])
        # transparency: it names its closest historical analogs
        self.assertEqual(len(p["analogs"]), 3)
        self.assertGreaterEqual(p["n_train"], 15)

    def test_leave_one_out_error_is_positive_when_a_line_cannot_fit(self):
        X = np.array([[0.], [1.], [2.], [3.], [4.], [5.]])
        y = np.array([0.0, 1.0, 4.0, 9.0, 16.0, 25.0])  # quadratic: a line must miss
        self.assertGreater(peak._loo_rmse(X, y, 0.0), 0.0)

    def test_unavailable_when_too_short(self):
        nino = [{"ym": f"2000-{m:02d}", "mean": 0.1} for m in range(1, 13)]
        wwv = [{"ym": f"2000-{m:02d}", "anomaly": 0.1} for m in range(1, 13)]
        self.assertFalse(peak.forecast_peak(nino, wwv)["available"])


if __name__ == "__main__":
    unittest.main()
