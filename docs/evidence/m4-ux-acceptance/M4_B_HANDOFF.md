# Flip M4-B — independent UX scenarios and product acceptance handoff

**Role:** independent supporting engineer (OpenCode / HY4 Flash).
**Branch:** `opencode/flip-m4-ux-acceptance`.
**Baseline commit:** `af8ba1f109a2a1c59fe36be044bc025a127ea025`.
**Scope:** fixtures and documentation only. **No merge into `main`.**
**No wallet, key, signing, broadcast, payment, live RPC call or publication.**
**Stop at M4-B.**

## 0. Setup deviation (recorded, not silently reconciled)

The task required confirming that PR #3 was merged into `main`. At task time the
GitHub API reported:

- PR #3 (`codex/flip-m3-integration`, "Integrate M3 verification engine and
  independent security acceptance") was **OPEN**: `state: open`, `merged: false`,
  `mergedAt: null`; merge commit `460a91e0…` existed as a proposed merge only.
- `main` was still the PR #2 merge commit
  `02463b1f370d39f6abab897d54d3438cd6056458` (M2 integration).

Following the precedent recorded in `docs/evidence/m3-verification/M3_B_HANDOFF.md`
§0, I treated the **head of PR #3** (`af8ba1f…`, the accepted M3 integration
state containing `docs/milestones/M3_ACCEPTANCE.md` and the implemented M3 CLI)
as the accepted M3 baseline and based this isolated branch on it. This is
visible in the branch ancestry, does not alter `main`, and does not resolve
repository integration. Codex must merge PR #3 before integrating this branch.

`AGENTS.md` was read and followed. Only the two owned write paths were changed.
All original M0/M0.5 evidence, frozen schemas, M2/M3 fixtures and the M3-B
handoff are byte-unchanged.

## 1. Fixture inventory

Byte sizes and SHA-256 values for every authored and captured file are in
`fixtures/m4-ux-acceptance/MANIFEST.json` (sections `authored` and `captured`).

| Path | Purpose |
| --- | --- |
| `fixtures/m4-ux-acceptance/README.md` | Index, provenance legend, regeneration commands |
| `fixtures/m4-ux-acceptance/MANIFEST.json` | Byte/hash register of all owned files |
| `fixtures/m4-ux-acceptance/journeys/JOURNEYS.json` | 13 golden journeys, all seven required fields each |
| `fixtures/m4-ux-acceptance/journeys/README.md` | Human-readable journey matrix |
| `fixtures/m4-ux-acceptance/cli-cases/CLI_ACCEPTANCE.md` | Executed case table and coverage map |
| `fixtures/m4-ux-acceptance/cli-cases/CASES.json` | Machine-readable executed + planned cases |
| `fixtures/m4-ux-acceptance/cli-cases/requests/*.json` | 15 neutral request fixtures + 2 provenance sidecars |
| `fixtures/m4-ux-acceptance/error-messages/error-catalog.json` | 12 plain-language error entries |
| `fixtures/m4-ux-acceptance/error-messages/ERROR_MESSAGE_REVIEW.md` | Wording review and acceptance checks |
| `fixtures/m4-ux-acceptance/browser/accessibility-matrix.json` | 11 a11y/browser scenarios, `SPEC_ONLY_NOT_EXECUTED` |
| `fixtures/m4-ux-acceptance/browser/ACCESSIBILITY_ACCEPTANCE_PLAN.md` | Execution protocol and pass/fail policy |
| `fixtures/m4-ux-acceptance/browser/playwright-spec.md` | Unexecuted Playwright scaffold |
| `fixtures/m4-ux-acceptance/docs/USER_GUIDE.md` | Nine bounded documentation topics |
| `fixtures/m4-ux-acceptance/generators/build_fixtures.py` | Deterministic neutral-fixture builder |
| `fixtures/m4-ux-acceptance/generators/run_cli_cases.ps1` | 21 baseline CLI cases |
| `fixtures/m4-ux-acceptance/generators/run_consumption_cases.ps1` | 5 trusted-consumption cases |
| `fixtures/m4-ux-acceptance/generators/run_local_double_cases.py` | Import success, not-found, STALE revalidation via local double |
| `fixtures/m4-ux-acceptance/generators/run_determinism_case.py` | 100 repeated compose builds |
| `fixtures/m4-ux-acceptance/generators/verify_fixtures.py` | Hash verification, regeneration check, summary/cases generation |
| `docs/evidence/m4-ux-acceptance/M4_B_HANDOFF.md` | This document |
| `docs/evidence/m4-ux-acceptance/executed/transcript.json` | 30 raw command captures (exit codes, stdout hashes, stderr) |
| `docs/evidence/m4-ux-acceptance/executed/summary.json` | Semantic outcomes extracted from captures |
| `docs/evidence/m4-ux-acceptance/executed/C##.stdout.txt`, `C##.stderr.txt` | Raw per-case output |

