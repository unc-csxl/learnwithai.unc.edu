/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { expect, test, type Locator, type Page } from '@playwright/test';

const PID = {
  sally: 111111111,
  ina: 222222222,
  tatum: 333333333,
  amy: 444444444,
} as const;

type OperatorRole = 'superadmin' | 'admin' | 'helpdesk';

async function loginAs(page: Page, pid: number): Promise<void> {
  await page.goto(`/api/auth/as/${pid}`);
  await page.waitForURL('**/courses');
  await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible();
}

async function logout(page: Page): Promise<void> {
  await page.getByRole('button', { name: 'Logout' }).click();
  await expect(page.getByRole('button', { name: 'Developer login' })).toBeVisible();
}

async function openOperations(page: Page): Promise<void> {
  await page.getByRole('link', { name: 'Operations' }).click();
  await page.waitForURL('**/operations/metrics');
  await expect(page.getByText('Active Users')).toBeVisible();
}

async function openJobControl(page: Page): Promise<void> {
  await page.getByRole('link', { name: 'Job Control' }).click();
  await page.waitForURL('**/operations/jobs');
  await expect(page.getByRole('region', { name: 'Job Control' })).toBeVisible();
}

async function goToOperators(page: Page): Promise<void> {
  const link = page.getByRole('link', { name: 'Operators' });
  await expect(link).toBeVisible();
  await link.click();
  await page.waitForURL('**/operations/operators');
  await expect(page.getByRole('button', { name: 'Add Operator' })).toBeVisible();
}

async function addOperator(page: Page, pid: number, role: OperatorRole): Promise<void> {
  await page.getByRole('button', { name: 'Add Operator' }).click();
  const dialog = page.locator('mat-dialog-container').last();
  await expect(dialog.getByRole('heading', { name: 'Add Operator' })).toBeVisible();

  const pidInput = dialog.locator('input[formControlName="pid"]');
  await pidInput.fill(String(pid));
  await expect(pidInput).toHaveValue(String(pid));

  await dialog.locator('mat-select[formControlName="role"]').click();
  await page.getByRole('option', { name: role, exact: true }).click();

  const grantButton = dialog.getByRole('button', { name: 'Grant Access' });
  await expect(grantButton).toBeEnabled();
  await grantButton.click();

  await expect(page.getByText('Operator access granted')).toBeVisible();
}

async function operatorRow(page: Page, userName: string): Promise<Locator> {
  const row = page.locator('tr', { hasText: userName }).first();
  await expect(row).toBeVisible();
  return row;
}

async function changeOperatorRole(page: Page, userName: string, role: OperatorRole): Promise<void> {
  const row = await operatorRow(page, userName);
  await row.locator('mat-select').click();
  await page.getByRole('option', { name: role, exact: true }).click();
  await expect(page.getByText('Role updated')).toBeVisible();
}

async function expectOperationsContextLinks(page: Page, links: string[]): Promise<void> {
  for (const link of links) {
    await expect(page.getByRole('link', { name: link })).toBeVisible();
  }
}

async function expectOperationsContextLinksAbsent(page: Page, links: string[]): Promise<void> {
  for (const link of links) {
    await expect(page.getByRole('link', { name: link })).toHaveCount(0);
  }
}

async function grantAdminAndHelpdesk(page: Page): Promise<void> {
  await loginAs(page, PID.amy);
  await openOperations(page);
  await goToOperators(page);
  await addOperator(page, PID.ina, 'admin');
  await addOperator(page, PID.tatum, 'helpdesk');
  await expect((await operatorRow(page, 'Ina Instructor')).getByText('222222222')).toBeVisible();
  await expect((await operatorRow(page, 'Tatum TA')).getByText('333333333')).toBeVisible();
  await logout(page);
}

