"""Freeze a small Nino 3.4 daily-mean slice as an offline fixture.

One time fixture builder for the backfill test. Reads one month of the PSL OISST
v2.1 daily mean over OPeNDAP and keeps only the Nino 3.4 box (5N to 5S, 170W to
120W = lon 190 to 240 east). The full yearly file is large; the box for one month
is a few tens of KB, so the gate stays offline and the repo stays light.
Provenance is written into the output as global attributes.

Run from the repo root with the project venv:
    .venv/bin/python tools/capture_daily_sample.py
"""
import datetime
import os
import sys

import netCDF4 as nc
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import manifest

YEAR = 2024
MONTH = 1  # January 2024: a strong El Nino month, a clear non-zero anomaly
SRC = f"https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.{YEAR}.nc"
OUT = f"fixtures/oisst/nino34_daily_sample_{YEAR}-{MONTH:02d}.nc"
LAT_MIN, LAT_MAX = -5.0, 5.0
LON_MIN, LON_MAX = 190.0, 240.0  # 170W to 120W, degrees east


def main():
    src = nc.Dataset(SRC)
    lat = src.variables["lat"][:]
    lon = src.variables["lon"][:]
    la = np.where((lat >= LAT_MIN) & (lat <= LAT_MAX))[0]
    lo = np.where((lon >= LON_MIN) & (lon <= LON_MAX))[0]

    tvar = src.variables["time"]
    dates = nc.num2date(tvar[:], tvar.units)
    keep = [i for i, d in enumerate(dates) if d.year == YEAR and d.month == MONTH]
    t0, t1 = keep[0], keep[-1] + 1
    sst = src.variables["sst"][t0:t1, la[0]:la[-1] + 1, lo[0]:lo[-1] + 1]  # (time, lat, lon)
    times = tvar[t0:t1]

    out = nc.Dataset(OUT, "w", format="NETCDF4")
    out.source_url = SRC
    out.region = "Nino 3.4 (5N to 5S, 170W to 120W = lon 190 to 240 east)"
    out.note = (f"Box subset of the PSL OISST v2.1 daily mean, {YEAR}-{MONTH:02d}, "
                "built via OPeNDAP as a fixture for the history transform. Do not edit.")
    retrieved_at = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    out.retrieved_at_utc = retrieved_at
    out.createDimension("time", sst.shape[0])
    out.createDimension("lat", sst.shape[1])
    out.createDimension("lon", sst.shape[2])
    vt = out.createVariable("time", "f8", ("time",))
    vt.units = tvar.units
    if hasattr(tvar, "calendar"):
        vt.calendar = tvar.calendar
    vt[:] = times
    vlat = out.createVariable("lat", "f4", ("lat",))
    vlat.units = "degrees_north"
    vlat[:] = lat[la]
    vlon = out.createVariable("lon", "f4", ("lon",))
    vlon.units = "degrees_east"
    vlon[:] = lon[lo]
    vs = out.createVariable("sst", "f4", ("time", "lat", "lon"), zlib=True, complevel=4)
    vs.units = "degC"
    vs.long_name = f"OISST v2.1 daily mean SST, {YEAR}-{MONTH:02d}"
    vs[:] = sst
    out.close()
    src.close()
    manifest.record("oisst_nino34_daily_sample_2024_01", OUT, SRC, retrieved_at,
                    note="Box subset (Nino 3.4) of one month of the PSL OISST daily mean, "
                         "fixture for the daily history transform, built by tools/capture_daily_sample.py.")
    print("wrote", OUT, "shape", sst.shape)


if __name__ == "__main__":
    main()
