"""Deterministic generator for the M2-B adversarial fixture corpus.

Reads only committed immutable M1-B evidence. Writes only:
  fixtures/m2-adversarial/{tap02-malformed,rpc-failures,integrity-negatives,m1-regressions,MANIFEST}.json

No network, no RPC, no signing, no product code. Run:
  python docs/evidence/m2-adversarial/build_corpus.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

WT = Path(__file__).resolve().parents[3]
RAW0 = WT / "docs" / "evidence" / "raw" / "M0"
RAW5 = WT / "docs" / "evidence" / "raw" / "M05"
OUT = WT / "fixtures" / "m2-adversarial"

ARCHIVED_VECTORS = RAW0 / "vectors.json"
ARCHIVED_NEGATIVES = RAW5 / "gate_b_negative.json"
ARCHIVED_MANIFEST = RAW5 / "gate_b_manifest.json"


def dump(name: str, obj: object) -> Path:
    path = OUT / name
    text = json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    return path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strip0x(value: str) -> str:
    return value[2:] if value.startswith("0x") else value


def u24(n: int) -> str:
    return n.to_bytes(3, "big").hex()


def nand(a: int, b: int) -> str:
    return "00" + u24(a) + u24(b)


def latch(d: int) -> str:
    return "01" + u24(d)


def ref(cpu_hex: str, cid: int, ins: list[int], n_out: int) -> str:
    cpu = bytes.fromhex(strip0x(cpu_hex))
    assert len(cpu) == 20
    return (
        "02"
        + cpu.hex()
        + cid.to_bytes(8, "big").hex()
        + bytes([len(ins), n_out]).hex()
        + "".join(u24(s) for s in ins)
    )


def synth_cpu(tag: int) -> str:
    # Always exactly 20 bytes: 18 zero bytes + a 2-byte big-endian tag.
    return "0x" + "00" * 18 + (tag & 0xFFFF).to_bytes(2, "big").hex()


def archived_case(name: str) -> dict:
    data = json.loads(ARCHIVED_VECTORS.read_text(encoding="utf-8"))
    return next(item for item in data["illFormed"] if item["name"] == name)


# ---------------------------------------------------------------------------
# Task A -- TAP-02 malformed-input corpus
# ---------------------------------------------------------------------------

def build_tap02(archive_sha: str) -> dict:
    cases: list[dict] = []

    def add(case_id: str, category: str, *, n_in: int, n_out: int, netlist: str,
            expected: dict, spec: str, provenance: str, refs: list | None = None,
            resolver: dict | None = None, executed: str = "reference_decoder_safe",
            note: str = "") -> None:
        raw_hex = strip0x(netlist)
        try:
            raw_len = len(bytes.fromhex(raw_hex))
            digest = hashlib.sha256(bytes.fromhex(raw_hex)).hexdigest()
        except ValueError:
            raw_len = None
            digest = None
        cases.append({
            "id": case_id,
            "category": category,
            "nIn": n_in,
            "nOut": n_out,
            "netlist": netlist,
            "netlist_bytes": raw_len,
            "netlist_sha256": digest,
            "refs": refs or [],
            "resolver": resolver or {},
            "expected_outcome": expected,
            "spec_reference": spec,
            "provenance": provenance,
            "archived_reference_decoder_execution": executed,
            "note": note,
        })

    spec_decode = "TAP-02 §3 well-formedness; archived reference.py decode()/load() (MIT, pinned in M1 Semantics)"
    spec_limit = "MVP_CONSTRAINTS.md §3 (bound records/REF depth/expanded gates) and §6 (5,000-gate / 5s / 64MiB ceilings)"

    a = archived_case("truncated_record")
    add("TAP-MAL-001", "truncated-netlist", n_in=a["nIn"], n_out=a["nOut"], netlist=a["netlist"],
        expected={"kind": "reject", "reason_prefix": "truncated record"},
        spec=spec_decode, provenance="ARCHIVED_VECTOR:vectors.json.illFormed.truncated_record",
        refs=a["refs"])

    a = archived_case("unknown_opcode")
    add("TAP-MAL-002", "invalid-opcode", n_in=a["nIn"], n_out=a["nOut"], netlist=a["netlist"],
        expected={"kind": "reject", "reason_prefix": "unknown opcode 0x03"},
        spec=spec_decode, provenance="ARCHIVED_VECTOR:vectors.json.illFormed.unknown_opcode",
        refs=a["refs"])

    a = archived_case("nand_forward_reference")
    add("TAP-MAL-003", "future-signal-reference", n_in=a["nIn"], n_out=a["nOut"], netlist=a["netlist"],
        expected={"kind": "reject", "reason_prefix": "signal 5 referenced by element at 4 is not available"},
        spec=spec_decode, provenance="ARCHIVED_VECTOR:vectors.json.illFormed.nand_forward_reference",
        refs=a["refs"])

    a = archived_case("ref_arity_mismatch")
    add("TAP-MAL-004", "invalid-ref-arity", n_in=a["nIn"], n_out=a["nOut"], netlist=a["netlist"],
        expected={"kind": "reject", "reason_prefix": "REF arity does not match the target circuit"},
        spec=spec_decode, provenance="ARCHIVED_VECTOR:vectors.json.illFormed.ref_arity_mismatch",
        refs=a["refs"])

    a = archived_case("nOut_zero")
    add("TAP-MAL-005", "incorrect-output-count", n_in=a["nIn"], n_out=a["nOut"], netlist=a["netlist"],
        expected={"kind": "reject", "reason_prefix": "nIn/nOut out of range"},
        spec=spec_decode, provenance="ARCHIVED_VECTOR:vectors.json.illFormed.nOut_zero",
        refs=a["refs"])

    a = archived_case("output_is_an_input")
    add("TAP-MAL-006", "incorrect-output-count", n_in=a["nIn"], n_out=a["nOut"], netlist=a["netlist"],
        expected={"kind": "reject", "reason_prefix": "too few signals for outputs"},
        spec=spec_decode, provenance="ARCHIVED_VECTOR:vectors.json.illFormed.output_is_an_input",
        refs=a["refs"])

    a = archived_case("more_outputs_than_elements")
    add("TAP-MAL-007", "incorrect-output-count", n_in=a["nIn"], n_out=a["nOut"], netlist=a["netlist"],
        expected={"kind": "reject", "reason_prefix": "too few signals for outputs"},
        spec=spec_decode, provenance="ARCHIVED_VECTOR:vectors.json.illFormed.more_outputs_than_elements",
        refs=a["refs"])

    a = archived_case("ref_target_not_registered")
    add("TAP-MAL-008", "unregistered-ref-target", n_in=a["nIn"], n_out=a["nOut"], netlist=a["netlist"],
        expected={"kind": "reject", "reason_prefix": "REF target is not a circuit of a registered processor"},
        spec=spec_decode, provenance="ARCHIVED_VECTOR:vectors.json.illFormed.ref_target_not_registered",
        refs=a["refs"])

    cpu_a = "0x839BDD6fA7A66416a609A735E11DE5411b98574E"
    add("TAP-MAL-009", "invalid-ref-header", n_in=2, n_out=1, netlist="0x02" + "aa" * 10,
        expected={"kind": "reject", "reason_prefix": "truncated record"},
        spec="TAP-02 §3 REF record: 20-byte cpu + 8-byte id + nIns/nOuts; truncated header is malformed",
        provenance="SYNTHETIC: deterministic 10-of-20-byte cpu header",
        note="REF cpu field deliberately truncated to 10 bytes.")

    add("TAP-MAL-010", "invalid-ref-header", n_in=2, n_out=1,
        netlist="0x02" + strip0x(cpu_a) + "00000000000000",
        expected={"kind": "reject", "reason_prefix": "truncated record"},
        spec="TAP-02 §3 REF record (8-byte circuit id); truncated header is malformed",
        provenance="SYNTHETIC: 3-of-8-byte circuit id using real processor address",
        note="REF circuit-id field deliberately truncated.")

    add("TAP-MAL-011", "invalid-ref-header", n_in=2, n_out=1,
        netlist="0x02" + strip0x(cpu_a) + "0000000000000001",
        expected={"kind": "reject", "reason_prefix": "truncated record"},
        spec="TAP-02 §3 REF record (nIns and nOuts bytes required)",
        provenance="SYNTHETIC: REF record with ni/no bytes omitted",
        note="ni/no count bytes deliberately absent.")

    add("TAP-MAL-012", "excessive-declared-count", n_in=65537, n_out=1, netlist="0x",
        expected={"kind": "reject", "reason_prefix": "nIn/nOut out of range"},
        spec="TAP-02 §3 MAX_PINS = 2^16; reference.py load() nIn/nOut check",
        provenance="SYNTHETIC: declared nIn = MAX_PINS + 1")

    add("TAP-MAL-013", "excessive-declared-count", n_in=1, n_out=65537, netlist="0x",
        expected={"kind": "reject", "reason_prefix": "nIn/nOut out of range"},
        spec="TAP-02 §3 MAX_PINS = 2^16; reference.py load() nIn/nOut check",
        provenance="SYNTHETIC: declared nOut = MAX_PINS + 1")

    add("TAP-MAL-014", "excessive-declared-count", n_in=2**24, n_out=1, netlist="0x" + nand(0, 1),
        expected={"kind": "reject", "reason_prefix": "more than 2^24 signals"},
        spec="TAP-02 §3 MAX_SIGNALS = 2^24; reference.py load() signal-count check",
        provenance="SYNTHETIC: declared nIn = 2^24 with one small NAND record",
        note="Bounded: decoder computes n_sig before any large allocation.")

    cycle_resolver = {
        "cpuA": {"cpu": synth_cpu(0xA1), "id": 1, "nIn": 0, "nOut": 1,
                 "netlist": "0x" + ref(synth_cpu(0xB2), 1, [], 1)},
        "cpuB": {"cpu": synth_cpu(0xB2), "id": 1, "nIn": 0, "nOut": 1,
                 "netlist": "0x" + ref(synth_cpu(0xA1), 1, [], 1)},
    }
    add("TAP-MAL-015", "recursive-dependency-cycle", n_in=0, n_out=1,
        netlist="0x" + ref(synth_cpu(0xA1), 1, [], 1),
        expected={"kind": "reject", "code": "REF_CYCLE", "reason": "A -> B -> A cycle must be detected and bounded"},
        spec=spec_limit + "; TAP-02 §3 REF closure must form a DAG",
        provenance="SYNTHETIC: two-processor REF cycle",
        resolver=cycle_resolver, executed="SKIPPED_NO_CYCLE_GUARD_IN_ARCHIVED_DECODER",
        note="Archived reference.py has no cycle guard; executing it would recurse. Specification-only.")

    deep_resolver: dict[str, dict] = {}
    for i in range(1, 66):
        cpu = synth_cpu(i)
        inner = ref(synth_cpu(i + 1), i + 1, [], 1) if i < 65 else nand(0, 1)
        deep_resolver[f"id{i}"] = {
            "cpu": cpu, "id": i, "nIn": 0, "nOut": 1, "netlist": "0x" + inner,
        }
    add("TAP-MAL-016", "deep-dependency-chain", n_in=0, n_out=1,
        netlist="0x" + ref(synth_cpu(1), 1, [], 1),
        expected={"kind": "bounded", "code": "REF_DEPTH_EXCEEDED", "depth": 65, "cap": 64},
        spec=spec_limit + "; M1 Limits.refDepthCap <= 64",
        provenance="SYNTHETIC: 65-link REF chain, one link beyond the frozen cap",
        resolver=deep_resolver, executed="SKIPPED_DEEP_RESOLUTION",
        note="Expected outcome is bounded rejection, not acceptance; no resolver execution claimed.")

    # Deterministic pattern instead of enumerating 1,251 resolver records: link i
    # uses cpu tag 1000+i and cid i; link 1251 terminates with one NAND record.
    big_pattern = {
        "kind": "synthetic_ref_chain",
        "links": 1251,
        "cpu_tag_base": 1001,
        "cid_start": 1,
        "cpu_encoding": "18 zero bytes + 2-byte big-endian tag (see build_corpus.synth_cpu)",
        "nIn": 0,
        "nOut": 1,
        "terminal_record": "NAND(0,1) -> 4 NAND gates after full flattening",
        "expanded_gates": 5004,
    }
    add("TAP-MAL-017", "oversized-expansion", n_in=0, n_out=1,
        netlist="0x" + ref(synth_cpu(1001), 1, [], 1),
        expected={"kind": "bounded", "code": "RESOURCE_LIMIT", "expanded_gates": 5004, "cap": 5000,
                  "verdict": "UNKNOWN"},
        spec=spec_limit + "; MVP_CONSTRAINTS.md §5 (timeout/limit => UNKNOWN)",
        provenance="SYNTHETIC: 1,251-link chain pattern flattening to 5,004 NAND gates",
        resolver=big_pattern, executed="SKIPPED_OVERSIZED_EXPANSION",
        note="Expected bounded UNKNOWN/RESOURCE_LIMIT; never EQUIVALENT. Resolver is a deterministic pattern, not expanded bytes.")

    add("TAP-MAL-018", "malformed-hex", n_in=2, n_out=1, netlist="0x0000000200000",
        expected={"kind": "reject", "code": "INVALID_INPUT", "reason": "odd-length hex byte string"},
        spec="flip-json-v1 HexBytes profile (even-length lowercase 0x hex); M1 models.py HexBytes",
        provenance="SYNTHETIC: odd-length hex payload",
        executed="SKIPPED_NOT_DECODEABLE_BYTES",
        note="Import layer must reject before decoder; bytes.fromhex cannot decode this value.")

    return {
        "schema": "flip-m2-adversarial/tap02-malformed/1",
        "purpose": "Deterministic malformed TAP-02 netlist corpus for M2 importer negative tests",
        "generated_by": "docs/evidence/m2-adversarial/build_corpus.py (stdlib only)",
        "immutable_archive_sha256": {
            "docs/evidence/raw/M0/vectors.json": archive_sha,
        },
        "provenance_legend": {
            "ARCHIVED_VECTOR": "Exact illFormed record from committed vectors.json; bytes not modified.",
            "SYNTHETIC": "Constructed deterministically; NOT an observation from any chain or audit run.",
        },
        "execution_legend": {
            "reference_decoder_safe": "Archived reference.py decode()/load() may be executed for an offline reason check.",
            "SKIPPED_*": "Not executed by design; expected outcome is a specification, not a reproduced result.",
        },
        "case_count": len(cases),
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Task B -- RPC failure fixtures
# ---------------------------------------------------------------------------

def build_rpc(pinned: dict) -> dict:
    cases = [
        {
            "id": "RPC-001", "scenario": "wrong-chain-id",
            "request": {"method": "eth_chainId", "params": []},
            "response": {"jsonrpc": "2.0", "id": 1, "result": "0x2105"},
            "reality": "0x2105 is Base mainnet (8453), not X Layer (196)",
            "expected_outcome": {"code": "WRONG_CHAIN", "action": "reject before any REF resolution"},
            "spec_reference": "MVP_CONSTRAINTS.md §1 (chain 196 only, verify eth_chainId per session)",
        },
        {
            "id": "RPC-002", "scenario": "empty-contract-code",
            "request": {"method": "eth_getCode", "params": ["0x839BDD6fA7A66416a609A735E11DE5411b98574E", "latest"]},
            "response": {"jsonrpc": "2.0", "id": 2, "result": "0x"},
            "expected_outcome": {"code": "MISSING_REFERENCE", "action": "reject unregistered processor"},
            "spec_reference": "MVP_CONSTRAINTS.md §4 (REF targets must be registered processors with existing circuits)",
        },
        {
            "id": "RPC-003", "scenario": "missing-circuit",
            "request": {"method": "circuitInfo(uint256)", "params": ["999999"]},
            "response": {"jsonrpc": "2.0", "id": 3, "error": {"code": -32000, "message": "no circuit"}},
            "expected_outcome": {"code": "MISSING_REFERENCE", "action": "reject; never cache as a valid circuit"},
            "spec_reference": "MVP_CONSTRAINTS.md §3-4; M0 audit B4 (selector/ABI provenance)",
        },
        {
            "id": "RPC-004", "scenario": "invalid-abi-response",
            "request": {"method": "netlist(uint256)", "params": ["1"]},
            "response": {"jsonrpc": "2.0", "id": 4, "result": "0x01"},
            "reality": "one byte cannot encode an ABI dynamic bytes value (offset+length+data)",
            "expected_outcome": {"code": "INVALID_ABI_RESPONSE", "action": "reject; do not hash truncated bytes"},
            "spec_reference": "MVP_CONSTRAINTS.md §3 (explicit ABI validation); M0 audit B4 (decoder hazard)",
        },
        {
            "id": "RPC-005", "scenario": "inconsistent-pinned-block",
            "request": {"method": "eth_getBlockByNumber", "params": ["0x488875b", False]},
            "response": {"jsonrpc": "2.0", "id": 5, "result": {"number": "0x488875b", "hash": "0x" + "11" * 32}},
            "second_response": {"jsonrpc": "2.0", "id": 6, "result": {"number": "0x488875b", "hash": "0x" + "22" * 32}},
            "expected_outcome": {"code": "IMPLEMENTATION_CHANGED", "action": "reject same-block divergence; no cached report reuse"},
            "spec_reference": "MVP_CONSTRAINTS.md §3 (pin block + hash; revalidate environment hashes)",
        },
        {
            "id": "RPC-006", "scenario": "timeout",
            "request": {"method": "eth_call", "params": [{"to": "0x839BDD6fA7A66416a609A735E11DE5411b98574E", "data": "0x"}]},
            "response": {"transport": {"timed_out": True, "elapsed_ms": 8000}},
            "expected_outcome": {"code": "RPC_UNAVAILABLE", "verdict": "UNKNOWN", "action": "never EQUIVALENT"},
            "spec_reference": "MVP_CONSTRAINTS.md §5 (timeout/resource limit => UNKNOWN) and §6 (5s check ceiling)",
        },
        {
            "id": "RPC-007", "scenario": "rate-limiting",
            "request": {"method": "eth_getStorageAt", "params": ["0x1f09daefa827f02cbb40967cc91b259763760761", "0x0", "latest"]},
            "response": {"jsonrpc": "2.0", "id": 7, "error": {"code": -32000, "message": "rate limited"}, "retryAfterSeconds": 5},
            "expected_outcome": {"code": "RPC_UNAVAILABLE", "verdict": "UNKNOWN", "action": "bounded retry only; no proof claim"},
            "spec_reference": "MVP_CONSTRAINTS.md §5; M0 R7 (public RPC latency/failure)",
        },
        {
            "id": "RPC-008", "scenario": "malformed-hex",
            "request": {"method": "eth_call", "params": [{"to": "0x839BDD6fA7A66416a609A735E11DE5411b98574E", "data": "0x"}]},
            "response": {"jsonrpc": "2.0", "id": 8, "result": "0xzz"},
            "expected_outcome": {"code": "INVALID_ABI_RESPONSE", "action": "reject non-hex result"},
            "spec_reference": "flip-json-v1 HexBytes (even-length lowercase hex); M0 audit B4 (result validation)",
        },
        {
            "id": "RPC-009", "scenario": "changed-beacon-implementation",
            "request": {"method": "eth_call", "params": [{"to": pinned["beacon"], "data": "0xbeaconImplementation()"}]},
            "response": {"jsonrpc": "2.0", "id": 9, "result": "0x0000000000000000000000001111111111111111111111111111111111111111"},
            "pinned_observed_value": pinned["beaconImplementation"],
            "expected_outcome": {"code": "IMPLEMENTATION_CHANGED", "action": "invalidate cached manifest and report"},
            "spec_reference": "MVP_CONSTRAINTS.md §3/§7; Gate B beacon-implementation-changed negative",
        },
        {
            "id": "RPC-010", "scenario": "changed-factory-implementation",
            "request": {"method": "eth_getStorageAt", "params": [pinned["factory"], pinned["factoryImplSlot"], "latest"]},
            "response": {"jsonrpc": "2.0", "id": 10, "result": "0x0000000000000000000000002222222222222222222222222222222222222222"},
            "pinned_observed_value": pinned["factoryImplAddress"],
            "expected_outcome": {"code": "IMPLEMENTATION_CHANGED", "action": "invalidate cached manifest and report"},
            "spec_reference": "MVP_CONSTRAINTS.md §3/§7; Gate B factory-implementation-changed negative",
        },
    ]
    for case in cases:
        case["provenance"] = "SYNTHETIC_MOCK"
        case["not_an_observation"] = True
        case["no_keys_or_signing"] = True
    return {
        "schema": "flip-m2-adversarial/rpc-failures/1",
        "purpose": "Mocked JSON-RPC failure responses for M2 importer negative tests",
        "generated_by": "docs/evidence/m2-adversarial/build_corpus.py (stdlib only)",
        "safety": "No private keys, no wallet, no signing, no transaction, no live RPC call.",
        "provenance_note": "Pinned historical values come from committed gate_b_manifest.json; all responses are synthetic.",
        "pinned_values_source": "docs/evidence/raw/M05/gate_b_manifest.json",
        "case_count": len(cases),
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Task C -- Integrity negatives (archived nine + deterministic extensions)
# ---------------------------------------------------------------------------

def build_integrity(archive_sha: str, pinned: dict) -> dict:
    archived = json.loads(ARCHIVED_NEGATIVES.read_text(encoding="utf-8"))
    reconstructed = [
        {
            "id": f"INT-NEG-{i:02d}",
            "mutation": item["mutation"],
            "detected": item["detected"],
            "issues": item["issues"],
            "expected_outcome": {"detected": True, "issues": item["issues"]},
            "provenance": "ARCHIVED_OBSERVATION:gate_b_negative.json.negativeTests",
            "not_a_live_observation_in_this_task": True,
        }
        for i, item in enumerate(archived["negativeTests"], start=1)
    ]

    def ext(case_id: str, mutation: str, expected: dict, spec: str) -> dict:
        return {
            "id": case_id,
            "mutation": mutation,
            "expected_outcome": expected,
            "spec_reference": spec,
            "provenance": "SYNTHETIC_EXTENSION",
            "not_an_observation": True,
        }

    spec_identity = "MVP_CONSTRAINTS.md §1/§7 (chain-bound identity, dependency closure, environment hashes)"
    spec_manifest = "Frozen manifest contract 1.0.0 (Snapshot/Environment/Digest/Block/Quantity); M1 independent review F-06"
    extensions = [
        ext("INT-EXT-001", "circuit identity with chainId field absent",
            {"code": "INVALID_INPUT", "detected": True,
             "note": "Current frozen M1 maps missing chainId to WRONG_CHAIN (review F-01); desired taxonomy is INVALID_INPUT."},
            spec_manifest + "; M1 independent review F-01"),
        ext("INT-EXT-002", "code hash written without the required 0x prefix",
            {"code": "INVALID_INPUT", "detected": True}, spec_manifest),
        ext("INT-EXT-003", "stale pinned block hash while block number is unchanged",
            {"code": "BLOCK_HASH_CHANGED", "detected": True}, spec_identity),
        ext("INT-EXT-004", "dependency netlistHash changed inside the closure",
            {"code": "DEPENDENCY_HASH_CHANGED", "detected": True}, spec_identity),
        ext("INT-EXT-005", "declared netlistHash disagrees with SHA-256 of supplied netlist bytes",
            {"code": "NETLIST_HASH_VS_BYTES_INCONSISTENT", "detected": True}, spec_identity),
        ext("INT-EXT-006", "duplicate circuit identity appears twice in one closure",
            {"code": "DUPLICATE_CIRCUIT", "detected": True}, "Frozen Manifest.unique_closure validator; " + spec_identity),
        ext("INT-EXT-007", "same processor address reused with chainId 8453",
            {"code": "CHAIN_MISMATCH", "detected": True}, spec_identity),
        ext("INT-EXT-008", "factory implementation hash replaced with beacon implementation hash",
            {"code": "IMPLEMENTATION_CHANGED", "detected": True}, spec_identity),
        ext("INT-EXT-009", "netlist bytes truncated at the pinned block but hash unchanged",
            {"code": "NETLIST_HASH_VS_BYTES_INCONSISTENT", "detected": True}, spec_identity),
    ]
    return {
        "schema": "flip-m2-adversarial/integrity-negatives/1",
        "purpose": "M0.5 nine-negative corpus reproduced verbatim plus synthetic integrity extensions",
        "generated_by": "docs/evidence/m2-adversarial/build_corpus.py (stdlib only)",
        "immutable_archive_sha256": {
            "docs/evidence/raw/M05/gate_b_negative.json": archive_sha,
        },
        "baseline": archived["baseline"],
        "archived_live_checks_note": "Historical cross-chain/block labels only; not re-fetched in this task.",
        "archived_case_count": len(reconstructed),
        "extension_count": len(extensions),
        "cases": reconstructed + extensions,
    }


# ---------------------------------------------------------------------------
# Task D -- M1 finding regression specifications (not executable vs frozen M1)
# ---------------------------------------------------------------------------

def build_m1_regressions() -> dict:
    cases = [
        {
            "id": "M1-REG-001",
            "title": "Missing-chainId error classification",
            "source_finding": "M1 independent review F-01 (Medium)",
            "reproduction": "Remove chainId from docs/schema/examples/circuit-identity.json and call validate_contract('circuit-identity', payload).",
            "current_observed": {"code": "WRONG_CHAIN"},
            "desired": {"code": "INVALID_INPUT", "reason": "field absent is not a wrong-chain value"},
            "test_specification": "assert ContractError.code == 'INVALID_INPUT' for missing chainId; assert WRONG_CHAIN only for present-but-invalid values.",
            "status": "SPEC_ONLY_NOT_PASSING_AGAINST_FROZEN_M1",
            "requires_contract_revision": True,
        },
        {
            "id": "M1-REG-002",
            "title": "Width/reference binding before proof acceptance",
            "source_finding": "M1 independent review F-02 (Medium)",
            "reproduction": "From comparison-report example set verdict EQUIVALENT/UNSAT, source+mappingValidation PASSED, integrity HISTORICAL, then inputMap=[] and outputMap=[0]; validate_contract currently accepts.",
            "current_observed": {"accepted": True},
            "desired": {"accepted": False,
                        "reason": "map widths must be resolved against the referenced project/manifests before a conclusive verdict"},
            "test_specification": "assert rejection when map lengths disagree with referenced artifact widths; assert rejection when referenced artifacts cannot be resolved/hash-checked; permit zero-input circuits only when the project itself declares zero inputs.",
            "status": "SPEC_ONLY_NOT_PASSING_AGAINST_FROZEN_M1",
            "requires_contract_revision": True,
        },
        {
            "id": "M1-REG-003",
            "title": "Empty revert data and incorrect pre-flight classification",
            "source_finding": "M1 independent review F-04 (Low); MVP_CONSTRAINTS.md §8",
            "reproduction": "Set preflight example status STRUCTURALLY_ACCEPTED, reasonCode null, classification KNOWN_BURN_STAGE, revertData '0x', matching CURRENT blocks; validate_contract currently accepts.",
            "current_observed": {"accepted": True},
            "desired": {"accepted": False,
                        "reason": "a conclusive structural receipt must carry observed revert evidence or be UNKNOWN"},
            "test_specification": "assert rejection of empty revertData for KNOWN_BURN_STAGE/KNOWN_STRUCTURAL_REJECTION; assert UNKNOWN when classification is unsupported or observation is absent.",
            "status": "SPEC_ONLY_NOT_PASSING_AGAINST_FROZEN_M1",
            "requires_contract_revision": True,
        },
        {
            "id": "M1-REG-004",
            "title": "Float chainId error taxonomy",
            "source_finding": "M1 independent review F-03 (Low)",
            "reproduction": "Set circuitId example chainId to 196.0; load_json rejects it before Pydantic and validate_contract returns INVALID_INPUT.",
            "current_observed": {"code": "INVALID_INPUT"},
            "desired": {"code": "WRONG_CHAIN", "note": "or document the distinction explicitly in CLI_EXIT_CODES.md"},
            "test_specification": "assert an exact code for all non-196 chain values and add exact-code assertions to test_wrong_chain.",
            "status": "SPEC_ONLY_NOT_PASSING_AGAINST_FROZEN_M1",
            "requires_contract_revision": False,
        },
    ]
    for case in cases:
        case["frozen_schema_modified"] = False
        case["claim"] = "Specification derived from review evidence; not an integrated test result."
    return {
        "schema": "flip-m2-adversarial/m1-regressions/1",
        "purpose": "Regression specifications for M1 review findings; Codex-owned contracts remain frozen",
        "generated_by": "docs/evidence/m2-adversarial/build_corpus.py (stdlib only)",
        "case_count": len(cases),
        "cases": cases,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    vectors_sha = sha256(ARCHIVED_VECTORS)
    negatives_sha = sha256(ARCHIVED_NEGATIVES)
    manifest_doc = json.loads(ARCHIVED_MANIFEST.read_text(encoding="utf-8"))
    xor = manifest_doc["manifests"][0]
    pinned = {
        "beacon": xor["beacon"],
        "beaconImplementation": xor["beaconImplementation"],
        "factory": xor["factory"],
        "factoryImplSlot": xor["factoryImplSlot"],
        "factoryImplAddress": xor["factoryImplAddress"],
    }

    outputs = [
        dump("tap02-malformed.json", build_tap02(vectors_sha)),
        dump("rpc-failures.json", build_rpc(pinned)),
        dump("integrity-negatives.json", build_integrity(negatives_sha, pinned)),
        dump("m1-regressions.json", build_m1_regressions()),
    ]
    manifest = {
        "schema": "flip-m2-adversarial/manifest/1",
        "generated_by": "docs/evidence/m2-adversarial/build_corpus.py",
        "generator_sha256": sha256(Path(__file__)),
        "deterministic": True,
        "note": "SHA-256 over exact file bytes; no embedded credentials; all synthetic cases explicitly labelled.",
        "artifacts": [
            {"path": f"fixtures/m2-adversarial/{p.name}", "bytes": p.stat().st_size, "sha256": sha256(p)}
            for p in outputs
        ],
    }
    dump("MANIFEST.json", manifest)
    print(json.dumps({"written": [str(p.relative_to(WT)) for p in outputs] + ["fixtures/m2-adversarial/MANIFEST.json"],
                      "artifacts": manifest["artifacts"]}, indent=2))


if __name__ == "__main__":
    main()
