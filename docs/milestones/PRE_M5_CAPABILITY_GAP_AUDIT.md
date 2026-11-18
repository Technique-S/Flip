# Pre-M5 six-capability gap audit

Assessment date 2026-11-19. Baseline **09f2482beae84be6d919ecd6957c4153d1924cca**, merged M4 main. Remote main matched this SHA when the audit began. This report assesses production code at that revision. Proposed behavior below is engineering planning.

## Decision and classification

**The six-capability pre-M5 gate is not satisfied.** M4 remains accepted for its documented bounded local verification scope. The expanded requirements introduce library, portability, diagnostic and transaction-authority work beyond that acceptance.

| Capability | Classification | Working production subset | Concrete completion gap | Proposed milestone |
|---|---|---|---|---|
| 1. Human and coding-agent workflows | PARTIAL | React and JSON CLI/API share Python core; schema exports, help, commands, CI build/test/verify | Agent task contract and supported closed-loop protocol, deployment approval artifact and enforcement | M4.5-1 and M4.5-4 |
| 2. Circuit and processor library | PARTIAL | Explicit address/ID import, registry validation, technical metadata and pinned snapshots | Factory enumeration, searchable persistent catalog, user metadata, favorites, recent-import history | M4.5-2 |
| 3. Authorized X Layer tape-out lifecycle | BLOCKED | Deterministic preparation and structural eth_call with current fee | Reliable total-cost/resource estimates, transaction preview, human authorization, signer/submission, confirmation and receipt | M4.5-0, M4.5-3 through M4.5-5 |
| 4. Agent safety | PARTIAL | Read-method allowlist, chain checks, local solver opt-in, bounded execution, proof rejection and cleanup | Transaction permissions, spend reservations, key boundary, one-use approval, nonce coordination and recovery journal | M4.5-0 and M4.5-4 |
| 5. Portable circuit project specification | PARTIAL | Project/source/manifest round-trip and independent-project evidence replay | Unified versioned project package containing named tests, version/migration policy and formal evidence envelope schema | M4.5-1 |
| 6. Debugging diagnostics | PARTIAL | Replayed input, reference/candidate outputs, mismatched bits and explicit pin editing | Trace from differing outputs to component connections, user expectations and validated repair suggestions | M4.5-2 |

PARTIAL means implemented production behavior covers a subset of the requested capability. BLOCKED for capability 3 means most lifecycle stages are MISSING and require a reviewed authority/architecture change plus live protocol verification before activation. No whole capability is COMPLETE. MISSING subfeatures below have no reachable implementation found in the inspected production modules.

## Evidence method and demonstrations

Inspected all production Python modules under packages/flip-core/src, packages/flip-cli/src and packages/flip-api/src, React/TypeScript source under apps/web/src, their tests, schemas, workflow configuration, README, AGENTS.md, PRD, architecture documents, MVP constraints and M4 handoffs/review. Historical planning statements and fixtures were distinguished from callable production behavior. Searches for discovery, favorites, history, signing, nonce and receipt behavior were followed through entry points. Absence findings combine those searches with the complete CLI operation list, API routes, RPC allowlist and web workflow controls.

Executed on Windows with CPython 3.14.6 and Node 24.18.0, using the locked workspace environment. Generated test/build outputs stayed in ignored locations. Production source, tests, dependency locks, frozen schemas and historical evidence were not edited. No live chain query, wallet connection, signature or broadcast was performed. Official Ethereum documentation was read only to ground the future approval design.

### Executed evidence

