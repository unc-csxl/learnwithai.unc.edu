/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { expect, test } from '@playwright/test';

/**
 * End-to-end tests for the roster page covering pagination,
 * search, visual presentation, and CSV upload.
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
    await expect(page.getByRole('cell', { name: 'Ina' })).toBeVisible();
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

test.describe('roster CSV upload', () => {
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

  test('shows upload CSV button on roster page', async ({ page }) => {
    await goToRoster(page);
    await expect(page.getByRole('button', { name: /Upload CSV/i })).toBeVisible();
  });

  test('uploads a Canvas CSV and shows results dialog', async ({ page }) => {
    await goToRoster(page);

    // Verify initial roster count (3 seeded members)
    await expect(page.locator('tr[mat-row]')).toHaveCount(3);

    // Build a minimal Canvas gradebook CSV with a new student
    const csv = [
      'Student,ID,SIS User ID,SIS Login ID,Section',
      ',,,,,Manual Posting',
      '    Points Possible,,,,,10.00',
      '"New, Student",999,444444444,newstudent,COMP423.SP26',
    ].join('\n');

    // Upload file via hidden input
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'roster.csv',
      mimeType: 'text/csv',
      buffer: Buffer.from(csv, 'utf-8'),
    });

    // Wait for the results dialog (worker must be running)
    await expect(page.getByText('Upload Results')).toBeVisible({ timeout: 15000 });

    // Verify the created count shows in the dialog
    await expect(page.getByText('Created')).toBeVisible();

    // Close the dialog
    await page.getByRole('button', { name: 'Close' }).click();

    // Roster should now have 4 members
    await expect(page.locator('tr[mat-row]')).toHaveCount(4);
  });
});
