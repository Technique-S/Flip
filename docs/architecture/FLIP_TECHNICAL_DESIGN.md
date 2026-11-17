# FLIP — Technical Design Specification

**Version:** 1.0 implementation proposal • **Date:** 2026-11-16  
**Status:** Prepared for engineering review; new architecture decisions are not audit-proven.  
**Product requirements:** Historical `CircuitForge_PRD_v1.md` FR-001–063 / NFR-01–12; new branding is **Flip**.

## 1. Selected stack and rationale

| Concern | Selection | Rationale / caveat |
|---|---|---|
| Shared verification runtime | Python 3.12+ with pinned tested minor version | Reuse independent audit's Python TAP-02 parser/evaluator and Minisat22/PySAT PoC; verify compatibility rather than blindly transplant code |
| API | FastAPI + Pydantic v2, ASGI | Thin typed adapter for shared Python core; validate versions on actual lockfile |
| CLI | Python `Typer` or `argparse` (prefer Typer if packaging clean) | Calls same core directly, JSON-first machine output |
| Solver | PySAT Minisat22/CDCL in **separate bounded OS process** | Reported 28/28 cases to 5,000 gates. Runtime license, platform and hard memory kill still need implementation proof |
| Web | React + TypeScript + Vite | Guided compact web workflow; UI does not replicate verifier logic |
| Frontend data | Generated TypeScript definitions from versioned JSON Schema/OpenAPI | Share schema meaning across languages; type generation is not the source of truth |
| Blockchain read adapter | Python `httpx` JSON-RPC with audited ABIs (using `eth_abi`/`eth_utils` only if necessary) | Avoid extra wallet libraries/signers; strictly allowlisted RPC methods |
| Canonical hash | SHA-256 over specified canonical UTF-8 JSON | Align with M0.5 manifest hash; define exact JSON number handling |
| Package/build | Python lock with hashes; npm/pnpm lock for web; monorepo | Reproducible installs; pin versions after clean-machine check |
| Tests | pytest + hypothesis, Vitest, Playwright | Separate pure logic, hostile-input, UI and integration coverage |
| Web hosting | Static frontend + small isolated Linux API container | Simpler and safer for native solver than promising untested WASM; public-service safeguards required |

**Rejected for MVP:** a second TypeScript SAT implementation; an always-on blockchain indexer; multi-RPC Byzantine quorum; a full general circuit canvas; browser WASM solver without parity measurement; user accounts; database of private user projects.

## 2. Monorepo and package layout

```text
flip/
  README.md
  LICENSE
  CONTRIBUTING.md
  docs/
    architecture/              # five planning docs
    schema/                    # published JSON Schema and example artifacts
    ux/                        # future UX spec
    evidence/                  # M0/M0.5 links and hash records
  packages/
    flip-core/                 # Python pip package: schema, chain, parse, refs, compose, verify, manifest, export
      pyproject.toml
      src/flip_core/
        schema/ chain/ tap02/ refs/ compose/ sim/ canary/ integrity/ preflight/ export/
      tests/
    flip-cli/                  # Python CLI depends on flip-core (same release version)
      pyproject.toml
      src/flip_cli/
      tests/
    flip-api/                  # FastAPI thin facade; depends on flip-core
      pyproject.toml
      src/flip_api/
      tests/
    flip-web/                  # React TypeScript UI, no solver and no user signing code
      src/app/ src/components/ src/features/ src/generated/ src/lib/
      tests/
  fixtures/
    golden/                    # known X Layer corpus snapshots with provenance
    malformed/ mutations/ integrity/ parity/
  scripts/
    generate_schemas.py
    check_write_rpc_absence.py
    normalized_parity.py
  .github/workflows/
```

**File ownership rule:** shared schema, core, API routes and package root are Codex-owned. OpenCode works in expressly delegated bounded subpaths (fixtures, test files, docs, standalone presentation components); never edits shared interfaces without a reviewed contract change.

## 3. Core contract conventions

### 3.1 Numeric and binary representations

