# Flip M2-B — adversarial import fixtures and test design handoff

**Role:** independent supporting verification engineer (OpenCode / HY4 Flash).
**Branch:** `opencode/flip-m2-adversarial-fixtures`. **Base:** accepted combined M1 integration commit `5f8a04bded526a4d47fddf7c2893ade485fe6940`.
**Scope:** fixtures and evidence only. No production package, schema, lockfile, CI config, Codex branch or archived raw fixture was modified. No merge; no transaction, signing or live RPC.

## 0. Base-commit note

The task said to start from "accepted merged M1 main". At branch creation `main` was still the seed commit `37c39b3cf06edad908a6c579b7b0a78f1b42c202`; the accepted M1 work (M1-A `6dc21e0`, M1-B `e4de86e`, integration checks, `M1_ACCEPTANCE.md`) is on `codex/flip-m1-integration` at `5f8a04b`. I based this branch on `5f8a04b` so the frozen contracts and immutable evidence are present, and I did not alter `main`. This deviation is intentional and recorded.

## 1. Fixture inventory

All artifacts are under `fixtures/m2-adversarial/`. Generator: `docs/evidence/m2-adversarial/build_corpus.py` (stdlib only). SHA-256 values are over exact file bytes (see `MANIFEST.json`).

| File | Bytes | SHA-256 | Cases | Purpose |
|---|---:|---|---:|---|
| `tap02-malformed.json` | 33,160 | `f40900cf151471bbfaff344c297322f048b3e339514f512775e30754e7b3d65c` | 18 | Task A: deterministic malformed TAP-02 netlists |
| `rpc-failures.json` | 8,352 | `1aa1aface3e080bcbfdd07b468f3a178018d93f5ffea0660f1c85f2f458dc609` | 10 | Task B: mocked JSON-RPC failure responses |
| `integrity-negatives.json` | 8,990 | `cd770d0e24c0156464b1dc7959f7765f41233969683efb414d95d143e49cd7ea` | 18 | Task C: archived nine plus nine synthetic extensions |
| `m1-regressions.json` | 4,170 | `15ac9ab3f972ecdb0014a5920001a32919970211667f0e734c381bb53053b605` | 4 | Task D: regression specifications for M1 findings |
| `MANIFEST.json` | 1,078 | — | — | Generated hash/size register |
| `.gitattributes` | 74 | — | — | `* -text` to preserve fixture bytes on all platforms |

Supporting evidence: `docs/evidence/m2-adversarial/{build_corpus.py,verify_corpus.py,corpus_verification.json,.gitattributes}` and this handoff.

## 2. Expected behavior and spec references

### Task A — TAP-02 malformed corpus (18 cases)

Each case records `nIn`, `nOut`, `netlist`, `netlist_bytes`, `netlist_sha256`, optional `refs`/`resolver`, `expected_outcome`, `spec_reference`, `provenance`, and an execution label.

| IDs | Category | Expected outcome | Spec reference |
|---|---|---|---|
| 001 | truncated netlist | reject `truncated record` | TAP-02 §3 / `decode()` |
| 002 | invalid opcode | reject `unknown opcode 0x03` | TAP-02 §3 |
| 003 | future signal reference | reject signal-not-available | TAP-02 §3 backward-reference rule |
| 004 | invalid REF arity | reject `REF arity does not match the target circuit` | TAP-02 §3 / `load()` |
| 005–007 | incorrect input/output counts | reject `nIn/nOut out of range` or `too few signals for outputs` | TAP-02 §3 |
| 008 | unregistered REF target | reject not-a-registered-processor | TAP-02 §3; MVP_CONSTRAINTS §4 |
| 009–011 | invalid REF header encoding (cpu 10/20 bytes, cid 3/8 bytes, missing ni/no) | reject `truncated record` | TAP-02 §3 REF record layout |
| 012–014 | excessive declared counts (nIn 65537, nOut 65537, nIn 2^24) | reject range/signal overflow **before allocation** | TAP-02 §3 MAX_PINS/MAX_SIGNALS |
| 015 | recursive dependency cycle (A→B→A) | bounded reject `REF_CYCLE` | MVP_CONSTRAINTS §3; M1 `refDepthCap ≤ 64` |
| 016 | 65-link REF chain | bounded reject `REF_DEPTH_EXCEEDED` (cap 64) | MVP_CONSTRAINTS §3/§6 |
| 017 | 1,251-link chain → 5,004 expanded gates | bounded `RESOURCE_LIMIT` / verdict `UNKNOWN`, never EQUIVALENT | MVP_CONSTRAINTS §5/§6 |
| 018 | odd-length hex byte string | reject `INVALID_INPUT` before decoding | flip-json-v1 `HexBytes`; `models.py` |

