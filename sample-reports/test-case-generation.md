# Test Case Generation

_Model: demo (recorded response)_

## Summary

These 18 cases cover every coupon rule using equivalence partitioning, 3-value boundary value analysis on all 8 limits found, a decision table for coupon eligibility, and state transitions for the lockout. They also include integration and non-functional checks. Every computed boundary probe value is used. Two gaps in the requirement are listed in the coverage notes.

## Test Cases

| Id | Title | Type | Technique | Coverage Item | Quality Characteristic | Priority | Requirement Ref | Preconditions | Steps | Test Data | Expected Result |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TC-001 | Valid 20% coupon reduces the item subtotal only | positive | equivalence_partitioning | valid percentage coupon partition | functional_suitability | P1 | Percentage coupon | Cart subtotal 180 AED, delivery fee 20 AED; Coupon SAVE20 is active | Open checkout; Enter SAVE20; Click Apply | SAVE20 (20%) | Discount 36.00 AED; total 164.00 AED (180 - 36 + 20) |
| TC-002 | Code is not case-sensitive | positive | equivalence_partitioning | lower-case variant of a valid code | functional_suitability | P2 | Code format | Coupon SAVE20 is active | Enter save20; Click Apply | save20 | Accepted; same 36.00 AED discount as SAVE20 |
| TC-003 | Code length boundaries: 5, 6, 7 characters | boundary | boundary_value_analysis | lower length bound 6 (probes 5, 6, 7) | functional_suitability | P2 | Code format | Active codes of 6 and 7 characters exist | Apply a 5-character code; Apply a 6-character code; Apply a 7-character code | ABCDE (5), ABCDE1 (6), ABCDE12 (7) | 5 rejected with a format error; 6 and 7 accepted |
| TC-004 | Code length boundaries: 11, 12, 13 characters | boundary | boundary_value_analysis | upper length bound 12 (probes 11, 12, 13) | functional_suitability | P2 | Code format | Active codes of 11 and 12 characters exist | Apply an 11-character code; Apply a 12-character code; Apply a 13-character code | ABCDEFGHIJ1 (11), ABCDEFGHIJ12 (12), ABCDEFGHIJ123 (13) | 11 and 12 accepted; 13 rejected with a format error |
| TC-005 | Percentage range boundaries: 4, 5, 6, 49, 50, 51 percent | boundary | boundary_value_analysis | percentage bounds 5 and 50 (probes 4, 5, 6, 49, 50, 51) | functional_suitability | P2 | Percentage range | Admin can create coupons | Create percentage coupons at 4, 5, 6, 49, 50 and 51 percent | 4 / 5 / 6 / 49 / 50 / 51 % | 5, 6, 49 and 50 accepted; 4 and 51 rejected at creation with a range error |
| TC-006 | Minimum subtotal boundaries: 99, 100, 101 AED | boundary | boundary_value_analysis | minimum subtotal 100 AED (probes 99, 100, 101) | functional_suitability | P1 | Minimum subtotal | Coupon SAVE20 is active | Set the subtotal to 99, 100 and 101 AED in turn; Apply SAVE20 each time | Subtotals 99 / 100 / 101 AED | Rejected at 99 AED with 'minimum 100 AED'; accepted at 100 and 101 AED |
| TC-007 | Fixed coupon amount boundaries: 19, 20, 21 AED | boundary | boundary_value_analysis | fixed amount 20 AED (probes 19, 20, 21) | functional_suitability | P2 | Fixed coupon | Fixed coupons worth 19, 20 and 21 AED exist; Subtotal 150 AED | Apply each coupon on a fresh cart | FLAT19 / FLAT20 / FLAT21 | Totals drop by exactly 19.00, 20.00 and 21.00 AED |
| TC-008 | Fixed coupon larger than the subtotal never gives a negative total | boundary | error_guessing | discount > subtotal (computation) | functional_suitability | P1 | Fixed coupon | Coupon worth 120 AED; Subtotal 101 AED, delivery 20 AED | Apply the coupon | FLAT120 | Item total floors at 0.00 AED; only the 20.00 AED delivery fee is charged |
| TC-009 | Usage limit per shopper: 0, 1, 2 previous uses | boundary | boundary_value_analysis | usage limit 1 (probes 0, 1, 2 prior uses) | functional_suitability | P1 | Usage limit | Coupon WELCOME with the default limit of 1 | Apply with 0 prior uses; Apply with 1 prior use; Apply with 2 prior uses (data seeded) | WELCOME; shopper usage counts 0 / 1 / 2 | Accepted with 0 prior uses; rejected with 'already used' at 1 and 2 |
| TC-010 | Lockout after 4, 5, 6 invalid attempts | boundary | state_transition | transition open -> locked at attempt 5 (probes 4, 5, 6) | security | P1 | Lockout | Logged-in shopper, no recent attempts | Enter 4 invalid codes, then a valid one; Reset; enter 5 invalid codes, then a valid one; Enter a 6th invalid code | BAD001 to BAD006, then SAVE20 | After 4 the valid code works; after 5 entry is locked; the 6th attempt shows the lock message |
| TC-011 | Attempt window: 9, 10, 11 minutes | boundary | boundary_value_analysis | attempt window 10 minutes (probes 9, 10, 11) | security | P2 | Lockout | Clock can be controlled in the test environment | Make 5 invalid attempts spread over 9 minutes; Repeat spread over 10 minutes; Repeat spread over 11 minutes | Attempt spacing for 9 / 10 / 11 minute windows | Locked for the 9 and 10 minute windows; not locked when the attempts span 11 minutes |
| TC-012 | Lock duration: 14, 15, 16 minutes | boundary | state_transition | transition locked -> open after 15 minutes (probes 14, 15, 16) | security | P2 | Lockout | Coupon entry locked | Try a valid code after 14 minutes; Try after 15 minutes; Try after 16 minutes | SAVE20 at +14 / +15 / +16 minutes | Rejected at 14 minutes; accepted at 15 and 16 minutes |
| TC-013 | Expired coupon is rejected | negative | decision_table | rule: expired = true -> reject | functional_suitability | P1 | Expiry | Coupon OLD10 expired yesterday; Subtotal 150 AED | Apply OLD10 | OLD10 | Rejected with an expiry message; total unchanged |
| TC-014 | Special characters in the code | negative | equivalence_partitioning | invalid character partition | security | P2 | Code format |  | Apply SAVE-20!; Apply ' OR 1=1 -- | SAVE-20!, ' OR 1=1 -- | Format error for both; no server error; nothing logged unescaped |
| TC-015 | Coupon removed when the subtotal drops below the minimum | integration | state_transition | transition applied -> removed on cart change | functional_suitability | P1 | Cart changes | SAVE20 applied, subtotal 110 AED | Remove a 20 AED item | Subtotal becomes 90 AED | Coupon removed with an explanation; total recalculated to 110.00 AED (90 + 20 delivery) |
| TC-016 | Discount shown on the confirmation email and the invoice PDF | integration | use_case | main flow: order -> email -> invoice | functional_suitability | P2 | Downstream display | Order placed with SAVE20 | Open the confirmation email; Download the invoice PDF | Order with SAVE20 | Both show SAVE20 and a 36.00 AED discount that matches the order summary |
| TC-017 | Double-submit and concurrent use of a single-use coupon | integration | error_guessing | concurrency / idempotency | reliability | P1 | Usage limit | Single-use coupon; The same shopper on two devices | Place two orders with the coupon at the same moment; Double-click Place order | ONCE50 | Only one order gets the discount; no duplicate order is created |
| TC-018 | Coupon field is accessible | non_functional | error_guessing | WCAG 2.2 AA: label, error announcement, keyboard | interaction_capability | P3 | Coupon entry | Screen reader (NVDA) on | Tab to the coupon field; Apply an invalid code | BAD001 | Field has a visible label; the error is announced and linked to the field; everything works by keyboard |

