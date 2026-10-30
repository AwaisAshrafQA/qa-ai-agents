---
name: qa-code-review
description: Review test automation code for hardcoded data, weak assertions, unstable locators, fixed waits, duplicated code and other causes of flaky or unmaintainable tests. Use when the user asks to review tests, a test pull request or automation framework code.
---

# Automation Code Review

## 1. Get the facts

Find the test files to review (the changed files in the branch, or the files the user names), then run:

```bash
qa-agents facts code-review <test files...>
```

If `qa-agents` is missing, install it: `pip install git+https://github.com/AwaisAshrafQA/qa-ai-agents`.

`facts.static_findings` lists candidate problems with file, line and rule. These come from a static scan: confirm or dismiss each one.

## 2. Analyse

Follow `instructions`. Open each file and check what a scan cannot: missing assertions, order dependence, shared state, missing cleanup, swallowed exceptions. Look at the project's page objects, fixtures and config before suggesting a fix, so fixes use what already exists.

## 3. Report

A verdict (approve, approve with comments, request changes), a summary, then comments as a table (file, line, rule, severity, problem, fix) and refactoring suggestions.

## 4. Offer next steps

- Apply the fixes. Ask first, change one file at a time, then run the affected tests and report the results.
- Add a lint rule that blocks the most common problem (e.g. `playwright/no-wait-for-timeout`).
