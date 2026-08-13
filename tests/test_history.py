"""Deterministic gate for the backfill transform (history.daily_series).

Feeds the frozen January 2024 Nino 3.4 box fixture through the same box,
cosine weighted area-average, and 1991 to 2020 climatology used by the live
oracle, and pins the produced anomalies to their golden values at 3 decimals.
Offline: netCDF4 reads a local fixture, no network. This is criterion 1 of the
V1 run contract (the training dataset is proven deterministic on a fixture).
"""
import os
import unittest

from enso_watch.history import daily_series, monthly_series

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "fixtures", "oisst", "nino34_daily_sample_2024-01.nc")
CLIM = os.path.join(ROOT, "fixtures", "oisst", "nino34_climatology_1991-2020.nc")
MONTHLY_FIXTURE = os.path.join(ROOT, "fixtures", "oisst", "nino34_monthly_sample_2023-2024.nc")
MONTHLY_CLIM = os.path.join(ROOT, "fixtures", "oisst", "nino34_monthly_climatology_1991-2020.nc")


class HistoryTransformTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = daily_series(FIXTURE, CLIM)

    def test_one_row_per_day(self):
        self.assertEqual(len(self.rows), 31)
        self.assertEqual(self.rows[0]["date"], "2024-01-01")
        self.assertEqual(self.rows[-1]["date"], "2024-01-31")

    def test_golden_first_day(self):
        r = self.rows[0]
        self.assertEqual(r["nino34_anomaly_c"], 2.123)
        self.assertEqual(r["region_mean_sst_c"], 28.551)
        self.assertEqual(r["climatology_mean_c"], 26.429)
        self.assertEqual(r["baseline"], "1991-2020")

    def test_golden_mid_and_last(self):
        self.assertEqual(self.rows[14]["date"], "2024-01-15")
        self.assertEqual(self.rows[14]["nino34_anomaly_c"], 1.766)
        self.assertEqual(self.rows[-1]["nino34_anomaly_c"], 1.81)

    def test_anomaly_is_the_difference(self):
        # the contract's definition. The anomaly is rounded from the full precision
        # difference, while region and climatology are each rounded independently,
        # so the two can differ by up to one milli-degree of rounding. The invariant
        # is that they agree within that tolerance, not to the last bit.
        for r in self.rows:
            self.assertAlmostEqual(
                r["nino34_anomaly_c"],
                r["region_mean_sst_c"] - r["climatology_mean_c"],
                delta=0.0015,
            )

    def test_january_2024_is_a_strong_el_nino(self):
        # a sanity band, not a golden: the whole month sits well above +0.5 C
        self.assertTrue(all(r["nino34_anomaly_c"] > 1.0 for r in self.rows))


class MonthlyHistoryTransformTest(unittest.TestCase):
    """The monthly history path: the cadence the forecast model trains on."""

    @classmethod
    def setUpClass(cls):
        cls.rows = monthly_series(MONTHLY_FIXTURE, MONTHLY_CLIM)

    def test_one_row_per_month(self):
        self.assertEqual(len(self.rows), 24)
        self.assertEqual(self.rows[0]["month"], "2023-01")
        self.assertEqual(self.rows[-1]["month"], "2024-12")

    def test_golden_endpoints(self):
        self.assertEqual(self.rows[0]["nino34_anomaly_c"], -0.687)
        self.assertEqual(self.rows[0]["region_mean_sst_c"], 25.804)
        self.assertEqual(self.rows[0]["climatology_mean_c"], 26.491)
        self.assertEqual(self.rows[-1]["nino34_anomaly_c"], -0.63)

    def test_el_nino_peak_is_december_2023(self):
        # the real 2023-24 El Nino peaked in Dec 2023; our own number must find it
        peak = max(self.rows, key=lambda r: r["nino34_anomaly_c"])
        self.assertEqual(peak["month"], "2023-12")
        self.assertEqual(peak["nino34_anomaly_c"], 2.011)

    def test_anomaly_is_the_difference(self):
        for r in self.rows:
            self.assertAlmostEqual(
                r["nino34_anomaly_c"],
                r["region_mean_sst_c"] - r["climatology_mean_c"],
                delta=0.0015,
            )


if __name__ == "__main__":
    unittest.main()
