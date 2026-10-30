"""JUnit XML parsing and summaries (works for JUnit, TestNG, pytest, Playwright and Cypress reporters)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass


@dataclass
class TestResult:
    suite: str
    name: str
    classname: str
    time: float
    status: str  # passed | failed | error | skipped
    message: str = ""
    details: str = ""

    @property
    def full_name(self) -> str:
        return f"{self.classname}.{self.name}" if self.classname else self.name

    def as_dict(self) -> dict:
        return asdict(self)


def parse_junit(xml_text: str) -> list[TestResult]:
    root = ET.fromstring(xml_text)
    suites = [root] if root.tag == "testsuite" else root.iter("testsuite")
    results: list[TestResult] = []
    for suite in suites:
        suite_name = suite.get("name", "")
        for case in suite.findall("testcase"):
            status, message, details = "passed", "", ""
            for tag in ("failure", "error", "skipped"):
                node = case.find(tag)
                if node is not None:
                    status = "failed" if tag == "failure" else tag
                    message = node.get("message", "") or ""
                    details = (node.text or "").strip()
                    break
            results.append(
                TestResult(
                    suite=suite_name,
                    name=case.get("name", ""),
                    classname=case.get("classname", ""),
                    time=float(case.get("time", 0) or 0),
                    status=status,
                    message=message.strip(),
                    details=details,
                )
            )
    return results


def summarise(results: list[TestResult]) -> dict:
    counts = Counter(r.status for r in results)
    executed = len(results) - counts["skipped"]
    passed = counts["passed"]
    by_suite: dict[str, Counter] = defaultdict(Counter)
    for r in results:
        by_suite[r.suite][r.status] += 1
    slowest = sorted(results, key=lambda r: r.time, reverse=True)[:5]
    return {
        "total": len(results),
        "passed": passed,
        "failed": counts["failed"],
        "errors": counts["error"],
        "skipped": counts["skipped"],
        "pass_rate_pct": round(100 * passed / executed, 1) if executed else 0.0,
        "duration_s": round(sum(r.time for r in results), 1),
        "by_suite": [
            {
                "suite": s,
                "passed": c["passed"],
                "failed": c["failed"] + c["error"],
                "skipped": c["skipped"],
            }
            for s, c in by_suite.items()
        ],
        "slowest": [{"test": r.full_name, "seconds": r.time} for r in slowest],
    }
