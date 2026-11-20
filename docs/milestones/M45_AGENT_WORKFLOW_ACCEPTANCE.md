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
| Tested acceptance/custody/CI integration | `ffaf426d7ff162e44678ddec75e3466af96b564a` |

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

The tested integration passed both platform jobs in
[push CI 44712700362](https://github.com/Technique-S/Flip/actions/runs/44712700362) and
[PR CI 44712923122](https://github.com/Technique-S/Flip/actions/runs/44712923122), all bound
to `ffaf426d7ff162e44678ddec75e3466af96b564a`. The acceptance-record follow-up changes
only documentation; its exact head and checks are retained in
[PR #8](https://github.com/Technique-S/Flip/pull/8). Final head CI must be green before merge.

| Required gate | Windows CI | Linux CI |
|---|---|---|
| Full Python suite, no failures/errors/skips | 648 passed | 648 passed |
| Chromium journeys, keyboard/mobile/axe and web/CLI parity | 23 passed | 23 passed |
| Independent acceptance observations | 27/27 exact semantic matches | 27/27 exact semantic matches |
| Authorization/freshness/API observations | 10/10 exact semantic matches | 10/10 exact semantic matches |
| Original workflow corpus and negatives | 15 scenarios + 5 negatives, in the 47 workflow tests | same |
| Cancellation, late revisions, resource ceilings, trusted corrections | passed | passed |
| Seven versioned schema profiles | passed | passed |
| Python/Node canonical parity | six vectors passed | six vectors passed |
| Locked installation, Ruff, frontend lint/build | passed | passed |
| Full custody/credential scan | passed; zero credential findings | passed; zero credential findings |
| External CLI/ASGI smokes and production benchmarks | passed | passed |

The push-run Python timings were 197.83 seconds (Windows) and 93.75 seconds (Linux).
Downloaded Linux JUnit confirms all 648 test nodes and zero failures/errors/skips; both
platform logs confirm counts and the 27 + 10 gate. Structured evidence and original tree
identities are in [acceptance-results.json](m45-agent-workflow/acceptance-results.json).

Local observations are kept separate: 23 Chromium tests passed, all seven schemas and
six canonical vectors passed, and the custody guard passed across 770 tracked files
with zero credential findings. A concurrent independent run matched 26/27 acceptance
observations; its CLI example hit OPERATION_DEADLINE and was rejected by the gate.
A separate authorization run matched 9/10, with API/core parity differing under runtime
limits. Neither run is credited as a passing acceptance gate. The unchanged six-step CLI
example subsequently completed serially. A diagnostic API/core pair both stopped at
BUDGET_EXHAUSTED/OPERATION_DEADLINE with identical semantic reproduction hashes, confirming
that bounded failures are not successful proof runs. The additional local full-suite invocation also produced failures during concurrent
diagnostics and is not credited as a green run on this host. Its raw JUnit is retained
in `.test-tmp/agent-python.xml`; final counts and dispositions are reported in the
integration completion response. The full isolated CI results remain the acceptance gate.
The accepted platform results above use isolated immutable CI checkouts; no local failure
was hidden by skipping tests, raising deadlines or changing production code.

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
The diagnostic completed with exit 0 in 218.844 seconds. The generator subprocess took
217.834 seconds, of which task E (benchmark generation) took 216.707 seconds; tasks A-D
combined took approximately 0.060 seconds. Every registered hash/size matched, authored
fixtures regenerated byte-identically, onchain-vector crosschecks and negative rejections
passed, all witnesses replayed, 17 recorded SAT expectations matched, and benchmark CNF
counts matched. This identifies the local bottleneck as the archival benchmark generator,
which performs sampled/exhaustive evaluation and capped stdlib DPLL measurements, rather
than an agent controller or production Minisat verification step. It does not establish
an unloaded-host timing or attribute all time to one inner benchmark algorithm.

Decision: retain the inherited 120-second test deadline and track this host-specific
runtime margin (F03-PERF-001 / D-RUNNER-001). The unchanged test passes on both hosted
platforms. Extending production deadlines or weakening historical validation is not
justified by a slow archival benchmarking pass on this host. The diagnostic is an
explicit scratch investigation, not a replacement or passing substitute for the timed
test. No archival result, assertion or production solver budget has been changed.

## Integration dependencies and exclusions

Portable Project 1.1 and the proposed M4.5-0 authorization architecture are excluded.
The portable adapter remains a separate follow-up after its own acceptance; this branch
uses only the frozen M3 execution request and the accepted agent workflow protocol.
There is no signing, wallet connection, transaction construction, spending, broadcast or
public solver hosting. Process containment/native solver identity remains platform-specific;
no live RPC or human usability study is claimed by deterministic acceptance.

## Verdict and merge gate

Independent verdict: **PASS** for the delivered implementation. Final integration
acceptance: **PASS** for that unchanged reviewed implementation and the tested integration
above, with the documented local runtime limitations. There are no unresolved severity
findings and no unreviewed production delta. The final record-only head must pass both
platform checks before PR #8 is merged, with origin/main ancestry and exact production
byte identity rechecked immediately before merge. Use the repository's established PR
merge-commit strategy to retain implementation, original corpus and independent review
ancestry. The resulting main SHA is recorded by PR #8's mergeCommit and the integration
completion response; it cannot be embedded self-referentially in its own merge tree.
