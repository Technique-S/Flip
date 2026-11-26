# Final merge recommendation — P7-V2-A

Exact reviewed head: `036c7a99f26d87dd4366762c8c3c059ac8e3d65d`
Production implementation: `b23d3dcf8f98e9b95cd0bc8ca8fbf612045e1daa`
Accepted main: `fc9c0c1bcb2557169dd89af0c3b2c5a7628c9adf`
Review evidence SHA: reported in the accompanying chat handoff.
PR #14 remains a draft; **no merge was performed**.

## Recommendation

**Code-level PASS for P7-V2-A.** All seven gates pass independently; no merge-decisive semantic blocker remains open. The owner may merge PR #14 after recording the accepted SEC-01 policy decision; that decision is repository-level and is not created by this review.

## Gate results

| Gate | Result | Basis |
|---|---|---|
| G0 Scope/authorization | PASS | NAND-only explicit bindings; no Python/schema/dependency/CI/release change; exact production tree at implementation head |
| G1 Canonical parity/no partial graph | PASS | 26 adversarial probes, 72 browser cases, exact request snapshots, real compose authority |
| G2 Proof freshness/dirty state | PASS | Real EQUIVALENT invalidated, historical-only view, export disabled, generation/abort binding |
| G3 Read-only/security | PASS | Only compose call; no wallet/network/graph mutation; release guard and protected rules intact; SEC-01 unchanged |
| G4 Keyboard/accessibility | PASS (automated) | 72 browser cases incl. focus regressions, axe, native controls; human AT trials NOT TESTED |
| G5 Network/pre-allocation budgets | PASS | Network recorder; 1 MiB/65000/255 guards; 178/179 boundary |
| G6 Dual-OS regression/custody | PASS | 702/72/28 on Ubuntu and Windows at exact head; local lint/build/schema/parity/guard/custody all pass |

## Findings

- V2A-F1 MEDIUM — inherited interactive budget and ~178-NAND ceiling not documented. Non-blocking; document and surface exact reason.
- V2A-F2 LOW — object-literal `__proto__` bypasses closed-key count in the pure validator; no canonical mutation, JSON-parsed form rejects. Non-blocking; normalize own keys and add a regression.
- V2A-I1 INFORMATIONAL — SEC-01 OPEN/HIGH under accepted solo-maintainer policy.

## 56-case coverage

PASS 30 · CONTRACT_MISMATCH 22 · NOT_EXECUTED 4 · FAIL 0. Every mismatch records its governing source (approved command contract, explicit-input authorization, inherited budget, out-of-scope output remap/REF authoring) in `case-reconciliation-final.json`. No original case was rewritten and no fixture was counted as a passing production test.

## Separate assessments

1. **V2-A functional acceptance — PASS**
2. **Canonical semantic correctness — PASS**
3. **Historical proof/evidence integrity — PASS**
4. **PR #14 merge readiness — PASS (code level; owner SEC-01 policy decision retained)**
5. **SEC-01 repository risk — OPEN / HIGH** (unchanged; not closed by V2-A)
6. **Overall P7 completion — FAIL** (V2-A is one increment; V2-B/V2-C, Canary, portability, guide and human/performance V7 work remain)
7. **P8 readiness — FAIL**
8. **Public deployment readiness — FAIL**

A passing V2-A review does not close SEC-01, complete P7, authorize live tape-out, or permit wallet/transaction/hosting work. No V2-B/V2-C implementation was performed. Stop with PR #14 unmerged pending the owner's decision.
