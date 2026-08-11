"""Compute the Nino 3.4 SST anomaly from an OISST daily file.

We compute the anomaly ourselves (the load bearing piece of enso-watch) rather
than copy a published number. The steps:

1. Area average the Nino 3.4 box (5N to 5S, 170W to 120W, that is lon 190 to 240
   east) of the daily OISST sea surface temperature.
2. Area average the 1991 to 2020 daily climatology of the same box, for the same
   day of the year.
3. The anomaly is the difference.

Area averaging is cosine of latitude weighted, and land or missing cells are
excluded from both the field and its weights.
"""
import netCDF4 as nc
import numpy as np

LAT_MIN, LAT_MAX = -5.0, 5.0
LON_MIN, LON_MAX = 190.0, 240.0  # 170W to 120W, degrees east
BASELINE = "1991-2020"


def _box_indices(lat, lon):
    la = np.where((lat >= LAT_MIN) & (lat <= LAT_MAX))[0]
    lo = np.where((lon >= LON_MIN) & (lon <= LON_MAX))[0]
    return la, lo


def _area_average(field, lat_box):
    """Cosine of latitude weighted mean of a (lat, lon) masked field."""
    w = np.cos(np.deg2rad(np.asarray(lat_box)))[:, None]  # (lat, 1)
    weights = np.broadcast_to(w, field.shape)
    mask = np.ma.getmaskarray(field)
    weights = np.ma.array(weights, mask=mask)
    return float(np.ma.average(field, weights=weights))


def _oisst_date(ds):
    tvar = ds.variables["time"]
    return nc.num2date(tvar[0], tvar.units)


def _climatology_index(cmonth, cday, month, day):
    """Row of the 365 day climatology for a calendar month and day.

    Leap day policy: the 1991 to 2020 daily climatology has 365 entries and no
    February 29. A February 29 observation is mapped to the February 28
    climatology, a documented and fixed choice (never changed silently).
    """
    idx = np.where((cmonth == month) & (cday == day))[0]
    if idx.size == 0 and (month, day) == (2, 29):
        idx = np.where((cmonth == 2) & (cday == 28))[0]
    if idx.size != 1:
        raise ValueError(
            f"climatology has {idx.size} entries for {month:02d}-{day:02d}, expected 1"
        )
    return int(idx[0])


def nino34_anomaly(oisst_path, climatology_path):
    """Return the Nino 3.4 anomaly and its parts for one OISST daily file.

    Both files must sit on the same 0.25 degree grid. Values are rounded to 3
    decimals, the frozen precision of the run contract.
    """
    ds = nc.Dataset(oisst_path)
    lat = ds.variables["lat"][:]
    lon = ds.variables["lon"][:]
    la, lo = _box_indices(lat, lon)
    lat_box = lat[la]
    sst = ds.variables["sst"][0, 0, la[0]:la[-1] + 1, lo[0]:lo[-1] + 1]  # (lat, lon)
    date = _oisst_date(ds)
    region_mean = _area_average(sst, lat_box)
    ds.close()

    clim = nc.Dataset(climatology_path)
    cmonth = clim.variables["month"][:]
    cday = clim.variables["day"][:]
    row = _climatology_index(cmonth, cday, date.month, date.day)
    clat = clim.variables["lat"][:]
    if not np.allclose(clat, lat_box):
        raise ValueError("climatology box latitudes do not align with the OISST grid")
    csst = clim.variables["sst"][row, :, :]  # (lat, lon)
    clim_mean = _area_average(csst, clat)
    clim.close()

    anomaly = region_mean - clim_mean
    return {
        "date": f"{date.year:04d}-{date.month:02d}-{date.day:02d}",
        "nino34_anomaly_c": round(anomaly, 3),
        "region_mean_sst_c": round(region_mean, 3),
        "climatology_mean_c": round(clim_mean, 3),
        "baseline": BASELINE,
    }
