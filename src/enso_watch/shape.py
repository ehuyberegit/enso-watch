"""Offline shape validators.

Confirm a source response still has the structure the transform expects. Used by
the live smoke check (which reports, never gates) and tested against the frozen
fixtures, so a real world format drift is caught early and loudly.

Each validator returns (ok, detail): ok is a bool, detail is a small dict for
the human report.
"""
import netCDF4 as nc

OISST_REQUIRED_VARS = {"sst", "lat", "lon", "time"}
OISST_LAT_N = 720
OISST_LON_N = 1440


def check_oisst_shape(path):
    dataset = nc.Dataset(path)
    try:
        have = set(dataset.variables.keys())
        missing = sorted(OISST_REQUIRED_VARS - have)
        lat_n = dataset.variables["lat"].size if "lat" in dataset.variables else 0
        lon_n = dataset.variables["lon"].size if "lon" in dataset.variables else 0
        sst_units = getattr(dataset.variables.get("sst"), "units", "") if "sst" in dataset.variables else ""
        ok = not missing and lat_n == OISST_LAT_N and lon_n == OISST_LON_N and sst_units == "Celsius"
        return ok, {"missing_vars": missing, "lat_n": int(lat_n), "lon_n": int(lon_n), "sst_units": sst_units}
    finally:
        dataset.close()


def _numeric_rows(path):
    with open(path) as handle:
        return [r.split() for r in handle if r.strip() and r.split()[0].isdigit()]


def check_control_columns(path):
    """CPC control: data rows start with a year and carry at least 10 columns
    (through NINO3.4 ANOM at index 9)."""
    rows = _numeric_rows(path)
    ok = bool(rows) and all(len(r) >= 10 for r in rows[-3:])
    return ok, {"rows": len(rows), "last_columns": len(rows[-1]) if rows else 0}


def check_oni_columns(path):
    """CPC ONI: data rows start with a season label then a 4 digit year, and
    carry exactly 4 columns (SEAS YR TOTAL ANOM)."""
    with open(path) as handle:
        rows = [
            r.split() for r in handle
            if r.strip() and len(r.split()) >= 2 and r.split()[1].isdigit() and len(r.split()[1]) == 4
        ]
    ok = bool(rows) and all(len(r) == 4 for r in rows[-3:])
    return ok, {"rows": len(rows), "last_columns": len(rows[-1]) if rows else 0}
