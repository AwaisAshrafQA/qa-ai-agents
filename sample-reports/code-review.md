# Automation Code Review

_Model: demo (recorded response)_

## Summary

Both files follow patterns that cause flaky, slow and hard-to-maintain tests: 5 fixed waits, positional XPath and CSS locators, hardcoded URLs and credentials, and assertions that pass even when the feature is broken. The two coupon tests in checkout.spec.ts duplicate the same setup. Changes are required before merge.

- **Verdict:** request_changes

## Comments

| File | Line | Rule | Severity | Problem | Fix |
|---|---|---|---|---|---|
| checkout.spec.ts | 13 | weak_assertion | high | toBeTruthy() passes for any non-empty text, so the test cannot detect a wrong total such as 160.00 instead of 164.00. | await expect(page.getByTestId('order-total')).toHaveText('AED 164.00'); |
| checkout.spec.ts | 25 | weak_assertion | high | A locator object is always defined, so this assertion can never fail. | await expect(page.getByRole('alert')).toHaveText('This coupon has expired'); |
| checkout.spec.ts | 32 | weak_assertion | medium | status < 500 accepts 4xx errors as success. | expect(response.status()).toBe(200), then assert the new total in the response body. |
| checkout.spec.ts | 8 | fixed_wait | high | A 3 second sleep wastes time when the app is fast and is still not enough when it is slow, which matches the timeout seen in CI. | Remove the wait; Playwright auto-waits on actions. Wait for the state you need: await expect(page.getByLabel('Coupon')).toBeEditable(); |
| checkout.spec.ts | 11 | fixed_wait | medium | A fixed wait after Apply. | await page.waitForResponse(r => r.url().includes('/api/coupons') && r.ok()); or assert the discount line directly. |
| checkout.spec.ts | 5 | unstable_locator | high | Positional XPath breaks when the layout changes. | page.getByRole('button', { name: 'Checkout as guest' }) |
| checkout.spec.ts | 7 | unstable_locator | high | .css-1x9fz2a is a generated class name that changes on every build; this is the locator in the CI timeout. | Add data-testid="continue-to-payment" and use page.getByTestId('continue-to-payment') |
| checkout.spec.ts | 4 | hardcoded_data | medium | The environment URL is hardcoded, so the test cannot run against other environments. | Set baseURL in playwright.config.ts from process.env.BASE_URL and use page.goto('/cart'). |
| checkout.spec.ts | 17 | duplicate_code | medium | Lines 17-21 repeat the guest setup from lines 4-8. | Move it to a fixture or a CheckoutPage.startAsGuest(email) helper. |
| checkout.spec.ts | 30 | other | medium | The test depends on an existing cart having at least 2 items, so it is order-dependent. | Seed the cart through the API in beforeEach so each test owns its data. |
| LoginTest.java | 17 | hardcoded_secret | high | A real-looking admin password is committed in the source. | Read credentials from environment variables or a secrets manager, e.g. System.getenv("QA_ADMIN_PASSWORD"). |
| LoginTest.java | 16 | unstable_locator | high | An absolute XPath from /html/body breaks on any DOM change. | By.id("email") or By.cssSelector("[data-testid='email']") |
| LoginTest.java | 19 | fixed_wait | high | Thread.sleep(5000) adds 5 seconds to every run and still races the page. | new WebDriverWait(driver, Duration.ofSeconds(10)).until(ExpectedConditions.visibilityOfElementLocated(By.id("welcome"))); |
| LoginTest.java | 30 | weak_assertion | high | assertTrue(true) means the invalid-login test can never fail. | Assert the exact error message and that the URL is still /login. |
| LoginTest.java | 11 | other | medium | The driver is created in a field and never closed, so tests share one browser and leak processes. | Create the driver in @BeforeMethod and call driver.quit() in @AfterMethod (or use a base test class). |

## Refactoring Suggestions

- Introduce page objects (CartPage, CheckoutPage, LoginPage) so locators live in one place.
- Agree a data-testid convention with the frontend team for all interactive elements.
- Add an ESLint rule (playwright/no-wait-for-timeout) and a Checkstyle rule that bans Thread.sleep in test code.
- Create test users and carts through the API in fixtures instead of the UI.

## Computed Locally

- **Files Reviewed:** 2

### Static Findings by Rule

