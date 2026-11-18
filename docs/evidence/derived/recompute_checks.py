"""Bounded, read-only re-derivation of provenance checks from committed raw fixtures.

No network, no RPC, no product code. Run from any CWD:
    python docs/evidence/derived/recompute_checks.py
"""

import hashlib
import json
import os

WT = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
)
RAW0 = os.path.join(WT, "docs", "evidence", "raw", "M0")
RAW5 = os.path.join(WT, "docs", "evidence", "raw", "M05")


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def sha_hex(hex_string):
    raw = bytes.fromhex(hex_string[2:] if hex_string.startswith("0x") else hex_string)
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    xl = load(os.path.join(RAW0, "xlayer_circuits.json"))
    cp = load(os.path.join(RAW0, "composition_poc.json"))
    wc = load(os.path.join(RAW0, "wiring_canary.json"))
    gb = load(os.path.join(RAW5, "gate_b_manifest.json"))
    gn = load(os.path.join(RAW5, "gate_b_negative.json"))
    cs = load(os.path.join(RAW5, "gate_c_scale.json"))
    st = load(os.path.join(RAW5, "gate_c_stateful.json"))
    ap2 = load(os.path.join(RAW5, "gate_a_probe2.json"))

    samples = xl["processors"]["0x839BDD6fA7A66416a609A735E11DE5411b98574E"]["sample"]
    xor1 = next(r["netlist"] for r in samples if r["circuitId"] == 1)
    nand2 = next(r["netlist"] for r in samples if r["circuitId"] == 2)

    xor_recomp = sha_hex(xor1)
    nand_recomp = sha_hex(nand2)
    comp_recomp = sha_hex(cp["composedNetlist"])

    scale_cases = sum(len(s["cases"]) for s in cs["scales"])

    result = {
        "label": "READ_ONLY_REGENERATED",
        "generated_by": "bounded local python re-derivation of committed raw fixtures; no network/RPC/product code",
        "chain_block_provenance": {
            "xlayer_circuits": {
                "rpc": xl["rpc"],
                "chainId": xl["chainId"],
                "headBlock": xl["headBlock"],
                "generated_utc": xl["generated_utc"],
            },
            "gate_b_manifest": {
                "rpcX": gb["rpcX"],
                "chainIdX": gb["chainIdX"],
                "blockNumberX": gb["blockNumberX"],
                "blockHashX": gb["blockHashX"],
                "tap02Version": gb["tap02Version"],
                "testSuiteHash": gb["testSuiteHash"],
            },
        },
        "recomputed_netlist_digests": {
            "xor1": {
                "source_netlist": xor1,
                **xor_recomp,
                "recorded_netlistSha256": cp["sources"][0]["netlistSha256"],
                "match": xor_recomp["sha256"] == cp["sources"][0]["netlistSha256"],
            },
            "nand2": {
                "source_netlist": nand2,
                **nand_recomp,
                "recorded_netlistSha256": cp["sources"][1]["netlistSha256"],
                "match": nand_recomp["sha256"] == cp["sources"][1]["netlistSha256"],
            },
            "composed_half_adder": {
                "source_netlist": cp["composedNetlist"],
                **comp_recomp,
                "recorded_composedNetlistBytes": cp["composedNetlistBytes"],
                "match_bytes": comp_recomp["bytes"] == cp["composedNetlistBytes"],
            },
        },
        "counts": {
            "wiring_mutation_cases": len(wc["rows"]),
            "wiring_scale_test_present": bool(wc.get("scaleTest")),
            "integrity_negative_cases": len(gn["negativeTests"]),
            "all_negative_detected": gn["allNegativeDetected"],
            "scale_target_counts": len(cs["scales"]),
            "scale_mode_cases": scale_cases,
            "correctness_safeguards": len(cs["correctnessSafeguards"]),
            "correctness_safeguards_all_passed": all(
                x["passed"] for x in cs["correctnessSafeguards"]
            ),
            "stateful_beats": st["beats"],
            "stateful_first_difference_beat": st["firstDifferenceBeat"],
            "stateful_reproducible": st["reproducible"],
        },
        "stateful_trace_matches_embedded_copy": (
            st["traceOriginal"] == cs["statefulKBeat"]["traceOriginal"]
            and st["traceMutant"] == cs["statefulKBeat"]["traceMutant"]
        ),
        "preflight_revert_evidence": {
            "revertArgDecode": ap2["revertArgDecode"],
            "tapeoutSimFull": ap2["tapeoutSimFull"],
            "overrideSupported": ap2["overrideSupported"],
        },
    }

    out_path = os.path.join(WT, "docs", "evidence", "derived", "recomputed_checks.json")
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print("wrote", out_path)
    print(json.dumps(result["counts"], indent=2))
    print(
        "recompute matches:",
        result["recomputed_netlist_digests"]["xor1"]["match"],
        result["recomputed_netlist_digests"]["nand2"]["match"],
        result["recomputed_netlist_digests"]["composed_half_adder"]["match_bytes"],
    )
    print(
        "stateful trace matches embedded copy:",
        result["stateful_trace_matches_embedded_copy"],
    )


if __name__ == "__main__":
    main()
