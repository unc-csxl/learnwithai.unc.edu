/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { expect, test, devices } from '@playwright/test';
import path from 'node:path';

const instructorPid = '222222222';
const fileSuffix = process.env.VISUAL_SUFFIX ?? 'baseline';

function screenshotPath(name: string): string {
  return path.join(process.cwd(), `tmp-${name}-${fileSuffix}.png`);
}

async function loginAndOpenCourse(page: import('@playwright/test').Page) {
  await page.goto(`/api/auth/as/${instructorPid}`);
  await page.waitForURL('**/courses');
  await page.getByText('COMP423').click();
  await page.waitForURL('**/courses/*/dashboard');
}

test.describe('visual style checks', () => {
  test.beforeEach(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('captures desktop sidenav states', async ({ page }) => {
    await loginAndOpenCourse(page);
    await page.getByRole('link', { name: /^Roster$/ }).click();
    await page.waitForURL('**/courses/*/roster');
    await page.getByRole('link', { name: /^Course Settings$/ }).hover();

    await page.locator('mat-sidenav').screenshot({
      path: screenshotPath('sidenav'),
    });

    await page.getByRole('link', { name: /COMP423/i }).screenshot({
      path: screenshotPath('course-nav'),
    });

    await expect(page.getByRole('link', { name: /^Roster$/ })).toBeVisible();
  });

  test('captures mobile roster controls', async ({ browser }) => {
    const context = await browser.newContext({
      ...devices['iPhone 13'],
      baseURL: test.info().project.use.baseURL,
    });
    const page = await context.newPage();

    await loginAndOpenCourse(page);
    await page.goto(page.url().replace('/dashboard', '/roster'));
    await page.waitForURL('**/courses/*/roster');

    const controls = page.locator('mat-form-field').locator('xpath=ancestor::div[1]').first();
    await expect(controls).toBeVisible();
    await controls.screenshot({
      path: screenshotPath('roster-controls'),
    });

    await context.close();
  });
});