| Demonstration | Exact command or path | Actual outcome |
|---|---|---|
| Product boundaries and independent CLI corpus | `python -m pytest packages/flip-core/tests/test_m4_workflow.py packages/flip-core/tests/test_m4_acceptance.py -q --junitxml=.venv/audit-tests.xml -o junit_family=legacy` | 74 passed. Includes local-double imports, stale/chain failures, evidence attacks, pre-flight and local deployment controls |
| Focused importer/worker/parity checks | `python -m pytest packages/flip-core/tests/test_m2_import.py packages/flip-core/tests/test_m3_engine.py -k "readonly or wrong_chain or unregistered or audited_81 or timeout_crash or full_request_python_node" -q --basetemp=.venv/audit-targeted --junitxml=.venv/audit-targeted.xml` | 7 passed, 105 deselected |
| Frontend installation/build | `npm ci`, `npm run build` from apps/web | Locked installation and TypeScript/esbuild build passed |
| Browser acceptance | `npm test` from apps/web | 11 passed in 1.3 minutes; loopback API, native worker and controlled RPC double |
| Original CLI sample | `flip sample half-adder --out .venv/project.json`; `flip compose --project .venv/project.json --out .venv/netlist.json`; `flip compare --project .venv/project.json --out .venv/equal.json` | Exit 0 for each, 81 bytes and EQUIVALENT |
| Mutation and evidence | `flip sample swapped --out .venv/mutation.json`; `flip compare --project .venv/mutation.json --out .venv/different.json`; `flip export --project .venv/mutation.json --out .venv/evidence.json`; `flip verify-bundle --project .venv/mutation.json --bundle .venv/evidence.json` | Sample exit 0; compare/export/replay each exit 1 for DIFFERENT, HISTORICAL |
| Web project round-trip | Actual Chromium session on `python -m flip_api.local --port 18763`; Open sample, Evidence, Save project; CLI `compose --project .venv/web-project.json`; confirmed reset; Open project file; Build netlist | PASS, 81-byte project persisted and rebuilt. Temporary audit harness `.venv/audit-roundtrip.cjs` was used only for observation |

Both original CLI and saved-web project composition produced SHA-256 `3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce`. The mutation produced input bits `01`, reference outputs `01`, candidate outputs `10`, replay `REF_BEAT_REPRODUCED`. With pins numbered from zero, both mapped output bits differ.

These executions demonstrate supported paths. They do not establish capabilities for missing features. The M4 platform matrix previously passed 514 Python and 11 Chromium tests on Windows/Linux at the reviewed M4 head. That is historical baseline evidence, separate from this audit's selected local reruns. [M4 closure CI](https://github.com/Technique-S/Flip/actions/runs/44419430690)

## 1. Dual human and coding-agent workflows — PARTIAL

**Production locations.** `packages/flip-cli/src/flip_cli/main.py::main` exposes sample, import/inspect, new-project, compose, compare, vectors, consume, preflight, revalidate, export, inspect-evidence and verify-bundle, with JSON outputs and stable exits. `packages/flip-api/src/flip_api/app.py::m3_request` calls `flip_core.verification.execute` or `flip_core.workflow.product`. React's `apps/web/src/model.ts::api` submits to the same API. The CLI imports the same functions. There is no JavaScript proof engine. README and `docs/milestones/M4_A_HANDOFF.md` document usage. `docs/schema/1.0.0`, `docs/schema/m2/1.0.0` and `docs/schema/m3/1.0.0` expose structured contracts. `.github/workflows/m1-contracts.yml` builds, tests and checks artifacts on both platforms.

**Tests and proof of work.** The executed CLI chain above covers preparation, build, comparison, mutation and evidence replay. `test_m4_workflow.py::test_product_roundtrip` checks CLI/API semantics. `apps/web/tests/workflow.spec.ts` checks browser-to-CLI evidence parity. `test_m3_engine.py::test_full_request_python_node_hash_parity` verifies canonical cross-language hashing.

**Missing behavior.** An agent can already edit a project JSON file and run supported commands and repo tests. There is no single machine task specification binding requested changes, allowed operations, test suite, budget, iteration history and required stop/approval conditions. There is no deploy command or persisted deployment approval protocol. Repository review and human git approvals are a process control, with no application artifact representing deployment authority. Current code-building agents execute through the host environment; the solver sandbox does not sandbox arbitrary source builds or npm scripts.

