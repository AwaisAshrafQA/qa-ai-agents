"""6. Flaky Test Analysis Agent: execution-history statistics plus root-cause analysis.

Flip rate follows Kowalczyk et al. (Apple, ICSE-SEIP 2020): pass<->fail transitions / (runs - 1).
Root-cause categories follow Luo et al. (FSE 2014), Eck et al. (FSE 2019) and Gruber et al. (2022).
"""

from __future__ import annotations

import csv
import io
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from qa_agents.core.base import Agent, by_suffix, facts_block
from qa_agents.core.llm import AgentError
from qa_agents.tools.text import error_signature

MIN_RUNS = 5
FLAKY_FLIP_RATE = 0.15
RECENT_WINDOW = 10

COLUMN_ALIASES = {
    "run_id": ["run_id", "run", "build", "build_id", "build number", "pipeline", "job", "run id", "execution id"],
    "timestamp": ["timestamp", "date", "time", "started", "start_time", "created", "run_date", "datetime"],
    "test": ["test", "test_name", "testname", "test name", "name", "testcase", "test case", "full_name", "title"],
    "status": ["status", "result", "outcome", "state", "verdict"],
    "duration_ms": ["duration_ms", "duration", "time_ms", "elapsed_ms", "duration (ms)"],
    "error": ["error", "message", "failure", "error_message", "failure message", "reason"],
    "env": ["env", "environment", "agent", "host", "machine", "platform", "browser", "os"],
}
PASS = {"passed", "pass", "success", "succeeded", "ok", "green", "true", "1"}
FAIL = {"failed", "fail", "failure", "error", "errored", "broken", "red", "false", "0", "timedout", "timeout"}


class FlakyInsight(BaseModel):
    test: str
    classification: Literal["flaky", "broken", "stable"]
    root_cause_type: Literal[
        "async_wait", "concurrency", "test_order_dependency", "shared_test_data", "resource_leak",
        "network", "time", "io", "randomness", "floating_point", "unordered_collection",
        "platform_dependency", "timeout", "external_dependency", "product_defect", "unknown",
    ]
    likely_root_cause: str
    evidence: str
    how_to_confirm: str
    recommended_fix: str
    quarantine: bool


class FlakyAnalysis(BaseModel):
    summary: str
    insights: list[FlakyInsight]
    patterns: list[str]
    prevention: list[str]


def _parse_time(value: str):
    value = value.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d", "%d/%m/%Y %H:%M", "%d/%m/%Y", "%m/%d/%Y %H:%M", "%m/%d/%Y"):
        try:
            return datetime.strptime(value.replace("Z", "+0000") if "%z" in fmt else value, fmt).replace(tzinfo=None)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value).replace(tzinfo=None)
    except ValueError:
        return None


def _flip_rate(outcomes: list[str]) -> float:
    flips = sum(1 for a, b in zip(outcomes, outcomes[1:]) if a != b)
    return flips / (len(outcomes) - 1) if len(outcomes) > 1 else 0.0


def _map_columns(fieldnames: list[str]) -> dict[str, str]:
    lower = {(f or "").strip().lower(): f for f in fieldnames}
    mapping = {}
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in lower:
                mapping[field] = lower[alias]
                break
    return mapping


