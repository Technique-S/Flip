# Trust-root assessment — corrected V1 release guard

## Architecture as implemented

1. `.github/workflows/m1-contracts.yml` (line 35-48) pins the raw SHA-256 of `docs/release/V1_RELEASE_TRUST.json` and verifies the current normalized bytes of the checker (`currentSourceHashes`) and the imported showcase library (`bootstrapSourceHashes`) **before** invoking the release checker.
2. `docs/release/V1_RELEASE_TRUST.json` records the authorized historical commit/tree/four blob IDs, the current checker hash and the bootstrap library hash. `.gitattributes` forces LF checkout for this file so its raw digest is platform-stable.
3. `scripts/check_m45_release_package.mjs` validates current checker bytes, asserts the exact current-checked and historical-exemption sets, pins the historical commit/tree/blobs, and compares the full historical integrity fields of the inventory before checking current artifacts.

## Independently verified values

| Object | Expected | Observed |
|---|---|---|
| Historical commit | `7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f` | matches `trust.commit` and hardcoded `releaseSourceRef` |
| Historical tree | `1acefac7b498167b970044f872e8a753ac6b6917` | `git rev-parse <ref>^{tree}` matches |
| Inventory blob | `65fda37f236db96a35e6abee210ab408ca6aa019` | matches |
| `apps/web/package.json` blob | `bda099080b6ca7d8ce70cb002c835ecd82c397f2` | matches |
| `apps/web/package-lock.json` blob | `8ac5579e7167c3369f288de29bfc6a27b90e2ef6` | matches |
| `apps/showcase/recordings/manifest.json` blob | `1cad0d727d0b22d34d2b236f28e9f6795cb23a65` | matches |
| Trust metadata raw SHA-256 | `c7f129581342c63887ec0d90c5e62bf3daa17f79468d63cbc0ba4f387901c1f0` | matches workflow inline constant |
| Current checker SHA-256 (LF-normalized) | `75ca91168241181626ab443f6a638681e7067d3b6ae8694e10eaad12cea7dfb1` | matches |
| `apps/showcase/lib.mjs` SHA-256 | `d123aa28ac8431bad73d02186e99e9d764477554cda1ae31c5ad712ab341c834` | matches |

Historical inventory fields `sourceHashes`, `staticChecksums`, `staticChecksumManifest`, `recordingHashes`, `acceptedRuntimeSha` and `r2AuditSha` are byte-equal to the same JSON blob at the immutable R3 commit. Current `CHECKSUMS.json` and its manifest hash are validated against those pinned fields. The remaining descriptive inventory fields (`dependencyMetadata`, `validation`, `distribution`, `branch`, etc.) are not consumed by the checker for authorization; tampering with them does not change artifact decisions.

## Required properties

| Property | Assessment |
|---|---|
| Current checker bytes validated | YES (`currentSourceHashes` + checker lines 11-15 + CI bootstrap) |
| Exemption set exact and minimal | YES (`historicalSourcePaths` asserted equal to exactly two dependency files, line 116; `currentCheckedPaths` asserted equal to metadata keys, line 11) |
| Trusted metadata includes current executable hashes | YES (checker + showcase lib) |
| Bootstrap runs before checker in CI | YES (workflow step 35-49) |
| Historical commit/tree/blob consistency | YES (all five values verified above) |
| Historical source/static/recording/manifest identities authenticated | YES (lines 119-120, six fields) |
| Current generated artifacts validated | YES (`sums` vs pinned `staticChecksums`; CHECKSUMS sha vs pinned manifest) |
| No circular hash dependency | YES in code: metadata digest lives in workflow, workflow digest does not live in metadata, historical inventory blob ID lives in metadata. The cycle is closed only by an external protected workflow (see below). |
| Missing Git objects / invalid ancestry fail closed | YES (shipped `missing-history`, `wrong-history`; D7 tree mismatch) |
| Windows/Ubuntu line endings | YES (checker/lib normalized; metadata forced LF by `.gitattributes`; D9/D10 confirm) |
| No fallback expands trusted scope | YES (exact set assertions; no generic catch that widens checks) |
| Tampered trust metadata rejected | YES (B2b, D2, D5, D7) |

## What the CI bootstrap detects vs what it cannot

The bootstrap detects: a checker changed without metadata, metadata changed without the workflow digest, a changed imported library, malformed/missing metadata, and a mismatch between current executable bytes and metadata. These are all PR-visible changes inside a single branch.

It **cannot** detect a coordinated change to checker + metadata + the workflow digest, because the digest is stored in the same mutable workflow that the PR may edit. Case D8 demonstrated that such a coordinated change passes both the bootstrap and the checker. The handoff acknowledges this and assigns it to owner-controlled branch protection; this review independently confirms the need.

**The workflow is PR content, not an independently protected trust root.** Calling it one would be incorrect.

## Repository-level control needed (owner action)

Verified independently: `GET /repos/Technique-S/Flip/branches/main/protection` returns HTTP 404 `Branch not protected`. Required controls before merge:

- Protect `main`; require the `contracts` status check to succeed for both `ubuntu-latest` and `windows-latest` matrix legs.
- Require review of changes to `.github/workflows/m1-contracts.yml`, `docs/release/V1_RELEASE_TRUST.json`, `scripts/check_m45_release_package.mjs` and `apps/showcase/lib.mjs` (ruleset/CODEOWNERS or equivalent).
- Dismiss stale approvals on new pushes; do not allow bypass actors to skip required checks.

With those controls, D8 requires an authorised reviewer and cannot be self-approved by the PR author. Until then, the repository-level posture is **FAIL** even though the code-level guard is correct.

## Residual assumptions

- Trust in the Git object store and in the protected workflow/reviewer set.
- No claim of resistance to a fully compromised runner, GitHub account with bypass rights, or replacement of the Git object database.
- CI per-platform test counts could not be read from the log-receiver endpoint in this environment; job/step conclusions were verified and local counts match the implementer's report.
