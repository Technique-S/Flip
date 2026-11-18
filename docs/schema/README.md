# Flip contracts 1.0.0

Models in `packages/flip-core/src/flip_core/models.py` are authoritative. Standalone
JSON Schemas use Draft 2020-12 and `urn:flip:schema:<name>:1.0.0` identifiers.
Generate with `flip-schemas --out docs/schema/1.0.0`; add `--check` for drift detection.
Rebuild synthetic examples with `python docs/schema/build_examples.py`.

| Contract | Purpose |
| --- | --- |
| circuit-identity | Version, integer chain 196, normalized processor and decimal ID |
| project | Source manifests, ordered restricted REF/NAND recipe, explicit pins and bijective maps |
| manifest | Block-pinned circuit closure and per-circuit execution environment |
| comparison-report | Content references for both sides; independent proof, intent and freshness |
| preflight | Read-only receipt, fresh fee and structural classification only |
| error-envelope | Stable machine reason and bounded human-readable message |

All top-level artifacts and nested circuit identities explicitly require
`schemaVersion: "1.0.0"`. Every other version, including future patches/minors, is
rejected with `UNSUPPORTED_SCHEMA_VERSION`. No implicit migrations. Extra fields
are forbidden throughout. Defaults materialize before hashing; nullable fields
without defaults remain required.

JSON Schema validates wire shape. Pydantic additionally checks uint256 bounds,
bit lengths, recipe references/arity, mapping bijections, closure connectivity,
cycles/depth, witness consistency and verdict prerequisites. A JSON Schema pass
alone is not full Flip validation. Use `validate_contract` as the shared boundary.
Neither layer executes circuits, verifies chain truth, checks declared hashes
against missing raw bytes, or proves submitted evidence is genuine.

## Numbers, addresses and bytes

`chainId` is integer 196; strings, booleans, floats and other chains are rejected.
EVM IDs, block numbers and fees in wei are canonical **decimal strings**, `0` or
a nonzero digit followed by digits, <=uint256. No signs, leading zeros, hex or
scientific notation. TAP-02 REF recipe IDs additionally fit uint64 (eight bytes).
Counts, pins and budgets are bounded ordinary integers.

Addresses accept `0x` plus 40 hex digits and normalize to lowercase before hashing.
This is not EIP-55 checksum validation. Hashes are `0x` plus 64 lowercase hex digits.
Byte strings use lowercase even-length `0x` hex. Netlist hashes are SHA-256 over
**raw bytes**, not their JSON hex text. Artifact hashes cover canonical JSON.

Arrays retain order, including dependencies, edges, components and mappings.
Order is part of identity: producers must preserve it; validators never silently
sort arrays. Dependencies must form a connected DAG, with no duplicate circuit
identities/edges or nesting >64. Each snapshot records factory/implementation,
beacon/implementation and processor code hashes at the manifest block. The
implementation slot field stores the observed 32-byte storage word; its decoded
address and code hash are separate required fields. Slot/ABI/registry validation
and resolving content-addressed references are M2 gates.

## TAP-02 bitvector provenance

`BitVector` requires `encoding: "tap02-lsb0-v1"`, width, and a `0`/`1` string.
Character i is vector bit i, mapping to bit i mod 8 of byte floor(i/8). Thus
`"100000001"`, width 9, packs to `0x0101`. Numeric vectors and other encodings are
rejected. Canonical output has exactly ceil(width/8) bytes and zero high padding.
Raw contract inputs are lenient about missing bytes and padding; a future
evaluator must preserve that behavior separately. M1 implements no packer/evaluator.

Provenance is TAP-02 §5 and inspected `pack`/`unpack` functions at revision
`527477ecb7cf68ee9e86d8292669d57fe1680572`:

