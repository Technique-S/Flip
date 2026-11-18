# Accessibility and browser acceptance plan — M4-B

**Status: SPECIFICATION ONLY — NO BROWSER TESTS WERE EXECUTED.** The accepted M3
baseline contains no `packages/flip-web` application and no pre-flight UI.
Nothing in this directory claims a test ran or passed. Machine source:
[`accessibility-matrix.json`](accessibility-matrix.json); executable scaffold:
[`playwright-spec.md`](playwright-spec.md).

## Scope

The plan covers the PRD's accessibility baseline (FR-001, NFR-09, NFR-12) and
the M4 product journeys J01–J13. It is an **independent acceptance
specification** for Codex to integrate once the web application and its frozen
props/API contracts exist.

## Scenario matrix

| ID | Scenario | Primary checks | WCAG targets | Journey links |
| --- | --- | --- | --- | --- |
| B01 | Keyboard-only operation | Every primary action reachable and operable; no traps | 2.1.1 | J01, J04, J12 |
| B02 | Focus order and visibility | Reading order; focus after errors; visible indicator | 2.4.3, 2.4.7, 3.3.1 | J02, J10, J11 |
| B03 | Accessible labels | Named controls; numbered pins/widths in the tree; user-supplied labels marked | 4.1.2 | J02, J04 |
| B04 | Result announcements | Live region states verdict and freshness separately; witness table headers | 4.1.3, 1.4.1 | J01, J06, J07 |
| B05 | Responsive layout | 320/768/1280 px; no lost function; report header stays visible | 1.4.10 | J01, J04, J07, J13 |
| B06 | Loading and error states | Text progress; cancellable; errors match `error-catalog.json`; state preserved | 4.1.3, 3.3.1, 3.3.3 | J02, J10, J11 |
| B07 | Timeouts | UNKNOWN text, reason visible, no EQUIVALENT styling, rerun works | 4.1.3, 1.4.1 | J08 |
| B08 | Repeated workflow | Five runs; identical digest/verdict; no stale fragments | 4.1.3 | J01, J05 |
| B09 | Refresh and recovery | State restored; confirmed reset; quota errors in text | 3.3.1, 4.1.3 | J01, J02 |
| B10 | Export accessibility | Named download; accessible summary; statuses separated after re-import | 2.1.1, 4.1.2, 1.4.1 | J12 |
| B11 | Pre-flight separation | Distinct status region; no success styling for UNKNOWN; no wallet control | 1.4.1, 4.1.3 | J13 |

## Execution protocol for Codex

1. Freeze the UI contract first (roles, labels, live regions, result regions).
   Do not rewrite these scenarios to match implementation accidents; report a
   defect instead.
2. Wire the Playwright scaffold in `playwright-spec.md`, replacing only the
   `data-testid` mapping table with real selectors. Keep the assertions and
   accessibility-tree checks unchanged.
3. Run `axe-core` on every distinct state: empty, loading, EQUIVALENT,
   DIFFERENT, UNKNOWN, STALE, error and pre-flight UNKNOWN.
4. Perform one manual screen-reader pass per result class (B04) and one manual
   keyboard-only completion of J01 (B01). Automated checks do not replace these.
5. Correlate browser results with CLI correlates named in the matrix. A browser
   verdict must carry the same verdict class, reason code and freshness axis as
   the corresponding CLI case (`C04`, `C05`, `C06`, `C08`, `C22`, `C25`, `C29`).
6. Record actual runs in a new evidence file with browser version, viewport,
   axe version, failures and screenshots. Until then, every scenario stays
   `SPEC_ONLY_NOT_EXECUTED`.

## Pass/fail policy

- A scenario passes only when **all** of its pass criteria hold; partial passes
  are reported as failures with the unmet criterion named.
- Colour-only status, unlabelled controls, keyboard traps, a timeout shown as
  EQUIVALENT, or a pre-flight UNKNOWN shown as success are **blocking** defects.
- No execution claim may be added to this plan by editing the status field
  without an accompanying executed evidence file.

## Provenance

This plan was authored from the frozen PRD, technical design, M3 interface
README and the executed CLI transcript. It contains no browser observation.
