"""Offline gate for the ridge forecast model.

Two load bearing tests: ridge recovers a known linear law exactly at lambda 0,
and the walk forward is leakage free (chopping every row after a target must not
change the forecast made before it, so the model cannot have used the future).
"""
import unittest

import numpy as np

from enso_watch import model


class RidgeTest(unittest.TestCase):
    def test_recovers_linear_law_at_lambda_zero(self):
        X = np.array([[1., 0.], [0., 1.], [1., 1.], [2., 1.], [1., 2.], [3., 2.], [2., 3.]])
        y = X @ np.array([2.0, -1.0]) + 0.5
        m = model.ridge_fit(X, y, lam=0.0)
        pred = model.ridge_predict(m, X)
        self.assertTrue(np.allclose(pred, y, atol=1e-9))

    def test_ridge_shrinks_weights_below_linear(self):
        X = np.array([[1., 0.], [0., 1.], [1., 1.], [2., 1.], [1., 2.], [3., 2.], [2., 3.]])
        y = X @ np.array([2.0, -1.0]) + 0.5
        big = np.linalg.norm(model.ridge_fit(X, y, lam=0.0)["w"][1:])
        small = np.linalg.norm(model.ridge_fit(X, y, lam=10.0)["w"][1:])
        self.assertLess(small, big)


class AlignTest(unittest.TestCase):
    def test_inner_join_on_common_months(self):
        nino = [{"ym": "2000-01", "mean": 0.5}, {"ym": "2000-02", "mean": 0.6}, {"ym": "2000-03", "mean": 0.7}]
        wwv = [{"ym": "2000-02", "anomaly": 1.0}, {"ym": "2000-03", "anomaly": 1.2}, {"ym": "1999-12", "anomaly": 9.9}]
        rows = model.align(nino, wwv)
        self.assertEqual([r["ym"] for r in rows], ["2000-02", "2000-03"])
        self.assertEqual(rows[0]["month"], 2)
        self.assertEqual(rows[0]["nino"], 0.6)
        self.assertEqual(rows[0]["wwv"], 1.0)


class WalkForwardModelTest(unittest.TestCase):
    def _rows(self, n):
        # a deterministic, learnable series: nino oscillates, wwv leads it a little
        rows = []
        for i in range(n):
            month = (i % 12) + 1
            nino = round(1.5 * np.sin(i / 7.0), 4)
            wwv = round(1.5 * np.sin((i + 3) / 7.0), 4)  # leads nino by ~3 steps
            rows.append({"ym": f"{1990 + i // 12:04d}-{month:02d}", "nino": nino, "wwv": wwv, "month": month})
        return rows

    def test_lead_below_one_raises(self):
        with self.assertRaises(ValueError):
            model.walk_forward_model(self._rows(60), lead=0, min_train=24, lam=1.0)

    def test_hindcast_is_dated_and_matches_pairs(self):
        rows = self._rows(200)
        recs = model.hindcast(rows, lead=3, min_train=60, lam=1.0)
        pairs = model.walk_forward_model(rows, lead=3, min_train=60, lam=1.0)
        self.assertEqual(len(recs), len(pairs))
        self.assertEqual(set(recs[0]), {"month", "forecast", "actual"})
        self.assertLess(recs[0]["month"], recs[-1]["month"])  # in time order
        self.assertEqual((recs[0]["forecast"], recs[0]["actual"]), pairs[0])

    def test_no_future_leakage_by_truncation(self):
        rows = self._rows(200)
        lead, min_train = 3, 60
        full = model.walk_forward_model(rows, lead, min_train, lam=1.0)
        # keep only up to the first issue's target: nothing after it exists
        first_issue = min_train - 1
        truncated = model.walk_forward_model(rows[:first_issue + lead + 1], lead, min_train, lam=1.0)
        # same first forecast proves the model never used data after the target
        self.assertEqual(len(truncated), 1)
        self.assertAlmostEqual(full[0][0], truncated[0][0], places=12)


