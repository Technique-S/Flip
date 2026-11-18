"""Bounded synchronous JSON-RPC transport, with read methods/selectors only."""

import os
import re
import time
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx

from flip_core.abi import SELECTORS
from flip_core.canonical import load_json
from flip_core.contracts import ContractError
from flip_core.import_models import ImportBudget

READ_METHODS = frozenset(
    {"eth_chainId", "eth_getBlockByNumber", "eth_call", "eth_getCode", "eth_getStorageAt"}
)


@dataclass(frozen=True)
class RpcSettings:
    endpoint: str = "https://rpc.xlayer.tech"
    timeout_ms: int = 5000
    retries: int = 1

    @classmethod
    def from_environment(cls):
        try:
            return cls(
                os.getenv("FLIP_RPC_URL", "https://rpc.xlayer.tech"),
                int(os.getenv("FLIP_RPC_TIMEOUT_MS", "5000")),
                int(os.getenv("FLIP_RPC_RETRIES", "1")),
            )
        except (ValueError, ContractError) as exc:
            raise ContractError("RPC_UNAVAILABLE", "Invalid local RPC configuration.") from exc

    def __post_init__(self):
        if not isinstance(self.endpoint, str):
            raise ContractError("INVALID_INPUT", "Invalid RPC endpoint configuration.")
        try:
            url = urlsplit(self.endpoint)
            _ = url.port
        except ValueError as exc:
            raise ContractError("INVALID_INPUT", "Invalid RPC endpoint configuration.") from exc
        if (
            url.scheme not in ("https", "http")
            or not url.hostname
            or url.username
            or url.password
            or url.fragment
        ):
            raise ContractError("INVALID_INPUT", "Invalid RPC endpoint configuration.")
        if type(self.timeout_ms) is not int or not 1 <= self.timeout_ms <= 30_000:
            raise ContractError("INVALID_INPUT", "RPC timeout must be 1..30000 ms.")
        if type(self.retries) is not int or not 0 <= self.retries <= 2:
            raise ContractError("INVALID_INPUT", "RPC retries must be 0..2.")


class RpcClient:
    def __init__(self, settings: RpcSettings, budget: ImportBudget, transport=None):
        self.settings, self.budget = settings, budget
        self.calls = 0
        self.deadline = time.monotonic() + budget.deadlineMs / 1000
        self.client = httpx.Client(
            transport=transport,
            follow_redirects=False,
            trust_env=False,
            headers={"Accept-Encoding": "identity"},
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.client.close()

    def remaining(self) -> float:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise ContractError("RESOURCE_LIMIT", "Import deadline exceeded.")
        return remaining

    def call(self, method: str, params: list):
        if method not in READ_METHODS:
            raise ContractError("INVALID_INPUT", "RPC method is not allowlisted.")
        if method == "eth_call":
            if len(params) != 2 or set(params[0]) != {"to", "data"}:
                raise ContractError(
                    "INVALID_INPUT", "Only bounded read-only contract calls are allowed."
                )
            data = params[0]["data"]
            lengths = {
                "nextId": 10,
                "circuitInfo": 74,
                "netlist": 74,
                "factory": 10,
                "isCPU": 74,
                "circuitBeacon": 10,
                "implementation": 10,
                "isSealed": 10,
            }
            if (
                not isinstance(data, str)
                or not any(
                    data.startswith("0x" + selector) and len(data) == lengths[name]
                    for name, selector in SELECTORS.items()
                )
                or not re.fullmatch(r"0x[0-9a-f]+", data)
            ):
                raise ContractError("INVALID_INPUT", "Contract selector is not allowlisted.")
        return self._read(method, params)

    def _read(self, method, params, *, capture_revert=False):
        if method not in READ_METHODS:
            raise ContractError("INVALID_INPUT", "Only read-only RPC methods are supported.")
        for attempt in range(self.settings.retries + 1):
            if self.calls >= self.budget.maxRequests:
                raise ContractError("RESOURCE_LIMIT", "RPC request budget exceeded.")
            self.calls += 1
            timeout = min(self.settings.timeout_ms / 1000, self.remaining())
            try:
                with self.client.stream(
                    "POST",
                    self.settings.endpoint,
                    json={"jsonrpc": "2.0", "id": self.calls, "method": method, "params": params},
                    timeout=timeout,
                ) as response:
                    response.raise_for_status()
                    if response.headers.get("content-encoding", "identity").lower() != "identity":
                        raise ValueError("compressed RPC responses are unsupported")
                    if int(response.headers.get("content-length", "0")) > 2_100_000:
                        raise ContractError("RESOURCE_LIMIT", "RPC response byte budget exceeded.")
                    raw = bytearray()
                    for chunk in response.iter_bytes(chunk_size=65536):
                        self.remaining()
                        if len(raw) + len(chunk) > 2_100_000:
                            raise ContractError(
                                "RESOURCE_LIMIT", "RPC response byte budget exceeded."
                            )
                        raw.extend(chunk)
                result = load_json(bytes(raw))
                if not isinstance(result, dict) or result.get("jsonrpc") != "2.0":
                    raise ValueError("invalid envelope")
                if type(result.get("id")) is not int or result["id"] != self.calls:
                    raise ValueError("mismatched id")
                if ("result" in result) == ("error" in result):
                    raise ValueError("ambiguous result")
                if "error" in result:
                    error = result["error"]
                    if (
                        capture_revert
                        and isinstance(error, dict)
                        and type(error.get("code")) is int
                        and error["code"] in (3, -32000)
                        and isinstance(error.get("message"), str)
                        and error["message"].lower().startswith("execution reverted")
                    ):
                        return {"revert": error.get("data")}
                    lookup = method == "eth_call" and params[0]["data"][2:10] in (
                        SELECTORS["circuitInfo"],
                        SELECTORS["netlist"],
                    )
                    if lookup and isinstance(error, dict) and type(error.get("code")) is int:
                        # Closed known-revert classification only. Unknown provider
                        # failures remain RPC_UNAVAILABLE; remote text is not echoed.
                        if error["code"] in (-32000, 3) and error.get("message") in (
                            "no circuit",
                            "execution reverted: no circuit",
                        ):
                            raise ContractError(
                                "MISSING_REFERENCE", "Circuit lookup reports no existing circuit."
                            )
                    raise ValueError("RPC error")
                return None if capture_revert else result["result"]
            except ContractError:
                raise
            except (httpx.HTTPError, ValueError, TypeError, UnicodeError, RecursionError) as exc:
                transient = isinstance(exc, httpx.TransportError) or (
                    isinstance(exc, httpx.HTTPStatusError)
                    and (exc.response.status_code == 429 or exc.response.status_code >= 500)
                )
                if not transient or attempt == self.settings.retries:
                    raise ContractError(
                        "RPC_UNAVAILABLE", "RPC request failed or returned malformed data."
                    ) from exc
                time.sleep(min(0.1 * (2**attempt), self.remaining()))
        raise ContractError("RPC_UNAVAILABLE", "RPC retries exhausted.")


def quantity(value: object) -> int:
    if (
        not isinstance(value, str)
        or not re.fullmatch(r"0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)", value)
        or len(value) > 66
    ):
        raise ContractError("INVALID_INPUT", "Malformed RPC quantity.")
    return int(value, 16)
