---
name: qa-release-readiness
description: Decide go, go with conditions or no-go for a release from test results, open defects, the risk register and release criteria, with quality gates checked in code. Use when the user asks whether a release is ready, for a go/no-go, sign-off or release-readiness report.
---

# Release Readiness

## 1. Get the facts

Collect the JUnit XML reports, a defects CSV, a risks YAML (`risks:` with likelihood, impact, mitigation, owner) and a criteria YAML, for example:

```yaml
release: 2.4.0
criteria:
  min_pass_rate: 95
  max_open_critical: 0
  max_open_major: 0
  require_smoke_pass: true
  max_high_risks_without_mitigation: 0
```

Ask the user for their real criteria; don't make them up. Then run:

```bash
qa-agents facts release-readiness <results.xml...> defects.csv risks.yaml criteria.yaml
```

If `qa-agents` is missing, install it: `pip install git+https://github.com/AwaisAshrafQA/qa-ai-agents`.

`facts.gates` shows each criterion with its target, actual value and pass/fail. `facts.all_gates_passed` is the overall result.

## 2. Analyse

Follow `instructions` and the `guardrails`: if `all_gates_passed` is false, the decision is never "go", whatever else looks good.

## 3. Report

Decision, confidence and rationale, then blocking issues, the exact conditions that would change the decision to go, residual risks (risk, level, mitigation) and recommendations. Include the gates table from the facts.

## 4. Offer next steps

- Draft the release sign-off note or the risk section of the release notes.