**Dependencies and milestone.** M4.5-1 should define the agent task/result envelope and documented edit/build/test/verify loop over the portable project. M4.5-4 must enforce the deployment approval boundary. Automated acceptance must show identical core outputs, structured terminal failures and deterministic stop on budget exhaustion. Manual acceptance must show that an agent cannot self-approve deployment. A future code-build sandbox requires an explicit trust boundary for untrusted repositories and dependencies.

## 2. Circuit and processor library — PARTIAL

**Production locations.** `flip_core.abi.FACTORY` pins `0x1f09daefa827f02cbb40967cc91b259763760761`. `ImportService.import_circuit`, `PinnedReader.environment` and `PinnedReader.resolve` validate the caller-supplied processor against factory `isCPU`, verify factory/beacon/code identities, check circuit existence via `nextId`, decode `circuitInfo` and `netlist`, and resolve REFs under limits. The UI's `App.tsx::live` and `SourceCard` expose manual imports and technical metadata. `ContentCache` is a bounded in-memory content cache. `sessionStorage` holds the active project. Neither is a library index.

The built-in half-adder uses processor `0x839bdd6fa7a66416a609a735e11de5411b98574e`, XOR #1 and NAND #2, from archived block 76206482. These addresses have recorded validation provenance. This audit did not freshly verify their current onchain state. Loading the sample does not convert them into current observations. Source aliases are local identifiers, not verified human circuit descriptions.

**Tests.** `test_m2_import.py::test_import_recorded_xor_and_nand_with_strict_block_context`, `test_cycle_unregistered_and_arity`, `test_cache_is_immutable_historical_and_bounded` and `test_revalidation_detects_real_closure_changes` cover importer integrity. Executed M4 CLI cases C27/C28/C30 cover a controlled import, missing circuit and changed implementation. The second browser workflow exercises inspection and additional import.

**Missing behavior.** There is no live factory processor enumeration adapter, pagination/indexer, circuit search, curated address directory, names/descriptions/tags provenance, favorites or durable recent-import list. `abi.SELECTORS` contains registration lookup but no enumeration selector. `nextId` checks existence bounds for a known processor; it does not implement a discoverable catalog. A transient last-inspected circuit and the sources in one project do not provide a recent-import history.

**Dependencies and milestone.** M4.5-2L should first verify the deployed factory enumeration/event ABI and its upgrade semantics, then add bounded discovery and a chain/block-aware local index, search and user collections. Technical metadata must remain distinguishable from user-authored labels. Automated tests need pagination, ID gaps, reorg, stale code, HTML/text injection, search freshness and storage migration cases. A separately identified live read-only check must establish the actual discovery ABI and address provenance. A discovered circuit becomes executable only after the existing trusted importer validates it.

## 3. Authorized X Layer tape-out lifecycle — BLOCKED

**Production locations.** `compile_project` prepares deterministic TAP-02 bytes and computes gate/dependency counts. `preflight.py::StructuralReader.probe` reads `TAPEOUT_FEE()` and constructs an ABI-encoded tapeout call only for `eth_call`, using a fixed synthetic caller and a temporary fee-balance override. `preflight` re-resolves dependencies and reviewed implementation identity at a fresh pinned block. It recognizes strict burn-stage and structural reverts. `workflow.product('export')` can attach that observation.

**Tests.** `test_m4_workflow.py::test_preflight_transport`, `test_unrecognized_burn_is_inconclusive`, `test_invalid_rpc_config_is_inconclusive`, plus `test_m4_acceptance.py::test_historical_preflight_fixture`, all ran. They cover fee/block binding, chain, empty and ambiguous data, RPC failures, changed implementations and reorgs. The archived structural observation at block 76234348 is retained evidence of that specific observation.

