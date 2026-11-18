"""Task A extension: circuit identity / manifest hash substitution against compare."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import review_common as rc  # noqa: E402
from flip_core.contracts import ContractError  # noqa: E402


def attempt(name, mutate):
    req = mutate(rc.base_request())
    try:
        out = rc.run("compare", req)
        return {"case": name, "outcome": "ACCEPTED",
                "verdict": out["report"]["verification"]["verdict"], "SAFE": False}
    except ContractError as exc:
        return {"case": name, "outcome": "REJECTED", "code": exc.code,
                "message": exc.message, "SAFE": True}
    except Exception as exc:  # noqa: BLE001
        return {"case": name, "outcome": "ERROR",
                "detail": "%s: %s" % (type(exc).__name__, exc), "SAFE": False}


def swap_netlist(req):
    r = copy.deepcopy(req)
    # Keep XOR#1 identity/hash pinned but supply NAND#2 bytes instead.
    r.imports[0].circuits[0].netlist = r.imports[1].circuits[0].netlist
    return r


def alter_manifest_hash(req):
    r = copy.deepcopy(req)
    r.imports[0].manifest.root.netlistHash = "0x" + "ab" * 32
    return r


def alter_processor(req):
    r = copy.deepcopy(req)
    r.project.sources[0].identity.processor = "0x" + "12" * 20
    return r


def alter_manifest_hash_field(req):
    r = copy.deepcopy(req)
    r.project.sources[0].manifestHash = "0x" + "cd" * 32
    return r


def main():
    rows = [
        attempt("swap_imported_netlist_bytes", swap_netlist),
        attempt("alter_manifest_root_netlist_hash", alter_manifest_hash),
        attempt("alter_project_source_processor", alter_processor),
        attempt("alter_project_source_manifest_hash", alter_manifest_hash_field),
    ]
    out = {"schema": "flip-m3-independent-identity-review/1",
           "commit": "59751e20590117f0cbc4ef41b9b30d836e533f84",
           "cases": rows, "all_safe": all(r.get("SAFE") for r in rows)}
    (HERE / "identity-attacks.json").write_text(
        json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
