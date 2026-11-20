# M4.5-1I — Post-merge acceptance

## Accepted implementation and exact main

PR [#9](https://github.com/Technique-S/Flip/pull/9) is **MERGED**, using the repository's
history-preserving merge-commit strategy, at
`868b9eb68dd2a760abeeeb5078ccfe1cc0c76ce1` (2026-11-20 15:34:04 UTC).
That SHA is the tested implementation main revision. Its complete tree is byte-identical
to approved PR head `9c0c23698dfd1c7045de348da851c28d68f5e22b`.
CI-tested production revision is `f3d7b8e50fc5415af8cf50bf2c7319529915c4f0`;
its only subsequent approved-head delta was the integration handoff Markdown.

[Approved-head CI 44729535286](https://github.com/Technique-S/Flip/actions/runs/44729535286)
and [post-merge main CI 44764568925](https://github.com/Technique-S/Flip/actions/runs/44764568925)
are SUCCESS: every Windows/Linux step passed. Browser, all nine schema profiles,
canonical parity, custody, credentials, full Python, lint/build, independent agent checks,
portability corpus, external smokes, acceptance reports and benchmarks were retained.
The accepted full-suite inventory is 702 Python and 27 Chromium tests per platform.

The dedicated `codex/flip-m45-agent-portable-postmerge` branch preserves final review history
and this acceptance record separately. It changes no application, core, CLI/API, frontend,
solver or versioned contract bytes. Its Windows/Linux CI must also pass before merge.
After that evidence merge, final main is the merge commit containing this record; the
implementation remains the exact tree above in all production and frozen-contract paths.
The final merge SHA is reported with the completed integration and available from GitHub's
merge record, rather than embedding a self-referential hash in this file.

## Final independent evidence

OpenCode final review `4ad32846a995255105aa027e9809599e2cb9562f` is **PASS** for
exact head `9c0c23698dfd1c7045de348da851c28d68f5e22b`: 26/26 independent adapter checks,
including 10/10 fail-closed attacks. Custody discrepancy resolved; no remaining finding
blocks this integration. The earlier standalone and portable reports remain unchanged,
including their original conclusions and limitations.

The review is exactly one evidence-only commit above the approved head, with no duplicated
integration ancestry. It was merged conflict-free into the dedicated acceptance branch
(merge `d6082b30900f1910dd3409d4f96661d6f0abfa58`), not merged directly from the review branch.
Original report, raw observations and independent harness are preserved byte-for-byte:

| Original artifact | Bytes | SHA-256 |
|---|---:|---|
| `docs/evidence/m45-agent-portable-final-review/M45_AGENT_PORTABLE_FINAL_REVIEW.md` | 14293 | `c4ba9ec626a166c5f2ad38d0df0d55f22ebcdf45369d78080b436f56a64c08eb` |
| `docs/evidence/m45-agent-portable-final-review/results/independent-adapter-checks.json` | 10350 | `2ee72da015b123ec862defe35384d030dc46f30580931c91c72e2db1ea6a18bf` |
| `fixtures/m45-agent-portable-final-review/harness/independent_adapter_checks.py` | 35059 | `e080e931fdf959c9a86aa4460054055cd38ea62e690b41ec13d86ca85f409428` |

Exact Git/checkout comparisons against the review revision are enforced by the existing
repository custody gate. `-text` attributes preserve original checkout bytes. Only the exact
immutable harness is excluded from formatting. Credential scanning still covers all files;
no broad binary/large-file exception was added. A CI wrapper executes the original harness
with its output redirected to `.test-tmp/final-adapter-review`, selects the native CLI path
per OS, pins default RPC to a deterministic loopback changed-dependency fixture, verifies
all 26 case IDs and passing results, and leaves original results untouched.
The wrapper log and new observations are scratch outputs, not replacements for review evidence.

## Post-merge production smoke results

Executed after PR #9 merged, on acceptance tree based on main
`868b9eb68dd2a760abeeeb5078ccfe1cc0c76ce1`, with unchanged production/schema bytes:

| Check | Result |
|---|---|
| Integrated adapter suite | 32 passed in 135.62s |
| Original independent adapter harness, scratch replay | 26/26 PASS, including all 10 attacks |
| Integrated Chromium workflows | 2 passed in 46.2s; no retries/flakes |
| Nine schema export drift checks | PASS |
| Node parity | Six base vectors, three portable packages, adapter plan and pins PASS |
| Ruff lint / format, frontend lint / build | PASS |
| Full archive/review custody and credential scan | PASS; zero credential findings |

The combined 15-stage test opens/converts the legacy execution project into Portable 1.1,
runs declared vectors, reproduces a DIFFERENT witness in the trusted evaluator, inspects
connection diagnostics, proposes then verifies/applies a correction, and creates a separate
revision. Original package and evidence remain unchanged. It checks parent/ordered raw
before-after hashes, exports new evidence, and independently replays it EQUIVALENT with
HISTORICAL freshness. Chromium reopens the revision and independently replays via CLI,
requires explicit selection, and checks cancellation/late-result rejection. Publication and
deployment intentions terminate at STOP_AUTHORIZATION with one log and no later operation.
Frozen contracts and archive custody remain intact.

## Supported capabilities and non-capabilities

Supported: bounded local human/agent Portable 1.1 workflows through a shared native core;
named vectors, witness-backed behavioral comparison and diagnostics; explicit trusted
correction and revision creation; separate receipts and content-addressed evidence;
CLI/API semantic parity; historical replay; cancellation and resource/identity boundaries.

No wallet connection, signer, signing permission, transaction construction, spending,
broadcast, payment, deployment, live publication or public solver hosting is provided.
The proposed M4.5-0 authorization architecture
`8ea1b26c2667b2db86c34087e25c976f121c147e` is not an ancestor. Package metadata, hashes and
revision chains authenticate no author and cannot grant authority or CURRENT freshness.

## Retained limitations and release disposition

The inherited 120-second archival regeneration deadline and historical assertions are
unchanged. Full approved-head and post-merge hosted CI passed them; prior host-sensitive
runtime diagnostics remain contextual evidence in the earlier acceptance records.
The debugger browser test waits for the actual verified response before its unchanged
5-second rendering check; no retry, sleep or timeout increase was introduced.

Evidence is historical/reference-relative; old engine-bound bundles may fail compatibility
honestly. Missing evidence stays missing. Concurrent workflows can create sibling revisions;
there is no global author/linear revision registry. The independent C10 freshness attack
failed closed by operation deadline rather than a dedicated freshness diagnostic; no
CURRENT claim or revision was accepted. No live RPC revalidation, human screen-reader
session, local Linux process-tree containment or public exposure was exercised here.

During adoption of the additional cross-platform independent replay gate, initial Linux
run [44766702007](https://github.com/Technique-S/Flip/actions/runs/44766702007) failed without
retained case details. Diagnostic run [44767905737](https://github.com/Technique-S/Flip/actions/runs/44767905737)
identified C10: `status=COMPLETE`, `originalPreserved=true`, and
`exportFreshnessHistorical=true`. Its `noRevision` field calls the harness helper
`no_authority`, which returns false for *any* COMPLETE status, even a readonly operation.
C10 requests `createRevision=false` and only revalidation; source review confirms this
cannot create a revision/export or grant authority. Revalidation performs a fresh RPC
import, so successful trusted rereading can legitimately COMPLETE. The inherited default
public RPC makes the negative expectation provider/network dependent. The archived
Windows observation (deadline exhaustion) remains unchanged.

The CI wrapper now pins its default RPC configuration to the existing loopback
`LibraryChain` fixture with a changed beacon implementation. Explicit per-case settings
(such as B10) remain intact. C10 therefore checks its intended negative condition against
an actually changed dependency, through real native RPC/revalidation. The wrapper requires
observed RPC traffic and records environment provenance in scratch. All original assertions,
harness bytes, deadlines and results remain unchanged. Failure rows and diagnostic artifacts
are retained even on CI failure. This is a test-environment correction, not a production fix
or a rewritten independent conclusion; no timeout was increased and no assertion relaxed.

No known production blocker remains for the accepted read-only integration once the evidence PR's
required CI succeeds. Broader release, wallet/transaction authorization, deployment and
public hosting remain separate work requiring their own requirements, review and authority.
No authorized tape-out implementation was started. Stop after this integration.
