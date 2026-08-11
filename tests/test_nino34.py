"""The observation gate: the Nino 3.4 transform on frozen fixtures.

The golden is the exact output of the transform on the captured OISST daily file
and the box climatology, at the run contract precision of 3 decimals. Any drift
from it is a red gate. A second test cross checks our raw region SST against the
independent CPC control, a loose sanity band (different products), not an exact gate.
"""
import os
import unittest

from enso_watch.nino34 import nino34_anomaly

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OISST = os.path.join(ROOT, "fixtures", "oisst", "oisst-avhrr-v02r01.20260701.nc")
CLIM = os.path.join(ROOT, "fixtures", "oisst", "nino34_climatology_1991-2020.nc")
CONTROL = os.path.join(ROOT, "fixtures", "cpc", "ersst5.nino.mth.91-20.ascii")

GOLDEN = {
    "date": "2026-07-01",
    "nino34_anomaly_c": 1.744,
    "region_mean_sst_c": 29.215,
    "climatology_mean_c": 27.47,
    "baseline": "1991-2020",
}


def _last_cpc_nino34_sst(path):
    """Latest monthly Nino 3.4 SST from the CPC control file.

    Columns: YR MON NINO1+2 ANOM NINO3 ANOM NINO4 ANOM NINO3.4 ANOM.
    """
    with open(path) as handle:
        rows = [r.split() for r in handle if r.strip() and r.split()[0].isdigit()]
    return float(rows[-1][8])


class Nino34Test(unittest.TestCase):
    def test_golden_transform(self):
        self.assertEqual(nino34_anomaly(OISST, CLIM), GOLDEN)

    def test_region_sst_near_cpc_control(self):
        result = nino34_anomaly(OISST, CLIM)
        control_sst = _last_cpc_nino34_sst(CONTROL)
        self.assertLess(
            abs(result["region_mean_sst_c"] - control_sst),
            0.5,
            "our OISST region SST drifted far from the CPC control",
        )


if __name__ == "__main__":
    unittest.main()
