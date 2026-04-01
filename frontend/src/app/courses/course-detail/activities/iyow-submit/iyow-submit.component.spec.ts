import { TestBed } from '@angular/core/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { signal, WritableSignal } from '@angular/core';
import { IyowSubmit } from './iyow-submit.component';
import { PageTitleService } from '../../../../page-title.service';
import { SuccessSnackbarService } from '../../../../success-snackbar.service';
import { JobUpdateService } from '../../../../job-update.service';
import { ActivityService } from '../activity.service';

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
        { provide: ActivityService, useValue: mockActivityService },
        { provide: ActivatedRoute, useValue: mockRoute },
      ],
    });

    const fixture = TestBed.createComponent(IyowSubmit);
    fixture.detectChanges();

    return { fixture, mockPageTitle, mockSnackbar, mockJobUpdate, mockActivityService, jobSignals };
  }

  it('should load activity and set title', async () => {
    const { fixture, mockPageTitle } = setup();
    await flush();
    fixture.detectChanges();

    expect(mockPageTitle.setTitle).toHaveBeenCalledWith('Test IYOW');
    expect(fixture.nativeElement.textContent).toContain('Explain X');
  });

  it('should subscribe to job updates and unsubscribe on destroy', () => {
    const { fixture, mockJobUpdate } = setup();
    expect(mockJobUpdate.subscribe).toHaveBeenCalledWith(1);

    fixture.destroy();
    expect(mockJobUpdate.unsubscribe).toHaveBeenCalledWith(1);
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
          response_text: 'My answer',
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

    expect(fixture.nativeElement.textContent).toContain('Good work!');
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

    // Should show spinner for pending
    expect(fixture.nativeElement.textContent).toContain('Generating feedback');

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
});
