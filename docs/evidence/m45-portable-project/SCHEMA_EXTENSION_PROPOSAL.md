# M4.5-1 — Portable project schema extension proposal

**Status:** specification only. No frozen schema is altered and no migration is implemented.

## 1. Minimal versioned extension

Introduce an **additive** `flip-portable-project-1.1.0` envelope that *contains* the
existing artifacts by reference and digest rather than redefining them:

```
flip-portable-project-1.1.0
  schemaVersion, kind: "PORTABLE_PROJECT"
  executionRequest: <m3-1.0.0 VERIFICATION_REQUEST, byte-identical>
  executionRequestHash: <content_hash of embedded request>
  tests[]: <named vector sets; each is a VectorRequest-compatible object>
    name, vectors[], expectedCoverage, declaredIntent
  evidenceRefs[]: { kind: "FLIP_EVIDENCE", digest, reproduce, engineHash }
  revision: { parentHash: digest|null, revisionHash: digest, editLog[] }
  provenance: { sourceFreshness, observationBlock, syntheticFlags }
```

This is the smallest change that satisfies the complete pre-M5 specification while
leaving `1.0.0` (v1/M2/M3/library/debug contracts) frozen and byte-identical.

## 2. Fields

**Required**

- `executionRequest` and `executionRequestHash` — byte-identical embedded request; the
  1.0 execution request remains the canonical executable core.
- `tests[]` — at least one named vector set or an explicit empty-list with a
  `noDeclaredTests` marker; `vectors[]` must satisfy the existing VectorRequest bounds.
- `evidenceRefs[]` — content-addressed references to evidence bundles; no bundle content
  is duplicated.
- `revision` — `parentHash` (null for genesis) and `revisionHash` binding the ordered
  edit log; each edit records a hash of the before/after execution request.

**Optional**

- `provenance` — freshness annotations and synthetic flags; absent fields mean
  UNSPECIFIED, never CURRENT.
- `agentTaskRef` — digest of an M4.5-1A agent workflow task envelope (see below).

## 3. Migration path

1. A `1.0.0` file imports unchanged into `1.1.0` by wrapping it in `executionRequest`,
   computing `executionRequestHash`, setting `tests: []` with `noDeclaredTests: true`,
   `evidenceRefs: []`, and `revision.parentHash: null`. No source bytes change.
2. A `1.1.0` export to `1.0.0` emits only `executionRequest` and reports an explicit
   lossy-conversion notice for tests, evidence refs and revision history.
3. Unknown future versions fail closed with `UNSUPPORTED_SCHEMA_VERSION`; no silent
   downgrade.

## 4. Canonical serialization and hash compatibility

- Use the existing `flip-json-v1` canonical encoding (sorted keys, minimal separators,
  decimal strings for IDs, lowercase normalized addresses).
- `content_hash` of the embedded execution request is **identical** to today's request
  hash; historical comparison/project hashes remain valid and comparable.
- New top-level hashes are additional; they never replace or recompute existing manifest,
  netlist or project hashes.
- `revisionHash` chains `parentHash` + ordered edit hashes deterministically; a missing
  or reordered edit log invalidates it.

## 5. Validation behavior

- Shape validation never establishes proof or freshness (consistent with all Flip schemas).
- The embedded execution request must re-validate, compile and, if evidence refs are
  present, replay against caller-selected identities before any test/evidence claim is used.
- A digest mismatch in `evidenceRefs` or `executionRequestHash` is INVALID_INPUT; a stale
  dependency is STALE and blocks composition; neither can be self-declared CURRENT.
- An empty `tests[]` without `noDeclaredTests` is invalid.

## 6. Relationship to the agent workflow protocol

The M4.5-1A agent protocol already defines bounded `build/test/compare/inspect/
propose/verify/export/stop_authorization` operations and requires per-iteration hashes,
budgets and deterministic logs. `flip-portable-project-1.1.0` is the **input/output
package** for that protocol: `agentTaskRef` binds a task envelope to the revision it
operates on, and `revision.editLog` records accepted edits with their hashes. Agent
prompts and project metadata remain non-permissions; the publication stop boundary is
unchanged.

## 7. Risks

- Wrap-alongside rather than inline: keeping the 1.0 request byte-identical preserves all
  historical hashes; duplicating fields would fork hash semantics.
- Evidence refs must be content-addressed or cross-project substitution remains possible
  (demonstrated by P09).
- Named tests need an explicit empty marker or "absent" will be mistaken for "no tests
  required" (P04).
