"""1. Requirement Review Agent: finds missing acceptance criteria, edge cases and unclear wording.

Ambiguity terms come from the NASA ARM tool (Wilson, 1997) and the requirements-smell categories
of Femmer et al. (JSS 2017); structural checks follow INVEST and ISTQB CTFL v4.0.1.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel

from qa_agents.core.base import Agent, facts_block, file_block

AMBIGUITY = {
    "weak_phrase": [
        "adequate", "as a minimum", "as applicable", "as appropriate", "appropriate", "be able to", "be capable",
        "but not limited to", "capability of", "capability to", "effective", "if practical", "normal", "normally",
        "provide for", "timely", "tbd", "tbc",
    ],
    "optional": ["can", "may", "optionally", "should", "could", "might"],
    "subjective": [
        "user friendly", "user-friendly", "easy", "easily", "easy to use", "simple", "intuitive", "seamless",
        "fast", "quick", "quickly", "slow", "robust", "flexible", "efficient", "cost effective", "nice", "modern", "clean",
    ],
    "loophole": ["as far as possible", "if possible", "where possible", "where feasible", "if needed", "as needed", "as required", "reasonable"],
    "superlative": ["best", "highest", "lowest", "fastest", "optimal", "maximum possible", "minimum possible", "always", "never"],
    "open_ended": ["etc", "and so on", "and/or", "some", "various", "several", "many", "few", "approximately", "about", "around", "similar"],
}
_TERM_RE = {
    cat: re.compile(r"(?<![\w-])(" + "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True)) + r")(?![\w-])", re.IGNORECASE)
    for cat, terms in AMBIGUITY.items()
}
_GWT_RE = re.compile(r"^\s*(?:[-*]|\d+\.)?\s*(given|when|then)\b", re.IGNORECASE)
_STORY_RE = re.compile(r"\bas an?\b.+\bi (?:want|need|can)\b", re.IGNORECASE)
_BENEFIT_RE = re.compile(r"\bso that\b|\bin order to\b", re.IGNORECASE)
_NEGATIVE_AC_RE = re.compile(r"\b(invalid|error|fail|fails|reject|declin|expired|not allowed|cannot|can't|unauthori|denied|empty|missing|exceed|limit)\w*", re.IGNORECASE)
_NFR_RE = re.compile(r"\b(seconds?|ms|response time|performance|load|secur|encrypt|permission|role|audit|log|accessib|wcag|screen reader|availability|uptime|gdpr|pii|privacy)\w*", re.IGNORECASE)
_SENSITIVE_RE = re.compile(r"\b(pay|payment|card|checkout|price|discount|coupon|refund|password|login|personal|address|email|phone|upload)\w*", re.IGNORECASE)


class Issue(BaseModel):
    story: str
    category: Literal[
        "missing_acceptance_criteria", "edge_case", "ambiguity", "contradiction", "non_functional",
        "dependency", "testability", "story_structure",
    ]
    severity: Literal["high", "medium", "low"]
    finding: str
    question_for_product_owner: str


class StoryVerdict(BaseModel):
    story: str
    readiness: Literal["ready", "needs_clarification", "not_ready"]
    reason: str


class SuggestedCriterion(BaseModel):
    story: str
    criterion: str


class RequirementReview(BaseModel):
    summary: str
    stories: list[StoryVerdict]
    issues: list[Issue]
    suggested_acceptance_criteria: list[SuggestedCriterion]


def split_stories(text: str) -> list[tuple[str, list[str]]]:
    stories: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        heading = re.match(r"^#{1,3}\s+(.*)", line)
        if heading:
            stories.append((heading.group(1).strip(), []))
        elif stories:
            stories[-1][1].append(line)
    return stories or [("Requirements", text.splitlines())]


def acceptance_criteria(body: list[str]) -> list[str]:
    criteria, in_ac = [], False
    for line in body:
        if re.search(r"acceptance criteria|^\s*AC\s*:", line, re.IGNORECASE):
            in_ac = True
            continue
        bullet = re.match(r"^\s*(?:[-*]|\d+[.)])\s+(\S.*)", line)
        if in_ac and bullet:
            criteria.append(bullet.group(1))
        elif in_ac and line.strip() and not bullet and line.strip().endswith(":"):
            in_ac = False
    criteria += [l.strip() for l in body if _GWT_RE.match(l) and l.strip() not in criteria and not re.match(r"^\s*(?:[-*]|\d+[.)])", l)]
    return criteria


def story_facts(title: str, body: list[str]) -> dict:
    text = "\n".join([title, *body])
    criteria = acceptance_criteria(body)
    ambiguous = {}
    for cat, rx in _TERM_RE.items():
        found = sorted({m.group(1).lower() for m in rx.finditer(text)})
        if found:
            ambiguous[cat] = found
    checks = []
    if not criteria:
        checks.append("no acceptance criteria")
    elif not any(_NEGATIVE_AC_RE.search(c) for c in criteria):
        checks.append("acceptance criteria cover only positive scenarios")
    if _STORY_RE.search(text) and not _BENEFIT_RE.search(text):
        checks.append("no 'so that' benefit (INVEST: Valuable)")
    if not _STORY_RE.search(text) and len(text) > 40:
        checks.append("not written as 'As a <role>, I want <goal>, so that <benefit>'")
    if len(criteria) > 10:
        checks.append(f"{len(criteria)} acceptance criteria: may be too large to estimate (INVEST: Small)")
    if re.search(r"\b(and|or)\b", title, re.IGNORECASE) and not re.search(r"\b(and|or)\b.*\b(and|or)\b", title, re.IGNORECASE) and len(title.split()) > 4:
        checks.append("title joins two goals with and/or: may not be singular")
    if _SENSITIVE_RE.search(text) and not _NFR_RE.search(text):
        checks.append("touches money, accounts or personal data but states no non-functional requirement")
    return {
        "story": title,
        "acceptance_criteria_count": len(criteria),
        "given_when_then_lines": sum(1 for line in body if _GWT_RE.match(line)),
        "ambiguous_terms": ambiguous,
        "structural_checks": checks,
    }


class RequirementReviewAgent(Agent):
    name = "requirement-review"
    title = "Requirement Review"
    summary = "Reviews user stories for missing acceptance criteria, edge cases and unclear requirements."
    inputs_help = "one or more Markdown/text files of user stories (one '#' heading per story)"
    example_files = ["stories.md"]
    output_model = RequirementReview
    system_prompt = """Task: review user stories before sprint planning, as a QA engineer in refinement.
For each story decide if it is ready for development and testing.
Use the locally computed ambiguous terms and structural checks as leads (dismiss false positives,
e.g. "can" in "the shopper can enter a code" is fine), then apply the expert checklist: requirement
quality (29148), INVEST, acceptance-criteria quality, edge-case heuristics, non-functional needs
(ISO 25010, WCAG 2.2 AA) and contradictions between stories. Phrase each finding as a concrete
question the product owner can answer. Suggest acceptance criteria in Given/When/Then form with
concrete values, covering negative scenarios too.
Readiness: not_ready if there are no usable acceptance criteria or a high-severity gap;
needs_clarification for open questions that would change the tests; ready otherwise."""

    def analyse(self, files):
        stories = []
        for f in files:
            stories += [story_facts(t, b) for t, b in split_stories(f.text())]
        return {"story_count": len(stories), "stories": stories}

    def build_prompt(self, files, facts):
        docs = "\n\n".join(file_block(f) for f in files)
        return f"{docs}\n\n{facts_block(facts)}\n\nReview every story above."
