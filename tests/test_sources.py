"""Offline tests for the live source url builders. No network: these assert the
url shape only. Existence checks and downloads are exercised by the live pull and
smoke commands, which are outside the gate.
"""
import datetime
import unittest
from unittest import mock

from enso_watch import sources

OISST_ROOT = (
    "https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation"
    "/v2.1/access/avhrr"
)


class UrlBuilderTest(unittest.TestCase):
    def test_oisst_url_final(self):
        url = sources.oisst_url(datetime.date(2026, 7, 1))
        self.assertEqual(url, f"{OISST_ROOT}/202607/oisst-avhrr-v02r01.20260701.nc")

    def test_oisst_url_preliminary(self):
        url = sources.oisst_url(datetime.date(2026, 7, 1), preliminary=True)
        self.assertEqual(url, f"{OISST_ROOT}/202607/oisst-avhrr-v02r01.20260701_preliminary.nc")

    def test_zero_padding(self):
        url = sources.oisst_url(datetime.date(2026, 1, 5))
        self.assertIn("/202601/oisst-avhrr-v02r01.20260105.nc", url)


class UrlExistsBranchTest(unittest.TestCase):
    """The load bearing distinction: 200 exists, 404 absent, everything else is a
    loud transient. subprocess is mocked, so no network and no curl are involved.
    """

    def _run(self, returncode, http_code="", stderr=""):
        return mock.Mock(returncode=returncode, stdout=http_code, stderr=stderr)

    def test_http_200_is_present(self):
        with mock.patch("enso_watch.sources.subprocess.run", return_value=self._run(0, "200")):
            self.assertTrue(sources.url_exists("https://example/file.nc"))

    def test_http_404_is_absent(self):
        with mock.patch("enso_watch.sources.subprocess.run", return_value=self._run(0, "404")):
            self.assertFalse(sources.url_exists("https://example/file.nc"))

    def test_http_403_raises_not_absent(self):
        with mock.patch("enso_watch.sources.subprocess.run", return_value=self._run(0, "403")):
            with self.assertRaises(RuntimeError):
                sources.url_exists("https://example/file.nc")

    def test_http_503_raises_not_absent(self):
        with mock.patch("enso_watch.sources.subprocess.run", return_value=self._run(0, "503")):
            with self.assertRaises(RuntimeError):
                sources.url_exists("https://example/file.nc")

    def test_curl_network_failure_raises(self):
        with mock.patch("enso_watch.sources.subprocess.run", return_value=self._run(28, "", "timed out")):
            with self.assertRaises(RuntimeError):
                sources.url_exists("https://example/file.nc")


if __name__ == "__main__":
    unittest.main()
