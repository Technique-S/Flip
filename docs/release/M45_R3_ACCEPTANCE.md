# M4.5-R3 — Acceptance preparation record

Later integration: see the [R3-E documentation resolution and integration record](M45_R3_MERGE.md)
for the independent conditional acceptance, F-01/F-02 fixes and preserved F-03 limitation.
The preparation snapshot below is retained with its original execution history.

Prepared 2026-11-23. **Independent acceptance: PENDING. Stop before merge or release.**
The seven-page showcase is a curated recorded presentation, not an interactive proof
engine or a continuous video. Opening pages displays saved results; it computes no proof.

## Exact revisions and scope

| Role | Exact Git SHA |
|---|---|
| Accepted main, fetched and confirmed | `b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b` |
| Original R3 delivery, fetched and tested | `1783b61fefc41007b745753b09c4e0e70a8af7f7` |
| Preserved OpenCode research | `82e25deef9ae3498f837e188a7faed0ed61cd7ff` |
| Acceptance test/source revision tested locally | `a5c9a73abcacd2eb6aa519852c5b9667502749f3` |
| Historical R2 audit / recording source | `39df7af4c2784502d243e6cc00be43fa84b5799b` |

This document is added after testing the acceptance test/source revision. Its containing
commit is documentation only; obtain its exact head from the draft PR and verify
`git rev-parse HEAD`. A document cannot embed its own containing commit SHA. Final-head
CI must be checked separately; a successful older run does not establish a newer head.

The change inventory against accepted main comprises the rewritten source-setup README;
seven R2 release records; the separate HTML/CSS generator, seven recording JSON inputs
and provenance manifest, tests and guide under `apps/showcase`; four original R3 release
guides/inventory and an offline example request; the release integrity checker; additive
CI build/check/browser steps and report upload; line-ending rules; nine unchanged
OpenCode research files; the new acceptance tests; and this document. Generated `dist`
and local QA outputs remain ignored. No dependency was added.

Ownership: Codex owns the presentation, integration, release docs and test harness.
OpenCode owns the original research/specifications in
`docs/evidence/m45-release-acceptance`. Its three original fixture files are archived
under `original-fixtures/`, outside the production fixture namespace; the test maps
those paths to `fixtures/m45-release-acceptance` at the research SHA.
Those nine files were copied from the exact research SHA without rewriting conclusions.
Their historical statements such as "no viewer exists" and `SPECIFICATION_ONLY` describe
that earlier review. They are not a new review of R3. The custody test compares every
file with its original Git blob. The fixture SHA-256 is
`c50aa3012f228ecbfc09c56f2415f38cb3adaa5b739adc3f4b799f21bbce988f`.

Production `packages`, `apps/web`, `docs/schema`, `uv.lock` and `pyproject.toml` match
accepted main exactly. Existing evidence and fixtures from main are unchanged; the
research files are additions. Original R2/R3 release records and recording bytes are
unchanged from the delivery. No production verification semantics or prior CI gate was
changed. No confirmed original-delivery defect was found. The preparation introduced one
fixture-placement defect, reproduced and corrected as described below; no runtime
or showcase behavior was changed.

## Executed checks

Local environment: Windows x64, Node 24.18.0 and CPython 3.14.6, existing locked
development environment. `uv` was unavailable on this terminal's PATH; native checks used
the existing `.venv/Scripts/flip.exe`, not a new install. No clean-install claim is made.

