"""Additive M2 contracts. The six frozen M1 wire schemas remain unchanged."""

from typing import Annotated, Literal, Self

from pydantic import ConfigDict, Field, model_validator

from flip_core.canonical import content_hash
from flip_core.models import CircuitIdentity, Contract, Digest, HexBytes, Integrity, Manifest


class ImportBudget(Contract):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    maxNetlistBytes: Annotated[int, Field(ge=1, le=1_000_000)] = 250_000
    maxTotalBytes: Annotated[int, Field(ge=1, le=1_000_000)] = 1_000_000
    maxRecords: Annotated[int, Field(ge=1, le=5000)] = 5000
    maxTotalRecords: Annotated[int, Field(ge=1, le=5000)] = 5000
    maxGates: Annotated[int, Field(ge=1, le=5000)] = 2500
    maxDepth: Annotated[int, Field(ge=1, le=64)] = 64
    maxCircuits: Annotated[int, Field(ge=1, le=1251)] = 128
    maxRequests: Annotated[int, Field(ge=1, le=8192)] = 256
    deadlineMs: Annotated[int, Field(ge=1, le=120_000)] = 60_000


class CircuitBytes(Contract):
    identity: CircuitIdentity
    netlist: HexBytes


class ImportResult(Contract):
    schemaVersion: Literal["1.0.0"]
    kind: Literal["CIRCUIT_IMPORT"]
    manifest: Manifest
    manifestHash: Digest
    circuits: Annotated[list[CircuitBytes], Field(min_length=1, max_length=1251)]
    integrity: Integrity
    pinning: Literal["NUMBER_WITH_HEADER_RECHECK"]
    trust: Literal["SINGLE_RPC_OBSERVATION"]

    @model_validator(mode="after")
    def content_bound(self) -> Self:
        import hashlib

        if self.manifestHash != content_hash(self.manifest):
            raise ValueError("manifest hash mismatch")
        expected = {
            content_hash(s.identity): s.netlistHash
            for s in [self.manifest.root, *self.manifest.dependencies]
        }
        actual = {
            content_hash(c.identity): "0x"
            + hashlib.sha256(bytes.fromhex(c.netlist[2:])).hexdigest()
            for c in self.circuits
        }
        if actual != expected or len(self.circuits) != len(expected):
            raise ValueError("netlist bytes do not bind the complete manifest closure")
        if self.integrity.freshness == "CURRENT":
            if self.manifest.observation != "SINGLE_RPC":
                raise ValueError("offline snapshots cannot be current")
            if self.integrity.checkedBlock != self.manifest.block:
                raise ValueError("checked block must bind manifest block")
        return self


class RevalidationResult(Contract):
    schemaVersion: Literal["1.0.0"]
    kind: Literal["MANIFEST_REVALIDATION"]
    previousManifestHash: Digest
    observed: ImportResult
    integrity: Integrity
    changes: list[
        Literal[
            "ROOT_CHANGED",
            "DEPENDENCIES_CHANGED",
            "NETLIST_CHANGED",
            "INTERFACE_CHANGED",
            "FACTORY_IMPLEMENTATION_CHANGED",
            "BEACON_IMPLEMENTATION_CHANGED",
            "PROCESSOR_CODE_CHANGED",
            "ENVIRONMENT_CHANGED",
            "SEMANTICS_CHANGED",
            "BLOCK_CHANGED",
        ]
    ]

    @model_validator(mode="after")
    def consistent_freshness(self) -> Self:
        if self.integrity.checkedBlock != self.observed.manifest.block:
            raise ValueError("revalidation block does not match observed manifest")
        if bool(self.changes) != (self.integrity.freshness == "STALE"):
            raise ValueError("changed manifests must be stale")
        if self.integrity.freshness == "CURRENT" and self.observed.integrity.freshness != "CURRENT":
            raise ValueError("historical observations cannot yield current revalidation")
        return self
