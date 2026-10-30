"""7. Defect Drafting Agent: logs, screenshots and API responses into a structured bug report."""

from __future__ import annotations

import base64
import json
import re
from typing import Literal

from pydantic import BaseModel

from qa_agents.core.base import IMAGE_TYPES, Agent, facts_block, file_block
_ERROR_LINE = re.compile(r"\b(WARN|ERROR|FATAL|Exception|Traceback|panic)\b")
_STATUS = re.compile(r"\b(?:HTTP/\d\.\d\s+|status[=: ]+)([1-5]\d\d)\b", re.IGNORECASE)
_IDS = re.compile(r"(?i)\b(request[-_ ]?id|correlation[-_ ]?id|trace[-_ ]?id|x-request-id)[\"'\s:=]+([\w-]{6,})")
_TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")


class DefectReport(BaseModel):
    title: str
    summary: str
    severity: Literal["critical", "major", "minor", "trivial"]
    priority: Literal["P1", "P2", "P3", "P4"]
    component: str
    environment: str
    preconditions: list[str]
    steps_to_reproduce: list[str]
    expected_result: str
    actual_result: str
    evidence: list[str]
    suspected_root_cause: str
    labels: list[str]
    open_questions: list[str]


def scan_text(text: str) -> dict:
    lines = text.splitlines()
    stamps = _TIMESTAMP.findall(text)
    return {
        "error_lines": [l.strip()[:200] for l in lines if _ERROR_LINE.search(l)][:15],
        "http_statuses": sorted(set(_STATUS.findall(text))),
        "ids": sorted({f"{k}: {v}" for k, v in _IDS.findall(text)}),
        "time_window": [min(stamps), max(stamps)] if stamps else [],
    }


def scan_json(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"valid_json": False}
    keys = ("status", "statusCode", "code", "error", "errorCode", "message", "detail", "traceId", "requestId")
    found = {k: data[k] for k in keys if isinstance(data, dict) and k in data}
    return {"valid_json": True, "key_fields": found}


class DefectDraftingAgent(Agent):
    name = "defect-drafting"
    title = "Defect Report"
    summary = "Turns logs, screenshots and API responses into a structured bug report with reproduction steps."
    inputs_help = "any mix of .log/.txt, API response .json, screenshots (.png/.jpg) and notes (.md)"
    example_files = ["notes.md", "checkout-service.log", "api_response.json", "screenshot.png"]
    output_model = DefectReport
    system_prompt = """Task: write one high-quality defect report from the evidence provided.
Reproduction steps must be numbered, minimal and runnable by someone who was not there.
Expected vs actual must be precise (status codes, values, messages). Reference evidence by file
name, line, request id and timestamp. Set severity by user impact and priority by business
urgency; justify both in the summary. Put unknowns (e.g. exact build, frequency) under open
questions instead of guessing. Title format: [Component] What fails, when or where."""

    def analyse(self, files):
        facts = {}
        for f in files:
            if f.suffix in IMAGE_TYPES:
                facts[f.name] = {"type": "screenshot", "bytes": f.path.stat().st_size}
            elif f.suffix == ".json":
                facts[f.name] = scan_json(f.text())
            else:
                facts[f.name] = scan_text(f.text())
        return facts

    def build_prompt(self, files, facts):
        blocks: list[dict] = []
        for f in files:
            if f.suffix in IMAGE_TYPES:
                data = base64.standard_b64encode(f.path.read_bytes()).decode("utf-8")
                blocks.append({"type": "text", "text": f"Screenshot: {f.name}"})
                blocks.append({"type": "image", "source": {"type": "base64", "media_type": IMAGE_TYPES[f.suffix], "data": data}})
        texts = "\n\n".join(file_block(f) for f in files if f.suffix not in IMAGE_TYPES)
        blocks.append({"type": "text", "text": f"{texts}\n\n{facts_block(facts)}\n\nDraft the defect report."})
        return blocks
