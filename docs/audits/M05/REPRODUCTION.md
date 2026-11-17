# Reproduction Guide — M0.5 Final Verification

All commands use **Python 3.14.6** and are read-only with respect to X Layer (no transactions, no credentials, no funds). Working directory for all commands unless noted: `C:\research\circuitforge-feasibility\m05-final-verification\experiments`.

## Prerequisites
- Original audit artifacts at `C:\research\circuitforge-feasibility\experiments\` (preserved unchanged) are imported as modules (`tap02_reference.py`, `compose_poc.py`, `wiring_canary.py`).
- Isolated solver vendor directory: `experiments\vendor\` (`python-sat 1.9.dev22`, Minisat22; installed via `pip install python-sat --no-deps --target vendor` — no global install).
- Public RPCs: `https://rpc.xlayer.tech` (chainId 196), `https://base-pokt.nodies.app` (chainId 8453).

## Gate A — Publication readiness
```
python src\gate_a_probe.py        # selector proof, TAPEOUT_FEE, transistor address, registration
python src\gate_a_probe2.py       # revert arg decode, storage-override capability, estimateGas
python src\gate_a_probe3.py       # transistor contract bytecode inspection
python src\selector_scan.py       # per-contract selector presence
python src\token_inspect.py       # transistor contract storage
python src\proc0_inspect.py       # PROC0 storage/beacon proxy structure
```
Also from the original package (composition reproduction, output saved here):
```
cd C:\research\circuitforge-feasibility
python experiments\src\compose_poc.py > m05-final-verification\experiments\results\gate_a_compose_rerun.json
```
Evidence: `results/gate_a_probe*.json`, `results/gate_a_compose_rerun.json`, `results/selector_scan.json`.

## Gate B — Integrity manifest + negative tests
```
python src\gate_b_manifest.py     # live canonical manifests for xor1 + wrapper4 (REF closure)
python src\gate_b_negative.py     # 9 synthetic negative fixtures + live cross-chain checks
```
Evidence: `results/gate_b_manifest.json`, `results/gate_b_negative.json`.

## Gate C — Wiring Canary scale
```
python src\gate_c_worker.py "<json config>"    # single-case worker (invoked by the parent)
python src\gate_c_scale.py                     # full benchmark (checkpoints to gate_c_scale_partial.json)
python src\gate_c_finalize.py                  # merges checkpoint + safeguards + stateful PoC -> gate_c_scale.json
python src\gate_c_stateful.py                  # standalone bounded k-beat trace comparison
```
Evidence: `results/gate_c_scale.json`, `results/gate_c_scale_run.txt`.

## Gate D — Differentiation
- Official canvas bundle saved at `fixtures/tapeout_net_bundle.js` (SHA-256 `0c532120c91d15367da384da0dad3692f03acaee321c874aad3963c8c5aebf0c`; fetched from `https://tapeout.net/app/assets/index-DizVcbig.js` with browser headers via `curl.exe`); feature extraction:
```
python src\bundle_inspect.py
python src\bundle_inspect2.py
```
- `tapeout.pro` homepage text fetched 2026-11-16 (-homepage, "Circuit Verifier" section).
- `tapeout.link` description fetched 2026-11-16.
- TapeKit README fetched from `https://raw.githubusercontent.com/TapeOutProtocol/TapeKit/main/README.md`.
Evidence: `results/bundle_features.json`.

## Key assertions to check in outputs
- `gate_a_probe.json`: `errorSelectorCheck.matches == true`; `TAPEOUT_FEE() == 0x49e57d6354000`; `isSealed() == 0`.
- `gate_a_probe2.json`: `overrideSupported == false`; `tapeoutSimFull.status == "reverted"`; revert args `(0xf00d, 0, 1, 0)`.
- `gate_b_negative.json`: `allNegativeDetected == true`; `chainIds` 196 vs 8453.
- `gate_c_scale.json`: all 7 correctness safeguards `passed == true`; timeouts map to UNKNOWN; Minisat22 verdicts match expected across all 7 gate counts (50–5,000); `gate_c_stateful.json.firstDifferenceBeat == 0`, `reproducible == true`.
