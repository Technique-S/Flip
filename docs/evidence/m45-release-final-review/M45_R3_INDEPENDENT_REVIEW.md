# M4.5-R3 — Independent static showcase and release review

**Reviewer role:** independent supporting verification engineer (OpenCode / HY4 Flash).
**Status:** review complete. No merge, deploy, publish, submission, signing, wallet or transaction action was performed.
**Write ownership observed:** only `docs/evidence/m45-release-final-review/` and `fixtures/m45-release-final-review/` on branch `opencode/flip-m45-release-final-review`.

---

## 1. Exact tested SHAs and later changes

| Item | Value | Verification |
|---|---|---|
| Review branch | `opencode/flip-m45-release-final-review` | created from the target SHA in a dedicated worktree |
| **Target head (exact)** | `1783b61fefc41007b745753b09c4e0e70a8af7f7` | `git rev-parse origin/codex/flip-m45-release-package` = target SHA; `git cat-file -t` = commit |
| Target commit | `release: prepare inert historical showcase and source package guides`, committer `OpenCode HY4 Flash <opencode@flip.local>`, 2026-11-23 00:18:22 +0100 | `git show -s` |
| Commits after target on branch | **0** | `git rev-list --count 1783b61..origin/codex/flip-m45-release-package` = `0` |
| **Previous fixtures head (exact)** | `82e25deef9ae3498f837e188a7faed0ed61cd7ff` | `git rev-parse origin/opencode/flip-m45-release-acceptance` = fixtures SHA; `git cat-file -t` = commit |
| Fixtures commit | `docs(m45-release): independent release acceptance materials`, 2026-11-22 23:59:56 +0100 | `git show -s` |

Both specified SHAs match the branch heads exactly. **No later changes** exist on the target branch after the initial SHA, and no later changes on the fixtures branch after the previous fixtures SHA. Baselines referenced by the release (`b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b` accepted runtime; `39df7af4c2784502d243e6cc00be43fa84b5799b` reviewed R2) were confirmed to exist as commits.

Repository-level AGENTS.md was read before any file write; its constraints (stay in allowed paths, never mislabel structural validation as publication, no signing/publication, preserve immutable evidence, no direct merge to main) were followed.

---

## 2. Executed commands (observed outcomes)

All commands run from `C:\Users\Kazi\Documents\Flip\flip-m45-release-final-review` unless noted. Environment: Windows x64, Node `v24.18.0`, npm `11.16.0`, Python `3.14.6`, `gh 2.96.0`; `uv` is **not installed** in this environment.

| Command | Exit / observed result |
|---|---|
| `git fetch origin --prune` | 0 |
| `git rev-parse` / `git cat-file -t` / `git rev-list --count` on both SHAs | exact values in §1; count 0 |
| `git worktree add -b opencode/flip-m45-release-final-review … 1783b61` | 0; 883 files checked out at exact SHA |
| `node apps/showcase/build.mjs` | 0 — `Built 19 deterministic static files; no client JavaScript, backend, native proof or network.` |
| `node apps/showcase/build.mjs --check` | 0 — byte-identical rebuild |
| `node scripts/check_m45_release_package.mjs` | 0 — `PASS: 19 checksummed inert files, 110 local links; no scripts, server, imports, native binaries, RPC, wallet or publication surface.` |
| `python <independent_hash_check.py>` (own SHA-256 implementation) | 0 — `ALL_INDEPENDENT_HASH_CHECKS_OK`; 19 files, 18 checksum entries; manifest SHA `0d4161ac…6029` matches pinned `lib.mjs` value; BUILD capabilities all false; inventory cross-check OK |
| `python <static_security_scan.py>` | 0 — `STATIC_SECURITY_SCAN_OK`; extension counts `{css:1, html:7, json:10, txt:1}`; no symlinks/executable magic/active elements/non-local hrefs/CSS `@import` or `url()` |
| `node <escaping_check.mjs>` | 0 — `ESCAPE_OK`; hostile `<img onerror>` string escaped to entities; table cells inert |
| `python <native_ref_scan.py>` | 0 — only inert recorded strings `Minisat`/`solver_worker.py` in recorded JSON metadata; no `pysat`, `spawn(`, `Worker(`, `wasm`, `import(` or `FLIP_LOCAL_SOLVER` executable references |
| `python <claim_integrity_check.py>` | 0 — `ALL_CLAIM_INTEGRITY_CHECKS_OK`; 12/12 cases PASS; 25 displayed values match artifacts |
| `gh api repos/Technique-S/Flip/commits/1783b61…/check-runs` | both matrix check runs `conclusion: success` (URLs in §7) |
| `git -C …/repo diff --name-status b537eb6 1783b61 -- docs/schema/ apps/web/ packages/ uv.lock apps/web/package-lock.json fixtures/ docs/evidence/` | **empty** — frozen paths byte-identical |

