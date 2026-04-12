/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { expect, test, type Page } from '@playwright/test';

async function expectLandingCardCentered(page: Page): Promise<void> {
  const viewport = page.viewportSize();
  expect(viewport).not.toBeNull();

  const overflow = await page.evaluate(() => {
    const doc = document.documentElement;
    const body = document.body;
    return {
      xOverflow: Math.max(doc.scrollWidth, body.scrollWidth) - doc.clientWidth,
      yOverflow: Math.max(doc.scrollHeight, body.scrollHeight) - doc.clientHeight,
      scrollX: window.scrollX,
      scrollY: window.scrollY,
    };
  });

  expect(overflow.xOverflow).toBe(0);
  expect(overflow.yOverflow).toBe(0);
  expect(overflow.scrollX).toBe(0);
  expect(overflow.scrollY).toBe(0);

  const card = page.locator('mat-pane').first();
  const box = await card.boundingBox();
  expect(box).not.toBeNull();

  const centerX = (box?.x ?? 0) + (box?.width ?? 0) / 2;
  const centerY = (box?.y ?? 0) + (box?.height ?? 0) / 2;

  expect(Math.abs(centerX - viewport!.width / 2)).toBeLessThanOrEqual(24);
  expect(Math.abs(centerY - viewport!.height / 2)).toBeLessThanOrEqual(24);
}

test.describe('landing page', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('shows landing page for unauthenticated users', async ({ page }) => {
    await page.goto('/');

    // Branding
    await expect(page.getByText('LEARN')).toBeVisible();
    await expect(page.getByText('with')).toBeVisible();
    await expect(page.getByText('AI')).toBeVisible();

    // Interlocking NC logo
    await expect(page.getByRole('img', { name: 'UNC Chapel Hill' })).toBeVisible();

    // Login button
    await expect(page.getByRole('button', { name: /Login via UNC Onyen/ })).toBeVisible();

    // Dev login button (development mode)
    await expect(page.getByRole('button', { name: 'Developer login' })).toBeVisible();
  });

  test('keeps the login card centered without page scroll on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto('/');

    await expect(page.getByRole('button', { name: 'Developer login' })).toBeVisible();
    await expectLandingCardCentered(page);
  });

  test('keeps the login card centered without page scroll on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');

    await expect(page.getByRole('button', { name: 'Developer login' })).toBeVisible();
    await expectLandingCardCentered(page);
  });

  test('redirects unauthenticated users from protected routes to landing', async ({ page }) => {
    await page.goto('/courses');

    // Should be redirected to landing
    await expect(page.getByRole('button', { name: /Login via UNC Onyen/ })).toBeVisible();
  });

  test('login as Ina Instructor via dev login menu', async ({ page }) => {
    await page.goto('/');

    // Open the dev login menu
    await page.getByRole('button', { name: 'Developer login' }).click();

    // Select Ina Instructor from the menu
    await page.getByRole('menuitem', { name: /Ina Instructor/ }).click();

    // Should land on the courses page after authentication
    await page.waitForURL('**/courses');

    // Verify authenticated state
    await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible();

    // Verify course data is visible
    await expect(page.getByText('COMP423')).toBeVisible();
  });
});
