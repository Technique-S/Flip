# Editor and learning interface specification

Mode: Operate for composer; Read/Operate for guide. Proposed behavior only; no mock screenshot is evidence. Preserve current `style.css` tokens: white #FFFFFF, ink #17191D, cobalt #0055CC, neutral line #D6D8DC and soft #F6F7F8. Existing Inter/Segoe UI/Arial fallback, 15px base, 1.5 leading remain starting points. Use 4/8px spacing increments, restrained borders, ≥44px primary touch controls, visible focus and no gradient/glow/continuous signal animation.

## Layout within the existing app

```text
Existing workflow navigation (Sources / Composition / Canary / Evidence / Library)
┌ Project ID/name · Unsaved wiring / Unsaved layout · Undo Redo · Visual | Advanced ┐
│ Palette (240) │ Canvas (flex, min 360 at desktop)       │ Inspector (280–320)    │
│ Search       │ Select / Connect / Pan · Zoom / Fit     │ Exact selected pins   │
│ NAND         │ external inputs → NAND / REF → outputs │ Source / dependency   │
│ LATCH status │                                       │ Connection / help     │
│ REF imports  │                                       │                       │
├──────────────┴───────────────────────────────────────┴───────────────────────┤
│ Diagnostics dock: Validation | Simulation | Verification | Evidence             │
└─────────────────────────────────────────────────────────────────────────────────┘
```

This is a schematic specification, not a proposed replacement app shell. Desktop ≥1200px shows rails; 768–1199px defaults one inspector/palette drawer open. At 320/390px show a full-width canvas or equivalent numeric/table panel, one dismissible drawer and a collapsed diagnostics summary. Keep document scrolling available; do not force a 3-panel miniature. At 200%/400% zoom controls reflow, no clipped proof/scope text. Dock resize is bounded, keyboard adjustable and remembers view preference only. No speculative New project wizard or deployment control.

Top project label uses actual projectId with full identity accessible. Distinguish “edited”, “stored in this session” and “downloaded”; browser downloads cannot guarantee filesystem persistence. Visual and wiring dirtiness are independent. Visual/Advanced switch retains draft and selection by stable identity and never compiles/normalizes silently. Simulation/verification/evidence actions reuse existing consent/trust checks and routes, with result summary linked from dock; they may initially navigate to existing pages instead of duplicating them.

Palette searches component names and imported sources. NAND has a recognizable gate outline with inversion bubble **and text**; REF a rectangle with alias, exact identity/trust disclosure and numeric socket counts; LATCH a d/q state symbol and status “inspect only / authoring unsupported” until implemented. Inputs/outputs are project interface controls, not invented circuit primitives/constants. Reuse Library favorites/recents and import flow; catalog label is not verified identity. Empty palette explains actual source import; no fake library entries. Node body can be selected without dragging. Inspector edits validate numeric IDs/counts and show manifest/block/dependency context.

## Tool and input behavior

| Action | Mouse/touch | Keyboard/assistive equivalent |
|---|---|---|
| Select/multiselect | Click/tap, Shift-click, marquee in Select mode | Labeled node/edge list and checkboxes; select all scoped to canvas focus. |
| Place | Drag palette item or select Add then tap position | Palette Add at viewport center, focus inspector; no required spatial gesture. |
| Connect | Drag source socket to compatible destination; tap-source then tap-target alternative | Inspector Source component/output and Destination/input selects + Connect button; announce accepted/rejected result. |
| Reconnect | Select wire then move endpoint, confirm driver replacement | Selected edge inspector changes source; explicit Replace connection command. |
| Pan/zoom | Pan tool/Space-drag, visible zoom±/Fit, pinch supported without swallowing page scroll | Toolbar commands; arrow node movement only when graph focus owns them; browser zoom remains available. |
| Cancel/delete | Escape/cancel active gesture; Delete shows incident-edge preview for destructive edits | Escape returns focus to origin; Delete ignored in text fields; confirm through accessible dialog. |
| Undo/redo | Toolbar | Ctrl/Cmd+Z, Shift+Ctrl/Cmd+Z only in editor scope; preserve native text editing history. |
| Inspect result | Select diagnostic row/edge | Row focus/activate selects target and pans without stealing reading position; “Focus selected item” explicit button. |

Only Select/Connect/Pan persist as modes, visibly labeled. Use `V`/`C`/`H` optionally while canvas has focus, not globally in typing contexts; shortcuts are proposed and documented through Help. No proprietary shortcut list copied. Escape cancels pointer capture, connect mode or selection in that order. Handle pointercancel/lost capture/window blur without committing a half edit. Panning does not mark wiring dirty.

