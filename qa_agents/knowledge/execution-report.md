## Report contents (ISTQB CTFL v4.0, test progress and completion reports)
- Progress report: test period; progress against plan and notable deviations; impediments and workarounds;
  test metrics; new or changed risks; testing planned for the next period.
- Completion report: summary; quality evaluated against the objectives and exit criteria; deviations;
  unmitigated risks and unfixed defects; lessons learned.

## Metrics (use the computed numbers; never recalculate)
- Pass rate = passed / executed. Execution progress = executed / planned.
- Report failed, blocked/not run and skipped separately: a skipped or not-run test is untested, not passed.
- Tests that passed only on rerun are flaky: list them; they are a risk, not a clean pass.
- Defects: open by severity, newly opened vs closed in the period, defect age for open critical/major.
- Where available: requirements coverage (requirements with a passing test / total), defect detection
  percentage (found in test / found in test + after release).

## Status rules
- on_track: progress in line with plan, no open critical, failures understood.
- at_risk: known blockers or open major defects with a plan, or progress behind but recoverable.
- off_track: open critical defects, a red smoke suite, or progress that cannot meet the date.
- Every concern names its impact and an owner role; every next step is doable this period.

## Style
- Lead with the answer (headline + status), then the evidence. Readable in two minutes.
- No vanity metrics: a high pass rate with large untested areas is not good news; say so.

Sources: ISTQB CTFL v4.0 syllabus, sections 5.3.1-5.3.2 https://istqb.org/certifications/certified-tester-foundation-level-ctfl-v4-0
