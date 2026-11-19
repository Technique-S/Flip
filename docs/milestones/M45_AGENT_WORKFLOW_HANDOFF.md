# M4.5 — Bounded agent workflow implementation handoff

Date: 2026-11-20 (Africa/Lagos). Delivery branch: `codex/flip-m45-agent-workflow`.
**Implementation complete; independent production review remains required. Do not merge.**
The acceptance verdict and exact platform observations are recorded below and in
[validation results](m45-agent-workflow/validation-results.json).

| Role | Exact commit |
|---|---|
| Accepted debugger main, PR #7 confirmed merged | `bba6f3d301b08c0dcbbfd0b363b99a15179414db` |
| Original independent agent corpus | `996a300324877d0017cbe0cdb23d8da76692862c` |
| History-preserving corpus integration | `1baea9518f2b08508258e11b9c6f5160ba3d99cd` |
| Initial production implementation | `5fb91579cbe6f79fefef2ff7059ff80f1af27d0f` |
| Final tested production code | `0ba49cdb2aa804f8ecd9aca066b5433a747e169a` |

The delivery commit after the tested production revision adds only this handoff and
validation record. Its exact SHA is reported in the delivery response. Main stays at
the accepted debugger baseline. No PR or merge is performed by this milestone.

## Production behavior

`flip_core.agent_workflow.execute`, `flip workflow --request ... --out ...`, and
`POST /api/agent/v1/execute` share one additive protocol,
`m45-agent-workflow-1.0.0`. See the [contract](../schema/m45-agent-workflow/README.md),
[integration guide](../agents/WORKFLOW_INTEGRATION.md),
[reusable skill](../../.agents/skills/flip-agent-workflow/SKILL.md), and
[executable correction request](../schema/m45-agent-workflow/examples/correction.json).

The controller dispatches a finite list of typed operations to the existing Python
importer, library, compiler, vector evaluator, comparator, debugger and evidence
consumer. Discover/import/build/test/compare/inspect/propose/verify/apply/export,
portable bundle replay, revalidation and a terminal publication handoff are supported.
It contains no LLM, natural-language synthesis, shell command, dynamic module choice
or agent-supplied Python execution. External agents supply explicit goals, references,
vectors and structured candidate mappings. Library pagination/cursors and selected
identities are declared inputs; the controller does not infer authorization or an
executable circuit from names or discovery metadata.

Each attempt has versioned inputs, structured outputs/errors, retryability,
project/execution hashes, a semantic output hash, a chained log hash, cumulative usage
and remaining count budgets. Full receipt checksums include the original raw runtime
observations; deterministic reproduction hashes exclude the documented empirical
fields. Same-platform successful replay produces the same semantic trace. Neither
checksum is a proof certificate: bundle verification always recomputes with the
existing engine against a separately selected execution request.

Maximum iterations, tool requests, aggregate wire attempts, overall deadline,
per-operation deadline/output budgets, import/trace limits, project proof limits
and receipt bytes are enforced. Overall timing includes admission and engine-identity
setup. Every operation runs in a contained, short-lived worker. Parent polling
cancels, kills and reaps active work; late results cannot select a revision. Windows
uses a kill-on-close Job for its venv launcher, operation and native solver. The
existing nested solver retains its separate one-process/64 MiB/five-second cap.
Linux uses address-space/CPU limits and parent-death containment. Only a trusted
internal helper's optional outer process count was added; default solver behavior
and all frozen resource contracts are unchanged.

Only an explicitly retryable UNKNOWN can retry, under an explicit policy and all
remaining budgets. A retry never changes the selected project's proof limits or
reference. DIFFERENT is completed evidence, not a transient error. STALE,
BUDGET_EXHAUSTED, CANCELLED, INVALID_INPUT and STOP_AUTHORIZATION terminate. A new
request is required for recovery. Wire usage after a killed worker is conservatively
reserved and labeled, rather than fabricated as an exact observed count.

