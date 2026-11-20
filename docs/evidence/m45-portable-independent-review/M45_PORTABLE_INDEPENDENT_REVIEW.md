# M4.5-1P-V — Independent Portable Project 1.1 review

**Role:** independent supporting verification engineer (OpenCode / HY4 Flash).

| Role | Exact SHA |
|---|---|
| Accepted baseline | `bba6f3d301b08c0dcbbfd0b363b99a15179414db` (ancestor confirmed) |
| **Delivery SHA tested** | **`136b1115ee0f5ffe0a5583d68c474641fdce1ca1`** (equals remote head; no newer delta) |
| Independent corpus | `2f3d6263edf4e62ad4e94718c99f6c1a79e350a1` (separate branch; NOT an ancestor — expected) |

**Recommendation: CONDITIONAL PASS.** No integrity, authority or revision-chain defect was
found. One host-specific, timing-sensitive inherited Chromium test is flaky under full-suite
load; it passes in isolation and is not a Portable defect.

## 1. Commands executed

```powershell
# independent harnesses (real core/CLI/API)
.venv\Scripts\python.exe fixtures/m45-portable-independent-review/harness/portable_acceptance.py
.venv\Scripts\python.exe fixtures/m45-portable-independent-review/harness/evidence_trust.py
.venv\Scripts\python.exe fixtures/m45-portable-independent-review/harness/portable_api.py

# original 12-case corpus + focused production tests
.venv\Scripts\python.exe scripts/check_m45_portability.py
.venv\Scripts\python.exe -m pytest -q packages/flip-core/tests/test_m45_portable.py -o junit_family=legacy

# browser / schema / parity / custody
cd apps/web; npm run build; npm test -- --reporter=list
cd ..; node docs/schema/m45-portable-project/check-canonical.mjs
.venv\Scripts\python.exe -m flip_core.portable_schema_export --out docs/schema/m45-portable-project/1.1.0 --check
.venv\Scripts\python.exe scripts/check_m1_repository.py
.venv\Scripts\python.exe -m pytest -q --junitxml=... -o junit_family=legacy
```

## 2. Task A — legacy compatibility (independent, A01–A08)

| Case | Observed |
|---|---|
| Legacy file accepted by `flip compose` | exit 0, netlist hash `3dbb65a6…3ce` |
| 81-byte half-adder byte-identical | matches archived digest |
| Legacy wrapped in Portable 1.1 | `PORTABLE_PROJECT`, `executionRequestHash 0x18f3b6ec…3961` |
| Portable yields exact legacy request | `open.executionRequest == LEGACY` (exact) |
| Unsupported version | `UNSUPPORTED_SCHEMA_VERSION`, no conversion |
| Downgrade without acknowledgement | `INVALID_INPUT` (`LOSSY_CONVERSION_REQUIRES_ACKNOWLEDGEMENT`) |
| Lossy downgrade with `allowLossy` | reports `discardedFields` = tests, noDeclaredTests, evidenceRefs, revision, ancestors, provenance, agentTaskRef + warning |

A successful migration performs no new proof: `validate`/`open` are explicitly
`LOCAL_DATA_INTEGRITY_ONLY`, and `open` recompiles the existing imports but does not
rerun SAT or upgrade freshness.

## 3. Task B — named vectors (B01–B05)

Named vector round trip produced `VECTORS_MATCH` with `PARTIAL_DECLARED_DOMAIN` coverage —
never EQUIVALENT. Duplicate names, empty tests without `noDeclaredTests`, malformed
bitstrings and incompatible widths were all rejected `INVALID_INPUT`. The implementation
also bounds 64 sets / 4,096 rows / 2,000,000 work units and a 5 s dispatch deadline.

## 4. Task C — evidence trust (C01–C05 + E01–E07 with recomputed hashes)

- Substituted digest, false CURRENT provenance, cross-chain change, fabricated artifact
  and changed reproduction context all reject at `validate`/`replay-evidence`.
