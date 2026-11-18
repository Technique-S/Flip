# Flip M2-C — independent importer acceptance review

**Role:** supporting verification engineer (OpenCode / HY4 Flash). **Branch:** `opencode/flip-m2-independent-review`.
**Review type:** read-only, offline, mocked-transport execution. No production code, schema, CI, config or Codex branch was modified. No merge; no live RPC, signing, transaction or publication.

## 0. Revision actually tested

| Item | Commit |
|---|---|
| Implementation under review (`codex/flip-m2-import-integrity`) | `e5c47e55ff1600a62ef2cb96c19abb51b33d32f5` |
| Implementation change | `0c26ab7aebba0269b41a05de657578bdb2ba6075` |
| M1 merge base | `8e9b6b928b5d08b7383ae2413dec26d6068ea44e` |
| M2-B fixture corpus used as input | `3cdbf14f59eb842f395da368e2e08d1f5708aa28` |
| M1 independent review (earlier) | `0b440e5a37f402ababd3079ff558de1c6b2e23f4` |

**Target branch availability and mid-review update:** `codex/flip-m2-integration` did **not** exist when this review started, so I reviewed `codex/flip-m2-import-integrity` at `e5c47e5` as instructed. The integration branch **became available during the review** at `0a89282f878dfaff8314fe375c780b9fd0d01bda` (merges M2-A at `e5c47e5` and M2-B at `3cdbf14`, plus fix commit `6b5db5f`). I therefore performed the required follow-up read-only check against `0a89282` and report both results below. `e5c47e5` is an ancestor of `0a89282`. No claim is made about any other commit.

## 1. Inspection summary (Task A)

- **RPC adapter** (`rpc.py`): allowlisted methods/selectors, identity + envelope + id checks, response/byte/deadline bounds, at most `retries+1 <= 3` attempts, 429/5xx retry only.
- **ABI decoder** (`abi.py`): strict 32-byte words, 160-bit addresses, four uint32 `circuitInfo` words, exact offset/length/padding for dynamic bytes.
- **TAP-02 decoder** (`tap02.py`): bounded record loop, NAND/LATCH/REF layouts, backward-reference check, signal/gate/state ceilings, no evaluator.
- **REF resolver** (`importer.py`): number-pinned session, cycle path detection, memoized nodes with height accounting, per-use gate/state summation, arity and metadata cross-checks.
- **Integrity engine** (`integrity.py`): content-addressed 16-entry/8 MiB cache that always downgrades reads to HISTORICAL/STALE, full-closure revalidation with deterministic change categories.
- **Cache invalidation**: `mark_stale` on changed revalidation; noncanonical old block yields BLOCK_CHANGED.
- **CLI/API**: versioned import/inspect/revalidate routes, server-controlled RPC config, two-job semaphore, canonical JSON; compare/compose/preflight remain 501 / exit 6.
- **New schemas**: three additive `1.0.0` contracts (ImportResult, RevalidationResult, ImportBudget); six M1 schemas untouched.
- Compared against `MVP_CONSTRAINTS.md` §1–§9 and the M2-A/M2-B handoffs. No M0.5 limit was relaxed; no proof/preflight claim was added.

## 2. Commands actually executed

```powershell
# review branch created from e5c47e5; M2-B fixtures imported from 3cdbf14 into owned dirs
git switch -c opencode/flip-m2-independent-review e5c47e5
git checkout 3cdbf14 -- fixtures/m2-adversarial docs/evidence/m2-adversarial

# existing suite, read-only, clean non-editable install in the Codex M2 worktree
PYTHONDONTWRITEBYTECODE=1
cd flip-m2
.venv-clean\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=<review>\.m2-review-tmp --tb=short

# independent harness against the installed implementation
.venv-clean\Scripts\python.exe <review>\docs\evidence\m2-independent-review\harness.py
```

The harness constructs `httpx.MockTransport` responses, drives the real `ImportService`, `RpcClient`, `tap02.decode`, `ContentCache`, FastAPI `TestClient` and CLI subprocess. Transcripts: `docs/evidence/m2-independent-review/results_e5c47e5.json` and `results_0a89282.json` (the harness writes `results.json` by default; each run was copied to the commit-specific name above).

Follow-up against the integration branch (same read-only commands, `flip-m2-integration` worktree and its clean venv):

```powershell
cd flip-m2-integration
.venv-clean\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=<review>\.m2-intg-tmp --tb=short
.venv-clean\Scripts\python.exe <review>\docs\evidence\m2-independent-review\harness.py
```

## 3. Tests passed / failed / skipped

- **Existing M2 suite at `e5c47e5`:** `217 passed in 28.06s`, exit 0, no warnings.
- **Existing suite at integration `0a89282`:** `279 passed in 30.39s`, exit 0 (217 baseline + 62 new corpus checks). Both Codex worktrees stayed clean.
- **Independent harness:** 26 checks — **23 PASS, 0 FAIL, 3 INFO** at *both* `e5c47e5` and `0a89282`. The newer commit changed one observed code: `RPC-002` (empty contract code) now returns `MISSING_REFERENCE` instead of `INVALID_INPUT`, aligning with the M2-B fixture. All other check outcomes are unchanged.
- **Passed checks:** wrong-chain rejected before state reads (`methods == ["eth_chainId"]`); RPC failure corpus all produced structured `ContractError`; budgets for gates/netlist bytes/requests; cycle rejection (`BAD_NETLIST`, “cycle”); 66-node chain rejected at depth 65 with cap 64; dependency netlist mutation → `NETLIST_CHANGED` + `STALE`; cache read → `HISTORICAL`, after revalidation → `STALE`; missing chainId → `INVALID_INPUT` (M1 F-01 corrected); API compare/preflight/compose → 501 and CLI compare → exit 6; proof flags and empty-revert claims do not unlock consumers; ≤3 attempts on forced 503; block-hash change → `IMPLEMENTATION_CHANGED`; factory/beacon implementation changes detected on revalidation; tampered caller manifest not trusted.
- **Skipped by design:** TAP-MAL-018 odd-length hex (cannot become bytes); TAP-MAL-004/008/015/016/017 decode as structurally valid single netlists and require resolver/expansion semantics (covered by dedicated importer checks above, not by `decode` alone).

