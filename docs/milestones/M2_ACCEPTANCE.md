# Flip M2 combined acceptance

**Date:** 2026-11-18 (Africa/Lagos). **Integration owner:** Codex.
**Decision: M2 PASS — bounded importer/integrity milestone.**
**M3 readiness:** ready to begin scoped M3 engineering after integration review;
proof consumers must satisfy the explicit gates below before accepting results.
No M3 feature, composer, evaluator, SAT solver, UI, wallet or publication path was added.
This report does not authorize merging the PR without review or establish release readiness.

## Integrated revisions and ancestry

| Revision | Exact commit |
| --- | --- |
| Latest accepted main / merged M1 | `8e9b6b928b5d08b7383ae2413dec26d6068ea44e` |
| M2-A importer | `e5c47e55ff1600a62ef2cb96c19abb51b33d32f5` |
| M2-B corpus | `3cdbf14f59eb842f395da368e2e08d1f5708aa28` |
| Merge M2-A | `a9dc0f3f68ee59fd7a242d6b793869f9f4c28910` |
| Merge M2-B | `774d9f00db33b037107ce2f68f03e44e8529694a` |
| Combined checks and focused corrections | `6b5db5f7003bfa7a8b6b321addb2d2c0b543903b` |

Branch `codex/flip-m2-integration` was created from freshly fetched `origin/main`
in a dedicated `flip-m2-integration` worktree. Both source branches existed locally
and remotely at the requested commits. All existing worktrees were clean at inspection.
Both histories were merged with `--no-ff`; no conflicts, rebases, force pushes,
agent-branch overwrites or direct main changes occurred.

M2-B was authored from `5f8a04b`, the accepted M1 integration tree before PR #1
merged it as `8e9b6b9`. That is the common ancestor of the two agent branches and
an ancestor of accepted main. Its deviation is documented in the immutable M2-B
handoff; no history was rewritten to conceal it. M2-A is based on accepted main.

M2-B changed only `fixtures/m2-adversarial/` and `docs/evidence/m2-adversarial/`.
All eleven authored files retain exact Git/checkout bytes. Original raw evidence,
PRD, architecture, audit documents, AGENTS.md, `.gitignore`, frozen M1 models/
serialization and all v1/M2 JSON Schemas are unchanged. No wire-breaking correction
was required. New tests, verification config, narrow runtime fixes and this report
are owned by Codex.

## Combined validation

