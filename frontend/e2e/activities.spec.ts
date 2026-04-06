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
  test.beforeEach(async ({ request }) => {
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
    await expect(page.getByRole('button', { name: 'Try Again' })).toBeVisible();
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

    await page.getByRole('button', { name: 'Try Again' }).click();

    const responseField = page.getByLabel('Your response');
    await expect(responseField).toHaveValue(/Dependency injection is when you pass/i);

    // Fill in a new response
    const responseText =
      '**Dependency injection** means that instead of a class creating its own dependencies, ' +
      'they are provided from the outside. This makes code more testable and flexible.';
    await responseField.fill(responseText);

    // Submit the form
    await page.getByRole('button', { name: 'Save' }).click();

    // Should show success snackbar
    await expect(page.getByText('Response submitted!')).toBeVisible();

    // The new submission should appear
    const submissionSection = page.getByLabel('Your submission');
    await expect(submissionSection.locator('strong')).toContainText('Dependency injection');
    await expect(page.getByRole('button', { name: 'Try Again' })).toBeVisible();
  });

  test('student can cancel a dirty edit and return to the saved submission view', async ({
    page,
  }) => {
    const courseId = await goToActivities(page, STUDENT_PID);

    await page.getByText(SEEDED_ACTIVITY_TITLE).click();
    await page.waitForURL(`**/courses/${courseId}/activities/*/submit`);

    await page.getByRole('button', { name: 'Try Again' }).click();
    await page.getByLabel('Your response').fill('Edited response that should be discarded.');

    page.once('dialog', async (dialog) => {
      expect(dialog.message()).toContain('Discard your unsaved changes?');
      await dialog.accept();
    });

    await page.getByRole('button', { name: 'Cancel' }).click();

    await expect(page.getByLabel('Your response')).toHaveCount(0);
    await expect(page.getByRole('region', { name: 'Your submission' })).toContainText(
      'Dependency injection is when you pass the things',
    );
    await expect(page.getByRole('button', { name: 'Try Again' })).toBeVisible();
  });
});

test.describe('activities — instructor views student submissions', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('instructor sees the simplified activity date card on the submissions page', async ({
    page,
  }) => {
    const courseId = await goToActivities(page, INSTRUCTOR_PID);

    // Click on the seeded activity (instructors go to detail page)
    await page.getByText(SEEDED_ACTIVITY_TITLE).click();
    await page.waitForURL(`**/courses/${courseId}/activities/*`);

    // Verify the simplified activity information card is displayed
    const content = page.getByLabel('Activity information');
    await expect(content.getByText('Release date')).toBeVisible();
    await expect(content.getByText('Due date')).toBeVisible();
    await expect(content.getByText(SEEDED_PROMPT)).not.toBeVisible();
    await expect(content.getByText('Rubric')).not.toBeVisible();
  });

  test('instructor sees roster table with submitted and non-submitted students', async ({
    page,
  }) => {
    const courseId = await goToActivities(page, INSTRUCTOR_PID);

    await page.getByText(SEEDED_ACTIVITY_TITLE).click();
    await page.waitForURL(`**/courses/${courseId}/activities/*`);

    // The submissions table should show enrolled students
    const table = page.getByRole('table', { name: 'Student submissions' });
    await expect(table).toBeVisible();

    // Sally Student submitted — should be a link
    await expect(table.getByRole('link', { name: 'Student, Sally' })).toBeVisible();

    // The summary should show submission count
    await expect(page.getByLabel('Submission summary')).toContainText('students have submitted');
  });

  test('instructor clicks student name to view submission detail', async ({ page }) => {
    const courseId = await goToActivities(page, INSTRUCTOR_PID);

    await page.getByText(SEEDED_ACTIVITY_TITLE).click();
    await page.waitForURL(`**/courses/${courseId}/activities/*`);

    // Click the student link
    const table = page.getByRole('table', { name: 'Student submissions' });
    await table.getByRole('link', { name: 'Student, Sally' }).click();
    await page.waitForURL(`**/courses/${courseId}/activities/*/submissions/*`);

    await expect(page.getByRole('heading', { name: /Submission \d+/ })).toBeVisible();
    await expect(page.getByLabel('Submission navigation')).toContainText(
      'Submitted by Sally Student',
    );
    await expect(page.getByRole('button', { name: 'Previous' })).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Next' })).toBeDisabled();
    await expect(page.getByLabel('Jump to a submitted student')).toBeVisible();

    // Should see the submission detail with response text and feedback
    await expect(
      page.getByText('Dependency injection is when you pass the things', { exact: false }),
    ).toBeVisible();
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

    // Should show prompt and an empty submission card.
    await expect(page.getByText('Explain why automated testing is important.')).toBeVisible();
    await expect(page.getByText('Your Submission')).toBeVisible();

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

    // Instructor should see the student's submission in the roster table
    const table = page.getByRole('table', { name: 'Student submissions' });
    await expect(table.getByRole('link', { name: 'Student, Sally' })).toBeVisible();
  });
});

