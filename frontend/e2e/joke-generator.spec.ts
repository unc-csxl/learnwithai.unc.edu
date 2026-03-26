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

  test('submitting a request shows a pending spinner (regression)', async ({ page }) => {
    await page.goto('/api/auth/as/222222222');
    await page.waitForURL('**/courses');

    await page.getByText('COMP423').click();
    await page.waitForURL('**/courses/*/dashboard');

    await page.getByRole('link', { name: /Instructor Tools/i }).click();
    await page.waitForURL('**/courses/*/tools');

    await page.getByRole('link', { name: /Open Joke Generator tool/i }).click();
    await page.waitForURL('**/courses/*/tools/joke-generator');

    // Submit a new joke request
    await page.getByRole('textbox', { name: /joke prompt/i }).fill('Tell me a joke about testing');
    await page.getByRole('button', { name: 'Generate' }).click();

    // The request should appear with a pending status (may transition to
    // processing/completed/failed if a worker picks it up quickly).
    await expect(page.getByText('Tell me a joke about testing')).toBeVisible({ timeout: 5000 });

    // Verify the snackbar confirmation appeared, proving the API accepted it.
    await expect(page.getByText('Joke request submitted!')).toBeVisible({ timeout: 5000 });

    // The request's status should be expressed through the nested job field.
    // Previously, a regression left request.status undefined (spinner never
    // appeared). Now the status must resolve to an actual job status word.
    const statusText = page.locator('.request-card').first().locator('mat-card-subtitle');
    await expect(statusText).toContainText(/Pending|Processing|Completed|Failed/, {
      timeout: 10000,
    });
  });
});