- `chainId` canonical JSON integer `196` (all requests refuse others).
- `processor` and other EVM addresses: validate as 20-byte addresses; normalized lower-case `0x` + 40 hex in digests, EIP-55 checksum only for display.
- `circuitId`, block number, and EVM big integer quantities: **decimal strings** in API/public JSON to avoid JS 53-bit losses; internal Python `int`.
- Netlists: bytes internally; lowercase `0x` hex on JSON wire and inside portable artifacts; validate byte length before decoding.
- Bitvectors: `"0"`/`"1"` strings or explicit LSB-first arrays with `bitOrder:"tape02"`, never arbitrary JS numbers for wide inputs. **Implement exact reference-tested TAP-02 packing; do not guess orientation.**
- Timestamps and empirical runtime are *noncanonical* envelope fields; exclude them from content hashes.
- Canonical JSON: normalized keys sorted recursively, UTF-8, no insignificant whitespace; strings normalized as specified by schema. `manifestHash = sha256(canonical_bytes(payload_without_hash))`; self-hash field excluded. JSON serialization version must be pinned and tested with cross-language golden vectors.
- Project file and report schemas use independent versions; initial `1.0.0`, with compatibility policy: reject unsupported majors, migrate known minors only with explicit migration log.

### 3.2 Sample project contract (schematic, not executable golden fixture)

```json
{
  "schemaVersion": "1.0.0",
  "network": {"chainId": 196},
  "sources": [{"alias": "xor", "processor": "0x839bdd6fa7a66416a609a735e11de5411b98574e", "circuitId": "1", "manifestHash": "<sha256-hex>"}],
  "components": [{"instanceId": "xor1", "sourceAlias": "xor"}],
  "wires": [{"from": {"kind": "external", "index": 0}, "to": {"instanceId": "xor1", "pin": 0}}],
  "candidate": {"outputs": [{"instanceId": "xor1", "pin": 0}]},
  "comparison": {"mode": "reference", "baselineManifestHash": "<sha256-hex>", "inputMap": [0,1], "outputMap": [0]},
  "limits": {"gateCap": 2500, "refDepthCap": 64, "solverTimeoutMs": 5000, "solverMemoryMiB": 64}
}
```

Production schema must contain every required field and exact mapping validity checks. Do not use this partial illustration as a test fixture.

### 3.3 Result contract

A report has **separate axes**:

- `verification.kind`: `PAIRWISE_EQUIVALENCE` | `VECTOR_TEST` | `BOUNDED_TRACE`.
- `verification.verdict`: `EQUIVALENT`, `DIFFERENT`, `UNKNOWN` for exact stateless pairwise; vector and trace tests have their own typed statuses (`VECTORS_MATCH`, `VECTORS_MISMATCH`, `BOUNDED_TRACE_DIFFERENCE`, `BOUNDED_TRACE_NO_DIFFERENCE`, `UNKNOWN`). Do not conflate.
- `verification.intent`: `TRUSTED_REFERENCE`, `USER_VECTORS`, `UNDECLARED`. With `UNDECLARED`, pairwise comparison is possible but shown as *behavioral diff*, never “correctness”.
- `integrity.freshness`: `CURRENT` | `HISTORICAL` | `STALE` | `UNVERIFIED`.
- `preflight.status`: independent `STRUCTURALLY_ACCEPTED` | `REJECTED` | `UNKNOWN`, never an alias for verification verdict.
- `error.code`: stable machine-readable reason (`WRONG_CHAIN`, `BAD_NETLIST`, `REF_DEPTH_EXCEEDED`, `RPC_UNAVAILABLE`, `IMPLEMENTATION_CHANGED`, `SOLVER_TIMEOUT`, `WITNESS_REPLAY_FAILED`, `UNSUPPORTED_STATEFUL_PROOF`, etc.). Invalid input/API errors are not proof verdicts.

**Necessary distinction:** SAT `UNSAT` proves pairwise equivalence under the chosen model even if no semantic oracle is trusted. Missing **second comparison target or required mapping** is `INVALID_INPUT/UNKNOWN`; merely missing an intent declaration cannot erase a valid pairwise finding.

