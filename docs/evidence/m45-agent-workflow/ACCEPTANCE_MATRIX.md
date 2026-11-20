# M4.5-1A — Agent workflow acceptance matrix

**Baseline:** accepted main after PR #5 merge, `1136b187bd68328cea4975caea50904ccece08fd`.
**Status:** independent test and contract corpus. The agent-native interface itself is not
implemented on this baseline; only cases mapped to existing CLI operations were executed.

Classification legend:

| Label | Meaning |
|---|---|
| **EXECUTED_OFFLINE** | Real `flip` CLI invoked with archived pinned inputs; no RPC |
| **EXECUTED_WITH_LOOPBACK_DOUBLE** | Real CLI invoked against a synthetic chain-196 RPC on loopback |
| **EXECUTED_ABSENCE_EVIDENCE** | Real command executed only to evidence that a capability does not exist |
| **PARTIAL_LIBRARY_DEPENDENT** | Unchanged path executed; stale/upgrade variant left to a future integration |
| **SPEC_ONLY_NOT_IMPLEMENTED** | Contract only; no successful result is claimed |

## A. Required workflow cases

| ID | Step | Classification | Command(s) / contract | Observed result |
|---|---|---|---|---|
| AW-01 | create_project | EXECUTED_OFFLINE | `flip sample half-adder` | exit 0; `M3_EXECUTION`, chain 196, archived identities |
| AW-02 | search_library | EXECUTED_WITH_LOOPBACK_DOUBLE | `flip library --request library-search.json` | exit 0; status `COMPLETE`, bounded page, no `CURRENT` |
| AW-03 | import | EXECUTED_WITH_LOOPBACK_DOUBLE | `flip import --processor … --id 1` | exit 0; `CIRCUIT_IMPORT`, manifest chain 196 |
| AW-04 | build | EXECUTED_OFFLINE | `flip compose --project half-adder.json` | exit 0; netlist hash `3dbb65a6…3ce` (81-byte composition) |
| AW-05 | test | EXECUTED_OFFLINE | `flip vectors --project half-adder-vectors.json` | exit 0; `VECTORS_MATCH`, 4 declared rows |
| AW-06 | compare | EXECUTED_OFFLINE | `flip compare --project half-adder.json` | exit 0; UNSAT / `EQUIVALENT` |
| AW-07 | inspect_difference | EXECUTED_OFFLINE | `flip sample swapped`, then `flip compare` | exits 0 then 1; `DIFFERENT` with replayed witness |
| AW-08 | inspect | SPEC_ONLY_NOT_IMPLEMENTED | CLI help shows no diagnostics command | Agent must report `UNSUPPORTED`; no cone or fault claim |
| AW-09 | propose_correction | SPEC_ONLY_NOT_IMPLEMENTED | Advisory patch against a declared prior mapping | Requires explicit human application |
| AW-10 | verify | EXECUTED_OFFLINE | `flip compare` after explicit correction | exit 0; full fresh comparison, `EQUIVALENT` |
| AW-11 | export | EXECUTED_OFFLINE | `flip export --project half-adder.json` | exit 0; `FLIP_EVIDENCE`, no chain claim |
| AW-12 | verify_bundle | EXECUTED_OFFLINE | `flip verify-bundle --project … --bundle …` | exit 0; `TRUSTED_LOCAL_COMPARISON`, recomputed |
| AW-13 | retry | EXECUTED_OFFLINE | 1 ms deadline compare, then default compare | exits 2 then 0; `UNKNOWN` then `EQUIVALENT` |
| AW-14 | revalidate | PARTIAL_LIBRARY_DEPENDENT | `flip revalidate --manifest manifest.json` | exit 0 on unchanged double; stale variant spec-only |
| AW-15 | stop_authorization | EXECUTED_ABSENCE_EVIDENCE | CLI help + read-only `flip preflight` | exits 0 then 2 (`UNKNOWN`); no publish/sign/broadcast command |

`results/executed-commands.json` records 18 real subprocess invocations: **18/18 expected
exit codes and all expected semantic fields matched**, with stdout/stderr/output SHA-256
digests and wall times.

## B. Negative and failure cases

| ID | Scenario | Classification | Expected safe behavior |
|---|---|---|---|
| AW-N01 | Malformed comparison output | SPEC_ONLY | Parse failure maps to UNKNOWN; no verdict/export |
| AW-N02 | Invalid schema | EXECUTED_OFFLINE | `flip validate project invalid-schema.json` exit 3 |
| AW-N03 | Stale bindings | SPEC_ONLY | STALE; no trusted composition input |
| AW-N04 | Unsupported circuit | SPEC_ONLY | Reject before solving; never EQUIVALENT |
| AW-N05 | Exhausted step/RPC budget | SPEC_ONLY | UNKNOWN + deterministic partial log; no infinite loop |

## C. Coverage of required topics

| Required topic | Coverage |
|---|---|
| Agent creates project from identities | AW-01 |
| Library search | AW-02 |
| Verified import | AW-03 |
| Composition | AW-04 |
| Truth-table validation | AW-05 |
| Trusted reference comparison | AW-06 |
| DIFFERENT + witness | AW-07 |
| Connection diagnostics | AW-08 (specification), M4.5-2D corpus |
| Correction proposal | AW-09 (specification) |
| Revalidation to EQUIVALENT | AW-10 |
| Evidence export | AW-11 |
| Cross-session verification | AW-12 |
| UNKNOWN + safe retry | AW-13 |
| Stale dependencies | AW-14 |
| Publication authority boundary | AW-15 |
| Malformed/invalid/stale/unsupported/exhausted | AW-N01…N05 |

## D. Not executed on this baseline

- AW-08, AW-09, AW-15's actual stop handoff and AW-N01/N03/N04/N05: no production
  agent-interface, diagnostic command or approval broker exists.
- The stale double for AW-14 and live library-derived `new-project` were not run.
- No signing, wallet, broadcast, payment or live chain observation.

A passing fixture is not a successful agent run and never creates transaction authority.
