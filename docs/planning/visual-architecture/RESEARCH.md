# Independent interaction and technology research

Consulted 2026-11-23. This is primary-document/registry research, not hands-on competitor usability testing. Observations are separated from Flip design inferences. No source, icon, screenshot or proprietary example code was copied. A feature being documented does not establish accessibility, speed or suitability in Flip.

## Competitor interaction matrix

| Reference / observed behavior | Adopt for Flip (design inference) | Deliberately avoid |
|---|---|---|
| [CircuitVerse key features](https://docs.circuitverse.org/chapter1/chapter1-keyfeatures/): drag/drop editor, configurable component properties, multibit interfaces, reusable nested subcircuits and timing diagrams | Searchable circuit palette; numeric input/output affordances; REF reuse with explicit hierarchy | Its simulation engine, buses, cloud/collaboration model and timing behavior are not Flip semantics. No colored live signal without an actual engine observation. |
| [CircuitVerse canvas](https://docs.circuitverse.org/chapter3/chapter3-canvas/): component placement and properties panel, rearrangement and subcircuit organization | A quiet canvas plus selected-item inspector; reveal child structure separately | Do not make free rotation or visual proximity change pin meaning. Deep REF content stays bounded and read-only initially. |
| [Logisim-evolution toolbar](https://mbaillif.github.io/Logisim-evolution-documentation/en/html/guide/gui/gui-toolsbar.html): separate poke/select/wire tools, shortcuts, simulation controls and single-step/tick actions | Explicit Select/Connect/Pan mode, visible active tool, Escape cancellation and shortcut help; keep editing and observed results distinguishable | Poke/tick/live simulation cannot be promised by current stateless UI. Do not copy desktop Ctrl-number shortcuts that conflict with browser tabs. |
| [KiCad schematic editor](https://docs.kicad.org/master/en/eeschema/eeschema.html#_net_highlighting): net highlighting with navigator; [ERC](https://docs.kicad.org/master/en/eeschema/eeschema.html#_electrical_rules_checking) separates connection errors/warnings | Diagnostic list selects relevant wire/pin and pans into view; explicit unbound/incompatible connection findings; hierarchy breadcrumbs | Electrical power/drive/ERC rules are not canonical Flip rules. Geometric crossings never imply electrical joins. Structural validity never proves behavioral equivalence. |
| [FigJam connectors](https://help.figma.com/hc/en-us/articles/1500004414542-Create-diagrams-and-flows-with-connectors-in-FigJam): bent/curved/straight connectors, endpoints move with attached objects, explicit connector mode and Escape exit | Retained socket attachment, obvious connector mode, reconnect handles, limited contextual tools | Shape-level attachment and arbitrary strokes cannot become executable pin connections. No auto-connect-on-nearby-node. |
| [FigJam navigation](https://help.figma.com/hc/en-us/articles/1500004414582-Pan-and-zoom-in-FigJam), [selection](https://help.figma.com/hc/en-us/articles/1500004292221-Select-move-and-order-objects-in-FigJam), [keyboard guidance](https://help.figma.com/hc/en-us/articles/360040328653-Use-Figma-products-with-a-keyboard) | Fit/zoom percentage, discoverable pan, multiselection and documented keyboard equivalents; inspector reachable outside canvas | Do not infer full assistive-technology conformance from these docs or copy proprietary UI. No keyboard command depends on undiscoverable hover. |

KiCad source is a moving **master/nightly** manual (observed 10.99, doc revision `37fef10f`), not evidence about a pinned stable release. CircuitVerse observations above are digital-logic concepts, not protocol interoperability claims. Flip's distinguishing layer is replayed reference-relative evidence and identity-bound correction, not drawing alone.

## React Flow engineering findings

The [core](https://reactflow.dev/) supplies a node UI toolkit. [Unique custom handles](https://reactflow.dev/learn/customization/handles) allow `sourceHandle`/`targetHandle` mapping to numeric pin IDs. [Controlled state](https://reactflow.dev/learn/advanced-use/state-management) can project canonical state, but a graph store must not become a second executable model. [Connection validation](https://reactflow.dev/examples/interaction/validation) offers `isValidConnection`; this is feedback only, never a trusted validation boundary.

[Accessibility documentation](https://reactflow.dev/learn/advanced-use/accessibility) describes node/edge focus, selection, movement, ARIA instructions and focus panning. It does not demonstrate a complete keyboard circuit-wiring workflow for Flip; an inspector/table connect form is required. [Performance guidance](https://reactflow.dev/learn/advanced-use/performance) recommends narrow subscriptions and stable/memoized components/callbacks. Large port counts and edge overlays still require Flip benchmarks.

The [auto-layout example](https://reactflow.dev/examples/layout/auto-layout) and [undo/redo example](https://reactflow.dev/examples/interaction/undo-redo) are **Pro examples**. Do not copy their hooks. Core [MIT licensing](https://github.com/xyflow/xyflow/blob/main/LICENSE) does not license that paid source. Implement a small Flip-owned command log; start with deterministic columns/manual layout. An optional later layout engine requires its own exact package/notice review and layout-only history command.

## Registry observations (no installation)

Commands: `npm view @xyflow/react version peerDependencies license engines --json`; `npm view rete version license --json`; `npm view rete-react-plugin version peerDependencies license --json`.

| Package observed | License / declared compatibility | Interpretation |
|---|---|---|
| `@xyflow/react@13.0.2` | MIT, React/react-dom/types >=18, Node >=20 | Declared ranges include Flip React 19.3.1/Node 24.18.0. TypeScript 7/esbuild 0.28.2, Strict Mode, CSS and runtime behavior NOT TESTED with this package. Freeze exact tested version during V1, not a moving latest tag. |
| `rete@2.0.6` | MIT | Engine/editor ecosystem is feasible, but Flip must not enable a new dataflow/control-flow evaluator. |
| `rete-react-plugin@2.1.2` | MIT; React 16.8.6/17/18/19 ranges; rete ^2.0.1, area/render-utils plugins and styled-components 5/6 peers | More integration dependencies than current React-only runtime. Peer metadata is not a working build. |

Primary registry is accessed by npm; raw observations and exact toolchain checksums are in evidence/baseline.json. [Rete validation](https://retejs.org/docs/guides/validation/), [history](https://retejs.org/docs/guides/undo-redo/) and [React renderer](https://retejs.org/docs/guides/renderers/react/) make it a credible alternative. [Rete licensing](https://retejs.org/docs/licensing/) explicitly distinguishes mostly MIT packages from CC-BY-NC-SA-4.0 advanced `rete-structures`/`rete-scopes-plugin`; do not blanket-assume the whole ecosystem is MIT.

## Explicit decision matrix

Scores are engineering judgments, **not measurements**: 1 poor/high work, 3 feasible/moderate work, 5 strong/low work. No numerical score asserts UX acceptance. Equal-weight sums are only a compact comparison; one-engine/license/keyboard constraints are hard vetoes.

| Criterion | React Flow | Rete editor/React | Custom SVG |
|---|---:|---:|---:|
| Circuit sockets/symbol flexibility | 4 | 5 | 4 |
| Integration with present React/toolchain | 5 | 3 | 3 |
| Beginner discoverability with custom inspector | 4 | 4 | 3 |
| Advanced edit efficiency | 4 | 4 | 3 |
| Accessibility foundations / remaining burden | 4 | 3 | 2 |
| Expected performance / bounded rendering control | 4 | 4 | 3 |
| Maintenance/dependency risk | 4 | 3 | 2 |
| License clarity for required minimal packages | 5 | 3 | 5 |
| Renderer-neutral portability | 4 | 4 | 5 |
| Fit with restrained Flip visual identity | 5 | 4 | 5 |
| Sum / 50 | 43 | 37 | 35 |

Select React Flow provisionally, contingent on V1 compatibility, licensing and accessibility tests. Retain Rete as fallback if React Flow fails measured requirements; do not add both. Custom SVG offers maximum drawing control but transfers the interaction/accessibility maintenance burden to Flip. A large-network renderer such as Cytoscape may suit later read-only dependency exploration, but is not selected for the editable socket UX.

## Rights and reuse boundaries

CircuitVerse's [source license](https://github.com/CircuitVerse/CircuitVerse/blob/master/LICENSE) is MIT; [Logisim-evolution](https://github.com/logisim-evolution/logisim-evolution/blob/main/README.md#license) declares GPLv3. KiCad's manual states its own GPLv3+/CC-BY-3.0+ terms; documentation licensing is distinct from application/plugin code. These references are studied as interaction patterns only. Figma materials remain proprietary; no icons/screenshots/code extraction. No competitor code is necessary for this plan.

Review licenses/notices of exact graph/transitive/layout packages before adding locks. Flip owner/source/content-rights decisions remain outstanding from release review; an MIT graph library does not clear Flip distribution rights. No license is chosen by this branch.
