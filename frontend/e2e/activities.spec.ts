import { expect, test } from '@playwright/test';

// PIDs from dev_data.py
const INSTRUCTOR_PID = '222222222';
const STUDENT_PID = '111111111';

const SEEDED_ACTIVITY_TITLE = 'Explain Dependency Injection';
const SEEDED_PROMPT =
  'In your own words, explain what dependency injection is and why it is useful in software engineering.';

/** Login as a specific user and navigate to the course's activities page. */
async function goToActivities(page: import('@playwright/test').Page, pid: string): Promise<number> {
  await page.goto(`/api/auth/as/${pid}`);
  await page.waitForURL('**/courses');

  await page.getByText('COMP423').click();
  await page.waitForURL('**/courses/*/dashboard');

  await page.getByRole('link', { name: /Student Activities/i }).click();
  await page.waitForURL('**/courses/*/activities');

  const match = page.url().match(/\/courses\/(\d+)\//);
  if (!match) throw new Error(`Could not determine course ID from URL: ${page.url()}`);
  return Number(match[1]);
}

test.describe('activities — instructor creates an IYOW activity', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('displays the seeded activity on the activities list', async ({ page }) => {
    await goToActivities(page, INSTRUCTOR_PID);

    // The seeded activity should be visible
    await expect(page.getByText(SEEDED_ACTIVITY_TITLE)).toBeVisible();
    await expect(page.locator('mat-chip').getByText('IYOW')).toBeVisible();
  });

  test('instructor can create a new IYOW activity', async ({ page }) => {
    const courseId = await goToActivities(page, INSTRUCTOR_PID);

    // Click the create button
    await page.getByRole('link', { name: /Create IYOW Activity/i }).click();
    await page.waitForURL(`**/courses/${courseId}/activities/create-iyow`);

    // Fill out the form
    await page.getByLabel('Title').fill('Explain Recursion');
    await page.getByLabel('Prompt').fill('In your own words, explain what recursion is.');
    await page.getByLabel('Rubric').fill('Student should mention base case and self-referencing.');
    await page.getByLabel('Release date').fill('2025-01-01T00:00');
    await page.getByLabel('Due date').fill('2026-12-31T23:59');

    // Submit the form
    await page.getByRole('button', { name: 'Create Activity' }).click();

    // Should redirect back to the activities list with a success snackbar
    await page.waitForURL(`**/courses/${courseId}/activities`);
    await expect(page.getByText('IYOW activity created!')).toBeVisible();

    // The new activity should be in the list
    await expect(page.getByText('Explain Recursion')).toBeVisible();
  });
});

test.describe('activities — student submits to an activity', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('student sees the seeded activity in their activities list', async ({ page }) => {
    await goToActivities(page, STUDENT_PID);

    // Student should see the released activity
    await expect(page.getByText(SEEDED_ACTIVITY_TITLE)).toBeVisible();

    // Student should NOT see the Create button
    await expect(page.getByRole('link', { name: /Create IYOW Activity/i })).not.toBeVisible();
  });

  test('student can view activity and see their existing submission', async ({ page }) => {
    const courseId = await goToActivities(page, STUDENT_PID);

    // Click into the seeded activity (students go to submit page)
    await page.getByText(SEEDED_ACTIVITY_TITLE).click();
    await page.waitForURL(`**/courses/${courseId}/activities/*/submit`);

    // The activity prompt should be displayed
    await expect(page.getByText(SEEDED_PROMPT)).toBeVisible();

    // The seeded submission should be visible with its feedback
    await expect(page.getByText('Your Submission')).toBeVisible();
    await expect(
      page.getByText('Dependency injection is when you pass the things', { exact: false }),
    ).toBeVisible();
    await expect(page.getByText('AI Feedback')).toBeVisible();
    await expect(
      page.getByText('Great start! You correctly identified', { exact: false }),
    ).toBeVisible();
  });

  test('student can make a new submission', async ({ page }) => {
    const courseId = await goToActivities(page, STUDENT_PID);

    // Navigate to the activity submit page
    await page.getByText(SEEDED_ACTIVITY_TITLE).click();
    await page.waitForURL(`**/courses/${courseId}/activities/*/submit`);

    // The "Submit Again" heading should be present since there's already a submission
    await expect(page.getByText('Submit Again')).toBeVisible();

    // Fill in a new response
    const responseText =
      'Dependency injection means that instead of a class creating its own dependencies, ' +
      'they are provided from the outside. This makes code more testable and flexible.';
    await page.getByLabel('Your response').fill(responseText);

    // Submit the form
    await page.getByRole('button', { name: 'Submit' }).click();

    // Should show success snackbar
    await expect(page.getByText('Response submitted!')).toBeVisible();

    // The new submission should appear
    await expect(page.getByText(responseText)).toBeVisible();
  });
});

