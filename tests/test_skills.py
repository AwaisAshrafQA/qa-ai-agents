"""The Claude Code skills stay in step with the agents, and `qa-agents facts` works without a model."""

import json
import re
import sys
from pathlib import Path

import pytest
import yaml

from qa_agents.agents import ALL_AGENTS
from qa_agents.cli import main

SKILLS = Path(__file__).resolve().parent.parent / ".claude" / "skills"
sys.path.insert(0, str(SKILLS.parent.parent / "scripts"))
import sync_skill_references as sync  # noqa: E402


def frontmatter(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    assert match, f"{path} has no YAML frontmatter"
    return yaml.safe_load(match.group(1)), match.group(2)


@pytest.mark.parametrize("agent_cls", ALL_AGENTS, ids=lambda a: a.name)
def test_every_agent_has_a_matching_skill(agent_cls):
    path = SKILLS / f"qa-{agent_cls.name}" / "SKILL.md"
    assert path.is_file(), f"missing skill for {agent_cls.name}"
    meta, body = frontmatter(path)
    assert meta["name"] == f"qa-{agent_cls.name}"
    assert 40 < len(meta["description"]) <= 1024 and "Use when" in meta["description"]
    assert f"qa-agents facts {agent_cls.name} " in body
    for rule in agent_cls.guardrails:
        assert "guardrails" in body, f"{agent_cls.name} has guardrails the skill must mention"


@pytest.mark.parametrize("agent_cls", ALL_AGENTS, ids=lambda a: a.name)
def test_skill_structure_and_reference_in_sync(agent_cls):
    folder = SKILLS / f"qa-{agent_cls.name}"
    _, body = frontmatter(folder / "SKILL.md")
    for section in ("## 1. Inputs", "## 2. Compute the facts", "## 4. Report", "## 5. Quality bar", "## 6. Next steps"):
        assert section in body, f"{agent_cls.name}: missing '{section}'"
    assert "reference.md" in body and "ask first" in body.lower()
    expected = sync.expected(agent_cls.name)
    actual = (folder / "reference.md").read_text(encoding="utf-8")
    assert actual == expected, f"run: python scripts/sync_skill_references.py ({agent_cls.name} reference.md is stale)"


def test_no_stray_skills():
    names = {p.name for p in SKILLS.iterdir() if p.is_dir()}
    assert names == {f"qa-{a.name}" for a in ALL_AGENTS}


@pytest.mark.parametrize("agent_cls", ALL_AGENTS, ids=lambda a: a.name)
def test_facts_command(agent_cls, examples, capsys):
    files = [str(examples / agent_cls.name / f) for f in agent_cls.example_files]
    assert main(["facts", agent_cls.name, *files]) == 0
    brief = json.loads(capsys.readouterr().out)
    assert brief["agent"] == agent_cls.name
    assert brief["instructions"].startswith("You are a senior QA engineer")
    assert brief["output_fields"] == list(agent_cls.output_model.model_fields)
    assert brief["guardrails"] == agent_cls.guardrails
    assert isinstance(brief["facts"], dict) and brief["facts"]
