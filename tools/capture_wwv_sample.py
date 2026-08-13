"""Freeze a small slice of the NOAA PMEL warm water volume file as a fixture.

One time fixture builder for the WWV parser test. Downloads the live wwv.dat,
keeps the attribution header and the 1997 to 1998 rows (a textbook El Nino
precursor build up and collapse), and writes it under fixtures/pmel. The parser
test then runs offline against this frozen slice.

Run from the repo root with the project venv:
    .venv/bin/python tools/capture_wwv_sample.py
"""
import datetime
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import manifest
from enso_watch import sources

OUT = "fixtures/pmel/wwv_sample.dat"
ROW = re.compile(r"^(\d{4})(\d{2})\s")
Y0, Y1 = 1997, 1998


def main():
    tmp = sources.download(sources.WWV_URL, "data/_incoming/wwv.dat")
    with open(tmp, encoding="utf-8") as fh:
        lines = fh.readlines()

    kept = []
    for line in lines:
        m = ROW.match(line)
        if m is None:
            # keep the header and attribution lines, drop nothing structural
            if not line[:1].isdigit():
                kept.append(line)
            continue
        if Y0 <= int(m.group(1)) <= Y1:
            kept.append(line)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as out:
        out.writelines(kept)
    retrieved_at = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest.record("pmel_wwv_sample_1997_1998", OUT, sources.WWV_URL, retrieved_at,
                    note="Header plus the 1997-98 rows of the NOAA PMEL warm water volume file, "
                         "fixture for the WWV parser, built by tools/capture_wwv_sample.py.")
    print("wrote", OUT, f"({sum(1 for l in kept if ROW.match(l))} data rows)")


if __name__ == "__main__":
    main()
