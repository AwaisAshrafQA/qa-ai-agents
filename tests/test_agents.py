"""End-to-end agent runs in demo mode, guardrails, prompts and the CLI."""

import json

import pytest

from qa_agents.agents import ALL_AGENTS, get_agent
from qa_agents.agents.regression_selection import RegressionPlan, Recommendation
from qa_agents.agents.release_quality import ReleaseReadiness
from qa_agents.cli import main
from qa_agents.core.llm import AgentError, DemoClient

from conftest import FakeLLM


@pytest.mark.parametrize("agent_cls", ALL_AGENTS, ids=lambda a: a.name)
def test_every_agent_runs_in_demo_mode(agent_cls, examples):
    agent = agent_cls()
    files = [examples / agent.name / f for f in agent.example_files]
    result = agent.run(files, DemoClient())
    assert isinstance(result.output, agent.output_model)
    md = result.to_markdown()
    assert md.startswith(f"# {agent.title}")
    assert "## Computed Locally" in md
    json.loads(result.to_json())


def test_ten_agents_with_unique_names():
    assert len(ALL_AGENTS) == 10
    assert len({a.name for a in ALL_AGENTS}) == 10


def test_release_guardrail_blocks_go_when_gates_fail(examples):
    agent = get_agent("release-readiness")
    optimistic = ReleaseReadiness(
        decision="go", confidence="high", rationale="Looks fine.", blocking_issues=[],
        conditions=[], residual_risks=[], recommendations=[],
    )
    files = [examples / "release-readiness" / f for f in agent.example_files]
    result = agent.run(files, FakeLLM(optimistic))
    assert result.output.decision == "no_go"
    assert "Pass rate" in result.output.blocking_issues[0]
    assert result.notes and "go" in result.notes[0]


def test_regression_guardrail_adds_missing_mandatory_tests(examples):
    agent = get_agent("regression-selection")
    thin_plan = RegressionPlan(
        summary="Run pricing only.",
        recommendations=[Recommendation(test_id="PRC-001", decision="must_run", reason="changed"),
                         Recommendation(test_id="CHK-001", decision="optional", reason="smoke")],
        additional_risks=[], unmapped_change_advice=[], estimated_scope="2 tests",
    )
    files = [examples / "regression-selection" / f for f in agent.example_files]
    result = agent.run(files, FakeLLM(thin_plan))
    decisions = {r.test_id: r.decision for r in result.output.recommendations}
    assert decisions["CHK-001"] == "must_run"
    assert decisions["PRC-002"] == decisions["CHK-002"] == decisions["SRC-001"] == "must_run"
    assert len(result.notes) == 4


def test_prompt_contains_facts_and_numbered_code(examples):
    agent = get_agent("code-review")
    demo_output = DemoClient().run(agent="code-review", system="", prompt="", schema=agent.output_model)
    llm = FakeLLM(demo_output)
    agent.run([examples / "code-review" / "LoginTest.java"], llm)
    call = llm.calls[0]
    assert "  19| " in call["prompt"] and "Thread.sleep(5000);" in call["prompt"]
    assert 'computed_locally="true"' in call["prompt"]
    assert call["system"].startswith("You are a senior QA engineer")


def test_defect_agent_sends_screenshot_as_image(examples):
    agent = get_agent("defect-drafting")
    demo_output = DemoClient().run(agent="defect-drafting", system="", prompt="", schema=agent.output_model)
    llm = FakeLLM(demo_output)
    agent.run([examples / "defect-drafting" / f for f in agent.example_files], llm)
    blocks = llm.calls[0]["prompt"]
    images = [b for b in blocks if b["type"] == "image"]
    assert len(images) == 1 and images[0]["source"]["media_type"] == "image/png"


def test_missing_file_is_a_clear_error(tmp_path):
    with pytest.raises(AgentError, match="not found"):
        get_agent("requirement-review").run([tmp_path / "nope.md"], DemoClient())


def test_wrong_input_type_is_a_clear_error(examples):
    with pytest.raises(AgentError, match="OpenAPI"):
        get_agent("api-contract").run([examples / "requirement-review" / "stories.md"], DemoClient())


def test_cli_list_and_run(capsys, examples, tmp_path):
    assert main(["list"]) == 0
    assert "release-readiness" in capsys.readouterr().out
    out = tmp_path / "report.json"
    code = main(["run", "failure-analysis", str(examples / "failure-analysis" / "results.xml"), "--demo", "--json", "--out", str(out)])
    assert code == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["facts"]["failed_tests"] == 4
    assert data["facts"]["by_category"]["app_defect"] == 1


def test_cli_example_all(tmp_path):
    assert main(["example", "all", "--demo", "--out", str(tmp_path)]) == 0
    assert len(list(tmp_path.glob("*.md"))) == 10


def test_cli_reports_errors_with_exit_code_2(capsys, tmp_path):
    assert main(["run", "api-contract", str(tmp_path / "missing.yaml"), "--demo"]) == 2
    assert "error:" in capsys.readouterr().err
