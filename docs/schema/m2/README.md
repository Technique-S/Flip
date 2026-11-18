# M2-A importer interfaces and contract decision

These are additive contracts, each versioned `1.0.0` in its own schema namespace.
The six M1 schemas and canonical JSON profile remain byte-identical. Generate/check
with `python -m flip_core.import_schema_export --out docs/schema/m2/1.0.0 [--check]`.
JSON Schema validates shape; the shared Pydantic/service boundary also binds raw
netlist bytes, manifest hashes, complete closure and observed counts.

## Shared service

`ImportService(RpcSettings(...), ImportBudget(...)).import_circuit(identity,
block_number=None)` returns `ImportResult`. Its `manifest` is the frozen v1 Manifest,
with exact preserved netlists in `circuits`, a canonical `manifestHash`, explicit
`NUMBER_WITH_HEADER_RECHECK` pinning and `SINGLE_RPC_OBSERVATION` trust.
`revalidate(manifest)` imports the entire closure again at a fresh head and checks
the old block's canonical identity. It returns `RevalidationResult` with both the
old digest and a new observed artifact, plus deterministic change categories.
It never overwrites the supplied historical manifest.

M2 validates real metadata: root/request identity, per-REF chain/factory membership,
existence, I/O arity, exact original bytes, structural references, independently
summed expanded gate/state counts and complete environment identities. Counts
are not trusted merely because `circuitInfo` returned them.

Manifest and raw-byte digests are SHA-256, including code-byte digests (matching
the audit convention); they are not Ethereum Keccak code hashes. The stored
factory implementation slot value is validated and decoded, and processor beacon
storage must match the factory beacon. All code addresses must have nonempty code.
The declared TAP-02 semantics version is a modeling assumption, not a new proof
that an upgraded implementation obeys that semantics.

## Freshness and cache

Only a successful fresh-head session with chain ID 196 checked before/after,
all state calls pinned to one block number, and an unchanged block hash at the end
can return CURRENT. This means observed at `checkedBlock`, not permanently current.
Number-pinning plus header rechecks detects reorgs but does not defeat a dishonest
RPC operator or provide atomic EIP-1898/hash-pinned reads. It fails closed on a
changed block or inconsistent data. No hash-pinning claim is made.

An explicit block number always yields HISTORICAL, even if it happens to be the
head. Cache reads always yield HISTORICAL or known STALE, never CURRENT. The
in-memory cache stores serialized copies, keyed by the full canonical manifest
digest (binding chain, content, closure, environment and block), with 16 entries /
8 MiB maximum. It is public-snapshot caching, not user/project persistence.
Revalidation invalidates known changed entries while retaining their old evidence.
On RPC failure there is no automatic cache fallback relabeled as fresh.

## API compatibility

- `POST /api/v1/import` and `/api/v1/inspect`: frozen v1 CircuitIdentity JSON.
  Optional `?blockNumber=<decimal string>` requests a historical block.
- `POST /api/v1/revalidate`: frozen v1 Manifest JSON; no block override.
- HTTP 200 contains only import/revalidation observations, never a proof verdict.
  Invalid schema/ABI/netlist is 422; RPC failure 503; budget/concurrency breach 429;
  changed pinned block 409; request body >1 MiB 413. Errors use v1 ErrorEnvelope.
- To preserve M1 compatibility, unversioned legacy object bodies still receive
  HTTP 501 / NOT_IMPLEMENTED. They cannot start a live import. Versioned malformed
  bodies receive explicit validation errors. No audit-JSON-to-v1 adapter is implied.
- Endpoint/timeout/retries are deployment configuration (`FLIP_RPC_URL`,
  `FLIP_RPC_TIMEOUT_MS`, `FLIP_RPC_RETRIES`), never an arbitrary RPC URL in a request.
  At most two import/revalidation jobs run concurrently; an exhausted slot fails
  immediately. Cancellation does not kill a running thread; its job deadline and
  I/O budgets still bound it. Public hosting/rate-limit hardening is a later gate.
