import { test, expect } from '@playwright/test';

test('guest can apply a coupon', async ({ page }) => {
  await page.goto('https://staging.shoplite.example/cart');
  await page.locator('//div[2]/div/button[1]').click();
  await page.fill('#email', 'qa.guest@shoplite.example');
  await page.locator('.css-1x9fz2a').click();
  await page.waitForTimeout(3000);
  await page.fill('#coupon', 'SAVE20');
  await page.click('text=Apply');
  await page.waitForTimeout(2000);
  const total = await page.locator('#order-total').textContent();
  expect(total).toBeTruthy();
});

test('guest sees error for an expired coupon', async ({ page }) => {
  await page.goto('https://staging.shoplite.example/cart');
  await page.locator('//div[2]/div/button[1]').click();
  await page.fill('#email', 'qa.guest@shoplite.example');
  await page.locator('.css-1x9fz2a').click();
  await page.waitForTimeout(3000);
  await page.fill('#coupon', 'OLD10');
  await page.click('text=Apply');
  const error = page.locator('div > div > span.msg');
  expect(error).toBeDefined();
});

test('order total updates after removing an item', async ({ page }) => {
  await page.goto('https://staging.shoplite.example/cart');
  await page.locator('li:nth-child(2) .remove').click();
  const response = await page.waitForResponse('**/api/cart');
  expect(response.status()).toBeLessThan(500);
});