- With deliberately **recomputed** metadata/revision hashes (so only the semantic attack
  remains): false CURRENT, foreign execution evidence, changed engine identity and
  changed reproduction identity still reject; a checksum-valid fabricated EQUIVALENT
  artifact is rejected on replay.
- **Important design property observed:** `validate` accepts an internally consistent
  package with a substituted evidence digest (E02) or changed engine hash (E04). This is
  intentional and documented — validation proves only local data integrity, never
  evidence existence or equivalence. `replay-evidence` rejects both (E07, E04). No proof
  authority is granted by package validation alone. No URL is fetched and the reproduce
  string is never executed.

## 5. Task D — revision-chain correctness (D01–D10)

Using a genuine 2-ancestor chain (built via `create_package` with two real execution
changes), all attacks rejected `INVALID_INPUT`: missing parent, forged genesis, reordered
ancestors, duplicate sequence, broken link, truncated history, changed before/after hash,
cross-project reuse, disguised rollback, and unsupported future version
(`UNSUPPORTED_SCHEMA_VERSION`). The implementation documents that a valid hash chain
authenticates neither authorship nor a global namespace; no author permission is inferred.

## 6. Task E — web, CLI, API

- Core/CLI/API parity: `validate` produced identical `executionRequestHash` across core,
  `flip portable` and `POST /api/v1/portable`; replay-evidence requires solver opt-in +
  loopback (501 when disabled, 200 when enabled).
- Chromium: **24/25 passed**; both portable journeys (CLI-compatible package/tests/revision
  save/refresh/lossy downgrade; tamper rejection preserving the open project) passed.
  One unrelated inherited debugger-acceptance test failed under full-suite load with a
  5 s expect timeout, but passed when run alone (18 s). Recorded as flaky/host timing, not
  a portable defect; production tests were not modified. Keyboard/narrow-viewport and
  axe checks in the other journeys passed.
- Original 12-case corpus harness: `passed 12 / total 12`. Focused portable tests: 22 passed.
- Schema drift: portable schema export PASS; Python/Node canonical parity 3/3 PASS.
- Custody/credential: PASS, 0 findings (after restoring pinned LF bytes for a Windows
  `core.autocrlf` checkout artifact in previously merged review evidence).

## 7. Task F — resource/security boundaries

Requests over 1 MiB reject `RESOURCE_LIMIT`; authority fields reject `INVALID_INPUT`;
the replay endpoint is loopback/opt-in gated; no wallet/signing/transaction operation
exists; provenance cannot declare CURRENT; invalid encodings are rejected by JSON parsing.
No missing size/count limit was found.

## 8. Findings and limitations

| Severity | Finding |
|---|---|
| CRITICAL / HIGH / MEDIUM | none |
| LOW | Inherited `debugging-acceptance.spec.ts:71` is timing-sensitive: fails with a 5 s expect timeout under full-suite load, passes in isolation. Portable journeys unaffected; no production test changed. |
| INFORMATIONAL | `validate` intentionally accepts internally consistent forged evidence refs (integrity ≠ proof); `replay-evidence` is the trusted boundary and rejects them. |
| INFORMATIONAL | Windows CRLF checkout artifact in previously merged review evidence (environment, not production). |

Full Python suite: **623 passed, 0 failed** (0 skipped). Unlike earlier review branches,
the inherited 120 s scratch-regeneration timeout did not recur in this run; all production
and inherited tests passed.

## 9. Acceptance

**CONDITIONAL PASS** for `136b1115ee0f5ffe0a5583d68c474641fdce1ca1`. Portable 1.1 preserves
legacy bytes/hashes, bounds named tests and revisions, keeps evidence replay behind trusted
recomputation, and rejects all forgery/chain attacks. The only caveat is the low-severity
inherited browser-test flakiness. Do not merge from this review branch.