Corrections preserve the original project. A proposal can restore the debugger's
declared local prior or carry externally supplied numeric mappings; it remains
CANDIDATE_ACTION. Only candidate wiring may change. Reference, source bindings,
imports, intent and limits must match the exact original execution hash/action ID.
A separate verification step runs a new trusted comparison. Explicit local apply
requires VERIFIED_CORRECTION and runs another comparison immediately before selecting
the revision. Export compares again. Reusing an old action after application or
changing its project/reference fails closed. Structural cone membership never proves
a uniquely defective wire; vector success never becomes universal equivalence.

An onchain publication request becomes terminal **STOP_AUTHORIZATION** (CLI exit 9),
with proposed action, exact project/execution/netlist/manifest identities and a human
handoff reason. It contains no signing capability, grant, token or resumable approval.
Remaining steps and retries cannot override the stop. Prompts, metadata, aliases,
receipts and skill text never become permissions. The proposed authorization
architecture `8ea1b26c2667b2db86c34087e25c976f121c147e` is not an ancestor of this branch.

## Independent corpus and compatibility decisions

All **31 original files** and **30 manifest entries** remain exact original Git and
checkout bytes, including the original report and manifest. The custody guard checks
history, exact scope inventory, batched original/current blobs, checkout bytes,
manifest coverage, sizes and hashes. Exact archive attributes and three narrow Ruff
generator exclusions preserve evidence. Credential, binary and 200,000-byte checks
are unchanged; no broad exception or test namespace bypass was added.

The original handoff records 27 manifest entries; the actual committed manifest has
30. Its 18 historical CLI invocations and baseline/absence observations remain
unchanged and are not credited with testing this implementation. A separate
production adapter executes all 15 cases and five negatives against current services.

| Corpus cases | Actual production coverage / disposition |
|---|---|
| AW-01 | Historical sample creates an explicit pinned M3 project. |
| AW-02 / AW-03 | Bounded registry discovery and fresh M2 import through synthetic loopback RPC, with wire accounting. |
| AW-04 / AW-05 | Existing 81-byte composition hash and four declared vector rows. |
| AW-06 / AW-07 | EQUIVALENT; DIFFERENT with an independently replayed witness and no retry. |
| AW-08 | Current accepted debugger traces paths without unique fault attribution; the older baseline's UNSUPPORTED observation is preserved. |
| AW-09 | Separate, bound candidate proposal; no implicit application. The later apply test is an explicit local step authorized by its declared workflow. |
| AW-10 | Fresh verification, explicit apply with another verification, then EQUIVALENT export. |
| AW-11 / AW-12 | Fresh export; replay in another CLI process against separately selected execution; altered bundle rejected. |
| AW-13 | Forced 1 ms solver limit yields UNKNOWN twice under a one-retry policy. Limits are not silently raised; a changed budget requires a new declared request. |
| AW-14 | Genuine imported snapshot revalidated against a changed beacon implementation returns STALE and blocks build. |
| AW-15 | STOP_AUTHORIZATION ends the plan before later export or any submission capability. |
| AW-N01 | Malformed service output fails UNKNOWN, with no downstream export. |
| AW-N02 | Unknown schema/invalid JSON fail INVALID_INPUT. |
| AW-N03 | Hash-inconsistent imported data is rejected by the frozen M2 input contract as INVALID_INPUT before a workflow can emit STALE. No frozen validator was weakened to satisfy the proposed label. |
| AW-N04 | Stateful import cannot enter stateless composition/proof. |
| AW-N05 | Tool/iteration/RPC limits produce BUDGET_EXHAUSTED with a partial log; no infinite loop. |

All eight proposed operations are supported. The eight proposed status classes are
represented, with STOP_AUTHORIZATION replacing the proposed spelling
STOPPED_FOR_AUTHORIZATION and explicit CANCELLED/INVALID_INPUT outcomes added in the
new profile. PREPARED/RUNNING are internal lifecycle states. Logs are an ordered JSON
array in the JSON-first receipt, rather than a separate streaming JSONL service.
These are versioned production decisions, not edits to the independent specification.
No frozen M1/M2/M3/library/debugging schema changed.

## Validation and development failures

