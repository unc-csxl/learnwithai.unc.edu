/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { expect, test } from '@playwright/test';

test.describe('profile editor', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('navigates to profile page and edits name', async ({ page }) => {
    // Login as Ina Instructor
    await page.goto('/api/auth/as/222222222');
    await page.waitForURL('**/courses');

    // User profile link should be visible in sidenav
    const profileLink = page.getByRole('link', { name: 'Edit profile' });
    await expect(profileLink).toBeVisible();
    await expect(profileLink).toContainText('Ina Instructor');

    // Navigate to the profile page
    await profileLink.click();
    await page.waitForURL('**/profile');

    // Non-editable account info should be shown as readable text (not form inputs)
    await expect(page.getByText('222222222')).toBeVisible();
    expect(await page.locator('input[readonly]').count()).toBe(0);

    // Editable fields should be pre-populated
    const givenNameInput = page.locator('input[formControlName="given_name"]');
    const familyNameInput = page.locator('input[formControlName="family_name"]');
    await expect(givenNameInput).toHaveValue('Ina');
    await expect(familyNameInput).toHaveValue('Instructor');

    // Change the given name
    await givenNameInput.clear();
    await givenNameInput.fill('Irene');

    // Submit the form
    await page.getByRole('button', { name: 'Save' }).click();

    // Should navigate to courses list
    await page.waitForURL('**/courses');

    // Should show a success snackbar notification
    await expect(page.getByText('Profile updated.')).toBeVisible({ timeout: 5000 });

    // The sidenav should reflect the updated name
    await expect(page.getByRole('link', { name: 'Edit profile' })).toContainText(
      'Irene Instructor',
    );
  });
});
