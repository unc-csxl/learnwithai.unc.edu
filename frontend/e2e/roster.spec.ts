import { expect, test } from '@playwright/test';

/**
 * End-to-end tests for the roster page covering pagination,
 * search, and visual presentation of member data.
 */
test.describe('roster features', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  /** Helper: login as instructor and navigate to roster. */
  async function goToRoster(page: import('@playwright/test').Page) {
    await page.goto('/api/auth/as/222222222');
    await page.waitForURL('**/courses');
    await page.getByText('COMP423').click();
    await page.waitForURL('**/courses/*/dashboard');
    await page.getByRole('link', { name: /Roster/i }).click();
    await page.waitForURL('**/courses/*/roster');
  }

  test('displays roster table with name, PID, and email columns', async ({ page }) => {
    await goToRoster(page);

    // Verify column headers
    await expect(page.getByRole('columnheader', { name: 'Given Name' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Family Name' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'PID' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Email' })).toBeVisible();

    // Verify data rows (3 members seeded)
    const rows = page.locator('tr[mat-row]');
    await expect(rows).toHaveCount(3);
  });

  test('shows search input and paginator', async ({ page }) => {
    await goToRoster(page);

    await expect(page.getByLabel('Search roster by name, PID, or email')).toBeVisible();
    await expect(page.locator('mat-paginator')).toBeVisible();
  });

  test('filters roster by name via search', async ({ page }) => {
    await goToRoster(page);

    const searchInput = page.getByLabel('Search roster by name, PID, or email');
    await searchInput.fill('Sally');

    // Wait for debounce and API response
    await page.waitForTimeout(500);

    const rows = page.locator('tr[mat-row]');
    await expect(rows).toHaveCount(1);
    await expect(page.getByText('Sally')).toBeVisible();
    await expect(page.getByText('111111111')).toBeVisible();
  });

  test('filters roster by PID via search', async ({ page }) => {
    await goToRoster(page);

    const searchInput = page.getByLabel('Search roster by name, PID, or email');
    await searchInput.fill('333');

    await page.waitForTimeout(500);

    const rows = page.locator('tr[mat-row]');
    await expect(rows).toHaveCount(1);
    await expect(page.getByText('Tatum')).toBeVisible();
  });

  test('filters roster by email via search', async ({ page }) => {
    await goToRoster(page);

    const searchInput = page.getByLabel('Search roster by name, PID, or email');
    await searchInput.fill('instructor@');

    await page.waitForTimeout(500);

    const rows = page.locator('tr[mat-row]');
    await expect(rows).toHaveCount(1);
    await expect(page.getByText('Ina')).toBeVisible();
  });

  test('shows no results message for unmatched search', async ({ page }) => {
    await goToRoster(page);

    const searchInput = page.getByLabel('Search roster by name, PID, or email');
    await searchInput.fill('zzz_no_match');

    await page.waitForTimeout(500);

    await expect(page.getByText('No members found')).toBeVisible();
  });

  test('ignores search shorter than 3 characters', async ({ page }) => {
    await goToRoster(page);

    const searchInput = page.getByLabel('Search roster by name, PID, or email');
    await searchInput.fill('ab');

    await page.waitForTimeout(500);

    // All 3 members should still be visible
    const rows = page.locator('tr[mat-row]');
    await expect(rows).toHaveCount(3);
  });
});
