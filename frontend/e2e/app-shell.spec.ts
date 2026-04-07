/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { expect, test } from '@playwright/test';

test.describe('application shell (authenticated)', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('renders the application shell after login', async ({ page }) => {
    // Authenticate via dev login
    await page.goto('/api/auth/as/222222222');
    await page.waitForURL('**/courses');

    await expect(page.getByRole('link', { name: 'Learn with AI home' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Courses' })).toBeVisible();
    await expect(page.getByText('My Courses')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible();
  });
});
