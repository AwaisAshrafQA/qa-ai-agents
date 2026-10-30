# Regression Test Selection

_Model: demo (recorded response)_

## Summary

The change touches discount calculation and coupon rules (pricing), the order summary UI (checkout), a feature-flag file and a database migration. Run all pricing and checkout tests plus the invoice test, because invoices depend on pricing. Keep the smoke tests. Two files are not mapped to any module and need manual checks.

## Estimated Scope

7 must_run and 2 should_run tests, about 25 minutes, plus a 30 minute manual migration rehearsal.

## Recommendations

| Test Id | Decision | Reason |
|---|---|---|
| PRC-001 | must_run | discount_calculator.py changed, and this module had a critical expiry defect (SL-367) |
| PRC-002 | must_run | Discount maths changed; protects against negative totals |
| CHK-001 | must_run | Smoke test; the order summary changed in the checkout flow |
| PRC-003 | must_run | coupon_rules.py changed; minimum subtotal rule |
| PRC-004 | must_run | coupon_rules.py changed, and the migration adds a coupon usage index |
| CHK-002 | must_run | order_summary.tsx changed; it shows the discount and the delivery fee |
| CHK-003 | should_run | Same checkout module, but this payment path is not touched by the change |
| INV-001 | should_run | Invoices depend on pricing, and SL-380 (missing coupon line) was fixed recently |
| SRC-001 | must_run | Smoke test: always part of the run, even though search is not affected |

## Additional Risks

- db/migrations/0042_add_coupon_usage_index.sql: check that it runs on a production-sized data set without long table locks.
- config/feature_flags.yaml: check which flags changed and test both states of any coupon-related flag.

## Unmapped Change Advice

- Map db/migrations/* and config/* to a 'platform' module in test_map.yaml so future changes trigger the right tests.
- For this release, add a one-off migration rehearsal and a flag on/off check to the plan.

## Computed Locally

- **Changed Files:** 5
- **Estimated Minutes Must and Should:** 25

### Changed Modules

#### Pricing

- src/pricing/discount_calculator.py
- src/pricing/coupon_rules.py

#### Checkout

- src/checkout/order_summary.tsx

### Indirectly Affected Modules

- invoices

### Unmapped Files

- config/feature_flags.yaml
- db/migrations/0042_add_coupon_usage_index.sql

### Candidate Tests

| Test Id | Name | Module | Impact | Priority | Smoke | Defect History Score | Score | Minutes |
|---|---|---|---|---|---|---|---|---|
| PRC-001 | Percentage coupon applies to subtotal only | pricing | direct | P1 | no | 18 | 88 | 2 |
| PRC-002 | Fixed coupon never makes total negative | pricing | direct | P1 | no | 18 | 88 | 2 |
| CHK-001 | Guest checkout with card | checkout | direct | P1 | yes | 2 | 82 | 4 |
| PRC-003 | Coupon minimum subtotal 100 AED | pricing | direct | P2 | no | 18 | 78 | 2 |
| PRC-004 | Coupon usage limit per shopper | pricing | direct | P2 | no | 18 | 78 | 3 |
| CHK-002 | Order summary shows discount and delivery fee | checkout | direct | P1 | no | 2 | 72 | 3 |
| CHK-003 | Cash on delivery order | checkout | direct | P2 | no | 2 | 62 | 4 |
| INV-001 | Invoice PDF shows applied discount | invoices | indirect | P2 | no | 6 | 46 | 3 |
| SRC-001 | Search returns products | search | none | P1 | yes | 0 | 40 | 2 |

### Mandatory Test Ids

- PRC-001
- PRC-002
- CHK-001
- CHK-002
- SRC-001
