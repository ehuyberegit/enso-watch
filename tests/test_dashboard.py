"""Offline test of the dashboard's series aggregation (pure, no network, no server)."""

import json
import tempfile
import unittest
from pathlib import Path

from enso_watch.dashboard import build_series


def _write(dir_path, name, daily, status=None):
    doc = {"daily_series": daily}
    if status is not None:
        doc["status"] = status
    (Path(dir_path) / name).write_text(json.dumps(doc), encoding="utf-8")


def _rec(date, anomaly, status="preliminary"):
    return {
        "date": date,
        "nino34_anomaly_c": anomaly,
        "baseline": "1991-2020",
        "provenance": {"source": "NOAA OISST", "status": status},
    }


class BuildSeriesTest(unittest.TestCase):
    def test_merges_and_sorts_by_date(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "enso-watch-2026-08-11.json", [_rec("2026-08-11", 2.682)])
            _write(d, "enso-watch-2026-08-10.json", [_rec("2026-08-10", 2.754)])
            out = build_series(d)
            dates = [r["date"] for r in out["daily_series"]]
            self.assertEqual(dates, ["2026-08-10", "2026-08-11"])
            self.assertEqual(out["record_count"], 2)
            self.assertEqual(len(out["source_files"]), 2)

    def test_final_replaces_preliminary_for_same_date(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "enso-watch-2026-08-10.json", [_rec("2026-08-10", 2.700, status="preliminary")])
            _write(d, "enso-watch-2026-08-10_final.json", [_rec("2026-08-10", 2.650, status="final")])
            out = build_series(d)
            self.assertEqual(out["record_count"], 1)
            self.assertEqual(out["daily_series"][0]["nino34_anomaly_c"], 2.650)

    def test_latest_status_wins(self):
        with tempfile.TemporaryDirectory() as d:
            _write(d, "enso-watch-2026-08-10.json", [_rec("2026-08-10", 2.7)], status={"oni_latest": 1.3, "oni_season": "AMJ"})
            _write(d, "enso-watch-2026-08-11.json", [_rec("2026-08-11", 2.6)], status={"oni_latest": 1.39, "oni_season": "MJJ"})
            out = build_series(d)
            self.assertEqual(out["status"]["oni_season"], "MJJ")

    def test_empty_dir_is_honest(self):
        with tempfile.TemporaryDirectory() as d:
            out = build_series(d)
            self.assertEqual(out["record_count"], 0)
            self.assertIsNone(out["status"])
            self.assertEqual(out["daily_series"], [])


if __name__ == "__main__":
    unittest.main()