- **Hardcoded Data:** 9
- **Unstable Locator:** 10
- **Hardcoded Secret:** 2
- **Fixed Wait:** 5
- **Weak Assertion:** 5
- **Duplicate Code:** 1

### Static Findings by Severity

- **Medium:** 10
- **High:** 22

### Static Findings

| File | Line | Rule | Severity | Code |
|---|---|---|---|---|
| LoginTest.java | 15 | hardcoded_data | medium | driver.get("https://staging.shoplite.example/login"); |
| LoginTest.java | 16 | unstable_locator | high | driver.findElement(By.xpath("/html/body/div[1]/form/input[1]")).sendKeys("admin@shoplite.example"); |
| LoginTest.java | 16 | hardcoded_data | medium | driver.findElement(By.xpath("/html/body/div[1]/form/input[1]")).sendKeys("admin@shoplite.example"); |
| LoginTest.java | 17 | hardcoded_secret | high | driver.findElement(By.id("password")).sendKeys("Admin@123"); |
| LoginTest.java | 18 | unstable_locator | high | driver.findElement(By.xpath("//button[2]")).click(); |
| LoginTest.java | 19 | fixed_wait | high | Thread.sleep(5000); |
| LoginTest.java | 20 | weak_assertion | high | Assert.assertNotNull(driver.findElement(By.id("welcome"))); |
| LoginTest.java | 25 | hardcoded_data | medium | driver.get("https://staging.shoplite.example/login"); |
| LoginTest.java | 26 | unstable_locator | high | driver.findElement(By.xpath("/html/body/div[1]/form/input[1]")).sendKeys("admin@shoplite.example"); |
| LoginTest.java | 26 | hardcoded_data | medium | driver.findElement(By.xpath("/html/body/div[1]/form/input[1]")).sendKeys("admin@shoplite.example"); |
| LoginTest.java | 27 | hardcoded_secret | high | driver.findElement(By.id("password")).sendKeys("wrong"); |
| LoginTest.java | 28 | unstable_locator | high | driver.findElement(By.xpath("//button[2]")).click(); |
| LoginTest.java | 29 | fixed_wait | high | Thread.sleep(5000); |
| LoginTest.java | 30 | weak_assertion | high | Assert.assertTrue(true); |
| checkout.spec.ts | 4 | hardcoded_data | medium | await page.goto('https://staging.shoplite.example/cart'); |
| checkout.spec.ts | 5 | unstable_locator | high | await page.locator('//div[2]/div/button[1]').click(); |
| checkout.spec.ts | 6 | hardcoded_data | medium | await page.fill('#email', 'qa.guest@shoplite.example'); |
| checkout.spec.ts | 7 | unstable_locator | high | await page.locator('.css-1x9fz2a').click(); |
| checkout.spec.ts | 8 | fixed_wait | high | await page.waitForTimeout(3000); |
| checkout.spec.ts | 11 | fixed_wait | high | await page.waitForTimeout(2000); |
| checkout.spec.ts | 13 | weak_assertion | high | expect(total).toBeTruthy(); |
| checkout.spec.ts | 17 | hardcoded_data | medium | await page.goto('https://staging.shoplite.example/cart'); |
| checkout.spec.ts | 17 | duplicate_code | medium | lines 17-20 repeat lines starting at 4 |
| checkout.spec.ts | 18 | unstable_locator | high | await page.locator('//div[2]/div/button[1]').click(); |
| checkout.spec.ts | 19 | hardcoded_data | medium | await page.fill('#email', 'qa.guest@shoplite.example'); |
| checkout.spec.ts | 20 | unstable_locator | high | await page.locator('.css-1x9fz2a').click(); |
| checkout.spec.ts | 21 | fixed_wait | high | await page.waitForTimeout(3000); |
| checkout.spec.ts | 24 | unstable_locator | high | const error = page.locator('div > div > span.msg'); |
| checkout.spec.ts | 25 | weak_assertion | high | expect(error).toBeDefined(); |
| checkout.spec.ts | 29 | hardcoded_data | medium | await page.goto('https://staging.shoplite.example/cart'); |
| checkout.spec.ts | 30 | unstable_locator | high | await page.locator('li:nth-child(2) .remove').click(); |
| checkout.spec.ts | 32 | weak_assertion | high | expect(response.status()).toBeLessThan(500); |
