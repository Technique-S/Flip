# Third-party licensing and distribution notice inventory

**Status: INVENTORY ONLY — NO LICENSE SELECTED. Date 2026-11-22.**
This document does not choose Flip's license, grant reuse rights, clear contributed material or approve a
distribution. Owner/rights reviewer decision remains BLOCKED (R2 G17/G18).

## 1. Sources and execution status

- **EXECUTED_NOW:** parsed `docs/release/M45_R2_EVIDENCE.json` `dependencyMetadata` (35 Python, 17 Node entries) and `apps/web/package-lock.json` (70 installed package entries with `license` fields) from accepted main / R2 source.
- **R2_EXECUTED:** installed license files and upstream notices inspected by Codex; see R2 blockers §Licensing, `docs/schema/DEPENDENCIES.md` and `docs/milestones/M3_A_SOLVER.md`.
- **NOT VERIFIED:** full native-component rights clearance, installer SBOM, contributor material rights, stock media/music/logos, final video assets. No installer or bundle exists to inventory definitively.

## 2. Flip's own source

| Item | State | Required action |
|---|---|---|
| Root own-source license | **ABSENT** — no root LICENSE; R2 evidence records GitHub API `license: null` | Owner selects terms or explicit permitted-use statement; agents must not infer or invent one. |
| Public repository visibility | Confirmed by R2 | Visibility is not a license and does not authorize redistribution or reuse. |
| Historical PRD, audit reports, fixtures | Preserved immutable evidence | Do not silently relicense or fold them into any chosen Flip license; attribute and check contributor/upstream rights separately. |
| Ownership declarations / eligibility | Owner field | Cannot be supplied by this review. |

## 3. Python runtime and build toolchain (R2 evidence / existing inventory)

| Component | Version | Declared license evidence | Distribution note |
|---|---|---|---|
| CPython | 3.14.6 | PSF-2.0 | Runtime not bundled in an all-in-one app here. |
| uv | 0.9.11 | MIT OR Apache-2.0 | Tooling; preserve notices if redistributed. |
| python-sat (PySAT) | 1.9.dev23 | MIT (installed metadata and upstream notice; pinned prerelease) | Wrapper metadata does not clear every native solver linked in the wheel. Do not upgrade during audit. |
| MiniSat22 | selected at runtime | Permissive MIT-style with notice conditions | Selecting one solver does not remove obligations for other native code in the wheel. |
| six | 1.17.0 | MIT | Transitive dependency; preserve notice. |
| certifi | 2026.10.23 | MPL-2.0 | Source/notice obligations depend on actual distribution. |
| pytest, pydantic, fastapi, httpx, ruff and other locked packages | see `docs/schema/DEPENDENCIES.md` and R2 evidence JSON | Mostly MIT / BSD variants; `packaging` Apache-2.0 OR BSD-2-Clause; `typing-extensions` PSF-2.0 | Retain license files from installed distributions if redistributing. |

R2 Python metadata counts: MIT 19, BSD-3-Clause 6, MPL-2.0 1, Apache-2.0 OR BSD-2-Clause 1, BSD-2-Clause 1, MIT OR Apache-2.0 1, PSF-2.0 1, and 5 entries with `declaredLicense: null`.

The five null entries are: `colorama 0.4.6` (classifier BSD), `ruff 0.14.5` (classifier MIT), and the three
first-party packages `flip-core`, `flip-cli`, `flip-api` (no declared license). First-party packages inherit
the unresolved own-source decision; colorama/ruff need classifier-backed notice checks if redistributed.

**Historical note:** `docs/schema/DEPENDENCIES.md` says PySAT/MiniSat22 "is not installed" for M1. That was
true at M1 and is superseded by M3/R2; do not rewrite the historical statement, and do not conclude from it
that solver licensing is settled.

## 4. Frontend / Node inventory

`apps/web/package.json` declares direct dependencies `react 19.3.1`, `react-dom 19.3.1`; devDependencies
`@axe-core/playwright 4.14.0`, `@biomejs/biome 2.6.8`, `@playwright/test 1.65.1`, `@types/react 19.3.0`,
`@types/react-dom 19.3.0`, `esbuild 0.28.2`, `typescript 7.0.2`.

**EXECUTED_NOW** `package-lock.json` license field counts across 70 installed entries: MIT 33, Apache-2.0 24,
MIT OR Apache-2.0 11, MPL-2.0 2. Notable entries: `react`/`react-dom` MIT, `esbuild` MIT (all platform
packages MIT), `playwright` and `typescript` Apache-2.0 (platform packages), `axe-core` and
`@axe-core/playwright` MPL-2.0, `@biomejs/biome` MIT OR Apache-2.0.

**Discrepancy to preserve:** R2 evidence JSON records `declaredLicense: null` for all 17 Node entries, while
the accepted lockfile has explicit `license` fields. Treat the lockfile as the more specific source for the
installed tree, but do not rewrite R2 evidence; record both when assembling a notice bundle.

Test/build tools (Playwright, axe-core, Biome, TypeScript, esbuild) are not automatically shipped in the
frontend bundle. The notice obligation follows what is actually redistributed, not only the top-level names.

## 5. Data, specification and media

| Item | Evidence | Consequence |
|---|---|---|
| TAP-02 specification | `docs/schema/DEPENDENCIES.md`: CC0-1.0 | Preserve exact upstream provenance and versioned link. |
| TAP-02 reference implementation | `docs/milestones/M3_A_SOLVER.md`: MIT | Upstream evaluator is not vendored or installed; do not claim it is part of the distributed product. |
| Audited sample circuits / vectors | Immutable evidence and pinned hashes in accepted docs | Report as historical/reference-relative evidence; attribute provenance; do not relabel as Flip-owned circuits. |
| Screenshots and fresh PNG captures | R2 records them in ignored scratch, not committed | Need privacy/rights review and narrow custody registration before use as release assets. |
| Video, captions, title cards, stock images/music/logos | Demo script says none cleared or added | Owner must use owned/cleared material and retain attribution. |
| Browser storage | sessionStorage/package state; localStorage `flip-library-m45-v1` | Local plaintext; no secrets or personal data; not a durable portable backup. |

## 6. Required notice bundle for any approved distribution

1. A license/permission notice for Flip's own source, selected by the owner.
2. Installed distribution license files for every redistributed Python package, including all native solver components in the exact wheel.
3. Node package notices for whatever is actually shipped in the frontend artifact; distinguish build/test-only dependencies.
4. Runtime notices (CPython, Node, uv) if those runtimes are bundled rather than externally provisioned.
5. TAP-02 specification/reference attribution with exact version/hash.
6. Rights/privacy clearance for screenshots, sample identities, aliases, names and video assets.
7. A manifest mapping each notice to the exact artifact version and hash.

npm's "zero known vulnerabilities" during install is neither a license clearance nor a supply-chain security
assessment (R2). No all-in-one binary, root LICENSE or complete notice bundle exists on accepted main.

## 7. Approval still required

- Owner/rights reviewer: own-source license or permitted-use terms.
- Owner: contribution/material attribution and event rights declarations.
- Maintainer: notice bundle for the exact approved artifact, if distribution is approved.
- Owner: explicit hosting/distribution authorization; no agent may infer or grant it.

Until these are recorded, the distribution/licensing gate remains **BLOCKED**.
