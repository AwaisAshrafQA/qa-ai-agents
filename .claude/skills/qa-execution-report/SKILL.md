---
name: qa-execution-report
description: Write a QA status or test completion report from test results, defect status and progress (ISTQB v4.0 report contents) with headline, on-track/at-risk/off-track status, exact metrics, highlights, concerns and owned next steps. Use when the user asks for a test summary, QA status update, sprint/daily test report or test completion report.
---

# Test Execution Report

## 1. Inputs

- JUnit XML reports.
- A defects CSV; a Jira or Azure DevOps export works.
- Optionally, a progress YAML with `planned_tests`, `sprint`, `test_window` and `environment`.

Ask for the planned test count if progress matters to the audience.

## 2. Compute the facts

```bash
qa-agents facts execution-report <results.xml...> [defects.csv] [progress.yaml]
```

The facts include:
- totals: executed, passed, failed, skipped, pass rate
- results per suite, the slowest tests and a smoke summary
- the failed and skipped tests
- tests that passed only on rerun
- defects by severity, with the age of open critical and major defects
- progress, with the number of tests not run

All numbers come from code: quote them exactly.

If `qa-agents` is missing, run `pip install git+https://github.com/AwaisAshrafQA/qa-ai-agents`. If it still can't run, count from the reports yourself with [reference.md](reference.md), and say so.

## 3. Analyse

Follow `instructions` (expert checklist: ISTQB report contents, metrics, status rules). Untested is not passed: report failed, skipped and not-run tests separately.

## 4. Report

The headline and status first, then:
- the executive summary
- a results table taken from the facts
- highlights and concerns
- defect commentary
- next steps, each with an owner role

It should take two minutes to read.

## 5. Quality bar (check before presenting)

- Every number matches `facts` exactly.
- The status follows the rules: an open critical defect or a red smoke suite means `off_track`.
- Every concern states its impact.

## 6. Next steps (ask first)

- Write a short version for Slack, Teams or email. If a messaging connector is available, post only after the user explicitly approves.
