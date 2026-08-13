"""Freeze a small Nino 3.4 monthly-mean slice as an offline fixture.

One time fixture builder for the monthly history test. Reads two years of the
PSL OISST v2.1 monthly mean over OPeNDAP and keeps only the Nino 3.4 box. Small,
so the gate stays offline. Provenance is written as global attributes.

Run from the repo root with the project venv:
    .venv/bin/python tools/capture_monthly_sample.py
"""
import datetime
import os
import sys

import netCDF4 as nc
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import manifest

SRC = "https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.mon.mean.nc"
OUT = "fixtures/oisst/nino34_monthly_sample_2023-2024.nc"
LAT_MIN, LAT_MAX = -5.0, 5.0
LON_MIN, LON_MAX = 190.0, 240.0  # 170W to 120W, degrees east
Y0, Y1 = 2023, 2024  # a full El Nino build and its decay: clear non-zero anomalies


def main():
    src = nc.Dataset(SRC)
    lat = src.variables["lat"][:]
    lon = src.variables["lon"][:]
    la = np.where((lat >= LAT_MIN) & (lat <= LAT_MAX))[0]
    lo = np.where((lon >= LON_MIN) & (lon <= LON_MAX))[0]

    tvar = src.variables["time"]
    dates = nc.num2date(tvar[:], tvar.units)
    keep = [i for i, d in enumerate(dates) if Y0 <= d.year <= Y1]
    t0, t1 = keep[0], keep[-1] + 1
    sst = src.variables["sst"][t0:t1, la[0]:la[-1] + 1, lo[0]:lo[-1] + 1]
    times = tvar[t0:t1]

    out = nc.Dataset(OUT, "w", format="NETCDF4")
    out.source_url = SRC
    out.region = "Nino 3.4 (5N to 5S, 170W to 120W = lon 190 to 240 east)"
    out.note = (f"Box subset of the PSL OISST v2.1 monthly mean, {Y0} to {Y1}, "
                "built via OPeNDAP as a fixture for the monthly history transform. Do not edit.")
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
    vs.long_name = f"OISST v2.1 monthly mean SST, {Y0} to {Y1}"
    vs[:] = sst
    out.close()
    src.close()
    manifest.record("oisst_nino34_monthly_sample_2023_2024", OUT, SRC, retrieved_at,
                    note="Box subset (Nino 3.4) of two years of the PSL OISST monthly mean, "
                         "fixture for the monthly history transform, built by tools/capture_monthly_sample.py.")
    print("wrote", OUT, "shape", sst.shape)


if __name__ == "__main__":
    main()
