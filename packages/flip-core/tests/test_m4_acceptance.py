"""Execute independent M4 assets without rewriting historical evidence."""

import importlib.util
import json
import shlex
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from flip_api.app import _slots, app
from flip_cli.main import main as cli
from flip_core.canonical import canonical_bytes, content_hash
from flip_core.verification import engine_identity, execute
from flip_core.workflow import product, sample
from test_m2_import import FakeChain, identity

ROOT = Path(__file__).resolve().parents[3]
FIX = ROOT / "fixtures/m4-ux-acceptance"
CASES = json.loads((FIX / "cli-cases/CASES.json").read_bytes())["executed"]


def evidence(record_property, case, expected, actual, boundary):
    record_property(
        "m4_case", json.dumps(dict(id=case, expected=expected, actual=actual, boundary=boundary))
    )


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_independent_cli(case, tmp_path, capsysbinary, record_property, monkeypatch):
    id = case["id"]
    args = shlex.split(case["command"].replace("\\", "/"))[1:]
    expected = case["exitCode"]
    server = None
    if id == "C29":
        values = [
            execute(
                "compose", (FIX / "cli-cases/requests/half-adder-equivalent.json").read_bytes()
            )["netlist"]
            for _ in range(100)
        ]
        assert len(set(values)) == 1 and len(bytes.fromhex(values[0][2:])) == 81
        evidence(
            record_property,
            id,
            "100 identical 81-byte builds",
            "100 identical 81-byte builds",
            "production composer x100",
        )
        return
    if id in ("C27", "C28", "C30"):
        module = load_module("m4_double", FIX / "generators/run_local_double_cases.py")
        chain = module.NotFoundChain() if id == "C28" else FakeChain()
        if id == "C30":
            manifest = chain.service().import_circuit(identity()).manifest
            path = tmp_path / "manifest.json"
            path.write_bytes(canonical_bytes(manifest))
            args[args.index("--manifest") + 1] = str(path)
            chain.beacon_impl = "0x" + "cd" * 20
        server, thread = module.serve(chain)
        args[args.index("--rpc-url") + 1] = f"http://127.0.0.1:{server.server_port}"
    if id == "C18":
        monkeypatch.setenv("FLIP_RPC_URL", "http://127.0.0.1:1")
        monkeypatch.setenv("FLIP_RPC_RETRIES", "0")
        expected = 2
    if id == "C19":
        expected = 0
    # Captured native/source hashes are historical and platform-specific.
    if id in ("C22", "C26"):
        captured = json.loads((ROOT / args[args.index("--project") + 1]).read_bytes())
        expected = (
            case["exitCode"] if captured["claimedResult"]["engine"] == engine_identity() else 7
        )
    try:
        try:
            actual = cli(args)
        except SystemExit as exc:
            actual = exc.code
        value = capsysbinary.readouterr().out
        assert actual == expected, (id, value)
        if id not in ("C01", "C02"):
            value = json.loads(value)
            if id in ("C22", "C26"):
                if expected == 7:
                    assert value["error"]["code"] == "IMPLEMENTATION_CHANGED"
                claim = json.loads((ROOT / args[args.index("--project") + 1]).read_bytes())
                claim["claimedResult"] = execute("compare", claim["executionRequest"])
                path = tmp_path / "adapted.json"
                path.write_bytes(canonical_bytes(claim))
                assert cli(["consume", "--project", str(path)]) == (0 if id == "C22" else 1)
            elif id not in ("C18", "C19"):
                semantic = case["semantic"]
                if "errorCode" in semantic:
                    assert value["error"]["code"] == semantic["errorCode"]
                if "verdict" in semantic:
                    assert (
                        value.get("report", {})
                        .get("verification", {})
                        .get("verdict", value.get("verdict"))
                        == semantic["verdict"]
                    )
        evidence(
            record_property,
            id,
            f"exit {expected}",
            f"exit {actual}",
            "CLI main; local double imports; historical engine binding and current replay",
        )
    finally:
        if server:
            server.shutdown()
            server.server_close()
            thread.join(5)


def test_custody_and_neutral_regeneration(record_property):
    source = "52814f5cef02716f4a9e49842ae520cdf7937a31"
    paths = (
        subprocess.check_output(["git", "diff", "--name-only", source + "^", source], cwd=ROOT)
        .decode()
        .splitlines()
    )
    assert len(paths) == 100
    for path in paths:
        assert path.startswith(("fixtures/m4-ux-acceptance/", "docs/evidence/m4-ux-acceptance/"))
        assert (ROOT / path).read_bytes() == subprocess.check_output(
            ["git", "show", source + ":" + path], cwd=ROOT
        )
    module = load_module("m4_register", FIX / "generators/verify_fixtures.py")
    module.regeneration_check()
    for name in json.loads((FIX / "cli-cases/requests/SOURCES.json").read_bytes())["derivations"]:
        evidence(
            record_property,
            "N-" + name,
            "exact scratch regeneration",
            "exact scratch regeneration",
            "independent generator",
        )


