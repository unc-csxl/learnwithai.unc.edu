/*
 * Copyright (c) 2026 Kris Jordan
 * SPDX-License-Identifier: MIT
 */

import { expect, test } from '@playwright/test';

test.describe('course settings', () => {
  test.beforeEach(async ({ request }) => {
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

    // Should navigate back to the course dashboard
    await page.waitForURL('**/courses/*/dashboard');

    // Should show a success snackbar notification
    await expect(page.getByText('Course settings updated.')).toBeVisible({ timeout: 5000 });
  });

  test('sidebar reflects updated course number and name after save', async ({ page }) => {
    // Login as Ina Instructor
    await page.goto('/api/auth/as/222222222');
    await page.waitForURL('**/courses');

    // Navigate to the course
    await page.getByText('COMP423').click();
    await page.waitForURL('**/courses/*/dashboard');

    const sidenav = page.locator('mat-sidenav');

    // Sidebar initially shows old course info
    await expect(sidenav).toContainText('COMP423');

    // Navigate to Course Settings and change course number and name
    await page.getByRole('link', { name: 'Course Settings' }).click();
    await page.waitForURL('**/courses/*/settings');

    const courseNumberInput = page.locator('input[formControlName="course_number"]');
    const nameInput = page.locator('input[formControlName="name"]');
    await courseNumberInput.fill('COMP524');
    await nameInput.fill('Advanced Software Engineering');

    await page.getByRole('button', { name: 'Save' }).click();
    await page.waitForURL('**/courses/*/dashboard');

    // Sidebar should immediately reflect the updated course number.
    await expect(sidenav).toContainText('COMP524');

    // The course list should reflect the updated name after returning to courses.
    await page.getByRole('link', { name: 'Courses' }).click();
    await page.waitForURL('**/courses');
    await expect(page.getByText('Advanced Software Engineering')).toBeVisible();
  });

  test('student cannot see course settings link', async ({ page }) => {
    // Login as Sally Student
    await page.goto('/api/auth/as/111111111');
    await page.waitForURL('**/courses');

    // Navigate to the course
    await page.getByText('COMP423').click();
    await page.waitForURL('**/courses/*/student');

    // Student view should not show Course Settings
    const sidenav = page.locator('mat-sidenav');
    await expect(sidenav.getByRole('link', { name: 'Course Settings' })).toHaveCount(0);
  });
});
