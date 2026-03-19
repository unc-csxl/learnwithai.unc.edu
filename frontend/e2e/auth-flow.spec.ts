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
    await page.waitForURL('**/courses/*/roster');

    // The roster tab should be active and show all three members
    await expect(page.getByText('222222222')).toBeVisible();
    await expect(page.getByText('111111111')).toBeVisible();
    await expect(page.getByText('333333333')).toBeVisible();
  });
});
