import { expect, test } from '@playwright/test';

/**
 * End-to-end test for the instructor joke generator tool. Resets the database,
 * authenticates as Ina Instructor, navigates to the tools page, and verifies
 * that the seeded joke request is visible.
 */
test.describe('joke generator tool', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('displays the tools landing page with the Joke Generator card', async ({ page }) => {
    await page.goto('/api/auth/as/222222222');
    await page.waitForURL('**/courses');

    await page.getByText('COMP423').click();
    await page.waitForURL('**/courses/*/dashboard');

    await page.getByRole('link', { name: /Instructor Tools/i }).click();
    await page.waitForURL('**/courses/*/tools');

    await expect(page.getByText('Joke Generator')).toBeVisible();
    await expect(page.getByText('Generate course-related jokes using AI')).toBeVisible();
  });

  test('navigates to the joke generator and shows seeded joke request', async ({ page }) => {
    await page.goto('/api/auth/as/222222222');
    await page.waitForURL('**/courses');

    await page.getByText('COMP423').click();
    await page.waitForURL('**/courses/*/dashboard');

    await page.getByRole('link', { name: /Instructor Tools/i }).click();
    await page.waitForURL('**/courses/*/tools');

    await page.getByRole('link', { name: /Open Joke Generator tool/i }).click();
    await page.waitForURL('**/courses/*/tools/joke-generator');

    // The seeded completed joke request should be visible
    await expect(page.getByText('Tell me 3 jokes about software engineering')).toBeVisible();
    await expect(page.getByText('Why do programmers prefer dark mode?')).toBeVisible();
    await expect(page.getByText('Completed')).toBeVisible();
  });

  test('shows the prompt form', async ({ page }) => {
    await page.goto('/api/auth/as/222222222');
    await page.waitForURL('**/courses');

    await page.getByText('COMP423').click();
    await page.waitForURL('**/courses/*/dashboard');

    await page.getByRole('link', { name: /Instructor Tools/i }).click();
    await page.waitForURL('**/courses/*/tools');

    await page.getByRole('link', { name: /Open Joke Generator tool/i }).click();
    await page.waitForURL('**/courses/*/tools/joke-generator');

    // The form should be present with a prompt input and submit button
    await expect(page.getByRole('textbox', { name: /joke prompt/i })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Generate' })).toBeVisible();
  });
});
