<!-- Generated from qa_agents/knowledge/regression-selection.md by scripts/sync_skill_references.py. Do not edit here. -->

## Terms (Yoo & Harman 2012 survey)
- Selection: choose the tests relevant to a change. Prioritisation: order tests so faults are found as early
  as possible. Minimisation: permanently remove redundant tests (not done here).
- A safe selection technique keeps every test that could reveal a fault in the change. Module-map selection
  is UNSAFE (heuristic), so it must be paired with an always-run set and a full run before release.

## Selection checklist
- Change impact: changed files -> modules -> tests, plus the modules that depend on them (indirect impact).
- Always run: smoke/critical-path tests, new or changed tests, and tests for any area that has no mapping.
- Build, dependency, CI or shared configuration changes (pom.xml, build.gradle, package.json, lockfiles,
  requirements.txt, Dockerfile, CI pipelines, shared libraries) can affect everything: recommend the full suite.
- Database migrations: run data-access tests and a migration rehearsal (forward and rollback).
- Feature-flag changes: test both flag states for the affected features.
- Risk weighting: defect history per module, code churn, number of recent authors (Google found code changed
  by more than 3 developers breaks more often), and business criticality.
- History-based (Elbaum et al., Google): favour tests that failed recently or have not run for a while;
  discount known-flaky tests by their flip rate rather than dropping them.

## Prioritisation
- Order: smoke -> directly impacted P1 -> highest defect-history modules -> indirect -> the rest.
- Report the estimated duration, and what is deliberately NOT run and why.

Sources: Yoo & Harman, "Regression testing minimization, selection and prioritization: a survey", STVR 2012 ·
Rothermel & Harrold on safe selection (via Graves et al.) · Elbaum, Rothermel, Penix, "Techniques for improving
regression testing in continuous integration development environments", FSE 2014
https://research.google/pubs/techniques-for-improving-regression-testing-in-continuous-integration-development-environments/ ·
Memon et al., "Taming Google-Scale Continuous Testing", ICSE-SEIP 2017 https://research.google/pubs/pub45861/
