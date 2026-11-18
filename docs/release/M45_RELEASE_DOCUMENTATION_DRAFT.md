# Flip — draft release documentation (M4.5-R)

**Factual basis:** accepted baseline `09f2482beae84be6d919ecd6957c4153d1924cca`,
`README.md`, `docs/milestones/M4_A_HANDOFF.md`, `M4_ACCEPTANCE.md` and the
independent M4 review. Draft only; no unpublished feature is promised.

## What Flip does

Flip is a **local circuit workbench**. It imports X Layer circuit definitions
with read-only calls, resolves their `REF` dependencies into an integrity
manifest, composes a small set of components with explicit numbered pins,
compares a candidate wiring against a reference under pinned stateless TAP-02
semantics, explains differences with an independently replayed counterexample,
and exports a canonical JSON evidence bundle. It also offers a read-only
structural pre-flight. It does not deploy, mint, sign or publish anything.

## Who it is for

An application developer integrating existing TapeOut circuits, or a circuit
maintainer who needs to show that a refactor preserved behaviour. The user has
processor addresses and circuit IDs, possibly a previous version or expected
vectors, and wants pre-publication behavioural confidence. No wallet is needed.

## Start the local application

```sh
uv sync --locked
npm ci --prefix apps/web
npm run build --prefix apps/web
uv run --frozen python -m flip_api.local
```

Open <http://127.0.0.1:8000> and choose **Open sample**. Set
`FLIP_LOCAL_SOLVER=1` in the server environment before launch to enable native
comparison, export and replay; imports and the historical sample work without
it. Only localhost is supported. See `docs/milestones/M4_A_HANDOFF.md`.

## Use the CLI

```sh
uv run flip sample half-adder --out project.json
uv run flip compose --project project.json --out composition.json
uv run flip compare --project project.json --out comparison.json
uv run flip sample swapped --out mutation.json
uv run flip compare --project mutation.json --out difference.json
uv run flip export --project mutation.json --out evidence.json
uv run flip inspect-evidence --bundle evidence.json
uv run flip verify-bundle --project mutation.json --bundle evidence.json
```

Live read-only commands (separate, opt-in RPC): `inspect`, `import`,
`new-project`, `revalidate`, `preflight`, and `export --observe-chain`. Set
`FLIP_RPC_URL` to a trusted operator; HTTP clients cannot choose arbitrary
endpoints. Output is JSON on stdout; scripts must read both the JSON and the
exit code. Exit codes: 0 completed/equivalence, 1 DIFFERENT, 2 UNKNOWN,
3 invalid input/wrong chain, 4 RPC failure, 6 unavailable legacy operation,
7 stale binding, 8 structural rejection.

## What the proof outcomes mean

- **EQUIVALENT** — no input distinguishes the two circuits under the declared
  stateless semantics, bit order, pin mapping and pinned dependencies. It is
  pairwise behavioural equivalence under a model, **not** a claim that either
  circuit is correct, secure or safe to publish.
- **DIFFERENT** — at least one input produces different outputs, and the
  witness was replayed independently on both circuits. It does not say which
  behaviour is intended without a trusted oracle.
- **UNKNOWN** — no trustworthy complete verdict: timeout, resource limit,
  missing target/map, RPC failure or stale input. It is never EQUIVALENT.

Intent modes are trusted reference, previous version or undeclared behavioural
diff. Only the first two support a correctness-relative claim, and even then
the claim is relative to the declared reference.

## Historical versus current evidence

Every report shows verdict and freshness on separate axes. Archived sample
comparisons are **HISTORICAL** and reproducible; a caller-supplied `CURRENT`
flag cannot promote them. If an environment or dependency hash changes,
earlier evidence becomes **STALE** but remains reviewable. A fresh observation
requires an actual read at a pinned block and is labelled `CURRENT` with its
block, fee and `SINGLE_RPC` provenance. A single RPC remains a trust assumption.

## What structural pre-flight proves

A read-only `eth_call` at a freshly pinned block checks chain identity, source
block canonicality, dependency/environment snapshots, reviewed implementation
hashes and the current fee. `STRUCTURALLY ACCEPTED` means the checks reached the
known insufficient-balance burn-stage revert for the exact fixed caller and
expected gate count. `REJECTED` names a known structural revert; `UNKNOWN`
covers empty or ambiguous data, unavailable overrides, RPC failure and changed
implementation. It proves **nothing** about a paid burn, minted transistor,
successful deployment or ownership. No transaction is broadcast.

## Supported limitations

- X Layer mainnet chain 196 only; no testnet or generic cross-chain execution.
- Stateless circuits for exact comparison; stateful is out of scope for the
  accepted product.
- 2,500 gates default, 5,000 maximum, REF depth 64, 5 s deadline and 64 MiB
  worker memory; exceeding them yields UNKNOWN.
- No wallet, signing, broadcast, payment, token acquisition or publication.
- No public solver hosting; the launcher is loopback-only and solver execution
  needs explicit local opt-in.
- No malicious-RPC resistance and no multi-operator consensus.
- Manual auditory screen-reader testing remains unexecuted.
- The composed sample is an archived local fixture, **not** deployed onchain.

## Six proposed pre-M5 capabilities (status summary)

The following are proposed capability areas under review, not all shipped:

1. **Human and coding-agent workflows** — local React UI, JSON-first CLI,
   versioned schemas and a shared engine are present; explicit human
   deployment approval is not implemented because no deployment exists.
2. **Circuit and processor library** — import/inspect of a supplied identity is
   present; search, favorites, recently imported and metadata catalogue are
   not present on this baseline.
3. **Authorized X Layer tape-out lifecycle** — structural pre-flight is
   present; transaction preview, authorization, submission, confirmation and
   receipt are **not implemented**. No write transaction exists.
4. **Agent execution safety** — permission boundaries, chain verification,
   resource limits and replay rejection exist; spending limits and transaction
   authorization are not applicable without a write path.
5. **Portable circuit project format** — versioned project and evidence JSON,
   web↔CLI exchange, deterministic reproduction and replay verification are
   present.
6. **Circuit debugging diagnostics** — replayed counterexample inputs, actual
   versus expected outputs, bit-level differences and non-colour labels are
   present; automatic connection-level correction guidance is not implemented.

See `docs/release/M45_INDEPENDENT_READINESS.md` for the evidence classification
of each sub-item.

## Current release blockers / open risks

- Public hosting (authentication, process isolation, aggregate budgets and
  request controls) is **blocked**.
- Manual screen-reader session is **blocked/unexecuted**.
- Write-enabled tape-out lifecycle is **not implemented** and must not be
  advertised.
- Hackathon access-link requirement is unconfirmed for a loopback-only app
  (`docs/release/M45_HACKATHON_COMPLIANCE.md`, H-09).
- Solver distribution/licensing notices and Flip's own source license remain
  administrative open items.
