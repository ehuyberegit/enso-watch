"""Backfill our own Nino 3.4 daily anomaly history from PSL OISST daily means.

Walks year by year over the PSL OISST v2.1 daily mean files via OPeNDAP, box
subsets the Nino 3.4 region, and computes the daily anomaly against the frozen
1991 to 2020 climatology, reusing history.daily_series (the same transform the
gate proves offline). Writes the growing series to data/history/nino34_daily.csv
incrementally, one year at a time, so a killed run keeps its progress and can
resume. A provenance sidecar records the source, the span, and the method.

Network at the edges only. This tool is never imported by the offline gate.

Run from the repo root with the project venv:
    .venv/bin/python tools/backfill_nino34.py [start_year] [end_year]
Defaults: start_year=1982 (OISST v2.1 begins Sept 1981), end_year=current year.
"""
import csv
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from enso_watch.history import daily_series

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIM = os.path.join(ROOT, "fixtures", "oisst", "nino34_climatology_1991-2020.nc")
OUT_DIR = os.path.join(ROOT, "data", "history")
CSV_PATH = os.path.join(OUT_DIR, "nino34_daily.csv")
PROV_PATH = os.path.join(OUT_DIR, "nino34_daily.provenance.json")
SRC_TMPL = "https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.{year}.nc"
FIELDS = ["date", "nino34_anomaly_c", "region_mean_sst_c", "climatology_mean_c", "baseline"]


def _covered_years():
    """Years already present in the CSV, so a resumed run skips them."""
    if not os.path.exists(CSV_PATH):
        return set()
    years = set()
    with open(CSV_PATH) as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            years.add(row["date"][:4])
    return {int(y) for y in years}


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 1982
    end = int(sys.argv[2]) if len(sys.argv) > 2 else datetime.date.today().year
    os.makedirs(OUT_DIR, exist_ok=True)

    done = _covered_years()
    new_file = not os.path.exists(CSV_PATH)
    handle = open(CSV_PATH, "a", newline="")
    writer = csv.DictWriter(handle, fieldnames=FIELDS)
    if new_file:
        writer.writeheader()
        handle.flush()

    covered, missing, total = sorted(done), [], 0
    for year in range(start, end + 1):
        if year in done:
            print(f"  {year}: already present, skip", flush=True)
            continue
        url = SRC_TMPL.format(year=year)
        try:
            rows = daily_series(url, CLIM)
        except Exception as exc:  # a year may be absent or the server may blip
            print(f"  {year}: SKIPPED ({type(exc).__name__}: {exc})", flush=True)
            missing.append(year)
            continue
        for r in rows:
            writer.writerow(r)
        handle.flush()
        covered.append(year)
        total += len(rows)
        print(f"  {year}: {len(rows)} days  (last {rows[-1]['date']} "
              f"{rows[-1]['nino34_anomaly_c']:+.3f} C)", flush=True)
    handle.close()

    prov = {
        "product": "Nino 3.4 daily anomaly history (computed by enso-watch)",
        "source_name": "NOAA PSL OISST v2.1 daily mean",
        "dataset": "sst.day.mean.YYYY.nc via OPeNDAP",
        "retrieval_url_template": SRC_TMPL,
        "baseline": "1991-2020",
        "method": ("Nino 3.4 box (5N to 5S, 170W to 120W = lon 190 to 240 east), "
                   "cosine of latitude weighted area average, minus the frozen "
                   "1991 to 2020 daily box climatology, land and missing cells "
                   "excluded from both sides. Same transform as the live oracle."),
        "years_covered": sorted(set(covered)),
        "years_missing": sorted(missing),
        "pulled_at_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    with open(PROV_PATH, "w") as p:
        json.dump(prov, p, indent=2)
        p.write("\n")

    span = f"{min(covered)}-{max(covered)}" if covered else "none"
    print(f"done. span {span}, {total} new rows written. "
          f"missing years: {missing or 'none'}", flush=True)


if __name__ == "__main__":
    main()
