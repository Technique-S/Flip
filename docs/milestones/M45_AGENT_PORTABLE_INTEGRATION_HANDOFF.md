# M4.5-1I — Portable project / agent workflow integration handoff

Status: production integration delivered for **independent delta review**. Do not merge
until that review passes. No main merge is authorized by this handoff.

## Baselines and history

| Role | Exact revision |
|---|---|
| Accepted main after PR #8 | `b9042cc66775405b5d0ca5a2be35197dabad0527` |
| Reviewed portable implementation | `136b1115ee0f5ffe0a5583d68c474641fdce1ca1` |
| Portable independent review, CONDITIONAL PASS | `8daacf7af2a1cfc17d83a33f7841d1088807ec82` |
| Accepted agent implementation | `d2638d057b6236286480891d6fdd7dfb0402bc5a` |
| Original portability research | `2f3d6263edf4e62ad4e94718c99f6c1a79e350a1` |

Fetched refs matched all requested baselines. The dedicated branch is
`codex/flip-m45-agent-portable-integration`. Reviewed portable implementation, its complete
independent review, and original research are integrated through merge commits retaining
all original history. Accepted controller, raw proof fixtures and all frozen schemas remain.
The original review is unchanged, including its low-severity browser-flakiness finding;
this handoff does not rewrite CONDITIONAL PASS into an independent approval of the adapter.

## Conflicts and material delta

Manual union resolutions retained both sides in `.gitattributes`, CI, CLI and API:
all workflow and portable commands/routes/validators/handlers/tests remain available.
Both sets of archive attributes and schema/corpus/parity gates remain enabled.
Independent research/review archives are pinned by history, exact Git/checkout bytes,
manifest coverage and hashes. Only their exact immutable harnesses are excluded from
formatting; there is no general binary/large-file/credential exemption.

Material production changes requiring review:

* Additive `agent_portable_adapter.py` and `m45-agent-portable-1.0.0` request/result/plan
  schemas, with exact package/revision/request pins and one trusted controller invocation.
* New `flip agent-portable` preparation/execution and bounded loopback API routes,
  plus frontend aliases. The two preexisting dispatchers remain supported.
* React workflow controls, explicit verified-revision opening/download, separate receipts
  and evidence, cancellation/late-result invalidation, keyboard focus recovery and
  historical/relative-proof wording.

The accepted controller/models/worker/operations and the existing compiler, evaluator,
SAT implementation, evidence consumer, canonical serializer and portable validator are
unchanged. No engine is duplicated in JavaScript. Full contract and hash/budget decisions:
[adapter contract](../schema/m45-agent-portable/README.md).

## Commit boundaries

Original package/revision and artifact files are preserved. Explicit allowed apply runs
trusted verification and requires exact original bindings. Every changed revision needs
post-tests and a new trusted export. Named vector matches never become universal proofs.
Ordered successful-apply records link raw before/after request hashes and the original
parent head; new evidence references bind only the revised head. Previous evidence remains
in the original package/files. Revision/task/receipt checksums authenticate no author and
grant no permission. Missing evidence remains missing, while supplied evidence is replayed
by the existing trusted consumer. Wrong identities and changed implementations fail closed.

One shared resource budget accounts for injected test/evidence operations. Admission and
commit deadlines cannot reset the canonical task budget. Cancellation, resource exhaustion,
UNKNOWN/STALE, failed verification, and terminal authorization stops cannot publish a new
package. The browser never selects a late result or replaces the open project implicitly.
CLI output exclusively creates a new path. Concurrent calls are stateless sibling branches,
not a global linear history or author registry.

PUBLISH/DEPLOY purpose stops before queued operations at STOP_AUTHORIZATION. No signer,
wallet, transaction construction, spending, broadcast, payment, publication or public
solver hosting is present. M4.5-0 transaction architecture remains separate.

## Validation and reliability

Validation is ongoing; final exact SHA, counts, failures and Windows/Linux CI are reported
with the draft PR. Current focused checks cover the complete 15-stage combined journey,
raw/sparse hash identity, before/after revisions, named vectors, replayed witnesses,
connection diagnostics, separate candidate/verify/apply, independently replayable evidence,
foreign/stale/forged inputs, broken ancestry, missing closure, wrong engine, cancellation
before commit, deadlines, output budgets, repeated/concurrent operations, legacy dispatch,
CLI/API parity and lossy downgrade notices. Browser coverage exercises mismatch stop,
explicit correction continuation, separate exports, original preservation, CLI replay,
manual opening, session restore, publication stop, late-response cancellation, mobile and axe.

Track reliability separately:

* Inherited archival test: original 120-second deadline and historical hash/regeneration
  assertions are unchanged. The accepted agent acceptance diagnostic identified task E
  benchmark generation as the local bottleneck (216.707 / 218.844 seconds total), while
  hosted Windows/Linux passed the unchanged test. No performance or proof claim is inferred
  from archival measurements. See the accepted PR #8 record for the original investigation.
* Inherited debugger Chromium test: original review failed the 5-second UI locator while
  bounded native verify-correction was still in progress. The revised test awaits the
  exact verification HTTP response, checks the actual VERIFIED_CORRECTION/EQUIVALENT
  response, then checks UI rendering with the unchanged locator timeout. It still requires
  two fresh verification requests and no restored proof/undo authority after refresh.
  No sleeps, global retries or increased timeout were added. This test-only delta also
  requires review; full-suite Windows/Linux results determine current reliability.

Required checks: full Python/Chromium suites, nine schema profiles, original 12 portability
cases, 27+10 independent agent checks, both canonical parity gates plus adapter plan parity,
Ruff/frontend lint/build, custody/credentials, external smokes and Windows/Linux CI.
Raw independent reports/results must never be overwritten by new observations.

## Reproduce and review

Use the locked environment (`uv sync --locked`, `npm ci --prefix apps/web`). Run
`uv run --frozen pytest -q`, `npm run lint --prefix apps/web`,
`npm run build --prefix apps/web`, `npm test --prefix apps/web`, all schema commands
in CI, three Node canonical scripts and the custody/credential guard with --require-clean.
New tests: `packages/flip-core/tests/test_m45_agent_portable.py` and
`apps/web/tests/agent-portable.spec.ts`. The bounded API is opt-in/loopback like the
accepted controller. Existing Playwright port environment variables isolate worktrees.

Independent reviewer priorities: raw versus normalized hash boundaries; source/reference
substitution; explicit apply-only state changes; complete post-test/export gating; old/new
artifact separation and missing/forged evidence; cancellation around revision publication;
resource accounting without request-hash timing noise; terminal publication stops;
parallel/repeated requests and exclusive file output; legacy route union; untouched frozen
contracts and raw review history. No review verdict for this new production delta is claimed.