def analyse_history(csv_text: str) -> dict:
    text = csv_text.strip()
    try:
        dialect = csv.Sniffer().sniff(text.splitlines()[0], delimiters=",;\t")
    except (csv.Error, IndexError):
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    cols = _map_columns(reader.fieldnames or [])
    if "test" not in cols or "status" not in cols or not ({"run_id", "timestamp"} & cols.keys()):
        raise AgentError(
            "History CSV needs a test, a status and a run id or timestamp column "
            "(e.g. run_id,timestamp,test,status,duration_ms,error,env). "
            f"Columns found: {', '.join(reader.fieldnames or []) or 'none'}."
        )
    rows, unknown_status = [], Counter()
    for i, raw in enumerate(reader):
        get = lambda k: (raw.get(cols[k]) or "").strip() if k in cols else ""
        status = get("status").lower()
        outcome = "passed" if status in PASS else "failed" if status in FAIL else None
        if outcome is None:
            if status not in ("skipped", "skip", "ignored", "pending", "not run", ""):
                unknown_status[status] += 1
            continue
        rows.append({
            "order": i, "run_id": get("run_id") or get("timestamp"), "time": _parse_time(get("timestamp")) if get("timestamp") else None,
            "test": get("test"), "outcome": outcome, "duration": get("duration_ms"), "error": get("error"), "env": get("env"),
        })
    if not rows:
        raise AgentError("The history CSV has no passed or failed results to analyse.")

    per_test: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        per_test[r["test"]].append(r)

    stats = []
    for test, runs in per_test.items():
        runs.sort(key=lambda r: (r["time"] is None, r["time"] or datetime.min, r["order"]))
        outcomes = [r["outcome"] for r in runs]
        fails = outcomes.count("failed")
        flip_rate = _flip_rate(outcomes)
        durations = []
        for r in runs:
            try:
                durations.append(float(r["duration"]))
            except ValueError:
                pass
        mean = statistics.mean(durations) if durations else 0
        cv = statistics.pstdev(durations) / mean if len(durations) > 1 and mean else 0.0
        errors = Counter(error_signature(r["error"]) for r in runs if r["error"] and r["outcome"] == "failed")
        env_runs = Counter(r["env"] for r in runs if r["env"])
        env_fails = Counter(r["env"] for r in runs if r["env"] and r["outcome"] == "failed")
        trailing_fails = len(outcomes) - len("".join("p" if o == "passed" else "f" for o in outcomes).rstrip("f"))
        flips = sum(1 for a, b in zip(outcomes, outcomes[1:]) if a != b)
        if len(outcomes) < MIN_RUNS:
            label = "insufficient_data"
        elif trailing_fails >= 3 and flips <= 1:
            label = "broken"  # passed, then failed every run since: a regression, not flakiness
        elif 0 < fails < len(outcomes) and flip_rate >= FLAKY_FLIP_RATE:
            label = "flaky"
        elif trailing_fails >= 3:
            label = "broken"
        else:
            label = "stable"
        first_fail = next((i for i, o in enumerate(outcomes) if o == "failed"), None)
        stats.append(
            {
                "test": test,
                "runs": len(outcomes),
                "failures": fails,
                "fail_rate_pct": round(100 * fails / len(outcomes), 1),
                "flip_rate_pct": round(100 * flip_rate, 1),
                "recent_flip_rate_pct": round(100 * _flip_rate(outcomes[-RECENT_WINDOW:]), 1),
                "duration_cv_pct": round(100 * cv, 1),
                "label": label,
                "first_failure_run": runs[first_fail]["run_id"] if first_fail is not None else "",
                "last_3_runs": outcomes[-3:],
                "top_errors": [e for e, _ in errors.most_common(3)],
                "failures_by_env": {e: f"{env_fails[e]}/{env_runs[e]}" for e in env_runs if env_fails[e]},
            }
        )
    stats.sort(key=lambda s: (s["label"] != "flaky", s["label"] != "broken", -s["flip_rate_pct"]))
    facts = {
        "tests_analysed": len(stats),
        "runs_analysed": len({r["run_id"] for r in rows}),
        "label_counts": dict(Counter(s["label"] for s in stats)),
        "flaky_or_broken": [s for s in stats if s["label"] in ("flaky", "broken")],
        "thresholds": {"min_runs": MIN_RUNS, "flaky_flip_rate_pct": round(100 * FLAKY_FLIP_RATE), "recent_window_runs": RECENT_WINDOW},
    }
    if unknown_status:
        facts["ignored_statuses"] = dict(unknown_status)
    return facts


class FlakyAnalysisAgent(Agent):
    name = "flaky-tests"
    title = "Flaky Test Analysis"
    summary = "Uses execution history to find frequently failing tests, failure patterns and root causes."
    inputs_help = "a CSV of execution history: run_id, timestamp, test, status, duration_ms, error, env (common export column names are recognised)"
    example_files = ["execution_history.csv"]
    output_model = FlakyAnalysis
    system_prompt = """Task: explain flaky and broken tests from execution-history statistics.
Flip rate (how often pass/fail alternates), fail rate, duration variance, error signatures and
failures per environment were computed locally. For each flaky or broken test, infer the most
likely root-cause category from the evidence, using the expert checklist (e.g. timeouts with high
duration variance suggest async_wait; failures on one environment only suggest platform_dependency
or network; 'already exists' suggests shared_test_data; consistent failures since a given run are a
product_defect, not flakiness). Say how to confirm the cause (rerun, reorder, isolate, vary the clock
or seed), recommend a specific fix and whether to quarantine it now. Then list patterns across tests
and how to prevent new flakiness."""

    def analyse(self, files):
        csvs = by_suffix(files, ".csv")
        if not csvs:
            raise AgentError("flaky-tests needs an execution history .csv file.")
        merged = csvs[0].text().strip() + "".join("\n" + c.text().strip().split("\n", 1)[-1] for c in csvs[1:])
        return analyse_history(merged)

    def build_prompt(self, files, facts):
        return f"{facts_block(facts)}\n\nAnalyse the flaky and broken tests above."
