"""Defect export (CSV) loading and summaries. Works with a plain Jira/Azure DevOps CSV export."""

from __future__ import annotations

import csv
import io
from collections import Counter

SEVERITY_ORDER = ["critical", "major", "minor", "trivial"]
OPEN_STATUSES = {"open", "new", "in progress", "reopened", "to do", "blocked", "in review"}


def load_defects(csv_text: str) -> list[dict[str, str]]:
    rows = list(csv.DictReader(io.StringIO(csv_text.strip())))
    return [{k.strip().lower(): (v or "").strip() for k, v in row.items() if k} for row in rows]


def is_open(defect: dict[str, str]) -> bool:
    return defect.get("status", "").lower() in OPEN_STATUSES


def summarise_defects(defects: list[dict[str, str]]) -> dict:
    open_defects = [d for d in defects if is_open(d)]
    sev = Counter(d.get("severity", "").lower() for d in open_defects)
    return {
        "total": len(defects),
        "open": len(open_defects),
        "closed": len(defects) - len(open_defects),
        "open_by_severity": {s: sev.get(s, 0) for s in SEVERITY_ORDER},
        "open_critical_and_major": [
            {k: d.get(k, "") for k in ("id", "title", "severity", "status", "module")}
            for d in sorted(open_defects, key=lambda d: _sev_rank(d))
            if d.get("severity", "").lower() in ("critical", "major")
        ],
    }


def _sev_rank(d: dict[str, str]) -> int:
    s = d.get("severity", "").lower()
    return SEVERITY_ORDER.index(s) if s in SEVERITY_ORDER else len(SEVERITY_ORDER)
