"""Offline gate for the warm water volume parser (wwv.parse_wwv).

Parses the frozen 1997 to 1998 PMEL slice (a textbook precursor build up and
collapse) and pins the values, so a silent change in the source format or the
parser is caught. Offline: reads a local fixture, no network.
"""
import os
import unittest

from enso_watch.wwv import parse_wwv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "fixtures", "pmel", "wwv_sample.dat")


class WwvParseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(FIXTURE, encoding="utf-8") as fh:
            cls.rows = parse_wwv(fh.read())

    def test_skips_header_and_keeps_every_month(self):
        self.assertEqual(len(self.rows), 24)
        self.assertEqual(self.rows[0]["month"], "1997-01")
        self.assertEqual(self.rows[-1]["month"], "1998-12")

    def test_golden_values_in_1e14_units(self):
        first = self.rows[0]
        self.assertEqual(first["wwv_volume_1e14_m3"], 26.919)
        self.assertEqual(first["wwv_anomaly_1e14_m3"], 1.635)
        self.assertEqual(self.rows[-1]["wwv_anomaly_1e14_m3"], -2.663)

    def test_precursor_peak_leads_the_1997_el_nino(self):
        # the warm water built to its peak in spring 1997, ahead of the late-1997
        # El Nino peak: the two season lead the model will learn from
        peak = max(self.rows, key=lambda r: r["wwv_anomaly_1e14_m3"])
        self.assertEqual(peak["month"], "1997-04")
        self.assertEqual(peak["wwv_anomaly_1e14_m3"], 3.117)

    def test_negative_anomaly_parses(self):
        # the source writes negatives as "-.4883405E+14"; every parsed value is a float
        self.assertTrue(all(isinstance(r["wwv_anomaly_1e14_m3"], float) for r in self.rows))
        self.assertTrue(any(r["wwv_anomaly_1e14_m3"] < 0 for r in self.rows))


if __name__ == "__main__":
    unittest.main()