### Task B — RPC failure fixtures (10 cases)

All are `SYNTHETIC_MOCK`, `not_an_observation: true`, `no_keys_or_signing: true`: wrong chain ID (0x2105), empty code (`0x`), missing circuit (`no circuit`), invalid ABI (`0x01`), inconsistent same-block hash, 8 s timeout, rate limit (retry-after 5), malformed hex (`0xzz`), changed beacon implementation, changed factory implementation. Expected codes: `WRONG_CHAIN`, `MISSING_REFERENCE`, `INVALID_ABI_RESPONSE`, `IMPLEMENTATION_CHANGED`, `RPC_UNAVAILABLE`/`UNKNOWN`. Specs: MVP_CONSTRAINTS §1, §3–§7 and M0 Gate B negative taxonomy. Pinned comparison values come from the archived `gate_b_manifest.json` and are labelled historical, not fresh.

### Task C — Integrity negatives (18 cases)

Nine `ARCHIVED_OBSERVATION` records reproduce `gate_b_negative.json` verbatim (wrong chain 8453, changed circuit ID, changed netlist hash, changed REF dependency, changed factory slot, changed beacon impl, unexpected processor, stale block, inconsistent RPC bytes; `allNegativeDetected: true`). Nine `INT-EXT-00x` `SYNTHETIC_EXTENSION` cases add: missing chainId, unprefixed code hash, stale block hash, dependency hash change, bytes-vs-hash inconsistency, duplicate closure identity, cross-chain address reuse, factory/beacon hash swap, truncated netlist bytes. Each synthetic case states `expected_outcome.code` and `not_an_observation: true`.

### Task D — M1 regression specifications (4 cases)

`M1-REG-001` missing chainId should be `INVALID_INPUT` (currently `WRONG_CHAIN`); `M1-REG-002` conclusive report must bind map widths to referenced artifacts (currently a vacuous `inputMap=[]` report is accepted); `M1-REG-003` empty `revertData` must not yield `STRUCTURALLY_ACCEPTED` (currently accepted); `M1-REG-004` float chainId taxonomy must be exact or explicitly documented. All are `SPEC_ONLY_NOT_PASSING_AGAINST_FROZEN_M1`; no frozen schema was changed.

## 3. Provenance classification

| Class | Meaning | Applied to |
|---|---|---|
| `ARCHIVED_VECTOR` / `ARCHIVED_OBSERVATION` | Exact record from committed immutable M1-B evidence; bytes not modified | TAP cases 001–008; nine integrity negatives |
| `SYNTHETIC` / `SYNTHETIC_EXTENSION` / `SYNTHETIC_MOCK` | Constructed deterministically by this task; **not** a chain observation or audit result | TAP cases 009–018; RPC cases; nine integrity extensions |
| `SPEC_ONLY` | Regression specification derived from M1 independent review `0b440e5`; no new claim of observed behavior | four M1 regression cases |

Historical pinned values (factory/beacon implementation, slots) are sourced from committed `gate_b_manifest.json` and retain the inherited `RAW_REPLAYED` provenance label: copied-byte integrity only, not fresh execution or verified original chain of custody. The canonical `C:\research\circuitforge-feasibility\...` originals remain absent.

## 4. Test commands actually executed

