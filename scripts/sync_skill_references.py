"""Copy each agent's expert checklist into its Claude Code skill folder as reference.md.

The skills read reference.md when the qa-agents CLI cannot run, so they keep working without the package.
Run after editing anything in qa_agents/knowledge/:  python scripts/sync_skill_references.py
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEADER = "<!-- Generated from qa_agents/knowledge/{name}.md by scripts/sync_skill_references.py. Do not edit here. -->\n\n"


def expected(name: str) -> str:
    return HEADER.format(name=name) + (ROOT / "qa_agents" / "knowledge" / f"{name}.md").read_text(encoding="utf-8")


def main() -> None:
    for source in sorted((ROOT / "qa_agents" / "knowledge").glob("*.md")):
        target = ROOT / ".claude" / "skills" / f"qa-{source.stem}" / "reference.md"
        target.write_text(expected(source.stem), encoding="utf-8", newline="\n")
        print(f"{source.name} -> {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
