"""Peak forecast: when the current El Nino peaks, and how high, with uncertainty.

A fixed lead forecast ("the value in 6 months") is academic. What matters for
impact is the PEAK: its timing and its magnitude. Two facts make this tractable,
and we lean on both honestly:

- Timing is largely known in advance. El Nino events phase lock to the seasonal
  cycle: they peak in November to January. So we read the timing from the empirical
  distribution of past peak months, not from a fragile model.
- Magnitude is foretold by the precursor. We fit the eventual peak on the current
  Nino 3.4 anomaly and the current warm water volume, over the past decades, and
  validate it leave one year out so the reported uncertainty (the typical miss) is
  real out of sample, not flattering in sample error.

Honesty about the small sample: there are only a few dozen years and a handful of
strong El Ninos, so the magnitude uncertainty is wide. It is reported, never
hidden. And the peak estimate is never below what the ongoing event has already
reached, which the latest observation pins down.
"""
import numpy as np

from enso_watch.model import align, ridge_fit, ridge_predict

# Aug(Y) to Feb(Y+1): the window an El Nino peak falls in.
_WIN_THIS = (8, 9, 10, 11, 12)
_WIN_NEXT = (1, 2)


def _nino_by_ym(nino_monthly):
    return {m["ym"]: m["mean"] for m in nino_monthly}


def _event_peak(nino_by_ym, year):
    """The max Nino 3.4 and its month in the Aug(year) to Feb(year+1) window."""
    months = [f"{year}-{mm:02d}" for mm in _WIN_THIS] + [f"{year + 1}-{mm:02d}" for mm in _WIN_NEXT]
    vals = [(ym, nino_by_ym[ym]) for ym in months if ym in nino_by_ym]
    if len(vals) < 5:
        return None
    ym, v = max(vals, key=lambda t: t[1])
    return {"peak_ym": ym, "peak_value": round(v, 3)}


def _training(aligned, nino_by_ym, issue_mm, skip_year):
    by = {r["ym"]: r for r in aligned}
    rows = []
    for Y in sorted({int(r["ym"][:4]) for r in aligned}):
        if Y == skip_year:
            continue  # the ongoing event has no completed peak yet
        issue = by.get(f"{Y}-{issue_mm:02d}")
        pk = _event_peak(nino_by_ym, Y)
        if issue and pk:
            rows.append({"year": Y, "issue_nino": issue["nino"], "issue_wwv": issue["wwv"],
                         "peak_value": pk["peak_value"], "peak_ym": pk["peak_ym"],
                         "peak_month": int(pk["peak_ym"][5:7])})
    return rows


def _loo_rmse(X, y, lam):
    """Leave one out RMSE: the honest typical miss on a year the fit never saw."""
    n = len(y)
    res = []
    for i in range(n):
        idx = [j for j in range(n) if j != i]
        m = ridge_fit(X[idx], y[idx], lam)
        res.append(y[i] - float(ridge_predict(m, X[i:i + 1])[0]))
    return float(np.sqrt(np.mean(np.square(res))))


def _current_event_max(nino_by_ym, threshold=0.5):
    """The highest Nino 3.4 the ongoing warm run has already reached.

    Walks back from the latest observed month while the anomaly stays above the
    El Nino threshold, so the peak estimate can never be below reality.
    """
    yms = sorted(nino_by_ym)
    i = len(yms) - 1
    best = (yms[i], nino_by_ym[yms[i]])
    while i >= 0 and nino_by_ym[yms[i]] >= threshold:
        if nino_by_ym[yms[i]] > best[1]:
            best = (yms[i], nino_by_ym[yms[i]])
        i -= 1
    return {"max_ym": best[0], "max_value": round(best[1], 3), "latest_ym": yms[-1]}


def forecast_peak(nino_monthly, wwv_monthly, lam=0.0, warm_threshold=0.5, strong_threshold=1.5):
    """Forecast the current event's peak: month, magnitude, and uncertainty."""
    aligned = align(nino_monthly or [], wwv_monthly or [])
    nino_by_ym = _nino_by_ym(nino_monthly or [])
    if len(aligned) < 60:
        return {"available": False}

    latest_ym = max(nino_by_ym)              # freshest Nino 3.4, which may lead the WWV
    issue_mm = int(latest_ym[5:7])
    issue_year = int(latest_ym[:4])
    issue_nino = nino_by_ym[latest_ym]
    issue_wwv = aligned[-1]["wwv"]           # latest WWV, carried forward when it lags
    wwv_month = aligned[-1]["ym"]
    rows = _training(aligned, nino_by_ym, issue_mm, skip_year=issue_year)
    if len(rows) < 8:
        return {"available": False}

    X = np.array([[r["issue_nino"], r["issue_wwv"]] for r in rows], dtype=float)
    y = np.array([r["peak_value"] for r in rows], dtype=float)
    fit = ridge_fit(X, y, lam)
    predicted = float(ridge_predict(fit, np.array([[issue_nino, issue_wwv]], dtype=float))[0])
    sigma = _loo_rmse(X, y, lam)

    # Timing phase locks by strength: strong El Ninos peak Nov to Jan, while weak
    # ones can peak off season. A developing strong event (like now) should read its
    # timing from the strong analogs, not from every warm year.
    warm = [r for r in rows if r["peak_value"] > warm_threshold]
    strong = [r for r in warm if r["peak_value"] >= strong_threshold]
    predicted_strong = predicted >= strong_threshold
    timing_set = strong if (predicted_strong and len(strong) >= 4) else (warm or rows)
    months = [r["peak_month"] for r in timing_set]
    modal = max(set(months), key=months.count)

    def concrete(mm):
        return f"{issue_year + (0 if mm >= 7 else 1)}-{mm:02d}"

    concrete_months = sorted(concrete(mm) for mm in set(months))  # chronological across the year boundary

    obs = _current_event_max(nino_by_ym, warm_threshold)
    estimate = max(predicted, obs["max_value"])

    cur = (issue_nino, issue_wwv)
    for r in rows:
        r["dist"] = float(np.hypot(r["issue_nino"] - cur[0], r["issue_wwv"] - cur[1]))
    analogs = [{"year": r["year"], "issue_nino": r["issue_nino"], "issue_wwv": r["issue_wwv"],
                "peak_ym": r["peak_ym"], "peak_value": r["peak_value"]}
               for r in sorted(rows, key=lambda r: r["dist"])[:3]]

    return {
        "available": True,
        "issue_month": latest_ym,
        "wwv_month": wwv_month,
        "latest_observed": obs["latest_ym"],
        "observed_max": {"month": obs["max_ym"], "value": obs["max_value"]},
        "magnitude": {"predicted": round(predicted, 2), "estimate": round(estimate, 2),
                      "sigma": round(sigma, 2),
                      "low": round(estimate - sigma, 2), "high": round(estimate + sigma, 2)},
        "timing": {"peak_month": concrete(modal), "modal_month": modal,
                   "range": [concrete_months[0], concrete_months[-1]],
                   "basis": "strong events" if timing_set is strong else "warm events",
                   "n_timing": len(timing_set)},
        "running_hotter_than_analogs": obs["max_value"] > predicted,
        "n_train": len(rows),
        "n_warm": len(warm),
        "current": {"issue_nino": round(issue_nino, 3), "issue_wwv": round(issue_wwv, 3)},
        "analogs": analogs,
    }