Harness scripts are preserved under `fixtures/m45-release-final-review/harness/`; JSON results under `fixtures/m45-release-final-review/`.

**Not executed locally (explicit UNKNOWN/NOT VERIFIED, not inferred pass):** `uv sync --locked`, pytest suite, Ruff lint/format, schema `--check` exports, 27 production Chromium tests, `node apps/showcase/test.mjs` (local attempt in the CI subagent failed `MODULE_NOT_FOUND` because `apps/web/node_modules` is absent), clean-novice install, human screen-reader session, Safari/Firefox, physical assistive devices. These were independently confirmed *remotely* via the exact-head CI run (§7) and the uploaded `showcase-results.json` artifacts; I did not read every raw CI log line.

---

## 3. A — Static security (generated output, not only source)

Artifact build: 19 deterministic files = 7 HTML + 1 CSS + 10 JSON + 1 TXT. `dist` is gitignored; the builder rejects unexpected files and symlinks. My independent SHA-256 implementation reproduced every entry in `CHECKSUMS.json`, the recording-manifest pin, the `BUILD.json` source hashes and the release inventory (including the documented CRLF→LF normalization convention). Zero mismatches.

| # | Required check | Observation | Verdict |
|---|---|---|---|
| A1 | No client JavaScript | 0 `<script>` elements on all 7 pages; 0 `on*` attributes / `javascript:` URLs; `BUILD.json` capability `clientJavaScript:false`; injected API probes never fired | PASS |
| A2 | No executable imported artifacts | Extensions only `.html/.css/.json/.txt`; no symlinks, no MZ/ELF/Mach-O/PK magic; no `import(`, `spawn(`, `Worker(`, `wasm`, `FLIP_LOCAL_SOLVER` references; `Minisat22`/`solver_worker.py` occur only as inert recorded data in historical JSON | PASS |
| A3 | No backend / solver / RPC / wallet calls | CSP `connect-src 'none'`; zero `fetch`/XHR/WebSocket/EventSource/beacon/wallet-provider calls under instrumentation; zero `/api/`, `127.0.0.1`, localhost, WS or RPC requests; no server/API route in the package | PASS |
| A4 | No external network requests | 12 CDP-observed requests with JS enabled and 12 with JS disabled, **all** `file:///…/apps/showcase/dist/…`; zero http/https; zero external CSS (`@import`/`url()` absent), fonts, images or telemetry | PASS |
| A5 | No hidden publication controls | 0 forms/inputs/buttons/iframes/objects/embed/media/svg; `BUILD.json` capabilities `publication:false`, `wallet:false`, `rpc:false`, `backend:false`, `nativeSolver:false`; evidence page states "There is no publication control here" | PASS |
| A6 | No unsafe links / active content | All `href` values local relative paths or `#main`; checker confirmed 110 local links with no scheme-relative, absolute, escaped or percent-encoded paths and no broken fragments | PASS |
| A7 | No unexpected generated files | Exactly 19 expected files; builder and checker reject extra/stale files; `--check` proven fail-closed by the CI subagent's tamper probe (modified `dist/index.html` → exit 1, then restored) | PASS |
| A8 | CSP and file-integrity restrictions | Meta CSP on every page: `default-src 'none'; script-src 'none'; connect-src 'none'; style-src 'self'; object-src 'none'; frame-src 'none'; worker-src 'none'; media-src 'none'; base-uri 'none'; form-action 'none'`; `<meta name="referrer" content="no-referrer">`; all hashes re-derived independently | PASS |
| A9 | No untrusted HTML injection | Builder's `text()`/`code()`/`table()` escape `& < > " '`; independent node check escaped `<img src=x onerror="attack()">` to entities and rendered hostile table strings inert; tampered recording rejected by pinned byte/hash checks | PASS |
| A10 | No silent substitution of archived evidence | Recording manifest pins SHA-256 of all 7 inputs and declares `sourceReceiptSha256`/`sourceReplayRequestSha256`; I verified those equal the curated `receipt.json`/`replay.request.json` bytes, and all 25 displayed witness/hash/correction/revision/evidence values equal the accepted artifact JSONs (§4). **Limitation:** the original R2 browser-journey source files were not locatable as separate local artifacts in the available worktrees/QA dirs or git object history, so the "copied byte for byte" historical claim rests on the manifest's pinned declaration rather than an independent original-vs-copy diff. No evidence of substitution was found. | PASS with INFO limitation |

A source scan alone is **not** treated as runtime proof: A1–A9 were corroborated with a real Chromium session under both JS-enabled and JS-disabled conditions (§5).

---

## 4. B — Claim integrity (12 negative cases + artifact cross-check)

Executed the 12 synthetic misleading-claim cases from `flip-m45-release-acceptance@82e25de…:fixtures/m45-release-acceptance/claim-negative-cases.json`. The fixture explicitly declares itself `SPECIFICATION_ONLY / INVENTED_TEST_INPUT`; this review is the first recorded execution against the built artifact. Method and per-case observations are in `fixtures/m45-release-final-review/claim-case-results.json`.

| Case | Category | Verdict | Key observed counter-evidence |
|---|---|---|---|
| N-01 | Misleading CURRENT | PASS | No affirmative CURRENT claim; only negations ("No current-chain or authorship claim"; "not authorship, current chain state or signing permission"); freshness = HISTORICAL |
| N-02 | Equivalent from vectors | PASS | "Four declared vectors illustrate the interface; they are not a universal equivalence proof" |
| N-03 | Equivalent from checksum | PASS | "File checksums detect byte changes … not authorship or truth"; "Integrity is not proof authority" |
| N-04 | Deployment claim | PASS | "Publication is outside this showcase"; no deployed/published text; no signing capability |
| N-05 | Correction from preparation | PASS | Distinct propose/verify/apply; "separate verify and apply operations" |
| N-06 | Stale evidence as current | PASS | Freshness HISTORICAL; preserve old evidence, never override engine pins |
| N-07 | UNKNOWN relabeled | PASS | "A live timeout would be UNKNOWN. No such computation occurs in this showcase" |
| N-08 | Unique defective wire | PASS | "does not prove which wire is uniquely defective"; `Unique fault claim: false`; AMBIGUOUS_MULTIPLE_CAUSES |
| N-09 | Engine identity ignored | PASS | Native runtime SHA displayed; changed engine requires fresh local evidence |
| N-10 | Partial catalog as complete | PASS | No registry/catalog completeness claim in the package |
| N-11 | Wallet/publication success | PASS | "No backend, native solver, wallet or RPC connection"; "no wallet, signer, RPC client, transaction path or permission grant"; zero probe calls |
| N-12 | Metadata as authority | PASS | Hashes are "not authorship, current chain state or signing permission"; "does not select or modify a project" |

**Result: 12/12 rejected or relabeled by the implementation's own text; no misleading claim survives.** No page claims CURRENT chain evidence, newly deployed circuits, live solver execution, correctness beyond reference-relative equivalence, unique defective-wire localization, automatic correctness of a candidate correction, human-approved transaction execution, onchain publication, or actual adoption/revenue.

**Independent value comparison:** 25/25 displayed values matched the accepted artifacts — witness `REF_BEAT_REPRODUCED`, input `01` → reference `01` / candidate `10`, coverage `EXACT_STATELESS_PAIRWISE`, engine/request hashes, `Minisat22`/`SAT`, diagnostic `AMBIGUOUS_MULTIPLE_CAUSES`/`uniqueFaultClaim=false`, `VERIFIED_CORRECTION` with `EQUIVALENT`/`UNSAT`, Portable 1.1 schema/parent/revision hashes, evidence verdict/coverage/timestamp/content hash/limitations, and both recorded SHA pins. Zero mismatches.

---

## 5. C — User experience and accessibility (real Chromium)

Browser-use local Chromium (isolated temp profile) with CDP `Network`/`Runtime`/`Log` domains enabled, file URLs, offline emulation where noted.

- **Navigation:** all seven pages visited via "Next recorded step:" links with JS enabled; each URL, `<h1>` and `aria-current="page"` matched the expected step. With JS disabled, all seven pages were navigable by focusing the Next link and pressing Enter.
- **File links:** revision page link `artifacts/project.json` opened offline to the exact packaged JSON (8,944 browser chars = 8,944 disk chars); all eight evidence download links opened offline to their exact local files. The package does **not** claim forced-download behavior (documented troubleshooting agrees).
- **Keyboard/focus:** first Tab focused `A.skip "Skip to the recorded step"` with a visible `solid 2.4px rgb(0,85,204)` outline; Enter moved focus to `main#main` with visible outline; native `<details>` `<summary>` opened with Enter (JS disabled).
- **Accessible table semantics:** all data tables use `<caption>`, `<th scope="col">` and `<th scope="row">`; scope-attribute counts per page: index 5, composition 12, difference 6, connections 12, correction 11, revision 9, evidence 0 (no table). Axe confirms no table violations.
- **Screen sizes:** at 320px and 390px, all seven pages had `scrollWidth <= innerWidth` (305≤320, 375≤390) — no horizontal overflow. Reduced-motion emulation (`prefers-reduced-motion: reduce`) produced `animationName: none` on all seven pages at both widths.
- **Refresh / offline:** `Page.reload` on `evidence.html` with networking emulated offline returned the same URL/title and RECORDED text. No storage writes: `localStorage` and `sessionStorage` lengths were 0 before and after all interactions.
- **Automated accessibility:** axe-core 4.14.1, tags `wcag2a`, `wcag2aa`, `wcag21aa`, all 7 pages at 1036px and 390px: **0 violations, 0 incomplete**, 18–20 passes per page. Visual inspection of a rendered page confirmed the RECORDED/HISTORICAL banner, current-step nav state and readable link layout.
- **Runtime security:** JS-enabled traversal injected probes for `fetch`/XHR/WebSocket/EventSource/beacon and `window.ethereum`/`window.solana`; **zero calls** recorded; 0 page errors; 12 requests all local `file://`. JS-disabled traversal: 12 requests all local `file://`.

