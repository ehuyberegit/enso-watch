"""The live daily pull: download the real sources, run the same transform, write
the dated JSON product.

Network at the edges only; the transform and the output contract are identical to
the offline path. The 1991 to 2020 box climatology is the frozen fixture (a fixed
baseline, not a daily pull). Raw downloads land in data/_incoming (gitignored);
the product lands in data/ as a dated JSON.
"""
import datetime
import json
import os

from enso_watch import sources
from enso_watch.output import build_output
from enso_watch.provenance import provenance_block

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLIMATOLOGY = os.path.join(ROOT, "fixtures", "oisst", "nino34_climatology_1991-2020.nc")
INCOMING = os.path.join(ROOT, "data", "_incoming")
OUT_DIR = os.path.join(ROOT, "data")


def _now_utc():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def pull(start_date=None):
    start = start_date or datetime.datetime.utcnow().date()
    day, oisst_u, status = sources.resolve_latest(start)
    if not day:
        raise RuntimeError("no OISST daily file found in the recent window")

    oisst_path = sources.download(oisst_u, os.path.join(INCOMING, os.path.basename(oisst_u)))
    oni_path = sources.download(sources.ONI_URL, os.path.join(INCOMING, "oni.ascii.txt"))
    control_path = sources.download(
        sources.CONTROL_URL, os.path.join(INCOMING, "ersst5.nino.mth.91-20.ascii")
    )

    pulled_at = _now_utc()
    oisst_provenance = provenance_block("NOAA OISST", "v2.1", oisst_u, pulled_at, status)
    oni_provenance = provenance_block("NOAA CPC ONI", "ascii v6", sources.ONI_URL, pulled_at, "published")

    out = build_output(
        oisst_path, CLIMATOLOGY, oni_path, control_path, oisst_provenance, oni_provenance
    )
    os.makedirs(OUT_DIR, exist_ok=True)
    dest = os.path.join(OUT_DIR, f"enso-watch-{day.isoformat()}.json")
    # Atomic write: a killed process must never leave a truncated product that a
    # scheduled workflow would then commit.
    tmp = dest + ".tmp"
    with open(tmp, "w") as handle:
        json.dump(out, handle, indent=2)
        handle.write("\n")
    os.replace(tmp, dest)
    return dest, out


def main():
    dest, out = pull()
    daily = out["daily_series"][0]
    status = out["status"]
    print(f"wrote {dest}")
    print(f"  date {daily['date']}  anomaly {daily['nino34_anomaly_c']} C ({daily['provenance']['status']})")
    print(f"  status {status['phase']} / {status['strength']}  ONI {status['oni_latest']}")


if __name__ == "__main__":
    main()
