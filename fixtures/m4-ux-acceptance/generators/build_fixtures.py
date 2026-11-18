"""Deterministic M4-B neutral fixtures derived only from frozen M3 inputs.

Usage (from repository root, uv sync --locked already applied):

    uv run --frozen python fixtures/m4-ux-acceptance/generators/build_fixtures.py build
    uv run --frozen python fixtures/m4-ux-acceptance/generators/build_fixtures.py consumption \
        --equivalent docs/evidence/m4-ux-acceptance/executed/compare-equivalent.stdout.json \
        --different  docs/evidence/m4-ux-acceptance/executed/compare-different.stdout.json

The `build` step reads (never edits) the committed half-adder execution request and
writes neutral request variants into `fixtures/m4-ux-acceptance/cli-cases/requests/`.
The `consumption` step does NOT invent claims: it consumes the actual stdout captured
from `flip compare --project ...` on the pinned baseline and derives consumer-pinned
hashes from that evidence.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from flip_core.canonical import canonical_bytes
from flip_core.composition import compile_project
from flip_core.execution import evaluate
from flip_core.verification import parse_request

ROOT = Path(__file__).resolve().parents[3]
SAMPLE = ROOT / "docs/schema/m3/examples/half-adder.request.json"
OUT = ROOT / "fixtures/m4-ux-acceptance/cli-cases/requests"


def load_sample() -> dict:
    return json.loads(SAMPLE.read_bytes())


def write_json(name: str, value: object) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_bytes(canonical_bytes(value) + b"\n")


def write_raw(name: str, raw: bytes) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_bytes(raw)


def build() -> None:
    sample = load_sample()

    # Byte-identical baseline copy: the frozen committed request, not a rewrite.
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "half-adder-equivalent.json").write_bytes(SAMPLE.read_bytes())

    # DIFFERENT: swap the candidate's declared output order. The reference stays
    # untouched; the explicit outputMap [0,1] then pairs carry with sum.
    different = copy.deepcopy(sample)
    different["project"]["candidate"]["outputs"] = list(
        reversed(different["project"]["candidate"]["outputs"])
    )
    write_json("half-adder-different-output-order.json", different)

    # UNKNOWN: the smallest allowed native worker deadline (1 ms). Timeout => UNKNOWN.
    timeout = copy.deepcopy(sample)
    timeout["project"]["limits"]["solverTimeoutMs"] = 1
    write_json("half-adder-unknown-timeout.json", timeout)

    # A caller-supplied CURRENT flag must not change the HISTORICAL classification.
    current_claim = copy.deepcopy(sample)
    for item in current_claim["imports"]:
        item["integrity"]["freshness"] = "CURRENT"
    write_json("half-adder-current-freshness-claim.json", current_claim)

    # Malformed input: structurally invalid JSON bytes.
    write_raw("malformed-request.json", b'{"schemaVersion":"m3-1.0.0",\n')

    # Unsupported version: only a version label is changed.
    unsupported = copy.deepcopy(sample)
    unsupported["schemaVersion"] = "m4-1.0.0"
    write_json("unsupported-version.json", unsupported)

    # Wrong chain: a single import identity is relabelled as Base 8453.
    wrong_chain = copy.deepcopy(sample)
    wrong_chain["imports"][0]["manifest"]["root"]["identity"]["chainId"] = 8453
    wrong_chain["imports"][0]["circuits"][0]["identity"]["chainId"] = 8453
    write_json("wrong-chain.json", wrong_chain)

    # Invalid pin mapping: outputMap references a non-existent candidate output.
    bad_map = copy.deepcopy(sample)
    bad_map["project"]["comparison"]["outputMap"] = [0, 2]
    write_json("invalid-pin-map.json", bad_map)

    # Vector request: expected rows are computed from the committed reference
    # candidate by the pinned M3 evaluator, never hand-typed. This is an
    # engine-derived oracle, not an independent external specification.
    vectors = copy.deepcopy(sample)
    source_request = parse_request(SAMPLE.read_bytes())
    composition = compile_project(source_request.project, source_request.imports)
    rows = []
    for a in (0, 1):
        for b in (0, 1):
            bits = [a, b]
            observed = evaluate(composition.reference, bits)
            rows.append(
                {
                    "inputs": {
                        "encoding": "tap02-lsb0-v1",
                        "width": len(bits),
                        "bits": "".join(str(bit) for bit in bits),
                    },
                    "outputs": {
                        "encoding": "tap02-lsb0-v1",
                        "width": len(observed),
                        "bits": "".join(str(bit) for bit in observed),
                    },
                }
            )
    vectors["vectors"] = rows
    write_json("half-adder-vectors.json", vectors)

    # Extract the genuine M2 import manifest captured inside the frozen sample,
    # for revalidate/wrong-chain CLI cases. It is a historical observation.
    write_json("import-manifest.json", sample["imports"][0]["manifest"])

    sources = {
        "generator": "fixtures/m4-ux-acceptance/generators/build_fixtures.py",
        "source": "docs/schema/m3/examples/half-adder.request.json",
        "sourceSha256": hashlib.sha256(SAMPLE.read_bytes()).hexdigest(),
        "derivations": {
            "half-adder-equivalent.json": "byte-identical copy of source",
            "half-adder-different-output-order.json": "candidate.outputs reversed",
            "half-adder-unknown-timeout.json": "limits.solverTimeoutMs set to 1 (minimum)",
            "half-adder-current-freshness-claim.json": "import freshness flags set to CURRENT",
            "malformed-request.json": "truncated JSON bytes, no production schema involved",
            "unsupported-version.json": "schemaVersion changed to m4-1.0.0",
            "wrong-chain.json": "one import identity and manifest root chainId changed to 8453",
            "invalid-pin-map.json": "comparison.outputMap changed to [0,2]",
            "import-manifest.json": "historical M2 manifest captured in source imports[0]",
            "half-adder-vectors.json": "four rows from pinned flip_core.evaluate on source",
        },
        "provenance": "NEUTRAL_DERIVED_FROM_FROZEN_M3_SAMPLE; offline, no fabricated proof",
    }
    write_json("SOURCES.json", sources)


def consumption(equivalent: Path, different: Path) -> None:
    eq = json.loads(equivalent.read_bytes())
    diff = json.loads(different.read_bytes())

    def pin(claim: dict, name: str) -> dict:
        request = claim["reproduction"]
        return {
            "schemaVersion": "m3-1.0.0",
            "kind": "M3_CONSUMPTION",
            "executionRequest": request,
            "claimedResult": claim,
            "expectedProjectHash": claim["report"]["projectHash"],
            "expectedReferenceHash": claim["report"]["referenceManifestHash"],
        }

    write_json("consumption-valid.json", pin(eq, equivalent.name))

    forged = pin(eq, equivalent.name)
    forged["claimedResult"] = copy.deepcopy(forged["claimedResult"])
    forged["claimedResult"]["report"]["verification"]["verdict"] = "DIFFERENT"
    write_json("consumption-forged-verdict.json", forged)

    stale = pin(eq, equivalent.name)
    stale["expectedReferenceHash"] = "0x" + "00" * 32
    write_json("consumption-changed-reference.json", stale)

    current = pin(eq, equivalent.name)
    current["claimedResult"] = copy.deepcopy(current["claimedResult"])
    current["claimedResult"]["report"]["integrity"]["freshness"] = "CURRENT"
    write_json("consumption-current-relabel.json", current)

    # A real DIFFERENT claim with a real replayed witness is needed for the
    # witness-consumption path; no witness text is manufactured here.
    write_json("consumption-different.json", pin(diff, different.name))

    write_json(
        "CONSUMPTION_SOURCES.json",
        {
            "generator_subcommand": "consumption",
            "equivalentStdout": str(equivalent),
            "differentStdout": str(different),
            "derivations": {
                "consumption-valid.json": "unmodified executed claim plus consumer-pinned hashes",
                "consumption-forged-verdict.json": "verdict relabelled EQUIVALENT -> DIFFERENT",
                "consumption-changed-reference.json": "expectedReferenceHash set to zero digest",
                "consumption-current-relabel.json": "claimed freshness HISTORICAL -> CURRENT",
                "consumption-different.json": "executed DIFFERENT claim with its replayed witness",
            },
            "provenance": "CLAIMS ARE CAPTURED CLI OUTPUT, NOT AUTHOR-ASSERTED RESULTS",
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build")
    consume_parser = sub.add_parser("consumption")
    consume_parser.add_argument("--equivalent", type=Path, required=True)
    consume_parser.add_argument("--different", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "build":
        build()
    else:
        consumption(args.equivalent, args.different)
    print(f"wrote fixtures under {OUT}")


if __name__ == "__main__":
    main()
