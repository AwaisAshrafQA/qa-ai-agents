# SL-101 Coupon codes at checkout

Shoppers can apply one coupon per order on the checkout page.

Rules:
- Coupon codes are 6 to 12 characters, letters and digits only, not case-sensitive.
- A percentage coupon gives between 5 and 50 percent off the cart subtotal (before delivery fee).
- A fixed coupon gives a set amount off, e.g. 20 AED, and never makes the total negative.
- The cart subtotal must be at least 100 AED for any coupon to apply.
- Each coupon has an expiry date and a usage limit per shopper (default 1 times).
- After 5 attempts with invalid codes in 10 minutes, coupon entry is locked for 15 minutes.
- The applied discount is shown on the order summary, the confirmation email and the invoice PDF.
- Removing an item so the subtotal drops below the minimum removes the coupon with a message.