test.describe('activities — instructor views student submissions', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('instructor can view activity detail with prompt and rubric', async ({ page }) => {
    const courseId = await goToActivities(page, INSTRUCTOR_PID);

    // Click on the seeded activity (instructors go to detail page)
    await page.getByText(SEEDED_ACTIVITY_TITLE).click();
    await page.waitForURL(`**/courses/${courseId}/activities/*`);

    // Verify activity information is displayed
    const content = page.getByLabel('Activity information');
    await expect(content.getByText(SEEDED_ACTIVITY_TITLE)).toBeVisible();
    await expect(content.getByText('IYOW Activity')).toBeVisible();
    await expect(content.getByText(SEEDED_PROMPT)).toBeVisible();

    // Instructor should see the rubric
    await expect(content.getByText('Rubric')).toBeVisible();
    await expect(content.getByText('The student should mention', { exact: false })).toBeVisible();
  });

  test('instructor sees the seeded student submission with feedback', async ({ page }) => {
    const courseId = await goToActivities(page, INSTRUCTOR_PID);

    await page.getByText(SEEDED_ACTIVITY_TITLE).click();
    await page.waitForURL(`**/courses/${courseId}/activities/*`);

    // The submissions section should show the student's submission
    await expect(page.getByText('Submissions')).toBeVisible();
    await expect(page.getByText('Student 111111111')).toBeVisible();
    await expect(
      page.getByText('Dependency injection is when you pass the things', { exact: false }),
    ).toBeVisible();

    // The feedback should be visible
    await expect(
      page.getByText('Great start! You correctly identified', { exact: false }),
    ).toBeVisible();
  });
});

test.describe('activities — student does not see rubric', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('student sees the prompt but not the rubric on the submit page', async ({ page }) => {
    const courseId = await goToActivities(page, STUDENT_PID);

    await page.getByText(SEEDED_ACTIVITY_TITLE).click();
    await page.waitForURL(`**/courses/${courseId}/activities/*/submit`);

    // The prompt should be displayed
    await expect(page.getByText(SEEDED_PROMPT)).toBeVisible();

    // The rubric should NOT be visible to students
    await expect(page.getByText('The student should mention', { exact: false })).not.toBeVisible();
  });
});

test.describe('activities — full instructor-to-student flow', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('instructor creates activity, student submits, instructor sees it', async ({ page }) => {
    // Step 1: Instructor creates a new activity
    const courseId = await goToActivities(page, INSTRUCTOR_PID);

    await page.getByRole('link', { name: /Create IYOW Activity/i }).click();
    await page.waitForURL(`**/courses/${courseId}/activities/create-iyow`);

    await page.getByLabel('Title').fill('Explain Testing');
    await page.getByLabel('Prompt').fill('Explain why automated testing is important.');
    await page.getByLabel('Rubric').fill('Should mention regression prevention and confidence.');
    await page.getByLabel('Release date').fill('2025-01-01T00:00');
    await page.getByLabel('Due date').fill('2026-12-31T23:59');
    await page.getByRole('button', { name: 'Create Activity' }).click();
    await page.waitForURL(`**/courses/${courseId}/activities`);
    await expect(page.getByText('Explain Testing')).toBeVisible();

    // Step 2: Student logs in and submits to the new activity
    await page.goto(`/api/auth/as/${STUDENT_PID}`);
    await page.waitForURL('**/courses');
    await page.getByText('COMP423').click();
    await page.waitForURL('**/courses/*/dashboard');
    await page.getByRole('link', { name: /Student Activities/i }).click();
    await page.waitForURL('**/courses/*/activities');
    await page.getByText('Explain Testing').click();
    await page.waitForURL(`**/courses/${courseId}/activities/*/submit`);

    // Should show prompt, no existing submission
    await expect(page.getByText('Explain why automated testing is important.')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Your Response' })).toBeVisible();

    await page
      .getByLabel('Your response')
      .fill(
        'Automated testing is important because it catches regressions early ' +
          'and gives developers confidence when refactoring code.',
      );
    await page.getByRole('button', { name: 'Submit' }).click();
    await expect(page.getByText('Response submitted!')).toBeVisible();

    // Step 3: Instructor views the new activity and sees the student's submission
    await page.goto(`/api/auth/as/${INSTRUCTOR_PID}`);
    await page.waitForURL('**/courses');
    await page.getByText('COMP423').click();
    await page.waitForURL('**/courses/*/dashboard');
    await page.getByRole('link', { name: /Student Activities/i }).click();
    await page.waitForURL('**/courses/*/activities');
    await page.getByText('Explain Testing').click();
    await page.waitForURL(`**/courses/${courseId}/activities/*`);

    // Instructor should see the student's submission
    await expect(page.getByText('Student 111111111')).toBeVisible();
    await expect(page.getByText('catches regressions early', { exact: false })).toBeVisible();
  });
});
