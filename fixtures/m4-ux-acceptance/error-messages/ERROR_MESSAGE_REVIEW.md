# Product error-message review — M4-B

Machine source: [`error-catalog.json`](error-catalog.json). This is a **UX
review artefact**, not production copy shipped by this branch. It is grounded in
the frozen error envelope (`docs/schema/1.0.0/error-envelope.schema.json`), the
CLI exit contract (`docs/schema/CLI_EXIT_CODES.md`), the M3 interface README and
the executed cases in `../cli-cases/CLI_ACCEPTANCE.md`.

## Review rules applied

1. **Lead with the situation, not the code.** The title and first sentence answer
   "what happened?" in ordinary language. The code is never the headline.
2. **Keep the code, but put it in `<details>`.** Each catalogue entry has a
   `technicalDetails` object intended for a collapsed "Technical details"
   disclosure containing code, exit class, detection boundary and executed case
   IDs. Automation keeps the machine-readable envelope; people read prose.
3. **Say what the message does not mean.** This is the main guard against
   overclaiming. It is mandatory for all 12 entries.
4. **Give one safe next action.** No dead ends, no "contact support" without an
   alternative, and no action that would broadcast a transaction.
5. **Do not moralise about a DIFFERENT result.** "The two circuits behave
   differently" replaces "your circuit is wrong", "bug detected", "verification
   failed" or "regression confirmed".
6. **Timeout = UNKNOWN.** E06 and E07 never use the words equal, equivalent or
   passed, and they explicitly state that no verdict was reached.
7. **Separate trust axes.** Stale/IMPLEMENTATION_CHANGED (E04/E05) describe
   evidence freshness; DIFFERENT (E09) describes behaviour; pre-flight statuses
   (E11/E12) describe publication structure. None is an alias for another.

## Wording substitutions

| Avoid | Use instead | Why |
| --- | --- | --- |
| "Verification failed" for DIFFERENT | "The two circuits behave differently on this input" | A difference is a finding, not a tool failure or a verdict on the user |
| "Circuit is broken / bug found" | " behaviours differ; intended behaviour is unknown without a trusted oracle" | No intent oracle was established |
| "Timeout — circuits are equivalent" | "Inconclusive — solver timed out (UNKNOWN)" | A timeout can never produce EQUIVALENT |
| "Published / deployment successful" for STRUCTURALLY ACCEPTED | "Structural checks passed to the burn stage; nothing was broadcast or paid" | Structural acceptance is not publication |
| "Chain error" for WRONG_CHAIN | "This circuit is on the wrong network" | Names the actual mismatch and the supported chain |
| "Invalid circuit" for MISSING_REFERENCE | "That circuit ID could not be found" | Distinguishes absence from malformation |
| "Proof verified / formally correct" for EQUIVALENT | "No difference found under the pinned stateless semantics and mapping" | Bounds the claim to the model and mapping |
| "Fresh" for a cached result with `CURRENT` flag set | "HISTORICAL — cached inputs cannot be promoted by a flag" | Freshness is an observation, not a caller assertion |

## Acceptance checks for Codex integration

- [ ] Every error title and first sentence in the catalogue appears verbatim or
      meaning-equivalent in the UI for the matching envelope code.
- [ ] Each rendered error has a collapsed "Technical details" disclosure; the
      code is not the only visible text.
- [ ] E09 never appears with wording that assigns fault or correctness.
- [ ] E06/E07 render the verdict text `UNKNOWN` and never the `EQUIVALENT` badge.
- [ ] E11/E12 render pre-flight status in its own labelled region, separate from
      the comparison verdict, with "no transaction was broadcast" visible.
- [ ] Errors are announced to assistive technology and associated with the
      control or result region that caused them (see
      `../browser/ACCESSIBILITY_ACCEPTANCE_PLAN.md`, B02/B08/B11).
- [ ] Machine envelopes remain unchanged: the plain-language layer must not
      replace or rewrite `error.code`.

## Provenance note

The technical codes and exit classes are observed facts from the pinned
baseline. The plain-language sentences are proposed product copy requiring
Codex/product review; they are not claims that an M4 UI already renders them.
No pre-flight error was executed on the baseline — E11/E12 are specifications.
