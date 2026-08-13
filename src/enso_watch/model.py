"""Our own simple forecast model: ridge regression on the ingredients.

Step 3 of V1. The model reads a few honest predictors at the issue month and
predicts the Nino 3.4 anomaly a lead ahead:

- current Nino 3.4 anomaly (the persistence signal),
- warm water volume anomaly (the precursor, leads El Nino by about two seasons),
- the season (sine and cosine of the calendar month, so the model can learn that
  skill depends on the time of year, the spring predictability barrier).

It is a linear model fit by ridge regression, solved in closed form with numpy
(no scikit-learn dependency): standardize the features, add an intercept, and
solve (X'X + lambda*I) w = X'y with the intercept left unregularized. Linear
regression is the same with lambda = 0; ridge (lambda > 0) just damps the weights
so a short training window does not overfit.

Honesty is enforced by the same walk forward as the baselines: at each issue
month the model is trained only on pairs whose target was already observed by
then, then asked to predict the future. It is scored by the same RMSE and ACC and
compared to the baselines, so a gain is a real gain.
"""
import math

import numpy as np

from enso_watch.skill import acc, rmse

FEATURES = ("nino34", "wwv", "season_sin", "season_cos")


def _row_features(nino, wwv, month_num):
    ang = 2.0 * math.pi * (month_num - 1) / 12.0
    return [nino, wwv, math.sin(ang), math.cos(ang)]


def align(nino_monthly, wwv_monthly):
    """Inner join the Nino 3.4 and WWV monthly series on their common months.

    nino_monthly: rows with keys "ym" and "mean". wwv_monthly: rows with keys
    "ym" and "anomaly". Returns rows sorted by month, each with nino, wwv, and the
    calendar month number, over the overlapping span only.
    """
    wwv = {m["ym"]: m["anomaly"] for m in wwv_monthly}
    rows = [
        {"ym": m["ym"], "nino": m["mean"], "wwv": wwv[m["ym"]], "month": int(m["ym"][5:7])}
        for m in nino_monthly if m["ym"] in wwv
    ]
    rows.sort(key=lambda r: r["ym"])
    return rows


