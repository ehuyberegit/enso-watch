"""Freeze the 1991 to 2020 MONTHLY SST climatology for the Nino 3.4 box.

One time fixture builder for the monthly history path. Reads the official PSL
OISST v2.1 1991 to 2020 monthly long term mean over OPeNDAP and keeps only the
Nino 3.4 box (5N to 5S, 170W to 120W = lon 190 to 240 east) across the 12
climatological months. Small (a few KB), so the gate stays offline. Provenance
is written into the output as global attributes.

Run from the repo root with the project venv:
    .venv/bin/python tools/capture_monthly_climatology.py
"""
import datetime
import os
import sys

import netCDF4 as nc
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import manifest

SRC = "https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.mon.ltm.1991-2020.nc"
OUT = "fixtures/oisst/nino34_monthly_climatology_1991-2020.nc"
LAT_MIN, LAT_MAX = -5.0, 5.0
LON_MIN, LON_MAX = 190.0, 240.0  # 170W to 120W, degrees east


def main():
    src = nc.Dataset(SRC)
    lat = src.variables["lat"][:]
    lon = src.variables["lon"][:]
    la = np.where((lat >= LAT_MIN) & (lat <= LAT_MAX))[0]
    lo = np.where((lon >= LON_MIN) & (lon <= LON_MAX))[0]
    sst = src.variables["sst"][:, la[0]:la[-1] + 1, lo[0]:lo[-1] + 1]  # (12, lat, lon)
    tvar = src.variables["time"]
    dates = nc.num2date(tvar[:], tvar.units)
    months = np.array([d.month for d in dates], dtype="i2")

    out = nc.Dataset(OUT, "w", format="NETCDF4")
    out.source_url = SRC
    out.baseline = "1991-2020"
    out.region = "Nino 3.4 (5N to 5S, 170W to 120W = lon 190 to 240 east)"
    out.note = ("Box subset of the PSL OISST v2.1 1991 to 2020 monthly long term "
                "mean, built via OPeNDAP. Do not edit.")
    retrieved_at = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    out.retrieved_at_utc = retrieved_at
    out.createDimension("time", sst.shape[0])
    out.createDimension("lat", sst.shape[1])
    out.createDimension("lon", sst.shape[2])
    vlat = out.createVariable("lat", "f4", ("lat",))
    vlat.units = "degrees_north"
    vlat[:] = lat[la]
    vlon = out.createVariable("lon", "f4", ("lon",))
    vlon.units = "degrees_east"
    vlon[:] = lon[lo]
    vm = out.createVariable("month", "i2", ("time",))
    vm[:] = months
    vs = out.createVariable("sst", "f4", ("time", "lat", "lon"), zlib=True, complevel=4)
    vs.units = "degC"
    vs.long_name = "1991-2020 monthly climatological SST"
    vs[:] = sst
    out.close()
    src.close()
    manifest.record("oisst_nino34_monthly_climatology_1991_2020", OUT, SRC, retrieved_at,
                    note="Box subset (Nino 3.4) of the PSL OISST 1991-2020 monthly long term mean, "
                         "the monthly baseline, built by tools/capture_monthly_climatology.py.")
    print("wrote", OUT, "shape", sst.shape, "months", list(months))


if __name__ == "__main__":
    main()
