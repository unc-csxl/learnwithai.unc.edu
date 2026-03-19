import { expect, test } from '@playwright/test';

test.describe('logout flow', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('logging out returns user to the landing/login gate', async ({ page }) => {
    await page.goto('/');

    // Login via developer menu as Ina Instructor
    await page.getByRole('button', { name: 'Developer login' }).click();
    await page.getByRole('menuitem', { name: /Ina Instructor/ }).click();

    // Confirm we're authenticated and on the courses page
    await page.waitForURL('**/courses');
    await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible();

    // Click Logout
    await page.getByRole('button', { name: 'Logout' }).click();

    // Expect to be returned to the landing/login gate
    await expect(page.getByRole('button', { name: /Login via UNC Onyen/ })).toBeVisible();
  });
});
