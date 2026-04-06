import { TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { signal, WritableSignal } from '@angular/core';
import { IyowSubmit } from './iyow-submit.component';
import { PageTitleService } from '../../../../page-title.service';
import { SuccessSnackbarService } from '../../../../success-snackbar.service';
import { JobUpdateService } from '../../../../job-update.service';
import { LayoutNavigationService } from '../../../../layout/layout-navigation.service';
import { ActivityService } from '../activity.service';
import { CourseService } from '../../../course.service';

const flush = () => new Promise((resolve) => setTimeout(resolve));

const baseActivity = {
  id: 10,
  title: 'Test IYOW',
  prompt: 'Explain X',
  type: 'iyow',
  release_date: '2025-01-01T00:00:00Z',
  due_date: '2025-06-01T00:00:00Z',
  course_id: 1,
  created_at: '2025-01-01T00:00:00Z',
};

describe('IyowSubmit', () => {
  function setup(
    overrides: {
      activityService?: object;
      jobSignals?: Map<number, WritableSignal<{ status: string } | null>>;
    } = {},
  ) {
    const mockPageTitle = { title: vi.fn(), setTitle: vi.fn() };
    const mockSnackbar = { open: vi.fn() };
    const jobSignals = overrides.jobSignals ?? new Map();
    const mockJobUpdate = {
      subscribe: vi.fn(),
      unsubscribe: vi.fn(),
      updateForJob: vi.fn((id: number) => {
        if (!jobSignals.has(id)) jobSignals.set(id, signal(null));
        return jobSignals.get(id)!;
      }),
    };
    const mockActivityService = overrides.activityService ?? {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      getActiveSubmission: vi.fn(() => Promise.resolve(null)),
      submitIyow: vi.fn(() =>
        Promise.resolve({
          id: 100,
          response_text: 'My answer',
          feedback: null,
          job: { id: 42, status: 'pending' },
        }),
      ),
    };
    const mockCourseService = {
      getMyCourses: vi.fn(() =>
        Promise.resolve([
          {
            id: 1,
            course_number: 'COMP423',
            name: 'Foundations of Software Engineering',
            description: '',
            term: 'spring',
            year: 2026,
            membership: { type: 'student', state: 'enrolled' },
          },
        ]),
      ),
    };
    const mockLayoutNavigation = { setContextSection: vi.fn(), clearContext: vi.fn() };
    const mockRoute = {
      parent: { parent: { snapshot: { paramMap: new Map([['id', '1']]) } } },
      snapshot: { paramMap: new Map([['activityId', '10']]) },
    };

    TestBed.configureTestingModule({
      imports: [IyowSubmit],
      providers: [
        provideRouter([]),
        { provide: PageTitleService, useValue: mockPageTitle },
        { provide: SuccessSnackbarService, useValue: mockSnackbar },
        { provide: JobUpdateService, useValue: mockJobUpdate },
        { provide: LayoutNavigationService, useValue: mockLayoutNavigation },
        { provide: CourseService, useValue: mockCourseService },
        { provide: ActivityService, useValue: mockActivityService },
        { provide: ActivatedRoute, useValue: mockRoute },
      ],
    });

    const fixture = TestBed.createComponent(IyowSubmit);
    fixture.detectChanges();

    return {
      fixture,
      mockPageTitle,
      mockSnackbar,
      mockJobUpdate,
      mockActivityService,
      mockCourseService,
      mockLayoutNavigation,
      jobSignals,
    };
  }

  it('should load activity and set title', async () => {
    const { fixture, mockPageTitle, mockLayoutNavigation } = setup();
    await flush();
    fixture.detectChanges();

    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Test IYOW');
    expect(mockLayoutNavigation.setContextSection).toHaveBeenCalledWith(
      expect.objectContaining({
        visibleBaseRoutes: ['/courses/1/student', '/courses/1/activities'],
        groups: expect.arrayContaining([
          expect.objectContaining({
            items: expect.arrayContaining([
              expect.objectContaining({
                route: '/courses/1/activities/10/submit',
                label: 'Submissions',
              }),
            ]),
          }),
        ]),
      }),
    );
    expect(fixture.nativeElement.textContent).toContain('Explain X');
  });

  it('should render the initial submission editor inside the submission card', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    const content = fixture.nativeElement.textContent;

    expect(content).toContain('Your Submission');
    expect(content).not.toContain('Submitted');
    expect(content).not.toContain('AI Feedback');
    expect(fixture.nativeElement.querySelector('textarea')).not.toBeNull();
  });

  it('should show preview and test context for staff users', async () => {
    const { fixture, mockCourseService, mockLayoutNavigation } = setup();
    mockCourseService.getMyCourses.mockResolvedValueOnce([
      {
        id: 1,
        course_number: 'COMP423',
        name: 'Foundations of Software Engineering',
        description: '',
        term: 'spring',
        year: 2026,
        membership: { type: 'instructor', state: 'enrolled' },
      },
    ]);

    const newFixture = TestBed.createComponent(IyowSubmit);
    newFixture.detectChanges();
    await flush();
    newFixture.detectChanges();

    expect(mockLayoutNavigation.setContextSection).toHaveBeenLastCalledWith(
      expect.objectContaining({
        visibleBaseRoutes: ['/courses/1/dashboard', '/courses/1/activities'],
        groups: expect.arrayContaining([
          expect.objectContaining({
            items: expect.arrayContaining([
              expect.objectContaining({ route: '/courses/1/activities/10', label: 'Submissions' }),
              expect.objectContaining({ label: 'Activity Editor' }),
              expect.objectContaining({ label: 'Preview & Test' }),
            ]),
          }),
        ]),
      }),
    );

    fixture.destroy();
    newFixture.destroy();
  });

  it('should subscribe to job updates and unsubscribe on destroy', () => {
    const { fixture, mockJobUpdate, mockLayoutNavigation } = setup();
    expect(mockJobUpdate.subscribe).toHaveBeenCalledWith(1);

    fixture.destroy();
    expect(mockJobUpdate.unsubscribe).toHaveBeenCalledWith(1);
    expect(mockLayoutNavigation.clearContext).not.toHaveBeenCalled();
  });

  it('should submit response via template and show snackbar', async () => {
    const { fixture, mockActivityService, mockSnackbar } = setup();
    await flush();
    fixture.detectChanges();

    const component = fixture.componentInstance;
    (component as unknown as { form: { patchValue: (v: object) => void } }).form.patchValue({
      response_text: 'This is my detailed explanation of the concept.',
    });
    fixture.detectChanges();

    const form = fixture.nativeElement.querySelector('form') as HTMLFormElement;
    form.dispatchEvent(new Event('submit'));
    await flush();
    fixture.detectChanges();

    expect(
      (mockActivityService as { submitIyow: ReturnType<typeof vi.fn> }).submitIyow,
    ).toHaveBeenCalledOnce();
    expect(mockSnackbar.open).toHaveBeenCalledWith('Response submitted!');
    expect(fixture.nativeElement.textContent).toContain('My answer');
    expect(fixture.nativeElement.textContent).toContain('Try Again');
    expect(fixture.nativeElement.querySelector('textarea')).toBeNull();
  });

  it('should show error on submission failure', async () => {
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      getActiveSubmission: vi.fn(() => Promise.resolve(null)),
      submitIyow: vi.fn(() => Promise.reject(new Error('fail'))),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    const component = fixture.componentInstance;
    (component as unknown as { form: { patchValue: (v: object) => void } }).form.patchValue({
      response_text: 'This is my detailed explanation of the concept.',
    });

    (component as unknown as { onSubmit: () => Promise<void> }).onSubmit();
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Failed to submit response.');
  });

  it('should not submit if form is invalid', async () => {
    const { fixture, mockActivityService } = setup();
    const component = fixture.componentInstance;

    (component as unknown as { onSubmit: () => Promise<void> }).onSubmit();
    await flush();

    expect(
      (mockActivityService as { submitIyow: ReturnType<typeof vi.fn> }).submitIyow,
    ).not.toHaveBeenCalled();
  });

  it('should show error on load failure', async () => {
    const mockActivityService = {
      get: vi.fn(() => Promise.reject(new Error('fail'))),
      getActiveSubmission: vi.fn(() => Promise.reject(new Error('fail'))),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Failed to load activity.');
  });

  it('should display active submission with feedback', async () => {
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      getActiveSubmission: vi.fn(() =>
        Promise.resolve({
          id: 100,
          response_text: '**My answer**',
          feedback: '- Good work!',
          is_active: true,
          submitted_at: '2025-03-01T00:00:00Z',
          job: { id: 42, status: 'completed', completed_at: '2025-03-01T01:00:00Z' },
        }),
      ),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Your Submission');
    expect(fixture.nativeElement.textContent).toContain('Submitted');
    expect(fixture.nativeElement.textContent).toContain('Try Again');
    expect(fixture.nativeElement.querySelector('textarea')).toBeNull();
    expect(fixture.nativeElement.textContent).toContain('AI Feedback');
    expect(fixture.nativeElement.querySelector('strong')?.textContent).toContain('My answer');
    expect(fixture.nativeElement.querySelector('li')?.textContent).toContain('Good work!');
  });

  it('should let the student edit a saved submission from the response text', async () => {
    const existingResponse = 'Dependency injection is useful because dependencies are provided.';
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      getActiveSubmission: vi.fn(() =>
        Promise.resolve({
          id: 100,
          response_text: existingResponse,
          feedback: 'Good work!',
          is_active: true,
          submitted_at: '2025-03-01T00:00:00Z',
          job: { id: 42, status: 'completed', completed_at: '2025-03-01T01:00:00Z' },
        }),
      ),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    const editButton = fixture.nativeElement.querySelector(
      'button[aria-label="Edit your submission"]',
    ) as HTMLButtonElement;
    editButton.click();
    fixture.detectChanges();

    const textarea = fixture.nativeElement.querySelector('textarea') as HTMLTextAreaElement;
    expect(textarea).not.toBeNull();
    expect(textarea.value).toContain(existingResponse);
    expect(fixture.nativeElement.textContent).toContain('Save');
  });

  it('should let the student edit a saved submission from the try again button', async () => {
    const existingResponse = 'Dependency injection keeps code testable and easier to swap.';
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      getActiveSubmission: vi.fn(() =>
        Promise.resolve({
          id: 101,
          response_text: existingResponse,
          feedback: 'Keep going!',
          is_active: true,
          submitted_at: '2025-03-01T00:00:00Z',
          job: { id: 43, status: 'completed', completed_at: '2025-03-01T01:00:00Z' },
        }),
      ),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    const tryAgainButton = fixture.nativeElement.querySelector(
      'button[mat-stroked-button]',
    ) as HTMLButtonElement;
    tryAgainButton.click();
    fixture.detectChanges();

    const textarea = fixture.nativeElement.querySelector('textarea') as HTMLTextAreaElement;
    expect(textarea.value).toContain(existingResponse);
    expect(fixture.nativeElement.textContent).toContain('Save');
    expect(fixture.nativeElement.textContent).toContain('Cancel');
  });

  it('should cancel editing without a confirmation when there are no changes', async () => {
    const existingResponse = 'Dependency injection keeps code testable and easier to swap.';
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      getActiveSubmission: vi.fn(() =>
        Promise.resolve({
          id: 101,
          response_text: existingResponse,
          feedback: 'Keep going!',
          is_active: true,
          submitted_at: '2025-03-01T00:00:00Z',
          job: { id: 43, status: 'completed', completed_at: '2025-03-01T01:00:00Z' },
        }),
      ),
    };
    const confirmSpy = vi.spyOn(globalThis, 'confirm');
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    const tryAgainButton = fixture.nativeElement.querySelector(
      'button[mat-stroked-button]',
    ) as HTMLButtonElement;
    tryAgainButton.click();
    fixture.detectChanges();

    const buttons = Array.from(
      fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>,
    );
    const cancelButton = buttons.find((button) =>
      button.textContent?.includes('Cancel'),
    ) as HTMLButtonElement;
    cancelButton.click();
    fixture.detectChanges();

    expect(confirmSpy).not.toHaveBeenCalled();
    expect(fixture.nativeElement.querySelector('textarea')).toBeNull();

    confirmSpy.mockRestore();
  });

  it('should confirm before discarding dirty edits', async () => {
    const existingResponse = 'Dependency injection keeps code testable and easier to swap.';
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      getActiveSubmission: vi.fn(() =>
        Promise.resolve({
          id: 101,
          response_text: existingResponse,
          feedback: 'Keep going!',
          is_active: true,
          submitted_at: '2025-03-01T00:00:00Z',
          job: { id: 43, status: 'completed', completed_at: '2025-03-01T01:00:00Z' },
        }),
      ),
    };
    const confirmSpy = vi.spyOn(globalThis, 'confirm').mockReturnValue(true);
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    const tryAgainButton = fixture.nativeElement.querySelector(
      'button[mat-stroked-button]',
    ) as HTMLButtonElement;
    tryAgainButton.click();
    fixture.detectChanges();

    const textarea = fixture.nativeElement.querySelector('textarea') as HTMLTextAreaElement;
    textarea.value = 'Changed answer';
    textarea.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    const buttons = Array.from(
      fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>,
    );
    const cancelButton = buttons.find((button) =>
      button.textContent?.includes('Cancel'),
    ) as HTMLButtonElement;
    cancelButton.click();
    fixture.detectChanges();

    expect(confirmSpy).toHaveBeenCalledWith('Discard your unsaved changes?');
    expect(fixture.nativeElement.querySelector('textarea')).toBeNull();
    expect(fixture.nativeElement.textContent).toContain(existingResponse);

    confirmSpy.mockRestore();
  });

  it('should keep editing when discard confirmation is rejected', async () => {
    const existingResponse = 'Dependency injection keeps code testable and easier to swap.';
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      getActiveSubmission: vi.fn(() =>
        Promise.resolve({
          id: 101,
          response_text: existingResponse,
          feedback: 'Keep going!',
          is_active: true,
          submitted_at: '2025-03-01T00:00:00Z',
          job: { id: 43, status: 'completed', completed_at: '2025-03-01T01:00:00Z' },
        }),
      ),
    };
    const confirmSpy = vi.spyOn(globalThis, 'confirm').mockReturnValue(false);
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    const tryAgainButton = fixture.nativeElement.querySelector(
      'button[mat-stroked-button]',
    ) as HTMLButtonElement;
    tryAgainButton.click();
    fixture.detectChanges();

    const textarea = fixture.nativeElement.querySelector('textarea') as HTMLTextAreaElement;
    textarea.value = 'Changed answer';
    textarea.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    const buttons = Array.from(
      fixture.nativeElement.querySelectorAll('button') as NodeListOf<HTMLButtonElement>,
    );
    const cancelButton = buttons.find((button) =>
      button.textContent?.includes('Cancel'),
    ) as HTMLButtonElement;
    cancelButton.click();
    fixture.detectChanges();

    expect(confirmSpy).toHaveBeenCalledWith('Discard your unsaved changes?');
    expect(fixture.nativeElement.querySelector('textarea')).not.toBeNull();
    expect((fixture.nativeElement.querySelector('textarea') as HTMLTextAreaElement).value).toBe(
      'Changed answer',
    );

    confirmSpy.mockRestore();
  });

  it('should ignore edit requests when there is no active submission', async () => {
    const { fixture } = setup();
    await flush();
    fixture.detectChanges();

    const component = fixture.componentInstance as unknown as {
      startEditingSubmission: () => void;
      editingSubmission: () => boolean;
    };

    component.startEditingSubmission();

    expect(component.editingSubmission()).toBe(false);
  });

  it('should ignore cancel requests when edit mode is not active', async () => {
    const existingResponse = 'Dependency injection keeps code testable and easier to swap.';
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      getActiveSubmission: vi.fn(() =>
        Promise.resolve({
          id: 101,
          response_text: existingResponse,
          feedback: 'Keep going!',
          is_active: true,
          submitted_at: '2025-03-01T00:00:00Z',
          job: { id: 43, status: 'completed', completed_at: '2025-03-01T01:00:00Z' },
        }),
      ),
    };
    const confirmSpy = vi.spyOn(globalThis, 'confirm');
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    const component = fixture.componentInstance as unknown as {
      cancelEditingSubmission: () => void;
      editingSubmission: () => boolean;
    };

    component.cancelEditingSubmission();

    expect(confirmSpy).not.toHaveBeenCalled();
    expect(component.editingSubmission()).toBe(false);

    confirmSpy.mockRestore();
  });

  it('should watch pending active submission job and refresh on complete', async () => {
    const jobSignals = new Map<number, WritableSignal<{ status: string } | null>>();
    const pendingSub = {
      id: 200,
      response_text: 'Waiting',
      feedback: null,
      is_active: true,
      submitted_at: '2025-03-01T00:00:00Z',
      job: { id: 77, status: 'pending' },
    };
    const completedSub = { ...pendingSub, feedback: 'Done!', job: { id: 77, status: 'completed' } };

    const getActiveSubmission = vi
      .fn()
      .mockResolvedValueOnce(pendingSub)
      .mockResolvedValueOnce(completedSub);

    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      getActiveSubmission,
    };
    const { fixture } = setup({ activityService: mockActivityService, jobSignals });
    await flush();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain(
      'The AI is reviewing your latest submission.',
    );
    expect(fixture.nativeElement.textContent).not.toContain('Generating feedback');

    // Simulate job completing
    jobSignals.get(77)!.set({ status: 'completed' });
    TestBed.flushEffects();
    await flush();
    fixture.detectChanges();

    expect(getActiveSubmission).toHaveBeenCalledTimes(2);
  });

  it('should watch job after submit when job is not completed', async () => {
    const jobSignals = new Map<number, WritableSignal<{ status: string } | null>>();
    const { fixture, mockActivityService } = setup({ jobSignals });
    await flush();
    fixture.detectChanges();

    const component = fixture.componentInstance;
    (component as unknown as { form: { patchValue: (v: object) => void } }).form.patchValue({
      response_text: 'This is my detailed explanation of the concept.',
    });

    (component as unknown as { onSubmit: () => Promise<void> }).onSubmit();
    await flush();
    fixture.detectChanges();

    // Should have started watching job 42
    expect(
      (mockActivityService as { submitIyow: ReturnType<typeof vi.fn> }).submitIyow,
    ).toHaveBeenCalledOnce();
    expect(jobSignals.has(42)).toBe(true);
  });

  it('should not watch job when submit returns completed status', async () => {
    const jobSignals = new Map<number, WritableSignal<{ status: string } | null>>();
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      getActiveSubmission: vi.fn(() => Promise.resolve(null)),
      submitIyow: vi.fn(() =>
        Promise.resolve({
          id: 100,
          response_text: 'Done',
          feedback: 'Immediate feedback',
          job: { id: 99, status: 'completed' },
        }),
      ),
    };
    const { fixture } = setup({ activityService: mockActivityService, jobSignals });
    await flush();
    fixture.detectChanges();

    const component = fixture.componentInstance;
    (component as unknown as { form: { patchValue: (v: object) => void } }).form.patchValue({
      response_text: 'This is my detailed explanation of the concept.',
    });

    (component as unknown as { onSubmit: () => Promise<void> }).onSubmit();
    await flush();
    fixture.detectChanges();

    expect(jobSignals.has(99)).toBe(false);
  });

  it('should show spinner while submitting', async () => {
    let resolveSubmit!: (v: unknown) => void;
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      getActiveSubmission: vi.fn(() => Promise.resolve(null)),
      submitIyow: vi.fn(
        () =>
          new Promise((resolve) => {
            resolveSubmit = resolve;
          }),
      ),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    const component = fixture.componentInstance;
    (component as unknown as { form: { patchValue: (v: object) => void } }).form.patchValue({
      response_text: 'This is my detailed explanation of the concept.',
    });

    (component as unknown as { onSubmit: () => Promise<void> }).onSubmit();
    fixture.detectChanges();

    const button = fixture.nativeElement.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    expect(button.disabled).toBe(true);

    resolveSubmit({ id: 100, response_text: 'x', feedback: null, job: null });
    await flush();
    fixture.detectChanges();
  });

  it('should show saving state while resubmitting an existing response', async () => {
    let resolveSubmit!: (v: unknown) => void;
    const existingResponse = 'Dependency injection allows dependencies to be provided.';
    const mockActivityService = {
      get: vi.fn(() => Promise.resolve({ ...baseActivity })),
      getActiveSubmission: vi.fn(() =>
        Promise.resolve({
          id: 100,
          response_text: existingResponse,
          feedback: 'Prior feedback',
          is_active: true,
          submitted_at: '2025-03-01T00:00:00Z',
          job: { id: 42, status: 'completed', completed_at: '2025-03-01T01:00:00Z' },
        }),
      ),
      submitIyow: vi.fn(
        () =>
          new Promise((resolve) => {
            resolveSubmit = resolve;
          }),
      ),
    };
    const { fixture } = setup({ activityService: mockActivityService });
    await flush();
    fixture.detectChanges();

    const tryAgainButton = fixture.nativeElement.querySelector(
      'button[mat-stroked-button]',
    ) as HTMLButtonElement;
    tryAgainButton.click();
    fixture.detectChanges();

    const form = fixture.nativeElement.querySelector('form') as HTMLFormElement;
    form.dispatchEvent(new Event('submit'));
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain('Saving');

    resolveSubmit({ id: 101, response_text: existingResponse, feedback: null, job: null });
    await flush();
    fixture.detectChanges();
  });
});
