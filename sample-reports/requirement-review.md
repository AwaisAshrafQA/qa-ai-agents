# Requirement Review

_Model: demo (recorded response)_

## Summary

One of three stories is ready. SL-101 has acceptance criteria but they are not measurable, and SL-102 has none at all. SL-103 is close to ready; it needs payment-failure handling and a rule for when an existing account's email is used for a guest order.

## Stories

| Story | Readiness | Reason |
|---|---|---|
| SL-101 Apply a discount coupon at checkout | needs_clarification | The criteria say a coupon 'reduces the order total' and show an 'appropriate message', but neither is testable: there is no discount base, no rule for stacking or expiry, and no defined messages. |
| SL-102 Save cart for logged-in users | not_ready | There are no acceptance criteria. 'Sync quickly' has no target, and there is no rule for merging a guest cart into a saved cart, or for out-of-stock and price changes. |
| SL-103 Guest checkout | needs_clarification | The happy path is clear in Given/When/Then form. Payment failure, the duplicate-email rule and email delivery failure are not covered. |

## Issues

| Story | Category | Severity | Finding | Question for Product Owner |
|---|---|---|---|---|
| SL-101 Apply a discount coupon at checkout | ambiguity | high | The discount base is undefined: it is not clear whether a percentage coupon applies to the items only or also to the delivery fee and taxes. | Is the discount calculated on the item subtotal only, before the delivery fee and VAT? |
| SL-101 Apply a discount coupon at checkout | missing_acceptance_criteria | high | There are no criteria for expired, already-used or minimum-spend coupons, and no criteria for more than one coupon on an order. | Which coupon states must be rejected, and can an order have more than one coupon? |
| SL-101 Apply a discount coupon at checkout | ambiguity | medium | 'An appropriate message' cannot be verified. | What is the exact message text for each rejection reason (invalid, expired, minimum not met, already used)? |
| SL-101 Apply a discount coupon at checkout | edge_case | medium | The story does not say what happens to an applied coupon when the cart changes (an item is removed or a quantity changes). | Is the coupon re-validated on every cart change, and what does the shopper see if it stops being valid? |
| SL-102 Save cart for logged-in users | missing_acceptance_criteria | high | The story has no acceptance criteria. | Can we agree on the criteria in refinement: saving, restoring, merging, and expiry of saved carts? |
| SL-102 Save cart for logged-in users | non_functional | medium | 'Sync quickly' has no measurable target. | What is the maximum acceptable delay before a cart change appears on another device (for example, 5 seconds)? |
| SL-102 Save cart for logged-in users | edge_case | high | The story does not cover merging a guest cart with a saved cart on login, or saved items that changed price or went out of stock. | On login, do we merge the guest cart and the saved cart? If so, what happens to duplicate items and items whose price changed? |
| SL-103 Guest checkout | edge_case | medium | The story does not say what happens when a guest enters an email address that already belongs to a registered account. | Should a guest be able to check out with a registered email address, or be prompted to log in? |
| SL-103 Guest checkout | missing_acceptance_criteria | medium | There are no criteria for a declined card or for a confirmation email that fails to send. | What should the guest see after a declined payment, and is the order kept if the email fails? |
| SL-103 Guest checkout | dependency | low | Cash on delivery may depend on the delivery area. | Is cash on delivery available in every delivery area, or only in some areas? |

## Suggested Acceptance Criteria

| Story | Criterion |
|---|---|
| SL-101 Apply a discount coupon at checkout | Given a cart subtotal of 200 AED and a valid 20% coupon, when I apply the coupon, then the discount is 40 AED and is calculated on the item subtotal only. |
| SL-101 Apply a discount coupon at checkout | Given an expired coupon, when I apply it, then the order total is unchanged and I see 'This coupon has expired'. |
| SL-102 Save cart for logged-in users | Given I add an item on my phone, when I open the cart on my laptop within 5 seconds, then I see the same item and quantity. |
| SL-102 Save cart for logged-in users | Given I have a guest cart and a saved cart, when I log in, then the two carts are merged and quantities of identical items are added together. |
| SL-103 Guest checkout | Given my card is declined, when I place a guest order, then no order is created, my cart is kept and I see the reason for the decline. |

## Computed Locally

- **Story Count:** 3

### Stories

- **Story:** SL-101 Apply a discount coupon at checkout
- **Acceptance Criteria Count:** 3
- **Given When Then Lines:** 0

#### Ambiguous Terms

##### Weak Phrase

- appropriate

##### Optional

- can
- should

#### Structural Checks

- touches money, accounts or personal data but states no non-functional requirement

- **Story:** SL-102 Save cart for logged-in users
- **Acceptance Criteria Count:** 0
- **Given When Then Lines:** 0

#### Ambiguous Terms

##### Optional

- can
- should

##### Subjective

- quickly

#### Structural Checks

- no acceptance criteria
- no 'so that' benefit (INVEST: Valuable)

- **Story:** SL-103 Guest checkout
- **Acceptance Criteria Count:** 3
- **Given When Then Lines:** 2

#### Ambiguous Terms

##### Optional

- can

#### Structural Checks

- acceptance criteria cover only positive scenarios
- no 'so that' benefit (INVEST: Valuable)
