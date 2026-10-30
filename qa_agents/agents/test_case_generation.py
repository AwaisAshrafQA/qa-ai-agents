"""2. Test Case Generation Agent: positive, negative, boundary and integration scenarios."""

from __future__ import annotations

import re
from collections import Counter
from typing import Literal

from pydantic import BaseModel

from qa_agents.core.base import Agent, facts_block, file_block

_UNITS = (
    r"(characters?|chars?|letters?|items?|digits?|%|percent|minutes?|mins?|seconds?|secs?|ms|milliseconds?|hours?|hrs?"
    r"|days?|weeks?|months?|years?|AED|USD|EUR|GBP|SAR|INR|PKR|dollars?|MB|KB|GB|attempts?|times|tries|retries|products?"
    r"|users?|orders?|files?|rows?|records?|pages?|requests?|words?|lines?|kg|km)"
)
_LIMIT_RE = re.compile(
    r"(?P<phrase>(?:at least|minimum(?: of)?|min\.?|at most|maximum(?: of)?|max\.?|up to|no more than|no less than|more than"
    r"|less than|fewer than|greater than|over|under|between|exactly|>=|<=|≥|≤|<|>)?\s*"
    r"(?:(?:AED|USD|EUR|GBP|\$|€|£)\s*)?"
    r"(?P<a>\d+(?:[.,]\d+)?)(?:\s*(?:and|to|-|–)\s*(?P<b>\d+(?:[.,]\d+)?))?\s*" + _UNITS + r"(?![a-z]))",
    re.IGNORECASE,
)
_CONDITION_RE = re.compile(r"\b(if|unless|only if|when|otherwise|except|provided that|in case|after|once|must)\b", re.IGNORECASE)
_STATE_RE = re.compile(r"\b(status|state|pending|active|inactive|locked|expired|cancel+ed|shipped|draft|approved|rejected|suspended|paid|refunded)\b", re.IGNORECASE)
_PARAM_RE = re.compile(r"\b(browsers?|devices?|roles?|payment methods?|currenc(?:y|ies)|languages?|locales?|platforms?|plans?|tiers?)\b", re.IGNORECASE)

Technique = Literal[
    "equivalence_partitioning", "boundary_value_analysis", "decision_table", "state_transition",
    "pairwise", "use_case", "error_guessing",
]
QualityCharacteristic = Literal[
    "functional_suitability", "performance_efficiency", "compatibility", "interaction_capability",
    "reliability", "security", "maintainability", "flexibility", "safety",
]


class TestCase(BaseModel):
    __test__ = False  # not a pytest test class

    id: str
    title: str
    type: Literal["positive", "negative", "boundary", "integration", "non_functional"]
    technique: Technique
    coverage_item: str
    quality_characteristic: QualityCharacteristic
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
    """3-value BVA (ISTQB): the boundary and both neighbours, at the value's own precision."""
    if re.fullmatch(r"\d{1,3}(,\d{3})+", value):
        value = value.replace(",", "")  # thousands separator
    value = value.replace(",", ".")
    if "." in value:
        places = len(value.split(".")[1])
        step = 10 ** -places
        v = float(value)
        return [round(v - step, places), v, round(v + step, places)]
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


def suggest_techniques(text: str, limits: list[dict]) -> list[str]:
    out = ["equivalence_partitioning: every input and output field"]
    if limits:
        out.append(f"boundary_value_analysis (3-value): {len(limits)} numeric limits found")
    conditions = len(_CONDITION_RE.findall(text))
    if conditions >= 2:
        out.append(f"decision_table: {conditions} conditional phrases (if/when/unless...) combine into rules")
    states = sorted({m.lower() for m in _STATE_RE.findall(text)})
    if states:
        out.append(f"state_transition: lifecycle terms found ({', '.join(states[:8])})")
    params = sorted({m.lower() for m in _PARAM_RE.findall(text)})
    if len(params) >= 2:
        out.append(f"pairwise: several independent parameters ({', '.join(params)})")
    return out


def uncovered_probes(limits: list[dict], cases) -> list[dict]:
    """Probe values that appear in no test case: a deterministic check of the generated suite."""
    corpus = " ".join(
        f"{c.title} {c.test_data} {' '.join(c.steps)} {c.coverage_item} {c.expected_result}" for c in cases
    )
    numbers = set(re.findall(r"-?\d+(?:\.\d+)?", corpus.replace(",", "")))
    numbers |= {n.rstrip("0").rstrip(".") for n in numbers if "." in n}
    missing = []
    for limit in limits:
        absent = [p for p in limit["probe_values"] if str(p) not in numbers and f"{p:g}" not in numbers]
        if absent:
            missing.append({"limit": limit["text"], "values_not_tested": absent})
    return missing


class TestCaseGenerationAgent(Agent):
    name = "test-case-generation"
    title = "Test Case Generation"
    summary = "Creates positive, negative, boundary and integration test cases from requirements."
    inputs_help = "requirement or user-story files (Markdown/text)"
    example_files = ["coupon_requirement.md"]
    output_model = TestSuite
    system_prompt = """Task: design a test suite from the requirements, as an ISTQB-trained test analyst.
Apply the suggested techniques and name the technique and coverage item on every case
(e.g. technique boundary_value_analysis, coverage item "subtotal = 99 AED (below min 100)").
Cover positive (happy paths), negative (one invalid input per test), boundary (EVERY locally
computed probe value must appear in a test), integration (other services, payments, notifications,
persistence, concurrency) and the non-functional cases the requirement implies (security,
performance, accessibility, reliability), tagged with the ISO 25010 characteristic.
Each case must be independent, have concrete test data and one observable expected result.
Number cases TC-001, TC-002... Prioritise P1 for revenue, security, data-loss or compliance risk.
Use coverage notes for gaps and contradictions in the requirement. List automation candidates and why."""

    def analyse(self, files):
        text = "\n".join(f.text() for f in files)
        limits = find_limits(text)
        return {"numeric_limits": limits, "suggested_techniques": suggest_techniques(text, limits)}

    def build_prompt(self, files, facts):
        docs = "\n\n".join(file_block(f) for f in files)
        return f"{docs}\n\n{facts_block(facts)}\n\nDesign the test suite."

    def finalise(self, output, facts, notes):
        cases = output.test_cases
        facts["cases_by_type"] = dict(Counter(tc.type for tc in cases))
        facts["cases_by_technique"] = dict(Counter(tc.technique for tc in cases))
        facts["cases_by_priority"] = dict(Counter(tc.priority for tc in cases))
        ids = [tc.id for tc in cases]
        if len(ids) != len(set(ids)):
            notes.append("Duplicate test case ids: " + ", ".join(sorted({i for i in ids if ids.count(i) > 1})))
        missing = uncovered_probes(facts["numeric_limits"], cases)
        if missing:
            facts["boundary_values_not_covered"] = missing
            notes.append(f"{sum(len(m['values_not_tested']) for m in missing)} boundary probe values are not used by any test case; see 'Boundary Values Not Covered'.")
        if not any(tc.type == "negative" for tc in cases):
            notes.append("The suite has no negative test cases.")
        return output
