"""Compute a Nino 3.4 daily anomaly series from an OISST daily-mean source.

The backfill's load-bearing module. Given a source of daily sea surface
temperature on the OISST 0.25 degree grid (a local netCDF fixture, or a PSL
OPeNDAP url) with variables lat, lon, time, sst(time, lat, lon), and the frozen
1991 to 2020 box climatology, it produces one anomaly row per day, reusing the
exact box, cosine weighted area-average, and climatology-index logic of nino34.py.

It is offline-testable: point it at a captured fixture slice and it is fully
deterministic, no network. The live backfill (tools/backfill_nino34.py) points
it at PSL OPeNDAP urls; the gate points it at a frozen fixture.

Note the shape difference from nino34.py: the live daily pull reads NCEI files
with sst(time, zlev, lat, lon), while the PSL daily means read here are
sst(time, lat, lon) with no zlev level. Same grid, same box, same climatology,
so the anomaly is comparable; only the array indexing differs, which is why this
is a separate function rather than a reuse of nino34_anomaly.
"""
import netCDF4 as nc
import numpy as np

from enso_watch.nino34 import _area_average, _box_indices, _climatology_index, BASELINE


def _climatology_box_means(clim, lat_box):
    """Precompute the area-averaged climatology of the box for every stored day.

    Returns (cmonth, cday, means) so a lookup by calendar (month, day) is one
    index, not a re-average per observed day.
    """
    cmonth = clim.variables["month"][:]
    cday = clim.variables["day"][:]
    clat = clim.variables["lat"][:]
    if not np.allclose(clat, lat_box):
        raise ValueError("climatology box latitudes do not align with the SST grid")
    csst = clim.variables["sst"][:, :, :]  # (time, lat, lon)
    means = np.array([_area_average(csst[r], clat) for r in range(csst.shape[0])])
    return cmonth, cday, means


def daily_series(sst_source, climatology_path, chunk=30):
    """Return a list of anomaly rows, one per day, for a daily-mean SST source.

    Each row: date (YYYY-MM-DD), nino34_anomaly_c, region_mean_sst_c,
    climatology_mean_c, baseline. Values rounded to 3 decimals, the frozen
    precision of the run contract. The box SST is read in time chunks so a large
    OPeNDAP response stays under the server's size cap.
    """
    src = nc.Dataset(sst_source)
    try:
        lat = src.variables["lat"][:]
        lon = src.variables["lon"][:]
        la, lo = _box_indices(lat, lon)
        lat_box = lat[la]

        tvar = src.variables["time"]
        ntime = src.dimensions["time"].size
        dates = nc.num2date(tvar[:], tvar.units)

        clim = nc.Dataset(climatology_path)
        try:
            cmonth, cday, clim_means = _climatology_box_means(clim, lat_box)
        finally:
            clim.close()

        svar = src.variables["sst"]
        rows = []
        for t0 in range(0, ntime, chunk):
            t1 = min(t0 + chunk, ntime)
            block = svar[t0:t1, la[0]:la[-1] + 1, lo[0]:lo[-1] + 1]  # (t, lat, lon)
            for k in range(t1 - t0):
                d = dates[t0 + k]
                region_mean = _area_average(block[k], lat_box)
                row = _climatology_index(cmonth, cday, d.month, d.day)
                clim_mean = float(clim_means[row])
                rows.append({
                    "date": f"{d.year:04d}-{d.month:02d}-{d.day:02d}",
                    "nino34_anomaly_c": round(region_mean - clim_mean, 3),
                    "region_mean_sst_c": round(region_mean, 3),
                    "climatology_mean_c": round(clim_mean, 3),
                    "baseline": BASELINE,
                })
        return rows
    finally:
        src.close()


def _monthly_climatology_means(clim, lat_box):
    """Area-averaged 1991 to 2020 climatology of the box for each calendar month.

    Returns a dict {month: mean} for months 1 to 12, so a monthly observation is
    a single lookup by its calendar month.
    """
    cmonth = clim.variables["month"][:]
    clat = clim.variables["lat"][:]
    if not np.allclose(clat, lat_box):
        raise ValueError("climatology box latitudes do not align with the SST grid")
    csst = clim.variables["sst"][:, :, :]  # (12, lat, lon)
    return {int(cmonth[r]): _area_average(csst[r], clat) for r in range(csst.shape[0])}


def monthly_series(mon_sst_source, monthly_climatology_path, chunk=120):
    """Return a list of monthly anomaly rows for a monthly-mean SST source.

    The history path for the forecast model. Given the PSL OISST monthly mean
    (sst.mon.mean.nc, variables lat, lon, time, sst(time, lat, lon)) and the
    frozen 1991 to 2020 monthly box climatology, it produces one row per month,
    reusing the same box and cosine weighted area-average as the daily oracle,
    only at the cadence the forecast runs at (Nino 3.4 is a monthly index).

    Each row: month (YYYY-MM), nino34_anomaly_c, region_mean_sst_c,
    climatology_mean_c, baseline. Values rounded to 3 decimals. Offline-testable
    against a captured fixture; the live backfill points it at a PSL url.
    """
    src = nc.Dataset(mon_sst_source)
    try:
        lat = src.variables["lat"][:]
        lon = src.variables["lon"][:]
        la, lo = _box_indices(lat, lon)
        lat_box = lat[la]

        tvar = src.variables["time"]
        ntime = src.dimensions["time"].size
        dates = nc.num2date(tvar[:], tvar.units)

        clim = nc.Dataset(monthly_climatology_path)
        try:
            clim_means = _monthly_climatology_means(clim, lat_box)
        finally:
            clim.close()

        svar = src.variables["sst"]
        rows = []
        for t0 in range(0, ntime, chunk):
            t1 = min(t0 + chunk, ntime)
            block = svar[t0:t1, la[0]:la[-1] + 1, lo[0]:lo[-1] + 1]  # (t, lat, lon)
            for k in range(t1 - t0):
                d = dates[t0 + k]
                region_mean = _area_average(block[k], lat_box)
                clim_mean = float(clim_means[d.month])
                rows.append({
                    "month": f"{d.year:04d}-{d.month:02d}",
                    "nino34_anomaly_c": round(region_mean - clim_mean, 3),
                    "region_mean_sst_c": round(region_mean, 3),
                    "climatology_mean_c": round(clim_mean, 3),
                    "baseline": BASELINE,
                })
        return rows
    finally:
        src.close()
