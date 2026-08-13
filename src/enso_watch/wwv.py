"""Parse the NOAA PMEL warm water volume (WWV) monthly series.

WWV is the equatorial Pacific upper ocean heat content (the volume of water
warmer than 20 C, over 5N to 5S, 120E to 80W). Its anomaly is the precursor king
of ENSO forecasting: a build up of warm water leads an El Nino by about two
seasons, which is exactly why the forecast model reads it. Source is the GTMBA
Project Office (McPhaden), NOAA/PMEL.

The file is plain text: four attribution lines, a blank line, a "date Volume
Anomaly" header, then one row per month:

    198001 0.2609619E+16 0.8121139E+14

Volume and anomaly are in m**3. We keep them in units of 1e14 m**3 for readable
numbers (the anomaly then lands in a small single digit range). Pure and offline:
feed it text (a fixture, or a live download), it never touches the network.
"""
import re

_ROW = re.compile(r"^(\d{4})(\d{2})\s+(\S+)\s+(\S+)\s*$")
_SCALE = 1e14


def parse_wwv(text):
    """Return a list of monthly rows from the raw WWV file text.

    Each row: month (YYYY-MM), wwv_volume_1e14_m3, wwv_anomaly_1e14_m3, rounded
    to 3 decimals. Non data lines (the header and attribution) are skipped.
    """
    rows = []
    for line in text.splitlines():
        m = _ROW.match(line)
        if not m:
            continue
        year, month, volume, anomaly = m.groups()
        rows.append({
            "month": f"{year}-{month}",
            "wwv_volume_1e14_m3": round(float(volume) / _SCALE, 3),
            "wwv_anomaly_1e14_m3": round(float(anomaly) / _SCALE, 3),
        })
    return rows
