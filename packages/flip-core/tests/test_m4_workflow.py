"""Offline acceptance for the new product boundary and structural observation."""

import copy
import json

import httpx
import pytest
from fastapi.testclient import TestClient
from flip_api.app import app
from flip_cli.main import main
from flip_core import preflight as pf
from flip_core.canonical import canonical_bytes, content_hash
from flip_core.contracts import ContractError
from flip_core.rpc import READ_METHODS, RpcSettings
from flip_core.verification import parse_request
from flip_core.workflow import product, sample
from test_m2_import import FakeChain, identity


def body(request):
    return dict(kind="PRODUCT_REQUEST", schemaVersion="m4-1.0.0", executionRequest=request)


@pytest.mark.parametrize("variant,code", [("half-adder", 0), ("swapped", 1)])
def test_product_roundtrip(variant, code, tmp_path, capsysbinary, monkeypatch):
    monkeypatch.setenv("FLIP_LOCAL_SOLVER", "1")
    client = TestClient(app, client=("127.0.0.1", 1))
    project, artifact = tmp_path / "project.json", tmp_path / "evidence.json"
    assert main(["sample", variant, "--out", str(project)]) == 0
    assert client.get("/api/v1/sample/" + variant).content == project.read_bytes().strip()
    assert main(["export", "--project", str(project), "--out", str(artifact)]) == code
    saved = json.loads(artifact.read_bytes())
    request = body(json.loads(project.read_bytes()))
    web = client.post("/api/v1/export", json=request).json()
    assert saved["comparison"]["report"] == web["comparison"]["report"]
    assert main(["verify-bundle", "--project", str(project), "--bundle", str(artifact)]) == code
    result = client.post("/api/v1/verify-bundle", json={**request, "bundle": saved})
    assert result.json()["report"] == saved["comparison"]["report"]
    assert result.json()["report"]["integrity"]["freshness"] == "HISTORICAL"
    assert main(["inspect-evidence", "--bundle", str(artifact)]) == 0
    inspected = json.loads(capsysbinary.readouterr().out.splitlines()[-1])
    assert inspected["trust"] == "UNVERIFIED_FILE_CLAIMS"
    assert saved["chainObservation"] is None
    assert artifact.read_bytes() == canonical_bytes(saved) + b"\n"


def test_bundle_recomputed_against_independent_project():
    request = body(sample("swapped"))
    bundle = product("export", request)
    different = body(sample("half-adder"))
    with pytest.raises(ContractError):
        product("verify-bundle", {**different, "bundle": bundle})
    bundle["comparison"]["report"]["candidateManifestHash"] = "0x" + "00" * 32
    bundle.pop("contentHash")
    bundle["contentHash"] = content_hash(bundle)
    with pytest.raises(ContractError):
        product("verify-bundle", {**request, "bundle": bundle})


@pytest.mark.parametrize("operation", ["export", "verify-bundle"])
def test_public_or_disabled_native_rejected(operation, monkeypatch):
    path = "/api/v1/" + operation
    data = body(sample("half-adder"))
    monkeypatch.setenv("FLIP_LOCAL_SOLVER", "1")
    assert TestClient(app).post(path, json=data).status_code == 501
    monkeypatch.delenv("FLIP_LOCAL_SOLVER")
    assert TestClient(app, client=("127.0.0.1", 1)).post(path, json=data).status_code == 501
    assert TestClient(app).post(path, content=b"x" * 1_048_577).status_code == 413


def burn(sender=int(pf.CALLER, 16), balance=0, needed=1, token=0):
    return bytes.fromhex("03dee4c5") + b"".join(
        pf.word(v) for v in (sender, balance, needed, token)
    )


@pytest.mark.parametrize(
    "data",
    [b"", burn()[:4], burn() + b"\x00", burn(1), burn(balance=1), burn(needed=2), burn(token=1)],
)
def test_unrecognized_burn_is_inconclusive(data):
    assert pf.classify(data, 1)[0] == "UNKNOWN"


