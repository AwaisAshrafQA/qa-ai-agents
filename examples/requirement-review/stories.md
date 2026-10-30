# SL-101 Apply a discount coupon at checkout

As a shopper, I want to apply a coupon code at checkout so that I pay less.

Acceptance criteria:
- The shopper can enter a coupon code on the checkout page.
- A valid coupon reduces the order total.
- The system should show an appropriate message for invalid coupons.

# SL-102 Save cart for logged-in users

As a logged-in shopper, I want my cart saved so I can continue on another device.

Notes: cart should sync quickly between devices.

# SL-103 Guest checkout

As a guest, I want to check out without creating an account.

Acceptance criteria:
- Given I am not logged in, when I go to checkout, then I can continue as a guest.
- Given I check out as a guest, when I place the order, then I receive an order confirmation email.
- Guest orders support card and cash on delivery payment methods.