**Missing stages.** There is no real sender/account preparation, balance/allowance/resource ownership check, validated total gas estimate, maximum all-in spend estimate, signable preview, human approval, signer adapter, transaction submission, pending-state journal, confirmation/finality policy, replacement/reorg recovery or circuit receipt verification. The synthetic burn revert identifies a structural stage. It does not establish the real sender has the tokens or funds required, or that publication will succeed. Existing gate counts are useful inputs to a future estimate, not a complete fee/resource quote.

**Dependencies and milestone.** The original constraints and system architecture expressly exclude writes. The new mandatory lifecycle requires a reviewed versioned architecture decision, protocol verification and approval design before code introduces a signer. M4.5-0 must resolve the scope/authority change. M4.5-3 should implement a read-only quote and exact-byte preview against a real selected sender. M4.5-4 should add authority and mocked transaction orchestration. M4.5-5 may perform one separately authorized capped live acceptance only after those gates. Automated fixtures cover transaction mechanics. Actual submission/confirmation requires human and live-chain verification and remains unexecuted here.

## 4. Agent safety — PARTIAL

**Production locations.** `rpc.py::READ_METHODS` allows only chain ID, block, eth_call, code and storage reads. `PinnedReader._chain` rejects other networks. `flip_api.local.application` enforces loopback, Host/origin and cross-site restrictions and disables proxy-header trust. `app.py::m3_request` requires `FLIP_LOCAL_SOLVER=1` and a loopback peer for sensitive native operations, with a 1 MiB body cap and two slots. `isolation.py::run_worker` and `solver_worker.py` enforce worker lifecycle limits. Trusted `consume` recompiles, recomputes and replays claims against caller-selected identities. RPC endpoints come from trusted local configuration, with credentials in URLs rejected by `RpcSettings`.

**Tests.** Executed `test_public_or_disabled_native_rejected`, `test_local_service_transport_boundary`, `test_concurrency_closed`, ten `test_bundle_attacks` cases, importer wrong-chain tests, and `test_timeout_crash_and_memory_containment` demonstrate the existing boundaries. Worker allocation is Windows private commit or Linux virtual address space. It is not a uniform whole-process RSS guarantee.

**Missing behavior.** Solver opt-in is a local execution permission, not a transaction spending authorization. No sender/contract/function permission grant, spend ledger, approval expiry, transaction nonce reservation, replay journal or wallet secret interface exists. No signing credentials are required or stored by current product paths. Credential pattern scanning detects some accidental commits; it is not runtime key management. Browser session data and evidence are untrusted inputs, and successful proof replay provides no transaction authority. Error recovery and process cleanup work for reads and solver jobs; they do not implement reconciliation after an ambiguous broadcast.

**Dependencies and milestone.** M4.5-0 and M4.5-4 should implement the approval protocol below with a durable journal and transaction mocks. Agent tools must be independently denied signing and broadcasting, with authority held by a separate human-controlled broker. Tests must cover spoofed approvals, changed payloads, parallel spend reservations, expired/revoked grants and unknown submission state. Public untrusted solver hosting remains blocked by its existing deployment gates.

## 5. Portable circuit project specification — PARTIAL

**Production locations.** `models.py::CircuitIdentity`, `Source`, `Candidate`, `Project`, `Manifest`, `ComparisonReport` and `BitVector` encode versioned identities, explicit connections, widths, semantics and evidence. `composition_models.py::LocalProject` adds local reference composition. `verification.py::VerificationRequest` wraps the project with complete imported netlist bytes, manifests and relation. `VectorRequest` separately adds vector rows. `workflow.product` exports M4 JSON evidence with canonical checksum, reproduction request and engine binding. `App.tsx::openProject`, Save project and replay controls provide browser interchange with the CLI.

**Demonstration and tests.** The actual web-save/CLI-compose/web-re-import demonstration above passed. The original browser workflow passes evidence through an independent CLI process and replays it against an explicitly selected project. `test_product_roundtrip`, `test_bundle_recomputed_against_independent_project`, `test_chain_change_downgrades_export_and_replay` and binding attacks test the trust boundary.

