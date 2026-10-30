<!-- Generated from qa_agents/knowledge/code-review.md by scripts/sync_skill_references.py. Do not edit here. -->

## Test smells (van Deursen et al. 2001; tsDetect catalogue)
- Assertion Roulette: several assertions without messages, so a failure doesn't say which check broke.
- Eager Test: one test exercises many behaviours; split it so each test has one reason to fail.
- Mystery Guest: depends on external files, databases or shared accounts the test doesn't create.
- General Fixture: setup creates more than each test needs; Resource Optimism: assumes a resource exists.
- Conditional Test Logic: if/for/while/switch inside a test hides paths that never run.
- Exception Handling: try/catch used to pass or fail a test, or exceptions swallowed silently.
- Empty Test / Unknown Test: no statements, or no assertion at all (a test that cannot fail).
- Redundant Assertion: always true, e.g. assertTrue(true), assertEquals(x, x).
- Sensitive Equality: comparing toString() output. Magic Number Test: unexplained literals in assertions.
- Sleepy Test: Thread.sleep / time.sleep. Ignored Test: @Disabled/@Ignore/.skip with no ticket or reason.
- Redundant Print: console.log / System.out left in tests. Test Code Duplication: copy-pasted steps.
- Test Run War / order dependence: tests share mutable state (users, carts, DB rows) and break in parallel.

## Waiting (official guidance)
- Playwright: actions auto-wait; use web-first assertions (`await expect(locator).toBeVisible()`).
  `expect(await locator.isVisible()).toBe(true)` checks once and does not retry. `waitUntil: 'networkidle'`
  is discouraged in the docs; avoid `page.waitForTimeout` in tests.
- Cypress: `cy.wait(<number>)` is an anti-pattern; wait on route aliases (`cy.intercept().as('x')` then
  `cy.wait('@x')`) or on assertions, which retry.
- Selenium: do not mix implicit and explicit waits (unpredictable wait times); use WebDriverWait /
  FluentWait with ExpectedConditions.

## Locators (official guidance)
- Playwright priority: getByRole, getByText, getByLabel, getByPlaceholder, getByAltText, getByTitle,
  getByTestId. CSS/XPath are not recommended because the DOM changes; prefer user-facing attributes.
- Cypress: use dedicated `data-cy` / `data-test` / `data-testid` attributes; avoid tag, class and id
  selectors; use `cy.contains` when the text itself matters.
- Selenium: a unique, stable ID first, then a well-written CSS selector; avoid absolute or index-based XPath.
- Never use generated class names (css-1x9fz2a, jss123, sc-abcde) or positional selectors (nth-child, [2]).

## Isolation and structure
- Each test must run alone and in any order: create its own data (API/fixtures), clean up in setup of the
  next run (Cypress advises before/beforeEach), never rely on a previous test.
- Use Page Objects / screenplay / helpers so locators live in one place; keep assertions in tests.
- Log in programmatically (API, cy.session, storageState) instead of through the UI in every test.
- Configure baseURL/baseUrl and environments outside the test code.
- `.only` / `fit` committed to main silently disables the rest of the suite: always high severity.
- `{ force: true }` / JavaScript clicks bypass actionability checks and hide real UI bugs.

## Secrets and test data (OWASP Secrets Management Cheat Sheet)
- No credentials, API keys, tokens, private keys or connection strings in test code; load them from
  environment variables or a secrets manager, and mask them in logs and CI output.
- Use generated, synthetic data (e.g. Faker) instead of real emails, phone numbers or card numbers;
  card-like numbers that pass the Luhn check are a compliance risk even in tests.
- A leaked secret must be revoked first, then rotated: say so when you find one.

## API test code (REST Assured, Playwright request, requests/pytest)
- Assert exact status codes (not `< 500`), the response schema and the key values, not just presence.
- Negative tests must assert the error code/message; a 5xx on bad input is a defect.

Sources: van Deursen, Moonen, van den Bergh, Kok, "Refactoring Test Code" (XP2001) https://ir.cwi.nl/pub/4324 ·
tsDetect test smells https://testsmells.org/pages/testsmells.html · Playwright best practices
https://playwright.dev/docs/best-practices and locators https://playwright.dev/docs/locators · Cypress best
practices https://docs.cypress.io/app/core-concepts/best-practices · Selenium waits
https://www.selenium.dev/documentation/webdriver/waits/ and locators
https://www.selenium.dev/documentation/test_practices/encouraged/locators/ · OWASP Secrets Management Cheat
Sheet https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
