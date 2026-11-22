# X Layer compatibility evidence and gaps

**Status: EVIDENCE RECORD. Date 2026-11-22.** Read-only research only.
No wallet connection, key creation, signature, broadcast or spend occurred.

## 1. Method and limits

- Official documentation was discovered through `mcporter call exa.web_search_exa` (agent-reach search
  backend) and read as search-result highlights; direct `webfetch` of the OKX docs host failed with a
  transport error. `gh api` was used for the public TAP-10 PR.
- Onchain observations used **bounded JSON-RPC POST reads** to `https://rpc.xlayer.tech`.
  One `eth_chainId` call, then batches of 10, 9, 4 and 2 calls, then one single `eth_call`, were
  issued in this session. Selectors were computed locally with the repository's dependency-free Keccak helper
  (`fixtures/m45-library-discovery/generators/keccak_selectors.py`).
- The RPC operator is a **single untrusted provider**. Responses are not consensus-verified and are
  not independent-operator evidence. Block hashes/numbers below are observations, not finality claims.
- `agent-reach doctor --json` was attempted but the `agent-reach` CLI is not installed in this
  environment; `mcporter` exa and harness web tools were used instead.
- A successful `eth_call`, `eth_estimateGas` or read-only state-override probe **does not prove that a
  paid transaction will succeed, be included, be final, or have the assumed fee**. That inference is
  expressly rejected here.

## 2. Required compatibility items

