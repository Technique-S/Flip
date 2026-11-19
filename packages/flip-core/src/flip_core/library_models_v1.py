"""Additive M4.5 library contracts; no change to historical M1/M2/M3 schemas."""

import unicodedata
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from flip_core import abi
from flip_core.models import Address, Block, Chain, Contract, Digest, Environment, Quantity

VERSION = "m45-library-1.0.0"
Freshness = Literal["HISTORICAL", "STALE", "UNKNOWN", "REORGED", "VERIFICATION_FAILED"]
Source = Literal["FACTORY_ENUMERATION", "KNOWN_SEED", "USER_IMPORT", "USER_FAVORITE_ONLY"]


def display_text(value: str) -> str:
    # React renders this as text. Do not HTML-encode here (which would double-escape).
    return "".join(c for c in unicodedata.normalize("NFKC", value) if c.isprintable())[:256]


class LibraryIdentity(Contract):
    chainId: Chain = 196
    factory: Literal[abi.FACTORY] = abi.FACTORY
    processor: Address
    circuitId: Quantity | None = None

    @field_validator("processor", mode="before")
    @classmethod
    def normalize(cls, value):
        return value.lower() if isinstance(value, str) else value

    @model_validator(mode="after")
    def nonzero(self):
        if int(self.processor, 16) == 0 or self.circuitId == "0":
            raise ValueError("zero identity")
        return self

    @property
    def key(self):
        prefix = f"196:{self.factory}:{self.processor}"
        return prefix if self.circuitId is None else f"{prefix}:{self.circuitId}"


class LibraryRecord(Contract):
    identity: LibraryIdentity
    sources: Annotated[list[Source], Field(min_length=1, max_length=4)]
    block: Block | None = None
    environment: Environment | None = None
    environmentDigest: Digest | None = None
    processorNumber: Quantity | None = None
    nextId: Quantity | None = None
    nIn: int | None = Field(default=None, ge=0, le=2**32 - 1)
    nOut: int | None = Field(default=None, ge=0, le=2**32 - 1)
    nState: int | None = Field(default=None, ge=0, le=2**32 - 1)
    gateCount: int | None = Field(default=None, ge=0, le=2**32 - 1)
    onchainName: str = Field(default="", max_length=256)
    onchainSymbol: str = Field(default="", max_length=256)
    metadataTrust: Literal["ONCHAIN_DISPLAY_ONLY"] = "ONCHAIN_DISPLAY_ONLY"
    freshness: Freshness = "UNKNOWN"
    existence: Literal[
        "OWNER_OF", "SEED_HINT", "IMPORTED", "USER_POINTER", "REGISTERED_PROCESSOR"
    ] = "SEED_HINT"
    manifestHash: Digest | None = None
    netlistHash: Digest | None = None
    dependencyHashes: Annotated[list[Digest], Field(max_length=1251)] = []
    # Deliberately no executable/CURRENT flag. Only M2 import can produce execution input.

    @property
    def key(self):
        return self.identity.key

    @field_validator("onchainName", "onchainSymbol")
    @classmethod
    def text(cls, value):
        return display_text(value)


class Favorite(Contract):
    identity: LibraryIdentity
    label: str = Field(default="", max_length=256)
    description: str = Field(default="", max_length=256)
    tags: Annotated[list[Annotated[str, Field(max_length=256)]], Field(max_length=16)] = []

    @field_validator("label", "description")
    @classmethod
    def text(cls, value):
        return display_text(value)

    @field_validator("tags")
    @classmethod
    def tag_text(cls, value):
        return [display_text(t) for t in value]


class Recent(Contract):
    identity: LibraryIdentity
    manifestHash: Digest
    block: Block


class Overlay(Contract):
    favorites: Annotated[list[Favorite], Field(max_length=256)] = []
    aliases: Annotated[list[Favorite], Field(max_length=256)] = []
    recents: Annotated[list[Recent], Field(max_length=30)] = []


class Catalog(Contract):
    schemaVersion: Literal["m45-library-1.0.0"] = VERSION
    kind: Literal["LIBRARY_CATALOG"] = "LIBRARY_CATALOG"
    records: Annotated[list[LibraryRecord], Field(max_length=1000)] = []
    overlay: Overlay = Field(default_factory=Overlay)


class Cursor(Contract):
    offset: Quantity
    block: Block
    environmentDigest: Digest
    processor: Address | None = None


class LibraryRequest(Contract):
    schemaVersion: Literal["m45-library-1.0.0"] = VERSION
    kind: Literal["LIBRARY_REQUEST"] = "LIBRARY_REQUEST"
    operation: Literal[
        "discover", "circuits", "search", "favorite", "unfavorite", "alias", "import", "revalidate"
    ]
    catalog: Catalog = Field(default_factory=Catalog)
    identity: LibraryIdentity | None = None
    cursor: Cursor | None = None
    limit: int = Field(default=12, ge=1, le=50)
    query: str = Field(default="", max_length=256)
    metadata: Favorite | None = None


class LibraryResult(Contract):
    schemaVersion: Literal["m45-library-1.0.0"] = VERSION
    kind: Literal["LIBRARY_RESULT"] = "LIBRARY_RESULT"
    status: Literal[
        "COMPLETE",
        "COMPLETE_WITH_GAPS",
        "PARTIAL_BOUNDED",
        "UNKNOWN",
        "ENVIRONMENT_CHANGED",
        "REORGED",
        "VERIFICATION_FAILED",
        "ABORTED",
    ]
    errorCode: str | None = None
    catalog: Catalog
    results: Annotated[list[LibraryRecord], Field(max_length=1000)] = []
    cursor: Cursor | None = None
    total: Quantity | None = None
    block: Block | None = None
    sharedEnvironment: dict | None = None
    rpcCallsUsed: int = 0
    rpcCallBudget: int = 256
    retriesUsed: int = 0
    missingIds: list[Quantity] = []
    trust: Literal["SINGLE_UNTRUSTED"] = "SINGLE_UNTRUSTED"
    abiProvenance: Literal["TAP10_KECCAK_RESEARCH_5c7bcfb"] = "TAP10_KECCAK_RESEARCH_5c7bcfb"
    imported: dict | None = None
