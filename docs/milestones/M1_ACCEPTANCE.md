# Flip M1 acceptance

**Date:** 2026-11-18 (Africa/Lagos). **Owner:** Codex, lead/integration engineer.
**Decision: M1 PASS — frozen foundations and historical evidence integration only.**
Ready to begin bounded M2 engineering with the gates below. This is not acceptance
of live imports, circuit execution, equivalence proofs, publication or a release.
Stop after this report and the integration PR; main is not merged by this task.

## Revisions and integration

Repository: [Technique-S/Flip](https://github.com/Technique-S/Flip).
Integration branch: `codex/flip-m1-integration`, created in the sibling
`flip-integration` worktree from freshly fetched `origin/main`.

| Revision | Full commit |
| --- | --- |
| Seed / latest main at integration | `37c39b3cf06edad908a6c579b7b0a78f1b42c202` |
| M1-A, codex/flip-m1-core | `6dc21e0b97ffe03273a62ea1e9499e6346244d32` |
| M1-B, opencode/flip-m1-fixtures | `e4de86ef8870fb9b85adf94ace400791a479f985` |
| Merge M1-A, two parents | `fb8510b438b5f93a32db81f4ec7895d0f3f7df3a` |
| Merge M1-B, two parents | `516fb841051c41742f085efda586b8f78cb6a336` |
| Integration checks | `c4b824c16ea43ae494de0034dec9ffdc638f3c46` |
| Validated integration code/config | `1135afaf17d1cdaaa362145c8e1d3e0525113c28` |

Both agent commits were present locally and have the seed as their common ancestor.
M1-B had no remote branch: it was located through `git worktree list` / `git branch
-avv`, not assumed pushed. Its commit is now reachable through the integration
branch. Both histories were preserved with `merge --no-ff`; there were no merge
conflicts, force pushes, rewrites of agent branches or direct main changes.

All three initial worktrees were clean. On the final recheck, OpenCode had moved
its own worktree to the separate `opencode/m1-independent-review` branch; its
requested M1-B branch still points to the exact commit above. That later review
was inspected read-only, not merged. All worktrees were clean at that recheck.

Ownership review: M1-A modifies only its root/build/CI, package and schema paths;
M1-B modifies only `fixtures/` and `docs/evidence/`. Seed PRD, architecture, original
audit documents and AGENTS.md are byte-identical in Git. Integration adds only
test/build verification and this report; no product source or frozen schema changed.

## Acceptance results

[Combined Windows and Linux CI, validated code/config](https://github.com/Technique-S/Flip/actions/runs/44232520959)
completed successfully at `1135afa`. The report-only follow-up is checked by the
same workflow; see the integration PR's latest checks for its final head.

| Check | Observed result |
| --- | --- |
| Clean Windows install | New `.venv`, uv 0.9.11, `sync --locked --no-cache --no-editable`, CPython 3.14.6; all 33 distributions installed |
| Complete pytest, Windows local | **163 passed**, 31.46 s; no warnings |
| Complete pytest, Windows CI | **163 passed**, 5.13 s |
| Complete pytest, Ubuntu CI | **163 passed**, 3.58 s |
| Original M1-A coverage | All 155 tests retained unchanged and green; eight integration checks added |
| Ruff | Lint and format pass on maintained code, including new scripts/tests |
| JSON Schemas | Six Draft 2020-12 schemas checked by existing roundtrip/schema tests; generated output has no drift |
| Canonical JSON | Python golden tests and six independent Node 24.18.0 vectors pass |
| CLI/API smoke | Identical normalized project bytes; CLI compare exit 6; real loopback ASGI liveness and compare HTTP 501 / NOT_IMPLEMENTED |
| Archive byte integrity | 12 raw plus two derived files match registered size and SHA-256 over exact Git blob bytes and checkout bytes |
| Provenance and tracked files | Both agent ancestors present; protected paths/frozen contracts unchanged; exactly 12 raw artifacts tracked; unexpected raw paths still ignored |
| Credentials / binaries | Pattern scan of all tracked text found no credential patterns; no unexpected binary/key/archive files; documented UTF-16 JSON decodes successfully |
| Cleanliness | Clean-tree checker passes on committed code; `git diff --check` passes for integration edits; only ignored environment/test scratch is created |

The test count is descriptive, not the acceptance criterion. New checks cover
archive-byte preservation, isolated derived recomputation, stored netlist/digest
consistency, recorded scale/negative findings, legacy manifest digests, stored
vectors/traces/revert data, historical-state rejection and REPORT_ONLY gaps.
They do not implement or replay a circuit evaluator, integrity engine or solver.

### Changes needed to combine the branches

- Added narrow `-text` Git attributes for raw artifacts and the two registered
  derived files. This preserves original LF/CRLF and UTF-16 LE/BOM bytes on both
  platforms. `.gitignore` is unchanged from M1-A; `/docs/evidence/raw/` still
  excludes new unregistered files while the 12 explicit tracked files remain tracked.
- Windows checkout initially converted the LF `vectors.json` and two LF derived
  files to CRLF. Their working copies were restored directly from their existing
  Git blobs after adding attributes. No committed historical bytes changed.
- Excluded only `docs/evidence/derived/recompute_checks.py` from Ruff: it is an
  immutable archival tool, not maintained product code. Its exact bytes are checked
  and it is executed against scratch copies; the resulting JSON matches the
  committed derived report byte-for-byte. All other maintained Python is linted.
- CI fetches full history so provenance checks can resolve the local-only M1-B
  ancestor, and runs the repository checker and real CLI/API smoke on both OSes.
- No dependency, lockfile, package source, published schema or original M1-A test
  was changed. No conflicts required content resolution.

### Failures found and resolved

The first combined run had 158 passes / four new-check failures: checkout byte
conversion, its derived-output comparison, and two incorrect test assumptions
(`sources[].id`, not `circuitId`; packing cases are nested under `packingEdgeCases.cases`).
Inspection corrected the new tests and checkout protection; no archived data or
expected findings were changed. Initial new-code import/format issues were corrected.

[First integration CI](https://github.com/Technique-S/Flip/actions/runs/44232486037)
failed Ruff E501 on a newly added clean-tree-check line. Commit `1135afa` formats
that line; the subsequent Windows/Linux run above passed. Hosted runners also
emit upstream action Node-runtime/runner-image migration notices; these did not
fail acceptance. No remaining M1 test failure is hidden or waived.

## Evidence integrity and provenance limits

The immutable [source inventory](../evidence/SOURCE_INVENTORY.md) records all file
sizes/hashes. We independently recomputed SHA-256 over Git **blob contents**;
Git object IDs themselves use a different hash framing and are not file SHA-256.
All 14 registered values match. All 12 raw blobs additionally matched the currently
accessible local source files under `C:\Users\Kazi\Documents\Flip\experiments`
and `C:\Users\Kazi\Documents\Flip\m05-final-verification\experiments`.

The canonical `C:\research\circuitforge-feasibility\experiments` and nested
`m05-final-verification\experiments` directories remain absent. Matching a local
copy does **not** establish identity with the originally audited originals, author,
run environment or RPC truth. The inherited `RAW_REPLAYED` label is retained as
historical metadata: acceptance establishes copied-byte integrity, not fresh
execution or independently verified original chain of custody. No REPORT_ONLY
claim is upgraded, missing data reconstructed, or stronger provenance asserted.

Offline findings reproduced from available bytes:

- XOR#1: 28 bytes, SHA-256 `d3f8f3a8316a49023a82436e92607f77a51e7f1b96b614b3d71417372f3f6a9f`.
- NAND#2: 21 bytes, SHA-256 `91c81eb018919169c97a8b7e10f4ab9bb2792960f53c0f4de3e3d2681939fd8e`.
- Composed half-adder: 81 bytes, SHA-256 `3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce`.
  Netlist bytes agree between the UTF-8 record and 6,836-byte UTF-16 LE/BOM rerun.
  Four recorded truth-table rows agree across stored expected/official/independent values.
- Both legacy manifest digests reproduce by hashing legacy sorted compact JSON
  without `manifestHash`; root/dependency netlist hashes match their stored bytes.
- Nine negative records have detected flags/issues; seven targets contain 28
  internally consistent recorded Minisat verdicts, seven safeguard pass flags,
  and timeout/skipped fallback records retain UNKNOWN. These are recorded results,
  not a fresh integrity-checker or SAT execution.
- The vector file hash matches frozen Semantics.testSuiteHash; it contains five
  valid, eight ill-formed and five packing cases. This counts records, not 18-vector replay.
- Eight-beat stored traces agree between standalone/embedded copies; recorded first
  difference is beat 0. No sequential evaluator was run.
- Preflight captures a revert / null result, unsupported override and decoded
  `[61453, 0, 1, 0]` fields. No successful simulation or publication is inferred.

Captured chain 196, block number/hash and fee fields are historical record labels.
Atomic/block-pinned RPC consistency and current chain state were not established
anew. The regression `test_imported_history_does_not_become_current_chain_verification`
rejects the legacy manifest as a v1 artifact, requires a revalidation block for
CURRENT, and confirms the import endpoint still returns NOT_IMPLEMENTED.

NAND/composed canonical manifests, a 100-run determinism log, original audited
directories, some selector/history evidence, live freshness and worker containment
remain absent or REPORT_ONLY as documented in [MISSING_ARTIFACTS](../evidence/MISSING_ARTIFACTS.md).
No network/RPC, solver, witness replay, signing, payment or broadcast was performed.

The credential check covers PEM private-key markers, GitHub/AWS token patterns
and quoted credential assignments. Public hashes/calldata are not treated as secret
keys solely for having 64 hex characters. This is a bounded pattern scan, not a
guarantee that arbitrary future secrets will be detected.

## Schema compatibility and M2 gates

The frozen `1.0.0` schemas, canonicalization profile, limits, error codes and
proof/intent/freshness axes are unchanged. Legacy audit JSON intentionally is not
accepted directly as v1: it uses integer IDs/block numbers, unprefixed code hashes,
flat environment keys and ABI words rather than v1 decimal strings, normalized
identities, nested objects and boolean fields. No runtime evidence adapter was
introduced. A future explicit adapter must preserve raw bytes, bind complete
dependency/environment data and keep historical evidence separate from freshness.

A separate local review at `0b440e5a37f402ababd3079ff558de1c6b2e23f4`
reported no Critical/High defects and conditional M1 foundation acceptance. Its
uncommitted-scaffolding finding is resolved by the committed checks and green CI.
The following remaining limitations were inspected/reproduced and are explicit
consumer gates, not silently changed frozen contracts:

| Limitation | Required before relying on M2+ results |
| --- | --- |
| Missing chainId currently maps to WRONG_CHAIN; float JSON is rejected earlier as INVALID_INPUT | Review/document exact taxonomy and add focused regressions in a controlled contract revision |
| A conclusive imported report can self-assert mapping validation without binding map widths to its referenced project/manifests | Resolve/hash-check referenced artifacts and validate actual widths before trusting/displaying a proof; zero-input circuits themselves remain valid |
| A self-declared known-burn preflight can contain empty revert bytes | Future producer/classifier must reject unsupported classifications or return UNKNOWN; schema acceptance is never observed structural progress |
| Original custody and live freshness remain unverified | Obtain original artifacts or explicitly accept/revalidate alternative provenance; do not turn historical data into CURRENT by schema validation |

These issues do not expose an implemented RPC/proof/preflight workflow in M1:
all product routes remain NOT_IMPLEMENTED. They block trusting future producers
without the specified checks. M2 may begin core work, but is not accepted here.
Parser/ABI/REF limits, manifest validation/freshness, actual solver binary/license
selection, hard 5s/64MiB containment, semantic replay and later product licensing
remain separate requirements. No M0.5 resource ceiling or exclusion is relaxed.

## Reproduce from a clean checkout

Use full Git history (CI uses `fetch-depth: 0`), CPython 3.14.6 and Node 24.18.0.
Commands below are PowerShell; on Linux substitute `.bootstrap/bin/uv` and
`.venv/bin/python`/tool paths.

```powershell
git clone --branch codex/flip-m1-integration https://github.com/Technique-S/Flip.git flip-m1
cd flip-m1
python -m venv .bootstrap
.\.bootstrap\Scripts\python.exe -m pip install uv==0.9.11
.\.bootstrap\Scripts\uv.exe sync --locked --no-cache --no-editable
.\.venv\Scripts\python.exe -m pytest -q --tb=short
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .
.\.venv\Scripts\flip-schemas.exe --out docs/schema/1.0.0 --check
node docs/schema/check-canonical.mjs
.\.venv\Scripts\python.exe scripts/smoke_m1.py
.\.venv\Scripts\python.exe scripts/check_m1_repository.py --require-clean
git diff --check
git status --porcelain
```

These checks were executed on the integration worktree; its initial clean install
used the already bootstrapped pinned uv executable in the adjacent Codex worktree.
Tests run the unchanged archival recomputation tool only in disposable scratch,
so neither originals nor committed derived evidence is rewritten. Both hosted
OSes independently perform clean locked installs and the same acceptance checks.
The integration PR targets main for review; no PR merge is part of this handoff.
