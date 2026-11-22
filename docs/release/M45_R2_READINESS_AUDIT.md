# M4.5-R2 — Read-only release readiness audit

Audit date: **2026-11-22**. Production baseline: `b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b`.
The owner's supplied SHA is a prefix of this full SHA. Fresh fetch confirmed origin/main
at that revision. Branch: `codex/flip-m45-release-readiness`. This is a documentation-only
assessment, not authorization to host a solver, deploy, submit, sign or spend.

## Decision and evidence standard

**Credible supported local technical demonstration: PASS. Complete hackathon release: PARTIAL.**
Judge-access acceptance and distribution rights remain BLOCKED. Manual auditory
screen-reader testing is NOT TESTED. No independent first-time developer study was run.
A passing test or local checksum is not proof of event eligibility, authorship, live
publication, current chain state, adoption or revenue.

| Gate | Assessment | Reason |
|---|---|---|
| Technical local demo | PASS, supported Windows/Linux checkout path | Fresh Windows local 702 Python and 27 Chromium tests pass; accepted-main Linux/Windows CI is green. Prerequisites and narrow supported scope still matter. |
| Judge access | BLOCKED | Public repository is reachable, but no organizer-confirmed application-access arrangement or accessible hosted demonstration exists. |
| Submission completeness | PARTIAL | Product/video/quickstart drafts supplied; actual video, final access URL, owner declarations and final form review remain outstanding. |
| Public interactive deployment | BLOCKED | No reviewed authentication, aggregate isolation/rate/storage controls or authorized host. Loopback guards must not be bypassed. |
| Write-enabled publication | BLOCKED | Deliberately absent. STOP_AUTHORIZATION is a terminal handoff; no wallet, signer, transaction or permission broker. |

[Access options and current official-rule ledger](M45_R2_ACCESS_OPTIONS.md),
[blockers and ordered worklist](M45_R2_RELEASE_BLOCKERS.md), and
[command/source evidence](M45_R2_EVIDENCE.json) distinguish observation from inference.

## What was actually reproduced

All automated browser actions below ran the **existing isolated Playwright suite** against
its own loopback API and synthetic RPC fixture. This did not resume the blocked personal
browser action. The Computer Use restriction was a browser-URL verification protection,
not a Flip application error. No personal browser, screen reader or submission form was
controlled in this resumed audit. Manual browser evidence is NOT VERIFIED; manual speech
output is NOT TESTED. Test assertions and screenshots are engineering evidence, not a
human usability study.

| Journey | Result | Actual method and boundary |
|---|---|---|
| 1. Start from documented instructions | PARTIAL | Existing checkout environment installed successfully with uv 0.9.11, CPython 3.14.6, Node 24.18.0/npm 11.16.0; npm ci, lint and build exited 0. Test servers used the documented local launcher. uv was not on this host's PATH, so the audit used an already installed explicit uv executable. This was not a clean-PC novice trial. |
| 2. Browse processors and circuits | PASS for fixture journey; PARTIAL for live coverage | L01–L03 tests passed discovery, sparse IDs, metadata, pagination, favorite/import and persistence. Separate real read-only CLI discovery returned two registered processors, PARTIAL_BOUNDED, exit 0, 29 RPC calls at block 76571242. Bounded core browsing returned circuit IDs 1 and 2 at block 76571124, PARTIAL_BOUNDED. No complete enumeration claim. |
| 3. Compose archived half-adder | PASS | workflow.spec.ts built 81 bytes / 8 expanded gates, then evaluated four named inputs. This is local historical composition, not an onchain publication. |
| 4. Introduce wiring error | PASS | Existing workflow selected Swap outputs, retaining the reference. |
| 5. Wiring Canary difference | PASS | DIFFERENT was backed by evaluator-replayed witness and two differing mapped outputs; the separate CLI comparison/replay agreed. |
| 6. Inspect connections | PASS | debugging.spec.ts asserted VERIFIED_DIFFERENCE / AMBIGUOUS_MULTIPLE_CAUSES and witness-bound relevant paths; screenshot inspected. Relevant paths are not unique fault attribution. |
| 7. Verify correction | PASS | A separately declared trusted local prior was verified, applied locally, compared EQUIVALENT and reverted. Agent flow also required explicit verify/apply. No unknown oracle was invented. |
| 8. Export Portable 1.1 | PASS | portable.spec.ts saved/reopened the package, tests/history and explicit lossy downgrade; tampered imports were rejected without losing the open project. |
| 9. Coding agent processes project | PASS | agent-portable.spec.ts and Python tests exercised preparation, exact pins, mismatch stop/explicit continuation, trusted correction, new parent-linked revision and separate receipt. |
| 10. Independent evidence replay | PASS on this native engine | workflow.spec.ts replayed a browser export through CLI and browser; agent-portable.spec.ts independently replayed the revised package through CLI as EQUIVALENT / HISTORICAL. Cross-platform native binary identity can require fresh local evidence. |
| 11. Publication boundary | PASS | Browser and Python assertions observed terminal STOP_AUTHORIZATION, one stop log, no revised package and no later queued operation. CLI exit 9 is a stop, not publication success. |