- `/healthz` retains its M1 liveness-only label for compatibility; it is not a
  capability/version claim. The OpenAPI import request/response schemas describe M2.

## CLI

```text
flip inspect --processor 0x839bdd6fa7a66416a609a735e11de5411b98574e --id 1
flip import --identity identity.json --block-number 76056306 --out imported.json
flip revalidate --manifest manifest.json
```

Flags include `--rpc-url`, `--timeout-ms` (1..30000), `--retries` (0..2),
`--gate-cap` (default 2500, <=5000), `--max-depth` (default/max 64).
`--out` atomically replaces a complete validated JSON artifact. Stdout remains one
canonical JSON object. Existing exits remain: 0 completed import/check, 2 budget
inconclusive, 3 invalid input, 4 infrastructure, 6 unimplemented, 7 stale/changed.
Bare legacy import/inspect/revalidate commands remain exit 6. Exit 0 for import
does not assert equivalence, intended correctness or publication.

## Bounded decoding and RPC

Defaults / hard maximums: per netlist 250,000 / 1,000,000 bytes, total closure
1,000,000 bytes, 5,000 local/total records, 2,500 / 5,000 expanded gates, depth 64,
128 / 1,251 unique circuits, 256 / 8,192 RPC attempts, 60 / 120 seconds per job.
These additional decoder/transport bounds are conservative design limits, not
extensions of the audited solver maxima. State <=2^24 and signals <=2^24 retain
TAP-02 protocol bounds. No state bit arrays or expanded circuit trees are allocated.
REF targets are memoized; gate/state totals count repeated uses, not just unique
nodes. Cached subgraph heights still count against deeper paths.

Transport accepts only five read methods and eight exact read selectors. Request
attempts, retries, timeouts, response bytes and wall deadline are bounded; errors
do not become successful observations. Redirects and compressed responses are
rejected, response IDs/envelopes and ABI offsets/word widths/padding are validated.
Normal state reads use the pinned number, not `latest`. Chain identity is checked
again before returning. There is no signer, arbitrary RPC relay, transaction
constructor, evaluator, composer or solver.

The job deadline is cooperative: it is checked between phases, records/closures
and streamed chunks; HTTP timeouts bound individual I/O phases by the remaining
budget. It is not an OS process-kill guarantee, and DNS/OS scheduling can delay
cancellation. This importer does not claim solver-style hard containment.

## Version decision: missing chain ID

M1's error mapper incorrectly classified a *missing* chainId as WRONG_CHAIN.
M2 corrects it to existing INVALID_INPUT; a supplied non-196/wrong-type value is
still WRONG_CHAIN. Floats/exponent notation fail earlier as INVALID_INPUT at the
canonical-JSON boundary. Both classifications have exact-code regression tests.
This is a narrow validation bug correction, not a wire/schema migration: no field,
enum, schema version or artifact hash changes. Clients that relied on the erroneous
missing-field classification must handle INVALID_INPUT. Other v1 bytes/semantics
remain frozen. Package/tool version stays unreleased 0.1.0 under the frozen literal;
the handoff Git revision identifies this implementation. A future tool-version
change needs an explicit contract compatibility decision.

## Blocking consumer gates (not implemented in M2)

M3 must resolve the actual project and both manifests by their declared hashes,
bind reference/candidate identities and actual input/output widths to project
mappings, then perform supported proof/witness replay. A self-declared
`mappingValidation: PASSED`, a content hash, or schema validation is insufficient.
Zero-input circuits remain valid; blanket non-empty-map checks would be incorrect.

M4 preflight must require a fresh fee and block-bound revalidation, nonempty
recognized revert evidence and selector/argument decoding before structural
classification. Empty or unrecognized errors must yield UNKNOWN, never acceptance.
The frozen permissive evidence fields were not silently tightened here. Both
consumers remain HTTP 501 / NOT_IMPLEMENTED and CLI exit 6; tests ensure crafted
proof flags and empty-revert claims cannot unlock them. M2 import freshness is
not a proof/preflight status and cannot be displayed as either.
