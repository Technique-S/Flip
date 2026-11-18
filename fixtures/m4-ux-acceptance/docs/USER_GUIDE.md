# Flip — bounded user guide (M4-B draft)

This is a documentation fixture for Codex/product review. It describes the
**supported stateless workflow** and its limits. It does not describe features
that are not implemented in the accepted M3 baseline.

## 1. What Flip does

Flip imports genuine X Layer circuit identities using read-only calls, resolves
their `REF` dependencies into a bounded integrity manifest, composes a small
number of components with explicit numeric pin connections, compares two
stateless circuits under pinned TAP-02 semantics, explains differences with a
counterexample that is replayed independently, and exports reproducible
evidence. Its optional structural pre-flight is read-only.

The product promise is: **change the wiring, verify the behaviour, share the
evidence** — within the narrow scope below.

## 2. When to use Flip

Use Flip when you have X Layer mainnet (`chainId = 196`) circuit identities and
you want to know whether a stateless rewiring or refactor changed observable
behaviour relative to something you already have: a previous version, a trusted
reference circuit, or your own expected vectors.

It is useful for checking pin swaps and duplicate connections, confirming that
a symmetric rewrite preserves behaviour, producing a concrete failing input for
a regression, and packaging the result so someone else can reproduce it
offline.

Do not use Flip for general circuit drawing, HDL/Verilog compilation, testnet
work, unbounded sequential equivalence, wallet operations or publishing.

## 3. What EQUIVALENT means

`EQUIVALENT` means that, under the declared stateless TAP-02 semantics, bit
ordering, pin mapping and dependency versions, no input in the modelled domain
produces different outputs between the two compared circuits. The SAT solver
returned UNSAT within the published resource limits.

It is **pairwise behavioural equivalence under a model**. It does not mean
either circuit is correct, secure, safe to publish, or equivalent to a real-world
intention. When no trusted oracle was declared, the UI must read "same
behaviour; intended correctness unknown".

## 4. What DIFFERENT means

`DIFFERENT` means Flip found at least one input where the outputs differ, and an
independent evaluator replayed that input on both circuits and confirmed the
different outputs before the result was shown. The input and both outputs are
provided as a counterexample; minimization is heuristic and is not claimed to
be globally minimal.

A difference is a fact about two behaviours, **not a judgement about your
circuit**. Without a trusted oracle, Flip cannot tell you which behaviour is
intended or which circuit, if either, is wrong.

## 5. What UNKNOWN means

`UNKNOWN` means Flip could not reach a trustworthy complete verdict. Common
reasons are a solver timeout, a resource ceiling, an unresolved reference, an
unavailable network reader, a stale environment, or a missing required pin
mapping. It may also be an explicit invalid-input state when the comparison
cannot even be set up.

`UNKNOWN` is never reported as `EQUIVALENT`. A timeout or a killed worker is an
inconclusive attempt, not evidence that the circuits match. The result carries a
reason code so you know what to change or retry.

## 6. Why an intent oracle matters

A SAT comparison answers "do these two behaviours differ?". It cannot answer
"is the behaviour I wanted?". For that, Flip needs an external point of
reference you trust: a previous version other developers rely on, a reference
circuit, or expected vectors you supply. Flip calls this the intent oracle.

Declaring an oracle changes what you may **claim**, not what the solver proves.
With a trusted reference, `EQUIVALENT` supports "my refactor matches the version
others rely on". With no declaration, a valid pairwise result is still
displayed, but only as a behavioural diff. A name such as `sum` or `xor` is
never treated as intent or proof of compatibility.

## 7. Historical versus current evidence

These are two independent axes:

- **Verdict** — `EQUIVALENT`, `DIFFERENT` or `UNKNOWN` (what the comparison
  found).
- **Freshness** — `CURRENT`, `HISTORICAL`, `STALE` or `UNVERIFIED` (how the
  pinned chain observation relates to the chain now).

A comparison over archived captures is `HISTORICAL` and remains reproducible
and reviewable. A caller-supplied `CURRENT` flag cannot promote cached data:
flip compare reports `HISTORICAL` even when an import says `CURRENT`. If a
dependency or implementation hash changes, earlier evidence becomes `STALE`;
it is kept for review but loses any "current" badge. A successful local
comparison is never a fresh onchain observation.

## 8. What read-only pre-flight proves

Read-only structural pre-flight performs no transaction. It re-reads the
current fee and environment, then classifies the candidate as exactly one of:

- `STRUCTURALLY ACCEPTED` — the read-only checks progressed through structural
  validation to the known resource-burn stage;
- `REJECTED` — a named structural check failed;
- `UNKNOWN` — the reader, override or revert reason could not establish a
  structural result.

It proves nothing about having paid a burn, minted a transistor, simulated the
full transaction, or published a circuit. No wallet connection, signing,
payment or broadcast is part of Flip. In the accepted M3 baseline this command
is reserved and returns `NOT_IMPLEMENTED`; the descriptions above are the
bounded M4 target contract.

## 9. What Flip does not guarantee

- Unrestricted onchain execution, deployment, minting, publication or
  transaction success.
- Formal verification of your application, security, or real-world intent.
  `EQUIVALENT` is bounded to stateless pairwise semantics, an explicit mapping
  and the pinned dependency/environment hashes.
- Protection against a malicious RPC operator or agreement between multiple
  operators. Observations are single-RPC and labelled as such.
- Correctness of the native solver for all possible circuits, globally minimal
  counterexamples, or browser/WASM latency parity with native benchmark numbers.
- Unbounded stateful equivalence. Stateful circuits, when supported later, get
  only a bounded trace comparison and never an unbounded `EQUIVALENT` verdict.
- Results above the published budgets: 2,500 gates by default, 5,000 maximum,
  REF depth 64, 5-second deadline and 64 MiB logical worker memory. Exceeding
  them yields `UNKNOWN`, not a stronger claim.

Always read the verdict together with its oracle mode, mapping, limits, reason
code and freshness before relying on it.
