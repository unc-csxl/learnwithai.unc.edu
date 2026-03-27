import { expect, test } from '@playwright/test';

const SEEDED_PROMPT = 'Tell me 3 jokes about software engineering';
const SEEDED_JOKE = 'Why do programmers prefer dark mode? Because light attracts bugs!';
const SEEDED_COMPLETED_AT = '2025-01-15T10:00:12Z';

async function openJokeGenerator(page: Parameters<typeof test>[0]['page']): Promise<string> {
  await page.goto('/api/auth/as/222222222');
  await page.waitForURL('**/courses');

  await page.getByText('COMP423').click();
  await page.waitForURL('**/courses/*/dashboard');

  await page.getByRole('link', { name: /Instructor Tools/i }).click();
  await page.waitForURL('**/courses/*/tools');

  await page.getByRole('link', { name: /Open Joke Generator tool/i }).click();
  await page.waitForURL('**/courses/*/tools/joke-generator');

  const match = page.url().match(/\/courses\/(\d+)\//);
  if (!match) throw new Error(`Could not determine course ID from URL: ${page.url()}`);
  return match[1];
}

async function formatCompletedAtInBrowser(
  page: Parameters<typeof test>[0]['page'],
  completedAt: string,
): Promise<string> {
  return page.evaluate((value) => {
    const completedDate = new Date(value);
    const month = new Intl.DateTimeFormat('en-US', { month: 'long' }).format(completedDate);
    const day = completedDate.getDate();
    const year = completedDate.getFullYear();
    const hours = completedDate.getHours();
    const minutes = completedDate.getMinutes();
    const displayHour = hours % 12 || 12;
    const meridiem = hours >= 12 ? 'pm' : 'am';
    const time =
      minutes === 0
        ? `${displayHour}${meridiem}`
        : `${displayHour}:${minutes.toString().padStart(2, '0')}${meridiem}`;

    const ordinalSuffix = (dayOfMonth: number): string => {
      if (dayOfMonth >= 11 && dayOfMonth <= 13) return 'th';
      switch (dayOfMonth % 10) {
        case 1:
          return 'st';
        case 2:
          return 'nd';
        case 3:
          return 'rd';
        default:
          return 'th';
      }
    };

    return `${month} ${day}${ordinalSuffix(day)}, ${year} at ${time}`;
  }, completedAt);
}

async function expectSeededCompletedRequest(
  page: Parameters<typeof test>[0]['page'],
): Promise<void> {
  const expectedCompletedAt = await formatCompletedAtInBrowser(page, SEEDED_COMPLETED_AT);
  const seededCard = page.locator('.request-card').filter({ hasText: SEEDED_PROMPT });

  await expect(seededCard.getByText(SEEDED_PROMPT)).toBeVisible();
  await expect(seededCard.getByText(SEEDED_JOKE)).toBeVisible();
  await expect(seededCard.locator('mat-card-subtitle')).toContainText(expectedCompletedAt);
  await expect(seededCard.locator('mat-card-subtitle')).not.toContainText('Completed');
}

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
    await openJokeGenerator(page);
    await expectSeededCompletedRequest(page);
  });

  test('shows the prompt form', async ({ page }) => {
    await openJokeGenerator(page);
    await expectSeededCompletedRequest(page);

    // The form should be present with a prompt input and submit button
    await expect(page.getByRole('textbox', { name: /joke prompt/i })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Generate' })).toBeVisible();
  });

  test('submitting a request shows a pending spinner (regression)', async ({ page }) => {
    await openJokeGenerator(page);
    await expectSeededCompletedRequest(page);

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
