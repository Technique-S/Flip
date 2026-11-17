# Gate A — Publication Readiness (X Layer, read-only verification)

## Status: **PARTIAL** — STRUCTURALLY ACCEPTED verified; SIMULATION SUCCESS blocked by RPC capability; REAL PUBLICATION out of scope.

## A1. Composition reproduction (VERIFIED)

`results/gate_a_compose_rerun.json` — independent rerun of `experiments/src/compose_poc.py` (exit 0):
- Source A: processor `0x839BDD6fA7A66416a609A735E11DE5411b98574E` #1 (XOR), netlist SHA-256 `d3f8f3a8…a9f`, `nIn=2, nOut=1`, 4 NAND gates.
- Source B: same processor #2 (NAND), netlist SHA-256 `91c81eb0…3f8e`, `nIn=2, nOut=1`, 3 NAND gates.
- Composed netlist: **81 bytes**, 2 REF + 1 glue NAND, `nIn=2, nOut=2`, deterministic across 100 builds, truth table 4/4 correct on both evaluators.
- Independent live re-fetch via `eth_call` confirmed XOR #1 netlist hash `d3f8f3a8…a9f` unchanged (`results/gate_b_manifest.json`).

## A2. Publication requirements (VERIFIED from deployed contracts)

| Requirement | Evidence | Value |
|---|---|---|
| `tapeout(bytes netlist, uint32 nIn, uint32 nOut) payable` | TAP-02 §6 + selector `0x7bd3ac1d` present in circuit impl bytecode | confirmed |
| Fixed fee | `PROC0.TAPEOUT_FEE()` via `eth_call` (`results/gate_a_probe.json`) | `0x49E57D6354000` wei = **0.0013 OKB** (independently re-confirmed; previous ±1 wei scan agrees) |
| Transistor resources | PROC0 storage slot 0 / `transistors()` getter | `0xbe0eee424c49d44592e4d498740f5b031ef8e26d` (small 295-byte contract, bound to PROC0 in slot 1) |
| Required burn for this circuit | TAP-02 §6: burns top-level NAND+LATCH count (REFd gates not re-burned) | 1 transistor token id 0 (one top-level NAND), confirmed by decoded revert `needed=1, id=0` |
| Ready-made REFs at publication time | TAP-02 §3 cond. 6; `isCPU(PROC0)=1`, circuits #1/#2 exist | satisfied |
| Authorization / ownership | No `owner()` on processor; fee + burn only | any caller with fee + transistors may publish |
| Mutability | factory `isSealed()=0`, factory impl `0x336e9f0f…`, beacon owner = factory | fee/burn rules can change via upgrade — **re-read at publication time** |

### Revert `0x03dee4c5` — positively identified (VERIFIED)
- `keccak256("ERC1155InsufficientBalance(address,uint256,uint256,uint256)")[:4] == 0x03dee4c5` — computed independently with a pure-Python Keccak-256 (`results/gate_a_probe.json`).
- Decoded args from the live `eth_call`: `(sender=0x0000…f00d, balance=0, needed=1, id=0)` (`results/gate_a_probe2.json`).
- Meaning: the composed netlist **passed all §1–7 well-formedness checks**; execution reached the transistor burn and failed only because the synthetic caller owns no transistor token. The selector is not stored as a PUSH4 immediate in any scanned contract (PROC0 proxy, circuit impl, beacon, factory impl, transistor address) — likely emitted via assembly/forwarded returndata; its *semantics* are unambiguous from the signature and decoded fields.
- Ill-formed controls were rejected earlier in the sequence with `"REF: pin mismatch"`, `"NAND: future signal"`, `"bad opcode"` — so the acceptance was specific, not universal.

## A3. No-broadcast publication simulation (PARTIAL / BLOCKED)

| Method | Result |
|---|---|
| `eth_call` value + from override | WORKS. Well-formed netlist → reach burn & revert with ERC1155InsufficientBalance; ill-formed → §3 revert. |
| EOA balance state override (`{caller: {balance: …}}`) | WORKS (used in fee discovery). |
| **ERC-1155 storage override on transistor contract** | **NOT SUPPORTED** — `eth_call` with storage keys returns `Invalid params` on `https://rpc.xlayer.tech` (`results/gate_a_probe2.json`). |
| Full SIMULATION SUCCESS (call returns new circuit id) | **NOT ACHIEVABLE** with this RPC — caller cannot be given transistor balance inside `eth_call` without a storage override. |
| `eth_estimateGas` for tapeout path | `EVM error: OutOfFunds` (revert short-circuits estimation). |

**Classification achieved:** STRUCTURALLY ACCEPTED (the strongest honest label). SIMULATION SUCCESS and REAL PUBLICATION are explicitly NOT claimed.

## A4. Publish-readiness answer

**The half-adder is ready for an explicitly authorized publication test, conditional on acquiring one transistor token (id 0) for the publishing account and having ≥0.0013 OKB + gas.** Nothing in the netlist, the fee logic, or the §3 validator blocks it.

Required before a real test (all OUTSTANDING, none verifiable read-only):
1. Acquire 1 transistor token `id=0` (mint/purchase path NOT verified in this audit — UNVERIFIED).
2. Connect a wallet with ≥0.0013 OKB; `eth_call` pre-flight immediately before signing (fee/impl may change because `isSealed=0`).
3. Broadcast `tapeout(0x02839b…, 2, 2)` from that wallet; confirm minted circuit id via `nextId()` before/after and verify stored `netlist(id)` hash equals `d3f8…` composition hash.
4. Evaluate the published circuit with `eval(id, bytes)` for all 4 inputs and compare to the half-adder truth table; check `circuitInfo(id)` gate count equals 1 top-level NAND (+REF expansion).

Total cost estimate: **0.0013 OKB fee + gas (UNKNOWN — estimate blocked by burn revert) + 1 transistor token (acquisition cost UNKNOWN)**. No 10× or other improvement claim is made.
