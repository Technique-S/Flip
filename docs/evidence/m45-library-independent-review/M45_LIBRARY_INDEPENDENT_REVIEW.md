# M4.5-2L — Independent circuit library review

**Role:** independent supporting verification engineer (OpenCode / HY4 Flash).
**Tested SHA:** `dec9420bb76e9245c6740bf3d92031d175e408ec`
(`codex/flip-m45-circuit-library`, verified equal to the remote branch head at task time).
**Review branch:** `opencode/flip-m45-library-independent-review`, created from the tested
SHA. No production package, frontend, schema, lock, CI file, existing fixture or Codex
branch was edited. No signing, wallet, broadcast, payment or intentional live chain call.

Severity scale: CRITICAL / HIGH / MEDIUM / LOW / INFORMATIONAL.

## 1. Executive result

**Acceptance recommendation: CONDITIONAL PASS.** The catalog cannot grant transaction
authority: there is no executable flag in a library record, every import/revalidation
re-enters the M2 importer, injected authority fields are rejected by schema validation,
and failed revalidation produces no trusted composition input. No CRITICAL or HIGH finding
and no authority-bypass path was found. Two user-visible issues (one MEDIUM, one LOW) and
test/reproduction caveats should be tracked by Codex.

| Severity | Count | Findings |
|---|---:|---|
| CRITICAL | 0 | none |
| HIGH | 0 | none |
| MEDIUM | 1 | F-01 corrupted persisted catalog disables known-address fallback |
| LOW | 2 | F-02 favorite-only record trust label; F-03 scratch-regeneration test timeout |
| INFORMATIONAL | 4 | I-01 build precondition; I-02 dependency install precondition; I-03 cursor replay; I-04 harness-side endpoint correction |

## 2. Executed commands

From `C:\Users\Kazi\Documents\Flip\repo` (CPython 3.14.6, Node 24.18.0, pinned `.venv`):

```powershell
# baseline repository suites
.venv\Scripts\python.exe -m pytest -q --junitxml=fixtures/m45-library-independent-review/results/pytest-baseline.xml -o junit_family=legacy
.venv\Scripts\python.exe -m pytest -q packages/flip-core/tests/test_m1_integration.py::test_report_only_gaps_are_not_executable_golden_fixtures packages/flip-core/tests/test_m3_acceptance.py::test_custody_and_scratch_regeneration -o junit_family=legacy

# independent production harnesses (OpenCode-owned doubles)
.venv\Scripts\python.exe fixtures/m45-library-independent-review/harness/independent_core_checks.py
.venv\Scripts\python.exe fixtures/m45-library-independent-review/harness/independent_cli_api_checks.py
node fixtures/m45-library-independent-review/harness/browser_observations.mjs

# browser suites, after restoring the locked install and rebuilding the bundle
cd apps/web
npm ci
npm run build
npm test -- --reporter=list
```

Captured outputs are registered in
`docs/evidence/m45-library-independent-review/RESULTS_MANIFEST.json`
(15 tracked files: harnesses, logs, JSON observations and two screenshots; generated
bytecode is excluded).

## 3. Passed / failed / skipped

### 3.1 Independent core production checks — 24 executed, 0 harness errors

`independent_core_checks.py` calls the real `LibraryService.execute` with an
OpenCode-owned `httpx.MockTransport` double. Full observations:
`results/independent-core-checks.json`.

