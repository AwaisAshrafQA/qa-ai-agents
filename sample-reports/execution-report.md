# Test Execution Report

_Model: demo (recorded response)_

## Headline

Release 2.4.0 regression: 86.7% pass rate; one coupon pricing defect (SL-402) is behind both failures

- **Status:** at_risk

## Executive Summary

We executed 15 of 18 planned tests (83.3%). 13 passed, 2 failed and 1 was skipped. The smoke suite is fully green. Both failures come from the same open major defect, SL-402: percentage coupons are calculated including the delivery fee. Status is at risk, not off track, because the cause is known and isolated, but the release cannot be signed off until SL-402 is fixed and re-tested.

## Defect Commentary

4 defects are open: 0 critical, 1 major, 2 minor, 1 trivial. SL-402 is the only one that affects release readiness: it undercharges every percentage-coupon order. SL-398 (13-character coupon accepted) and SL-395 (coupon missing from the email) are minor and could be deferred with product approval. SL-390 is cosmetic.

## Highlights

- Smoke suite 4/4 green, including guest checkout with card and login
- Order creation, cancellation rules and 404 handling all pass in the API suite
- SL-387 (critical refund defect) and SL-384 (search price filter) are closed and verified

## Concerns

- SL-402 (major, pricing) is open and causes both failed tests: an API total of 160.00 against an expected 164.00, and the same wrong amount in the order summary UI
- Apple Pay checkout was skipped because the sandbox is not available on staging, so this payment method is untested
- 3 planned tests have not run yet, with the test window ending on 2026-10-30

## Next Steps

- Pricing team: fix SL-402 in rc4 (discount base = item subtotal)
- QA: re-run the pricing and checkout suites on rc4 and close SL-402
- QA: run the 3 remaining planned tests before 2026-10-30
- DevOps: provide an Apple Pay sandbox, or Product: accept the risk of skipping Apple Pay

## Computed Locally

### Results

- **Total:** 16
- **Executed:** 15
- **Passed:** 13
- **Failed:** 2
- **Errors:** 0
- **Skipped:** 1
- **Pass Rate Pct:** 86.7
- **Duration S:** 61.5

#### By Suite

| Suite | Passed | Failed | Skipped |
|---|---|---|---|
| smoke | 4 | 0 | 0 |
| api-orders | 5 | 1 | 0 |
| web-checkout | 4 | 1 | 1 |

#### Slowest

| Test | Seconds |
|---|---|
| smoke.guest checkout with card | 14.8 |
| checkout.invoice PDF shows applied discount | 9.7 |
| checkout.saved card checkout | 7.9 |
| checkout.cash on delivery order | 6.4 |
| smoke.login with email | 4.2 |

#### Smoke

- **Total:** 4
- **Failed:** 0
- **Skipped:** 0

### Failed Tests

| Test | Message |
|---|---|
| orders.CreateOrderTest.applies 20 percent coupon to subtotal | Expected total 164.00 but was 160.00 |
| checkout.order summary shows coupon discount | expected 'AED 164.00' to equal 'AED 160.00' |

### Skipped Tests

| Test | Reason |
|---|---|
| checkout.apple pay checkout | Apple Pay sandbox not available on staging |

### Defects

- **Total:** 7
- **Open:** 4
- **Closed:** 3

#### Open by Severity

- **Critical:** 0
- **Major:** 1
- **Minor:** 2
- **Trivial:** 1

#### Open Critical and Major

| Id | Title | Severity | Status | Module |
|---|---|---|---|---|
| SL-402 | Percentage coupon applied to delivery fee as well as items | major | Open | pricing |

#### Open Critical Major Age Days

| Id | Severity | Age Days |
|---|---|---|
| SL-402 | major | 2 |

### Progress

- **Release:** 2.4.0
- **Sprint:** Sprint 44
- **Test Window:** 2026-10-26 to 2026-10-30
- **Environment:** staging (build 2026.10.28-rc3)
- **Planned Tests:** 18
- **Executed Pct:** 83.3
- **Not Run:** 3
