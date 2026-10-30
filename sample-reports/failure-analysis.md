# Failure Analysis

_Model: demo (recorded response)_

## Summary

There were 4 failures with 4 different causes: 1 product defect in coupon pricing, 1 environment outage (the refunds sandbox was down), 1 automation issue (a generated CSS class locator) and 1 test-data collision. Only the pricing defect needs a developer; the other three are owned by QA and DevOps.

## Failures

| Test | Category | Confidence | Evidence | Root Cause | Next Action | Owner |
|---|---|---|---|---|---|---|
| orders.CreateOrderTest.applies 20 percent coupon to subtotal | app_defect | high | The test expected 164.00 but got 160.00. The pricing-service log for req-7f3a91c2 says the coupon was 'applied to cart total incl. delivery fee'. | The 20% discount is calculated on subtotal + delivery fee (200.00) instead of the item subtotal (180.00). | Raise a defect for the pricing service with the request id and the log line; keep the test as is. | developer |
| orders.CancelOrderTest.cancels a paid order | environment | high | SocketTimeoutException in RefundClient. The payments-service log shows 'refunds-sandbox.example unreachable: connect ECONNREFUSED', followed by a 504 at the gateway for req-b21e0d77. | The third-party refunds sandbox was unavailable during the run. | Re-run after the sandbox is healthy, and add a health check that skips refund tests with a clear reason when the sandbox is down. | devops |
| checkout.spec.ts.guest can apply a coupon | automation_issue | high | TimeoutError waiting for locator('.css-1x9fz2a'). No matching error appears in the service logs, and the other checkout tests reached the same page. | The locator is a build-generated CSS class that changed in the latest frontend build. | Replace it with a data-testid or role locator and remove the fixed waits in the same test. | qa_automation |
| checkout.spec.ts.registered user checks out with saved card | test_data | high | POST /api/test-users returned 409 'user already exists: qa.buyer01@shoplite.example' from fixtures/users.ts:22. | The fixture creates a user with a fixed email, which collides with a user left over from an earlier run. | Generate a unique email per run (e.g. a timestamp suffix) and delete the user in teardown. | test_data_owner |

## Patterns

- Both web-checkout failures are test-side problems (locator and data), so the checkout feature itself passed in this run.
- The one real product defect also explains the failed coupon checks in other suites; expect related UI failures until it is fixed.
- The environment failure lines up with a single dependency outage at 02:14-02:15, not with general instability.

## Computed Locally

- **Failed Tests:** 4

### Failures

| Test | Suite | Message | Heuristic Category |
|---|---|---|---|
| orders.CreateOrderTest.applies 20 percent coupon to subtotal | api-orders | Expected total 164.00 but was 160.00 | app_defect |
| orders.CancelOrderTest.cancels a paid order | api-orders | java.net.SocketTimeoutException: connect timed out | environment |
| checkout.spec.ts.guest can apply a coupon | web-checkout | TimeoutError: locator.click: Timeout 10000ms exceeded. | automation_issue |
| checkout.spec.ts.registered user checks out with saved card | web-checkout | Error: user already exists: qa.buyer01@shoplite.example (409) | test_data |

### By Category

- **App Defect:** 1
- **Environment:** 1
- **Automation Issue:** 1
- **Test Data:** 1
