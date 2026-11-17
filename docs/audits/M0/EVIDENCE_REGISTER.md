# Evidence Register

Labels follow strict epistemic discipline:
- **VERIFIED**: Directly observed via local execution, read-only RPC response, or fetched source artifact in this audit.
- **DOCUMENTED**: Stated in official TAPs/TapeOut docs, hackathon page, or ecosystem listings; not independently executed unless also marked VERIFIED.
- **INFERRED**: Derived logically from verified facts.
- **UNVERIFIED**: Not tested or not reachable.
- **CONTRADICTED**: Directly disproven by live chain/execution evidence.
- **BLOCKED**: Could not be executed under read-only/network constraints.

| ID | Claim / Observation | Status | Evidence / Artifact |
|----|---------------------|--------|---------------------|
| E-01 | X Layer mainnet RPC `https://rpc.xlayer.tech` responds with `chainId = 196` (head block 76,020,810 at initial probe; 76,046,274 at bench). | VERIFIED | `results/xlayer_probe_20261116_014404.json`, `results/bench_g.json` |
| E-02 | X Layer testnet RPC `https://testrpc.xlayer.tech` responds with `chainId = 1952` (not `195` as sometimes assumed). | VERIFIED | `results/xlayer_probe_20261116_014404.json` |
| E-03 | TAP-10 factory `0x1f09DAeFA827f02CBb40967cc91b259763760761` is deployed on X Layer mainnet (131-byte proxy, `cpuCount = 423`, `isSealed = 0`). | VERIFIED | `results/xlayer_probe_20261116_014404.json` |
| E-04 | Factory ERC-1967 implementation slot on X Layer mainnet is `0x336e9f0f4c3fee7c8c803377e4dea00293f4ae2a` (9,376 bytes), which **differs** from TAP-10's documented `0x74956236...`. | CONTRADICTED (doc) / VERIFIED (chain) | `results/xlayer_probe_20261116_014404.json`, `results/fee_scan.json` |
| E-05 | Factory beacon `0xf70d...0991C` points to circuit implementation `0x977f217887E085D298Cb3819cDAD5A0ee35F29B2` (12,562 bytes), matching TAP-10 docs. | VERIFIED | `results/xlayer_probe_20261116_014404.json`, `results/fee_scan.json` |
| E-06 | Processor 1 `0x0565EA48CA41Ae559d8d491dbb0a9ec945DB551b` matches docs (`name = "My4004"`, `symbol = "CPU"`, `nextId = 100`). | VERIFIED | `results/xlayer_probe_20261116_014404.json` |
| E-07 | TAP-10 factory address has **no code** on X Layer testnet (`chainId = 1952`). | VERIFIED | `results/xlayer_probe_20261116_014404.json` |
| E-08 | TAP issue #44's claimed "Circuit City Constitution" circuit at X Layer `0x8B61D4ad238F2f5BA6A8720444C5A6613f2e62F4` #1 has **zero circuits** (`nextId = 1`, processor index 258 on X Layer; no code on Base). | CONTRADICTED | `results/processor_enum.json`, `results/constitution_circuit.json`, `results/base_check.json` |
| E-09 | Base mainnet (`https://base-pokt.nodies.app`) shares the same factory and processor 1 addresses (`cpuCount = 106`, processor 1 `"TapeOutTestBase"`, `nextId = 10`). | VERIFIED | `results/base_check.json` |
| E-10 | All 18 official TAP-02 test vectors (5 valid, 8 ill-formed, 5 packing edge cases) pass identically on both `tap02_reference.py` and `independent_eval.py`. | VERIFIED | `results/semantics_matrix.json` |
| E-11 | Across 50 fetched X Layer circuits (`fixtures/corpus.json`), 35 circuits with recorded onchain `eval()`/`step()` results (224 stateless cases, 15 stateful circuits, 2 cross-processor `REF` wrappers `proc0#4` and `proc1#1` → `core#102`) match local simulation with 0 mismatches. | VERIFIED | `results/corpus_semantics_check.json` |
| E-12 | Half-adder composed from deployed `proc0#1` (XOR) and `proc0#2` (NAND) produces a deterministic 81-byte netlist (`2 REFs + 1 NAND`) matching the 4-row half-adder truth table on both evaluators. | VERIFIED | `results/composition_poc.json` |
| E-13 | `TAPEOUT_FEE` on X Layer mainnet is `0.0013 OKB` (`1,300,000,000,000,000 wei`), verified by ±1 wei `eth_call` scan. | VERIFIED | `results/tapeout_sim.json`, `results/tapeout_verdicts.json` |
| E-14 | Simulated `tapeout()` (`eth_call` with state override at `0.0013 OKB`) accepts the composed 81-byte half-adder through all TAP-02 §1–7 structural checks (reverts only at transistor burn `0x03dee4c5` with `needed=1` for its single top-level NAND), while rejecting 3 ill-formed controls with `"REF: pin mismatch"`, `"NAND: future signal"`, `"bad opcode"`. | VERIFIED | `results/tapeout_verdicts.json` |
| E-15 | Wiring Canary exact Tseitin+DPLL SAT matches exhaustive ground truth on all 4 half-adder mutants (2 equivalent UNSAT proofs, 2 differing SAT witnesses verified by `beat()`) and on an 8-input parity chain of 7 real XOR `REF` imports (28 NAND gates, 173 clauses, 11.02 ms), while both faulted and base parity pass TAP-02 §3 structural checks. | VERIFIED | `results/wiring_canary.json` |
| E-16 | Local simulation scales linearly: `decode` ~2.4 ms (1k gates) / ~27.0 ms (10k gates); `beat` ~0.27 ms (1k gates) / ~2.86 ms (10k gates, ~0.29 µs/gate) in pure Python 3.14.6. | VERIFIED | `results/bench_g.json` |
| E-17 | X Layer `eth_estimateGas`: `eval()` on `proc0#1` (XOR) = `55,924 gas`, `proc0#2` (NAND) = `53,674 gas`, `netlist()` getter = `40,524 gas`; `eth_gasPrice = 20,000,001 wei` (~0.02 gwei); public RPC median RTT = `1,317.3 ms`. | VERIFIED | `results/bench_g.json` |
| E-18 | TapeAPI lists 37 ecosystem tools including official `tapeout.net` canvas, `TapeOut.build` (BLIF export), `tapeout.pro` (exhaustive circuit-vs-task verifier), and `BEM Clock`. | DOCUMENTED | TapeAPI catalog fetched in Phase 1 |
| E-19 | OKX "X Layer TapeOut Accelerate" hackathon runs Oct 16 – Dec 7, 2026 23:59 UTC (100,000 USDT pool); developer tools are eligible and must submit an X Layer processor address + circuit ID + ≤3 min demo video. | DOCUMENTED | Hackathon announcement page |
| E-20 | Live onchain `tapeout()` transaction broadcast / transistor burn on X Layer mainnet. | BLOCKED (by audit policy) | Read-only constraint; simulated via `eth_call` state override only |
| E-21 | Exact Wiring Canary equivalence checking for **stateful** (`LATCH`) circuits. | UNVERIFIED (unsupported in PoC) | `wiring_canary.py` raises `ValueError` on `LATCH`; requires bounded model checking / k-induction |
