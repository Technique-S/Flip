# M4.5-R2 — Release gates, rights and smallest remaining work

Date: 2026-11-22. Accepted production baseline:
`b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b`.
This register separates a working local read-only tool from judge access, submission,
public operation and paid/onchain authority. It is not permission to implement the latter.

## Classification

PASS = observed evidence meets the scoped requirement. PARTIAL = evidence exists but a
stated subrequirement is incomplete. FAIL = a checked requirement is contradicted by
observed facts. BLOCKED = a decision, authorization, rights or technical prerequisite is
missing. NOT TESTED = no actual execution/observation. Source-access NOT VERIFIED is
recorded explicitly where retrieval could not establish a fact. These labels are not
interchangeable; a prohibited deployment is not a failed Flip regression.

## Requirement-by-requirement register

| ID | Requirement / release scope | Status | Evidence and remaining acceptance condition |
|---|---|---|---|
| G01 | Accepted local human/agent runtime | PASS | 702 Python / 27 Chromium locally, existing accepted-main CI on both OSes. Original production/frozen contracts unchanged. |
| G02 | Current root README product status | FAIL | It still says adapter review is pending and mixes current setup with historical unimplemented milestones. Review the draft replacement in R2; do not rewrite historical reports. |
| G03 | First-time onboarding | PARTIAL | Existing-worktree install/build works; prerequisites not turnkey, uv absent from PATH here, native opt-in must precede startup. No clean-PC novice trial. |
| G04 | Live X Layer catalog | PARTIAL | Two processor records and two circuit metadata records observed on bounded pages. No complete discovery, freshly verified netlist hashes or malicious-provider resistance asserted. Offline sample is separate. |
| G05 | Canary, diagnostics, corrections, Portable 1.1 and replay | PASS | Existing real-engine browser/Python tests; original preserved, explicit verify/apply/open, content-addressed evidence and relative historical labels. |
| G06 | Publication stop / non-authority | PASS | STOP_AUTHORIZATION terminal; no later queue/new revision. Signing, wallet, transaction/spending paths absent. |
| G07 | Windows checkout installation | PASS in audited environment | Pinned local runtime, locked sync, npm ci/build and native suites pass. This is not a validation of every installer or fresh Windows machine. |
| G08 | Linux checkout installation | PASS by remote CI / NOT TESTED as local desktop | Accepted-main Ubuntu job performs locked install, full suites, containment and smokes. No claim of a Linux GUI or assistive-tech session here. |
| G09 | Reproducible frontend build | PASS, same host | Repeated artifacts byte-identical; hashes in evidence JSON. No cross-platform bit-for-bit native-wheel promise. |
| G10 | Frozen schema/canonical compatibility | PASS | Nine schema drift checks and three Node parity gates. Native evidence is engine-bound; a different binary may require fresh local proof. |
| G11 | Automated access checks | PASS in covered states | Axe, keyboard/focus, narrow layout and reduced-motion regressions pass. Passing these is not a full WCAG conformance declaration. |
| G12 | Manual screen-reader speech / human novice study | NOT TESTED | No human auditory or first-time study results. Computer Use restriction is preserved; actual expected-versus-spoken observations are required. |
| G13 | Judge application-access link | BLOCKED | No organizer-confirmed source/local/static access arrangement and no verified deployed app. Public GitHub alone is insufficient evidence. |
| G14 | Final submission form and eligibility | NOT VERIFIED / BLOCKED | Form retrieval inaccessible. Owner must inspect current fields, eligibility, contact details, rights and declarations; no auto-submission. |
| G15 | Official-rule review | PASS for retrieval, PARTIAL for compliance | Current official text retrieved independently; deadline remains provisional; access interpretation/entrant declarations unconfirmed. See H1–H8 ledger. |
| G16 | Product/video/submission copy | PARTIAL | Drafts supplied; no actual edited video, final captions, real access URL or owner-approved submission yet. |
| G17 | Own-source license / allowed reuse | BLOCKED for a licensed distribution | No root license and GitHub license=null. Owner chooses license or appropriate explicit permitted-use terms. This audit neither selects a license nor claims the event mandates a particular open-source license. |
| G18 | Third-party distribution notices / asset rights | PARTIAL; bundled executable BLOCKED | Metadata and selected upstream notices inspected, but no complete installer notice bundle or rights clearance for every linked native component/asset. Preserve all applicable obligations before redistribution. |
| G19 | Credentials / archive custody | PASS | Existing exact-byte and pattern guards retained. Staged 862-file scan passed with zero findings; clean-commit gate is required before delivery. No binary exception or original-result rewrite. |
| G20 | Browser storage / privacy | PARTIAL | Session and persistent library stores are local plaintext, with recovery behavior. No secret storage, complete data-erasure workflow or hosted retention policy is claimed. |
| G21 | CI/reliability | PASS for accepted baseline; scoped caveats | Local suites and b537eb6 CI green. Historical archival limit and debugger sync unchanged; C10 independent harness default now uses existing deterministic loopback changed dependency. New branch CI is read separately after push. |
| G22 | Downloadable supported installer / wheel-only product | BLOCKED | Source-relative assets/sample paths, no supported installer, no full wheel/native notices/OS distribution QA. A GitHub ZIP is not a tested installed product. |
| G23 | Restricted or public native solver hosting | BLOCKED | No owner authorization or target-host authentication, abuse quotas, aggregate memory/CPU/process controls, retention/monitoring evidence. No tunnel/port-forward workaround. |
| G24 | Write-enabled publication | BLOCKED, intentionally outside release | No signer/approval broker/transaction lifecycle; separate architecture remains unmerged. Not needed to invent a success for the local demo. |