| Item | Status | Evidence | Implication / gate |
|---|---|---|---|
| Chain ID | **VERIFIED** | Official network docs list mainnet chain ID `196`, testnet `1952`, native token OKB; read-only `eth_chainId` returned `0xc4` (196). | Accepted `chainId=196` convention is consistent. Still verify per session, as MVP_CONSTRAINTS requires. |
| Transaction formats | **PARTIAL** | `eth_getBlockByNumber` at height 76,571,210 returned 14 transactions: 12 × `type 0x2` (EIP-1559), 1 × `type 0x0` (legacy), 1 × `type 0x7e` (OP deposit). OKX transaction API documents `transactionType` 0/1/2. | LEGACY/EIP-1559 union is plausible; deposit type is outside the proposed profile and must remain excluded. Signer support for each variant still needs certification (D01/D04). |
| Exact signer compatibility | **UNKNOWN** | OKX provider documentation describes account connection, transaction sending and EIP-5792 `wallet_sendCalls`; sources read do not demonstrate raw-sign-only output before broadcast. The ADR itself states OKX's send path has editable gas fields and unverified raw-sign support. | No live signing until a device/app/firmware/adapter profile returns signed bytes before submission and passes exact-field and mutation tests. |
| Processor / factory mutability | **CONTRADICTED / PARTIAL** | Read-only at session block 76,571,177: factory `isSealed() = 0`, owner `0xb3d85b42a045c1a88d800cad0f55d2566a4d3138`, ERC-1967 implementation `0x336e9f0f4c3fee7c8c803377e4dea00293f4ae2a`. Beacon `owner() = 0`, `implementation() = 0x977f217887e085d298cb3819cdad5a0ee35f29b2`. Open TAP-10 v1.2 PR lists current X Layer factory implementation `0xb41C1E7602EB5734BE2430b72178cCb814A5293d` and says an unsealed factory can still change the processor table / `isCPU`. | Processor code appears frozen but **factory is unsealed with an owner and an implementation not listed in v1.1 or the open v1.2 draft**. Effective immutability of the full execution context is not established (D10). |
| Gas / resource estimation | **PARTIAL** | `eth_estimateGas` on a zero-value zero-address transfer returned `0x5208` (21,000). Read-only `eth_call` to processor `TAPEOUT_FEE()` returned `1,300,000,000,000,000` wei (0.0013 OKB), matching M0. M0 records that real `tapeout()` estimation was blocked by the burn revert and that fee/burn needs state-override simulation. `[DOCUMENTED]` OP Stack has an intrinsic L1 data fee via `GasPriceOracle` (`getL1Fee(bytes)`), variable at inclusion. A synthetic `getL1Fee` probe was accepted but returned zero for a meaningless 4-byte blob. | Gas estimation capability exists; **complete fee bound and real tape-out resource sufficiency are UNKNOWN**. `otherFeeCapWei` is not onchain enforcement. D03/D06 remain blocked. |
| Finality observation | **PARTIAL / UNKNOWN semantics** | Tags returned distinct blocks: `latest` 76,571,210 (`0xb26418ef…625d`), `safe` 76,571,101 (`0x1bfc502a…5637`), `finalized` 76,569,783 (`0x6991d408…ea887b4`). `latest` and `pending` were equal. `[DOCUMENTED]` Open TAP-10 v1.2 says latest L2 blocks can be rewritten until posted to Ethereum and uses `safe` on L2. Official endpoints are OKX-operated; `xlayerrpc.okx.com` did not respond in this session. | Tag availability is verified; **meaning of `finalized`, independent-operator agreement and a verified finalized-block policy are UNKNOWN**. D05 remains blocked; no block count may be invented. |
| Publication receipts / events | **UNKNOWN** | `eth_getTransactionReceipt` for a documented mainnet transaction returned status `0x1`, block 31,131,765, type `0x0`, with no `l1Fee`-family fields exposed in the sampled response. Archived live observation states: "no factory registration event signature is defined in TAP-10; raw logs recorded only as availability observation". `eth_subscribe` docs confirm `newHeads`/`logs` with reorg notifications; `newPendingTransactions` is not supported. | No authoritative publication-event ABI is established. Receipt/content verification cannot be certified until a reviewed ABI and a real canonical receipt are captured. A status-1 receipt alone is insufficient. |
| Atomic execution guard feasibility | **UNKNOWN / NOT DEMONSTRATED** | No guard contract is implemented or authorized by the proposal. `[DOCUMENTED]` TAP-10 v1.2 describes approved contracts writing as a container within one transaction for messaging keys, not an atomic cap guard over a direct EOA `tapeout()` call. A wrapper would change target/calldata and require a separate reviewed intent/ABI profile. | The proposal's guard remains a design idea. With an unsealed factory, no atomic enforcement of the approved resource maximum is demonstrated. D10 remains a live blocker. |
| No-signing simulation options | **PARTIAL** | `eth_call` with a third `{}` state-override object was accepted for `nextId()` and returned the same value as the non-override call. `eth_estimateGas` and a synthetic `getL1Fee` call were accepted. M0 records state-override use to reach the burn stage. | Read-only simulation exists, but it is **not** proof of paid-transaction success, inclusion, finality or fee settlement. All simulation results must stay labeled structural/UNKNOWN per existing pre-flight semantics. |

## 3. Exact read-only observations (this session)

All values are verbatim from the RPC responses. Decimal conversions are reviewer computations.

