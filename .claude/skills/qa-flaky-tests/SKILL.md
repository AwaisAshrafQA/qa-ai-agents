---
name: qa-flaky-tests
description: Find flaky and broken tests from execution history using fail rate, flip rate, duration variance and error signatures, then explain the root causes and fixes. Use when the user asks about flaky tests, unstable pipelines or which tests to quarantine.
---

# Flaky Test Analysis

## 1. Get the facts

You need a history CSV with the columns `run_id,timestamp,test,status,duration_ms,error,env`. If the user has JUnit reports from several runs instead, build that CSV from them first. Then run:

```bash
qa-agents facts flaky-tests <execution_history.csv>
```

If `qa-agents` is missing, install it: `pip install git+https://github.com/AwaisAshrafQA/qa-ai-agents`.

`facts.flaky_or_broken` gives each problem test's runs, fail rate, flip rate, duration variance, top error signatures and failures by environment. These come from code: use them exactly.

## 2. Analyse

Follow `instructions`. Open the test code for each flaky test: the root cause is usually visible there (fixed waits, shared data, order dependence).

## 3. Report

A summary, one row per test (classification, root-cause type, likely cause, evidence, fix, quarantine yes/no), then patterns and prevention.

## 4. Offer next steps

- Rerun a flaky test several times in a row (e.g. Playwright `--repeat-each=10`) to confirm it. Ask first.
- Apply the fix, or add the project's quarantine tag with an owner and a fix-by date.