## 2. Exact reproduction commands

```powershell
uv sync --locked
uv run --frozen python fixtures/m4-ux-acceptance/generators/build_fixtures.py build
powershell -ExecutionPolicy Bypass -File fixtures/m4-ux-acceptance/generators/run_cli_cases.ps1
uv run --frozen python fixtures/m4-ux-acceptance/generators/build_fixtures.py consumption `
  --equivalent docs/evidence/m4-ux-acceptance/executed/C04.stdout.txt `
  --different  docs/evidence/m4-ux-acceptance/executed/C05.stdout.txt
powershell -ExecutionPolicy Bypass -File fixtures/m4-ux-acceptance/generators/run_consumption_cases.ps1
uv run --frozen python fixtures/m4-ux-acceptance/generators/run_local_double_cases.py
uv run --frozen python fixtures/m4-ux-acceptance/generators/run_determinism_case.py
uv run --frozen python fixtures/m4-ux-acceptance/generators/verify_fixtures.py
```

Environment: CPython 3.14.6, uv 0.9.11, pinned `uv.lock`, Windows. No dependency
was added and no lockfile was changed. `uv` was bootstrapped locally only
(`python -m pip install --user uv==0.9.11`); it is not a repository requirement.

`verify_fixtures.py` rebuilt the 10 neutral request fixtures in a scratch
directory and required byte equality, then verified all registered hashes.
Result: `regeneration exact for 10 request fixtures`; `verified 29 authored and
61 captured files`; `summary cases: 30`.

## 3. Executed checks

All 30 cases were executed on the accepted M3 baseline. Process exit codes and
semantic fields were recorded separately; command success was never treated as
proof of equivalence.

| Group | Cases | Observed outcome |
| --- | --- | --- |
| Contract/bootstrap | C01, C02, C15–C17 | exit 0; canonicalization and hashing only, no proof |
| Compose + determinism | C03, C29 | 81-byte netlist digest `0x3dbb65a6…`; 100/100 identical builds |
| Compare verdicts | C04, C05, C06 | EQUIVALENT / DIFFERENT (replayed witness) / UNKNOWN (`SOLVER_TIMEOUT`) |
| Vectors | C07 | `VECTORS_MATCH`, 4-row exhaustive declared domain |
| Historical restrictions | C08, C22, C25, C30 | caller `CURRENT` ignored; false CURRENT rejected; STALE after simulated upgrade |
| Invalid input / version | C09, C10, C12 | exit 3 `INVALID_INPUT` |
| Wrong chain | C11, C13, C21 | exit 3 `WRONG_CHAIN` before state reads |
| RPC failures | C14 | exit 4 `RPC_UNAVAILABLE` |
| Trusted consumption | C22–C26 | valid claim recomputed; forged verdict, changed reference and CURRENT relabel rejected; DIFFERENT witness recomputed |
| Local-double import | C27, C28 | success; `MISSING_REFERENCE` for absent circuit |
| Reserved M4 commands | C18, C19, C20 | exit 6 `NOT_IMPLEMENTED` as expected on M3 |

