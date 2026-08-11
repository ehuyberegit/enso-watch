"""Offline tests for the shape validators, against the frozen fixtures (the known
good shape) and against mangled inputs (drift must be rejected).
"""
import os
import tempfile
import unittest

import netCDF4 as nc

from enso_watch import shape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OISST = os.path.join(ROOT, "fixtures", "oisst", "oisst-avhrr-v02r01.20260701.nc")
ONI = os.path.join(ROOT, "fixtures", "cpc", "oni.ascii.txt")
CONTROL = os.path.join(ROOT, "fixtures", "cpc", "ersst5.nino.mth.91-20.ascii")


def _write_temp(text):
    handle = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
    handle.write(text)
    handle.close()
    return handle.name


class ShapeTest(unittest.TestCase):
    def test_oisst_shape_ok(self):
        ok, detail = shape.check_oisst_shape(OISST)
        self.assertTrue(ok, detail)

    def test_oisst_shape_reject_wrong_grid(self):
        # A structurally valid netCDF but with the wrong grid size must be rejected.
        path = tempfile.NamedTemporaryFile(suffix=".nc", delete=False).name
        dataset = nc.Dataset(path, "w")
        try:
            dataset.createDimension("lat", 10)
            dataset.createDimension("lon", 10)
            dataset.createDimension("time", 1)
            dataset.createVariable("lat", "f4", ("lat",))
            dataset.createVariable("lon", "f4", ("lon",))
            dataset.createVariable("time", "f4", ("time",))
            sst = dataset.createVariable("sst", "f4", ("time", "lat", "lon"))
            sst.units = "Celsius"
            dataset.close()
            ok, _ = shape.check_oisst_shape(path)
            self.assertFalse(ok)
        finally:
            os.unlink(path)

    def test_control_columns_ok(self):
        ok, detail = shape.check_control_columns(CONTROL)
        self.assertTrue(ok, detail)

    def test_oni_columns_ok(self):
        ok, detail = shape.check_oni_columns(ONI)
        self.assertTrue(ok, detail)

    def test_control_columns_reject_mangled(self):
        path = _write_temp("2026   6   25.94   2.82\n")  # 4 columns, fewer than 10
        try:
            ok, _ = shape.check_control_columns(path)
            self.assertFalse(ok)
        finally:
            os.unlink(path)

    def test_oni_columns_reject_mangled(self):
        path = _write_temp("  DJF 2026  26.15  -0.39  EXTRA\n")  # 5 columns, not 4
        try:
            ok, _ = shape.check_oni_columns(path)
            self.assertFalse(ok)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
