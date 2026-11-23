# Draft submission claim audit, video accuracy and owner approvals

**Status: CLAIM CROSS-CHECK — not a submitted entry. Date 2026-11-22.**
Reviewed draft: `docs/release/M45_R2_SUBMISSION_DRAFT.md` and `M45_R2_DEMO_SCRIPT.md` at Codex R2 commit `39df7af`.
Accepted implementation evidence: main `b537eb6` plus R2's recorded execution. Assessments below are about
what evidence supports, not about whether the owner should submit.

## 1. Claim-by-claim crosswalk

Labels: **SUPPORTED** (accepted evidence matches claim), **QUALIFIED** (true only with an explicit scope),
**UNSUPPORTED** (no accepted evidence), **NOT TESTED** (human/access/novice claim), **BLOCKED** (decision absent).

| ID | Draft claim | Status | Evidence / qualifier | Required edit or gate |
|---|---|---|---|---|
| C-01 | "Local-first circuit workbench for developers and coding agents" | SUPPORTED | Accepted local launcher, CLI, bounded agent controller and portable adapter; R2 executed local suites | None beyond supported Windows/Linux checkout scope |
| C-02 | "Import or open pinned circuit snapshots, compose explicit TAP-02 netlists, compare wiring revision against declared reference, inspect counterexample" | SUPPORTED (QUALIFIED scope) | R2 journeys 2–5 PASS in isolated loopback tests; PRD/MVP semantics; sample is HISTORICAL | State that comparison is stateless, reference-relative and bounded; keep UNKNOWN semantics |
| C-03 | "Portable Project 1.1 carries tests, revision history and content-addressed evidence references" | SUPPORTED | Accepted portable 1.1 contract and R2 journey 8 PASS | Do not imply authorship, CURRENT freshness or transaction authority from hashes |
| C-04 | "Bounded agent workflows use the same native verifier and stop at publication intent" | SUPPORTED | `stop_authorization` terminal; `signingCapability=False`; R2 journey 11 PASS; exit 9 | Say "stop at a handoff", not "publish" or "deploy" |
| C-05 | "Does not publish circuits, connect a wallet, sign or spend" | SUPPORTED | Frontend source grep found no wallet/signing code; RPC allowlist read-only; R2 G06/G24; accepted authority design unmerged | Keep the claim; do not pair it with any publication-success screenshot |
| C-06 | "DIFFERENT backed by evaluator-replayed witness" | SUPPORTED | R2 journey 5 and accepted Wiring Canary semantics | Clarify that a witness shows behavior difference, not which design is correct absent an oracle |
| C-07 | "81-byte composed half-adder; four vectors illustrate pins" | SUPPORTED (QUALIFIED) | R2 journey 3/4; draft explicitly says vectors are not universal proof | Retain the "illustrate, not prove" wording |
| C-08 | "Verified correction" | SUPPORTED (QUALIFIED) | R2 journey 7: declared trusted local prior, separate verify/apply, reverted | Must say declared reference-relative and explicit local apply; never autonomous repair |
| C-09 | "Browser and CLI independently replay proof claim" | SUPPORTED (QUALIFIED) | R2 journey 10 PASS on this native engine | Add: engine identity is bound; a different native binary may require fresh local evidence |
| C-10 | "X Layer and TapeOut are central to the product, not decorative" | QUALIFIED | Chain 196 binding, processor/circuit IDs, dependency manifests and read-only importer are implemented; R2 live discovery was bounded (two processors) | Do not claim complete registry, current XOR/NAND byte identity or malicious-RPC resistance |
| C-11 | Sample identities and netlist hashes | SUPPORTED as historical | Draft table cites archived hashes and accepted source; R2 metadata page did not provide netlist hashes | Use "archived/recorded"; never relabel as CURRENT from the November 22 metadata page |
| C-12 | "We built all listed components during the event window" | QUALIFIED | Draft lists git commit SHAs/dates for nine additions; commit metadata is not authorship attestation | Owner must confirm actual creation, prior work and borrowed-material attribution (H4) |
| C-13 | Target personas, acquisition channels, commercial use cases and proposed revenue | QUALIFIED / hypothesis | Draft labels them intended/future and explicitly says no measured demand or revenue | Keep all "proposed/hypothesis" qualifiers; no conversion or 10× claims |
| C-14 | "Flip is open source" | UNSUPPORTED | No root license; GitHub `license: null` (R2 G17) | Remove or replace with owner-approved terms after decision |
| C-15 | "Judge can access the app via a URL" | BLOCKED | No organizer-confirmed method; no deployed/verified URL (R2 G13/H3) | Do not state an access URL until method confirmed and rehearsed |
| C-16 | "Static viewer / downloadable installer available" | UNSUPPORTED | R2 says static viewer is proposed, not built; current dist needs API; no installer (G22) | Remove until separately authorized and accepted |
| C-17 | Accessibility / usable workflow claims | NOT TESTED | R2 automated checks PASS; manual speech and novice study NOT TESTED | Do not claim WCAG conformance, screen-reader success or novice completion |
| C-18 | "No native solver or write-RPC path" | SUPPORTED for accepted app; SPECIFICATION for viewer | Read-only RPC allowlist, loopback guards, R2 G06; static viewer not built | Use separate static-showcase checks before making the claim for a viewer |
| C-19 | "Current onchain circuit ID created / publication succeeded" | UNSUPPORTED | No transaction, wallet or broadcast occurred; local half-adder has no new onchain ID | Never add such a scene or claim |
| C-20 | "npm install showed zero vulnerabilities" as security claim | UNSUPPORTED | R2 explicitly says this is neither license clearance nor security assessment | Do not use as a security or supply-chain claim |

