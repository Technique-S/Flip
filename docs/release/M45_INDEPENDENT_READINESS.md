# M4.5-R — independent release evidence matrix

**Baseline reviewed:** `09f2482beae84be6d919ecd6957c4153d1924cca` (accepted
main, merge commit #4). **Role:** independent evidence collection for Codex's
authoritative engineering gap audit. This report does not replace that audit
and does not infer implementation from PRD or architecture plans.

**Classification rules**
- `VERIFIED` — implementation file and at least one executed test/report or
  directly reproduced command on the baseline.
- `PARTIAL` — some sub-items verified; others missing or only adjacent
  primitives exist.
- `MISSING` — zero implementation matches in source.
- `NOT TESTED` — code exists but no executed evidence was found/performed here.
- `BLOCKED` — cannot be verified under current constraints (no assistive-tech
  session, no public deployment, no write authorization).

## Capability 1 — Human and coding-agent workflows: **PARTIAL**

| Sub-item | Class | Evidence |
| --- | --- | --- |
| Human visual UI | VERIFIED | `apps/web/src/App.tsx` (four-page workflow, Sources/Composition/Wiring Canary/Evidence), `Composer.tsx`, `Comparison.tsx`, `model.ts`, `style.css`; tests `apps/web/tests/acceptance.spec.ts` (B01–B11), `workflow.spec.ts`, `review.spec.ts`; `M4_ACCEPTANCE.md` lines 61, 85 report 11 Chromium tests passing per platform. |
| Agent-native CLI | VERIFIED | `packages/flip-cli/src/flip_cli/main.py` implements `validate`, `canonical`, `hash`, `sample`, `import`, `inspect`, `new-project`, `compose`, `compare`, `vectors`, `consume`, `preflight`, `revalidate`, `export`, `inspect-evidence`, `verify-bundle` with canonical JSON output and typed `ExitCode`; `packages/flip-cli/tests/test_cli.py::test_reserved_operations`, `test_contract_commands`, `test_invalid_arguments_structured`, `test_wrong_chain_cli`. CLI demo executed on this baseline (see `M45_DEMO_SCRIPT.md`). |
| Structured I/O schemas | VERIFIED | `flip_core/models.py` (`CONTRACTS`, `CircuitIdentity`, `Project`, `Manifest`, `ComparisonReport`, `Witness`, `Preflight`, `ErrorEnvelope`), `import_models.py`, `composition_models.py`, `verification.py`; `contracts.py::validate_contract`; frozen `docs/schema/1.0.0/`, `m2/1.0.0/`, `m3/1.0.0/`; `test_contracts.py::test_roundtrip_schema_and_determinism`, `test_generated_schemas_have_no_drift`, `test_unsupported_versions`, `test_wrong_chain`. |
| Shared canonical engine | VERIFIED | `flip_core/verification.py::compare/consume/check_vectors/engine_identity/execute`, `canonical.py`, `execution.py`, `cnf.py`, `isolation.py`, `solver_worker.py`, `workflow.py::product`; API routes in `flip_api/app.py` call the same core; `test_m3_engine.py`, `test_m4_workflow.py::test_product_roundtrip`. |
| Agent build/test/verify loop | PARTIAL | Tooling exists (`package.json` lint/build/test; `.github/workflows/m1-contracts.yml`; `scripts/smoke_m1.py`, `smoke_m3.py`, `check_m1_repository.py`, `report_m3_acceptance.py`, `report_m4_acceptance.py`, `benchmark_m3.py`), but no single agent-orchestrated loop command/endpoint was found. |
| Explicit human deployment approval | MISSING | Zero implementation matches in `packages/` and `apps/web/src`. The UI trust assertion ("Why do you trust this reference?") is a reference-trust declaration, not deployment approval. `M4_ACCEPTANCE.md` lines 71, 81 state no signing/wallet/payment/broadcast and no M5 deployment authorization. |

**Potential discrepancy for Codex:** "agent build/test/verify loop" should not be
marked VERIFIED merely because CI runs those commands; no agent-facing
orchestration surface exists on this baseline.

## Capability 2 — Circuit and processor library: **MISSING** (as a library)

| Sub-item | Class | Evidence |
| --- | --- | --- |
| Verified processor addresses | PARTIAL | `flip_core/abi.py::FACTORY`, `preflight.py::CALLER/IMPLEMENTATION/PROXY`; `importer.py::PinnedReader.environment()` validates `isCPU`, factory, beacon slot and code hashes dynamically. No curated "verified processors" registry; the sample processor address appears in docs/fixtures, not a code registry. |
| Circuit address/reference discovery | MISSING | No source enumerates circuits. `nextId` is used only for existence checks (`importer.py:244-245`); import/inspect require an explicit processor and ID. |
| Live X Layer factory discovery | PARTIAL | `importer.py:148-163` reads factory code, implementation slot, beacon and `isSealed`; `preflight.py:92-99` rechecks hashes. This is inspection of a hardcoded factory address, not discovery of a factory. |
| Search and metadata | MISSING | Zero feature matches for search/catalog/browse/metadata in source. |
| Verified favorites | MISSING | Zero matches. |
| Recently imported circuits | MISSING | No UI history. `flip_core/integrity.py::ContentCache` is a bounded 16-entry content cache that downgrades freshness; it is not a recent-imports library. |
| Chain and provenance labels | VERIFIED (pinned sources) | `models.py::Freshness/Integrity/Manifest.observation`, `import_models.py::trust="SINGLE_RPC_OBSERVATION"`, `pinning="NUMBER_WITH_HEADER_RECHECK"`, web `SourceCard` displaying processor/hash/block/gates; `test_revalidation_detects_real_closure_changes`, `test_corpus_coverage_and_provenance_are_not_promoted`. |

**Potential discrepancy:** do not count a pinned factory constant plus a docs
address as a "verified circuit library"; no discovery/search/favorites exist.

## Capability 3 — Authorized X Layer tape-out lifecycle: **MISSING**

| Sub-item | Class | Evidence |
| --- | --- | --- |
| Circuit preparation | VERIFIED | `flip_core/workflow.py::project_from_import`, `product("new-project")`, CLI `--source/--project`; `test_new_project_import_only`, `test_product_roundtrip`. |
| Structural validation | VERIFIED | `flip_core/preflight.py::classify/preflight`, `tap02.py::decode`, strict importer; `test_preflight_transport`, `test_preflight_requires_current_fee_and_matching_block`; M4 acceptance lines 35, 37. |
| Live fee / resource estimates | PARTIAL | Fee read via selector `0xadfb2b69` (`preflight.py:42`), `CallObservation.feeWei`, `test_historical_preflight_fixture` (`1300000000000000`). No `estimateGas`; audit recorded `estimateGas` blocked by burn revert (`M05/SECURITY_REVIEW.md`). |
| Transaction preview | MISSING | No transaction construction; `Preflight.mode = "READ_ONLY_ETH_CALL"`; the synthetic balance override is confined to one `eth_call`. |
| Explicit authorization | MISSING | Zero matches for approval/authorization/sign in product source. |
| Submission | MISSING | Zero matches; `rpc.py::READ_METHODS` allowlists five read methods and explicitly rejects `eth_sendRawTransaction` (`test_m2_import.py::test_retry_budget_and_bad_rpc_envelopes`). |
| Confirmation | MISSING | Zero matches. |
| Final circuit receipt | MISSING | Zero matches. |

**No write transaction was executed.** This capability is a proposed future
scope, not an existing feature; the official hackathon FAQ does not require a
newly deployed processor or circuit (see `M45_HACKATHON_COMPLIANCE.md` H-08).

## Capability 4 — Agent execution safety: **PARTIAL**

| Sub-item | Class | Evidence |
| --- | --- | --- |
| Permission boundaries | VERIFIED | `rpc.py::READ_METHODS`, selector allowlist, endpoint validation, `trust_env=False`; `flip_api/local.py` loopback peer + TrustedHost + Origin/cross-site + CSP; `app.py` body cap/solver gate; tests `test_local_service_transport_boundary`, `test_public_or_disabled_native_rejected`, `test_concurrency_closed`, `test_api_never_publicly_enables_native_solver`. Independent probes T-01…T-14 recorded 400 Host, 403 origin/cross-site, 413 oversized, 429 on excess parallelism. |
| Human approval | MISSING | Zero implementation matches; only the reference-trust assertion exists. |
| Chain verification | VERIFIED | `importer.py::eth_chainId==196`, block pin and reorg check, environment hashes; `preflight.py:80-99`; `test_wrong_chain_fails_before_state_reads`, M3/M4 wrong-chain corpus. |
| Transaction preview | MISSING | Same as Capability 3. |
| Spending limits | MISSING | No monetary limit code; implemented caps are compute/resource budgets (`models.py::Limits`, `ImportBudget`, RPC request cap, solver isolation). |
| Credential safeguards | VERIFIED (scanning) | `scripts/check_m1_repository.py::credential scan`, M2 verifier scan, `test_git_provenance_and_secret_patterns`; no key/wallet handling in runtime. |
| Idempotency / replay protection | PARTIAL | No transaction idempotency/nonce (no writes). Verification-level protection exists: `verification.py::consume` recomputes, pins hashes, reruns UNSAT and replays DIFFERENT; `workflow.py::verify-bundle`; tests `test_trusted_consumer_reruns_and_rejects_fabricated_equivalence`, `test_bundle_attacks`, `test_bundle_recomputed_against_independent_project`. |
| Failure recovery | VERIFIED | `rpc.py` bounded retries/deadline, `UNKNOWN` semantics, worker cleanup; UI session restore and confirmed reset; tests `test_interfaces_recover_after_timeout`, `B07`, `B08`, `B09`, `test_timeout_crash_and_memory_containment`, `test_platform_fail_closed_and_repeated_cleanup`. |

## Capability 5 — Portable circuit project format: **VERIFIED**

| Sub-item | Class | Evidence |
| --- | --- | --- |
| Web-to-CLI exchange | VERIFIED | Web `download("project.json", req)` and `openProject()` in `App.tsx`; CLI `--project`; `workflow.spec.ts` browser→CLI parity; `test_product_roundtrip`. |
| Versioned schema | VERIFIED | `1.0.0`, `m3-1.0.0`, `m4-1.0.0` literals; strict rejection via `contracts.py`; `docs/schema/README.md`; `test_unsupported_versions`. |
| Circuit/processor identities | VERIFIED | `CircuitIdentity`, `Source`, `Snapshot`, `Environment`; import binding checks; `docs/schema/examples/project.json`. |
| Test vectors | PARTIAL | `ExpectedVector`, `VectorRequest`, `check_vectors()` with mismatches/coverage, CLI `vectors`, API `/api/v1/vectors`; but a separate request, not a field of `project.json`. |
| Verification manifests | VERIFIED | `Manifest`, `ComparisonReport`, `FLIP_EVIDENCE` envelope with `contentHash`, `limitations`, `reproduce`. |
| Export/re-import | VERIFIED | `workflow.py::product("export"/"verify-bundle")`, `inspect-evidence`, API routes, web Evidence page; tests `test_chain_change_downgrades_export_and_replay`, `test_bundle_attacks`. |
| Deterministic reproduction | VERIFIED | `canonical.py::flip-json-v1`, `content_hash`, `engine_identity()`, `reproduction`/`requestHash`, Node parity script; tests `test_canonical_golden`, `test_full_request_python_node_hash_parity`. |

## Capability 6 — Circuit debugging diagnostics: **PARTIAL**

| Sub-item | Class | Evidence |
| --- | --- | --- |
| Counterexample inputs | VERIFIED | `models.py::Witness`; `verification.py:168-181` SAT witness with independent replay; UI "Replayed counterexample"; tests `test_independent_witnesses`, `test_canary_and_every_witness_replays`, `test_different_requires_replayed_distinguishing_witness`. Executed demo witness `01 → reference 01 / candidate 10`. |
| Actual vs expected outputs | VERIFIED | Vector `mismatches` with `expected`/`actual`; web truth table "Expected / Observed"; witness "Reference / Candidate"; B04. |
| Bit-level differences | VERIFIED | `Comparison.tsx:45-57` per-pin `≠ Different` / `= Same` text plus double underline; witness width validation. |
| Connection-level diagnostics | MISSING | Zero matches mapping a differing bit back to a component/pin/netlist connection. Only manual "Swap outputs / Restore original" for the sample and endpoint highlighting in the editor. |
| Actionable correction guidance | MISSING | No wired `nextAction`/guidance in web or CLI source. The `fixtures/m4-ux-acceptance/error-messages/error-catalog.json` fixture proposes copy but is not consumed by the application. |
| Difference-vs-fault distinction | VERIFIED | `Comparison.tsx` undeclared-intent text; `verification.py::correctness=INTENT_UNKNOWN`; `ComparisonPlan.intent_asserted`; tests `test_equivalence_is_relative_and_freshness_independent`, `test_unknown_never_equivalent_and_requires_reason`. |

## Cross-cutting evidence limits

- Manual auditory screen-reader session: **BLOCKED / NOT TESTED** (`M4_ACCEPTANCE.md` line 27; independent review §7). Browser AX-tree and live-region checks are not a replacement.
- Live X Layer import/revalidation on this baseline: **NOT TESTED** in this task; executed CLI cases used a local RPC double. One prior read-only pre-flight was observed at block 76234348 and recorded in `M4_A_LIVE_PREFLIGHT.json`.
- Public deployment controls: **BLOCKED**; no public instance exists.
- All six capability conclusions are based on files at `09f2482` plus tests/reports cited above; no PRD requirement alone was treated as implementation evidence.

## Overall independent view

Capabilities 5 and parts of 1/4/6 are release-evidence backed. Capability 2 is
missing as a library, capability 3 is missing as a lifecycle, and capability 1's
human deployment approval and capability 4's transaction approval/spending
limits are absent **by design** because no write path exists. Codex should
decide whether these are M5 scope additions or acceptance criteria to be
explicitly marked out of scope.
