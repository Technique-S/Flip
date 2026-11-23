# Release guard security review — independent

Target: `scripts/check_m45_release_package.mjs` and `apps/showcase/tests/release-guard.spec.mjs` at exact PR head `006050d7b8349dca3c263da2e3f1112617706541`.
Pristine result: `node apps/showcase/build.mjs && node scripts/check_m45_release_package.mjs` → **PASS: 19 checksummed inert files, 130 local links**; showcase suite **26/26** including the seven new cases.

**Verdict: BLOCKING FINDING (RG-01).** The PR removes a previously enforced self-integrity tripwire on the checker and replaces it with a historical trust root that is itself a mutable literal inside the checker. Retargeting that root or widening the historical exception set is not detected. A coordinated tamper of static release artifacts plus the inventory also passes.

## Change under review

```diff
+ const releaseSourceRef = "7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f";
+ const historicalSourcePaths = new Set([
+   "apps/web/package.json",
+   "apps/web/package-lock.json",
+   "scripts/check_m45_release_package.mjs",
+ ]);
+ execFileSync("git", ["merge-base", "--is-ancestor", releaseSourceRef, "HEAD"]);
+ const historicalFile = (name) => execFileSync("git", ["show", `${releaseSourceRef}:${name}`], ...);
+ const originalInventory = JSON.parse(historicalFile("docs/release/M45_R3_ASSET_INVENTORY.json"));
+ assert.deepEqual(inventory.sourceHashes, originalInventory.sourceHashes, ...);
...
- (await readFile(name, "utf8")).replaceAll("\r\n", "\n")
+ (historicalSourcePaths.has(name) ? historicalFile(name) : await readFile(name, "utf8")).replaceAll("\r\n", "\n")
```

The R3 inventory `sourceHashes` map was verified byte-identical to the inventory at the immutable accepted R3 commit `7ecfb9b…`, and all 12 recorded SHA/size pairs still validate — 9 against current checkout, 3 against Git history. The inventory itself is not in `sourceHashes`, and neither `staticChecksums` nor `staticChecksumManifest` is compared to the historical inventory.

## Adversarial method

Harness `release-guard-attack-harness.mjs` creates temporary scratch copies containing the checker, its recordings, current `dist`, docs, link targets and a `.git` pointer to the real object database. Each attack runs the **scratch copy** of the checker (a corrected harness detail — executing the pristine repository checker would invalidate the results) and records exit status and output. Results: `release-guard-attack-results.json`.

| Case | Expected | Observed | Finding |
|---|---|---|---|
| `coordinated-static-artifact-and-inventory-tamper` | REJECT | **PASS** | RG-02 |
| `single-original-source-hash-tamper` | REJECT | REJECT | — |
| `pinned-commit-identifier-retarget` | REJECT | **PASS** | RG-01 |
| `checker-allowlist-expansion-self-tamper` | REJECT | **PASS** | RG-01 |
| `checker-bypass-of-current-static-check` | REJECT | REJECT | — |
| `checker-allowlist-expansion-plus-current-source-tamper` | REJECT | **PASS** | RG-01 |

The shipped seven tests were independently re-run and all passed; they do not exercise any of the four accepted tampers above.

### Reproduction details

1. **RG-01 — checker self-tamper is invisible.** Replace `"scripts/check_m45_release_package.mjs",` in the `historicalSourcePaths` set with itself plus `"apps/showcase/style.css",`, and overwrite current `apps/showcase/style.css`. The executed checker is now the tampered file, but its own inventory hash entry is read with `git show 7ecfb9b…:scripts/check_m45_release_package.mjs` (because it is in the exempt set), so it matches the original inventory. The tampered current stylesheet is also read from history and matches. Output ends with `PASS:` — a current source file was modified and the guard approved it.
2. **RG-01 — pinned commit retarget.** Change `releaseSourceRef` to `39322e49f9fb1aa83a726fe3bbe81921c7e0f21e` (a real ancestor with identical protected paths, therefore an identical `sourceHashes` map). Output: `R3 historical source provenance at 39322e49…` followed by `PASS:`. No check binds the literal to the authorised commit identity.
3. **RG-02 — coordinated static tamper.** Append a marker to `apps/showcase/dist/index.html`; recompute `CHECKSUMS.json["index.html"]`; set `inventory.staticChecksums` to that recomputed map and `inventory.staticChecksumManifest.sha256` to the new manifest hash. `sourceHashes` is untouched. Output: `PASS:` with tampered static release content. The checker compares current `dist` to current `inventory` only; the historical inventory's static fields are never consulted.
4. **Pre-PR comparison.** `old-guard-self-tamper-check.mjs` restores the two dependency files to accepted-main bytes and appends a comment to the accepted-main checker. The pre-PR checker rejects with `AssertionError: Release source drift: scripts/check_m45_release_package.mjs` (exit 1). The PR-head checker accepts the equivalent self-tamper. This is a regression in an enforced guarantee, not merely a new design choice.

## Scope assessment

Authorised historical provenance: frontend `package.json`, frontend `package-lock.json`, and checker source — exactly the three paths in `historicalSourcePaths`. No other source path was added by the implementation. That part matches the handoff and the owner's documented authorisation. The problem is *how* those paths and the trust root are protected, not *which* paths were exempted.

The checker still performs all pre-existing current-checkout checks for non-exempt sources, static file extension allowlisting, CSP strings, local-link resolution, build capability flags and artefact checksums. Nothing was deleted from those paths. However, because the checker is now itself exempt from current-source validation, any future change to the checker — including weakening those checks — passes the source-hash phase without the inventory tripwire that previously forced a visible, reviewable inventory update.

## Required corrections (all before merge)

1. **Keep the checker in current-checkout validation.** Remove `scripts/check_m45_release_package.mjs` from `historicalSourcePaths`. If the checker must change in this PR, update the inventory entry for it in the same reviewed change, as was done for R3 originally. That preserves the self-drift tripwire.
2. **Bind the historical commit independently.** Verify `git rev-parse <ref>^{tree}` (and, preferably, the blob IDs of the three historical files) against constants stored in a *non-exempt, current-checked* file, so changing the literal in the checker cannot redirect provenance. Keep the ancestry assertion.
3. **Pin historical static checksums too.** Add `assert.deepEqual(inventory.staticChecksums, originalInventory.staticChecksums)` and `assert.equal(inventory.staticChecksumManifest.sha256, originalInventory.staticChecksumManifest.sha256)`. This makes coordinated static/inventory tamper fail.
4. **Restrict the exemption to exactly the two dependency files.** Treat any additional entry in `historicalSourcePaths` as a release-guard change requiring its own authorisation and inventory update.
5. **Add regression cases** for: checker self-tamper, pinned-commit retarget, allowlist expansion plus current-source tamper, and coordinated static + inventory tamper. Keep all seven existing cases and the original assertions unchanged.

## Bottom line

The historical R3 inventory source hashes and original checksums are intact at this head, and all shipped tests pass. But the newly introduced provenance mechanism is self-referential and therefore bypassable. Under the review mandate this is a blocking finding; V1 should not merge until RG-01 and RG-02 are corrected and RG-03's missing cases are added.
