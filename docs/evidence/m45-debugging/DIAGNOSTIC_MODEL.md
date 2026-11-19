# M4.5-2D — Connection-level diagnostic model

**Status:** independent fixture design and evidence; no production diagnostic is implemented.
**Baseline:** accepted M4 main `09f2482beae84be6d919ecd6957c4153d1924cca`.
**Branch:** `opencode/flip-m45-debugging-fixtures`.
**Companions:** `ACCEPTANCE_MATRIX.md`, `HANDOFF.md`,
`fixtures/m45-debugging/cases/debugging-corpus.json`.

Classification used here:

- **SOURCE OBSERVED** — read from an accepted source/evidence file.
- **EXECUTED FIXTURE CHECK** — computed and verified by the independent generator/verifier.
- **SPECIFICATION ONLY** — a rule or UX expectation for future production support.

## 1. Intent and boundary

The pre-M5 gap audit records the exact missing behavior: no traced signal cone, no
ranked implicated connections, no reusable per-connection diagnostic artifact and no
general repair workflow; the existing "Restore original" action is a fixed sample action,
not a diagnosis engine. It also requires that a cone be labeled as *relevant computation*
rather than proof of a unique faulty edge, and that candidate repairs be applied
deliberately and rechecked with the trusted comparator. [SOURCE OBSERVED]

This model adds a deterministic, bounded tracer and a conservative attribution language.
It does not change verdicts, schemas, netlist bytes, permissions or any transaction path.
No language model is used as a proof or fault oracle.

## 2. Connection model

A TAP-02 netlist is decoded into elements with stable numbered pins. Signal `0`/`1` are
constants, inputs occupy `2..nIn+1`, and each element emits outputs from `first_out`.
A REF element resolves to a sub-circuit through a declared `(processor, circuitId)`
identity. A connection is therefore:

```
connectionRef = <componentPath>/element[<index>].in[<pin>]
sourceSignal  = <signal number in that component scope>
sourceDescription = const0 | const1 | input[i] | NAND[k].out[j] | REF[k].out[j]
```

`componentPath` is stable across edits (`top`, then `top/ref[<index>]`, and so on for
nested REFs). This is the traceability bridge from a displayed diagnostic to a concrete
netlist connection and to the identity whose `netlistSha256` is recorded.

## 3. Signal-cone trace algorithm (Task B)

Given the output-map pins selected for each differing output bit:

1. Resolve the emitting element by signal number; record its path, `elementIndex` and
   `outputPin`.
2. Record every input pin as a connection with its source signal and description.
3. Recurse on non-constant sources; stop at `const0`, `const1` or a top-level input.
4. For a REF element, descend into the resolved sub-circuit with a path-qualified prefix
   (this is what makes nested-REF diagnostics traceable).
5. Stop at `nodeCap`; a truncated cone yields `UNKNOWN_NO_ATTRIBUTION`, never a ranking.

The tracer output is ordered by `(path, elementIndex, inputPin)` and carries `nodesVisited`,
`nodeCap` and `truncated`. It is computed by two independent evaluators (recursive and
flattened) for every authored truth table; disagreement aborts generation.
[EXECUTED FIXTURE CHECK]

## 4. Attribution rules

| Class | When used | What it permits |
|---|---|---|
| `PROVEN_BEHAVIORAL_DIFFERENCE` | A witness replays under both evaluators with recorded reference/candidate outputs | State which output bits differ under that input; nothing about cause |
| `RELEVANT_COMPUTATION` | Any cone member, including EQUIVALENT designs | Display connections as computation relevant to an output |
| `SUSPECTED_CANDIDATE` | A declared prior mapping/edit set exists and the connection lies in the differing cone | Offer an unconfirmed candidate; never call it wrong |
| `AMBIGUOUS_MULTIPLE_CAUSES` | More than one candidate connection, or several single-edge edits give the same behavior | Say the exact defective connection cannot be identified |
| `NO_FAULT_ATTRIBUTION` | Exhaustive EQUIVALENT result | Explicitly attribute nothing; suppress all suspect highlighting |
| `UNKNOWN_NO_ATTRIBUTION` | Timeouts, truncation, missing/stale closure, invalid input | No verdict, no suspect, no correction claim |
| `STRUCTURAL_REJECTION_NO_ATTRIBUTION` | Forward/unbound pin, arity failure, other structural rejection | Explain the rejection only |

