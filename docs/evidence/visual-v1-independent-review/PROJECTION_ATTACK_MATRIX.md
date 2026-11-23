# Projection attack matrix — independent

Target: `apps/web/src/visual/projection.ts` at PR head `006050d7b8349dca3c263da2e3f1112617706541`, adapter `flip-visual-adapter-1.0.0`.
Harness: `projection-attack-harness.mjs`; bundled target: `projection.bundle.mjs` (esbuild, Node platform); raw results: `projection-attack-results.json`.
All mutations are applied to in-memory deep clones of `docs/schema/m3/examples/half-adder.request.json`. Each case re-serialises the input before and after to prove the projection does not mutate it.

**Result: 54 cases, 54 expected outcomes, 0 failures, 0 input mutations.**

## Accepted cases (legitimate structures)

| ID | Expected | Observed | What it proves |
|---|---|---|---|
| baseline-real-sample | ACCEPT | ACCEPT | 5 nodes, 8 edges, unique edge IDs, every edge endpoint resolves to a real rendered handle, adapter version correct |
| empty-components-with-external-output | ACCEPT | ACCEPT | Empty component list with a direct external→output mapping is a valid 2-node graph |
| zero-inputs | ACCEPT | ACCEPT | `nIn=0` REF with zero inputs and one output renders without phantom input handles |
| processor-uppercase-valid | ACCEPT | ACCEPT | Case-insensitive `0x` processor regex, with manifest identity kept in exact agreement |
| circuit-id-2^64-minus-1 | ACCEPT | ACCEPT | Largest valid uint64 decimal string preserved verbatim |
| uint53-plus-one-preserved | ACCEPT | ACCEPT | `9007199254740993` survives as string (no Number conversion) |
| empty-source-alias-malformed | ACCEPT | ACCEPT | **Observation:** alias syntax is not validated; see PROJ-01 |
| xss-alias-displayed-as-text | ACCEPT | ACCEPT | `<script>` alias is retained as plain string data; React escapes it in the UI (no HTML injection in projection) |
| source-and-identity-are-detached-copies | ACCEPT | ACCEPT | Displayed `source` and `identity` are not the same objects as canonical ones; mutating them leaves the request byte-identical |
| derived-locators-resolve-existing-fields | ACCEPT | ACCEPT | Every `#out:n` locator resolves to an existing `nIn`, `.kind` or `sources[j].nOut` field |
| pin-mappings-are-copies | ACCEPT | ACCEPT | Port `mapping` is a copy, not the canonical Pin object |

## Rejected cases (fail closed, zero partial graph)

Each case produced a `Visual view unavailable: … Use Advanced…` error. None produced nodes or edges.

| Category | Cases |
|---|---|
| Structural | `empty-components-no-outputs`, `null-top-level`, `imports-not-array`, `sources-not-array`, `components-over-500` |
| Component identity | `duplicate-component-id`, `instance-id-with-slash`, `instance-id-65-chars`, `instance-id-leading-digit` |
| Arity / kind | `nand-one-input`, `nand-three-inputs`, `unsupported-kind-LATCH`, `unsupported-kind-lowercase` |
| Pin indices | `pin-out-of-range`, `pin-negative`, `pin-fractional`, `pin-string-zero`, `pin-nan`, `pin-infinity`, `missing-input-pin` |
| References | `forward-reference`, `self-reference`, `unknown-component-reference` |
| Bounds | `nIn-above-512`, `nIn-negative`, `nIn-fractional` |
| Source identity / state | `stateful-source-nState-1`, `stateful-manifest-root`, `wrong-chain`, `source-chain-mismatch`, `source-schema-mismatch`, `processor-malformed`, `circuit-id-leading-zero`, `circuit-id-hex`, `circuit-id-2^64`, `circuit-id-21-digits`, `manifest-root-mismatch`, `manifest-nIn-mismatch`, `duplicate-source-alias`, `missing-source-alias`, `numeric-source-alias` |
| Display strings | `html-instance-id-rejected`, `unicode-instance-id-rejected` |

## Identity and aliasing analysis

- **Edge-ID aliasing:** IDs are `<target>/in/<i>`. Component targets are `candidate/component/<instanceId>` where `name()` allows only `[A-Za-z][A-Za-z0-9_-]{0,63}` — no `/`, no leading digit, max 64 chars. The reserved bank IDs are `candidate/external` and `candidate/outputs`, which cannot equal any `candidate/component/…` string. Within a target, `i` is unique. Verified by the baseline case's `new Set(ids).size === ids.length`.
- **Handle aliasing:** source handles are `out:<p.pin>`; the source node's outputs are generated as `out:0…out:(width-1)`, and `pin()` enforces `p.pin < width`. Target handles are `in:<i>` with `i < inputs.length`. Every rendered edge endpoint therefore resolves.
- **Locator integrity:** input port locators are `project.candidate.components[i].inputs[j]` or `project.candidate.outputs[j]`. Output port locators are `project.candidate.nIn#out:j`, `project.candidate.components[i].kind#out:j` or `project.sources[k].nOut#out:j`. The harness resolves the pre-`#` path against the canonical object; all resolved to defined values.
- **Import binding:** `r.imports.find(entry => entry.manifestHash === s.manifestHash)` must yield a root whose processor, circuitId, chainId, nIn, nOut and nState agree with the REF source. Import and processor identities are read-only inputs; they are never rewritten.
- **Position determinism:** `x = level*330`, `y` accumulated from `Math.max(inputs.length, outputs.length, 1)` per row. No random or environment input. The projection never writes back to the request (all 54 cases verified byte-identical input).

## Residual observations

- **PROJ-01 (LOW):** source `alias` is only de-duplicated via a Map; no format/length validation. An empty alias (`""`) and a `<script>` alias were accepted. The UI renders it as React text, so there is no injection, but the architecture's "strict length/encoding" identity hygiene is not fully enforced for aliases.
- **PROJ-02 (LOW):** the aggregate edge/pin budget is checked at `projection.ts:235-239` after `ports()` and `connections()` have materialised objects. Because components are capped at 500 and REF `nIn`/`nOut` at 255, the worst case before rejection is on the order of 1.3×10^5 objects — bounded, but earlier counting would be cheaper.
- **Not covered:** no genuine decoded REF internals or LATCH structure exists in the accepted request transport; V1 explicitly defers those. This review does not treat that deferral as a defect.
- **Not a benchmark:** these are correctness/robustness cases. The 100/200 and 500/1,000 node performance gates are V7 work and were not run.
