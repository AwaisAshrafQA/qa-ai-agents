"""The shared agent shape: compute facts locally, ask Claude, apply guardrails."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar, Sequence

from pydantic import BaseModel

from qa_agents.core.llm import LLM, AgentError, Prompt

SYSTEM_PREAMBLE = """You are a senior QA engineer working inside an engineering team.
Ground every statement in the inputs you are given. When you rely on an assumption, say so.
Facts marked "computed locally" were calculated by deterministic code: treat them as correct
and do not contradict them. Be specific: name the story, test, endpoint, file or line.
Write in plain, professional English that a developer or product owner can act on.

"""

MAX_LINES_PER_FILE = 2000


@dataclass
class InputFile:
    path: Path

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def suffix(self) -> str:
        return self.path.suffix.lower()

    def text(self) -> str:
        return self.path.read_text(encoding="utf-8", errors="replace")

    def lines(self) -> list[str]:
        return self.text().splitlines()


@dataclass
class AgentResult:
    agent: str
    title: str
    model: str
    facts: dict[str, Any]
    output: BaseModel
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "model": self.model,
            "facts": self.facts,
            "output": self.output.model_dump(mode="json"),
            "notes": self.notes,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def to_markdown(self) -> str:
        from qa_agents.core.render import render_result

        return render_result(self)


class Agent(ABC):
    name: ClassVar[str]
    title: ClassVar[str]
    summary: ClassVar[str]
    inputs_help: ClassVar[str]
    system_prompt: ClassVar[str]
    output_model: ClassVar[type[BaseModel]]
    example_files: ClassVar[list[str]] = []
    guardrails: ClassVar[list[str]] = []  # enforced in finalise(); stated for skill users

    def analyse(self, files: list[InputFile]) -> dict[str, Any]:
        """Deterministic pre-processing. Results go to Claude and into the report."""
        return {}

    @abstractmethod
    def build_prompt(self, files: list[InputFile], facts: dict[str, Any]) -> Prompt: ...

    def finalise(self, output: BaseModel, facts: dict[str, Any], notes: list[str]) -> BaseModel:
        """Guardrails and post-processing applied to Claude's answer."""
        return output

    def load(self, paths: Sequence[str | Path]) -> list[InputFile]:
        if not paths:
            raise AgentError(f"{self.name} needs input files: {self.inputs_help}")
        files = [InputFile(Path(p)) for p in paths]
        for f in files:
            if not f.path.is_file():
                raise AgentError(f"Input file not found: {f.path}")
        return files

    def brief(self, paths: Sequence[str | Path]) -> dict[str, Any]:
        """Everything an assistant needs to do the judgment part itself (used by the Claude Code skills)."""
        files = self.load(paths)
        return {
            "agent": self.name,
            "inputs": [str(f.path) for f in files],
            "instructions": (SYSTEM_PREAMBLE + self.system_prompt).strip(),
            "guardrails": self.guardrails,
            "output_fields": list(self.output_model.model_fields),
            "facts": self.analyse(files),
        }

    def run(self, paths: Sequence[str | Path], llm: LLM) -> AgentResult:
        files = self.load(paths)
        facts = self.analyse(files)
        prompt = self.build_prompt(files, facts)
        output = llm.run(
            agent=self.name,
            system=SYSTEM_PREAMBLE + self.system_prompt,
            prompt=prompt,
            schema=self.output_model,
        )
        notes: list[str] = []
        output = self.finalise(output, facts, notes)
        return AgentResult(self.name, self.title, llm.model, facts, output, notes)


def file_block(f: InputFile, numbered: bool = False) -> str:
    """Wrap a file for the prompt. Very long files are cut, and the cut is stated."""
    lines = f.lines()
    note = ""
    if len(lines) > MAX_LINES_PER_FILE:
        note = f' note="showing the last {MAX_LINES_PER_FILE} of {len(lines)} lines"'
        offset = len(lines) - MAX_LINES_PER_FILE
        lines = lines[offset:]
    else:
        offset = 0
    if numbered:
        lines = [f"{offset + i + 1:>4}| {line}" for i, line in enumerate(lines)]
    body = "\n".join(lines)
    return f'<file name="{f.name}"{note}>\n{body}\n</file>'


def facts_block(facts: dict[str, Any]) -> str:
    return "<facts computed_locally=\"true\">\n" + json.dumps(facts, indent=2, ensure_ascii=False) + "\n</facts>"


def by_suffix(files: list[InputFile], *suffixes: str) -> list[InputFile]:
    return [f for f in files if f.suffix in suffixes]
