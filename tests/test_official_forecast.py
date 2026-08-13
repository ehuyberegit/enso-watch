"""Offline gate for the CPC official ENSO forecast parser.

Parses the frozen CPC probabilities page and pins the issue label and the per
season phase probabilities, so a silent change in the page format or the parser
is caught. Offline: reads a local fixture, no network.
"""
import os
import unittest

from enso_watch.official_forecast import parse_cpc_probabilities

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE = os.path.join(ROOT, "fixtures", "cpc", "roni_probabilities.html")


class ParseCpcForecastTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(FIXTURE, encoding="utf-8") as fh:
            cls.parsed = parse_cpc_probabilities(fh.read())

    def test_issue_label(self):
        self.assertEqual(self.parsed["issued"], "August 2026")

    def test_nine_overlapping_seasons(self):
        seasons = self.parsed["seasons"]
        self.assertEqual(len(seasons), 9)
        self.assertEqual(seasons[0]["season"], "JAS")
        self.assertEqual(seasons[0]["months"], "Jul Aug Sep")
        self.assertEqual(seasons[-1]["season"], "MAM")

    def test_probabilities_and_order(self):
        first, last = self.parsed["seasons"][0], self.parsed["seasons"][-1]
        self.assertEqual((first["p_la_nina"], first["p_neutral"], first["p_el_nino"]), (0, 0, 100))
        self.assertEqual((last["p_la_nina"], last["p_neutral"], last["p_el_nino"]), (0, 18, 82))

    def test_every_row_sums_to_100(self):
        for s in self.parsed["seasons"]:
            self.assertEqual(s["p_la_nina"] + s["p_neutral"] + s["p_el_nino"], 100)

    def test_missing_table_raises(self):
        with self.assertRaises(ValueError):
            parse_cpc_probabilities("<html><body>no table here</body></html>")


if __name__ == "__main__":
    unittest.main()
