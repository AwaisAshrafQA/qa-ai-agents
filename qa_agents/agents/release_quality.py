"""10. Release Quality Analysis Agent: release-readiness report with deterministic quality gates."""

from __future__ import annotations

from typing import Literal

import yaml
from pydantic import BaseModel

from qa_agents.agents.execution_reporting import results_facts
from qa_agents.core.base import Agent, by_suffix, facts_block
from qa_agents.core.llm import AgentError

RISK_LEVEL = {"high": 3, "medium": 2, "med": 2, "low": 1}


class RiskAssessment(BaseModel):
    risk: str
    level: Literal["high", "medium", "low"]
    mitigation: str


class ReleaseReadiness(BaseModel):
    decision: Literal["go", "go_with_conditions", "no_go"]
    confidence: Literal["high", "medium", "low"]
    rationale: str
    blocking_issues: list[str]
    conditions: list[str]
    residual_risks: list[RiskAssessment]
    recommendations: list[str]


def evaluate_gates(criteria: dict, facts: dict) -> list[dict]:
    results, defects = facts["results"], facts.get("defects", {})
    open_sev = defects.get("open_by_severity", {})
    gates = []

    def gate(name, target, actual, passed):
        gates.append({"gate": name, "target": target, "actual": actual, "passed": passed})

    if "min_pass_rate" in criteria:
        gate("Pass rate", f">= {criteria['min_pass_rate']}%", f"{results['pass_rate_pct']}%", results["pass_rate_pct"] >= criteria["min_pass_rate"])
    if "max_open_critical" in criteria:
        gate("Open critical defects", f"<= {criteria['max_open_critical']}", open_sev.get("critical", 0), open_sev.get("critical", 0) <= criteria["max_open_critical"])
    if "max_open_major" in criteria:
        gate("Open major defects", f"<= {criteria['max_open_major']}", open_sev.get("major", 0), open_sev.get("major", 0) <= criteria["max_open_major"])
    if criteria.get("require_smoke_pass"):
        smoke = [s for s in results["by_suite"] if "smoke" in s["suite"].lower()]
        failed = sum(s["failed"] for s in smoke)
        gate("Smoke suite green", "0 failures", f"{failed} failures" if smoke else "no smoke suite found", bool(smoke) and failed == 0)
    if "max_high_risks_without_mitigation" in criteria:
        unmitigated = [r for r in facts.get("risks", []) if r["level"] == "high" and not r.get("mitigation")]
        gate("Unmitigated high risks", f"<= {criteria['max_high_risks_without_mitigation']}", len(unmitigated), len(unmitigated) <= criteria["max_high_risks_without_mitigation"])
    return gates


class ReleaseQualityAgent(Agent):
    name = "release-readiness"
    title = "Release Readiness"
    summary = "Uses test results, unresolved defects and risks to produce a release-readiness report."
    inputs_help = "JUnit XML report(s), defects .csv, risks .yaml and release criteria .yaml"
    example_files = ["results.xml", "defects.csv", "risks.yaml", "criteria.yaml"]
    output_model = ReleaseReadiness
    guardrails = ["If facts.all_gates_passed is false, the decision must not be 'go'."]
    system_prompt = """Task: recommend go / go_with_conditions / no_go for a release.
Quality gates were evaluated locally against the team's criteria. A failed gate is a hard
blocker unless the criteria explicitly allow a waiver: never recommend 'go' while a gate fails.
Weigh open defects by user impact, the risk register (likelihood x impact, mitigations) and
which areas failed tests touch. List blocking issues, the exact conditions that would turn the
decision into go, residual risks after release and recommendations (monitoring, feature flags,
rollback plan, hotfix window). Be direct: this report goes to the release manager."""

    def analyse(self, files):
        facts = results_facts(files)
        criteria, risks = {}, []
        for f in by_suffix(files, ".yaml", ".yml"):
            data = yaml.safe_load(f.text()) or {}
            if "criteria" in data:
                criteria = data["criteria"]
                facts["release"] = data.get("release", "")
            if "risks" in data:
                for r in data["risks"]:
                    score = RISK_LEVEL.get(str(r.get("likelihood", "")).lower(), 1) * RISK_LEVEL.get(str(r.get("impact", "")).lower(), 1)
                    level = "high" if score >= 6 else "medium" if score >= 3 else "low"
                    risks.append({**r, "score": score, "level": level})
        if not criteria:
            raise AgentError("release-readiness needs a criteria .yaml with a 'criteria:' section.")
        facts["risks"] = sorted(risks, key=lambda r: -r["score"])
        facts["gates"] = evaluate_gates(criteria, facts)
        facts["all_gates_passed"] = all(g["passed"] for g in facts["gates"])
        return facts

    def build_prompt(self, files, facts):
        return f"{facts_block(facts)}\n\nAssess release readiness."

    def finalise(self, output, facts, notes):
        if not facts["all_gates_passed"] and output.decision == "go":
            failed = ", ".join(g["gate"] for g in facts["gates"] if not g["passed"])
            output.decision = "no_go"
            output.blocking_issues.insert(0, f"Failed quality gates: {failed}")
            notes.append(f"Decision changed from 'go' to 'no_go' because these gates failed: {failed}.")
        return output