**Required caveat:** automated browser/axe checks **cannot replace a human screen-reader session**, a novice first-install study, or physical assistive-device testing. The release docs themselves record those as NOT PERFORMED; this review did not perform them either.

---

## 6. D — Release documentation

Reviewed with a dedicated subagent (full evidence: temp scratch report summarised here; key file/line citations below) and spot-checked independently.

| Area | Verdict | Evidence |
|---|---|---|
| README install instructions | PARTIAL | `README.md:39-47` clone/`b537eb6` pin/uv/npm steps present and correctly ordered for Windows x64 and Linux; but the R3-only pin is missing (finding F-01) |
| Versions/dependency requirements | PASS | `README.md:30-33`, `M45_R3_PACKAGING.md:17-25`; enforced by `.python-version`, `pyproject.toml` (`==3.14.6`, uv `==0.9.11`); locks present and hashed |
| Windows/Linux commands | PASS | PowerShell `$env:FLIP_LOCAL_SOLVER='1'` vs Linux `FLIP_LOCAL_SOLVER=1`, both with `--frozen` (`README.md:56-65`); loopback launcher guards in code |
| Solver opt-in | PASS | `README.md:54-70`; five code gates require `FLIP_LOCAL_SOLVER == "1"`; "not wallet authorization" stated |
| Supported feature list | PASS | `README.md:12-23,166-167`; explicit unsupported list `:168-171` |
| Unsupported publication claims | PASS | "Flip does not publish circuits" (`:6`); STOP_AUTHORIZATION terminal (`:23,111-112`); hash ≠ authority (`:87`); structural validation never labeled publication |
| Historical evidence limitations | PASS | `README.md:154-160`, `M45_R3_PACKAGING.md:88`, `M45_R3_HANDOFF.md:98-102`; engine pins must never be overridden |
| Troubleshooting | PASS | `M45_R3_PACKAGING.md:77-94` (14 rows), including static JSON link behavior and cross-OS evidence rejection; `:96-98` honestly lists manual checks NOT PERFORMED |
| Asset/checksum inventory | PASS | `M45_R3_ASSET_INVENTORY.json` binds locks, static sources, recordings, all-false capabilities and 18 output checksums + hashed `CHECKSUMS.json`; my independent hash check matched |
| Third-party license notices | PASS | `M45_R3_PACKAGING.md:59-75` inventory with explicit "not a license text bundle"; no root LICENSE; Python/Node license metadata preserved. **No source license was chosen or recommended — owner/legal decision only.** |
| Handoff / storyboard honesty | PASS | `M45_R3_HANDOFF.md:86-107` marks license/judge access BLOCKED, video PARTIAL, manual checks NOT TESTED; `M45_R3_DEMO_AND_CHECKLIST.md:1-5` is explicitly a draft storyboard; no adoption/revenue/video claims |

