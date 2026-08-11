"""The machine gate: run the whole test suite offline, deterministically.

Before importing any test, install an offline guard that blocks every non
loopback Python socket connection (see enso_watch.offline_guard for the exact,
honest scope). The observation gate must prove the transform on frozen fixtures,
with no dependency on the live world. Network is a separate, non gating smoke check.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from enso_watch.offline_guard import install as install_offline_guard


def main():
    install_offline_guard()
    os.chdir(ROOT)
    loader = unittest.TestLoader()
    suite = loader.discover("tests", pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
