"""Forecast skill machinery: baselines, walk forward validation, and scoring.

This is the honest judge the whole V1 forecast rests on. Before any model, we
fix the bar it must clear (the baselines) and the way we measure (walk forward,
no future leakage), so a later model's skill is a real gain, not a data leak.

Vocabulary:
- A **forecaster** is a function forecaster(history, lead) -> float. It sees only
  the anomaly values up to and including the issue month (history), and returns
  the predicted anomaly `lead` months ahead. Seeing only history is what makes
  the evaluation leakage free: the signature cannot look into the future.
- **Persistence**: predict that the anomaly stays at its last observed value. The
  naive but strong baseline (ENSO is highly autocorrelated month to month).
- **Climatology**: predict zero anomaly (the climatological state). The "no
  information" baseline.
- **Walk forward**: step through time, at each issue month predict `lead` ahead
  from history only, collect (forecast, actual) pairs over a fixed test window.
- **RMSE**: root mean square error, in degrees C. Lower is better.
- **ACC**: anomaly correlation coefficient, the Pearson correlation between the
  forecast and the actual anomalies. The standard ENSO skill score. 1 is perfect,
  0 is no skill. A constant forecaster (climatology) has zero variance, so its ACC
  is undefined; we report it as 0.0 (no skill) by convention.

Pure and offline: feed it numbers, it never touches the network.
"""
import math


def persistence(history, lead):
    """Predict the anomaly stays at its last observed value."""
    return history[-1]


def climatology(history, lead):
    """Predict the climatological state: zero anomaly."""
    return 0.0


FORECASTERS = {"persistence": persistence, "climatology": climatology}


def walk_forward(values, forecaster, lead, min_train):
    """Return (forecast, actual) pairs over a leakage free walk forward.

    values: the anomaly series in time order. At each issue index i (from
    min_train-1 onward), the forecaster sees only values[:i+1] and predicts index
    i+lead; the actual is values[i+lead]. min_train fixes the same test window for
    every forecaster and lead, so scores are comparable.
    """
    if lead < 1:
        raise ValueError("lead must be at least 1 month")
    pairs = []
    for i in range(min_train - 1, len(values) - lead):
        history = values[:i + 1]
        pairs.append((forecaster(history, lead), values[i + lead]))
    return pairs


def rmse(pairs):
    """Root mean square error of (forecast, actual) pairs, in the series units."""
    if not pairs:
        return None
    return math.sqrt(sum((f - a) ** 2 for f, a in pairs) / len(pairs))


def acc(pairs):
    """Anomaly correlation coefficient (Pearson) of (forecast, actual) pairs.

    Returns 0.0 (no skill) when either side has no variance, e.g. the climatology
    baseline whose forecast is a constant zero.
    """
    n = len(pairs)
    if n < 2:
        return None
    fs = [f for f, _ in pairs]
    a_s = [a for _, a in pairs]
    mf, ma = sum(fs) / n, sum(a_s) / n
    cov = sum((f - mf) * (a - ma) for f, a in pairs)
    vf = sum((f - mf) ** 2 for f in fs)
    va = sum((a - ma) ** 2 for a in a_s)
    if vf <= 0 or va <= 0:
        return 0.0
    return cov / math.sqrt(vf * va)


def evaluate(values, leads=(1, 2, 3, 6), min_train=120):
    """Score every baseline over every lead, on one shared test window.

    Returns a dict: {forecaster_name: {lead: {"acc", "rmse", "n"}}}. min_train
    fixes the test window (default 120 months of warmup, so the score is over the
    part of the record a trained model could also have reached).
    """
    board = {}
    for name, fn in FORECASTERS.items():
        per_lead = {}
        for lead in leads:
            pairs = walk_forward(values, fn, lead, min_train)
            per_lead[lead] = {
                "acc": (round(acc(pairs), 3) if acc(pairs) is not None else None),
                "rmse": (round(rmse(pairs), 3) if rmse(pairs) is not None else None),
                "n": len(pairs),
            }
        board[name] = per_lead
    return board
