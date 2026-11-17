# X Layer Compatibility & Economics

## 1. Network Endpoints

| Network | Endpoint | Status | Verified Chain ID | Notes |
|---------|----------|--------|-------------------|-------|
| X Layer Mainnet | `https://rpc.xlayer.tech` | **VERIFIED** | `196` | Reliable; median RTT `1,317.3 ms` (min `1,067.3 ms`, max `1,778.0 ms`, n=10). |
| X Layer Mainnet | `https://xlayerrpc.okx.com` | Failed | — | DNS resolution failure (`getaddrinfo failed`). |
| X Layer Mainnet | `https://rpc.xlayer.com` | Failed | — | TLS error (`EE certificate key too weak`). |
| X Layer Mainnet | `https://endpoints.omniatech.io/v1/xlayer/mainnet/public` | Failed | — | HTTP 521. |
| X Layer Testnet | `https://testrpc.xlayer.tech` | **VERIFIED** | `1952` | Note: chainId is `1952`, not `195`. |
| X Layer Testnet | `https://endpoints.omniatech.io/v1/xlayer/testnet/public` | Failed | — | HTTP 521. |

**Implication for CircuitForge:** Do not hardcode a single fallback list assuming `okx.com` or `omniatech.io` work, and do not hardcode `195` for X Layer testnet. Ship `https://rpc.xlayer.tech` as default with user-configurable RPC URLs.

## 2. Deployed Contract State (X Layer Mainnet)

| Contract | Address | Verified State | Match vs TAP-10 Docs |
|----------|---------|----------------|----------------------|
| Factory Proxy | `0x1f09DAeFA827f02CBb40967cc91b259763760761` | 131-byte proxy; `cpuCount = 423`; `isSealed = 0` | Proxy address matches; `isSealed = 0` means **unsealed / upgradeable**. |
| Factory Impl (ERC-1967 slot) | `0x336e9f0f4c3fee7c8c803377e4dea00293f4ae2a` | 9,376 bytes | **CONTRADICTS** TAP-10 (`0x74956236...`); factory has been upgraded since 2026-09-27. |
| Beacon | `0xf70d...0991C` | Points to `0x977f217887E085D298Cb3819cDAD5A0ee35F29B2` | Matches TAP-10. |
| Circuit Impl | `0x977f217887E085D298Cb3819cDAD5A0ee35F29B2` | 12,562 bytes | Matches TAP-10. |
| Processor 0 | `0x839BDD6fA7A66416a609A735E11DE5411b98574E` | Active (`#1` XOR, `#2`/`#3` NAND, `#4` REF wrapper) | `cpuAt(0)` verified. |
| Processor 1 | `0x0565EA48CA41Ae559d8d491dbb0a9ec945DB551b` | `name="My4004"`, `symbol="CPU"`, `nextId=100` | Matches TAP-10. |
| X Layer Testnet Factory | `0x1f09DAeFA827f02CBb40967cc91b259763760761` | `hasCode = false` | Not deployed at the shared address on testnet (`1952`). |

### Cross-Chain Address Collision Finding
On Base mainnet (`https://base-pokt.nodies.app`), the **exact same** factory (`cpuCount = 106`) and processor 1 (`0x0565EA48...`, `name = "TapeOutTestBase"`, `nextId = 10`) exist. Because TAP-02 `REF` records encode only a 20-byte `cpu` address and 8-byte `id` with **no chain ID**, a netlist cannot self-identify its chain. CircuitForge must bind every imported `REF` to an explicit `(chainId, cpu, id)` tuple in project metadata.

## 3. TAP-02 §3 Compliance on X Layer

TAP-02's reference docs only verified §3 onchain validation on BSC. This audit independently verified it on X Layer mainnet via read-only `eth_call` with state override:
- **Exact fee (`TAPEOUT_FEE`):** `0.0013 OKB` (`1,300,000,000,000,000 wei`), confirmed by ±1 wei boundary scan (`tapeout_sim.json`).
- **Valid composed netlist (81-byte half-adder):** Passed all §1–7 structural checks and reached transistor burn (`0x03dee4c5(sender, balance=0, needed=1, tokenId=0)` — matching its single top-level `NAND` gate).
- **Ill-formed controls:** Rejected with exact documented revert strings `"REF: pin mismatch"`, `"NAND: future signal"`, and `"bad opcode"`.

## 4. Gas, Latency & Fee Economics

Measured on X Layer mainnet (`bench_g.json`, block `76,046,274`):
- **`eth_gasPrice`:** `20,000,001 wei` (~0.02 gwei)
- **`eval()` gas (`proc0#1` XOR):** `55,924 gas` (~`1.12e-6 OKB` at 0.02 gwei — negligible vs `0.0013 OKB` tapeout fee)
- **`eval()` gas (`proc0#2` NAND):** `53,674 gas`
- **`netlist()` getter gas (`proc0#1`):** `40,524 gas`
- **Public RPC latency:** `1,317.3 ms` median RTT per `eth_call` (`>1s` per call).

**UX implication:** Fetching 50+ circuits sequentially over `https://rpc.xlayer.tech` takes ~1–5 minutes (observed: 312 s for 45 circuits in `scan_corpus2.py`). CircuitForge **must** cache fetched netlists locally (content-addressed by `(chainId, cpu, id)`) and run all simulation/verification locally (~`0.3 µs/gate` in Python, faster in JS/WASM), reserving RPC calls for import, `eth_call` pre-flight validation, and final `tapeout()`.