## 4. Internal interfaces (proposed, stable after M1)

```python
@dataclass(frozen=True)
class CircuitKey:
    chain_id: int
    processor: str
    circuit_id: int

class ReadOnlyChain(Protocol):
    def chain_id(self) -> int: ...
    def fetch_snapshot(self, key: CircuitKey, block_tag: str | int) -> CircuitSnapshot: ...
    def fetch_environment(self, block_tag: str | int) -> EnvironmentSnapshot: ...
    def preflight_call(self, payload: bytes, value_wei: int, block_tag: str | int) -> RpcCallResult: ...

class CircuitResolver(Protocol):
    def resolve_closure(self, root: CircuitKey, budget: ImportBudget) -> ResolvedClosure: ...

class Composer(Protocol):
    def compile(self, plan: CompositionPlan, closure: ResolvedClosure) -> ComposedCircuit: ...

class Comparator(Protocol):
    def compare(self, pair: ComparisonPair, budget: SolverBudget) -> ComparisonResult: ...

class Integrity(Protocol):
    def manifest(self, closure: ResolvedClosure) -> IntegrityManifest: ...
    def revalidate(self, manifest: IntegrityManifest, live: EnvironmentSnapshot) -> FreshnessResult: ...
```

These are semantic contracts; use exact Python types and module APIs established through schema tests in M1. Make all caller-visible errors typed. Avoid hidden network calls inside parser/SAT modules.

## 5. Chain reader and integrity manifest design

### Read sequence

1. Call `eth_chainId` and require `196`.
2. Pin a block number **and block hash**; retrieve headers and enforce consistent observation context. Where RPC supports EIP-1898 hash-pinned calls, use them; otherwise use block number with before/after hash checks and mark the limitation.
3. Check factory at audited address `0x1f09DAeFA827f02CBb40967cc91b259763760761` and verify code/registry identity.
4. Fetch `nextId`, `circuitInfo`, `netlist` with ABI-tested decoding; reject nonexistent IDs and malformed netlists.
5. Enumerate REF targets and recursively resolve closure with cycle detection, memoization, depth cap 64, record/expanded-gate budgets and request cap. Reject cross-chain input before lookup.
6. Collect factory ERC-1967 implementation storage slot/code hash, processor proxy code hash, beacon and implementation codehash, `isSealed`, and dependency-specific environment identities.
7. Compute canonical manifest and digest. Cache on `(196, processor, id, netlistHash, factoryImplHash, beaconImplHash, closureDigest)`.
8. Re-read live environment and dependency closure before marking verification **CURRENT**, exporting a fresh report or running pre-flight. Changed environment turns *freshness* `STALE`; historical report remains intact.

Audit warning: on X Layer the factory was observed unsealed (`isSealed=0`) and the documented implementation differed from the live contract. Do **not** treat proxy address or proxy bytecode as sufficient identity. Cross-chain REF records are chain-blind; Base 8453 had colliding addresses with different state.

### Defensive constraints

- Import budget: include byte cap, record cap, expanded-gate cap, REF arity cap, depth cap 64, max total referenced circuits and cumulative RPC budget. Set exact non-solver caps through hostile fixture tests before M2 acceptance; do not assume gate count alone prevents exponential expansion.
- Cache only immutable **content snapshots**, not assertions of permanent chain truth.
- Untrusted RPC data can be self-consistent but false. Report provenance as `single-rpc observation` and do not claim malicious-RPC resistance.

## 6. Restricted composer

- Composition inputs: actual source REF identities, numbered bit pins, named *user* aliases marked unverified, explicit external inputs, limited glue `NAND`, specified output ordering.
- Type-check each edge, arity, index range, fan-out, undefined source and cycles. Topologically order instances; deterministically allocate signals and encode REF records under TAP-02. Support any required final-output copy/buffer using verified gate encodings and report overhead.
- Refuse unsupported stateful composition in P0; P1 may only compare already-loaded stateful circuits over bounded traces, not certify arbitrary sequential compositions.
- Never infer business intent from pin names or claim compatibility from widths alone.
- Golden fixture: XOR proc0#1 + NAND proc0#2 → 81-byte half-adder, 2 REF + 1 NAND, 4/4 truth-table, 100 identical output hashes. No deployment required for this test.

