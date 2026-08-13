"""Offline test of the official reference parsing, against the frozen fixtures."""

import os
import unittest

from enso_watch.official import build_official, parse_monthly_nino34, parse_oni_seasonal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTROL = os.path.join(ROOT, "fixtures", "cpc", "ersst5.nino.mth.91-20.ascii")
ONI = os.path.join(ROOT, "fixtures", "cpc", "oni.ascii.txt")


class MonthlyNino34Test(unittest.TestCase):
    def test_parses_the_nino34_anomaly_column(self):
        series = parse_monthly_nino34(CONTROL)
        # The fixture starts at 1950-01 and the Nino 3.4 anomaly is the last column.
        self.assertEqual(series[0], {"year": 1950, "month": 1, "anomaly_c": -1.99})
        # Latest captured month in the fixture.
        self.assertEqual(series[-1], {"year": 2026, "month": 6, "anomaly_c": 1.44})

    def test_header_and_blank_lines_skipped(self):
        series = parse_monthly_nino34(CONTROL)
        self.assertTrue(all("year" in r and "anomaly_c" in r for r in series))
        self.assertGreater(len(series), 900)  # ~76 years of months


class OniSeasonalTest(unittest.TestCase):
    def test_parses_seasonal_oni(self):
        series = parse_oni_seasonal(ONI)
        self.assertEqual(series[0], {"season": "DJF", "year": 1950, "oni": -1.32})
        self.assertEqual(series[-1], {"season": "MJJ", "year": 2026, "oni": 1.39})


class BuildOfficialTest(unittest.TestCase):
    def test_assembles_both_series_with_provenance(self):
        out = build_official(CONTROL, ONI, {"source": "ctrl"}, {"source": "oni"})
        self.assertEqual(out["monthly_nino34"]["provenance"], {"source": "ctrl"})
        self.assertEqual(out["oni_seasonal"]["provenance"], {"source": "oni"})
        self.assertGreater(len(out["monthly_nino34"]["series"]), 900)
        self.assertGreater(len(out["oni_seasonal"]["series"]), 900)


if __name__ == "__main__":
    unittest.main()
