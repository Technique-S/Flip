# M4-C product integration acceptance

## Revisions and custody

The integration branch starts at accepted main **0bd006336d9ab710706e1e11aa0533636d7fae1e**. M4-A **f4d5b3a981d4cd5906c3ab11942c106f5becc7a9** is merged by **ccde35341fdca20ce88182b2bc7a9183d0431089**. M4-B **52814f5cef02716f4a9e49842ae520cdf7937a31** is merged by **884605f84edce24caf24e5a33be38ba87b2ec1ad**. Its parent is the M3 PR head af8ba1f, which is an ancestor of the accepted M3 merge. Both histories are preserved.

All 100 M4-B paths remain byte-identical to their source commit. Existing schema versions, protected planning documents, historical evidence and inherited test cases remain present. One historical namespace assertion is extended only to the custody-checked M4-B fixture directory. The checker pins the corrected file hash. All historical missing-artifact assertions remain active. The repository checker now enforces M4-B custody alongside prior evidence and scans every tracked file for credential patterns, oversized files and binaries. No new raw historical evidence was generated.

## Product acceptance scope

The machine-readable [case results](M4_CASE_RESULTS.json) are extracted from actual JUnit properties and Chromium JSON results. They include the 30 independent CLI cases, planned capabilities, ten neutral regenerations, ten proof attacks, concurrency, and explicit mappings for J01â€“J13, E01â€“E12 and B01â€“B11. Mappings list the executed paths supporting each scenario. The historical M4-B labels remain intact.

C18 now executes the implemented pre-flight with a refused loopback endpoint and yields UNKNOWN. C19 exports JSON evidence. C20 preserves the legacy bare sample behavior. P04 invokes the explicit half-adder variant. P02 and P03 exercise the implemented JSON evidence format and independent project pins. The ZIP/SHA256SUMS proposal is inapplicable to this implementation.

C22 and C26 first execute the original captured claim. Matching engine bytes allow replay. Different native binary hashes require IMPLEMENTATION_CHANGED. A separately generated current-engine claim then executes through the same consumer. This allows Linux and Windows to test the actual platform binding without rewriting a capture or bypassing identity checks.

P05 uses a controlled loopback RPC double. No fresh mainnet observation is claimed in M4-C. P01 reproduces the exact archived M4-A burn-stage revert, block binding and fee. The observation belongs to block 76234348 on 2026-11-18.

## Findings and corrections

Chromium identified missing focus placement and focus outline after an error. Errors now receive keyboard focus with a cobalt outline. Completed comparisons announce verdict, freshness, intent and counterexample availability through a polite status region. Timeout copy includes the machine code and a retry action.

The browser previously lost the active project on refresh. It now saves the project in session storage, validates it through the actual composer before restoration, and identifies the restored snapshot. Reset requires an explicit confirmation. Storage quota or availability errors instruct the user to save a project file. Reports and chain freshness are recomputed through their existing operations.

The narrow-screen test checks all four workflow pages at 320, 768 and 1280 px. Axe checks WCAG A/AA rules in Chromium. Actual keyboard traversal reaches sample, build, comparison and JSON download. Tests exercise input and output mapping, non-color difference labels, repeated execution, timeout recovery, visible errors, refresh/reset, storage failure, download and replay. The reduced-motion test exposed a CSS specificity defect after formatter cleanup. The reduced-motion selector now takes precedence over control transitions. Chromium verifies the computed duration is zero.

Manual auditory screen-reader output remains BLOCKED because no assistive-technology session was available. Browser accessibility-tree names, table semantics and live-region text were tested. This limitation is retained in the case report.

## Verification, security and structural pre-flight

The production comparison, evaluator and native solver are inherited from M3. Browser, API and CLI call those shared operations. The 81-byte half-adder and all four rows execute through the trusted core. The browser exports a difference and a separate CLI process replays it. Swapped output wiring produces a reproducible witness, restored wiring proves equivalent, and a 1 ms deadline yields UNKNOWN.

Ten additional bundle attacks replace verdict, witness input, project binding, reference identity, manifest hash, freshness, engine identity, selected project, envelope version and dependency closure. Each HTTP request is rejected without a proof report. The unchanged inherited suite also covers import failures, wrong chain, malformed circuits, stale dependencies, private worker deadlines, process cleanup and crash recovery.

Pre-flight re-resolves source/dependency snapshots at a current pinned block, checks the original block's canonicality, chain identity, reviewed implementation hashes and current fee. The fixed synthetic caller receives a fee balance override only within eth_call. Strict burn decoding binds all four fields and expected local gate count. Empty data, successful/ambiguous result shapes, unavailable overrides, failed RPC responses, reorgs and changed implementations yield UNKNOWN. Known structural reverts yield REJECTED. Structural acceptance is limited to the observed burn stage.

The supported launcher binds loopback and rejects remote peers, hostile Host/origin and cross-site requests. Solver operations require deliberate local opt-in. Input size and two-job concurrency ceilings are enforced. The solver remains approved for bounded local use. Windows private commit and Linux virtual address space have different meanings and do not establish uniform whole-service RSS containment.

## Reproduction

Run from the integration workspace with CPython 3.14.6, uv 0.9.11 and Node 24.18.0.

```sh
uv sync --locked
npm ci --prefix apps/web
npm run lint --prefix apps/web
npm run build --prefix apps/web
uv run --frozen pytest -q --junitxml=.venv/m4-all.xml -o junit_family=legacy
# Run from apps/web after installing Chromium.
npm test
# Return to the repository root.
uv run python scripts/report_m4_acceptance.py --junit .venv/m4-all.xml --browser .test-tmp/m4-browser.json --out docs/milestones/M4_CASE_RESULTS.json
```

CI executes the same Python and browser suites on Windows and Linux, plus Ruff, frozen schema exports, Node canonical vectors, evidence custody, credential scans, CLI/ASGI smoke checks and the native benchmark. Each runner uploads its actual acceptance report.

See [local usage and trust boundaries](M4_A_HANDOFF.md) for installation and supported CLI commands. Session storage now retains the active project through refresh within the same browser session. A saved project file remains the portable recovery format.

## Decision

M4 acceptance is limited to the local developer workflow with the explicitly documented manual screen-reader limitation. M5 readiness requires independent review of this integration. Public hosting remains blocked pending deployment-specific authentication, process isolation, aggregate budgets and request controls. M4-C adds no signing, wallet, payment or transaction broadcast path.