## 7. Verification and Wiring Canary

### Exact stateless pairwise comparison

1. Validate both circuits and identical/explicitly mapped external I/O domains; assert supported stateless and same pinned semantics assumptions.
2. Recursively inline REF behavior under explicit bounded budgets. Compare **outputs and mappings**, not only gate counts.
3. Encode a SAT miter via Tseitin clauses using independent variable namespaces and shared mapped external inputs; `OR` per-output XOR-differences.
4. Run Minisat22 in OS-isolated worker with **5 s** deadline and **64 MiB hard memory limit**, plus up-front equivalent-gate cap 2,500 default, user-raised at most 5,000. REF nesting cap 64.
5. `UNSAT` => `EQUIVALENT` within modeled stateless domain; `SAT` => obtain witness and independently run TAP-02 `beat` on both sides. If outputs differ, `DIFFERENT` with witness; if not, `UNKNOWN` with internal mismatch error and block export of trusted proof.
6. Attempt witness minimization under bounded, documented budget; never say “globally minimal” without a separate proof. Re-verify minimized witness.
7. Timeout, worker kill, unsupported feature, resource ceiling or ambiguous mapping => `UNKNOWN`/typed invalid input, never EQUIVALENT.

The M0.5 28/28 SAT checks arose from a specific XOR-chain benchmark family (up to 5,000 gates, max ~1.4 s, peak <8 MiB). Do not generalize those timings to arbitrary graphs, platform RSS, or web hosting without measured parity.

### Vectors and absence of intent

- Explicit expected vectors may show `VECTORS_MATCH`/`VECTORS_MISMATCH` with stated input coverage. No full proof unless exhaustive domain actually evaluated and validated.
- Candidate vs baseline **without declared trusted oracle** can still return pairwise EQUIVALENT/DIFFERENT, but UI says *“same/different behavior, intended correctness unknown”*.
- Do not use a vector-only oracle as a basis for SAT universal EQUIVALENT unless the entire specified truth-table domain is represented and proved.

### P1 bounded stateful comparison

- Allow at most 8 beats with an explicit zero-state initial condition and user input sequence. Return first differing beat/output/state or `BOUNDED_TRACE_NO_DIFFERENCE`. Never call this unbounded equivalence.

## 8. Solver isolation, cancellation and hard limits

A safe public endpoint cannot simply `await` a blocking SAT call or rely on a Python-level timeout. Each verification spawns a short-lived worker process (or pre-spawned one isolated job per process) under an OS/container limit. Parent enforces wall timeout, kills process tree on timeout, reaps children, deletes temps and returns `UNKNOWN` with reason. For Linux, use cgroups/container worker memory controls or a measured equivalent; avoid asserting `RLIMIT_AS` works universally with native PySAT libraries. Test against hostile resource fixture on actual deployment target. Limits apply *per job*, plus service concurrency cap and API rate limits. Store only sanitized telemetry and correlation IDs.

## 9. HTTP API design (read-only product operations)

Version prefix `/api/v1`; all endpoints accept versioned schemas, return structured errors and never construct signable transactions. Endpoint names are proposed design choices:

| Method/path | Request | Success result | Notes |
|---|---|---|---|
| `GET /healthz` | none | liveness | Not verification status |
| `POST /api/v1/import` | `CircuitKey` | `CircuitSnapshot + Manifest` | Live reads, allowlisted RPC |
| `POST /api/v1/compose` | `Project` | `ComposedCircuit` | No chain write |
| `POST /api/v1/compare` | `ComparisonRequest` | `ComparisonResult` | Worker-isolated SAT |
| `POST /api/v1/revalidate` | `Manifest` | `FreshnessResult` | Block-pinned chain read |
| `POST /api/v1/preflight` | `Candidate + Manifest` | `PreflightResult` | `eth_call`, fresh fee |
| `POST /api/v1/export` | `Project + Report` | streamed ZIP | Strict size checks, no untrusted filename paths |

