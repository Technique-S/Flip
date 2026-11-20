# M4.5-1A-V — Independent agent workflow review

**Role:** independent supporting verification engineer (OpenCode / HY4 Flash).

| Role | Exact SHA |
|---|---|
| Accepted baseline | `bba6f3d301b08c0dcbbfd0b363b99a15179414db` (ancestor confirmed) |
| **Delivery SHA tested** | **`d2638d057b6236286480891d6fdd7dfb0402bc5a`** |
| Original corpus | `996a300324877d0017cbe0cdb23d8da76692862c` |

Remote `codex/flip-m45-agent-workflow` head equalled the delivery SHA at review time;
no newer acceptance commit was found. **Recommendation: PASS.** No unauthorized action,
fabricated conclusive result or failed containment was observed.

## 1. Commands executed

```powershell
# focused production workflow tests
.venv\Scripts\python.exe -m pytest -q packages/flip-core/tests/test_m45_agent_workflow.py -o junit_family=legacy

# independent harnesses (real core / CLI / API)
.venv\Scripts\python.exe fixtures/m45-agent-workflow-independent-review/harness/independent_acceptance.py
.venv\Scripts\python.exe fixtures/m45-agent-workflow-independent-review/harness/authorization_checks.py

# shipped example through the real CLI
$env:FLIP_LOCAL_SOLVER=1
.venv\Scripts\flip.exe workflow --request docs/schema/m45-agent-workflow/examples/correction.json --out receipt.json

# suites / schema / custody
cd apps/web; npm run build; npm test -- --reporter=list
cd ..; .venv\Scripts\python.exe -m pytest -q --junitxml=... -o junit_family=legacy
.venv\Scripts\python.exe -m flip_core.agent_schema_export --out docs/schema/m45-agent-workflow/1.0.0 --check
.venv\Scripts\python.exe scripts/check_m1_repository.py
```

## 2. Task A — production workflow acceptance (independent, 27/27 executed)

`independent_acceptance.py` built its own requests and drove the real controller via
core and CLI. All 15 corpus scenarios and five negatives were covered:

| Area | Observed |
|---|---|
| Discover through bounded RPC double | `COMPLETE`, 21 read-only RPC calls (`READ_METHODS`), trust `SINGLE_UNTRUSTED` |
| Import verified source | `COMPLETE`, 19 RPC calls, fresh `CURRENT` (a genuine fresh read, not promotion) |
| Deterministic composition | `COMPLETE`, netlist hash `3dbb65a6…3ce` |
| Vector evaluation | `VECTORS_MATCH`, 4 rows |
| EQUIVALENT comparison | `COMPLETE` / `EQUIVALENT` |
| DIFFERENT + witness | `DIFFERENT`, `REF_BEAT_REPRODUCED`, 1 tool request |
| Connection debugging | `DIFFERENT`, 56 connections, `uniqueFaultClaim: false` |
| Candidate proposal | `CANDIDATE_ACTION`, final execution hash unchanged |
| Fresh verify + apply | six step statuses `DIFFERENT,DIFFERENT,COMPLETE×4`; verify/apply `VERIFIED_CORRECTION`; final verdict `EQUIVALENT`; original preserved |
| Export + cross-session replay | `FLIP_EVIDENCE`, replay `EQUIVALENT` |
| Bounded UNKNOWN retry | `UNKNOWN` after 2 attempts, both `SOLVER_TIMEOUT`, final hash unchanged |
| Stale dependency | `STALE`, log stops after 1 step, final hash unchanged |
| Prompt as permission | rejected `INVALID_INPUT` |
| STOP_AUTHORIZATION | terminal, 1 log, `signingCapability: false`, `retryable: false`, proposed action `ONCHAIN_PUBLICATION`, later queued step not run |
| Fabricated report / false correction / other project | all rejected; final execution unchanged |

Negatives: malformed worker output → UNKNOWN; invalid schema → INVALID_INPUT; corrupted
manifest hash → INVALID_INPUT; unsupported circuit → UNKNOWN/INVALID_INPUT; exhausted
iteration budget → BUDGET_EXHAUSTED. The shipped CLI correction example produced a
6-step `COMPLETE` receipt (exit 0). The focused Codex workflow suite: **47 passed**.

## 3. Task B — authorization findings (10/10 clean)

`authorization_checks.py` confirmed:

- `permissions`, `approvalToken`, `transactionAuthority`, `signer` injected at request
  or step level are rejected (`extra=forbid` at the typed boundary) — `INVALID_INPUT`.
