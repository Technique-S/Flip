# Original adversarial attacks — independent retest

Corrected target: `53a7f1cdd729188c7bfd593d37049836b6ed6a12`. Previously failed head: `006050d7b8349dca3c263da2e3f1112617706541`.
Original FAIL evidence branch/commit: `opencode/flip-visual-v1-independent-review` / `1bfc6f677d6f4bd84ced14b078a96f6460f379a3` — verified unchanged.
Harness: `security-rereview-harness.mjs`; machine-readable output: `security-rereview-results.json`. Implementer replay: `docs/ux/visual-v1/results/run-attack-harness.mjs` (retained original bodies; byte-identical harness proven by normalized SHA comparison).

**Result: all four previously accepted attacks are now rejected at the intended integrity boundary. 19/19 harness cases OK.**

## Four original bypasses

| Original attack | Old outcome | New outcome | Triggering check (verified in stderr) | Command |
|---|---|---|---|---|
| 1. Checker self-tamper / exemption expansion | ACCEPT | **REJECT** (exit 1) | `Current checker integrity mismatch` (plain tamper); `Current checker scope changed` (allowlist expansion) | `node <scratch>/scripts/check_m45_release_package.mjs` from scratch cwd |
| 2. Historical commit retarget | ACCEPT | **REJECT** (exit 1) | `Current checker integrity mismatch` (checker edit) and `Authorized historical commit mismatch` (metadata-only retarget) | same |
| 3. Exemption expansion + current-source tamper | ACCEPT | **REJECT** (exit 1) | `Current checker scope changed` | same |
| 4. Coordinated artifact + inventory checksum tamper | ACCEPT | **REJECT** (exit 1) | `Historical static integrity mismatch: staticChecksums` | same |

Case identifiers: `B1-checker-self-tamper`, `B1b-checker-exemption-expansion`, `B2-historical-commit-retarget-checker`, `B2b-historical-commit-retarget-metadata`, `B3-exemption-expansion-plus-current-source-tamper`, `B4-coordinated-artifact-and-inventory-tamper`.

Additional confirmations: `B0-pristine-checker` PASS with `PASS: 19 checksummed inert files, 130 local links`; `B5-source-hash-tamper` REJECT via `Historical R3 source inventory changed`. The implementer's six-case replay also reports 6/6 REJECT with boundary-specific assertions in the showcase suite (`release-guard.spec.mjs:79`).

## Method controls

- Scratch copies contain the checker, trust metadata, full inventory source-hash paths, README files, all `docs/release` files, `apps/showcase/dist`, `apps/showcase/recordings` and every documentation link target. Failures therefore originate from integrity checks, not missing fixtures.
- The **modified scratch checker** is executed (`spawnSync(process.execPath, [join(root, "scripts/check_m45_release_package.mjs")], {cwd: root})`). Running the pristine repository checker would invalidate the test.
- Each case asserts both exit status and a diagnostic regex; a generic process failure without the expected protection is recorded as FAIL, not credited.
- Original pre-fix baselines in `docs/ux/visual-v1/results/security-before.json` record four unexpected accepts at `006050d7…`.

## Bootstrap challenges (Phase D)

Exact inline bootstrap code was extracted from `.github/workflows/m1-contracts.yml` and executed with `node --input-type=module -e <code>` in the scratch tree.

| Case | Expected | Observed | Diagnostic |
|---|---|---|---|
| D0 pristine | PASS | PASS | — |
| D1 changed checker, unchanged metadata | REJECT | REJECT | `CI checker integrity mismatch` |
| D2 changed metadata, unchanged workflow digest | REJECT | REJECT | `CI release trust metadata mismatch` |
| D3 changed imported `apps/showcase/lib.mjs` | REJECT | REJECT | `CI checker integrity mismatch` |
| D4 missing trust metadata | REJECT | REJECT | `ENOENT` |
| D5 invalid checksum formatting | REJECT | REJECT | `CI release trust metadata mismatch` |
| D6 checker + metadata coordinated | REJECT | REJECT | `CI release trust metadata mismatch` |
| D7 unauthorized historical tree identity | REJECT | REJECT | `Historical tree mismatch` |
| D9 CRLF checker | PASS | PASS | normalized before hashing |
| D10 CRLF trust metadata | REJECT | REJECT | `CI release trust metadata mismatch` (gitattributes enforces LF) |

**D8 (residual):** when the checker, its metadata hash and the workflow's inline metadata digest are all changed consistently, the bootstrap **PASSES** and the checker's current-source check passes. This demonstrates that the bootstrap is only as trustworthy as the workflow that carries it. Because `main` is currently unprotected, this remains an exploitable repository-level path, requiring owner branch protection (see `TRUST_ROOT_ASSESSMENT.md`).
