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


FULL_SUITE_TRIGGERS = [
    r"(^|/)(pom\.xml|build\.gradle(\.kts)?|settings\.gradle(\.kts)?|package\.json|package-lock\.json|yarn\.lock|pnpm-lock\.yaml"
    r"|requirements[^/]*\.txt|pyproject\.toml|poetry\.lock|Pipfile(\.lock)?|go\.mod|go\.sum|Gemfile(\.lock)?|\w+\.csproj|Directory\.Build\.props)$",
    r"(^|/)Dockerfile[^/]*$|(^|/)docker-compose[^/]*\.ya?ml$",
    r"(^|/)\.github/workflows/|(^|/)\.gitlab-ci\.yml$|(^|/)Jenkinsfile$|(^|/)azure-pipelines[^/]*\.ya?ml$",
    r"(^|/)(playwright|cypress|jest|vitest|karma|testng|pytest)\.config\.\w+$|(^|/)conftest\.py$|(^|/)testng\.xml$",
]
TEST_PATH = re.compile(r"(^|/)(tests?|specs?|e2e|__tests__|cypress|src/test)/|\.(spec|test|cy)\.[jt]sx?$|(^|/)test_[^/]+\.py$|Tests?\.(java|cs|kt)$")
MIGRATION_PATH = re.compile(r"(^|/)(migrations?|db/migrate|flyway|liquibase|alembic)/", re.IGNORECASE)


def parse_changes(text: str) -> list[str]:
    """Accepts `git diff --name-only`, `--name-status` (incl. renames) or `--stat` output, any OS path style."""
    paths: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or re.match(r"^\d+ files? changed", line):
            continue
        if "|" in line:  # --stat: "src/a.ts | 12 +++--"
            line = line.split("|")[0].strip()
        parts = re.split(r"\t+", line) if "\t" in line else line.split()
        if len(parts) > 1 and re.fullmatch(r"[AMDRCTU]\d*", parts[0]):
            parts = parts[1:]  # --name-status, renames give "R100 old new"
        elif len(parts) > 1:
            parts = [" ".join(parts)]  # a path that contains spaces
        for token in parts:
            token = token.strip().strip('"').replace("\\", "/").removeprefix("./")
            if ("/" in token or re.search(r"\.\w+$", token)) and token not in paths:
                paths.append(token)
    return paths


def validate_test_map(test_map) -> dict:
    example = "modules:\n  checkout:\n    paths: [\"src/checkout/**\"]\n    depends_on: [pricing]\n    tests:\n      - {id: CHK-001, name: Guest checkout, priority: P1, tags: [smoke], minutes: 4}"
    if not isinstance(test_map, dict) or not isinstance(test_map.get("modules"), dict) or not test_map["modules"]:
        raise AgentError(f"The test map needs a 'modules:' section. Example:\n{example}")
    for name, cfg in test_map["modules"].items():
        if not isinstance(cfg, dict):
            raise AgentError(f"Module '{name}' in the test map must be a mapping with paths and tests.")
        if not cfg.get("paths"):
            raise AgentError(f"Module '{name}' has no 'paths' globs, so no change can ever map to it.")
        for i, t in enumerate(cfg.get("tests") or []):
            if not isinstance(t, dict) or not t.get("id"):
                raise AgentError(f"Test #{i + 1} in module '{name}' has no 'id'.")
            if t.get("priority", "P3") not in PRIORITY_WEIGHT:
                raise AgentError(f"Test {t['id']} has priority '{t.get('priority')}'; use P1, P2 or P3.")
        unknown = set(cfg.get("depends_on") or []) - set(test_map["modules"])
        if unknown:
            raise AgentError(f"Module '{name}' depends on unknown module(s): {', '.join(sorted(unknown))}.")
    return test_map


def _matches(path: str, glob: str) -> bool:
    glob = glob.replace("\\", "/").removeprefix("./")
    return fnmatch.fnmatch(path, glob) or (glob.endswith("/**") and path.startswith(glob[:-3] + "/"))