## 2. Three-minute video accuracy checklist

Use `M45_R2_DEMO_SCRIPT.md` as the storyboard. A finished video must satisfy every item below; none is satisfied
by passing automated tests alone.

| ID | Check | Required observation |
|---|---|---|
| V-01 | Exact build identity visible | Pinned commit `b537eb6` (or the owner's approved final freeze SHA), supported runtime and local URL shown |
| V-02 | Truthful opening | "Runs locally, no wallet" with no implied hosted service |
| V-03 | Library segment label | Fixture / historical seed / dated single-RPC capture stated; metadata not presented as a complete verified registry |
| V-04 | Sample provenance | Archived XOR/NAND dependencies and 81-byte local composition labeled HISTORICAL; no new onchain ID claimed |
| V-05 | Verdict semantics | DIFFERENT tied to replayed witness; EQUIVALENT conditional on stateless reference and mapping; UNKNOWN defined as inconclusive |
| V-06 | Correction sequence | Declared prior, verify before apply, original retained, revert shown; no "autonomous bug fix" wording |
| V-07 | Portable/agent sequence | Separate project/evidence/receipt; explicit open of new revision; finite agent budget; no invented continuation |
| V-08 | Replay honesty | Real CLI command shown; engine identity acknowledged; no precomputed output presented as a newly completed proof |
| V-09 | STOP boundary | `STOP_AUTHORIZATION` and one stop log visible; exit 9 explained as a stop; no "deployment succeeded" caption |
| V-10 | Business claims | Target users and proposed paid model labeled proposed; no revenue, adoption or time-improvement claim |
| V-11 | Editing honesty | Any trimmed wait labeled; no sped-up solver timer; uncut run/logs retained |
| V-12 | Rights and privacy | Owned/cleared footage, captions and title card; no personal tabs, aliases, usernames, secrets or third-party logos without clearance |
| V-13 | Duration | Final captioned video ≤180 seconds; pacing not achieved by rushing pin tables |
| V-14 | Captions reviewed | Spoken claims and on-screen labels match; DIFFERENT/UNKNOWN/STOP wording preserved in captions |
| V-15 | Access claim | Closing card names the organizer-confirmed access method; if unconfirmed, says so rather than inventing a URL |

Status: **SPECIFICATION**. No video exists in this branch; R2 demo script is a recording plan only.

## 3. Exact owner approvals still required before release

Each item must be recorded by the owner with date and exact value. No agent may supply or infer these.

| ID | Approval | Why it blocks |
|---|---|---|
| O-01 | Own-source license or explicit permitted-use terms; scope for historical artifacts and contributions | G17; without it, distribution/reuse claims are unsupported |
| O-02 | Rights clearance for sample/vector provenance, screenshots, captions, title cards, media and any third-party logos | G18; video/assets cannot be published otherwise |
| O-03 | Organizer-confirmed judge-access method and exact wording/date of confirmation | H3/G13; judge access remains BLOCKED |
| O-04 | Entrant/team/contact details, eligibility and rights declarations | H8/G14; form was inaccessible and NOT VERIFIED |
| O-05 | Final submission copy, tagline and claim qualifiers from §1 | Owner must approve exact public wording |
| O-06 | Final captioned ≤3-minute video and its accuracy checklist (V-01–V-15) | G16; no video produced |
| O-07 | Human screen-reader results accepted and any fixes reviewed | G12; manual speech NOT TESTED |
| O-08 | First-time developer trial results accepted | G03; no novice study performed |
| O-09 | Any static viewer or hosted artifact: explicit hosting authorization plus organizer acceptance of display-only access | R2 access options; public/native hosting is BLOCKED |
| O-10 | Final freeze revision, artifact checksums and judge-access rehearsal sign-off | Release integrity; no freeze yet |
| O-11 | Manual submission and terms acceptance under separate authorization | No auto-submission; owner action required |
| O-12 | Any future public native solver or write-enabled feature | Separate security/authorization scope; explicitly deferred |

## 4. Stop rule

A claim may appear in public material only when its evidence status is SUPPORTED or explicitly QUALIFIED with
the required wording, and the relevant owner approval is recorded. PARTIAL, NOT TESTED and BLOCKED claims stay
out of the submission or are stated as limitations. Passing local tests never converts O-01–O-12 into approvals.