test.describe('operations e2e flows', () => {
  test.beforeEach(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('shows the Operations nav and role-specific pages for superadmin, admin, and helpdesk', async ({
    page,
  }) => {
    await grantAdminAndHelpdesk(page);

    await loginAs(page, PID.amy);
    await expect(page.getByRole('link', { name: 'Operations' })).toBeVisible();
    await openOperations(page);
    await expectOperationsContextLinks(page, [
      'Usage Metrics',
      'Impersonate',
      'Job Control',
      'Operators',
    ]);
    await logout(page);

    await loginAs(page, PID.ina);
    await expect(page.getByRole('link', { name: 'Operations' })).toBeVisible();
    await openOperations(page);
    await expectOperationsContextLinks(page, ['Usage Metrics', 'Job Control', 'Operators']);
    await expectOperationsContextLinksAbsent(page, ['Impersonate']);
    await logout(page);

    await loginAs(page, PID.tatum);
    await expect(page.getByRole('link', { name: 'Operations' })).toBeVisible();
    await openOperations(page);
    await expectOperationsContextLinks(page, ['Usage Metrics', 'Job Control']);
    await expectOperationsContextLinksAbsent(page, ['Impersonate', 'Operators']);
  });

  test('hides the Operations nav for non-operators', async ({ page }) => {
    await loginAs(page, PID.sally);
    await expect(page.getByRole('link', { name: 'Operations' })).toHaveCount(0);
    await page.goto('/operations');
    await page.waitForURL('**/courses');
    await expect(page.getByRole('link', { name: 'Operations' })).toHaveCount(0);
  });

  test('allows a superadmin to impersonate another user and exit impersonation', async ({
    page,
  }) => {
    await loginAs(page, PID.amy);
    await openOperations(page);

    await page.getByRole('link', { name: 'Impersonate' }).click();
    await page.waitForURL('**/operations/impersonate');
    await page.locator('input[autocomplete="off"]').fill('Sally');

    await expect(page.getByRole('cell', { name: 'Sally Student' })).toBeVisible();
    const sallyRow = page.locator('tr', { hasText: 'Sally Student' }).first();
    await sallyRow.getByRole('button', { name: 'Impersonate' }).click();

    await page.waitForURL('**/courses');
    await expect(page.getByRole('alert')).toContainText('Viewing as Sally Student');
    await expect(page.getByRole('link', { name: 'Operations' })).toHaveCount(0);
    await expect(page.getByLabel('Edit profile')).toContainText('Sally Student');

    await page.getByRole('button', { name: 'Exit Impersonation' }).click();
    await page.waitForURL('**/operations/metrics');
    await expect(page.getByRole('link', { name: 'Operations' })).toBeVisible();
    await expect(page.getByLabel('Edit profile')).toContainText('Amy Administrator');
  });

  test('allows a superadmin to elevate an existing user to an operator role', async ({ page }) => {
    await loginAs(page, PID.amy);
    await openOperations(page);
    await goToOperators(page);

    await addOperator(page, PID.ina, 'admin');

    const row = await operatorRow(page, 'Ina Instructor');
    await expect(row.getByText('222222222')).toBeVisible();
    await expect(row.getByText('admin', { exact: true })).toBeVisible();

    await logout(page);
    await loginAs(page, PID.ina);
    await expect(page.getByRole('link', { name: 'Operations' })).toBeVisible();
  });

  test('allows a superadmin to modify an operator role and applies the new permissions', async ({
    page,
  }) => {
    await loginAs(page, PID.amy);
    await openOperations(page);
    await goToOperators(page);

    await addOperator(page, PID.ina, 'admin');
    await changeOperatorRole(page, 'Ina Instructor', 'helpdesk');

    const row = await operatorRow(page, 'Ina Instructor');
    await expect(row.getByText('helpdesk', { exact: true })).toBeVisible();

    await logout(page);
    await loginAs(page, PID.ina);
    await openOperations(page);
    await expectOperationsContextLinks(page, ['Usage Metrics', 'Job Control']);
    await expectOperationsContextLinksAbsent(page, ['Impersonate', 'Operators']);
  });

  test('shows usage metrics cards on the metrics page', async ({ page }) => {
    await loginAs(page, PID.amy);
    await openOperations(page);

    const metricsRegion = page.getByRole('region', { name: 'Usage Metrics' });
    await expect(metricsRegion).toBeVisible();
    await expect(metricsRegion.getByText('Active Users')).toBeVisible();
    await expect(metricsRegion.getByText('Active Courses')).toBeVisible();
    await expect(metricsRegion.getByText('Submissions')).toBeVisible();
    await expect(metricsRegion.getByText('Jobs Run')).toBeVisible();
    await expect(metricsRegion.locator('.metric-card')).toHaveCount(4);
  });

  test('shows job control panes and queue table for operators', async ({ page }) => {
    await loginAs(page, PID.amy);
    await openOperations(page);
    await openJobControl(page);

    const jobControlRegion = page.getByRole('region', { name: 'Job Control' });
    await expect(jobControlRegion.getByRole('heading', { name: 'Now' })).toBeVisible();
    await expect(jobControlRegion.getByRole('heading', { name: 'Queues' })).toBeVisible();
    await expect(jobControlRegion.getByRole('heading', { name: 'Failures' })).toBeVisible();
    await expect(jobControlRegion.getByRole('heading', { name: 'Workers' })).toBeVisible();
    await expect(page.getByRole('switch', { name: 'Toggle auto-refresh' })).toBeVisible();
    await expect(jobControlRegion.locator('.queue-table')).toBeVisible();
  });
});