| Probe | Result |
|---|---|
| `eth_chainId` | `0xc4` = 196 |
| `eth_blockNumber` (batch 1) | `0x4906229` = 76,571,177 |
| `eth_getBlockByNumber("latest")` (batch 2) | `0x490624a` = 76,571,210, hash `0xb26418efb0392c94c20c140431e3cca1f606d73ff8573d0c18553268fbfb625d`, `baseFeePerGas 0x1312d00` = 20,000,000, `gasLimit 0xc845880`, `blobGasUsed 0x136410` |
| `eth_getBlockByNumber("safe")` | `0x49061dd` = 76,571,101, hash `0x1bfc502a7010d613e1728c07340f20d589eae57c5e5846fa1c350bc437615637` |
| `eth_getBlockByNumber("finalized")` | `0x4905cb7` = 76,569,783, hash `0x6991d408c302e3f1f40c3b8a448ca71fbef9c9cdcca0f418fbee7f867ea887b4` |
| `eth_getBlockByNumber("pending")` | Equal to `latest` |
| Block transaction types at `latest` | 14 total: `0x2` × 12, `0x0` × 1, `0x7e` × 1 |
| Factory ERC-1967 implementation slot | `0x000000000000000000000000336e9f0f4c3fee7c8c803377e4dea00293f4ae2a` |
| Factory `isSealed()` (`0x631f9852`) | `0x000…0000` = 0 |
| Factory `owner()` (`0x8da5cb5b`) | `0x000000000000000000000000b3d85b42a045c1a88d800cad0f55d2566a4d3138` |
| Factory `cpuCount()` (`0xa94da8a7`) | `0x1b9` = 441 (accepted fixture at block 76,277,110: 430) |
| Processor 0 `nextId()` (`0x61b8ce8c`) | `0x69` = 105 (accepted fixture: 104) |
| Processor 0 `TAPEOUT_FEE()` (`0xadfb2b69`) | `0x49e57d6354000` = 1,300,000,000,000,000 wei |
| Beacon `implementation()` (`0x5c60da1b`) | `0x000000000000000000000000977f217887e085d298cb3819cdad5a0ee35f29b2` |
| Beacon `owner()` (`0x8da5cb5b`) | `0x000…0000` = 0 |
| `eth_call` with `{}` override on `nextId()` | `0x69` (same as no override) |
| `eth_estimateGas` (zero-value transfer) | `0x5208` = 21,000 |
| Sampled historical transaction `0x7db1728b…81fec01e77c8684a6e2df912db408189dc7` | `type 0x0`, block `0x1db1b71` = 31,131,765, status `0x1`, `gasUsed 0x43ce1`; no `l1Fee` fields in response |

Locally recomputed selectors: `isSealed() = 631f9852`, `implementation() = 5c60da1b`,
`TAPEOUT_FEE() = adfb2b69`, `getL1Fee(bytes) = 49948e0e`, `nextId() = 61b8ce8c` (matches accepted evidence).

## 4. Primary sources

- OKX, X Layer network information: `https://web3.okx.com/onchainos/dev-docs/xlayer/developer/build-on-xlayer/network-information`
- OKX, RPC endpoints and supported methods: `https://web3.okx.com/onchainos/dev-docs/xlayer/developer/rpc-endpoints/rpc-endpoints`
- OKX, Flashblocks overview (`pending` tag, flashblock/canonical hash difference): `https://web3.okx.com/onchainos/dev-docs/xlayer/developer/flashblocks/overview`
- OKX, About X Layer (OP Stack, EVM equivalence, gas token OKB): `https://web3.okx.com/onchainos/dev-docs/xlayer/developer/build-on-xlayer/about-xlayer`
- OKX, Contracts (GasPriceOracle and fee vault predeploys): `https://web3.okx.com/onchainos/dev-docs/xlayer/developer/build-on-xlayer/contracts`
- OKX, Provider API (account/send/EIP-5792): `https://web3.okx.com/onchainos/dev-docs/wallet/dapp-connect/chains/evm/provider`
- OKX, Websocket endpoints (`newHeads`/`logs` reorg semantics; `newPendingTransactions` unsupported): `https://web3.okx.com/onchainos/dev-docs/xlayer/developer/websockets-endpoints/websocket-endpoints`
- OKX engineering, Hybrid Proof (optimistic path with ZK arbitration; 1-day testnet challenge): `https://www.okx.com/en-us/learn/x-layer-hybrid-proof`
- Optimism docs, fee estimation (L1 data fee separate from execution gas): `https://docs.optimism.io/app-developers/guides/transactions/estimates`
- Optimism docs, op-reth JSON-RPC (receipt L1 fee fields): `https://docs.optimism.io/node-operators/reference/op-reth-json-rpc`
- TapeOutProtocol/TAPs PR #88, TAP-10 v1.2 (**open**, not merged): `https://github.com/TapeOutProtocol/TAPs/pull/88`

## 5. Bottom line

The EVM/chain-ID/transaction-format basics are consistent with the proposal. The live-critical assumptions are not:
raw-signing capability, complete fee bounds, verified finality with independent operators, authoritative
publication events, and effective immutability of the whole execution context are all unresolved or
contradicted by current observations. These are gates, not optimizations.