**Missing behavior.** The current interchange unit is the full M3 execution request, even though CLI calls its file `--project`. A bare Project is not a self-contained executable package. There is no single normative package binding named user tests, multiple revisions, expected outcomes, evidence references and source licenses/provenance as one round-trippable specification. User vectors are a separate request shape; the web UI exposes the fixed sample table, not arbitrary named project test suites. `Semantics.testSuiteHash` identifies the engine's reference suite, not the user's project tests. M4 product envelopes use manually checked dictionaries, without their own exported JSON Schema. No project migration/export-downgrade policy is implemented.

Native engine hashes bind the exact platform build. A file from a different native build can fail trusted consume with IMPLEMENTATION_CHANGED; the project remains usable to run a fresh comparison on the new engine. Canonical semantic hashes exist, but browser JSON.stringify and independently timed runs do not guarantee byte-identical downloaded files. UI pin-option budgets and the HTTP 1 MiB limit are narrower than some core/CLI limits. Portable-completion criteria must specify a common profile.

**Dependencies and milestone.** M4.5-1 should introduce a new project package version and formal schemas for all new envelope types, preserving v1/M2/M3 readers and historical hashes. Add named vectors, project revision references, artifact digests, capability requirements and a migration report. Cross-platform replay must distinguish recorded-engine verification from fresh-engine reproduction. Tests must prove web-to-CLI-to-web preservation of all supported fields and fail closed on lossy conversion or unsupported versions.

## 6. Debugging diagnostics — PARTIAL

**Production locations.** `verification.py::mapped_outputs` evaluates mapped reference/candidate outputs; `compare` independently replays a SAT witness. `models.py::Witness` carries input and output bitvectors plus replay/minimization labels. `check_vectors` reports expected/actual outputs for user-provided vectors. `apps/web/src/Comparison.tsx::Verdict` renders inputs, aligned outputs, pin indices and 'Different' text with non-color double underlines. `Composer.tsx::row` exposes explicit connection editing and highlights the selected destination/source. The sample's Restore original action provides a predefined repair.

**Tests and evidence.** The demonstrated witness `01 -> reference 01 / candidate 10` is evaluator-reproduced. Browser B04 checks mapped output behavior, differing bits and announcements. `test_canary_and_every_witness_replays` tests mutations and evaluator replay. The existing workflow restores the original design and returns EQUIVALENT. Width/forward-reference validators reject invalid mappings, although errors often describe a structural class rather than locating each faulty connection.

**Missing behavior.** Reference output is a comparison baseline; its status as expected behavior depends on the user's intent anchor. There is no traced signal cone tying a differing bit to source component/pin edges, no ranked implicated connections, no reusable per-connection diagnostic artifact or general proposed correction. Manual selection highlight is independent of the computed witness. The fixed Restore original sample action is not a general diagnosis or repair engine. Counterexample minimization is heuristic, not a globally minimal cause.

**Dependencies and milestone.** M4.5-2D should add bounded evaluator tracing and stable component-to-emitted-signal source maps, then display implicated cones. A cone must be labeled as relevant computation rather than proof of a unique faulty edge. Candidate repairs require explicit user application and rerunning the trusted comparator/test suite; verification of one input alone is insufficient. Automated acceptance needs multi-output mappings, constants/REF boundaries, ambiguous causes, zero-input circuits and resource limits. Human usability checks must assess whether a first-time developer can explain and correct a new mutation.

## Architecture change, threat model and approval protocol

### Change admission

The latest user requirement establishes authorized tape-out as a future capability. The audit instruction authorizes planning only. Before implementation, publish a versioned successor decision to the read-only architecture and MVP constraints. Preserve the historical documents. Specify local signer custody, supported account types and chain, allowed target/function, quote limits, finality policy, crash recovery and human approval semantics. A static UI release approval and a mainnet spend approval are separate scoped decisions.