**API status vs proof status:** HTTP `200` can contain `DIFFERENT` or `UNKNOWN` as a completed verification attempt; invalid schema → `422`; provider outage → `503`; hard resource breach → `429`/`422` or `200 UNKNOWN` according to frozen error contract. Do not conflate network status with proof truth.

**No arbitrary RPC proxy:** APIs accept circuit identities and limited configuration, never a user-provided arbitrary fetch URL. No CORS wildcard with credentials; no unsanitized full project logging; no executable content in uploaded bundles.

## 10. CLI contract and packaging

Recommended executable name: **`flip`**. Commands:

```text
flip sample --out sample.flip.json
flip inspect --processor 0x... --id 1 --format json
flip compose --project project.flip.json --out candidate.bin
flip compare --project project.flip.json --format json
flip preflight --project project.flip.json --format json
flip export --project project.flip.json --out proof.zip
flip verify-bundle --bundle proof.zip --format json
```

CLI output: JSON on stdout, diagnostics on stderr, `--json`/`--format json` deterministic by default for scripting. `--offline` supports pinned local fixtures but cannot mark current chain freshness. Define exit codes before M4: proposed `0` completed satisfactory match/equivalence, `1` valid DIFFERENT, `2` UNKNOWN/inconclusive, `3` invalid input, `4` RPC/infrastructure error, `5` internal bug; CLI machine JSON remains authoritative. `--help` documents these and no wallet commands exist.

`flip verify-bundle` checks artifact hashes and repeats locally available tests; it does **not** turn a single-RPC historical report into a fresh chain-verified one. Clean-machine native install tested on at least Linux + Windows if feasible; list tested platforms honestly.

## 11. Portable evidence bundle and schema

Recommended `flip-proof-v1.zip` contents:

```text
project.json
candidate.netlist.bin
reference.netlist.bin            # if available and permitted
manifest-candidate.json
manifest-reference.json          # if applicable
oracle.json                       # reference linkage or vectors
comparison.json
preflight.json                    # optional independent state
reproduction.md
SHA256SUMS
```

- Paths fixed; disallow zip-slip, symlinks, absolute paths and unbounded decompression.
- Evidence checksums cover raw content; archive file *byte determinism* requires pinned metadata (entry order, timestamps, compression options, encoding), tested on build pipeline. Canonical JSON/report hash determinism is the mandatory initial guarantee; archive byte determinism is a desired addition, not a proxy for correctness.
- Include the exact source and environment hashes plus engine/semantics/test-suite versions. Mark oracle trust assertions as user-declared where appropriate.
- Report historical evidence separately from current onchain freshness. Do not include secrets, access tokens or private data in default demo fixtures.

## 12. UI architecture and first-use product

Guided linear web flow **Start → Import → Compose → Compare → Evidence / Pre-flight**.

- Start: functional sample (`DIFFERENT` → corrected `EQUIVALENT`) with clear historical-pinned label, no wallet.
- Import: address + decimal ID, chain fixed at 196, source metadata + warnings and current/historical badge.
- Compose: explicit pin-mapping **table** as v1 design choice; optional graph visualization only after usability need. Show numbered pins and preview; no generic NAND editor.
- Compare: candidate/reference selector; vector mode; user-declared intent; solver budget; irreversible claiming forbidden.
- Results: verdict, freshness (separate), assumptions, replayable witness, explain output bits, source hashes, and export action.
- Pre-flight: separate structured status and fee-as-observed; no signing control.
- Session persistence: browser storage with schema migration, restore/recover/reset, quota-error handling; no accounts.
- Accessible semantics: keyboard support, labels, focus, error announcements, color-independent status.

## 13. Security test matrix (minimum)

