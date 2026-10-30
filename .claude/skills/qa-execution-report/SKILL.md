---
name: qa-execution-report
description: Write a QA status report from test results, defect status and test progress, with a headline, on-track/at-risk/off-track status, highlights, concerns and next steps. Use when the user asks for a test summary, QA status update, sprint test report or daily report.
---

# Test Execution Report

## 1. Get the facts

Collect the JUnit XML reports, a defects CSV (`id,title,severity,status,module`) and optionally a progress YAML (`planned_tests`, `sprint`, `test_window`, `environment`). Then run:

```bash
qa-agents facts execution-report <results.xml...> [defects.csv] [progress.yaml]
```

If `qa-agents` is missing, install it: `pip install git+https://github.com/AwaisAshrafQA/qa-ai-agents`.

The facts hold the totals, pass rate, per-suite results, slowest tests, failed tests, defects by severity and progress. They come from code: quote the numbers exactly and never recalculate them.

## 2. Analyse

Follow `instructions`. Keep it readable in two minutes.

## 3. Report

Headline, status, executive summary, highlights, concerns, defect commentary and next steps (each with an owner role). Include a small results table taken from the facts.

## 4. Offer next steps

- A short version for Slack or Teams, or an email to stakeholders. Show it and let the user send it; if a messaging connector is available, post only after explicit approval.