- A write catalog operation (`tapeout`) is rejected; discovery accepts only
  read-only library operations.
- A fabricated `STOP_AUTHORIZATION` artifact cannot be selected as an import/build
  source (`INVALID_INPUT`).
- HISTORICAL imports remain HISTORICAL through compare and export (`promoted: false`).
- A forged correction action ID, changed execution hash, or applied-to-another-project
  binding yields STALE/INVALID_INPUT with the final execution unchanged.
- API parity: same status and `reproductionHash` as core; solver-disabled API returns 501.
- The reusable skill (`SKILL.md`) and integration guide explicitly state instructions
  are never transaction authority; the runtime type boundary enforces this regardless
  of instruction text. No network write method is reachable.

**No authorization bypass or fabricated conclusion was found.**

## 4. Task C — bounded execution and cancellation

- Cancel before execution: `CANCELLED`, 0 logs, 0 tool requests.
- Cancel during execution: `CANCELLED`, 1 log, `rpcAccounting: RESERVED_ON_INTERRUPTION`,
  no late wire requests arrived after cancellation (late result discarded).
- Iteration / tool-request / overall deadline ceilings each produced
  `BUDGET_EXHAUSTED` with partial logs and no COMPLETE step.
- `boundary()` is polled before every attempt and again after each operation; a late
  successful worker result cannot override cancellation or deadline. `next_current`
  is committed only from the worker's process-local execution request and only for
  COMPLETE/DIFFERENT/STOP_AUTHORIZATION — a cancelled operation selects no new revision.
- Windows uses a kill-on-close Job (launcher+operation+solver, 512 MiB); Linux uses
  RLIMIT_AS/CPU and parent-death signalling with process-group kill; unsupported
  platforms fail closed. These are observed design/implementation facts; actual
  cross-platform process-tree behaviour on Linux was not exercised locally (CI is
  recorded separately).

## 5. Task D — reproducibility and trust binding

- Two identical requests produced identical status, `reproductionHash` and chained
  `entryHash` values; `receiptHash` equals the checksum of the rest of the receipt —
  a checksum, not a proof certificate.
- `engineHash` is bound to controller + engine source bytes; scope is
  `LOCAL_BOUNDED_HISTORICAL_REFERENCE_RELATIVE`.
- Malformed service output maps to UNKNOWN; changed references between steps fail.
- CLI/API/core semantic equivalence confirmed (E09, D03).

## 6. Suites and findings

- Focused workflow tests: 47 passed. Independent harness: 27/27 executed, no errors.
- Authorization checks: 10/10 clean. Chromium: **23 passed**.
- Agent-workflow and inherited schema drift checks: PASS. Custody/credential guard:
  PASS (0 findings). A Windows `core.autocrlf` CRLF artifact in previously merged
  review evidence initially failed the custody check; after restoring pinned LF bytes
  the guard passed. No production failure was observed.
- Full Python suite: **647 passed, 1 failed**. The single failure is
  `test_custody_and_scratch_regeneration` — a known 120 s `subprocess.TimeoutExpired`
  in the inherited M3-B scratch verifier (the F-03 finding from earlier reviews), not
  an agent-workflow or production failure. All custody/hash assertions in that test
  before the timed subprocess passed, and the standalone custody guard returned PASS.

| Severity | Finding |
|---|---|
| CRITICAL / HIGH / MEDIUM / LOW | none |
| INFORMATIONAL | CRLF checkout artifact in previously merged review evidence (environment, not production). |
| INFORMATIONAL | Full-suite `test_custody_and_scratch_regeneration` hit its known 120 s inner timeout (F-03); the custody guard itself passes and no library regression was reproduced. |
| INFORMATIONAL | A fresh import legitimately reports `CURRENT` because it performs a new read; this is distinct from promoting saved HISTORICAL evidence, which was confirmed absent. |

## 7. Limitations

Linux process containment and native solver behaviour were not exercised locally;
cross-platform CI results are recorded externally. Human screen-reader and
first-time-developer usability sessions were not performed. No live RPC honesty,
public hosting, signing, broadcast or publication was tested. Timeouts and malformed
outputs remain UNKNOWN by design.

## 8. Acceptance

**PASS** for `d2638d057b6236286480891d6fdd7dfb0402bc5a`. The controller is bounded,
deterministic, reproducible and unable to bypass the trusted importer or authorization
boundary. Do not merge from this review branch.
