"""Offline test of the dashboard's series aggregation (pure, no network, no server)."""

import json
import math
import tempfile
import unittest
from pathlib import Path

from enso_watch.dashboard import build_series, load_history, load_wwv, load_skill


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


class LoadHistoryTest(unittest.TestCase):
    def _repo(self, dir_path, lines, provenance=None):
        hist = Path(dir_path) / "data" / "history"
        hist.mkdir(parents=True)
        (hist / "nino34_monthly.csv").write_text(
            "month,nino34_anomaly_c,region_mean_sst_c,climatology_mean_c,baseline\n" + lines,
            encoding="utf-8",
        )
        if provenance is not None:
            (hist / "nino34_monthly.provenance.json").write_text(json.dumps(provenance), encoding="utf-8")

    def test_absent_history_is_honest(self):
        with tempfile.TemporaryDirectory() as d:
            out = load_history(d)
            self.assertFalse(out["available"])

    def test_monthly_series_span_and_latest(self):
        with tempfile.TemporaryDirectory() as d:
            self._repo(d,
                "2023-12,2.011,28.587,26.576,1991-2020\n"
                "2024-01,1.8,28.3,26.5,1991-2020\n"
                "2024-12,-0.63,25.947,26.577,1991-2020\n",
                provenance={"source_name": "NOAA PSL OISST v2.1 monthly mean"})
            out = load_history(d)
            self.assertTrue(out["available"])
            self.assertEqual(out["month_count"], 3)
            self.assertEqual(out["span"], ["2023-12", "2024-12"])
            self.assertEqual(out["monthly"][0], {"ym": "2023-12", "mean": 2.011})
            self.assertEqual(out["latest"], {"month": "2024-12", "anomaly_c": -0.63})
            self.assertEqual(out["provenance"]["source_name"], "NOAA PSL OISST v2.1 monthly mean")

    def test_unsorted_input_is_sorted_by_month(self):
        with tempfile.TemporaryDirectory() as d:
            self._repo(d, "2024-03,1.0,28,27,1991-2020\n2024-01,2.0,28,26,1991-2020\n")
            out = load_history(d)
            self.assertEqual([m["ym"] for m in out["monthly"]], ["2024-01", "2024-03"])
            self.assertEqual(out["latest"]["month"], "2024-03")

    def test_torn_line_is_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            # a half written last line (a real risk while the backfill writes) must not crash the lens
            self._repo(d, "2024-01,1.0,28.0,27.0,1991-2020\n2024-02,\n")
            out = load_history(d)
            self.assertEqual(out["month_count"], 1)
            self.assertEqual(out["latest"]["month"], "2024-01")


class LoadWwvTest(unittest.TestCase):
    def _repo(self, dir_path, lines, provenance=None):
        hist = Path(dir_path) / "data" / "history"
        hist.mkdir(parents=True)
        (hist / "wwv_monthly.csv").write_text(
            "month,wwv_volume_1e14_m3,wwv_anomaly_1e14_m3\n" + lines, encoding="utf-8")
        if provenance is not None:
            (hist / "wwv_monthly.provenance.json").write_text(json.dumps(provenance), encoding="utf-8")

    def test_absent_is_honest(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(load_wwv(d)["available"])

    def test_reads_anomaly_span_and_latest(self):
        with tempfile.TemporaryDirectory() as d:
            self._repo(d,
                "1997-04,30.0,3.117\n1998-12,22.93,-2.663\n",
                provenance={"source_name": "NOAA PMEL GTMBA warm water volume"})
            out = load_wwv(d)
            self.assertTrue(out["available"])
            self.assertEqual(out["month_count"], 2)
            self.assertEqual(out["span"], ["1997-04", "1998-12"])
            self.assertEqual(out["monthly"][0], {"ym": "1997-04", "anomaly": 3.117})
            self.assertEqual(out["latest"], {"month": "1998-12", "anomaly": -2.663})
            self.assertEqual(out["provenance"]["source_name"], "NOAA PMEL GTMBA warm water volume")


class LoadSkillTest(unittest.TestCase):
    def test_short_history_is_not_available(self):
        hist = {"monthly": [{"ym": "2020-01", "mean": 0.1}]}
        self.assertFalse(load_skill(hist, {})["available"])

    def test_scores_baselines_without_wwv(self):
        hist = {"monthly": [{"ym": f"{2000 + i // 12}-{i % 12 + 1:02d}", "mean": math.sin(i / 6.0)}
                            for i in range(200)]}
        out = load_skill(hist, {})
        self.assertTrue(out["available"])
        self.assertEqual(set(out["board"]), {"persistence", "climatology"})
        self.assertFalse(out["model_available"])
        for lead in out["leads"]:
            self.assertEqual(out["board"]["climatology"][lead]["acc"], 0.0)

    def test_model_row_appears_with_wwv(self):
        months = [f"{2000 + i // 12}-{i % 12 + 1:02d}" for i in range(200)]
        hist = {"monthly": [{"ym": months[i], "mean": math.sin(i / 6.0)} for i in range(200)]}
        wwv = {"monthly": [{"ym": months[i], "anomaly": math.sin((i + 3) / 6.0)} for i in range(200)]}
        out = load_skill(hist, wwv)
        self.assertTrue(out["model_available"])
        self.assertIn("model", out["board"])
        self.assertEqual(set(out["weights"]), {"nino34", "wwv", "season"})


if __name__ == "__main__":
    unittest.main()
