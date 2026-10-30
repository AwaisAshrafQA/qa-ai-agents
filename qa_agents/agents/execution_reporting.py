"""9. Test Execution Reporting Agent: results, defect status and progress into a stakeholder QA report."""

from __future__ import annotations

from typing import Literal

import yaml
from pydantic import BaseModel

from qa_agents.core.base import Agent, by_suffix, facts_block
from qa_agents.core.llm import AgentError
from qa_agents.tools.defects import load_defects, summarise_defects
from qa_agents.tools.junit import parse_junit, summarise


class QAReport(BaseModel):
    headline: str
    status: Literal["on_track", "at_risk", "off_track"]
    executive_summary: str
    highlights: list[str]
    concerns: list[str]
    defect_commentary: str
    next_steps: list[str]


def progress_facts(progress: dict, executed: int) -> dict:
    planned = int(progress.get("planned_tests", 0) or 0)
    out = {k: v for k, v in progress.items() if k != "planned_tests"}
    if planned:
        out["planned_tests"] = planned
        out["executed_pct"] = round(100 * executed / planned, 1)
    return out


def results_facts(files) -> dict:
    reports = by_suffix(files, ".xml")
    if not reports:
        raise AgentError("At least one JUnit XML report is required.")
    results = []
    for f in reports:
        results += parse_junit(f.text())
    facts = {"results": summarise(results)}
    facts["failed_tests"] = [
        {"test": r.full_name, "message": r.message[:160]} for r in results if r.status in ("failed", "error")
    ]
    defects = []
    for f in by_suffix(files, ".csv"):
        defects += load_defects(f.text())
    if defects:
        facts["defects"] = summarise_defects(defects)
    return facts


class ExecutionReportingAgent(Agent):
    name = "execution-report"
    title = "Test Execution Report"
    summary = "Combines test results, defect status and progress into a QA report for stakeholders."
    inputs_help = "JUnit XML report(s), defects .csv and optional progress .yaml (planned_tests, sprint, dates)"
    example_files = ["results.xml", "defects.csv", "progress.yaml"]
    output_model = QAReport
    system_prompt = """Task: write the QA status report for engineering and product leads.
All numbers were computed locally: use them exactly, never recalculate or round differently.
Lead with the headline and status (on_track / at_risk / off_track) and justify it in two or three
sentences. Highlights and concerns must be specific (tests, modules, defect ids). Comment on
open critical and major defects and their impact. Next steps need an owner role and are
actionable this sprint. Keep it short enough to read in two minutes."""

    def analyse(self, files):
        facts = results_facts(files)
        for f in by_suffix(files, ".yaml", ".yml"):
            executed = facts["results"]["total"] - facts["results"]["skipped"]
            facts["progress"] = progress_facts(yaml.safe_load(f.text()) or {}, executed)
        return facts

    def build_prompt(self, files, facts):
        return f"{facts_block(facts)}\n\nWrite the QA report."