Keep the trusted verification core read-only. Introduce a separate proposed transaction-intent builder, policy/approval broker, human-controlled external signer adapter, submission adapter and durable reconciliation journal. An agent may prepare a proposal and consume verification results. It may not issue its own human grant, access private keys or choose an arbitrary contract call. A signer that accepts transactions from any same-origin/local client without policy enforcement would bypass this boundary.

### Assets, attackers and boundaries

Assets include the human's native currency and transistor resources, account nonce, exact circuit bytes and identity, approval scope, signing authority and receipt integrity. Treat projects, circuit descriptions, agent output, RPC responses, browser storage, build dependencies and imported evidence as untrusted. The threat model covers malicious or mistaken agents, hostile metadata/prompt injection, compromised web content, dishonest/stale RPC responses, concurrent jobs, mutable implementations, reorgs and crashes. A fully compromised OS or signer can defeat application checks and remains an explicit residual assumption.

| Threat | Required control and acceptance test |
|---|---|
| Metadata or agent text induces an unintended call | Structured allowlisted tape-out intent, escaped display labels, independent decoding at approval; malicious metadata cannot set target/function/value |
| Candidate, target, sender or environment changes after review | Bind exact calldata and circuit bytes, chain, sender, processor, ABI and implementation/dependency digests to the preview; invalidate approval on any mismatch |
| Wrong network or cross-chain transaction | Check wallet and RPC chain 196 before preview and before signing/submission; use chain-bound transaction signing and test collisions |
| Reused or spoofed human approval | Authenticated human-controlled broker, unpredictable one-use request ID, expiry, durable atomic consume/revoke state; agent cannot manufacture grants |
| Duplicate/replaced transaction or ambiguous RPC response | Reserve sender/chain/nonce, persist intent and signed-transaction hash before submission, reconcile first; any replacement requires a newly approved exact payload |
| Overspend through fees, tokens or parallel jobs | Integer native-value and gas caps, explicit token burn quantity and token contract/ID, per-operation and aggregate budget reservations including pending work; enforce in the broker and signer adapter |
| Receipt or circuit ID substituted | Bind transaction hash, receipt status, canonical block and selected processor; decode verified events and re-import the actual circuit bytes/metadata; never infer the new ID solely from a changing global nextId |
| Secret leakage or approval capability exported | Keep keys in the external signer; redact sensitive provider data; exclude grants and unbroadcast signed payloads from portable project/evidence exports |
| Upgrade/reorg/RPC equivocation | Fresh code/dependency/fee checks, reviewed ABI, explicit freshness window, confirmation policy and receipt canonicality checks; disagreement stops authorization |
| Crash after signing or submission | Durable journal and spend reservations survive restart; unknown outcomes remain pending reconciliation; retries do not silently create a second intent |

Transaction chain binding and account nonce address different replay domains from a human application's one-use approval. EIP-712 structured signing, if later selected for an authorization format, still requires application replay controls. Exact X Layer fee, gas accounting, transaction-type support, contract events and confirmation rules need separate current verification before a live acceptance. [EIP-155](https://eips.ethereum.org/EIPS/eip-155), [EIP-712](https://eips.ethereum.org/EIPS/eip-712), [Ethereum transaction structure](https://ethereum.org/developers/docs/transactions/)

### Proposed approval sequence