Hard rules:

- A witness proves a difference **relative to the selected reference**. The reference's
  status as *expected behavior* depends on the user's declared intent; without a declared
  oracle the result is behavioral diff only. [SOURCE OBSERVED: M3 schema README]
- A connection is never labeled "wrong" on cone membership alone.
- Aliases such as `xor`, `sum`, `carry` or user labels are never an intent oracle.
- Exactly one candidate under a declared prior mapping is still a candidate, not a proven
  fault; applying it requires user action and a fresh full comparison.
- Diagnostics cannot weaken `EQUIVALENT`/`DIFFERENT`/`UNKNOWN` semantics or grant authority.

## 5. Worked cases

| Case | Coverage | Diagnostic result |
|---|---|---|
| D01 | Swapped outputs | Both output-map pins in cone; `AMBIGUOUS_MULTIPLE_CAUSES` |
| D02 | Incorrect REF input mapping | Both REF input pins implicated; asymmetric F makes the swap observable |
| D03 | Duplicate fan-out | One candidate pin under a declared prior mapping; `SUSPECTED_CANDIDATE` |
| D04 | Unbound pin 99 | Structural rejection; no cone and no attribution |
| D05 | Three-output rotation | Multiple output-map candidates |
| D06 | Multiple simultaneous edits | Candidates span REF inputs and output map; ambiguous |
| D07 | Nested REF (top → wrapper → F) | Cone crosses REF boundary with path-qualified connections |
| D08 | Commutative rewiring | EQUIVALENT, zero suspects — no false attribution |
| D09 | Several contributing connections | Only connections in the differing cone are shown; others are not attributed |
| D10 | Indistinguishable causes | Two distinct single-edge mutations yield the same wrong truth table; no unique cause |

D10 is not hand-asserted: `build_corpus.py` searches a fixed ordered mutation space and
selects the first equivalence class containing at least two distinct element connections.
The verifier re-evaluates every alternative and confirms the identical wrong table.
[EXECUTED FIXTURE CHECK]

## 6. Correction guidance (Task C)

Each of the eight guidance items carries exactly one of three classifications:

- `VERIFIED_CORRECTION` — restoring the declared prior mapping was re-compared in the
  fixture and restored EQUIVALENT (D02, D03). Scope: the declared synthetic reference only.
- `CANDIDATE_DIAGNOSTIC_ACTION` — inspect the output map, replay the witness, or rerun a
  full comparison after edits. No fault is asserted and nothing is changed by the suggestion.
- `EXPLANATION_ONLY` — unbound-pin rejection, equivalent rewiring, and indistinguishable
  causes. No action or repair claim.

Guidance is advisory text. No item may set a target, function, value, permission or
approval. There is no LLM oracle field in any fixture (`llmOracle: NONE`).

## 7. UX and structured output (Task D)

The UX expectation fixture pins these fields to existing Flip conventions (M3 schema and
M4 browser evidence): highlighted source→destination pin pairs, witness inputs as LSB0
BitVectors, mapped reference/candidate outputs, zero-based differing output bits,
confidence/scope labels from the class list above (never probabilities), path-qualified
traceability to `netlistSha256`, text labels accompanying every highlight, non-color double
underlines for differing bits, plain-text announcements, and CLI JSON with stable exit
codes where `1` means DIFFERENT but never "the connection was proven defective".
[SPECIFICATION ONLY for production rendering]

## 8. Limitations

- The independent evaluator is a stdlib reference, not the production solver; production
  replay and equivalence must be re-run through the trusted engine.
- All circuits and identities are synthetic. No live RPC, deployment or publication.
- Large cones are bounded by `nodeCap`; truncation is UNKNOWN, not a ranking.
- Greedy/heuristic witness reduction in the production engine is not globally minimal; this
  corpus uses first-difference exhaustive witnesses, not minimal-cause claims.
- Human usability with an unfamiliar mutation remains unexecuted.

## 9. Reproduction

```powershell
python fixtures/m45-debugging/generators/build_corpus.py
python fixtures/m45-debugging/generators/verify_corpus.py
```

See `ACCEPTANCE_MATRIX.md` for the executed check list and the specification-only items.
