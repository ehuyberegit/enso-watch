"""Score the forecast baselines over our Nino 3.4 history and log the run.

Loads the committed monthly history, runs persistence and climatology through the
walk forward harness at several leads, prints the scoreboard (the bar any model
must clear), and appends the result to data/experiments.jsonl. Offline: it reads
a committed CSV, no network.

Run from the repo root with the project venv:
    .venv/bin/python tools/run_baselines.py
"""
import csv
import datetime
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from enso_watch import skill, model
from enso_watch.experiments import log_experiment

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY = os.path.join(ROOT, "data", "history", "nino34_monthly.csv")
WWV = os.path.join(ROOT, "data", "history", "wwv_monthly.csv")
LOG = os.path.join(ROOT, "data", "experiments.jsonl")
LEADS = (1, 2, 3, 6)
MIN_TRAIN = 120


def load_history():
    nino, values = [], []
    with open(HISTORY, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            nino.append({"ym": row["month"], "mean": float(row["nino34_anomaly_c"])})
            values.append(float(row["nino34_anomaly_c"]))
    return nino, values


def load_wwv():
    if not os.path.exists(WWV):
        return []
    with open(WWV, encoding="utf-8") as fh:
        return [{"ym": r["month"], "anomaly": float(r["wwv_anomaly_1e14_m3"])} for r in csv.DictReader(fh)]


def main():
    nino, values = load_history()
    board = skill.evaluate(values, leads=LEADS, min_train=MIN_TRAIN)

    wwv = load_wwv()
    weights = None
    mod = model.evaluate_model(nino, wwv, leads=LEADS, min_train=MIN_TRAIN) if wwv else {"available": False}
    if mod.get("available"):
        board["model"] = mod["board"]
        weights = mod["weights"]

    print(f"Nino 3.4 forecast skill, {len(values)} months ({nino[0]['ym']} to {nino[-1]['ym']}), "
          f"test window from month {MIN_TRAIN} on.\n")
    print("lead(mo)  " + "".join(f"{n:>22}" for n in board))
    print("          " + "".join(f"{'ACC / RMSE(C)':>22}" for _ in board))
    for lead in LEADS:
        cells = "".join(f"{board[name][lead]['acc']:>10} /{board[name][lead]['rmse']:>9}  " for name in board)
        print(f"{lead:>6}    {cells}")
    if weights:
        print(f"\nmodel leanings at lead {mod['weights_lead']} (standardized): "
              f"current temp {weights['nino34']}, warm water {weights['wwv']}, season {weights['season']}")

    log_experiment(LOG, {
        "at_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kind": "forecast_skill",
        "target": "nino34_monthly_anomaly",
        "n_months": len(values),
        "span": [nino[0]["ym"], nino[-1]["ym"]],
        "min_train": MIN_TRAIN,
        "leads": list(LEADS),
        "board": board,
        "model_weights": weights,
        "note": ("persistence and climatology (the bar), and our ridge model on "
                 "current temp, warm water volume, and season" if weights else
                 "persistence and climatology, the bar any model must beat"),
    })
    print(f"\nlogged to {os.path.relpath(LOG, ROOT)}")


if __name__ == "__main__":
    main()
