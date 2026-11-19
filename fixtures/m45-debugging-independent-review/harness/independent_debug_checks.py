"""Independent verification of production M4.5-2D diagnostics.

Uses the OpenCode M4.5-2D stdlib evaluator (debug_core) on the exact netlist bytes
pinned in the request; never takes the production comparator as the expected oracle.
Also drives the production CLI for diagnose/verify-correction and adversarial requests.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVID = ROOT / "docs/evidence/m45-debugging-independent-review"
RUN = EVID / "results/run"
sys.path.insert(0, str(ROOT / "fixtures/m45-debugging/generators"))
import debug_core as dc  # noqa: E402

FLIP = str(ROOT / ".venv/Scripts/flip.exe")
OUT = EVID / "results/independent-debug-checks.json"


def load_bank(request):
    bank = {}
    for imp in request["executionRequest"]["imports"]:
        for circuit in imp["circuits"]:
            key = (circuit["identity"]["processor"].removeprefix("0x"),
                   int(circuit["identity"]["circuitId"]))
            bank[key] = (2, 1, bytes.fromhex(circuit["netlist"][2:]))
    return bank


def design_elements(design, sources):
    """Mirror the compiler's explicit component order and signal numbering."""
    els, signal = [], 2 + design["nIn"]

    def pin_source(pin):
        return 2 + pin["pin"] if pin["component"] is None else -1  # resolved by caller

    for component in design["components"]:
        ins = []
        for pin in component["inputs"]:
            if pin["component"] is None:
                ins.append(2 + pin["pin"])
            else:
                # Previous component's single output signal.
                idx = next(i for i, c in enumerate(design["components"])
                           if c["instanceId"] == pin["component"])
                ins.append(2 + design["nIn"] + idx)
        if component["kind"] == "REF":
            alias = component["sourceAlias"]
            source = sources[alias]
            els.append(dc.ref(source[0].removeprefix("0x"), source[1], ins, 1))
        else:
            els.append(dc.nand(*ins))
        signal += 1
    return els, signal


def evaluate(request, design_name):
    project = request["executionRequest"]["project"]
    design = project[design_name]
    sources = {s["alias"]: (s["identity"]["processor"], int(s["identity"]["circuitId"]))
               for s in project["sources"]}
    els, end = design_elements(design, sources)
    bank = load_bank(request)
    circuit = dc.load(dc.encode(els), design["nIn"], len(design["outputs"]), bank)
    out_signals = {}
    for component in design["components"]:
        idx = next(i for i, c in enumerate(design["components"])
                   if c["instanceId"] == component["instanceId"])
        out_signals[component["instanceId"]] = 2 + design["nIn"] + idx
    omap = [out_signals[o["component"]] + o["pin"] for o in design["outputs"]]
    return dc.exhaustive(circuit, omap)


def run_cli(request_path, out_path, operation=None, action_id=None):
    payload = json.loads(request_path.read_bytes())
    if operation:
        payload["operation"] = operation
    if action_id is not None:
        payload["actionId"] = action_id
    path = request_path.with_name(request_path.stem + ".variant.json")
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    env = dict(os.environ, FLIP_LOCAL_SOLVER="1")
    proc = subprocess.run([FLIP, "debug", "--request", str(path), "--out", str(out_path)],
                          cwd=ROOT, env=env, capture_output=True, timeout=120)
    result = None
    if out_path.exists():
        try:
            result = json.loads(out_path.read_bytes())
        except ValueError:
            result = None
    return {"exit": proc.returncode, "result": result,
            "stderrTail": proc.stderr.decode("utf-8", "replace")[-200:]}


