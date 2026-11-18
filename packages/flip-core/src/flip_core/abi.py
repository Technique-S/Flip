"""Explicit, strict ABI codecs for the bounded read-only importer interface."""

import re

from flip_core.contracts import ContractError

FACTORY = "0x1f09daefa827f02cbb40967cc91b259763760761"
IMPLEMENTATION_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
BEACON_SLOT = "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50"
# TAP-02 section 6; remaining selectors verified against the inspected audit
# Keccak-256 helper. No SHA3-256 substitution and no dynamic ABI/RPC proxy.
SELECTORS = {
    "nextId": "61b8ce8c",
    "circuitInfo": "084d60f1",
    "netlist": "3fc4be56",
    "factory": "c45a0155",
    "isCPU": "5f5a364f",
    "circuitBeacon": "ddcb22fa",
    "implementation": "5c60da1b",
    "isSealed": "631f9852",
}


def malformed(message: str = "Malformed ABI response.") -> ContractError:
    return ContractError("INVALID_INPUT", message)


def hex_bytes(value: object, cap: int) -> bytes:
    if not isinstance(value, str) or len(value) > 2 + 2 * cap:
        raise malformed("Malformed or oversized hex response.")
    if not re.fullmatch(r"0x(?:[0-9a-fA-F]{2})*", value):
        raise malformed("Malformed hex response.")
    return bytes.fromhex(value[2:])


def uint(value: object, bits: int = 256) -> int:
    raw = hex_bytes(value, 32)
    if len(raw) != 32 or int.from_bytes(raw, "big") >= 2**bits:
        raise malformed()
    return int.from_bytes(raw, "big")


def address(value: object) -> str:
    number = uint(value, 160)
    if number == 0:
        raise malformed("Zero implementation/processor address.")
    return "0x" + number.to_bytes(20, "big").hex()


def calldata(name: str, argument: int | str | None = None) -> str:
    selector = SELECTORS[name]
    if argument is None:
        return "0x" + selector
    number = int(argument, 16) if isinstance(argument, str) else argument
    if type(number) is not int or not 0 <= number < 2**256:
        raise malformed("Invalid ABI argument.")
    return "0x" + selector + number.to_bytes(32, "big").hex()


def info(value: object) -> tuple[int, int, int, int]:
    raw = hex_bytes(value, 128)
    if len(raw) != 128:
        raise malformed("circuitInfo must contain exactly four ABI words.")
    fields = tuple(int.from_bytes(raw[i : i + 32], "big") for i in range(0, 128, 32))
    if any(v >= 2**32 for v in fields):
        raise malformed("circuitInfo uint32 overflow.")
    return fields


def dynamic_bytes(value: object, cap: int) -> bytes:
    raw = hex_bytes(value, 64 + ((cap + 31) // 32) * 32)
    if len(raw) < 64 or int.from_bytes(raw[:32], "big") != 32:
        raise malformed("Invalid ABI bytes offset.")
    size = int.from_bytes(raw[32:64], "big")
    if size > cap:
        raise ContractError("RESOURCE_LIMIT", "Netlist byte budget exceeded.")
    padded = ((size + 31) // 32) * 32
    if len(raw) != 64 + padded or any(raw[64 + size :]):
        raise malformed("Invalid ABI bytes length/padding.")
    return raw[64 : 64 + size]
