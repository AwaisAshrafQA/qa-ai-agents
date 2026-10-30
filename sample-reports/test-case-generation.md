# Test Case Generation

_Model: demo (recorded response)_

## Summary

These 14 cases cover the coupon rules: the code format, the discount range, the minimum subtotal, usage limits, lockout, and how the discount shows up on downstream documents. The boundary cases probe every limit that was computed locally.

## Test Cases

| Id | Title | Type | Priority | Requirement Ref | Preconditions | Steps | Test Data | Expected Result |
|---|---|---|---|---|---|---|---|---|
| TC-001 | Valid 20% coupon reduces the item subtotal | positive | P1 | Percentage coupon | Cart subtotal 180 AED, delivery fee 20 AED; Coupon SAVE20 is active | Open checkout; Enter SAVE20; Click Apply | SAVE20 (20%) | Discount 36.00 AED, total 164.00 AED (180 - 36 + 20) |
| TC-002 | Coupon code is not case-sensitive | positive | P2 | Code format | Coupon SAVE20 is active | Enter save20; Click Apply | save20 | The coupon is accepted and the same discount as SAVE20 is applied |
| TC-003 | Fixed coupon applies a set amount | positive | P1 | Fixed coupon | Subtotal 150 AED; Coupon FLAT20 (20 AED) is active | Apply FLAT20 | FLAT20 | The total drops by exactly 20.00 AED |
| TC-004 | Code length at the boundaries (5, 6, 12, 13 characters) | boundary | P2 | Code format | Active codes exist with 6 and 12 characters | Apply a 5-character code; Apply a 6-character code; Apply a 12-character code; Apply a 13-character code | ABCDE, ABCDE1, ABCDEFGHIJ12, ABCDEFGHIJ123 | 6 and 12 characters are accepted; 5 and 13 are rejected with a format error |
| TC-005 | Minimum subtotal at the boundaries (99, 100, 101 AED) | boundary | P1 | Minimum subtotal | Coupon SAVE20 is active | Set the subtotal to 99, 100 and 101 AED in turn; Apply SAVE20 each time | Subtotals 99 / 100 / 101 AED | Rejected at 99 AED; accepted at 100 and 101 AED |
| TC-006 | Percentage limits (4, 5, 50, 51 percent) | boundary | P2 | Percentage range | Admin can create coupons | Create coupons at 4, 5, 50 and 51 percent | 4 / 5 / 50 / 51 % | 5 and 50 percent are allowed; 4 and 51 percent are rejected when the coupon is created |
| TC-007 | Fixed coupon larger than the subtotal | boundary | P1 | Fixed coupon | Coupon worth 120 AED; Subtotal 101 AED | Apply the coupon | FLAT120 | The item total floors at 0.00 AED, only the delivery fee is charged, and the total is never negative |
| TC-008 | Lockout after 5 invalid attempts in 10 minutes | boundary | P1 | Lockout | Logged-in shopper | Enter 4 invalid codes; Enter a 5th invalid code; Enter a valid code | BAD001 to BAD005, then SAVE20 | After the 5th attempt coupon entry is locked for 15 minutes, and the valid code is rejected while the lock lasts |
| TC-009 | Expired coupon is rejected | negative | P1 | Expiry | Coupon OLD10 expired yesterday | Apply OLD10 | OLD10 | The coupon is rejected with an expiry message and the total is unchanged |
| TC-010 | Usage limit reached | negative | P1 | Usage limit | The shopper already used WELCOME once | Apply WELCOME on a new order | WELCOME | Rejected with 'already used' |
| TC-011 | Special characters in the code | negative | P2 | Code format |  | Apply SAVE-20! | SAVE-20! | Format error; no request reaches the pricing service |
| TC-012 | Coupon removed when the subtotal drops below 100 AED | integration | P1 | Cart changes | SAVE20 applied, subtotal 110 AED | Remove a 20 AED item | Subtotal 90 AED | The coupon is removed, a message explains why, and the total is recalculated |
| TC-013 | Discount on the confirmation email and the invoice PDF | integration | P2 | Downstream display | Order placed with SAVE20 | Open the confirmation email; Download the invoice PDF | Order with SAVE20 | Both show the coupon code and a 36.00 AED discount that matches the order summary |
| TC-014 | Two sessions apply a single-use coupon at the same time | integration | P2 | Usage limit | Single-use coupon; The same shopper is logged in on two devices | Place two orders with the coupon at the same moment | ONCE50 | Only one order gets the discount |

## Coverage Notes

- Every numeric limit in the requirement has a below / at / above probe.
- The requirement does not say whether VAT is applied before or after the discount, so tax calculation is not covered.
- Time-zone handling for expiry dates should be confirmed (local time or UTC).

## Automation Candidates

- TC-001 to TC-011 at the API level (fast, data-driven over the probe values)
- TC-012 and TC-013 as end-to-end UI tests, with an email inbox API and PDF text checks
- TC-014 as a concurrency test against the orders API

## Computed Locally

### Numeric Limits

| Text | Probe Values |
|---|---|
| 6 to 12 characters | 5; 6; 7; 11; 12; 13 |
| between 5 and 50 percent | 4; 5; 6; 49; 50; 51 |
| 20 AED | 19; 20; 21 |
| at least 100 AED | 99; 100; 101 |
| 1 times | 0; 1; 2 |
| 5 attempts | 4; 5; 6 |
| 10 minutes | 9; 10; 11 |
| 15 minutes | 14; 15; 16 |

### Cases by Type

- **Positive:** 3
- **Boundary:** 5
- **Negative:** 3
- **Integration:** 3

### Cases by Priority

- **P1:** 8
- **P2:** 6
