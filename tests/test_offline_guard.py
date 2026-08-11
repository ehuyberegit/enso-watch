"""Prove the offline guard actually blocks, so drift is caught by the gate
itself, not by a reviewer probing by hand.
"""
import socket
import unittest

from enso_watch.offline_guard import install

_NON_LOOPBACK = ("140.172.38.100", 80)


class OfflineGuardTest(unittest.TestCase):
    def setUp(self):
        install()

    def test_blocks_non_loopback_connect(self):
        with self.assertRaises(RuntimeError):
            socket.socket().connect(_NON_LOOPBACK)

    def test_blocks_non_loopback_connect_ex(self):
        with self.assertRaises(RuntimeError):
            socket.socket().connect_ex(_NON_LOOPBACK)


if __name__ == "__main__":
    unittest.main()
