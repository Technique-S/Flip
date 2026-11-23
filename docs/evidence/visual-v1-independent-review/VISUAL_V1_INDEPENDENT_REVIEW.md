# P7-V1 independent acceptance review

Reviewer: OpenCode (independent adversarial reviewer). Date: 2026-11-23.
Repository: `https://github.com/Technique-S/Flip` · PR: https://github.com/Technique-S/Flip/pull/12
**No merge, deploy, transaction, wallet, hosting, redesign or V2 implementation was performed.**

## Verdict

**FAIL** — V1 is not safe to merge as currently proposed.

The read-only projection itself is sound: all 54 independent projection attack cases, 42 workbench browser tests, 702 Python tests and the full schema/canonical/custody chain pass, and no semantic mutation or network path was found in the Visual view. However, the authorized release-guard scope extension introduces a **provenance-checker bypass**: the checker no longer detects its own tampering, and its pinned historical commit identifier and exception set can be silently retargeted. A coordinated tamper of the frozen static release artifacts plus the release inventory also passes. Per the review mandate, a provenance-checker bypass is blocking.

Separate assessments: (1) V1 merge readiness **NOT READY**; (2) P7 milestone completeness **NOT COMPLETE**; (3) P8 readiness **NOT READY**; (4) public release readiness **NOT READY**. V1 acceptance would not imply P7 or P8 completion in any case.

## A. Repository and scope verification

| Item | Verified value |
|---|---|
| PR head (`refs/pull/12/head`) | `006050d7b8349dca3c263da2e3f1112617706541` |
| Local checked-out review head | `006050d7b8349dca3c263da2e3f1112617706541` |
| Accepted main baseline | `7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f` |
| Approved architecture commit | `39322e49f9fb1aa83a726fe3bbe81921c7e0f21e` |
| Initial V1 implementation | `2d497c93c6365eda5bcdad99f5c439db237139e4` |
| Final visual implementation | `5cd90f99c359ed9a28066295a8e848b79f16744f` |
| Authorized guard integration | `8fa211118689690df81964fb8c3c6e7389e14a0a` |
| PR state | open, `mergeable: true`, `mergeable_state: clean` |

`git merge-base --is-ancestor` returned 0 for both the accepted main baseline and the architecture commit against the PR head. All refs were fetched with `git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'`.

**Diff against accepted main:** 38 files, 8,124 insertions, 155 deletions.
**Production delta against architecture:** exactly 9 files — `apps/web/package.json`, `apps/web/package-lock.json`, `apps/web/src/Composer.tsx`, four new `apps/web/src/visual/*` files, `apps/web/tests/visual-readonly.spec.ts`, `scripts/check_m45_release_package.mjs`, and new `apps/showcase/tests/release-guard.spec.mjs`. The remaining 28 changed paths are documentation under `docs/planning/**`, `docs/ux/visual-v1/results/**` and `docs/milestones/**`.

Git tree/blob equality against accepted main confirmed for: `packages` (Python core/API/CLI) `370b362c…`, `fixtures` `78129e65…`, `.github` `e6d2d0a3…`, `pyproject.toml`, `uv.lock`, `conftest.py`, `apps/web/src/App.tsx`, `apps/web/src/style.css`, `apps/web/src/model.ts`, `apps/web/build.mjs`, `apps/web/playwright.config.mjs`, `apps/web/index.html`, `agent-tasks`. No CI, schema, fixture, verifier, API, CLI or Python core file changed. The sole shared-script change is the separately authorized `scripts/check_m45_release_package.mjs`.

## B. Canonical projection adversarial audit

`src/visual/projection.ts` was reviewed line by line and exercised with an independent 54-case harness (`projection-attack-harness.mjs`; results in `projection-attack-results.json`). **54/54 cases produced the expected result, with the input unchanged in every case.** Details in [PROJECTION_ATTACK_MATRIX.md](PROJECTION_ATTACK_MATRIX.md).

Confirmed properties:
- Nodes are emitted only for `candidate/external`, each ordered entry of `candidate.components`, and `candidate/outputs`. Every edge is derived solely from a canonical `candidate.components[i].inputs[j]` or `candidate.outputs[j]` entry, after the source pin is resolved and range-checked. No visual connection exists without a canonical source relationship.
- NAND requires exactly two scalar inputs; REF requires `nState === 0`, `nIn` inputs, `nOut > 0`, valid chain/schema/processor/circuitId, and an import-manifest root that agrees on identity and interface.
- Order is deterministic: array order preserved, positions derived from index-only levels/rows, no randomness, no Date/Math.random.
- All handles are `in:<decimal index>` / `out:<decimal index>`; edge IDs are `<target>/in/<index>`. The reserved banks (`candidate/external`, `candidate/outputs`) cannot collide with `candidate/component/<instanceId>` because `name()` forbids `/` and leading digits. No edge-ID alias was found.
- Derived output locators resolve to real fields (`candidate.nIn`, `components[i].kind`, `sources[j].nOut`) with a `#out:<index>` fragment; all 5 nodes' 54 pin locators resolve to existing canonical values in the harness.
- Decimal IDs are kept as strings; `9007199254740993` and `18446744073709551615` round-trip exactly; `"0001"`, hex and ≥2^64 are rejected.
- Source and identity objects shown in the inspector are detached copies; pin mappings are object copies. Mutating the projected source, identity or mapping did not change the request.
- Unsupported structures fail closed with a single `Visual view unavailable: … Use Advanced…` message and zero nodes/edges; the browser test confirmed the Advanced view remains usable and no partial graph is rendered.

