# Canonical contract extracted from accepted baseline

Source references are at baseline `fc9c0c1bcb2557169dd89af0c3b2c5a7628c9adf`. This is a reading guide for fixture authors, not a new schema or validation authority.

## Names, pins and component shapes

| Rule | Exact constraint | Source |
|---|---|---|
| Name | `^[A-Za-z][A-Za-z0-9_-]{0,63}$` | `packages/flip-core/src/flip_core/models.py:14` |
| Pin index | integer `0..65535` | `models.py:11` |
| Pin reference | `component: null` means external; otherwise component instanceId; pin < referenced component width | `models.py:186-189`, `models.py:243-249` |
| NAND | exactly 2 scalar inputs | `models.py:198-201` |
| REF | sourceAlias Name; inputs `0..255` and must equal source `nIn`; `nState` must be 0; circuitId < 2^64 | `models.py:191-195`, `models.py:255-261` |
| Component array | max 5,000; duplicate instanceId rejected; backward references only | `models.py:207-210`, `models.py:250-253` |
| Outputs | 1..65,536; every pin must resolve | `models.py:210`, `models.py:264-265` |
| nIn | 0..65,536 | `models.py:208` |
| Comparison maps | inputMap/outputMap complete bijections over candidate nIn/output count | `models.py:271-276` |
| Local reference design | referenceCandidate must share candidate `nIn` and output count | `composition_models.py:62-68` |
| Strict schema | `extra="forbid"`, `strict=True` | `models.py:59-60` |

## Compiler semantics that must not be reimplemented in JS

- NAND with identical inputs compiles to the canonical inverter `NAND(x, constant-one)`; this preserves audited glue bytes (`composition.py:117-121`).
- REF emits a TAP-02 REF record with processor/circuitId/arity from the validated import (`composition.py:20-29`, `composition.py:123-137`).
- Output signals that are not already final are copied with explicit NAND pairs (`composition.py:141-156`).
- Gate/depth/closure budgets come from `project.limits` and Python; client checks are latency reduction only (`composition.py:105-106`, `composition.py:157-165`).
- Manifest/project/netlist hashes use `flip_core.canonical.content_hash` and the existing `sha` (`composition.py:168-182`).

## V1 display guards (not new canonical limits)

- `nIn ≤ 512`, components `≤ 500`, outputs `1..512`, aliases canonical Name, no duplicate aliases (`apps/web/src/visual/projection.ts:66-79`).
- Pre-allocation counters: 4,096 visible pins and 1,000 connections (`projection.ts:85-95`, `projection.ts:134-136`, `projection.ts:245-249`).
- Pin resolution requires a previously defined component width; forward/self/cyclic references fail (`projection.ts:124-133`).
- REF requires matching import manifest root identity and interface (`projection.ts:174-197`).
- Derived output locators use existing `nIn`, `.kind` or `sources[j].nOut` fields; no invented `.outputs` record (`projection.ts:211-220`).

## Consequence for V2-A fixtures

1. An edit that produces a valid canonical candidate but exceeds the V1 display budget must be REJECTED in the visual editor, not silently truncated or exported.
2. An edit that produces an invalid canonical candidate must never be committed, even if the client pre-check passes.
3. Any output-count change must be accompanied by a complete `outputMap` update; the fixture V2A-11D encodes this explicitly.
4. Hashes are outputs of trusted compose; this package supplies only genuine baseline hashes and exact expected candidate objects.