Overall: technical local demo PASS; judge access BLOCKED; submission completeness PARTIAL;
public interactive deployment BLOCKED; write-enabled publication BLOCKED.

## Licensing and third-party rights disposition

[GitHub's licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
distinguishes a public repository from an open-source license. The owner retains the
choice. Do not advertise unrestricted reuse, redistribute an installer under an invented
license, or silently extend a chosen license to legacy research assets or contributors'
material. Inventory source, dependencies, sample/vector data, reports, screenshots and video
assets; preserve provenance and document any exclusions/permissions. Owner declarations
and event terms acceptance cannot be supplied by this audit.

| Component / observed version | Declared license / notice evidence | Release consequence |
|---|---|---|
| python-sat 1.9.dev23 | Installed metadata and [exact release page](https://pypi.org/project/python-sat/1.9.dev23/) identify MIT; it is a pinned prerelease. Installed LICENSE.txt and [upstream notice](https://raw.githubusercontent.com/pysathq/pysat/master/LICENSE.txt) observed. | Do not upgrade in an audit. Preserve notices; wrapper metadata does not settle every bundled native solver's rights. |
| MiniSat22 selected at runtime | [MiniSat notice](https://raw.githubusercontent.com/niklasso/minisat/master/LICENSE) is permissive MIT-style with notice conditions. | Selecting one solver does not remove obligations for other native code linked into the wheel. All-component packaging audit remains necessary. |
| six 1.17.0, React/react-dom 19.3.1, scheduler 0.28.0 | MIT in installed metadata/package manifests. | Retain applicable notices in redistributed source/bundles. |
| certifi 2026.10.23 | MPL-2.0 metadata; installed license file observed. | Review corresponding source/notice obligations for the actual distribution, rather than blanket-relicensing dependencies. |
| axe-core 4.14.1 / @axe-core/playwright 4.14.0 | MPL-2.0 package metadata. | These are test dependencies, not evidence that an installer may discard their notices if shipped. |
| Playwright 1.65.1 / TypeScript 7.0.2 | Apache-2.0 metadata. | Test/build versus shipped artifacts differ; preserve applicable notices for what is actually redistributed. |
| esbuild 0.28.2 / Biome 2.6.8 | MIT / MIT OR Apache-2.0 metadata. Native tool packages also present. | Generated frontend bundle and shipped tool binaries require different inventories; inspect selected artifact, not only top-level names. |
| CPython, Node and uv runtimes | Existing dependency documentation records PSF, MIT plus bundled notices, MIT OR Apache-2.0 respectively. | Do not build an all-in-one app without complete runtime/binary notices and per-OS QA. |
| TAP-02 specification/reference/vector context | Existing pinned [solver/licensing record](../milestones/M3_A_SOLVER.md) and [dependency inventory](../schema/DEPENDENCIES.md). | Preserve exact upstream provenance. The M1 inventory's statement that PySAT was not installed is historical and superseded by M3; do not rewrite it. |

Installed metadata inventory in the evidence JSON is an observation, not a complete legal
clearance or installer SBOM. No all-in-one binary, root LICENSE or third-party notice bundle
was created. npm's reported zero known vulnerabilities during installation is not a security
assessment, a license clearance or proof against supply-chain compromise.

## Public-hosting safety gate

[Existing solver containment limits](../milestones/M3_A_SOLVER.md) apply per child, not all
parent/service allocations. Windows private commit and Linux virtual address space are not
a uniform RSS guarantee. Existing loopback peer/Host/origin checks, 1 MiB requests and two
execution slots are local controls, not public authentication or multi-tenant isolation.

Any proposal for interactive judge hosting must first name its operator/host, authenticate
judges, define quotas and total compute/storage budgets, test aggregate cancellation and
process-tree cleanup under abuse, protect logs/data, define retention/deletion, and undergo
independent target-host review. No exposed uvicorn worker, reverse proxy, tunnel or relaxed
Host/Origin check is an acceptable shortcut. A static recorded viewer avoids native-worker
exposure but still needs separate owner authorization and truthful labels.

## Ordered minimum worklist

Estimates are planning ranges, not measured delivery commitments. Dates are relative to the
November 22 audit and must move if the organizer changes the provisional schedule.

| Order | Owner / target | Work and acceptance evidence | Impact / risk / estimated effort |
|---|---|---|---|
| 1 | Owner, by Nov 24 | Resolve H3 with organizers and inspect the real form through a permitted human session. Retain the actual response/requirements and choose the access path. | Highest eligibility leverage; low technical risk; 30–60 minutes to prepare inquiry, response time unknown. No automatic contact. |
| 2 | Owner/rights reviewer, by Nov 24 | Decide own-source permissions/license and clear contributed/source/demo material. Record decision and applicable notices. | Distribution blocker; cannot be decided by agent; review effort depends on rights provenance. |
| 3 | Maintainer, by Nov 25 | Review/adopt the concise quickstart; remove current-status contradictions without editing archival reports. Test pristine checkout on supported Windows/Linux with a developer unfamiliar with Flip. | High usability value, low runtime risk; roughly half a day plus tester availability. |
| 4 | Human accessibility tester, by Nov 26 | Perform the spoken-output matrix in the demo checklist; triage real issues in a small separately reviewed patch if needed. | Accessibility confidence; unknown findings; 1–2 hours initial test, fix time not estimated without findings. |
| 5 | Owner/demo author, by Nov 27 | Record/rehearse captioned ≤3-minute video, curate actual project/evidence/receipt artifacts and rights-cleared screenshots; keep native-engine labels. | High judge comprehension; about a day, contingent on approved access/materials. No fabricated timings or publication. |
| 6 | Maintainer + owner, conditional | If H3 accepts it, prepare a pinned source-checkout distribution with prerequisites/checksums. If a browser URL is required, seek explicit authorization for an inert static recorded-evidence viewer. Review that artifact, not the current frontend with dead API routes. | Minimum access-dependent work; static viewer estimate 1–2 days after clear scope/authorization; no implementation/hosting here. |
| 7 | Release owner, target freeze Dec 1 | Freeze accepted revision/materials, retest links and supported setup, repeat relevant regression/custody checks and perform a judge-access rehearsal without privileged developer knowledge. | Low change risk; reserve several days for actual access problems. |
| 8 | Owner, recheck by Dec 5 and before final deadline | Confirm schedule/form/rights and submit manually only under separate authorization. | Administrative critical path; this audit does not submit or accept terms on the owner's behalf. |

**Defer:** public/authenticated native solver, installer bundling of all runtimes, arbitrary
new agent actions, wallet integration and authorized tape-out implementation. They add
security/distribution review rather than resolving the current access and evidence gaps.
Do not spend the remaining event window rebuilding an accepted core to avoid those decisions.