Live reads used https://rpc.xlayer.tech with no credentials or write method. The normal-budget
CLI page was requested at 2026-11-22T09:37:54.434387Z and completed in 14.781s.
Its pinned block hash was `0xd371e4e731916d7fd9d7db94f8d4c800e1772ea0463aba069bd9183e4f33e2c2`.
A separate deliberately small 24-call / 20-second core discovery hit RESOURCE_LIMIT after
24 calls and returned UNKNOWN; it did not silently retry or promote partial data. The
normal-budget CLI then demonstrated that this was not evidence that normal discovery
always fails. Library observations are SINGLE_UNTRUSTED and stored as HISTORICAL.
Circuit browsing metadata did not include a freshly verified netlist hash. No current
XOR/NAND byte identity or whole-chain completeness is asserted from that page.

## Validation observed in R2

| Check | Result |
|---|---|
| Full local Python | 702 passed, 763.42s, no skips; unchanged 120-second archival regeneration test included |
| Full existing Chromium | 27 passed, 156.907s, zero unexpected/flaky/skipped results |
| Frontend lint / build | PASS; 20 files linted; repeated same-host build hashes match |
| Ruff lint / format | PASS; 88 files already formatted |
| Versioned schema drift | All nine profiles PASS |
| Python/Node hash parity | Six base vectors, three portable packages, adapter plan/pins PASS |
| Existing agent/portable review corpora | PASS: 27 agent + 10 authorization, 12 portability, 26 final adapter checks (including 10 attacks) |
| New-document links / credential and historical custody checks | PASS: 23 local links, 862 tracked files scanned, zero credential findings; original archive/review bytes intact |
| Accepted-main Windows/Linux CI | PASS, run 44773778968, head b537eb6; independently re-read via GitHub API in this audit |

