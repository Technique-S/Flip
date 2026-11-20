# M4.5 agent + portable integration — independent review

**Role:** independent verification engineer (OpenCode / HY4 Flash).

| Role | Exact SHA |
|---|---|
| Accepted baseline | `bba6f3d301b08c0dcbbfd0b363b99a15179414db` |
| Agent workflow delivery | `d2638d057b6236286480891d6fdd7dfb0402bc5a` (ancestor confirmed) |
| Portable project delivery | `136b1115ee0f5ffe0a5583d68c474641fdce1ca1` (ancestor confirmed) |
| Agent workflow review evidence | `7b4b1f711ddc9676141becfae2fc77a3d5941374` (ancestor confirmed) |
| Portable review evidence | `8daacf7af2a1cfc17d83a33f7841d1088807ec82` (ancestor confirmed) |
| **Integration head tested** | **`cef5f4d0649eebb89bc237290eb949d9ecd823fb`** |

**Branch availability note:** the requested remote ref
`codex/flip-m45-agent-portable-integration` was **absent** from `origin` (`git ls-remote`
confirmed only the two delivery branches and earlier integrations). The integration head
was available as a **local** branch `codex/flip-m45-agent-portable-integration`; its two
merge commits (`f576cec`, `cef5f4d`) combine the agent-workflow-acceptance mainline with
the portable-project branch and both independent review evidence commits. Both delivery
SHAs are confirmed ancestors. This is recorded as a limitation; the exact local head SHA
above is what was tested.

**Recommendation: PASS.** No proof forgery, unauthorized operation, or silent original
overwrite was observed across the previously untested trust boundaries.

## 1. Commands executed

```powershell
# independent integration harness (real core/CLI/API)
.venv\Scripts\python.exe fixtures/m45-agent-portable-independent-review/harness/integration_acceptance.py

# inherited focused suites and corpus
.venv\Scripts\python.exe -m pytest -q packages/flip-core/tests/test_m45_agent_workflow.py packages/flip-core/tests/test_m45_portable.py -o junit_family=legacy
.venv\Scripts\python.exe scripts/check_m45_portability.py

# browser / schema / parity
cd apps/web; npm run build; npm test -- --reporter=list
cd ..; node docs/schema/m45-portable-project/check-canonical.mjs
.venv\Scripts\python.exe -m flip_core.agent_schema_export --out docs/schema/m45-agent-workflow/1.0.0 --check
.venv\Scripts\python.exe -m flip_core.portable_schema_export --out docs/schema/m45-portable-project/1.1.0 --check

# full suite and custody
.venv\Scripts\python.exe -m pytest -q --junitxml=... -o junit_family=legacy
.venv\Scripts\python.exe scripts/check_m1_repository.py
```

## 2. Independently executed outcomes (18/18, no harness errors)

| ID | Boundary | Observed |
|---|---|---|
| I01 | Portable package → agent execution identity | `open` hash equals package head; agent `compare` → EQUIVALENT |
| I02 | Raw package as workflow execution | rejected `INVALID_INPUT` — explicit open required |
| I03 | Named vector binding | portable `VECTORS_MATCH`/`PARTIAL_DECLARED_DOMAIN` equals agent `VECTORS_MATCH` on same vectors |
| I04 | Duplicate vector inputs | rejected `INVALID_INPUT` |
| I05 | Agent correction → new revision | apply `VERIFIED_CORRECTION`; original preserved; new sequence 1 with parent = genesis hash |
| I06 | Cancelled execution | `CANCELLED`, 0 logs, portable package bytes unchanged |
| I07 | Evidence generation → ref → replay | `FLIP_EVIDENCE` digest wrapped as ref; `REPLAYED`, trust `TRUSTED_ENGINE_REPLAY_ONLY` |
| I08 | Foreign evidence substitution | wrap accepts a self-consistent ref, but **trusted replay rejects** `INVALID_INPUT` |
| I09 | Revision-chain tampering | rejected `INVALID_INPUT` |
| I10 | STALE provenance | `open` blocked `IMPLEMENTATION_CHANGED`; `validate` still works (integrity only) |
| I11 | UNKNOWN / deadline | 2×`SOLVER_TIMEOUT` then UNKNOWN, final unchanged; separate 1-iteration budget → `BUDGET_EXHAUSTED` |
| I12 | STOP_AUTHORIZATION | terminal, 1 log, no signing capability, not retryable |
| I13 | CLI/API/core parity | workflow `reproductionHash` and portable `executionRequestHash` identical across core/API |
| I14 | Legacy compatibility | compose exit 0, `3dbb65a6…3ce`, portable round-trip exact |
| X01 | Forged correction | forged actionId → `STALE`, no correction, original unchanged |
| X02 | Authority-field injection | both protocols reject `INVALID_INPUT` |
| X03 | Reused old correction | `UNKNOWN`, final unchanged |
| X04 | Cancellation race | `CANCELLED`, 0 logs, package unchanged |

