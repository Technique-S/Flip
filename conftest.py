"""Mandatory pytest is offline. Local ASGI/socket pairs remain available."""

import ipaddress
import socket

import pytest


def local_address(address):
    if isinstance(address, (str, bytes)):  # local AF_UNIX paths
        return True
    host = address[0]
    if host in ("localhost", b"localhost"):
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


@pytest.fixture(autouse=True)
def prevent_external_network(monkeypatch):
    connect, connect_ex, getaddrinfo = (
        socket.socket.connect,
        socket.socket.connect_ex,
        socket.getaddrinfo,
    )

    def checked_connect(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6) and not local_address(address):
            raise AssertionError("External network is forbidden in mandatory pytest.")
        return connect(sock, address)

    def checked_connect_ex(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6) and not local_address(address):
            raise AssertionError("External network is forbidden in mandatory pytest.")
        return connect_ex(sock, address)

    def checked_dns(host, *args, **kwargs):
        if host is not None and not local_address((host,)):
            raise AssertionError("External DNS is forbidden in mandatory pytest.")
        return getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", checked_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", checked_connect_ex)
    monkeypatch.setattr(socket, "getaddrinfo", checked_dns)
