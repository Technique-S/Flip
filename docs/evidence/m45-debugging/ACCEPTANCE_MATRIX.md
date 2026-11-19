# M4.5-2D — Acceptance matrix

**Status:** fixture-level evidence plus specifications for future production support.
No production diagnostic exists on the accepted M4 baseline; nothing here is a passing
product test.

## Classification legend

| Label | Meaning |
|---|---|
| **SOURCE OBSERVED** | Read from accepted source/evidence (gap audit, M3 schema, M4 browser evidence) |
| **EXECUTED FIXTURE CHECK** | Actually run by `verify_corpus.py` in this task; result recorded in `verification-transcript.json` |
| **SPECIFICATION ONLY** | Required future behavior; not implemented or executed here |

## A. Task A corpus coverage — all EXECUTED FIXTURE CHECK (generation and re-derivation)

| Case | Required coverage | Verdict | Differing bits | Diagnostic class |
|---|---|---|---|---|
| D01 | Swapped outputs | DIFFERENT | `[0,1]` | AMBIGUOUS_MULTIPLE_CAUSES |
| D02 | Incorrect REF input mapping | DIFFERENT | `[0]` | AMBIGUOUS_MULTIPLE_CAUSES |
| D03 | Duplicate fan-out | DIFFERENT | `[0]` | SUSPECTED_CANDIDATE |
| D04 | Disconnected/unbound pin | INVALID_INPUT | `[]` | STRUCTURAL_REJECTION_NO_ATTRIBUTION |
| D05 | Wrong output ordering | DIFFERENT | `[1,2]` | AMBIGUOUS_MULTIPLE_CAUSES |
| D06 | Multiple simultaneous changes | DIFFERENT | `[0,1]` | AMBIGUOUS_MULTIPLE_CAUSES |
| D07 | Nested REF dependencies | DIFFERENT | `[0]` | AMBIGUOUS_MULTIPLE_CAUSES |
| D08 | Equivalent rewiring | EQUIVALENT | `[]` | NO_FAULT_ATTRIBUTION |
| D09 | Several possible contributing connections | DIFFERENT | `[1]` | AMBIGUOUS_MULTIPLE_CAUSES |
| D10 | Exact defective connection not uniquely identifiable | DIFFERENT | `[0]` | AMBIGUOUS_MULTIPLE_CAUSES |

Each case stores exact circuit identities (`processorHex`, `circuitId`, `netlistHex`,
`netlistSha256`), output maps, exhaustive truth tables, witness inputs, reference and
candidate outputs, differing bits and a path-qualified cone. Truth tables are exhaustive
for every case (2, 4 or 8 inputs depending on the design) and are cross-checked by two
independent evaluators at generation time.

## B. Executed acceptance checks (Task E)

All rows below were executed by `python fixtures/m45-debugging/generators/verify_corpus.py`
with result `PASS`. Exact per-check counts are in `docs/evidence/m45-debugging/verification-transcript.json`.

| ID | Check | Required topic | Result |
|---|---|---|---|
| V01 | Manifest hash and byte size for all authored files | integrity | EXECUTED FIXTURE CHECK — PASS |
| V02 | Byte-identical scratch regeneration of all authored JSON | determinism | EXECUTED FIXTURE CHECK — PASS |
| V03 | Archived XOR#1 `[0,1,1,0]` and NAND#2 `[1,1,1,0]` calibration | trusted vectors | EXECUTED FIXTURE CHECK — PASS |
| E01 | Every DIFFERENT witness replays under recursive and flat evaluators | correct witness replay | EXECUTED FIXTURE CHECK — PASS |
| E02 | Differing output indices match an independent full truth-table diff | affected-bit accuracy | EXECUTED FIXTURE CHECK — PASS |
| E03 | EQUIVALENT cases produce no suspects | no false attribution | EXECUTED FIXTURE CHECK — PASS |
| E04 | Invalid/stale/UNKNOWN cases emit no verdict and no correction | UNKNOWN honesty | EXECUTED FIXTURE CHECK — PASS |
| E05 | D10 alternatives are distinct connections with an identical wrong table | multiple plausible causes | EXECUTED FIXTURE CHECK — PASS |
| E06 | Missing REF target is rejected and not attributed | missing dependency closure | EXECUTED FIXTURE CHECK — PASS |
| E07 | Cone node cap truncates and yields UNKNOWN | resource-limit handling | EXECUTED FIXTURE CHECK — PASS |
| E08 | Verified prior-mapping corrections restore equivalence in-fixture | correction guidance | EXECUTED FIXTURE CHECK — PASS |
| E09 | Guidance uses only the three allowed classifications; `llmOracle: NONE` | no unverified oracle | EXECUTED FIXTURE CHECK — PASS |
| E10 | Every diagnostic expectation sets `uniqueFaultClaim: false` | no unique fault claim | EXECUTED FIXTURE CHECK — PASS |

## C. Specification-only items (not executable on this baseline)

| ID | Item | Why not executable |
|---|---|---|
| S01 | Production UI highlighted source/destination pin pairs | No M4.5-2D component exists; highlight contract is pinned in `ux-expectations.json` |
| S02 | Browser announcements and non-color-only differing-bit display | Requires a real assistive-technology session on the future view |
| S03 | CLI diagnostic JSON and exit codes | No diagnostic command is implemented; contract follows M3/CLI conventions |
| S04 | Applying a candidate repair and rerunning the trusted comparator | Production edit/composition flow absent; fixture verifies the repair in isolation only |
| S05 | First-time developer usability with an unfamiliar mutation | Requires a human session |
| S06 | Live closure freshness / current chain state | No live RPC or publication authorized; all identities synthetic |

## D. Coverage of required acceptance topics

| Required topic | Coverage |
|---|---|
| Correct witness replay | E01, D01–D03, D05–D07, D09–D10 |
| Accurate affected-bit identification | E02, D01, D05, D09 |
| Equivalent designs get no false fault attribution | E03, D08 |
| UNKNOWN yields no definitive correction claim | E04, E07, S03 |
| Multiple plausible causes | E05, D01, D02, D05, D06, D09, D10 |
| Missing or stale dependency closure | E06, D04, S06 |
| Resource-limit handling | E07 |
| Traceability to a netlist connection | A-case cones (path + elementIndex + inputPin + netlistSha256); S01 |
| Accessible non-color-only descriptions | `ux-expectations.json`; S02 |

## E. Execution limits

- The independent evaluator is a stdlib reference. It does not establish production
  solver, native-engine or WASM parity.
- No test here executes against production Flip code; the verifier uses only its own
  generators and the committed fixture bytes.
- A `VERIFIED_CORRECTION` is scoped to restoring equivalence with a declared synthetic
  reference; it is not absolute proof of intended behavior.
- Timeout or resource-limit outcomes remain UNKNOWN and must never be relabeled to force a pass.