Detailed commands, exit codes, stdout SHA-256 values and semantic outcomes are
in `executed/transcript.json` and `executed/summary.json`.

Two fixture-side corrections were made during development, never to production
code or acceptance thresholds: (1) a provenance `_note` field was removed from
consumption fixtures because frozen contracts use `extra="forbid"`; (2) the
"circuit not found" double was changed to report `nextId = 1` so the importer's
real `MISSING_REFERENCE` path was exercised instead of a decode error.

## 4. Planned but unexecuted cases

| ID | Capability | Why unexecuted | Required M4 outcome |
| --- | --- | --- | --- |
| P01 | `flip preflight` | reserved; C18 exit 6 | one of STRUCTURALLY_ACCEPTED / REJECTED(reason) / UNKNOWN; no publication claim |
| P02 | `flip export` | reserved; C19 exit 6 | path-safe portable bundle with SHA256SUMS and no secrets |
| P03 | `flip verify-bundle` | no M3 implementation | checksum + repeated local checks; never upgrades HISTORICAL |
| P04 | `flip sample` | reserved; C20 exit 6 | emits pinned offline sample request |
| P05 | live X Layer `inspect`/`import` | no live RPC authorized | CURRENT single-RPC observation with pinned block/chain verification |
| P06 | Browser E2E B01–B11 | no M4 web application | see accessibility matrix |
| J13 | Read-only pre-flight UI | no M4 web application / preflight reserved | separate status region, no wallet control |

No passing result is claimed for any of these.

## 5. Provenance classifications

| Class | Used for | Meaning |
| --- | --- | --- |
| `PINNED_M3_BASELINE` | C01–C26, C29 | executed with pinned uv on the accepted M3 head; no live RPC |
| `LOCAL_DOUBLE_OFFLINE_ARCHIVED_BYTES` | C27, C28, C30 | loopback double reusing committed M2 offline transport and archived M0/M0.5 bytes; **not live chain state** |
| `NEUTRAL_DERIVED_FROM_FROZEN_M3_SAMPLE` | `cli-cases/requests/*` | mechanically derived from the frozen half-adder request; sources recorded in `SOURCES.json` |
| `CLAIMS_CAPTURED_CLI_OUTPUT` | `consumption-*.json` | claims taken from actual `flip compare` stdout; no authored proof text |
| `SPEC_ONLY_NOT_EXECUTED` | browser matrix, J13, P01–P06 | capability absent on baseline |

Archived real circuits originate from `docs/evidence/raw/M0/`; all composed
mutations, timeouts, consumption forgeries and environment changes are
**synthetic**. No synthetic circuit was deployed and no RPC endpoint was
contacted. `CURRENT`/`STALE` labels from C27/C30 describe the simulated double
only and must never be quoted as live X Layer evidence.

## 6. Expected outcomes summary (UI and CLI)

- **CLI:** exit 0 EQUIVALENT / compose, 1 DIFFERENT, 2 UNKNOWN, 3 invalid input
  or wrong chain, 4 RPC failure, 6 NOT_IMPLEMENTED, 7 STALE. JSON fields are
  authoritative; a completed process is not a proof.
- **Journeys:** J03–J08, J10, J11 have executed CLI equivalents. J01, J02, J09,
  J12 are partial (CLI done, web M4 portion specified). J13 is specification
  only.
- **UI when available:** verdict, freshness, oracle mode, pin map and reason code
  must be shown as separate labelled text; DIFFERENT must never say the user's
  circuit is wrong; UNKNOWN must never be styled as EQUIVALENT; pre-flight
  status must never reuse verification badges. Copy is proposed in
  `error-catalog.json` and `USER_GUIDE.md`, not yet shipped.

