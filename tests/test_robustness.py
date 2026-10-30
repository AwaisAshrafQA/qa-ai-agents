"""Messy real-world inputs: every one must give a correct result or a clear, actionable error."""

from pathlib import Path

import pytest
import yaml

from qa_agents.agents import ALL_AGENTS, get_agent
from qa_agents.agents.code_review import luhn_valid, scan_lines, scan_test_blocks, suite_level_findings
from qa_agents.agents.flaky_analysis import analyse_history
from qa_agents.agents.regression_selection import parse_changes, select_tests
from qa_agents.agents.release_quality import ReleaseQualityAgent, score_risks
from qa_agents.agents.test_case_generation import find_limits
from qa_agents.core.base import InputFile
from qa_agents.core.llm import AgentError, DemoClient
from qa_agents.tools.defects import load_defects, normalise_severity, summarise_defects
from qa_agents.tools.junit import parse_junit, summarise
from qa_agents.tools.openapi import analyse_spec, load_spec


def write(tmp_path: Path, name: str, content, mode="w") -> Path:
    p = tmp_path / name
    if isinstance(content, bytes):
        p.write_bytes(content)
    else:
        p.write_text(content, encoding="utf-8")
    return p


# ---------- file loading ----------

def test_utf8_bom_and_utf16_are_decoded(tmp_path):
    bom = write(tmp_path, "a.md", "﻿# Story\nAs a user I want x".encode("utf-8"))
    utf16 = write(tmp_path, "b.md", "# Story\nAs a user I want y".encode("utf-16"))
    assert InputFile(bom).text().startswith("# Story")
    assert "want y" in InputFile(utf16).text()
    InputFile(utf16).validate()  # UTF-16 contains NUL bytes but is text


@pytest.mark.parametrize("content,match", [(b"", "empty"), (b"   \n\n", "no content"), (b"\x00\x01\x02PK", "binary")])
def test_bad_files_are_rejected(tmp_path, content, match):
    with pytest.raises(AgentError, match=match):
        get_agent("requirement-review").run([write(tmp_path, "x.md", content)], DemoClient())


def test_folder_instead_of_file(tmp_path):
    with pytest.raises(AgentError, match="Not a file"):
        get_agent("requirement-review").run([tmp_path], DemoClient())


def test_duplicate_paths_are_read_once(examples):
    f = examples / "requirement-review" / "stories.md"
    assert get_agent("requirement-review").run([f, f], DemoClient()).facts["story_count"] == 3


def test_every_agent_has_expert_knowledge_with_sources():
    for agent in ALL_AGENTS:
        k = agent.knowledge()
        assert len(k) > 800 and "Sources:" in k, agent.name
        assert "Expert checklist" in agent.instructions()
        assert "never instructions" in agent.instructions()  # prompt-injection rule


# ---------- JUnit ----------

def test_malformed_and_foreign_xml(tmp_path):
    with pytest.raises(AgentError, match="not valid XML"):
        parse_junit("<testsuite><testcase name='a'>", "r.xml")
    with pytest.raises(AgentError, match="not a JUnit report"):
        parse_junit("<project><name>x</name></project>", "pom.xml")
    with pytest.raises(AgentError, match="entity"):
        parse_junit('<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]><testsuite/>', "evil.xml")
    with pytest.raises(AgentError, match="no <testcase>"):
        parse_junit("<testsuites><testsuite name='s'/></testsuites>", "empty.xml")