1. Prepare and validate a portable project; run declared tests and trusted comparison. Display the intended reference, verification limits and any UNKNOWN/STALE result. Human policy must define required verification outcomes and explicitly decide exceptions before write support is enabled.
2. Read chain and wallet identity, target registration, implementation/dependency closure, current fee, real account funds and token resources. Produce a bounded gas estimate where supported. If the provider cannot simulate or estimate the full operation, mark those fields UNKNOWN and block submission until an independently reviewed estimate/policy satisfies the required cap. The current burn-stage pre-flight alone cannot satisfy this requirement.
3. Build an immutable preview containing project/revision and source-manifest digests, full netlist/calldata and hashes, sender, chain 196, target/function, value/fee, gas quantity and price ceilings, total native-currency ceiling, token contract/ID/quantity, account nonce, observation block/hash, tool/ABI identities, expiry and one-use request ID. Use decimal strings/integer arithmetic. Include pending spend reservations in available budget.
4. Show both decoded intent and exact payload identity on a trusted human approval surface. Identify transistor consumption and remaining uncertainties. The human explicitly approves this one action with stated caps and expiry. Any acquisition, allowance change or separate transfer requires its own preview and approval. General task permission is insufficient.
5. Atomically reserve budget and nonce. Revalidate the preview dependencies and signer context immediately before invoking the external signer. Changes in account, chain, bytes, implementation, fee, nonce or caps require a replacement preview and fresh approval. The signer independently decodes/compares the payload to prevent a UI or agent substitution.
6. Journal the signed transaction hash and payload binding before submission, then submit only the approved transaction. Mark SUBMISSION_UNKNOWN on transport ambiguity. Reconcile by transaction hash and sender/nonce before any retry. Re-sending identical bytes under the same identity is different from approving a new transaction or fee replacement.
7. Track pending, replaced, reverted, dropped and reorged states. Release or settle budget according to actual costs and verified state; a revert can still consume gas. Record the chosen confirmation/finality threshold and evidence for that policy.
8. After required confirmations, derive the circuit ID from a verified event or other reviewed authoritative contract result, re-import its complete bytes and closure, and check against the approved composition. Emit a versioned circuit receipt bound to transaction, block, processor, circuit ID, netlist, manifests and authorization reference. Any mismatch remains a failed/reconciliation state.

Proposed durable states are PREPARED, AWAITING_APPROVAL, APPROVED, SIGNING, SIGNED, SUBMISSION_UNKNOWN, PENDING, CONFIRMED, REVERTED, REPLACED, DROPPED, REORGED, EXPIRED and REVOKED. Transitions need transactional storage and concurrency tests. Labels alone do not provide permission enforcement.

## Versioned migration proposal

Introduce a proposed `flip-project-2.0.0` package and separately versioned library-entry, diagnostic and transaction-intent/approval/receipt envelopes. Names are planning placeholders. Preserve all frozen schema files and readers. Publish new JSON Schema and generated frontend bindings with explicit supported-version dispatch. Require migration fixtures and canonical hash parity on both platforms.

Legacy execution-request import should preserve its exact bytes/hash as a referenced legacy artifact, then create a new package with an explicit mapping report and no newly inferred test, intent, freshness or spending authority. Missing project tests must remain visibly unspecified. Exporting to a legacy profile must reject unsupported fields or produce a separately acknowledged lossy-conversion report. Tests/evidence upgrades must invalidate derived package hashes and approval bindings. Approval capabilities and private signing data must never be valid project extensions.

Cross-platform policy should allow a fresh computation with a recorded new engine identity while retaining the original claim as historical evidence. It must not relabel an old proof as validated under a new engine. Define a shared web/CLI size and interface profile, plus a clearly documented CLI-only larger profile.

## Acceptance separation and next decision

Automated gates can establish parsers, deterministic artifacts, shared semantics, policy enforcement against doubles, nonce/budget concurrency, reorg recovery and receipt matching. They can also show rejection of fabricated approval/proof data. They cannot establish real account control, real spend approval, current mainnet discovery behavior or final publication merely from fixtures.

Manual acceptance must include keyboard/screen-reader review of the exact financial preview and a human refusal/expiry flow. Live read-only acceptance must verify discovery/ABI and real fee/resource observations. A live write acceptance needs separately authorized account, target, circuit bytes, spend ceilings and confirmation policy. Its receipt must be retained with exact block and transaction identity.

The prioritized [M4.5 engineering plan](M4_5_ENGINEERING_PLAN.md) defines the implementation gates. M5 must not describe the six capabilities as complete until each has its own evidence and the transaction authority design has been approved.