[Windows/Linux combined CI](https://github.com/Technique-S/Flip/actions/runs/44270238999)
passed for `6b5db5f`. The documentation-only acceptance commit is rechecked by the
same workflow; the PR exposes checks for its final head and proposed merge tree.

| Check | Actual outcome |
| --- | --- |
| Clean locked install | CPython 3.14.6, uv 0.9.11; new `.venv-clean`, cache disabled, non-editable workspace packages |
| Full Windows local pytest | **279 passed**, 33.81 s, no failures/errors/skips/xfails |
| Prior accepted coverage | All **217 prior cases** still execute and pass; no removed/skipped test |
| New corpus coverage | **50 distinct corpus IDs** execute: 18 TAP, 10 RPC, 18 integrity, 4 M1 regressions |
| Supplemental safety checks | **12** checks for regeneration/provenance, network isolation, aggregate budgets, computed expansion, repeated state/gates, cache fallback and ABI widths |
| Ruff lint / format | Pass; 28 maintained Python files formatted |
| Frozen v1 / M2 schemas | Generation/drift checks pass; schema files/models remain byte-identical to their accepted source revisions |
| Python/Node canonical parity | Existing Python assertions plus all six independent Node 24.18.0 vectors pass |
| CLI/API | Existing contract/import parity tests pass; real local ASGI smoke passes for canonical bytes, liveness, exit 6 / HTTP 501 gates |
| Fixture integrity/regeneration | Four registered corpus JSON files, generator digest and MANIFEST regenerate exactly in scratch; source bytes unchanged |
| Repository/provenance | Both histories retained; protected files, all 14 M1 registered blobs and all eleven M2-B authored files match their source Git bytes |
| Secret/binary review | Bounded tracked-text credential patterns found zero findings; no unexpected binary/key/archive files |
| Windows and Linux CI | Both clean-run jobs passed; no live RPC is necessary for either |

Installed imports were confirmed under `.venv-clean/Lib/site-packages`, not an
editable source path. [M2_CASE_RESULTS.json](M2_CASE_RESULTS.json) records every
corpus test node, outcome and inherited provenance label, extracted from actual
pytest JUnit output. Counts measure coverage, not proof of correctness by themselves.

### Preservation of prior tests

The initial merge ran **216 passed / one failed**. The failing historical-evidence
test assumed `fixtures/` would forever contain no JSON. It now permits only the
registered `fixtures/m2-adversarial/` namespace while retaining the prohibition
outside it. New independent hash/provenance/regeneration tests cover that namespace;
the historical missing NAND/composed manifests and REPORT_ONLY gaps remain absent.
This is the only prior test assertion adjusted, with the same test node retained.
Its reviewed Git-content SHA-256 is pinned in the repository checker:
`5f6cb596e5e669c4efe64fc270391768645bde6207a8fef4812e2040f4f9eaf2`.
All other baseline test files remain byte-identical to M2-A. No test was removed,
made a skip, marked xfail or changed to accept fabricated historical evidence.

The imported generator/verifier produced **78 initial Ruff findings**. Rather than
rewrite registered evidence, only those two exact archival-script paths were added
to the existing Ruff exclusion list. Maintained code is fully linted/formatted.
The unchanged generator is executed in scratch and its bytes/hash are checked.

## Verified defects and corrections

The first new acceptance run reproduced **five failures / 57 passes**:
TAP-MAL-008, RPC-002 and RPC-003 exposed missing-reference error classification;
two focused checks exposed late aggregate-budget enforcement.

1. **Missing-reference classification.** Empty expected contract code,
   unregistered processors, positive IDs beyond nextId and closed known
   `no circuit` lookup errors now use existing `MISSING_REFERENCE`. ID zero remains
   INVALID_INPUT. Malformed ABI/registration booleans remain INVALID_INPUT; unknown
   provider errors remain RPC_UNAVAILABLE. Remote error text is not echoed. The
   JSON-RPC lookup recognition is restricted to circuitInfo/netlist selectors,
   known error codes and exact known messages. No new error enum was introduced.
2. **Pre-allocation aggregate limits.** Once total bytes or records are exhausted,
   a child netlist is no longer fetched/decoded. Each next decode receives the
   remaining byte/record allowance, bounded by the original per-node allowance.
   Oversized dynamic-byte responses fail RESOURCE_LIMIT before byte allocation.
   Original defensive post-checks remain. Budgets and schema maxima were not raised.

The same targeted checks then all passed. Early new-code import/line-format
findings were corrected before the committed CI run. No remaining failure is
waived. One manual diff command used the M1 base for schemas first added by M2-A;
repeating against the correct M2-A revision confirmed no schema change.
uv's obsolete-distribution skip notices are not test failures.

### Safety review findings

- A memoized child retains its subtree height; deeper reuse cannot bypass depth 64.
- Expanded gate/state totals count every REF use, while closure identities/edges
  are unique. A positive repeated-LATCH case has two state bits/two gates but one
  dependency; understated state metadata is rejected.
- A shallow synthetic DAG with 1,251 uses of a four-gate child computes 5,004 gates
  and is rejected at the actual expansion check despite metadata claiming 5,000.
- Uint32 tuples, 160-bit addresses and exact ABI word lengths reject overflow and
  truncation. No integer truncation was found or introduced.
- Same-number/different-hash reads fail before a current result is produced. Old
  noncanonical blocks and changed dependency/implementation data make revalidation STALE.
- RPC failure does not read a cached result as fallback. Cache reads remain
  HISTORICAL/known STALE. Invalid/missing-reference imports leave no new cache entry.
- A root pytest guard blocks non-loopback DNS and sockets in the test process.
  Transport doubles never contact a provider; generator subprocesses are inspected
  stdlib-only scratch operations. This is not a claim of an OS-wide network sandbox.

## Cases executed and rejection reasons

The corpus's proposed error names are not all published v1 codes. Tests assert
actual frozen-compatible categories independently; fixture bytes and expectation
metadata were not edited to manufacture agreement. Error-envelope failures are
inconclusive import outcomes, not comparison verdicts.

### TAP-02 — 18/18

| IDs | Actual boundary and outcome |
| --- | --- |
| 001, 009–011 | Decoder: BAD_NETLIST, truncated record/header |
| 002 | Decoder: BAD_NETLIST, unknown opcode |
| 003 | Decoder: BAD_NETLIST, forbidden forward NAND/REF signal |
| 004 | Local decode executes and succeeds structurally; resolver then rejects BAD_NETLIST for target arity mismatch |
| 005, 012–014 | Decoder: BAD_NETLIST for out-of-range declared pin counts, before allocation; 014 also violates signal bounds |
| 006–007 | Decoder: BAD_NETLIST, too few produced outputs |
| 008 | Local decode executes and succeeds structurally; registered-target lookup then rejects MISSING_REFERENCE |
| 015 | Resolver: BAD_NETLIST with cycle reason; fixture's REF_CYCLE is mapped to the existing taxonomy |
| 016 | Resolver: REF_DEPTH_EXCEEDED at the 64-depth boundary; read budget is sufficient to reach that boundary |
| 017 | Declared 5,004-gate root: RESOURCE_LIMIT before netlist fetch/expansion |
| 018 | Transport hex validation: INVALID_INPUT for odd-length hex before decoding |

All fourteen formerly reference-decoder-safe cases execute against Flip's decoder.
Twelve are locally malformed; two require the registered REF/arity boundary as
shown. Archived reference reason strings/order are not Flip's wire contract: e.g.
case 014 can be rejected earlier for pin range without allocating a signal vector.

Case 017 is a **symbolic** 1,251-link pattern, not a complete encoded 5,004-gate
graph. We do not claim its unprovided full expansion was replayed. Its declared
budget is tested directly, and the separate shallow 5,004-gate multiplicity test
isolates the computed expansion guard without weakening depth 64. The original
long-chain recipe would also encounter depth limits; no cap is raised to run it.
Cases 015–018 were not executed by the archived verifier, but are executed now at
their correct Flip boundaries. Historical SKIPPED labels remain unchanged metadata,
not current passing-test labels. No current pytest case is skipped.

### RPC — 10/10

| ID | Outcome |
| --- | --- |
| 001 | WRONG_CHAIN before state/REF reads |
| 002 | Empty code -> MISSING_REFERENCE |
| 003 | Known no-circuit lookup revert -> MISSING_REFERENCE, not a provider outage |
| 004 | Truncated dynamic ABI -> INVALID_INPUT (fixture proposal INVALID_ABI_RESPONSE) |
| 005 | Inconsistent pinned hash -> IMPLEMENTATION_CHANGED; no cached current result |
| 006 | Synthetic ReadTimeout -> RPC_UNAVAILABLE after exactly three attempts at retry setting 2 |
| 007 | JSON-RPC rate-limit error -> RPC_UNAVAILABLE after one attempt; arbitrary retryAfterSeconds is not trusted or slept |
| 008 | Malformed hex -> INVALID_INPUT (fixture proposal INVALID_ABI_RESPONSE) |
| 009 | Changed beacon implementation -> STALE / BEACON_IMPLEMENTATION_CHANGED; old cache entry invalidated |
| 010 | Changed factory implementation -> STALE / FACTORY_IMPLEMENTATION_CHANGED; old cache entry invalidated |

Fixture method/storage labels are partly symbolic. Tests map them to the actual
read selectors/ERC-1967 slot and correlate response IDs to each generated request;
the original response payloads and on-disk fixtures are not rewritten. This is a
deterministic local specification test, not replay of a captured network transcript.

### Integrity — 18/18

| Archived ID | Mutation exercised and outcome |
| --- | --- |
| INT-NEG-01 | Wrong chain -> WRONG_CHAIN |
| 02 | Changed circuit ID with old content -> STALE, changed netlist/interface |
| 03 | Changed declared netlist hash -> STALE / NETLIST_CHANGED |
| 04 | Changed dependency identity/edges -> STALE / DEPENDENCIES_CHANGED |
| 05 | Changed factory slot -> STALE / FACTORY_IMPLEMENTATION_CHANGED |
| 06 | Changed beacon implementation -> STALE / BEACON_IMPLEMENTATION_CHANGED |
| 07 | Unexpected processor -> rejected missing reference |
| 08 | Old noncanonical block hash -> STALE / BLOCK_CHANGED |
| 09 | Changed supplied RPC netlist bytes -> STALE / NETLIST_CHANGED |

| Synthetic ID | Mutation exercised and outcome |
| --- | --- |
| INT-EXT-001 | Missing chainId -> INVALID_INPUT |
| 002 | Unprefixed code hash -> INVALID_INPUT |
| 003 | Same-number stale hash -> STALE / BLOCK_CHANGED |
| 004 | Dependency content hash change -> STALE / NETLIST_CHANGED |
| 005 | Declared hash versus supplied bytes mismatch -> ImportResult validation rejects |
| 006 | Duplicate closure identity -> INVALID_INPUT |
| 007 | Cross-chain reuse of the same address -> WRONG_CHAIN |
| 008 | Factory/beacon code-hash swap -> STALE / FACTORY_IMPLEMENTATION_CHANGED; distinct synthetic code identities prevent a vacuous identical-hash test |
| 009 | Truncated bytes with unchanged hash -> ImportResult validation rejects |

The nine archived records contain descriptions/issues rather than full mutated
input payloads. Tests instantiate those mutations on controlled local doubles;
they do not claim a fresh execution of the original Gate B checker or chain reads.

### M1 regressions — 4/4

- M1-REG-001: missing chainId is INVALID_INPUT; supplied invalid chains remain WRONG_CHAIN.
- M1-REG-002: crafted conclusive report with an empty self-declared map cannot
  unlock the proof consumer: HTTP 501 / NOT_IMPLEMENTED.
- M1-REG-003: empty or unrecognized revert data cannot unlock structural preflight:
  HTTP 501 / NOT_IMPLEMENTED.
- M1-REG-004: float chainId is exactly INVALID_INPUT at the canonical-JSON boundary;
  the distinction is explicitly documented in the existing M2 interface decision.

The v1 shape validator's permissiveness for self-declared proof/preflight fields
remains visible in tests. A shape pass is not a trusted-consumer pass. No frozen
wire contract was silently tightened, and no unavailable consumer is represented
as implemented. M3/M4 must bind and verify actual evidence before enabling them.

## Provenance, skipped scenarios and residual risks

Four registered corpus byte hashes match M2-B's MANIFEST; generator SHA-256 is
`f6860d7d82ee34c66a46e93c272f3a28197d8dcbdd9ccf687e3dd67b6dd0f73c`.
All fixture JSON plus MANIFEST regenerate byte-for-byte in disposable scratch.
The eleven M2-B authored files, nested byte-preserving attributes, twelve original
raw artifacts and two original derived files are unchanged.

Archived provenance remains copied-byte integrity only: canonical audited
`C:\research\circuitforge-feasibility\...` experiment directories are absent.
SYNTHETIC/MOCK/EXTENSION and SPEC_ONLY labels remain labels, never upgraded to
onchain observations. M2-B's statements about an unimplemented importer and old
M1 behavior describe its historical base, not the current accepted software.

**No new live RPC smoke was run for M2-C.** M2-A's captured block-76206482 imports
remain historical. Synthetic transport tests can exercise a CURRENT code path,
but are not current chain evidence. No evaluator/solver/witness replay, full
18-vector semantic parity, signing, transaction or publication is claimed.

The archived verifier script is preserved, not rerun to overwrite its historical
transcript: it depends on an external machine path and probes older M1 behavior.
Its portable regeneration function is covered by the unchanged generator in
scratch; Flip's actual decoder/resolver/transport/consumer gates replace the old
nonportable decoder probe. This is not a skipped current acceptance case.

Remaining risks/gates:

- Number-pinning plus header rechecks is not atomic EIP-1898 state access, finality
  or resistance to a dishonest single RPC operator.
- Deadlines are cooperative and I/O-phase bounded, not OS kill guarantees;
  public-service rate controls and hard solver isolation remain later gates.
- Cache reads are historical/known stale, not a global chain monitor. Every
  manifest must be freshly revalidated before a current claim.
- M3 must hash-resolve actual projects/manifests, bind reference/candidate
  identities and real I/O widths/mappings, and independently reproduce witnesses.
  Self-declared flags cannot stand in for those checks, including zero-input cases.
- M4 must obtain fresh fee/implementation observations and recognize/decode actual
  nonempty revert evidence. Unknown/empty errors must remain UNKNOWN.
- Source licensing and native solver distribution/containment decisions remain
  unresolved release requirements. No M0.5 ceiling or exclusion is relaxed.

No unresolved critical importer/integrity defect requiring a schema break was
found. These remaining gates limit downstream readiness rather than being waived
by the M2 PASS decision. Main is unchanged pending PR review and approval.

## Reproduction

Full Git history, Python 3.14.6, uv 0.9.11 and Node 24.18.0 are required.
Windows commands below were actually executed from the integration worktree
(the pinned uv executable initially came from the adjacent Codex bootstrap):

```powershell
python -m venv .bootstrap
.\.bootstrap\Scripts\python.exe -m pip install uv==0.9.11
$env:UV_PROJECT_ENVIRONMENT = '.venv-clean'
.\.bootstrap\Scripts\uv.exe sync --locked --no-cache --no-editable
Remove-Item Env:UV_PROJECT_ENVIRONMENT
.\.venv-clean\Scripts\python.exe -m pytest -q --tb=short --junitxml=.bootstrap/M2_C_RESULTS.xml
.\.venv-clean\Scripts\ruff.exe check .
.\.venv-clean\Scripts\ruff.exe format --check .
.\.venv-clean\Scripts\flip-schemas.exe --out docs/schema/1.0.0 --check
.\.venv-clean\Scripts\python.exe -m flip_core.import_schema_export --out docs/schema/m2/1.0.0 --check
node docs/schema/check-canonical.mjs
.\.venv-clean\Scripts\python.exe scripts/smoke_m1.py
.\.venv-clean\Scripts\python.exe scripts/check_m1_repository.py --require-clean
git diff --check
git status --porcelain
```

Use `.venv-clean/bin/` and `.bootstrap/bin/` on Linux. The adversarial suite alone
is `python -m pytest packages/flip-core/tests/test_m2_corpus.py -q`. Regeneration is
part of that suite and writes only scratch copies. Do not run the historical
generator/verifier in place and overwrite the archived corpus/evidence.
