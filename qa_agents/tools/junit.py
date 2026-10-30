"""JUnit XML parsing and summaries.

Handles the dialects written by JUnit/Maven Surefire, TestNG, pytest, Playwright, Cypress, Jest,
Gradle and most CI tools: <testsuites> or a single <testsuite> root, nested suites, failures with
or without a message, and Surefire rerun elements (<flakyFailure>, <flakyError>, <rerunFailure>,
<rerunError>).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass

from qa_agents.core.llm import AgentError

RERUN_TAGS = ("flakyFailure", "flakyError", "rerunFailure", "rerunError")


@dataclass
class TestResult:
    __test__ = False  # not a pytest test class

    suite: str
    name: str
    classname: str
    time: float
    status: str  # passed | failed | error | skipped
    message: str = ""
    details: str = ""
    reruns: int = 0  # Surefire rerun attempts recorded for this test
    flaky: bool = False  # failed at least once, then passed on rerun

    @property
    def full_name(self) -> str:
        return f"{self.classname}.{self.name}" if self.classname else self.name

    def as_dict(self) -> dict:
        return asdict(self)


def _seconds(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return 0.0


def _first_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()[:300]
    return ""


def parse_junit(xml_text: str, source: str = "report") -> list[TestResult]:
    if re.search(r"<!ENTITY", xml_text[:5000], re.IGNORECASE):
        raise AgentError(f"{source}: XML entity declarations are not allowed in test reports.")
    try:
        root = ET.fromstring(xml_text.strip())
    except ET.ParseError as exc:
        raise AgentError(f"{source} is not valid XML ({exc}). Is the report complete?") from exc
    if root.tag not in ("testsuites", "testsuite", "testrun"):
        raise AgentError(f"{source} is XML but not a JUnit report (root element <{root.tag}>).")

    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    results: list[TestResult] = []
    for suite in suites:
        suite_name = suite.get("name", "") or ""
        for case in suite.findall("testcase"):
            status, message, details = "passed", "", ""
            for tag in ("failure", "error", "skipped"):
                node = case.find(tag)
                if node is not None:
                    status = {"failure": "failed", "error": "error", "skipped": "skipped"}[tag]
                    details = (node.text or "").strip()
                    message = (node.get("message") or "").strip() or _first_line(details) or node.get("type", "")
                    break
            reruns = [n for t in RERUN_TAGS for n in case.findall(t)]
            flaky = status == "passed" and any(n.tag.startswith("flaky") for n in reruns)
            if flaky and not message:
                first = reruns[0]
                message = (first.get("message") or "").strip() or _first_line(first.text or "")
            results.append(
                TestResult(
                    suite=suite_name,
                    name=case.get("name", "") or "(unnamed test)",
                    classname=case.get("classname", "") or "",
                    time=_seconds(case.get("time")),
                    status=status,
                    message=message,
                    details=details,
                    reruns=len(reruns),
                    flaky=flaky,
                )
            )
    if not results:
        raise AgentError(f"{source} contains no <testcase> elements.")
    return results


def summarise(results: list[TestResult]) -> dict:
    counts = Counter(r.status for r in results)
    executed = len(results) - counts["skipped"]
    passed = counts["passed"]
    by_suite: dict[str, Counter] = defaultdict(Counter)
    for r in results:
        by_suite[r.suite or "(no suite)"][r.status] += 1
    slowest = sorted(results, key=lambda r: r.time, reverse=True)[:5]
    flaky = [r.full_name for r in results if r.flaky]
    smoke = [r for r in results if "smoke" in f"{r.suite} {r.full_name}".lower()]
    summary = {
        "total": len(results),
        "executed": executed,
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
        "smoke": {
            "total": len(smoke),
            "failed": sum(1 for r in smoke if r.status in ("failed", "error")),
            "skipped": sum(1 for r in smoke if r.status == "skipped"),
        },
    }
    if flaky:
        summary["passed_only_on_rerun"] = flaky
    if executed == 0:
        summary["warning"] = "No tests were executed (all skipped or none found)."
    return summary