```powershell
# from the opencode worktree, on branch opencode/flip-m2-adversarial-fixtures
$env:PYTHONDONTWRITEBYTECODE='1'
python docs\evidence\m2-adversarial\build_corpus.py
& 'C:\Users\Kazi\Documents\Flip\Flip_M1_Engineering_Starter\flip-integration\.venv\Scripts\python.exe' `
    docs\evidence\m2-adversarial\verify_corpus.py
```

Verification script operations: (1) compare each fixture byte length and SHA-256 to `MANIFEST.json`; (2) copy authored tree plus immutable raw evidence into a temporary scratch tree, re-run the generator there and require byte-identical outputs; (3) import the archived `tap02_reference.py` read-only and call `load()` for cases labelled `reference_decoder_safe`; (4) probe current frozen-M1 behavior for the three behavioral regressions; (5) bounded credential-pattern scan. Transcript: `corpus_verification.json`.

## 5. Actual outcomes

- **Hash/size register:** 4/4 artifacts match `MANIFEST.json`; `all_hashes_match: true`.
- **Determinism:** `exact_regeneration: true`, no differing files.
- **Archived decoder checks:** 14/14 safe cases raised `IllFormed`; all 14 `reason_prefix_match: true` (e.g. `truncated record at byte 4`, `unknown opcode 0x03 at byte 0`, `REF arity does not match the target circuit`, `more than 2^24 signals`). This is an **offline decoder reason check**, not an M2 importer test.
- **Intentionally not executed:** `TAP-MAL-015` (no cycle guard in archived decoder), `TAP-MAL-016` (deep resolution), `TAP-MAL-017` (oversized expansion), `TAP-MAL-018` (not decodeable to bytes). Their expected outcomes remain specifications.
- **Current frozen-M1 baseline:** `M1-REG-001` → `WRONG_CHAIN` (undesired), `M1-REG-002` → `ACCEPTED` (undesired), `M1-REG-003` → `ACCEPTED` (undesired). Recorded as baseline evidence, **not** as passing tests.
- **Secrets/size:** 0 credential-pattern hits; largest fixture 33,160 bytes; no keys, signing material or binaries.
- **No integrated M2 tests were run.** There is no implemented importer/integrity engine; no claim of integrated pass, RPC verification, solver execution or chain observation is made.

## 6. Unresolved findings and limits

1. M2 importer and integrity engine are not implemented; every `expected_outcome` is a design contract awaiting Codex implementation.
2. The archived reference decoder has no cycle guard, depth cap or expansion budget; cases 015–017 cannot be reproduced offline and must be enforced by M2 code.
3. M1 review findings F-01, F-02 and F-04 remain present in the frozen contracts; the regression specs are not passing and need a controlled contract revision.
4. RPC fixtures use symbolic method names (`circuitInfo(uint256)`, etc.); exact selectors and ABI decoding remain a Codex adapter responsibility.
5. Archived vectors/negatives are local copies of unavailable canonical originals; provenance is copied-byte integrity, not fresh chain truth. No live RPC was contacted.
6. No CI configuration was changed; wiring these data-driven cases into CI is a Codex task.

## 7. Recommendations for Codex

- Implement the TAP-02 decoder with explicit cycle detection, `refDepthCap ≤ 64` and a pre-allocation expanded-gate budget; use cases 001–018 as the negative suite and require the recorded reject reasons.
- Add an RPC response validator producing `WRONG_CHAIN`, `MISSING_REFERENCE`, `INVALID_ABI_RESPONSE`, `IMPLEMENTATION_CHANGED` and `UNKNOWN` for timeout/rate-limit; never map a timeout to EQUIVALENT.
- Make the integrity checker rebind chainId, pinned block hash, environment hashes, closure uniqueness and `netlistHash` vs raw bytes; the nine extensions target exactly those gaps.
- Resolve M1 F-01/F-02/F-04 in a versioned contract revision, then enable the four regression specs as real tests.
- Wire `fixtures/m2-adversarial/*.json` into a data-driven CI test in a Codex-owned test directory; keep the local `.gitattributes -text` rules so bytes remain identical on both OSes.

End of M2-B deliverables. No merge into `main`.
