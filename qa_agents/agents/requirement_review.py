"""1. Requirement Review Agent: finds missing acceptance criteria, edge cases and unclear wording."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel

from qa_agents.core.base import Agent, facts_block, file_block

VAGUE_TERMS = [
    "should", "fast", "quickly", "user-friendly", "easy", "easily", "appropriate", "etc",
    "as needed", "some", "various", "normally", "approximately", "optimal", "seamless",
    "intuitive", "robust", "tbd", "if possible", "and/or", "reasonable",
]
_VAGUE_RE = re.compile(r"\b(" + "|".join(re.escape(t) for t in VAGUE_TERMS) + r")\b", re.IGNORECASE)
_GWT_RE = re.compile(r"^\s*(?:[-*]|\d+\.)?\s*(given|when|then)\b", re.IGNORECASE)


class Issue(BaseModel):
    story: str
    category: Literal["missing_acceptance_criteria", "edge_case", "ambiguity", "contradiction", "non_functional", "dependency"]
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


def story_facts(title: str, body: list[str]) -> dict:
    criteria, in_ac = 0, False
    for line in body:
        if re.search(r"acceptance criteria", line, re.IGNORECASE):
            in_ac = True
            continue
        if in_ac and re.match(r"^\s*(?:[-*]|\d+\.)\s+\S", line):
            criteria += 1
        elif in_ac and line.strip() and not line.startswith(" ") and line.strip().endswith(":"):
            in_ac = False
    vague = sorted({m.group(1).lower() for line in body + [title] for m in _VAGUE_RE.finditer(line)})
    return {
        "story": title,
        "acceptance_criteria_count": criteria,
        "given_when_then_lines": sum(1 for line in body if _GWT_RE.match(line)),
        "vague_terms": vague,
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
Find: missing or untestable acceptance criteria, unhandled edge cases (empty, max, concurrent,
offline, permissions, time zones, currency, localisation), ambiguous wording, contradictions,
missing non-functional requirements (performance, security, accessibility) and hidden dependencies.
Phrase each finding as a concrete question the product owner can answer.
Suggest acceptance criteria in Given/When/Then form, testable and measurable."""

    def analyse(self, files):
        stories = []
        for f in files:
            stories += [story_facts(t, b) for t, b in split_stories(f.text())]
        return {"story_count": len(stories), "stories": stories}

    def build_prompt(self, files, facts):
        docs = "\n\n".join(file_block(f) for f in files)
        return f"{docs}\n\n{facts_block(facts)}\n\nReview every story above."
