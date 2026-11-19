# Circuit Library contracts 1.0 and 1.1

Current `schemaVersion: m45-library-1.1.0`. M1, M2, M3, M4 and the library's frozen
`1.0.0/` schemas remain unchanged. `1.1.0/` introduces truthful `USER_SUPPLIED`
metadata provenance for user-only pointers. Unknown versions and fields are rejected.

The original Python model implementation is retained byte-for-byte in
`library_models_v1.py`; the schema exporter defaults to that frozen version. Current
callers use `library_models.py` (1.1). Both wire versions use the existing major-v1
HTTP endpoint and CLI, with dispatch by explicit `schemaVersion`.

Version 1.0 has only `ONCHAIN_DISPLAY_ONLY` in its enum, so it cannot truthfully
encode a favorite-only record. Legacy requests still receive valid 1.0 envelopes:
ordinary observations continue to work; user-only records are omitted and the
response reports `UNKNOWN / UNSUPPORTED_SCHEMA_VERSION` when a result requires
their newer provenance value. Their pointers remain intact in the overlay. Send
a 1.1 request to retrieve them as `USER_SUPPLIED`. This is an explicit upgrade
requirement, never a changed enum in an old schema or a false onchain claim.

A 1.1 request may carry a known 1.0 catalog. The complete old catalog is first
validated against its frozen model; identity and overlay data are preserved, the
catalog version changes to 1.1, and old user-pointer records get `USER_SUPPLIED`.
Unknown/authority fields are rejected before migration. Browser restoration keeps
original 1.0 bytes until the first edit, then writes a `flip-library-m45-v1-1.0.0-backup`
copy before saving the new catalog. Corrupt-data recovery remains a separate path.

HTTP: `POST /api/library/v1/execute`, JSON request/response. CLI:

```powershell
flip library --request docs/schema/m45-library/examples/1.1.0/discover.json --catalog catalog.json --out page.json
flip library --request docs/schema/m45-library/examples/1.1.0/search.json --catalog catalog.json
flip library --request docs/schema/m45-library/examples/1.1.0/circuits.json --catalog catalog.json
```

Operations: `discover`, `circuits`, `search`, `favorite`, `unfavorite`, `alias`,
`import`, `revalidate`. An identity is `(196, factory, processor, circuitId?)`;
the stable key is the colon-separated lowercase representation, with decimal
string circuit IDs. A null circuit ID denotes a processor. Search matches all
space-separated casefolded substrings over identity, processor number, onchain
display metadata and local aliases/favorites. Search results have an explicit limit
and total; the browser additionally pages saved records locally.

`discover` reads the current count, never a historical constant. `circuits` reads
the selected processor's exclusive `nextId` bound. Each request scans at most 50
indices (default 12), with at most 256 RPC attempts / 60 seconds by default. A
workbench processor page requests two entries to allow room for environment reads
on the public provider; circuit pages request 12 candidates. A
cursor binds offset, processor, block number/hash and environment digest. Resume
uses that same historical block; refresh without a cursor observes a new block.
Single-provider number pinning includes a final chain/header recheck, matching M2.
An opaque or authenticated cursor is unnecessary: it grants no authority and every
supplied value is bounded and independently checked.

Results distinguish COMPLETE, COMPLETE_WITH_GAPS, PARTIAL_BOUNDED, UNKNOWN,
ENVIRONMENT_CHANGED, REORGED, VERIFICATION_FAILED and ABORTED. `errorCode` uses
the inherited reason codes plus `BLOCK_IDENTITY_MISMATCH`. Network failures never
mean absence. Only closed known missing-token reverts count as gaps. HTTP 429,
5xx, transport failures and JSON-RPC -32005 use bounded retries; attempts count
against the budget. A page commits only after its final identity recheck.

Catalog observations are HISTORICAL/STALE/UNKNOWN/REORGED/VERIFICATION_FAILED;
there is intentionally no CURRENT or executable catalog field. `import` and
`revalidate` always rerun M2's complete importer at a fresh block, including REF
closure. Changed observed environments/netlists/dependencies return no import
payload. The changed observation is retained for inspection; an explicit subsequent
import/revalidation can accept that freshly inspected version. M2's CURRENT refers
only to that fresh observation, never to saved catalog data. Importing stateful
circuits is valid inspection; the composition UI refuses stateless composition.

Onchain display names have `ONCHAIN_DISPLAY_ONLY` trust. Synthesized user-only
pointers have `USER_SUPPLIED`, UNKNOWN freshness and no onchain evidence. Local labels are stored
in the separate overlay and never rename identity. Text is NFKC normalized, stripped
of nonprinting controls, limited to 256 characters and rendered as React text.
Authority-looking unknown fields cause contract rejection. HTML-looking text remains
literal text. Labels, favorites and recents never supply importer execution inputs.

Storage limits: 1,000 observations, 256 favorites, 256 aliases, 30 recents, 768 KiB
catalog with 384 KiB maximum overlay. Records are evicted before user pointers.
Search synthesizes an UNKNOWN user-pointer record for favorites absent from the
observation cache. CLI writes atomically to an explicitly selected `--catalog`
file; browser storage uses `flip-library-m45-v1`. CLI/API have the same pure
catalog-in/catalog-out contract; the server does not persist user collections.
HTTP input remains limited to 1 MiB and server concurrency remains two operations.
Browser Stop aborts its request and the service checks disconnect/abort between
bounded RPC attempts. In-flight reads finish within their configured timeout.
CLI Ctrl+C emits a structured RESOURCE_LIMIT error, exit 2; no partial page is saved.

CLI exits: 0 complete/partial bounded page, 2 unknown/abort/verification failure,
3 invalid contract/input, 7 changed environment/reorg. Network settings remain
operator environment configuration, never request metadata or browser-supplied URLs.

Generate/check schemas with:

```powershell
python -m flip_core.library_schema_export --out docs/schema/m45-library/1.0.0 --check
python -m flip_core.library_schema_export --version 1.1.0 --out docs/schema/m45-library/1.1.0 --check
```
