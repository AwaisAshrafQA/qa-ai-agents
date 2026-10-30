"""Defect export loading and summaries.

Accepts plain CSVs and raw exports from Jira, Azure DevOps, GitHub and similar tools: column names
are matched by alias, comma or semicolon delimiters are detected, and severity scales such as
"Blocker", "1 - Critical", "S2" or a priority column are normalised to critical/major/minor/trivial.
Unknown statuses count as OPEN, so a missing mapping can never hide a defect from a quality gate.
"""

from __future__ import annotations

import csv
import io
import re
from collections import Counter

from qa_agents.core.llm import AgentError

SEVERITY_ORDER = ["critical", "major", "minor", "trivial"]

COLUMN_ALIASES = {
    "id": ["id", "key", "issue key", "issue id", "defect id", "bug id", "work item id", "number"],
    "title": ["title", "summary", "name", "subject"],
    "severity": ["severity", "custom field (severity)", "bug severity"],
    "priority": ["priority"],
    "status": ["status", "state", "resolution status"],
    "module": ["module", "component", "components", "component/s", "area path", "area", "feature", "labels"],
    "created": ["created", "created date", "opened", "created at"],
}

SEVERITY_ALIASES = [
    ("critical", r"blocker|critical|highest|urgent|showstopper|^s?0$|^s?1\b|^p0$|^1\s*-"),
    ("major", r"major|high|^s?2\b|^p1$|^2\s*-"),
    ("minor", r"minor|medium|normal|moderate|^s?3\b|^p2$|^3\s*-"),
    ("trivial", r"trivial|low|lowest|cosmetic|^s?4\b|^p[34]$|^4\s*-"),
]

CLOSED_STATUSES = {
    "closed", "done", "resolved", "fixed", "verified", "released", "completed", "complete",
    "won't fix", "wont fix", "won't do", "rejected", "duplicate", "cancelled", "canceled",
    "not a bug", "works as designed", "by design", "cannot reproduce", "obsolete", "removed",
}


def normalise_severity(value: str) -> str:
    v = value.strip().lower()
    for level, pattern in SEVERITY_ALIASES:
        if v and re.search(pattern, v):
            return level
    return "unknown" if v else ""


def load_defects(csv_text: str, source: str = "defects.csv") -> list[dict[str, str]]:
    text = csv_text.strip()
    if not text:
        return []
    try:
        dialect = csv.Sniffer().sniff(text.splitlines()[0], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    headers = {(h or "").strip().lower(): h for h in (reader.fieldnames or [])}
    mapping = {}
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in headers:
                mapping[field] = headers[alias]
                break
    if "id" not in mapping and "title" not in mapping:
        raise AgentError(f"{source}: no id or title column found. Columns seen: {', '.join(headers) or 'none'}.")

    defects = []
    for row in reader:
        d = {field: (row.get(col) or "").strip() for field, col in mapping.items()}
        if not any(d.values()):
            continue
        raw = d.get("severity") or d.get("priority", "")
        d["severity"] = normalise_severity(raw)
        if raw and d["severity"] == "unknown":
            d["severity_raw"] = raw
        d.setdefault("status", "")
        defects.append(d)
    return defects


def is_open(defect: dict[str, str]) -> bool:
    return defect.get("status", "").strip().lower() not in CLOSED_STATUSES


def summarise_defects(defects: list[dict[str, str]]) -> dict:
    open_defects = [d for d in defects if is_open(d)]
    sev = Counter(d.get("severity", "") or "unknown" for d in open_defects)
    summary = {
        "total": len(defects),
        "open": len(open_defects),
        "closed": len(defects) - len(open_defects),
        "open_by_severity": {s: sev.get(s, 0) for s in SEVERITY_ORDER},
        "open_critical_and_major": [
            {k: d.get(k, "") for k in ("id", "title", "severity", "status", "module")}
            for d in sorted(open_defects, key=_sev_rank)
            if d.get("severity") in ("critical", "major")
        ],
    }
    if sev.get("unknown"):
        summary["open_with_unknown_severity"] = sev["unknown"]
    unknown_status = sorted({d["status"] for d in open_defects if d["status"].lower() not in _KNOWN_OPEN})
    if unknown_status:
        summary["statuses_treated_as_open"] = unknown_status
    return summary


_KNOWN_OPEN = {"open", "new", "in progress", "reopened", "to do", "todo", "blocked", "in review", "active", "triage", "backlog", "committed", "assigned"}


def _sev_rank(d: dict[str, str]) -> int:
    s = d.get("severity", "")
    return SEVERITY_ORDER.index(s) if s in SEVERITY_ORDER else len(SEVERITY_ORDER)
