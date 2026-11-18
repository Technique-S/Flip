"""Generate concrete request files used by CLI/API checks (owned fixture path)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import review_common as rc  # noqa: E402

REQ = HERE / "requests"
REQ.mkdir(exist_ok=True)


def dump(name, value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    (REQ / name).write_bytes(data)
    return len(data)


def main():
    base = rc.base_request()
    eq = rc.run("compare", base)
    diff_req = rc.swap_outputs(base)
    diff = rc.run("compare", diff_req)

    sizes = {}
    sizes["valid_equivalent.json"] = dump("valid_equivalent.json", base.model_dump(mode="json"))
    sizes["valid_different.json"] = dump("valid_different.json", diff_req.model_dump(mode="json"))

    valid_consume = rc.consume_request(base, eq)
    sizes["valid_consume.json"] = dump("valid_consume.json", valid_consume)

    # Forge an EQUIVALENT claim from a genuinely DIFFERENT execution result.
    forged = rc.consume_request(diff_req, diff)
    v = forged["claimedResult"]["report"]["verification"]
    v["verdict"] = "EQUIVALENT"
    v["solverOutcome"] = "UNSAT"
    v["reasonCode"] = None
    v["witness"] = None
    sizes["forged_equivalent_consume.json"] = dump(
        "forged_equivalent_consume.json", forged)

    # A frozen v1 comparison report: schema-valid shape, no additive M3 kind.
    frozen = json.loads((rc.REPO / "docs/schema/examples/comparison-report.json").read_text())
    sizes["frozen_v1_report.json"] = dump("frozen_v1_report.json", frozen)

    # Malformed proof: claimed verdict inconsistent with solver outcome.
    bad = copy.deepcopy(valid_consume)
    bad["claimedResult"]["report"]["verification"]["solverOutcome"] = "NOT_RUN"
    sizes["invalid_proof_shape.json"] = dump("invalid_proof_shape.json", bad)

    print(json.dumps(sizes, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