@pytest.mark.parametrize(
    "case,status,reason",
    [
        ("burn", "STRUCTURALLY_ACCEPTED", None),
        ("structural", "REJECTED", "STRUCTURAL_REJECTION"),
        ("empty", "UNKNOWN", "UNRECOGNIZED_REVERT"),
        ("success", "UNKNOWN", "UNRECOGNIZED_REVERT"),
        ("rpc", "UNKNOWN", "RPC_UNAVAILABLE"),
        ("stale", "UNKNOWN", "IMPLEMENTATION_CHANGED"),
        ("chain", "UNKNOWN", "WRONG_CHAIN"),
        ("implementation", "UNKNOWN", "IMPLEMENTATION_CHANGED"),
        ("reorg", "UNKNOWN", "IMPLEMENTATION_CHANGED"),
    ],
)
def test_preflight_transport(case, status, reason, monkeypatch):
    chain = FakeChain()
    request = sample("half-adder")
    for idx, cid in enumerate((1, 2)):
        artifact = chain.service().import_circuit(identity(cid))
        request["imports"][idx] = artifact.model_dump(mode="json")
        request["project"]["sources"][idx]["manifestHash"] = artifact.manifestHash
    env = artifact.manifest.root.environment
    # Synthetic bytecode is isolated to this fixture. Production pins the reviewed code.
    if case != "implementation":
        monkeypatch.setattr(pf, "IMPLEMENTATION", env.beaconImplementation.codeHash)
    monkeypatch.setattr(pf, "PROXY", env.processorCodeHash)
    if case == "stale":
        chain.factory_impl = "0x" + "dd" * 20
    if case == "chain":
        chain.chain_id = 1
    calls = []

    def handle(req):
        payload = json.loads(req.content)
        method, params = payload["method"], payload["params"]
        assert method in READ_METHODS
        calls.append((method, params))
        reply = {"jsonrpc": "2.0", "id": payload["id"]}
        data = params[0]["data"] if method == "eth_call" else ""
        if data == "0xadfb2b69":
            assert params[1] == "0x64"
            reply["result"] = "0x" + pf.word(1234).hex()
        elif data.startswith("0x7bd3ac1d"):
            assert params[0]["value"] == hex(1234) and params[0]["from"] == pf.CALLER
            assert params[1:] == ["0x64", {pf.CALLER: {"balance": hex(1234)}}]
            encoded = bytes.fromhex(data[10:])
            assert encoded[:128] == b"".join(pf.word(v) for v in (96, 2, 2, 81))
            revert = burn()
            if case == "structural":
                revert = bytes.fromhex("08c379a0") + pf.word(32) + pf.abi_bytes(b"bad opcode")
            if case == "empty":
                revert = b""
            if case == "rpc":
                return httpx.Response(503)
            if case == "reorg":
                chain.reorg = True
                chain.headers = 1
            if case == "success":
                reply["result"] = {"revert": "0x" + burn().hex()}
            else:
                reply["error"] = {
                    "code": 3,
                    "message": "execution reverted",
                    "data": "0x" + revert.hex(),
                }
        else:
            return chain.handler(req)
        return httpx.Response(200, json=reply)

    result = pf.preflight(
        parse_request(request), RpcSettings(retries=0), httpx.MockTransport(handle)
    )
    assert (result["status"], result["reasonCode"]) == (status, reason)
    if status != "UNKNOWN":
        assert result["observation"]["feeWei"] == "1234"
        assert result["observation"]["block"] == result["integrity"]["checkedBlock"]
    if case in ("stale", "implementation", "chain"):
        assert not any(m == "eth_call" and p[0]["data"] == "0xadfb2b69" for m, p in calls)


def test_new_project_import_only():
    item = sample("half-adder")["imports"][0]
    value = dict(kind="PRODUCT_REQUEST", schemaVersion="m4-1.0.0", source=item)
    request = product("new-project", value)
    assert request["project"]["sources"][0]["manifestHash"] == item["manifestHash"]
    forged = copy.deepcopy(value)
    forged["source"]["manifest"]["root"]["nIn"] = 1
    assert TestClient(app).post("/api/v1/new-project", json=forged).status_code == 422
    stateful = FakeChain().service().import_circuit(identity(4))
    with pytest.raises(ContractError, match="stateless"):
        product("new-project", {**value, "source": stateful.model_dump(mode="json")})


def test_local_service_transport_boundary(tmp_path, monkeypatch):
    from flip_api import local

    (tmp_path / "index.html").write_text("Flip", encoding="utf-8")
    monkeypatch.setattr(local, "DIST", tmp_path)
    service = local.application()
    url = "http://127.0.0.1:8000"
    remote = TestClient(service, base_url=url, client=("192.0.2.1", 443))
    assert remote.get("/healthz").status_code == 403
    client = TestClient(service, base_url=url, client=("127.0.0.1", 4000))
    assert client.get("/", headers={"Host": "other.invalid"}).status_code == 400
    assert client.get("/", headers={"Origin": "https://other.invalid"}).status_code == 403
    assert client.get("/", headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    response = client.get("/", headers={"Origin": url})
    assert (
        response.text == "Flip"
        and "frame-ancestors 'none'" in response.headers["content-security-policy"]
    )


def test_invalid_rpc_config_is_inconclusive(monkeypatch):
    monkeypatch.setenv("FLIP_RPC_TIMEOUT_MS", "invalid")
    result = product("preflight", body(sample("half-adder")))
    assert (result["status"], result["reasonCode"]) == ("UNKNOWN", "RPC_UNAVAILABLE")