@pytest.mark.parametrize(
    "attack",
    [
        "verdict",
        "witness",
        "project",
        "reference",
        "manifest",
        "current",
        "engine",
        "different-project",
        "corrupt",
        "closure",
    ],
)
def test_bundle_attacks(attack, record_property, monkeypatch):
    monkeypatch.setenv("FLIP_LOCAL_SOLVER", "1")
    request = sample("swapped")
    body = dict(kind="PRODUCT_REQUEST", schemaVersion="m4-1.0.0", executionRequest=request)
    bundle = product("export", body)
    claim = bundle["comparison"]
    if attack == "verdict":
        claim["report"]["verification"].update(
            verdict="EQUIVALENT", solverOutcome="UNSAT", witness=None
        )
    if attack == "witness":
        claim["report"]["verification"]["witness"]["inputs"]["bits"] = "11"
    if attack == "project":
        claim["report"]["projectHash"] = "0x" + "ff" * 32
    if attack == "reference":
        claim["referenceIdentity"]["netlistHash"] = "0x" + "ff" * 32
    if attack == "manifest":
        claim["report"]["candidateManifestHash"] = "0x" + "ff" * 32
    if attack == "current":
        claim["report"]["integrity"] = {
            "freshness": "CURRENT",
            "checkedBlock": request["imports"][0]["manifest"]["block"],
        }
    if attack == "engine":
        claim["engineHash"] = "0x" + "ff" * 32
    if attack == "different-project":
        body["executionRequest"] = sample("half-adder")
    if attack == "corrupt":
        bundle["schemaVersion"] = "unsupported"
    if attack == "closure":
        body["executionRequest"]["imports"][0]["circuits"] = []
    bundle.pop("contentHash")
    bundle["contentHash"] = content_hash(bundle)
    response = TestClient(app, client=("127.0.0.1", 1)).post(
        "/api/v1/verify-bundle", json={**body, "bundle": bundle}
    )
    assert response.status_code == 422
    assert "report" not in response.json()
    evidence(
        record_property,
        "T-" + attack,
        "reject without proof",
        response.json(),
        "HTTP -> product -> trusted consumer",
    )


def test_concurrency_closed(record_property, monkeypatch):
    monkeypatch.setenv("FLIP_LOCAL_SOLVER", "1")
    assert _slots.acquire(False) and _slots.acquire(False)
    try:
        response = TestClient(app, client=("127.0.0.1", 1)).post(
            "/api/v1/compare", json=sample("half-adder")
        )
        assert response.status_code == 429
    finally:
        _slots.release()
        _slots.release()
    evidence(
        record_property,
        "S-concurrency",
        "429 RESOURCE_LIMIT",
        response.json(),
        "real shared semaphore",
    )


@pytest.mark.parametrize("operation", ["export", "verify-bundle"])
def test_planned_product_cases(operation, record_property):
    request = sample("half-adder")
    body = dict(kind="PRODUCT_REQUEST", schemaVersion="m4-1.0.0", executionRequest=request)
    bundle = product("export", body)
    if operation == "verify-bundle":
        actual = product(operation, {**body, "bundle": bundle})["report"]["verification"]["verdict"]
        id = "P03"
    else:
        actual = bundle["comparison"]["report"]["verification"]["verdict"]
        id = "P02"
    assert actual == "EQUIVALENT"
    evidence(
        record_property,
        id,
        "EQUIVALENT historical JSON evidence",
        actual,
        "M4 JSON format replaces planned ZIP; caller pins project",
    )


def test_planned_sample(record_property):
    assert cli(["sample", "half-adder"]) == 0
    evidence(
        record_property,
        "P04",
        "explicit historical sample",
        "emitted sample",
        "CLI requires explicit variant",
    )


def test_historical_preflight_fixture(record_property):
    from flip_core.preflight import classify

    value = json.loads((ROOT / "docs/milestones/M4_A_LIVE_PREFLIGHT.json").read_bytes())
    assert classify(bytes.fromhex(value["observation"]["revertData"][2:]), 1) == (
        "STRUCTURALLY_ACCEPTED",
        None,
        "KNOWN_BURN_STAGE",
    )
    assert value["observation"]["block"] == value["integrity"]["checkedBlock"]
    assert value["observation"]["feeWei"] == "1300000000000000"
    evidence(
        record_property,
        "P01",
        "strict historical burn decode",
        "STRUCTURALLY_ACCEPTED at recorded block 76234348",
        "archived M4-A observation; no fresh RPC",
    )


@pytest.mark.parametrize(
    "case,change",
    [
        ("E03", lambda r: r["project"]["comparison"].update(outputMap=[0, 2])),
        ("E07", lambda r: r["project"]["limits"].update(gateCap=1)),
        (
            "E08",
            lambda r: r["project"]["comparison"].update(
                intent="TRUSTED_REFERENCE", trustAssertion=None
            ),
        ),
    ],
)
def test_error_requests(case, change, record_property):
    value = sample("half-adder")
    change(value)
    response = TestClient(app).post("/api/v1/compose", json=value)
    assert response.status_code in (422, 429)
    assert "report" not in response.json()
    evidence(
        record_property,
        case,
        "structured rejection",
        response.json(),
        "actual composer API boundary",
    )
