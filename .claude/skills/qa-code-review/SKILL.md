---
name: qa-code-review
description: Review UI and API test automation code (Playwright, Cypress, Selenium, REST Assured, pytest, etc.) for test smells and flaky patterns - fixed waits, unstable locators, hardcoded secrets and data, weak or missing assertions, focused/skipped tests, swallowed exceptions, duplication - against official framework guidance. Use when the user asks to review tests, a test pull request or automation framework code.
---

# Automation Code Review

## 1. Inputs

The test files to review: the files changed in the branch (`git diff --name-only origin/main...HEAD`), or the files the user names. Also note the project's page objects, fixtures and config, so the fixes you suggest reuse what already exists.

## 2. Compute the facts

```bash
qa-agents facts code-review <test files...>
```

`facts.static_findings` lists candidate problems with file, line, rule and default severity. The rules cover:
- fixed, discouraged and mixed waits
- unstable locators
- hardcoded secrets and hardcoded data (with a Luhn check for card numbers)
- weak, non-retrying and missing assertions
- focused and skipped tests
- forced actions
- swallowed exceptions
- conditional logic
- debug output
- duplicated blocks

Comments, including `/* */` blocks, are ignored.

If `qa-agents` is missing, run `pip install git+https://github.com/AwaisAshrafQA/qa-ai-agents`. If it still can't run, review the files with [reference.md](reference.md), and say that the static scan was not run.

## 3. Analyse

Follow `instructions` (expert checklist: test-smell catalogue, Playwright, Cypress and Selenium official guidance, OWASP secrets). Confirm or dismiss each static finding with a reason. Then add what a scan can't see: order dependence, shared state, missing cleanup, tests that can't fail, UI login repeated in every test.

## 4. Report

A verdict (approve, approve with comments, or request changes), a summary, comments as a table (file, line, rule, severity, problem, fix) and refactoring suggestions. Each fix uses the framework's own idiom, for example `getByRole` / `expect(...).toBeVisible()`, `cy.intercept` + `cy.wait('@alias')`, or `WebDriverWait`.

## 5. Quality bar (check before presenting)

- Any high-severity finding left means the verdict is "request changes".
- Every line number exists in the file.
- Any hardcoded secret comes with a reminder that it must be revoked and rotated, not just removed.

## 6. Next steps (ask first)

- Apply the fixes one file at a time, then run the affected tests and report the results.
- Add lint rules for the most common problem (e.g. `playwright/no-wait-for-timeout`, `no-only-tests`) and a secret scanner (gitleaks or detect-secrets) to CI.
