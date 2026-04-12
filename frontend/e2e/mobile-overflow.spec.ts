import { expect, test, type Page } from '@playwright/test';

const MOBILE_VIEWPORT = { width: 390, height: 844 };
const SUPERADMIN_PID = 444444444;

async function loginAsSuperadmin(page: Page): Promise<void> {
  await page.goto(`/api/auth/as/${SUPERADMIN_PID}`);
  await page.waitForURL('**/courses');
  await expect(page.getByRole('button', { name: 'Toggle navigation' })).toBeVisible();
}

async function expectDocumentFitsViewport(page: Page): Promise<void> {
  const overflow = await page.evaluate(() => {
    const doc = document.documentElement;
    const body = document.body;
    const scrollWidth = Math.max(doc.scrollWidth, body.scrollWidth);
    const scrollHeight = Math.max(doc.scrollHeight, body.scrollHeight);
    return {
      xOverflow: scrollWidth - doc.clientWidth,
      yOverflow: scrollHeight - doc.clientHeight,
    };
  });

  expect(overflow.xOverflow).toBe(0);
  expect(overflow.yOverflow).toBe(0);
}

async function expectToolbarPinned(page: Page): Promise<void> {
  const toolbar = page.locator('.app-toolbar');
  const content = page.locator('main.content');
  const before = await toolbar.boundingBox();

  await content.evaluate((element) => {
    element.scrollTop = 240;
  });
  await page.waitForTimeout(100);

  const after = await toolbar.boundingBox();
  expect(before).not.toBeNull();
  expect(after).not.toBeNull();
  expect(Math.abs((after?.y ?? 0) - (before?.y ?? 0))).toBeLessThan(1);
}

async function expectHorizontalOverflowIsContained(
  page: Page,
  containerSelector: string,
): Promise<void> {
  const container = page.locator(containerSelector).first();
  await expect(container).toBeVisible();

  const overflow = await container.evaluate((element) => ({
    clientWidth: element.clientWidth,
    scrollWidth: element.scrollWidth,
  }));

  expect(overflow.scrollWidth).toBeGreaterThanOrEqual(overflow.clientWidth);

  if (overflow.scrollWidth > overflow.clientWidth) {
    const toolbar = page.locator('.app-toolbar');
    const before = await toolbar.boundingBox();

    await container.evaluate((element) => {
      element.scrollLeft = Math.min(240, element.scrollWidth - element.clientWidth);
    });
    await page.waitForTimeout(100);

    const after = await toolbar.boundingBox();
    expect(Math.abs((after?.x ?? 0) - (before?.x ?? 0))).toBeLessThan(1);
  }

  await expectDocumentFitsViewport(page);
}

test.describe('mobile viewport overflow', () => {
  test.use({ viewport: MOBILE_VIEWPORT, isMobile: true, hasTouch: true });

  test.beforeEach(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('keeps the landing page and app shell inside the viewport', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('button', { name: 'Developer login' })).toBeVisible();
    await expectDocumentFitsViewport(page);
    await page.screenshot({ path: 'tmp/verified-landing-mobile.png', fullPage: true });

    await loginAsSuperadmin(page);
    await expect(page.getByRole('link', { name: 'Create Course' })).toBeVisible();
    await expectDocumentFitsViewport(page);
    await expectToolbarPinned(page);
    await page.screenshot({ path: 'tmp/verified-courses-mobile.png', fullPage: true });
  });

  test('contains operations-page overflow inside content regions', async ({ page }) => {
    await loginAsSuperadmin(page);

    await page.goto('/operations/metrics');
    await expect(page.getByRole('region', { name: 'Usage Metrics' })).toBeVisible();
    await expectDocumentFitsViewport(page);
    await expectToolbarPinned(page);
    await page.screenshot({ path: 'tmp/verified-operations-metrics-mobile.png', fullPage: true });

    await page.goto('/operations/impersonate');
    await expect(page.locator('input[autocomplete="off"]')).toBeVisible();
    await page.locator('input[autocomplete="off"]').fill('Sally');
    await expect(page.getByRole('cell', { name: 'Sally Student' })).toBeVisible();
    await expectHorizontalOverflowIsContained(page, '.table-scroll');
    await expectToolbarPinned(page);
    await page.screenshot({
      path: 'tmp/verified-operations-impersonate-mobile.png',
      fullPage: true,
    });

    await page.goto('/operations/jobs');
    await expect(page.getByRole('region', { name: 'Job Queue Control' })).toBeVisible();
    await expectHorizontalOverflowIsContained(page, '.table-scroll');
    await expectToolbarPinned(page);
    await page.screenshot({ path: 'tmp/verified-operations-jobs-mobile.png', fullPage: true });

    await page.goto('/operations/operators');
    await expect(page.getByRole('button', { name: 'Add Operator' })).toBeVisible();
    await expectHorizontalOverflowIsContained(page, '.table-scroll');
    await expectToolbarPinned(page);
    await page.screenshot({ path: 'tmp/verified-operations-operators-mobile.png', fullPage: true });
  });
});
