"""8. Regression Test Selection Agent: code changes + module map + defect history into a ranked test plan."""

from __future__ import annotations

import fnmatch
import re
from typing import Literal

import yaml
from pydantic import BaseModel

from qa_agents.core.base import Agent, facts_block
from qa_agents.core.llm import AgentError
from qa_agents.tools.defects import load_defects

PRIORITY_WEIGHT = {"P1": 30, "P2": 20, "P3": 10}
SEVERITY_WEIGHT = {"critical": 10, "major": 6, "minor": 2, "trivial": 1}


class Recommendation(BaseModel):
    test_id: str
    decision: Literal["must_run", "should_run", "optional"]
    reason: str


class RegressionPlan(BaseModel):
    summary: str
    recommendations: list[Recommendation]
    additional_risks: list[str]
    unmapped_change_advice: list[str]
    estimated_scope: str


def parse_changes(text: str) -> list[str]:
    """Accepts `git diff --name-only`, `--name-status` or `--stat` output."""
    paths = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" in line:  # --stat: "src/a.ts | 12 +++--"
            line = line.split("|")[0]
        token = line.split()[-1]  # --name-status: "M\tsrc/a.ts"
        if "/" in token or re.search(r"\.\w+$", token):
            paths.append(token)
    return paths


def select_tests(changes: list[str], test_map: dict, defects: list[dict]) -> dict:
    modules = test_map.get("modules") or {}
    changed_modules: dict[str, list[str]] = {}
    unmapped = []
    for path in changes:
        hits = [m for m, cfg in modules.items() if any(fnmatch.fnmatch(path, g) for g in cfg.get("paths", []))]
        for m in hits:
            changed_modules.setdefault(m, []).append(path)
        if not hits:
            unmapped.append(path)
    indirect = {
        m for m, cfg in modules.items()
        if m not in changed_modules and set(cfg.get("depends_on", [])) & changed_modules.keys()
    }
    defect_score = {}
    for m in modules:
        score = sum(SEVERITY_WEIGHT.get(d.get("severity", "").lower(), 0) for d in defects if d.get("module") == m)
        defect_score[m] = min(score, 30)

    ranked = []
    for m, cfg in modules.items():
        impact = "direct" if m in changed_modules else "indirect" if m in indirect else "none"
        for t in cfg.get("tests", []):
            smoke = "smoke" in t.get("tags", [])
            if impact == "none" and not smoke:
                continue
            score = PRIORITY_WEIGHT.get(t.get("priority", "P3"), 10) + defect_score[m] + (10 if smoke else 0)
            score += {"direct": 40, "indirect": 20, "none": 0}[impact]
            ranked.append(
                {
                    "test_id": t["id"],
                    "name": t.get("name", ""),
                    "module": m,
                    "impact": impact,
                    "priority": t.get("priority", "P3"),
                    "smoke": smoke,
                    "defect_history_score": defect_score[m],
                    "score": score,
                    "minutes": t.get("minutes", 0),
                }
            )
    ranked.sort(key=lambda r: -r["score"])
    return {
        "changed_files": len(changes),
        "changed_modules": changed_modules,
        "indirectly_affected_modules": sorted(indirect),
        "unmapped_files": unmapped,
        "candidate_tests": ranked,
        "mandatory_test_ids": [r["test_id"] for r in ranked if r["smoke"] or (r["impact"] == "direct" and r["priority"] == "P1")],
    }


class RegressionSelectionAgent(Agent):
    name = "regression-selection"
    title = "Regression Test Selection"
    summary = "Uses code changes, affected modules and historical defects to recommend regression tests."
    inputs_help = "changed files (.txt from git diff --name-only), test map (.yaml) and optional defect history (.csv)"
    example_files = ["changed_files.txt", "test_map.yaml", "defect_history.csv"]
    output_model = RegressionPlan
    system_prompt = """Task: choose the regression tests to run for this change set.
Candidate tests were scored locally from: direct vs indirect module impact, test priority, smoke
tag and the module's defect history. Decide must_run / should_run / optional for each candidate
and give a one-line reason tied to the changed files. Every mandatory_test_id must be must_run.
Flag risks the mapping cannot see (shared libraries, config, migrations, feature flags) and say
what to do about unmapped files. Estimate total scope and run time."""

    def analyse(self, files):
        changes = [f for f in files if f.suffix in (".txt", ".diff", "")]
        maps = [f for f in files if f.suffix in (".yaml", ".yml")]
        if not changes or not maps:
            raise AgentError("regression-selection needs a changed-files .txt and a test map .yaml.")
        defects = []
        for f in files:
            if f.suffix == ".csv":
                defects += load_defects(f.text())
        test_map = yaml.safe_load(maps[0].text()) or {}
        return select_tests(parse_changes(changes[0].text()), test_map, defects)

    def build_prompt(self, files, facts):
        return f"{facts_block(facts)}\n\nRecommend the regression run."

    def finalise(self, output, facts, notes):
        chosen = {r.test_id: r for r in output.recommendations}
        for test_id in facts["mandatory_test_ids"]:
            rec = chosen.get(test_id)
            if rec is None:
                output.recommendations.append(Recommendation(test_id=test_id, decision="must_run", reason="Added by guardrail: smoke or P1 test in a directly changed module."))
                notes.append(f"{test_id} was missing from the model's plan and was added as must_run.")
            elif rec.decision != "must_run":
                rec.decision = "must_run"
                notes.append(f"{test_id} was raised to must_run (smoke or P1 in a directly changed module).")
        by_id = {c["test_id"]: c for c in facts["candidate_tests"]}
        facts["estimated_minutes_must_and_should"] = sum(
            by_id.get(r.test_id, {}).get("minutes", 0) for r in output.recommendations if r.decision != "optional"
        )
        return output
