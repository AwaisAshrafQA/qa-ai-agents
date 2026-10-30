# Release Readiness

_Model: demo (recorded response)_

- **Decision:** no_go
- **Confidence:** high

## Rationale

Two quality gates fail. The pass rate is 86.7% against a target of 95%, and there is 1 open major defect against a limit of 0. Both come from SL-402, which undercharges every percentage-coupon order, a direct revenue impact that also matches the top-ranked risk R1 (high likelihood, high impact). The smoke suite is green and there are no open critical defects, so the release is close: one fix and re-test should clear both gates.

## Blocking Issues

- SL-402: percentage coupon calculated on subtotal plus delivery fee (open, major)
- Pass rate 86.7% is below the 95% gate

## Conditions

- SL-402 is fixed in rc4 and verified by PRC-001 and CHK-002
- The pricing and checkout regression suites are re-run with a pass rate of at least 95%
- Alternative if the fix slips: ship with percentage coupons switched off via the coupons.percent flag, with Product sign-off

## Residual Risks

| Risk | Level | Mitigation |
|---|---|---|
| R2: the coupon usage index migration may lock the coupon_usage table | high | Run it in the low-traffic window; it has been rehearsed on a production-sized copy |
| R3: Apple Pay is untested on staging | low | None recorded. Add a production smoke test right after deployment and monitor Apple Pay success rates |

## Recommendations

- Ship coupon changes behind the coupons.percent flag so they can be switched off quickly
- Watch average discount per order and the coupon error rate for 48 hours after release
- Keep a rollback plan for migration 0042 and a hotfix window open for the first 24 hours

## Computed Locally

- **Release:** 2.4.0
- **All Gates Passed:** no

### Results

- **Total:** 16
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

### Failed Tests

| Test | Message |
|---|---|
| orders.CreateOrderTest.applies 20 percent coupon to subtotal | Expected total 164.00 but was 160.00 |
| checkout.order summary shows coupon discount | expected 'AED 164.00' to equal 'AED 160.00' |

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

### Risks

| Id | Description | Likelihood | Impact | Mitigation | Owner | Score | Level |
|---|---|---|---|---|---|---|---|
| R1 | Coupon discount miscalculated when delivery fee applies (SL-402), customers undercharged | high | high | Fix in rc4, or disable percentage coupons with the coupons.percent feature flag | Pricing team | 9 | high |
| R2 | New coupon usage index migration locks the coupon_usage table on large data sets | medium | high | Run migration in the low-traffic window; tested on a production-sized copy | Platform team | 6 | high |
| R3 | Apple Pay checkout not tested on staging (sandbox unavailable) | low | medium |  | QA | 2 | low |

### Gates

| Gate | Target | Actual | Passed |
|---|---|---|---|
| Pass rate | >= 95% | 86.7% | no |
| Open critical defects | <= 0 | 0 | yes |
| Open major defects | <= 0 | 1 | no |
| Smoke suite green | 0 failures | 0 failures | yes |
| Unmitigated high risks | <= 0 | 0 | yes |
