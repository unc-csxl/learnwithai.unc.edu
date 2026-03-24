import { expect, test } from '@playwright/test';

test.describe('course settings', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('instructor can edit course settings', async ({ page }) => {
    // Login as Ina Instructor
    await page.goto('/api/auth/as/222222222');
    await page.waitForURL('**/courses');

    // Navigate to the course
    await page.getByText('COMP423').click();
    await page.waitForURL('**/courses/*/dashboard');

    // Navigate to Course Settings
    await page.getByRole('link', { name: 'Course Settings' }).click();
    await page.waitForURL('**/courses/*/settings');

    // Form should be pre-populated with existing course data
    const courseNumberInput = page.locator('input[formControlName="course_number"]');
    const nameInput = page.locator('input[formControlName="name"]');
    const descInput = page.locator('textarea[formControlName="description"]');

    await expect(courseNumberInput).toHaveValue('COMP423');
    await expect(nameInput).toHaveValue('Foundations of Software Engineering');

    // Update the description
    await descInput.fill('An updated course description');

    // Submit the form
    await page.getByRole('button', { name: 'Save' }).click();

    // Should show success message
    await expect(page.getByRole('status')).toContainText('Course settings updated');
  });

  test('student cannot see course settings link', async ({ page }) => {
    // Login as Sally Student
    await page.goto('/api/auth/as/111111111');
    await page.waitForURL('**/courses');

    // Navigate to the course
    await page.getByText('COMP423').click();
    await page.waitForURL('**/courses/*/activities');

    // Student view should not show Course Settings
    const sidenav = page.locator('mat-sidenav');
    await expect(sidenav.getByRole('link', { name: 'Course Settings' })).toHaveCount(0);
  });
});
