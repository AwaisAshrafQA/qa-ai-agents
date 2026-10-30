"""Deterministic pre-processing: no model involved, exact expectations."""

from qa_agents.agents.code_review import find_duplicates, scan_lines
from qa_agents.agents.failure_analysis import heuristic_category
from qa_agents.agents.flaky_analysis import analyse_history, error_signature
from qa_agents.agents.regression_selection import parse_changes, select_tests
from qa_agents.agents.requirement_review import split_stories, story_facts
from qa_agents.agents.test_case_generation import find_limits
from qa_agents.tools.defects import load_defects, summarise_defects
from qa_agents.tools.junit import parse_junit, summarise
from qa_agents.tools.openapi import analyse_spec, load_spec


def test_junit_summary(examples):
    results = parse_junit((examples / "execution-report" / "results.xml").read_text())
    s = summarise(results)
    assert (s["total"], s["passed"], s["failed"], s["skipped"]) == (16, 13, 2, 1)
    assert s["pass_rate_pct"] == 86.7


def test_junit_single_testsuite_root():
    xml = '<testsuite name="s"><testcase name="a" time="1"/><testcase name="b"><error message="boom"/></testcase></testsuite>'
    results = parse_junit(xml)
    assert [r.status for r in results] == ["passed", "error"]
    assert results[1].message == "boom"


def test_defect_summary(examples):
    defects = load_defects((examples / "execution-report" / "defects.csv").read_text())
    s = summarise_defects(defects)
    assert s["open"] == 4
    assert s["open_by_severity"] == {"critical": 0, "major": 1, "minor": 2, "trivial": 1}
    assert s["open_critical_and_major"][0]["id"] == "SL-402"


def test_openapi_gaps(examples):
    facts = analyse_spec(load_spec((examples / "api-contract" / "orders_api.yaml").read_text()))
    by_ep = {e["endpoint"]: e for e in facts["endpoints"]}
    assert facts["endpoint_count"] == 3
    assert "no security requirement declared" in by_ep["GET /orders/{orderId}"]["gaps"]
    assert "200 response has no schema" in by_ep["POST /orders/{orderId}/cancel"]["gaps"]
    fields = {f["field"]: f for f in by_ep["POST /orders"]["request_fields"]}
    assert fields["items[].quantity"]["constraints"] == {"minimum": 1}
    assert fields["paymentMethod"]["required"] is True


def test_requirement_story_facts(examples):
    stories = [story_facts(t, b) for t, b in split_stories((examples / "requirement-review" / "stories.md").read_text())]
    assert [s["acceptance_criteria_count"] for s in stories] == [3, 0, 3]
    assert "quickly" in stories[1]["vague_terms"]


def test_boundary_limits():
    limits = {l["text"]: l["probe_values"] for l in find_limits("Codes are 6 to 12 characters. Subtotal at least 100 AED.")}
    assert limits["6 to 12 characters"] == [5, 6, 7, 11, 12, 13]
    assert limits["at least 100 AED"] == [99, 100, 101]


def test_code_scan_rules():
    lines = [
        "await page.waitForTimeout(3000);",
        "await page.locator('//div[2]/button[1]').click();",
        "driver.findElement(By.id(\"password\")).sendKeys(\"x\"); String password = \"Admin@123\";",
        "expect(total).toBeTruthy();",
        "// Thread.sleep(1000) in a comment is ignored",
    ]
    rules = {(f["line"], f["rule"]) for f in scan_lines("t.ts", lines)}
    assert {(1, "fixed_wait"), (2, "unstable_locator"), (3, "hardcoded_data"), (4, "weak_assertion")} <= rules
    assert not any(line == 5 for line, _ in rules)


def test_duplicate_detection():
    block = ["await page.goto('/cart');", "await page.fill('#email', user);", "await page.click('#continue');", "await page.fill('#coupon', code);"]
    findings = find_duplicates("t.ts", block + ["expect(a).toBe(1);"] + block)
    assert len(findings) == 1 and findings[0]["line"] == 6


def test_failure_heuristics():
    assert heuristic_category("connect ECONNREFUSED 10.0.0.1:443") == "environment"
    assert heuristic_category("409 Conflict: user already exists") == "test_data"
    assert heuristic_category("TimeoutError: waiting for locator('#pay')") == "automation_issue"
    assert heuristic_category("AssertionError: expected 164 but was 160") == "app_defect"
    assert heuristic_category("something odd") == "unknown"


def test_flaky_history(examples):
    facts = analyse_history((examples / "flaky-tests" / "execution_history.csv").read_text())
    labels = {s["test"]: s["label"] for s in facts["flaky_or_broken"]}
    assert labels["checkout.spec.ts > guest can apply a coupon"] == "flaky"
    assert labels["search.spec.ts > filters products by price"] == "broken"
    cancel = next(s for s in facts["flaky_or_broken"] if "CancelOrderTest" in s["test"])
    assert cancel["failures_by_env"] == {"staging-b": 4}
    assert facts["label_counts"]["stable"] == 2


def test_error_signature_groups_ids():
    assert error_signature("user qa.buyer04 req-9f8e7d6c5b failed after 3012ms") == error_signature(
        "user qa.buyer11 req-0a1b2c3d4e failed after 2950ms"
    )


def test_parse_changes_formats():
    text = "M\tsrc/a.py\nsrc/b.ts | 12 +++--\n 3 files changed, 10 insertions(+)\nsrc/c.sql\n"
    assert parse_changes(text) == ["src/a.py", "src/b.ts", "src/c.sql"]


def test_regression_selection(examples):
    import yaml

    folder = examples / "regression-selection"
    facts = select_tests(
        parse_changes((folder / "changed_files.txt").read_text()),
        yaml.safe_load((folder / "test_map.yaml").read_text()),
        load_defects((folder / "defect_history.csv").read_text()),
    )
    assert set(facts["changed_modules"]) == {"pricing", "checkout"}
    assert facts["indirectly_affected_modules"] == ["invoices"]
    assert "db/migrations/0042_add_coupon_usage_index.sql" in facts["unmapped_files"]
    ids = [c["test_id"] for c in facts["candidate_tests"]]
    assert "PRF-001" not in ids  # unaffected, non-smoke
    assert ids[0].startswith("PRC")  # pricing has the heaviest defect history
    assert {"PRC-001", "PRC-002", "CHK-001", "CHK-002", "SRC-001"} == set(facts["mandatory_test_ids"])
