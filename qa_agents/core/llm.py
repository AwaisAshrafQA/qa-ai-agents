"""Model access: the real Claude client and an offline demo client with the same interface."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

DEFAULT_MODEL = "claude-opus-5-5"
DEMO_DIR = Path(__file__).resolve().parent.parent / "demo"

Prompt = str | list[dict[str, Any]]


class AgentError(RuntimeError):
    """A problem the user can act on (missing key, bad input, refusal...)."""


class LLM(Protocol):
    model: str

    def run(self, *, agent: str, system: str, prompt: Prompt, schema: type[T]) -> T: ...


class ClaudeClient:
    """Calls Claude through the Anthropic SDK and returns a validated Pydantic object.

    Structured outputs (`messages.parse`) guarantee the response matches the agent's
    schema, so no agent has to scrape JSON out of free text.
    """

    def __init__(self, model: str | None = None, effort: str = "high", client: Any = None):
        import anthropic

        self.model = model or os.environ.get("QA_AGENTS_MODEL", DEFAULT_MODEL)
        self.effort = effort
        try:
            self._client = client or anthropic.Anthropic()
        except anthropic.AnthropicError as exc:
            raise AgentError(
                "No Anthropic credentials found. Set ANTHROPIC_API_KEY, or add --demo to "
                "replay recorded responses."
            ) from exc

    def run(self, *, agent: str, system: str, prompt: Prompt, schema: type[T]) -> T:
        import anthropic

        try:
            response = self._client.messages.parse(
                model=self.model,
                max_tokens=16000,
                system=system,
                output_config={"effort": self.effort},
                messages=[{"role": "user", "content": prompt}],
                output_format=schema,
            )
        except anthropic.AuthenticationError as exc:
            raise AgentError("ANTHROPIC_API_KEY is invalid. Check the key, or use --demo.") from exc
        except anthropic.RateLimitError as exc:
            raise AgentError("Rate limited by the Claude API. Wait a moment and retry.") from exc
        except anthropic.APIStatusError as exc:
            raise AgentError(f"Claude API error {exc.status_code}: {exc.message}") from exc
        except anthropic.APIConnectionError as exc:
            raise AgentError("Could not reach the Claude API. Check your network.") from exc
        except ValidationError as exc:
            # parse() validates while reading the response, so a refusal or a truncated
            # answer surfaces here before stop_reason can be checked.
            raise AgentError(
                f"Claude's answer for {agent} was incomplete or declined. "
                "Retry, or split the input into smaller files."
            ) from exc

        if response.stop_reason == "refusal":
            raise AgentError(f"Claude declined this request ({agent}). Review the inputs.")
        if response.stop_reason == "max_tokens":
            raise AgentError("The response hit the token limit. Split the input into smaller files.")
        if response.parsed_output is None:
            raise AgentError("Claude returned no structured output.")
        return response.parsed_output


class DemoClient:
    """Replays a recorded response per agent, so everything runs without an API key.

    The locally computed facts are still real; only the model's part is recorded.
    """

    model = "demo (recorded response)"

    def __init__(self, demo_dir: Path = DEMO_DIR):
        self.demo_dir = demo_dir

    def run(self, *, agent: str, system: str, prompt: Prompt, schema: type[T]) -> T:
        path = self.demo_dir / f"{agent}.json"
        if not path.is_file():
            raise AgentError(f"No recorded demo response for '{agent}'.")
        return schema.model_validate_json(path.read_text(encoding="utf-8"))
