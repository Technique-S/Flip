# Baseline verification and execution record

Date: 2026-11-23, Africa/Lagos. Original repository/worktree clean. Fetched origin and inspected main, pending PRs and PR #11 release. Accepted main is **`7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f`**; `gh pr list --state open` returned `[]`. [Main Windows/Linux CI 45171298993](https://github.com/Technique-S/Flip/actions/runs/45171298993) is completed SUCCESS at that exact SHA. PR #11 and its conditional independent review are preserved; no release/deployment authorization follows from that merge.

New research branch `codex/flip-visual-architecture` starts at audit `6427b1b291f67151cc62ba413dc607e40be2af72`, itself documentation-only above main. Prior audit files remain unchanged. [Checksum manifest](evidence/baseline.json) records exact accepted Git tree IDs, Git blob IDs and SHA-256 of **Git bytes** for 21 implementation/toolchain files; checkout CRLF normalization is not confused with canonical source changes. Protected tree equality against main passed. No installed graph package or lockfile change.

Source directive copied without alteration from the user attachment to [directive.txt](source/directive.txt), SHA-256 `d3b8d86853ca70363f6900125a2aa56e81b2b8ac973530be8165e83a267ab1cb`. Authoritative pre-M5 TXT SHA-256 is `f1f5629cf3323be909e067eda34a1108d4f5e35d7aa26fb975b2ee3715085c95`; requested `.md` location is absent, documented rather than fabricated.

## Inspected current implementation

The relevant current files were reread in this task, not inferred solely from the old report:

| Source at accepted main | Observed fact / architecture implication |
|---|---|
| `apps/web/src/App.tsx:21`, `replace/change` around :260–296 | Five current workflow pages; existing UI interactive pin budget and shared mutation path clear built/proof state. Composition-local integration can preserve shell. |
| `Composer.tsx:92`, `model.ts:1–80` | Numeric NAND/REF table, not graph editor; explicit scalar Pin and ordered Design. Existing Advanced remains usable. |
| `style.css:4–15` | Ink #17191D, cobalt #0055CC, white/neutral palette, 15px Inter/Segoe UI/Arial basis. No redesign needed. |
| `models.py:186–284`, `composition_models.py:22–73` | Strict PinSource/Component union, one-bit pins, arity, backward references, uint64 REF IDs, stateless and complete mapping checks. No LATCH recipe variant. |
| `composition.py:42–170` | Trusted import/closure binding; NAND/REF emission; stateless source guard and final-output copy NANDs. UI must not invent binary indexes or equivalent sorting rules. |
| `tap02.py::decode`, `execution.py::beat/evaluate` | Bounded LATCH decoder/beat exists below current stateless compose/verification interface. Not a current editor/trace feature. |
| `verification.py:135–195` | Shared compiler, SAT worker and independently evaluated witness; timeout/replay failure remains UNKNOWN. Structural validation isn't proof. |
| `debugging_models.py:36–107`, `debugging.py::ConeTracer/prior_action/execute` | Side/path/hash-qualified relevant connections, ambiguity and correction bindings; no uniquely proven defective wire or arbitrary internal signal-value API. |
| `portable.py:77–110`, portable schema | Fixed hash preimages/strict 1.1 fields; no layout. New version needed. |
| API/CLI dispatch and local guards | Existing compose/vectors/compare/debug/portable transport shared with core; no graph-specific decoder projection endpoint, signer or public solver. |

AGENTS, README, current milestone update TXT, PRD, technical constraints, architecture/ownership/dependencies, P1–P6 acceptance records and R3 release evidence are the governance baseline. The previous [exact evidence index](../pre-m5/EVIDENCE.md) links accepted code/tests and retained platform results. Source inspection supports adapter design; it does not prove proposed features work.

## Actual checks this task

Reused CPython 3.14.6 environment at `C:/Users/Kazi/Documents/Flip/repo/.venv/Scripts/python.exe`; explicit PYTHONPATH points to this new worktree's core/CLI/API source. No native clean-install claim. Node toolchain declared/previously observed 24.18.0; installed React 19.3.1, TypeScript 7.0.2 and esbuild 0.28.2 remain lockfile facts. Graph compatibility was researched via npm metadata only, not tested by installing/building it.

```powershell
$env:PYTHONPATH = "$PWD/packages/flip-core/src;$PWD/packages/flip-cli/src;$PWD/packages/flip-api/src"
& C:/Users/Kazi/Documents/Flip/repo/.venv/Scripts/python.exe -m pytest packages/flip-core/tests/test_m3_engine.py::test_audited_81_bytes_100_builds_and_truth_table packages/flip-core/tests/test_m3_engine.py::test_real_xor_nand_wrapper_and_stateful_rejection packages/flip-core/tests/test_m45_portable.py::test_named_roundtrip_exact_request_hash_and_bytes packages/flip-core/tests/test_m45_debugging_adversarial.py::test_nonidentity_pin_order_selects_correct_reference_and_candidate_trace_roots -q --junitxml=.test-tmp/architecture-baseline.xml
```

Result: **4 passed in 2.94 seconds**, zero skips/failures/errors. [Unedited JUnit](evidence/baseline-junit.xml), SHA-256 `ae77abc27b1cea91478ae74451eaca9da3767f6505ae6ffd98b6531b10c22064`.

The earlier audit's 140 Python/4 browser passes, frontend build/lint and 921-file custody scan remain separately attributed evidence at `6427b1b`; these were not recredited as fresh full-suite checks. Current task did not rerun the whole browser suite because runtime is unchanged. New renderer benchmarks, guided project completion, mouse/touch editor tests and human trials remain NOT TESTED. No source fixture regeneration, live RPC, transaction, hosting or signing was performed.

`npm view` outputs for React Flow 13.0.2, Rete 2.0.6 and React plugin 2.1.2 are preserved as parsed primary registry observations in baseline.json. Peer ranges are not build results. References were read through web tools; the attempted Logisim `LICENSE` URL returned 404, so upstream README's license section and supplied documentation were used instead. No inference of licensing from the failed URL.

Final documentation checks validate internal links, exact captured source/report checksums, four JUnit outcomes, protected paths and unchanged prior audit. Raw source snapshots intentionally retain original Markdown hard-break whitespace; they are excluded from authored-document whitespace normalization. No production policy/test/custody guard is changed. Final commit SHA and push verification are reported in the chat handoff, avoiding a self-referential containing-commit hash.
