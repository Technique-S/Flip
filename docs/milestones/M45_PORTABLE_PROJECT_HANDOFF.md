# M4.5 portable project production handoff

Branch: `codex/flip-m45-portable-project`. Base:
`bba6f3d301b08c0dcbbfd0b363b99a15179414db`. No merge into main.

## Implementation and provenance

The additive `flip-portable-project-1.1.0` package embeds the exact existing M3
execution-request object and hash, named tests, explicit empty-test marker,
content-addressed FLIP_EVIDENCE references, ordered revision ancestry, provenance and
optional non-authoritative agent task digest. It introduces no dependencies or frozen
schema changes. The canonical serializer, compiler, evaluator, solver, evidence consumer
and their engine-identity source bytes remain unchanged.

Read the [contract and hash decisions](../schema/m45-portable-project/README.md) for exact
field types, preimages, limits and operations. Shape checks are local data integrity only;
trusted evidence replay remains a separate invocation of the existing engine.

Independent source: `opencode/flip-m45-portable-project-evidence`, exact commit
`2f3d6263edf4e62ad4e94718c99f6c1a79e350a1`. Its audit, acceptance matrix, proposal,
handoff, requests and raw observations are copied without content changes under
`docs/evidence/m45-portable-project/`. Its original executable harness is preserved
byte-for-byte in that directory's `harness/run_portability_cases.py.txt`. The production
runner checks that snapshot's digest before execution and redirects new observations
into ignored scratch space. The independent archived observations remain historical.
The existing fixture namespace restriction and inherited test files are preserved;
new portable regressions live in their own test module.

## Interfaces and migration

* Core: `packages/flip-core/src/flip_core/portable.py`, additive schema exporter and
  generated package/request schemas plus Python/Node goldens.
* CLI: `flip portable --request operation.json [--out new-revision.json]` implements
  wrap, validate, open, test, replay-evidence and explicit downgrade. Existing executable
  CLI commands accept portable or legacy projects. Portable output exclusively creates
  new files; an existing output path is an error, preserving previous revisions.
* HTTP: bounded `POST /api/v1/portable`, shared core semantics, existing concurrency
  limit. Replay inherits loopback and solver-opt-in restrictions. HTTP compose/compare
  accept either format; existing product API bodies consume the extracted request.
* React: existing Sources file picker opens either version. Evidence adds complete
  package download, test/reference import, inspection, named-vector execution, revision
  inspection, referenced-file replay, missing-evidence checks and acknowledged legacy
  conversion. The existing legacy Save project action remains available. Session restore
  retains the saved package alongside the executable draft. New work is styled with
  Flip's existing controls, semantic sections, visible focus and mobile wrapping.

Legacy wrapping creates a genesis revision and explicit no-declared-tests marker unless
supplied tests exist. It invents no tests/evidence/freshness. Downgrade requires
`allowLossy: true` and discloses tests, noDeclaredTests, evidenceRefs, revision, ancestors,
provenance and agentTaskRef as discarded fields. Future versions reject. Old execution
and canonical evidence-verification semantics remain intact. Portable execution blocks
STALE dependencies; historical replay can retain a stale observation or fail the frozen
consumer's exact binding checks. A changed request requires explicit removal/replacement
of old evidence references before a new revision can be saved.

## Acceptance and reproducible checks

Run with the locked Python 3.14.6/uv environment and the existing frontend lockfile:

```text
uv sync --locked
npm ci --prefix apps/web
uv run --frozen pytest -q --junitxml=.test-tmp/portable-python.xml -o junit_family=legacy
uv run --frozen ruff check .
uv run --frozen ruff format --check .
npm run lint --prefix apps/web
npm run build --prefix apps/web
npm test --prefix apps/web
uv run --frozen python scripts/check_m45_portability.py
uv run --frozen python -m flip_core.portable_schema_export --out docs/schema/m45-portable-project/1.1.0 --check
node docs/schema/m45-portable-project/check-canonical.mjs
uv run --frozen python scripts/check_m1_repository.py --require-clean
```

All existing frozen schema exporters and canonical parity gates remain in CI; the new
portable drift/parity and independent 12-case runner are added to both Windows/Linux
jobs. Existing custody/credential gates remain enabled. No live RPC is required:
changed-chain behavior uses a loopback synthetic double. Browser test ports optionally
use `FLIP_TEST_APP_PORT` and `FLIP_TEST_RPC_PORT` to avoid other active worktrees.