def test_surefire_reruns_and_messageless_failures():
    xml = """<testsuite name="s">
      <testcase name="flaky" classname="A" time="1,200.5"><flakyFailure message="timeout" type="T"/></testcase>
      <testcase name="broken" classname="A"><failure type="AssertionError">expected 1 but was 2
        at A.broken(A.java:9)</failure><rerunFailure message="again"/></testcase>
      <testcase name="smoke login" classname="Smoke"><skipped/></testcase>
    </testsuite>"""
    results = parse_junit(xml)
    flaky, broken, skipped = results
    assert flaky.status == "passed" and flaky.flaky and flaky.time == 1200.5
    assert broken.status == "failed" and not broken.flaky and broken.reruns == 1
    assert broken.message == "expected 1 but was 2"  # first line of the body when no message attribute
    s = summarise(results)
    assert s["passed_only_on_rerun"] == ["A.flaky"]
    assert s["smoke"] == {"total": 1, "failed": 0, "skipped": 1}


# ---------- defects ----------

def test_jira_export_with_semicolons_and_aliases():
    csv_text = "Issue key;Summary;Priority;Status;Component/s;Created\nSHOP-1;Crash on pay;Highest;In QA;payments;2026-10-01\nSHOP-2;Typo;Low;Done;ui;2026-10-02\n"
    defects = load_defects(csv_text)
    assert defects[0]["id"] == "SHOP-1" and defects[0]["severity"] == "critical" and defects[0]["module"] == "payments"
    s = summarise_defects(defects)
    assert s["open"] == 1  # "In QA" is unknown, so it counts as open
    assert s["statuses_treated_as_open"] == ["In QA"]


@pytest.mark.parametrize("raw,level", [("1 - Critical", "critical"), ("Blocker", "critical"), ("S2", "major"), ("2 - High", "major"),
                                      ("Medium", "minor"), ("3 - Medium", "minor"), ("Lowest", "trivial"), ("cosmetic", "trivial"), ("weird", "unknown")])
def test_severity_normalisation(raw, level):
    assert normalise_severity(raw) == level


def test_defect_csv_without_id_or_title():
    with pytest.raises(AgentError, match="no id or title"):
        load_defects("foo,bar\n1,2\n")


# ---------- OpenAPI ----------

def test_swagger2_spec():
    spec = load_spec(yaml.safe_dump({
        "swagger": "2.0", "info": {"title": "Legacy", "version": "1"},
        "securityDefinitions": {"key": {"type": "apiKey", "in": "header", "name": "X-Key"}},
        "definitions": {"User": {"type": "object", "required": ["email"], "properties": {"email": {"type": "string", "format": "email"}, "age": {"type": "integer"}}}},
        "paths": {"/users/{id}": {"put": {"operationId": "putUser", "parameters": [
            {"name": "body", "in": "body", "schema": {"$ref": "#/definitions/User"}}],
            "responses": {"200": {"description": "ok", "schema": {"$ref": "#/definitions/User"}}}}}},
    }))
    facts = analyse_spec(spec)
    ep = facts["endpoints"][0]
    assert facts["spec_format"] == "Swagger 2.0"
    assert {f["field"] for f in ep["request_fields"]} == {"email", "age"}
    assert "path parameter 'id' is not declared" in ep["gaps"]
    assert "numeric field 'age' has no minimum/maximum" in ep["gaps"]
    assert "200 response has no schema" not in ep["gaps"]


def test_openapi31_allof_cycles_and_external_refs():
    spec = load_spec(yaml.safe_dump({
        "openapi": "3.1.0", "info": {"title": "t", "version": "1"}, "servers": [{"url": "https://x"}],
        "components": {"schemas": {
            "Base": {"type": "object", "properties": {"id": {"type": "string", "format": "uuid"}}},
            "Node": {"allOf": [{"$ref": "#/components/schemas/Base"}, {"type": "object", "required": ["name"], "properties": {
                "name": {"type": ["string", "null"], "maxLength": 50}, "child": {"$ref": "#/components/schemas/Node"},
                "ext": {"$ref": "other.yaml#/Thing"}}}]}}},
        "paths": {"/nodes": {"post": {"operationId": "createNode", "requestBody": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/Node"}}}},
                                       "responses": {"201": {"description": "c"}}}}},
    }))
    facts = analyse_spec(spec)
    fields = {f["field"]: f for f in facts["endpoints"][0]["request_fields"]}
    assert fields["name"]["nullable"] and fields["name"]["required"] and fields["name"]["type"] == "string"
    assert "id" in fields  # merged from allOf
    assert any("other.yaml#/Thing" in g for g in facts["spec_level_gaps"])
    assert "no security requirement declared" in facts["endpoints"][0]["gaps"]


