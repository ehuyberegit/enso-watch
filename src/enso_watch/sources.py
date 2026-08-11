"""Live source access for the daily pull.

Network at the edges only. This module is never imported by the offline gate.
It builds the real source URLs, checks existence, downloads, and resolves the
latest available OISST day (final if present, else the preliminary file).

Network I/O goes through curl, not Python's stdlib urllib. curl is ubiquitous
(present on the CI runners too), respects the environment's proxy, and gives us
exit codes that cleanly separate a genuine HTTP 404 (absent) from a transient
network failure, so the walk back never mistakes a blip for an absent day. It
also sidesteps a urllib/TLS hang seen against some NOAA hosts on the stock macOS
Python.
"""
import datetime
import os
import subprocess

OISST_BASE = (
    "https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation"
    "/v2.1/access/avhrr"
)
ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
CONTROL_URL = "https://www.cpc.ncep.noaa.gov/data/indices/ersst5.nino.mth.91-20.ascii"

def oisst_url(date, preliminary=False):
    """The daily OISST netCDF url for a date (a datetime.date)."""
    ym = f"{date.year:04d}{date.month:02d}"
    ymd = f"{date.year:04d}{date.month:02d}{date.day:02d}"
    suffix = "_preliminary" if preliminary else ""
    return f"{OISST_BASE}/{ym}/oisst-avhrr-v02r01.{ymd}{suffix}.nc"


def url_exists(url, timeout=30):
    """True only on HTTP 200, False only on a genuine 404, raise on anything else.

    We read the real HTTP status code rather than infer it from curl's collapsed
    exit code: `curl --fail` returns the same code for 404 and for 403, 429, 500,
    503. Reading `%{http_code}` lets a transient block or server error raise
    (loud) instead of being misread as an absent file (silent stale day), which
    "false by default" forbids.
    """
    result = subprocess.run(
        ["curl", "-sS", "-I", "-o", os.devnull, "-w", "%{http_code}",
         "--max-time", str(timeout), url],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"existence check failed (network) for {url}: curl exit {result.returncode} {result.stderr.strip()}")
    code = result.stdout.strip()
    if code == "200":
        return True
    if code == "404":
        return False
    raise RuntimeError(f"existence check for {url} returned HTTP {code}")


def download(url, dest, timeout=180):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    result = subprocess.run(
        ["curl", "-sS", "--fail", "--max-time", str(timeout), "-o", dest, url],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"download failed for {url}: curl exit {result.returncode} {result.stderr.strip()}")
    return dest


def resolve_oisst(date):
    """Return (url, status) for a date: final if present, else preliminary, else (None, None)."""
    final = oisst_url(date, preliminary=False)
    if url_exists(final):
        return final, "final"
    prelim = oisst_url(date, preliminary=True)
    if url_exists(prelim):
        return prelim, "preliminary"
    return None, None


def resolve_latest(start_date, max_back_days=7):
    """Walk back from start_date to find the most recent available OISST day.

    Returns (date, url, status) or (None, None, None). OISST daily has a short
    lag, so the newest day is often a day or two back, and often preliminary. A
    transient error propagates (url_exists raises), it is not swallowed as absence.
    """
    for offset in range(max_back_days):
        day = start_date - datetime.timedelta(days=offset)
        url, status = resolve_oisst(day)
        if url:
            return day, url, status
    return None, None, None
