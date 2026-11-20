# Portable project 1.1

`flip-portable-project-1.1.0` is an additive envelope around the accepted M3 execution
request. Frozen M1/M2/M3/library/debug schemas and engine bytes are unchanged. The
independent proposal and observations are preserved under
`docs/evidence/m45-portable-project/`, sourced from
`2f3d6263edf4e62ad4e94718c99f6c1a79e350a1`.

## Transport and conversion

Use `flip portable --request operation.json [--out new-file.json]` or
`POST /api/v1/portable` with exactly the same JSON. `--out` exclusively creates a new
file and refuses an existing destination. The API is stateless. Browser saves include
the revision number/hash in the filename; browser download settings control filesystem
placement. Browser session storage retains the last committed package alongside the
current executable draft. Save/download a revision before closing the session.

```json
{
  "schemaVersion": "flip-portable-project-1.1.0",
  "kind": "PORTABLE_REQUEST",
  "operation": "wrap",
  "executionRequest": "REPLACE_THIS_STRING_WITH_THE_EXISTING_M3_REQUEST_OBJECT"
}
```

The example above is a template, not a valid execution request. The generated
[golden packages](1.1.0/golden.json) contain complete valid examples.

| Operation | Required payload | Result |
|---|---|---|
| `wrap` | `executionRequest` | New genesis package; no implicit tests or evidence |
| `wrap` with ancestry | `executionRequest`, `previous`, `expectedRevisionHash` matching previous head | New revision, retains parent and ordered ancestors; optional `description` |
| `validate` | `package` | Validated package; local data integrity only |
| `open` | `package` | Original `executionRequest` and package, after trusted compilation |
| `test` | `package` | Named existing vector-evaluator results, never an equivalence proof |
| `replay-evidence` | `package`, optional `artifacts` mapping digest to FLIP_EVIDENCE object | Per-reference `REPLAYED` or `MISSING_EVIDENCE`; rejects corrupt, substituted or incompatible artifacts |
| `downgrade` | `package`, `allowLossy: true` | Legacy `executionRequest`, explicit `discardedFields` and warning |

`wrap` optionally accepts `tests`, `evidenceRefs`, `provenance`, `agentTaskRef`.
Omission preserves previous metadata; supplied arrays replace the array, including `[]`
to explicitly remove it. Changed execution requests require explicit removal/replacement
of old evidence references. Other operations optionally accept `expectedRevisionHash`
to pin the selected head. Unknown or irrelevant fields fail closed. Unsupported package
versions produce `UNSUPPORTED_SCHEMA_VERSION`; no automatic conversion occurs.

Existing `flip compose`, `compare`, `export`, `verify-bundle`, `preflight` accept either
legacy execution requests or portable packages. HTTP `compose`/`compare` also accept
either. Existing product API callers can explicitly use `open.executionRequest`.
`vectors` retains its frozen external VectorRequest interface; package tests use `test`.
The browser's **Save project** retains its legacy behavior; **Save complete portable
project** includes metadata. **Export legacy project** requires the loss acknowledgement.
A bare M1 Project lacks import bytes and cannot be made executable without separately
supplying its existing M3 execution request; the converter does not invent imports.

## Hash preimages and revision decisions

All digests use existing `flip-json-v1`: SHA-256 of UTF-8 JSON, sorted ASCII object keys,
minimal separators, no floats/unsafe integers/duplicate keys, array order preserved.
Digests are lowercase `0x` plus 64 hex digits. Address/ID validation uses the frozen M3
contract; no new executable interpretation is introduced.

* `executionRequest` preserves the supplied JSON object, without inserting default
  fields or duplicating project state elsewhere in the package. Formatting whitespace
  is not part of a JSON object's identity.
* `executionRequestHash = content_hash(executionRequest)` hashes that exact supplied
  object. The frozen engine continues to use its own normalized-model `requestHash`
  and project/manifest hashes; these are neither replaced nor overridden. For a sparse
  legacy object with omitted defaults, its transport hash can differ from the engine's
  normalized request hash. Both retain their existing canonical preimages.
* `metadataHash` hashes exactly `schemaVersion`, `kind`, `tests`, `noDeclaredTests`,
  `evidenceRefs`, `provenance`, `agentTaskRef`, with their normalized package values.
* Each revision hashes the full revision object **except `revisionHash`**: `projectId`,
  `sequence`, `parentHash`, `executionRequestHash`, `metadataHash`, ordered `editLog`.
  The schema version is bound through `metadataHash`; there is no implicit delimiter,
  timestamp, author or platform component.
* Genesis has sequence 0, null parent, and first edit's `beforeHash: null`.
  Later revisions increment sequence and use the preceding revision hash as parent.
  Their first `beforeHash` equals the preceding execution request hash. Each next edit
  starts at the preceding edit's `afterHash`; final `afterHash` equals the record's
  execution request hash. Metadata-only edits may have equal before/after hashes.
