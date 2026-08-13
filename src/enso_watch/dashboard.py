"""The local dashboard: a private, read only view over the committed JSON.

It invents nothing. It reads the dated product files under data/, merges them into
one time series (derived, never a new source of truth), and serves a static page on
localhost. The truth stays the JSON in git; this is a lens on it.

`build_series(data_dir)` is pure and offline, so the machine gate can test it.
`serve()` wires the build to python's stdlib http server and opens the browser.
"""

from __future__ import annotations

import glob
import http.server
import json
import os
import socketserver
import webbrowser
from pathlib import Path

# Preliminary records get replaced by final ones for the same date. If two files
# ever carry the same date, the more settled status wins.
_STATUS_RANK = {"final": 3, "published": 2, "preliminary": 1}


def _record_status_rank(record: dict) -> int:
    prov = record.get("provenance") or {}
    return _STATUS_RANK.get(prov.get("status"), 0)


def build_series(data_dir: str | os.PathLike) -> dict:
    """Merge every dated product file into one series, sorted by date.

    Returns a dict with the full daily series (deduped by date), the latest status
    record, and the list of source files it was derived from. Pure and offline.
    """
    data_dir = Path(data_dir)
    files = sorted(glob.glob(str(data_dir / "enso-watch-*.json")))

    daily_by_date: dict[str, dict] = {}
    status_by_date: dict[str, dict] = {}

    for path in files:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        for rec in doc.get("daily_series", []):
            date = rec.get("date")
            if date is None:
                continue
            prev = daily_by_date.get(date)
            # keep the more settled record when a date repeats
            if prev is None or _record_status_rank(rec) >= _record_status_rank(prev):
                daily_by_date[date] = rec
        status = doc.get("status")
        if status is not None:
            # key the status by the file's own latest daily date, so the newest wins
            dates = [r.get("date") for r in doc.get("daily_series", []) if r.get("date")]
            key = max(dates) if dates else Path(path).stem
            status_by_date[key] = status

    daily = [daily_by_date[d] for d in sorted(daily_by_date)]
    latest_status = None
    if status_by_date:
        latest_status = status_by_date[max(status_by_date)]

    return {
        "daily_series": daily,
        "status": latest_status,
        "record_count": len(daily),
        "source_files": [Path(p).name for p in files],
    }


def load_official(repo_root: str | os.PathLike, months: int = 48, seasons: int = 24) -> dict:
    """The official reference to compare against, windowed to a recent slice.

    Prefers the live product (data/official.json, refreshed by the pull). Falls
    back to the frozen fixture when the live one is absent (a clean checkout that
    has never pulled), and says which basis it used so the UI can be honest.
    """
    from enso_watch.official import build_official

    repo_root = Path(repo_root)
    live = repo_root / "data" / "official.json"
    if live.exists():
        official = json.loads(live.read_text(encoding="utf-8"))
        basis = "live pull"
    else:
        fix = repo_root / "fixtures" / "cpc"
        official = build_official(
            fix / "ersst5.nino.mth.91-20.ascii",
            fix / "oni.ascii.txt",
            {"source": "NOAA CPC Nino3.4 monthly", "note": "frozen fixture"},
            {"source": "NOAA CPC ONI", "note": "frozen fixture"},
        )
        basis = "frozen fixture (no live pull yet)"

    m = official.get("monthly_nino34", {})
    o = official.get("oni_seasonal", {})
    return {
        "basis": basis,
        "monthly_nino34": {"series": (m.get("series") or [])[-months:], "provenance": m.get("provenance")},
        "oni_seasonal": {"series": (o.get("series") or [])[-seasons:], "provenance": o.get("provenance")},
    }


