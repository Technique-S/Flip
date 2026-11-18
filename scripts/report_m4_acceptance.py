"""Combine executed pytest and Chromium results with explicit specification mappings."""

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--browser", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    tree = ET.parse(args.junit)
    tests = {
        t.get("name"): not any(t.find(x) is not None for x in ("failure", "error", "skipped"))
        for t in tree.iter("testcase")
    }
    cases = []
    for test in tree.iter("testcase"):
        for prop in test.findall("./properties/property"):
            if prop.get("name") == "m4_case":
                item = json.loads(prop.get("value"))
                item.update(
                    status="PASS" if tests[test.get("name")] else "FAIL",
                    command="python -m pytest packages/flip-core/tests/test_m4_acceptance.py::"
                    + test.get("name")
                    + " -q",
                    reason=None,
                )
                cases.append(item)
    browser = json.loads(args.browser.read_text(encoding="utf-8"))
    browser_tests = {}

    def collect(suite):
        for spec in suite.get("specs", []):
            browser_tests[spec["title"]] = all(t.get("status") == "expected" for t in spec["tests"])
        for child in suite.get("suites", []):
            collect(child)

    for suite in browser["suites"]:
        collect(suite)

    def mapped(id, title, need, web=()):
        matched = [name for name in tests if any(n in name for n in need)]
        rendered = [name for name in browser_tests if any(n in name for n in web)]
        ok = (
            bool(matched or rendered)
            and all(tests[n] for n in matched)
            and all(browser_tests[n] for n in rendered)
        )
        cases.append(
            dict(
                id=id,
                expected=title,
                actual=dict(python=matched, chromium=rendered),
                status="PASS" if ok else "FAIL",
                command="pytest selectors and npm test -- --grep selectors listed in actual",
                reason=None,
                boundary="Executed product operations; mappings identify tested portions",
            )
        )

    journey_tests = [
        (["test_product_roundtrip"], ["historical sample"]),
        (["C27", "C28"], ["keyboard and narrow"]),
        (["C08"], ["historical sample"]),
        (["C03"], ["keyboard and narrow"]),
        (["C29"], ["historical sample"]),
        (["C04"], ["historical sample"]),
        (["C05", "C26"], ["historical sample"]),
        (["C06"], ["B07"]),
        (["C30", "test_chain_change"], []),
        (["C14"], ["B02"]),
        (["C12"], ["B04"]),
        (["test_product_roundtrip"], ["historical sample"]),
        (["test_preflight_transport", "test_historical_preflight"], ["B11"]),
    ]
    fixture = ROOT / "fixtures/m4-ux-acceptance"
    for j, (py, web) in zip(
        json.loads((fixture / "journeys/JOURNEYS.json").read_bytes())["journeys"],
        journey_tests,
        strict=True,
    ):
        mapped(j["id"], j["title"], py, web)
    errors = [
        ["C11"],
        ["C28"],
        ["E03"],
        ["test_chain_change"],
        ["C30"],
        ["C06"],
        ["E07"],
        ["E08"],
        ["C05"],
        ["C14"],
        ["test_preflight_transport[structural"],
        ["test_preflight_transport[empty"],
    ]
    for i, need in enumerate(errors, 1):
        mapped("E" + str(i).zfill(2), "Error scenario exercised at product boundary", need)
    for i in range(1, 12):
        token = "B" + str(i).zfill(2)
        mapped(token, "Chromium accessibility scenario " + token, [], [token])
    mapped("P05", "Controlled RPC import, chain check and pinned single-RPC observation", ["C27"])
    mapped("P06", "Chromium application acceptance", [], ["B01", "B03", "B11"])
    cases.append(
        dict(
            id="MANUAL-SCREEN-READER",
            expected="Auditory screen-reader smoke",
            actual=None,
            status="BLOCKED",
            command=None,
            reason=(
                "No screen-reader session available. Chromium accessibility tree, "
                "live region text and axe were exercised."
            ),
            boundary="manual assistive technology",
        )
    )
    result = dict(
        schemaVersion="m4-acceptance-1",
        sources=dict(
            m3="0bd006336d9ab710706e1e11aa0533636d7fae1e",
            m4a="f4d5b3a981d4cd5906c3ab11942c106f5becc7a9",
            m4b="52814f5cef02716f4a9e49842ae520cdf7937a31",
        ),
        suite=dict(total=len(tests), passed=sum(tests.values())),
        browser=browser_tests,
        cases=cases,
        result="PASS"
        if all(tests.values())
        and all(browser_tests.values())
        and all(c["status"] != "FAIL" for c in cases)
        else "FAIL",
        limitations=[
            (
                "Journey mappings report exercised product paths. "
                "M4-B capture/plan metadata remains historical."
            ),
            (
                "P02/P03 use JSON evidence with independent project pins. "
                "ZIP and SHA256SUMS plan is inapplicable."
            ),
            "P04 uses explicit half-adder variant. P05 uses controlled RPC, not fresh mainnet.",
            "B04 manual speech output remains unexecuted. All automated checks must pass.",
        ],
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "result": result["result"],
                "tests": len(tests),
                "browser": len(browser_tests),
                "cases": len(cases),
            }
        )
    )
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
