"""10. Release Quality Analysis Agent: release-readiness report with deterministic quality gates."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from qa_agents.agents.execution_reporting import load_yaml, results_facts
from qa_agents.core.base import Agent, by_suffix, facts_block
from qa_agents.core.llm import AgentError

RISK_LEVEL = {"very high": 3, "high": 3, "medium": 2, "med": 2, "moderate": 2, "low": 1, "very low": 1}
KNOWN_CRITERIA = {
    "min_pass_rate": "Pass rate (%) of executed tests",
    "max_open_critical": "Open critical defects",
    "max_open_major": "Open major defects",
    "require_smoke_pass": "Smoke suite (any suite or test with 'smoke' in its name) fully green",
    "max_high_risks_without_mitigation": "High risks without a mitigation",
    "min_executed_pct": "Executed tests as a % of planned_tests (also set planned_tests)",
    "max_skipped": "Skipped tests",
    "max_flaky_passes": "Tests that passed only on rerun",
}


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


def _level(value) -> int | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return 3 if value >= 4 else 2 if value >= 3 else 1 if value >= 1 else None  # 1-5 scales
    return RISK_LEVEL.get(str(value).strip().lower())


def score_risks(raw: list) -> list[dict]:
    risks = []
    for i, r in enumerate(raw or []):
        if not isinstance(r, dict):
            raise AgentError(f"Risk #{i + 1} must be a mapping with description, likelihood, impact and mitigation.")
        likelihood, impact = _level(r.get("likelihood")), _level(r.get("impact"))
        if likelihood is None or impact is None:
            level, score = "high", None  # unknown is treated as high until someone rates it
        else:
            score = likelihood * impact
            level = "high" if score >= 6 else "medium" if score >= 3 else "low"
        risks.append({**r, "mitigation": (r.get("mitigation") or "").strip(), "score": score, "level": level,
                      **({"note": "likelihood or impact missing/unrecognised: treated as high"} if score is None else {})})
    return sorted(risks, key=lambda r: -(r["score"] or 99))


def _number(criteria: dict, key: str) -> float:
    value = criteria[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AgentError(f"Criterion '{key}' must be a number, got {value!r}.")
    return value


def evaluate_gates(criteria: dict, facts: dict) -> list[dict]:
    results = facts["results"]
    defects = facts.get("defects")
    gates = []

    def gate(name, target, actual, passed):
        gates.append({"gate": name, "target": target, "actual": actual, "passed": bool(passed)})

    if "min_pass_rate" in criteria:
        target = _number(criteria, "min_pass_rate")
        gate("Pass rate", f">= {target}%", f"{results['pass_rate_pct']}% of {results['executed']} executed",
             results["executed"] > 0 and results["pass_rate_pct"] >= target)
    for key, sev in (("max_open_critical", "critical"), ("max_open_major", "major")):
        if key in criteria:
            target = _number(criteria, key)
            if defects is None:
                gate(f"Open {sev} defects", f"<= {target:g}", "no defect data provided", False)
            else:
                actual = defects["open_by_severity"].get(sev, 0)
                gate(f"Open {sev} defects", f"<= {target:g}", actual, actual <= target)
    if criteria.get("require_smoke_pass"):
        smoke = results["smoke"]
        found = smoke["total"] > 0
        gate("Smoke suite green", "0 failures, 0 skipped",
             f"{smoke['failed']} failed, {smoke['skipped']} skipped of {smoke['total']}" if found else "no smoke tests found",
             found and smoke["failed"] == 0 and smoke["skipped"] == 0)
    if "max_high_risks_without_mitigation" in criteria:
        target = _number(criteria, "max_high_risks_without_mitigation")
        unmitigated = [r.get("id", r.get("description", "?")) for r in facts.get("risks", []) if r["level"] == "high" and not r["mitigation"]]
        gate("Unmitigated high risks", f"<= {target:g}", len(unmitigated), len(unmitigated) <= target)
    if "min_executed_pct" in criteria:
        target = _number(criteria, "min_executed_pct")
        planned = criteria.get("planned_tests")
        if not planned:
            gate("Executed vs planned", f">= {target}%", "planned_tests not set in criteria", False)
        else:
            pct = round(100 * results["executed"] / planned, 1)
            gate("Executed vs planned", f">= {target}%", f"{pct}% ({results['executed']}/{planned})", pct >= target)
    if "max_skipped" in criteria:
        target = _number(criteria, "max_skipped")
        gate("Skipped tests", f"<= {target:g}", results["skipped"], results["skipped"] <= target)
    if "max_flaky_passes" in criteria:
        target = _number(criteria, "max_flaky_passes")
        flaky = len(results.get("passed_only_on_rerun", []))
        gate("Passed only on rerun", f"<= {target:g}", flaky, flaky <= target)
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
Quality gates were evaluated locally against the team's criteria. A failed gate is a hard blocker
unless the criteria explicitly allow a waiver: never recommend 'go' while a gate fails.
Weigh open defects by user impact, the risk register (likelihood x impact, mitigations), skipped or
untested areas and which areas failed tests touch. List blocking issues, the exact, verifiable
conditions that would turn the decision into go, residual risks after release and recommendations
(monitoring, feature flags, rollback plan, hotfix window). Be direct: this goes to the release manager."""

    def analyse(self, files):
        facts = results_facts(files)
        criteria, risks, seen_criteria = {}, [], False
        for f in by_suffix(files, ".yaml", ".yml"):
            data = load_yaml(f)
            if "criteria" in data:
                seen_criteria = True
                criteria = data["criteria"] or {}
                if not isinstance(criteria, dict):
                    raise AgentError(f"'criteria' in {f.name} must be a mapping, e.g. min_pass_rate: 95.")
                facts["release"] = str(data.get("release", ""))
            if "risks" in data:
                risks += score_risks(data["risks"])
        if not seen_criteria or not criteria:
            options = "\n".join(f"  {k}: ...   # {v}" for k, v in KNOWN_CRITERIA.items())
            raise AgentError(f"release-readiness needs a criteria .yaml, e.g.\nrelease: 2.4.0\ncriteria:\n{options}")
        unknown = sorted(set(criteria) - set(KNOWN_CRITERIA) - {"planned_tests"})
        if unknown:
            facts["ignored_criteria"] = unknown
        facts["risks"] = risks
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