No HIGH-severity documentation finding; no false publication, wallet, revenue or video claim found.

---

## 7. E — Regression and CI

- **CI for exact head:** PASS/VERIFIED independently via `gh api …/commits/1783b61…/check-runs`: `contracts (ubuntu-latest)` id `137393711513` and `contracts (windows-latest)` id `137393711190`, both `status: completed`, `conclusion: success`, run `45082540732` (`M1 contracts`, 2026-11-22T23:18:32Z). Every step in both jobs reported `success`, including `uv sync --locked`, `npm ci`/lint/build, `npm test`, the four additive static-showcase steps, Ruff, all schema `--check` exports, pytest, acceptance checks, three Node canonical-parity gates, `check_m1_repository.py --require-clean`, smoke/benchmark scripts. Uploaded artifacts contain `showcase-results.json` with `commitHash 1783b61…`, 6 expected / 0 skipped / 0 unexpected / 0 flaky / 0 retries on both OSes. Only annotations are benign Node-20 deprecation notices. Workflow history shows the static steps were added only at `1783b61` with no pre-existing gate removed.
- **Static showcase checks:** PASS locally (3 commands exit 0) plus fail-closed `--check` tamper probe (§2).
- **Production Python/browser checks:** NOT VERIFIED locally (uv, `.venv`, `apps/web/node_modules` absent); PASS remotely for the exact head per CI step conclusions and downloaded artifacts. This distinction is explicitly preserved.
- **Custody/credential scan:** `scripts/check_m1_repository.py` (stdlib-only) completed locally with exit 0 — 883 tracked files scanned, `credential_pattern_findings: 0`, `result: PASS`; CI ran the same with `--require-clean` successfully. Read-only grep found only defensive scanner code and an RPC credential-rejection guard, no stored secrets. A source scan is **not** treated as proof of browser runtime.
- **Frozen schemas/previous evidence:** PASS — `git diff` against both `b537eb6` and `39df7af` was **empty** for `docs/schema/`, `apps/web/`, `packages/`, `uv.lock`, `apps/web/package-lock.json`, `fixtures/` and `docs/evidence/`. Full diff shows only 3 modified presentation files (`.gitattributes`, workflow, README) and additive showcase/release files; no legacy gate removed, no dependency/file-size exemption added.