The original independent P01–P12 cases execute unchanged against production with scratch
outputs and freshly generated native-engine evidence. Additional regressions cover named
vectors and expected coverage, empty markers, evidence digests/engine/request identities,
missing artifacts, substituted/corrupt claims, cross-project reuse, full revision chain
validation, ordered multiple-edit logs, pinned parents, invalid future schemas, lossy
warnings, stale dependencies, exact 81-byte half-adder reproduction and legacy CLI/API
parity. Chromium covers a full portable import/test/save/refresh/downgrade journey, both
viewports, axe, and invalid-version recovery without replacing the active project.
Actual final counts and remote CI status are reported with the final commit rather than
inferred from this checklist.

## Agent workflow adapter: deferred shared-file changes

Inspected `codex/flip-m45-agent-workflow` independently; no agent production controller,
protocol or worker file is merged or modified here. Its `WorkflowRequest.executionRequest`
and `WorkflowResult.executionRequest` use the frozen VerificationRequest.

Adapter contract after independent acceptance:

1. Caller selects a package and trusted head. Call portable `open` with
   `expectedRevisionHash`; use its embedded execution request as the controller's
   existing `WorkflowRequest.executionRequest`. Preserve `previous` package outside the
   controller. Package instructions, intent, provenance, tests and `agentTaskRef` confer
   no permissions.
2. Named tests remain an explicit operation. Build existing VectorRequests by combining
   the extracted request with one set's `vectors`; do not reinterpret coverage as SAT
   proof. Workflow budgets and allowed operation lists remain authoritative.
3. Consume the controller result as data. Do not infer acceptance from COMPLETE or a
   stored VERIFIED_CORRECTION. Revalidate/recompile a returned request; accepted local
   changes become portable `wrap` using the selected previous package and pinned parent.
   Add the workflow task envelope's canonical digest as `agentTaskRef` only. Explicitly
   replace/remove old evidence references if the execution request changed; attach new
   evidence only using its actual artifact digest and current request identity.
4. Record accepted edits in order. Separate request hashes and workflow receipt hashes
   retain their own preimages. Revision hashes do not authenticate the controller or
   author. Preserve previous package files and the original workflow receipt.
5. A publication request still terminates at **STOP_AUTHORIZATION**. The adapter cannot
   convert a task reference, successful comparison or revision into onchain authority.

Exact follow-up ownership: Codex owns a new
`packages/flip-core/src/flip_core/agent_portable_adapter.py` (suggested additive module),
with any dispatcher hooks in `agent_operations.py` / `agent_workflow.py` deferred until
that branch's acceptance. Controller models in `agent_models.py` remain frozen unless
an independently accepted version is introduced. The CLI/API dispatcher files are owned
by Codex and will need ordinary conflict resolution when both feature branches merge;
this branch adds only portable dispatch and does not resolve by dropping workflow routes.
Frontend adapter work should stay in `Portable.tsx`/a new agent-specific component.

Required follow-up tests: package-to-controller request hash parity; named tests within
workflow budgets; accepted edit-to-new-revision binding and ordered logs; unchanged
original package on rejection/cancellation/UNKNOWN; stale/missing evidence; foreign
receipt/task/project substitution; export/replay with current engine; terminal
STOP_AUTHORIZATION with no retry, signer, broadcast or resumed grant. Controller receipts
and package metadata never become proof authority.

## Remaining limitations

Evidence files remain separate content-addressed artifacts; no remote resolver or ZIP
fetch is introduced. Compatible native engine bytes/platform are required for trusted
replay; mismatches fail closed. Session storage is best-effort and browser download
placement is user-controlled. Previous revision records contain hashes/descriptions,
not complete historical content: retain old package files for restoration. There is
no global project namespace, author authentication, remote revision registry, chain
freshness guarantee or public solver hosting. Requests including ancestry/artifacts must
fit 1 MiB; history never truncates silently. Live upgrades and human usability studies
remain outside deterministic acceptance. No transaction signing, broadcasting, payments,
publication, public hosting or agent-controller integration is implemented here.
