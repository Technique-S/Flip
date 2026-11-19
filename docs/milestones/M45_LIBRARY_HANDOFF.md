# M4.5-2L Circuit Library handoff

Read-only milestone, based on accepted M4 `09f2482beae84be6d919ecd6957c4153d1924cca`.
Branch: `codex/flip-m45-circuit-library`. Independent acceptance is still required;
this branch must not be merged into main by its author.

## Implemented journeys

- Open Circuit Library from the workbench without a project. Known-address hints
  are available immediately through offline catalog operations. Discover processors
  reads cpuCount/cpuAt/isCPU, environment and optional display-only names/symbols.
- Select a processor, Browse circuits, inspect numeric input/output/state pins and
  gate counts. ownerOf validates existence before circuitInfo; sparse IDs are skipped.
  Next discovery page resumes a pinned block/environment cursor with bounded work.
- Search saved addresses, IDs, names and local aliases. Inspect metadata separately
  from identity. Save/remove favorites or local aliases. Favorites survive stale
  observations and cache eviction as selectable user pointers.
- Revalidate reads the complete M2 circuit/REF closure. Import into composition
  independently rereads that closure, passes the resulting M2 import to M4
  new-project and opens the existing numeric pin composer. Stateful entries remain
  inspectable with stateless composition disabled. A changed or failed revalidation
  emits no usable import payload.
- Successful imports create bounded persisted recents with manifest digest and
  block identity. Reload the workbench, reopen Library, select Recent imports or
  Favorites. Browser storage and CLI catalog files contain historical observations.
- CLI `flip library --request ... --catalog ...` and HTTP
  `POST /api/library/v1/execute` consume the same versioned request and core service.
  See [contract and examples](../schema/m45-library/README.md).

## Implementation inventory

Core: additive library models, bounded discovery/catalog service and schema exporter;
read-selector additions in abi/rpc; optional abort callback in M2 importer. API and
CLI are thin adapters. Web: Library component, navigation integration and scoped
white/near-black/cobalt layout. No dependencies added or locks changed.

The catalog cannot express CURRENT/executable. A fresh complete M2 import is the
only composition input. Single RPC observations do not establish consensus truth.
No wallet, signer, write RPC, token acquisition, spending, transaction construction
or submission capability was introduced.

## Source provenance and custody

Reviewed research commit `5c7bcfbc8babb58d5f040fe869e2017f4a8c46fd`: exactly 24
documentation/fixture/generator files, zero production files. Integrated using a
history-preserving merge. All its Git blobs and 19 registered manifest files are
preserved byte-for-byte. Added LF checkout attributes to preserve those hashes on
Windows. Immutable research generators are excluded from formatting, matching the
existing archival policy; the manifest verifier runs in CI instead.

Reviewed audit `962f5beeea9a485e8d4088ab1e67e0f8d69e6a27` and authority-design
`8ea1b26c2667b2db86c34087e25c976f121c147e`; neither was merged. Their broader
transaction architecture remains proposed and outside this milestone.

The historical report-only test needed exactly one additional allowed synthetic
namespace. Its exact resulting SHA-256 is registered in the repository guard;
no historical evidence claim or test assertion was removed. The guard additionally
checks all 24 research blobs and checkout bytes.

## Acceptance mapping

`packages/flip-core/tests/test_m45_library.py` implements all 12 synthetic themes:
C01 enumeration/search; C02 interfaces/stateful labeling; C03 sparse IDs;
C04 bounded pagination/dedup/large ranges; C05 outage retention; C06 HTTP throttle
retry budgets; C07 factory changes; C08 beacon changes; C09 reorg/cursor binding;
C10 canonical mixed-case dedup/provenance; C11 persisted favorite pointers;
C12 metadata control stripping/authority-field rejection. Additional tests cover
wrong chain/invalid/unregistered addresses, aborts, write-method rejection, fresh
import/revalidation, bounded recents, API/core/CLI parity and schema validation.

The research RPC scripts are scenario specifications, not complete wire recordings:
they omit environment reads, one isCPU argument is incomplete, circuitInfo tuples
repeat `0x` between words, and C04 repeats one processor address. The test adapter
supplies explicitly synthetic inherited M2 environments and normalizes tuple
delimiters in memory only. Source fixtures remain unchanged. Production ABI
decoding remains strict. C06's two throttle outcomes are injected as real HTTP 429
responses using the fixture's expected count; wire attempts include environment
reads and therefore are not the scenario's illustrative four calls.

Chromium L01 covers discover → circuit browsing → local alias/escaped hostile text
→ favorite → revalidate → composition import → reload → recents/favorites.
L02 covers known-address fallback and retained stale favorites at 390px width.
L03 exercises actual backend circuit cursors, missing IDs and stateful import
blocking. L01/L02 also run axe and retain desktop/mobile screenshots in `.test-tmp`.
Inherited browser journeys continue to cover the M4 workbench.

## Validation record

Final command results are recorded in `M45_LIBRARY_VALIDATION.json` alongside this
handoff. Mandatory tests are offline; conftest forbids external network access.
Live smoke is opt-in via `scripts/smoke_m45_library_live.py` and is absent from CI.
The separate [live read-only capture](M45_LIBRARY_LIVE_SMOKE.json) records chain
196, factory count, bounded processor/circuit pages, block/hash, code identities,
single-provider trust, request counts and no signing/broadcast.

Earlier iterations exposed malformed research tuple delimiters, Windows checkout
line endings, a browser-double missing-circuit envelope and an incorrect test
dropdown locator. These were corrected without loosening production ABI validation.
One initial full Python run had a missing namespace registration and an overlapping
targeted pytest invocation that cleared the shared test temporary directory. Final
validation runs pytest without concurrent pytest processes.

## Limits

This is a bounded library, not a complete chain index. Refresh is explicit, pages
are capped, and no historical count is treated as current. Prior-block checks in
discovery sample at most four stored block identities within the RPC budget;
complete selected-circuit import checks its own prior block and full closure.
The public provider is untrusted. No malicious-RPC resistance is claimed. Saved
records remain historical and the next executable import always reads again.

Windows tests and Chromium are executed locally. Linux execution remains a CI
matrix result until actually observed. Automated axe/accessibility tree checks
do not constitute a human screen-reader or developer usability session. Broader
M4.5 portability, diagnostics, authority and M5 work are intentionally outside this
branch. Stop after this library milestone.
