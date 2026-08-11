"""Capture the 1991 to 2020 daily SST climatology for the Nino 3.4 box.

One time fixture builder. Reads the official PSL OISST v2.1 1991 to 2020 daily
climatology over OPeNDAP and freezes only the Nino 3.4 region (5N to 5S, 170W to
120W, that is lon 190 to 240 in degrees east) across all 365 climatological days.
The full source file is 1.4 GB globally; we keep only the box (a few MB) so the
test gate stays offline and the repo stays light. Provenance is written into the
output file as global attributes.

Run from the repo root with the project venv:
    .venv/bin/python tools/capture_climatology.py
"""
import datetime

import netCDF4 as nc
import numpy as np

SRC = "https://psl.noaa.gov/thredds/dodsC/Datasets/noaa.oisst.v2.highres/sst.day.mean.ltm.1991-2020.nc"
OUT = "fixtures/oisst/nino34_climatology_1991-2020.nc"
LAT_MIN, LAT_MAX = -5.0, 5.0
LON_MIN, LON_MAX = 190.0, 240.0  # 170W to 120W, degrees east


def main():
    src = nc.Dataset(SRC)
    lat = src.variables["lat"][:]
    lon = src.variables["lon"][:]
    la = np.where((lat >= LAT_MIN) & (lat <= LAT_MAX))[0]
    lo = np.where((lon >= LON_MIN) & (lon <= LON_MAX))[0]
    # The DAP server caps response size, so read the box in time chunks and stack.
    ntime = src.dimensions["time"].size
    svar = src.variables["sst"]
    chunks = []
    step = 30
    for t0 in range(0, ntime, step):
        t1 = min(t0 + step, ntime)
        chunks.append(svar[t0:t1, la[0]:la[-1] + 1, lo[0]:lo[-1] + 1])
    sst = np.ma.concatenate(chunks, axis=0)  # (time, lat, lon)

    tvar = src.variables["time"]
    dates = nc.num2date(tvar[:], tvar.units)
    months = np.array([d.month for d in dates], dtype="i2")
    days = np.array([d.day for d in dates], dtype="i2")

    out = nc.Dataset(OUT, "w", format="NETCDF4")
    out.source_url = SRC
    out.baseline = "1991-2020"
    out.region = "Nino 3.4 (5N to 5S, 170W to 120W = lon 190 to 240 east)"
    out.note = ("Box subset of the official PSL OISST 1991 to 2020 daily "
                "climatology, built via OPeNDAP. Do not edit.")
    out.retrieved_at_utc = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
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
    vd = out.createVariable("day", "i2", ("time",))
    vd[:] = days
    vs = out.createVariable("sst", "f4", ("time", "lat", "lon"), zlib=True, complevel=4)
    vs.units = "degC"
    vs.long_name = "1991-2020 daily climatological SST"
    vs[:] = sst
    out.close()
    src.close()
    print("wrote", OUT, "shape", sst.shape)


if __name__ == "__main__":
    main()
