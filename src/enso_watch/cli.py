"""Emit the V0 JSON product to stdout, built from the frozen fixtures.

This is the offline demonstration of the output contract. The live daily pull
(build step 5) will feed the same builder from real source responses.
"""
import json
import os

from enso_watch.output import build_output, offline_provenance

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIXTURES = os.path.join(ROOT, "fixtures")


def main():
    oisst_provenance, oni_provenance = offline_provenance(FIXTURES)
    out = build_output(
        os.path.join(FIXTURES, "oisst", "oisst-avhrr-v02r01.20260701.nc"),
        os.path.join(FIXTURES, "oisst", "nino34_climatology_1991-2020.nc"),
        os.path.join(FIXTURES, "cpc", "oni.ascii.txt"),
        os.path.join(FIXTURES, "cpc", "ersst5.nino.mth.91-20.ascii"),
        oisst_provenance,
        oni_provenance,
    )
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