[Accepted-main CI](https://github.com/Technique-S/Flip/actions/runs/44773778968) is historical
remote evidence from November 20, not a fresh Linux desktop trial on November 22. The
unchanged push workflow also runs on the documentation branch; its eventual result must
be read from GitHub rather than inferred from local success. Installed dependencies use
locked versions/hashes. Two same-host frontend builds yielded flip.js 278,735 bytes,
flip.css 8,889 bytes and index.html 345 bytes. Artifact hashes are in the evidence JSON.
This establishes repeatability here, not byte-identical native wheels across operating systems.

Raw new logs, receipts and generated PNGs remain in ignored `.test-tmp/r2` and
`.test-tmp/browser`; only their manifest/provenance is committed. The unchanged custody gate
admits only its existing registered PNGs. No new binary namespace or guard exemption was
introduced merely to publish screenshots. Fresh images need deliberate rights/privacy and
custody registration in a later reviewed evidence change before sharing as release assets.

## User-facing findings, not invented user-test outcomes

| ID | Priority | Verified location / observation | Smallest safe next action |
|---|---|---|---|
| R2-UX01 | P1 | README says adapter review is pending, then presents obsolete M2/M3/starter status; current acceptance is complete. | Review a concise current quickstart, move historical context behind a clear link, retain original reports. Draft provided; root README unchanged here. |
| R2-UX02 | P1 | Initial README command assumes uv is installed. Solver opt-in is prose after the launch block. | Put prerequisites and shell-specific opt-in before launch; explain disabled solver / HTTP 501. |
| R2-UX03 | P2 | Evidence screen contains package save, correction, receipt, evidence downloads, explicit open, generic replay and pre-flight. Mobile screenshot is a long vertical workflow. | Add a short ordered recipe/glossary in docs first. Explain why a prepared correction does not replace the original until explicit opening. No production redesign proposed as a prerequisite. |
| R2-UX04 | P2 | Debugger exposes numeric pins and machine classifications; it correctly says causes are ambiguous. | Narrate one concrete output swap and keep the non-unique-cause wording in the video. Do not describe this as autonomous bug repair. |
| R2-UX05 | P2 | Separate downloads and native engine identity are real provenance requirements. | Tell judges to keep project + evidence + receipt, replay on their local engine and regenerate if engine identity changed. |

These are source/screenshot-backed engineering observations and onboarding hypotheses.
They are not reports of a developer becoming confused in a study. No production fix was made.

## Interface audit and accessibility

Operate-mode technical audit using existing source, fresh automated captures and test results:

| Dimension | Conservative score / 4 | Basis / gap |
|---|---:|---|
| Accessibility | 2 | Automated axe, labels, table semantics, keyboard/focus tests pass; manual auditory output NOT TESTED, so no full WCAG conformity claim. |
| Performance | 3 | Small measured static bundle, bounded table/options and finite worker budgets; no low-end-device cold-start or adversarial public-host SLO benchmark. |
| Theming | 3 | Coherent light-theme tokens and focus states in inspected captures; no dark-theme promise. |
| Responsive | 3 | Existing tests cover 320/390/768/1280-width behavior, no horizontal overflow assertions fail; mobile is dense and lengthy. |
| Implementation integrity | 3 | Shared core and honest trust labels, explicit local apply/open, bounded operations; stale onboarding text remains. |
| Total | 14 / 20 | Audit rubric, not an accessibility certification or independent user verdict. |

Manual screen-reader acceptance remains a release gap. Test with NVDA or Narrator on the
actual supported browser/OS and retain tool versions plus **spoken** output for sample
loading, import failure, EQUIVALENT, DIFFERENT witness table, UNKNOWN timeout, correction,
new-revision selection, cancellation and STOP_AUTHORIZATION. Check headings/landmarks,
keyboard order, table headers, labels, focus recovery and live-region timing. Record
expected and actual speech, result and workaround for each case. Automated accessibility
trees are not substitutes for listening. Do not bypass the Computer Use protection to do it.

## Provenance, licensing and data

- Offline proofs remain historical and reference-relative. Vector matches cover declared
  inputs; universal stateless equivalence needs the trusted comparison. UNKNOWN is inconclusive.
- Project and portable selection use sessionStorage; library favorites, aliases, recents and
  recovery copies use localStorage (`flip-library-m45-v1`). Both are local plaintext browser
  storage, not a secret store or durable portable backup. Resetting the workspace must not be
  described as clearing all library/browser data. Save explicit files; use supported browser
  controls for cleanup after the demo. Do not put secrets or personal data in projects/aliases.
- A live RPC receives network/query data and is a single-provider trust assumption. CI/browser
  fixtures are synthetic. The historical sample can run without network once dependencies exist.
- No root own-source license or package licensing decision was found; GitHub API license=null.
  See [rights and release blockers](M45_R2_RELEASE_BLOCKERS.md). No license was selected here.
- Original independent reports and archived fixtures were not edited. The older unmerged
  release evidence at ddbd72e655c0afe4085e5c949f5e1741c7a6f552 tested pre-library main 09f2482;
  its MISSING library/agent findings must not be silently applied to today's accepted product.
