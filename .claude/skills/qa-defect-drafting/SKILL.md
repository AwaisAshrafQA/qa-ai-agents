---
name: qa-defect-drafting
description: Turn logs, screenshots, API responses and tester notes into a complete bug report with title, severity, reproduction steps, expected and actual results and evidence. Use when the user asks to write, draft or file a bug, defect or Jira issue.
---

# Defect Drafting

## 1. Get the facts

Collect the evidence files: logs (`.log`/`.txt`), API responses (`.json`), screenshots (`.png`/`.jpg`) and notes (`.md`). Save pasted text to files first. Then run:

```bash
qa-agents facts defect-drafting <files...>
```

If `qa-agents` is missing, install it: `pip install git+https://github.com/AwaisAshrafQA/qa-ai-agents`.

The facts give the error lines, HTTP statuses, request ids and time window found in each file.

## 2. Analyse

Follow `instructions`. Open each screenshot and read it yourself. Cross-check the numbers between screenshot, log and API response. If the code is in this repository, look for the suspected root cause, but label it as suspected.

## 3. Report

A ready-to-file bug report: title (`[Component] What fails, when or where`), summary, severity and priority with a reason, component, environment, preconditions, numbered steps to reproduce, expected result, actual result, evidence, suspected root cause, labels and open questions.

## 4. Offer next steps

- If a Jira or Linear connector is available, offer to create the issue. Show the final text and wait for the user's approval before creating it.
- Write a failing automated test that reproduces the bug.