Two low-severity observations: source alias syntax is not validated (an empty alias is accepted; display remains escaped React text), and the connection/pin budget is checked only after ports/edges are materialized (worst case ~128k objects are created before rejection, still bounded by the ≤500/≤255 pre-checks).

## C. Semantic and state preservation

Independent parity evidence (`docs/ux/visual-v1/results/canonical-parity.json`) was re-read and compared: `before == after` for the stored execution request, `compiledBefore == compiledAfter` for the trusted compose response, including identical `netlist`, `projectHash` `0xff70814e…` and `manifestHash` `0x10a26167…`. The browser test additionally asserted exact `sessionStorage` bytes before/after 2 mode round-trips, preserved Advanced mapping values and "Netlist built" result, and exactly equal trusted compose responses. The Visual pane receives `request` directly; `Composer.tsx` toggles only a local `useState(false)` flag and passes no `change`/`build`/`next` callback into `VisualComposer`. No normalization, recompilation, hidden request or hash recomputation was found in the mode-switch path.

`Composer.tsx:111` places the build result and "Compare circuits →" control inside `<div hidden={visual}>`, so those actions are unavailable while in Visual mode. This is a workflow limitation, not state loss; Advanced restores them unchanged.

## D. Read-only enforcement

Code inspection found no `onNodesChange`, `onEdgesChange`, `onConnect`, `onReconnect`, `onNodesDelete`, `onEdgesDelete` or `onNodeDragStop` callback. `nodesDraggable={false}`, `nodesConnectable={false}`, `edgesReconnectable={false}`, `deleteKeyCode={null}`, all handles `isConnectable={false}`, nodes and edges `deletable:false`/`reconnectable:false`.

An independent browser attack test (`readonly-attack.spec.mjs`, 1/1 pass) actually attempted: node body drag (position unchanged within 2px), source→target handle drag (edge count unchanged), edge endpoint reconnect drag (unchanged), node-select then Delete/Backspace/Ctrl+X/Ctrl+C/Ctrl+V/Ctrl+Z (counts unchanged), inspector select interactions (selection only), 12 rapid Visual↔Advanced switches (counts unchanged), and Shift+wheel over the canvas. Stored request bytes were identical before and after; zero network requests and zero page errors occurred during the Visual session.

## E. React rendering and accessibility

See [ACCESSIBILITY_AND_USABILITY.md](ACCESSIBILITY_AND_USABILITY.md). Automated results: axe zero violations at desktop, 390px and 320px; 42/42 workbench browser tests including StrictMode remount; keyboard component/pin inspection verified; pan, zoom and fit verified by viewport transform change; reduced motion applied. Real screenshots from this review's own reproducible Playwright run were inspected — not the developer's private screenshot path.

Untested by automation: real screen-reader speech, physical touch devices, 200%/400% browser zoom, forced-colors mode, and 100/200/500-node performance benchmarks. These remain P7-V7 items and are not claimed here.

## F. Dependency, licensing and bundle review

- Installed `@xyflow/react` is exactly `13.0.2`, `license: MIT`, with lockfile integrity `sha512-dURQCKhz4TEYc43pp9yY4LeEvC7rmHLPeit396VKA9wSNjda245nA4JTZV3ieekB2dx7kwGjvXQELmsZ0FpVAA==`, lockfile v3, exact root pin. Peers React/react-dom/types ≥18 and Node ≥20; build used React/react-dom 19.3.1, TypeScript 7.0.2, Node 24.18.0.
- `npm ci` reported 0 vulnerabilities and only the expected pending esbuild install-script warning; no allowlist/policy override was needed.
- `src/visual/notices.ts` contains 26 retained runtime notices, including `react-compiler-runtime 1.0.0 (MIT)`. No Pro example hooks/source or competitor assets were found in the visual subtree. No `fetch`/XHR/network call exists in `src/visual/**` or the new Composer code.
- Production build passed. Measured bundle: PR head `flip.js` **567,908 B raw / 177,465 B gzip**; accepted-main baseline built from a clean temporary worktree at `7ecfb9b` **278,735 B raw / 84,711 B gzip** (+103.8% raw, +109.5% gzip). The handoff's "≈568 KB / 177 KB vs 279 KB / 85 KB" claim is numerically accurate, but the >2× initial-JS growth is not accompanied by V7 benchmark evidence.

## G. Independent release-guard security review

