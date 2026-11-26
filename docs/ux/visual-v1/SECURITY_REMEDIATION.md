# P7-V1 security remediation — independent re-review required

Previous head: `006050d7b8349dca3c263da2e3f1112617706541`. Independent FAIL: `1bfc6f677d6f4bd84ced14b078a96f6460f379a3` on branch `opencode/flip-visual-v1-independent-review`. Original reports/results remain unchanged on that branch. This report does not supersede the FAIL with a self-issued PASS.

## Before / after

The original attack bodies were reproduced before changing production code: six cases, four unexpected accepts (coordinated HTML/inventory modification, commit retarget, checker exemption expansion, exemption expansion plus current-source modification). Actual pre-fix results: `results/security-before.json`. Original harness bytes are retained as `results/original-attack-harness.mjs.txt`. Executable runner adapts relative import/output paths, creates scratch output directory and records stderr; attack bodies are unchanged. It executes the modified scratch checker, not the pristine repository checker.

RG-01: checker removed from historical exemption set. Current checker bytes are hashed against newly reviewed `docs/release/V1_RELEASE_TRUST.json`, without changing any original R3 inventory/hash. Exact exemption set is asserted to be only package.json and package-lock.json. Current checked-source keys are also asserted. Historical commit, tree and four blob identities (inventory, two dependency files, recording manifest) are independently recorded in this non-exempt metadata; ancestry remains required. Current checker changes require explicit metadata/checksum review.

RG-02: original sourceHashes plus staticChecksums, complete staticChecksumManifest, recordingHashes and runtime/audit identities are compared against the authorized historical inventory. Actual output still matches current CHECKSUMS and the validated historical fields. Existing CSP, no-network, link, file-type and source checks remain. Original inventory and recordings are byte-identical to accepted main.

RG-03: retain seven original guard cases; execute all six independent attacks as a regression with specific integrity diagnostics (current checker scope/hash, historical source inventory, historical static integrity). Additional test coordinates checker+metadata modification and executes the actual CI bootstrap code, requiring CI metadata-integrity rejection. Scratch cases retain valid link targets and history so unrelated missing files cannot satisfy assertions.

## Trust roots and limits

A checker cannot prevent arbitrary replacement of its own executable code. A second mutable file alone does not solve that problem. The standalone current-source tripwire detects the reviewed single-file attacks, not an attacker who can replace every validator.

A separate inline CI bootstrap pins the raw metadata SHA-256 in `.github/workflows/m1-contracts.yml`, checks current normalized checker bytes and the imported showcase library before invoking the checker. Metadata has LF checkout enforced for cross-platform byte identity. Chain: protected/reviewed workflow -> metadata digest -> current executable hashes and historical commit/tree/blobs -> historical inventory -> retained source/recording/static hashes -> actual current distribution. There is no hash cycle; historical R3 inventory is never rewritten to pin the changed checker. A future checker change requires metadata and workflow digest changes in the same explicit review.

**Owner action / not claimed enforced:** protect main and required status checks; require review of workflow, trust metadata, checker and imported library changes (CODEOWNERS/ruleset or equivalent protected-reference/required-workflow policy); restrict bypass and dismiss stale approvals on push. The main-branch protection API returned HTTP 404 "Branch not protected" during remediation. Required protection is an outstanding owner action; it is not established by this patch or by passing PR-owned CI. An attacker authorized to alter/bypass the protected workflow can change the inline digest or disable it. Merge remains contingent on independent review of this complete delta and the owner's policy decision. No claim of resistance to a fully compromised repository/runner/Git object store.

## Remaining review findings

UX-01: Visual explicitly explains that Build/compare remain in Advanced, with a visible Return to Advanced actions button. It switches view only, duplicating no execution. Focused browser test checks that Build stays hidden in Visual and becomes available through the obvious return action.

PROJ-01: source aliases and used REF aliases now use canonical Name syntax guards. PROJ-02: cumulative ports and connections are checked before each allocation, rather than only after materialization. Both are display protections only, not a new validation authority. Existing postconditions and canonical recipe meaning are unchanged.

No Python core, frozen schemas, old projection observations, original R3 inventory/recordings or reviewer evidence changed. No V2, semantic editing, transaction, hosting or deployment work.

## Validation / review handoff

Local and final-head hosted results are recorded on draft PR #12 after execution. No running check counts as PASS. Review should inspect exact corrected head and re-run all four accepted attacks plus the coordinated bootstrap attack. Prior failures and corrected scratch-test issues remain distinguishable from successful final runs. The original review FAIL remains the merge disposition until a new independent review says otherwise.

Reproduce: `node apps/showcase/build.mjs`, `node scripts/check_m45_release_package.mjs`, `node apps/showcase/test.mjs`, `npm test --prefix apps/web`, `uv run --frozen pytest -q`, existing nine schema export and three canonical parity commands, Ruff/lint/build, clean committed-tree custody scan. Hosted CI runs all these on Windows/Ubuntu. Exact implementation/head SHAs and run links are recorded on PR #12 rather than embedded self-referentially here.