---

## 8. Remaining release blockers and severity classification

Severity scale: **HIGH** = security/claim/runtime defect requiring rejection; **MEDIUM** = material release-usability or process gap; **LOW** = minor accuracy/consistency issue; **INFO** = limitation or caveat, no defect found.

| ID | Severity | Finding | Owner action |
|---|---|---|---|
| F-01 | **MEDIUM** | The exact R3 delivery SHA is referenced but never actually stated in the release docs: `README.md:50` says it is "given in its handoff", but `M45_R3_HANDOFF.md:6-8` deliberately omits its own hash and `M45_R3_PACKAGING.md:12-13` supplies no value. I confirmed by grep that `1783b61…` appears in **no** release doc. A reader following `README.md:42`'s `b537eb6` pin gets the accepted runtime but not `apps/showcase` or the R3-only commands. | Publish the pin in a separate, non-self-referential delivery record and cross-reference it unambiguously before release. |
| F-02 | **LOW** | `M45_R3_DEMO_AND_CHECKLIST.md:28` marks source-pinned Windows/Linux instructions `[x]`, which overstates completion given F-01. | Reword after F-01 is fixed. |
| F-03 | **INFO** | Original R2 source files behind the "copied byte for byte" provenance declaration were not independently locatable in the available local trees/git objects; provenance rests on the manifest's pinned hashes. No substitution evidence found. | Retain the originals with the archived evidence for an independent original-vs-copy diff if strict provenance is required. |
| F-04 | **INFO** | Human screen-reader, novice-install, Safari/Firefox and physical assistive-device testing were not performed by this review (nor by the release package). | Human checks required before any accessibility claim. |
| F-05 | **INFO** | CI emits benign Node-20 deprecation annotations; inventory hashes use documented CRLF→LF normalization; validation counts are self-reported but internally consistent. | Auditors apply the stated normalization; no defect. |

