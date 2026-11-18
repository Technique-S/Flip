"""flip-json-v1: a deliberately restricted, language-neutral canonical JSON profile."""

import hashlib
import json
from typing import Any

from pydantic import BaseModel

MAX_SAFE_INTEGER = 2**53 - 1


def _check(value: Any) -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if abs(value) > MAX_SAFE_INTEGER:
            raise ValueError("unsafe JSON integer; use a decimal string")
        return
    if type(value) is str:
        value.encode("utf-8", errors="strict")  # rejects lone surrogates
        return
    if type(value) is list:
        for item in value:
            _check(item)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str or not key.isascii():
                raise ValueError("object keys must be ASCII strings")
            _check(item)
        return
    raise ValueError("unsupported JSON type (floats are forbidden)")


def canonical_bytes(value: Any) -> bytes:
    """Hash all supplied fields; no hidden removal, rounding or Unicode normalization."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json", by_alias=True)
    _check(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )


def content_hash(value: Any) -> str:
    return "0x" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_number(value: str) -> None:
    raise ValueError(f"non-integer JSON number forbidden: {value}")


def _integer(value: str) -> int:
    if value == "-0":
        raise ValueError("negative zero forbidden")
    return int(value)


def load_json(data: str | bytes) -> Any:
    value = json.loads(
        data,
        object_pairs_hook=_pairs,
        parse_float=_reject_number,
        parse_constant=_reject_number,
        parse_int=_integer,
    )
    _check(value)
    return value
