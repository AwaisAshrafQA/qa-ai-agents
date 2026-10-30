"""4. Automation Code Review Agent: test smells, flaky patterns and hygiene problems in test code.

Static rules follow the test-smell catalogue (van Deursen et al. 2001; tsDetect, Peruma et al.),
the official Playwright / Cypress / Selenium guidance and the OWASP Secrets Management Cheat Sheet.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from typing import Literal

from pydantic import BaseModel

from qa_agents.core.base import Agent, facts_block, file_block

Rule = Literal[
    "fixed_wait", "discouraged_wait", "mixed_waits", "unstable_locator", "hardcoded_secret",
    "hardcoded_data", "weak_assertion", "non_retrying_assertion", "missing_assertion",
    "focused_test", "skipped_test", "forced_action", "swallowed_exception", "conditional_logic",
    "debug_output", "duplicate_code", "test_isolation", "other",
]

# rule -> (default severity, patterns)
RULES: dict[str, tuple[str, list[re.Pattern]]] = {
    "fixed_wait": ("high", [
        re.compile(r"Thread\.sleep\s*\("),
        re.compile(r"\btime\.sleep\s*\("),
        re.compile(r"waitForTimeout\s*\("),
        re.compile(r"cy\.wait\(\s*\d"),
        re.compile(r"\bTask\.Delay\s*\(|\bThread\.Sleep\s*\("),
        re.compile(r"new Promise\(\s*\(?\w*\)?\s*=>\s*setTimeout"),
        re.compile(r"\bsleep\(\s*\d"),
    ]),
    "discouraged_wait": ("medium", [
        re.compile(r"""waitUntil\s*:\s*['"]networkidle['"]"""),
        re.compile(r"waitForLoadState\(\s*['\"]networkidle['\"]"),
    ]),
    "mixed_waits": ("medium", [re.compile(r"implicitlyWait\s*\(|ImplicitWait\s*=|implicitly_wait\s*\(")]),
    "unstable_locator": ("high", [
        re.compile(r"""["'](?:xpath=)?/html/"""),
        re.compile(r"""["'](?:xpath=)?//[^"']*\[\d+\]"""),
        re.compile(r":nth-child\(\d+\)|:nth-of-type\(\d+\)|\.nth\(\d+\)|\.eq\(\d+\)"),
        re.compile(r"""["'][^"']*(?:\b(?:div|span)\s*>\s*){2,}"""),
        re.compile(r"\.css-[a-z0-9]{5,}|\bjss\d+|\bsc-[a-zA-Z]{5,}|\bMui\w+-root-\d+"),
    ]),
    "hardcoded_secret": ("high", [
        re.compile(r"AKIA[0-9A-Z]{16}"),
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        re.compile(r"eyJ[\w-]{10,}\.[\w-]{10,}\.[\w-]{10,}"),
        re.compile(r"Bearer\s+[A-Za-z0-9._~+/-]{20,}"),
        re.compile(r"""(?i)\b(password|passwd|pwd|secret|api[_-]?key|access[_-]?token|client[_-]?secret)\w*["']?\s*[,:=]\s*["'][^"'\s]{4,}["']"""),
        re.compile(r"""(?i)#(?:password|pwd)\b.*\b(?:sendKeys|fill|type)\(\s*["'][^"']{4,}["']"""),
        re.compile(r"""(?i)\b(?:password|pwd)["']?\)\)?\.(?:sendKeys|fill|type)\(\s*["'][^"']{4,}["']"""),
    ]),
    "hardcoded_data": ("medium", [
        re.compile(r"""["'][\w.+-]+@[\w-]+\.[\w.]+["']"""),
        re.compile(r"""["']https?://[^"']+["']"""),
    ]),
    "weak_assertion": ("high", [
        re.compile(r"\bassert\s+True\b|assertTrue\(\s*true\s*\)|expect\(\s*true\s*\)\.toBe\(\s*true\s*\)"),
        re.compile(r"assert(?:Equals|That)?\(\s*(\w+)\s*,\s*\1\s*\)"),
        re.compile(r"\.toBeTruthy\(\)|\.toBeDefined\(\)|\.not\.toBeNull\(\)|\.not\.toBeUndefined\(\)"),
        re.compile(r"\bassertNotNull\s*\("),
        re.compile(r"""\.should\(\s*["']exist["']\s*\)"""),
        re.compile(r"assert\s+len\([^)]*\)\s*>\s*0|\.length\)\.toBeGreaterThan\(0\)|toHaveLength\.?\(?greaterThan"),
        re.compile(r"statusCode\(\s*(?:greaterThan|lessThan)|\.status\(?\)?\)\.toBeLessThan\(\s*500\s*\)|status_code\s*<\s*500"),
        re.compile(r"^\s*assert\s+\w+(\.\w+)*\s*$"),
    ]),
    "non_retrying_assertion": ("medium", [
        re.compile(r"expect\(\s*await\s+.*?\.(?:isVisible|isEnabled|isChecked|isHidden|isEditable|textContent|innerText|inputValue|getAttribute|count)\("),
    ]),
    "focused_test": ("high", [re.compile(r"\b(?:test|it|describe|context)\.only\s*\(|\bf(?:it|describe)\s*\(")]),
    "skipped_test": ("low", [re.compile(r"\b(?:test|it|describe)\.skip\s*\(|\bx(?:it|describe)\s*\(|@Ignore\b|@Disabled\b|pytest\.mark\.skip|@unittest\.skip|\[Ignore\]")]),
    "forced_action": ("medium", [
        re.compile(r"force\s*:\s*true"),
        re.compile(r"""executeScript\(\s*["']arguments\[0\]\.click\(\)"""),
    ]),
    "swallowed_exception": ("high", [
        re.compile(r"catch\s*\([^)]*\)\s*\{\s*\}"),
        re.compile(r"except(?:\s+\w+(?:\s+as\s+\w+)?)?\s*:\s*pass\b"),
        re.compile(r"\.catch\(\s*\(\)\s*=>\s*\{?\s*\}?\s*\)"),
    ]),
    "debug_output": ("low", [re.compile(r"console\.log\(|System\.out\.print|\bprint\(|cy\.pause\(\)|page\.pause\(\)|debugger;")]),
}

