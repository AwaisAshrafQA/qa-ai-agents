---
name: qa-failure-analysis
description: Classify failed automated tests as app defect, automation issue, test data problem or environment failure, using JUnit XML reports, logs and stack traces. Use when a test run or CI pipeline fails, or the user asks why tests failed or wants them triaged.
---

# Failure Analysis

## 1. Get the facts

Find the JUnit XML reports (e.g. `target/surefire-reports`, `test-results`, `reports/junit`) and any application, CI or browser logs from the same run. Ask if you can't find them. Then run:

```bash
qa-agents facts failure-analysis <reports.xml...> [logs...]
```

If `qa-agents` is missing, install it: `pip install git+https://github.com/AwaisAshrafQA/qa-ai-agents`.

`facts.failures` lists each failed test with a keyword-based `heuristic_category`. It is a hint, not a verdict.

## 2. Analyse

Follow `instructions`. Read the stack traces and logs yourself and match them by request id and timestamp. Open the failing test code when you need to decide between an automation issue and an app defect.

## 3. Report

A summary, then one row per failure (test, category, confidence, evidence, root cause, next action, owner), then patterns across failures and the count per category.

## 4. Offer next steps

- Rerun the failing tests to confirm the classification. Ask first, and run only those tests.
- Fix automation issues and test-data problems in the test code.
- For app defects, draft the bug report with the `qa-defect-drafting` skill.
