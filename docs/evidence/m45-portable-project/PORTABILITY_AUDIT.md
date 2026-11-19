# M4.5-1 — Portable project format audit

**Role:** independent supporting verification engineer (OpenCode / HY4 Flash).
**Tested SHA:** `bba6f3d301b08c0dcbbfd0b363b99a15179414db` (accepted main after PR #7 merge).
**Mode:** read-only production audit plus independent fixtures. No production module,
schema, frontend, CI or Codex branch was modified. No wallet, signing or transaction.

## 1. What a "project" actually is today

There are three distinct artifacts, and the acceptance requirement often conflates them:

| Artifact | Wire shape | What it carries |
|---|---|---|
| v1 `Project` (`1.0.0`) | `project.json` nested field | schemaVersion, projectId, chainId, toolVersion, `sources[]` (alias, identity, manifestHash, nIn/nOut/nState), `candidate` (components + numbered pins + outputs), `comparison` (inputMap/outputMap, intent, trustAssertion), `limits` |
| M3 execution request (`m3-1.0.0`) | the CLI `--project` file; browser "Save project" emits exactly this | all of the above plus `imports[]` (full M2 `ImportResult`: exact netlist bytes, full manifest with block, closure edges, semantics, environment) and `relation` |
| Product evidence bundle (`FLIP_EVIDENCE`, m4 envelope) | `export` output; separate file | comparison report, both source snapshots, engine/tool identities, `chainObservation`, `limitations`, `reproduce` command, `contentHash` |

A `VectorRequest` is a **separate** request kind carrying `vectors[]`; test vectors are
not embedded in the project or execution request. There is no revision ancestry or edit
history field anywhere in the current project format.

This was verified from source (`models.py`, `verification.py`, `workflow.py`) and from
captured artifacts (`results/run/`): the saved project exposes keys
`[imports, kind, project, relation, schemaVersion]`, `vectors` is absent, and the first
import's circuit carries `{identity, netlist}` with a full `{block, dependencies, edges,
root, semantics, ...}` manifest.

## 2. Field-by-field audit

| Required field | Embedded where | Status |
|---|---|---|
| Schema version | v1 `project.schemaVersion`, request `schemaVersion` (`m3-1.0.0`) | **EMBEDDED / reliable** |
| Project identity | `project.projectId`, chainId | **EMBEDDED** |
| Processor/circuit identities | `sources[].identity`, `imports[].circuits[].identity` | **EMBEDDED (full)** |
| Component mappings | `candidate.components[].inputs` (numbered pins), `comparison.inputMap/outputMap` | **EMBEDDED** |
| Import snapshots | `imports[]` with netlist bytes + manifest | **EMBEDDED (exact bytes)** |
| Dependency closure | `imports[].manifest.dependencies/edges` | **EMBEDDED** |
| Test vectors + expected behavior | separate `VectorRequest`; not in project | **GAP — external only** |
| Comparison intent + selected reference | `comparison.intent`, `trustAssertion`, `referenceAlias`/`referenceCandidate` | **EMBEDDED** |
| Verification evidence | separate `FLIP_EVIDENCE` bundle, referenced by `reproduce` string | **GAP — external only** |
| Revision ancestry / edit history | none | **GAP — absent** |
| Hashes to reproduce | `manifestHash`, `netlistHash`, `contentHash` (bundle), request hash | **EMBEDDED across project + bundle** |
| Historical/current freshness | `imports[].integrity.freshness` (HISTORICAL/STALE), bundle chainObservation | **EMBEDDED / preserved** |

## 3. Executed checks

Commands (from `results/executed-cases.json`, 12/12 passed):

```powershell
$env:FLIP_LOCAL_SOLVER=1
.venv\Scripts\flip.exe sample half-adder --out project.json
.venv\Scripts\flip.exe compose --project project.json --out composition.json
.venv\Scripts\flip.exe compare --project project.json --out comparison.json
.venv\Scripts\flip.exe export --project project.json --out evidence.json
.venv\Scripts\flip.exe verify-bundle --project project.json --bundle evidence.json
.venv\Scripts\python.exe fixtures/m45-portable-project/generators/run_portability_cases.py
node fixtures/m45-portable-project/generators/browser_roundtrip.mjs
.venv\Scripts\python.exe fixtures/m45-portable-project/generators/verify_portability.py
```

- **P12 complete historical offline reproduction:** byte-identical 81-byte composition
  `0x3dbb65a6…3ce`, EQUIVALENT comparison, export and replay, all `HISTORICAL`, no live RPC.
- **P01/P02 web↔CLI:** browser "Save project" exports the same M3 execution request;
  `openProject` validates via compose; re-import reproduced EQUIVALENT. Browser
  observation recorded 9 steps, saved schema `m3-1.0.0`, `vectors` absent, no CURRENT claim.
- **P03 edits:** modified output map re-imported and composed successfully.
- **P06/P08/P11** missing dependency, wrong schema version and incompatible toolVersion
  were rejected before build (exit 3).
- **P07/P09/P10** stale chain observation, cross-project evidence and corrupted
  `contentHash` were not promoted/accepted on replay.
- **P04** confirmed vectors are external; **P05** (loopback double with changed beacon
  implementation) is marked STALE and blocked composition — executed against a synthetic
  manifest, not a live chain.

The independent verifier returned `PASS` (manifest, 12 cases, 12 executed, browser
round-trip, no embedded vectors/revision).

## 4. Compatibility risks

- The same file is both "project" (CLI) and "execution request" (web), but the acceptance
  spec treats a "portable project" as a self-contained package with named tests and
  evidence — which is only achieved by shipping **multiple** files today.
- External evidence bundles are referenced by a reproduce *string*, not a cryptographic
  digest embedded in the project; a caller must select the right bundle explicitly.
- No revision ancestry means an edit history cannot be reconstructed from the project.
- Stale imports are preserved, never promoted to CURRENT; this is correct but means a
  saved project is always historical.

## 5. Classification

**PARTIAL.** The current format reliably carries identities, mappings, import snapshots,
dependency closure, intent and freshness, and reproduces results offline. It does **not**
embed named test vectors/expected behavior, verification evidence digests, or revision
ancestry in the portable project unit; these remain external artifacts. See
`SCHEMA_EXTENSION_PROPOSAL.md` for the smallest backward-compatible versioned extension.