def main():
    checks = []
    base_req = RUN / "base.request.json"
    request = json.loads(base_req.read_bytes())
    witness_req = json.loads((RUN / "base.result.json").read_bytes())
    witness = witness_req["comparison"]["report"]["verification"]["witness"]

    ref_table = evaluate(request, "referenceCandidate")
    cand_table = evaluate(request, "candidate")
    bits = [int(c) for c in witness["inputs"]["bits"]]
    packed = sum(bit << i for i, bit in enumerate(bits))
    independent_ref = ref_table[packed]["out"]
    independent_cand = cand_table[packed]["out"]
    expected_ref = [int(c) for c in witness["referenceOutputs"]["bits"]]
    expected_cand = [int(c) for c in witness["candidateOutputs"]["bits"]]
    differing = [i for i, (a, b) in enumerate(zip(independent_ref, independent_cand)) if a != b]
    checks.append({
        "id": "A01", "name": "Independent witness replay",
        "inputs": bits, "independentReference": independent_ref,
        "independentCandidate": independent_cand,
        "productionReference": expected_ref, "productionCandidate": expected_cand,
        "independentDifferingBits": differing,
        "productionDifferingBits": witness_req["differingOutputBits"],
        "passed": independent_ref == expected_ref and independent_cand == expected_cand
                  and differing == witness_req["differingOutputBits"],
    })

    # Structural cone membership: every connectionRef must name a real element/pin
    # in the compiled netlist produced by the independent `flip compose` command.
    execution = RUN / "base.execution.json"
    execution.write_text(json.dumps(request["executionRequest"], indent=2,
                                    sort_keys=True) + "\n", encoding="utf-8")
    compiled_path = RUN / "compiled.json"
    subprocess.run([FLIP, "compose", "--project", str(execution),
                    "--out", str(compiled_path)], cwd=ROOT, env=dict(os.environ,
                    FLIP_LOCAL_SOLVER="1"), capture_output=True, timeout=120)
    compiled = json.loads(compiled_path.read_bytes())
    top_els = dc.decode(bytes.fromhex(compiled["netlist"][2:]),
                        request["executionRequest"]["project"]["candidate"]["nIn"])
    bad = []
    for c in witness_req["connections"]:
        ref = c["connectionRef"]
        if ref.startswith("top/outputMap["):
            pin = int(ref.split("[")[1].split("]")[0])
            if pin >= len(request["executionRequest"]["project"]["candidate"]["outputs"]):
                bad.append(ref)
            continue
        if ref.startswith("top/element[") and c["path"] == "top":
            idx = int(ref.split("[")[1].split("]")[0])
            if idx >= len(top_els):
                bad.append(ref)
                continue
            element = top_els[idx]
            if ".in[" in ref:
                pin = int(ref.split(".in[")[1].split("]")[0])
                if pin >= len(element.ins):
                    bad.append(ref)
            continue
        if c["path"] != "top" and not c.get("sourceNetlistHash"):
            bad.append(ref)
    nested = sorted({c["path"] for c in witness_req["connections"] if c["path"] != "top"})
    nested_bound = all(c.get("sourceIdentity") is not None
                       for c in witness_req["connections"] if c["path"] != "top")
    checks.append({"id": "A02", "name": "Path-qualified connection membership",
                   "connectionCount": len(witness_req["connections"]),
                   "compiledElements": len(top_els),
                   "invalidRefs": bad, "nestedPaths": nested,
                   "nestedIdentitiesBound": nested_bound,
                   "passed": not bad and nested_bound})

    # Classification claims.
    checks.append({"id": "A03", "name": "Relevance vs fault claim",
                   "classification": witness_req["classification"],
                   "attribution": witness_req["attribution"],
                   "uniqueFaultClaim": witness_req["uniqueFaultClaim"],
                   "connectionClasses": sorted({c["classification"] for c in witness_req["connections"]}),
                   "passed": witness_req["uniqueFaultClaim"] is False
                             and all(c["classification"] == "RELEVANT_CONNECTION"
                                     for c in witness_req["connections"])})

    # EQUIVALENT -> no attribution: use the declared prior design as candidate.
    equiv = json.loads(json.dumps(request))
    equiv["executionRequest"]["project"]["candidate"] = json.loads(json.dumps(
        equiv["executionRequest"]["project"]["referenceCandidate"]))
    ep = RUN / "equivalent.request.json"
    ep.write_text(json.dumps(equiv, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    er = run_cli(ep, RUN / "equivalent.result.json")
    checks.append({"id": "A04", "name": "Equivalent design has no fault attribution",
                   "exit": er["exit"],
                   "classification": (er["result"] or {}).get("classification"),
                   "connections": len((er["result"] or {}).get("connections", [])),
                   "actions": len((er["result"] or {}).get("actions", [])),
                   "passed": (er["result"] or {}).get("classification") == "NO_FAULT_ATTRIBUTION"
                             and not (er["result"] or {}).get("connections")
                             and not (er["result"] or {}).get("actions")})

    # Forged / stale / wrong binding attacks.
    attacks = []
    forged = json.loads(json.dumps(request))
    forged["executionRequest"]["imports"][0]["circuits"][0]["netlist"] = "0x000000"
    fp = RUN / "attack-forged-netlist.request.json"
    fp.write_text(json.dumps(forged, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    fr = run_cli(fp, RUN / "attack-forged-netlist.result.json")
    attacks.append({"id": "B01", "name": "Forged netlist bytes",
                    "exit": fr["exit"], "classification": (fr["result"] or {}).get("classification"),
                    "reason": (fr["result"] or {}).get("reasonCode"),
                    "connections": len((fr["result"] or {}).get("connections", [])),
                    "outputExists": bool(fr["result"]),
                    "passed": fr["exit"] in (2, 3)
                              and (fr["result"] or {}).get("classification") in ("UNKNOWN", None)
                              and not (fr["result"] or {}).get("connections")
                              and not (fr["result"] or {}).get("correction")
                              and (fr["result"] or {}).get("correction") is None})

    stale = json.loads(json.dumps(request))
    for imp in stale["executionRequest"]["imports"]:
        imp["integrity"]["freshness"] = "STALE"
    sp = RUN / "attack-stale.request.json"
    sp.write_text(json.dumps(stale, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sr = run_cli(sp, RUN / "attack-stale.result.json")
    attacks.append({"id": "B02", "name": "Stale manifest freshness",
                    "exit": sr["exit"], "classification": (sr["result"] or {}).get("classification"),
                    "reason": (sr["result"] or {}).get("reasonCode"),
                    "passed": (sr["result"] or {}).get("classification") == "UNKNOWN"})

    forged_action = json.loads(json.dumps(request))
    forged_action["schemaVersion"] = "m45-debugging-1.0.0"
    forged_action["operation"] = "verify-correction"
    forged_action["actionId"] = "0x" + "00" * 32
    ap = RUN / "attack-forged-action.request.json"
    ap.write_text(json.dumps(forged_action, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ar = run_cli(ap, RUN / "attack-forged-action.result.json")
    attacks.append({"id": "B03", "name": "Forged actionId cannot grant correction",
                    "exit": ar["exit"], "classification": (ar["result"] or {}).get("classification"),
                    "correction": (ar["result"] or {}).get("correction"),
                    "passed": (ar["result"] or {}).get("correction") is None})

    # Genuine correction replay using the returned actionId.
    action_id = witness_req["actions"][0]["actionId"]
    gr = run_cli(base_req, RUN / "verified-correction.result.json",
                 operation="verify-correction", action_id=action_id)
    correction = (gr["result"] or {}).get("correction") or {}
    checks.append({"id": "A05", "name": "Verified correction replay",
                   "exit": gr["exit"], "classification": correction.get("classification"),
                   "scope": correction.get("scope"),
                   "revalidation": correction.get("revalidation"),
                   "passed": correction.get("classification") == "VERIFIED_CORRECTION"
                             and correction.get("scope") == "EXACT_STATELESS_SELECTED_REFERENCE_HISTORICAL"})

    record = {"artifactType": "INDEPENDENT_DEBUG_CHECK",
              "testedSha": "b9d3fc3f87d34cc6bd46e2a716504fe113f44f48",
              "independentCore": dc.CORE_VERSION,
              "checks": checks, "attacks": attacks,
              "passed": sum(1 for c in checks + attacks if c["passed"]),
              "total": len(checks) + len(attacks)}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    print(json.dumps({"passed": record["passed"], "total": record["total"],
                      "failures": [c["id"] for c in checks + attacks if not c["passed"]]},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
