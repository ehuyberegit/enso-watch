"""Ingest the NOAA PMEL warm water volume monthly series into the history.

Downloads the live wwv.dat (the ENSO precursor, full basin 5N-5S 120E-80W),
parses it with wwv.parse_wwv (the same parser the gate proves offline on a
fixture), and writes data/history/wwv_monthly.csv plus a provenance sidecar.

Network at the edges only; never imported by the offline gate.

Run from the repo root with the project venv:
    .venv/bin/python tools/ingest_wwv.py
"""
import csv
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from enso_watch import sources
from enso_watch.wwv import parse_wwv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "history")
CSV_PATH = os.path.join(OUT_DIR, "wwv_monthly.csv")
PROV_PATH = os.path.join(OUT_DIR, "wwv_monthly.provenance.json")
FIELDS = ["month", "wwv_volume_1e14_m3", "wwv_anomaly_1e14_m3"]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"pulling {sources.WWV_URL} ...", flush=True)
    raw = sources.download(sources.WWV_URL, os.path.join(ROOT, "data", "_incoming", "wwv.dat"))
    with open(raw, encoding="utf-8") as fh:
        rows = parse_wwv(fh.read())
    if not rows:
        raise RuntimeError("WWV parse produced no rows (source format may have changed)")

    tmp = CSV_PATH + ".tmp"
    with open(tmp, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, CSV_PATH)

    prov = {
        "product": "Warm water volume monthly anomaly (NOAA PMEL, ingested by enso-watch)",
        "source_name": "NOAA PMEL GTMBA warm water volume",
        "dataset": "wwv.dat, full basin 5N-5S 120E-80W",
        "retrieval_url": sources.WWV_URL,
        "units": "1e14 m^3",
        "note": ("Upper ocean heat content (volume above the 20 C isotherm). Its "
                 "anomaly leads Nino 3.4 by about two seasons, the model's precursor."),
        "span": [rows[0]["month"], rows[-1]["month"]],
        "month_count": len(rows),
        "pulled_at_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(PROV_PATH, "w") as p:
        json.dump(prov, p, indent=2)
        p.write("\n")

    print(f"done. {len(rows)} months ({rows[0]['month']} to {rows[-1]['month']}). "
          f"last anomaly {rows[-1]['wwv_anomaly_1e14_m3']:+.3f} (1e14 m^3)", flush=True)


if __name__ == "__main__":
    main()