Wires default left→right with source direction cue and modest orthogonal/stepped bends. Crossing is visibly non-junction; branching is repeated source fan-out, not an implicit bus. Hover alone is insufficient; focus/selection exposes numeric endpoints. Cobalt indicates selection, not logical one or verified correctness. Invalid draft uses icon + dashed line + message; witness relevance uses a distinct heavier/patterned overlay + text. High contrast/forced colors must preserve shape/line distinctions. Selection and diagnosis can coexist without erasing one another.

## State and diagnostic contract

Empty/opening/ready-invalid-draft/validating/ready-valid/running/UNKNOWN/DIFFERENT/EQUIVALENT are separate states, with preserved last valid project and exact response identity. Disabled actions say why. Render and RPC failures offer retry without reset. Changing wiring invalidates result authority immediately; previous proof may remain in history labeled for its old request, never as current status.

Dock Validation lists exact target, rule and recovery. Simulation shows actual vector inputs/expected/observed output bits and coverage; no free-running simulation/tick UI until backend support exists. Verification shows reference/relation, freshness, engine/limits, witness replay and result. Evidence offers actual project/artifact save and independent replay, not a screenshot export mistaken for proof.

Visual Canary flow: explicitly select baseline/reference → snapshot original → choose reversible mapping mutation → preview before/after → validate/commit → run actual comparison → inspect real witness and bound relevant paths → restore original → run new comparison → export/replay actual evidence. A reliable candidate correction remains a separate verified/apply action; do not generalize arbitrary mutation into automatic repair. Show ambiguous attribution and historical scope inline. If current API only returns terminal output bits, internal selected-wire values read “not observed”; no implied live signal state.

## P8: actual UI integration

Implement dedicated User Guide entry and two paths; retain the authoritative [seven-module curriculum and actual control map](../pre-m5/P8_CURRICULUM.md). Experienced cards cover navigation, open, discovery/import, Visual/Advanced/pins, actual vectors, comparison/debug, export/replay and the accurate optional-deployment boundary. Beginner modules remain: ecosystem; components; first project; visual wiring; simulation/debugging; verification/evidence; complete guided project. Do not replace these with generic tooltips.

UX-01 uses one versioned term catalog for processor, REF, NAND, LATCH, SAT, netlist, pin, dependency, counterexample and evidence, plus width/order/freshness/reference. Labeled Help buttons open concise explanations next to relevant controls with keyboard/touch/Escape/focus return. Essential trust/UNKNOWN explanations stay inline.

UX-02 uses stable `data-guide-anchor` IDs for actual controls and predicate-bound events, not translated labels/pixel coordinates. Proposed anchors: `project.openSample`, `composition.viewToggle`, `palette.addNand`, `inspector.connect`, `composition.build`, `canary.run`, `debug.inspect`, `debug.restore`, `evidence.export`, `evidence.replay`. These are future attributes, not claims they exist today. Next/Back/Exit always available. Back changes lesson position, not project state. Missing/ambiguous/unmounted target pauses safely; no guessed click or auto permission/trust. Step completion requires matching actual operation result/revision; click, HTTP 200, checksum or filename alone is insufficient. Invalid/UNKNOWN goes to recovery, not success.

Keep versioned progress ≤64 KiB in separate local learning storage; quota/corrupt/blocked storage gets notice and session fallback. Restore step only after checking actual project/revision. No progress record restores proof, CURRENT or correction authority. Guide is a nonmodal docked panel during real actions, with explicit focus-target action and no trap/occluded errors. Screenshots are captured from exact implemented SHA, viewport and project identity; annotate actual controls only.

UX-03 requires nine non-destructive lessons: invalid address; missing ID; incompatible pins; wrong output map; RPC failure; timeout/UNKNOWN; stale evidence; malformed file; unsaved work/recovery. Each explains failure/cause/protection/recovery/prevention. Use learner copies and controlled fixture failures, not live service sabotage or global RPC setting changes. Unsupported lesson action stays unavailable/clearly recorded until a real isolated exercise exists. Do not auto reset a user's work.

Capstone emits a real saved project/visual layout, named vectors, faulty/original wiring, independently replayed DIFFERENT witness, bound diagnosis/correction, final comparison and evidence artifact replayed against independently selected project through CLI. Completion observes matching event/artifact IDs. Retain failed/abandoned sessions; no simulated learner success or publication.

Human acceptance requires at least one novice and one experienced circuit developer plus actual screen-reader use. Record hardware/software/tasks, assistance, confusion, errors, outcomes, artifact hashes and ensuing fixes. Automated axe, screenshots and this plan cannot replace those sessions. No humans were tested in this checkpoint.
