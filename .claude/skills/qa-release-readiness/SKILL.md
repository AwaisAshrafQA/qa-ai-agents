---
name: qa-release-readiness
description: Decide go, go with conditions or no-go for a release from test results, open defects, the risk register (likelihood x impact) and release criteria, with quality gates evaluated in code (pass rate, open critical/major, smoke, unmitigated risks, execution, skipped, flaky). Use when the user asks whether a release is ready, for a go/no-go, sign-off or release-readiness report.
---

# Release Readiness

## 1. Inputs

Collect:
- JUnit XML reports
- a defects CSV (Jira or Azure DevOps export)
- a risks YAML (`risks:` with id, description, likelihood, impact, mitigation and owner; ratings can be low/medium/high or 1-5)
- a criteria YAML

Ask the user for their real criteria; never make them up. Supported criteria:

```yaml
release: 2.4.0
criteria:
  min_pass_rate: 95
  max_open_critical: 0
  max_open_major: 0
  require_smoke_pass: true
  max_high_risks_without_mitigation: 0
  min_executed_pct: 95        # needs planned_tests
  planned_tests: 120
  max_skipped: 5
  max_flaky_passes: 0
```

## 2. Compute the facts

```bash
qa-agents facts release-readiness <results.xml...> defects.csv risks.yaml criteria.yaml
```

`facts.gates` shows each criterion's target, actual value and pass/fail. `facts.all_gates_passed` is the overall result. The gates fail safe:
- missing defect data fails the defect gates
- skipped smoke tests fail the smoke gate
- a risk with an unrated likelihood or impact counts as high

If `qa-agents` is missing, run `pip install git+https://github.com/AwaisAshrafQA/qa-ai-agents`. If it still can't run, evaluate each criterion by hand with [reference.md](reference.md), and say so.

## 3. Analyse

Follow `instructions` and the `guardrails`: if `all_gates_passed` is false, the decision is never "go". Weigh the open defects by user impact, the risk register, untested areas and the areas the failed tests touch.

## 4. Report

The decision, confidence and rationale, then:
- the gates table from the facts
- blocking issues
- the exact, verifiable conditions that would turn the decision into "go", each with an owner
- residual risks (risk, level, mitigation)
- recommendations: feature flags, canary or staged rollout, a rollback plan, monitoring and a hotfix window

## 5. Quality bar (check before presenting)

- The decision is consistent with the gates.
- Every condition can be checked, e.g. "SL-402 verified fixed by PRC-001", never "monitor closely".
- Every high risk has a mitigation and an owner, or appears as a blocker.

## 6. Next steps (ask first)

- Draft the release sign-off note, or the risk section of the release notes.
