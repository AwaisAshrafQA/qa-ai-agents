from pathlib import Path

import pytest

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


class FakeLLM:
    """Returns a prepared output and records what the agent sent."""

    model = "fake"

    def __init__(self, output):
        self.output = output
        self.calls = []

    def run(self, *, agent, system, prompt, schema):
        self.calls.append({"agent": agent, "system": system, "prompt": prompt, "schema": schema})
        return self.output


@pytest.fixture
def examples() -> Path:
    return EXAMPLES
