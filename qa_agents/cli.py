"""Command line: `qa-agents list | run <agent> <files...> | facts <agent> <files...> | example <agent|all>`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from qa_agents.agents import ALL_AGENTS, REGISTRY, get_agent
from qa_agents.core.llm import AgentError, ClaudeClient, DemoClient

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def _client(args):
    if args.demo:
        return DemoClient()
    return ClaudeClient(model=args.model, effort=args.effort)


def _emit(result, args) -> None:
    text = result.to_json() if args.json else result.to_markdown()
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        sys.stdout.write(text)


def cmd_list(_args) -> int:
    for i, a in enumerate(ALL_AGENTS, start=1):
        print(f"{i:>2}. {a.name:<22} {a.summary}")
        print(f"    {'':<22} input: {a.inputs_help}")
    return 0


def cmd_run(args) -> int:
    _emit(get_agent(args.agent).run(args.files, _client(args)), args)
    return 0


def cmd_facts(args) -> int:
    """Deterministic analysis only: no model call, no API key."""
    sys.stdout.write(json.dumps(get_agent(args.agent).brief(args.files), indent=2, ensure_ascii=False) + "\n")
    return 0


def cmd_example(args) -> int:
    names = list(REGISTRY) if args.agent == "all" else [args.agent]
    llm = _client(args)
    for name in names:
        agent = get_agent(name)
        folder = EXAMPLES_DIR / name
        result = agent.run([folder / f for f in agent.example_files], llm)
        if args.agent == "all":
            out = Path(args.out or "reports") / f"{name}.{'json' if args.json else 'md'}"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(result.to_json() if args.json else result.to_markdown(), encoding="utf-8")
            print(f"{name:<22} -> {out}")
        else:
            _emit(result, args)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="qa-agents", description="Claude-powered agents for QA work.")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list the agents").set_defaults(func=cmd_list)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--demo", action="store_true", help="replay recorded responses (no API key needed)")
    common.add_argument("--json", action="store_true", help="output JSON instead of Markdown")
    common.add_argument("--out", help="write to this file (or folder, for 'example all')")
    common.add_argument("--model", help="Claude model id (default: claude-opus-5-5, or $QA_AGENTS_MODEL)")
    common.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])

    run = sub.add_parser("run", parents=[common], help="run an agent on your files")
    run.add_argument("agent", choices=list(REGISTRY))
    run.add_argument("files", nargs="+")
    run.set_defaults(func=cmd_run)

    facts = sub.add_parser("facts", help="print the locally computed facts and the agent's instructions as JSON (no API call)")
    facts.add_argument("agent", choices=list(REGISTRY))
    facts.add_argument("files", nargs="+")
    facts.set_defaults(func=cmd_facts)

    ex = sub.add_parser("example", parents=[common], help="run an agent on the bundled examples")
    ex.add_argument("agent", choices=[*REGISTRY, "all"])
    ex.set_defaults(func=cmd_example)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    try:
        return args.func(args)
    except AgentError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
