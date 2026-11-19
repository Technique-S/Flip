# M4.5-2L-D Independent review reconciliation

## Final merge authorization and evidence integration — 2026-11-19

OpenCode's final delta review at `96187da8718bcf7d14a452685f7de84231895920`
independently recommends **PASS** for the exact reviewed product tree at
`786cbca056c6cd61ca0e7a5b61ddbc772a55a800`. The user subsequently authorized the
final library merge, superseding the pending-review gate recorded in the historical
reconciliation below.

Both reviews are preserved through history-preserving merges into PR #5:

- Original review `9741e66ae385979dc0d18c89aec4ec6ed93ff285` / PR #6:
  merge `d6fb6a22b0c6c87d801ae500634486119cb7b3bd`.
- Final delta review `96187da8718bcf7d14a452685f7de84231895920`:
  merge `4ffaf0bb0431342a1e8f6c1850b77fbd17ff0d86`.

All 32 archived files, including both original manifests, remain byte-identical to
their respective review commits. Each manifest covers 15 artifacts and is itself
pinned to its original blob. No reviewer report was rewritten or credited with
testing a later implementation. Product code, tests, dependencies, lockfiles,
frozen schemas and discovery fixtures remain identical to the reviewed head.

The integration-only changes register both reviews in the custody guard, preserve
their original line endings with `-text`, and exclude only four frozen Python
harnesses from Ruff formatting/linting, as with earlier independent archives.
The guard requires both review commits in history and checks all archive bytes,
manifest coverage, hashes and checkout identity. The four reviewed PNG files are
admitted by exact hash and signature; all review text, including UTF-16 logs,
still undergoes the credential scan. No general binary or directory exemption is
introduced. Windows checkout line-ending conversion was corrected from the original
Git blobs before validation; the archived Git evidence was never changed.