Detailed in [RELEASE_GUARD_SECURITY_REVIEW.md](RELEASE_GUARD_SECURITY_REVIEW.md). The shipped seven tests pass (26/26 showcase suite), and the pristine checker passes (19 files, 130 links). Independent adversarial cases found **four accepted tampers that should have been rejected**, including two newly introduced bypasses of the historical provenance mechanism. The pre-PR checker was independently shown to reject its own self-tamper with `Release source drift: scripts/check_m45_release_package.mjs`; the PR-head checker does not. This is the blocking finding.

## H. Regression and exact-head CI — independently executed

| Check | Fresh local result |
|---|---|
| `npm ci --prefix apps/web` | 37 packages, 0 vulnerabilities, exit 0 |
| `npm run lint` | 25 files, 0 findings, exit 0 |
| `npm run build` | exit 0 |
| `npm test` (workbench) | **42 passed**, 0 skipped/failed, 2.4 min |
| `node apps/showcase/build.mjs` + `--check` | 19 deterministic files, exit 0 |
| `node scripts/check_m45_release_package.mjs` (pristine) | PASS, 19 files / 130 links |
| `node apps/showcase/test.mjs` | **26 passed**, 0 skipped/failed, 49.8 s |
| `uv run --frozen pytest -q` | **702 passed**, 523.75 s |
| 9 frozen schema exporters `--check` | 9/9 exit 0 |
| 3 canonical parity checks | 3/3 exit 0 |
| Ruff check / format | 88 files, exit 0 |
| Agent acceptance / portable review / smoke M1 / smoke M3 | 10/10, 26/26, PASS, PASS |
| Independent projection harness | 54/54 expected, 0 failures |
| Independent read-only browser attack | 1/1 pass |
| Independent release-guard attacks | 4/6 unexpectedly PASSED (blocking) |

Exact-head hosted CI verified through the GitHub API at head `006050d7…`: workflow runs `45182811594` and `45182820732`, each with `contracts (ubuntu-latest)` and `contracts (windows-latest)` — **all four jobs `conclusion: success`**. The earlier failed runs `45181066145` / `45181184502` were at `cfb68b4…`, not at the final head, matching the handoff's retained-failure account. No previous run was counted as a new local result.

Custody/credential check (`scripts/check_m1_repository.py --require-clean`) is reported in [FINAL_HANDOFF.md](FINAL_HANDOFF.md) after the review branch commit, because `--require-clean` rejects any untracked evidence file.

## I. Findings

| ID | Severity | Location | Impact | Correction |
|---|---|---|---|---|
| RG-01 | **BLOCKER** | `scripts/check_m45_release_package.mjs:98-113` | Checker self-tamper, pinned-commit retarget and allowlist expansion are not detected; provenance trust root is a mutable literal in the very file it purports to pin. | Do not exempt the checker from current-checkout source validation; verify the historical commit's tree/blob IDs against independent constants outside the checker; pin the allowlist as a non-executable, current-checked constant. |
| RG-02 | **HIGH** | `scripts/check_m45_release_package.mjs:83-94,106` | `staticChecksums` / `staticChecksumManifest` are not compared to the historical inventory; coordinated tamper of static artifact + CHECKSUMS + inventory passes. | Assert deep equality of both static-checksum fields against `originalInventory` from the immutable commit. |
| RG-03 | **MEDIUM** | `apps/showcase/tests/release-guard.spec.mjs:48-78` | Seven cases omit checker self-tamper, commit retarget, allowlist expansion and coordinated static+inventory tamper; previously enforced self-drift detection was dropped without replacement. | Add at least four fail-closed cases listed in the security review; keep the old self-drift guarantee. |
| UX-01 | **MEDIUM** | `apps/web/src/Composer.tsx:111,274,285` | Build result and "Compare circuits →" are hidden in Visual mode, so the read-only view cannot continue the workflow without a mode switch. | Keep a read-only result summary/navigation affordance visible in Visual mode, or document the switch explicitly in the pane. |
| PROJ-01 | **LOW** | `apps/web/src/visual/projection.ts:76-77` | Source alias syntax is unvalidated; empty/numeric aliases can be accepted. Display is React-escaped, so no XSS, but strict identity hygiene is weaker than the architecture contract. | Apply the same `name()` validation to source aliases and to `c.sourceAlias` when it is used. |
| PROJ-02 | **LOW** | `apps/web/src/visual/projection.ts:235-239` | Port/edge budget is enforced after materialisation; a bounded hostile recipe can allocate up to ~128k display objects before failing. | Enforce cumulative port/edge counters inside the loops before constructing each collection. |
| INFO-01 | **INFORMATIONAL** | build output | Initial JS more than doubles vs accepted main; V7 performance gates not run in V1. | Carry the measured baseline into V7 benchmark scope; do not treat this as a V1 blocker. |
| INFO-02 | **INFORMATIONAL** | screenshots / spec | Real screen-reader speech, touch-device use, 200/400% zoom, forced colors and large-graph performance remain untested. | Schedule in V7 human/measurement acceptance, not V1. |

## J. Ownership and next action

Review branch: `opencode/flip-visual-v1-independent-review`, based on the exact PR head. All harnesses, results and reports are confined to `docs/evidence/visual-v1-independent-review/**`. No production implementation, fixture, CI, schema or existing test was modified. The PR remains open and unmerged.
