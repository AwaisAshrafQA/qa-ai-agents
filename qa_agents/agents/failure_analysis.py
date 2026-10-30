"""5. Failure Analysis Agent: classifies failures as app defect, automation issue, test data or environment."""

from __future__ import annotations

import re
from collections import Counter
from typing import Literal

from pydantic import BaseModel

from qa_agents.core.base import Agent, by_suffix, facts_block, file_block
from qa_agents.core.llm import AgentError
from qa_agents.tools.junit import parse_junit

Category = Literal["app_defect", "automation_issue", "test_data", "environment", "unknown"]

# Order matters: the first matching category wins.
HEURISTICS: list[tuple[str, re.Pattern]] = [
    ("environment", re.compile(
        r"ECONNREFUSED|Connection refused|ECONNRESET|ETIMEDOUT|ENOTFOUND|getaddrinfo|\b50[234]\b|"
        r"Service Unavailable|Bad Gateway|Gateway Time-?out|SSL|certificate|connect timed out|"
        r"OutOfMemory|No space left|browser has disconnected|Target closed", re.IGNORECASE)),
    ("test_data", re.compile(
        r"duplicate key|already exists|\b409\b|user not found|no such user|account (?:is )?locked|"
        r"expired (?:coupon|card|token)|insufficient (?:stock|balance|funds)|fixture|seed data|"
        r"test data", re.IGNORECASE)),
    ("automation_issue", re.compile(
        r"NoSuchElement|StaleElementReference|ElementNotInteractable|ElementClickIntercepted|"
        r"strict mode violation|waiting for (?:locator|selector)|locator\(|Timed out \d+ms waiting|"
        r"Unable to locate element|is not attached to the DOM|cy\.get\(\) .*never found", re.IGNORECASE)),
    ("app_defect", re.compile(
        r"AssertionError|expected .* (?:but was|to (?:equal|be))|Expected:? .*Received|"
        r"\b500\b|Internal Server Error|NullPointerException|TypeError", re.IGNORECASE)),
]


class FailureVerdict(BaseModel):
    test: str
    category: Category
    confidence: Literal["high", "medium", "low"]
    evidence: str
    root_cause: str
    next_action: str
    owner: Literal["developer", "qa_automation", "test_data_owner", "devops", "triage"]


class FailureAnalysis(BaseModel):
    summary: str
    failures: list[FailureVerdict]
    patterns: list[str]


def heuristic_category(text: str) -> str:
    for category, pattern in HEURISTICS:
        if pattern.search(text):
            return category
    return "unknown"


class FailureAnalysisAgent(Agent):
    name = "failure-analysis"
    title = "Failure Analysis"
    summary = "Classifies failures from reports, logs and stack traces as app defect, automation issue, test data or environment."
    inputs_help = "JUnit XML report(s), plus optional .log/.txt files (app, CI or browser logs)"
    example_files = ["results.xml", "api-gateway.log"]
    output_model = FailureAnalysis
    system_prompt = """Task: triage failed automated tests after a CI run.
Classify each failure as app_defect (the product is wrong), automation_issue (the test or
framework is wrong), test_data (missing, stale or conflicting data), environment (infra, network,
dependency or config) or unknown. A keyword hint was computed locally; confirm or override it
using the stack trace AND the logs (e.g. a 500 in the test plus a matching error in the service
log is an app defect; a timeout while the gateway logs show the dependency was down is environment).
Quote the decisive evidence, state the root cause, the next action and who should own it.
Finish with cross-failure patterns (same root cause, same service, same time window)."""

    def analyse(self, files):
        reports = by_suffix(files, ".xml")
        if not reports:
            raise AgentError("failure-analysis needs at least one JUnit XML report.")
        failed = []
        for f in reports:
            for r in parse_junit(f.text()):
                if r.status in ("failed", "error"):
                    failed.append(
                        {
                            "test": r.full_name,
                            "suite": r.suite,
                            "message": r.message[:300],
                            "heuristic_category": heuristic_category(f"{r.message}\n{r.details}"),
                        }
                    )
        return {"failed_tests": len(failed), "failures": failed}

    def build_prompt(self, files, facts):
        docs = "\n\n".join(file_block(f) for f in files)
        return f"{docs}\n\n{facts_block(facts)}\n\nClassify every failed test."

    def finalise(self, output, facts, notes):
        facts["by_category"] = dict(Counter(v.category for v in output.failures))
        return output