## 4. Findings

No Critical or High defect was reproduced.

### F-1 — Low — JSON-RPC application errors collapse into `RPC_UNAVAILABLE`
`rpc.py` maps any JSON-RPC `error` object to `ValueError("RPC error")` → `ContractError("RPC_UNAVAILABLE")` (CLI 4 / API 503). A deterministic application outcome such as `{"error":{"code":-32000,"message":"no circuit"}}` is therefore indistinguishable from a transport outage.
**Reproduction:** M2-B fixture `RPC-003` through `ImportService` → `ContractError(code="RPC_UNAVAILABLE")`; Codex's own `test_missing_ids_rejected` asserts only that *some* `ContractError` is raised.
**Impact:** clients cannot tell “missing circuit” from “RPC down”, and a deterministic absence is reported as infrastructure failure rather than `UNKNOWN`/structured rejection. `MVP_CONSTRAINTS.md` §5 reserves UNKNOWN for inconclusive conditions.
**Recommendation:** classify known revert selectors / `-32000` application errors separately from transport failures; at minimum document the current mapping in `docs/schema/m2/README.md`.

### F-2 — Informational — M2-B fixture error-code expectations differ from implementation taxonomy
At `e5c47e5`: `RPC-002` `INVALID_INPUT` vs expected `MISSING_REFERENCE`; `RPC-003` `RPC_UNAVAILABLE` vs `MISSING_REFERENCE`; `RPC-004`/`RPC-008` `INVALID_INPUT` vs `INVALID_ABI_RESPONSE`; `RPC-009` accepted on a fresh import (implementation changes are only detectable against a pinned prior manifest, which revalidation correctly reports). At integration `0a89282`, `RPC-002` was corrected to `MISSING_REFERENCE`; remaining differences are `RPC-003`, `RPC-004`, `RPC-008` and the fresh-import/revalidation distinction. These are design choices, not failures.
**Recommendation:** align the remaining fixture `expected_outcome.code` values with the frozen M2 taxonomy; keep fresh-import vs revalidation semantics explicit.

### F-3 — Informational — Depth-cap boundary semantics are ambiguous
`importer.resolve` rejects only when `depth > maxDepth`. With `maxDepth=64`, a chain of 65 nodes (64 REF edges, terminal node at depth 64) is accepted; a 66-node chain (depth 65) is rejected. M2-B fixture `TAP-MAL-016` describes a “65-link chain” as one link beyond the cap. Both readings are defensible because `MVP_CONSTRAINTS.md` §6 calls 1,250 chained REFs a “linear chain depth 1,250” (edges).
**Recommendation:** define “depth” explicitly as REF-edge count in the M2 schema README and align fixture wording; no production change is implied if 64 REF edges is intended.

### F-4 — Resolved — Integration branch reviewed after appearing mid-review
`codex/flip-m2-integration` became available at `0a89282` during this review. The follow-up read-only check was executed: 279 tests passed and the harness reported 23 PASS / 0 FAIL. No new blocking issue was introduced by the merge or the `6b5db5f` fix. If Codex moves the branch again, a further short re-check is needed; this report is valid for `0a89282`.

## 5. Source and evidence limitations

- All import checks used mocked JSON-RPC responses; no live X Layer read was performed in this review. Codex's separately recorded live smoke is historical evidence, not reproduced here.
- The canonical original audit directories remain unavailable; imported M0/M0.5 data retains copied-byte provenance only.
- The M2-B corpus used here is my own earlier design specification (`3cdbf14`), not Codex-frozen tests; its expected codes are proposals (F-2).
- No claim of circuit semantic correctness, equivalence, solver replay, malicious-RPC resistance, publication or release readiness is made. Structural import produces observations only.

## 6. Required fixes / follow-ups

1. Decide and document JSON-RPC error classification for application reverts (F-1).
2. Align remaining M2-B fixture expected codes with the frozen M2 taxonomy (F-2).
3. Define depth semantics and align fixture wording (F-3).
4. Re-check only if `codex/flip-m2-integration` moves beyond `0a89282` (F-4).

## 7. Acceptance recommendation

**Accept the M2 combined implementation at integration commit `0a89282` for the engineering gate.** Both the implementation-only commit `e5c47e5` (217 tests) and the integration head `0a89282` (279 tests) pass their suites, and all 23 independent adversarial checks pass at both heads through actual invocation of `ImportService`, the decoder, cache, API and CLI. Resource ceilings, cycle/depth bounds, chain binding, cache freshness downgrade, dependency invalidation, corrected missing-chainId classification and blocked proof/preflight consumers were observed directly. No Critical or High issue was found. F-1–F-3 are documentation/conformance alignments, not blockers. This is not acceptance of live chain truth, circuit semantics, solver proof, preflight, malicious-RPC resistance or release readiness. This review performed no production edits and merged nothing into `main`.

End of M2-C review.