| Threat/failure | Expected behavior |
|---|---|
| Wrong chain / Base address collision | Reject before import; manifest chain-bound |
| Beacon/implementation change with same netlist | Mark report stale; cannot claim fresh |
| Corrupt netlist / forward REF / unknown opcode | Reject prior to execution |
| Recursive REF cycle / deep closure / giant widths | Bounded failure, no server freeze |
| Inaccurate pin metadata | Mark user-asserted; never proof of intent |
| Solver crash/time/memory exhaustion | Kill/reap worker, `UNKNOWN`, preserve project |
| SAT witness mismatch with evaluator | `UNKNOWN` + critical internal error; block trusted DIFFERENT |
| Unknown pre-flight revert | `UNKNOWN`, never structural success |
| `eth_sendRawTransaction` or signer invocation | Regression test fails build; methods absent in runtime |
| Malicious ZIP artifact | Reject paths, size, expansion, hash mismatch |
| Untrusted RPC inconsistency | Mark unverifiable; do not assert malicious-RPC resistance |
| Server project exfiltration risk | Explicit web-processing disclosure; no retained user projects; CLI local alternative |

## 14. Verification/CI acceptance mapping

| PRD acceptance | Modules | Test owner |
|---|---|---|
| AT-01 sample miswire/fix | web, canary, export | Codex E2E + OpenCode sample fixtures |
| AT-02 live XOR/NAND import | chain, manifest | Codex + OpenCode frozen corpus tests |
| AT-03 cross-chain collision | chain, integrity | OpenCode tests / Codex implementation |
| AT-04 REF malicious/oversized | parser, refs | OpenCode hostile fixtures / Codex validation |
| AT-05 81-byte half-adder | composer, sim | Codex + OpenCode fixture assertions |
| AT-06 explicit oracle and vectors | schema, canary, UI | Codex + OpenCode test data |
| AT-07 SAT 28-case benchmark/7 safeguards | canary, worker | Codex + OpenCode independent benchmarks |
| AT-08 9 integrity mutations | manifest | OpenCode negative tests, Codex review |
| AT-09 CLI/web parity | cli, API, schemas | Codex integration, OpenCode parity harness |
| AT-10 burn pre-flight truth | preflight | Codex implementation, OpenCode fixture tests |
| AT-11 stateful P1 | sim, trace | Later, only after all P0 green |
| AT-12 stress/accessibility | all | OpenCode fixtures + Codex E2E |
| AT-13 user pilots | product research | Founder/community recruitment |
| AT-14 release readiness | release pipeline | Codex lead + OpenCode checklist |

## 15. Engineering work admission gates

- **M1:** Freeze schema/CLI/error contracts, clone golden fixture corpus and release reference data with hashes.
- **M2:** Chain reads and manifest revalidation verified on real X Layer; independent negative fixtures green.
- **M3:** Compose + SAT + witness replay; limits enforced in target worker environment.
- **M4:** Both CLI and public web flow, identical normalized artifact hashes, sample and export; pre-flight classification.
- **M5:** Adversarial suite, five-user pilot if available (report actual sample size), deployment/docs/demo, current hackathon rules verification; no unapproved chain spend.
- **M6:** P1 bounded trace only after M1–M5 accepted; cut if any P0 gate at risk.

## 16. Engineering decisions still requiring explicit verification

1. Confirm PySAT Minisat22 license and OS/container distribution constraints, including native wheel availability for target Python version.
2. Verify strict **64 MiB** per-verification worker enforcement on production host, accounting for interpreter and native runtime overhead. If impossible, change containment strategy through an ADR with measurable equivalent protection, or block public solver deployment; do not silently enlarge the approved logical budget.
3. Freeze exact TAP-02 bit packing against M0 official vectors before writing canonical external input schema.
4. Benchmark real target hardware/service and user-observed latency; M0.5 native scale numbers are not SLO promises.
5. Official hackathon requirement for submitted X Layer processor+circuit ID needs final independent verification and, if a **new** circuit is required, a separately authorized transaction outside the Flip MVP.

**No source report establishes current end-user demand.** Engineering success is measurable via tests; product usefulness requires external pilot evidence.