| ID | Scenario | Observed |
|---|---|---|
| A01 | Bounded processor enumeration | First page `PARTIAL_BOUNDED`, cursor offset `2`, two records; second page completes; 3 `cpuAt` reads |
| A02 | Sparse circuit IDs | `COMPLETE_WITH_GAPS`, `missingIds=["3"]`, no fabricated record for the gap |
| A03 | Search by address, ID and alias | 1 address match, 7 ID-token matches, 1 alias match |
| A04 | Hostile onchain display metadata | Bidi/control characters removed; normalized name displayed |
| A05 | Favorites and recents | Favorite stored; import `COMPLETE` with `imported` payload; 1 recent retained |
| A07 | Beacon implementation change | Revalidation `ENVIRONMENT_CHANGED` / `IMPLEMENTATION_CHANGED`, record `STALE`, no import produced |
| A08 | Failed revalidation | `VERIFICATION_FAILED` / `MISSING_REFERENCE`, `importProduced=false` |
| A09 | Partial discovery and RPC outage | Outage `UNKNOWN` / `RPC_UNAVAILABLE`, prior snapshot retained, no new records committed |
| A10 | HTTP 429 rate limiting | `COMPLETE` with `retriesUsed=2`, bounded calls |
| A11 | Cursor ownership | Different-scan cursor rejected `INVALID_INPUT`; see I-03 |
| B01 | Wrong-chain provider (8453) | `WRONG_CHAIN` before state reads |
| B02 | Malformed `cpuCount` ABI | `INVALID_INPUT`, `UNKNOWN`, no trusted records |
| B03 | Incorrect/huge `cpuCount` | `PARTIAL_BOUNDED` with cursor; no unbounded scan |
| B04 | Duplicate processor addresses | Single canonical record per `(chain, factory, processor)` |
| B05 | Large `nextId` (2^64) | `UNKNOWN` / `INVALID_INPUT` with 17 bounded calls; no unbounded claims |
| B06/B07 | Factory / beacon implementation change between pages | Page-two invalidation, stale records, no trusted commit |
| B08 | Reorg between pages | Block-identity mismatch handling exercised; no trusted commit |
| B09 | Markup + authority fields in user metadata | `extra_forbidden` validation rejection; no authority field accepted |
| B10 | Corrupted persisted favorites | `ValidationError` at model boundary |
| B11 | Cross-network / cross-project identity | Both rejected at model boundary |
| B12 | Selector custody | All nine compared production selectors equal independently verified values |
| B13 | Registered fixture custody | 19 fixture files, zero hash mismatches |
| B14 | Favorite-only provenance | See F-02 |

### 3.2 CLI/API parity — passed

`independent_cli_api_checks.py` invoked the real `flip library` CLI subprocess and the
real FastAPI route against the same loopback double: CLI exit `0`, both `PARTIAL_BOUNDED`,
normalized shapes identical, catalog persisted, invalid operation `422`, corrupt catalog
`422` with `INVALID_INPUT`. See `results/independent-cli-api-checks.json`.

### 3.3 Browser — 14/14 Playwright tests passed after build

Initial run without rebuilding served a stale bundle: 4 passed / 10 failed (Library
button absent). After `npm ci` + `npm run build`, all 14 passed, including L01–L03 library
journeys, axe checks, keyboard and 390px viewport. Log:
`results/browser-playwright-after-build.log`. This is a precondition, not a product defect
(I-01, I-02).

### 3.4 Repository baseline — partially passed

Full suite: **533 passed, 2 failed** (`results/pytest-baseline.log`). The first failure
was caused by this review's initial evidence JSON placed under `fixtures/`, which a
production custody test scans; after moving evidence to `docs/evidence/`, the targeted
rerun of that test passed. The remaining failure,
`test_custody_and_scratch_regeneration`, is a 120 s subprocess timeout (F-03). No library
test failed.

### 3.5 Skipped / not executable here

Human screen-reader review, real hardware key handling, live provider honesty,
multi-operator agreement and actual transaction publication were not performed and are
not claimed. No live RPC was part of the final runs.

## 4. Browser observations (independent script)

`results/browser-observations.json` and two screenshots record:

- Keyboard-only Tab/Enter reached and opened Circuit Library (`keyboardFocusReachedLibrary: true`).
- Initial known-address fallback: two `KNOWN_SEED` records with freshness `UNKNOWN` and
  `0/256 RPC reads`; inspector says “Revalidation required for use”, “Unverified seed hint”,
  “Not imported”.
- Discovery status text: `COMPLETE · 21/256 RPC reads`; fallback simulation:
  `UNKNOWN · RPC_UNAVAILABLE · 21/256 RPC reads` plus “Enumeration unavailable. Known-address hints and saved favorites remain selectable.”
- Address search returned one record; circuit-ID token search returned two; Add favorite
  toggled to Remove favorite.
- Stale records displayed as `STALE · KNOWN_SEED` / `STALE · FACTORY_ENUMERATION, KNOWN_SEED`.
- Narrow viewport 390×844: no horizontal overflow. Text labels, not color, carry state.
- Corrupted persisted favorites: see F-01.

Confusing workflow (not an objective defect): the status line reports `COMPLETE` even
when the displayed rows are only local known-address seeds (`0/256 RPC reads`); a
first-time user may read “COMPLETE” as “chain verified”. The inspector does clarify
freshness, but the top-level status wording could be more explicit.

## 5. Security findings

### F-01 — MEDIUM — Corrupted persisted catalog disables known-address fallback