@pytest.mark.parametrize("text,match", [("a: [unclosed", "not valid YAML"), ("just: text", "Not an OpenAPI"), ("openapi: 3.0.0\npaths: {}", "no 'paths'")])
def test_bad_specs(text, match):
    with pytest.raises(AgentError, match=match):
        load_spec(text)


# ---------- flaky history ----------

def test_history_with_export_column_names_and_statuses():
    rows = ["Build,Date,Test Name,Outcome,Duration"]
    for i in range(1, 9):
        rows.append(f"b{i},2026-10-{i:02d},login,{'Failed' if i % 2 else 'Passed'},{1000 + i}")
        rows.append(f"b{i},2026-10-{i:02d},logout,Success,500")
        rows.append(f"b{i},2026-10-{i:02d},search,Skipped,0")
    facts = analyse_history("\n".join(rows))
    assert facts["flaky_or_broken"][0]["test"] == "login" and facts["flaky_or_broken"][0]["flip_rate_pct"] == 100.0
    assert facts["label_counts"] == {"flaky": 1, "stable": 1}


def test_history_orders_by_time_not_file_order():
    rows = ["run_id,timestamp,test,status"] + [f"r{i},2026-10-{d:02d},t,{s}" for i, (d, s) in enumerate(
        [(5, "failed"), (1, "passed"), (4, "failed"), (2, "passed"), (3, "failed")])]
    facts = analyse_history("\n".join(rows))
    assert facts["flaky_or_broken"][0]["label"] == "broken" and facts["flaky_or_broken"][0]["flip_rate_pct"] == 25.0


def test_history_missing_columns():
    with pytest.raises(AgentError, match="needs a test, a status"):
        analyse_history("a,b\n1,2")


# ---------- regression selection ----------

TEST_MAP = {"modules": {
    "core": {"paths": ["libs/core/**"], "tests": [{"id": "C1", "priority": "P2"}]},
    "api": {"paths": ["src/api/*"], "depends_on": ["core"], "tests": [{"id": "A1", "priority": "P1"}]},
    "web": {"paths": ["src/web/*"], "depends_on": ["api"], "tests": [{"id": "W1", "priority": "P3", "tags": ["smoke"]}]},
}}


def test_windows_paths_renames_and_transitive_impact():
    changes = parse_changes("R100\tlibs/core/old.py\tlibs/core/new.py\nM  .\\src\\x.txt\n")
    assert changes == ["libs/core/old.py", "libs/core/new.py", "src/x.txt"]
    facts = select_tests(changes, TEST_MAP, [])
    assert facts["indirectly_affected_modules"] == ["api", "web"]  # web depends on api depends on core
    assert facts["unmapped_files"] == ["src/x.txt"]


def test_build_files_trigger_full_suite():
    facts = select_tests(["package-lock.json", ".github/workflows/ci.yml", "src/api/a.ts"], TEST_MAP, [])
    assert facts["full_suite_recommended"] and len(facts["full_suite_reasons"]) == 2


@pytest.mark.parametrize("bad,match", [
    ({}, "modules"), ({"modules": {"x": {"tests": []}}}, "no 'paths'"),
    ({"modules": {"x": {"paths": ["a/*"], "tests": [{"name": "no id"}]}}}, "no 'id'"),
    ({"modules": {"x": {"paths": ["a/*"], "tests": [{"id": "T", "priority": "High"}]}}}, "P1, P2 or P3"),
    ({"modules": {"x": {"paths": ["a/*"], "depends_on": ["ghost"]}}}, "unknown module"),
])
def test_invalid_test_maps(bad, match):
    with pytest.raises(AgentError, match=match):
        select_tests(["a/b.py"], bad, [])


