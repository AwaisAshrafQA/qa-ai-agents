## Classification signals (heuristics used in industry triage; not a formal standard)
- app_defect: assertion on business values fails the same way on rerun; stack frames in application code;
  a matching 5xx or exception in the service log for the same request id; area changed recently.
- automation_issue: NoSuchElement / StaleElement / locator timeout, NPE or TypeError inside test code,
  test-only stack frames; started after a test-code change; the feature works when checked by hand or API.
- test_data: 404 / not found, 409 / duplicate key / constraint violation, expired or locked accounts,
  missing fixtures; several unrelated tests that share the same data fail together.
- environment: connection refused/reset, DNS, TLS/certificate, timeout before any assertion, OOM, disk
  full, 502/503/504 from a dependency, lost CI agent; many unrelated tests fail in one job, on one host,
  or in the same minute.
- flaky (not a failure class here): passes on rerun at the same commit. Surefire records these as
  <flakyFailure>/<flakyError> and the build passes; <rerunFailure>/<rerunError> mean it failed every rerun.

## Method
- Cluster first: failures with the same error signature, host or time window usually share one cause;
  a cluster across unrelated tests points to environment or shared data, not N separate bugs.
- Use time and request ids to join test failures to service logs; quote the decisive line.
- Confidence: high only when two independent signals agree (e.g. assertion + matching server error);
  low when only the keyword hint supports it. Recommend a rerun when it would settle the question.
- A false alarm is a failure not caused by the code under test (Herzig & Nagappan, Microsoft): environment
  and test-side failures must not reach developers as product bugs.
- Never mark a real product defect as flaky to get a green build.

## JUnit XML facts
- <failure> = assertion failed; <error> = unexpected exception; <skipped> = not executed; a <testcase>
  with no child passed. There is no official schema; tools differ in attributes and nesting.

Sources: Herzig & Nagappan, "Empirically Detecting False Test Alarms Using Association Rules", ICSE-SEIP 2015
https://www.microsoft.com/en-us/research/publication/empirically-detecting-false-test-alarms-using-association-rules/ ·
Jiang et al., "What Causes My Test Alarm?", ICSE 2017 https://arxiv.org/abs/1703.00768 · JUnit XML format notes
https://github.com/testmoapp/junitxml · Maven Surefire rerun docs
https://maven.apache.org/surefire/maven-surefire-plugin/examples/rerun-failing-tests.html