class PhaseProbsTest(unittest.TestCase):
    def test_sums_to_100(self):
        for v, s in [(2.0, 0.3), (0.0, 0.4), (-1.5, 0.5), (0.6, 0.9)]:
            p = model.phase_probs(v, s)
            self.assertEqual(p["p_la_nina"] + p["p_neutral"] + p["p_el_nino"], 100)

    def test_strong_warm_is_el_nino(self):
        p = model.phase_probs(2.0, 0.3)
        self.assertGreater(p["p_el_nino"], 95)

    def test_near_zero_is_mostly_neutral(self):
        p = model.phase_probs(0.0, 0.3)
        self.assertGreater(p["p_neutral"], p["p_el_nino"])
        self.assertGreater(p["p_neutral"], p["p_la_nina"])

    def test_strong_cold_is_la_nina(self):
        p = model.phase_probs(-1.5, 0.4)
        self.assertGreater(p["p_la_nina"], 95)


class ForwardAndCompareTest(unittest.TestCase):
    def _series(self, n):
        nino, wwv = [], []
        for i in range(n):
            month = (i % 12) + 1
            nino.append({"ym": f"{1990 + i // 12:04d}-{month:02d}", "mean": float(np.sin(i / 7.0))})
            wwv.append({"ym": f"{1990 + i // 12:04d}-{month:02d}", "anomaly": float(np.sin((i + 3) / 7.0))})
        return nino, wwv

    def test_forward_has_future_months_in_order(self):
        nino, wwv = self._series(200)
        fwd = model.forecast_forward(nino, wwv, leads=(1, 2, 3))
        self.assertTrue(fwd["available"])
        self.assertGreater(fwd["forward"][1]["month"], fwd["issue_month"])
        self.assertGreater(fwd["forward"][3]["month"], fwd["forward"][1]["month"])

    def test_compare_to_official_shape(self):
        nino, wwv = self._series(200)  # issue month lands 2006-08, forward covers Sep..Feb
        official = {"issued": "Test", "seasons": [
            {"season": "SON", "months": "Sep Oct Nov", "p_la_nina": 0, "p_neutral": 10, "p_el_nino": 90},
            {"season": "OND", "months": "Oct Nov Dec", "p_la_nina": 0, "p_neutral": 20, "p_el_nino": 80},
        ]}
        c = model.compare_to_official(nino, wwv, official)
        self.assertTrue(c["available"])
        self.assertEqual(len(c["seasons"]), 2)
        self.assertTrue(0.0 <= c["overall_agreement"] <= 1.0)
        for s in c["seasons"]:
            self.assertEqual(s["ours"]["p_la_nina"] + s["ours"]["p_neutral"] + s["ours"]["p_el_nino"], 100)
        # the forward series (for the plume chart): future months with an uncertainty band
        self.assertIn("forward", c)
        self.assertTrue(len(c["forward"]) >= 1)
        f0 = c["forward"][0]
        self.assertEqual(set(f0) >= {"month", "value", "lo", "hi", "sigma"}, True)
        self.assertLessEqual(f0["lo"], f0["value"])
        self.assertGreaterEqual(f0["hi"], f0["value"])


class EvaluateModelTest(unittest.TestCase):
    def test_unavailable_when_overlap_too_short(self):
        nino = [{"ym": f"2000-{m:02d}", "mean": 0.1} for m in range(1, 13)]
        wwv = [{"ym": f"2000-{m:02d}", "anomaly": 0.1} for m in range(1, 13)]
        out = model.evaluate_model(nino, wwv, leads=(1,), min_train=120)
        self.assertFalse(out["available"])

    def test_board_and_weights_present(self):
        nino, wwv = [], []
        for i in range(200):
            month = (i % 12) + 1
            v = float(np.sin(i / 7.0))
            nino.append({"ym": f"{1990 + i // 12:04d}-{month:02d}", "mean": v})
            wwv.append({"ym": f"{1990 + i // 12:04d}-{month:02d}", "anomaly": float(np.sin((i + 3) / 7.0))})
        out = model.evaluate_model(nino, wwv, leads=(1, 3), min_train=60)
        self.assertTrue(out["available"])
        self.assertEqual(set(out["board"]), {1, 3})
        self.assertEqual(set(out["weights"]), {"nino34", "wwv", "season"})


if __name__ == "__main__":
    unittest.main()
