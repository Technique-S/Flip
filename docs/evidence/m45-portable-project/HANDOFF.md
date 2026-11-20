# M4.5-1 — Portable project evidence handoff

**Tested SHA:** `bba6f3d301b08c0dcbbfd0b363b99a15179414db` (accepted main after PR #7 merge).
**Branch:** `opencode/flip-m45-portable-project-evidence` (from that main; not merged).
**Final commit SHA:** reported in the completion response.

## Scope

Read-only audit plus independent fixtures. Wrote only under
`docs/evidence/m45-portable-project/` and `fixtures/m45-portable-project/`. No production
package, schema, frontend, CI, dependency lock, archived evidence or Codex branch was
edited. No wallet, signing, transaction or live chain observation.

## Deliverables

- `PORTABILITY_AUDIT.md` — field-by-field audit and executed checks.
- `ACCEPTANCE_MATRIX.md` — 12 cases and required-field coverage.
- `SCHEMA_EXTENSION_PROPOSAL.md` — backward-compatible `flip-portable-project-1.1.0` wrap extension.
- `cases/portability-cases.json`, `requests/*.json`, `results/executed-cases.json`,
  `results/browser-roundtrip.json`, `MANIFEST.json`.
- `fixtures/m45-portable-project/generators/*.py` and `browser_roundtrip.mjs`.

## Counts and results

- 12 portability cases, **12/12 executed and passed**.
- Browser round-trip: 9 recorded steps; saved schema `m3-1.0.0`, vectors absent,
  reimport EQUIVALENT, no CURRENT claim.
- Independent verifier: `PASS` (manifest, cases, executed, browser, no embedded
  vectors/revision).
- Classification: **PARTIAL** against the complete pre-M5 portable-project specification.

## Reproduction

```powershell
python fixtures/m45-portable-project/generators/build_portability_fixtures.py
.venv\Scripts\python.exe fixtures/m45-portable-project/generators/run_portability_cases.py
node fixtures/m45-portable-project/generators/browser_roundtrip.mjs
.venv\Scripts\python.exe fixtures/m45-portable-project/generators/verify_portability.py
```

Build the frontend (`npm ci`, `npm run build` in `apps/web`) before the browser script.

## Key finding

The current "project" (an M3 execution request) reliably embeds identities, mappings,
import snapshots, dependency closure, intent, hashes and HISTORICAL/STALE freshness, and
reproduces offline byte-identically. It does **not** embed named test vectors/expected
behavior, verification evidence digests or revision ancestry — those are separate
artifacts (VectorRequest, FLIP_EVIDENCE bundle) or absent. The proposed 1.1 wrap extension
adds them by content-addressed reference without altering any frozen schema or hash.
