"""Offline guard for the machine gate.

Patch Python socket connections so any non loopback target raises. This proves
the test suite touches only local fixtures. It guards Python level sockets, both
`connect` and `connect_ex`.

It deliberately does NOT claim to intercept networking done inside C extensions
(for example netCDF4's own OPeNDAP client), which never passes through Python's
socket layer. Fixture capture that needs the network is a separate tool
(tools/capture_climatology.py), never part of the gate. The gate's real
guarantee is that the tested transform reads only local fixtures.
"""
import socket

_ALLOWED = {"127.0.0.1", "::1", "localhost"}
_installed = False


def _host(address):
    return address[0] if isinstance(address, tuple) else address


def install():
    """Install the guard once. Idempotent."""
    global _installed
    if _installed:
        return
    real_connect = socket.socket.connect
    real_connect_ex = socket.socket.connect_ex

    def connect(self, address):
        if _host(address) not in _ALLOWED:
            raise RuntimeError(f"offline gate: network blocked ({_host(address)})")
        return real_connect(self, address)

    def connect_ex(self, address):
        if _host(address) not in _ALLOWED:
            raise RuntimeError(f"offline gate: network blocked ({_host(address)})")
        return real_connect_ex(self, address)

    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    _installed = True
