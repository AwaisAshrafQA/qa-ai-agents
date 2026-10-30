<!-- Generated from qa_agents/knowledge/release-readiness.md by scripts/sync_skill_references.py. Do not edit here. -->

## Go / no-go checklist
- All exit criteria met, or each deviation explicitly waived by a named owner (waivers are conditions, not silence).
- No open critical defects; no open major defect without an approved workaround.
- Smoke / critical-path suite 100% green; every failure triaged (none unexplained); flaky passes confirmed by rerun.
- High-risk areas covered by tests; untested areas (skipped, not run, sandbox unavailable) listed as residual risk.
- Static quality gate passing where used (e.g. SonarQube "Sonar way" on new code: no new issues, A ratings,
  all new security hotspots reviewed, >= 80% coverage, <= 3% duplication).
- Risk register: risk level = likelihood x impact (ISTQB); every high risk has a mitigation and an owner.

## Decision rules
- no_go: any failed hard gate, an open critical defect, a red smoke suite or an unmitigated high risk.
- go_with_conditions: gates pass but residual risks need specific, verifiable conditions (e.g. feature flag
  off, hotfix window, monitoring alert), each with an owner.
- go: all gates pass, residual risks low and accepted.
- Conditions must be checkable ("SL-402 verified fixed in rc4 by PRC-001"), not vague ("monitor closely").

## Release safeguards
- Rollback ready before rollout ("no good rollout without a corresponding rollback"); database schema
  changes complicate rollback, so plan them as expand/contract.
- Canary or staged rollout comparing the canary with a control group; feature flags for risky changes.
- Monitoring and alerts on the changed flows for the first hours/days.
- DORA: change fail rate = share of deployments needing immediate intervention; failed deployment recovery
  time = time to recover from one. Readiness decisions aim to keep both low.

Sources: ISTQB CTFL v4.0 (risk level, exit criteria) · SonarQube quality gates
https://docs.sonarsource.com/sonarqube-server/quality-standards-administration/managing-quality-gates/introduction-to-quality-gates ·
Google SRE Workbook, "Canarying Releases" https://sre.google/workbook/canarying-releases/ · Google CRE, "Reliable releases
and rollbacks" https://cloud.google.com/blog/products/gcp/reliable-releases-and-rollbacks-cre-life-lessons/ · DORA metrics
https://dora.dev/guides/dora-metrics/
