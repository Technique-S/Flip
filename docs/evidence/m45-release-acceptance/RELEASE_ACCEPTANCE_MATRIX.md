# M4.5-R3 — Independent release acceptance matrix

**Status: ACCEPTANCE MATERIALS (specifications plus clearly marked executed checks). Date 2026-11-22.**
**Reviewer: OpenCode / HY4 Flash (support). No release, deployment, hosting, submission or license decision is made here.**

## 0. Baseline and evidence standard

| Item | Value |
|---|---|
| Accepted production main | `b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b` |
| Codex R2 release audit | `codex/flip-m45-release-readiness` @ `39df7af` (documentation only, based on accepted main) |
| Review branch | `opencode/flip-m45-release-acceptance` (created from accepted main) |
| Allowed write scope | `docs/evidence/m45-release-acceptance/`, `fixtures/m45-release-acceptance/` only |
| Production / Codex release branch | Unchanged |

Evidence labels:

- **EXECUTED_NOW** — read-only command run by this reviewer in this session; exact commands and results in `HANDOFF.md`.
- **R2_EXECUTED** — executed and recorded by Codex's R2 audit, not re-run here.
- **SPECIFICATION** — acceptance check prepared for a future artifact; not executed because the artifact does not exist.
- **NOT_TESTED / BLOCKED** — no observation, or a decision/authorization is missing.

No passing check may be relabeled as a judge-access, licensing, accessibility or submission approval.

## 1. Release disposition (unchanged from R2, independently checked for consistency)

| Layer | Status | Basis |
|---|---|---|
| Supported local technical demo | PASS, scoped | R2_EXECUTED 702 Python / 27 Chromium; accepted-main CI; prerequisites and HISTORICAL/native-engine limits remain. |
| Judge access | BLOCKED | Organizer has not confirmed an accepted delivery method; no verified access URL (R2 H3). |
| Submission completeness | PARTIAL | Drafts only; no video, contact fields, final declarations or submitted form. |
| Public interactive deployment | BLOCKED | No authorization, auth/quota/isolation/host review; loopback guards must not be bypassed. |
| Write-enabled publication | BLOCKED | Intentionally absent; `STOP_AUTHORIZATION` is terminal. |
| Manual auditory accessibility / novice trial | NOT_TESTED | Protocols provided here; no human results invented. |
| Own-source license / redistribution rights | BLOCKED | No root license; owner decision required. |

## 2. Acceptance matrix

| ID | Mission task / requirement | Method | Evidence status | Pass condition | Current result |
|---|---|---|---|---|---|
| RA-01 | Static showcase: no native solver calls | Static artifact scan + runtime process observation | SPECIFICATION | No `/api/`, solver worker, PySAT/MiniSat process, `FLIP_LOCAL_SOLVER`, `pysat`, `solver_worker` reference or child process in the viewer artifact or runtime; all verdicts are precomputed | Cannot pass yet: no static viewer exists; current `apps/web/dist` calls same-origin `/api/...` (R2 source observation) |
| RA-02 | Static showcase: no signing/wallet code | Static scan + network capture | EXECUTED_NOW on current frontend source + SPECIFICATION for viewer | No provider objects, wallet SDKs, `eth_sign*`, `personal_sign`, `eth_send*`, key/seed handling, or wallet UI; zero signing/wallet network events | Current frontend source has no wallet/signing code; only disclosure text about "No transaction broadcast" was found. Viewer check pending |
| RA-03 | Static showcase: no write-RPC calls | Allowlist scan + network capture | EXECUTED_NOW on core + SPECIFICATION for viewer | Only read methods `eth_chainId`, `eth_getBlockByNumber`, `eth_call`, `eth_getCode`, `eth_getStorageAt`; no `eth_sendRawTransaction`, `eth_sendTransaction`, `eth_sign*`, `wallet_*`; static viewer makes **no** RPC calls at all | `flip_core/rpc.py` enforces `READ_METHODS` and rejects non-allowlisted methods. No `check_write_rpc_absence.py` script exists (design proposal only). Viewer check pending |
| RA-04 | Misleading CURRENT / EQUIVALENT / deployment / verified-correction claims | Negative fixtures | SPECIFICATION (fixtures provided) | All 12 `claim-negative-cases.json` cases are rejected or relabeled by the reviewed viewer/UI; no fresh-verification or publication claim from recorded data | Fixtures ready; no implementation to execute |
| RA-05 | First-time developer trial | Human protocol, unassisted | NOT_TESTED | Pinned supported OS, prerequisites installed by tester, unassisted task completion, measured times/errors, exit codes and trust labels recorded | Protocol provided; no human trial performed |
| RA-06 | Manual screen-reader speech | Human protocol | NOT_TESTED | Expected vs actual spoken output recorded for navigation, witness tables, correction, UNKNOWN and provenance; focus/live-region behavior checked on supported OS/browser | Protocol provided; R2 automated axe/keyboard tests do not substitute |
| RA-07 | Third-party licensing / notices | Inventory + owner decision | EXECUTED_NOW inventory; BLOCKED decision | Per-component license and notice inventory for the exact distributed artifact; owner selects own-source terms; no invented license | Inventory in `RIGHTS_AND_NOTICES.md`; no root license; no installer SBOM; owner approval missing |
| RA-08 | Draft submission claims vs accepted evidence | Claim crosswalk | EXECUTED_NOW source/R2 cross-check | Each claim has an accepted-evidence reference and an explicit scope qualifier; unsupported claims removed | Crosswalk in `SUBMISSION_CLAIM_AUDIT.md`; several claims need qualifiers or owner confirmation |
| RA-09 | Three-minute video accuracy | Recording checklist | SPECIFICATION | Every scene matches the script's truthful wording; exact commit visible; no wallet/publication/success claims; captions and rights cleared | Checklist provided; no video produced |
| RA-10 | Owner approvals | Decision register | BLOCKED | All named approvals recorded by the owner with dates and exact values | `SUBMISSION_CLAIM_AUDIT.md` §3 and `HANDOFF.md` §5 |
| RA-11 | Final judge-access acceptance | Conditional method-specific checks | SPECIFICATION / BLOCKED | Organizer confirms a permitted method, then the matching checklist passes with a judge rehearsal | `RELEASE_ACCEPTANCE_MATRIX.md` §4 |
| RA-12 | Historical evidence preserved | Git diff + custody | EXECUTED_NOW | Only the two allowed directories differ from accepted main; no original evidence or acceptance check modified | Verified via `git diff --name-only b537eb6..HEAD` before commit (see HANDOFF) |
| RA-13 | No runtime/security regressions introduced by this work | Git scope | EXECUTED_NOW | No production, schema, lockfile or CI file changed on this branch | Verified by git status/diff |

