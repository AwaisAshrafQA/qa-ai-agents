---
name: qa-flaky-tests
description: Find flaky and broken tests from execution history using flip rate (Apple), fail rate, duration variance, error signatures and per-environment failures, then explain root causes using the flaky-test research taxonomy (async wait, concurrency, order dependency, time, network...) with how to confirm, fix and whether to quarantine. Use when the user asks about flaky tests, unstable pipelines or which tests to quarantine.
---

# Flaky Test Analysis

## 1. Inputs

You need an execution history CSV. Common export column names are recognised, for example Build, Date, Test Name, Outcome, Duration and Environment.

If the user only has JUnit reports from several runs, build the CSV from them first, with the columns `run_id,timestamp,test,status,duration_ms,error,env`. Fewer than 5 runs per test is not enough to judge; say so.

## 2. Compute the facts

```bash
qa-agents facts flaky-tests <execution_history.csv>
```

`facts.flaky_or_broken` gives each problem test:
- runs and fail rate
- flip rate, overall and over the last 10 runs
- duration variance
- the first failing run and the last 3 outcomes
- top error signatures
- failures by environment (failed/total)

A test that passed and then failed every run since is labelled `broken`, which means a regression, not flakiness.

If `qa-agents` is missing, run `pip install git+https://github.com/AwaisAshrafQA/qa-ai-agents`. If it still can't run, compute the flip rate yourself as transitions / (runs - 1), using [reference.md](reference.md), and say so.

## 3. Analyse

Follow `instructions` (expert checklist: Luo et al. and later categories, detection methods, metrics, quarantine policy). Open each flaky test's code: the cause is usually visible, such as sleeps, shared data, order dependence, unseeded randomness or time-zone assumptions.

## 4. Report

A summary, then one row per test (classification, root-cause type, likely cause, evidence, how to confirm, fix, quarantine yes/no), then patterns across tests and prevention steps.

## 5. Quality bar (check before presenting)

- Broken tests are reported as product defects or regressions, not as flakiness.
- Every root cause cites the statistic or code line that supports it.
- A quarantine recommendation always comes with an owner and a fix-by date.

## 6. Next steps (ask first)

- Confirm a test by rerunning it in a loop, e.g. Playwright `--repeat-each=20`, pytest-rerunfailures or Surefire `rerunFailingTestsCount`, or in a different order.
- Apply the fix, or add the project's quarantine tag.
