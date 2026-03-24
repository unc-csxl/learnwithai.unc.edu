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

    // Readonly fields should display correct values
    const pidInput = page.locator('input[readonly]').first();
    await expect(pidInput).toHaveValue('222222222');

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

    // Should show success message
    await expect(page.getByRole('status')).toContainText('Profile updated');

    // The sidenav should reflect the updated name
    await expect(page.getByRole('link', { name: 'Edit profile' })).toContainText(
      'Irene Instructor',
    );
  });
});
