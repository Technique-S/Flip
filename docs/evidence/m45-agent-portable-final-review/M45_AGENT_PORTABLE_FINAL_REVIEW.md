# M4.5-1I-V2 — Final adapter delta independent review

**Role:** independent verification engineer (OpenCode / HY4 Flash).
**Scope:** PR [#9](https://github.com/Technique-S/Flip/pull/9), the *final* adapter
introduced by `303203a` (not the pre-adapter `cef5f4d` tested by the earlier review).
No wallet, signing, transaction construction, broadcast, payment or publication was
performed or configured.

## 0. Exact revisions tested

| Role | Exact SHA | Verified how |
|---|---|---|
| Reported final head / PR #9 head | `9c0c23698dfd1c7045de348da851c28d68f5e22b` | `git fetch origin refs/pull/9/head`; remote PR ref and GitHub API both resolve to this SHA |
| CI-tested production/custody revision | `f3d7b8e50fc5415af8cf50bf2c7319529915c4f0` | object present; CI run 44727792029 head SHA |
| Previous independent review (insufficient) | `182b96f99a4212447d0b7a37e9a01805c9f053dd` | object present in fetched history |
| Earlier review's tested head (pre-adapter) | `cef5f4d0649eebb89bc237290eb949d9ecd823fb` | delta base for this review |
| Accepted main base | `b9042cc66775405b5d0ca5a2be35197dabad0527` | PR base via GitHub API |

The head has **not moved**: `refs/remotes/origin/pr-9-head` equals the reported SHA.
PR #9 is `open`, `draft: true`, `merged: false`, `merged_at: null`. The branch
`opencode/flip-m45-agent-portable-final-review` was created from the exact head
`9c0c2369…`; no merge was made.

**Verdict: PASS.** No proof forgery, unauthorized authority, silent original
overwrite or custody defect was found in the final adapter delta. The earlier
review's PASS could not have served as approval of this code; this review does.

## 1. Task A — adapter delta (`cef5f4d..9c0c2369`)

Material production commits in the delta:

| Commit | Content |
|---|---|
| `303203a` | Additive `agent_portable_adapter.py`, schemas/goldens, CLI/API/React integration, byte-pinned portable review custody |
| `4287f8e` | Snapshot caller-owned mutable objects through canonical bytes before pin validation (`parse_adapter` re-loads the canonical snapshot) |
| `fa2c769` | Fail closed before extending a full portable revision chain (ancestry budget checked before work; final cancellation check) |
| `f3d7b8e` | Compare historical research bytes via `git -c core.autocrlf=false archive` |
| `9c0c2369` | Documentation only (handoff) — no production change |

Findings:

- **Adapter.** One bounded controller invocation; exact package/revision/request
  pins; adapter-generated steps use reserved `pp_` IDs; `raw_candidate` proves only
  `project.candidate` wiring changes; revision commit requires every post-test and a
  fresh trusted export with `EQUIVALENT` verdict; explicit `apply` records ordered
  raw before/after hashes. Confirmed by source review and independent execution.
- **Schemas.** `m45-agent-portable-1.0.0` request/result/preparation schemas and
  685-line golden; schema export `--check` passes; Python/Node canonical parity passes.
- **CLI/API.** `flip agent-portable` (plus `--prepare`, `--cancel-file`) added while
  `workflow`/`portable`/other legacy commands remain; API adds `/api/agent/v1/portable`
  and `/api/v1/agent-portable` (plus `/prepare` aliases), loopback-only, `FLIP_LOCAL_SOLVER`
  opt-in, two-slot admission, 1 MiB cap, disconnect cancellation. Legacy
  `/api/agent/v1/execute` and `/api/v1/portable` remain registered. Verified by diff
  review and live calls (§2/B14, P01).
- **React.** `AgentPortable.tsx` adds cancellation with late-result discard,
  STOP_AUTHORIZATION notice, separate receipt/evidence, and explicit
  "Open verified revision" / "Download verified revision" actions; no implicit
  project replacement. Both `agent-portable.spec.ts` workflows pass in Chromium.
- **Debugger synchronization.** `debugging-acceptance.spec.ts` now awaits the actual
  `/api/v1/debug` `verify-correction` response and asserts
  `VERIFIED_CORRECTION` / `EQUIVALENT` before the unchanged 5 s UI locator. This is a
  test-only delta: no global retry, no timeout increase. It passes in Chromium.
- **Frozen contracts and engine.** No change to comparator, SAT implementation,
  portable validator, accepted controller or frozen schemas; the delta is additive.

## 2. Task B — independent production execution

Harness: `fixtures/m45-agent-portable-final-review/harness/independent_adapter_checks.py`.
It drives the **real** core adapter, CLI and loopback API. Expected hashes are
recomputed by a standalone `json`+`hashlib` implementation of flip-json-v1 that does
not import `flip_core.canonical`; structural and authority invariants come from the
contract, not production output. Raw results:
`docs/evidence/m45-agent-portable-final-review/results/independent-adapter-checks.json`.

**Result: 26/26 checks pass** (checks B01–B15, C01–C10, P01). Highlights:

| ID | Check | Independently observed |
|---|---|---|
| B01 | Identity binding | Standalone SHA-256 of package/request equals `expectedPackageHash` (`0x9e7236…c319c`) and `expectedExecutionRequestHash` (`0x651541…e52`); all three tampered pins reject `INVALID_INPUT` |
| B02 | Named vectors | Good vectors → `pp_before0` `VECTORS_MATCH` / `EXHAUSTIVE_DECLARED_DOMAIN`; deliberately wrong expected output → `DIFFERENT`, no revision |
| B03 | DIFFERENT + debug | witness replay `REF_BEAT_REPRODUCED`; `uniqueFaultClaim: false` |
| B04–06 | Verify / apply / revision | `VERIFIED_CORRECTION` on verify and apply; independently recomputed `actionId` `0xa27b18…4509` matches exactly; `parentHash ==` original head; sequence `0→1`; `ancestors[-1]` = original; candidate equals declared reference; original unchanged |
| B07 | Original preservation | input body/package byte-equal after run; `originalPackage ==` input |
| B08 | Evidence/replay | old ref only in `originalPackage`; fresh refs bind revised head; trusted replay `REPLAYED` / `EQUIVALENT` / `HISTORICAL` |
| B09 | Cross-project evidence | foreign artifact → `INVALID_INPUT`, `inputEvidence=NOT_REPLAYED`, no revision |
| B10 | Changed dependency | revalidate with changed beacon → `STALE`, 1 log, no revision |
| B11 | Cancellation | immediate and post-hash race → `CANCELLED`, no receipt/revision, original preserved |
| B12 | Deadline/budget | `deadlineMs=1` → `BUDGET_EXHAUSTED`; `maxIterations=1` → `BUDGET_EXHAUSTED` with `iterations=1`; too-small receipt budget rejected before execution |
| B13 | Repeated/concurrent | body unchanged; readonly deterministic; two concurrent corrections produce sibling revisions from the same parent |
| B14 | Legacy routes | `/api/agent/v1/execute` 200, `/api/v1/portable` 200, `flip compose` exit 0 |
| B15a/b | STOP_AUTHORIZATION | PUBLISH and DEPLOY → `STOP_AUTHORIZATION`, 1 log, `signingCapability:false`, `retryable:false`, no revision, original preserved |
| P01 | Interface parity | CLI exit 0, API 200, core/CLI/API `reproductionHash` identical; `resultHash` equals standalone hash of the result minus itself |

## 3. Task C — adversarial attacks

All ten attacks fail closed. Every failure case was asserted to have
`revisionCreated == false`, `revisedPackage is None`, and `originalPackage ==` input
(the harness `no_authority` invariant), so no failure overwrites the original or
creates an authoritative proof claim.

| ID | Attack | Observed result |
|---|---|---|
| C01 | Forged `VERIFIED_CORRECTION` actionId | `STALE`; no revision; original preserved |
| C02 | Altered original package hash (content changed, pin unchanged) | rejected `INVALID_INPUT` before execution |
| C03 | Forged parent revision | rejected `INVALID_INPUT` |
| C04 | Project mutation after admission | adapter snapshot unchanged; steps retained; pin still matches standalone hash |
| C05 | Reused correction ID on another package | `UNKNOWN`; no revision; original preserved |
| C06 | Foreign evidence / forged engine hash | `INVALID_INPUT`; no revision; original preserved |
| C07 | Authority metadata (`transactionAuthority`, `approveAndPublish`, `signer`, `permissions`, step-level authority) | all rejected `INVALID_INPUT` |
| C08 | Cancellation racing revision creation | `CANCELLED`; no revision; original preserved |
| C09 | Budget reset between adapter/controller | `BUDGET_EXHAUSTED`, `iterations=1`; no revision |
| C10 | Forged `CURRENT` freshness | fail closed (`BUDGET_EXHAUSTED` via `revalidate`/`OPERATION_DEADLINE`); no revision; no `CURRENT` promotion; original preserved |

## 4. Task D — custody discrepancy disposition

**Precise finding: already resolved by reviewed changes at the exact PR #9 head;
still reproducible only on the stale checkout. Not a weakening, not an unresolved
defect.**

- **Actual file:** `docs/evidence/m45-portable-independent-review/results/pytest-full.xml`
  — a generated evidence log from commit `8daacf7`, size **200,624 bytes** (> the
  200,000-byte guard), Git blob `9691b5807acbd21d4d9b756b08e4e6012b06f364`,
  checkout SHA-256 `84f68c68…f96a8`. It is one of the 18 byte-pinned review files
  and is intentionally **omitted** from the 11-entry review manifest.
- **Applicable guard rule:** `scripts/check_m1_repository.py` rejects any tracked
  file over 200,000 bytes unless it is a registered large artifact or a pinned
  review blob. At `cef5f4d` the allowlist covered only `workflow_review_blobs`, so
  this XML failed with `unexpected large tracked file`; the previous review recorded
  that as a LOW bookkeeping finding and did not patch it.
- **Codex final registry / CI-tested tree:** `303203a` added
  `portable_review_evidence()`, which pins all 18 portable-review bytes to the exact
  Git blobs of revision `8daacf7` and byte-compares the checkout, and added
  `path in portable_review_blobs` to the large-file allowlist — a precise
  registration of immutable evidence, not a broad exception. `f3d7b8e` further
  disabled `core.autocrlf` for the historical research `git archive` comparison.
  Both are present at `9c0c2369`.
- **Independent verification:** `python scripts/check_m1_repository.py --require-clean`
  at the exact head exits 0 with `"result": "PASS"` and reports
  `portable_independent_review: {revision 8daacf7, target 136b111, files 18,
  manifestEntries 11}` and `portable_research: {files 36, additionalPinnedHarness …}`.
  The stale `repo` checkout at `182b96f9` contains neither function, so the old
  failure remains reproducible there only.
- **No weakening:** the guard still requires byte-for-byte equality with the
  original Git blob; altering the XML would still fail.
- Related but distinct Windows-only `git archive` autocrlf custody failure (CI run
  44727125851 at `fa2c769`) is resolved by `f3d7b8e`; CI run 44727792029 at
  `f3d7b8e` passes the custody/credential step on both OSes.

## 5. Task E — final acceptance

Locally executed at exact head `9c0c2369…` (Python 3.14.6, Node 24.18.0, Windows):

| Check | Result |
|---|---|
| Focused adapter suite `test_m45_agent_portable.py` | **32 passed** (145.68 s) |
| Independent adapter/attack harness | **26/26 pass** |
| Full Chromium (`npm test`) | **27 passed**, incl. both portable-agent workflows and debugger sync (2.8 min) |
| Schema drift: agent, portable, adapter exports `--check` | all exit 0 |
| Python/Node canonical parity: adapter plan/pins, 3 portable packages, 6 base vectors | all exit 0 |
| Portability corpus | **12/12 passed** |
| Agent acceptance + authorization checks | **27/27** and **10/10** exact semantic checks |
| Custody + credential guard `--require-clean` | **PASS**, 0 credential findings |
| Final delta scope | `9c0c2369` changes only the handoff markdown; `f3d7b8e` changes only the custody script |

Remote CI (verified via GitHub API):

- Exact head `9c0c2369…`: run **44729535286** (PR #9) — `conclusion: success`,
  both `contracts (windows-latest)` and `contracts (ubuntu-latest)` jobs and every
  step succeeded. Push run 44729527184 also succeeded.
- CI-tested production rev `f3d7b8e…`: run **44727792029** — `conclusion: success`,
  both OS jobs all steps (including full pytest, 27 Chromium, schema/parity, custody,
  smokes) succeeded.
- Earlier failing run **44727125851** at `fa2c769…` (pre-autocrlf-fix) is the recorded
  Windows custody failure, superseded as above.

Full local Python suite: **702 passed in 641.43 s (0:10:41), exit 0, no skips**
(`pytest -q --junitxml=… -o junit_family=legacy` with `FLIP_LOCAL_SOLVER=1`;
raw log `m45-full-suite.log` and junit `m45-final-junit.xml` retained in the review
temp directory). This matches the hosted Linux/Windows and local Windows counts
recorded in the integration handoff.

## 6. Limitations

- Verification is structural/historical/relative; no live RPC chain revalidation,
  human screen-reader session, Linux local process-tree containment or public solver
  exposure was exercised. These are outside the bounded local adapter scope.
- Vector verdicts are cross-checked between the adapter and the portable test path;
  hashes, authority invariants and revision structure are independently computed.
  A from-scratch TAP-02/SAT evaluator was not reimplemented.
- C10's forged-`CURRENT` attempt failed closed via `OPERATION_DEADLINE`/budget rather
  than an explicit "invalid freshness" message; the decisive property (no revision,
  no CURRENT promotion) held.
- The earlier review's CONDITIONAL PASS is not rewritten; this is a separate review
  of the final adapter delta.

## 7. Provenance and modified files

Only documentation and an independent fixture were added on the dedicated branch:

- `docs/evidence/m45-agent-portable-final-review/M45_AGENT_PORTABLE_FINAL_REVIEW.md` (this file)
- `docs/evidence/m45-agent-portable-final-review/results/independent-adapter-checks.json`
- `fixtures/m45-agent-portable-final-review/harness/independent_adapter_checks.py`

No production file, CI registry, frozen contract or original evidence was modified.

## 8. Acceptance

**PASS** for `9c0c23698dfd1c7045de348da851c28d68f5e22b`. The final adapter preserves
exact identities and originals, bounds work and deadlines, keeps evidence replay
behind trusted recomputation, commits revisions only through explicit verified apply
plus post-tests/export, terminates publication at STOP_AUTHORIZATION, and rejects all
tested forgery/authority/custody attacks. Do not merge from this review branch.
