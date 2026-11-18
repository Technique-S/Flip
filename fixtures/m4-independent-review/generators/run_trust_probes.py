# ruff: noqa: E501
"""M4-C trust-boundary HTTP probes against the documented local deployment.

All traffic targets 127.0.0.1. No live RPC is contacted by these probes except
where the running server's own default is used; probe results record exactly
what was observed. No claim is made that a 2xx response proves verification.

    uv run --frozen python fixtures/m4-independent-review/generators/run_trust_probes.py
"""

from __future__ import annotations

import copy
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[3]
REQ = ROOT / "fixtures/m4-independent-review/corpus"
DL = ROOT / "fixtures/m4-independent-review/downloads"
EXEC = ROOT / "docs/evidence/m4-independent-review/executed"
BASE = "http://127.0.0.1:8000"


def load(path: Path):
    return json.loads(path.read_bytes())


def post(client, path, body, headers=None):
    return client.post(
        BASE + path,
        content=body if isinstance(body, bytes | str) else json.dumps(body).encode(),
        headers=headers or {"Content-Type": "application/json"},
    )


def record(name, response, note=""):
    (EXEC / f"T-{name}.http.txt").write_text(
        f"HTTP {response.status_code}\n" + response.text[:12000], encoding="utf-8"
    )
    try:
        payload = response.json()
        code = payload.get("error", {}).get("code") if isinstance(payload, dict) else None
        verdict = None
        if isinstance(payload, dict) and "report" in payload:
            verdict = payload["report"]["verification"]["verdict"]
    except ValueError:
        code, verdict = None, None
    item = {
        "id": name,
        "status": response.status_code,
        "errorCode": code,
        "verdict": verdict,
        "note": note,
        "capture": f"docs/evidence/m4-independent-review/executed/T-{name}.http.txt",
    }
    print(name, item["status"], code or verdict or "")
    return item


def main() -> None:
    results = []
    with httpx.Client(timeout=30.0, trust_env=False) as client:
        original = client.get(BASE + "/api/v1/sample/half-adder").json()
        swapped = client.get(BASE + "/api/v1/sample/swapped").json()

        forged = load(REQ / "consumption-forged-verdict.json")
        results.append(
            record(
                "01-forged-verdict",
                post(client, "/api/v1/consume", forged),
                "verdict relabelled EQUIVALENT -> DIFFERENT",
            )
        )

        current = load(REQ / "consumption-current-relabel.json")
        results.append(
            record(
                "02-false-current",
                post(client, "/api/v1/consume", current),
                "freshness relabelled HISTORICAL -> CURRENT",
            )
        )

        stale = load(REQ / "consumption-changed-reference.json")
        results.append(
            record(
                "03-stale-reference",
                post(client, "/api/v1/consume", stale),
                "consumer reference pin replaced",
            )
        )

        wrong_chain = load(REQ / "wrong-chain.json")
        results.append(
            record(
                "04-wrong-chain-execution",
                post(client, "/api/v1/compare", wrong_chain),
                "manifest root chainId changed to 8453",
            )
        )

        bad_map = load(REQ / "invalid-pin-map.json")
        results.append(
            record(
                "05-malformed-mapping", post(client, "/api/v1/compose", bad_map), "outputMap [0,2]"
            )
        )

        results.append(
            record(
                "06-malformed-upload",
                post(client, "/api/v1/compose", b"{not json"),
                "raw malformed body",
            )
        )
        results.append(
            record(
                "07-oversized", post(client, "/api/v1/compose", b"x" * 1_100_000), "1.1 MiB body"
            )
        )

        results.append(
            record(
                "08-host-bypass",
                post(
                    client,
                    "/api/v1/compare",
                    original,
                    headers={"Content-Type": "application/json", "Host": "evil.example"},
                ),
                "spoofed Host",
            )
        )
        results.append(
            record(
                "09-origin-bypass",
                post(
                    client,
                    "/api/v1/compare",
                    original,
                    headers={"Content-Type": "application/json", "Origin": "http://evil.example"},
                ),
                "cross-origin header",
            )
        )
        results.append(
            record(
                "10-cross-site",
                post(
                    client,
                    "/api/v1/compare",
                    original,
                    headers={"Content-Type": "application/json", "Sec-Fetch-Site": "cross-site"},
                ),
                "cross-site fetch header",
            )
        )

        # Caller-supplied CURRENT cannot grant freshness on a normal comparison.
        results.append(
            record(
                "11-caller-current",
                post(
                    client, "/api/v1/compare", load(REQ / "half-adder-current-freshness-claim.json")
                ),
                "expect HISTORICAL in 200 body",
            )
        )

        # Cross-project bundle reuse: swapped project, original evidence.
        bundle_text = (DL / "evidence.json").read_text()
        cross = dict(
            schemaVersion="m4-1.0.0",
            kind="PRODUCT_REQUEST",
            executionRequest=swapped,
            bundleText=bundle_text,
        )
        results.append(
            record(
                "12-cross-project-bundle",
                post(client, "/api/v1/verify-bundle", cross),
                "bundle from different project",
            )
        )

        # Manipulated witness on a real DIFFERENT claim.
        different = load(REQ / "consumption-different.json")
        attack = copy.deepcopy(different)
        w = attack["claimedResult"]["report"]["verification"]["witness"]
        w["inputs"]["bits"] = "10" if w["inputs"]["bits"] != "10" else "01"
        results.append(
            record(
                "13-manipulated-witness",
                post(client, "/api/v1/consume", attack),
                "witness input bit changed",
            )
        )

        # Parallel resource exhaustion (two execution slots are documented).
        def one(_i):
            r = post(client, "/api/v1/compare", original)
            return r.status_code

        with ThreadPoolExecutor(max_workers=6) as pool:
            codes = list(pool.map(one, range(6)))
        results.append(
            {
                "id": "14-parallel-exhaustion",
                "status": sorted(codes),
                "errorCode": None,
                "verdict": None,
                "note": "six concurrent compare requests; documented concurrency is two",
                "capture": "docs/evidence/m4-independent-review/executed/T-14-parallel-exhaustion.http.txt",
            }
        )
        (EXEC / "T-14-parallel-exhaustion.http.txt").write_text(
            json.dumps({"statuses": codes}) + "\n", encoding="utf-8"
        )
        print("14-parallel-exhaustion", sorted(codes))

    (EXEC / "trust-probes.json").write_text(
        json.dumps({"schemaVersion": "m4-independent-review-1", "probes": results}, indent=2)
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