* `ancestors` contains all preceding revision records in oldest-first order; `revision`
  is the current head. Every record must bind the same embedded `project.projectId`.
  Its head metadata/execution digests must match the package. Broken, truncated,
  reordered, transplanted or incompatible chains reject. A caller can pin the head to
  detect replacement by another internally valid chain.

An ancestor record preserves checksums/edit descriptions, not the ancestor's entire
execution request/tests/evidence. Keep previous package files to restore old content.
An internally consistent hash chain authenticates neither the author nor a global
project namespace. Intentional complete rewriting/re-hashing cannot be prevented without
an independently trusted head. No signature/author permission is inferred.

## Named tests and bounds

Each set has unique `name` (frozen Name syntax), nonempty `declaredIntent` (up to 2,000
characters), `expectedCoverage` (`SELECTED_INPUTS` or `EXHAUSTIVE_DECLARED_DOMAIN`), and
1–4,096 existing ExpectedVector rows. At most 64 sets and 4,096 aggregate rows are allowed.
Each input/output BitVector uses `tap02-lsb0-v1`, exact candidate widths, and unique inputs
within its set. Exhaustive declarations require every input and at most 12 input bits.
The embedded execution request preserves comparison intent, mappings and source identities.
Expected outputs address numeric candidate pins, as in the existing vector evaluator;
they are not remapped into reference output order. `tests: []` requires
`noDeclaredTests: true`; populated tests require false. The existing aggregate evaluator
work ceiling (2,000,000 units) also applies across the entire package. Dispatch checks a
five-second deadline between test sets, in addition to existing per-set checks.

Declared coverage and intent are user metadata. Even exhaustive vector matches are labeled
VECTORS_MATCH, never promoted into SAT equivalence or intended correctness.

## Evidence and freshness

A reference has `kind: FLIP_EVIDENCE`, `digest`, `executionRequestHash`, the exact existing
`reproduce` command and `engineHash`. It binds the head request's transport hash.
`digest` is the existing FLIP_EVIDENCE `contentHash`: canonical artifact excluding its
`contentHash` member, not the digest of arbitrary formatted file bytes. This avoids
changing the existing evidence format. `engineHash` binds the comparison's engine identity.
Duplicate digests reject. At most 128 references are allowed.

`validate` proves neither evidence existence nor equivalence. `replay-evidence` checks the
supplied artifact's checksum, reproduction identity and engine pin, then calls the
**existing** `workflow.product('verify-bundle')`. That consumer independently binds the
selected project's normalized request, comparison maps, dependencies, manifests, engine
bytes and scope, reruns SAT, and replays differences. A checksum-valid embedded
EQUIVALENT is never sufficient. Missing artifacts return MISSING_EVIDENCE without fetching
URLs or executing the reproduction string. Corrupt/substituted files reject. Older engine
bytes/platforms fail the frozen identity check rather than silently trusting old claims.
A 15-second dispatch deadline bounds a replay batch; an active comparison remains subject
to its existing five-second worker ceiling. No partial proof is returned on budget failure.
HTTP replay requires the existing solver opt-in plus loopback client; local CLI uses the
existing isolated native engine. No JavaScript solver or RPC dependency is added.

Provenance has `sourceFreshness` UNSPECIFIED (default), HISTORICAL or STALE,
`observationBlock` (decimal string or null), and at most 32 `syntheticFlags` strings.
Absent provenance is UNSPECIFIED. CURRENT cannot be declared by package metadata.
The supplied annotations cannot confer authority or upgrade imported freshness.
STALE imports or a STALE provenance annotation block portable open/composition/test;
validation and archival conversion remain possible. Replay preserves stale observations
or rejects changed exact reproduction bindings. It never promotes a result to CURRENT.
Legacy request execution semantics remain unchanged.

All structured requests are bounded to 1 MiB, including ancestry/artifacts. History is
bounded to 1,024 revisions, 128 edits per record; callers must archive/split workflows
when the actual byte budget is reached, never silently truncate ancestry. JSON Schema
checks structural types; runtime validation additionally checks digests, chains, widths,
coverage and compilation. Shape validity is not proof validity.

## Regeneration and parity

```text
python -m flip_core.portable_schema_export --out docs/schema/m45-portable-project/1.1.0 [--check]
node docs/schema/m45-portable-project/check-canonical.mjs
python scripts/check_m45_portability.py
```

Python/Node goldens bind complete genesis, edited and synthetic metadata-rich packages, original requests,
metadata digests, ordered ancestry and full package canonical bytes. The independent
12-case harness is preserved byte-for-byte as `harness/run_portability_cases.py.txt`
inside the evidence directory. The production runner checks its SHA-256 and redirects
result locations, CLI path and loopback port into `.test-tmp`; archived observations remain immutable.
It generates a fresh native-engine evidence artifact for the current platform.
