"""Backfill our own Nino 3.4 MONTHLY anomaly history from the PSL OISST monthly mean.

The forecast model's training target. Reads the single PSL OISST v2.1 monthly
mean file (sst.mon.mean.nc, the whole record in one file) via OPeNDAP, box
subsets the Nino 3.4 region, and computes the monthly anomaly against the frozen
1991 to 2020 monthly climatology, reusing history.monthly_series (the same box
and area-average the gate proves offline). One light pull for four decades, at
the cadence the forecast runs at, rather than hundreds of heavy daily pulls.

Writes data/history/nino34_monthly.csv plus a provenance sidecar. Network at the
edges only; never imported by the offline gate.

Run from the repo root with the project venv:
    .venv/bin/python tools/backfill_nino34_monthly.py
"""
import csv
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from enso_watch.history import monthly_series

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIM = os.path.join(ROOT, "fixtures", "oisst", "nino34_monthly_climatology_1991-2020.nc")
OUT_DIR = os.path.join(ROOT, "data", "history")
CSV_PATH = os.path.join(OUT_DIR, "nino34_monthly.csv")
PROV_PATH = os.path.join(OUT_DIR, "nino34_monthly.provenance.json")
SRC = "https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.mon.mean.nc"
FIELDS = ["month", "nino34_anomaly_c", "region_mean_sst_c", "climatology_mean_c", "baseline"]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"pulling {SRC} ...", flush=True)
    rows = monthly_series(SRC, CLIM)

    tmp = CSV_PATH + ".tmp"
    with open(tmp, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, CSV_PATH)  # atomic: a killed run never commits a torn file

    prov = {
        "product": "Nino 3.4 monthly anomaly history (computed by enso-watch)",
        "source_name": "NOAA PSL OISST v2.1 monthly mean",
        "dataset": "sst.mon.mean.nc via OPeNDAP",
        "retrieval_url": SRC,
        "baseline": "1991-2020",
        "method": ("Nino 3.4 box (5N to 5S, 170W to 120W = lon 190 to 240 east), "
                   "cosine of latitude weighted area average, minus the frozen "
                   "1991 to 2020 monthly box climatology. Same box and baseline as "
                   "the live daily oracle, at the monthly cadence the forecast uses."),
        "span": [rows[0]["month"], rows[-1]["month"]] if rows else None,
        "month_count": len(rows),
        "pulled_at_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(PROV_PATH, "w") as p:
        json.dump(prov, p, indent=2)
        p.write("\n")

    span = f"{rows[0]['month']} to {rows[-1]['month']}" if rows else "none"
    print(f"done. {len(rows)} months ({span}). "
          f"last {rows[-1]['month']} {rows[-1]['nino34_anomaly_c']:+.3f} C", flush=True)


if __name__ == "__main__":
    main()