| Check | Observed outcome |
|---|---|
| Delivery static build, deterministic `--check`, integrity scan | PASS: 19 files, 110 local links |
| Delivery showcase suite | PASS: 6/6 |
| Acceptance source build, `--check`, integrity scan | PASS: same static output and inventory |
| Initial acceptance source Chromium suite | PASS: 19/19 at `8bcb1f2bbf65ed620a223a2c6207eac9ee0e9b47`, no skips/retries; 49.9 seconds |
| Corrected acceptance source Chromium suite | PASS: 19/19 at the corrected source revision, no skips/retries; 2.0 minutes |
| Fixture-placement regression test | Reproduced failure locally, then PASS after relocation (1/1, 4.57 seconds); existing runtime test unchanged |
| Negative claim cases N-01 through N-12 | PASS: 12 individually reported cases, two rejection paths each, DOM observations on all seven pages |
| Research custody | PASS: all nine original Git blobs identical |
| Native candidate comparison | DIFFERENT, exit 1; input `01`, reference `01`, candidate `10`, `REF_BEAT_REPRODUCED`, HISTORICAL |
| Native corrected evidence replay | PASS, exit 0, EQUIVALENT / UNSAT, HISTORICAL; original evidence retained |
| Production equality | PASS: empty Git diff against accepted main for the protected paths above |
| Local archival repository checker | PASS: clean checkout; 893 tracked files, 14 registered raw/derived blobs and prior review custody verified; zero credential-pattern findings |
| Delivery remote CI | PASS: [run 45082540732](https://github.com/Technique-S/Flip/actions/runs/45082540732), exact delivery SHA, Windows and Ubuntu success; completed 2026-11-22T23:28:09Z |
| Initial acceptance source remote CI | FAIL: [run 45127865959](https://github.com/Technique-S/Flip/actions/runs/45127865959) at `8bcb1f2bbf65ed620a223a2c6207eac9ee0e9b47`: Ubuntu 701 passed / 1 failed, Windows cancelled by fail-fast |
| Corrected acceptance source remote CI | PASS: [run 45128594426](https://github.com/Technique-S/Flip/actions/runs/45128594426), exact corrected source revision above; Windows and Ubuntu success, including full Python/production browser, showcase, schemas, custody and smoke gates |

The original delivery CI did not fail. The initial preparation run failed
`test_report_only_gaps_are_not_executable_golden_fixtures`: adding synthetic research
JSON under `fixtures/` violated its existing restricted corpus namespaces. Running
that exact pytest node locally reproduced the failure (1 failed in 4.95 seconds).
The correction moves the three original files byte-for-byte to the release evidence
archive and updates only the new custody/claim harness paths. No historical evidence,
production test, corpus allowlist, gate, timeout or conclusion was weakened.
Native replay and the full local custody scan above ran at the initial acceptance
revision, with the same unchanged runtime/recordings. Full Python/production browser
regression for the delivery was observed in that remote
matrix, not rerun locally in this preparation. Latest final-head CI is a separate merge
gate shown on the PR. This record is not independent approval.

## Reviewer reproduction

Use a full Git clone, with the research object available for the custody test:

```sh
git clone https://github.com/Technique-S/Flip.git
cd Flip
git fetch origin main codex/flip-m45-release-package opencode/flip-m45-release-acceptance
git checkout a5c9a73abcacd2eb6aa519852c5b9667502749f3
git rev-parse HEAD
git diff --exit-code b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b HEAD -- packages apps/web docs/schema uv.lock pyproject.toml
node apps/showcase/build.mjs
node apps/showcase/build.mjs --check
node scripts/check_m45_release_package.mjs
npm ci --prefix apps/web
npm exec --prefix apps/web -- playwright install chromium
node apps/showcase/test.mjs
```

Repeat on the exact PR head for acceptance. Node alone suffices to build/view; browser
QA dependencies need installation network access. The tests navigate offline `file://`
URLs and start no API server. Open `apps/showcase/dist/index.html` directly and follow
Sample → Composition → DIFFERENT → Connections → Correction → Portable revision →
Evidence. Retain the entire directory for local inspection.

The existing six tests verify the file-only request log; zero fetch/XHR/WebSocket/
EventSource/beacon/wallet-provider calls; no executable inputs; CSP script/connection
denials; artifact equality; recording tamper rejection and HTML escaping; keyboard
skip/step/disclosure behavior with JavaScript disabled; reduced motion; axe at 1280px
and 390px across all pages; and the 320px evidence overflow check. They do not establish
manual screen-reader speech, physical-device behavior or universal browser support.

The new `acceptance.spec.mjs` runs the twelve original synthetic claims individually.
Each is inserted into a source alias that would be displayed on the sample page.
The real builder rejects changed recording bytes, then rejects a rewritten manifest
even when the attacker updates its length and checksum. No forged HTML is generated.
All seven original offline pages are inspected for absence of the claim and presence
of RECORDED/HISTORICAL. Per-case JSON attachments record the input hash, rejection
messages, expected assertion and observed DOM state in `.test-tmp/r3/showcase-results.json`;
CI uploads that report in each OS artifact.

This is an enforced immutable-input boundary, not a semantic claim classifier or a
new proof of the hypothetical assertions. Supporting current-product semantics remain
in the unchanged production tests. General arbitrary-recording import is unsupported.
Changing the builder's trusted pins requires separate review.

For full repository custody, in a clean configured source checkout:

```sh
uv sync --locked
uv run --frozen python scripts/check_m1_repository.py --require-clean
```

## Witness, correction and source custody

The [recording manifest](../../apps/showcase/recordings/manifest.json) binds the accepted
runtime and R2 source, each JSON file's exact size/hash, curation method and environment.
DIFFERENT was recorded at `2026-11-22T09:33:20.694541+00:00`; EQUIVALENT at
`2026-11-22T09:33:29.641011+00:00`; curation at `2026-11-22T22:56:48.477957+00:00`.
Receipt SHA-256:
`b651a99486cbb6c7b053087b94ac9072f7dd9b0d4aae307b03e700441455c730`.
Replay-request SHA-256:
`2b77b5c59b07c2e135a55b805112c364ce87bde7bf64370b728c881b423ea46c`.

The receipt, portable revision and replay request are the preserved R2 journey outputs;
candidate/corrected execution requests, evidence extraction and compiled composition
are identified as supporting curation inputs. Reference: 81 bytes / 8 gates. Actual
different candidate: 109 bytes / 12 gates; it is not merely an output-swap example.
The [asset inventory](M45_R3_ASSET_INVENTORY.json) binds recording/source/static hashes.
Earlier scratch QA paths in that inventory are historical references, not a promise
that another clone contains those ignored files; reproduce fresh QA with the commands.

On a compatible installed native engine, from the repository root:

```sh
uv run --frozen flip compare --project apps/showcase/recordings/candidate.execution.json --out candidate-review.json
uv run --frozen flip verify-bundle --project apps/showcase/recordings/corrected.execution.json --bundle apps/showcase/recordings/evidence.json
```

Use a fresh output filename. The first command's exit 1 is the expected DIFFERENT
result. A platform engine mismatch must remain a rejection; retain historical evidence
and generate separately named local evidence. Never edit hashes or override identity
checks to make a replay pass. Static checksums establish byte custody, not proof,
authorship, current-chain freshness or authority.

Source setup and distribution details: [README](../../README.md),
[packaging guide](M45_R3_PACKAGING.md), [showcase guide](../../apps/showcase/README.md),
[R3 handoff](M45_R3_HANDOFF.md) and [demo checklist](M45_R3_DEMO_AND_CHECKLIST.md).
Exact review source: [tested tree](https://github.com/Technique-S/Flip/tree/a5c9a73abcacd2eb6aa519852c5b9667502749f3).
Original research: [immutable tree](https://github.com/Technique-S/Flip/tree/82e25deef9ae3498f837e188a7faed0ed61cd7ff).

## Outstanding acceptance and release gates

| Gate / owner | Status |
|---|---|
| Independent review of final PR head, all current CI and evidence | PENDING; no approval claimed |
| Own-source license, contributed/content rights and notices / owner | BLOCKED; no license selected or redistribution approval inferred |
| Organizer-confirmed judge-access method and rehearsal / owner | BLOCKED / NOT VERIFIED |
| Human novice install and auditory screen-reader trials / human tester | NOT TESTED; use unchanged [protocol](../evidence/m45-release-acceptance/HUMAN_TEST_PROTOCOL.md) |
| Final captioned video, submission copy, eligibility/contact and rights declarations / owner | PARTIAL / PENDING |
| Source distribution / maintainer and owner | Source-checkout instructions only; no installer or native binary bundle, macOS or wheel-only app promise |
| Public interactive hosting / independent security review and owner | BLOCKED, outside this package |

OpenCode's original [matrix](../evidence/m45-release-acceptance/RELEASE_ACCEPTANCE_MATRIX.md),
[security specification](../evidence/m45-release-acceptance/STATIC_SHOWCASE_SECURITY.md),
[rights inventory](../evidence/m45-release-acceptance/RIGHTS_AND_NOTICES.md) and
[owner decisions O-01–O-12](../evidence/m45-release-acceptance/SUBMISSION_CLAIM_AUDIT.md)
remain unchanged. Automated success does not resolve those human, rights or organizer gates.

No merge, public hosting/deployment, release publication, hackathon submission, license
selection or unapproved native binary redistribution was performed. No wallet, signing,
spending, transaction construction or broadcast capability was added. The native
workbench remains loopback-only with its existing opt-in; static output contains only
HTML/CSS/JSON/text. Stop pending independent acceptance.