def load_history(repo_root: str | os.PathLike) -> dict:
    """The training data ingredient: our own Nino 3.4 monthly anomaly history.

    Reads the backfilled CSV (data/history/nino34_monthly.csv), one row per month
    over the whole OISST record, computed by us at the cadence the forecast runs
    at. Pure and offline: it reads a committed file, never the network, and
    invents nothing. Returns a "not available yet" shape while the file is absent.
    """
    import csv as _csv

    repo_root = Path(repo_root)
    path = repo_root / "data" / "history" / "nino34_monthly.csv"
    if not path.exists():
        return {"available": False}

    monthly = []
    latest_row = None
    with open(path, encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            month = row.get("month")
            try:
                val = float(row["nino34_anomaly_c"])
            except (KeyError, ValueError, TypeError):
                continue  # skip a torn line from an in-flight write
            if not month:
                continue
            monthly.append({"ym": month, "mean": round(val, 3)})
            if latest_row is None or month > latest_row["month"]:
                latest_row = row

    monthly.sort(key=lambda m: m["ym"])
    prov_path = repo_root / "data" / "history" / "nino34_monthly.provenance.json"
    provenance = json.loads(prov_path.read_text(encoding="utf-8")) if prov_path.exists() else None

    return {
        "available": len(monthly) > 0,
        "month_count": len(monthly),
        "span": [monthly[0]["ym"], monthly[-1]["ym"]] if monthly else [None, None],
        "monthly": monthly,
        "latest": ({"month": latest_row["month"], "anomaly_c": round(float(latest_row["nino34_anomaly_c"]), 3)}
                   if latest_row else None),
        "provenance": provenance,
    }


def load_wwv(repo_root: str | os.PathLike) -> dict:
    """The precursor ingredient: NOAA PMEL warm water volume monthly anomaly.

    Reads data/history/wwv_monthly.csv (ingested from PMEL), the ENSO precursor
    whose anomaly leads Nino 3.4 by about two seasons. Pure and offline. Returns
    a "not available yet" shape while the file is absent.
    """
    import csv as _csv

    repo_root = Path(repo_root)
    path = repo_root / "data" / "history" / "wwv_monthly.csv"
    if not path.exists():
        return {"available": False}

    monthly = []
    latest_row = None
    with open(path, encoding="utf-8") as fh:
        for row in _csv.DictReader(fh):
            month = row.get("month")
            try:
                anom = float(row["wwv_anomaly_1e14_m3"])
            except (KeyError, ValueError, TypeError):
                continue
            if not month:
                continue
            monthly.append({"ym": month, "anomaly": round(anom, 3)})
            if latest_row is None or month > latest_row["month"]:
                latest_row = row

    monthly.sort(key=lambda m: m["ym"])
    prov_path = repo_root / "data" / "history" / "wwv_monthly.provenance.json"
    provenance = json.loads(prov_path.read_text(encoding="utf-8")) if prov_path.exists() else None

    return {
        "available": len(monthly) > 0,
        "month_count": len(monthly),
        "span": [monthly[0]["ym"], monthly[-1]["ym"]] if monthly else [None, None],
        "monthly": monthly,
        "latest": ({"month": latest_row["month"], "anomaly": round(float(latest_row["wwv_anomaly_1e14_m3"]), 3)}
                   if latest_row else None),
        "provenance": provenance,
    }


SKILL_LEADS = (1, 2, 3, 6)
SKILL_MIN_TRAIN = 120


def load_skill(history: dict, wwv: dict) -> dict:
    """Score the baselines and our model from the history, for the Skill tab.

    Pure and offline. Runs the walk forward evaluation of persistence and
    climatology (the bar to beat), and, when the warm water volume is available,
    our ridge model on the same window, so the three sit side by side. Returns a
    "not available" shape until there is enough history.
    """
    from enso_watch import skill, model

    monthly = (history or {}).get("monthly") or []
    values = [m["mean"] for m in monthly]
    if len(values) <= SKILL_MIN_TRAIN + max(SKILL_LEADS):
        return {"available": False, "leads": list(SKILL_LEADS), "min_train": SKILL_MIN_TRAIN}

    board = skill.evaluate(values, leads=SKILL_LEADS, min_train=SKILL_MIN_TRAIN)
    out = {
        "available": True,
        "leads": list(SKILL_LEADS),
        "min_train": SKILL_MIN_TRAIN,
        "n_months": len(values),
        "board": board,
        "model_available": False,
    }
    wwv_monthly = (wwv or {}).get("monthly") or []
    if wwv_monthly:
        m = model.evaluate_model(monthly, wwv_monthly, leads=SKILL_LEADS,
                                 min_train=SKILL_MIN_TRAIN, with_hindcast=True)
        if m.get("available"):
            board["model"] = m["board"]
            out["model_available"] = True
            out["weights"] = m["weights"]
            out["weights_lead"] = m["weights_lead"]
            out["hindcast"] = m["hindcast"]
    return out


def load_official_forecast(repo_root: str | os.PathLike) -> dict | None:
    """The ingested official CPC ENSO probability forecast, if present."""
    path = Path(repo_root) / "data" / "forecast" / "cpc_official.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_forecast(history: dict, wwv: dict, official: dict | None) -> dict:
    """Compare our forward forecast to the official CPC probabilities, for the Forecast tab.

    Pure and offline: runs our model forward from the latest data, turns it into
    phase probabilities, and measures agreement with the official forecast. Returns
    a "not available" shape until both the model and the official forecast exist.
    """
    from enso_watch import model

    if not official:
        return {"available": False, "reason": "no official forecast ingested"}
    monthly = (history or {}).get("monthly") or []
    wwv_monthly = (wwv or {}).get("monthly") or []
    if not wwv_monthly:
        return {"available": False, "reason": "no warm water volume"}
    cmp = model.compare_to_official(monthly, wwv_monthly, official, min_train=SKILL_MIN_TRAIN)
    if not cmp.get("available"):
        return {"available": False, "reason": "not enough overlap"}
    # the recent actual tail through the LATEST month, so the chart shows the real
    # value even past the issue month (the warm water volume lags), and the forecast
    # can be seen against it rather than hiding the gap
    cmp["recent"] = [{"month": m["ym"], "value": m["mean"]} for m in monthly][-30:]
    return cmp


def load_peak(history: dict, wwv: dict) -> dict:
    """Forecast the current event's peak (timing, magnitude, uncertainty), for the Forecast tab."""
    from enso_watch import peak

    monthly = (history or {}).get("monthly") or []
    wwv_monthly = (wwv or {}).get("monthly") or []
    if not wwv_monthly:
        return {"available": False}
    return peak.forecast_peak(monthly, wwv_monthly)


def load_experiments(repo_root: str | os.PathLike) -> list:
    """The experiment log: every scored run, newest first, for the Skill tab."""
    from enso_watch.experiments import read_experiments

    runs = read_experiments(Path(repo_root) / "data" / "experiments.jsonl")
    runs.sort(key=lambda r: r.get("at_utc", ""), reverse=True)
    return runs


def _provisional_month(history: dict, daily_series: list) -> dict | None:
    """A month-to-date estimate for the current month, from the daily values.

    The monthly history lags (it needs a full month), but we already have daily
    readings for the running month. Averaging them gives a provisional current
    month so the forecast starts from the real current state instead of pretending
    to predict a month we are already observing. Marked provisional and carries the
    number of days it averages, because early in the month it rests on few days.
    """
    monthly = (history or {}).get("monthly") or []
    if not monthly or not daily_series:
        return None
    last_ym = monthly[-1]["ym"]
    sums: dict[str, list] = {}
    for r in daily_series:
        ym = (r.get("date") or "")[:7]
        val = r.get("nino34_anomaly_c")
        if len(ym) == 7 and ym > last_ym and val is not None:
            acc = sums.setdefault(ym, [0.0, 0])
            acc[0] += val
            acc[1] += 1
    if not sums:
        return None
    ym = max(sums)
    total, n = sums[ym]
    return {"ym": ym, "mean": round(total / n, 3), "provisional": True, "n_days": n}


def _with_provisional(history: dict, prov: dict | None) -> dict:
    if not prov:
        return history
    return {**history, "monthly": ((history or {}).get("monthly") or []) + [{"ym": prov["ym"], "mean": prov["mean"]}]}


def _freshness(series: dict) -> dict:
    """When each stream was last updated, since they refresh at different rates."""
    daily = series.get("daily_series") or []
    dl = daily[-1] if daily else None
    dprov = (dl or {}).get("provenance") or {}
    of = series.get("official_forecast") or {}
    return {
        "daily": ({"date": dl["date"], "value": dl["nino34_anomaly_c"],
                   "status": dprov.get("status"), "pulled_at": dprov.get("pull_timestamp")}
                  if dl else None),
        "monthly": (series.get("history") or {}).get("latest"),
        "provisional_month": series.get("provisional_month"),
        "wwv": (series.get("wwv") or {}).get("latest"),
        "official_forecast": of.get("issued"),
    }


def write_series(repo_root: str | os.PathLike) -> Path:
    """Build the series and write it where the static page can fetch it."""
    repo_root = Path(repo_root)
    series = build_series(repo_root / "data")
    series["official"] = load_official(repo_root)
    series["history"] = load_history(repo_root)
    series["wwv"] = load_wwv(repo_root)
    series["skill"] = load_skill(series["history"], series["wwv"])
    series["official_forecast"] = load_official_forecast(repo_root)
    # bring the current month's daily readings into the model's current state, so the
    # forecast starts from reality (about +2.7 now) rather than the last full month
    prov = _provisional_month(series["history"], series.get("daily_series") or [])
    series["provisional_month"] = prov
    hist_now = _with_provisional(series["history"], prov)
    series["forecast"] = load_forecast(hist_now, series["wwv"], series["official_forecast"])
    series["peak"] = load_peak(hist_now, series["wwv"])
    series["experiments"] = load_experiments(repo_root)
    series["freshness"] = _freshness(series)
    out = repo_root / "ui" / "series.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(series, fh, indent=2)
    return out


def serve(port: int = 8000) -> None:
    """Rebuild the derived series, then serve the repo statically and open the UI."""
    repo_root = Path(__file__).resolve().parents[2]
    out = write_series(repo_root)
    print(f"built {out.relative_to(repo_root)} ({json.loads(out.read_text())['record_count']} days)")

    os.chdir(repo_root)
    handler = http.server.SimpleHTTPRequestHandler
    # If the requested port is taken, let the OS pick a free one (port 0).
    try:
        httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    except OSError:
        httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    with httpd:
        actual = httpd.server_address[1]
        url = f"http://127.0.0.1:{actual}/ui/"
        print(f"serving enso-watch dashboard at {url}")
        print("private and local. Ctrl-C to stop.")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped.")


if __name__ == "__main__":
    serve()
