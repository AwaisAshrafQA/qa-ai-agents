---
name: qa-defect-drafting
description: Turn logs, screenshots, API responses and tester notes into a complete, reproducible bug report (title, severity vs priority, environment, numbered steps, expected vs actual, evidence, suspected cause) following ISO 29119-3 and research on what developers need. Use when the user asks to write, draft or file a bug, defect or Jira issue.
---

# Defect Drafting

## 1. Inputs

Collect the evidence: logs (`.log`/`.txt`), API responses (`.json`), screenshots (`.png`/`.jpg`) and tester notes (`.md`). Save pasted text to files first. If the build, environment or reproduction rate is unknown, ask once, then record what's still unknown under open questions.

## 2. Compute the facts

```bash
qa-agents facts defect-drafting <files...>
```

For each file, the facts give its error and warning lines, HTTP statuses, request/trace ids and time window, plus the key fields of each JSON response.

If `qa-agents` is missing, run `pip install git+https://github.com/AwaisAshrafQA/qa-ai-agents`. If it still can't run, extract these yourself using [reference.md](reference.md).

## 3. Analyse

Follow `instructions` (expert checklist: Bettenburg et al. 2008 on what developers need, ISO 29119-3 incident report fields, ISTQB severity vs priority).
- Open every screenshot and read it yourself.
- Cross-check the values between the screenshot, the logs and the API response.
- If the code is in this repository, look for the suspected root cause, and label it as suspected.

Mask secrets and personal data in anything you quote.

## 4. Report

A ready-to-file bug report:
- title: `[Component] What fails, under which condition`
- summary
- severity and priority, each with a reason
- component and environment
- preconditions and test data
- numbered steps to reproduce
- expected and actual results with exact values
- evidence, with file names, lines, request ids and timestamps
- suspected root cause, labels and open questions

## 5. Quality bar (check before presenting)

- Someone who wasn't there could follow the steps and reproduce the bug.
- Expected and actual results differ in a specific, quoted value.
- Exactly one defect per report: split the report if the evidence shows two.

## 6. Next steps (ask first)

- If a Jira, Linear or GitHub connector is available, show the final text and create the issue only after the user approves.
- Write a failing automated test that reproduces the bug.