## 3. Trust-boundary findings

- **No silent original overwrite.** Apply and cancellation both preserve the original
  execution request and portable package; revisions are explicit new packages with a
  parent hash. Corrections are advisory until a fresh full comparison passes.
- **Wrap/validate is not proof.** `create_package` accepts a self-consistent evidence ref
  even when the artifact belongs to another project (I08 `wrapAccepted: true`), but the
  trusted `replay-evidence` consumer rejects it. This is the documented separation of
  data integrity from proof authority, and the decisive boundary held.
- **A valid hash chain authenticates neither author nor global namespace**; no author
  permission is inferred. All revision-chain tampering (missing parent, reorder, hash
  change, truncation) rejects.
- **STOP_AUTHORIZATION** is terminal across both workflows; continuing steps are not run.
- **No authority from metadata**: injected `transactionAuthority`, `approveAndPublish`,
  `signer`, `permissions` fields are rejected by both typed contracts.

## 4. Suites and regressions

- Focused agent + portable production tests: **69 passed**.
- Original 12-case portability corpus: **12/12 passed**.
- Chromium: **25/25 passed** on the integrated build (including both portable journeys;
  the earlier host-specific debugger flake did not recur here).
- Agent schema export, portable schema export, Python/Node canonical parity (3 packages): PASS.
- Credential scan over new evidence: 0 findings.

Full Python suite: **669 passed, 1 failed**. The single failure is
`test_git_provenance_and_secret_patterns`, caused solely by the custody-guard caveat
above (the previously committed large evidence XML). All other 669 tests — including
every agent-workflow, portable, debugger, library and inherited test — passed. No
production file, CI registry or original evidence was changed to obtain green results.

**Custody guard caveat:** `scripts/check_m1_repository.py` rejects
`docs/evidence/m45-portable-independent-review/results/pytest-full.xml` as an
"unexpected large tracked file" on the integration branch. That file is a **generated
evidence log from my own earlier portable review** (commit `8daacf7`), merged into this
integration head; the integration registry only whitelists the agent-workflow review's
blobs. This is integration bookkeeping, not a production or portable defect. I did **not**
modify production, CI, the registry, or original review evidence to obtain a green result.

## 5. Findings by severity

| Severity | Finding |
|---|---|
| CRITICAL / HIGH / MEDIUM | none |
| LOW | Integration custody registry omits a previously committed large generated evidence XML from the portable review; custody guard fails on that file. No security impact; bookkeeping only. |
| INFORMATIONAL | Integration branch existed locally but not on `origin`; tested the local head and recorded the limitation. |
| INFORMATIONAL | Wrap/validate accepts internally consistent forged evidence refs by design; trusted replay is the authority boundary and rejects them. |

## 6. Platform and unexecuted checks

No Linux process-tree containment, public solver exposure, human screen-reader session,
live RPC honesty, signing, broadcast or publication was tested. Windows is the tested
platform; cross-platform CI results are recorded externally, not re-executed here. The
full-suite custody caveat above is documented rather than patched.

## 7. Acceptance

**PASS** for `cef5f4d0649eebb89bc237290eb949d9ecd823fb`. The integrated agent + portable
implementation preserves identities, bounds tests/revisions, keeps evidence replay behind
trusted recomputation, preserves originals on failure/cancellation, and rejects all
forgery/authority/chain attacks exercised. Do not merge from this review branch.
