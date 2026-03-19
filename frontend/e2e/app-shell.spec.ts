import { expect, test } from '@playwright/test';

test('renders the application shell', async ({ page }) => {
  await page.goto('/courses');

  await expect(page.getByRole('link', { name: 'Learn with AI home' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Courses' })).toBeVisible();
  await expect(page.getByText('My Courses')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Login' })).toBeVisible();
});
