"""9. Test Execution Reporting Agent: results, defect status and progress into a stakeholder QA report."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

import yaml
from pydantic import BaseModel

from qa_agents.core.base import Agent, by_suffix, facts_block
from qa_agents.core.llm import AgentError
from qa_agents.tools.defects import is_open, load_defects, summarise_defects
from qa_agents.tools.junit import parse_junit, summarise


class QAReport(BaseModel):
    headline: str
    status: Literal["on_track", "at_risk", "off_track"]
    executive_summary: str
    highlights: list[str]
    concerns: list[str]
    defect_commentary: str
    next_steps: list[str]


def _age_days(created: str, today: date) -> int | None:
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y", "%d/%b/%y %I:%M %p"):
        try:
            return (today - datetime.strptime(created.strip(), fmt).date()).days
        except ValueError:
            continue
    return None


def load_yaml(f) -> dict:
    try:
        data = yaml.safe_load(f.text()) or {}
    except yaml.YAMLError as exc:
        raise AgentError(f"{f.name} is not valid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise AgentError(f"{f.name} must be a YAML mapping (key: value).")
    return data


def results_facts(files, today: date | None = None) -> dict:
    reports = by_suffix(files, ".xml")
    if not reports:
        raise AgentError("At least one JUnit XML report is required.")
    results = []
    for f in reports:
        results += parse_junit(f.text(), f.name)
    facts = {"results": summarise(results)}
    facts["failed_tests"] = [
        {"test": r.full_name, "message": r.message[:160]} for r in results if r.status in ("failed", "error")
    ]
    skipped = [{"test": r.full_name, "reason": r.message[:120]} for r in results if r.status == "skipped"]
    if skipped:
        facts["skipped_tests"] = skipped
    defects = []
    for f in by_suffix(files, ".csv"):
        defects += load_defects(f.text(), f.name)
    if defects:
        facts["defects"] = summarise_defects(defects)
        today = today or date.today()
        ages = []
        for d in defects:
            if is_open(d) and d.get("severity") in ("critical", "major") and d.get("created"):
                age = _age_days(d["created"], today)
                if age is not None:
                    ages.append({"id": d.get("id", ""), "severity": d["severity"], "age_days": age})
        if ages:
            facts["defects"]["open_critical_major_age_days"] = ages
    return facts


def progress_facts(progress: dict, executed: int) -> dict:
    out = {k: v for k, v in progress.items() if k != "planned_tests"}
    try:
        planned = int(progress.get("planned_tests") or 0)
    except (TypeError, ValueError):
        raise AgentError("planned_tests in the progress file must be a whole number.")
    if planned:
        out["planned_tests"] = planned
        out["executed_pct"] = round(100 * executed / planned, 1)
        out["not_run"] = max(planned - executed, 0)
    return out


class ExecutionReportingAgent(Agent):
    name = "execution-report"
    title = "Test Execution Report"
    summary = "Combines test results, defect status and progress into a QA report for stakeholders."
    inputs_help = "JUnit XML report(s), defects .csv and optional progress .yaml (planned_tests, sprint, test_window, environment)"
    example_files = ["results.xml", "defects.csv", "progress.yaml"]
    output_model = QAReport
    system_prompt = """Task: write the QA status report for engineering and product leads.
All numbers were computed locally: use them exactly, never recalculate or round differently.
Lead with the headline and status (on_track / at_risk / off_track) and justify it in two or three
sentences, using the status rules in the expert checklist. Report failed, skipped and not-run tests
separately: untested is not passed. Highlights and concerns must be specific (tests, modules,
defect ids). Comment on open critical and major defects, their impact and age. Next steps need an
owner role and are actionable this period. Keep it short enough to read in two minutes."""

    def analyse(self, files):
        facts = results_facts(files)
        for f in by_suffix(files, ".yaml", ".yml"):
            executed = facts["results"]["executed"]
            facts["progress"] = progress_facts(load_yaml(f), executed)
        return facts

    def build_prompt(self, files, facts):
        return f"{facts_block(facts)}\n\nWrite the QA report."
