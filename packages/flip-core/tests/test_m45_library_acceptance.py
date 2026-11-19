"""Codex acceptance reproductions; separate from immutable OpenCode review evidence."""

import pytest
from fastapi.testclient import TestClient
from flip_api.app import app
from flip_core import abi
from flip_core.library_models import Favorite
from pydantic import ValidationError
from test_m45_library import LibraryChain, identity, request


def test_alias_and_favorite_metadata_are_both_searchable():
    service = LibraryChain().library()
    alias = service.execute(
        request(
            "alias",
            identity=identity(cid="1"),
            metadata=Favorite(identity=identity(cid="1"), label="localalias", tags=["alias-tag"]),
        )
    )
    favorite = service.execute(
        request(
            "favorite",
            identity=identity(cid="1"),
            catalog=alias.catalog,
            metadata=Favorite(
                identity=identity(cid="1"),
                label="favorite-label",
                description="favorite description",
            ),
        )
    )
    for query in ("localalias", "alias-tag", "favorite-label", "favorite description"):
        found = service.execute(request("search", catalog=favorite.catalog, query=query))
        assert [r.identity for r in found.results] == [identity(cid="1")], query
    with TestClient(app) as client:
        result = client.post(
            "/api/library/v1/execute",
            json=request("search", catalog=favorite.catalog, query="localalias").model_dump(
                mode="json"
            ),
        )
        assert result.status_code == 200 and len(result.json()["results"]) == 1


def test_factory_refresh_invalidates_circuits_after_processor_code_changes():
    chain = LibraryChain()
    service = chain.library()
    prior = service.execute(request("circuits", identity=identity())).catalog
    prior = service.execute(request("favorite", identity=identity(cid="1"), catalog=prior)).catalog
    answer = chain.answer

    def changed_code(method, params):
        if method == "eth_getCode" and params[0] == identity().processor:
            return "0x60026000"
        return answer(method, params)

    chain.answer = changed_code
    result = service.execute(request("discover", catalog=prior))
    assert result.status == "ENVIRONMENT_CHANGED"
    assert result.errorCode == "IMPLEMENTATION_CHANGED"
    circuits = [r for r in result.catalog.records if r.environment and r.identity.circuitId]
    assert circuits and all(r.freshness == "STALE" for r in circuits)
    assert result.catalog.overlay.favorites == prior.overlay.favorites
    assert result.imported is None


def test_saved_current_claim_rejected_and_unregistered_import_always_fresh():
    chain = LibraryChain()
    service = chain.library()
    prior = service.execute(request("import", identity=identity(cid="1")))
    saved = prior.catalog.model_dump(mode="json")
    saved["records"][-1]["freshness"] = "CURRENT"
    with pytest.raises(ValidationError):
        request("import", identity=identity(cid="1"), catalog=saved)
    chain.unregistered.add(identity().processor)
    result = service.execute(request("import", identity=identity(cid="1"), catalog=prior.catalog))
    assert result.status == "VERIFICATION_FAILED"
    assert result.errorCode == "MISSING_REFERENCE" and result.imported is None
    calls = [p for p in chain.requests if p["method"] == "eth_call"]
    assert any(p["params"][0]["data"].startswith("0x" + abi.SELECTORS["isCPU"]) for p in calls)
