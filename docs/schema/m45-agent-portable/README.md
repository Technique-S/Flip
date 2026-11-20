# Portable packages with bounded agent workflows

Profile: `m45-agent-portable-1.0.0`. This additive adapter keeps Portable 1.1 and the
accepted `m45-agent-workflow-1.0.0` controller unchanged. It introduces no evaluator,
SAT implementation, transaction operation, author identity or permission grant.

## Operations

| Interface | Preparation (no proof) | Bounded execution |
|---|---|---|
| CLI | `flip agent-portable --prepare --request preparation.json` | `flip agent-portable --request request.json --out new-result.json` |
| API | `POST /api/agent/v1/portable/prepare` | `POST /api/agent/v1/portable` |
| Browser alias | `/api/v1/agent-portable/prepare` | `/api/v1/agent-portable` |

Preparation accepts `{package, action}` with optional version/kind defaults, where action
is `inspect`, `correct`, `verify-edit`, or `publish`. `verify-edit` also requires an explicit
`draftExecutionRequest`; only its candidate wiring may differ. Preparation returns
`{request, trust: "UNVERIFIED_PLAN_AND_IDENTITIES_ONLY"}`. Execute the inner `request`
object, not the preparation response wrapper. Preparation hashes and builds a plan; it
does not verify a correction or grant permission.

Execution is a strict `AGENT_PORTABLE_REQUEST`: `package`, `expectedPackageHash`,
`expectedRevisionHash`, `expectedExecutionRequestHash`, `workflow`, and explicit
`createRevision`. The optional flags `runNamedTests` (default true),
`continueOnTestMismatch` and `continueOnEvidenceDifference` (default false),
`evidenceArtifacts` (digest-to-artifact mapping), and `purpose` (`LOCAL`, `PUBLISH`,
`DEPLOY`) have only the documented local meanings. Unknown fields reject.

The embedded `workflow` uses the existing typed controller request with
`executionRequest: null`; the adapter supplies only the selected package's exact core.
Execution steps may build, test, compare, inspect, propose/verify/apply a correction,
export/replay evidence, revalidate, or stop authorization. Sample/import/discover and
foreign build/revalidation sources cannot replace the selected project in this adapter.
They remain available through the unchanged standalone controller. Step IDs beginning
`pp_` are reserved for explicit adapter-generated tests, replay and commit gates.

## Identities and canonical parity

All digests use existing flip-json-v1 SHA-256. `expectedPackageHash` hashes the exact
supplied package object, `expectedRevisionHash` pins its head, and
`expectedExecutionRequestHash` pins the package's raw request transport hash.
The controller independently uses its frozen normalized execution-request hash. Sparse
legacy requests retain their original representation; a successful edit changes only
`project.candidate`, never defaults, source identities, imports, reference, intent or limits.

`requestHash` hashes the normalized adapter request. `adapterHash` hashes the current
adapter and portable-validator source digests; the receipt retains the unchanged trusted
controller/engine identity. `resultHash` covers the complete result except itself.
`reproductionHash` covers requestHash, adapterHash, the controller's semantic
reproductionHash, status, originalRevisionHash, finalExecutionHash and ordered accepted
edits. It excludes incidental new evidence timestamps/digests by using the existing
semantic receipt hash. It is a checksum, never author or proof authority.

A new revision hash still covers its actual content-addressed evidence references.
Separate fresh proof exports can therefore produce different artifact/revision identities
while retaining identical semantic reproduction hashes. Revision hashes are deterministic
for the actual recorded artifacts and edits, not a promise that independent clock-stamped
exports have identical bytes. Python/Node goldens bind preparation and all three input pins.

## One controller and one resource budget

The adapter validates the package, compiles its complete closure and checks stale flags.
It preserves the original and expands the plan into one existing controller invocation:
provided referenced evidence is replayed, named test sets run before the declared steps,
and requested revision creation adds post-edit named tests plus a fresh trusted export.
Missing evidence is reported MISSING_EVIDENCE, never REPLAYED or verified. Provided corrupt,
foreign, engine-incompatible or reproduction-incompatible evidence fails before commit.
Neither artifact URLs nor reproduce strings are fetched or executed.