def select_tests(changes: list[str], test_map: dict, defects: list[dict]) -> dict:
    modules = validate_test_map(test_map)["modules"]
    changed_modules: dict[str, list[str]] = {}
    unmapped = []
    for path in changes:
        hits = [m for m, cfg in modules.items() if any(_matches(path, g) for g in cfg.get("paths", []))]
        for m in hits:
            changed_modules.setdefault(m, []).append(path)
        if not hits:
            unmapped.append(path)

    # Transitive closure: a module is indirectly affected if anything it depends on (at any depth) changed.
    indirect: set[str] = set()
    frontier = set(changed_modules)
    while frontier:
        nxt = {m for m, cfg in modules.items() if set(cfg.get("depends_on") or []) & frontier} - set(changed_modules) - indirect
        indirect |= nxt
        frontier = nxt

    defect_score = {}
    for m in modules:
        score = sum(SEVERITY_WEIGHT.get(d.get("severity", ""), 0) for d in defects if d.get("module", "").lower() == m.lower())
        defect_score[m] = min(score, 30)

    ranked: dict[str, dict] = {}
    for m, cfg in modules.items():
        impact = "direct" if m in changed_modules else "indirect" if m in indirect else "none"
        for t in cfg.get("tests") or []:
            smoke = "smoke" in (t.get("tags") or [])
            if impact == "none" and not smoke:
                continue
            score = PRIORITY_WEIGHT[t.get("priority", "P3")] + defect_score[m] + (10 if smoke else 0)
            score += {"direct": 40, "indirect": 20, "none": 0}[impact]
            entry = {
                "test_id": str(t["id"]),
                "name": t.get("name", ""),
                "module": m,
                "impact": impact,
                "priority": t.get("priority", "P3"),
                "smoke": smoke,
                "defect_history_score": defect_score[m],
                "score": score,
                "minutes": t.get("minutes", 0) or 0,
            }
            if entry["test_id"] not in ranked or ranked[entry["test_id"]]["score"] < score:
                ranked[entry["test_id"]] = entry  # a test listed under several modules keeps its best score
    candidates = sorted(ranked.values(), key=lambda r: (-r["score"], r["test_id"]))

    full_suite_reasons = [p for p in changes if any(re.search(rx, p) for rx in FULL_SUITE_TRIGGERS)]
    facts = {
        "changed_files": len(changes),
        "changed_modules": changed_modules,
        "indirectly_affected_modules": sorted(indirect),
        "unmapped_files": unmapped,
        "changed_test_files": [p for p in changes if TEST_PATH.search(p)],
        "migration_files": [p for p in changes if MIGRATION_PATH.search(p)],
        "candidate_tests": candidates,
        "mandatory_test_ids": [r["test_id"] for r in candidates if r["smoke"] or (r["impact"] == "direct" and r["priority"] == "P1")],
        "full_suite_recommended": bool(full_suite_reasons),
    }
    if full_suite_reasons:
        facts["full_suite_reasons"] = full_suite_reasons
    if not changes:
        facts["warning"] = "No changed files were found in the input."
    return facts


class RegressionSelectionAgent(Agent):
    name = "regression-selection"
    title = "Regression Test Selection"
    summary = "Uses code changes, affected modules and historical defects to recommend regression tests."
    inputs_help = "changed files (.txt from git diff --name-only), test map (.yaml) and optional defect history (.csv)"
    example_files = ["changed_files.txt", "test_map.yaml", "defect_history.csv"]
    output_model = RegressionPlan
    guardrails = [
        "Every test in facts.mandatory_test_ids must be must_run.",
        "If facts.full_suite_recommended is true, the plan must say a full regression run is needed before release.",
    ]
    system_prompt = """Task: choose the regression tests to run for this change set.
Candidate tests were scored locally from: direct vs indirect module impact, test priority, smoke
tag and the module's defect history. Decide must_run / should_run / optional for each candidate
and give a one-line reason tied to the changed files. Selection by module map is heuristic (unsafe
in the regression-testing sense), so be explicit about what is NOT being run and why.
Changed test files must run. Database migrations need data-access tests and a forward/rollback
rehearsal. Build, dependency or CI changes (facts.full_suite_reasons) call for a full run.
Flag risks the mapping cannot see (shared libraries, config, feature flags) and say what to do
about unmapped files. Estimate total scope and run time."""

    def analyse(self, files):
        changes = [f for f in files if f.suffix in (".txt", ".diff", ".patch", "")]
        maps = [f for f in files if f.suffix in (".yaml", ".yml")]
        if not changes or not maps:
            raise AgentError("regression-selection needs a changed-files .txt (git diff --name-only) and a test map .yaml.")
        defects = []
        for f in files:
            if f.suffix == ".csv":
                defects += load_defects(f.text(), f.name)
        try:
            test_map = yaml.safe_load(maps[0].text()) or {}
        except yaml.YAMLError as exc:
            raise AgentError(f"{maps[0].name} is not valid YAML: {exc}") from exc
        changed = []
        for f in changes:
            changed += [p for p in parse_changes(f.text()) if p not in changed]
        return select_tests(changed, test_map, defects)

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
        if facts.get("full_suite_recommended") and "full" not in output.estimated_scope.lower():
            output.additional_risks.insert(0, "Build, dependency or CI files changed (" + ", ".join(facts["full_suite_reasons"]) + "): run the FULL regression suite before release.")
            notes.append("A full-suite recommendation was added because build, dependency or CI files changed.")
        by_id = {c["test_id"]: c for c in facts["candidate_tests"]}
        facts["estimated_minutes_must_and_should"] = sum(
            by_id.get(r.test_id, {}).get("minutes", 0) for r in output.recommendations if r.decision != "optional"
        )
        return output
