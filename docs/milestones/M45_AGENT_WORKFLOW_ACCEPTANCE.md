# M4.5-1A-C — Agent workflow acceptance

Date: 2026-11-20 (Africa/Lagos). Integration branch:
`codex/flip-m45-agent-workflow-acceptance`.

## Exact revisions and disposition

| Role | Revision |
|---|---|
| Accepted debugger baseline; fetched origin/main at admission | `bba6f3d301b08c0dcbbfd0b363b99a15179414db` |
| Delivered and independently reviewed agent implementation | `d2638d057b6236286480891d6fdd7dfb0402bc5a` |
| Independent review, PASS | `7b4b1f711ddc9676141becfae2fc77a3d5941374` |
| History-preserving review integration | `583b5176a452cf06a419c7cc60e5148bb880fbbd` |

Remote implementation/review heads matched the supplied commits after fetch. Main was
still the accepted debugger baseline and an ancestor of the delivery; the delivery was
an ancestor of the review. No production changes followed the reviewed delivery.
This branch preserves the review using a merge commit, without altering its conclusions
or any of its 14 original files. Both original corpus and review remain in history.

The independent report records no CRITICAL/HIGH/MEDIUM/LOW finding, 27 acceptance
observations and 10 clean authorization/freshness/API observations. Its full Python
observation was 647 passed and one inherited archival-regeneration timeout; this is
preserved, not rewritten as a passing local run. The manifest actually registers ten
files, despite the handoff's nine-file description; custody additionally pins all
14 files, including the generated logs omitted from the manifest. This is an inventory
clarification, not a change to the PASS verdict or original evidence.

## Permission and stop boundaries

STOP_AUTHORIZATION is terminal: no later step runs, no retry resumes it, signingCapability
is false, and a fresh workflow request confers no publication authority. Injected
permissions, approvalToken, transactionAuthority, signer, step permissions, write catalog
operations and fabricated stop artifacts fail closed. Historical compare/export remains
HISTORICAL; a genuinely fresh read can be CURRENT without granting persistence or proof
authority. A cancelled operation cannot commit a late execution request or select/apply a
later revision. Resource ceilings produce bounded terminal outcomes, never false success.

DIFFERENT requires a trusted witness replay; proposed corrections remain CANDIDATE_ACTION
until a fresh trusted comparison verifies them. Applying a correction compares again and
requires exact project/execution/action bindings. Serialized COMPLETE, EQUIVALENT,
VERIFIED_CORRECTION, prompts, receipts and metadata do not substitute for trusted checks.

## Acceptance validation

Validation is in progress on the history-preserving acceptance branch. The final table
will record exact CI revisions and executed outcomes before merge. Current requirements:
full inherited/new Python suite, 23 Chromium journeys, all 15 original workflow scenarios
and five negatives, the independent 27 + 10 checks, cancellation/resource limits, CLI/API
semantic parity, seven versioned schema profiles, canonical Python/Node parity, locked
installation, lint/build and credential/evidence custody on Windows and Linux.

Fresh independent harness runs use `scripts/check_m45_agent_acceptance.py`. Their original
source bytes remain unchanged; only CLI executable path and scratch output paths differ
by platform. Each current observation is asserted against its recorded semantic result,
with only the platform-native engine digest treated as platform-specific. Neither raw
archived results nor harness source is rewritten. CI runs this gate on both platforms.

The custody guard checks all review blobs against the original review commit and checkout,
manifest hashes/sizes, exact archive inventory, review ancestry and original corpus.
The single 328,278-byte UTF-16 stdout file is allowed only as an exact pinned review blob;
no general binary/large-file exemption or credential-scan exemption is introduced. Raw
archive attributes preserve UTF-16 and LF/CRLF bytes. Ruff excludes only the two immutable
review harnesses; their bytes are independently pinned instead of reformatted.

## Archival timeout investigation

The inherited M3 test retains its 120-second deadline and every hash, size and regeneration
assertion. `scripts/diagnose_m3_archival_runtime.py` runs the original verifier in disposable
scratch without changing that test deadline. In-memory wrappers time the original
builder's task functions; source bytes and deterministic authored outputs remain intact.
Timing observations and the decision will be recorded after the diagnostic completes.
No archival result, assertion or production solver budget has been changed.

## Integration dependencies and exclusions

Portable Project 1.1 and the proposed M4.5-0 authorization architecture are excluded.
The portable adapter remains a separate follow-up after its own acceptance; this branch
uses only the frozen M3 execution request and the accepted agent workflow protocol.
There is no signing, wallet connection, transaction construction, spending, broadcast or
public solver hosting. Process containment/native solver identity remains platform-specific;
no live RPC or human usability study is claimed by deterministic acceptance.

## Verdict and merge gate

Independent verdict: PASS for the delivered implementation. Integration verdict: PENDING
final platform checks and archival diagnostic. Merge is allowed only after those checks
are recorded and green, with production byte identity reconfirmed against the reviewed
SHA and main ancestry rechecked. The repository's established history-preserving PR merge
strategy will retain both implementation and independent-review history.