DIFFERENT is a completed behavioral result. Default test/evidence differences stop the
plan. The two continuation flags explicitly allow diagnostics/correction after those
respective differences; they do not authorize retries or relax UNKNOWN/stale handling.
Each named test preserves its name/intent/coverage/vectors in the package; receipt IDs
`pp_beforeN`/`pp_afterN` map to package.tests[N]. Vector matches remain VECTORS_MATCH,
not universal equivalence.

Input is limited to 1 MiB. Expanded plans must fit 64 steps, and named-vector aggregate
work across both passes is limited to 2,000,000 units using the greatest declared
candidate/reference cost. Existing row/width/coverage limits remain enforced. Generated
steps consume the original iteration, tool, RPC, operation/output and receipt budgets;
no budget resets or silent raises occur. The total deadline includes adapter admission
and revision preparation and is enforced through cancellation and final boundary checks,
without injecting measured milliseconds into the canonical controller request.

Output is bounded by the selected workflow receipt budget. On overflow no revision is
returned; large receipt/diagnostic data may be omitted with an explicit resource error,
while the complete original package remains. An input budget too small to retain the
original is rejected before execution. API execution uses the existing two-slot admission,
loopback and FLIP_LOCAL_SOLVER opt-in. Disconnect and CLI SIGINT/--cancel-file stop work.

## Explicit revision commit and evidence

Only the existing controller's explicit `apply` can change candidate wiring. It requires
its process-local proposal and a fresh VERIFIED_CORRECTION; apply compares again.
The adapter then requires every post-test and the final trusted export to complete for
the final execution identity. Early stopOn or partial progress cannot bypass this gate.
The export reruns the existing comparator; named vectors do not substitute for it.

Successful applies produce oldest-first edit records with raw before/after hashes and
step/action identities. Metadata-only verified revisions have equal before/after hashes.
The new package links the original head and retains its ancestor records and named tests.
Its agentTaskRef is the actual normalized controller-task digest, non-authoritative metadata.
Fresh references point only to genuine returned FLIP_EVIDENCE exports bound to the new
request. Prior references remain intact in `originalPackage` and the caller's original
artifact files; they are not relabeled as proof for a changed head.

`AGENT_PORTABLE_RESULT` returns `originalPackage`, `revisedPackage` (null on no commit),
`revisionCreated`, the unmodified controller `receipt` separately, new `evidenceArtifacts`,
input-evidence availability/replay status, hashes and errors. Failure/cancellation may
leave an uncommitted candidate in the diagnostic receipt; it never selects a revised
package. Cancellation is checked before and after hashing the proposed package and at
the response boundary. STOP_AUTHORIZATION never produces a revision or later operation.

The service is stateless: simultaneous requests can create explicit sibling revisions
from the same pinned parent. There is no global revision registry or author namespace.
Callers must select their next trusted head; the CLI refuses to overwrite output files.
Browser output stays separate until the user chooses Open verified revision; saved files
and session state are not automatically replaced by a receipt or a late response.

## Authorization and freshness

PUBLISH or DEPLOY purpose prepends terminal STOP_AUTHORIZATION before all queued work.
It creates no approval, transaction, signer, wallet or spending operation. The accepted
controller's stop behavior and explicit stop_authorization step remain unchanged.
Project metadata, checksums, prompts, task digests and successful tests cannot override it.
The proposed transaction-authorization architecture remains excluded.

Package validation establishes local integrity only. Trusted replay always recomputes.
Verification labels remain historical and relative to selected references; metadata cannot
promote HISTORICAL/STALE into CURRENT. Explicit revalidation can detect changed chain
implementations and terminate STALE without committing a revision. Old native-engine
bundles can fail identity checks after a legitimate engine change; no stored EQUIVALENT
claim is promoted to compensate. No live RPC is required for deterministic tests.

Regenerate/check: `python -m flip_core.agent_portable_schema_export --out
 docs/schema/m45-agent-portable/1.0.0 [--check]`; parity:
`node docs/schema/m45-agent-portable/check-canonical.mjs`.
