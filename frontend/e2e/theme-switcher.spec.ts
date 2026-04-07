/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { expect, test } from '@playwright/test';

test.describe('theme switcher', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('cycles through system, light, and dark modes', async ({ page }) => {
    // Authenticate via dev login
    await page.goto('/api/auth/as/222222222');
    await page.waitForURL('**/courses');

    // Default: system mode
    const themeBtn = page.getByRole('button', { name: /Theme:/ });
    await expect(themeBtn).toHaveAccessibleName('Theme: System');

    // Click → light
    await themeBtn.click();
    await expect(themeBtn).toHaveAccessibleName('Theme: Light');
    await expect(page.locator('html')).toHaveClass(/light/);
    const lightScheme = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('color-scheme').trim(),
    );
    expect(lightScheme).toBe('light');

    // Click → dark
    await themeBtn.click();
    await expect(themeBtn).toHaveAccessibleName('Theme: Dark');
    await expect(page.locator('html')).toHaveClass(/dark/);
    const darkScheme = await page.evaluate(() =>
      getComputedStyle(document.documentElement).getPropertyValue('color-scheme').trim(),
    );
    expect(darkScheme).toBe('dark');

    // Click → back to system
    await themeBtn.click();
    await expect(themeBtn).toHaveAccessibleName('Theme: System');
    await expect(page.locator('html')).not.toHaveClass(/light/);
    await expect(page.locator('html')).not.toHaveClass(/dark/);
  });

  test('persists theme preference across navigation', async ({ page }) => {
    await page.goto('/api/auth/as/222222222');
    await page.waitForURL('**/courses');

    // Set dark mode
    const themeBtn = page.getByRole('button', { name: /Theme:/ });
    await themeBtn.click(); // system → light
    await themeBtn.click(); // light → dark
    await expect(themeBtn).toHaveAccessibleName('Theme: Dark');

    // Reload the page
    await page.reload();
    await page.waitForURL('**/courses');

    // Should still be dark
    await expect(page.getByRole('button', { name: 'Theme: Dark' })).toBeVisible();
    await expect(page.locator('html')).toHaveClass(/dark/);
  });
});
