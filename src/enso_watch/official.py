"""The official reference series, parsed from the CPC ascii files.

Two official curves we compare ourselves against, both on the same 1991 to 2020
base as our own computation:
  - the monthly Nino 3.4 anomaly (ersst5.nino.mth.91-20.ascii, last ANOM column),
    the same quantity we compute daily from OISST, but monthly averaged;
  - the seasonal ONI (oni.ascii.txt), a 3 month running mean of that anomaly, the
    official ENSO index.

These are the CONTROL, never the source: we compute our own daily number and show
the gap. Pure and offline, so the gate can test the parsing against the fixtures.
"""

from __future__ import annotations


def parse_monthly_nino34(path):
    """Official monthly Nino 3.4 anomaly, oldest first.

    File columns: YR MON NINO1+2 ANOM NINO3 ANOM NINO4 ANOM NINO3.4 ANOM.
    The Nino 3.4 anomaly is the last column.
    """
    series = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            fields = line.split()
            if len(fields) < 10 or not fields[0].isdigit():
                continue
            series.append({
                "year": int(fields[0]),
                "month": int(fields[1]),
                "anomaly_c": round(float(fields[9]), 3),
            })
    return series


def parse_oni_seasonal(path):
    """Official seasonal ONI, oldest first. Columns: SEAS YR TOTAL ANOM."""
    series = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            fields = line.split()
            if len(fields) < 4 or not (fields[1].isdigit() and len(fields[1]) == 4):
                continue
            series.append({
                "season": fields[0],
                "year": int(fields[1]),
                "oni": round(float(fields[3]), 3),
            })
    return series


def build_official(control_path, oni_path, provenance_control, provenance_oni):
    """Assemble the official reference product, each series with its provenance."""
    return {
        "monthly_nino34": {
            "series": parse_monthly_nino34(control_path),
            "provenance": provenance_control,
        },
        "oni_seasonal": {
            "series": parse_oni_seasonal(oni_path),
            "provenance": provenance_oni,
        },
    }
