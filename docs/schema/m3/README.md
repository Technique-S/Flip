# M3 execution interfaces — m3-1.0.0

Frozen v1 and M2 schemas, hashes, examples and tests are unchanged. This additive
namespace distinguishes an executable request from an untrusted serialized claim.
An existing `ComparisonReport` is still only a shape unless the trusted consumer
repeats validation and solving.

## Requests

`VerificationRequest` contains `schemaVersion: "m3-1.0.0"`,
`kind: "M3_EXECUTION"`, `project`, `imports`, and `relation`.
Imports are complete M2 `ImportResult` objects including exact dependency bytes.
Each declared source resolves by manifest hash and actual root identity. Actual
decoded widths, state, gates, REF edges, environment and closure must agree;
caller aliases never define semantics. Exactly one distinct import per source is
required, all at the same block and consistent factory/beacon execution context.
Repeated instances reuse a source alias.

Projects may use the unchanged v1 `Project` for imported-reference comparisons or
the additive `LocalProject` (`schemaVersion: "m3-1.0.0"`) for two local designs.
The latter replaces the imported reference alias with `referenceCandidate` using
the same bounded `Candidate` recipe shape; `comparison.referenceAlias` is null.
No synthetic onchain circuit ID is assigned to a local composition.

Components have explicit `instanceId`, `kind`, numbered input pins and REF source
aliases. Component order must already be a valid dependency order. Forward edges,
cycles, missing pins and wrong arity are rejected. All declared sources are
validated even when not executed. The candidate manifest includes the snapshots
actually executed and hashes of all declared source manifests.

`inputMap[i]` selects the **candidate input** used for reference input i.
`outputMap[i]` selects the **candidate output** compared with reference output i.
Both maps are complete bijections of the actual interfaces. Zero inputs require
the same identity and width checks; zero outputs are invalid under TAP-02/v1.

`relation` is `REFERENCE`, `PREVIOUS_VERSION` or `BEHAVIORAL`. The first two
require a user trust assertion and `TRUSTED_REFERENCE`; behavioral comparisons
require `UNDECLARED`. None of these declarations authenticate a real-world oracle.
No claim is inferred from aliases such as “xor”, “sum” or “carry”.

`VectorRequest` adds `vectors` with exact-width `inputs` and expected `outputs`
using v1 LSB0 BitVectors. Duplicate inputs reject. At most 4,096 rows and
2,000,000 expanded work units are allowed. Full input coverage is labeled only
when every distinct input exists (at most 12 bits); partial matches are not
universal equivalence. Results are VECTORS_MATCH/VECTORS_MISMATCH, never SAT proofs.

## Execution and output

```text
flip compose --project request.json [--out composition.json]
flip compare --project request.json [--out comparison.json]
flip vectors --project vectors.json [--out vector-result.json]
flip consume --project consumption.json [--out recomputed-comparison.json]
```

Files contain full versioned execution requests, not a bare v1 project. `--out`
writes JSON (the composed bytes are in `netlist`), not a binary or ZIP export.
CLI exits remain 0 completed match/compose, 1 DIFFERENT/vector mismatch,
2 UNKNOWN/resource limit, 3 invalid input, 4 RPC infrastructure, 5 internal,
6 unavailable, 7 stale import and 8 structural rejection. The last categories
retain their v1/M2 meanings. Structured JSON is authoritative.

The equivalent routes are POST `/api/v1/compose`, `/api/v1/compare`,
`/api/v1/vectors`, `/api/v1/consume`. JSON bodies use the same shared core.
Invalid requests return 422, request size 413, local resource/concurrency
rejections 429, completed comparisons (including UNKNOWN) 200. Legacy bodies and
bare serialized reports still receive 501 and cannot unlock a proof consumer.
Preflight/export remain 501. Liveness retains its frozen legacy response.

**Native HTTP execution is disabled by default.** For a trusted local process,
set `FLIP_LOCAL_SOLVER=1`, bind uvicorn to `127.0.0.1`, and use it directly from
loopback. Compare/consume additionally check the connected peer. Do not expose
this configuration through a public proxy: peer checks are not authentication.
No public solver deployment or public rate-control readiness is claimed.
API request cap is 1 MiB; CLI input cap is 4 MiB; local API concurrency is two.

Conclusive output contains the frozen report, exact reference/candidate identities
and manifests, project/request hashes, reproduction request, declared maps,
source/native implementation hashes, solver outcome, resource metrics, timestamp,
coverage, intent and freshness. There are no fabricated confidence probabilities.
UNSAT means exact stateless pairwise EQUIVALENT; SAT only becomes DIFFERENT after
independent local replay. Timeout, crash, containment or replay failure yields
UNKNOWN. Invalid interfaces/dependencies reject before solving.

All local results are HISTORICAL (or STALE when an input was already stale).
Neither supplied CURRENT flags nor fresh computation make cached chain data
current. M2 revalidation remains a separate observation operation. The archived
sample block is 76206482; no M3 test makes a new chain observation.

## Trusted consumption

`ConsumptionRequest` uses `kind: "M3_CONSUMPTION"`, `executionRequest`,
`claimedResult`, `expectedProjectHash`, and `expectedReferenceHash`. The expected
hashes must come from the consumer's selected project/reference, not be copied
from an untrusted report. The core also exposes `consume(request, claim,
expected_project_hash=..., expected_reference_hash=...)`.

Consumption resolves/compiles again, verifies all bindings and engine hashes,
reruns SAT even for claimed EQUIVALENT, and independently replays a claimed
DIFFERENT witness. A changed project, dependency, reference, implementation or
empty fabricated mapping cannot be promoted by self-declared PASSED flags.
UNKNOWN cannot be consumed as conclusive. Returned evidence is newly constructed;
caller-supplied resource, coverage and timestamp fields are never promoted.

Reports are reproducible evidence, not signed certificates or independently
checkable UNSAT proof traces. Native solver correctness remains an assumption.
Platform-specific native hashes deliberately prevent silently trusting another
build's result; recompute on the target platform to obtain new evidence. This
does not authenticate an RPC provider or a user-declared baseline.

## Reproduction

The committed half-adder request uses genuine M2 XOR #1/NAND #2 captures. Regenerate
with `python scripts/make_m3_sample.py --out request.json`. Its generated bytes
match the immutable audited 81-byte fixture, four rows, with 100 identical builds.
NAND(x,x) canonicalizes to NAND(x,constant-one), preserving behavior and reproducing
the audited carry inverter. Non-final selected outputs get an explicit inversion
bank and final contiguous NAND buffer bank; gate overhead is counted.

Run `python -m flip_core.verification_schema_export --out docs/schema/m3/1.0.0 --check`
for schema drift. `python scripts/benchmark_m3.py --out bench.json` repeats the
28-case benchmark through production construction/replay; its transport context
is explicitly synthetic, while XOR bytes are archived real bytes. Live RPC smoke
remains separate and opt-in. No export ZIP, M4 preflight, UI or signing is added.
