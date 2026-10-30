---
name: qa-regression-selection
description: Recommend which regression tests to run for a change set (branch, PR or release) from the changed files, a module-to-test map with dependencies and defect history; scores risk, keeps smoke and P1 tests, flags migrations, unmapped files and build/dependency changes that need a full run. Use when the user asks what to test for a change, or how to shorten a regression run safely.
---

# Regression Test Selection

## 1. Inputs

1. The changed files: run `git diff --name-only origin/main...HEAD > changed_files.txt` and adjust the base branch. Output from `--name-status` or `--stat` also works, and so do Windows paths.
2. The test map YAML: modules with path globs, `depends_on` and tests (id, priority P1-P3, tags, minutes). If the project has none, build one from the folder structure and test tags, and show it to the user before relying on it.
3. Optional: defect history as a CSV. A Jira or Azure DevOps export works.

## 2. Compute the facts

```bash
qa-agents facts regression-selection changed_files.txt test_map.yaml [defects.csv]
```

The facts include:
- direct impact, and indirect impact through transitive dependencies
- risk-scored `candidate_tests`
- `mandatory_test_ids`
- `unmapped_files`, `changed_test_files` and `migration_files`
- `full_suite_recommended`, set when build, dependency, CI or test-config files changed

The test map is validated, and errors say exactly what to fix.

If `qa-agents` is missing, run `pip install git+https://github.com/AwaisAshrafQA/qa-ai-agents`. If it still can't run, map the files by hand with [reference.md](reference.md), and say so.

## 3. Analyse

Follow `instructions` and both `guardrails`:
- every mandatory test is `must_run`
- when `full_suite_recommended` is true, the plan says a full run is needed before release

Module-map selection is heuristic, so state what is not run and why. Open the unmapped and migration files to judge their risk.

## 4. Report

A summary, then a table of tests (id, decision, reason tied to a changed file), then additional risks, advice on unmapped files, and the estimated scope and time.

## 5. Quality bar (check before presenting)

- All mandatory tests are present as `must_run`.
- Changed test files are run.
- Migrations come with a forward and rollback rehearsal.
- Feature-flag changes are tested in both states.

## 6. Next steps (ask first)

- Give the exact command for the project's runner (Playwright `--grep`, a TestNG group, `pytest -k`, a Maven `-Dgroups` value), and run it if the user agrees.
- Add the unmapped paths to the test map.