TEST_START = re.compile(
    r"^\s*(?:(?:test|it)(?:\.(?:only|skip|fixme|fail|slow))?\s*\(\s*['\"`]|(?:async\s+)?def\s+test_\w*\s*\(|@Test\b|\[(?:Test|Fact|TestMethod)\])"
)
ASSERTION = re.compile(
    r"\b(?:assert\w*|expect|should|verify\w*|validate\w*|softly)\b|toHave|toBe|toEqual|toMatch|statusCode\(|\.then\(\)\.",
)
CONTROL_FLOW = re.compile(r"^\s*(?:if|for|while|switch)\s*\(|^\s*(?:if|for|while)\s+[^:]+:\s*$")


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


def luhn_valid(digits: str) -> bool:
    total, parity = 0, len(digits) % 2
    for i, ch in enumerate(digits):
        d = int(ch)
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def code_lines(lines: list[str]) -> list[tuple[int, str]]:
    """(line number, code) for lines that are not comments; handles // # and /* */ blocks."""
    out, in_block = [], False
    for no, line in enumerate(lines, start=1):
        s = line.strip()
        if in_block:
            if "*/" in s:
                in_block = False
            continue
        if s.startswith("/*"):
            in_block = "*/" not in s
            continue
        if not s or s.startswith(("//", "#", "*")):
            continue
        out.append((no, line))
    return out


def scan_lines(file: str, lines: list[str]) -> list[dict]:
    findings = []
    for no, line in code_lines(lines):
        stripped = line.strip()
        hit_secret = False
        for rule, (severity, patterns) in RULES.items():
            if rule == "hardcoded_data" and hit_secret:
                continue  # a secret on this line is already reported
            if any(p.search(line) for p in patterns):
                findings.append({"file": file, "line": no, "rule": rule, "severity": severity, "code": stripped[:140]})
                hit_secret = hit_secret or rule == "hardcoded_secret"
        for m in re.finditer(r"""["'](\d{13,19})["']""", line):
            if luhn_valid(m.group(1)):
                findings.append({"file": file, "line": no, "rule": "hardcoded_data", "severity": "high", "code": "card-number-like value (passes Luhn check)"})
    return findings


