# Flaky Test Analysis

_Model: demo (recorded response)_

## Summary

Of 6 tests across 12 nightly runs, 3 are flaky and 1 is broken. Each flaky test has a different cause: an async wait, an environment-specific network dependency, and shared test data. The price filter test has failed in every run since run 9 with a low flip rate, which is the signature of a product regression, not flakiness.

## Insights

| Test | Classification | Root Cause Type | Likely Root Cause | Evidence | How to Confirm | Recommended Fix | Quarantine |
|---|---|---|---|---|---|---|---|
| checkout.spec.ts > guest can apply a coupon | flaky | async_wait | The test clicks a build-generated CSS class after a fixed 3 second wait. When the page renders slowly, the click times out at 10 seconds. | 72.7% flip rate; every failure is the same locator timeout; duration varies by 25.6%; failures appear on both environments. | Run it 20 times with Playwright --repeat-each=20, then again with CPU throttling; the failure rate should rise under load. | Use a data-testid or role locator and a web-first assertion instead of waitForTimeout. | yes |
| orders.CancelOrderTest > cancels a paid order | flaky | network | Every failure happened on staging-b, where the connection to the refunds sandbox times out. | failures_by_env: staging-b 4/4 runs failed, staging-a 0; 111.8% duration variation caused by 30 second timeouts; a single error signature. | Call the refunds sandbox health endpoint from a staging-b agent and from a staging-a agent. | Fix the network route from staging-b to the refunds sandbox, and add a dependency health check that skips refund tests with a clear reason when the sandbox is down. | no |
| checkout.spec.ts > registered user checks out with saved card | flaky | shared_test_data | The fixture creates users with predictable emails that collide with leftovers from earlier runs. | Every failure is a 409 'user already exists'; duration is stable (5.3%), which rules out timing. | Run the suite twice in a row against the same environment without cleanup; the second run should fail. | Generate a unique email per run and delete the user in teardown. | no |
| search.spec.ts > filters products by price | broken | product_defect | A consistent failure since run-009 (0 results for 50-100 AED) points to a regression in the search price filter or its index. | Flip rate is only 9.1%: it passed for 8 runs, then failed in all 4 runs from run-009. | Query the search API for the 50-100 AED range directly; bisect the changes merged before run-009. | Treat this as a product defect: raise a bug, and re-index search on staging if the index is stale. | no |

## Patterns

- Failures are spread across different root causes; there is no systemic framework problem.
- Environment-specific failures cluster on staging-b, so environment health should be part of the nightly report.
- Two of the four problems are test-design issues (waits, data) that review rules could prevent.

## Prevention

- Block waitForTimeout and Thread.sleep with lint rules in CI.
- Have every fixture generate unique data and clean up after itself.
- Track flip rate weekly and quarantine tests above 30% automatically, with an owner and a fix-by date.
- Run a dependency health check at the start of each pipeline and tag failures it explains as environment issues.

## Computed Locally

- **Tests Analysed:** 6
- **Runs Analysed:** 12

### Label Counts

- **Flaky:** 3
- **Broken:** 1
- **Stable:** 2

### Flaky or Broken

- **Test:** checkout.spec.ts > guest can apply a coupon
- **Runs:** 12
- **Failures:** 5
- **Fail Rate Pct:** 41.7
- **Flip Rate Pct:** 72.7
- **Recent Flip Rate Pct:** 77.8
- **Duration Cv Pct:** 25.6
- **Label:** flaky
- **First Failure Run:** run-002

#### Last 3 Runs

- passed
- failed
- passed

#### Top Errors

- TimeoutError: locator.click: Timeout <n>ms exceeded. waiting for locator('.css-<n>x<n>fz<n>a')

#### Failures by Env

- **Staging-a:** 3/8
- **Staging-b:** 2/4

- **Test:** orders.CancelOrderTest > cancels a paid order
- **Runs:** 12
- **Failures:** 4
- **Fail Rate Pct:** 33.3
- **Flip Rate Pct:** 63.6
- **Recent Flip Rate Pct:** 66.7
- **Duration Cv Pct:** 111.8
- **Label:** flaky
- **First Failure Run:** run-003

#### Last 3 Runs

- passed
- passed
- failed

#### Top Errors

- java.net.SocketTimeoutException: connect timed out at RefundClient.refund

#### Failures by Env

- **Staging-b:** 4/4

- **Test:** checkout.spec.ts > registered user checks out with saved card
- **Runs:** 12
- **Failures:** 3
- **Fail Rate Pct:** 25.0
- **Flip Rate Pct:** 36.4
- **Recent Flip Rate Pct:** 44.4
- **Duration Cv Pct:** 5.3
- **Label:** flaky
- **First Failure Run:** run-004

#### Last 3 Runs

- passed
- passed
- passed

#### Top Errors

- Error: POST /api/test-users returned <n> Conflict: user already exists: <email>

#### Failures by Env

- **Staging-a:** 2/8
- **Staging-b:** 1/4

- **Test:** search.spec.ts > filters products by price
- **Runs:** 12
- **Failures:** 4
- **Fail Rate Pct:** 33.3
- **Flip Rate Pct:** 9.1
- **Recent Flip Rate Pct:** 11.1
- **Duration Cv Pct:** 4.2
- **Label:** broken
- **First Failure Run:** run-009

#### Last 3 Runs

- failed
- failed
- failed

#### Top Errors

- AssertionError: expected <n> results but got <n> (price filter <n>-<n> AED)

#### Failures by Env

- **Staging-a:** 2/8
- **Staging-b:** 2/4

### Thresholds

- **Min Runs:** 5
- **Flaky Flip Rate Pct:** 15
- **Recent Window Runs:** 10