## Coverage Notes

- Every one of the 8 numeric limits is probed with 3-value BVA.
- Gap: the requirement does not say whether VAT is applied before or after the discount.
- Gap: the time zone used for expiry dates (local time or UTC) is not stated.
- Decision table (minimum met x active x not expired x under usage limit) gives 16 combinations; TC-001, TC-006, TC-009 and TC-013 cover the deciding rules.

## Automation Candidates

- TC-001 to TC-014 at the API level (fast, data-driven over the probe values)
- TC-015 and TC-016 as end-to-end UI tests, with an email inbox API and PDF text checks
- TC-017 as a concurrency test against the orders API; TC-018 with axe-core plus a manual screen-reader check

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

### Suggested Techniques

- equivalence_partitioning: every input and output field
- boundary_value_analysis (3-value): 8 numeric limits found
- decision_table: 2 conditional phrases (if/when/unless...) combine into rules
- state_transition: lifecycle terms found (locked)

### Cases by Type

- **Positive:** 2
- **Boundary:** 10
- **Negative:** 2
- **Integration:** 3
- **Non Functional:** 1

### Cases by Technique

- **Equivalence Partitioning:** 3
- **Boundary Value Analysis:** 7
- **Error Guessing:** 3
- **State Transition:** 3
- **Decision Table:** 1
- **Use Case:** 1

### Cases by Priority

- **P1:** 8
- **P2:** 9
- **P3:** 1