**No HIGH-severity finding.** No security, claim-integrity, UX or regression defect was observed within the tested bounds. Blockers that are explicitly owner decisions and were **not** taken by this review: own-source license selection, third-party/content rights clearance, hosting/organizer-confirmed judge access, final captioned video and manual submission. These are documented as BLOCKED/NOT TESTED in `M45_R2_READINESS_AUDIT.md`, `M45_R3_HANDOFF.md` and the demo checklist. This review did not choose a license.

---

## 9. Recommendation

**CONDITIONAL PASS.**

Rationale: the exact target implementation meets the static-security (A), claim-integrity (B), browser/accessibility (C), documentation (D) and regression/CI (E) requirements within the conditions actually tested, with R3 CI green on the exact head and zero frozen-schema/evidence changes. Conditions attached to the PASS are: (1) remedy F-01 (and consequently F-02) so the R3 delivery pin is actually obtainable from release documentation; (2) keep the owner/legal decisions (license, rights, hosting/judge access) and the human screen-reader/novice checks as explicit pre-release gates; (3) preserve the archived originals referenced in F-03 if strict provenance verification is required. None of these conditions was performed or waived by this independent review.

**Stop here:** no merge, deploy, publish, host, submit, sign, wallet connection, transaction or tape-out action was performed.
