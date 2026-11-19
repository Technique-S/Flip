# Connection diagnostics 1.0

This additive `m45-debugging-1.0.0` contract leaves the accepted M1/M2/M3 and library
schemas unchanged. Shape validation never establishes proof or chain freshness.

`flip debug --request request.json [--out result.json]` and
`POST /api/v1/debug` execute the same shared Python engine. HTTP execution uses the
existing `FLIP_LOCAL_SOLVER=1`, loopback-only and two-slot solver boundary. Input is
limited to 1 MiB. The API rejects query parameters and unknown fields/versions.

See [the request example](examples/swapped-prior.request.json) and
[its original execution project](examples/swapped-prior.execution.json). Open the
execution project in Flip, run a comparison, then select **Inspect connection paths**.
The example is historical, not a live observation.

## Evidence and classification

| Classification | Meaning |
|---|---|
| VERIFIED_DIFFERENCE | M3's SAT witness has been independently replayed again by the trusted evaluator. |
| RELEVANT_CONNECTION | A connection in a structural backward cone rooted at a differing mapped output. This is a relevance label, never a defective-wire claim. |
| CANDIDATE_ACTION | A proposed revision of declared prior numeric mappings, not a verified correction. |
| VERIFIED_CORRECTION | A new structural validation, identity/hash/closure replay and exact stateless comparison returned EQUIVALENT for the separate revision. |
| UNKNOWN | Stale/unverified closure, unsupported structure, a bound or deadline, failed witness replay or inconclusive comparison. No connections/actions/correction claim survive diagnostic failure. |
| NO_FAULT_ATTRIBUTION | EQUIVALENT designs receive no suspect connections or correction actions. |

`attribution` separately distinguishes ambiguous multiple causes, a single unverified
candidate under a declared prior reference, no fault attribution, and unknown. Even
one declared edit is not proof of a uniquely defective connection. `uniqueFaultClaim`
is always false. Aliases, labels, and metadata are never intent or authorization.

## Deterministic trace

The existing compiler validates and builds both designs using M2 snapshot resolution.
The trusted comparison supplies a replayed witness. Differing reference-output bits
map through the explicit output bijection to candidate pins; reference inputs retain
their explicit ordering. The tracer follows actual compiled signal producers through
NAND pins, individual REF outputs, child input boundaries, and parent source mappings.
An unused REF output's computation is excluded. Constants terminate traversal.

Connections are sorted by `(side, connectionRef)` and identified by side plus a stable
`top/ref[index]/element[index].in[pin]` path. Repeated instances retain distinct paths
even when the resolver shares an immutable child circuit. Each edge binds its local
netlist hash; nested scopes include the exact circuit identity. REF output edges run
from the child's output signal to the parent's REF output pin, with separate source
path/hash/identity fields. Dataflow is not reversed by backward traversal. Root recipe components
include instance IDs and original numeric `projectPin` mappings. Compiler-generated
copy/inverter records remain explicitly generated, not invented user components.
`projectPin` describes the recipe before the compiler's accepted NAND canonicalization;
`sourceSignal` describes the actual compiled connection.

Both manifest hashes, exact request/project hashes, comparison engine identity and
diagnostic engine source hash are bound in the result. `semanticHash` covers the entire
result except itself. Comparison wall-clock resources and `verifiedAt` are excluded
from diagnostics so CLI/API output is canonically identical on the same engine/runtime.
Runtime/native engine identity may legitimately differ across platforms.

## Proposals and explicit replay

A proposal requires a declared trusted local reference (`referenceCandidate`), matching
topological instance IDs, kinds and source bindings. It restores that prior design's
input/output mappings in a separate validated request and provides a numeric before/after
diff. Different component/source topology, undeclared intent or absent prior mappings
produce no automatic correction proposal. Relevant paths still support manual inspection.

Set `operation="verify-correction"` and the returned `actionId` to test a proposal.
The engine reconstructs the action from the original request; it accepts no caller-supplied
replacement imports, oracle, permission or report. The action ID binds original and
revised request hashes. A new comparison must return EQUIVALENT before the correction
is classified VERIFIED_CORRECTION. A failed/unknown check cannot grant that label.
Neither diagnose nor verify-correction mutates the input or writes a project.

The web interface requires selection and an explicit local apply action. It retains the
original execution in workspace state, allows rerun and revert across navigation, and
blocks reverting over subsequent unrelated edits. Undo is session memory, not a persistent
version store; save the original project/download the diagnostic before refreshing.
The visible diff is limited to 50 edits; larger proposals are available as JSON and
require an explicit separate project file. Trace rendering is paginated at 50 connections.

## Bounds and freshness

Diagnostics default to 64 sources, 128 circuit records (maximum 256), 250,000 circuit
bytes (maximum 1,000,000), and 5,000 combined expanded gates (maximum 10,000). Existing
M3 per-design gate, REF resolution, source validation and isolated solver hard limits
remain active. Trace limits default to 4,096 visited nodes, 4,096 connections, 20,000
indexed signals and depth 32; maxima are 8,192 / 8,192 / 100,000 / 64 respectively.
Indexing and traversal check a 1,000 ms cooperative deadline (maximum 5,000 ms).
An operation deadline of 15,000 ms (maximum 30,000 ms) is checked between bounded core
phases; it does not replace the existing isolated worker's hard solver deadline.

Every operation replays pinned identities, netlist hashes and dependency closure through
the existing resolver. Cached CURRENT flags grant no freshness: results explicitly state
`PINNED_SNAPSHOT_ONLY_NOT_LIVE`. Stale/unverified imports fail closed. A verified correction
is scoped to the exact selected reference over historical snapshots; it is not a claim
about current chain implementations or intended application correctness. Live read-only
revalidation remains the existing separate workflow; no diagnostic operation contacts RPC.

CLI exits: 0 for no-fault equivalence or a verified correction; 1 for a diagnosed
difference; 2 for UNKNOWN or an unverified correction; 3 for invalid requests/files.
Ctrl-C retains the existing explicit resource-abort result. Output files use the existing
atomic writer and are written only when requested.

No LLM assigns causes or verdicts. No wallet, signer, transaction or spending authority exists.
