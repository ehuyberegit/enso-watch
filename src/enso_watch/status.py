"""Official ENSO status from the CPC ONI ascii file.

Read the latest ONI value and derive the ENSO phase and strength band from the
documented thresholds. We derive the label ourselves from the number; we do not
scrape a rendered page. The file columns are SEAS YR TOTAL ANOM, where ANOM is
the ONI (a 3 month running mean of the Nino 3.4 anomaly).
"""
PHASE_THRESHOLD = 0.5  # degC


def _phase(oni):
    if oni >= PHASE_THRESHOLD:
        return "el_nino"
    if oni <= -PHASE_THRESHOLD:
        return "la_nina"
    return "neutral"


def _strength(oni):
    magnitude = abs(oni)
    if magnitude < 0.5:
        return "none"
    if magnitude < 1.0:
        return "weak"
    if magnitude < 1.5:
        return "moderate"
    if magnitude < 2.0:
        return "strong"
    return "very_strong"


def oni_status(oni_path):
    """Latest ONI value plus the derived phase and strength."""
    with open(oni_path) as handle:
        rows = [r.split() for r in handle if r.strip()]
    rows = [r for r in rows if len(r) >= 4 and r[1].isdigit() and len(r[1]) == 4]
    if not rows:
        raise ValueError("no ONI data rows found")
    season, year, _total, anom = rows[-1][0], int(rows[-1][1]), rows[-1][2], float(rows[-1][3])
    oni = round(anom, 3)
    return {
        "oni_latest": oni,
        "oni_season": f"{season} {year}",
        "phase": _phase(oni),
        "strength": _strength(oni),
    }
