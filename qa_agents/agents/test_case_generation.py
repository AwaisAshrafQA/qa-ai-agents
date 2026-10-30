"""2. Test Case Generation Agent: positive, negative, boundary and integration scenarios."""

from __future__ import annotations

import re
from collections import Counter
from typing import Literal

from pydantic import BaseModel

from qa_agents.core.base import Agent, facts_block, file_block

_UNITS = r"(characters?|chars?|items?|digits?|%|percent|minutes?|mins?|seconds?|secs?|hours?|days?|AED|USD|MB|KB|attempts?|times|products?|users?|years?)"
_LIMIT_RE = re.compile(
    r"(?P<phrase>(?:at least|minimum(?: of)?|min\.?|at most|maximum(?: of)?|max\.?|up to|no more than|more than|less than|over|under|between)?\s*"
    r"(?P<a>\d+(?:\.\d+)?)(?:\s*(?:and|to|-)\s*(?P<b>\d+(?:\.\d+)?))?\s*" + _UNITS + r")",
    re.IGNORECASE,
)


class TestCase(BaseModel):
    id: str
    title: str
    type: Literal["positive", "negative", "boundary", "integration"]
    priority: Literal["P1", "P2", "P3"]
    requirement_ref: str
    preconditions: list[str]
    steps: list[str]
    test_data: str
    expected_result: str


class TestSuite(BaseModel):
    summary: str
    test_cases: list[TestCase]
    coverage_notes: list[str]
    automation_candidates: list[str]


def _probes(value: str) -> list[float | int]:
    if "." in value:
        v = float(value)
        return [round(v - 0.01, 2), v, round(v + 0.01, 2)]
    v = int(value)
    return [v - 1, v, v + 1]


def find_limits(text: str) -> list[dict]:
    """Numeric limits in the requirement text, with the values worth probing around each."""
    limits, seen = [], set()
    for m in _LIMIT_RE.finditer(text):
        phrase = " ".join(m.group("phrase").split())
        if phrase.lower() in seen:
            continue
        seen.add(phrase.lower())
        probes = _probes(m.group("a"))
        if m.group("b"):
            probes += _probes(m.group("b"))
        limits.append({"text": phrase, "probe_values": sorted(set(probes))})
    return limits


class TestCaseGenerationAgent(Agent):
    name = "test-case-generation"
    title = "Test Case Generation"
    summary = "Creates positive, negative, boundary and integration test cases from requirements."
    inputs_help = "requirement or user-story files (Markdown/text)"
    example_files = ["coupon_requirement.md"]
    output_model = TestSuite
    system_prompt = """Task: design a test suite from the requirements.
Cover positive (happy paths), negative (invalid input, unauthorised, wrong state), boundary
(use the locally computed probe values: below, at and above every limit) and integration
scenarios (other services, payments, notifications, persistence, concurrency).
Each case must be independent, have concrete test data and one observable expected result.
Number cases TC-001, TC-002... Prioritise P1 for revenue, security or data-loss risk.
List which cases are good automation candidates and why."""

    def analyse(self, files):
        text = "\n".join(f.text() for f in files)
        return {"numeric_limits": find_limits(text)}

    def build_prompt(self, files, facts):
        docs = "\n\n".join(file_block(f) for f in files)
        return f"{docs}\n\n{facts_block(facts)}\n\nDesign the test suite."

    def finalise(self, output, facts, notes):
        facts["cases_by_type"] = dict(Counter(tc.type for tc in output.test_cases))
        facts["cases_by_priority"] = dict(Counter(tc.priority for tc in output.test_cases))
        return output
