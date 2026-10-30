"""4. Automation Code Review Agent: hardcoded data, weak assertions, unstable locators, fixed waits, duplication."""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from typing import Literal

from pydantic import BaseModel

from qa_agents.core.base import Agent, facts_block, file_block

Rule = Literal["fixed_wait", "unstable_locator", "hardcoded_data", "weak_assertion", "duplicate_code", "other"]

RULES: dict[str, list[re.Pattern]] = {
    "fixed_wait": [
        re.compile(r"Thread\.sleep\s*\("),
        re.compile(r"\btime\.sleep\s*\("),
        re.compile(r"waitForTimeout\s*\("),
        re.compile(r"cy\.wait\(\s*\d"),
        re.compile(r"\bsetTimeout\s*\("),
        re.compile(r"\bTask\.Delay\s*\(|\bThread\.Sleep\s*\("),
    ],
    "unstable_locator": [
        re.compile(r"[\"'](?:xpath=)?/html/"),
        re.compile(r"[\"'](?:xpath=)?//[^\"']*\[\d+\]"),
        re.compile(r":nth-child\(\d+\)|:nth-of-type\(\d+\)"),
        re.compile(r"[\"'][^\"']*(?:\b(?:div|span)\s*>\s*){2,}"),
        re.compile(r"\.css-[a-z0-9]{5,}|\bjss\d+|\bsc-[a-zA-Z]{5,}"),
    ],
    "hardcoded_data": [
        re.compile(r"[\"'][\w.+-]+@[\w-]+\.[\w.]+[\"']"),
        re.compile(r"(?i)(password|passwd|pwd|secret|token|api[_-]?key)[\"']?\s*[,:=]\s*[\"'][^\"']{3,}[\"']"),
        re.compile(r"[\"']https?://[^\"']+[\"']"),
        re.compile(r"[\"']\d{13,19}[\"']"),
    ],
    "weak_assertion": [
        re.compile(r"\bassert\s+True\b|assertTrue\(\s*true\s*\)"),
        re.compile(r"\.toBeTruthy\(\)|\.toBeDefined\(\)|\.not\.toBeNull\(\)"),
        re.compile(r"\bassertNotNull\s*\("),
        re.compile(r"\.should\(\s*[\"']exist[\"']\s*\)"),
        re.compile(r"assert\s+len\([^)]*\)\s*>\s*0|\.length\)\.toBeGreaterThan\(0\)"),
        re.compile(r"statusCode\(\s*greaterThan|\.status\)\.toBeLessThan\(500\)"),
    ],
}


class ReviewComment(BaseModel):
    file: str
    line: int
    rule: Rule
    severity: Literal["high", "medium", "low"]
    problem: str
    fix: str


class CodeReview(BaseModel):
    summary: str
    verdict: Literal["approve", "approve_with_comments", "request_changes"]
    comments: list[ReviewComment]
    refactoring_suggestions: list[str]


def scan_lines(file: str, lines: list[str]) -> list[dict]:
    findings = []
    for no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith(("//", "#", "*")):
            continue
        for rule, patterns in RULES.items():
            if any(p.search(line) for p in patterns):
                findings.append({"file": file, "line": no, "rule": rule, "code": stripped[:140]})
    return findings


def find_duplicates(file: str, lines: list[str], window: int = 4) -> list[dict]:
    """Blocks of `window` meaningful lines that appear more than once."""
    meaningful = [(i + 1, re.sub(r"\s+", " ", l.strip())) for i, l in enumerate(lines)]
    meaningful = [(n, l) for n, l in meaningful if len(l) > 8 and l not in ("});", "})", "end", "}")]
    seen: dict[str, int] = {}
    findings, last_reported = [], -10
    for i in range(len(meaningful) - window + 1):
        chunk = meaningful[i : i + window]
        key = hashlib.sha1("\n".join(l for _, l in chunk).encode()).hexdigest()
        if key in seen and chunk[0][0] > last_reported + window:
            findings.append(
                {
                    "file": file,
                    "line": chunk[0][0],
                    "rule": "duplicate_code",
                    "code": f"lines {chunk[0][0]}-{chunk[-1][0]} repeat lines starting at {seen[key]}",
                }
            )
            last_reported = chunk[0][0]
        seen.setdefault(key, chunk[0][0])
    return findings


class CodeReviewAgent(Agent):
    name = "code-review"
    title = "Automation Code Review"
    summary = "Flags hardcoded data, weak assertions, unstable locators, fixed waits and duplicate code."
    inputs_help = "test automation source files (.java, .ts, .js, .py, .cs ...)"
    example_files = ["checkout.spec.ts", "LoginTest.java"]
    output_model = CodeReview
    system_prompt = """Task: review test automation code like a senior SDET in a pull request.
The static scan already found candidate lines: confirm or dismiss each one, and add issues the scan
cannot see (missing assertions, order-dependent tests, no cleanup, shared state, poor naming,
logic in tests, missing waits on network/API, swallowed exceptions).
For every comment give the exact line and a concrete fix (code snippet or approach): e.g. replace
fixed waits with web-first assertions or explicit waits, use role/test-id locators, move data to
fixtures/env/secrets, assert exact values and schemas, extract duplicated steps to page objects
or helpers. Ignore duplicates that are only imports or brackets."""

    def analyse(self, files):
        findings = []
        for f in files:
            lines = f.lines()
            findings += scan_lines(f.name, lines) + find_duplicates(f.name, lines)
        findings.sort(key=lambda x: (x["file"], x["line"]))
        return {"static_findings_by_rule": dict(Counter(x["rule"] for x in findings)), "static_findings": findings}

    def build_prompt(self, files, facts):
        code = "\n\n".join(file_block(f, numbered=True) for f in files)
        return f"{code}\n\n{facts_block(facts)}\n\nReview this automation code."
