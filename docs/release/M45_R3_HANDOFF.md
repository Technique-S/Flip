# M4.5-R3 — Release package handoff

Date: 2026-11-23. Branch: `codex/flip-m45-release-package`.
Base accepted main: `b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b`.
Reviewed R2 audit: `39df7af4c2784502d243e6cc00be43fa84b5799b`.
The exact delivery SHA is the immutable commit accompanying this record (`git rev-parse
HEAD` after checkout). CI results attach to that exact GitHub head, not to a self-referential
hash written into this file. No merge, deployment, application submission or transaction.

## Delivered behavior

The corrected [README](../../README.md) describes the actual accepted product and
source installation, local solver opt-in, half-adder/correction walkthrough, CLI workflow,
portable round-trip and historical boundaries. The [packaging guide](M45_R3_PACKAGING.md)
provides version/notice inventory, source pinning, reproducibility and troubleshooting.
The [storyboard and checklist](M45_R3_DEMO_AND_CHECKLIST.md) remain clearly marked drafts.
The [asset inventory](M45_R3_ASSET_INVENTORY.json) records hashes and provenance.

The separate [static showcase](../../apps/showcase/README.md) builds 19 HTML/CSS/JSON/text
files and opens directly by file URL. Seven pages show selected archived snapshots:
sample, composition, DIFFERENT, relevant connections, verified correction, portable
revision and evidence. The reference has 8 gates / 81 bytes; the recorded candidate has
12 gates / 109 bytes. Witness input 01 gives reference 01 and candidate 10. Diagnostics
retain AMBIGUOUS_MULTIPLE_CAUSES and uniqueFaultClaim=false. The saved correction is
VERIFIED_CORRECTION with EQUIVALENT/UNSAT historical evidence. The new Portable 1.1
revision links its parent and retains one named four-vector test set and an evidence ref.

This is a recorded demonstration, not live proof or a continuous video. A persistent
RECORDED/HISTORICAL banner, reference-relative scope and explicit capability limits
remain on every page. JSON links open exact local files; browser Save as retains copies.
No source license, installer, native binary, hosted endpoint or video was published.

## Security and custody

- No client JavaScript, backend, native solver, wallet, RPC, publication UI, uploads,
  evaluation of artifact code, external fonts/images, telemetry or imported executables.
- Meta CSP denies scripts/connections/objects/frames/workers/media/forms. No server is
  required. Build uses only Node built-ins; no runtime/solver modules are imported.
- Fixed filenames and a pinned recording-manifest SHA bind all inputs. Displayed strings
  are escaped. Distribution checker rejects unexpected file types, active elements,
  external references, broken local links and checksum drift; builder rejects stale files
  and symlinks. Tamper/HTML-string attack tests fail closed.
- Offline Chromium traversal records only local package requests; instrumented fetch,
  XHR, WebSocket, EventSource, beacon and injected wallet providers receive zero calls.
  Tests also traverse with JavaScript disabled. No API server starts for showcase tests.
- The original receipt, portable revision and replay request were copied unchanged from
  R2's passing integrated browser journey. Derived execution/evidence/compiler files are
  identified separately in `recordings/manifest.json`; original independent harness and
  reports are unchanged. Compatible Windows native curation reproduced DIFFERENT and
  replayed the correction as EQUIVALENT/HISTORICAL before static rendering.
- Production packages, apps/web, schema contracts, locks, archival evidence and earlier
  release reports remain identical to accepted/R2 source. Only release presentation,
  documentation, new checks and additive CI steps are introduced. No legacy CI gate or
  deadline was removed or increased; no dependency or file-size exemption was added.

## Acceptance evidence

Commands run from the R3 source root. Windows x64, Python 3.14.6, uv 0.9.11,
Node 24.18.0, npm 11.16.0. Locked installation and existing frontend build succeeded.
Final command outcomes are recorded below before delivery; remote Windows/Linux checks
are authoritative for their individual exact head. Existing CI retains full Python,
27 production browser checks, schema/parity, custody and archival tests, with additive
static build/check/security/browser steps and uploaded showcase JSON results.

| Gate | Result / evidence |
|---|---|
| Deterministic static build / rebuild | PASS: 19 files, build then --check; output checksums retained in inventory |
| Offline capability boundary | PASS: file-only traversal, zero sensitive calls and no external requests |
| Tampering / text injection | PASS: modified recording rejected; HTML-like strings escaped |
| Showcase browser suite | PASS: 6/6, no retries/skips; local JSON opens exact package |
| Automated accessibility | PASS: axe WCAG 2 A/AA + 2.1 AA across all 7 pages at 1280/390px; 320px overflow check; reduced-motion and keyboard/JS-disabled checks |
| Visual inspection | PASS: actual automated desktop DIFFERENT and mobile revision screenshots inspected; original design retained |
| Native / production browser regression | PASS: 101 portable/agent/workflow Python tests in 494.27s; all 27 production Chromium tests in 246.03s, no skips/retries/flakes |
| README CLI round-trip / workflow | PASS: 10 commands; sample/compose/compare/export/replay, four-step offline workflow, wrap/validate/open/downgrade (explicit allowLossy) |
| Local links | PASS: 110 relative links across static output and release documentation |
| Source lint / hash parity | PASS: Ruff lint/format (88 files), frontend lint/build, all three Node canonical parity gates |
| Credential / immutable custody | PASS: 883 tracked files scanned, zero credential-pattern findings; exact archived/review blobs intact |
| Remote Windows / Linux CI | Check exact delivery commit's M1 contracts matrix; no local Linux or clean novice install claim |

Local QA JSON/XML and screenshots live under ignored `.test-tmp/r3`; CI uploads its
showcase JSON. Hashes/provenance in the committed inventory identify durable release
inputs, output and the selected local result files. The design detector reported only the existing Inter font choice; it is intentionally
retained from the established workbench, with no font download. No new screenshot binary is added
outside the existing archival custody policy.

## Limitations and owner decisions

| Requirement | Status |
|---|---|
| Recorded static/local technical presentation | PASS within tested Chromium/source/platform bounds |
| Own-source license and content/dependency redistribution rights | BLOCKED: owner/legal decision; no license selected |
| Judge application-access acceptance | BLOCKED / NOT VERIFIED: R2 official-source ledger preserved; a GitHub/static URL is not assumed compliant |
| Actual video, captions, final application assets | PARTIAL: storyboard/checklist ready; recording and final timed captions not produced |
| Manual auditory screen reader, independent novice install, physical mobile browser, Safari/Firefox | NOT TESTED |
| Public native solver / interactive deployment | BLOCKED and outside scope; no tunnel or exposed worker |
| Write-enabled publication, wallet, signing, spending or transactions | Unsupported; no path added |

The inherited R2 source observations are not a fresh organizer confirmation. This work
performs no personal-browser Computer Use action and does not bypass the earlier URL
confidence restriction. Automated isolated browser checks are separate permitted tests.
Historical evidence remains historical; cross-platform native engine pins can differ and
must never be overridden to make a recording appear current or compatible.

Recommended minimum: owner clears rights and confirms the access arrangement, a human
checks fresh installation and screen-reader behavior, then records the captioned local/
recorded walkthrough and supplies an exact source pin plus inert evidence presentation.
Any hosting, redistribution, license choice or submission needs separate owner action.
Stop here: no tape-out or authorization-architecture implementation is begun.
