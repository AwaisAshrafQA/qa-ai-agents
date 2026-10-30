"""Generic Markdown rendering for any agent's facts and output."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


def render_result(result) -> str:
    out = [f"# {result.title}", "", f"_Model: {result.model}_", ""]
    data = result.output.model_dump(mode="json")
    out.append(_render(data, level=2))
    for note in result.notes:
        out += ["", f"> **Guardrail:** {note}"]
    if result.facts:
        out += ["", "## Computed Locally", "", _render(result.facts, level=3)]
    return "\n".join(out).rstrip() + "\n"


def _title(key: str) -> str:
    small = {"and", "or", "of", "to", "for", "by", "in"}
    words = key.replace("_", " ").split()
    return " ".join(w if (i and w in small) else w[:1].upper() + w[1:] for i, w in enumerate(words))


def _cell(value: Any) -> str:
    if isinstance(value, list):
        value = "; ".join(_cell(v) for v in value)
    elif isinstance(value, dict):
        value = ", ".join(f"{k}: {_cell(v)}" for k, v in value.items())
    elif isinstance(value, bool):
        value = "yes" if value else "no"
    return str(value).replace("|", "\\|").replace("\n", " ")


def _is_scalar(value: Any) -> bool:
    return not isinstance(value, (dict, list))


def _table(rows: list[dict[str, Any]]) -> str:
    cols: list[str] = []
    for row in rows:
        cols += [k for k in row if k not in cols]
    head = "| " + " | ".join(_title(c) for c in cols) + " |"
    sep = "|" + "|".join("---" for _ in cols) + "|"
    body = ["| " + " | ".join(_cell(r.get(c, "")) for c in cols) + " |" for r in rows]
    return "\n".join([head, sep, *body])


def _render(value: Any, level: int) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if isinstance(value, dict):
        parts = []
        scalars = {k: v for k, v in value.items() if _is_scalar(v)}
        for k, v in scalars.items():
            if isinstance(v, str) and len(v) > 90:
                parts.append(f"{'#' * level} {_title(k)}\n\n{v}")
            else:
                parts.append(f"- **{_title(k)}:** {_cell(v)}")
        for k, v in value.items():
            if k in scalars:
                continue
            if not v:
                continue
            parts.append(f"{'#' * level} {_title(k)}\n\n{_render(v, level + 1)}")
        return "\n\n".join(_merge_bullets(parts))
    if isinstance(value, list):
        if not value:
            return "_None._"
        if all(isinstance(v, dict) for v in value):
            if all(all(_is_scalar(x) or isinstance(x, list) for x in v.values()) for v in value):
                return _table(value)
            return "\n\n".join(_render(v, level) for v in value)
        return "\n".join(f"- {_cell(v)}" for v in value)
    return _cell(value)


def _merge_bullets(parts: list[str]) -> list[str]:
    """Keep consecutive '- **Key:** value' lines together as one list."""
    merged: list[str] = []
    for p in parts:
        if p.startswith("- **") and merged and merged[-1].startswith("- **"):
            merged[-1] += "\n" + p
        else:
            merged.append(p)
    return merged
