"""F-02 versioned provenance and legacy wire compatibility regressions."""

import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from flip_api.app import app
from flip_core import library_models_v1 as v1
from flip_core.canonical import canonical_bytes
from flip_core.library import LibraryService
from flip_core.library_models import (
    Catalog,
    Favorite,
    LibraryIdentity,
    LibraryRecord,
    LibraryRequest,
)
from flip_core.library_protocol import parse_library_request
from pydantic import ValidationError


def pointer():
    return LibraryIdentity(processor="0x" + "77" * 20, circuitId="77")


def favorite_request():
    return LibraryRequest(
        operation="favorite",
        identity=pointer(),
        metadata=Favorite(identity=pointer(), label="local-only"),
    )


def test_F02_pointer_has_user_provenance_and_no_onchain_evidence():
    result = LibraryService().execute(favorite_request())
    assert result.schemaVersion == "m45-library-1.1.0"
    row = result.results[0]
    assert row.metadataTrust == "USER_SUPPLIED"
    assert row.existence == "USER_POINTER" and row.sources == ["USER_FAVORITE_ONLY"]
    assert row.freshness == "UNKNOWN"
    assert row.block is row.environment is row.netlistHash is row.manifestHash is None
    assert result.rpcCallsUsed == 0 and result.imported is None
    with pytest.raises(ValidationError):
        LibraryRecord.model_validate(
            {**row.model_dump(mode="json"), "metadataTrust": "ONCHAIN_DISPLAY_ONLY"}
        )


@pytest.mark.parametrize("version", ["m45-library-1.0.0", "m45-library-1.1.0"])
def test_F02_cli_api_core_use_same_versioned_pointer_representation(tmp_path, version):
    req = favorite_request().model_dump(mode="json", exclude={"catalog"})
    req["schemaVersion"] = version
    expected = LibraryService().execute(parse_library_request(req)).model_dump(mode="json")
    with TestClient(app) as client:
        response = client.post("/api/library/v1/execute", json=req)
        assert response.status_code == 200 and response.json() == expected
    path = tmp_path / "request.json"
    path.write_bytes(canonical_bytes(req))
    completed = subprocess.run(
        [sys.executable, "-m", "flip_cli", "library", "--request", str(path)], capture_output=True
    )
    assert completed.returncode == (2 if version == v1.VERSION else 0)
    assert json.loads(completed.stdout) == expected


def test_frozen_v1_cannot_encode_user_trust_and_returns_explicit_upgrade_status():
    assert isinstance(parse_library_request({"operation": "search"}), v1.LibraryRequest)
    request = parse_library_request(
        {
            "schemaVersion": v1.VERSION,
            "operation": "favorite",
            "identity": pointer().model_dump(mode="json"),
        }
    )
    result = LibraryService().execute(request)
    assert isinstance(result, v1.LibraryResult)
    assert result.schemaVersion == v1.VERSION
    assert result.status == "UNKNOWN" and result.errorCode == "UNSUPPORTED_SCHEMA_VERSION"
    assert result.results == []
    assert result.catalog.overlay.favorites[0].identity.processor == pointer().processor
    v1.LibraryResult.model_validate(result.model_dump(mode="json"))
    old_row = LibraryRecord(
        identity=pointer(),
        sources=["USER_FAVORITE_ONLY"],
        existence="USER_POINTER",
        metadataTrust="USER_SUPPLIED",
    )
    with pytest.raises(ValidationError):
        v1.LibraryRecord.model_validate(old_row.model_dump(mode="json"))
    # The old response schema remains usable for onchain/known-address records.
    plain = LibraryService().execute(
        parse_library_request({"schemaVersion": v1.VERSION, "operation": "search"})
    )
    assert plain.status == "COMPLETE" and plain.results
    assert all(r.metadataTrust == "ONCHAIN_DISPLAY_ONLY" for r in plain.results)


def test_known_catalog_migration_preserves_pointers_and_rejects_unknown_authority():
    old = v1.Catalog()
    old.overlay.favorites.append(
        v1.Favorite(
            identity=v1.LibraryIdentity(**pointer().model_dump(mode="json")), label="old favorite"
        )
    )
    old.records.append(
        v1.LibraryRecord(
            identity=old.overlay.favorites[0].identity,
            sources=["USER_FAVORITE_ONLY"],
            existence="USER_POINTER",
        )
    )
    raw = old.model_dump(mode="json")
    original = canonical_bytes(raw)
    upgraded = Catalog.model_validate(raw)
    assert canonical_bytes(raw) == original
    assert upgraded.schemaVersion == "m45-library-1.1.0"
    assert upgraded.records[0].metadataTrust == "USER_SUPPLIED"
    assert upgraded.overlay.favorites[0].label == "old favorite"
    raw["overlay"]["favorites"][0]["permissions"] = ["SIGN"]
    with pytest.raises(ValidationError):
        Catalog.model_validate(raw)