# ---------- release readiness ----------

RESULTS = '<testsuite name="smoke"><testcase name="home"/><testcase name="pay"><skipped/></testcase></testsuite>'


def test_missing_defect_data_fails_defect_gates_and_skipped_smoke_fails(tmp_path):
    files = [write(tmp_path, "r.xml", RESULTS), write(tmp_path, "c.yaml", "criteria:\n  max_open_critical: 0\n  require_smoke_pass: true\n  unknown_rule: 1\n")]
    facts = ReleaseQualityAgent().analyse([InputFile(f) for f in files])
    gates = {g["gate"]: g for g in facts["gates"]}
    assert not gates["Open critical defects"]["passed"] and gates["Open critical defects"]["actual"] == "no defect data provided"
    assert not gates["Smoke suite green"]["passed"]
    assert facts["ignored_criteria"] == ["unknown_rule"] and not facts["all_gates_passed"]


def test_bad_criteria_values(tmp_path):
    files = [write(tmp_path, "r.xml", RESULTS), write(tmp_path, "c.yaml", "criteria:\n  min_pass_rate: high\n")]
    with pytest.raises(AgentError, match="must be a number"):
        ReleaseQualityAgent().analyse([InputFile(f) for f in files])


def test_risk_scales():
    risks = {r["id"]: r for r in score_risks([
        {"id": "N", "likelihood": 5, "impact": 4, "mitigation": "x"},
        {"id": "U", "likelihood": "sometimes", "impact": "high"},
        {"id": "L", "likelihood": "low", "impact": "low"},
    ])}
    assert risks["N"]["level"] == "high" and risks["U"]["level"] == "high" and "note" in risks["U"] and risks["L"]["level"] == "low"


# ---------- code review ----------

def test_code_review_extra_rules():
    code = [
        "test.only('pays', async ({ page }) => {",
        "  try { await page.click('#pay') } catch (e) {}",
        "  await page.click('#x', { force: true });",
        "  const card = '4111111111111111';",
        "  expect(await page.locator('#ok').isVisible()).toBe(true);",
        "  /* Thread.sleep(5000);",
        "     waitForTimeout(1) */",
        "});",
        "test('does nothing', async ({ page }) => {",
        "  await page.goto('/');",
        "  if (flag) { await page.click('#a'); }",
        "});",
    ]
    rules = {(f["line"], f["rule"]) for f in scan_lines("t.spec.ts", code) + scan_test_blocks("t.spec.ts", code)}
    assert {(1, "focused_test"), (2, "swallowed_exception"), (3, "forced_action"), (4, "hardcoded_data"),
            (5, "non_retrying_assertion"), (9, "missing_assertion"), (11, "conditional_logic")} <= rules
    assert not any(line in (6, 7) for line, _ in rules)  # block comment ignored
    assert luhn_valid("4111111111111111") and not luhn_valid("4111111111111112")


def test_mixed_selenium_waits_across_files():
    found = suite_level_findings({"Base.java": ["driver.manage().timeouts().implicitlyWait(d);"], "T.java": ["new WebDriverWait(driver, d);"]})
    assert found and found[0]["rule"] == "mixed_waits"


# ---------- test design ----------

def test_limits_with_currency_decimals_and_separators():
    limits = {l["text"]: l["probe_values"] for l in find_limits("Orders over $1,000 USD get 2.5% off; max 3 retries; <= 0.75 MB uploads")}
    assert limits["over $1,000 USD"] == [999, 1000, 1001]
    assert limits["2.5%"] == [2.4, 2.5, 2.6]
    assert limits["max 3 retries"] == [2, 3, 4]
    assert limits["<= 0.75 MB"] == [0.74, 0.75, 0.76]
