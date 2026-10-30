"""6. Flaky Test Analysis Agent: execution-history statistics plus root-cause analysis."""

from __future__ import annotations

import csv
import io
import re
import statistics
from collections import Counter, defaultdict
from typing import Literal

from pydantic import BaseModel

from qa_agents.core.base import Agent, by_suffix, facts_block
from qa_agents.core.llm import AgentError

MIN_RUNS = 5
FLAKY_FLIP_RATE = 0.15


class FlakyInsight(BaseModel):
    test: str
    classification: Literal["flaky", "broken", "stable"]
    root_cause_type: Literal[
        "timing_or_wait", "test_order_dependency", "shared_test_data", "environment_instability",
        "async_ui_rendering", "network_or_third_party", "product_race_condition", "unknown",
    ]
    likely_root_cause: str
    evidence: str
    recommended_fix: str
    quarantine: bool


class FlakyAnalysis(BaseModel):
    summary: str
    insights: list[FlakyInsight]
    patterns: list[str]
    prevention: list[str]


def error_signature(error: str) -> str:
    """Normalise ids, numbers and hashes so the same error groups together."""
    sig = re.sub(r"0x[0-9a-f]+|[0-9a-f]{8,}|\d+", "<n>", error.strip(), flags=re.IGNORECASE)
    return sig[:160]


def analyse_history(csv_text: str) -> dict:
    rows = list(csv.DictReader(io.StringIO(csv_text.strip())))
    required = {"run_id", "timestamp", "test", "status"}
    if not rows or not required <= set(rows[0]):
        raise AgentError(f"History CSV needs columns: {', '.join(sorted(required))} (optional: duration_ms, error, env).")
    per_test: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        per_test[r["test"]].append(r)

    stats = []
    for test, runs in per_test.items():
        runs.sort(key=lambda r: r["timestamp"])
        outcomes = [r["status"].strip().lower() for r in runs if r["status"].strip().lower() in ("passed", "failed")]
        fails = outcomes.count("failed")
        flips = sum(1 for a, b in zip(outcomes, outcomes[1:]) if a != b)
        flip_rate = flips / (len(outcomes) - 1) if len(outcomes) > 1 else 0.0
        durations = [float(r["duration_ms"]) for r in runs if r.get("duration_ms")]
        cv = statistics.pstdev(durations) / statistics.mean(durations) if len(durations) > 1 and statistics.mean(durations) else 0.0
        errors = Counter(error_signature(r["error"]) for r in runs if r.get("error"))
        env_fails = Counter(r.get("env", "") for r in runs if r["status"].lower() == "failed" and r.get("env"))

        if len(outcomes) < MIN_RUNS:
            label = "insufficient_data"
        elif fails and fails < len(outcomes) and flip_rate >= FLAKY_FLIP_RATE:
            label = "flaky"
        elif fails >= 3 and all(o == "failed" for o in outcomes[-3:]):
            label = "broken"
        else:
            label = "stable"
        stats.append(
            {
                "test": test,
                "runs": len(outcomes),
                "failures": fails,
                "fail_rate_pct": round(100 * fails / len(outcomes), 1) if outcomes else 0.0,
                "flip_rate_pct": round(100 * flip_rate, 1),
                "duration_cv_pct": round(100 * cv, 1),
                "label": label,
                "top_errors": [e for e, _ in errors.most_common(3)],
                "failures_by_env": dict(env_fails),
            }
        )
    stats.sort(key=lambda s: (s["label"] != "flaky", s["label"] != "broken", -s["flip_rate_pct"]))
    labels = Counter(s["label"] for s in stats)
    return {
        "tests_analysed": len(stats),
        "runs_analysed": len({r["run_id"] for r in rows}),
        "label_counts": dict(labels),
        "flaky_or_broken": [s for s in stats if s["label"] in ("flaky", "broken")],
    }


class FlakyAnalysisAgent(Agent):
    name = "flaky-tests"
    title = "Flaky Test Analysis"
    summary = "Uses execution history to find frequently failing tests, failure patterns and root causes."
    inputs_help = "a CSV of execution history: run_id, timestamp, test, status, duration_ms, error, env"
    example_files = ["execution_history.csv"]
    output_model = FlakyAnalysis
    system_prompt = """Task: explain flaky and broken tests from execution-history statistics.
Flip rate (how often pass/fail alternates), fail rate, duration variance, error signatures and
failures per environment were computed locally. For each flaky or broken test, infer the most
likely root cause from that evidence (e.g. high duration variance plus timeouts suggests waits;
failures only on one env suggests environment; 'already exists' suggests shared data; failures
only when run after a specific test suggests order dependency). Recommend a specific fix and
whether to quarantine it now. Then list patterns across tests and how to prevent new flakiness."""

    def analyse(self, files):
        csvs = by_suffix(files, ".csv")
        if not csvs:
            raise AgentError("flaky-tests needs an execution history .csv file.")
        return analyse_history("\n".join([csvs[0].text()] + [c.text().split("\n", 1)[-1] for c in csvs[1:]]))

    def build_prompt(self, files, facts):
        return f"{facts_block(facts)}\n\nAnalyse the flaky and broken tests above."
