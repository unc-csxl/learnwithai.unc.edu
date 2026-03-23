import { expect, test } from '@playwright/test';

/**
 * End-to-end test that resets the database, authenticates via the dev login
 * shortcut, then navigates through courses and the roster to verify all
 * seeded data is visible.
 */
test.describe('authenticated course and roster flow', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('stays authenticated after a full page refresh', async ({ page }) => {
    await page.goto('/api/auth/as/222222222');

    await page.waitForURL('**/courses');
    await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible();

    await page.reload();

    await page.waitForURL('**/courses');
    await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible();
    await expect(page.getByText('COMP423')).toBeVisible();
  });

  test('login, view courses, and verify roster', async ({ page }) => {
    // Dev login as Ina Instructor (pid 222222222)
    await page.goto('/api/auth/as/222222222');

    // After redirect chain, should land on the courses page (default route)
    await page.waitForURL('**/courses');

    // Should see Logout button (authenticated) rather than Login
    await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible();

    // Should see the COMP423 course card
    await expect(page.getByText('COMP423')).toBeVisible();

    // Navigate to the course detail page
    await page.getByText('COMP423').click();
    await page.waitForURL('**/courses/*/dashboard');

    await expect(page.getByRole('link', { name: /Dashboard/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /Student Activities/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /Instructor Tools/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /Roster/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /Course Settings/i })).toBeVisible();

    await page.getByRole('link', { name: /Roster/i }).click();
    await page.waitForURL('**/courses/*/roster');

    // The roster screen should show all three members
    await expect(page.getByText('222222222')).toBeVisible();
    await expect(page.getByText('111111111')).toBeVisible();
    await expect(page.getByText('333333333')).toBeVisible();
  });
});