## 3. Mapping to R2 gates

| R2 gate | Independent acceptance item |
|---|---|
| G01, G05, G06, G10, G19, G21 | RA-08 cross-check of accepted claims; RA-12/13 scope checks |
| G02, G03, G16 | RA-05 novice trial and RA-08 README/quickstart claim review |
| G04 | RA-04 "CURRENT/complete registry" negative fixtures |
| G11, G12 | RA-06 screen-reader protocol |
| G13, G14, G15 | RA-10/RA-11 owner approvals and judge-access method confirmation |
| G17, G18, G20, G22 | RA-07 rights/notices and distribution limitations |
| G23, G24 | RA-01/02/03 static-showcase security and STOP_AUTHORIZATION claims |

## 4. Judge-access acceptance checks (conditional on organizer confirmation)

No check below is active until the organizer states which delivery method is accepted. Record the organizer's
answer, date, source and exact wording before running any of them.

### Method A — pinned source checkout + local launcher

1. A tester without prior Flip knowledge clones the pinned revision `b537eb6` and follows the reviewed quickstart.
2. Version checks show CPython 3.14.6, uv 0.9.11, Node 24.18.0 and npm 11.16.0 (or documented compatible pinned versions).
3. `uv sync --locked`, `npm ci --prefix apps/web`, `npm run build --prefix apps/web` exit 0.
4. Native solver opt-in is explained and set **before** launch; without it, native HTTP operations are intentionally unavailable (HTTP 501).
5. Launcher binds only `127.0.0.1`; loopback/TrustedHost/origin checks remain; no tunnel, proxy or `0.0.0.0` binding.
6. Tester completes the offline sample → DIFFERENT witness → declared-prior correction → portable save → CLI replay sequence unassisted.
7. Exit codes are interpreted correctly: DIFFERENT 1, UNKNOWN 2, INVALID_INPUT 3, STALE 7, STOP_AUTHORIZATION 9.
8. Jury evidence includes exact commands, times, failures and screenshots; no claim of live publication or wallet use.
9. Organizer confirms in writing that this arrangement satisfies the access requirement.

### Method B — static recorded-evidence viewer (not built, not hosted)

1. Owner explicitly authorizes the artifact and host; organizer confirms a static recorded display is acceptable.
2. RA-01/02/03 pass on the built artifact: no API calls, no native solver, no wallet/signing, no RPC writes, no backend/worker.
3. Every proof result is visibly labeled `RECORDED` or `HISTORICAL`; no live control claims fresh verification.
4. No `EQUIVALENT` is generated from a checksum, vector-only match or stale report; RA-04 cases pass.
5. Artifacts/downloads are rights-cleared with complete notices; no credentials, personal aliases or private logs.
6. Keyboard and screen-reader checks pass on the supported browser/OS; captions accurate.
7. The access URL works from a neutral network/browser and is verified by a judge rehearsal.

### Method C — downloadable supported distribution

Currently BLOCKED. Requires a tested installer/source bundle with checksums, per-OS QA, complete third-party
notices, upgrade/uninstall guidance and asset paths that do not depend on repository-relative source layout.
A GitHub ZIP is not an installed product (R2 G22).

### Method D — hosted interactive demonstration

Currently BLOCKED. Requires separate authorization and independent target-host review covering host identity,
judge authentication, quotas, aggregate CPU/memory/process isolation, cancellation under abuse, logs/retention,
secrets and operating responsibility. A password on the loopback launcher is not sufficient (R2 G23).

## 5. Gate ownership and stop rule

- Owner: rights/license, entrant/contact/eligibility, access arrangement, final copy/video, hosting, manual submission.
- Maintainer: quickstart correction and any small reviewed documentation patch; curated artifacts with notices.
- Human tester: screen-reader speech and novice trial; judge-access rehearsal.
- Agent: may only prepare documentation/fixtures on this branch. No deployment, wallet, transaction, submission or license choice.

If any BLOCKED/NOT_TESTED item remains, the release is not ready; do not substitute engineering test success for
human, rights or organizer acceptance.