Final production CI: [Windows/Linux run 44637097034](https://github.com/Technique-S/Flip/actions/runs/44637097034),
bound to `0ba49cdb2aa804f8ecd9aca066b5433a747e169a`. Downloaded JUnit and acceptance
artifacts, rather than only the workflow badge, determine the counts in the validation
record. The 601 inherited Python tests and 23 Chromium journeys remain present.
**Both platforms passed all 648 Python tests (601 inherited + 47 new) and 23 Chromium
tests, with zero Python failures/errors/skips. Implementation verdict: PASS for
bounded handoff and independent review; this is not merge approval.**

Local final focused workflow tests: **47 passed**. Local Chromium: **23 passed**;
frontend lint/TypeScript/build and Ruff check/format passed. All seven schema profiles,
six Node canonical vectors, independent fixture verifiers and external M1/M3 CLI/ASGI
smokes passed. The shipped CLI correction→export workflow completed successfully.
The reusable skill passed the bundled validator using PyYAML 6.0.3 in ignored scratch;
no application dependency or lockfile changed. Standalone clean custody/credentials
and exact archived bytes are recorded in the validation JSON.

An earlier development full local run collected 646 tests: **645 passed, one inherited
F03-PERF-001 failure**. Its 120-second scratch-regeneration subprocess timeout remains
unchanged. It started at `5fb9157`; the admission-deadline patch was committed while
that development run was active, so it is explicitly not final immutable-checkout
acceptance evidence. Final isolated CI and the subsequent focused run test `0ba49cd`.
The same local run's Git custody test passed in 130.377 seconds. Host runtime issues
are not claimed fixed, and a passing hosted run does not establish every local
layout's latency.

Initial development failures exposed the Windows venv launcher's extra process,
duplicate proposal classification arguments, malformed-output handling and an
inappropriate library double for a stateful dependency. These were corrected in
production/new tests without modifying archived sources or inherited assertions.
The first [CI run 44636475565](https://github.com/Technique-S/Flip/actions/runs/44636475565)
had 645 passes and one new cancellation-test failure; fail-fast cancelled Windows.
Its double recorded requests after an artificial delay, conflating server-side
completion of an already received read with a new request. The corrected test records
arrival before delay and retains the assertion that no new read arrives after
cancellation. An already delivered read cannot be withdrawn from the remote server;
its late response is discarded. Admission timing and late-revision rejection also
have focused regressions. No timeout was increased, failure skipped or proof weakened.

## Scope, remaining limits and review gate

This is bounded local/offline, stateless NAND/REF orchestration. Results remain
historical and relative to selected references, declared intent, pinned dependency
bytes and supported semantics. Single-RPC observations are not malicious-provider
resistance or permanent CURRENT authority. Live RPC was not used for mandatory tests
or claimed as new observation evidence. Receipt/native-engine hashes are platform
specific; timeouts and live observations need not reproduce identically.

No durable server sessions, persistent undo store, browser workflow designer,
natural-language synthesis, public solver deployment, wallet, signer, payment,
publication or spending implementation is included. Human usability/accessibility
sessions and independent review of the production workflow delta remain unperformed.
F03-PERF-001 (archival runtime margin) and D-RUNNER-001 (local Git/process runtime)
remain tracked in the accepted library/debugger follow-ups, with original assertions
and limits intact.

Changed areas: new `agent_models.py`, `agent_workflow.py`, `agent_operations.py`,
`agent_worker.py`, `agent_schema_export.py`, production corpus/security tests,
CLI/API adapters, the bounded Windows Job helper option, new schema/example/guide/
skill, example builder, custody guard, archive attributes, narrow Ruff exclusions,
CI schema check and README entry. The source corpus is integrated without byte edits.
No existing production test or dependency lock was changed.

Reproduce with `uv run --frozen pytest -q`, `npm test --prefix apps/web`, the seven
schema commands in CI, `node docs/schema/check-canonical.mjs`, and
`uv run --frozen python scripts/check_m1_repository.py --require-clean`.
Keep the branch unmerged for independent production review. This handoff grants no
release, publication or transaction authority. Stop after delivery.