The final integration checks, resulting main merge SHA and post-merge checks are
recorded in [PR #5](https://github.com/Technique-S/Flip/pull/5)'s final merge record.
F03-PERF-001 remains open in [the tracked follow-ups](M45_LIBRARY_FOLLOWUPS.md), with
the inherited 120-second limit and custody assertions unchanged. The unrelated
release-readiness branch is not included. This is library acceptance only.

## Historical reconciliation record

Assessment date: 2026-11-19. **Reconciliation verdict: PASS — ready for final independent delta review.**
The merge gate remains open: PR #5 must stay unmerged until that review confirms the fixes.
Codex validated the later changes below. OpenCode's original review remains frozen at its
original target and does not certify these changes.

## Exact revisions and preservation decision

| Role | Commit / artifact |
|---|---|
| Accepted remote main | `09f2482beae84be6d919ecd6957c4153d1924cca` — unchanged |
| Original library reviewed by OpenCode | `dec9420bb76e9245c6740bf3d92031d175e408ec` |
| PR #5 starting acceptance head | `60d9e94c4cfec9306492cb4016c4c6b60444a73f` |
| Completed independent review | `9741e66ae385979dc0d18c89aec4ec6ed93ff285` |
| Versioned provenance implementation | `9629391e419a996f40a76e313373f9a56320eef4` |
| Final tested code, including legacy wire defaults | `a184d776c896476be77f518b87885529a4038539` |
| Production acceptance PR | [PR #5](https://github.com/Technique-S/Flip/pull/5) |
| Frozen independent-review evidence PR | [PR #6](https://github.com/Technique-S/Flip/pull/6) |

The explicitly documented independent-review PR option was selected. PR #6 preserves
all **16 OpenCode-owned files unchanged**: report, manifest, harnesses, JSON observations,
UTF-16 logs and screenshots. All **15 manifest entries** match the exact Git blob sizes
and SHA-256 digests at `9741e66`. The manifest itself is also pinned in the inventory.
There are no production-source changes in that review branch's delta from `dec9420`.
See [independent-review-custody.json](m45-library-reconciliation/independent-review-custody.json).

The report is preserved at
[the original review commit](https://github.com/Technique-S/Flip/blob/9741e66ae385979dc0d18c89aec4ec6ed93ff285/docs/evidence/m45-library-independent-review/M45_LIBRARY_INDEPENDENT_REVIEW.md).
It records CONDITIONAL PASS at `dec9420`, zero CRITICAL/HIGH findings and no authority
bypass. Its findings were not rewritten. Its cited baseline pytest log/XML are not
among the committed manifest entries; no missing raw result was reconstructed. New
Codex runs and platform CI provide the later validation evidence.

The original research merge and all 24 research files remain intact. The authorization
architecture was not merged. PR #6 is an evidence-preservation PR, not approval of the
later production delta or a request to merge the old implementation into main.

## Finding-by-finding disposition

| Finding | Disposition | Actual reproduction and evidence |
|---|---|---|
| F-01 MEDIUM — malformed favorites disable fallback | RESOLVED BY EXISTING FIX; preserved | The exact reviewer sequence was run on the existing PR fix before provenance changes: put an object without identity into `overlay.favorites`, reload, reopen Library. The focused browser test passed. The final 18-test browser suite repeats it with an explicit legacy catalog: two seed rows return, a meaningful invalid-data warning appears, Loading known addresses disappears, original bytes remain unchanged, and rows are UNKNOWN rather than CURRENT. |
| F-02 LOW — favorite-only metadata says onchain | RESOLVED IN VERSIONED CONTRACT | Library 1.1 emits `metadataTrust=USER_SUPPLIED` for user-only records, with USER_POINTER existence, UNKNOWN freshness, no block/environment/netlist/manifest evidence and zero RPC calls. UI, API and CLI regressions verify the representation. Frozen 1.0 schemas and their model implementation are retained unchanged, with explicit compatibility behavior below. |
| F-03 LOW — inherited 120-second scratch timeout | INVESTIGATED; runtime-margin follow-up retained | The unchanged custody test passed serially in default and custom layouts. Default: 96.22 seconds total; custom: 87.27 seconds. Python startup was 0.10–0.11 seconds, fixture copying about 0.035 seconds and hashing 0.17–0.21 seconds. Execution inside the inherited test dominated. Historical failures are retained; no timeout or assertion was relaxed. |

F-01 production recovery logic was not replaced. Changes to that path only add the
separate valid-1.0 catalog migration/backup behavior required by F-02. Corrupt catalogs
are still rejected in full, never sanitized into claimed valid/executable state. Their
original bytes remain until an explicit edit, with a recovery copy preserved first.

The F-01 test is `apps/web/tests/library-acceptance.spec.ts`, titled
`F-01 exact malformed-favorites restore retains bytes and recovers seeds`. F-02's focused
core/API/CLI tests are in `packages/flip-core/tests/test_m45_library_provenance.py`, and
its UI test covers USER_SUPPLIED display and legacy-storage backup. The earlier Codex
alias-search, processor-code invalidation and recent-order fixes remain present.

## F-02 contract compatibility decision

The frozen 1.0 enum can express only ONCHAIN_DISPLAY_ONLY; adding USER_SUPPLIED there
would silently change a historical contract. Instead:

- The original three schemas in `docs/schema/m45-library/1.0.0/` remain byte-identical.
- The original model implementation is preserved byte-for-byte as `library_models_v1.py`.
- `library_models.py` and `docs/schema/m45-library/1.1.0/` define the current 1.1 profile.
- The existing HTTP endpoint and CLI dispatch on the explicit envelope version. Omitting
  the wire version retains the old 1.0 default. Current UI/examples explicitly send 1.1.
- Ordinary 1.0 observations still return valid 1.0 envelopes. When a user-only result
  cannot be represented truthfully, the legacy response reports UNKNOWN /
  UNSUPPORTED_SCHEMA_VERSION, omits that record and retains the pointer in the overlay.
  It never casts USER_SUPPLIED back to ONCHAIN_DISPLAY_ONLY. A 1.1 request retrieves it.
- A known 1.0 catalog is completely validated before migration into a 1.1 request.
  Unknown versions and authority fields are rejected. Identities and user collections
  are preserved; user-pointer provenance is corrected explicitly.
- Browser restore keeps valid original 1.0 bytes until an edit, then saves a 1.0 backup
  before writing 1.1. Corrupt-data recovery has its separate recovery copy.

The same-version API/CLI/core parity checks cover both wire versions, including legacy
exit 2 for the explicit upgrade status. The full decision and examples are documented
in [the library contract](../schema/m45-library/README.md). The schema exporter defaults
to frozen 1.0; `--version 1.1.0` checks the new profile. Both are checked in CI and the
repository custody guard now pins the frozen 1.0 schemas and model bytes.

## F-03 investigation and tracked follow-up

The optional development probe runs the original custody test serially in both layouts,
records startup/copy/hash timings, exact commands and output, interpreter/platform,
source hashes and elapsed time. The inner subprocess limit remains **120 seconds**.
No generator, historical fixture or test assertion was changed. Source hashes remain
unchanged, and the independent stdlib generator does not import the production library.

Both layouts passed in the current probe and the full local suite also passed. These
observations do not establish a unique cause for the earlier timeouts or show that the
directory name caused them. Measured startup and initial file-copy/hash work were too
small to account for the observed runtime. No genuine library regression was reproduced.
Runtime margin and host/environment variability remain qualified limitations.

Evidence: [regeneration-probe.json](m45-library-reconciliation/regeneration-probe.json).
Tracked follow-up: [F03-PERF-001](M45_LIBRARY_FOLLOWUPS.md). Earlier local timeout traces
remain in [the preceding acceptance evidence](m45-library-acceptance/local-test-results.json).
A repeat supported-runner failure reopens the gate; skipping the check or increasing its
limit to hide a regression is not an accepted resolution.

## Final validation and tested state

[validation-results.json](m45-library-reconciliation/validation-results.json) records the
actual local and downloaded CI results. Platform CI on the final code is
[run 44500076045](https://github.com/Technique-S/Flip/actions/runs/44500076045).

| Check | Outcome |
|---|---|
| Full local Python suite, started at implementation `9629391` | PASS — 543 tests, 376.78 seconds |
| Final focused library + API/CLI checks at `a184d77` | PASS — 59 tests |
| Final complete Chromium suite at `a184d77` | PASS — 18 tests |
| Linux and Windows full CI at `a184d77` | PASS — 543 tests per platform, zero failed/skipped; M3/M4 reports PASS |
| CLI/API same-version parity | PASS — both 1.0 and 1.1 pointer profiles, plus inherited interfaces |
| Frontend lint and build; Python lint and formatting | PASS |
| M1/M2/M3/library 1.0/library 1.1 schema drift | PASS |
| Canonical Python/Node hash parity | PASS — six vectors; canonical profile unchanged |
| Selector and research fixture custody | PASS — inherited independent Keccak proofs and 19 registered research files |
| Independent-review evidence custody | PASS — 15 manifest entries, all 16 owned files pinned unchanged |
| Standalone repository/credential scan at `a184d77` | PASS — 574 tracked files; zero credential findings |
| F-03 serial default/custom probes | PASS — unchanged 120-second test limit |
| External CLI/API M3 smoke | PASS |
| External M1 smoke | Concurrent startup attempt failed; identical serial rerun PASS; script and limit unchanged |

The last code adjustment after the full local run preserves the historical omitted-wire-
version default and adds truthful service union annotations. It is covered by the final
focused tests, Chromium rerun and both complete platform CI jobs at `a184d77`. This
handoff update changes only documentation/evidence. No later production code change is
implied by a newer report commit.

The concurrent M1 ASGI startup failure is retained in the validation record. Its cause is
UNKNOWN; it was not hidden by changing its startup deadline. Both platform CI smoke
steps passed. Browser validation used a fresh build; OpenCode I-01/I-02's install/build
preconditions remain in the normal setup documentation. Cursor replay remains bounded,
deduplicated and advisory (I-03). OpenCode's discarded harness endpoint attempt (I-04)
is not promoted into live observation evidence.

## Safety boundary, limits and delta-review handoff

All network chain operations remain read-only and bounded. No wallet/signing/broadcast
or spending path was added. Catalog records cannot express CURRENT. Labels, favorites,
recents and migrated pointers cannot grant proof or permissions; library import into
composition still requires a fresh full M2 import, registration and closure validation.
Frozen historical schemas, original tests, research bytes and the reviewer's report are
preserved. No transaction architecture or debugging feature was implemented.

Remaining limits: single-provider trust, bounded explicit discovery rather than a full
chain index, historical saved observations, no human screen-reader/usability claim,
and the F03-PERF-001 runtime-margin follow-up. No fresh live call was required for this
reconciliation; prior live captures remain separately labeled historical observations.

PR #5 is ready for an independent delta review of `60d9e94..HEAD`, concentrating on
version negotiation, pointer provenance, known catalog migration and unchanged custody
limits. PR #6 preserves the original review separately. The final independent reviewer
must confirm these fixes before PR #5 is merged. Main remains at the accepted M4 SHA;
no merge authorization or readiness to begin debugging implementation is granted here.