## 7. Accessibility acceptance matrix

Eleven scenarios are defined in `browser/accessibility-matrix.json` and
`ACCESSIBILITY_ACCEPTANCE_PLAN.md`: B01 keyboard-only operation, B02 focus order
and visibility, B03 accessible labels, B04 screen-reader result announcements,
B05 responsive layout at 320/768/1280 px, B06 loading/error states, B07
timeouts, B08 repeated execution, B09 refresh/recovery, B10 export
accessibility, B11 pre-flight separation. Each has steps, pass criteria, WCAG
targets, linked journeys and CLI correlates.

**Status: `SPEC_ONLY_NOT_EXECUTED`.** A Playwright/axe scaffold is supplied in
`browser/playwright-spec.md`; it has not been run. Codex should replace only its
selector map and keep the assertions.

## 8. Potential UX risks

1. **Overclaiming EQUIVALENT.** Users may read it as "correct" or "safe to
   publish". Mitigation: always show intent, mapping, limits and freshness
   beside the verdict (USER_GUIDE §3, error E08).
2. **DIFFERENT read as blame.** Mitigation: "the two circuits differ" wording,
   no bug/failure labels (error E09, J07).
3. **Timeout misread as equality.** Mitigation: UNKNOWN + reason text, no green
   styling, retry with enlarged budget (E06, B07).
4. **Stale evidence mistaken for current.** Mitigation: persistent text badge,
   no promotion by flags, revalidation after environment change (E04/E05, J09).
5. **Local-double results quoted as live.** Mitigation: provenance label on
   every C27/C28/C30 artifact and in this handoff.
6. **Pre-flight mistaken for publication.** Mitigation: separate status region,
   "no transaction broadcast" text, no wallet control (E11/E12, B11).
7. **Mapping tables inaccessible.** Mitigation: real table headers, numeric
   labels, per-cell errors, keyboard navigation (B03, J11).
8. **Long-running operations with no feedback.** Mitigation: text progress,
   cancellation, preserved project state (B06, J10).
9. **Refresh loses work.** Mitigation: local restoration notice and confirmed
   reset (B09).
10. **Export bundle seen as a certificate.** Mitigation: describe it as
    reproducible evidence; consumption recomputes and never makes it current
    (J12, USER_GUIDE §7).

## 9. Recommendations for Codex integration

1. Merge PR #3 into `main` first, then re-run the combined tree checks with this
   branch integrated. Do not merge this branch directly to `main`.
2. Adopt `JOURNEYS.json` as the source for the M4 E2E story, but keep each
   journey's execution-status field honest until its web steps actually run.
3. Convert `CASES.json` planned entries P01–P04 into executable CLI tests as
   each command is implemented; require the exact exit classes recorded here.
4. Use `error-catalog.json` as the copy contract for M4 error states, with the
   machine envelope untouched and technical details in a disclosure.
5. Wire `playwright-spec.md` after the UI props contract is frozen; run B01–B11
   with axe-core and record real evidence before flipping any status to
   executed.
6. Keep the local-double runner as an offline subprocess in CI for import,
   missing-circuit and STALE paths; never point it at a live endpoint and never
   label its `CURRENT` result as a chain observation.
7. Preserve the separation of verification verdict and freshness in every
   report and UI state; add regression tests for C08, C25 and C30 so a caller
   flag or cached input can never gain CURRENT status.
8. Do not broaden MVP scope: no generic editor, wallet, signing, broadcast,
   publication or unbounded stateful equivalence.

## 10. Modified files and completion

Owned files only:
`fixtures/m4-ux-acceptance/**` and `docs/evidence/m4-ux-acceptance/**`.
No production package, frontend file, shared schema, dependency lock, CI
configuration, Codex branch or original M0/M0.5 evidence was modified.

Commit SHA and final file list are reported in the completion message. No PR
was opened by this task and no merge was performed.

**End of M4-B deliverables.**
