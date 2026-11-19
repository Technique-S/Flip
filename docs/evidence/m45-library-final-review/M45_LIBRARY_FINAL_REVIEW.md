# M4.5-2L-E — Final independent library delta review

**Role:** independent verification engineer (OpenCode / HY4 Flash).
**PR:** [#5](https://github.com/Technique-S/Flip/pull/5), state `open`, `merged: false`.

| Role | Exact SHA |
|---|---|
| Accepted main (unchanged) | `09f2482beae84be6d919ecd6957c4153d1924cca` |
| Previously reviewed implementation | `dec9420bb76e9245c6740bf3d92031d175e408ec` |
| Previous independent review | `9741e66ae385979dc0d18c89aec4ec6ed93ff285` |
| CI-tested implementation | `a184d776c896476be77f518b87885529a4038539` |
| **Final PR #5 head tested here** | **`786cbca056c6cd61ca0e7a5b61ddbc772a55a800`** |

The diff from `a184d77` to the PR head contains only
`docs/milestones/M45_LIBRARY_ACCEPTANCE.md` and
`docs/milestones/m45-library-reconciliation/validation-results.json`; no production code
changed after the CI-tested commit.

**Recommendation: PASS.** F-01, F-02 and F-03 are independently dispositioned below; no
CRITICAL or HIGH finding remains and no path bypasses the M2 trusted importer.

## 1. Delta inspected

Production changes since `dec9420`:

- `apps/web/src/Library.tsx` — 1.1 wire version, rejected/legacy restore recovery,
  original-bytes retention, recent-order sorting, and explicit `USER_SUPPLIED` display.
- `flip_core/library_models.py` — version 1.1, `metadataTrust` union with
  `USER_SUPPLIED`, validator forbidding onchain trust on user-only pointers, explicit
  1.0 catalog migration.
- `flip_core/library_models_v1.py` (new, byte-identical copy of the frozen 1.0 models),
  `library_protocol.py` (version dispatch; legacy results suppress unrepresentable
  user-pointer records with `UNKNOWN` / `UNSUPPORTED_SCHEMA_VERSION` instead of lying).
- `flip_core/library.py` — duplicate label accumulation, `USER_SUPPLIED` on synthesized
  pointers, processor-level environment freshness invalidation, version dispatch.
- API/CLI dispatch on `parse_library_request`; schema exporter gains `--version`;
  CI adds a frozen-1.1 schema drift check; custody guard pins frozen 1.0 schemas and
  model bytes.
- New additive `docs/schema/m45-library/1.1.0/`, examples, focused tests, and browser
  acceptance tests `apps/web/tests/library-acceptance.spec.ts`.

No change was found in `ImportService._import`, `PinnedReader`, `abi.SELECTORS`, the
allowlisted read methods or the composition path. The catalog still has no executable or
`CURRENT` flag.

## 2. Commands and results

From `C:\Users\Kazi\Documents\Flip\repo` (CPython 3.14.6, Node 24.18.0):

```powershell
# harnesses copied into this evidence directory and adapted to schema 1.1.0
.venv\Scripts\python.exe docs/evidence/m45-library-final-review/harness/independent_core_checks.py
.venv\Scripts\python.exe docs/evidence/m45-library-final-review/harness/independent_cli_api_checks.py
cd apps/web; npm run build; npm test -- --reporter=list
node docs/evidence/m45-library-final-review/harness/browser_observations.mjs
cd ../..
.venv\Scripts\python.exe -m pytest -q --junitxml=docs/evidence/m45-library-final-review/results/pytest-full.xml -o junit_family=legacy
.venv\Scripts\python.exe scripts/check_m1_repository.py
.venv\Scripts\python.exe -m flip_core.library_schema_export --version 1.0.0 --out docs/schema/m45-library/1.0.0 --check
.venv\Scripts\python.exe -m flip_core.library_schema_export --version 1.1.0 --out docs/schema/m45-library/1.1.0 --check
.venv\Scripts\python.exe fixtures/m45-library-discovery/generators/verify_fixtures.py
gh api repos/Technique-S/Flip/pulls/5
gh api repos/Technique-S/Flip/actions/runs/44500076045[/jobs]
```

| Check | Result |
|---|---|
| Independent core production checks | **24 executed, 0 harness errors**; selectors 9/9 match; research fixtures 19/19 hashes match |
| CLI/API parity | CLI exit 0, both `PARTIAL_BOUNDED`, identical shapes, invalid op and corrupt catalog `422` |
| Chromium full suite (**after rebuild**) | **18 passed / 0 failed**, including F-01 and F-02 focused tests |
| Independent browser script | 20 recorded steps; keyboard entry true, narrow viewport no overflow, corrupt-storage recovery and USER_SUPPLIED inspector confirmed |
| Repository custody guard | `PASS`, 575 tracked files scanned, 0 credential findings |
| Frozen 1.0 and new 1.1 schema drift | both `PASS` |
| Research fixture verifier | `result: PASS`, `errors: []` |
| Full Python suite | **543 passed, 0 failed, 0 skipped** (387.32 s; JUnit XML captured) |
| CI run `44500076045` | `status: completed`, `conclusion: success`, `head_sha: a184d77…`; jobs `contracts (ubuntu-latest)` and `contracts (windows-latest)` both `success` |

Full captured evidence, including screenshots and logs, is in
`docs/evidence/m45-library-final-review/results/` with a SHA-256 register in
`RESULTS_MANIFEST.json`.

## 3. Finding dispositions

### F-01 (MEDIUM) — RESOLVED, independently reproduced

Original reproduction: corrupt `overlay.favorites` in `localStorage`, reload, reopen
Library → `"Invalid library request."`, zero rows, status stuck at "Loading known
addresses…".

Against the new build the same sequence produced: no error alert; **two** known-address
rows (`UNKNOWN · KNOWN_SEED`); status
`"Saved library is invalid or unsupported. Known addresses loaded; original saved data retained for recovery."`
followed by `COMPLETE · 0/256 RPC reads`. The original invalid bytes remain at the primary
storage key (the separate `-recovery` key is written on a later explicit edit, which is
the documented behavior). The focused browser test
`F-01 exact malformed-favorites restore retains bytes and recovers seeds` passes. Corrupt
catalogs are still rejected wholesale; they are never sanitized into trusted state.

### F-02 (LOW) — RESOLVED, independently reproduced

Core check B14: a user favorite for circuit 77, with no onchain read, now reports
`sources=["USER_FAVORITE_ONLY"]`, `existence="USER_POINTER"`,
`metadataTrust="USER_SUPPLIED"`, `netlistHash=null`. Browser: selecting the favorite-only
row shows `Metadata provenance USER_SUPPLIED`, `User pointer`,
`No onchain metadata observed`, `No chain observation`, `No onchain environment observed`,
`Not imported`. Forged authority fields remain rejected at schema validation. Legacy 1.0
requests suppress unrepresentable user-pointer results and return
`UNKNOWN / UNSUPPORTED_SCHEMA_VERSION` rather than relabeling them as onchain; a 1.1
request retrieves the truthful record.

### F-03 (LOW) — INVESTIGATED; no new defect, follow-up retained

The inherited 120 s inner timeout is unchanged. Codex's serial probe
(`regeneration-probe.json`) records two passing runs: default layout 96.22 s wall
(92.99 s test call) and custom layout 87.27 s wall (83.68 s test call), with startup
0.10–0.11 s, copy ~0.035 s and hashing ~0.17–0.21 s. My earlier local timeouts occurred
while other heavy harnesses ran concurrently; the full-suite result above is the
independent final observation. Root cause of the earlier timeouts is **not uniquely
established**, so runtime margin remains a tracked limitation (F03-PERF-001), not an
accepted library defect. No timeout or assertion was relaxed.

## 4. Trust-boundary and provenance verification

- No production change bypasses the M2 importer: `import_selected` still constructs a
  typed `CircuitIdentity` and calls `ImportService._import`; discovery records, aliases,
  favorites and metadata fields are never used as trust input.
- Observed freshness values across all independent outputs: `HISTORICAL`, `STALE`,
  `UNKNOWN`. `CURRENT` never appears; imported results are `HISTORICAL`, and a changed
  environment yields `ENVIRONMENT_CHANGED` with `STALE` and no import payload.
- Synthetic research cases remain labeled `SYNTHETIC`; live observations remain
  single-provider `OBSERVED_READ_ONLY`; no fixture was promoted to chain truth.
- Archived fixtures and frozen contracts: custody guard PASS, research manifest 19/19,
  frozen library 1.0 schemas and model bytes pinned by new guard assertions.

## 5. Remaining findings and limitations

| Severity | Item | Status |
|---|---|---|
| INFORMATIONAL | Default library view shows only processor-level rows until a processor or the Favorites/Recents filter is selected; a circuit-level favorite is invisible in the default view | Confusing workflow, not an objective defect; corrected by filter use |
| INFORMATIONAL | Legacy 1.0 clients receive `UNKNOWN / UNSUPPORTED_SCHEMA_VERSION` for user-pointer results | Intentional truthful compatibility behavior; documented |
| LOW | F-03 runtime margin / host variability | Tracked follow-up F03-PERF-001; not reproduced as a library regression |
| N/A | Human screen-reader session, live provider honesty, multi-operator agreement, signing/publication | Not performed; not claimed |

No CRITICAL, HIGH or MEDIUM finding remains.

## 6. Acceptance recommendation

**PASS** for PR #5 at `786cbca056c6cd61ca0e7a5b61ddbc772a55a800`, conditional only on
keeping the tracked F-03 runtime-margin follow-up and the documented 1.1 compatibility
notes. The three prior findings are dispositioned with independent evidence, the trusted
importer boundary is intact, frozen contracts and archived evidence are unchanged, and
Windows/Linux CI plus source identity are confirmed. This review does not merge or modify
Codex's PR.
