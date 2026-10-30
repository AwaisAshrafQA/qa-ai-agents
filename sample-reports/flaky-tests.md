# Flaky Test Analysis

_Model: demo (recorded response)_

## Summary

Of 6 tests across 12 nightly runs, 3 are flaky and 1 is broken. Each flaky test has a different cause: a wait or locator problem, an environment-specific dependency, and shared test data. The price filter test started failing on every run from run 9, which points to a regression rather than flakiness.

## Insights

| Test | Classification | Root Cause Type | Likely Root Cause | Evidence | Recommended Fix | Quarantine |
|---|---|---|---|---|---|---|
| checkout.spec.ts > guest can apply a coupon | flaky | timing_or_wait | The test clicks a build-generated CSS class after a fixed 3 second wait. When the page renders slowly, the click times out at 10 seconds. | 72.7% flip rate; every failure is the same locator timeout; duration varies by 25.6%; failures appear on both environments. | Use a data-testid locator and web-first assertions instead of waitForTimeout. | yes |
| orders.CancelOrderTest > cancels a paid order | flaky | environment_instability | All 4 failures happened on staging-b, where the refunds sandbox connection times out. | failures_by_env: staging-b 4, staging-a 0; 111.8% duration variation caused by 30 second timeouts; a single error signature. | Fix the network route from staging-b to the refunds sandbox, and add a dependency health check before refund tests. | no |
| checkout.spec.ts > registered user checks out with saved card | flaky | shared_test_data | The fixture creates users with predictable emails that collide with leftovers from earlier runs. | Every failure is a 409 'user already exists'; duration is stable (5.3%), which rules out timing. | Use a unique email per run and clean up users in teardown. | no |
| search.spec.ts > filters products by price | broken | unknown | A consistent failure since run 9 (0 results for 50-100 AED) suggests a regression in the search price filter or its index. | Flip rate is only 9.1%: it passed for 8 runs, then failed in every run from run 9. | Treat this as a product defect: check the changes merged before run 9 and re-index search on staging. | no |

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
- **Duration Cv Pct:** 25.6
- **Label:** flaky

#### Top Errors

- TimeoutError: locator.click: Timeout <n>ms exceeded. waiting for locator('.css-<n>x<n>fz<n>a')

#### Failures by Env

- **Staging-a:** 3
- **Staging-b:** 2

- **Test:** orders.CancelOrderTest > cancels a paid order
- **Runs:** 12
- **Failures:** 4
- **Fail Rate Pct:** 33.3
- **Flip Rate Pct:** 63.6
- **Duration Cv Pct:** 111.8
- **Label:** flaky

#### Top Errors

- java.net.SocketTimeoutException: connect timed out at RefundClient.refund

#### Failures by Env

- **Staging-b:** 4

- **Test:** checkout.spec.ts > registered user checks out with saved card
- **Runs:** 12
- **Failures:** 3
- **Fail Rate Pct:** 25.0
- **Flip Rate Pct:** 36.4
- **Duration Cv Pct:** 5.3
- **Label:** flaky

#### Top Errors

- Error: POST /api/test-users returned <n> Conflict: user already exists: qa.buyer<n>@shoplite.example

#### Failures by Env

- **Staging-a:** 2
- **Staging-b:** 1

- **Test:** search.spec.ts > filters products by price
- **Runs:** 12
- **Failures:** 4
- **Fail Rate Pct:** 33.3
- **Flip Rate Pct:** 9.1
- **Duration Cv Pct:** 4.2
- **Label:** broken

#### Top Errors

- AssertionError: expected <n> results but got <n> (price filter <n>-<n> AED)

#### Failures by Env

- **Staging-b:** 2
- **Staging-a:** 2
