---
name: qa-regression-selection
description: Recommend which regression tests to run for a change set, using the changed files, a module-to-test map and defect history. Use when the user asks what to test for a branch, pull request or release, or how to shorten a regression run.
---

# Regression Test Selection

## 1. Get the facts

1. Save the changed files: `git diff --name-only origin/main...HEAD > changed_files.txt` (adjust the base branch).
2. Find the test map YAML (modules with path globs, `depends_on` and tests). If the project has none, build one from the folder structure and test tags, and show it to the user before you rely on it.
3. Optionally, export defect history as CSV (`id,title,module,severity,status`).

```bash
qa-agents facts regression-selection changed_files.txt test_map.yaml [defects.csv]
```

If `qa-agents` is missing, install it: `pip install git+https://github.com/AwaisAshrafQA/qa-ai-agents`.

`facts.candidate_tests` are scored by impact, priority, smoke tag and defect history. `facts.unmapped_files` were matched to no module.

## 2. Analyse

Follow `instructions` and the `guardrails`: every test in `facts.mandatory_test_ids` is must_run, with no exceptions. Open the unmapped files to judge their risk (config, migrations, shared libraries).

## 3. Report

A summary, a table of tests (id, decision, reason), additional risks, advice on unmapped files and the estimated scope and time.

## 4. Offer next steps

- Give the exact command to run the selected tests with the project's runner (tags, grep, a TestNG group or pytest `-k`), and run it if the user agrees.
- Add the unmapped paths to the test map.