def ridge_fit(X, y, lam):
    """Closed form ridge fit on standardized features with an intercept.

    Returns a model dict with the weights and the standardization stats. The
    intercept (first column of ones) is never regularized.
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd[sd == 0] = 1.0
    Xs = (X - mu) / sd
    Xb = np.hstack([np.ones((Xs.shape[0], 1)), Xs])
    d = Xb.shape[1]
    reg = lam * np.eye(d)
    reg[0, 0] = 0.0  # do not regularize the intercept
    w = np.linalg.solve(Xb.T @ Xb + reg, Xb.T @ y)
    return {"w": w, "mu": mu, "sd": sd}


def ridge_predict(model, X):
    X = np.asarray(X, dtype=float)
    Xs = (X - model["mu"]) / model["sd"]
    Xb = np.hstack([np.ones((Xs.shape[0], 1)), Xs])
    return Xb @ model["w"]


def _feature_matrix(rows):
    return np.array([_row_features(r["nino"], r["wwv"], r["month"]) for r in rows], dtype=float)


def hindcast(rows, lead, min_train, lam, train_floor=48):
    """Leakage free dated forecasts for the ridge model at one lead.

    Issues from the same month as the baselines (min_train - 1) so the test window
    matches. At each issue i, train only on feature rows j whose target y[j+lead]
    was already observed by month i (that is j from 0 to i-lead), then predict the
    target for issue i. The model is retrained every issue on all data available
    then, which is cheap and always leakage free. Returns one record per target
    month: {"month", "forecast", "actual"}, so the forecast can be drawn against
    what really happened.
    """
    if lead < 1:
        raise ValueError("lead must be at least 1 month")
    X = _feature_matrix(rows)
    y = np.array([r["nino"] for r in rows], dtype=float)
    n = len(rows)
    records = []
    for i in range(min_train - 1, n - lead):
        n_train = i - lead + 1  # feature rows 0..i-lead, targets y[lead..i]
        if n_train < train_floor:
            continue
        model = ridge_fit(X[0:n_train], y[lead:lead + n_train], lam)
        forecast = float(ridge_predict(model, X[i:i + 1])[0])
        records.append({
            "month": rows[i + lead]["ym"],
            "forecast": round(forecast, 3),
            "actual": round(float(y[i + lead]), 3),
        })
    return records


def walk_forward_model(rows, lead, min_train, lam, train_floor=48):
    """Leakage free (forecast, actual) pairs for the ridge model at one lead."""
    return [(r["forecast"], r["actual"]) for r in hindcast(rows, lead, min_train, lam, train_floor)]


def full_fit_weights(rows, lam, lead):
    """Weights from a fit of the whole record AT A GIVEN LEAD, for interpretation.

    Fits features at month j against the anomaly `lead` months later (the same
    relationship the forecast uses), on the full record, and returns the
    standardized weight of each feature (comparable in size). This is a readout of
    what the model leans on for that lead, not a score (scoring is walk forward).
    At long leads the current temperature fades and the warm water volume carries
    more of the signal, which is the whole reason it is an ingredient.
    """
    X = _feature_matrix(rows)
    y = np.array([r["nino"] for r in rows], dtype=float)
    n = len(rows)
    model = ridge_fit(X[0:n - lead], y[lead:n], lam)
    w = model["w"][1:]  # drop intercept
    return {
        "nino34": round(float(w[0]), 3),
        "wwv": round(float(w[1]), 3),
        "season": round(float(math.hypot(w[2], w[3])), 3),
    }


_MONTHS = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
           "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}


def _add_months(ym, k):
    y, m = int(ym[:4]), int(ym[5:7])
    total = (y * 12 + (m - 1)) + k
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def _phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def phase_probs(value, sigma):
    """Turn a Nino 3.4 forecast (mean and spread) into phase probabilities.

    Treats the forecast as a Gaussian around `value` with standard deviation
    `sigma` (our own out of sample error at that lead), then reads off the chance
    of El Nino (above +0.5), La Nina (below -0.5), and Neutral (between), as
    integer percentages summing to 100. This is the honest bridge: our continuous
    forecast plus its measured uncertainty, in the same phase language CPC uses.
    """
    sigma = max(sigma, 1e-6)
    p_en = 1.0 - _phi((0.5 - value) / sigma)
    p_ln = _phi((-0.5 - value) / sigma)
    p_n = max(0.0, 1.0 - p_en - p_ln)
    pct = [round(100 * p_ln), round(100 * p_n), round(100 * p_en)]
    pct[pct.index(max(pct))] += 100 - sum(pct)  # nudge the largest so it sums to 100
    return {"p_la_nina": pct[0], "p_neutral": pct[1], "p_el_nino": pct[2]}


def forecast_forward(nino_monthly, wwv_monthly, leads=(1, 2, 3, 4, 5, 6), lam=1.0, train_floor=60):
    """Predict the next months from the latest data (train on the whole record).

    For each lead, fit the ridge on all pairs whose target is known, then predict
    from the last observed feature row. Returns the issue month and a forecast
    value per future month. This is the forward looking forecast (not a hindcast).
    """
    rows = align(nino_monthly or [], wwv_monthly or [])
    if len(rows) < train_floor + max(leads):
        return {"available": False}
    nino_by_ym = {m["ym"]: m["mean"] for m in (nino_monthly or [])}
    latest_ym = max(nino_by_ym)                     # issue from the freshest temperature
    issue_nino = nino_by_ym[latest_ym]
    issue_wwv = rows[-1]["wwv"]                      # latest WWV, carried forward when it lags
    issue_feat = np.array([_row_features(issue_nino, issue_wwv, int(latest_ym[5:7]))], dtype=float)
    X = _feature_matrix(rows)
    y = np.array([r["nino"] for r in rows], dtype=float)
    n = len(rows)
    forward = {}
    for lead in leads:
        m = ridge_fit(X[0:n - lead], y[lead:n], lam)
        val = float(ridge_predict(m, issue_feat)[0])
        forward[lead] = {"month": _add_months(latest_ym, lead), "value": round(val, 3)}
    return {"available": True, "issue_month": latest_ym, "wwv_month": rows[-1]["ym"], "forward": forward}


def compare_to_official(nino_monthly, wwv_monthly, official, lam=1.0, sigmas=None,
                        min_train=120):
    """Compare our forward forecast to the official CPC phase probabilities.

    Produces our forecast for the next months, turns each CPC 3 month season into
    our own phase probabilities (averaging our monthly forecasts over the season,
    with our measured spread), and measures how close the two are. Returns per
    season rows and an overall agreement (1 means identical, 0 means opposite).
    """
    fwd = forecast_forward(nino_monthly, wwv_monthly, leads=(1, 2, 3, 4, 5, 6), lam=lam)
    if not fwd.get("available") or not official or not official.get("seasons"):
        return {"available": False}
    if sigmas is None:
        ev = evaluate_model(nino_monthly, wwv_monthly, leads=(1, 2, 3, 4, 5, 6),
                            min_train=min_train, lam=lam)
        sigmas = {L: ev["board"][L]["rmse"] for L in ev["board"]} if ev.get("available") else {}
    by_num = {}   # calendar month number -> {value, sigma}; unique within a 6 month horizon
    for lead, rec in fwd["forward"].items():
        by_num[int(rec["month"][5:7])] = {"value": rec["value"], "sigma": sigmas.get(lead, 0.5), "ym": rec["month"]}

    rows_out, dists, matched = [], [], 0
    for s in official["seasons"]:
        nums = [_MONTHS.get(x) for x in s["months"].split()]
        if not all(nm in by_num for nm in nums):
            continue
        vals = [by_num[nm]["value"] for nm in nums]
        sigs = [by_num[nm]["sigma"] for nm in nums]
        mu, sg = sum(vals) / len(vals), sum(sigs) / len(sigs)
        ours = phase_probs(mu, sg)
        cpc = {"p_la_nina": s["p_la_nina"], "p_neutral": s["p_neutral"], "p_el_nino": s["p_el_nino"]}
        dist = 0.5 * (abs(ours["p_la_nina"] - cpc["p_la_nina"]) + abs(ours["p_neutral"] - cpc["p_neutral"])
                      + abs(ours["p_el_nino"] - cpc["p_el_nino"])) / 100.0
        dists.append(dist)
        if max(ours, key=ours.get) == max(cpc, key=cpc.get):
            matched += 1
        rows_out.append({"season": s["season"], "months": s["months"],
                         "our_nino34": round(mu, 3), "ours": ours, "cpc": cpc,
                         "agreement": round(1 - dist, 3)})
    if not rows_out:
        return {"available": False}
    forward_series = []
    for lead in sorted(fwd["forward"]):
        rec = fwd["forward"][lead]
        sig = float(sigmas.get(lead, 0.5))
        forward_series.append({
            "month": rec["month"], "value": rec["value"], "sigma": round(sig, 3),
            "lo": round(rec["value"] - sig, 3), "hi": round(rec["value"] + sig, 3),
        })
    return {
        "available": True,
        "issued": official.get("issued"),
        "issue_month": fwd["issue_month"],
        "seasons": rows_out,
        "forward": forward_series,
        "overall_agreement": round(1 - sum(dists) / len(dists), 3),
        "phase_match": f"{matched}/{len(rows_out)}",
    }


def evaluate_model(nino_monthly, wwv_monthly, leads=(1, 2, 3, 6), min_train=120, lam=1.0,
                   with_hindcast=False):
    """Score the ridge model over every lead, matched to the baseline window.

    Returns {"available", "board": {lead: {acc, rmse, n}}, "weights", "lam",
    "n_overlap"}, and, when with_hindcast is set, "hindcast": {lead: [dated
    forecast vs actual records]} so the forecast can be drawn over time. Not
    available when the Nino 3.4 and WWV series overlap too little to train and test.
    """
    rows = align(nino_monthly or [], wwv_monthly or [])
    if len(rows) <= min_train + max(leads):
        return {"available": False, "n_overlap": len(rows)}
    board = {}
    hind = {}
    for lead in leads:
        recs = hindcast(rows, lead, min_train, lam)
        pairs = [(r["forecast"], r["actual"]) for r in recs]
        board[lead] = {
            "acc": (round(acc(pairs), 3) if acc(pairs) is not None else None),
            "rmse": (round(rmse(pairs), 3) if rmse(pairs) is not None else None),
            "n": len(pairs),
        }
        hind[lead] = recs
    weights_lead = max(leads)
    out = {
        "available": True,
        "board": board,
        "weights": full_fit_weights(rows, lam, weights_lead),
        "weights_lead": weights_lead,
        "lam": lam,
        "n_overlap": len(rows),
        "span": [rows[0]["ym"], rows[-1]["ym"]],
    }
    if with_hindcast:
        out["hindcast"] = hind
    return out