def scan_test_blocks(file: str, lines: list[str]) -> list[dict]:
    """Per-test checks: tests with no assertion and tests with control flow."""
    starts = [no for no, line in code_lines(lines) if TEST_START.search(line)]
    findings = []
    for i, start in enumerate(starts):
        end = starts[i + 1] - 1 if i + 1 < len(starts) else len(lines)
        body = lines[start - 1 : end]
        text = "\n".join(body)
        if not ASSERTION.search(text):
            findings.append({"file": file, "line": start, "rule": "missing_assertion", "severity": "high", "code": lines[start - 1].strip()[:140]})
        for offset, line in enumerate(body[1:], start=start + 1):
            if CONTROL_FLOW.search(line):
                findings.append({"file": file, "line": offset, "rule": "conditional_logic", "severity": "medium", "code": line.strip()[:140]})
                break
    return findings


def find_duplicates(file: str, lines: list[str], window: int = 4) -> list[dict]:
    """Blocks of `window` meaningful lines that appear more than once."""
    meaningful = [(n, re.sub(r"\s+", " ", l.strip())) for n, l in code_lines(lines)]
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
                    "severity": "medium",
                    "code": f"lines {chunk[0][0]}-{chunk[-1][0]} repeat lines starting at {seen[key]}",
                }
            )
            last_reported = chunk[0][0]
        seen.setdefault(key, chunk[0][0])
    return findings


def suite_level_findings(files: dict[str, list[str]]) -> list[dict]:
    """Cross-file checks, e.g. Selenium implicit waits mixed with explicit waits."""
    text = "\n".join("\n".join(l) for l in files.values())
    out = []
    if re.search(r"implicitlyWait|implicitly_wait|ImplicitWait", text) and re.search(r"WebDriverWait|FluentWait", text):
        out.append({"file": "(suite)", "line": 0, "rule": "mixed_waits", "severity": "high",
                    "code": "implicit and explicit waits are both used; Selenium docs: do not mix them"})
    return out


class CodeReviewAgent(Agent):
    name = "code-review"
    title = "Automation Code Review"
    summary = "Flags hardcoded data, weak assertions, unstable locators, fixed waits and duplicate code."
    inputs_help = "test automation source files (.java, .ts, .js, .py, .cs ...)"
    example_files = ["checkout.spec.ts", "LoginTest.java"]
    output_model = CodeReview
    system_prompt = """Task: review test automation code like a senior SDET in a pull request.
The static scan found candidate problems with rule, line and default severity. Confirm or dismiss
each one (a URL in a config file or a skip with a linked ticket may be fine), and add the issues a
scan cannot see, using the expert checklist below. Every comment needs the exact line and a
concrete fix that uses the project's own framework idioms (code snippet or approach).
Verdict: request_changes if any high-severity issue remains; approve_with_comments for only
medium/low; approve only when nothing material is left. Ignore duplicates of imports or brackets."""

    def analyse(self, files):
        findings, all_lines = [], {}
        for f in files:
            lines = f.lines()
            all_lines[f.name] = lines
            findings += scan_lines(f.name, lines) + scan_test_blocks(f.name, lines) + find_duplicates(f.name, lines)
        findings += suite_level_findings(all_lines)
        findings.sort(key=lambda x: (x["file"], x["line"]))
        return {
            "files_reviewed": len(files),
            "static_findings_by_rule": dict(Counter(x["rule"] for x in findings)),
            "static_findings_by_severity": dict(Counter(x["severity"] for x in findings)),
            "static_findings": findings,
        }

    def build_prompt(self, files, facts):
        code = "\n\n".join(file_block(f, numbered=True) for f in files)
        return f"{code}\n\n{facts_block(facts)}\n\nReview this automation code."
