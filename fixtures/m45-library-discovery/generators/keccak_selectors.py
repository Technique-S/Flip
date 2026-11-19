"""Dependency-free Keccak-256 selector verification for M4.5-2L discovery research.

The permutation is a direct port of the reference Keccak-f[1600] round loop.
It is self-checked against (a) the published Keccak-256 empty-message digest and
(b) Python's hashlib.sha3_256 (identical permutation, different padding byte).
No network access and no third-party package is required.
"""
from __future__ import annotations

MASK = (1 << 64) - 1
RATE_BYTES = 136
LANES_PER_BLOCK = RATE_BYTES // 8

ROUND_CONSTANTS = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]
ROTATION_CONSTANTS = [
    1, 3, 6, 10, 15, 21, 28, 36, 45, 55, 2, 14, 27, 41, 56, 8, 25, 43, 62, 18, 39, 61, 20, 44,
]
PILN = [
    10, 7, 11, 17, 18, 3, 5, 16, 8, 21, 24, 4, 15, 23, 19, 13, 12, 2, 20, 14, 22, 9, 6, 1,
]

# Signatures whose selectors are relied upon by Flip or by the M0 audit source.
SIGNATURES = [
    "nextId()",
    "circuitInfo(uint256)",
    "netlist(uint256)",
    "cpuCount()",
    "cpuAt(uint256)",
    "isCPU(address)",
    "name()",
    "symbol()",
    "totalSupply()",
    "tapeout(bytes,uint32,uint32)",
    "ownerOf(uint256)",
]

# Values already present in verified source/evidence (see selector_proof.json provenance).
EXPECTED = {
    "nextId()": "61b8ce8c",                 # packages/flip-core/src/flip_core/abi.py
    "circuitInfo(uint256)": "084d60f1",     # packages/flip-core/src/flip_core/abi.py
    "netlist(uint256)": "3fc4be56",         # packages/flip-core/src/flip_core/abi.py
    "cpuCount()": "a94da8a7",               # experiments/src/xlayer_probe.py (M0 audit)
    "cpuAt(uint256)": "4bc7cbbd",           # experiments/src/xlayer_probe.py (M0 audit)
    "isCPU(address)": "5f5a364f",           # packages/flip-core/src/flip_core/abi.py
    "name()": "06fdde03",                   # experiments/src/xlayer_probe.py
    "symbol()": "95d89b41",                 # experiments/src/xlayer_probe.py
    "totalSupply()": "18160ddd",            # experiments/src/xlayer_probe.py
    "tapeout(bytes,uint32,uint32)": "7bd3ac1d",  # docs/audits/M05/PUBLICATION_READINESS.md
    "ownerOf(uint256)": "6352211e",         # EIP-721 standard signature
}


def _rol(value: int, count: int) -> int:
    return ((value << count) | (value >> (64 - count))) & MASK if count else value


def _permute(state: list[int]) -> None:
    for round_constant in ROUND_CONSTANTS:
        columns = [state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20]
                   for x in range(5)]
        for x in range(5):
            delta = columns[(x + 4) % 5] ^ _rol(columns[(x + 1) % 5], 1)
            for y in range(0, 25, 5):
                state[y + x] ^= delta
        temp = state[1]
        for i in range(24):
            j = PILN[i]
            saved = state[j]
            state[j] = _rol(temp, ROTATION_CONSTANTS[i])
            temp = saved
        for y in range(0, 25, 5):
            row = state[y:y + 5]
            for x in range(5):
                state[y + x] = row[x] ^ ((~row[(x + 1) % 5]) & row[(x + 2) % 5]) & MASK
        state[0] ^= round_constant


def keccak256(data: bytes) -> bytes:
    state = [0] * 25
    padded = bytearray(data)
    padded.append(0x01)  # Keccak padding; SHA3-256 would use 0x06 here.
    while len(padded) % RATE_BYTES != RATE_BYTES - 1:
        padded.append(0x00)
    padded.append(0x80)
    for offset in range(0, len(padded), RATE_BYTES):
        block = padded[offset:offset + RATE_BYTES]
        for lane in range(LANES_PER_BLOCK):
            state[lane] ^= int.from_bytes(block[lane * 8:(lane + 1) * 8], "little")
        _permute(state)
    digest = bytearray()
    for lane in range(4):
        digest += state[lane].to_bytes(8, "little")
    return bytes(digest)


def selector(signature: str) -> str:
    return keccak256(signature.encode("utf-8"))[:4].hex()


def self_test() -> dict:
    import hashlib
    assert keccak256(b"").hex() == (
        "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"
    ), "Keccak-256 empty-message known-answer test failed"
    # Identical permutation, SHA-3 padding byte 0x06: verify against stdlib.
    state = [0] * 25
    padded = bytearray(b"flip-m45-discovery")
    padded.append(0x06)
    while len(padded) % RATE_BYTES != RATE_BYTES - 1:
        padded.append(0x00)
    padded.append(0x80)
    for offset in range(0, len(padded), RATE_BYTES):
        block = padded[offset:offset + RATE_BYTES]
        for lane in range(LANES_PER_BLOCK):
            state[lane] ^= int.from_bytes(block[lane * 8:(lane + 1) * 8], "little")
        _permute(state)
    sha3_like = b"".join(state[i].to_bytes(8, "little") for i in range(4))
    assert sha3_like.hex() == hashlib.sha3_256(b"flip-m45-discovery").hexdigest(), (
        "Permutation cross-check against hashlib.sha3_256 failed"
    )
    results = {sig: selector(sig) for sig in SIGNATURES}
    for sig, expected in EXPECTED.items():
        assert results[sig] == expected, f"selector mismatch for {sig}"
    return {"empty_keccak256": keccak256(b"").hex(), "selectors": results,
            "verified_signatures": len(results)}


if __name__ == "__main__":
    import json
    print(json.dumps(self_test(), indent=2, sort_keys=True))