- [Specification, CC0-1.0](https://github.com/TapeOutProtocol/TAPs/blob/527477ecb7cf68ee9e86d8292669d57fe1680572/TAPs/TAP-02.md)
- [Reference implementation, MIT](https://github.com/TapeOutProtocol/TAPs/blob/527477ecb7cf68ee9e86d8292669d57fe1680572/assets/tap-02/reference.py)
- [Published vectors](https://github.com/TapeOutProtocol/TAPs/blob/527477ecb7cf68ee9e86d8292669d57fe1680572/assets/tap-02/vectors.json)

Full fetched-byte SHA-256 values appear in `source-provenance.json` and the
`Semantics` model. No abbreviated audit hash was expanded, and no missing raw
experiment was reconstructed. Packing checks do not establish full 18-vector
semantic parity or X Layer execution parity.

## Canonical JSON and SHA-256

`flip-json-v1` is a restricted profile, not all of RFC 8785. First validate to
normalize addresses and materialize defaults. Sort object keys recursively by
ASCII code point, preserve arrays, emit UTF-8 without BOM, whitespace or trailing
newline. Strings use JSON escaping and literal non-ASCII characters, with no
Unicode NFC/NFD normalization. ASCII keys only; lone surrogates are forbidden.
Null, booleans and empty strings remain distinct.

Numbers must be integers with absolute value <=9007199254740991. Floats, exponent
notation, NaN, infinity, negative zero, duplicate keys, non-string keys and other
Python types are rejected. Decimal-string EVM quantities avoid JS precision loss.
The CLI transport newline is excluded from hashes.

`content_hash(model)` is `0x` plus lowercase SHA-256 of those exact bytes. No
self-hash field exists in content models. Every field is hashed; none is silently
removed. Timestamps, elapsed time and diagnostics belong in a separate transport
envelope and are rejected by these content schemas. Freshness/block changes
therefore change report hashes; retain original artifacts for historical evidence.

`canonical-golden.json` supplies six synthetic examples with exact text, UTF-8 hex
and digest (including wide IDs, Unicode and numeric-looking keys). The independent
Node check is `node docs/schema/check-canonical.mjs`. It joins sorted keys directly;
inserting numeric keys into an object then JSON.stringify would reorder them.

## Evidence axes

- Proof: v1 supports `PAIRWISE_EQUIVALENCE`. `EQUIVALENT` requires declared
  stateless source/mapping validation, Minisat22 and UNSAT; `DIFFERENT` requires
  SAT and a reproduced distinguishing witness. `UNKNOWN` requires a reason and
  has no trusted witness. Imported assertions still require actual replay.
- Intent: `TRUSTED_REFERENCE` requires a user trust assertion; `UNDECLARED` makes
  no correctness claim. Pairwise equivalence can exist without an intent oracle;
  missing comparison target/mapping cannot yield a proof.
- Freshness: `CURRENT`, `HISTORICAL`, `STALE`, `UNVERIFIED`. Current requires a
  revalidation block. Stale historical evidence remains independently reviewable.
- Preflight: `STRUCTURALLY_ACCEPTED`, `REJECTED`, `UNKNOWN`. Conclusive receipts
  require same-block fee observation/revalidation. Burn-stage revert means
  structural progress only. Unknown revert is UNKNOWN; no fixed assumed fee,
  publication or simulation-success status exists.

Vector testing and zero-state traces (<=8 beats) require future separately typed
contracts and cannot be encoded as unbounded EQUIVALENT. No feature endpoint
produces reports in M1; example report/preflight are UNKNOWN / NOT_IMPLEMENTED.

## Preserved limits and deferred gates

Default 2,500 expanded gates, manual maximum 5,000; nesting <=64, timeout <=5,000 ms,
memory <=64 MiB. Recipe/edge/artifact bounds are conservative schema defenses,
not audited decoder guarantees. Measured 1,250 chained REFs / 1,251 external inputs
and <=50-gate Python DPLL fallback do not authorize exceeding these ceilings.
No solver/fallback is installed. Decoder byte/record/RPC/expanded-work budgets,
pre-SAT input guards, hard worker containment, raw corpus/9-negative replay and
fresh manifest checking remain mandatory later gates.
