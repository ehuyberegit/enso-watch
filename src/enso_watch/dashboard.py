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


def write_series(repo_root: str | os.PathLike) -> Path:
    """Build the series and write it where the static page can fetch it."""
    repo_root = Path(repo_root)
    series = build_series(repo_root / "data")
    series["official"] = load_official(repo_root)
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
