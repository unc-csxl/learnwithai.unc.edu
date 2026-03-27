import { expect, test } from '@playwright/test';

test.describe('landing page', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('shows landing page for unauthenticated users', async ({ page }) => {
    await page.goto('/');

    // Branding
    await expect(page.getByText('LEARN')).toBeVisible();
    await expect(page.getByText('with')).toBeVisible();
    await expect(page.getByText('AI')).toBeVisible();

    // Interlocking NC logo
    await expect(page.getByRole('img', { name: 'UNC Chapel Hill' })).toBeVisible();

    // Login button
    await expect(page.getByRole('button', { name: /Login via UNC Onyen/ })).toBeVisible();

    // Dev login button (development mode)
    await expect(page.getByRole('button', { name: 'Developer login' })).toBeVisible();
  });

  test('redirects unauthenticated users from protected routes to landing', async ({ page }) => {
    await page.goto('/courses');

    // Should be redirected to landing
    await expect(page.getByRole('button', { name: /Login via UNC Onyen/ })).toBeVisible();
  });

  test('login as Ina Instructor via dev login menu', async ({ page }) => {
    await page.goto('/');

    // Open the dev login menu
    await page.getByRole('button', { name: 'Developer login' }).click();

    // Select Ina Instructor from the menu
    await page.getByRole('menuitem', { name: /Ina Instructor/ }).click();

    // Should land on the courses page after authentication
    await page.waitForURL('**/courses');

    // Verify authenticated state
    await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible();

    // Verify course data is visible
    await expect(page.getByText('COMP423')).toBeVisible();
  });
});
