# Independent CLI acceptance cases — M4-B

**Baseline:** accepted M3 integration head `af8ba1f109a2a1c59fe36be044bc025a127ea025`
(PR #3 head; see the setup deviation in the handoff).
**Machine source:** [`CASES.json`](CASES.json). **Captured evidence:**
`docs/evidence/m4-ux-acceptance/executed/` (`transcript.json`, `summary.json`,
per-case `C##.stdout.txt` / `C##.stderr.txt`).

Only commands already implemented on the M3 baseline were executed. Planned M4
commands (`preflight`, `export`, `verify-bundle`, `sample`) are recorded as
**executable specifications with observed NOT_IMPLEMENTED baseline behaviour**,
never as fabricated passing results.

## Reproduction

```powershell
uv sync --locked
uv run --frozen python fixtures/m4-ux-acceptance/generators/build_fixtures.py build
powershell -ExecutionPolicy Bypass -File fixtures/m4-ux-acceptance/generators/run_cli_cases.ps1
# consume fixtures must exist first:
uv run --frozen python fixtures/m4-ux-acceptance/generators/build_fixtures.py consumption `
  --equivalent docs/evidence/m4-ux-acceptance/executed/C04.stdout.txt `
  --different  docs/evidence/m4-ux-acceptance/executed/C05.stdout.txt
powershell -ExecutionPolicy Bypass -File fixtures/m4-ux-acceptance/generators/run_consumption_cases.ps1
uv run --frozen python fixtures/m4-ux-acceptance/generators/run_local_double_cases.py
uv run --frozen python fixtures/m4-ux-acceptance/generators/run_determinism_case.py
uv run --frozen python fixtures/m4-ux-acceptance/generators/verify_fixtures.py
```

`uv` 0.9.11 and CPython 3.14.6 were used. The local-double runner imports the
repository's committed offline transport from
`packages/flip-core/tests/test_m2_import.py` and binds an ephemeral loopback port;
it never contacts a live RPC endpoint.

## Executed cases

Commands below omit the `uv run --frozen` prefix used to invoke `flip`. Exit
codes are process outcomes; the JSON envelope / report is authoritative.

| ID | Command (abbreviated paths) | Exit | Semantic outcome | Journey |
| --- | --- | ---: | --- | --- |
| C01 | `flip --version` | 0 | `Flip 0.1.0` | — |
| C02 | `flip --help` | 0 | documented command set | — |
| C03 | `flip compose --project …/half-adder-equivalent.json` | 0 | netlist digest `0x3dbb65a6…` (audited 81 bytes) | J04, J05 |
| C04 | `flip compare --project …/half-adder-equivalent.json` | 0 | **EQUIVALENT**, UNSAT, HISTORICAL | J01, J03, J06 |
| C05 | `flip compare --project …/half-adder-different-output-order.json` | 1 | **DIFFERENT**, SAT, replayed witness | J01, J07 |
| C06 | `flip compare --project …/half-adder-unknown-timeout.json` | 2 | **UNKNOWN**, `SOLVER_TIMEOUT`, INTERRUPTED | J08 |
| C07 | `flip vectors --project …/half-adder-vectors.json` | 0 | `VECTORS_MATCH`, exhaustive declared domain (4 rows) | J06 |
| C08 | `flip compare --project …/half-adder-current-freshness-claim.json` | 0 | EQUIVALENT but **HISTORICAL** despite caller `CURRENT` flags | J03 |
| C09 | `flip compare --project …/malformed-request.json` | 3 | `INVALID_INPUT` | J11 |
| C10 | `flip compare --project …/unsupported-version.json` | 3 | `INVALID_INPUT` for `m4-1.0.0` | — |
| C11 | `flip inspect --chain-id 8453 --processor 0x839b… --id 1` | 3 | `WRONG_CHAIN` before state reads | J02 |
| C12 | `flip compare --project …/invalid-pin-map.json` | 3 | `INVALID_INPUT`, map `[0,2]` rejected before SAT | J04, J11 |
| C13 | `flip import --chain-id 8453 --processor 0x839b… --id 1` | 3 | `WRONG_CHAIN` | J02 |
| C14 | `flip inspect … --rpc-url http://127.0.0.1:1 --timeout-ms 200 --retries 0` | 4 | `RPC_UNAVAILABLE` | J10 |
| C15 | `flip validate circuit-identity docs/schema/examples/circuit-identity.json` | 0 | contract consistency only | — |
| C16 | `flip canonical circuit-identity …` | 0 | canonical normalized contract | — |
| C17 | `flip hash manifest …` | 0 | `profile=flip-json-v1`, content hash | J12 |
| C18 | `flip preflight --project …/half-adder-equivalent.json` | 6 | `NOT_IMPLEMENTED` (reserved M4) | J13 |
| C19 | `flip export --project …/half-adder-equivalent.json` | 6 | `NOT_IMPLEMENTED` (reserved M4) | J12 |
| C20 | `flip sample` | 6 | `NOT_IMPLEMENTED` (reserved M4) | J01 |
| C21 | `flip revalidate --chain-id 8453 --manifest …/import-manifest.json` | 3 | `WRONG_CHAIN` | J02, J09 |
| C22 | `flip consume --project …/consumption-valid.json` | 0 | recomputed EQUIVALENT, HISTORICAL | J03, J12 |
| C23 | `flip consume --project …/consumption-forged-verdict.json` | 3 | `INVALID_INPUT` — relabelled verdict rejected | J07, J12 |
| C24 | `flip consume --project …/consumption-changed-reference.json` | 3 | `INVALID_INPUT` — pinned reference mismatch | J09, J12 |
| C25 | `flip consume --project …/consumption-current-relabel.json` | 3 | `INVALID_INPUT` — false CURRENT rejected | J03, J12 |
| C26 | `flip consume --project …/consumption-different.json` | 1 | recomputed **DIFFERENT** with replayed witness | J07, J12 |
| C27 | `flip import --processor 0x839b… --id 1 --rpc-url http://127.0.0.1:<ephemeral> …` | 0 | successful import; `integrity.freshness=CURRENT` **within the local double only** | J02, J10 |
| C28 | same double with `nextId=1` | 3 | `MISSING_REFERENCE` — circuit not found | J02 |
| C29 | `flip compose …` ×100 | 0 | one distinct digest, equal to audited digest | J05 |
| C30 | `flip revalidate --manifest …/import-manifest-local-double.json …` after simulated beacon upgrade | 7 | `freshness=STALE`; old evidence retained | J09 |

## Required coverage map

| Required topic | Executed case(s) | Limitation |
| --- | --- | --- |
| Import success | C27 | local double with archived bytes; no live X Layer call |
| Import failure | C11, C13, C14, C28 | wrong chain, RPC outage, missing circuit |
| Compose | C03, C29 | deterministic compile verified |
| Compare | C04, C05, C06, C08 | all three verdict classes plus freshness guard |
| Witness display | C05, C26 | witness bytes captured from real output; web rendering is spec only |
| EQUIVALENT | C04, C22 | pairwise, HISTORICAL, intent-qualified |
| DIFFERENT | C05, C26 | replayed witness; not a correctness judgement |
| UNKNOWN | C06 | real 1 ms native worker timeout |
| Unsupported versions | C10 | `m4-1.0.0` rejected |
| Canonical export | C15–C17 | contract-level canonicalize/hash only; ZIP export is reserved |
| Malformed inputs | C09, C12 | invalid JSON and invalid pin map |
| Wrong chain | C11, C13, C21 | reject before state reads |
| Historical evidence restrictions | C08, C22, C25, C30 | false CURRENT rejected; STALE on environment change |

## Planned but unexecuted cases (executable specifications)

| ID | Planned command | Precondition | Expected M4 outcome | Current baseline |
| --- | --- | --- | --- | --- |
| P01 | `flip preflight --project <project> --format json` | live read-only RPC, fresh fee | one of STRUCTURALLY_ACCEPTED / REJECTED / UNKNOWN; no publication claim | C18: exit 6 NOT_IMPLEMENTED |
| P02 | `flip export --project <project> --out bundle.zip` | completed comparison | deterministic, path-safe bundle with SHA256SUMS and no secrets | C19: exit 6 NOT_IMPLEMENTED |
| P03 | `flip verify-bundle --bundle bundle.zip --format json` | exported bundle in clean environment | checksum and artifact validation, repeated local checks; never upgrades HISTORICAL | no M3 implementation; specification only |
| P04 | `flip sample --out sample.flip.json` | none | emits the pinned sample request for offline onboarding | C20: exit 6 NOT_IMPLEMENTED |
| P05 | live `flip inspect/import` against X Layer `chainId=196` | authorized RPC, verified chain per session | CURRENT single-RPC observation with block/hash pinned | not executed; prohibited in this task |
| P06 | browser E2E of J01–J13 | M4 web application present | see `../browser/ACCESSIBILITY_ACCEPTANCE_PLAN.md` | no web application in this branch |

## Honesty notes

- A successful `flip compare` exit (C04) is **not** proof of equivalence; the
  report's `verification.verdict`, solver outcome, limits and freshness are read
  separately.
- C27/C30 use a local double. Their `CURRENT`/`STALE` labels describe the
  simulated environment only and must never be quoted as live chain state.
- No case in this file was weakened or rewritten to force a pass. The two
  initially failing consumption variants were corrected in the *fixture
  generator* (an invalid extra field forbidden by the frozen contract and a
  misleading not-found double), not in production code or acceptance thresholds.