**Reproduction.** Open the library, then set `localStorage["flip-library-m45-v1"]` to a
catalog whose `overlay.favorites` contains an object with no `identity`, reload, and open
Circuit Library. Observed: `role=alert` = “Invalid library request.”, zero library list
buttons, `role=status` = “Loading known addresses…”. The UI already contains the intended
message “Saved library could not be read. Known addresses are available.”, but it is only
used for `JSON.parse` failures; a server-side `422` for a valid-JSON invalid catalog does
not trigger a retry with an empty catalog.

**Impact.** Availability/usability only. No trusted or executable record is created; the
verified importer is untouched. Severity MEDIUM because the documented offline fallback
is unavailable exactly when local storage is corrupted.

**Recommendation.** On a rejected restore, retry `operate("search", {}, undefined)` with
an empty catalog and show the existing storage-note message.

### F-02 — LOW — Favorite-only record is labeled with onchain display trust

`LibraryRecord.metadataTrust` defaults to `ONCHAIN_DISPLAY_ONLY`. `search()` synthesizes
records for favorites/recents with `sources=["USER_FAVORITE_ONLY"]`,
`existence="USER_POINTER"`, `netlistHash=null`, but does not override `metadataTrust`.
Observed B14: a user favorite for circuit 77, with no onchain read, reports
`metadataTrust=ONCHAIN_DISPLAY_ONLY`. The executable distinction remains correct
(`USER_FAVORITE_ONLY`, `UNKNOWN`, no netlist hash), so this is a provenance-label defect,
not an authority problem.

**Recommendation.** Add a user-supplied trust value (e.g. `USER_SUPPLIED`) and set it on
synthesized pointer records.

### F-03 — LOW — `test_custody_and_scratch_regeneration` exceeds its 120 s subprocess timeout

Reproduced twice on this host: full suite and targeted rerun both fail with
`subprocess.TimeoutExpired` after 120 s while running the M3-B `verify_corpus.py` in a
scratch tree. The custody/hash assertions before the subprocess pass. A direct standalone
timing run was interrupted by a harness restart, so the actual duration is **UNKNOWN**;
no conclusion is drawn about Linux CI or Codex's local Windows run. This is a test
reliability/environment finding, not a library behavior defect.

### I-01 / I-02 — INFORMATIONAL — Browser preconditions

`npm test` against a stale `apps/web/dist` fails 10/14; `npm ci` is needed if the locked
`@axe-core/playwright` is absent. Both were corrected without editing locks or sources.

### I-03 — INFORMATIONAL — Cursor offset replay

A `discover` cursor with `offset` tampered to `0` is accepted and re-reads the first page;
records dedupe by key. This wastes reads but grants no trust and cannot create a duplicate
executable record. Circuit cursors with `offset < 1` are rejected.

### I-04 — INFORMATIONAL — Harness-side endpoint correction

The first CLI/API harness run set `FLIP_RPC_URL` only for the CLI subprocess, so the API
TestClient used the default public endpoint once. That observation was discarded; the
harness was corrected to set the environment before app construction and rerun. No live
observation or conclusion relies on that request.

## 6. Negative result: no authority bypass

Verified across core, CLI, API and browser paths:

- `LibraryRecord` has no `executable` or `CURRENT` flag (`library_models.py` line 66).
- `import_selected` constructs a typed `CircuitIdentity` and calls the real M2 importer;
  catalog labels, sources, favorites and aliases are never passed as trust.
- Injected `transactionAuthority`, `permissions`, `approved` and `spend_cap` fields are
  rejected by `extra_forbidden` (B09), and display text is normalized/control-stripped.
- Wrong chain, wrong factory, malformed ABI, reorg, changed implementations and failed
  revalidation all produced non-executable statuses (B01–B08, A07–A08).
- Failed revalidation returned `importProduced: false`; no composition input was emitted.

Therefore no blocking finding was identified.

## 7. Unverified claims

No claim is made about: live provider honesty or multi-operator agreement; Linux CI results;
human screen-reader usability; production solver/native parity; real tape-out, signing or
publication. Fixture passes are not current chain truth, and no historical observation was
promoted to `CURRENT`.

## 8. Acceptance recommendation

Accept M4.5-2L for the bounded, read-only catalog profile with the following conditions:
track F-01 (MEDIUM) and F-02 (LOW) as follow-up fixes; investigate F-03 test timeout on the
target CI host; document the browser build/install preconditions (I-01/I-02). No blocking
security finding was found, and the verified-importer boundary held under all exercised
adversarial cases. **Stop after this independent review; do not merge into `main`.**