test.describe('activities — real-time feedback processing', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('student submits, sees processing spinner, then feedback appears', async ({ page }) => {
    const courseId = await goToActivities(page, STUDENT_PID);

    // Navigate to the seeded activity submit page
    await page.getByText(SEEDED_ACTIVITY_TITLE).click();
    await page.waitForURL(`**/courses/${courseId}/activities/*/submit`);

    await page.getByRole('button', { name: 'Try Again' }).click();

    // Submit a new response
    await page
      .getByLabel('Your response')
      .fill(
        'Dependency injection is a design pattern where objects receive their dependencies ' +
          'from external sources rather than creating them internally.',
      );
    await page.getByRole('button', { name: 'Save' }).click();
    await expect(page.getByText('Response submitted!')).toBeVisible();

    // After submitting, a processing spinner should appear while the LLM job runs
    const status = page.getByRole('status');

    await expect(status).toContainText('The AI is reviewing your latest submission.', {
      timeout: 5000,
    });

    // Ultimately, AI Feedback should appear when the job completes via WebSocket
    await expect(page.getByText('AI Feedback')).toBeVisible({ timeout: 30000 });

    const feedbackSection = page.getByLabel('AI feedback');
    await expect(feedbackSection.getByText('AI Feedback')).toBeVisible();
    await expect(status).not.toBeVisible({ timeout: 30000 });
  });
});

test.describe('activities — table views', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('instructor sees table with title, dates, and submission count columns', async ({
    page,
  }) => {
    await goToActivities(page, INSTRUCTOR_PID);

    const table = page.getByLabel('Activities list');
    await expect(table).toBeVisible();

    // Verify column headers
    await expect(table.getByText('Title')).toBeVisible();
    await expect(table.getByText('Released Date')).toBeVisible();
    await expect(table.getByText('Due Date (User TZ)')).toBeVisible();
    await expect(table.getByText('Submissions')).toBeVisible();

    // The seeded activity should be a clickable link in the Title column
    const link = table.getByRole('link', { name: SEEDED_ACTIVITY_TITLE });
    await expect(link).toBeVisible();
  });

  test('student sees table with title, status, released date, and due columns', async ({
    page,
  }) => {
    await goToActivities(page, STUDENT_PID);

    const table = page.getByLabel('Activities list');
    await expect(table).toBeVisible();

    // Verify column headers
    await expect(table.getByText('Title')).toBeVisible();
    await expect(table.getByText('Status')).toBeVisible();
    await expect(table.getByText('Released Date')).toBeVisible();
    await expect(table.getByText('Due (User TZ)')).toBeVisible();

    // No submission count column for students
    await expect(table.getByText('Submissions')).not.toBeVisible();

    // The seeded activity should be a clickable link
    const link = table.getByRole('link', { name: SEEDED_ACTIVITY_TITLE });
    await expect(link).toBeVisible();
  });
});

test.describe('activities — submission detail with history', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('instructor can view full submission history for a student', async ({ page }) => {
    // First, have the student make a second submission so there's history
    const courseId = await goToActivities(page, STUDENT_PID);
    await page.getByText(SEEDED_ACTIVITY_TITLE).click();
    await page.waitForURL(`**/courses/${courseId}/activities/*/submit`);
    await page.getByRole('button', { name: 'Try Again' }).click();
    await page
      .getByLabel('Your response')
      .fill('Second attempt: DI means providing dependencies externally.');
    await page.getByRole('button', { name: 'Save' }).click();
    await expect(page.getByText('Response submitted!')).toBeVisible();

    // Now login as instructor and view the activity detail
    await page.goto(`/api/auth/as/${INSTRUCTOR_PID}`);
    await page.waitForURL('**/courses');
    await page.getByText('COMP423').click();
    await page.waitForURL('**/courses/*/dashboard');
    await page.getByRole('link', { name: /Student Activities/i }).click();
    await page.waitForURL('**/courses/*/activities');
    await page.getByText(SEEDED_ACTIVITY_TITLE).click();
    await page.waitForURL(`**/courses/${courseId}/activities/*`);

    // Click the student name to go to submission detail
    const table = page.getByRole('table', { name: 'Student submissions' });
    await table.getByRole('link', { name: 'Student, Sally' }).click();
    await page.waitForURL(`**/courses/${courseId}/activities/*/submissions/*`);

    await expect(page.getByRole('heading', { name: /Submission \d+/ })).toBeVisible();

    // Should show both submissions (most recent first, numbered from top)
    const submissionCards = page.locator('mat-card-title');
    await expect(submissionCards.filter({ hasText: 'Submission 1' })).toBeVisible();
    await expect(submissionCards.filter({ hasText: 'Submission 2' })).toBeVisible();

    // Second attempt should be visible
    await expect(
      page.getByText('Second attempt: DI means providing dependencies externally.'),
    ).toBeVisible();
  });
});

test.describe('activities — instructor edits activity', () => {
  test.beforeAll(async ({ request }) => {
    await request.post('/api/dev/reset-db');
  });

  test('instructor can edit an existing activity', async ({ page }) => {
    const courseId = await goToActivities(page, INSTRUCTOR_PID);

    // Go to activity detail
    await page.getByText(SEEDED_ACTIVITY_TITLE).click();
    await page.waitForURL(`**/courses/${courseId}/activities/*`);

    // Navigate to the edit page via sidenav
    await page.getByRole('link', { name: /Activity Editor/i }).click();
    await page.waitForURL(`**/courses/${courseId}/activities/*/edit`);

    // The form should be pre-populated
    await expect(page.getByLabel('Title')).toHaveValue(SEEDED_ACTIVITY_TITLE);

    // Update the title
    await page.getByLabel('Title').fill('Updated: Explain DI');
    await page.getByRole('button', { name: 'Save Changes' }).click();

    // Should redirect back to activity detail with success message
    await expect(page.getByText('Activity updated!')).toBeVisible();
    await page.waitForURL(`**/courses/${courseId}/activities/*`);

    await page.getByRole('link', { name: /Student Activities/i }).click();
    await page.waitForURL(`**/courses/${courseId}/activities`);
    await expect(page.getByText('Updated: Explain DI')).toBeVisible();
  });
});
