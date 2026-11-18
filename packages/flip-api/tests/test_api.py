import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from flip_api.app import MAX_BODY_BYTES, app
from flip_core.canonical import canonical_bytes
from flip_core.contracts import validate_contract

ROOT = Path(__file__).resolve().parents[3]
client = TestClient(app)


@pytest.mark.parametrize(
    "operation", ["import", "compose", "compare", "revalidate", "preflight", "export"]
)
def test_product_operations_do_not_claim_results(operation):
    response = client.post(f"/api/v1/{operation}", json={"anything": "not executed"})
    assert response.status_code == 501
    assert response.json()["error"]["code"] == "NOT_IMPLEMENTED"
    assert "verification" not in response.json()


@pytest.mark.parametrize(
    "kind",
    ["circuit-identity", "project", "manifest", "comparison-report", "preflight", "error-envelope"],
)
def test_contract_api_parity(kind):
    data = (ROOT / f"docs/schema/examples/{kind}.json").read_bytes()
    response = client.post(f"/api/v1/contracts/{kind}/validate", content=data)
    assert response.status_code == 200
    assert response.content == canonical_bytes(validate_contract(kind, data))


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("chainId", 8453, "WRONG_CHAIN"),
        ("schemaVersion", "2.0.0", "UNSUPPORTED_SCHEMA_VERSION"),
    ],
)
def test_contract_api_error(field, value, code):
    data = json.loads((ROOT / "docs/schema/examples/circuit-identity.json").read_bytes())
    data[field] = value
    response = client.post("/api/v1/contracts/circuit-identity/validate", json=data)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == code


def test_malformed_and_body_limit():
    response = client.post("/api/v1/contracts/project/validate", content=b"{")
    assert response.status_code == 422
    response = client.post(
        "/api/v1/contracts/project/validate", content=b"x" * (MAX_BODY_BYTES + 1)
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "RESOURCE_LIMIT"


def test_health_is_only_liveness():
    assert client.get("/healthz").json() == {"status": "M1_CONTRACTS_ONLY"}
    assert client.get("/openapi.json").status_code == 200
