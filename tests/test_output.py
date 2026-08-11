"""The output contract gate: shape, provenance completeness, and status golden.

The structural test is the run contract's criterion 4: every output record must
carry a complete, non empty provenance block. A single hole is a red gate.
"""
import os
import unittest

from enso_watch.output import build_output
from enso_watch.provenance import REQUIRED_FIELDS, is_complete

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURES = os.path.join(ROOT, "fixtures")
OISST = os.path.join(FIXTURES, "oisst", "oisst-avhrr-v02r01.20260701.nc")
CLIM = os.path.join(FIXTURES, "oisst", "nino34_climatology_1991-2020.nc")
ONI = os.path.join(FIXTURES, "cpc", "oni.ascii.txt")
CONTROL = os.path.join(FIXTURES, "cpc", "ersst5.nino.mth.91-20.ascii")

STATUS_GOLDEN = {
    "oni_latest": 1.39,
    "oni_season": "MJJ 2026",
    "phase": "el_nino",
    "strength": "moderate",
    "our_nino34_vs_official": 0.304,
    "control_period": "2026-06",
}
DAILY_FIELDS = ("date", "nino34_anomaly_c", "region_mean_sst_c", "climatology_mean_c", "baseline")


class OutputContractTest(unittest.TestCase):
    def setUp(self):
        self.out = build_output(OISST, CLIM, ONI, CONTROL, FIXTURES)

    def test_every_record_has_complete_provenance(self):
        records = list(self.out["daily_series"]) + [self.out["status"]]
        for record in records:
            self.assertIn("provenance", record)
            self.assertTrue(
                is_complete(record["provenance"]),
                f"incomplete provenance in {record}",
            )
            for field in REQUIRED_FIELDS:
                self.assertTrue(str(record["provenance"][field]).strip())

    def test_daily_record_shape(self):
        daily = self.out["daily_series"][0]
        for field in DAILY_FIELDS:
            self.assertIn(field, daily)
        self.assertEqual(daily["nino34_anomaly_c"], 1.744)
        self.assertEqual(daily["baseline"], "1991-2020")

    def test_status_golden(self):
        status = self.out["status"]
        for key, value in STATUS_GOLDEN.items():
            self.assertEqual(status[key], value, key)

    def test_incomplete_provenance_is_rejected(self):
        from enso_watch.provenance import provenance_block

        good = {
            "source": "NOAA OISST",
            "dataset_version": "v2.1",
            "retrieval_url": "https://example",
            "pull_timestamp": "2026-08-11T00:00:00Z",
            "status": "final",
        }
        self.assertTrue(is_complete(good))
        self.assertFalse(is_complete(dict(good, status="  ")))
        self.assertFalse(is_complete(dict(good, retrieval_url="")))
        self.assertFalse(is_complete(dict(good, source=None)))
        self.assertFalse(is_complete({k: v for k, v in good.items() if k != "status"}))
        with self.assertRaises(ValueError):
            provenance_block("NOAA OISST", "v2.1", "https://example", "2026-08-11T00:00:00Z", "")


if __name__ == "__main__":
    unittest.main()
