# Circuit Library contract v1

Additive `schemaVersion: m45-library-1.0.0`. M1, M2, M3 and M4 contracts and hash
profiles are unchanged. The three JSON Schemas in `1.0.0/` describe the request,
result and persisted catalog. Unknown versions and unknown fields are rejected;
there is no silent migration from an unknown version.

HTTP: `POST /api/library/v1/execute`, JSON request/response. CLI:

```powershell
flip library --request docs/schema/m45-library/examples/discover.json --catalog catalog.json --out page.json
flip library --request docs/schema/m45-library/examples/search.json --catalog catalog.json
flip library --request docs/schema/m45-library/examples/circuits.json --catalog catalog.json
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

Onchain display names have `ONCHAIN_DISPLAY_ONLY` trust. Local labels are stored
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
```
