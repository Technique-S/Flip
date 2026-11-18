# M4.5-R — outstanding security and licensing risk register

**Baseline:** `09f2482beae84be6d919ecd6957c4153d1924cca`.
**Purpose:** independent risk record for Codex and the release owner. It does
not duplicate Codex's engineering gap audit and does not authorize deployment.

Scope labels:
- **LOCAL MVP** — required for the supported single-developer local workflow.
- **WRITE-LIFECYCLE (proposed)** — would only be introduced by a future
  authorized tape-out transaction feature; no such code exists on this baseline.

Status labels: `MITIGATED_LOCALLY`, `OPEN`, `BLOCKED`, `NOT_APPLICABLE_LOCAL`,
`UNVERIFIED`.

| # | Risk | Scope | Status | Evidence / current control | Outstanding action |
| --- | --- | --- | --- | --- | --- |
| R-01 | Public solver isolation | LOCAL MVP | MITIGATED_LOCALLY / public BLOCKED | `flip_core/isolation.py` spawns one bounded worker; `flip_api/local.py` binds `127.0.0.1`, disables proxy headers, checks Host/Origin/cross-site, sets CSP; no-opt-in compare returns 501; independent review measured `[200,200,429,429,429,429]` for six parallel requests. | Do not expose publicly without deployment-specific process isolation, authentication and aggregate budgets. Local CI passing is not evidence of public safety. |
| R-02 | Windows/Linux memory enforcement | LOCAL MVP | MITIGATED_LOCALLY, platform-asymmetric | `M3_A_SOLVER.md`: Windows Job object caps 64 MiB private commit; Linux RLIMIT_AS caps virtual address space. M4 acceptance states these are not uniform whole-service RSS. | Measure actual deployment target; do not claim a 64 MiB RSS guarantee. |
| R-03 | Authentication and rate limiting | PUBLIC / WRITE-LIFECYCLE | BLOCKED / NOT_APPLICABLE_LOCAL | Local launcher has no accounts; two execution slots and 1 MiB request cap are local guards, not public controls (`M4_ACCEPTANCE.md`, `M4_A_HANDOFF.md`). | Add deployment authentication, rate/concurrency quotas and asset budgets before any public hosting. |
| R-04 | Transaction signing and authorization | WRITE-LIFECYCLE | NOT_APPLICABLE_LOCAL | M4 acceptance: "adds no signing, wallet, payment or transaction broadcast path"; repository scans for credential patterns; pre-flight uses a synthetic caller inside `eth_call` only. | If write capability is proposed, require explicit human approval, a separate authorization design and security review. Do not add covert signing. |
| R-05 | Spending limits | WRITE-LIFECYCLE | NOT_APPLICABLE_LOCAL | No payment path exists. `TAPEOUT_FEE()` is read for classification only; `MVP_CONSTRAINTS.md` §8 re-reads the fee each session. | Define explicit per-transaction ceilings and human confirmation before any write feature. |
| R-06 | Live-chain revalidation | LOCAL MVP | MITIGATED_LOCALLY, trust caveat | `importer.revalidate` and `preflight` pin block/hash and environment hashes; M3/M4 independent review confirmed STALE on changed beacon and current only for fresh observations. Single RPC remains a trust assumption (`M4_A_HANDOFF.md` §Evidence). | Do not claim malicious-RPC resistance or multi-operator consensus. Re-check before any "current" badge. |
| R-07 | Solver distribution/licensing | LOCAL MVP if redistributed | OPEN | `M3_A_SOLVER.md`: PySAT upstream MIT, MiniSat permissive MIT-style with notice obligations; installed wheel contains other native solvers whose notices must be preserved; no all-in-one binary shipped. | Audit and retain notices for **all** native components before bundling a wheel/binary; do not relicense. |
| R-08 | Dependency licenses | LOCAL MVP | OPEN (administrative) | `docs/schema/DEPENDENCIES.md` inventories declared licenses (MIT/BSD/MPL-2.0/PSF-2.0) and states no license has been selected for Flip's own source. | Choose a Flip license; preserve upstream notice files on distribution; verify MPL-2.0 certifi obligations if redistributed. |
| R-09 | Screen-reader manual testing | LOCAL MVP | BLOCKED | M4 acceptance: "Manual auditory screen-reader output remains BLOCKED because no assistive-technology session was available." AX-tree names, table semantics and live regions were tested; independent review did not perform a human screen-reader session. | Schedule one NVDA/VoiceOver session per result class before claiming full accessibility acceptance. |
| R-10 | Secrets and credential handling | LOCAL MVP | MITIGATED_LOCALLY | Repository checker scans tracked files for credential patterns; `readFile` caps uploads at 1 MiB; no wallet/key path; `local.py` refuses arbitrary RPC targets from HTTP clients. | Keep scans in CI; never commit wallet material or private RPC URLs. |
| R-11 | Browser data persistence | LOCAL MVP | MITIGATED_LOCALLY | Session storage restores the active project, validates it through `compose` before restore, and requires confirmed reset; quota errors direct the user to save a project file (`M4_ACCEPTANCE.md` lines 21–25, `M4_A_HANDOFF.md` line 93). | Treat local storage as non-secret; document that it is per-browser and not a portable backup. |
| R-12 | RPC trust assumptions | LOCAL MVP | MITIGATED_LOCALLY, OPEN for public | `RpcSettings` allowlists read methods; contract selectors validated; block/hash pinned; observation marked SINGLE_RPC; HTTP clients cannot choose arbitrary endpoints. | Do not assume honest RPC operator. Multi-operator agreement is a future requirement, not an MVP claim. |

## Explicit separation

The supported local MVP is safe for bounded offline/single-developer use under
the controls above. Every item marked `BLOCKED` or `NOT_APPLICABLE_LOCAL`
becomes a release-critical requirement only if the **proposed write-enabled
tape-out lifecycle** is introduced. That lifecycle is not implemented on this
baseline and is not authorized by this evidence package.

**Local CI passing is not sufficient grounds for public deployment.** Public
hosting remains blocked pending authentication, deployment process isolation,
aggregate resource controls, request limits and a formal hosting decision.

No write transaction, signing, broadcast, payment or live publication was
performed during this evidence work.
