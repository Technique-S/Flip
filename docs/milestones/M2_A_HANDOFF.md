# Flip M2-A handoff

**Date:** 2026-11-18 (Africa/Lagos). **Owner:** Codex, lead engineer.
**Decision: M2-A PASS — importer/integrity engineering acceptance.**
No M3 composition, Wiring Canary, evaluator, web UX, wallet, signing, broadcast,
fee expenditure or publication capability was added. This is not a public-service
security/release sign-off or a proof of either circuit's intended correctness.

## Baseline and revisions

[M1 PR #1](https://github.com/Technique-S/Flip/pull/1) was merged with explicit user
authorization, preserving both agent histories, at
`8e9b6b928b5d08b7383ae2413dec26d6068ea44e`. Local main was fast-forwarded to that
commit. A separate `flip-m2` worktree / `codex/flip-m2-import-integrity` branch was
created from synchronized main. Baseline: **163 passed** before implementation.

Implementation: `0c26ab7aebba0269b41a05de657578bdb2ba6075`.
[Windows and Linux implementation CI](https://github.com/Technique-S/Flip/actions/runs/44237948832)
passed. This handoff is a documentation-only follow-up; its branch-head workflow
repeats the same checks. M2 is pushed on its assigned branch and is not merged.

## Delivered files and behavior

| Files | Responsibility |
| --- | --- |
| `packages/flip-core/src/flip_core/rpc.py` | Bounded read-only HTTP/JSON-RPC transport, identity/envelope checks, retry/deadline/response limits |
| `abi.py` | Fixed verified read selectors; strict ABI words, addresses, uint32 tuples and dynamic bytes |
| `tap02.py` | NAND/LATCH/REF structural decoder, exact bytes and resource accounting; no evaluation |
| `importer.py` | Registered/existing circuit reads, number-pinned session, full REF DAG, memoization, cycles/depth, aggregate counts and environment identities |
| `integrity.py` | Content-addressed bounded historical cache, fresh closure revalidation, canonical-block/implementation invalidation |
| `import_models.py`, `import_schema_export.py` | Additive importer/result/budget contracts and standalone schema generation |
| `packages/flip-cli/src/flip_cli/main.py` | Import/inspect/revalidate entrypoints calling the shared service; atomic artifact output |
| `packages/flip-api/src/flip_api/app.py` | Versioned read-only routes, server-controlled RPC settings, two-job concurrency bound, structured errors and OpenAPI |
| `packages/flip-core/tests/test_m2_import.py` | 54 deterministic M2 test cases |
| `scripts/smoke_m2_live.py` | Separate opt-in live smoke; never run by mandatory CI |
| `docs/schema/m2/` | Three new schemas and interface/versioning/consumer-gate documentation |
| `docs/milestones/M2_A/` | Historical captures of real imports and live CLI/API parity |
| Root README, workflow, dependency metadata/lock, repository checker | Installation/docs, schema-drift CI, pinned HTTPX runtime dependency, M1 compatibility checks |

No original audit, historical PRD, architecture document, M1 evidence/fixture,
frozen schema/model/canonicalization or original M1 test was edited. `.gitignore`
and evidence byte-preservation attributes are unchanged. The repository checker
now freezes existing v1 wire artifacts/canonical rules rather than prohibiting
future runtime modules; it additionally pins all 163 accepted M1 tests to merged M1.
No test was removed or weakened to make M2 pass.

## Contracts and trust boundary

[M2 interfaces and formal version decision](../schema/m2/README.md) specify API,
CLI, budgets, error mapping, freshness, code-hash algorithm and limitations.

The six v1 schemas are byte-identical. New `ImportResult`, `RevalidationResult`
and `ImportBudget` schemas have independent `1.0.0` namespaces. Quantity strings,
chain 196, lowercase identities, canonical SHA-256 and TAP-02 provenance stay frozen.
HTTPX 0.28.1 was already pinned/installed for M1 tests and is promoted to core
runtime use; no dependency version was upgraded. Its existing BSD license inventory
still applies. No upstream evaluator or audit-script implementation is vendored.

The missing-chainId mapper is corrected from WRONG_CHAIN to existing INVALID_INPUT.
Supplied wrong-chain/wrong-type values remain WRONG_CHAIN; floats fail canonical
JSON parsing earlier as INVALID_INPUT. This is an explicitly documented validation
bug correction with no wire schema or artifact migration. Clients relying on the
old erroneous classification must adjust; exact-code regressions cover it.

Only a completed fresh-head import session may return CURRENT at its checked
block. Every state read is pinned to that number; chain identity is checked twice
and the block hash is rechecked before returning. Explicit-block imports and
stored captures are HISTORICAL. Cache reads cannot yield CURRENT, and known
changed entries become STALE. Revalidation freshly imports all sources, verifies
the old block is still canonical, compares bytes/counts/closure/environment and
retains original historical evidence.

Both source metadata and dependencies are checked: decoded gate/state totals must
match `circuitInfo`; each REF's actual I/O arity must match; registration, existence,
factory identity, processor beacon slot, implementations and nonempty code are
required. Proxy bytecode alone never establishes environment identity. Code hashes
use SHA-256 over fetched code bytes, matching the audit convention, not Keccak.

Proof and preflight consumers intentionally remain unimplemented. Tests ensure
self-declared mapping/proof flags and empty revert evidence return NOT_IMPLEMENTED.
Before M3 trusts any report, it must resolve/hash-bind actual projects/manifests,
identities and I/O widths, then perform supported proof/witness verification.
Before M4 structural acceptance, it must obtain a fresh fee/revalidation and decode
nonempty recognized revert evidence; unknown/empty errors must be UNKNOWN. Neither
gate can be bypassed by v1 schema validation or by this importer's freshness status.

## Actual validation results

| Acceptance | Evidence |
| --- | --- |
| Clean locked install | New `.venv-clean`, `--locked --no-cache --no-editable`, CPython 3.14.6, uv 0.9.11 |
| Complete offline suite | **217 passed**, 28.52 s locally, no pytest warnings; all original 163 plus 54 M2 |
| Windows/Linux CI | Both jobs passed at implementation commit above, with no live RPC in CI |
| Lint / format | Ruff checks pass; 26 maintained Python files formatted |
| Schema checks | Frozen six schemas and three new importer schemas have no drift; schema roundtrips/JSON Schema validation pass |
| Canonical parity | Existing Python hashes and all six independent Node 24.18.0 golden vectors pass |
| Read-only interfaces | Offline CLI/API import parity; real ASGI legacy smoke passes; real live pinned CLI/API parity also passes |
| Negative coverage | Wrong chain before state reads, invalid/missing IDs, malformed ABI/hex/netlists, trailing bytes, unregistered REF, arity mismatch, cycles and metadata disagreement |
| Resource coverage | Bytes, records, total closure, gates/multiplicity, unique nodes, depth including memoized subgraphs, request attempts and deadline checks |
| Integrity coverage | Factory/beacon implementation changes, modified identities/netlists/dependencies/interfaces, noncanonical old block and stale cache entries |
| Historical safety | Explicit-block/cached/captured evidence stays historical; legacy raw manifests cannot trigger fresh import; no proof/preflight claim is produced |
| Repository review | 14 M1 registered blob hashes still match, protected paths unchanged, bounded credential-pattern check found zero findings; working tree clean after commit |

The clean install imported flip-core from
`.venv-clean/Lib/site-packages/flip_core`, not the editable source directory.
No M2 test run failed. Early development lint/import-order formatting findings
were corrected before commit. Source inspection encountered a Windows console
Unicode printing error, corrected by escaping the display; source bytes were not
altered. uv logged harmless skips of obsolete setuptools distributions. There are
no hidden or waived test failures and no live-chain netlist discrepancies.

## Live read-only acceptance evidence

[Live captures](M2_A/live-smoke.json) were generated starting
`2026-11-18T04:18:37.103993+00:00` (05:18 Africa/Lagos). All three use block
`76206482`, hash
`0xce4394c5238d339ccf96d476e42a4f7b52d6fc24796a7f6c77dd93c914fff948`.

| Processor / ID | Observed result |
| --- | --- |
| `0x839bdd6fa7a66416a609a735e11de5411b98574e` / 1 | XOR label, 28 bytes, nIn 2 / nOut 1 / nState 0, 4 gates; hash matches `0xd3f8f3a8316a49023a82436e92607f77a51e7f1b96b614b3d71417372f3f6a9f` |
| Same / 2 | NAND label, 21 bytes, nIn 2 / nOut 1 / nState 0, 3 gates; hash matches `0x91c81eb018919169c97a8b7e10f4ab9bb2792960f53c0f4de3e3d2681939fd8e` |
| Same / 4 | 31-byte stateful wrapper; root hash matches `0x0d6225ff61bc8e990c757c9152a136ab580b5630c39317f81b9e05edce8070ad`; closure resolves core processor `0xf044d395c91e77459e6b2155015e14f0dd9b349f` / 102, aggregate nState 2 and 10 gates |

The environment observed factory implementation
`0x336e9f0f4c3fee7c8c803377e4dea00293f4ae2a`, beacon
`0xf70d1ed4f62cf3780157b0b421b7e2f45bd0991c`, implementation
`0x977f217887e085d298cb3819cdad5a0ee35f29b2`, and unsealed factory state.
The stored manifests contain all full code hashes and dependency environments.

[Live CLI/API parity](M2_A/live-api-cli.json): a real uvicorn subprocess and CLI
independently imported XOR at that explicit block; HTTP 200 / CLI exit 0, identical
canonical response bytes (apart from the CLI transport newline), manifest hash
`0x9cb088822cbcef579df1062c03d43ee9f81b1c5e34a4101341dd54423187ad57`.
The server was terminated/reaped after the check.

Live data is new single-RPC observation, not reconstructed M0/M0.5 evidence. Its
archival artifact freshness is HISTORICAL even where first observed at the head.
It does not repair the unavailable original-audit chain of custody, produce missing
historical manifests at older blocks, establish malicious-RPC resistance or prove
behavioral semantics. The original M1 evidence remains unchanged.

### Source provenance

Decoder/ABI rules were read from immutable
[TAP-02](https://github.com/TapeOutProtocol/TAPs/blob/527477ecb7cf68ee9e86d8292669d57fe1680572/TAPs/TAP-02.md)
at revision `527477ecb7cf68ee9e86d8292669d57fe1680572`, alongside the required
PRD/design/constraint/audit documents. The three circuit selectors match published
TAP-02 section 6. Other read selectors were derived with the inspected local
Keccak helper and exercised against live calls/storage; no NIST SHA3 substitution.
That local `gate_a_probe.py` copy has SHA-256
`15c854a852300f24a7f0aa09d5ce9e8331c7364b3ed3a693d3e6eb39ee3b0ca7`.
Its provenance remains a local-copy limitation; none of its code is shipped.
Pinned spec/reference/vector source hashes remain in the unchanged M1 provenance
record and Semantics contract.

## Reproduce

From the assigned branch, full Git history, Python 3.14.6 and Node 24.18.0:

```powershell
python -m venv .bootstrap
.\.bootstrap\Scripts\python.exe -m pip install uv==0.9.11
$env:UV_PROJECT_ENVIRONMENT = '.venv-clean'
.\.bootstrap\Scripts\uv.exe sync --locked --no-cache --no-editable
Remove-Item Env:UV_PROJECT_ENVIRONMENT
.\.venv-clean\Scripts\python.exe -m pytest -q --tb=short
.\.venv-clean\Scripts\ruff.exe check .
.\.venv-clean\Scripts\ruff.exe format --check .
.\.venv-clean\Scripts\flip-schemas.exe --out docs/schema/1.0.0 --check
.\.venv-clean\Scripts\python.exe -m flip_core.import_schema_export --out docs/schema/m2/1.0.0 --check
node docs/schema/check-canonical.mjs
.\.venv-clean\Scripts\python.exe scripts/smoke_m1.py
.\.venv-clean\Scripts\python.exe scripts/check_m1_repository.py --require-clean
```

These commands were actually executed; the install used the already bootstrapped
pinned uv executable from the adjacent Codex worktree. On Linux use corresponding
`bin` paths. Mandatory CI does not run the following optional network operation:

```powershell
.\.venv-clean\Scripts\python.exe scripts/smoke_m2_live.py --out .bootstrap/new-live-capture.json
.\.venv-clean\Scripts\flip.exe inspect --processor 0x839bdd6fa7a66416a609a735e11de5411b98574e --id 1
.\.venv-clean\Scripts\uvicorn.exe flip_api.app:app --host 127.0.0.1 --port 8000
```

The recorded live smoke used `--out docs/milestones/M2_A/live-smoke.json`.
A prior standalone CLI inspect also completed against the head and was retained
only as an ignored development output. For revalidation, save the `manifest`
member of an import result as standalone `manifest.json`, then run
`flip revalidate --manifest manifest.json`. API clients POST the frozen identity to
`/api/v1/import[?blockNumber=<decimal>]`, or a standalone manifest to
`/api/v1/revalidate`. Server RPC settings are configuration, not request fields.

## Remaining limits and architectural gates

- Pinning uses a block number with canonical-header rechecks, not EIP-1898 atomic
  hash-pinned reads. A single provider can lie consistently; no malicious-RPC
  resistance or finality guarantee is claimed. Providers must retain requested state.
- Import deadlines are cooperative with phase timeouts; DNS/OS scheduling can delay
  cancellation. Public rate limiting, deployment containment and stronger abuse
  controls remain hosting/release gates. No solver-style OS hard kill is claimed.
- Snapshot cache is bounded in memory and deliberately cannot assert freshness
  on read. No disk cache, user project persistence, arbitrary RPC proxy or automatic
  stale-cache fallback is implemented.
- Only registered processors using the verified factory/beacon-proxy relationship
  are supported. Other CPU implementations are rejected explicitly.
- Missing original audit directories and REPORT_ONLY gaps remain as documented
  in M1. New live captures are separate evidence, never retroactive verification.
- M3 project/report hash-and-width binding, actual proof/witness replay, and M4
  recognized-revert/fee preflight remain blocking gates. Stateful import metadata
  is supported; evaluation/unbounded sequential equivalence is not.
- Unreleased tool/package version remains 0.1.0 under the frozen literal; a future
  release/version change requires an explicit compatibility decision. Flip's own
  source license still requires a maintainer decision before distribution.

M2-A acceptance stops here. Main receives no M2 changes in this task.
